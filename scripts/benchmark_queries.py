"""Synthetic-only scale comparison. Does not run training or change real data."""
import json
import math
import statistics
import sys
import tempfile
import time
from pathlib import Path

PROJECT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(PROJECT),str(PROJECT/'tests')]
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from workbench_fixture import configure
from src import common
from src.workbench import views,storage
from src.workbench.queries import data_index

def measure(fn,n=50):
    t=time.perf_counter();value=fn();first=(time.perf_counter()-t)*1000;times=[]
    for _ in range(n):
        t=time.perf_counter();value=fn();times.append((time.perf_counter()-t)*1000)
    return {'n':n,'first_ms':first,'median_ms':statistics.median(times),'p95_ms':sorted(times)[math.ceil(n*.95)-1],'bytes':len(json.dumps(value,ensure_ascii=False).encode())}

results=[]
for count in (91,910):
    with tempfile.TemporaryDirectory(prefix='phlebitis-scale-') as directory,pytest.MonkeyPatch.context() as patch:
        root=Path(directory);app,_=configure(root,patch,include_reports=True)
        rows=common.read_manifest(root)
        for i in range(len(rows),count):
            ident=f'scale_{i:05}';path=root/'data/pending_review/scale'/f'{ident}.png';path.parent.mkdir(parents=True,exist_ok=True)
            Image.new('RGB',(100,80),(i%256,i//256,123)).save(path)
            row={**rows[8],'image_id':ident,'image_path':path.relative_to(root).as_posix(),'sha256':common.sha256(path),'yolo_path':'','annotation_path':''};rows.append(row)
        common.write_manifest(rows,root);data_index.rebuild(root)
        result={'photos':count,'source_bytes':sum((root/r['image_path']).stat().st_size for r in rows)}
        result['legacy_query']=measure(lambda:views.query_data(root=root))
        result['indexed_query']=measure(lambda:data_index.query(root))
        with storage.db() as con:
            for i in range(49 if count==91 else 490):
                ident=f'{i+9000:032x}'
                con.execute('INSERT INTO jobs(id,idem,kind,state,config,created,updated) VALUES(?,?,?,?,?,?,?)',(ident,None,'train','failed','{}',100,100))
            result['jobs']=con.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
            result['plans']={'classification':[tuple(r) for r in con.execute("EXPLAIN QUERY PLAN SELECT payload FROM data_index WHERE status='approved' AND eligible=1 ORDER BY id LIMIT 30")], 'scheduler':[tuple(r) for r in con.execute("EXPLAIN QUERY PLAN SELECT id FROM jobs WHERE state IN ('queued','running','cancelling')")]}
        sample=next((root/'runs/workbench/evaluations').glob('*/report.json'));template=common.read_json(sample)
        for i in range(15 if count==91 else 150):common.write_json(root/'runs/workbench/evaluations'/f'{i+8000:032x}'/'report.json',template)
        result['reports']=len(list((root/'runs/workbench/evaluations').glob('*/report.json')))
        with TestClient(app) as client:
            for endpoint in ('/data-query','/overview','/jobs-query','/reports-query','/artifacts','/curve-sources','/cases-query','/audit-query','/trash'):
                def query():
                    response=client.get('/api/v1'+endpoint);response.raise_for_status();return response.json()
                result[endpoint]=measure(query)
        results.append(result);print(json.dumps(result,ensure_ascii=False),flush=True)
out=PROJECT/'runtime/performance/scaled-queries.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
