"""History artifacts (legacy runs), hidden deleted models, cross-page selection and operation records."""
import json
import time
from src.common import write_json
from src.workbench import jobs, resources
from test_trash import app, wait, preview, commit, do, terminal_job  # noqa: F401  (fixture reuse)

LEGACY='demo_baseline_20260925T021038748271Z'


def legacy_run(root, name=LEGACY):
    folder=root/'runs'/name;(folder/'weights').mkdir(parents=True)
    (folder/'results.csv').write_text('epoch,metrics/mAP50(B)\n1,0.1\n',encoding='utf-8')
    (folder/'weights/best.pt').write_bytes(b'w'*64)
    return folder


def test_legacy_run_ids_are_validated(app):
    c,root,_=app
    for bad in ('workbench','../x','demo_baseline_x','evaluation_20260925T0/../../a'):
        p=preview(c,'move',[{'type':'legacy_run','id':bad}])
        assert p['blocked'], bad


def test_legacy_run_goes_through_trash_and_disappears_from_curves(app):
    c,root,_=app
    folder=legacy_run(root)
    from src.workbench.queries.legacy import rebuild
    rebuild(root)
    labels=[s['label'] for s in c.get('/api/v1/curve-sources').json()]
    assert LEGACY in labels
    moved=do(c,'move','legacy_run',LEGACY)
    assert moved['state']=='completed' and folder.exists(), 'moving to the trash keeps files'
    assert LEGACY not in [s['label'] for s in c.get('/api/v1/curve-sources').json()]
    listed=c.get('/api/v1/trash?type=legacy_run').json()
    assert [i['id'] for i in listed['items']]==[LEGACY]
    p=preview(c,'purge',[{'type':'legacy_run','id':LEGACY}]);assert not p['blocked'],p
    assert p['confirmation']=='永久刪除'
    r=commit(c,p);assert r.status_code==200,r.text
    done=wait(c,'/api/v1/trash/operations/'+r.json()['id'])
    assert done['state']=='completed',done
    assert not folder.exists(), 'empty folders are removed after verified file removal'
    assert resources.record('legacy_run',LEGACY)['state']=='purged'


def test_legacy_run_referenced_by_active_job_is_blocked(app):
    c,root,_=app
    legacy_run(root)
    ident=terminal_job(config={'model':'yolo11n','dataset':'runs/'+LEGACY+'/data.yaml'})
    with jobs.db() as con:con.execute("UPDATE jobs SET state='running' WHERE id=?",(ident,))
    p=preview(c,'move',[{'type':'legacy_run','id':LEGACY}])
    assert p['blocked'] and any(ident in b for i in p['items'] for b in i['blockers'])


def test_reports_and_curves_of_deleted_models_are_hidden(app):
    c,root,artifact=app
    job=terminal_job()
    with jobs.db() as con:
        con.execute("INSERT INTO resource_lifecycle(type,id,state,revision,moved,actor,summary,capacity,operation) VALUES('model',?,?,1,?,NULL,?,NULL,NULL)",
                    (artifact['id'],'purged',time.time(),json.dumps({'id':artifact['id'],'experiment':job})))
    assert job not in [s['id'] for s in c.get('/api/v1/curve-sources').json()]
    assert c.get('/api/v1/curve-history?source='+job).status_code>=400
    rid='9'*32;folder=root/'runs/workbench/evaluations'/rid;folder.mkdir(parents=True)
    write_json(folder/'report.json',{'model':'yolo11n','artifact':artifact['id'],'snapshot':'s','fold':0,'evaluated_at':'2026-10-14T00:00:00Z','metrics':{'member_hash':'x','complete':True},'samples':[]})
    reports=c.get('/api/v1/reports-query?size=100').json()
    assert rid not in [r['report_id'] for r in reports['items']]
    assert all(r.get('artifact')!=artifact['id'] for r in reports['items'])
    assert c.get('/api/v1/reports/'+rid+'/detail').status_code==404


def test_named_snapshot_moves_to_trash_and_is_no_longer_usable(app):
    c,root,_=app
    r=c.post('/api/v1/snapshots',json={'task':'detection','demo':True,'name':'  分期   測試 '});assert r.status_code==200,r.text
    version=r.json()['version'];assert r.json()['name']=='分期 測試'
    options={s['version']:s for s in c.get('/api/v1/snapshot-options').json()}
    assert options[version]['name']=='分期 測試'
    dataset=options[version]['folds'][0]['dataset']
    # A running job on the snapshot blocks removal.
    job=terminal_job(config={'model':'yolo11n','dataset':dataset})
    with jobs.db() as con:con.execute("UPDATE jobs SET state='running' WHERE id=?",(job,))
    assert preview(c,'move',[{'type':'snapshot','id':version}])['blocked']
    with jobs.db() as con:con.execute("UPDATE jobs SET state='succeeded' WHERE id=?",(job,))
    do(c,'move','snapshot',version)
    assert version not in [s['version'] for s in c.get('/api/v1/snapshot-options').json()]
    from src.data.dataset import validate_split
    import pytest
    with pytest.raises(ValueError,match='垃圾桶'):validate_split(root/dataset,root)
    item=next(i for i in c.get('/api/v1/trash?type=snapshot').json()['items'] if i['id']==version)
    assert item['summary']['name']=='分期 測試'
    do(c,'restore','snapshot',version)
    assert version in [s['version'] for s in c.get('/api/v1/snapshot-options').json()]
    do(c,'move','snapshot',version)
    p=preview(c,'purge',[{'type':'snapshot','id':version}]);assert not p['blocked'],p
    done=wait(c,'/api/v1/trash/operations/'+commit(c,p).json()['id'])
    assert done['state']=='completed' and not (root/'data/yolo'/version).exists()
    assert preview(c,'move',[{'type':'snapshot','id':'../manifest'}])['blocked']


def test_experiment_name_is_optional_display_label():
    from src.workbench.contracts import Experiment
    import pytest
    named=Experiment(model='efficientnet_b0',dataset='d',task='binary_classification',name='  EfficientNet   加權 ')
    assert named.name=='EfficientNet 加權' and named.model_dump()['name']=='EfficientNet 加權'
    assert 'name' not in Experiment(model='efficientnet_b0',dataset='d',task='binary_classification').model_dump(), 'old fingerprints unchanged'
    with pytest.raises(ValueError):Experiment(model='efficientnet_b0',dataset='d',name='x'*61)


def test_select_all_ids_follow_filters(app):
    c,root,_=app
    for _ in range(3):terminal_job(kind='predict')
    ids=c.get('/api/v1/jobs-query/ids?kind=predict').json()
    assert ids['total']==3==len(ids['ids'])
    audit=c.get('/api/v1/audit-query/ids').json()
    assert audit['total']==len(audit['ids'])>0 and audit['limit']==1000
    page=c.get('/api/v1/audit-query?size=1').json()
    assert page['total']==audit['total']


def test_preview_accepts_more_than_one_hundred_targets(app):
    c,root,_=app
    for i in range(105):jobs.audit('bulk_test',{'n':i})
    ids=c.get('/api/v1/audit-query/ids?action=bulk_test').json()['ids']
    assert len(ids)==105
    p=preview(c,'move',[{'type':'audit','id':i} for i in ids])
    assert len(p['items'])==105 and not p['blocked']
    too_many=c.post('/api/v1/trash/previews',json={'action':'move','targets':[{'type':'audit','id':str(i)} for i in range(1,1002)]})
    assert too_many.status_code in (400,422)


def test_operation_records_filter_and_delete(app):
    c,root,_=app
    job=terminal_job()
    moved=do(c,'move','job',job)
    jobs.audit('marker',{})
    audit_id=c.get('/api/v1/audit-query/ids?action=marker').json()['ids'][0]
    do(c,'move','audit',audit_id)
    by_type=c.get('/api/v1/trash/operation-history?type=job').json()
    assert [o['id'] for o in by_type['items']]==[moved['id']] and by_type['items'][0]['types']==['job']
    assert c.get('/api/v1/trash/operation-history?action=purge').json()['total']==0
    assert c.get('/api/v1/trash/operation-history?type=bogus').status_code==400
    ids=c.get('/api/v1/trash/operation-history/ids').json()['ids']
    assert len(ids)==2
    # A failed operation keeps its record for recovery.
    with jobs.db() as con:con.execute("UPDATE trash_operations SET state='needs_check' WHERE id=?",(ids[1],))
    check=c.post('/api/v1/trash/operation-history/delete',json={'ids':ids}).json()
    assert check['state']=='preview' and check['deletable']==1 and check['blocked'][0]['id']==ids[1]
    assert c.post('/api/v1/trash/operation-history/delete',json={'ids':ids,'confirmation':'錯誤'}).json()['state']=='preview'
    done=c.post('/api/v1/trash/operation-history/delete',json={'ids':ids,'confirmation':'永久刪除操作紀錄'}).json()
    assert done['deleted']==1
    remaining=c.get('/api/v1/trash/operation-history').json()
    assert [o['id'] for o in remaining['items']]==[ids[1]]
    # Trash items keep working without their (deleted) operation record.
    trashed={i['id']:i for i in c.get('/api/v1/trash').json()['items']}
    deleted=ids[0]
    assert all(i.get('operation')!=deleted for i in trashed.values())
    assert c.get('/api/v1/audit-query/ids?action=trash_operation_records_deleted').json()['total']==1
