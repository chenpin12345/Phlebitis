"""Staged inbox imports. Never executes package code or removes source files."""
from __future__ import annotations
import json
import os
import shutil
import time
import uuid
from pathlib import Path
from PIL import Image,UnidentifiedImageError
from src.common import inside,read_json,write_json,read_manifest,write_manifest,sha256,stamp
from src.workbench.storage import db,digest,file_lock,dataset_lock
from src.workbench.queries.data_index import stat_key

KINDS={'photos','models'}
MAX_FILES=1000
MAX_PHOTO=50*1024**2
MAX_PIXELS=25_000_000

def store(root):return db(root/'runtime/workbench')

def safe(path,root):
    """No links/reparse points at any component, including inbox itself."""
    path=Path(path)
    lexical=path.absolute()
    if not lexical.is_relative_to(root.absolute()):raise ValueError('路徑超出匯入管理範圍')
    current=root
    for part in lexical.relative_to(root.absolute()).parts:
        current=current/part
        if current.exists():
            st=current.lstat()
            if current.is_symlink() or getattr(st,'st_file_attributes',0)&1024:raise ValueError('不接受符號連結、junction 或 reparse point')
            if current.is_file() and st.st_nlink!=1:raise ValueError('不接受共享硬連結')
    return inside(path,root)

def batch_path(root,kind,batch):
    if kind not in KINDS or not batch or batch in ('.','..') or any(c in batch for c in '/\\:'):raise ValueError('無效的匯入批次')
    return safe(root/'inbox'/kind/batch,root)

def batches(root,kind):
    if kind not in KINDS:raise ValueError('無效的匯入類型')
    base=safe(root/'inbox'/kind,root)
    return {'items':[p.name for p in sorted(base.iterdir()) if p.is_dir() and not p.is_symlink() and not getattr(p,'is_junction',lambda:False)()] if base.exists() else []}

def save(root,item):
    item['updated']=time.time()
    with store(root) as con:
        con.execute('INSERT INTO imports(id,kind,batch,state,created,updated,session,idem,payload) VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET state=excluded.state,updated=excluded.updated,idem=excluded.idem,payload=excluded.payload',(item['id'],item['kind'],item['batch'],item['state'],item['created'],item['updated'],item['session'],item.get('idem'),json.dumps(item,ensure_ascii=False,allow_nan=False)))

def load(root,ident):
    if len(ident)!=32 or any(c not in '0123456789abcdef' for c in ident):raise ValueError('無效的匯入識別碼')
    with store(root) as con:r=con.execute('SELECT payload FROM imports WHERE id=?',(ident,)).fetchone()
    if not r:raise FileNotFoundError(ident)
    return json.loads(r[0])

def public(item,page=1,size=30):
    if page<1 or not 1<=size<=100:raise ValueError('無效的分頁')
    from src.workbench.views import redact
    result={k:v for k,v in item.items() if k not in ('session','idem','items')}
    result.update(items=item.get('items',[])[(page-1)*size:page*size],total=len(item.get('items',[])),page=page,size=size)
    return redact(result)

def inspect_file(path,root):
    safe(path,root);before=stat_key(path)
    if before is None:raise ValueError('來源檔案不存在')
    from src.workbench.managed_files import opened,identity
    with opened(path,root) as (stream,_):value=identity(stream)['sha256']
    if stat_key(path)!=before:raise ValueError('來源正在變更，請等複製完成後重新掃描')
    return {'source':path.relative_to(root).as_posix(),'sha256':value,'identity':before,'bytes':before[2]}

def photo_items(root,base):
    rows=read_manifest(root);known={r['sha256']:r['image_id'] for r in rows};names={Path(r['image_path']).name for r in rows}
    files=[]
    for directory,dirs,names_here in os.walk(base,followlinks=False):
        safe(Path(directory),root)
        for d in dirs:safe(Path(directory)/d,root)
        for name in sorted(names_here):
            files.append(Path(directory)/name)
            if len(files)>MAX_FILES:raise ValueError('批次超過 1000 個檔案，請分批匯入')
    images={p.with_suffix('') for p in files if p.suffix.lower() in ('.jpg','.jpeg','.png','.webp')}
    output=[]
    for path in files:
        if path.suffix.lower() in ('.json','.txt') and path.with_suffix('') in images:continue
        item={'name':path.relative_to(base).as_posix(),'action':'reject','reason':'不支援的檔案格式'}
        try:
            if path.suffix.lower() not in ('.jpg','.jpeg','.png','.webp'):raise ValueError('不支援的檔案格式')
            if path.stat().st_size>MAX_PHOTO:raise ValueError('單張圖片超過 50 MiB')
            item.update(inspect_file(path,root))
            with Image.open(path) as im:
                if im.format not in ('JPEG','PNG','WEBP') or im.width*im.height>MAX_PIXELS or min(im.size)<64:raise ValueError('圖片格式或尺寸不合規則（64 px 至 2500 萬像素）')
                size=im.size;orientation=im.getexif().get(274,1);im.load()
            if stat_key(path)!=item['identity']:raise ValueError('圖片仍在複製或已變更，請完成複製後重新掃描')
            item.update(size=list(size),orientation=orientation,name_conflict=path.name in names)
            names.add(path.name)
            if item['sha256'] in known:
                item.update(action='skip',reason='相同內容已存在',existing_image_id=known[item['sha256']]);output.append(item);continue
            annotations=[]
            for suffix in ('.json','.txt'):
                annotation=path.with_suffix(suffix)
                if not annotation.exists():continue
                if annotation.stat().st_size>1048576:raise ValueError('標註檔超過 1 MiB')
                info=inspect_file(annotation,root)
                try:
                    from src.data.labels import from_labelme,validate
                    if suffix=='.json':
                        payload=read_json(annotation)
                        if payload.get('imageData'):raise ValueError('標註包含嵌入圖片，請移除 imageData 後再匯入')
                        image_path=payload.get('imagePath','')
                        if image_path and (Path(image_path).name!=image_path or image_path!=path.name):raise ValueError('標註不可引用其他路徑')
                        from_labelme(payload,size)
                    else:validate([list(map(float,line.split())) for line in annotation.read_text(encoding='utf8').splitlines() if line.strip()])
                    info['state']='needs_confirmation' if orientation!=1 else 'provisional'
                except (ValueError,KeyError,TypeError) as exc:info.update(state='invalid',reason=str(exc))
                annotations.append(info)
            ident='import_'+uuid.uuid4().hex[:20];known[item['sha256']]=ident
            item.update(action='add',reason='待人工審查，標籤與分組保持未知',image_id=ident,annotations=annotations)
        except UnidentifiedImageError:item['reason']='無法解碼圖片；檔案可能損壞或內容與圖片格式不符'
        except (OSError,ValueError,Image.DecompressionBombError) as exc:item['reason']=str(exc).replace(str(root),'專案')
        output.append(item)
    return output

def model_item(root,base):
    manifest=safe(base/'package.json',root)
    if not manifest.is_file():raise ValueError('缺少 package.json；未知 .pt 不會被反序列化')
    if manifest.stat().st_size>1048576:raise ValueError('模型清單過大')
    package=read_json(manifest)
    if package.get('schema_version')!=1 or package.get('purpose') not in ('inference','base','checkpoint'):raise ValueError('不支援的模型包版本或用途')
    from src.workbench.contracts import MODELS,InferenceConfig
    if package.get('model') not in MODELS:raise ValueError('未支援的 adapter')
    files=package.get('files')
    if not isinstance(files,dict) or not files or len(files)>100:raise ValueError('缺少模型檔案清單或超過 100 個檔案')
    details=[]
    for name,expected in files.items():
        if not isinstance(name,str) or name.startswith(('/','\\')) or ':' in name or '..' in Path(name).parts:raise ValueError('模型檔案路徑越界')
        path=safe(base/name,root)
        if not path.is_relative_to(base) or path.suffix.lower() not in ('.pt','.pth','.safetensors','.npz','.json','.txt'):raise ValueError('不接受腳本或自訂載入碼')
        info=inspect_file(path,root)
        if info['sha256']!=expected:raise ValueError('模型內容不符合清單校驗值')
        details.append(info)
    # The package's own hash declarations are not a trust authority.
    source=package.get('source',{});purpose=package['purpose'];proof=None
    if source.get('type')=='project_artifact':
        from src.workbench import registry
        proof=registry.get(source.get('id',''))
        if proof['model']!=package['model'] or proof['files']!=files:raise ValueError('模型包與本專案登錄產物不相符')
        if purpose!='inference':raise ValueError('推論產物不能冒充基礎權重或續訓 checkpoint')
        policy=InferenceConfig(**package.get('config',{})).model_dump()
        if policy!=proof['config']:raise ValueError('匯入設定必須符合可追溯來源；登錄後可另建設定版本')
    elif source.get('type')=='official' and purpose=='base':
        # Trust only server-managed preparation receipts, never a receipt in inbox.
        provenance=root/'runtime/imports/trusted-official'/ (package['model']+'.json')
        if not provenance.exists():raise ValueError('尚無官方可信摘要，請先在模型目錄執行官方權重準備工作')
        proof=read_json(provenance)
        if proof.get('source')!=MODELS[package['model']]['source'] or proof.get('files')!=files:raise ValueError('未符合伺服器核對的官方權重摘要')
    elif source.get('type')=='project_job' and purpose=='checkpoint':
        if package['model']=='dinov2_small':raise ValueError('DINO 不支援 checkpoint 續訓')
        from src.workbench import jobs,resources
        resources.require_active('job',source.get('id',''));job=jobs.get(source['id'])
        if job['state'] not in jobs.TERMINAL or job['config'].get('model')!=package['model']:raise ValueError('來源工作不適用或仍在執行')
        from src.data.dataset import validate_split
        validate_split(inside(job['config']['dataset'],root),root)
        for name,expected in files.items():
            original=inside(jobs.folder(job['id'])/name,jobs.folder(job['id']))
            if not original.is_file() or sha256(original)!=expected:raise ValueError('Checkpoint 不符合來源工作')
        required={'experiment.json','effective.json'}|({'training/weights/last.pt','training/weights/best.pt'} if package['model'].startswith('yolo') else {'last.pt','artifact/model.pt'})
        if not required<=set(files):raise ValueError('Checkpoint 缺少完整續訓產物：'+', '.join(sorted(required-set(files))))
        proof={'job':job['id'],'config':job['config']}
    else:raise ValueError('來源未確認；模型保持隔離，不載入未知權重')
    return {'action':'add','name':base.name,'task':MODELS[package['model']]['task'],'reason':'來源與內容已核對；不自動啟用','package':package,'proof':proof,'files':details,'metadata':inspect_file(manifest,root),'bytes':sum(i['bytes'] for i in details)}

def preview(root,kind,batch,session='cli',ident=None,actor=None):
    ident=ident or uuid.uuid4().hex
    with file_lock(root/'runtime/imports'/(ident+'.lock')):
        return _preview(root,kind,batch,session,ident,actor)

def _preview(root,kind,batch,session,ident,actor):
    from src.workbench.storage import operator
    item={'id':ident or uuid.uuid4().hex,'kind':kind,'batch':batch,'created':time.time(),'session':session,'state':'scanning','items':[]}
    item['operator']=actor or operator.get()
    save(root,item)
    try:
        base=batch_path(root,kind,batch)
        if not base.is_dir():raise FileNotFoundError(base)
        item['items']=photo_items(root,base) if kind=='photos' else [model_item(root,base)]
        item['bytes']=sum(i.get('bytes',0) for i in item['items']);item['additional_bytes']=sum(i.get('bytes',0)+sum(a['bytes'] for a in i.get('annotations',[])) for i in item['items'] if i['action']=='add')
        item['required_free_bytes']=item['additional_bytes']*2+64*1024**2
        item['source_retained']=True;item['state']='ready';item['expires']=time.time()+300
    except Exception as exc:item.update(state='failed',error=str(exc))
    save(root,item);return item

def recheck(info,root):
    path=safe(root/info['source'],root)
    from src.workbench.managed_files import inspect
    if stat_key(path)!=info['identity'] or inspect(path,root)['sha256']!=info['sha256']:raise ValueError('來源於預覽後變更，請重新掃描')
    return path

def commit(root,ident,idem,session='cli',retry=False):
    if not idem or len(idem)>200:raise ValueError('必須提供有效的冪等鍵')
    item=load(root,ident)
    if item['session']!=session:raise ValueError('匯入預覽不屬於目前管理會話')
    with file_lock(root/'runtime/imports'/ (ident+'.lock')):
        with store(root) as con:old=con.execute('SELECT id FROM imports WHERE idem=?',(idem,)).fetchone()
        if old and old[0]!=ident:raise ValueError('冪等鍵已用於其他匯入')
        item=load(root,ident)
        if item['state']=='completed':return item
        if not retry and (item['state'] not in ('ready','queued') or (item['state']=='ready' and time.time()>item['expires'])):raise ValueError('預覽已過期或非可提交狀態')
        if retry and item['state'] not in ('failed','needs_check','running','queued'):raise ValueError('此操作不可重試')
        if item.get('idem') and item['idem']!=idem:raise ValueError('操作冪等鍵不相符')
        item.update(state='running',idem=idem);save(root,item)
        try:
            if shutil.disk_usage(root).free<item['required_free_bytes']:raise OSError('可用磁碟空間不足，尚未提交正式資料')
            if item['kind']=='photos':commit_photos(root,item)
            else:commit_model(root,item)
            item['cleanup_warnings']=cleanup_stage(root,item)
            item['state']='completed';save(root,item)
            write_json(root/'runtime/imports/receipts'/ (ident+'.json'),{k:v for k,v in item.items() if k not in ('session','idem')})
            from src.workbench.storage import audit
            audit('import_completed',{'import':ident,'kind':item['kind'],'batch':item['batch']},home=root/'runtime/workbench',actor=item.get('operator'))
        except Exception as exc:item.update(state='failed',error=str(exc));save(root,item)
        return item

def cleanup_stage(root,item):
    """Only recorded staging copies. Originals and installed files are never removed."""
    from src.workbench.managed_files import inspect,remove_verified
    stage=safe(root/'runtime/imports/staging'/item['id'],root);targets=[];warnings=[]
    if not stage.exists():return warnings
    for entry in item['items']:
        if entry.get('action')!='add':continue
        if item['kind']=='photos':
            targets.append((stage/(entry['image_id']+Path(entry['source']).suffix.lower()),entry['sha256']))
            targets.extend((stage/(entry['image_id']+'_'+str(n)+Path(ann['source']).suffix),ann['sha256']) for n,ann in enumerate(entry.get('annotations',[])))
        else:
            base=batch_path(root,'models',item['batch']).relative_to(root)
            targets.extend((stage/Path(f['source']).relative_to(base),f['sha256']) for f in entry['files'])
    for path,expected in targets:
        if not path.exists():continue
        try:
            record=inspect(path,stage)
            if record['sha256']!=expected:raise ValueError('暫存內容已改變')
            remove_verified(path,stage,record,lambda:None)
        except (OSError,ValueError) as exc:warnings.append(path.name+'：'+str(exc).replace(str(root),'專案'))
    # Empty directories have no data; leave nested empty directories for visibility.
    try:stage.rmdir()
    except OSError:pass
    return warnings

def commit_photos(root,item):
    stage=root/'runtime/imports/staging'/item['id'];safe(stage,root);stage.mkdir(parents=True,exist_ok=True)
    existing={r['sha256']:r['image_id'] for r in read_manifest(root)}
    for entry in item['items']:
        if entry['action']=='add' and entry['sha256'] in existing:entry.update(state='committed',existing_image_id=existing[entry['sha256']])
        if entry['action']!='add' or entry.get('state')=='committed':continue
        source=recheck(entry,root);target=stage/(entry['image_id']+source.suffix.lower())
        copy_verified(entry,root,target)
        if sha256(target)!=entry['sha256']:raise ValueError('暫存複本校驗失敗')
        for n,ann in enumerate(entry.get('annotations',[])):
            copy_verified(ann,root,stage/(entry['image_id']+'_'+str(n)+Path(ann['source']).suffix))
        entry['state']='staged';save(root,item)
    with dataset_lock(root):
        rows=read_manifest(root);known={r['sha256']:r for r in rows};fields=list(rows[0]) if rows else ['image_id','sha256','image_path','annotation_path','yolo_path','status','label_state','candidate_group','subject_id','group_verified','reviewer','reason','updated_at','original_paths']
        for entry in item['items']:
            if entry['action']!='add':continue
            if entry['sha256'] in known:
                entry.update(state='committed',existing_image_id=known[entry['sha256']]['image_id']);continue
            recheck(entry,root)
            source=stage/(entry['image_id']+Path(entry['source']).suffix.lower())
            dest=safe(root/'data/pending_review/unknown_source/images'/source.name,root);dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists():
                if sha256(dest)!=entry['sha256']:raise ValueError('目的檔案衝突，停止提交')
            else:os.replace(source,dest)
            for n,ann in enumerate(entry.get('annotations',[])):
                # Candidate annotations remain separate from authoritative labels.
                candidate=safe(root/'data/pending_review/unknown_source/candidates'/ (entry['image_id']+'_'+str(n)+Path(ann['source']).suffix),root);candidate.parent.mkdir(parents=True,exist_ok=True)
                staged=stage/candidate.name
                if candidate.exists():
                    if sha256(candidate)!=ann['sha256']:raise ValueError('候選標註目的檔案衝突')
                else:os.replace(staged,candidate)
            row={k:'' for k in fields};row.update(image_id=entry['image_id'],sha256=entry['sha256'],image_path=dest.relative_to(root).as_posix(),status='pending_review',label_state='unknown',group_verified='false',original_paths=json.dumps([entry['source']],ensure_ascii=False),updated_at=stamp(),reason='匯入批次 '+item['batch']+'；待人工確認')
            provenance=safe(root/'data/imports'/(entry['image_id']+'.json'),root)
            write_json(provenance,{'operation':item['id'],'batch':item['batch'],'source':entry['source'],'image_sha256':entry['sha256'],'orientation':entry.get('orientation'),'annotations':entry.get('annotations',[])})
            rows.append(row);known[row['sha256']]=row
        write_manifest(rows,root)
        for entry in item['items']:
            if entry['action']=='add':entry['state']='committed'
        save(root,item)
    from src.workbench.queries import data_index
    data_index.invalidate(root);data_index.request_rebuild(root)

def commit_model(root,item):
    entry=item['items'][0];base=batch_path(root,'models',item['batch'])
    checked=model_item(root,base)
    if checked['package']!=entry['package']:raise ValueError('模型清單已變更')
    for info in entry['files']+[entry['metadata']]:recheck(info,root)
    package=entry['package'];purpose=package['purpose'];stage=root/'runtime/imports/staging'/item['id'];safe(stage,root);stage.mkdir(parents=True,exist_ok=True)
    for info in entry['files']:
        relative=Path(info['source']).relative_to(base.relative_to(root));dest=safe(stage/relative,root);dest.parent.mkdir(parents=True,exist_ok=True);copy_verified(info,root,dest)
        if sha256(dest)!=info['sha256']:raise ValueError('模型暫存校驗失敗')
    from src.workbench.resources import resource_lock
    with resource_lock():
        # Recheck source lifecycle after staging, under the registration lease.
        model_item(root,base)
        staged_files={}
        for path in stage.rglob('*'):
            safe(path,root)
            if path.is_file():staged_files[path.relative_to(stage).as_posix()]=sha256(path)
        if staged_files!=package['files']:raise ValueError('暫存內容與核准模型清單不符')
        if purpose in ('inference','checkpoint'):
            from src.workbench import registry
            existing=next((read_json(p) for p in registry.VERSIONS.glob('*/artifact.json') if read_json(p).get('extra',{}).get('import_operation')==item['id']),None)
            if not existing:
                if purpose=='checkpoint':
                    from src.workbench.contracts import Experiment
                    policy=Experiment(**entry['proof']['config']).inference.model_dump()
                else:policy=package['config']
                # Keep the training dataset/protocol provenance of copied weights.
                # Evaluation must not silently treat the newly selected dataset as
                # their original training split.
                extra=dict(entry['proof'].get('extra',{})) if purpose=='inference' else {'dataset':entry['proof']['config']['dataset']}
                extra.update(import_operation=item['id'],purpose=purpose,source_artifact=package['source']['id'] if purpose=='inference' else None,source_job=package['source']['id'] if purpose=='checkpoint' else entry['proof'].get('experiment'))
                existing=registry.register(stage,package['model'],policy,'import_'+item['id'],entry['proof'].get('demo_only',True),extra,expected_files=package['files'])
            entry['artifact']=existing['id']
        else:
            # Base/checkpoint packages are not executable research versions.
            dest=safe(root/'models/pretrained/imported'/item['id'],root)
            if not dest.exists():dest.parent.mkdir(parents=True,exist_ok=True);stage.rename(dest)
            else:
                for name,expected in package['files'].items():
                    if sha256(safe(dest/name,root))!=expected:raise ValueError('已安裝模型內容不符，需人工檢查')
            write_json(dest/'import.json',{'operation':item['id'],'package':package,'source_job':package.get('source',{}).get('id'),'note':'未啟用；checkpoint 仍須保留來源工作及快照才可續訓'})
            entry['registered_path']=dest.relative_to(root).as_posix()
        entry['state']='committed';save(root,item)


def copy_verified(info,root,target):
    from src.workbench.managed_files import opened,identity
    with opened(safe(root/info['source'],root),root) as (stream,_):
        if identity(stream)['sha256']!=info['sha256']:raise ValueError('來源複製前內容變更')
        stream.seek(0)
        with safe(target,root).open('wb') as output:shutil.copyfileobj(stream,output,1024*1024)


def recover(root):
    with store(root) as con:ids=[r[0] for r in con.execute("SELECT id FROM imports WHERE state IN ('queued','running','scanning')")]
    for ident in ids:
        try:
            with file_lock(root/'runtime/imports'/(ident+'.lock')):
                item=load(root,ident)
                if item['state'] in ('queued','running'):
                    item.update(state='needs_check',error='服務中斷，請檢查並明確重試原範圍');save(root,item)
                elif item['state']=='scanning':
                    item.update(state='failed',error='掃描中斷，尚未提交；請重新掃描來源批次');save(root,item)
        except RuntimeError:pass # Another process still owns the operation.


def resolve_package(root,ident,purpose,model):
    item=load(root,ident)
    if item['state']!='completed' or item['kind']!='models':raise ValueError('匯入尚未完成')
    entry=item['items'][0];package=entry['package']
    if package['purpose']!=purpose or package['model']!=model:raise ValueError('匯入模型用途或方案不符')
    if purpose=='checkpoint':
        from src.workbench import registry,resources
        resources.require_active('job',package['source']['id'])
        registry.get(entry['artifact'])
        path=registry.artifact_path(entry['artifact'])
    else:path=safe(root/entry['registered_path'],root)
    for name,expected in package['files'].items():
        if sha256(safe(path/name,root))!=expected:raise ValueError('匯入模型完整性驗證失敗')
    return path,package


def packages(root,purpose,model=''):
    from src.workbench import resources
    with store(root) as con:rows=con.execute("SELECT payload FROM imports WHERE kind='models' AND state='completed' ORDER BY created DESC,id DESC").fetchall()
    result=[]
    for row in rows:
        item=json.loads(row[0]);entry=item['items'][0];package=entry['package']
        if package['purpose']!=purpose or model and package['model']!=model:continue
        if entry.get('artifact') and resources.record('model',entry['artifact'])['state']!='active':continue
        result.append({'id':item['id'],'name':item['batch'],'model':package['model'],'purpose':purpose,'source':package['source'],'artifact':entry.get('artifact')})
    return result


def candidate_annotations(root,ident,size,orientation):
    path=safe(root/'data/imports'/(ident+'.json'),root)
    if not path.exists():return []
    provenance=read_json(path);items=[]
    for n,ann in enumerate(provenance.get('annotations',[])):
        candidate=safe(root/'data/pending_review/unknown_source/candidates'/(ident+'_'+str(n)+Path(ann['source']).suffix),root)
        item={'name':Path(ann['source']).name,'state':ann.get('state'),'reason':ann.get('reason'),'boxes':None}
        if candidate.exists() and sha256(candidate)==ann['sha256'] and ann.get('state')=='provisional' and orientation==1:
            from src.data.labels import from_labelme,validate
            try:
                boxes=from_labelme(read_json(candidate),size) if candidate.suffix=='.json' else [list(map(float,line.split())) for line in candidate.read_text().splitlines() if line.strip()]
                validate(boxes);item['boxes']=boxes
            except ValueError as exc:item.update(state='invalid',reason=str(exc))
        items.append(item)
    return items
