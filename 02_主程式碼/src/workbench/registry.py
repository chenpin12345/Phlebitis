from __future__ import annotations
import shutil
import uuid
from pathlib import Path
from src.common import ROOT, inside, read_json, write_json, sha256, stamp
from src.workbench.storage import audit, file_lock, digest
from src.workbench.resources import guarded, require_active, states as resource_states

VERSIONS = ROOT / 'models/versions'
REFS = ROOT / 'models/references'

def artifact_path(ident):
    if not ident or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in ident):
        raise ValueError('Invalid model version')
    return VERSIONS / ident

@guarded
def register(source: Path, model: str, config: dict, experiment: str, demo=True, extra=None, *, expected_files=None):
    from src.workbench.resources import check_managed_path
    check_managed_path(source)
    ident = model + '_' + uuid.uuid4().hex[:16]
    path = artifact_path(ident); stage = VERSIONS / ('.' + ident)
    stage.mkdir(parents=True)
    if source.is_dir(): shutil.copytree(source,stage,dirs_exist_ok=True,ignore=shutil.ignore_patterns('artifact.json'))
    else: shutil.copy2(source,stage/source.name)
    files = {p.relative_to(stage).as_posix():sha256(p) for p in stage.rglob('*') if p.is_file()}
    if expected_files is not None and files!=expected_files:
        raise ValueError('登錄複本與核准模型清單不符，未發布版本')
    metadata = {'schema_version':1,'id':ident,'model':model,'experiment':experiment,'created':stamp(),'files':files,'artifact_hash':digest(files),'config':config,'demo_only':demo,'extra':extra or {}}
    write_json(stage/'artifact.json',metadata)
    stage.rename(path)
    audit('register_model',{'artifact':ident,'experiment':experiment})
    return metadata

def get(ident, verify=True):
    from src.workbench.resources import record, ResourceUnavailable
    if record('model',ident)['state']=='purged':raise ResourceUnavailable('model',ident,'purged')
    if verify: require_active('model',ident)
    path = artifact_path(ident)
    metadata = read_json(path/'artifact.json')
    if verify:
        for name, hash_value in metadata['files'].items():
            file = inside(path/name, path)
            if not file.is_file() or sha256(file)!=hash_value: raise ValueError('Model artifact integrity failure')
        if digest(metadata['files']) != metadata['artifact_hash']: raise ValueError('Artifact metadata mismatch')
    return metadata

def reports(ident):
    # Activation/evaluation authorization reads authoritative reports, not projections.
    return [r for p in sorted((ROOT/'runs/workbench/evaluations').glob('*/report.json')) if (r:=read_json(p)).get('artifact')==ident]

def listing(include_trashed=False):
    from src.workbench.storage import db
    import json
    with db() as con:
        evaluation_jobs=[dict(r) for r in con.execute("SELECT config,state,created FROM jobs WHERE kind='evaluate' ORDER BY created DESC")]
    states_path=ROOT/'data/snapshot_states.json'
    states=read_json(states_path) if states_path.exists() else {}
    result=[]
    by_artifact={}
    from src.workbench.queries.reports import summaries
    rows,_,_,_=summaries(ROOT,size=1000000)
    for report in reversed(rows):by_artifact.setdefault(report.get('artifact'),[]).append(report)
    latest_jobs={}
    for j in evaluation_jobs:latest_jobs.setdefault(json.loads(j['config']).get('artifact'),j)
    for meta in metadata_listing(include_trashed):
        evaluations=by_artifact.get(meta['id'],[])
        meta['reports']=[{**r,'applicable':r.get('snapshot') not in states} for r in evaluations]
        latest=latest_jobs.get(meta['id'])
        if evaluations and not meta['reports'][-1]['applicable']:state='not_applicable'
        elif latest and latest['state'] in ('queued','running'):state='pending' if latest['state']=='queued' else 'evaluating'
        elif latest and latest['state'] in ('failed','interrupted','cancelled'):state='failed'
        else:state='succeeded' if evaluations else 'pending'
        meta['evaluation_status']=state
        meta['active_evaluation']=bool(latest and latest['state'] in ('queued','running'))
        from src.workbench.contracts import experiment_task
        meta['task']=experiment_task(meta['model'],meta.get('extra',{}).get('task'))
        meta['label_scheme']=meta.get('extra',{}).get('label_scheme') or meta.get('config',{}).get('label_scheme') or ('detection_v1' if meta['model'].startswith('yolo') else 'binary_v1')
        with db() as con:
            row=con.execute('SELECT data FROM flags WHERE id=?',('model_attention:'+meta['id'],)).fetchone()
        meta['attention']=json.loads(row[0]) if row else None
        result.append(meta)
    return sorted(result,key=lambda x:x['created'],reverse=True)

def metadata_listing(include_trashed=False):
    """Recipe cards and overview don't need evaluation history or weight contents."""
    from src.workbench.queries.files import cached_many
    lifecycle=resource_states('model')
    paths=[p for p in VERSIONS.glob('*/artifact.json') if not p.parent.name.startswith('.') and (include_trashed or lifecycle.get(p.parent.name,'active')=='active')]
    return sorted((m for m in cached_many(paths,ROOT) if m.get('extra',{}).get('purpose')!='checkpoint'),key=lambda x:x['created'],reverse=True)

def count_active():return len(metadata_listing())

@guarded
def activate(ident, target='local', allow_unevaluated=False):
    if target not in ('local','line'): raise ValueError('Invalid reference')
    with file_lock(ROOT/'runtime/registry.lock'):
        metadata=get(ident)
        if metadata.get('extra',{}).get('purpose')=='checkpoint':raise ValueError('Checkpoint 不可啟用為推論模型')
        state_path=ROOT/'data/snapshot_states.json'
        snapshot_states=read_json(state_path) if state_path.exists() else {}
        matched=[r for r in reports(ident) if r['artifact_hash']==metadata['artifact_hash'] and r['config']==metadata['config'] and r['metrics']['complete'] and r.get('snapshot') not in snapshot_states]
        if not matched and (target=='line' or not allow_unevaluated): raise ValueError('A matching complete evaluation is required')
        path=REFS/(target+'.json')
        old=read_json(path) if path.exists() else None
        new={'artifact':ident,'updated':stamp(),'previous':old,'development_only':not bool(matched)}
        write_json(path,new)
        audit('activate_model',{'target':target,'artifact':ident,'previous':old})
        return new

@guarded
def rollback(target):
    path=REFS/(target+'.json')
    old=read_json(path)
    if not old.get('previous'): raise ValueError('No previous version')
    return activate(old['previous']['artifact'],target,old['previous'].get('development_only',False))

def import_legacy():
    """Copy the legacy selection into an immutable candidate without switching LINE."""
    marker=REFS/'legacy_import.json'
    if marker.exists(): return read_json(marker)
    selected=ROOT/'models/selected'
    if not (selected/'best.pt').exists(): return None
    meta=read_json(selected/'metadata.json')
    if sha256(selected/'best.pt')!=meta['weights_sha256']: raise ValueError('Legacy selected weight mismatch')
    from src.workbench.contracts import InferenceConfig
    config=InferenceConfig(threshold=meta.get('confidence',.5)).model_dump()
    legacy_report=read_json(selected/'evaluation.json') if (selected/'evaluation.json').exists() else {}
    extra={'legacy_metadata':meta}
    if legacy_report.get('dataset'):extra['dataset']=inside(legacy_report['dataset']).relative_to(ROOT).as_posix()
    item=register(selected/'best.pt','yolo11n',config,'legacy:'+meta['model_version'],meta.get('demo_only',True),extra)
    write_json(marker,{'artifact':item['id']})
    return {'artifact':item['id']}
