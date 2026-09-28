"""Re-evaluate existing smoke artifacts and reload all five through the simulator.

This deliberately does not start new training or activate a LINE model.
Run with a workbench server/manager available; reruns reuse recorded jobs.
"""
import argparse,json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.common import ROOT,read_json,write_json,inside,sha256
from src.workbench import jobs,lifecycle,simulation

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--refresh-evaluations',action='store_true');args=parser.parse_args()
    evidence_path=ROOT/'docs/workbench-smoke.json';evidence=read_json(evidence_path)
    selected=ROOT/'models/selected/best.pt';baseline_hash=sha256(selected)
    manager=jobs.Manager();manager.start()
    try:
        for item in evidence['jobs']:
            training=jobs.get(item['job'])
            if training['state']!='succeeded':raise RuntimeError(f"Training incomplete: {item['model']}")
            artifact=training['result']['artifact'];item['artifact']=artifact
            if args.refresh_evaluations or not item.get('evaluation_job'):
                evaluation=jobs.enqueue('evaluate',{'artifact':artifact,'dataset':training['config']['dataset'],'device':'0'})
                item['evaluation_job']=evaluation['id']
            write_json(evidence_path,evidence)
            while (evaluation:=jobs.get(item['evaluation_job']))['state'] not in jobs.TERMINAL:time.sleep(1)
            if evaluation['state']!='succeeded':raise RuntimeError(evaluation['error'])
            item['metrics']=evaluation['result']['metrics']
            split=read_json(inside(training['config']['dataset']).parent/'split.json')
            source=inside(split['members']['val'][0]['image_path'])
            asset=lifecycle.upload(source.read_bytes())
            event=simulation.dispatch({'session':'final-acceptance-'+item['model'],'artifact':artifact,'asset':asset['id'],'device':'0'})
            if 'job' not in event:raise RuntimeError(str(event))
            item['simulation_job']=event['job'];write_json(evidence_path,evidence)
            while (prediction:=jobs.get(event['job']))['state'] not in jobs.TERMINAL:time.sleep(1)
            if prediction['state']!='succeeded':raise RuntimeError(prediction['error'])
            item['reload_and_simulation']='passed'
            item['result_task']=prediction['result']['result']['task_type']
            item['status']=prediction['result']['result']['status']
            print(item['model'],item['metrics']['accuracy_display'],'reload + simulation passed',flush=True)
            write_json(evidence_path,evidence)
        evidence['all_five_paths_passed']=True
        evidence['original_selected_weight_unchanged']=sha256(selected)==baseline_hash
        evidence['line_reference_created']=(ROOT/'models/references/line.json').exists()
        write_json(evidence_path,evidence)
        return 0
    finally:manager.close()

if __name__=='__main__':raise SystemExit(main())
