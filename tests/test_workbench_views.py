import io
import json
from datetime import datetime, timezone
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from src.common import read_manifest, read_json, write_json, sha256
from src.data.dataset import review, build
from src.workbench import views, presentation, registry, storage
from workbench_fixture import configure

@pytest.fixture
def app(tmp_path,monkeypatch):
    application,artifact=configure(tmp_path,monkeypatch)
    with TestClient(application) as client:
        csrf=client.get('/api/v1/session').json()['csrf']
        client.headers.update({'X-CSRF-Token':csrf,'X-Operator':'%E6%B8%AC%E8%A9%A6%E7%94%B2'})
        yield client,tmp_path,artifact

def payload(client,ident,decision='approve',label='positive'):
    item=client.get('/api/v1/data/'+ident+'/annotation').json()
    return {'revision':item['revision'],'status':views.DECISIONS[decision],'decision':decision,'reviewer':'測試甲','reason':'synthetic review','label':label,'boxes':[[0,.5,.5,.4,.6]] if label=='positive' else []}

def test_overview_available_contract_and_full_query(app):
    c,root,_=app
    overview=c.get('/api/v1/overview').json()
    for view in ('approved','pending_review','excluded'):
        data=c.get('/api/v1/data-query',params={'view':view,'size':100}).json()
        assert overview['data'][view]==data['total']==len(data['items'])
        if view=='approved': assert {r['image_id'] for r in data['items']}=={r['image_id'] for r in read_manifest(root) if r['status']=='approved'}
    assert c.get('/api/v1/data-query?view=nope').status_code==400
    assert c.get('/api/v1/data-query?page=0').status_code==400
    first=c.get('/api/v1/data-query?view=pending_review&size=30').json()
    second=c.get('/api/v1/data-query?view=pending_review&size=30&page=2').json()
    assert len(first['items'])==30 and len(second['items'])==5
    assert not ({r['image_id'] for r in first['items']}&{r['image_id'] for r in second['items']})
    # Hospital-confirmed fixtures remain available without fabricated review identity/time.
    assert all(r['review'] is None for r in c.get('/api/v1/data-query?view=approved').json()['items'])

def test_review_transitions_filters_history_and_immutable_snapshot(app):
    c,root,_=app;ident='a_landscape'
    result=c.put('/api/v1/data/'+ident,json=payload(c,ident));assert result.status_code==200,result.text
    query=c.get('/api/v1/data-query?view=reviewed&reviewer='+__import__('urllib.parse',fromlist=['quote']).quote('測試甲')).json()
    assert query['total']==1 and query['items'][0]['review']['decision']=='approve'
    info=build(root=root);fold=info['folds'][0];saved=read_json(root/fold['dataset'].replace('dataset.yaml','split.json'))
    member=next(m for ms in saved['members'].values() for m in ms if m['image_id']==ident)
    original_hash=sha256(root/member['label_path']);assert member['review_revision']
    for decision in ('needs_changes','approve','exclude','reopen'):
        body=payload(c,ident,decision);r=c.put('/api/v1/data/'+ident,json=body);assert r.status_code==200,r.text
        completed=decision in ('approve','exclude')
        assert c.get('/api/v1/data-query?view=reviewed').json()['total']==int(completed)
        assert (ident in {x['image_id'] for x in c.get('/api/v1/data-query?view=approved').json()['items']})==(decision=='approve')
        assert c.put('/api/v1/data/'+ident,json=body).status_code==409
    assert len(c.get('/api/v1/data/'+ident+'/annotation').json()['history'])==5
    assert read_json(root/fold['dataset'].replace('dataset.yaml','split.json'))==saved
    assert sha256(root/member['label_path'])==original_hash
    assert read_json(root/'data/snapshot_states.json')[info['version']]['status']=='superseded'
    # Latest effective reviewer, not historical participant.
    body=payload(c,ident);body['reviewer']='測試乙';assert c.put('/api/v1/data/'+ident,json=body).status_code==200
    assert views.query_data(root,'reviewed',reviewer='測試甲')['total']==0
    assert views.query_data(root,'reviewed',reviewer='測試乙')['total']==1

@pytest.mark.parametrize('ident,size',[('a_landscape',(160,90)),('b_portrait',(90,160)),('c_square',(100,100)),('d_exif',(90,160))])
def test_preview_exif_and_annotation_save_reload(app,ident,size):
    c,root,_=app;row=next(r for r in read_manifest(root) if r['image_id']==ident);before=sha256(root/row['image_path'])
    response=c.get('/api/v1/data/'+ident+'/image');im=Image.open(io.BytesIO(response.content));assert im.size==size and im.getexif().get(274,1)==1
    body=payload(c,ident);body['boxes']=[[0,.4,.3,.2,.2]]
    assert c.put('/api/v1/data/'+ident,json=body).status_code==200
    actual=c.get('/api/v1/data/'+ident+'/annotation').json()['boxes'][0]
    assert actual==pytest.approx(body['boxes'][0],abs=1e-6)
    assert sha256(root/row['image_path'])==before

def test_mismatched_coordinates_are_not_silently_erased(app):
    c,root,_=app;ident='p_mismatch';old=c.get('/api/v1/data/'+ident+'/annotation').json();assert old['coordinate_warning'] and old['boxes']==[]
    body=payload(c,ident);assert c.put('/api/v1/data/'+ident,json=body).status_code==400
    assert c.get('/api/v1/data/'+ident+'/annotation').json()['revision']==old['revision']
    body['coordinate_resolution']='redraw';assert c.put('/api/v1/data/'+ident,json=body).status_code==200
    history=c.get('/api/v1/data/'+ident+'/annotation').json()['history']
    assert history[-1]['annotation_before']['imageWidth']==90
    assert history[-1]['annotation_after']['imageWidth']==160

def test_curve_sources_missing_duplicate_and_partial_lines(app):
    c,root,_=app;folder=root/'runs/workbench/jobs'/('1'*32)
    (folder/'progress.jsonl').write_text('{"epoch":2,"metrics":{"metrics/mAP50(B)":0.45}}\n{"epoch":4,"val_loss":1}\n{"epoch":')
    (folder/'training/results.csv').write_text('epoch,train/box_loss,val/box_loss,metrics/mAP50(B)\n1,1.2,1.4,.3\n2,.9,nan,.5\n2,.85,inf,.52\n3,.7,.8,.6\n')
    d=c.get('/api/v1/curve-history?source='+'1'*32).json()
    assert [p['epoch'] for p in d['points']]==[1,2,3]
    assert d['points'][1]['val/box_loss'] is None and d['points'][1]['metrics/mAP50(B)']==.52
    assert d['source']=='results.csv' and d['checkpoint']['epoch']==3 and d['warnings']
    efficient=c.get('/api/v1/curve-history?source='+'2'*32).json();assert efficient['task']=='classification' and 'val_accuracy' in efficient['metrics'] and 'train/box_loss' not in efficient['metrics']
    assert not c.get('/api/v1/curve-history?source='+'3'*32).json()['metrics']
    assert c.get('/api/v1/jobs/'+'4'*32+'/curves').status_code==400
    legacy=next(s for s in c.get('/api/v1/curve-sources').json() if s['id'].startswith('legacy_'))
    old=c.get('/api/v1/curve-history',params={'source':legacy['id']}).json();assert old['has_image'] and not old['points']
    assert c.get('/api/v1/curve-image',params={'source':legacy['id']}).status_code==200
    assert c.get('/api/v1/curve-history?source=../../secret').status_code==400

def test_artifact_details_settings_download_export_and_loader(app,monkeypatch):
    c,root,artifact=app;ident=artifact['id'];original=registry.get(ident)
    detail=c.get('/api/v1/artifacts/'+ident+'/detail').json()
    assert detail['requested']['parameters']['lr0']==.01 and detail['effective']['parameters']['lr0']==.005
    assert all(f['state']=='readable' and f['size']>0 for f in detail['files'])
    settings=c.get('/api/v1/artifacts/'+ident+'/settings?key=settings.json').json();assert settings['secret']=='[已遮罩]' and settings['names']=={'0':'phlebitis'}
    downloaded=c.get('/api/v1/artifacts/'+ident+'/file?key=best.pt');assert downloaded.content==b'synthetic-weight-for-download-tests' and 'attachment' in downloaded.headers['content-disposition']
    exported=c.get('/api/v1/artifacts/'+ident+'/export');assert exported.json()['inference']==original['config'] and 'attachment' in exported.headers['content-disposition']
    assert c.get('/api/v1/artifacts/'+ident+'/file?key=../../.env').status_code==400
    from src.workbench import adapters
    from src import model_api
    seen=[]
    class FakeYOLO:
        names={0:'phlebitis'}
        task='detect'
        def __init__(self,path):seen.append(Path(path).read_bytes())
    from pathlib import Path
    monkeypatch.setattr(model_api,'yolo_api',lambda:FakeYOLO)
    loaded=adapters.ModelPredictor(ident,'cpu');assert loaded.metadata==original and seen==[downloaded.content]
    path=registry.artifact_path(ident)/'settings.json';path.unlink()
    missing=c.get('/api/v1/artifacts/'+ident+'/detail').json();assert next(f for f in missing['files'] if f['name']=='settings.json')['state']=='missing'
    assert c.get('/api/v1/artifacts/'+ident+'/file?key=settings.json').status_code==404

def test_audit_timezone_stable_pages_unknowns_facets_and_actor(app):
    c,root,_=app;home=root/'runtime/workbench'
    lo,hi=views.date_bounds('2026-09-29','2026-09-29')
    assert datetime.fromtimestamp(lo,timezone.utc).isoformat().startswith('2026-09-28T16:00:00')
    with storage.db(home) as con:
        for at in (lo-1,lo,hi-1,hi):con.execute('INSERT INTO audit(at,actor,action,detail) VALUES(?,?,?,?)',(at,'edge','boundary','{}'))
        same=lo+100
        for i in range(4):con.execute('INSERT INTO audit(at,actor,action,detail) VALUES(?,?,?,?)',(same,'same','tie',json.dumps({'id':str(i),'_audit':{'outcome':'submitted'}})))
    d=c.get('/api/v1/audit-query?start=2026-09-29&end=2026-09-29&action=boundary').json();assert d['total']==2 and all(r['outcome']=='unknown' for r in d['items'])
    first=c.get('/api/v1/audit-query?action=tie&size=2').json()
    with storage.db(home) as con:con.execute('INSERT INTO audit(at,actor,action,detail) VALUES(?,?,?,?)',(same,'new','tie','{}'))
    second=c.get('/api/v1/audit-query',params={'action':'tie','size':2,'page':2,'snapshot':first['snapshot']}).json()
    assert first['total']==second['total']==4 and min(r['id'] for r in first['items'])>max(r['id'] for r in second['items'])
    assert 'new' in second['actors'] and 'boundary' in second['actions']
    assert c.get('/api/v1/audit-query?actor=__unknown__').json()['total']>=1
    assert c.get('/api/v1/audit-query?related='+'1'*32).json()['total']>=37
    assert c.get('/api/v1/audit-query?outcome=fake').status_code==400
    c.put('/api/v1/templates',json=[])
    actual=c.get('/api/v1/audit-query?action=save_templates').json()['items'][0];assert actual['actor']=='測試甲' and actual['outcome']=='succeeded'
    c.get('/api/v1/data-query?view=invalid') # GET doesn't produce a fabricated successful audit.
    c.put('/api/v1/data/absent',json={})
    assert c.get('/api/v1/audit-query?action=request_failed&outcome=failed').json()['total']>=1

def test_review_unknown_identity_and_filters_include_late_page(app):
    c,root,_=app
    body=payload(c,'p_033',label='negative');body['reviewer']='local_operator'
    assert c.put('/api/v1/data/p_033',json=body).status_code==200
    result=views.query_data(root,'reviewed',reviewer='__unknown__',size=1)
    assert result['total']==1 and result['items'][0]['image_id']=='p_033'
    assert result['items'][0]['review']['reviewer'] is None
    body=payload(c,'p_032',label='negative');body['reviewer']='last-page-reviewer'
    assert c.put('/api/v1/data/p_032',json=body).status_code==200
    assert views.query_data(root,'reviewed',reviewer='last-page-reviewer',size=1)['total']==1

def test_query_and_review_share_lock_and_latest_revision(app):
    from concurrent.futures import ThreadPoolExecutor
    import time
    c,root,_=app
    body=payload(c,'a_landscape')
    with ThreadPoolExecutor() as pool:
        with storage.dataset_lock(root):
            future=pool.submit(c.put,'/api/v1/data/a_landscape',json=body)
            time.sleep(.1)
            assert not future.done()
        assert future.result().status_code==200
    assert c.put('/api/v1/data/a_landscape',json=body).status_code==409

def test_corrupt_approved_data_not_counted_as_trainable(app):
    c,root,_=app
    row=next(r for r in read_manifest(root) if r['image_id']=='a_landscape')
    (root/row['yolo_path']).write_text('0 4 4 1 1')
    overview=c.get('/api/v1/overview').json()
    available=c.get('/api/v1/data-query?view=approved').json()
    pending=c.get('/api/v1/data-query?view=pending_review&size=100').json()
    assert overview['data']['approved']==available['total']==5
    assert 'a_landscape' in {r['image_id'] for r in pending['items']}
    with pytest.raises(ValueError,match='audit failed'):build(root=root)

def test_checkpoint_marker_follows_real_save_event_without_training(tmp_path,monkeypatch):
    from src.workbench import adapters
    from src.workbench.contracts import Experiment
    from src import model_api
    monkeypatch.setattr(adapters,'ROOT',tmp_path)
    monkeypatch.setattr(adapters,'inside',lambda path:tmp_path/path)
    write_json(tmp_path/'configs/train.json',{'model':'yolo11n.pt'})
    output=tmp_path/'job';output.mkdir();write_json(output/'effective.json',{})
    events={}
    class FakeYOLO:
        def __init__(self,source):pass
        def add_callback(self,name,callback):events[name]=callback
        def train(self,**kwargs):
            best=output/'training/weights/best.pt';best.parent.mkdir(parents=True);best.write_bytes(b'fixture')
            for epoch,fitness in ((0,.6),(1,.5),(2,.6)):
                events['on_model_save'](SimpleNamespace(epoch=epoch,best_fitness=.6,fitness=fitness,best=best))
                selected=read_json(output/'checkpoint_selection.json')
                assert selected['epoch']==(1 if epoch<2 else 3)
    monkeypatch.setattr(model_api,'yolo_api',lambda:FakeYOLO)
    adapters.yolo_train(Experiment(model='yolo11n',dataset='fixture',device='cpu',epochs=3),{},output,tmp_path/'source.pt')
    selection=read_json(output/'checkpoint_selection.json')
    assert selection['epoch']==3 and selection['value']==.6 and 'on_model_save' in selection['rule']
