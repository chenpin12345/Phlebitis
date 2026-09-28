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
from src.workbench.storage import db, audit, file_lock
from src.workbench.contracts import Experiment

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

def listing(limit=200):
    with db() as con: ids=[r[0] for r in con.execute('SELECT id FROM jobs ORDER BY created DESC'+(' LIMIT ?' if limit is not None else ''),((limit,) if limit is not None else ()))]
    return [get(i) for i in ids]

def enqueue(kind,config,idem=None):
    if kind not in {'train','evaluate','prepare','predict','regression'}: raise ValueError('Unsupported job kind')
    if kind=='train':
        cfg=Experiment(**config)
        if cfg.resume_job:
            old=get(cfg.resume_job)
            if old['state'] not in {'cancelled','interrupted','failed'}: raise ValueError('Resume requires an interrupted job')
            old_cfg=Experiment(**old['config'])
            requested=cfg.model_dump(); original=old_cfg.model_dump()
            for key in ('resume_job',): requested.pop(key); original.pop(key)
            if requested!=original: raise ValueError('Resume locks the original snapshot and training parameters')
            checkpoint=folder(cfg.resume_job)/('training/weights/last.pt' if cfg.model.startswith('yolo') else 'last.pt')
            if not checkpoint.is_file(): raise ValueError('No complete checkpoint; start a new experiment')
        config=cfg.model_dump()
    ident=uuid.uuid4().hex; idem=idem or ident
    with db() as con:
        con.execute('BEGIN IMMEDIATE')
        old=con.execute('SELECT id,kind,config FROM jobs WHERE idem=?',(idem,)).fetchone()
        if old:
            if old['kind']!=kind or json.loads(old['config'])!=config:raise ValueError('Idempotency key already used for different work')
            con.commit()
            return get(old['id'])
        path=folder(ident); path.mkdir(parents=True)
        write_json(path/'request.json',{'id':ident,'kind':kind,'config':config})
        now=time.time()
        con.execute('INSERT INTO jobs VALUES(?,?,?,?,?,?,?,?,?,?)',(ident,idem,kind,'queued',json.dumps(config),now,now,None,None,None))
    audit('enqueue',{'job':ident,'kind':kind,'config':config})
    return get(ident)

def update(ident,state,error=None,**process):
    with db() as con:
        row=con.execute('SELECT state FROM jobs WHERE id=?',(ident,)).fetchone()
        if not row: raise ValueError('Unknown job')
        allowed={'queued':{'running','cancelled','failed'},'running':{'running','cancelling','cancelled','failed','interrupted','succeeded'},'cancelling':{'cancelled','interrupted','failed'}}
        if state!=row[0] and state not in allowed.get(row[0],set()): raise ValueError(f'Invalid transition {row[0]} -> {state}')
        con.execute('UPDATE jobs SET state=?,updated=?,error=?,pid=COALESCE(?,pid),born=COALESCE(?,born) WHERE id=?',(state,time.time(),error,process.get('pid'),process.get('born'),ident))

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
        jobs=listing(limit=None); active=[]
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
