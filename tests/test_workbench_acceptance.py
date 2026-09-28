import json
import subprocess
import sys
import time
from types import SimpleNamespace

import numpy as np
import pytest


def test_machine_compute_lock_across_processes():
    from src.lock import OperationLock
    code="from src.lock import OperationLock\ntry:\n with OperationLock():print('acquired')\nexcept RuntimeError:print('blocked')"
    with OperationLock():
        result=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True,timeout=15)
        assert result.returncode==0 and result.stdout.strip()=='blocked'
    result=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True,timeout=15)
    assert result.returncode==0 and result.stdout.strip()=='acquired'


@pytest.fixture
def isolated_jobs(tmp_path,monkeypatch):
    from src.workbench import jobs,storage,lifecycle,simulation
    monkeypatch.setattr(jobs,'JOBS',tmp_path/'jobs')
    monkeypatch.setattr(jobs,'db',lambda:storage.db(tmp_path/'db'))
    monkeypatch.setattr(jobs,'audit',lambda *a,**k:None)
    monkeypatch.setattr(lifecycle,'expire_temporary',lambda:None)
    monkeypatch.setattr(simulation,'reconcile',lambda x:None)
    return jobs


def test_restarted_manager_recovers_missing_process(isolated_jobs):
    jobs=isolated_jobs
    job=jobs.enqueue('prepare',{'model':'yolo11n'})
    jobs.update(job['id'],'running',pid=999999,born=1)
    with jobs.db() as con:con.execute('UPDATE jobs SET updated=?',(time.time()-20,))
    jobs.Manager().tick()
    assert jobs.get(job['id'])['state']=='interrupted'


def test_pid_reuse_never_treated_as_worker(isolated_jobs,monkeypatch):
    jobs=isolated_jobs
    mock=SimpleNamespace(create_time=lambda:20,cmdline=lambda:['python','-m','src.workbench.worker','a'*32])
    monkeypatch.setattr(jobs.psutil,'Process',lambda pid:mock)
    assert jobs.owned_process({'pid':123,'born':10,'id':'a'*32}) is None
    assert jobs.owned_process({'pid':123,'born':20,'id':'b'*32}) is None
    assert jobs.owned_process({'pid':123,'born':20,'id':'a'*32}) is mock


def test_resume_locks_configuration(isolated_jobs):
    jobs=isolated_jobs
    job=jobs.enqueue('train',{'model':'efficientnet_b0','dataset':'snapshot','device':'cpu'})
    jobs.cancel(job['id']);(jobs.folder(job['id'])/'last.pt').write_bytes(b'fixture placeholder, not loaded')
    with pytest.raises(ValueError,match='locks'):
        jobs.enqueue('train',{**job['config'],'resume_job':job['id'],'epochs':3})


def test_frozen_efficient_backbone_keeps_bn_statistics():
    import torch
    from src.workbench.adapters import load_efficient,efficient_training_mode
    torch.set_num_threads(1)
    model=load_efficient()
    for p in model.features.parameters():p.requires_grad=False
    efficient_training_mode(model)
    before={n:b.clone() for n,b in model.features.named_buffers()}
    with torch.no_grad():model(torch.rand(2,3,224,224))
    assert all(torch.equal(before[n],b) for n,b in model.features.named_buffers())
    assert model.classifier.training and not model.features.training
    efficient_training_mode(model,'last_stage')
    assert model.features[-1].training and not model.features[0].training


def test_dino_scaler_uses_only_train_and_pipeline_reloads(tmp_path,monkeypatch):
    import torch,transformers
    from src.workbench import adapters
    from src.workbench.contracts import Experiment
    class Backbone:
        def to(self,*a):return self
        def eval(self):return self
        def parameters(self):return [torch.nn.Parameter(torch.zeros(1))]
    monkeypatch.setattr(transformers.Dinov2Model,'from_pretrained',lambda *a,**k:Backbone())
    train=[{'image_id':'a','label_state':'negative'},{'image_id':'b','label_state':'positive'}]
    def features(model,rows,*args):
        assert rows==train
        return np.array([[1.,2.],[3.,4.]])
    monkeypatch.setattr(adapters,'dino_features',features)
    base=tmp_path/'base';base.mkdir();(base/'model.safetensors').write_bytes(b'fixture')
    out=tmp_path/'job';out.mkdir()
    cfg=Experiment(model='dinov2_small',dataset='fixture',device='cpu')
    artifact,effective=adapters.dino_train(cfg,{'members':{'train':train,'val':[{'image_id':'never_fit','value':999}]}},out,base)
    saved=np.load(artifact/'classifier.npz',allow_pickle=False)
    assert saved['mean'].tolist()==[2.,3.] and saved['classes'].tolist()==[0,1]
    assert effective['train_only_scaler']
    scores=((np.array([[1.,2.],[3.,4.]])-saved['mean'])/saved['scale'])@saved['coef'].T+saved['intercept']
    assert scores[0,0]<0<scores[1,0]


def test_dino_cache_isolated_by_input_and_weight_version(tmp_path,monkeypatch):
    import torch
    from PIL import Image
    from src.workbench import adapters
    monkeypatch.setattr(adapters,'ROOT',tmp_path)
    monkeypatch.setattr(adapters,'inside',lambda value:__import__('pathlib').Path(value))
    image=tmp_path/'fixture.jpg';Image.new('RGB',(100,100),'red').save(image)
    row={'image_id':'fixture','dataset_sha256':'hash1','image_path':str(image)}
    count=[0]
    def model(**kwargs):
        count[0]+=1
        return SimpleNamespace(last_hidden_state=torch.ones((1,1,384)))
    job=tmp_path/'job';job.mkdir()
    for weight,content in [('w1','hash1'),('w1','hash1'),('w2','hash1'),('w2','hash2')]:
        adapters.dino_features(model,[{**row,'dataset_sha256':content}],'cpu',job,weight)
    assert count[0]==3


def test_conversation_regression_clock_and_tombstone(tmp_path):
    from src.workbench.simulation import replay_conversation,validate_expectations
    events=[{'type':'unsend','message_id':'m','at':1,'expected':'cancelled'},
            {'type':'reserve','event_id':'e','message_id':'m','at':2,'expected':'cancelled'},
            {'type':'reserve','event_id':'e2','message_id':'m','at':86402,'expected':'accepted'}]
    validate_expectations({'conversation':events,'score_range':[0,1],'max_latency_ms':50})
    assert all(r['pass'] for r in replay_conversation(events,tmp_path/'replay.sqlite3'))
    with pytest.raises(ValueError):validate_expectations({'score_range':[.8,.2]})


def test_line_drain_finishes_queue_before_releasing(tmp_path):
    from fastapi.testclient import TestClient
    from src.common import write_json
    from src.line_bot.service import create_app
    from test_line import FakePredictor,FakeLine,settings,post,event,until
    s=settings(tmp_path)
    class Slow(FakePredictor):
        def predict(self,raw):time.sleep(.15);return super().predict(raw)
    with TestClient(create_app(s,predictor=Slow(),client=FakeLine())) as c:
        post(c,[event()])
        write_json(s.runtime/'line-control.json',{'action':'drain'})
        until(lambda:c.app.state.predictor is None)
        assert not c.app.state.accepting
        assert c.app.state.queue.empty()
        assert c.get('/health').json()['status']=='draining_or_stopped'


def test_oof_rejects_training_protocol_change():
    from src.workbench.metrics import aggregate
    base={'model':'yolo11n','config':{},'snapshot':'fixed','samples':[],'train_groups':[],
          'metrics':{'accuracy':None,'complete':True},'training_protocol':{'seed':42}}
    with pytest.raises(ValueError,match='strategy/seed'):
        aggregate([base,{**base,'training_protocol':{'seed':43}}])


def test_config_clone_has_no_old_evaluation(tmp_path,monkeypatch):
    from src.workbench import registry
    monkeypatch.setattr(registry,'ROOT',tmp_path)
    monkeypatch.setattr(registry,'VERSIONS',tmp_path/'models/versions')
    monkeypatch.setattr(registry,'audit',lambda *a:None)
    source=tmp_path/'model.pt';source.write_bytes(b'fixture artifact, never loaded')
    old=registry.register(source,'efficientnet_b0',{'threshold':.5},'fixture')
    path=tmp_path/'runs/workbench/evaluations/old';path.mkdir(parents=True)
    (path/'report.json').write_text(json.dumps({'artifact':old['id'],'metrics':{'accuracy':1}}))
    new=registry.register(registry.artifact_path(old['id']),'efficientnet_b0',{'threshold':.8},'fixture')
    assert old['id']!=new['id'] and old['artifact_hash']==new['artifact_hash']
    assert registry.reports(old['id']) and registry.reports(new['id'])==[]


def test_invalid_compare_batch_never_partially_enqueues(monkeypatch):
    from fastapi.testclient import TestClient
    from src.workbench import api,jobs
    calls=[];monkeypatch.setattr(jobs,'enqueue',lambda *a,**k:calls.append(a))
    with TestClient(api.create_app(testing=True)) as c:
        headers={'x-csrf-token':c.get('/api/v1/session').json()['csrf']}
        result=c.post('/api/v1/experiments/batch',headers=headers,json=[
            {'model':'yolo11n','dataset':'same'},
            {'model':'yolo26s','dataset':'same','parameters':{'dfl':1.5}}])
    assert result.status_code==422 and not calls


def test_yolo_resume_writes_new_directory(tmp_path,monkeypatch):
    from pathlib import Path
    from src.workbench import adapters
    from src import model_api
    from src.common import write_json
    from src.workbench.contracts import Experiment
    monkeypatch.setattr(adapters,'ROOT',tmp_path)
    monkeypatch.setattr(adapters,'inside',lambda value:tmp_path/value)
    old=tmp_path/'runs/workbench/jobs/old/training/weights';old.mkdir(parents=True)
    (old/'best.pt').write_bytes(b'original immutable checkpoint')
    (old/'last.pt').write_bytes(b'interrupted checkpoint')
    write_json(tmp_path/'configs/train.json',{'model':'yolo11n.pt'})
    output=tmp_path/'new';output.mkdir();write_json(output/'effective.json',{})
    calls=[]
    class FakeYOLO:
        def __init__(self,source):assert source==str(old/'last.pt')
        def add_callback(self,*a):pass
        def train(self,**kwargs):
            calls.append(kwargs)
            (Path(kwargs['save_dir'])/'weights/best.pt').write_bytes(b'new best checkpoint')
    monkeypatch.setattr(model_api,'yolo_api',lambda:FakeYOLO)
    cfg=Experiment(model='yolo11n',dataset='fixture',device='cpu',resume_job='old')
    artifact,_=adapters.yolo_train(cfg,{},output,tmp_path/'pretrained.pt')
    assert calls[0]['save_dir']==str(output/'training') and calls[0]['resume']
    assert (old/'best.pt').read_bytes()==b'original immutable checkpoint'
    assert (artifact/'best.pt').read_bytes()==b'new best checkpoint'
