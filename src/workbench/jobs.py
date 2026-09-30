from __future__ import annotations
import json
import os
import subprocess
import sys
import threading
import time
import uuid
import psutil
from src.common import ROOT, read_json, write_json
from src.workbench.storage import db, audit, file_lock, operator
from src.workbench.contracts import Experiment
from src.workbench.resources import guarded, require_active, states, ResourceUnavailable

JOBS=ROOT/'runs/workbench/jobs'
TERMINAL={'succeeded','failed','cancelled','interrupted'}

def folder(ident):
    if len(ident)!=32 or any(c not in '0123456789abcdef' for c in ident): raise ValueError('Invalid job ID')
    return JOBS/ident

def get(ident):
    with db() as con:
        row=con.execute('SELECT * FROM jobs WHERE id=?',(ident,)).fetchone()
    if not row: raise ValueError('Unknown job')
    item=dict(row); item['config']=json.loads(item['config'])
    for name in ('progress','result','effective'):
        path=folder(ident)/(name+'.json')
        item[name]=read_json(path) if path.exists() else None
    return item

def listing(limit=200,include_trashed=False):
    clause='' if include_trashed else " WHERE NOT EXISTS (SELECT 1 FROM resource_lifecycle r WHERE r.type='job' AND r.id=jobs.id AND r.state!='active')"
    with db() as con: ids=[r[0] for r in con.execute('SELECT id FROM jobs'+clause+' ORDER BY created DESC,id DESC'+(' LIMIT ?' if limit is not None else ''),((limit,) if limit is not None else ()))]
    return [get(i) for i in ids]

@guarded
def enqueue(kind,config,idem=None):
    if kind not in {'train','evaluate','prepare','predict','regression'}: raise ValueError('Unsupported job kind')
    config=dict(config)
    if kind=='train':
        cfg=Experiment(**config)
        if cfg.resume_job:
            require_active('job',cfg.resume_job)
            old=get(cfg.resume_job)
            if old['state'] not in {'cancelled','interrupted','failed'}: raise ValueError('Resume requires an interrupted job')
            old_cfg=Experiment(**old['config'])
            requested=cfg.model_dump(); original=old_cfg.model_dump()
            for key in ('resume_job',): requested.pop(key); original.pop(key)
            if requested!=original: raise ValueError('Resume locks the original snapshot and training parameters')
            checkpoint=folder(cfg.resume_job)/('training/weights/last.pt' if cfg.model.startswith('yolo') else 'last.pt')
            if not checkpoint.is_file(): raise ValueError('No complete checkpoint; start a new experiment')
        config=cfg.model_dump()
    if idem:
        with db() as con:
            gone=con.execute('SELECT * FROM deleted_job_keys WHERE idem=?',(idem,)).fetchone()
            existing=con.execute('SELECT id,kind,config FROM jobs WHERE idem=?',(idem,)).fetchone()
        if gone:
            from src.workbench.storage import digest
            check=dict(config)
            if kind=='regression':check.pop('baseline_job',None)
            if gone['kind']!=kind or gone['fingerprint']!=digest(check):raise ValueError('Idempotency key already used for different work')
            raise ResourceUnavailable('job',gone['id'],'purged')
        if existing:
            old_config=json.loads(existing['config']);check=dict(old_config)
            if kind=='regression' and 'baseline_job' not in config:check.pop('baseline_job',None)
            if existing['kind']!=kind or check!=config:raise ValueError('Idempotency key already used for different work')
            return get(existing['id'])
    for field in ('artifact','initial_artifact'):
        if config.get(field):require_active('model',config[field])
    if kind=='regression' and 'baseline_job' not in config:
        candidates=[j for j in listing(limit=None) if j['kind']=='regression' and j['state']=='succeeded' and (folder(j['id'])/'regression.json').is_file()]
        config['baseline_job']=candidates[0]['id'] if candidates else None
    if config.get('baseline_job'):require_active('job',config['baseline_job'])
    ident=uuid.uuid4().hex; idem=idem or ident
    with db() as con:
        con.execute('BEGIN IMMEDIATE')
        old=con.execute('SELECT id,kind,config FROM jobs WHERE idem=?',(idem,)).fetchone()
        if old:
            if old['kind']!=kind or json.loads(old['config'])!=config:raise ValueError('Idempotency key already used for different work')
            con.commit()
            return get(old['id'])
        path=folder(ident); path.mkdir(parents=True)
        write_json(path/'request.json',{'id':ident,'kind':kind,'config':config,'actor':operator.get()})
        now=time.time()
        con.execute('INSERT INTO jobs(id,idem,kind,state,config,created,updated,pid,born,error) VALUES(?,?,?,?,?,?,?,?,?,?)',(ident,idem,kind,'queued',json.dumps(config),now,now,None,None,None))
    audit('enqueue',{'job':ident,'kind':kind,'config':config})
    return get(ident)

def update(ident,state,error=None,**process):
    with db() as con:
        row=con.execute('SELECT state FROM jobs WHERE id=?',(ident,)).fetchone()
        if not row: raise ValueError('Unknown job')
        allowed={'queued':{'running','cancelled','failed'},'running':{'running','cancelling','cancelled','failed','interrupted','succeeded'},'cancelling':{'cancelled','interrupted','failed'}}
        if state!=row[0] and state not in allowed.get(row[0],set()): raise ValueError(f'Invalid transition {row[0]} -> {state}')
        con.execute('UPDATE jobs SET state=?,updated=?,error=?,pid=COALESCE(?,pid),born=COALESCE(?,born) WHERE id=?',(state,time.time(),error,process.get('pid'),process.get('born'),ident))
    if state!=row[0]:
        request=folder(ident)/'request.json'
        actor=read_json(request).get('actor') if request.exists() else None
        audit('job_'+state,{'job':ident,'from':row[0],'state':state,'error':error},actor=actor,outcome=state)

def cancel(ident):
    item=get(ident)
    if item['state']=='queued': update(ident,'cancelled')
    elif item['state']=='running':
        (folder(ident)/'cancel').touch(); update(ident,'cancelling')
    audit('cancel',{'job':ident})
    return get(ident)

def owned_process(item):
    if not item['pid'] or not item['born']: return None
    try:
        p=psutil.Process(item['pid'])
        if abs(p.create_time()-item['born'])>.05: return None
        cmd=p.cmdline()
        if 'src.workbench.worker' not in cmd or item['id'] not in cmd: return None
        return p
    except (psutil.NoSuchProcess,psutil.AccessDenied): return None

class Manager:
    def __init__(self): self.stop=threading.Event(); self.thread=None;self.last_cleanup=0
    def start(self):
        self.thread=threading.Thread(target=self.run,daemon=True); self.thread.start()
    def close(self):
        # Workers are independent and continue across a browser/server restart.
        self.stop.set()
        if self.thread: self.thread.join(3)
    def run(self):
        while not self.stop.is_set():
            try:
                with file_lock(ROOT/'runtime/workbench-scheduler.lock'):
                    while not self.stop.is_set():
                        try: self.tick()
                        except Exception as exc: audit('scheduler_error',{'type':type(exc).__name__,'message':str(exc)})
                        self.stop.wait(1)
            except RuntimeError:self.stop.wait(2)
    def tick(self):
        if time.time()-self.last_cleanup>30:
            from src.workbench.lifecycle import expire_temporary
            expire_temporary();self.last_cleanup=time.time()
        jobs=listing(limit=None,include_trashed=True); active=[]
        from src.workbench.simulation import reconcile
        reconcile(jobs)
        for item in jobs:
            if item['state'] not in {'running','cancelling'}: continue
            proc=owned_process(item)
            if not proc:
                if time.time()-item['updated']>10: update(item['id'],'interrupted','Worker missing; checkpoint may be resumed')
                else: active.append(item)
            elif item['state']=='cancelling' and time.time()-item['updated']>30:
                children=proc.children(recursive=True)
                for child in children:
                    try:child.terminate()
                    except psutil.NoSuchProcess:pass
                proc.terminate()
                try: proc.wait(10)
                except psutil.TimeoutExpired: proc.kill(); proc.wait(10)
                _,alive=psutil.wait_procs(children,timeout=3)
                for child in alive:
                    try:child.kill()
                    except psutil.NoSuchProcess:pass
                update(item['id'],'cancelled','Controlled termination after 30 seconds; only completed checkpoints are usable')
            else: active.append(item)
        if active: return
        queued=[j for j in reversed(jobs) if j['state']=='queued']
        if not queued:return
        from src.lock import OperationLock
        try:
            with OperationLock(): pass
        except RuntimeError:return  # LINE/CLI still owns compute. Never remove its lock.
        item=queued[0]; update(item['id'],'running')
        log=(folder(item['id'])/'worker.log').open('ab')
        try:
            proc=subprocess.Popen([sys.executable,'-m','src.workbench.worker',item['id']],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0,env={**os.environ,'PYTHONUTF8':'1','HF_HUB_DISABLE_TELEMETRY':'1'})
            update(item['id'],'running',pid=proc.pid,born=psutil.Process(proc.pid).create_time())
        except Exception as exc: update(item['id'],'failed',str(exc))
        finally:log.close()
