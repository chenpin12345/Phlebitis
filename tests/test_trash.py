"""Destructive tests run exclusively under tmp_path and never use real weights."""
import json
import os
import sqlite3
import time
import uuid
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from src.common import read_json, write_json
from src.workbench import trash, resources, managed_files, jobs, registry, storage
from workbench_fixture import configure


@pytest.fixture
def app(tmp_path,monkeypatch):
    application,artifact=configure(tmp_path,monkeypatch)
    with TestClient(application) as c:
        c.headers.update({'X-CSRF-Token':c.get('/api/v1/session').json()['csrf'],'X-Operator':'test-operator'})
        yield c,tmp_path,artifact


def wait(c,url,finished=lambda d:d['state'] not in ('calculating','preparing','running')):
    deadline=time.monotonic()+15
    while time.monotonic()<deadline:
        r=c.get(url);assert r.status_code==200,r.text
        data=r.json()
        if finished(data):return data
        time.sleep(.03)
    raise AssertionError('maintenance timed out')


def preview(c,action,targets):
    r=c.post('/api/v1/trash/previews',json={'action':action,'targets':targets});assert r.status_code==200,r.text
    return wait(c,'/api/v1/trash/previews/'+r.json()['id'])


def commit(c,p,key=None):
    return c.post('/api/v1/trash/operations',json={'preview_id':p['id'],'confirmation':p.get('confirmation','')},headers={'Idempotency-Key':key or uuid.uuid4().hex})


def do(c,action,kind,ident):
    p=preview(c,action,[{'type':kind,'id':str(ident)}]);assert not p['blocked'],p
    r=commit(c,p);assert r.status_code==200,r.text
    return wait(c,'/api/v1/trash/operations/'+r.json()['id'])


def terminal_job(kind='train',config=None):
    ident=uuid.uuid4().hex;config=config or {'model':'yolo11n'};root=jobs.folder(ident);root.mkdir(parents=True)
    write_json(root/'request.json',{'id':ident,'kind':kind,'config':config})
    (root/'worker.log').write_bytes(b'x'*123)
    with jobs.db() as con:
        con.execute('INSERT INTO jobs(id,idem,kind,state,config,created,updated) VALUES(?,?,?,?,?,?,?)',
                    (ident,ident,kind,'succeeded',json.dumps(config),time.time(),time.time()))
    return ident


def test_migration_reentrant_audit_ids_never_reused(tmp_path):
    path=tmp_path/'workbench.sqlite3'
    with sqlite3.connect(path) as con:
        con.execute('CREATE TABLE audit(id INTEGER PRIMARY KEY,at REAL,actor TEXT,action TEXT,detail TEXT)')
        con.execute("INSERT INTO audit VALUES(99,1,NULL,'legacy','{}')")
    with storage.db(tmp_path) as con:
        assert con.execute('SELECT id FROM audit').fetchone()[0]==99
        con.execute('DELETE FROM audit WHERE id=99')
    with storage.db(tmp_path) as con:
        con.execute("INSERT INTO audit(at,actor,action,detail) VALUES(2,NULL,'new','{}')")
        assert con.execute('SELECT id FROM audit').fetchone()[0]==100
        assert con.execute('PRAGMA user_version').fetchone()[0]==1
    assert (tmp_path/'backups/before-trash-v1.sqlite3').exists()


def test_job_move_restore_and_internal_query(app):
    c,root,_=app;ident=terminal_job()
    state=jobs.get(ident)['state'];original=(jobs.folder(ident)/'worker.log').read_bytes()
    assert do(c,'move','job',ident)['state']=='completed'
    assert ident not in {j['id'] for j in c.get('/api/v1/jobs').json()}
    assert ident in {j['id'] for j in jobs.listing(include_trashed=True)}
    assert (jobs.folder(ident)/'worker.log').read_bytes()==original
    with pytest.raises(resources.ResourceUnavailable):resources.require_active('job',ident)
    assert do(c,'restore','job',ident)['state']=='completed'
    assert jobs.get(ident)['state']==state
    assert resources.record('job',ident)['state']=='active'
    assert preview(c,'restore',[{'type':'job','id':ident}])['blocked']


def test_audit_batch_visibility_identity_and_sqlite_capacity(app):
    c,root,_=app
    ids=[str(x['id']) for x in c.get('/api/v1/audit-query?size=2').json()['items']]
    targets=[{'type':'audit','id':i} for i in ids]
    before={i:dict(next(r for r in c.get('/api/v1/audit').json() if str(r['id'])==i)) for i in ids}
    p=preview(c,'move',targets);assert not p['blocked'];op=commit(c,p).json()
    assert op['state']=='completed'
    assert not set(ids)&{str(r['id']) for r in c.get('/api/v1/audit-query?size=100').json()['items']}
    listing=c.get('/api/v1/trash?type=audit&size=1').json();assert listing['total']==2 and len(listing['items'])==1
    cap=listing['items'][0]['capacity'];assert cap['database_content_estimate_bytes']>0 and cap['database_immediate_release_bytes'] is None
    for ident in ids:do(c,'restore','audit',ident)
    restored={str(r['id']):r for r in c.get('/api/v1/audit').json()}
    for ident in ids:assert restored[ident]==before[ident]


def test_audit_purge_keeps_new_management_event(app):
    c,_,_=app;ident=str(c.get('/api/v1/audit').json()[0]['id'])
    do(c,'move','audit',ident);r=do(c,'purge','audit',ident)
    assert r['state']=='completed' and r['removed_files']==0 and r['disk_reclaimed_bytes'] is None
    assert resources.record('audit',ident)['state']=='purged'
    events=c.get('/api/v1/audit').json()
    assert all(str(e['id'])!=ident for e in events)
    assert any(e['action']=='trash_purge_completed' for e in events)
    assert max(e['id'] for e in events)>int(ident)


@pytest.mark.skipif(os.name!='nt',reason='Windows handle deletion verified on Windows')
def test_model_purge_windows_handles_report_kept(app):
    c,root,a=app;ident=a['id']
    report_id=uuid.uuid4().hex;report=root/'runs/workbench/evaluations'/report_id/'report.json'
    write_json(report,{'artifact':ident,'model':'yolo11n','snapshot':'fixed','fold':0,'config':a['config'],'metrics':{'complete':True},'samples':[]})
    before=report.read_bytes();do(c,'move','model',ident)
    assert ident not in {r['id'] for r in c.get('/api/v1/artifacts').json()}
    assert c.post('/api/v1/artifacts/activate',json={'artifact':ident,'target':'local','allow_unevaluated':True}).status_code==409
    p=preview(c,'purge',[{'type':'model','id':ident}]);assert not p['blocked'],p
    expected=p['capacity']['estimated_release_bytes'];key=uuid.uuid4().hex;r=commit(c,p,key);assert r.status_code==200,r.text
    result=wait(c,'/api/v1/trash/operations/'+r.json()['id']);assert result['state']=='completed',result
    assert result['removed_logical_bytes']==expected
    assert not (registry.artifact_path(ident)/'best.pt').exists()
    assert report.read_bytes()==before
    assert c.get('/api/v1/reports').json()[0]['source_model_state']=='purged'
    with pytest.raises(resources.ResourceUnavailable):registry.get(ident)
    assert commit(c,p,key).json()['id']==r.json()['id']
    assert preview(c,'restore',[{'type':'model','id':ident}])['blocked']


@pytest.mark.skipif(os.name!='nt',reason='Windows handle deletion')
def test_job_purge_idempotency_and_retained_request(app):
    c,root,a=app;ident=terminal_job('evaluate',{'artifact':a['id'],'dataset':'fixture'})
    do(c,'move','job',ident);op=do(c,'purge','job',ident)
    assert op['state']=='completed',op
    assert op['removed_logical_bytes']==123
    assert (jobs.folder(ident)/'request.json').exists()
    assert c.get('/api/v1/jobs/'+ident).status_code==410
    with pytest.raises(resources.ResourceUnavailable):jobs.enqueue('evaluate',{'artifact':a['id'],'dataset':'fixture'},ident)
    with jobs.db() as con:assert con.execute('SELECT COUNT(*) FROM jobs WHERE idem=?',(ident,)).fetchone()[0]==0


def test_active_job_and_model_dependency_block_move(app):
    c,_,a=app;active=jobs.enqueue('evaluate',{'artifact':a['id'],'dataset':'x'})
    for kind,ident in [('job',active['id']),('model',a['id'])]:
        p=preview(c,'move',[{'type':kind,'id':ident}]);assert p['blocked']
        assert commit(c,p).status_code==400


def test_reference_chain_explicit_release(app):
    c,_,a=app;current='unrelated';path=registry.REFS/'local.json'
    write_json(path,{'artifact':current,'previous':{'artifact':a['id'],'previous':{'artifact':a['id'],'previous':None}}})
    p=preview(c,'move',[{'type':'model','id':a['id']}]);assert p['blocked']
    chain=c.get('/api/v1/references').json()[0]
    assert c.post('/api/v1/references/local/preview',json={'revision':chain['revision'],'indices':[0]}).status_code==400
    p=c.post('/api/v1/references/local/preview',json={'revision':chain['revision'],'indices':[1]}).json()
    assert c.post('/api/v1/references/commit',json={'preview_id':p['id'],'confirmation':'解除回復引用'}).status_code==200
    assert read_json(path)['artifact']==current
    assert read_json(path)['previous']['artifact']==a['id']
    assert preview(c,'move',[{'type':'model','id':a['id']}])['blocked']
    assert c.post('/api/v1/references/commit',json={'preview_id':p['id'],'confirmation':'解除回復引用'}).status_code==400


def test_new_reference_file_change_and_expired_preview_rejected(app):
    c,_,a=app;ident=a['id']
    p=preview(c,'move',[{'type':'model','id':ident}]);assert not p['blocked']
    write_json(registry.REFS/'line.json',{'artifact':ident,'previous':None})
    assert commit(c,p).status_code==400
    ident=terminal_job();p=preview(c,'move',[{'type':'job','id':ident}]);(jobs.folder(ident)/'worker.log').write_bytes(b'changed')
    assert commit(c,p).status_code==400
    p=preview(c,'move',[{'type':'job','id':ident}])
    with jobs.db() as con:con.execute('UPDATE trash_previews SET expires=0 WHERE id=?',(p['id'],))
    assert commit(c,p).status_code==400


def test_nontrash_purge_csrf_confirmation_and_request_scope(app):
    c,_,a=app;target={'type':'model','id':a['id']}
    assert preview(c,'purge',[target])['blocked']
    assert c.post('/api/v1/trash/previews',json={'action':'move','targets':[target],'path':'C:/'}).status_code==422
    assert c.post('/api/v1/trash/previews',json={'action':'move','targets':[target]},headers={'X-CSRF-Token':'wrong'}).status_code==403
    do(c,'move','model',a['id']);p=preview(c,'purge',[target])
    assert c.post('/api/v1/trash/operations',json={'preview_id':p['id'],'confirmation':''},headers={'Idempotency-Key':'missing-confirm'}).status_code==400
    assert (registry.artifact_path(a['id'])/'best.pt').exists()


def test_unknown_capacity_missing_files_and_hardlink_protection(app):
    c,root,a=app;do(c,'move','model',a['id'])
    weight=registry.artifact_path(a['id'])/'best.pt';link=root/'external-hardlink'
    os.link(weight,link)
    p=preview(c,'purge',[{'type':'model','id':a['id']}]);assert p['blocked'] and p['items'][0]['capacity']['file_bytes'] is None
    link.unlink();weight.unlink()
    p=preview(c,'restore',[{'type':'model','id':a['id']}]);assert p['blocked']
    assert p['items'][0]['capacity']['file_bytes'] is None


def test_safe_file_identity_and_boundary(app):
    _,root,_=app;managed=root/'safe';managed.mkdir();file=managed/'test.bin';file.write_bytes(b'abc')
    fp=managed_files.inspect(file,managed);assert fp['bytes']==3
    with pytest.raises(ValueError):managed_files.inspect(root/'configs/service.json',managed)
    file.write_bytes(b'changed')
    if os.name=='nt':
        with pytest.raises(ValueError):managed_files.remove_verified(file,managed,fp,lambda:None)
    assert file.read_bytes()==b'changed'


def test_sensitive_system_file_excluded_from_plan(app):
    c,_,a=app;do(c,'move','model',a['id'])
    (registry.artifact_path(a['id'])/'.env').write_text('SECRET=fake-only')
    p=preview(c,'purge',[{'type':'model','id':a['id']}]);assert p['blocked']
    assert 'fake-only' not in json.dumps(p)
    assert '.env' not in {f['path'] for f in p['items'][0]['files']}


@pytest.mark.skipif(os.name!='nt',reason='Windows deletion failure/retry')
def test_partial_failure_retry_and_recovery(app,monkeypatch):
    c,_,_=app;ident=terminal_job();do(c,'move','job',ident)
    original=managed_files.remove_verified
    monkeypatch.setattr(managed_files,'remove_verified',lambda *args:(_ for _ in ()).throw(PermissionError('fixture locked file')))
    op=do(c,'purge','job',ident);assert op['state']=='partial_failed'
    assert resources.record('job',ident)['state']=='partial_failed'
    assert preview(c,'restore',[{'type':'job','id':ident}])['blocked']
    monkeypatch.setattr(managed_files,'remove_verified',original)
    assert c.post('/api/v1/trash/operations/'+op['id']+'/retry').status_code==200
    assert wait(c,'/api/v1/trash/operations/'+op['id'])['state']=='completed'


def test_baseline_selected_from_active_jobs_only(app):
    c,_,a=app;old=terminal_job('regression',{'artifact':a['id']});write_json(jobs.folder(old)/'regression.json',{'cases':[]})
    do(c,'move','job',old)
    new=jobs.enqueue('regression',{'artifact':a['id']},'stable-regression')
    assert new['config']['baseline_job'] is None
    assert jobs.enqueue('regression',{'artifact':a['id']},'stable-regression')['id']==new['id']


def test_report_query_preserves_repeat_evaluations_and_image_membership(app):
    c,root,a=app
    for n in range(3):
        ident=str(n+7)*32
        write_json(root/'runs/workbench/evaluations'/ident/'report.json',{'artifact':a['id'],'model':'yolo11n' if n<2 else 'dinov2_small','snapshot':'fixed','fold':0,'metrics':{'complete':True,'member_hash':'same'},'samples':[{'image_id':'sample','truth':1}],'evaluated_at':str(n)})
    result=c.get('/api/v1/reports-query?model=yolo11n&size=1').json()
    assert result['total']==2 and len(result['items'])==1
    assert c.get('/api/v1/reports-query?model=yolo11').json()['total']==0
    assert c.get('/api/v1/reports/'+'7'*32+'/images/not-a-member').status_code==400
    assert c.get('/api/v1/reports/'+'7'*32+'/images/sample').status_code==404
    assert c.post('/api/v1/reports/oof',json={}).status_code in (404,405)
