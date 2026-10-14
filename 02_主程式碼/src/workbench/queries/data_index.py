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
    files=[root/'data/manifest.csv',root/'data/snapshot_states.json',root/'data/image_sources.json']
    files+=sorted((root/'data/reviews').glob('*.json'))
    files+=sorted((root/'data/label_evidence').glob('*.json'))
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
            from src.workbench.views import annotate, audit_failures, review_histories
            def report_progress(done,total):set_state(root,{**previous,'state':'checking','processed':done,'total':total})
            failures=audit_failures(audit(root,on_progress=report_progress))
            rows=[]
            # Eligibility rules live in src.data.tasks; this projection never re-implements them.
            for item in annotate(raw,failures,review_histories(root),root):
                review=item['review'];t=item['tasks']
                rows.append((item['image_id'],item['status'],int(item['training_eligible']),int(bool(review and review['completed'])),(review or {}).get('reviewer'),(review or {}).get('decision'),(review or {}).get('at'),json.dumps(item,ensure_ascii=False),
                             int(t['binary_classification']['eligible']),int(t['stage_classification']['eligible']),int(t['detection']['eligible']),item.get('display_name'),
                             item['labels']['cls_state'],item['labels']['det_state']))
            # Source files are read outside the dataset lock. Publication uses a bounded
            # short lock and rejects a generation changed while validation was running.
            with dataset_lock(root):
                if signature(root,True)!=before:raise RuntimeError('來源於檢查期間變更，請重新檢查')
                now=time.time()
                value={'state':'ready','checked_at':now,'revision':digest(raw),'signature':signature(root),'files_signature':before,'errors':len(failures)}
                with connection(root) as con:
                    con.execute('DELETE FROM data_index')
                    con.executemany('INSERT INTO data_index(id,status,eligible,reviewed,reviewer,decision,review_at,payload,eligible_binary,eligible_stage,eligible_detection,display_name,cls_state,det_state) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',rows)
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

TASK_COLUMNS={'':'eligible','binary_classification':'eligible_binary','stage_classification':'eligible_stage','detection':'eligible_detection'}
# Stop-use records apply immediately, even before the projection is rebuilt.
NOT_REVOKED="id NOT IN (SELECT ident FROM usage_revocations WHERE kind='image') AND COALESCE(json_extract(payload,'$.sha256'),'') NOT IN (SELECT ident FROM usage_revocations WHERE kind='sha256')"

@timed('data_query')
def query(root,view='pending_review',reviewer='',decision='',start='',end='',page=1,size=30,*,task='',_overview=False):
    if view not in VIEWS or decision and decision not in DECISIONS:raise ValueError('無效的資料分類或決定')
    if task not in TASK_COLUMNS:raise ValueError('無效的任務')
    if page<1 or not 1<=size<=100:raise ValueError('無效的分頁')
    lo,hi=date_bounds(start,end);meta=freshness(root);valid=meta['state']=='ready'
    column=TASK_COLUMNS[task]
    with connection(root) as con:
        con.execute('BEGIN')
        current=con.execute("SELECT value FROM query_meta WHERE name='data'").fetchone()
        if current:
            published=json.loads(current[0]);valid=valid and published.get('state')=='ready'
            meta=published if valid else {**published,'state':meta['state'] if meta['state']!='ready' else published.get('state','pending')}
        usable=f"({column}=1 AND {NOT_REVOKED})"
        conditions={'all':'1','approved':f"status='approved' AND {usable}" if valid else '0' ,'reviewed':'reviewed=1','excluded':"status='excluded'",'pending_review':"status='pending_review' OR (status='approved' AND "+(f'NOT {usable}' if valid else '1')+')'}
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
            extra['approved_labels']={r[0]:r[1] for r in con.execute(f"SELECT json_extract(payload,'$.label_state'),COUNT(*) FROM data_index WHERE status='approved' AND eligible_binary=1 AND {NOT_REVOKED} GROUP BY 1")} if valid else {}
            extra['stage_labels']={r[0]:r[1] for r in con.execute(f"SELECT json_extract(payload,'$.labels.stage'),COUNT(*) FROM data_index WHERE eligible_stage=1 AND {NOT_REVOKED} GROUP BY 1")} if valid else {}
            extra['task_counts']={t:con.execute(f"SELECT COUNT(*) FROM data_index WHERE {c}=1 AND {NOT_REVOKED}").fetchone()[0] if valid else 0 for t,c in TASK_COLUMNS.items() if t}
            extra['verified_subjects']=con.execute("SELECT COUNT(DISTINCT json_extract(payload,'$.subject_id')) FROM data_index WHERE json_extract(payload,'$.group_verified')='true' AND json_extract(payload,'$.subject_id')!=''").fetchone()[0]
        revoked={r[0] for r in con.execute("SELECT ident FROM usage_revocations WHERE kind IN ('image','sha256')")}
    for item in items:
        if not valid or item['image_id'] in revoked or item.get('sha256') in revoked:
            item['training_eligible']=False
            for value in item.get('tasks',{}).values():
                if value['eligible']:value.update(eligible=False,reasons=value['reasons']+(['資料索引尚未完成檢查'] if not valid else ['研究授權已撤回或停止使用']))
    return {'items':items,'total':total,'counts':counts,'reviewers':reviewers,'page':page,'size':size,'view':view,'task':task,'index':meta,**extra}

AREA_VIEWS={'pending','confirmed','excluded','all'}
AREA_LABELS={'normal','stage1','stage2','positive_unstaged','unknown','boxes','no_target','not_annotated'}
SOURCES={'yida','import','other'}

@timed('data_area_query')
def area_query(root,area,view='pending',label='',source='',reviewer='',page=1,size=30):
    """One work area (det = YOLO, cls = other models). The two areas never share state."""
    if area not in ('cls','det') or view not in AREA_VIEWS:raise ValueError('無效的工作區或分類')
    if label and label not in AREA_LABELS or source and source not in SOURCES:raise ValueError('無效的篩選')
    if page<1 or not 1<=size<=100:raise ValueError('無效的分頁')
    meta=freshness(root);column='cls_state' if area=='cls' else 'det_state'
    label_expr="json_extract(payload,'$.labels.stage')" if area=='cls' else "json_extract(payload,'$.labels.detection')"
    source_expr="CASE WHEN display_name IS NOT NULL THEN 'yida' WHEN id LIKE 'import_%' OR id LIKE 'line_%' THEN 'import' ELSE 'other' END"
    with connection(root) as con:
        con.execute('BEGIN')
        current=con.execute("SELECT value FROM query_meta WHERE name='data'").fetchone()
        published=json.loads(current[0]) if current else {'state':'pending'}
        valid=meta['state']=='ready' and published.get('state')=='ready'
        if not valid:meta={**published,'state':meta['state'] if meta['state']!='ready' else published.get('state','pending')}
        clauses=[];params=[]
        if label:clauses.append(label_expr+'=?');params.append(label)
        if source:clauses.append(source_expr+'=?');params.append(source)
        if reviewer:clauses.append("COALESCE(reviewer,'__unknown__')=?");params.append(reviewer)
        base=' AND '.join(clauses) or '1'
        counts={v:con.execute(f'SELECT COUNT(*) FROM data_index WHERE {base}'+('' if v=='all' else f' AND {column}=?'),params+([] if v=='all' else [v])).fetchone()[0] for v in AREA_VIEWS}
        where=base+('' if view=='all' else f' AND {column}=?');values=params+([] if view=='all' else [view])
        total=con.execute('SELECT COUNT(*) FROM data_index WHERE '+where,values).fetchone()[0]
        items=[json.loads(r[0]) for r in con.execute('SELECT payload FROM data_index WHERE '+where+f' ORDER BY ({column}=\'pending\') DESC,display_name IS NULL,COALESCE(display_name,id) LIMIT ? OFFSET ?',values+[size,(page-1)*size])]
        labels={r[0]:r[1] for r in con.execute(f'SELECT {label_expr},COUNT(*) FROM data_index GROUP BY 1')}
        sources={r[0]:r[1] for r in con.execute(f'SELECT {source_expr},COUNT(*) FROM data_index GROUP BY 1')}
        reviewers=[r[0] for r in con.execute('SELECT DISTINCT reviewer FROM data_index WHERE reviewer IS NOT NULL ORDER BY reviewer')]
        revoked={r[0] for r in con.execute("SELECT ident FROM usage_revocations WHERE kind IN ('image','sha256')")}
    # Only this area's fields are returned; the other area's labels and boxes are never exposed here.
    keep=('binary','stage','stage_source','quality','usage') if area=='cls' else ('detection','detection_source','usage')
    tasks_keep=('binary_classification','stage_classification') if area=='cls' else ('detection',)
    out=[]
    for item in items:
        state=item['labels']['cls_state' if area=='cls' else 'det_state']
        task_state={k:dict(v) for k,v in item.get('tasks',{}).items() if k in tasks_keep}
        if not valid or item['image_id'] in revoked or item.get('sha256') in revoked:
            for value in task_state.values():
                if value['eligible']:value.update(eligible=False,reasons=value['reasons']+(['資料索引尚未完成檢查'] if not valid else ['研究授權已撤回或停止使用']))
        out.append({'image_id':item['image_id'],'sha256':item.get('sha256'),'revision':item['revision'],'display_name':item.get('display_name'),'display_conflict':item.get('display_conflict'),
                    'source':'yida' if item.get('display_name') else 'import' if item['image_id'].startswith(('import_','line_')) else 'other',
                    'state':state,'labels':{k:item['labels'][k] for k in keep},'tasks':task_state,'review':item.get('review'),
                    'stage_suggestion':item.get('stage_suggestion') if area=='cls' else None,'name_variants':item.get('name_variants',[])})
    done=counts['confirmed'];total_all=counts['all']
    return {'area':area,'view':view,'items':out,'total':total,'counts':counts,'labels':labels,'sources':sources,'reviewers':reviewers,'page':page,'size':size,'index':meta,
            'progress':{'confirmed':done,'total':total_all,'excluded':counts['excluded'],'ratio':done/(total_all-counts['excluded']) if total_all-counts['excluded'] else None}}

def indexed_row(root, ident):
    with connection(root) as con:
        row=con.execute('SELECT payload FROM data_index WHERE id=?',(ident,)).fetchone()
    return json.loads(row[0]) if row else None

def overview(root):
    result=query(root,size=1,_overview=True)
    areas={}
    for area in ('det','cls'):
        value=area_query(root,area,'all',size=1)
        areas[area]={'counts':value['counts'],'progress':value['progress'],'labels':value['labels']}
    return {'areas':areas,'data':result['counts'],'approved_labels':result['approved_labels'],'stage_labels':result['stage_labels'],'task_counts':result['task_counts'],'verified_subjects':result['verified_subjects'],'index':result['index']}

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
