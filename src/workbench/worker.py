import sys
import traceback
from src.common import ROOT, read_json, write_json
from src.lock import OperationLock
from src.workbench import jobs, adapters, registry
from src.workbench.contracts import Experiment

def main(ident):
    path=jobs.folder(ident); request=read_json(path/'request.json'); config=request['config']
    from src.workbench.storage import operator
    operator.set(request.get('actor'))
    state='failed'; error=None
    try:
        with OperationLock():
            adapters.check_cancel(path)
            kind=request['kind']
            if kind=='prepare':
                output=adapters.prepare_verified(config['model'],path); result={'path':str(output.relative_to(ROOT))}
            elif kind=='train':
                cfg=Experiment(**config)
                output,effective=adapters.train(cfg,path)
                adapters.check_cancel(path)
                artifact=registry.register(output,cfg.model,cfg.inference.model_dump(),ident,cfg.demo,{'effective':effective,'dataset':cfg.dataset})
                evaluation=jobs.enqueue('evaluate',{'artifact':artifact['id'],'dataset':cfg.dataset,'device':cfg.device},idem='evaluate:'+artifact['id'])
                result={'artifact':artifact['id'],'evaluation_job':evaluation['id']}
            elif kind=='evaluate':
                output=ROOT/'runs/workbench/evaluations'/ident; output.mkdir(parents=True,exist_ok=True)
                report=adapters.evaluate(config['artifact'],config['dataset'],config.get('device','0'),output)
                result={'artifact':config['artifact'],'report':str((output/'report.json').relative_to(ROOT)),'metrics':report['metrics']}
                from src.workbench.storage import db
                import json
                with db() as con:confirmed=any(json.loads(r[0]).get('state')=='confirmed' for r in con.execute('SELECT data FROM cases'))
                if confirmed:
                    regression=jobs.enqueue('regression',{'artifact':config['artifact'],'device':config.get('device','0')},idem='post-evaluation-regression:'+ident)
                    result['regression_job']=regression['id']
            elif kind=='predict':
                from src.workbench.simulation import process
                result=process(config,path)
            elif kind=='regression':
                from src.workbench.simulation import run_regression
                result=run_regression(config,path)
            write_json(path/'result.json',result)
        state='cancelled' if jobs.get(ident)['state']=='cancelling' else 'succeeded'
    except adapters.Cancelled as exc: state='cancelled'; error=str(exc)
    except BaseException as exc:
        traceback.print_exc()
        error=type(exc).__name__+': '+str(exc)
    finally:
        try:
            from src.workbench.trash import seal_job
            from src.workbench.resources import resource_lock
            seal_job(ident)
            with resource_lock():
                if jobs.get(ident)['state']=='cancelling' and state=='succeeded':state='cancelled'
                jobs.update(ident,state,error)
        except Exception:
            traceback.print_exc()
            jobs.update(ident,'failed','無法完成產物歸屬紀錄；請檢查工作日誌')

if __name__=='__main__': main(sys.argv[1])
