"""Research resource lifecycle, exact previews and durable maintenance operations."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
import time
import uuid
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from src.common import read_json, write_json
from src.workbench import jobs, registry, resources, managed_files
from src.workbench.storage import digest, operator, file_lock
from src.workbench.views import date_bounds, redact


class Target(BaseModel):
    model_config = ConfigDict(extra='forbid')
    type: Literal['job','model','audit']
    id: str = Field(min_length=1,max_length=128)


class PreviewRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    action: Literal['move','restore','purge']
    targets: list[Target] = Field(min_length=1,max_length=100)


class CommitRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    preview_id: str
    confirmation: str = ''


class ReferenceRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    revision: str
    indices: list[int] = Field(min_length=1,max_length=100)


class PreviewResponse(BaseModel):
    model_config=ConfigDict(extra='allow')
    id: str
    state: Literal['calculating','ready','failed','expired','consumed']


class OperationResponse(BaseModel):
    model_config=ConfigDict(extra='allow')
    id: str
    action: Literal['move','restore','purge']
    state: Literal['preparing','running','completed','partial_failed','needs_check']
    result: list[dict]
    steps: list[dict]
    removed_files: int
    removed_logical_bytes: int


class TrashListResponse(BaseModel):
    model_config=ConfigDict(extra='allow')
    items: list[dict]
    total: int
    page: int
    size: int


def dump(value): return json.dumps(value,ensure_ascii=False,allow_nan=False)


def target_key(t): return t['type'] + ':' + str(t['id'])


def get_resource(kind, ident):
    ident=str(ident)
    if kind=='job':
        item=jobs.get(ident)
        return item,jobs.folder(ident)
    if kind=='model':
        item=registry.get(ident,verify=False)
        return item,registry.artifact_path(ident)
    if kind=='audit':
        if not ident.isdecimal() or int(ident)<1:raise ValueError('無效的稽核 ID')
        with jobs.db() as con: row=con.execute('SELECT * FROM audit WHERE id=?',(int(ident),)).fetchone()
        if not row:raise ValueError('原稽核紀錄不存在')
        item=dict(row);item['detail']=json.loads(item['detail'])
        return item,None
    raise ValueError('不支援的資源類型')


def summary(kind, item):
    if kind=='job':return {k:item.get(k) for k in ('id','kind','state','created','updated','config')}
    if kind=='model':return {k:item.get(k) for k in ('id','model','experiment','created','artifact_hash','config','extra')}
    return {k:item.get(k) for k in ('id','at','actor','action')}


def reference_chains():
    result=[]
    for target in ('local','line'):
        path=registry.REFS/(target+'.json')
        if not path.exists():result.append({'target':target,'revision':None,'nodes':[]});continue
        content=read_json(path);node=content;nodes=[]
        while node is not None:
            if not isinstance(node,dict) or not isinstance(node.get('artifact'),str) or len(nodes)>1000:
                raise ValueError('模型回復引用損毀，需先檢查引用紀錄')
            nodes.append({'index':len(nodes),'artifact':node['artifact'],'updated':node.get('updated'),'current':not nodes})
            node=node.get('previous')
        result.append({'target':target,'revision':digest(content),'nodes':nodes})
    return result


def dependencies(kind, ident, item):
    blockers=[];relations=[];warnings=[]
    if kind=='audit':
        operation_id=item.get('detail',{}).get('operation')
        if operation_id:
            with jobs.db() as con:op=con.execute('SELECT state FROM trash_operations WHERE id=?',(operation_id,)).fetchone()
            if op and op['state']!='completed':blockers.append('此稽核仍屬於未完成的管理操作，必須保留。')
        return blockers,relations,['永久刪除後不再保留原稽核事件內容；另留最小刪除摘要與管理事件。']
    all_jobs=jobs.listing(limit=None,include_trashed=True)
    if kind=='job' and item['state'] not in jobs.TERMINAL:
        blockers.append('工作尚未終止：'+item['state']+'；請先停止並等待終止狀態。')
    if kind=='job' and jobs.owned_process(item):blockers.append('工作程序仍在執行或結束整理中，請等待程序退出。')
    for j in all_jobs:
        cfg=j['config']; fields=('artifact','initial_artifact') if kind=='model' else ('resume_job','baseline_job','experiment','evaluation_job','regression_job')
        hits=[k for k in fields if cfg.get(k)==ident]
        if kind=='model' and cfg.get('checkpoint_import'):
            from src.imports.service import load as load_import
            imported=load_import(jobs.ROOT,cfg['checkpoint_import'])
            if imported['items'][0].get('artifact')==ident:hits.append('checkpoint_import')
        if hits:
            active=j['state'] not in jobs.TERMINAL
            relations.append({'type':'job','id':j['id'],'state':j['state'],'relation':hits,'required':active})
            if active:blockers.append(f"活動工作 {j['id']} 仍依賴此資源（{', '.join(hits)}）。")
        if kind=='job' and j['state'] not in jobs.TERMINAL and j['kind']=='regression' and 'baseline_job' not in cfg:
            blockers.append(f"舊版回歸工作 {j['id']} 未固定基準，請等待結束。")
    if kind=='model':
        for ref in reference_chains():
            for node in ref['nodes']:
                if node['artifact']==ident:
                    relations.append({'type':'reference','id':ref['target'],'index':node['index'],'required':True})
                    blockers.append(f"{ref['target']} {'目前使用' if node['current'] else '回復鏈第 '+str(node['index'])+' 層'}引用此模型；請先明確處理引用。")
        for p in registry.VERSIONS.glob('*/artifact.json'):
            other=read_json(p)
            if other.get('extra',{}).get('derived_from')==ident:
                relations.append({'type':'model','id':other['id'],'relation':'derived_from','required':False})
        warnings.append('權重刪除後，此版本不能重新推論或評估；既有評估報告仍保留。')
    else:
        for p in registry.VERSIONS.glob('*/artifact.json'):
            other=read_json(p)
            if other.get('experiment')==ident:relations.append({'type':'model','id':other['id'],'relation':'experiment','required':False})
        for j in all_jobs:
            path=jobs.folder(j['id'])/'regression.json'
            if path.exists() and read_json(path).get('baseline_job')==ident:
                relations.append({'type':'job','id':j['id'],'relation':'historical_baseline','required':False})
        with jobs.db() as con:
            for row in con.execute('SELECT id,status,payload FROM events'):
                payload=json.loads(row['payload'])
                if ident in (payload.get('job'),payload.get('trace_id')):
                    relations.append({'type':'event','id':row['id'],'relation':'job','required':row['status'] in ('queued','running')})
                    if row['status'] in ('queued','running'):blockers.append('事件 '+row['id']+' 尚待 reconcile，請等待狀態完成。')
        warnings.append('checkpoint 刪除後不能從此工作續訓；完整日誌與曲線刪除後無法重現該訓練過程。')
    for p in (registry.ROOT/'runs/workbench/evaluations').glob('*/report.json'):
        report=read_json(p)
        if (kind=='model' and report.get('artifact')==ident) or (kind=='job' and p.parent.name==ident):
            relations.append({'type':'report','id':p.parent.name,'relation':'historical','required':False})
    return sorted(set(blockers)),relations,warnings


# Established writer outputs: ownership also requires a matching immutable request.
JOB_LEAVES={'request.json','experiment.json','result.json','effective.json','progress.json','progress.jsonl','worker.log','cancel','last.pt','last.tmp','checkpoint_selection.json','regression.json','result.jpg','managed-files.json'}
TRAIN_LEAVES={'args.yaml','results.csv','results.png','labels.jpg','labels_correlogram.jpg','confusion_matrix.png','confusion_matrix_normalized.png','BoxF1_curve.png','BoxP_curve.png','BoxR_curve.png','BoxPR_curve.png','F1_curve.png','P_curve.png','R_curve.png','PR_curve.png'}
PROVENANCE={'request.json','experiment.json','effective.json','regression.json'}


def known_job_file(name,item,owned):
    if name in owned:return True
    if name in JOB_LEAVES:return True
    if name.startswith('training/weights/') and Path(name).name in ('best.pt','last.pt'):return item['kind']=='train'
    if name.startswith('training/') and (Path(name).name in TRAIN_LEAVES or Path(name).name.startswith(('train_batch','val_batch')) and Path(name).suffix=='.jpg'):return item['kind']=='train'
    return name.startswith('artifact/') and item['kind']=='train' and Path(name).name in ('best.pt','model.pt','classifier.npz','pipeline.json','config.json','model.safetensors','preprocessor_config.json')


def inventory(kind,item,root):
    files=[];retained=[];issues=[]
    if root is None:return files,retained,issues
    owned={};request_ok=True
    if kind=='job':
        request=root/'request.json'
        request_ok=request.is_file() and read_json(request).get('id')==item['id'] and read_json(request).get('config')==item['config']
        path=root/'managed-files.json'
        if path.exists():owned=read_json(path).get('files',{})
        if not request_ok:issues.append('工作 request 與資料庫不一致或缺失，無法確認產物歸屬。')
    declared=set(item.get('files',{})) if kind=='model' else set()
    seen=set()
    if not root.exists():return [],[],['資源目錄不存在；無法完整還原。']
    for path,link_error in managed_files.walk(root):
        name=path.relative_to(root).as_posix();seen.add(name)
        row={'path':name,'bytes':None,'identity':None,'reason':None}
        if path.name.startswith('.env') or path.suffix.lower() in ('.pem','.key','.py','.ps1','.exe','.dll','.sqlite3','.db'):
            row['reason']='程式、金鑰或資料庫內容不在此清理範圍'
            retained.append(row);issues.append(name+'：'+row['reason']);continue
        if link_error:
            row['reason']=link_error;issues.append(name+'：'+link_error);retained.append(row);continue
        try:
            fp=managed_files.inspect(path,root);row.update(bytes=fp['bytes'],identity=fp)
        except (OSError,ValueError) as exc:
            row['reason']=type(exc).__name__+'：'+str(exc);issues.append(name+'：'+row['reason']);retained.append(row);continue
        if kind=='model':
            allowed=name in declared or name=='artifact.json'
            if name in declared and row['identity']['sha256']!=item['files'][name]:
                issues.append(name+'：登錄雜湊不符');allowed=False
            reason='未登錄的模型檔案，無法證明歸屬'
        else:
            allowed=request_ok and known_job_file(name,item,owned)
            reason='保留歷史追溯／回歸報告' if name in PROVENANCE else '未確認歸屬的工作內容'
            if name in PROVENANCE:allowed=False
            if name in owned and owned[name]!=row['identity']['sha256']:
                allowed=False;reason='產物清單雜湊不符';issues.append(name+'：'+reason)
        if allowed:files.append(row)
        else:row['reason']=reason;retained.append(row)
    if kind=='model':
        for name in sorted(declared-seen):
            retained.append({'path':name,'bytes':None,'identity':None,'reason':'登錄檔案不存在'})
            issues.append(name+'：登錄檔案不存在')
    return sorted(files,key=lambda x:x['path']),sorted(retained,key=lambda x:x['path']),issues


def seal_job(ident):
    """Record actual files produced by a terminal worker; unknown legacy files stay protected."""
    root=jobs.folder(ident);item=jobs.get(ident);files={}
    for p,error in managed_files.walk(root):
        name=p.relative_to(root).as_posix()
        if not error and name not in PROVENANCE|{'managed-files.json','worker.log'} and known_job_file(name,item,{}):
            try:files[name]=managed_files.inspect(p,root)['sha256']
            except (OSError,ValueError):pass
    write_json(root/'managed-files.json',{'schema_version':1,'job':ident,'files':files})


def inspect_target(t,action):
    kind,ident=t['type'],str(t['id']);life=resources.record(kind,ident)
    item,root=get_resource(kind,ident)
    blockers,relations,warnings=dependencies(kind,ident,item)
    expected='active' if action=='move' else 'trashed'
    if life['state']!=expected:blockers.append('資源狀態已變更：'+life['state'])
    files,retained,issues=inventory(kind,item,root)
    # Unknown/unreadable files never silently enter a destructive plan.
    if action in ('purge','restore'):blockers.extend(issues)
    elif any('連結' in issue or '歸屬' in issue for issue in issues):blockers.extend(issues)
    if action=='restore' and kind=='model':
        blockers=[b for b in blockers if '引用此模型' not in b]
    content_bytes=sum(len(str(v).encode('utf-8')) for v in item.values() if v is not None) if kind in ('job','audit') else None
    all_files=files+retained;known=sum(f['bytes'] for f in all_files if f['bytes'] is not None)
    unknown=any(f['bytes'] is None for f in all_files) or bool(issues)
    capacity={'status':'unable' if unknown else 'estimated','calculated_at':time.time(),
              'file_bytes':None if unknown else known,'known_file_bytes':known,
              'exclusive_file_bytes':sum(f['bytes'] for f in files),
              'estimated_release_bytes':sum(f['bytes'] for f in files),
              'retained_file_bytes':None if any(f['bytes'] is None for f in retained) else sum(f['bytes'] for f in retained),
              'database_content_estimate_bytes':content_bytes,'database_immediate_release_bytes':None,
              'basis':'檔案邏輯 bytes；磁碟配置回收未精確量測。資料庫為欄位內容估計，刪除後空間可重用，不保證檔案縮小。',
              'limitations':issues}
    label=(item.get('config',{}).get('model') or item.get('kind')) if kind=='job' else item.get('model') if kind=='model' else item.get('action')
    return {'type':kind,'id':ident,'name':label or ident,'revision':life['revision'],'resource_state':life['state'],
            'source_fingerprint':digest(item),'source':item,'summary':redact(summary(kind,item)),
            'files':files,'retained':retained,'relations':relations,'blockers':sorted(set(blockers)),
            'warnings':warnings,'capacity':capacity,'root':str(root) if root else None}


def stable(item):
    return {k:v for k,v in item.items() if k not in ('capacity',)}


def batch_capacity(items):
    unique={};retained={};unknown=False
    for item in items:
        unknown |= item['capacity']['file_bytes'] is None
        for row,into in [(r,unique) for r in item['files']]+[(r,retained) for r in item['retained']]:
            fp=row.get('identity')
            if fp:into[(fp['device'],fp['inode'])]=fp['bytes']
    for key in retained:unique.pop(key,None)
    return {'known_file_bytes':sum({**unique,**retained}.values()),'file_bytes':None if unknown else sum({**unique,**retained}.values()),'estimated_release_bytes':sum(unique.values()),'retained_file_bytes':None if unknown else sum(retained.values()),'status':'unable' if unknown else 'estimated','basis':'依實體檔案去重的邏輯 bytes；SQLite 立即磁碟回收未知。'}


def save_capacity(item):
    with jobs.db() as con:
        con.execute('UPDATE resource_lifecycle SET capacity=? WHERE type=? AND id=? AND revision=?',
                    (dump(item['capacity']),item['type'],item['id'],item['revision']))


def list_trash(kind='',search='',start='',end='',actor='',sort='moved',direction='desc',page=1,size=30):
    if kind not in ('',*resources.TYPES) or sort not in ('moved','file_bytes','estimated_release_bytes') or direction not in ('asc','desc') or page<1 or not 1<=size<=100:
        raise ValueError('無效的垃圾桶篩選或分頁')
    lo,hi=date_bounds(start,end);clauses=["state NOT IN ('active','purged')"];values=[]
    if kind:clauses.append('type=?');values.append(kind)
    if search:clauses.append("(instr(lower(id),lower(?))>0 OR instr(lower(summary),lower(?))>0)");values.extend([search,search])
    if lo is not None:clauses.append('moved>=?');values.append(lo)
    if hi is not None:clauses.append('moved<?');values.append(hi)
    if actor=='__unknown__':clauses.append("(actor IS NULL OR actor='' OR actor='local_operator')")
    elif actor:clauses.append('actor=?');values.append(actor)
    expression='moved' if sort=='moved' else "json_extract(capacity,'$."+sort+"')"
    where=' AND '.join(clauses)
    with jobs.db() as con:
        total=con.execute('SELECT COUNT(*) FROM resource_lifecycle WHERE '+where,values).fetchone()[0]
        all_count=con.execute("SELECT COUNT(*) FROM resource_lifecycle WHERE state NOT IN ('active','purged')").fetchone()[0]
        actors=[r[0] for r in con.execute("SELECT DISTINCT actor FROM resource_lifecycle WHERE state NOT IN ('active','purged') AND actor IS NOT NULL ORDER BY actor")]
        page=min(page,max(1,(total+size-1)//size))
        rows=con.execute('SELECT * FROM resource_lifecycle WHERE '+where+' ORDER BY ('+expression+' IS NULL),'+expression+' '+direction+',type,id LIMIT ? OFFSET ?',values+[size,(page-1)*size]).fetchall()
    items=[]
    for row in rows:
        item=dict(row);item['summary']=json.loads(item['summary']);item['capacity']=json.loads(item['capacity']) if item['capacity'] else {'status':'pending'}
        if time.time()-item['capacity'].get('calculated_at',0)>1800 and item['capacity']['status']!='pending':item['capacity']['status']='stale'
        item['can_restore']=item['can_purge']=item['state']=='trashed'
        items.append(item)
    return redact({'items':items,'total':total,'all_count':all_count,'actors':actors,'page':page,'size':size})


def public_plan(plan):
    result={k:v for k,v in plan.items() if k!='items'}
    result['items']=[{k:v for k,v in i.items() if k not in ('root','source','source_fingerprint')} for i in plan.get('items',[])]
    return redact(result)


def operation(ident,page=1,size=100):
    if page<1 or not 1<=size<=100:raise ValueError('無效的操作紀錄分頁')
    with jobs.db() as con: row=con.execute('SELECT * FROM trash_operations WHERE id=?',(ident,)).fetchone()
    if not row:raise ValueError('刪除操作不存在')
    item=dict(row);item.pop('fingerprint');item.pop('idem')
    item['plan']=public_plan(json.loads(item['plan']));item['result']=json.loads(item['result'])
    for entry in item['plan']['items']:
        for field in ('files','retained'):
            entry[field+'_count']=len(entry[field]);entry[field]=entry[field][(page-1)*size:page*size]
    for entry in item['result']:
        retained=entry.get('retained',[]);entry['retained_count']=len(retained);entry['retained']=retained[(page-1)*size:page*size]
    with jobs.db() as con:
        stats=con.execute("SELECT COUNT(*),SUM(state='removed'),SUM(CASE WHEN state='removed' THEN bytes ELSE 0 END) FROM trash_steps WHERE operation=?",(ident,)).fetchone()
        steps=[dict(r) for r in con.execute('SELECT type,resource,path,state,bytes,error FROM trash_steps WHERE operation=? ORDER BY type,resource,path LIMIT ? OFFSET ?',(ident,size,(page-1)*size))]
    item['steps']=steps
    item['step_count'],item['removed_files'],item['removed_logical_bytes']=stats[0],stats[1] or 0,stats[2] or 0
    item['page']=page;item['size']=size
    item['disk_reclaimed_bytes']=None
    return redact(item)


def operation_lease(ident):
    if len(ident)!=32 or any(c not in '0123456789abcdef' for c in ident):raise ValueError('無效操作 ID')
    return file_lock(jobs.JOBS.parent/'maintenance-leases'/(ident+'.lock'))


def operation_history(page=1,size=30):
    if page<1 or not 1<=size<=100:raise ValueError('無效的操作分頁')
    with jobs.db() as con:
        total=con.execute('SELECT COUNT(*) FROM trash_operations').fetchone()[0]
        page=min(page,max(1,(total+size-1)//size))
        items=[dict(r) for r in con.execute('SELECT id,action,state,created,updated,actor FROM trash_operations ORDER BY created DESC,id DESC LIMIT ? OFFSET ?',(size,(page-1)*size))]
    return redact({'items':items,'page':page,'size':size,'total':total})


class Maintenance:
    def __init__(self,session):
        self.session=session
        self.pool=ThreadPoolExecutor(max_workers=2,thread_name_prefix='workbench-maintenance')
        self.closed=False

    def recover(self):
        with resources.resource_lock():
            with jobs.db() as con:
                pending=[r['id'] for r in con.execute("SELECT id FROM trash_operations WHERE state IN ('preparing','running')")]
            for ident in pending:
                lease=operation_lease(ident)
                try:lease.__enter__()
                except RuntimeError:continue  # Another process still owns this operation.
                try:
                    with jobs.db() as con:
                        con.execute("UPDATE trash_operations SET state='needs_check',updated=? WHERE id=? AND state IN ('preparing','running')",(time.time(),ident))
                        con.execute("UPDATE resource_lifecycle SET state='needs_check' WHERE state='purging' AND operation=?",(ident,))
                finally:lease.__exit__(None,None,None)

    def close(self):
        self.closed=True
        self.pool.shutdown(wait=True,cancel_futures=False)

    def preview(self,body):
        targets=[t.model_dump() for t in body.targets]
        if len({target_key(t) for t in targets})!=len(targets):raise ValueError('同一資源不能重複選取')
        ident=uuid.uuid4().hex;now=time.time()
        with jobs.db() as con:
            con.execute('INSERT INTO trash_previews(id,session,created,expires,state,plan) VALUES(?,?,?,?,?,?)',
                        (ident,self.session,now,now+300,'calculating',dump({'action':body.action,'targets':targets})))
        self.pool.submit(self._calculate,ident,body.action,targets)
        return {'id':ident,'state':'calculating'}

    def _calculate(self,ident,action,targets):
        items=[]
        try:
            for t in targets:
                try:
                    item=inspect_target(t,action);items.append(item);save_capacity(item)
                except Exception as exc:
                    items.append({**t,'name':t['id'],'blockers':[str(exc)],'warnings':[], 'files':[],'retained':[], 'relations':[],
                                  'capacity':{'file_bytes':None,'status':'unable'},'revision':resources.record(t['type'],t['id'])['revision']})
            # Shared physical files in the selected set are retained, not double-deleted.
            owners={}
            for item in items:
                for f in item['files']+item['retained']:
                    fp=f.get('identity')
                    if fp:owners.setdefault((fp['device'],fp['inode']),set()).add(target_key(item))
            for item in items:
                if any(len(owners.get((f['identity']['device'],f['identity']['inode']),()))>1 for f in item['files']):
                    item['blockers'].append('多個資源引用相同實體檔案，需先確認並解除共享關係。')
            plan={'action':action,'targets':targets,'items':items,'capacity':batch_capacity(items),
                  'confirmation':'永久刪除' if action=='purge' else '',
                  'blocked':any(i['blockers'] for i in items)}
            with jobs.db() as con:
                con.execute('UPDATE trash_previews SET state=?,plan=? WHERE id=?',('ready',dump(plan),ident))
        except Exception as exc:
            with jobs.db() as con:
                con.execute('UPDATE trash_previews SET state=?,plan=? WHERE id=?',('failed',dump({'error':str(exc),'action':action,'items':items}),ident))

    def get_preview(self,ident,page=1,size=100):
        if page<1 or not 1<=size<=100:raise ValueError('無效的預覽分頁')
        with jobs.db() as con:row=con.execute('SELECT * FROM trash_previews WHERE id=?',(ident,)).fetchone()
        if not row or row['session']!=self.session:raise ValueError('預覽不存在或管理會話已失效')
        result=dict(row);result.pop('session');plan=public_plan(json.loads(result.pop('plan')))
        for item in plan.get('items',[]):
            item['file_count']=len(item['files']);item['retained_count']=len(item['retained'])
            item['files']=item['files'][(page-1)*size:page*size]
            item['retained']=item['retained'][(page-1)*size:page*size]
        if time.time()>row['expires']:result['state']='expired'
        return {**result,**plan,'page':page,'size':size}

    def capacity(self,targets):
        for t in targets:
            if resources.record(t.type,t.id)['state']=='active':raise ValueError('容量重新計算只適用垃圾桶項目')
        return self.preview(PreviewRequest(action='purge',targets=targets))

    def commit(self,body,idem):
        if not idem or len(idem)>160:raise ValueError('缺少有效冪等鍵')
        fingerprint=digest(body.model_dump())
        with jobs.db() as con:
            old=con.execute('SELECT id,fingerprint FROM trash_operations WHERE idem=?',(idem,)).fetchone()
            row=con.execute('SELECT * FROM trash_previews WHERE id=?',(body.preview_id,)).fetchone()
        if old:
            if old['fingerprint']!=fingerprint:raise ValueError('冪等鍵已用於其他操作')
            return operation(old['id'])
        if not row or row['session']!=self.session or row['state']!='ready' or row['expires']<time.time():
            raise ValueError('預覽失效，請重新產生預覽')
        plan=json.loads(row['plan']);action=plan['action']
        if action not in ('move','restore','purge'):raise ValueError('此預覽不可提交至垃圾桶操作')
        if plan['blocked']:raise ValueError('存在硬性阻擋，請明確調整選取範圍並重新預覽')
        if body.confirmation!=plan['confirmation']:raise ValueError('確認文字不符')
        # Hash scans stay outside lifecycle/SQLite locks. Reserve only after a
        # second short state/dependency/handle check; execution rehashes each file.
        for expected in plan['items']:
            try:current=inspect_target(expected,action)
            except (ValueError,FileNotFoundError):
                with jobs.db() as con:repeated=con.execute('SELECT id,fingerprint FROM trash_operations WHERE idem=?',(idem,)).fetchone()
                if repeated:
                    if repeated['fingerprint']!=fingerprint:raise ValueError('冪等鍵已用於其他操作')
                    return operation(repeated['id'])
                raise
            if digest(stable(current))!=digest(stable(expected)) or current['blockers']:
                # Another request with this same key may have committed while
                # this request was scanning outside the reservation lock.
                with jobs.db() as con:repeated=con.execute('SELECT id,fingerprint FROM trash_operations WHERE idem=?',(idem,)).fetchone()
                if repeated:
                    if repeated['fingerprint']!=fingerprint:raise ValueError('冪等鍵已用於其他操作')
                    return operation(repeated['id'])
                raise ValueError('預覽後內容、狀態或相依性已變更，請重新預覽')
        # Compute owners include LINE and older CLI consumers that do not expose a DB lease.
        from contextlib import nullcontext
        from src.lock import OperationLock
        guard=OperationLock() if any(i['type']!='audit' for i in plan['items']) else nullcontext()
        with guard,resources.resource_lock():
            with jobs.db() as con:
                old=con.execute('SELECT id,fingerprint FROM trash_operations WHERE idem=?',(idem,)).fetchone()
            if old:
                if old['fingerprint']!=fingerprint:raise ValueError('冪等鍵已用於其他操作')
                return operation(old['id'])
            if row['expires']<time.time():raise ValueError('預覽已到期，請重新產生預覽')
            for expected in plan['items']:
                life=resources.record(expected['type'],expected['id'])
                source,root=get_resource(expected['type'],expected['id'])
                blocks,relations,warnings=dependencies(expected['type'],expected['id'],source)
                if life['revision']!=expected['revision'] or life['state']!=expected['resource_state'] or digest(source)!=expected['source_fingerprint'] or blocks or relations!=expected['relations']:
                    raise ValueError('預覽後內容、狀態或相依性已變更，請重新預覽')
                for f in expected['files']+expected['retained']:
                    if f.get('identity'):managed_files.verify_stat(root/f['path'],root,f['identity'])
            ident=uuid.uuid4().hex;now=time.time();actor=operator.get()
            with jobs.db() as con:
                con.execute('BEGIN IMMEDIATE')
                initial_result=[] if action=='purge' else [{'type':i['type'],'id':i['id'],'state':'succeeded'} for i in plan['items']]
                con.execute('INSERT INTO trash_operations(id,idem,fingerprint,action,state,created,updated,actor,plan,result) VALUES(?,?,?,?,?,?,?,?,?,?)',
                            (ident,idem,fingerprint,action,'preparing' if action=='purge' else 'completed',now,now,actor,dump(plan),dump(initial_result)))
                for item in plan['items']:
                    state='purging' if action=='purge' else 'trashed' if action=='move' else 'active'
                    con.execute('''INSERT INTO resource_lifecycle(type,id,state,revision,moved,actor,summary,capacity,operation) VALUES(?,?,?,?,?,?,?,?,?)
                        ON CONFLICT(type,id) DO UPDATE SET state=excluded.state,revision=excluded.revision,
                        moved=CASE WHEN ?='move' THEN excluded.moved ELSE resource_lifecycle.moved END,
                        actor=CASE WHEN ?='move' THEN excluded.actor ELSE resource_lifecycle.actor END,
                        summary=excluded.summary,capacity=excluded.capacity,operation=excluded.operation''',
                        (item['type'],item['id'],state,item['revision']+1,now,actor,dump(item['summary']),dump(item['capacity']),ident,action,action))
                    if action=='purge':
                        for f in item['files']:
                            con.execute('INSERT INTO trash_steps(operation,type,resource,path,state,identity,bytes,error) VALUES(?,?,?,?,?,?,?,?)',
                                        (ident,item['type'],item['id'],f['path'],'pending',dump(f['identity']),f['bytes'],None))
            jobs.audit('trash_'+action+'_submitted',{'operation':ident,'targets':plan['targets']},actor=actor,outcome='submitted')
            if action!='purge':
                results=[{'type':i['type'],'id':i['id'],'state':'succeeded'} for i in plan['items']]
                with jobs.db() as con:con.execute('UPDATE trash_operations SET state=?,result=?,updated=? WHERE id=?',('completed',dump(results),time.time(),ident))
                jobs.audit('trash_'+action+'_completed',{'operation':ident,'targets':plan['targets']},actor=actor)
            else:
                lease=operation_lease(ident);lease.__enter__()
                try:self.pool.submit(self.execute,ident,lease)
                except BaseException:
                    lease.__exit__(None,None,None)
                    raise
        return operation(ident)

    def execute(self,ident,lease=None):
        if lease is None:
            lease=operation_lease(ident)
            try:lease.__enter__()
            except RuntimeError:return
        try:
            with jobs.db() as con:
                row=con.execute('SELECT state FROM trash_operations WHERE id=?',(ident,)).fetchone()
            if not row or row['state']!='preparing':return
            self._execute(ident)
        finally:lease.__exit__(None,None,None)

    def _execute(self,ident):
        try:
            with jobs.db() as con:
                row=con.execute('SELECT * FROM trash_operations WHERE id=?',(ident,)).fetchone()
                con.execute('UPDATE trash_operations SET state=?,updated=? WHERE id=?',('running',time.time(),ident))
            plan=json.loads(row['plan']);results=[]
            for item in plan['items']:
                key=(item['type'],item['id']);failures=[]
                if resources.record(*key)['state']=='purged':
                    results.append({'type':key[0],'id':key[1],'state':'succeeded'});continue
                try:
                    with resources.resource_lock():
                        blocks,_,_=dependencies(*key,item['source'])
                        if blocks:raise ValueError('；'.join(blocks))
                    # Metadata is removed last so failures do not destroy restore diagnostics.
                    ordered=sorted(item['files'],key=lambda f:(f['path']=='artifact.json',f['path']))
                    for f in ordered:
                        if self.closed:raise RuntimeError('服務停止；尚未處理項目需重新檢查')
                        with jobs.db() as con:
                            step=con.execute('SELECT state FROM trash_steps WHERE operation=? AND type=? AND resource=? AND path=?',(ident,*key,f['path'])).fetchone()[0]
                        if step=='removed':continue
                        if failures and f['path']=='artifact.json':continue
                        try:
                            with resources.resource_lock():
                                life=resources.record(*key)
                                if life['state']!='purging' or life['operation']!=ident:raise ValueError('資源刪除預留已變更')
                                blocks,_,_=dependencies(*key,item['source'])
                                if blocks:raise ValueError('；'.join(blocks))
                                path=Path(item['root'])/f['path']
                                if not path.exists():raise ValueError('檔案不存在且沒有確認完成紀錄，需人工檢查')
                                def intent():
                                    with jobs.db() as con:con.execute('UPDATE trash_steps SET state=?,error=NULL WHERE operation=? AND type=? AND resource=? AND path=?',('intent',ident,*key,f['path']))
                                managed_files.remove_verified(path,Path(item['root']),f['identity'],intent)
                                with jobs.db() as con:con.execute('UPDATE trash_steps SET state=?,error=NULL WHERE operation=? AND type=? AND resource=? AND path=?',('removed',ident,*key,f['path']))
                        except Exception as exc:
                            failures.append(f['path']+'：'+str(exc))
                            with jobs.db() as con:con.execute('UPDATE trash_steps SET state=?,error=? WHERE operation=? AND type=? AND resource=? AND path=?',('failed',str(exc),ident,*key,f['path']))
                    if not failures:
                        with resources.resource_lock():
                            life=resources.record(*key)
                            blocks,_,_=dependencies(*key,item['source'])
                            if blocks or life['operation']!=ident or life['state']!='purging':raise ValueError('刪除預留或依賴已變更，需人工檢查')
                            with jobs.db() as con:
                                con.execute('BEGIN IMMEDIATE')
                                if key[0]=='job':
                                    source=item['source']
                                    original_config=dict(source['config'])
                                    if source['kind']=='regression':original_config.pop('baseline_job',None)
                                    original_request=read_json(jobs.folder(key[1])/'request.json')
                                    request_fingerprint=original_request.get('request_fingerprint') or digest(original_config)
                                    con.execute('INSERT OR IGNORE INTO deleted_job_keys(idem,id,kind,fingerprint) VALUES(?,?,?,?)',
                                                (source['idem'],key[1],source['kind'],request_fingerprint))
                                    con.execute('DELETE FROM jobs WHERE id=?',(key[1],))
                                elif key[0]=='audit':con.execute('DELETE FROM audit WHERE id=?',(int(key[1]),))
                                con.execute('UPDATE resource_lifecycle SET state=?,revision=revision+1,capacity=NULL WHERE type=? AND id=?',('purged',*key))
                                if key[0]=='audit':
                                    # Preview/operation caches must not retain a second copy
                                    # of a permanently deleted event's original detail.
                                    for table in ('trash_previews','trash_operations'):
                                        for cached in con.execute('SELECT id,plan FROM '+table).fetchall():
                                            saved=json.loads(cached['plan']);changed=False
                                            for entry in saved.get('items',[]):
                                                if entry['type']=='audit' and entry['id']==key[1] and 'source' in entry:
                                                    entry.pop('source');changed=True
                                            if changed:con.execute('UPDATE '+table+' SET plan=? WHERE id=?',(dump(saved),cached['id']))
                    else:
                        with jobs.db() as con:con.execute('UPDATE resource_lifecycle SET state=? WHERE type=? AND id=?',('partial_failed',*key))
                except Exception as exc:
                    failures.append(str(exc))
                    with jobs.db() as con:con.execute('UPDATE resource_lifecycle SET state=? WHERE type=? AND id=?',('needs_check',*key))
                results.append({'type':key[0],'id':key[1],'state':'failed' if failures else 'succeeded','errors':failures,'retained':item['retained']})
                with jobs.db() as con:con.execute('UPDATE trash_operations SET result=?,updated=? WHERE id=?',(dump(results),time.time(),ident))
            state='partial_failed' if any(r['state']=='failed' for r in results) else 'completed'
            with jobs.db() as con:con.execute('UPDATE trash_operations SET state=?,updated=? WHERE id=?',(state,time.time(),ident))
            jobs.audit('trash_purge_'+state,{'operation':ident,'results':results},actor=row['actor'],outcome='succeeded' if state=='completed' else 'failed')
        except Exception as exc:
            with jobs.db() as con:
                con.execute('UPDATE trash_operations SET state=?,updated=?,result=? WHERE id=?',('needs_check',time.time(),dump([{'state':'failed','errors':[str(exc)]}]),ident))
                con.execute("UPDATE resource_lifecycle SET state='needs_check' WHERE operation=? AND state='purging'",(ident,))

    def retry(self,ident):
        with resources.resource_lock():
            lease=operation_lease(ident);lease.__enter__()
            try:
                with jobs.db() as con:
                    row=con.execute('SELECT state,action FROM trash_operations WHERE id=?',(ident,)).fetchone()
                    if not row or row['action']!='purge' or row['state'] not in ('partial_failed','needs_check'):raise ValueError('此操作目前不可重試')
                    con.execute('UPDATE trash_operations SET state=?,updated=? WHERE id=?',('preparing',time.time(),ident))
                    con.execute("UPDATE resource_lifecycle SET state='purging' WHERE operation=? AND state IN ('partial_failed','needs_check')",(ident,))
                jobs.audit('trash_retry',{'operation':ident},outcome='submitted')
                self.pool.submit(self.execute,ident,lease)
            except BaseException:
                lease.__exit__(None,None,None)
                raise
        return operation(ident)

    def reference_preview(self,target,body):
        if target not in ('local','line'):raise ValueError('無效引用類型')
        chain=next(r for r in reference_chains() if r['target']==target)
        if chain['revision']!=body.revision:raise ValueError('引用已變更，請重新載入')
        indices=sorted(set(body.indices))
        if len(indices)!=len(body.indices) or any(i<=0 or i>=len(chain['nodes']) for i in indices):
            raise ValueError('僅能解除明確選取的歷史節點，不可移除目前模型')
        ident=uuid.uuid4().hex;now=time.time()
        plan={'action':'reference','target':target,'revision':body.revision,'indices':indices,
              'affected':[chain['nodes'][i] for i in indices],'confirmation':'解除回復引用','items':[]}
        with jobs.db() as con:con.execute('INSERT INTO trash_previews(id,session,created,expires,state,plan) VALUES(?,?,?,?,?,?)',
                                        (ident,self.session,now,now+300,'ready',dump(plan)))
        return self.get_preview(ident)

    def reference_commit(self,body):
        from src.lock import OperationLock
        with OperationLock(),resources.resource_lock():
            with jobs.db() as con:row=con.execute('SELECT * FROM trash_previews WHERE id=?',(body.preview_id,)).fetchone()
            if not row or row['session']!=self.session or row['state']!='ready' or row['expires']<time.time():raise ValueError('引用預覽已失效')
            plan=json.loads(row['plan'])
            if plan.get('action')!='reference' or body.confirmation!=plan['confirmation']:raise ValueError('確認內容不符')
            target=plan['target'];path=registry.REFS/(target+'.json');old=read_json(path)
            if digest(old)!=plan['revision']:raise ValueError('引用已變更，請重新預覽')
            nodes=[];node=old;index=0
            while node is not None:
                if index not in plan['indices']:nodes.append({k:v for k,v in node.items() if k!='previous'})
                node=node.get('previous');index+=1
            previous=None
            for node in reversed(nodes):node['previous']=previous;previous=node
            write_json(path,previous)
            with jobs.db() as con:con.execute('UPDATE trash_previews SET state=? WHERE id=?',('consumed',body.preview_id))
            jobs.audit('release_rollback_reference',{'target':target,'removed':plan['affected'],'revision_before':plan['revision'],'revision_after':digest(previous)})
            return {'target':target,'removed':plan['affected'],'current_unchanged':previous['artifact']==old['artifact']}
