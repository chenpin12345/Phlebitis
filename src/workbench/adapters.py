from __future__ import annotations

import io
import json
import math
import os
import random
import shutil
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps
from src.common import ROOT, inside, read_json, write_json, sha256, stamp
from src.data.dataset import validate_split
from src.inference.engine import decode_image, encode_result
from src.workbench.contracts import MODELS, Experiment, InferenceConfig
from src.workbench.storage import digest

PRETRAINED = ROOT/'models/pretrained'

class Cancelled(Exception): pass

def check_cancel(folder):
    if (folder/'cancel').exists(): raise Cancelled('使用者停止工作')

def progress(folder, stage, **values):
    write_json(folder/'progress.json', {'stage':stage,'at':time.time(),**values})
    with (folder/'progress.jsonl').open('a',encoding='utf-8') as f:
        f.write(json.dumps({'stage':stage,'at':time.time(),**values},ensure_ascii=False,allow_nan=False)+'\n')

def prepare(model, folder):
    PRETRAINED.mkdir(parents=True,exist_ok=True)
    progress(folder,'preparing_weights',model=model)
    if model=='dinov2_small':
        dest=PRETRAINED/model
        freshly_downloaded=not (dest/'model.safetensors').exists()
        if not (dest/'model.safetensors').exists():
            from huggingface_hub import snapshot_download, HfApi
            revision=HfApi().model_info(MODELS[model]['source']).sha
            source=snapshot_download(MODELS[model]['source'],revision=revision,allow_patterns=['config.json','model.safetensors'],cache_dir=str(PRETRAINED/'hf-cache'))
            shutil.copytree(source,dest,dirs_exist_ok=True)
            write_json(dest/'source.json',{'source':MODELS[model]['source'],'revision':revision})
        files={p.name:sha256(p) for p in dest.iterdir() if p.suffix in ('.safetensors','.json') and p.name!='provenance.json'}
        write_json(dest/'provenance.json',{'files':files,'source':MODELS[model]['source']})
        if freshly_downloaded:write_json(ROOT/'runtime/imports/trusted-official'/(model+'.json'),{'source':MODELS[model]['source'],'files':{p.name:sha256(p) for p in dest.iterdir() if p.name in ('config.json','model.safetensors')},'revision':revision})
        return dest
    dest=PRETRAINED/(model+('.pt' if model.startswith('yolo') else '.pth'))
    freshly_downloaded=not dest.exists()
    if not dest.exists():
        temporary=dest.with_suffix('.download')
        def report(block,size,total):
            check_cancel(folder)
            if block%128==0: progress(folder,'downloading',bytes=min(block*size,total) if total>0 else block*size,total=total)
        import requests
        for attempt in range(5):
            try:
                offset=temporary.stat().st_size if temporary.exists() else 0
                with requests.get(MODELS[model]['source'],headers={'Range':f'bytes={offset}-'} if offset else {},stream=True,timeout=(20,40)) as response:
                    response.raise_for_status()
                    append=offset>0 and response.status_code==206
                    if not append:offset=0
                    total=int(response.headers.get('content-length',0))+offset
                    with temporary.open('ab' if append else 'wb') as output:
                        done=offset
                        for chunk in response.iter_content(256*1024):
                            check_cancel(folder);output.write(chunk);done+=len(chunk)
                            progress(folder,'downloading',bytes=done,total=total,attempt=attempt+1)
                    if total and done!=total:raise OSError('Download incomplete')
                break
            except Cancelled:raise
            except Exception:
                if attempt==4:raise
                progress(folder,'retrying_download',attempt=attempt+2)
        temporary.replace(dest)
    write_json(dest.with_suffix('.source.json'),{'source':MODELS[model]['source'],'sha256':sha256(dest),'prepared':stamp()})
    if freshly_downloaded:
        write_json(ROOT/'runtime/imports/trusted-official'/(model+'.json'),{'source':MODELS[model]['source'],'files':{dest.name:sha256(dest)},'prepared':stamp()})
    return dest

def device_name(value):
    import torch
    if value!='cpu' and not torch.cuda.is_available(): raise ValueError('CUDA 不可用，請明確選擇 CPU。')
    return 'cpu' if value=='cpu' else 'cuda:0'

def tensor_image(image, augment=None):
    import torch
    image=ImageOps.pad(image.convert('RGB'),(224,224),method=Image.Resampling.BICUBIC,color=(124,116,104),centering=(.5,.5))
    if augment:
        if augment.get('flip',True) and random.random()<.5: image=ImageOps.mirror(image)
        rotation=float(augment.get('rotation',0))
        if rotation: image=image.rotate(random.uniform(-rotation,rotation),resample=Image.Resampling.BILINEAR,fillcolor=(124,116,104))
    x=torch.from_numpy(np.asarray(image).copy()).permute(2,0,1).float()/255
    return (x-torch.tensor([.485,.456,.406])[:,None,None])/torch.tensor([.229,.224,.225])[:,None,None]

def load_efficient(path=None):
    import torch
    from torchvision.models import efficientnet_b0
    model=efficientnet_b0(weights=None)
    if path: model.load_state_dict(torch.load(path,map_location='cpu',weights_only=True))
    model.classifier[1]=torch.nn.Linear(model.classifier[1].in_features,2)
    return model

def efficient_training_mode(model, strategy='backbone'):
    model.train()
    model.features.eval()
    if strategy=='last_stage': model.features[-1].train()

def efficient_train(cfg, split, folder, base):
    import torch
    from torch.utils.data import Dataset, DataLoader
    from src.workbench.registry import get, artifact_path
    params=cfg.parameters; device=device_name(cfg.device)
    model=load_efficient(base)
    if cfg.initial_artifact:
        prior=get(cfg.initial_artifact)
        if prior['model']!=cfg.model: raise ValueError('Initial artifact recipe mismatch')
        model.load_state_dict(torch.load(artifact_path(cfg.initial_artifact)/'model.pt',map_location='cpu',weights_only=True))
    for p in model.features.parameters(): p.requires_grad=False
    if params.get('freeze','backbone')=='last_stage':
        for p in model.features[-1].parameters(): p.requires_grad=True
    model.to(device)
    class Images(Dataset):
        def __init__(self,rows,augment=False): self.rows=rows; self.augment=augment
        def __len__(self): return len(self.rows)
        def __getitem__(self,i):
            row=self.rows[i]
            with Image.open(inside(row['image_path'])) as im: x=tensor_image(im,params if self.augment else None)
            return x,int(row['label_state']=='positive')
    train=DataLoader(Images(split['members']['train'],True),batch_size=cfg.batch,shuffle=True,num_workers=0)
    val=DataLoader(Images(split['members']['val']),batch_size=cfg.batch,num_workers=0)
    counts=np.bincount([int(x['label_state']=='positive') for x in split['members']['train']],minlength=2)
    weights=torch.tensor(counts.sum()/(2*counts),dtype=torch.float32,device=device) if params.get('class_weight')=='balanced' else None
    loss_fn=torch.nn.CrossEntropyLoss(weight=weights)
    optimizer_cls=torch.optim.AdamW if params.get('optimizer','AdamW')=='AdamW' else torch.optim.SGD
    optimizer=optimizer_cls([p for p in model.parameters() if p.requires_grad],lr=params.get('learning_rate',.001),weight_decay=params.get('weight_decay',.0001))
    scheduler=torch.optim.lr_scheduler.CosineAnnealingLR(optimizer,cfg.epochs) if params.get('scheduler','none')=='cosine' else None
    start=0; best=float('inf'); stale=0
    if cfg.resume_job:
        checkpoint=torch.load(resume_folder(cfg)/'last.pt',map_location=device,weights_only=True)
        model.load_state_dict(checkpoint['model']); optimizer.load_state_dict(checkpoint['optimizer'])
        if scheduler and checkpoint.get('scheduler'): scheduler.load_state_dict(checkpoint['scheduler'])
        start=checkpoint['epoch']; best=checkpoint['best']; stale=checkpoint['stale']
        if start>=cfg.epochs: raise ValueError('Checkpoint already completed requested epochs')
    actual={'freeze':params.get('freeze','backbone'),'scheduler':params.get('scheduler','none'),'class_weight':params.get('class_weight'),'flip':bool(params) and params.get('flip',True),'rotation':params.get('rotation',0),'optimizer':type(optimizer).__name__,'learning_rate':optimizer.param_groups[0]['lr'],'weight_decay':optimizer.param_groups[0]['weight_decay'],'epochs':cfg.epochs,'batch':cfg.batch,'imgsz':224,'device':cfg.device,'seed':cfg.seed,'patience':cfg.patience}
    effective={'parameters':actual,'total_parameters':sum(p.numel() for p in model.parameters()),'trainable_parameters':sum(p.numel() for p in model.parameters() if p.requires_grad),'checkpoint_metric':'validation_loss','preprocess':cfg.inference.preprocess}
    write_json(folder/'effective.json',effective)
    output=folder/'artifact'; output.mkdir(exist_ok=True)
    if cfg.resume_job:
        oldbest=resume_folder(cfg)/'artifact/model.pt'
        if oldbest.exists(): shutil.copy2(oldbest,output/'model.pt')
        selection=oldbest.parent.parent/'checkpoint_selection.json'
        if selection.exists(): shutil.copy2(selection,folder/'checkpoint_selection.json')
    for epoch in range(start,cfg.epochs):
        check_cancel(folder); efficient_training_mode(model,params.get('freeze','backbone'))
        loss_sum=0; seen=0
        for x,y in train:
            check_cancel(folder); x=x.to(device); y=y.to(device)
            optimizer.zero_grad(); loss=loss_fn(model(x),y); loss.backward(); optimizer.step()
            loss_sum+=loss.item()*len(y); seen+=len(y)
        model.eval(); val_loss=0; correct=0; total=0
        with torch.inference_mode():
            for x,y in val:
                x=x.to(device); y=y.to(device); logits=model(x)
                val_loss+=loss_fn(logits,y).item()*len(y); correct+=(logits.argmax(1)==y).sum().item(); total+=len(y)
        value=val_loss/total
        if value<best:
            best=value; stale=0
            torch.save(model.cpu().state_dict(),output/'model.pt'); model.to(device)
            write_json(folder/'checkpoint_selection.json',{'epoch':epoch+1,'value':value,'rule':'minimum validation_loss; strict improvement','artifact':'model.pt'})
        else: stale+=1
        if scheduler: scheduler.step()
        checkpoint={'epoch':epoch+1,'model':model.state_dict(),'optimizer':optimizer.state_dict(),'scheduler':scheduler.state_dict() if scheduler else None,'best':best,'stale':stale}
        torch.save(checkpoint,folder/'last.tmp'); os.replace(folder/'last.tmp',folder/'last.pt')
        progress(folder,'training',epoch=epoch+1,epochs=cfg.epochs,train_loss=loss_sum/seen,val_loss=value,val_accuracy=correct/total,vram_bytes=torch.cuda.max_memory_allocated() if device!='cpu' else None)
        if cfg.patience and stale>=cfg.patience: break
    return output,effective

def dino_features(model, members, device, folder, base_hash):
    import torch
    cache=ROOT/'runtime/workbench/features'; cache.mkdir(parents=True,exist_ok=True)
    values=[]
    for i,row in enumerate(members):
        check_cancel(folder)
        key=digest({'input':row['dataset_sha256'],'weights':base_hash,'preprocess':'rgb-letterbox224-imagenet-v1','pooling':'CLS'})
        path=cache/(key+'.npy')
        if path.exists(): features=np.load(path,allow_pickle=False)
        else:
            with Image.open(inside(row['image_path'])) as im: x=tensor_image(im).unsqueeze(0).to(device)
            with torch.inference_mode(): features=model(pixel_values=x).last_hidden_state[:,0].cpu().numpy()[0]
            np.save(path,features,allow_pickle=False)
        write_json(cache/(key+'.json'),{'image_id':row['image_id'],'input_hash':row['dataset_sha256'],'weights_hash':base_hash})
        values.append(features)
        progress(folder,'extracting_features',completed=i+1,total=len(members))
    return np.stack(values)

def dino_train(cfg, split, folder, base):
    from transformers import Dinov2Model
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression
    device=device_name(cfg.device)
    model=Dinov2Model.from_pretrained(base,local_files_only=True,use_safetensors=True).to(device).eval()
    for p in model.parameters(): p.requires_grad=False
    rows=split['members']['train']
    x=dino_features(model,rows,device,folder,sha256(base/'model.safetensors'))
    y=np.array([int(r['label_state']=='positive') for r in rows])
    params=cfg.parameters
    scaler=StandardScaler().fit(x) if params.get('standardize',True) else None
    if scaler is not None: x=scaler.transform(x)
    check_cancel(folder); progress(folder,'fitting_classifier',samples=len(y),features=x.shape[1])
    classifier=LogisticRegression(C=params.get('C',1),solver=params.get('solver','lbfgs'),max_iter=params.get('max_iter',200),class_weight=params.get('class_weight'),random_state=cfg.seed)
    classifier.fit(x,y)
    output=folder/'artifact'; output.mkdir(exist_ok=True)
    for name in ('config.json','model.safetensors','source.json'):
        if (base/name).exists(): shutil.copy2(base/name,output/name)
    np.savez(output/'classifier.npz',coef=classifier.coef_,intercept=classifier.intercept_,classes=classifier.classes_,mean=scaler.mean_ if scaler is not None else np.zeros(x.shape[1]),scale=scaler.scale_ if scaler is not None else np.ones(x.shape[1]))
    effective={'pooling':'CLS','parameters':classifier.get_params(),'total_parameters':sum(p.numel() for p in model.parameters()),'trainable_parameters':int(classifier.coef_.size+classifier.intercept_.size),'iterations':classifier.n_iter_.tolist(),'train_only_scaler':True,'feature_count':int(x.shape[1]),'backbone_hash':sha256(base/'model.safetensors')}
    write_json(output/'pipeline.json',effective)
    write_json(folder/'effective.json',effective)
    return output,effective

def yolo_train(cfg,split,folder,base):
    from src.model_api import yolo_api
    from src.workbench.registry import get,artifact_path
    params=read_json(ROOT/'configs/train.json'); params.pop('model',None)
    params.update(cfg.parameters)
    params.update(data=str(inside(cfg.dataset)),device=cfg.device,epochs=cfg.epochs,batch=cfg.batch,imgsz=cfg.imgsz,seed=cfg.seed,patience=cfg.patience,workers=cfg.parameters.get('workers',0),amp=bool(cfg.parameters.get('amp',False) and cfg.device!='cpu'),project=str(folder),name='training',exist_ok=True)
    if cfg.initial_artifact:
        prior=get(cfg.initial_artifact)
        if prior['model']!=cfg.model: raise ValueError('Fine-tune model family mismatch')
        base=artifact_path(cfg.initial_artifact)/'best.pt'
    if cfg.resume_job: base=resume_folder(cfg)/'training/weights/last.pt'
    model=yolo_api()(str(base))
    def callback(trainer):
        if (folder/'cancel').exists(): trainer.stop=True
        values={str(k):float(v) for k,v in trainer.metrics.items() if isinstance(v,(float,int)) and math.isfinite(v)}
        losses={k:float(v) for k,v in zip(trainer.loss_names,trainer.tloss.tolist())} if trainer.tloss is not None else {}
        progress(folder,'training',epoch=min(trainer.epoch+1,trainer.epochs),epochs=trainer.epochs,metrics=values,training_losses=losses,loss_names=list(trainer.loss_names),vram_bytes=__import__('torch').cuda.max_memory_allocated() if cfg.device!='cpu' else None)
        previous=read_json(folder/'effective.json') if (folder/'effective.json').exists() else {}
        effective={'parameters':vars(trainer.args),'optimizer':type(trainer.optimizer).__name__,'learning_rates':[g['lr'] for g in trainer.optimizer.param_groups],'total_parameters':sum(p.numel() for p in trainer.model.parameters()),'trainable_parameters':previous.get('trainable_parameters') or sum(p.numel() for p in trainer.model.parameters() if p.requires_grad),'loss_names':list(trainer.loss_names),'end2end':bool(getattr(trainer.model,'end2end',False))}
        write_json(folder/'effective.json',effective)
    model.add_callback('on_fit_epoch_end',callback)
    def record_selection(trainer):
        # Match the installed trainer's best.pt write rule, including ties.
        if trainer.best_fitness==trainer.fitness and trainer.best.is_file():
            write_json(folder/'checkpoint_selection.json',{'epoch':trainer.epoch+1,'value':float(trainer.fitness),'rule':'Ultralytics best_fitness == fitness at on_model_save','artifact':'best.pt'})
    model.add_callback('on_model_save',record_selection)
    model.add_callback('on_train_batch_end',lambda trainer:setattr(trainer,'stop',True) if (folder/'cancel').exists() else None)
    if cfg.resume_job:
        # Installed Ultralytics explicitly permits save_dir during resume.
        # Keep optimizer/checkpoint state but never overwrite the prior experiment.
        weights=folder/'training/weights'; weights.mkdir(parents=True,exist_ok=True)
        previous=resume_folder(cfg)/'training/weights/best.pt'
        if previous.exists():shutil.copy2(previous,weights/'best.pt')
        selection=resume_folder(cfg)/'checkpoint_selection.json'
        if selection.exists():shutil.copy2(selection,folder/'checkpoint_selection.json')
        model.train(resume=True,device=cfg.device,workers=cfg.parameters.get('workers',0),save_dir=str(folder/'training'))
        output=folder/'artifact'; output.mkdir(exist_ok=True); shutil.copy2(weights/'best.pt',output/'best.pt')
    else:
        model.train(**params)
        output=folder/'artifact'; output.mkdir(exist_ok=True); shutil.copy2(folder/'training/weights/best.pt',output/'best.pt')
    check_cancel(folder)
    return output,read_json(folder/'effective.json')

def train(cfg: Experiment, folder):
    import torch
    device_name(cfg.device)
    random.seed(cfg.seed); np.random.seed(cfg.seed); torch.manual_seed(cfg.seed)
    torch.set_num_threads(4)
    split=validate_split(inside(cfg.dataset))
    if split.get('purpose')=='independent_test':raise ValueError('Reserved independent test snapshots cannot be used for model selection/training')
    if split['demo_only'] and not cfg.demo: raise ValueError('未核對個案，必須明確勾選研究展示模式。')
    for subset in ('train','val'):
        if {r['label_state'] for r in split['members'][subset]} != {'positive','negative'}: raise ValueError('Both classes required in each split')
    base=prepare(cfg.model,folder) if not cfg.base_import else imported_base(cfg)
    write_json(folder/'experiment.json',{'requested':cfg.model_dump(),'split':split,'source':MODELS[cfg.model]['source'],'prepared_hash':sha256(base) if base.is_file() else sha256(base/'model.safetensors')})
    fn=yolo_train if cfg.model.startswith('yolo') else efficient_train if cfg.model=='efficientnet_b0' else dino_train
    return fn(cfg,split,folder,base)

class ModelPredictor:
    def __init__(self,ident,device='cpu'):
        import torch
        from src.workbench.registry import get,artifact_path
        self.metadata=get(ident)
        if self.metadata.get('extra',{}).get('purpose')=='checkpoint':raise ValueError('Checkpoint 不是推論模型')
        self.path=artifact_path(ident); self.device=device_name(device); self.raw_device=device
        self.config=read_json(ROOT/'configs/service.json'); self.policy=InferenceConfig(**self.metadata['config'])
        self.kind=self.metadata['model']; self.task=MODELS[self.kind]['task']
        if self.task=='detection':
            from src.model_api import yolo_api
            from src.inference.engine import validate_model
            self.model=yolo_api()(str(self.path/'best.pt')); validate_model(self.model)
        elif self.kind=='efficientnet_b0':
            self.model=load_efficient(); self.model.load_state_dict(torch.load(self.path/'model.pt',map_location='cpu',weights_only=True)); self.model.to(self.device).eval()
        else:
            from transformers import Dinov2Model
            self.model=Dinov2Model.from_pretrained(self.path,local_files_only=True,use_safetensors=True).to(self.device).eval()
            self.classifier=np.load(self.path/'classifier.npz',allow_pickle=False)
            if self.classifier['classes'].tolist()!=[0,1]: raise ValueError('Classifier label mapping mismatch')

    def predict(self,content):
        import torch
        import cv2
        start=time.perf_counter(); im=decode_image(content,self.config); cfg=self.policy
        gray=np.asarray(ImageOps.grayscale(ImageOps.contain(im,(512,512))))
        quality={'blur_variance':float(cv2.Laplacian(gray,cv2.CV_64F).var()),'dark_fraction':float((gray<15).mean()),'bright_fraction':float((gray>240).mean()),'mode':cfg.quality_mode,'content_recognition':'unsupported'}
        reasons=[]
        if quality['blur_variance']<cfg.blur_threshold: reasons.append('可能失焦，請確認拍攝清晰度')
        if quality['dark_fraction']>cfg.dark_fraction: reasons.append('大部分畫面過暗')
        if quality['bright_fraction']>cfg.bright_fraction: reasons.append('大部分畫面過亮')
        quality['reasons']=reasons
        boxes=[]; candidates=[]
        if self.task=='detection':
            r=self.model.predict(im,device=self.raw_device,imgsz=cfg.imgsz,conf=cfg.candidate_threshold,iou=cfg.iou,nms=False if cfg.postprocess=='end2end' else None,verbose=False)[0]
            candidates=[{'xyxy':[float(v) for v in b.xyxy[0].tolist()],'confidence':float(b.conf.item()),'class':'phlebitis'} for b in r.boxes]
            boxes=[b for b in candidates if b['confidence']>=cfg.threshold]
            score=max((b['confidence'] for b in candidates),default=0.)
            prediction=int(bool(boxes))
            from PIL import ImageDraw
            annotated=im.copy(); draw=ImageDraw.Draw(annotated)
            for b in boxes: draw.rectangle(b['xyxy'],outline='#06b6a4',width=max(2,im.width//200))
            semantics='maximum candidate box confidence; no box is not certainty of absence'
        else:
            x=tensor_image(im).unsqueeze(0).to(self.device)
            with torch.inference_mode():
                if self.kind=='efficientnet_b0': score=float(self.model(x).softmax(1)[0,1])
                else:
                    features=self.model(pixel_values=x).last_hidden_state[:,0].cpu().numpy()
                    c=self.classifier; z=((features-c['mean'])/c['scale'])@c['coef'].T+c['intercept']
                    score=float((1/(1+np.exp(-np.clip(z,-700,700))))[0,0])
            prediction=int(score>=cfg.threshold); annotated=im
            semantics='uncalibrated positive-class model score; not disease probability'
        status='suspected' if prediction else 'not_detected'
        if cfg.review_low_confidence and not prediction and self.task=='detection' and candidates: status='needs_review'
        if reasons and cfg.quality_mode=='reject': status='quality_rejected'
        jpeg,size=encode_result(annotated)
        record={'schema_version':1,'status':status,'task_type':self.task,'model_id':self.kind,'model_version':self.metadata['id'],'preprocess_version':cfg.preprocess,'prediction_score':score,'score_semantics':semantics,'decision_rule':cfg.model_dump(),'binary_prediction':prediction,'boxes':boxes if self.task=='detection' else None,'candidates':candidates if self.task=='detection' else None,'quality':quality,'demo_only':self.metadata['demo_only'],'elapsed_ms':round((time.perf_counter()-start)*1000,2),'source_size':list(im.size),'annotated_size':list(size),'severity':None}
        return record,jpeg

def evaluate(ident,dataset,device,folder):
    from src.workbench.registry import get
    from src.workbench.metrics import binary_metrics
    split=validate_split(inside(dataset)); metadata=get(ident); predictor=ModelPredictor(ident,device)
    training_dataset=metadata.get('extra',{}).get('dataset')
    actual_training=validate_split(inside(training_dataset)) if training_dataset else split
    if split.get('purpose')!='independent_test' and training_dataset and inside(training_dataset)!=inside(dataset):
        raise ValueError('Validation must match the trained fold; choose an explicitly reserved independent test snapshot for external evaluation')
    if {m['group'] for m in actual_training['members']['train']} & {m['group'] for m in split['members']['val']}:
        raise ValueError('Evaluation contains a training subject')
    records=[]
    for n,row in enumerate(split['members']['val']):
        check_cancel(folder)
        sample={'image_id':row['image_id'],'group':row['group'],'truth':int(row['label_state']=='positive')}
        try:
            result,jpeg=predictor.predict(inside(row['image_path']).read_bytes())
            sample.update(prediction=result['binary_prediction'],status=result['status'],score=result['prediction_score'],elapsed_ms=result['elapsed_ms'],boxes=result['boxes'],quality=result['quality'],source_size=result.get('source_size'),annotated_size=result.get('annotated_size'),coordinate_system='prediction: source pixels; truth: normalized YOLO xywh; preview: EXIF corrected')
            from PIL import ImageDraw
            rendered=Image.open(io.BytesIO(jpeg)).convert('RGB');draw=ImageDraw.Draw(rendered)
            truth_boxes=[list(map(float,line.split())) for line in inside(row['label_path']).read_text().splitlines() if line.strip()]
            for _,x,y,w,h in truth_boxes:draw.rectangle([(x-w/2)*rendered.width,(y-h/2)*rendered.height,(x+w/2)*rendered.width,(y+h/2)*rendered.height],outline='#e1a428',width=max(2,rendered.width//250))
            rendered.save(folder/(row['image_id']+'.jpg'),'JPEG',quality=90)
            sample['truth_boxes']=truth_boxes
        except Exception as exc: sample.update(error=type(exc).__name__+': '+str(exc),prediction=None)
        records.append(sample); progress(folder,'evaluating',completed=n+1,total=len(split['members']['val']))
    detection=None
    if predictor.task=='detection':
        m=predictor.model.val(data=str(inside(dataset)),device=device,imgsz=predictor.policy.imgsz,batch=2,workers=0,conf=.001,iou=predictor.policy.iou,nms=False if predictor.policy.postprocess=='end2end' else None,plots=True,project=str(folder),name='detection',verbose=False)
        detection={k:float(v) for k,v in m.results_dict.items() if isinstance(v,(int,float)) and math.isfinite(v)}
    metrics=binary_metrics(records,[r['image_id'] for r in split['members']['val']])
    # Evaluate training fit without augmentation; never label this as validation accuracy.
    train_samples=[]
    for row in actual_training['members']['train']:
        check_cancel(folder)
        r,_=predictor.predict(inside(row['image_path']).read_bytes())
        train_samples.append({'image_id':row['image_id'],'truth':int(row['label_state']=='positive'),'prediction':r['binary_prediction'],'status':r['status']})
    report={'schema_version':1,'artifact':ident,'artifact_hash':metadata['artifact_hash'],'model':metadata['model'],'config':metadata['config'],'dataset':dataset,'snapshot':inside(dataset).parent.parent.name,'split_hash':sha256(inside(dataset).parent/'split.json'),'fold':split['fold'],'evaluated_at':stamp(),'purpose':'validation','demo_only':split['demo_only'],'selection_bias':'validation may inform checkpoint/model choice; exploratory','metrics':metrics,'samples':records,'train_groups':sorted({r['group'] for r in split['members']['train']}),'training_fit':binary_metrics(train_samples),'detection_metrics':detection,'detection_note':'N/A: classification has no localization' if detection is None else 'AP conf=.001; binary threshold in config','code_version':code_version()}
    report.update(report_id=folder.name,purpose=split.get('purpose','validation'),train_groups=sorted({r['group'] for r in actual_training['members']['train']}),training_members_hash=digest(sorted(r['image_id'] for r in actual_training['members']['train'])),expected_folds=len(read_json(inside(dataset).parent.parent/'dataset_version.json')['folds']))
    experiment=ROOT/'runs/workbench/jobs'/metadata['experiment']/'request.json'
    if experiment.exists():
        protocol=read_json(experiment)['config'].copy()
        for key in ('dataset','resume_job'):protocol.pop(key,None)
        report['training_protocol']=protocol
    write_json(folder/'report.json',report)
    return report

def code_version():
    return digest({str(p.relative_to(ROOT)):sha256(p) for p in (ROOT/'src').rglob('*.py')})


def prepare_verified(model,folder):
    """Explicit prepare uses a fresh official download to establish provenance.

    This runs only in a dedicated worker process while holding the compute lock.
    Existing official files are never overwritten on a different hash.
    """
    global PRETRAINED
    original=PRETRAINED
    verification=folder/'official_verification'
    try:
        PRETRAINED=verification
        downloaded=prepare(model,folder)
    finally:PRETRAINED=original
    destination=original/downloaded.name
    if not destination.exists():
        destination.parent.mkdir(parents=True,exist_ok=True)
        if downloaded.is_dir():shutil.copytree(downloaded,destination)
        else:shutil.copy2(downloaded,destination)
    elif downloaded.is_file() and sha256(downloaded)!=sha256(destination):
        raise ValueError('既有基礎權重與本次官方下載不同；已保留既有檔案，請核對來源')
    elif downloaded.is_dir():
        expected={p.relative_to(downloaded).as_posix():sha256(p) for p in downloaded.rglob('*') if p.is_file()}
        actual={p.relative_to(destination).as_posix():sha256(p) for p in destination.rglob('*') if p.is_file()}
        if expected!=actual:raise ValueError('既有基礎權重目錄與官方下載不同；已保留既有檔案')
    return destination


def imported_base(cfg):
    from src.imports.service import resolve_package
    path,package=resolve_package(ROOT,cfg.base_import,'base',cfg.model)
    return path if cfg.model=='dinov2_small' else path/next(iter(package['files']))

def resume_folder(cfg):
    if not cfg.checkpoint_import:return ROOT/'runs/workbench/jobs'/cfg.resume_job
    from src.imports.service import resolve_package
    path,package=resolve_package(ROOT,cfg.checkpoint_import,'checkpoint',cfg.model)
    if package['source']['id']!=cfg.resume_job:raise ValueError('Checkpoint 原工作不相符')
    return path
