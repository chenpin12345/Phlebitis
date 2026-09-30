"""Finite, source-labelled metrics and controlled artifact inspection; no model loading."""
from __future__ import annotations
import csv
import json
import math
from src.common import ROOT, inside, read_json, sha256
from src.workbench import jobs, registry
from src.workbench.contracts import MODELS
from src.workbench.views import redact
from src.workbench.storage import digest

def legacy_sources(root=ROOT):
    folders={p.parent for pattern in ('results.csv','results.png') for p in (root/'runs').rglob(pattern) if 'workbench' not in p.relative_to(root/'runs').parts}
    return {'legacy_'+digest(p.relative_to(root).as_posix())[:20]:p for p in sorted(folders)}

def curve_sources(root=ROOT):
    items=[{'id':j['id'],'model':j['config'].get('model'),'state':j['state'],'created':j['created'],'label':j['id']} for j in jobs.listing(limit=None) if j['kind']=='train']
    items.extend({'id':ident,'model':None,'state':'historical','created':None,'label':p.relative_to(root/'runs').as_posix()} for ident,p in legacy_sources(root).items())
    return items

def curve_source(ident,root=ROOT):
    if not ident.startswith('legacy_'): return curves(ident)
    folder=legacy_sources(root).get(ident)
    if folder is None: raise ValueError('未登錄的歷史曲線來源')
    return {**metric_history(folder), 'id':ident,'state':'historical','model':None,'epochs':None,'progress':None}

def curve_image(ident,root=ROOT):
    folder=legacy_sources(root).get(ident) if ident.startswith('legacy_') else jobs.folder(ident)
    if folder is None: raise ValueError('未登錄的曲線來源')
    path=folder/'training/results.png'
    if not path.is_file():path=folder/'results.png'
    if not path.is_file(): raise FileNotFoundError(path)
    return path

def history(path):
    result=[]
    if path.exists():
        for line in path.read_text(encoding='utf-8',errors='replace').splitlines():
            try:
                record=json.loads(line)
                if isinstance(record,dict): result.append(record)
            except (ValueError,TypeError): pass # An active writer may not have finished its last line.
    return result

def finite(value):
    try:
        value=float(value)
        return value if math.isfinite(value) else None
    except (ValueError,TypeError): return None

def metric_history(folder, *, model='', epochs=None):
    points={}; warnings=[]; source=None
    csv_path=folder/'training/results.csv'
    if not csv_path.exists(): csv_path=folder/'results.csv'
    records=history(folder/'progress.jsonl')
    raw=[]
    for record in records:
        if 'epoch' not in record: continue
        values={k:record[k] for k in ('train_loss','val_loss','val_accuracy') if k in record}
        values.update(record.get('metrics') or {})
        losses=record.get('training_losses') or {}
        pairs=losses.items() if isinstance(losses,dict) else zip(record.get('loss_names',[]),losses)
        values.update({'train/'+k:v for k,v in pairs})
        raw.append((record.get('epoch'),values))
    if raw: source='progress.jsonl'
    if csv_path.exists():
        source='results.csv'
        with csv_path.open(encoding='utf-8-sig',newline='') as stream:
            for r in csv.DictReader(stream):
                r={str(k).strip():v for k,v in r.items() if k is not None}
                raw.append((r.pop('epoch',None),r))
    # CSV rows appended last override progress for the same epoch. Finite recorded values only.
    for epoch, values in raw:
        e=finite(epoch)
        if e is None or e<1 or not e.is_integer() or (epochs and e>epochs):
            warnings.append('忽略無效或超出要求範圍的 epoch：'+str(epoch)); continue
        e=int(e)
        normalized={k:finite(v) for k,v in values.items() if k!='time'}
        if e in points:
            for key,value in normalized.items():
                if value is not None or key not in points[e]: points[e][key]=value
        else: points[e]=normalized
    keys=sorted({k for p in points.values() for k,v in p.items() if v is not None})
    checkpoint=read_json(folder/'checkpoint_selection.json') if (folder/'checkpoint_selection.json').exists() else None
    return {'source':source,'points':[{'epoch':e,**{k:points[e].get(k) for k in keys}} for e in sorted(points)],
            'metrics':keys, 'warnings':sorted(set(warnings)), 'checkpoint':checkpoint,
            'current_epoch':max(points,default=None), 'task':MODELS.get(model,{}).get('task'),
            'has_image':(folder/'training/results.png').exists() or (folder/'results.png').exists()}

def curves(ident):
    item=jobs.get(ident)
    if item['kind']!='train': raise ValueError('此工作不是訓練實驗；回歸工作為回歸測試')
    return redact({**metric_history(jobs.folder(ident),model=item['config'].get('model',''),epochs=item['config'].get('epochs')),
            'id':ident,'state':item['state'],'model':item['config'].get('model'),'progress':item.get('progress'),
            'epochs':item['config'].get('epochs')})

def artifact_file(ident, key):
    meta=registry.get(ident,verify=False)
    if key not in meta.get('files',{}): raise ValueError('未登錄的產物')
    path=inside(registry.artifact_path(ident)/key,registry.artifact_path(ident))
    if not path.is_file(): raise FileNotFoundError(key)
    if sha256(path)!=meta['files'][key]: raise ValueError('產物完整性檢查失敗')
    return path

def artifact_detail(ident):
    meta=registry.get(ident,verify=False); files=[]
    for key,expected in meta.get('files',{}).items():
        row={'name':key,'format':key.rsplit('.',1)[-1], 'declared':True, 'size':None, 'state':'unchecked','sha256':expected}
        try:
            path=inside(registry.artifact_path(ident)/key,registry.artifact_path(ident))
            if not path.is_file(): row['state']='missing'
            else:
                row['size']=path.stat().st_size
                with path.open('rb') as f: f.read(1)
                row['state']='readable' # A download verifies hash; listing doesn't hash huge weights.
        except (OSError,ValueError): row['state']='inaccessible'
        row['kind']='weights' if row['format'] in ('pt','pth','npz','safetensors') else 'configuration' if row['format'] in ('json','yaml','yml') else 'image' if row['format'] in ('png','jpg','jpeg') else 'other'
        files.append(row)
    requested=None
    try: requested=jobs.get(meta.get('experiment') or '')['config']
    except (ValueError,FileNotFoundError): pass
    reports=registry.reports(ident)
    status=next((m.get('evaluation_status') for m in registry.listing() if m['id']==ident),None)
    return redact({'metadata':meta,'task':MODELS.get(meta.get('model'),{}).get('task'), 'files':files,
                   'requested':requested,'effective':meta.get('extra',{}).get('effective'),
                   'inference':meta.get('config'), 'reports':reports,'evaluation_status':status})

def file_settings(ident,key):
    path=artifact_file(ident,key)
    if path.suffix.lower() not in ('.json','.yaml','.yml'): raise ValueError('這不是設定檔')
    if path.stat().st_size>2_000_000: raise ValueError('設定檔超過檢視上限')
    if path.suffix.lower()=='.json': value=read_json(path)
    else:
        import yaml
        value=yaml.safe_load(path.read_text(encoding='utf-8-sig'))
    return redact(value)
