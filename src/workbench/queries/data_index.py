"""Versioned SQLite projection; full integrity work is never done by a list GET."""
import json
import threading
import time
from pathlib import Path
from src.common import read_manifest, read_json
from src.telemetry import timed
from src.workbench.storage import db, digest, dataset_lock, file_lock
from src.workbench.views import date_bounds, VIEWS, DECISIONS, timestamp

TTL = 86400
_workers = {}
_mutex = threading.Lock()

def connection(root):
    return db(Path(root)/'runtime/workbench')

def stat_key(path):
    try:
        s=path.stat();return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
    except FileNotFoundError:return None

@timed('stat_scan')
def signature(root, full=False):
    files=[root/'data/manifest.csv',root/'data/snapshot_states.json']
    files+=sorted((root/'data/reviews').glob('*.json'))
    if full:
        for row in read_manifest(root):
            from src.common import inside
            for key in ('image_path','annotation_path','yolo_path'):
                if row.get(key):files.append(inside(row[key],root))
    return digest([(str(p.relative_to(root)),stat_key(p)) for p in files])

def state(root):
    with connection(root) as con:
        row=con.execute("SELECT value FROM query_meta WHERE name='data'").fetchone()
    return json.loads(row[0]) if row else {'state':'pending','checked_at':None,'revision':None}

def set_state(root, value):
    with connection(root) as con:
        con.execute("INSERT OR REPLACE INTO query_meta(name,value) VALUES('data',?)",(json.dumps(value),))

def rebuild(root):
    root=Path(root)
    try:
        with file_lock(root/'runtime/data-index.lock'):
            previous=state(root)
            set_state(root,{**previous,'state':'checking','started_at':time.time(),'error':None})
            before=signature(root,True)
            raw=read_manifest(root)
            from src.data.dataset import audit
            def report_progress(done,total):set_state(root,{**previous,'state':'checking','processed':done,'total':total})
            failures={s.split(':',1)[0] for s in audit(root,on_progress=report_progress)['errors']}
            histories={}
            for path in sorted((root/'data/reviews').glob('*.json'),reverse=True):
                item=read_json(path);after=item.get('after',{})
                histories.setdefault(after.get('image_id'),[]).append(item)
            rows=[]
            for r in raw:
                review=None
                for item in histories.get(r['image_id'],[]):
                    after=item.get('after',{})
                    if digest(after)!=digest(r):continue
                    if after.get('reviewer')=='migration-audit':break
                    actor=after.get('reviewer','').strip()
                    actor=None if actor in ('','local_operator') else actor
                    decision=item.get('decision') or {'approved':'approve','excluded':'exclude','pending_review':'needs_changes'}.get(after.get('status'))
                    review={'decision':decision,'reviewer':actor,'at':timestamp(after.get('updated_at')),'reason':after.get('reason'),'revision':digest(item),'identity':'self_declared' if actor else 'unrecorded','completed':decision in ('approve','exclude'),'source':item.get('source','review_history')}
                    break
                eligible=r['status']=='approved' and r['image_id'] not in failures and (not review or review['decision']=='approve')
                item={**r,'revision':digest(r),'review':review,'training_eligible':eligible}
                rows.append((r['image_id'],r['status'],int(eligible),int(bool(review and review['completed'])),(review or {}).get('reviewer'),(review or {}).get('decision'),(review or {}).get('at'),json.dumps(item,ensure_ascii=False)))
            # Source files are read outside the dataset lock. Publication uses a bounded
            # short lock and rejects a generation changed while validation was running.
            with dataset_lock(root):
                if signature(root,True)!=before:raise RuntimeError('來源於檢查期間變更，請重新檢查')
                now=time.time()
                value={'state':'ready','checked_at':now,'revision':digest(raw),'signature':signature(root),'files_signature':before,'errors':len(failures)}
                with connection(root) as con:
                    con.execute('DELETE FROM data_index')
                    con.executemany('INSERT INTO data_index(id,status,eligible,reviewed,reviewer,decision,review_at,payload) VALUES(?,?,?,?,?,?,?,?)',rows)
                    con.execute("INSERT OR REPLACE INTO query_meta(name,value) VALUES('data',?)",(json.dumps(value),))
            return value
    except RuntimeError as exc:
        if '資源正在使用' in str(exc):return state(root)
        set_state(root,{**state(root),'state':'failed','retry_after':time.time()+30,'error':str(exc)});return state(root)
    except Exception as exc:
        set_state(root,{**state(root),'state':'failed','retry_after':time.time()+30,'error':type(exc).__name__+': '+str(exc)});return state(root)

def request_rebuild(root):
    root=Path(root)
    with _mutex:
        thread=_workers.get(str(root))
        if thread and thread.is_alive():return
        thread=threading.Thread(target=rebuild,args=(root,),daemon=True,name='dataset-index')
        _workers[str(root)]=thread;thread.start()

def invalidate(root):
    value=state(root);set_state(root,{**value,'state':'stale','retry_after':0})

def freshness(root):
    value=state(root)
    if value.get('retry_after',0)>time.time():return value
    if value.get('signature')!=signature(root) or time.time()-(value.get('checked_at') or 0)>TTL:
        value={**value,'state':'stale' if value.get('checked_at') else 'pending'}
        request_rebuild(root)
    return value

@timed('data_query')
def query(root,view='pending_review',reviewer='',decision='',start='',end='',page=1,size=30,*,_overview=False):
    if view not in VIEWS or decision and decision not in DECISIONS:raise ValueError('無效的資料分類或決定')
    if page<1 or not 1<=size<=100:raise ValueError('無效的分頁')
    lo,hi=date_bounds(start,end);meta=freshness(root);valid=meta['state']=='ready'
    with connection(root) as con:
        con.execute('BEGIN')
        current=con.execute("SELECT value FROM query_meta WHERE name='data'").fetchone()
        if current:
            published=json.loads(current[0]);valid=valid and published.get('state')=='ready'
            meta=published if valid else {**published,'state':meta['state'] if meta['state']!='ready' else published.get('state','pending')}
        conditions={'all':'1','approved':"status='approved' AND eligible=1" if valid else '0' ,'reviewed':'reviewed=1','excluded':"status='excluded'",'pending_review':"status='pending_review' OR (status='approved' AND "+('eligible=0' if valid else '1')+')'}
        clauses=['('+conditions[view]+')'];params=[]
        if reviewer:
            clauses.append("COALESCE(reviewer,'__unknown__')=?");params.append(reviewer)
        if decision:clauses.append('decision=?');params.append(decision)
        if lo is not None:clauses.append('review_at>=?');params.append(lo)
        if hi is not None:clauses.append('review_at<?');params.append(hi)
        where=' AND '.join(clauses)
        counts={v:con.execute('SELECT COUNT(*) FROM data_index WHERE '+q).fetchone()[0] for v,q in conditions.items()}
        total=con.execute('SELECT COUNT(*) FROM data_index WHERE '+where,params).fetchone()[0]
        items=[json.loads(r[0]) for r in con.execute('SELECT payload FROM data_index WHERE '+where+' ORDER BY id LIMIT ? OFFSET ?',params+[size,(page-1)*size])]
        reviewers=[r[0] for r in con.execute('SELECT DISTINCT reviewer FROM data_index WHERE reviewer IS NOT NULL ORDER BY reviewer')]
        extra={}
        if _overview:
            extra['approved_labels']={r[0]:r[1] for r in con.execute("SELECT json_extract(payload,'$.label_state'),COUNT(*) FROM data_index WHERE status='approved' AND eligible=1 GROUP BY 1")} if valid else {}
            extra['verified_subjects']=con.execute("SELECT COUNT(DISTINCT json_extract(payload,'$.subject_id')) FROM data_index WHERE json_extract(payload,'$.group_verified')='true' AND json_extract(payload,'$.subject_id')!=''").fetchone()[0]
    if not valid:
        for item in items:item['training_eligible']=False
    return {'items':items,'total':total,'counts':counts,'reviewers':reviewers,'page':page,'size':size,'view':view,'index':meta,**extra}

def overview(root):
    result=query(root,size=1,_overview=True)
    return {'data':result['counts'],'approved_labels':result['approved_labels'],'verified_subjects':result['verified_subjects'],'index':result['index']}

class Monitor:
    def __init__(self,root):self.root=Path(root);self.stop=threading.Event();self.thread=None
    def start(self):
        def run():
            while not self.stop.is_set():
                try:
                    from src.workbench.queries.legacy import rebuild as legacy_rebuild
                    legacy_rebuild(self.root)
                    value=state(self.root)
                    if value.get('files_signature')!=signature(self.root,True) or time.time()-(value.get('checked_at') or 0)>TTL:
                        invalidate(self.root);request_rebuild(self.root)
                except Exception:request_rebuild(self.root)
                self.stop.wait(30)
        self.thread=threading.Thread(target=run,daemon=True);self.thread.start()
    def close(self):
        self.stop.set()
        if self.thread:self.thread.join(2)
        worker=_workers.get(str(self.root))
        if worker:worker.join(15)
