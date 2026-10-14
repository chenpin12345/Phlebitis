"""Historical reports stay independent of executable model/job lifecycles."""
from src.common import read_json, inside
from src.workbench import jobs, registry, resources
from src.workbench.contracts import MODELS
from src.workbench.views import redact


def get(ident):
    jobs.folder(ident)
    return read_json(registry.ROOT/'runs/workbench/evaluations'/ident/'report.json')


def model_state(ident,states):
    if ident in states:return states[ident]
    try:exists=bool(ident) and (registry.artifact_path(ident)/'artifact.json').is_file()
    except (ValueError,TypeError,OSError):exists=False
    return 'active' if exists else 'unrecorded'


def purged_models(states=None):
    """Artifacts permanently deleted from the trash; their reports are no longer listed."""
    states=resources.states('model') if states is None else states
    return {ident for ident,state in states.items() if state=='purged'}


def listing():
    root=registry.ROOT;path=root/'data/snapshot_states.json'
    snapshot_states=read_json(path) if path.exists() else {}
    model_states=resources.states('model');job_states=resources.states('job')
    with jobs.db() as con:known_jobs={r[0] for r in con.execute('SELECT id FROM jobs')}
    result=[]
    for p in sorted((root/'runs/workbench/evaluations').glob('*/report.json')):
        r=read_json(p)
        result.append({**r,'report_id':p.parent.name,'snapshot_state':snapshot_states.get(r.get('snapshot')),
                       'source_model_state':model_state(r.get('artifact'),model_states),
                       'source_job_state':job_states.get(p.parent.name,'active' if p.parent.name in known_jobs else 'unrecorded')})
    return redact(result)


def query(model='',page=1,size=30):
    if page<1 or not 1<=size<=100:raise ValueError('無效的報告分頁')
    from src.workbench.queries import reports as index
    states=resources.states('model');job_states=resources.states('job')
    rows,total,page,models=index.summaries(registry.ROOT,model,page,size,exclude_artifacts=purged_models(states))
    with jobs.db() as con:known={r[0] for r in con.execute('SELECT id FROM jobs')}
    path=registry.ROOT/'data/snapshot_states.json';snapshots=read_json(path) if path.exists() else {}
    for row in rows:
        row.update(source_model_state=model_state(row.get('artifact'),states),source_job_state=job_states.get(row['report_id'],'active' if row['report_id'] in known else 'unrecorded'),snapshot_state=snapshots.get(row.get('snapshot')))
    return {'items':redact(rows),'total':total,'page':page,'size':size,'models':sorted(set(MODELS)|set(models))}


def samples(ident,page=1,size=30,image=''):
    if page<1 or not 1<=size<=100:raise ValueError('無效的樣本分頁')
    jobs.folder(ident)
    from src.workbench.queries import reports as index
    return redact(index.samples(registry.ROOT,ident,page,size,image))


def image_path(ident,image):
    report=get(ident)
    if not image.replace('_','').replace('-','').isalnum() or image not in {s['image_id'] for s in report.get('samples',[])}:
        raise ValueError('圖片不屬於此評估報告')
    state_path=registry.ROOT/'data/snapshot_states.json'
    states=read_json(state_path) if state_path.exists() else {}
    status=states.get(report.get('snapshot'))
    if status:
        from fastapi import HTTPException
        raise HTTPException(410,'此報告圖片的授權資料已撤回或到期')
    base=registry.ROOT/'runs/workbench/evaluations'/ident
    path=inside(base/(image+'.jpg'),base)
    if not path.is_file():raise FileNotFoundError('評估時保存的圖片不存在；未使用目前 manifest 圖片替代。')
    return path
