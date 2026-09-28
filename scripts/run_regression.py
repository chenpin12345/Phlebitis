"""Manual/CI entry point for real local regression cases. Never activates models."""
import argparse,json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.workbench.jobs import enqueue,get,Manager,TERMINAL

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--artifact',required=True)
    parser.add_argument('--device',choices=['cpu','0'],default='cpu')
    args=parser.parse_args()
    job=enqueue('regression',{'artifact':args.artifact,'device':args.device})
    manager=Manager();manager.start()
    try:
        while True:
            item=get(job['id'])
            if item['state'] in TERMINAL:break
            time.sleep(1)
        print(json.dumps(item['result'] or {'error':item['error']},ensure_ascii=False,indent=2))
        if item['state']!='succeeded':return 1
        outcomes=item['result']['cases']
        return int(any(c.get('functional_pass') is False or c.get('score_range_pass') is False or c.get('latency_pass') is False or c.get('error') for c in outcomes))
    finally:manager.close()

if __name__=='__main__':raise SystemExit(main())
