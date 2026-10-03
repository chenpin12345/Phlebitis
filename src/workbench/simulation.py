from __future__ import annotations
import json
import time
import uuid
from src.common import ROOT, inside, read_json, write_json, sha256
from src.line_bot.service import Store
from src.line_bot.messages import command, text_message, results
from src.workbench.storage import HOME, db, audit,file_lock

def store(clock=None):
    return Store(HOME/'simulation.sqlite3',reconcile=False,**({'clock':clock} if clock else {}))

def record_event(event_id,session,message,status,payload):
    with db() as con:
        con.execute('INSERT OR REPLACE INTO events(id,session,message,status,payload,updated) VALUES(?,?,?,?,?,?)',(event_id,session,message,status,json.dumps(payload,ensure_ascii=False),time.time()))

def dispatch(payload):
    from src.workbench.resources import resource_lock
    with resource_lock(),file_lock(HOME/'simulation-dispatch.lock'):
        return _dispatch(payload)

def _dispatch(payload):
    from src.workbench.jobs import enqueue,listing
    session=payload.get('session','demo-1')
    if not isinstance(session,str) or len(session)>80: raise ValueError('Invalid synthetic user')
    mid=payload.get('message_id') or uuid.uuid4().hex
    eid=payload.get('event_id') or uuid.uuid4().hex
    now=float(payload.get('clock',time.time()))
    if not __import__('math').isfinite(now):raise ValueError('Clock must be finite')
    if payload.get('type')!='unsend' and payload.get('text') is None:
        from src.workbench.registry import get,reports
        from src.workbench.lifecycle import asset_path
        asset_path(payload.get('asset'))
        if payload.get('scenario')!='missing_model':
            model=get(payload.get('artifact'))
            if not reports(model['id']) and not payload.get('development',False):raise ValueError('未評估模型必須明確勾選開發測試')
        if payload.get('device','0') not in ('cpu','0'):raise ValueError('Invalid device')
    scoped_mid=session+':'+mid
    s=store(lambda:now)
    try:
        if payload.get('type')=='unsend':
            s.unsend(scoped_mid)
            with db() as con:
                rows=con.execute('SELECT id,payload FROM events WHERE session=? AND message=?',(session,mid)).fetchall()
            for row in rows:
                data=json.loads(row['payload'])
                if data.get('job'):
                    from src.workbench.jobs import cancel
                    from src.workbench.resources import record
                    if record('job',data['job'])['state']=='active':cancel(data['job'])
                if data.get('trace_id'):
                    from src.workbench.jobs import folder
                    (folder(data['trace_id'])/'result.jpg').unlink(missing_ok=True)
                record_event(row['id'],session,mid,'cancelled',data)
            return {'status':'cancelled','message_id':mid}
        text=payload.get('text')
        state=s.reserve(eid,scoped_mid,session,'completed' if text is not None else 'queued')
        if state!='accepted':
            data={'status':state,'event_id':eid,'message_id':mid}
            if state=='busy':
                s.reserve(eid,scoped_mid,session,'rejected')
                data['messages']=[text_message('上一張照片仍在處理，請等待結果後再傳送。')]
                record_event(eid,session,mid,'rejected',data)
            return data
        if text is not None:
            data={'messages':[text_message(command(str(text)))],'route':'reply','event_id':eid,'message_id':mid}
            record_event(eid,session,mid,'completed',data);return data
        if len([j for j in listing() if j['kind']=='predict' and j['state'] not in {'failed','succeeded','cancelled','interrupted'}])>=4 or payload.get('scenario')=='queue_full':
            s.update(eid,'rejected'); data={'status':'rejected','messages':[text_message('目前分析工作已滿，請稍後重新傳送。')]}
            record_event(eid,session,mid,'rejected',data); return data
        config={k:payload[k] for k in ('asset','artifact','device','scenario','development') if k in payload}
        config.update(session=session,event_id=eid,message_id=mid,clock=now)
        try:job=enqueue('predict',config,idem='simulation:'+eid)
        except BaseException:
            s.update(eid,'failed',error='enqueue_failed');raise
        data={'job':job['id'],'event_id':eid,'message_id':mid,'status':'queued'}
        record_event(eid,session,mid,'queued',data)
        return data
    finally:s.close()

def process(config,folder):
    from src.workbench.adapters import ModelPredictor
    from src.workbench.lifecycle import asset_path
    eid=config['event_id']; s=store()
    try:
        if s.cancelled(eid): return {'status':'cancelled'}
        s.update(eid,'running')
        if config.get('scenario')=='download_failure': raise ValueError('Simulated image download failure')
        if config.get('scenario')=='missing_model': raise ValueError('Simulated model missing; prepare a trained artifact')
        raw=asset_path(config['asset']).read_bytes()
        predictor=ModelPredictor(config['artifact'],config.get('device','0'))
        record,jpeg=predictor.predict(raw)
        # In a timeout replay, computation still finishes before the resource lease exits.
        if config.get('scenario')=='timeout': raise TimeoutError('Simulated analysis deadline exceeded; compute drained')
        if s.cancelled(eid): return {'status':'cancelled'}
        (folder/'result.jpg').write_bytes(jpeg)
        url='/api/v1/jobs/'+folder.name+'/image'
        payload=results(record,url)
        route='push' if config.get('scenario')=='push' or time.time()-config['clock']>=45 else 'reply'
        delivery='delivery_unconfirmed' if config.get('scenario')=='send_failure' else 'sent'
        data={'result':record,'messages':payload,'delivery':delivery,'route':route,'trace_id':folder.name,'event_id':eid,'message_id':config['message_id'],'input_sha256':__import__('hashlib').sha256(raw).hexdigest(),'artifact':config['artifact'],'dataset':predictor.metadata.get('extra',{}).get('dataset'),'simulated':True,'browser_rendering':'approximation; actual LINE client not verified','expires':time.time()+3600}
        s.update(eid,'completed',error=delivery if delivery!='sent' else None)
        record_event(eid,config['session'],config['message_id'],'completed',data)
        return data
    except Exception as exc:
        s.update(eid,'failed',error=type(exc).__name__)
        record_event(eid,config['session'],config['message_id'],'failed',{'error':str(exc),'messages':[text_message('分析失敗，請檢查除錯資訊後重試。')]})
        raise
    finally:s.close()

def reconcile(jobs):
    s=store()
    try:
        for job in jobs:
            if job['kind']!='predict' or job['state'] not in {'cancelled','interrupted','failed'}:continue
            eid=job['config']['event_id']
            row=s.db.execute('SELECT status FROM jobs WHERE event_id=?',(eid,)).fetchone()
            if row and row[0] in ('queued','running'):
                s.update(eid,'cancelled' if job['state']=='cancelled' else 'failed',error=job['state'])
                record_event(eid,job['config']['session'],job['config']['message_id'],job['state'],{'error':job['error'],'job':job['id']})
    finally:s.close()

def validate_expectations(case):
    import math
    bounds=case.get('score_range')
    if bounds is not None and (not isinstance(bounds,list) or len(bounds)!=2 or not all(isinstance(x,(int,float)) and math.isfinite(x) for x in bounds) or not 0<=bounds[0]<=bounds[1]<=1):raise ValueError('score_range must be [minimum,maximum] within 0..1')
    latency=case.get('max_latency_ms')
    if latency is not None and (not isinstance(latency,(int,float)) or not math.isfinite(latency) or latency<=0):raise ValueError('max_latency_ms must be positive')
    events=case.get('conversation',[])
    if not isinstance(events,list) or len(events)>30:raise ValueError('Conversation replay supports at most 30 events')
    for e in events:
        if e.get('type') not in ('reserve','unsend','complete','text'):raise ValueError('Unsupported replay event')
        if not isinstance(e.get('at',0),(int,float)) or not math.isfinite(e.get('at',0)):raise ValueError('Invalid replay clock')

def replay_conversation(events,path):
    """Replay shared LINE event rules with an isolated database and no network client."""
    clock=[0.];s=Store(path,clock=lambda:clock[0],reconcile=False);out=[]
    try:
        for i,e in enumerate(events):
            clock[0]=e.get('at',clock[0]);kind=e['type'];eid=e.get('event_id',str(i));mid=e.get('message_id',eid)
            if kind=='unsend':s.unsend(mid);actual='cancelled'
            elif kind=='complete':s.update(eid,'completed');actual='completed'
            elif kind=='text':actual=command(e.get('text',''))
            else:actual=s.reserve(eid,mid,e.get('user','synthetic'))
            expected=e.get('expected');passed=actual==expected if expected is not None else None
            out.append({'event':i,'actual':actual,'expected':expected,'pass':passed})
    finally:s.close()
    return out

def run_regression(config,folder):
    from src.workbench.adapters import ModelPredictor,check_cancel,progress
    from src.workbench.lifecycle import asset_path
    predictor=ModelPredictor(config['artifact'],config.get('device','0'))
    with db() as con: cases=[json.loads(r[0]) for r in con.execute('SELECT data FROM cases')]
    cases=[c for c in cases if c.get('state')=='confirmed']
    previous={};baseline_id=None
    from src.workbench.resources import require_active
    from src.workbench import jobs
    baseline_id=config.get('baseline_job')
    if baseline_id:
        require_active('job',baseline_id)
        report=read_json(jobs.folder(baseline_id)/'regression.json')
        previous={(c['case'],c.get('revision')):c for c in report['cases']}
    outcomes=[]
    for case in cases:
        check_cancel(folder)
        try:
            validate_expectations(case)
            record,_=predictor.predict(asset_path(case['asset']).read_bytes())
            expected=case.get('expected_status')
            passed=record['status']==expected if expected else None
            conversation=replay_conversation(case.get('conversation',[]),folder/(case['id']+'-conversation.sqlite3'))
            if any(e['pass'] is False for e in conversation):passed=False
            score=record.get('prediction_score');bounds=case.get('score_range')
            latency=record['elapsed_ms'];limit=case.get('max_latency_ms')
            correct=record['binary_prediction']==int(case['label']=='positive') if case.get('label') in ('positive','negative') else None
            old=previous.get((case['id'],case['revision']))
            change='no_matching_baseline'
            if old and old.get('model_correct') is not None and correct is not None:change='unchanged' if correct==old['model_correct'] else 'improved' if correct else 'regressed'
            outcomes.append({'case':case['id'],'revision':case['revision'],'expected':expected,'actual':record['status'],'functional_pass':passed,'latency_ms':latency,'latency_pass':latency<=limit if limit is not None else None,'score_range_pass':bool(score is not None and bounds[0]<=score<=bounds[1]) if bounds else None,'label_confirmed':case.get('label') in ('positive','negative'),'model_correct':correct,'change':change,'conversation':conversation})
        except Exception as exc:outcomes.append({'case':case['id'],'error':str(exc),'functional_pass':False})
        progress(folder,'regression',completed=len(outcomes),total=len(cases))
    result={'artifact':config['artifact'],'artifact_hash':predictor.metadata['artifact_hash'],'inference_config':predictor.metadata['config'],'baseline_job':baseline_id,'cases':outcomes,'note':'人工案例回歸，不是獨立測試集；基準輸出不是真實標籤。改善／退步僅比較同一人工案例版本；不自動啟用模型。'}
    write_json(folder/'regression.json',result); return result
