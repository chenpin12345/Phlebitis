from concurrent.futures import ThreadPoolExecutor
import time
import uuid
from typing import Literal
from fastapi import APIRouter
from pydantic import BaseModel,ConfigDict,Field
from src.imports import service
from src.workbench.storage import file_lock,operator

class Scan(BaseModel):
    model_config=ConfigDict(extra='forbid')
    kind:Literal['photos','models']
    batch:str=Field(min_length=1,max_length=150)

class Commit(BaseModel):
    model_config=ConfigDict(extra='forbid')
    preview_id:str
    idempotency_key:str=Field(min_length=1,max_length=200)
    confirmation:Literal['確認匯入']

def mount(app,root,session):
    router=APIRouter(prefix='/api/v1/imports');pool=ThreadPoolExecutor(max_workers=2,thread_name_prefix='research-import')

    @router.get('/packages')
    def packages(purpose:Literal['base','checkpoint'],model:str=''):return service.packages(root,purpose,model)

    @router.post('/operations/{ident}/resume')
    def resume(ident:str):
        item=service.load(root,ident);entry=item['items'][0]
        if item['state']!='completed' or entry.get('package',{}).get('purpose')!='checkpoint':raise ValueError('不是可續訓的匯入')
        from src.workbench import jobs
        original=jobs.get(entry['package']['source']['id'])
        return jobs.enqueue('train',{**original['config'],'resume_job':original['id'],'checkpoint_import':ident},idem='resume-import:'+ident)

    @router.get('/batches')
    def batches(kind:Literal['photos','models']):return service.batches(root,kind)

    @router.get('/operations')
    def history(kind:Literal['photos','models'],page:int=1,size:int=30):
        if page<1 or not 1<=size<=100:raise ValueError('無效的分頁')
        with service.store(root) as con:
            total=con.execute('SELECT COUNT(*) FROM imports WHERE kind=?',(kind,)).fetchone()[0]
            rows=con.execute('SELECT id,batch,state,created,updated FROM imports WHERE kind=? ORDER BY created DESC,id DESC LIMIT ? OFFSET ?',(kind,size,(page-1)*size)).fetchall()
        return {'items':[dict(r) for r in rows],'total':total,'page':page,'size':size}

    @router.post('/previews')
    def scan(body:Scan):
        if not service.batch_path(root,body.kind,body.batch).is_dir():raise FileNotFoundError(body.batch)
        ident=uuid.uuid4().hex
        item={'id':ident,'kind':body.kind,'batch':body.batch,'state':'scanning','created':time.time(),'session':session,'items':[]}
        service.save(root,item)
        pool.submit(service.preview,root,body.kind,body.batch,session,ident,operator.get())
        return service.public(item)

    @router.get('/previews/{ident}')
    @router.get('/operations/{ident}')
    def detail(ident:str,page:int=1,size:int=30):return service.public(service.load(root,ident),page,size)

    @router.post('/operations')
    def submit(body:Commit):
        service.load(root,body.preview_id) # Validate identifier before constructing a lock path.
        with file_lock(root/'runtime/imports'/(body.preview_id+'.lock')):
            item=service.load(root,body.preview_id)
            if item['session']!=session:raise ValueError('預覽不屬於目前管理會話')
            if item.get('idem'):
                if item['idem']!=body.idempotency_key:raise ValueError('冪等鍵不相符')
                return service.public(item)
            if item['state']!='ready' or time.time()>item['expires']:raise ValueError('預覽尚未完成或已過期')
            if not any(e['action']=='add' for e in item['items']):raise ValueError('沒有可新增的項目')
            item.update(state='queued',idem=body.idempotency_key);service.save(root,item)
        pool.submit(service.commit,root,item['id'],body.idempotency_key,session)
        return service.public(item)

    @router.post('/operations/{ident}/retry')
    def retry(ident:str):
        service.load(root,ident)
        with file_lock(root/'runtime/imports'/(ident+'.lock')):
            item=service.load(root,ident)
            if item['state'] not in ('failed','needs_check') or not item.get('idem'):raise ValueError('此操作不可重試，請重新掃描')
            # Fresh management CSRF validation authorizes retry after server restart.
            item['session']=session;item['state']='queued';service.save(root,item)
        pool.submit(service.commit,root,ident,item['idem'],session,True)
        return service.public(item)

    app.include_router(router)
    return pool
