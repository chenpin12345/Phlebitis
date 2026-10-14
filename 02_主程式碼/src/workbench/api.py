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
from urllib.parse import urlparse, unquote

from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from PIL import Image, ImageOps
from src.common import ROOT, read_json, write_json, read_manifest, inside, stamp
from src.common import code_path
from src.workbench.storage import db, audit, digest, HOME, flag, operator
from src.workbench.contracts import MODELS, Experiment, Review, SnapshotRequest, SwitchRequest,InferenceConfig,ClassificationReview,DetectionReview,BatchStageConfirm,experiment_task
from src.workbench import jobs, registry, lifecycle, simulation
from src.workbench import trash, resources, report_views

def create_app(*,testing=False):
    from src.workbench.queries import data_index
    index_monitor=data_index.Monitor(ROOT)
    if testing:
        data_index.rebuild(ROOT)
        from src.workbench.queries.legacy import rebuild as legacy_rebuild
        legacy_rebuild(ROOT)
    manager=jobs.Manager()
    maintenance=trash.Maintenance(secrets.token_urlsafe(32))
    @asynccontextmanager
    async def lifespan(app):
        if not testing:
            maintenance.recover()
            from src.imports.service import recover as recover_imports
            recover_imports(ROOT)
            from src.data.dataset import recover_reviews
            from src.workbench.storage import file_lock
            with file_lock(ROOT/'runtime/data.lock'): recover_reviews(ROOT)
            registry.import_legacy()
            index_monitor.start()
            manager.start()
        yield
        manager.close()
        maintenance.close()
        import_pool.shutdown(wait=True,cancel_futures=True)
        index_monitor.close()
    app=FastAPI(title='Phlebitis local workbench',lifespan=lifespan,docs_url=None,redoc_url=None)
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=['127.0.0.1','localhost']+(['testserver'] if testing else []))
    csrf=secrets.token_urlsafe(32)
    from src.workbench.routes.imports import mount
    import_pool=mount(app,ROOT,csrf)
    from src.workbench.routes.intake import mount as mount_intake
    mount_intake(app)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request,exc):
        return JSONResponse({'detail':[{'loc':e.get('loc',[]),'type':e.get('type','invalid')} for e in exc.errors()]},status_code=422)

    @app.exception_handler(resources.ResourceUnavailable)
    async def resource_error(request,exc):
        return JSONResponse({'detail':str(exc),'resource_state':exc.state,'type':exc.kind,'id':exc.ident},status_code=410 if exc.state=='purged' else 409)

    @app.middleware('http')
    async def browser_boundary(request,call_next):
        request.state.started=time.perf_counter()
        from src.telemetry import current
        measurements={};metric_token=current.set(measurements)
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
        actor=unquote(request.headers.get('x-operator','')).strip()
        if len(actor)>100: return JSONResponse({'detail':'操作者名稱過長'},status_code=400)
        actor_token=operator.set(actor or None)
        try:
            response=await call_next(request)
            if request.method not in ('GET','HEAD','OPTIONS') and response.status_code>=400:
                audit('request_failed',{'path':request.url.path,'method':request.method,'status':response.status_code},outcome='failed')
        finally:
            operator.reset(actor_token)
            current.reset(metric_token)
        response.headers['Server-Timing']='total;dur='+str(round((time.perf_counter()-request.state.started)*1000,2))+''.join(','+key+';dur='+str(round(value['ms'],2)) for key,value in measurements.items())
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

    @app.get('/api/v1/trash',response_model=trash.TrashListResponse)
    def trash_list(type:str='',search:str='',start:str='',end:str='',actor:str='',sort:str='moved',direction:str='desc',page:int=1,size:int=30):
        return trash.list_trash(type,search,start,end,actor,sort,direction,page,size)

    @app.get('/api/v1/trash/operation-history')
    def trash_history(page:int=1,size:int=30,type:str='',action:str=''):return trash.operation_history(page,size,type,action)

    @app.get('/api/v1/trash/operation-history/ids')
    def trash_history_ids(type:str='',action:str=''):return trash.operation_history_ids(type,action)

    @app.post('/api/v1/trash/operation-history/delete')
    def trash_history_delete(body:trash.OperationRecordDelete):return trash.delete_operation_records(body)

    @app.post('/api/v1/trash/previews',response_model=trash.PreviewResponse)
    def trash_preview(body:trash.PreviewRequest):return maintenance.preview(body)

    @app.get('/api/v1/trash/previews/{ident}',response_model=trash.PreviewResponse)
    def trash_preview_status(ident,page:int=1,size:int=100):return maintenance.get_preview(ident,page,size)

    @app.post('/api/v1/trash/operations',response_model=trash.OperationResponse)
    def trash_commit(body:trash.CommitRequest,request:Request):return maintenance.commit(body,request.headers.get('idempotency-key'))

    @app.get('/api/v1/trash/operations/{ident}',response_model=trash.OperationResponse)
    def trash_operation(ident,page:int=1,size:int=100):return trash.operation(ident,page,size)

    @app.post('/api/v1/trash/operations/{ident}/retry')
    def trash_retry(ident):return maintenance.retry(ident)

    @app.post('/api/v1/trash/capacity')
    def trash_capacity(body:list[trash.Target]):
        if not 1<=len(body)<=100:raise ValueError('每次限 1–100 個明確項目')
        return maintenance.capacity(body)

    @app.get('/api/v1/trash/{kind}/{ident}')
    def trash_detail(kind,ident):
        item=resources.record(kind,ident)
        if item['state']=='active':raise ValueError('此資源不在垃圾桶')
        from src.workbench.views import redact
        return redact(item)

    @app.get('/api/v1/references')
    def references():return trash.reference_chains()

    @app.post('/api/v1/references/{target}/preview')
    def reference_preview(target,body:trash.ReferenceRequest):return maintenance.reference_preview(target,body)

    @app.post('/api/v1/references/commit')
    def reference_commit(body:trash.CommitRequest):return maintenance.reference_commit(body)

    @app.get('/api/v1/reports-query')
    def reports_query(model:str='',page:int=1,size:int=30):return report_views.query(model,page,size)

    @app.get('/api/v1/reports/{ident}/samples')
    def report_samples(ident,page:int=1,size:int=30,image:str=''):return report_views.samples(ident,page,size,image)

    @app.get('/api/v1/reports/{ident}/detail')
    def report_detail(ident):
        report=next((r for r in report_views.listing() if r['report_id']==ident),None)
        if report is None or report.get('source_model_state')=='purged':raise FileNotFoundError(ident)
        return {k:v for k,v in report.items() if k!='samples'}

    @app.get('/api/v1/reports/{ident}/comparison/{image}')
    def report_comparison(ident,image,model:str=''):
        current=report_views.get(ident)
        if image not in {s['image_id'] for s in current.get('samples',[])}:raise ValueError('圖片不屬於選取報告')
        result=[]
        for r in report_views.listing():
            if model and r.get('model')!=model:continue
            if r.get('source_model_state')=='purged':continue
            # Different tasks or label schemes are never placed side by side.
            if r.get('label_scheme','binary_v1')!=current.get('label_scheme','binary_v1') or r.get('task')!=current.get('task'):continue
            if r['snapshot']!=current['snapshot'] or r['fold']!=current['fold'] or r['metrics']['member_hash']!=current['metrics']['member_hash'] or not r['metrics']['complete'] or r.get('snapshot_state'):continue
            sample=next((s for s in r['samples'] if s['image_id']==image),None)
            if sample:result.append({k:v for k,v in {**r,'sample':sample}.items() if k!='samples'})
        return result

    @app.get('/api/v1/overview')
    def overview():
        return {**data_index.overview(ROOT),'jobs':jobs.summaries()['items'],'references':{t:read_json(registry.REFS/(t+'.json')) if (registry.REFS/(t+'.json')).exists() else None for t in ('local','line')},'artifacts':registry.count_active()}

    @app.post('/api/v1/data-index/rebuild')
    def rebuild_index():
        data_index.invalidate(ROOT);data_index.request_rebuild(ROOT)
        return data_index.state(ROOT)

    @app.get('/api/v1/data-index')
    def index_status():return data_index.freshness(ROOT)

    @app.get('/api/v1/doctor')
    def doctor():
        packages={}; errors=[]; cuda=gpu=vram=free=compute_available=None
        from src.lock import OperationLock
        try:
            with OperationLock():compute_available=True
        except RuntimeError:compute_available=False
        except OSError:errors.append('無法檢查運算鎖狀態')
        for name in ['torch','torchvision','ultralytics','transformers','safetensors','scikit-learn','fastapi','psutil']:
            try:packages[name]=version(name)
            except PackageNotFoundError:packages[name]=None
        try:
            import torch
            cuda=torch.cuda.is_available()
            if cuda: gpu=torch.cuda.get_device_name(0);vram=torch.cuda.get_device_properties(0).total_memory
        except Exception as exc: errors.append('GPU 檢查失敗：'+str(exc))
        try: free=round(shutil.disk_usage(ROOT).free/1024**3,1)
        except OSError as exc: errors.append('磁碟檢查失敗：'+str(exc))
        return {'packages':packages,'cuda':cuda,'gpu':gpu,'vram':vram,'free_disk_gb':free,'compute_available':compute_available,'check_errors':errors,'frontend_ready':code_path('web/dist/index.html',ROOT).exists(),'ports':{'workbench':8765,'line':8000},'line_credentials_required':False,'repair':'執行 scripts/setup-workbench.ps1 安裝專案依賴；GPU 不可用時明確選擇 CPU。'}

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
    def data():
        from src.data.tasks import row_revision
        return [{**r,'revision':row_revision(r)} for r in read_manifest()]

    @app.get('/api/v1/data-query')
    def data_query(view:str='pending_review',reviewer:str='',decision:str='',start:str='',end:str='',page:int=1,size:int=30,task:str=''):
        return data_index.query(ROOT,view,reviewer,decision,start,end,page,size,task=task)

    @app.get('/api/v1/data-area')
    def data_area(area:str,view:str='pending',label:str='',source:str='',reviewer:str='',page:int=1,size:int=30):
        return data_index.area_query(ROOT,area,view,label,source,reviewer,page,size)

    @app.post('/api/v1/data/source-rules/apply')
    def apply_source_rules():
        """Re-apply the authorized filename rule (idempotent; human results are kept)."""
        from src.data.source_rules import apply_authorized_rules
        from src.workbench.storage import dataset_lock
        report=apply_authorized_rules(ROOT)
        data_index.rebuild(ROOT)
        from src.workbench.queries.images import clear
        clear(ROOT)
        audit('apply_source_rules',{'summary':report['summary']})
        return {'summary':report['summary'],'items':report['items']}

    @app.get('/api/v1/label-schemes')
    def label_schemes():
        from src.data.tasks import SCHEMES,TASKS,TASK_NAMES,TASK_SCHEME,REASONS
        return {'tasks':[{'id':t,'name':TASK_NAMES[t],'scheme':TASK_SCHEME[t]} for t in TASKS],'schemes':SCHEMES,'reasons':REASONS}

    @app.get('/api/v1/audit-query')
    def audit_query(actor:str='',action:str='',related:str='',outcome:str='',start:str='',end:str='',page:int=1,size:int=30,snapshot:str=''):
        from src.workbench.views import query_audit
        with db() as con: return query_audit(con,actor,action,related,outcome,start,end,page,size,int(snapshot) if snapshot else None)

    @app.get('/api/v1/audit-query/ids')
    def audit_query_ids(actor:str='',action:str='',related:str='',outcome:str='',start:str='',end:str='',snapshot:str=''):
        from src.workbench.views import query_audit
        with db() as con: return query_audit(con,actor,action,related,outcome,start,end,1,30,int(snapshot) if snapshot else None,ids_only=True)

    @app.get('/api/v1/jobs/{ident}/curves')
    def job_curves(ident):
        from src.workbench.presentation import curves
        return curves(ident)

    @app.get('/api/v1/curve-sources')
    def curve_sources():
        from src.workbench.presentation import curve_sources
        return curve_sources(ROOT)

    @app.get('/api/v1/curve-history')
    def curve_history(source:str):
        from src.workbench.presentation import curve_source
        return curve_source(source,ROOT)

    @app.get('/api/v1/curve-image')
    def curve_image(source:str):
        from src.workbench.presentation import curve_image
        return FileResponse(curve_image(source,ROOT),media_type='image/png')

    @app.get('/api/v1/artifacts/{ident}/detail')
    def artifact_detail(ident):
        from src.workbench.presentation import artifact_detail
        return artifact_detail(ident)

    @app.get('/api/v1/artifacts/{ident}/settings')
    def artifact_settings(ident,key:str):
        from src.workbench.presentation import file_settings
        return file_settings(ident,key)

    @app.get('/api/v1/artifacts/{ident}/export')
    def artifact_export(ident):
        from src.workbench.presentation import artifact_detail
        return JSONResponse(artifact_detail(ident),headers={'Content-Disposition':'attachment; filename="model-settings.json"'})

    @app.get('/api/v1/artifacts/{ident}/file')
    def artifact_download(ident,key:str):
        from src.workbench.presentation import artifact_file,file_settings
        path=artifact_file(ident,key)
        if path.suffix.lower() in ('.json','.yaml','.yml'):
            return JSONResponse(file_settings(ident,key),headers={'Content-Disposition':'attachment; filename="settings.json"'})
        return FileResponse(path,filename=path.name)

    def find_image(ident):
        row=next((r for r in read_manifest() if r['image_id']==ident),None)
        if row is None: raise HTTPException(404)
        return row

    @app.get('/api/v1/data/{ident}/image')
    def data_image(ident,thumbnail:bool=False):
        from src.workbench.queries.images import render
        return Response(render(ROOT,find_image(ident),thumbnail),media_type='image/jpeg')

    @app.get('/api/v1/data/{ident}/annotation')
    def annotation(ident,area:str=''):
        if area not in ('','cls','det'):raise ValueError('無效的工作區')
        full=annotation_detail(ident)
        if not area:return full
        # Each work area only receives its own fields; boxes never reach the classification area.
        labels=full['labels'];state=labels['cls_state' if area=='cls' else 'det_state']
        keep=('binary','stage','stage_source','quality','usage') if area=='cls' else ('detection','detection_source','usage')
        tasks_keep=('binary_classification','stage_classification') if area=='cls' else ('detection',)
        history=[h for h in full['history'] if {'classification':'cls','detection':'det'}.get(h.get('task'),area)==area]
        evidence=[e for e in full['evidence'] if {'classification':'cls','stage_classification':'cls','detection':'det'}.get(e.get('task'),area)==area]
        common={'row':{k:v for k,v in full['row'].items() if k in ('image_id','status','subject_id','group_verified','original_paths','quality_state','reviewer','updated_at')},
                'revision':full['revision'],'area':area,'state':state,'labels':{k:labels[k] for k in keep},'tasks':{k:v for k,v in (full['tasks'] or {}).items() if k in tasks_keep} if full['tasks'] else None,
                'index_current':full['index_current'],'display_name':full['display_name'],'aliases':full['aliases'],'display_conflict':full['display_conflict'],
                'name_variants':full['name_variants'],'history':history,'evidence':evidence,'original_size':full['original_size'],
                'rule_applied':any(h.get('source')=='authorized_filename_rule' for h in history)}
        if area=='cls':return {**common,'stage_suggestion':full['stage_suggestion']}
        return {**common,'boxes':full['boxes'],'import_candidates':full['import_candidates'],'coordinate_warning':full['coordinate_warning'],'orientation':full['orientation'],'coordinate_system':full['coordinate_system']}

    def annotation_detail(ident):
        from src.data.labels import orient_boxes,from_labelme
        row=find_image(ident)
        with Image.open(inside(row['image_path'])) as im: orientation=im.getexif().get(274,1); size=im.size
        boxes=[]; diagnostic=None
        if row['yolo_path'] and inside(row['yolo_path']).exists(): boxes=[list(map(float,line.split())) for line in inside(row['yolo_path']).read_text().splitlines() if line.strip()]
        elif row['annotation_path']:
            try: boxes=from_labelme(read_json(inside(row['annotation_path'])),size)
            except ValueError as exc: diagnostic=str(exc)
        history=[read_json(p) for p in sorted((ROOT/'data/reviews').glob('*_'+ident+'.json'))]
        from src.imports.service import candidate_annotations
        from src.data import tasks as task_rules, sources, evidence
        indexed=data_index.indexed_row(ROOT,ident)
        return {'import_candidates':candidate_annotations(ROOT,ident,size,orientation),'row':row,'revision':task_rules.row_revision(row),'boxes':orient_boxes(boxes,orientation),'orientation':orientation,'original_size':size,'coordinate_system':'EXIF-corrected normalized YOLO xywh','history':history,'coordinate_warning':diagnostic,
                'labels':task_rules.effective(row),'tasks':(indexed or {}).get('tasks'),'index_current':bool(indexed and indexed.get('revision')==task_rules.row_revision(row)),
                'stage_suggestion':evidence.suggestion(ident,row,ROOT),'evidence':evidence.read(ident,ROOT)['entries'],**sources.lookup(ident,root=ROOT),
                'name_variants':sources.variants(read_manifest(),sources.load(ROOT)).get(ident,[])}

    def staged_annotation(row,body_boxes):
        from src.data.labels import orient_boxes,validate
        validate(body_boxes)
        with Image.open(inside(row['image_path'])) as im: orientation=im.getexif().get(274,1);w,h=im.size
        boxes=orient_boxes(body_boxes,{6:8,8:6}.get(orientation,orientation))
        shapes=[{'label':'phlebitis','shape_type':'rectangle','points':[[(x-bw/2)*w,(y-bh/2)*h],[(x+bw/2)*w,(y+bh/2)*h]]} for _,x,y,bw,bh in boxes]
        staged=HOME/'staging'/(uuid.uuid4().hex+'.json')
        write_json(staged,{'imageWidth':w,'imageHeight':h,'shapes':shapes})
        return staged

    def after_review(ident,body,task):
        data_index.rebuild(ROOT)
        from src.workbench.queries.images import clear
        clear(ROOT)
        audit('review',{'image_id':ident,'task':task,'reason':body.reason,'reviewer':body.reviewer,'revision_before':body.revision},actor=body.reviewer)

    @app.put('/api/v1/data/{ident}')
    def save_review(ident,body:Review):
        """Legacy single form (older clients/CLI parity). New pages use the task endpoints."""
        from src.data.dataset import review
        row=find_image(ident)
        existing=annotation(ident)
        if existing['coordinate_warning'] and body.coordinate_resolution!='redraw': raise ValueError('舊標註座標需人工確認；請選擇在正向預覽重新標註，原始檔仍保留。')
        if body.label=='negative' and body.boxes: raise ValueError('陰性資料不可包含病灶框')
        staged=staged_annotation(row,body.boxes)
        try:
            args=body.model_dump();args.pop('boxes')
            result=review(ident,annotation=str(staged),**args)
            after_review(ident,body,'legacy')
            return result
        finally:staged.unlink(missing_ok=True)

    @app.put('/api/v1/data/{ident}/classification')
    def save_classification(ident,body:ClassificationReview):
        from src.data.dataset import review
        from src.workbench.views import DECISIONS
        find_image(ident)
        result=review(ident,revision=body.revision,task='classification',decision=body.decision,label=body.label,stage=body.stage,quality=body.quality,
                      reviewer=body.reviewer,reason=body.reason,subject_id=body.subject_id,clear_subject=body.clear_subject,category=body.category)
        after_review(ident,body,'classification');return result

    @app.put('/api/v1/data/{ident}/detection')
    def save_detection(ident,body:DetectionReview):
        from src.data.dataset import review
        from src.workbench.views import DECISIONS
        row=find_image(ident)
        existing=annotation(ident)
        if existing['coordinate_warning'] and body.detection=='boxes' and body.coordinate_resolution!='redraw': raise ValueError('舊標註座標需人工確認；請選擇在正向預覽重新標註，原始檔仍保留。')
        if body.detection!='boxes' and body.boxes:raise ValueError('只有「已確認病灶框」可以送出框選')
        if body.detection=='boxes' and not body.boxes:raise ValueError('請至少畫一個病灶框')
        staged=staged_annotation(row,body.boxes)
        try:
            result=review(ident,revision=body.revision,task='detection',decision=body.decision,detection=body.detection,
                          annotation=str(staged) if body.detection!='not_annotated' else '',reviewer=body.reviewer,reason=body.reason,category=body.category,coordinate_resolution=body.coordinate_resolution,
                          subject_id='')
            after_review(ident,body,'detection');return result
        finally:staged.unlink(missing_ok=True)

    @app.post('/api/v1/data/stage-confirm')
    def confirm_stages(body:BatchStageConfirm):
        """Human confirmation of rule-prefilled stages; never applied without this call."""
        from src.data.dataset import review
        from src.data import evidence
        from src.data.tasks import STAGE_TO_BINARY
        results=[]
        for item in body.items:
            ident=str(item.get('image_id','')); approve=bool(item.get('approve',False))
            try:
                row=find_image(ident);hint=evidence.suggestion(ident,row,ROOT)
                if not hint:raise ValueError('沒有可確認的規則分期')
                if hint['conflict']:raise ValueError('規則分期有衝突，請個別審查：'+'；'.join(hint['conflict_reasons']))
                if item.get('stage')!=hint['value']:raise ValueError('送出的分期與規則預填值不同，請個別審查')
                from src.data.tasks import area_state
                if area_state(row,'cls')=='excluded':raise ValueError('已排除的照片需個別審查')
                decision='approve' if approve or area_state(row,'cls')=='confirmed' else 'needs_changes'
                review(ident,revision=item.get('revision'),task='classification',decision=decision,label=STAGE_TO_BINARY[hint['value']],stage=hint['value'],
                       reviewer=body.reviewer,reason=body.reason+'（確認規則 '+str(hint['rule'])+' 預填分期）')
                results.append({'image_id':ident,'ok':True})
            except (ValueError,RuntimeError,HTTPException) as exc:
                results.append({'image_id':ident,'ok':False,'error':getattr(exc,'detail',None) or str(exc)})
        data_index.rebuild(ROOT)
        from src.workbench.queries.images import clear
        clear(ROOT)
        audit('stage_confirm',{'reviewer':body.reviewer,'confirmed':sum(r['ok'] for r in results),'failed':sum(not r['ok'] for r in results)},actor=body.reviewer)
        return {'results':results}

    @app.get('/api/v1/snapshots')
    def snapshots():return [read_json(p) for p in sorted((ROOT/'data/yolo').glob('*/dataset_version.json'),reverse=True)]

    @app.get('/api/v1/snapshot-options')
    def snapshot_options():
        from src.workbench.queries.files import cached_many
        rows=cached_many(sorted((ROOT/'data/yolo').glob('*/dataset_version.json'),reverse=True),ROOT)
        states_path=ROOT/'data/snapshot_states.json'
        states=read_json(states_path) if states_path.exists() else {}
        def fold_view(fold):
            from collections import Counter
            members=fold.get('members',{})
            return {**{a:b for a,b in fold.items() if a!='members'},'counts':{name:len(m) for name,m in members.items()},
                    'class_counts':{name:dict(Counter(x.get('target') or x.get('label_state') for x in m if isinstance(x,dict))) for name,m in members.items()}}
        # Snapshots moved to the trash (or purged) are no longer listed anywhere.
        removed={k for k,v in resources.states('snapshot').items() if v!='active'}
        rows=[row for row in rows if row.get('version') not in removed]
        return [{**{k:([fold_view(f) for f in v] if k=='folds' else v) for k,v in row.items() if k in ('version','name','purpose','folds','demo_only','created_at','task','label_scheme','class_mapping','schema_version')},
                 'task':row.get('task'),'label_scheme':row.get('label_scheme') or 'binary_v1','legacy':row.get('schema_version',2)<3,
                 # Withdrawn/superseded snapshots are refused by training; the UI hides them from new experiments.
                 'state':('withdrawn' if row.get('withdrawn') else (states.get(row['version']) or {}).get('status')),'state_reason':(states.get(row['version']) or {}).get('reason')} for row in rows]

    @app.post('/api/v1/snapshots')
    def snapshot(body:SnapshotRequest):
        from src.data.dataset import build
        info=build(**body.model_dump());audit('snapshot',{'version':info['version']});return info

    @app.get('/api/v1/models')
    def models():
        cards=[]
        artifacts=registry.metadata_listing()
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

    @app.get('/api/v1/jobs-query')
    def jobs_query(page:int=1,size:int=30,kind:str=''):return jobs.summaries(page,size,kind)

    @app.get('/api/v1/jobs-query/ids')
    def jobs_query_ids(kind:str=''):return jobs.summary_ids(kind)

    @app.get('/api/v1/jobs')
    def job_list():return jobs.listing()

    def preflight_experiment(body):
        from src.data.dataset import validate_split
        from src.workbench.adapters import device_name
        from src.workbench.adapters import check_split_task
        split=validate_split(inside(body.dataset))
        if split.get('purpose')=='independent_test':raise ValueError('獨立測試快照不能用於訓練或選模。')
        if split['demo_only'] and not body.demo:raise ValueError('此快照尚未核對個案，請明確選擇研究展示模式。')
        check_split_task(split,experiment_task(body.model,body.task))
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
    def job(ident,details:bool=True):
        state=resources.record('job',ident)['state']
        if state=='purged':raise resources.ResourceUnavailable('job',ident,state)
        item=jobs.get(ident); log=jobs.folder(ident)/'worker.log'
        item['resource_state']=state
        item['log']=''
        if details and log.exists():
            with log.open('rb') as stream:
                stream.seek(max(0,log.stat().st_size-72000));item['log']=stream.read(72000).decode('utf-8',errors='replace')[-18000:]
        curve=jobs.folder(ident)/'progress.jsonl'
        from src.workbench.presentation import history
        item['history']=history(curve)[-1000:] if details else []
        from src.workbench.views import redact
        return redact(item)

    @app.get('/api/v1/jobs/{ident}/log')
    def job_log(ident,offset:int=0,limit:int=65536):
        if offset<0 or not 1<=limit<=262144:raise ValueError('無效的日誌範圍')
        if resources.record('job',ident)['state']=='purged':raise resources.ResourceUnavailable('job',ident,'purged')
        path=jobs.folder(ident)/'worker.log'
        if not path.exists():return {'text':'','next_offset':0,'reset':False,'eof':True}
        size=path.stat().st_size;reset=offset>size;offset=0 if reset else offset
        with path.open('rb') as stream:stream.seek(offset);content=stream.read(limit);end=stream.tell()
        return {'text':content.decode('utf8',errors='replace'),'next_offset':end,'reset':reset,'eof':end>=size}

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
    @resources.guarded
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
        return report_views.listing()

    @app.get('/api/v1/reports/{ident}/export')
    def report_export(ident):
        jobs.folder(ident)
        audit('export_report',{'report':ident})
        from src.workbench.views import redact
        return JSONResponse(redact(report_views.get(ident)),headers={'Content-Disposition':'attachment; filename="evaluation-'+ident+'.json"'})

    @app.get('/api/v1/reports/{ident}/images/{image}')
    def report_image(ident,image):
        return FileResponse(report_views.image_path(ident,image),media_type='image/jpeg')

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
        simulation.clear_session(session)
        audit('reset_simulator',{'session':session});return {'reset':True}

    @app.get('/api/v1/cases')
    def cases():
        with db() as con: return [json.loads(r[0]) for r in con.execute('SELECT data FROM cases')]

    @app.get('/api/v1/cases-query')
    def cases_query(page:int=1,size:int=30):
        from src.workbench.queries.records import page_records
        return page_records('cases',page,size)

    @app.get('/api/v1/simulation-query')
    def simulation_query(session:str='demo-1',page:int=1,size:int=30):
        from src.workbench.queries.records import page_records
        return page_records('events',page,size,session)

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
            con.execute('INSERT OR REPLACE INTO cases(id,revision,data) VALUES(?,?,?)',(ident,rev,json.dumps(body,ensure_ascii=False)))
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
        with db() as con:return [dict(r) for r in con.execute("SELECT * FROM audit WHERE NOT EXISTS (SELECT 1 FROM resource_lifecycle r WHERE r.type='audit' AND r.id=CAST(audit.id AS TEXT) AND r.state!='active') ORDER BY id DESC LIMIT 200")]

    @app.get('/api/v1/templates')
    def templates():return flag('templates') or []

    @app.put('/api/v1/templates')
    def save_templates(body:list[dict]):
        for item in body:Experiment(**item['config'])
        audit('save_templates',{'count':len(body)});return flag('templates',body)

    dist=code_path('web/dist',ROOT)
    if dist.exists():app.mount('/',StaticFiles(directory=dist,html=True),name='frontend')
    else:
        @app.get('/')
        def missing_ui():return JSONResponse({'message':'請先執行 scripts/setup-workbench.ps1 建置網頁'},status_code=503)
    return app
