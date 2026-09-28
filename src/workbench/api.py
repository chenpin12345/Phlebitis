from __future__ import annotations
import io
import json
import secrets
import shutil
import time
import uuid
from contextlib import asynccontextmanager
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from PIL import Image, ImageOps
from src.common import ROOT, read_json, write_json, read_manifest, inside, stamp
from src.workbench.storage import db, audit, digest, HOME, flag
from src.workbench.contracts import MODELS, Experiment, Review, SnapshotRequest, SwitchRequest,InferenceConfig
from src.workbench import jobs, registry, lifecycle, simulation

def create_app(*,testing=False):
    manager=jobs.Manager()
    @asynccontextmanager
    async def lifespan(app):
        if not testing:
            from src.data.dataset import recover_reviews
            from src.workbench.storage import file_lock
            with file_lock(ROOT/'runtime/data.lock'): recover_reviews(ROOT)
            registry.import_legacy()
            manager.start()
        yield
        manager.close()
    app=FastAPI(title='Phlebitis local workbench',lifespan=lifespan,docs_url=None,redoc_url=None)
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=['127.0.0.1','localhost']+(['testserver'] if testing else []))
    csrf=secrets.token_urlsafe(32)

    @app.middleware('http')
    async def browser_boundary(request,call_next):
        if request.headers.get('sec-fetch-site')=='cross-site':return JSONResponse({'detail':'Cross-site request denied'},status_code=403)
        origin=request.headers.get('origin')
        if origin and origin != str(request.base_url).rstrip('/'):
            return JSONResponse({'detail':'Cross-origin access denied'},status_code=403)
        if request.method not in ('GET','HEAD','OPTIONS'):
            if not secrets.compare_digest(request.headers.get('x-csrf-token',''),csrf):
                return JSONResponse({'detail':'頁面驗證已失效，請重新整理。'},status_code=403)
            if request.url.path!='/api/v1/assets':
                size=0
                chunks=[]
                async for chunk in request.stream():
                    size+=len(chunk)
                    if size>1048576:return JSONResponse({'detail':'JSON request exceeds 1 MB'},status_code=413)
                    chunks.append(chunk)
                request._body=b''.join(chunks)
        response=await call_next(request)
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Cache-Control']='no-store'
        response.headers['Content-Security-Policy']="default-src 'self'; img-src 'self' blob: data:; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'"
        return response

    @app.exception_handler(ValueError)
    async def value_error(request,exc):
        return JSONResponse({'detail':str(exc)},status_code=409 if 'revision conflict' in str(exc) else 400)
    @app.exception_handler(RuntimeError)
    async def runtime_error(request,exc):return JSONResponse({'detail':str(exc)},status_code=409)
    @app.exception_handler(FileNotFoundError)
    async def file_error(request,exc):return JSONResponse({'detail':'必要檔案不存在，請檢查環境或重新準備資料。'},status_code=404)

    @app.get('/api/v1/session')
    def session():return {'csrf':csrf,'actor':'local_operator','research_only':True}

    @app.get('/api/v1/overview')
    def overview():
        from collections import Counter
        rows=read_manifest(); states=jobs.listing()
        return {'data':dict(Counter(r['status'] for r in rows)),'approved_labels':dict(Counter(r['label_state'] for r in rows if r['status']=='approved')),'verified_subjects':len({r['subject_id'] for r in rows if r['group_verified']=='true' and r['subject_id']}),'jobs':states,'references':{t:read_json(registry.REFS/(t+'.json')) if (registry.REFS/(t+'.json')).exists() else None for t in ('local','line')},'artifacts':len(registry.listing())}

    @app.get('/api/v1/doctor')
    def doctor():
        import torch
        packages={}
        for name in ['torch','torchvision','ultralytics','transformers','safetensors','scikit-learn','fastapi','psutil']:
            try:packages[name]=version(name)
            except PackageNotFoundError:packages[name]=None
        return {'packages':packages,'cuda':torch.cuda.is_available(),'gpu':torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,'vram':torch.cuda.get_device_properties(0).total_memory if torch.cuda.is_available() else None,'free_disk_gb':round(shutil.disk_usage(ROOT).free/1024**3,1),'frontend_ready':(ROOT/'web/dist/index.html').exists(),'ports':{'workbench':8765,'line':8000},'line_credentials_required':False,'repair':'執行 scripts/setup-workbench.ps1 安裝專案依賴；GPU 不可用時明確選擇 CPU。'}

    @app.get('/api/v1/line/state')
    def line_state():
        import psutil
        path=ROOT/'runtime/line-state.json'
        if not path.exists():return {'state':'not_started'}
        state=read_json(path)
        try:
            process=psutil.Process(state['pid']);cmd=process.cmdline()
            if 'src' not in cmd or 'serve' not in cmd:return {'state':'not_running'}
        except (psutil.NoSuchProcess,psutil.AccessDenied):return {'state':'not_running'}
        return state

    @app.post('/api/v1/line/drain')
    def drain_line():
        state=line_state()
        if state['state'] not in ('accepting','draining'):raise ValueError('No active LINE intake to stop')
        write_json(ROOT/'runtime/line-control.json',{'action':'drain','requested':stamp()})
        audit('drain_line',{'impact':'stop accepting images; finish received jobs; release model compute'})
        return {'state':'draining','message':'停止新照片接案，待既有工作完成後釋放模型。重新啟動 LINE 前需清除停止要求。'}

    @app.get('/api/v1/data')
    def data():return [{**r,'revision':digest(r)} for r in read_manifest()]

    def find_image(ident):
        row=next((r for r in read_manifest() if r['image_id']==ident),None)
        if row is None: raise HTTPException(404)
        return row

    @app.get('/api/v1/data/{ident}/image')
    def data_image(ident):
        row=find_image(ident)
        with Image.open(inside(row['image_path'])) as im:
            image=ImageOps.exif_transpose(im).convert('RGB'); image.thumbnail((1800,1800)); buf=io.BytesIO();image.save(buf,'JPEG',quality=90)
        return Response(buf.getvalue(),media_type='image/jpeg')

    @app.get('/api/v1/data/{ident}/annotation')
    def annotation(ident):
        from src.data.labels import orient_boxes,from_labelme
        row=find_image(ident)
        with Image.open(inside(row['image_path'])) as im: orientation=im.getexif().get(274,1); size=im.size
        boxes=[]
        if row['yolo_path'] and inside(row['yolo_path']).exists(): boxes=[list(map(float,line.split())) for line in inside(row['yolo_path']).read_text().splitlines() if line.strip()]
        elif row['annotation_path']:
            try: boxes=from_labelme(read_json(inside(row['annotation_path'])),size)
            except ValueError: pass
        history=[read_json(p) for p in sorted((ROOT/'data/reviews').glob('*_'+ident+'.json'))]
        return {'row':row,'revision':digest(row),'boxes':orient_boxes(boxes,orientation),'orientation':orientation,'original_size':size,'coordinate_system':'EXIF-corrected normalized YOLO xywh','history':history}

    @app.put('/api/v1/data/{ident}')
    def save_review(ident,body:Review):
        from src.data.labels import orient_boxes,validate
        from src.data.dataset import review
        row=find_image(ident)
        validate(body.boxes)
        if body.label=='positive' and body.status=='approved' and not body.boxes: raise ValueError('陽性資料必須標註矩形框')
        if body.label=='negative' and body.boxes: raise ValueError('陰性資料不可包含病灶框')
        with Image.open(inside(row['image_path'])) as im: orientation=im.getexif().get(274,1);w,h=im.size
        boxes=orient_boxes(body.boxes,{6:8,8:6}.get(orientation,orientation))
        shapes=[{'label':'phlebitis','shape_type':'rectangle','points':[[(x-bw/2)*w,(y-bh/2)*h],[(x+bw/2)*w,(y+bh/2)*h]]} for _,x,y,bw,bh in boxes]
        staged=HOME/'staging'/(uuid.uuid4().hex+'.json')
        write_json(staged,{'imageWidth':w,'imageHeight':h,'shapes':shapes})
        try:
            args=body.model_dump();args.pop('boxes')
            result=review(ident,annotation=str(staged),**args)
            audit('review',{'image_id':ident,'reason':body.reason,'reviewer':body.reviewer,'revision_before':body.revision})
            return result
        finally:staged.unlink(missing_ok=True)

    @app.get('/api/v1/snapshots')
    def snapshots():return [read_json(p) for p in sorted((ROOT/'data/yolo').glob('*/dataset_version.json'),reverse=True)]

    @app.post('/api/v1/snapshots')
    def snapshot(body:SnapshotRequest):
        from src.data.dataset import build
        info=build(**body.model_dump());audit('snapshot',{'version':info['version']});return info

    @app.get('/api/v1/models')
    def models():
        cards=[]
        artifacts=registry.listing()
        for key,value in MODELS.items():
            path=ROOT/'models/pretrained'/(key if key=='dinov2_small' else key+('.pt' if key.startswith('yolo') else '.pth'))
            ready=(path/'model.safetensors').exists() if key=='dinov2_small' else path.exists()
            cards.append({'id':key,**value,'state':'ready' if ready else 'missing_weights','labels':'positive boxes / negative empty labels' if value['task']=='detection' else 'confirmed positive / negative','accuracy':None,'resume':key!='dinov2_small'})
            measured=next((a.get('extra',{}).get('effective') for a in artifacts if a['model']==key and a.get('extra',{}).get('effective')),None)
            cards[-1]['measured']=measured
            cards[-1]['device_requirements']='CUDA GPU or explicitly selected CPU'
            deps=['ultralytics'] if key.startswith('yolo') else ['torchvision'] if key=='efficientnet_b0' else ['transformers','safetensors','scikit-learn']
            cards[-1]['dependencies']={}
            for dep in deps:
                try:cards[-1]['dependencies'][dep]=version(dep)
                except PackageNotFoundError:cards[-1]['dependencies'][dep]=None;cards[-1]['state']='missing_dependencies'
        return cards

    @app.get('/api/v1/experiment-schema')
    def experiment_schema():return Experiment.model_json_schema()

    @app.post('/api/v1/models/{model}/prepare')
    def prepare(model):
        if model not in MODELS:raise ValueError('Unknown model')
        return jobs.enqueue('prepare',{'model':model})

    @app.get('/api/v1/jobs')
    def job_list():return jobs.listing()

    def preflight_experiment(body):
        from src.data.dataset import validate_split
        from src.workbench.adapters import device_name
        split=validate_split(inside(body.dataset))
        if split.get('purpose')=='independent_test':raise ValueError('獨立測試快照不能用於訓練或選模。')
        if split['demo_only'] and not body.demo:raise ValueError('此快照尚未核對個案，請明確選擇研究展示模式。')
        for subset in ('train','val'):
            if {r['label_state'] for r in split['members'][subset]}!={'positive','negative'}:raise ValueError('訓練與驗證折均須有確認的正負樣本。')
        device_name(body.device)
        if body.initial_artifact and registry.get(body.initial_artifact)['model']!=body.model:raise ValueError('初始權重必須屬於相同模型方案。')

    @app.post('/api/v1/experiments')
    def new_experiment(body:Experiment,request:Request):
        preflight_experiment(body)
        return jobs.enqueue('train',body.model_dump(),request.headers.get('idempotency-key'))

    @app.post('/api/v1/experiments/batch')
    def experiment_batch(body:list[Experiment],request:Request):
        if not 1<=len(body)<=5:raise ValueError('每次比較限 1–5 個模型工作。')
        if len({c.model for c in body})!=len(body) or len({c.dataset for c in body})!=1:raise ValueError('比較工作須為不同模型、同一快照與 fold。')
        for cfg in body:preflight_experiment(cfg)
        key=request.headers.get('idempotency-key') or uuid.uuid4().hex
        return [jobs.enqueue('train',cfg.model_dump(),key+':'+str(i)) for i,cfg in enumerate(body)]

    @app.get('/api/v1/jobs/{ident}')
    def job(ident):
        item=jobs.get(ident); log=jobs.folder(ident)/'worker.log'
        item['log']=log.read_text(encoding='utf-8',errors='replace')[-18000:] if log.exists() else ''
        curve=jobs.folder(ident)/'progress.jsonl'
        item['history']=[json.loads(line) for line in curve.read_text(encoding='utf-8').splitlines()[-1000:]] if curve.exists() else []
        return item

    @app.get('/api/v1/jobs/{ident}/events')
    async def job_events(ident,request:Request):
        import asyncio
        async def events():
            while not await request.is_disconnected():
                item=jobs.get(ident)
                yield 'data: '+json.dumps(item,ensure_ascii=False)+'\n\n'
                if item['state'] in jobs.TERMINAL:break
                await asyncio.sleep(1)
        return StreamingResponse(events(),media_type='text/event-stream')

    @app.get('/api/v1/jobs/{ident}/chart')
    def chart(ident):return FileResponse(jobs.folder(ident)/'training/results.png',media_type='image/png')

    @app.post('/api/v1/jobs/{ident}/cancel')
    def cancel(ident):return jobs.cancel(ident)

    @app.get('/api/v1/jobs/{ident}/image')
    def job_image(ident):
        item=jobs.get(ident)
        if item['kind']!='predict' or not item['result'] or item['result'].get('expires',0)<time.time():raise HTTPException(410)
        s=simulation.store()
        try:
            if s.cancelled(item['config']['event_id']): raise HTTPException(410)
        finally:s.close()
        return FileResponse(jobs.folder(ident)/'result.jpg',media_type='image/jpeg')

    @app.get('/api/v1/artifacts')
    def artifacts():return registry.listing()

    @app.post('/api/v1/artifacts/activate')
    def activate(body:SwitchRequest):
        from src.lock import OperationLock
        with OperationLock(): return registry.activate(body.artifact,body.target,body.allow_unevaluated)

    @app.post('/api/v1/artifacts/rollback/{target}')
    def rollback(target):
        if target not in ('local','line'): raise ValueError('Invalid reference')
        from src.lock import OperationLock
        with OperationLock(): return registry.rollback(target)

    @app.post('/api/v1/artifacts/{ident}/evaluate')
    def evaluate(ident,body:dict):
        registry.get(ident)
        from src.data.dataset import validate_split
        validate_split(inside(body['dataset']))
        return jobs.enqueue('evaluate',{'artifact':ident,'dataset':body['dataset'],'device':body.get('device','0')})

    @app.post('/api/v1/artifacts/{ident}/configuration')
    def configure_artifact(ident,body:InferenceConfig,device:str='0'):
        if device not in ('cpu','0'):raise ValueError('Invalid device')
        original=registry.get(ident)
        checked=Experiment(model=original['model'],dataset='configuration_only',inference=body)
        new=registry.register(registry.artifact_path(ident),original['model'],checked.inference.model_dump(),original['experiment'],original['demo_only'],{**original['extra'],'derived_from':ident})
        dataset=original['extra'].get('dataset')
        if dataset:jobs.enqueue('evaluate',{'artifact':new['id'],'dataset':dataset,'device':device})
        audit('inference_configuration',{'before':ident,'after':new['id'],'config':body.model_dump()})
        return new

    @app.get('/api/v1/reports')
    def reports():
        states_path=ROOT/'data/snapshot_states.json';states=read_json(states_path) if states_path.exists() else {}
        return [{**read_json(p),'report_id':p.parent.name,'snapshot_state':states.get(read_json(p).get('snapshot'))} for p in sorted((ROOT/'runs/workbench/evaluations').glob('*/report.json'))]

    @app.get('/api/v1/reports/{ident}/export')
    def report_export(ident):
        jobs.folder(ident)
        audit('export_report',{'report':ident})
        return FileResponse(ROOT/'runs/workbench/evaluations'/ident/'report.json',filename='evaluation-'+ident+'.json')

    @app.get('/api/v1/reports/{ident}/images/{image}')
    def report_image(ident,image):
        jobs.folder(ident)
        if not image.replace('_','').replace('-','').isalnum():raise ValueError('Invalid image ID')
        return FileResponse(ROOT/'runs/workbench/evaluations'/ident/(image+'.jpg'))

    @app.post('/api/v1/reports/oof')
    def oof(body:dict):
        from src.workbench.metrics import aggregate
        paths=[ROOT/'runs/workbench/evaluations'/jobs.folder(i).name/'report.json' for i in body['reports']]
        reports=[read_json(p) for p in paths]
        states=read_json(ROOT/'data/snapshot_states.json') if (ROOT/'data/snapshot_states.json').exists() else {}
        if any(r['snapshot'] in states for r in reports):raise ValueError('撤銷／不適用的資料快照不可彙整為目前效能。')
        return aggregate(reports)

    @app.post('/api/v1/assets')
    async def upload(request:Request,research:bool=False,authorization:str='',purpose:str=''):
        chunks=[];total=0
        async for chunk in request.stream():
            total+=len(chunk)
            if total>10485760:raise HTTPException(413,'圖片上限 10 MB')
            chunks.append(chunk)
        return lifecycle.upload(b''.join(chunks),research=research,authorization=authorization,purpose=purpose)

    @app.get('/api/v1/assets/{ident}/image')
    def asset_image(ident):return FileResponse(lifecycle.asset_path(ident),media_type='image/jpeg')

    @app.post('/api/v1/simulation/events')
    def simulate(body:dict):return simulation.dispatch(body)

    @app.get('/api/v1/simulation/{session}')
    def conversation(session):
        with db() as con: rows=con.execute('SELECT * FROM events WHERE session=? ORDER BY updated',(session,)).fetchall()
        return [{**dict(r),'payload':json.loads(r['payload'])} for r in rows]

    @app.delete('/api/v1/simulation/{session}')
    def reset(session):
        with db() as con:rows=con.execute('SELECT message FROM events WHERE session=?',(session,)).fetchall()
        for row in rows:simulation.dispatch({'session':session,'type':'unsend','message_id':row['message']})
        with db() as con:con.execute('DELETE FROM events WHERE session=?',(session,))
        audit('reset_simulator',{'session':session});return {'reset':True}

    @app.get('/api/v1/cases')
    def cases():
        with db() as con: return [json.loads(r[0]) for r in con.execute('SELECT data FROM cases')]

    @app.post('/api/v1/cases')
    def save_case(body:dict):
        from src.data.labels import validate
        from src.workbench.simulation import validate_expectations
        validate_expectations(body)
        validate(body.get('boxes',[]))
        if body.get('label')=='negative' and body.get('boxes'):raise ValueError('陰性圖片不可有陽性框')
        lifecycle.asset_path(body['asset'])
        if body.get('state') not in ('pending','confirmed'):raise ValueError('Invalid case state')
        if body['state']=='confirmed' and (not body.get('reviewer') or body.get('label') not in ('positive','negative')):raise ValueError('人工確認需要審查者及正負標籤')
        ident=body.get('id') or uuid.uuid4().hex
        if len(ident)!=32 or any(c not in '0123456789abcdef' for c in ident):raise ValueError('Invalid case ID')
        if body.get('expected_status') not in ('suspected','not_detected','quality_rejected','needs_review'):raise ValueError('Invalid expected status')
        with db() as con:
            con.execute('BEGIN IMMEDIATE')
            old=con.execute('SELECT revision,data FROM cases WHERE id=?',(ident,)).fetchone()
            if old and body.get('revision')!=old[0]:raise ValueError('revision conflict')
            rev=(old[0] if old else 0)+1
            body.update(id=ident,revision=rev)
            if old:write_json(HOME/'case_history'/ident/(str(old[0])+'.json'),json.loads(old[1]))
            con.execute('INSERT OR REPLACE INTO cases VALUES(?,?,?)',(ident,rev,json.dumps(body,ensure_ascii=False)))
        audit('case_review',{'id':ident,'revision':rev});return body

    @app.post('/api/v1/regression')
    def regression(body:dict):
        registry.get(body['artifact']);return jobs.enqueue('regression',{'artifact':body['artifact'],'device':body.get('device','0')})

    @app.post('/api/v1/cases/{ident}/promote')
    def promote(ident,body:dict):
        from src.workbench.research import promote
        return promote(ident,independent=bool(body.get('independent',False)),subject_id=body.get('subject_id',''))

    @app.get('/api/v1/independent-test')
    def independent_status():
        path=ROOT/'data/independent_test/manifest.json'
        return read_json(path) if path.exists() else []

    @app.post('/api/v1/independent-test/snapshot')
    def independent_snapshot():
        from src.workbench.research import build_independent
        return build_independent()

    @app.get('/api/v1/retention')
    def retention():return lifecycle.preview_cleanup()

    @app.post('/api/v1/retention/cleanup')
    def cleanup(body:dict):return lifecycle.cleanup(body['ids'])

    @app.post('/api/v1/assets/{ident}/withdraw')
    def withdraw(ident):return lifecycle.withdraw(ident)

    @app.get('/api/v1/audit')
    def audits():
        with db() as con:return [dict(r) for r in con.execute('SELECT * FROM audit ORDER BY id DESC LIMIT 200')]

    @app.get('/api/v1/templates')
    def templates():return flag('templates') or []

    @app.put('/api/v1/templates')
    def save_templates(body:list[dict]):
        for item in body:Experiment(**item['config'])
        audit('save_templates',{'count':len(body)});return flag('templates',body)

    dist=ROOT/'web/dist'
    if dist.exists():app.mount('/',StaticFiles(directory=dist,html=True),name='frontend')
    else:
        @app.get('/')
        def missing_ui():return JSONResponse({'message':'請先執行 scripts/setup-workbench.ps1 建置網頁'},status_code=503)
    return app
