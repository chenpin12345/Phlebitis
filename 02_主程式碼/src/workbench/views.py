"""Read models for the workbench. Existing manifest and immutable snapshots remain authoritative."""
from __future__ import annotations
import json
import math
from datetime import datetime, timezone, timedelta
from pathlib import Path
from src.common import ROOT, read_json, read_manifest
from src.workbench.storage import digest

VIEWS = {'pending_review', 'reviewed', 'approved', 'excluded', 'all'}
DECISIONS = {'approve': 'approved', 'exclude': 'excluded', 'needs_changes': 'pending_review', 'reopen': 'pending_review'}

def timestamp(value):
    if not value: return None
    try:
        if isinstance(value, (int, float)): return float(value)
        if 'T' in value and '-' not in value:
            return datetime.strptime(value, '%Y%m%dT%H%M%S%fZ').replace(tzinfo=timezone.utc).timestamp()
        return datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()
    except (ValueError, TypeError): return None

def date_bounds(start='', end=''):
    """UI calendar dates are Asia/Taipei; end date includes the whole local day."""
    tz = timezone(timedelta(hours=8))
    try:
        lo = datetime.strptime(start, '%Y-%m-%d').replace(tzinfo=tz).timestamp() if start else None
        hi = (datetime.strptime(end, '%Y-%m-%d').replace(tzinfo=tz) + timedelta(days=1)).timestamp() if end else None
    except ValueError: raise ValueError('日期格式必須為 YYYY-MM-DD')
    if lo is not None and hi is not None and lo >= hi: raise ValueError('日期範圍無效')
    return lo, hi

def match_review(row, items):
    """Latest review whose recorded 'after' row equals the current row (newest first)."""
    from src.data.tasks import row_revision
    current = row_revision(row)
    for item in items:
        after = item.get('after', {})
        if row_revision(after) != current: continue
        # Technical migration records are history, not human decisions.
        if after.get('reviewer') == 'migration-audit': return None
        actor = after.get('reviewer', '').strip()
        if actor in ('', 'local_operator'): actor = None
        decision = item.get('decision') or {'approved':'approve', 'excluded':'exclude', 'pending_review':'needs_changes'}.get(after.get('status'))
        return {'decision':decision, 'reviewer':actor, 'at':timestamp(after.get('updated_at')), 'reason':after.get('reason'),
                'revision':digest(item), 'identity':'self_declared' if actor else 'unrecorded', 'task':item.get('task'),
                'completed':decision in ('approve','exclude'), 'source':item.get('source','review_history')}
    return None

def review_histories(root=ROOT):
    histories={}
    for path in sorted((root/'data/reviews').glob('*.json'),reverse=True):
        item=read_json(path)
        histories.setdefault(item.get('after',{}).get('image_id'),[]).append(item)
    return histories

def current_review(row, root=ROOT):
    items=[read_json(p) for p in sorted((root/'data/reviews').glob('*_'+row['image_id']+'.json'), reverse=True)]
    return match_review(row, items)

def annotate(raw, failures, histories, root=ROOT):
    """Shared row projection used by the query index, snapshots and tests."""
    from src.data import tasks, sources, evidence, revocations
    table=revocations.revoked(root); names=sources.load(root); variants=sources.variants(raw,names)
    rows=[]
    for r in raw:
        review=match_review(r,histories.get(r['image_id'],[]))
        task_state=tasks.eligibility(r,audit_error=failures.get(r['image_id']),review=review,revoked=revocations.is_revoked(r,table))
        rows.append({**r,'revision':tasks.row_revision(r),'review':review,'tasks':task_state,'labels':tasks.effective(r),
                     'training_eligible':any(v['eligible'] for v in task_state.values()),
                     'stage_suggestion':evidence.suggestion(r['image_id'],r,root),'name_variants':variants.get(r['image_id'],[]),**sources.lookup(r['image_id'],names)})
    return rows

def audit_failures(report):
    failures={}
    for item in report['errors']:
        ident,_,message=item.partition(':');failures.setdefault(ident,message.strip())
    return failures

def data_rows(root=ROOT):
    from src.data.dataset import audit
    # Reuse exactly the integrity/annotation checks applied when building snapshots.
    return annotate(read_manifest(root),audit_failures(audit(root)),review_histories(root),root)

def task_ok(row, task=''):
    if task: return row['tasks'][task]['eligible']
    return row['training_eligible']

def in_view(row, view, task=''):
    if view=='all': return True
    if view=='reviewed': return bool(row['review'] and row['review']['completed'])
    if view=='approved': return task_ok(row,task)
    if view=='pending_review': return row['status']=='pending_review' or (row['status']=='approved' and not task_ok(row,task))
    return row['status']==view

def query_data(root=ROOT, view='pending_review', reviewer='', decision='', start='', end='', page=1, size=30, task=''):
    from src.data.tasks import TASKS
    if task and task not in TASKS: raise ValueError('無效的任務')
    if view not in VIEWS: raise ValueError('無效的資料分類')
    if decision and decision not in DECISIONS: raise ValueError('無效的審查決定')
    if page<1 or not 1<=size<=100: raise ValueError('無效的分頁')
    lo, hi=date_bounds(start,end)
    rows=data_rows(root)
    counts={v:sum(in_view(r,v,task) for r in rows) for v in VIEWS}
    facets=sorted({r['review']['reviewer'] for r in rows if r['review'] and r['review']['reviewer']})
    def match(r):
        review=r['review'] or {}; at=review.get('at')
        if not in_view(r,view,task): return False
        if reviewer and (review.get('reviewer') or '__unknown__')!=reviewer: return False
        if decision and review.get('decision')!=decision: return False
        if lo is not None and (at is None or at<lo): return False
        if hi is not None and (at is None or at>=hi): return False
        return True
    found=sorted((r for r in rows if match(r)),key=lambda r:r['image_id'])
    return {'items':found[(page-1)*size:page*size], 'total':len(found), 'counts':counts,
            'reviewers':facets, 'page':page, 'size':size, 'view':view, 'task':task}

SENSITIVE = {'token','secret','password','authorization','csrf','channel_access_token','channel_secret','access_token'}
def redact(value):
    if isinstance(value,float) and not math.isfinite(value): return None
    if isinstance(value,dict): return {k:('[已遮罩]' if any(s in str(k).lower() for s in SENSITIVE) else redact(v)) for k,v in value.items()}
    if isinstance(value,list): return [redact(v) for v in value]
    return value

SELECT_ALL_LIMIT = 1000


def query_audit(connection, actor='', action='', related='', outcome='', start='', end='', page=1, size=30, snapshot=None, ids_only=False):
    if page<1 or not 1<=size<=100: raise ValueError('無效的分頁')
    if outcome not in ('','unknown','submitted','succeeded','failed','cancelled','interrupted','running'): raise ValueError('無效的結果分類')
    lo,hi=date_bounds(start,end)
    cap=connection.execute('SELECT COALESCE(MAX(id),0) FROM audit').fetchone()[0] if snapshot is None else snapshot
    if cap<0: raise ValueError('無效的稽核分頁版本')
    visible="NOT EXISTS (SELECT 1 FROM resource_lifecycle r WHERE r.type='audit' AND r.id=CAST(audit.id AS TEXT) AND r.state!='active')"
    clauses=['id<=?',visible]; values=[cap]
    for key,val in [('actor',actor),('action',action)]:
        if key=='actor' and val=='__unknown__': clauses.append("(actor IS NULL OR actor IN ('','local_operator'))")
        elif val: clauses.append(f'{key}=?'); values.append(val)
    if lo is not None: clauses.append('at>=?'); values.append(lo)
    if hi is not None: clauses.append('at<?'); values.append(hi)
    if outcome: clauses.append("COALESCE(json_extract(detail,'$._audit.outcome'),'unknown')=?"); values.append(outcome)
    if related:
        clauses.append("EXISTS (SELECT 1 FROM json_tree(audit.detail) WHERE type IN ('text','integer') AND CAST(value AS TEXT)=?)")
        values.append(related)
    where=' AND '.join(clauses)
    total=connection.execute('SELECT COUNT(*) FROM audit WHERE '+where,values).fetchone()[0]
    if ids_only:
        # Explicit "select all matching" across pages; bounded like trash previews.
        ids=[str(r[0]) for r in connection.execute('SELECT id FROM audit WHERE '+where+' ORDER BY at DESC,id DESC LIMIT ?',values+[SELECT_ALL_LIMIT])]
        return {'ids':ids,'total':total,'limit':SELECT_ALL_LIMIT,'snapshot':cap}
    rows=connection.execute('SELECT * FROM audit WHERE '+where+' ORDER BY at DESC,id DESC LIMIT ? OFFSET ?',values+[size,(page-1)*size]).fetchall()
    items=[]
    for row in rows:
        r=dict(row); detail=json.loads(r['detail']); r['detail']=redact(detail)
        r['outcome']=detail.get('_audit',{}).get('outcome','unknown')
        r['actor']=None if r['actor'] in ('','local_operator') else r['actor']; items.append(r)
    return {'items':items,'total':total,'page':page,'size':size,'snapshot':cap,
            'actors':[r[0] for r in connection.execute("SELECT DISTINCT actor FROM audit WHERE actor NOT IN ('','local_operator') AND "+visible+" ORDER BY actor")],
            'actions':[r[0] for r in connection.execute('SELECT DISTINCT action FROM audit WHERE '+visible+' ORDER BY action')]}
