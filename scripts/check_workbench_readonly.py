"""Read-only acceptance check on real metadata; never schedules jobs or starts training."""
import json
from fastapi.testclient import TestClient
from src.common import ROOT, write_json
from src.workbench.api import create_app
from src.workbench import registry
from src.lock import OperationLock

def main():
    evidence={'training_started':False,'scheduler_started':False}
    with TestClient(create_app(testing=True)) as client:
        overview=client.get('/api/v1/overview');overview.raise_for_status();stats=overview.json()
        evidence['counts']=stats['data']
        evidence['views']={}
        for view in ('approved','pending_review','excluded','reviewed','all'):
            response=client.get('/api/v1/data-query',params={'view':view,'size':100});response.raise_for_status();data=response.json()
            assert data['total']==stats['data'][view]
            evidence['views'][view]={'total':data['total'],'matches_overview':True}
        artifacts=client.get('/api/v1/artifacts');artifacts.raise_for_status()
        evidence['artifact_count']=len(artifacts.json())
        evidence['curve_sources']=len(client.get('/api/v1/curve-sources').json())
        active=[j for j in stats['jobs'] if j['state'] in ('running','cancelling')]
        evidence['active_jobs']=len(active)
        candidate=next((a for a in artifacts.json() if a['model']=='yolo11n'),None)
        if active:evidence['model_load']='not run: a compute job is active'
        elif candidate:
            # Read actual local weights on CPU; no fit/predict/evaluate or network calls.
            from src.workbench.adapters import ModelPredictor
            with OperationLock():
                predictor=ModelPredictor(candidate['id'],'cpu')
                assert predictor.model.names=={0:'phlebitis'}
                evidence['model_load']={'artifact':candidate['id'],'device':'cpu','class_names':predictor.model.names,'passed':True}
            response=client.get('/api/v1/artifacts/'+candidate['id']+'/detail');response.raise_for_status()
            evidence['artifact_detail_readable']=True
            raw=client.get('/api/v1/artifacts/'+candidate['id']+'/export');raw.raise_for_status()
            assert raw.json()['inference']==registry.get(candidate['id'])['config']
            evidence['export_preserves_inference']=True
    write_json(ROOT/'docs/verification/real-data-readonly.json',evidence)
    print(json.dumps(evidence,ensure_ascii=False))

if __name__=='__main__':main()
