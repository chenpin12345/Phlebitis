import json
import threading
import time
import pytest
from fastapi.testclient import TestClient
from src.workbench.contracts import Experiment,InferenceConfig
from src.workbench.metrics import binary_metrics,aggregate
from src.workbench.api import create_app
from src.line_bot.messages import results
from src.line_bot.service import create_app as line_app
from test_line import FakePredictor,FakeLine,settings,post,event,until

def test_timeout_send_failure_keeps_single_compute_slot(tmp_path):
    class Slow(FakePredictor):
        active=0; maximum=0; completed=0
        def predict(self,raw):
            self.active+=1;self.maximum=max(self.maximum,self.active)
            try:time.sleep(.2);return super().predict(raw)
            finally:self.active-=1;self.completed+=1
    class Failing(FakeLine):
        async def send(self,*args):raise RuntimeError('send failed')
    p=Slow();s=settings(tmp_path);s.timeout=.01
    with TestClient(line_app(s,predictor=p,client=Failing())) as c:
        e2=event('two','222');e2['source']['userId']='another-user'
        post(c,[event(),e2]);until(lambda:p.completed==2)
    assert p.maximum==1

@pytest.mark.parametrize('state,text',[('quality_rejected','品質不足'),('needs_review','人工確認')])
def test_all_nonbinary_statuses_preserved(state,text):
    payload=results({'status':state,'boxes':[],'model_version':'test','elapsed_ms':1},'https://local/result')
    assert text in json.dumps(payload,ensure_ascii=False)
    assert '分析完成：未偵測' not in json.dumps(payload,ensure_ascii=False)

def test_classifier_positive_has_no_fake_boxes():
    record={'status':'suspected','task_type':'classification','boxes':None,'prediction_score':.8,'model_version':'x','elapsed_ms':1}
    assert '疑似陽性' in json.dumps(results(record,'/image'),ensure_ascii=False)
    with pytest.raises(ValueError):results({**record,'status':'unexpected'},'/image')

def test_metrics_denominators_and_missing_members():
    samples=[{'image_id':str(i),'truth':t,'prediction':p} for i,(t,p) in enumerate([(1,1),(1,0),(0,1),(0,0)])]
    m=binary_metrics(samples)
    assert m['accuracy']==m['sensitivity']==m['specificity']==m['precision']==m['f1']==m['balanced_accuracy']==.5
    assert m['tp']==m['tn']==m['fp']==m['fn']==1
    assert m['accuracy_display']=='50%（2/4）'
    assert binary_metrics([])['accuracy'] is None
    negative=binary_metrics([{'image_id':'a','truth':0,'prediction':0}])
    assert negative['precision'] is None and negative['balanced_accuracy'] is None
    partial=binary_metrics(samples,['0','1','2','3','missing'])
    assert not partial['complete'] and partial['missing_members']==['missing']

def test_refusal_coverage_separate_from_binary():
    m=binary_metrics([{'image_id':'a','truth':1,'prediction':1,'status':'quality_rejected'},{'image_id':'b','truth':0,'prediction':0,'status':'not_detected'}])
    assert m['accuracy']==1 and m['coverage']==.5 and m['rejected']==1

def test_model_specific_parameter_contracts():
    base={'model':'yolo11n','dataset':'fake'}
    with pytest.raises(ValueError):Experiment(**base,parameters={'optimizer':'auto','lr0':.01})
    with pytest.raises(ValueError):Experiment(**base,parameters={'class_weight':'balanced'})
    with pytest.raises(ValueError):Experiment(model='yolo26s',dataset='fake',parameters={'dfl':1.5})
    with pytest.raises(ValueError):Experiment(model='dinov2_small',dataset='fake',resume_job='a')
    e=Experiment(model='efficientnet_b0',dataset='fake')
    assert e.inference.imgsz==224 and 'letterbox224' in e.inference.preprocess
    with pytest.raises(ValueError):Experiment(**base,inference={'candidate_threshold':.9,'threshold':.5})

def test_admin_host_origin_and_csrf():
    with TestClient(create_app(testing=True)) as c:
        token=c.get('/api/v1/session').json()['csrf']
        assert c.post('/api/v1/experiments',json={}).status_code==403
        assert c.get('/api/v1/session',headers={'host':'evil.example'}).status_code==400
        assert c.get('/api/v1/session',headers={'origin':'https://evil.example'}).status_code==403
        assert c.post('/api/v1/experiments',headers={'x-csrf-token':token},json={}).status_code==422

def test_line_app_does_not_expose_admin(tmp_path):
    with TestClient(line_app(settings(tmp_path),predictor=FakePredictor(),client=FakeLine())) as c:
        for path in ('/api/v1/data','/api/v1/jobs','/api/v1/audit','/api/v1/session'):
            assert c.get(path).status_code==404

def test_oof_rejects_repeated_samples():
    r={'model':'x','config':{},'snapshot':'a','samples':[{'image_id':'i','group':'validation','truth':0,'prediction':0}],'train_groups':['training'],'metrics':{'accuracy':1}}
    with pytest.raises(ValueError,match='repeated'):aggregate([r,r])

def test_shared_store_controlled_clock_unsend(tmp_path):
    from src.line_bot.service import Store
    clock=[100.]
    s=Store(tmp_path/'sim.sqlite3',clock=lambda:clock[0])
    s.unsend('message')
    assert s.reserve('e','message','user')=='cancelled'
    clock[0]+=86401
    assert s.reserve('e','message','user')=='accepted'
    s.close()

def test_jobs_idempotency_and_invalid_state(tmp_path,monkeypatch):
    from src.workbench import jobs,storage
    monkeypatch.setattr(jobs,'JOBS',tmp_path/'jobs')
    monkeypatch.setattr(jobs,'db',lambda:storage.db(tmp_path/'db'))
    monkeypatch.setattr(jobs,'audit',lambda *a,**k:None)
    a=jobs.enqueue('prepare',{'model':'yolo11n'},'same')
    b=jobs.enqueue('prepare',{'model':'yolo11n'},'same')
    assert a['id']==b['id']
    with pytest.raises(ValueError):jobs.enqueue('prepare',{'model':'yolo11s'},'same')
    jobs.cancel(a['id'])
    with pytest.raises(ValueError):jobs.update(a['id'],'running')

def test_registry_atomic_switch_failure_preserves_reference(tmp_path,monkeypatch):
    from src.workbench import registry
    from src.common import write_json,read_json
    monkeypatch.setattr(registry,'ROOT',tmp_path)
    monkeypatch.setattr(registry,'REFS',tmp_path/'references')
    monkeypatch.setattr(registry,'get',lambda ident:{'artifact_hash':ident,'config':{}})
    monkeypatch.setattr(registry,'reports',lambda ident:[{'artifact_hash':ident,'config':{},'metrics':{'complete':True}}])
    monkeypatch.setattr(registry,'audit',lambda *a:None)
    registry.activate('old')
    before=read_json(tmp_path/'references/local.json')
    def fail(*args):raise OSError('injected before atomic replace')
    monkeypatch.setattr(registry,'write_json',fail)
    with pytest.raises(OSError):registry.activate('new')
    assert read_json(tmp_path/'references/local.json')==before

def test_classifier_preprocessing_full_image_and_normalization():
    from src.workbench.adapters import tensor_image
    from PIL import Image
    x=tensor_image(Image.new('RGB',(300,100),'red'))
    assert tuple(x.shape)==(3,224,224)
    # Letterboxing preserves the full width; red center and neutral padding differ.
    assert float(x[0,112,112])>2 and abs(float(x[0,0,112]))<.1
