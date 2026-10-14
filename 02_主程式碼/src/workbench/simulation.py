from __future__ import annotations
import json
import time
import uuid
from src.common import ROOT, inside, read_json, write_json, sha256
from src.common import config_path
from src.line_bot.service import Store
from src.line_bot.messages import command, text_message, results
from src.workbench.storage import HOME, db, audit,file_lock

def store(clock=None):
    return Store(HOME/'simulation.sqlite3',reconcile=False,**({'clock':clock} if clock else {}))

def record_event(event_id,session,message,status,payload):
    with db() as con:
        con.execute('INSERT OR REPLACE INTO events(id,session,message,status,payload,updated) VALUES(?,?,?,?,?,?)',(event_id,session,message,status,json.dumps(payload,ensure_ascii=False),time.time()))

PENDING=HOME/'line_pending'
SCENARIOS={'','queue_full','missing_model','download_failure','timeout','send_failure','push','inference_failure','unsupported_task','corrupt_image','too_large','unsupported_format'}
DELIVERY_NOTE='模擬送達：只表示本機模擬 transport 已記錄，不是 LINE 平台回執'

def conversation(session,s,now):
    from src.line_bot.conversation import Conversation
    # Local transport: synthetic user key, no LINE token/secret/tunnel, never calls the Messaging API.
    return Conversation(s,source='simulator',user_key=lambda user:'sim:'+user,pending_dir=PENDING,
                        message_id_pattern=r'[A-Za-z0-9_\-:.]{1,200}',clock=lambda:now,session=session)

def add_message(session,direction,kind,payload,status,event_id=None):
    now=time.time()
    with db() as con:
        cur=con.execute('INSERT INTO sim_messages(session,direction,event_id,kind,payload,status,created,updated) VALUES(?,?,?,?,?,?,?,?)',
                        (session,direction,event_id,kind,json.dumps(payload,ensure_ascii=False),status,now,now))
        return cur.lastrowid

def set_status(session,event_id,status,direction='user'):
    with db() as con:con.execute('UPDATE sim_messages SET status=?,updated=? WHERE session=? AND event_id=? AND direction=?',(status,time.time(),session,event_id,direction))

def user_message(session,event_id):
    with db() as con:
        row=con.execute("SELECT id,status FROM sim_messages WHERE session=? AND event_id=? AND direction='user'",(session,event_id)).fetchone()
    return dict(row) if row else None

def deliver(session,event_id,messages,scenario=''):
    """Local transport 'send'. Status is a simulation status, never a LINE receipt."""
    status='failed_simulated' if scenario=='send_failure' else 'delivered_simulated'
    for m in messages:add_message(session,'bot',m.get('type','unknown'),m,status,event_id)
    return status

def dispatch(payload):
    from src.workbench.resources import resource_lock
    with resource_lock(),file_lock(HOME/'simulation-dispatch.lock'):
        return _dispatch(payload)

def _dispatch(payload):
    from src.line_bot.conversation import Incoming,Reply,Enqueue,Unsent
    from src.workbench.jobs import enqueue,listing
    session=payload.get('session','demo-1')
    if not isinstance(session,str) or not 1<=len(session)<=80: raise ValueError('Invalid synthetic user')
    mid=payload.get('message_id') or uuid.uuid4().hex
    eid=payload.get('event_id') or uuid.uuid4().hex
    now=float(payload.get('clock',time.time()))
    if not __import__('math').isfinite(now):raise ValueError('Clock must be finite')
    scenario=payload.get('scenario') or ''
    if scenario not in SCENARIOS:raise ValueError('Unknown simulation scenario')
    kind=payload.get('type') or ('text' if payload.get('text') is not None else 'image')
    if kind not in ('text','image','postback','unsend','follow'):raise ValueError('Unsupported simulated event')
    if kind=='image':
        from src.workbench.registry import get,reports
        from src.workbench.lifecycle import asset_path
        asset_path(payload.get('asset'))
        if scenario not in ('missing_model','corrupt_image','too_large','unsupported_format'):
            if not payload.get('artifact'):raise ValueError('尚未選擇模型；可改用「無模型」情境測試')
            model=get(payload.get('artifact'))
            if not reports(model['id']) and not payload.get('development',False):raise ValueError('未評估模型必須明確勾選開發測試')
        if payload.get('device','0') not in ('cpu','0'):raise ValueError('Invalid device')
    scoped_mid=session+':'+mid
    s=store(lambda:now)
    try:
        conv=conversation(session,s,now)
        retry=user_message(session,eid)
        if kind=='unsend':
            conv.handle(Incoming('unsend',None,scoped_mid,session))
            with db() as con:
                rows=con.execute('SELECT id,payload FROM events WHERE session=? AND message=?',(session,mid)).fetchall()
                con.execute("UPDATE sim_messages SET status='unsent',updated=? WHERE session=? AND direction='user' AND json_extract(payload,'$.message_id')=?",(time.time(),session,mid))
                con.execute("UPDATE sim_messages SET status='withdrawn_by_unsend',updated=? WHERE session=? AND direction='bot' AND event_id IN (SELECT event_id FROM sim_messages WHERE session=? AND direction='user' AND json_extract(payload,'$.message_id')=?)",(time.time(),session,session,mid))
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
        shown={'text':{'text':payload.get('text','')},'follow':{'text':'（加入好友）'},'postback':{'text':payload.get('display') or '（選單操作）','data':payload.get('data')},
               'image':{'asset':payload.get('asset')}}[kind]
        if retry is None:add_message(session,'user','image' if kind=='image' else 'text',{**shown,'message_id':mid,'event':kind},'sending',eid)
        else:set_status(session,eid,'sending')
        incoming={'text':lambda:Incoming('text',eid,scoped_mid,session,'sim',text=str(payload.get('text',''))),
                  'follow':lambda:Incoming('follow',eid,'',session,'sim',text='專題介紹'),
                  'postback':lambda:Incoming('postback',eid,'postback:'+eid,session,'sim',data=payload.get('data')),
                  'image':lambda:Incoming('image',eid,scoped_mid,session,'sim')}[kind]()
        busy_queue=kind=='image' and (scenario=='queue_full' or len([j for j in listing() if j['kind']=='predict' and j['state'] not in {'failed','succeeded','cancelled','interrupted'}])>=4)
        actions=conv.handle(incoming)
        result={'event_id':eid,'message_id':mid,'status':'duplicate' if not actions else 'accepted','retry':retry is not None}
        for action in actions:
            if isinstance(action,Reply):
                result['delivery']=deliver(session,eid,action.messages,scenario)
                result['messages']=action.messages
                record_event(eid,session,mid,'completed',{'messages':action.messages,'route':'reply','event_id':eid,'message_id':mid})
            elif isinstance(action,Enqueue):
                if busy_queue:
                    message=conv.queue_full(eid);deliver(session,eid,[message])
                    record_event(eid,session,mid,'rejected',{'status':'rejected','messages':[message]})
                    result.update(status='rejected',messages=[message]);continue
                config={k:payload[k] for k in ('asset','artifact','device','development') if k in payload}
                config.update(session=session,event_id=eid,message_id=mid,clock=now,scenario=scenario)
                try:job=enqueue('predict',config,idem='simulation:'+eid)
                except BaseException:
                    s.update(eid,'failed',error='enqueue_failed');set_status(session,eid,'failed_simulated');raise
                with db() as con:
                    con.execute("UPDATE sim_messages SET payload=json_set(payload,'$.job',?) WHERE session=? AND event_id=? AND direction='user'",(job['id'],session,eid))
                record_event(eid,session,mid,'queued',{'job':job['id'],'event_id':eid,'message_id':mid,'status':'queued'})
                result.update(status='queued',job=job['id'])
        set_status(session,eid,'sent_simulated' if result['status']!='duplicate' else ('sent_simulated' if retry else 'duplicate_ignored'))
        return result
    finally:s.close()

def process(config,folder):
    import secrets
    from src.workbench.adapters import ModelPredictor
    from src.workbench.lifecycle import asset_path
    from src.inference.engine import InvalidImage,decode_image
    eid=config['event_id']; s=store(); scenario=config.get('scenario') or ''
    session=config['session']
    try:
        if s.cancelled(eid): return {'status':'cancelled'}
        s.update(eid,'running')
        if scenario=='download_failure': raise ValueError('Simulated image download failure')
        if scenario=='missing_model': raise LookupError('目前沒有可用的模型，請稍後再試。')
        if scenario=='inference_failure': raise RuntimeError('Simulated inference failure')
        service=read_json(config_path('service.json',ROOT))
        raw=asset_path(config['asset']).read_bytes()
        if scenario=='corrupt_image':raw=b'not an image'
        if scenario=='too_large':raw=b'0'*(service['max_image_bytes']+1)
        if scenario=='unsupported_format':
            import io
            from PIL import Image
            buffer=io.BytesIO();Image.new('RGB',(80,80)).save(buffer,'BMP');raw=buffer.getvalue()
        decode_image(raw,service)
        predictor=ModelPredictor(config['artifact'],config.get('device','0'))
        if scenario=='unsupported_task':raise LookupError('此模型不支援這項分析任務，請改用已啟用的模型。')
        record,jpeg=predictor.predict(raw)
        # In a timeout replay, computation still finishes before the resource lease exits.
        if scenario=='timeout': raise TimeoutError('Simulated analysis deadline exceeded; compute drained')
        if s.cancelled(eid): return {'status':'cancelled'}
        results(record,'')
        (folder/'result.jpg').write_bytes(jpeg)
        url='/api/v1/jobs/'+folder.name+'/image'
        token=secrets.token_urlsafe(32)
        conv=conversation(session,s,time.time())
        offer=conv.finish(event_id=eid,token=token,record=record,raw=raw,ttl=3600,service_config=service)
        payload=conv.result_messages(record,url,token,offer)
        route='push' if scenario=='push' or time.time()-config['clock']>=45 else 'reply'
        delivery=deliver(session,eid,payload,scenario)
        data={'result':record,'messages':payload,'delivery':delivery,'delivery_note':DELIVERY_NOTE,'route':route,'trace_id':folder.name,'event_id':eid,'message_id':config['message_id'],'input_sha256':__import__('hashlib').sha256(raw).hexdigest(),'artifact':config['artifact'],'dataset':predictor.metadata.get('extra',{}).get('dataset'),'simulated':True,'consent_offered':bool(offer),'browser_rendering':'approximation; actual LINE client not verified','expires':time.time()+3600}
        if delivery!='delivered_simulated':s.update(eid,'completed',error='delivery_unconfirmed')
        record_event(eid,session,config['message_id'],'completed',data)
        return data
    except Exception as exc:
        s.update(eid,'failed',error=type(exc).__name__)
        if isinstance(exc,InvalidImage):text=str(exc)
        elif isinstance(exc,LookupError):text=str(exc).strip("'")
        elif isinstance(exc,TimeoutError):text='分析逾時，請稍後重新傳送。'
        else:text='分析暫時失敗，請稍後重新傳送照片。'
        message=text_message(text);deliver(session,eid,[message])
        record_event(eid,session,config['message_id'],'failed',{'error':str(exc),'messages':[message]})
        if isinstance(exc,(InvalidImage,LookupError,TimeoutError)):return {'status':'failed','error':text}
        raise
    finally:s.close()

def transcript(session,before=None,limit=30):
    """Chat history newest-last; older pages load upward (not a research pager)."""
    from src.workbench import jobs
    if not 1<=limit<=100:raise ValueError('Invalid page size')
    with db() as con:
        clause='AND id<?' if before else ''
        rows=con.execute('SELECT * FROM sim_messages WHERE session=? '+clause+' ORDER BY id DESC LIMIT ?',(session,*( [int(before)] if before else []),limit+1)).fetchall()
    more=len(rows)>limit;rows=list(reversed(rows[:limit]));items=[]
    for r in rows:
        item={**dict(r),'payload':json.loads(r['payload'])}
        job=item['payload'].get('job')
        if job:
            try:item['job_state']=jobs.get(job)['state']
            except Exception:item['job_state']='unknown'
        items.append(item)
    return {'items':items,'has_more':more,'next_before':items[0]['id'] if items and more else None,'delivery_note':DELIVERY_NOTE}

def clear_session(session):
    with db() as con:
        con.execute('DELETE FROM sim_messages WHERE session=?',(session,))
        con.execute('DELETE FROM events WHERE session=?',(session,))

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
