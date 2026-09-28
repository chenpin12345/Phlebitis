"""Explicit finite real-model acceptance. No LINE activation or real messages."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.common import ROOT,write_json
from src.data.dataset import build
from src.workbench.jobs import enqueue
from src.workbench.contracts import MODELS,Experiment

def main():
    snapshot=build(demo=True)
    dataset=snapshot['folds'][0]['dataset']
    records=[]
    for model in MODELS:
        cfg=Experiment(model=model,dataset=dataset,device='0',demo=True,epochs=2,batch=2,imgsz=320,patience=2,inference={'imgsz':320},parameters={'max_iter':100} if model=='dinov2_small' else {})
        job=enqueue('train',cfg.model_dump())
        records.append({'model':model,'job':job['id']})
    result={'purpose':'finite workflow acceptance; NOT clinical or performance validation','snapshot':snapshot['version'],'jobs':records,'line_activated':False}
    write_json(ROOT/'docs/workbench-smoke.json',result)
    print(result)

if __name__=='__main__':main()
