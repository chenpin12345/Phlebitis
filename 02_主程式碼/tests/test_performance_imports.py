"""Isolated correctness tests; never load a model or mutate production data."""
import json
import shutil
from pathlib import Path
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from workbench_fixture import configure
from src.common import read_manifest,read_json,write_json,sha256
from src.imports import service
from src.workbench.queries import data_index,images

@pytest.fixture
def environment(tmp_path,monkeypatch):
    app,artifact=configure(tmp_path,monkeypatch,include_reports=True)
    with TestClient(app) as client:yield tmp_path,client,artifact

def photo(root,name='batch'):
    path=root/'inbox/photos'/name/'photo.jpg';path.parent.mkdir(parents=True,exist_ok=True)
    Image.new('RGB',(100,80),'purple').save(path);return path

def test_warm_queries_do_not_hash(environment,monkeypatch):
    root,client,_=environment
    from src.data import dataset
    monkeypatch.setattr(dataset,'audit',lambda *_:pytest.fail('GET must not perform audit'))
    for _ in range(3):
        assert client.get('/api/v1/data-query?view=approved').json()['total']==6
        assert client.get('/api/v1/overview').json()['data']['approved']==6

def test_stale_index_never_grants_eligibility(environment,monkeypatch):
    root,client,_=environment
    monkeypatch.setattr(data_index,'request_rebuild',lambda root:None)
    data_index.invalidate(root)
    assert client.get('/api/v1/data-query?view=approved').json()['total']==0
    rows=client.get('/api/v1/data-query?view=all&size=100').json()['items']
    assert all(not row['training_eligible'] for row in rows)
    data_index.rebuild(root)
    assert client.get('/api/v1/data-query?view=approved').json()['total']==6

def test_photo_idempotency_dedup_and_source_preservation(environment):
    root,_,_=environment;source=photo(root);before=len(read_manifest(root))
    shutil.copy2(source,source.with_name('duplicate.jpg'))
    item=service.preview(root,'photos','batch');assert sorted(x['action'] for x in item['items'])==['add','skip']
    result=service.commit(root,item['id'],'fixed');assert result['state']=='completed'
    assert service.commit(root,item['id'],'fixed')['state']=='completed'
    rows=read_manifest(root);assert len(rows)==before+1
    row=next(r for r in rows if r['image_id'].startswith('import_'))
    assert row['status']=='pending_review' and row['label_state']=='unknown' and row['group_verified']=='false'
    assert sha256(root/row['image_path'])==sha256(source) and source.exists()
    assert all(x['action']=='skip' for x in service.preview(root,'photos','batch')['items'])

def test_corrupt_photo_changed_source_and_disk_full(environment,monkeypatch):
    root,_,_=environment;source=photo(root)
    source.with_name('bad.jpg').write_bytes(b'not an image')
    item=service.preview(root,'photos','batch');assert any(x['action']=='reject' for x in item['items'])
    source.write_bytes(b'changed')
    assert service.commit(root,item['id'],'changed')['state']=='failed'
    source=photo(root,'disk');item=service.preview(root,'photos','disk')
    monkeypatch.setattr(shutil,'disk_usage',lambda _:type('Disk',(),{'free':0})())
    assert '磁碟' in service.commit(root,item['id'],'disk')['error']
    assert len(read_manifest(root))==42

def test_unknown_model_does_not_deserialize(environment):
    root,_,_=environment;folder=root/'inbox/models/unknown';folder.mkdir(parents=True)
    (folder/'best.pt').write_bytes(b'unsafe pickle')
    result=service.preview(root,'models','unknown');assert result['state']=='failed' and 'package.json' in result['error']

def test_traced_model_new_version_does_not_activate(environment):
    root,_,artifact=environment
    folder=root/'inbox/models/known';shutil.copytree(root/'models/versions'/artifact['id'],folder)
    write_json(folder/'package.json',{'schema_version':1,'purpose':'inference','model':artifact['model'],'source':{'type':'project_artifact','id':artifact['id']},'files':artifact['files'],'config':artifact['config']})
    item=service.preview(root,'models','known');assert item['state']=='ready'
    result=service.commit(root,item['id'],'model');assert result['state']=='completed'
    ident=result['items'][0]['artifact'];assert ident!=artifact['id']
    assert read_json(root/'models/versions'/ident/'artifact.json')['extra']['import_operation']==item['id']
    assert read_json(root/'models/versions'/ident/'artifact.json')['extra']['dataset']==artifact['extra']['dataset']
    assert not list((root/'runtime/imports/staging'/item['id']).glob('*.pt'))
    assert not (root/'models/references/local.json').exists()
    assert not (root/'models/references/line.json').exists()

def test_model_path_traversal_rejected(environment):
    root,_,artifact=environment;folder=root/'inbox/models/bad';folder.mkdir(parents=True)
    write_json(folder/'package.json',{'schema_version':1,'purpose':'inference','model':'yolo11n','source':{'type':'project_artifact','id':artifact['id']},'files':{'../outside.pt':'0'}})
    assert service.preview(root,'models','bad')['state']=='failed'

def test_cache_rechecks_missing_and_modified_source(environment):
    root,_,_=environment;row=read_manifest(root)[0]
    first=images.render(root,row,True);assert first==images.render(root,row,True)
    (root/row['image_path']).write_bytes(b'changed')
    with pytest.raises(ValueError):images.render(root,row,True)
    (root/row['image_path']).unlink()
    with pytest.raises(FileNotFoundError):images.render(root,row,True)

def test_curve_partial_line_and_replacement(tmp_path):
    from src.workbench.queries.curves import lines
    path=tmp_path/'progress.jsonl';path.write_bytes(b'{"epoch":1}\n{"epoch":')
    assert lines(path)==['{"epoch":1}']
    with path.open('ab') as f:f.write(b'2}\n')
    assert len(lines(path))==2
    path.write_bytes(b'new\n');assert lines(path)==['new']

def test_import_interrupted_before_manifest_is_resumable(environment,monkeypatch):
    root,_,_=environment;photo(root);item=service.preview(root,'photos','batch')
    original=service.write_manifest
    monkeypatch.setattr(service,'write_manifest',lambda *a:(_ for _ in ()).throw(OSError('injected commit failure')))
    result=service.commit(root,item['id'],'interrupt');assert result['state']=='failed'
    assert len(read_manifest(root))==42
    monkeypatch.setattr(service,'write_manifest',original)
    result=service.commit(root,item['id'],'interrupt',retry=True)
    assert result['state']=='completed' and len(read_manifest(root))==43
    assert len({r['image_id'] for r in read_manifest(root)})==43

def test_restart_does_not_automatically_import(environment):
    root,_,_=environment;photo(root);item=service.preview(root,'photos','batch')
    item.update(state='running',idem='restart');service.save(root,item);service.recover(root)
    assert service.load(root,item['id'])['state']=='needs_check'
    assert len(read_manifest(root))==42
    assert service.commit(root,item['id'],'restart',retry=True)['state']=='completed'

def test_expired_preview_and_foreign_session_rejected(environment):
    root,_,_=environment;photo(root);item=service.preview(root,'photos','batch',session='one')
    with pytest.raises(ValueError):service.commit(root,item['id'],'x',session='two')
    item['expires']=0;service.save(root,item)
    with pytest.raises(ValueError):service.commit(root,item['id'],'x',session='one')

def test_hardlink_source_and_annotation_not_accepted(environment):
    root,_,_=environment;source=photo(root)
    import os
    os.link(source,source.with_name('linked.jpg'))
    item=service.preview(root,'photos','batch')
    assert all(i['action']=='reject' for i in item['items'])

def test_annotation_provisional_and_exif_preserved(environment):
    root,_,_=environment;source=photo(root)
    exif=Image.Exif();exif[274]=6;Image.new('RGB',(120,80),'purple').save(source,exif=exif)
    source.with_suffix('.txt').write_text('0 0.5 0.5 0.3 0.4\n')
    item=service.preview(root,'photos','batch');assert item['items'][0]['annotations'][0]['state']=='needs_confirmation'
    result=service.commit(root,item['id'],'exif');assert result['state']=='completed'
    row=next(r for r in read_manifest(root) if r['image_id'].startswith('import_'))
    assert row['annotation_path']==row['yolo_path']==''
    assert sha256(root/row['image_path'])==sha256(source)

def test_job_summary_and_report_page_are_bounded(environment):
    root,client,_=environment
    result=client.get('/api/v1/jobs-query?size=1&kind=train').json()
    assert result['total']==3 and len(result['items'])==1
    assert 'result' not in result['items'][0] and 'log' not in result['items'][0]
    report=client.get('/api/v1/reports-query?model=yolo11n&size=1').json()
    assert report['total']==2 and len(report['items'])==1 and 'samples' not in report['items'][0]

def test_snapshot_options_and_optional_logs(environment):
    root,client,_=environment
    write_json(root/'data/yolo/options/dataset_version.json',{'version':'options','folds':[{'fold':0,'dataset':'options/fold0/dataset.yaml','members':{'train':['a','b'],'val':['c']}}]})
    response=client.get('/api/v1/snapshot-options');assert response.status_code==200
    assert response.json()[0]['folds'][0]['counts']=={'train':2,'val':1}
    for item in response.json():
        for fold in item['folds']:assert 'counts' in fold and 'members' not in fold
    ident='1'*32
    from src.workbench import jobs
    (jobs.folder(ident)/'worker.log').write_text('test log')
    assert client.get(f'/api/v1/jobs/{ident}?details=false').json()['log']==''
    assert client.get(f'/api/v1/jobs/{ident}?details=true').json()['log']=='test log'

def test_cases_and_events_paginate_full_collection(environment):
    root,client,_=environment
    from src.workbench.storage import db
    with db() as con:
        for i in range(65):
            con.execute('INSERT INTO cases(id,revision,data) VALUES(?,?,?)',(f'case{i:04}',1,json.dumps({'id':f'case{i:04}','revision':1})))
            con.execute('INSERT INTO events(id,session,message,status,payload,updated) VALUES(?,?,?,?,?,?)',(f'event{i:04}','paging',str(i),'queued' if i==0 else 'completed','{}',100))
    cases=client.get('/api/v1/cases-query?size=30').json();assert cases['total']>=65 and len(cases['items'])==30
    event=client.get('/api/v1/simulation-query?session=paging&size=30&page=2').json()
    assert event['total']==65 and event['active_count']==1 and len(event['items'])==30
    assert client.get('/api/v1/simulation-query?size=1000').status_code==400

def test_interrupted_scan_can_be_rescanned(environment):
    root,_,_=environment;photo(root);item=service.preview(root,'photos','batch')
    item['state']='scanning';service.save(root,item);service.recover(root)
    assert service.load(root,item['id'])['state']=='failed'
    assert service.preview(root,'photos','batch')['state']=='ready'

def test_concurrent_image_requests_convert_once(environment,monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    root,_,_=environment;row=read_manifest(root)[0];images.clear(root)
    original=images.sha256;calls=[]
    def counted(path):calls.append(path);return original(path)
    monkeypatch.setattr(images,'sha256',counted)
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(lambda _:images.render(root,row,True),range(4)))
    assert len(calls)==1 and all(value==results[0] for value in results)

def test_official_receipt_import_and_selection(environment,monkeypatch):
    root,_,_=environment
    from src.workbench import adapters
    import requests
    class Download:
        status_code=200;headers={'content-length':'17'}
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def raise_for_status(self):pass
        def iter_content(self,*args):yield b'synthetic weights'
    monkeypatch.setattr(requests,'get',lambda *a,**k:Download())
    monkeypatch.setattr(adapters,'PRETRAINED',root/'models/pretrained')
    job=root/'runs/workbench/jobs'/('9'*32);job.mkdir(parents=True)
    source=adapters.prepare_verified('yolo11n',job)
    proof=read_json(root/'runtime/imports/trusted-official/yolo11n.json')
    package=root/'inbox/models/official';package.mkdir(parents=True);shutil.copy2(source,package/source.name)
    write_json(package/'package.json',{'schema_version':1,'purpose':'base','model':'yolo11n','source':{'type':'official'},'files':proof['files']})
    item=service.preview(root,'models','official');assert item['state']=='ready'
    item=service.commit(root,item['id'],'official');assert item['state']=='completed'
    path,_=service.resolve_package(root,item['id'],'base','yolo11n');assert sha256(path/source.name)==sha256(source)

def test_single_data_rebuild_for_concurrent_requests(environment,monkeypatch):
    import threading
    from concurrent.futures import ThreadPoolExecutor
    root,_,_=environment;entered=threading.Event();release=threading.Event();calls=[]
    def controlled(root):calls.append(root);entered.set();release.wait(5)
    monkeypatch.setattr(data_index,'rebuild',controlled)
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda _:data_index.request_rebuild(root),range(8)))
    assert entered.wait(1) and len(calls)==1
    release.set();data_index._workers[str(root)].join(2)

def test_checkpoint_import_is_not_inference_model(environment,monkeypatch):
    root,_,_=environment
    from src.workbench import jobs,registry,adapters
    from src.workbench.contracts import Experiment
    from src.data import dataset
    ident='2'*32;cfg=Experiment(model='efficientnet_b0',dataset='fixture/fold0/dataset.yaml',device='cpu').model_dump()
    with jobs.db() as con:con.execute('UPDATE jobs SET config=? WHERE id=?',(json.dumps(cfg),ident))
    folder=jobs.folder(ident)
    for name in ('last.pt','artifact/model.pt','experiment.json','effective.json'):
        p=folder/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'{}' if p.suffix=='.json' else b'synthetic-checkpoint')
    package=root/'inbox/models/checkpoint';package.mkdir(parents=True)
    files={}
    for name in ('last.pt','artifact/model.pt','experiment.json','effective.json'):
        p=package/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(folder/name,p);files[name]=sha256(p)
    monkeypatch.setattr(dataset,'validate_split',lambda *a:{})
    write_json(package/'package.json',{'schema_version':1,'purpose':'checkpoint','model':'efficientnet_b0','source':{'type':'project_job','id':ident},'files':files})
    item=service.preview(root,'models','checkpoint');assert item['state']=='ready'
    item=service.commit(root,item['id'],'checkpoint');assert item['state']=='completed'
    model_id=item['items'][0]['artifact']
    assert model_id not in {m['id'] for m in registry.listing()}
    with pytest.raises(ValueError):registry.activate(model_id,allow_unevaluated=True)
    resume=Experiment(**{**cfg,'resume_job':ident,'checkpoint_import':item['id']})
    assert adapters.resume_folder(resume)==registry.artifact_path(model_id)
    assert jobs.enqueue('train',resume.model_dump(),'checkpoint-job')['state']=='queued'
    from src.workbench import trash
    blockers,_,_=trash.dependencies('model',model_id,registry.get(model_id))
    assert any('checkpoint_import' in b for b in blockers)
