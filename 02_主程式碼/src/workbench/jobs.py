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
from src.paths import CODE_ROOT
from src.workbench.storage import db, audit, file_lock, operator, digest
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

def hydrate(row):
    item=dict(row);item['config']=json.loads(item['config'])
    for name in ('progress','result','effective'):
        path=folder(item['id'])/(name+'.json')
        item[name]=read_json(path) if path.exists() else None
    return item

def listing(limit=200,include_trashed=False):
    clause='' if include_trashed else " WHERE NOT EXISTS (SELECT 1 FROM resource_lifecycle r WHERE r.type='job' AND r.id=jobs.id AND r.state!='active')"
    with db() as con:rows=con.execute('SELECT * FROM jobs'+clause+' ORDER BY created DESC,id DESC'+(' LIMIT ?' if limit is not None else ''),((limit,) if limit is not None else ())).fetchall()
    return [hydrate(row) for row in rows]

def summaries(page=1,size=30,kind=''):
    if page<1 or not 1<=size<=100:raise ValueError('無效的分頁')
    where="NOT EXISTS (SELECT 1 FROM resource_lifecycle r WHERE r.type='job' AND r.id=jobs.id AND r.state!='active')"
    values=[]
    if kind:where+=' AND kind=?';values.append(kind)
    with db() as con:
        total=con.execute('SELECT COUNT(*) FROM jobs WHERE '+where,values).fetchone()[0]
        rows=con.execute('SELECT id,kind,state,created,updated,error,config FROM jobs WHERE '+where+' ORDER BY created DESC,id DESC LIMIT ? OFFSET ?',values+[size,(page-1)*size]).fetchall()
    items=[]
    for row in rows:
        item=dict(row);cfg=json.loads(item['config']);item['config']={k:cfg[k] for k in ('model','artifact','dataset','epochs','name') if k in cfg};items.append(item)
    with db() as con:active_count=con.execute("SELECT COUNT(*) FROM jobs WHERE state IN ('queued','running','cancelling')").fetchone()[0]
    return {'items':items,'total':total,'page':page,'size':size,'active_count':active_count}

SELECT_ALL_LIMIT=1000

def summary_ids(kind=''):
    """Every id matching the list filter, for an explicit 'select all' across pages."""
    where="NOT EXISTS (SELECT 1 FROM resource_lifecycle r WHERE r.type='job' AND r.id=jobs.id AND r.state!='active')"
    values=[]
    if kind:where+=' AND kind=?';values.append(kind)
    with db() as con:
        total=con.execute('SELECT COUNT(*) FROM jobs WHERE '+where,values).fetchone()[0]
        ids=[r[0] for r in con.execute('SELECT id FROM jobs WHERE '+where+' ORDER BY created DESC,id DESC LIMIT ?',values+[SELECT_ALL_LIMIT])]
    return {'ids':ids,'total':total,'limit':SELECT_ALL_LIMIT}

def scheduling_rows():
    with db() as con:
        rows=con.execute("SELECT * FROM jobs WHERE state IN ('queued','running','cancelling') OR (kind='predict' AND state IN ('failed','interrupted','cancelled') AND NOT EXISTS (SELECT 1 FROM scheduler_reconciled r WHERE r.id=jobs.id AND r.updated=jobs.updated)) ORDER BY created DESC,id DESC").fetchall()
    return [hydrate(row) for row in rows]


@guarded
def enqueue(kind,config,idem=None):
    if kind not in {'train','evaluate','prepare','predict','regression'}: raise ValueError('Unsupported job kind')
    config=dict(config)
    if kind=='train':
        cfg=Experiment(**config)
        config=cfg.model_dump()
    if idem:
        with db() as con:
            gone=con.execute('SELECT * FROM deleted_job_keys WHERE idem=?',(idem,)).fetchone()
            existing=con.execute('SELECT id,kind,config FROM jobs WHERE idem=?',(idem,)).fetchone()
        if gone:
            check=dict(config)
            if gone['kind']!=kind or gone['fingerprint']!=digest(check):raise ValueError('Idempotency key already used for different work')
            raise ResourceUnavailable('job',gone['id'],'purged')
        if existing:
            old_config=json.loads(existing['config']);check=dict(old_config)
            if kind=='regression' and 'baseline_job' not in config:check.pop('baseline_job',None)
            if existing['kind']!=kind or check!=config:raise ValueError('Idempotency key already used for different work')
            return get(existing['id'])
    if kind=='train':
        if cfg.resume_job:
            require_active('job',cfg.resume_job)
            old=get(cfg.resume_job)
            if old['state'] not in {'cancelled','interrupted','failed'}: raise ValueError('Resume requires an interrupted job')
            old_cfg=Experiment(**old['config'])
            requested=cfg.model_dump(); original=old_cfg.model_dump()
            for key in ('resume_job','checkpoint_import'): requested.pop(key,None); original.pop(key,None)
            if requested!=original: raise ValueError('Resume locks the original snapshot and training parameters')
            source_folder=folder(cfg.resume_job)
            if cfg.checkpoint_import:
                from src.imports.service import resolve_package
                source_folder,package=resolve_package(ROOT,cfg.checkpoint_import,'checkpoint',cfg.model)
                if package['source']['id']!=cfg.resume_job:raise ValueError('Checkpoint 原工作不相符')
            checkpoint=source_folder/('training/weights/last.pt' if cfg.model.startswith('yolo') else 'last.pt')
            if not checkpoint.is_file(): raise ValueError('No complete checkpoint; start a new experiment')
        if cfg.base_import:
            from src.imports.service import resolve_package
            resolve_package(ROOT,cfg.base_import,'base',cfg.model)
    for field in ('artifact','initial_artifact'):
        if config.get(field):
            require_active('model',config[field])
            from src.workbench.registry import get as get_model
            if get_model(config[field],verify=False).get('extra',{}).get('purpose')=='checkpoint':raise ValueError('Checkpoint 只能用於明確續訓')
    request_fingerprint=digest(config)
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
        write_json(path/'request.json',{'id':ident,'kind':kind,'config':config,'actor':operator.get(),'request_fingerprint':request_fingerprint})
        now=time.time()
        con.execute('INSERT INTO jobs(id,idem,kind,state,config,created,updated,pid,born,error) VALUES(?,?,?,?,?,?,?,?,?,?)',(ident,idem,kind,'queued',json.dumps(config),now,now,None,None,None))
    audit('enqueue',{'job':ident,'kind':kind,'config':config})
    return get(ident)

@guarded
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

@guarded
def cancel(ident):
    require_active('job',ident)
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
            try:
                from src.workbench.intake import run_cleanup
                run_cleanup()
            except Exception:pass  # Each task records its own retry reason; never block scheduling.
        jobs=scheduling_rows(); active=[]
        from src.workbench.simulation import reconcile
        reconcile(jobs)
        with db() as con:
            con.executemany("INSERT OR REPLACE INTO scheduler_reconciled(id,updated) VALUES(?,?)",[(j["id"],j["updated"]) for j in jobs if j["state"] in TERMINAL])
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
            # The worker imports `src`, which lives in the code folder (not the data root used for outputs).
            proc=subprocess.Popen([sys.executable,'-m','src.workbench.worker',item['id']],cwd=CODE_ROOT,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0,env={**os.environ,'PYTHONUTF8':'1','HF_HUB_DISABLE_TELEMETRY':'1','PYTHONPATH':str(CODE_ROOT)+os.pathsep+os.environ.get('PYTHONPATH','')})
            update(item['id'],'running',pid=proc.pid,born=psutil.Process(proc.pid).create_time())
        except Exception as exc: update(item['id'],'failed',str(exc))
        finally:log.close()
