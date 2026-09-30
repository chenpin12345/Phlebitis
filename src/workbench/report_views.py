"""Historical reports stay independent of executable model/job lifecycles."""
from src.common import read_json, inside
from src.workbench import jobs, registry, resources
from src.workbench.contracts import MODELS


def get(ident):
    jobs.folder(ident)
    return read_json(registry.ROOT/'runs/workbench/evaluations'/ident/'report.json')


def listing():
    root=registry.ROOT;path=root/'data/snapshot_states.json'
    snapshot_states=read_json(path) if path.exists() else {}
    model_states=resources.states('model');job_states=resources.states('job')
    result=[]
    for p in sorted((root/'runs/workbench/evaluations').glob('*/report.json')):
        r=read_json(p)
        result.append({**r,'report_id':p.parent.name,'snapshot_state':snapshot_states.get(r.get('snapshot')),
                       'source_model_state':model_states.get(r.get('artifact'),'active'),
                       'source_job_state':job_states.get(p.parent.name,'active')})
    return result


def query(model='',page=1,size=30):
    if page<1 or not 1<=size<=100:raise ValueError('無效的報告分頁')
    reports=listing();options=sorted(set(MODELS)|{r['model'] for r in reports})
    if model and len(model)>100:raise ValueError('模型識別碼過長')
    rows=[r for r in reports if not model or r.get('model')==model]
    rows.sort(key=lambda r:(r.get('evaluated_at') or '',r['report_id']),reverse=True)
    total=len(rows);page=min(page,max(1,(total+size-1)//size))
    return {'items':[{k:v for k,v in r.items() if k!='samples'} for r in rows[(page-1)*size:page*size]],
            'total':total,'page':page,'size':size,'models':options}


def samples(ident,page=1,size=30):
    if page<1 or not 1<=size<=100:raise ValueError('無效的樣本分頁')
    report=get(ident);rows=report.get('samples',[])
    page=min(page,max(1,(len(rows)+size-1)//size))
    return {'items':rows[(page-1)*size:page*size],'total':len(rows),'page':page,'size':size}


def image_path(ident,image):
    report=get(ident)
    if not image.replace('_','').replace('-','').isalnum() or image not in {s['image_id'] for s in report.get('samples',[])}:
        raise ValueError('圖片不屬於此評估報告')
    state_path=registry.ROOT/'data/snapshot_states.json'
    states=read_json(state_path) if state_path.exists() else {}
    if states.get(report.get('snapshot'),{}).get('status')=='withdrawn':raise ValueError('此報告圖片的授權資料已撤回')
    base=registry.ROOT/'runs/workbench/evaluations'/ident
    path=inside(base/(image+'.jpg'),base)
    if not path.is_file():raise FileNotFoundError('評估時保存的圖片不存在；未使用目前 manifest 圖片替代。')
    return path
