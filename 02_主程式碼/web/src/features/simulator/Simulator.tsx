import {useEffect,useRef,useState} from 'react';
import {api,useData,names} from '../../shared/ui';
import {SimulationTimeline} from '../../shared/readable';
import {Field,Heading} from '../../shared/app-ui';
import {LineMessage,ResultImage,quickItems} from './LineMessage';
type Obj=Record<string,any>;

const SCENARIO_NAMES:Obj={'':'正常分析',queue_full:'佇列已滿／忙碌',missing_model:'無可用模型',unsupported_task:'模型不支援此任務',download_failure:'圖片下載失敗',corrupt_image:'圖片損毀',too_large:'超過大小上限',unsupported_format:'不支援的格式',timeout:'推論逾時',inference_failure:'推論失敗',send_failure:'回覆傳送失敗（模擬）',push:'超過 reply 時限改用 push'};
const USER_STATUS:Obj={sending:'傳送中…',sent_simulated:'已送出（模擬）',duplicate_ignored:'重複事件已忽略',unsent:'已收回',failed_simulated:'傳送失敗'};
const time=(s:number)=>new Date(s*1000).toLocaleTimeString('zh-TW',{hour:'2-digit',minute:'2-digit',hour12:false,timeZone:'Asia/Taipei'});
function stored(key:string,fallback:string){try{return localStorage.getItem(key)||fallback}catch{return fallback}}

function RichMenu({menu,onAction}:{menu:Obj,onAction:(text:string)=>void}){
 const size=menu.menu.size;
 return <div className="rich-menu" style={{aspectRatio:`${size.width}/${size.height}`}} role="group" aria-label="圖文選單">{menu.areas.map((a:Obj,i:number)=><button key={i} className={'rich-area'+(i===0?' primary':'')} style={{left:a.bounds.x/size.width*100+'%',top:a.bounds.y/size.height*100+'%',width:a.bounds.width/size.width*100+'%',height:a.bounds.height/size.height*100+'%'}} onClick={()=>onAction(a.action.text)}><b>{a.action.text}</b><small>{a.description}</small></button>)}</div>;
}

export function Simulator({act}:any){
 const artifacts=useData('/artifacts');const menu=useData('/simulation/rich-menu');
 const [platform,setPlatform]=useState(()=>stored('simulator.platform','ios'));
 const [session,setSession]=useState('demo-1'),[artifact,setArtifact]=useState(''),[device,setDevice]=useState('0'),[scenario,setScenario]=useState(''),[development,setDevelopment]=useState(false),[offset,setOffset]=useState(0);
 const [text,setText]=useState(''),[menuOpen,setMenuOpen]=useState(false),[last,setLast]=useState<Obj|null>(null),[failed,setFailed]=useState<Obj[]>([]),[older,setOlder]=useState<Obj[]>([]),[olderCursor,setOlderCursor]=useState<number|null>(null),[olderError,setOlderError]=useState('');
 const transcript=useData('/simulation/'+encodeURIComponent(session)+'/messages?limit=30',1500,d=>!d?.items?.some((m:Obj)=>m.status==='sending'||['queued','running','cancelling'].includes(m.job_state)));
 const events=useData('/simulation-query?session='+encodeURIComponent(session)+'&page=1',3000,d=>d.active_count===0);
 const chat=useRef<HTMLDivElement>(null);
 useEffect(()=>{api('/overview').then(x=>{if(x.references.local?.artifact)setArtifact(x.references.local.artifact)}).catch(()=>{})},[]);
 useEffect(()=>{setOlder([]);setOlderCursor(null);setFailed([]);setLast(null);setOlderError('')},[session]);
 useEffect(()=>{if(transcript.data)setOlderCursor(c=>c??transcript.data.next_before)},[transcript.data]);
 const latest:Obj[]=transcript.data?.items||[];const ids=new Set(latest.map(m=>m.id));const messages=[...older.filter(m=>!ids.has(m.id)),...latest];
 useEffect(()=>{chat.current?.scrollTo({top:chat.current.scrollHeight})},[latest.length,failed.length]);
 const changePlatform=(p:string)=>{setPlatform(p);try{localStorage.setItem('simulator.platform',p)}catch{}};
 const post=async(body:Obj)=>{setLast(body);try{const r=await api('/simulation/events','POST',body);setFailed(f=>f.filter(x=>x.body.event_id!==body.event_id));transcript.refresh();events.refresh();return r}catch(e){setFailed(f=>[...f.filter(x=>x.body.event_id!==body.event_id),{body,error:(e as Error).message}]);throw e}};
 const send=(payload:Obj)=>post({session,artifact,device,scenario,development,clock:Date.now()/1000-offset,event_id:crypto.randomUUID(),message_id:crypto.randomUUID(),...payload});
 const sendText=(value:string)=>act(()=>send({type:'text',text:value}),'文字事件已送出（本機模擬）');
 const action=(a:Obj)=>a.type==='postback'?act(()=>send({type:'postback',data:a.data,display:a.displayText||a.label}),'選擇已送出（本機模擬）'):sendText(a.text);
 const loadOlder=async()=>{if(!olderCursor)return;setOlderError('');try{const page=await api('/simulation/'+encodeURIComponent(session)+'/messages?limit=30&before='+olderCursor);setOlder(o=>[...page.items,...o]);setOlderCursor(page.next_before)}catch(e){setOlderError((e as Error).message)}};
 const lastMessage=messages.at(-1);const quick=lastMessage?.direction==='bot'?quickItems(lastMessage.payload):[];
 const pendingAnalysis=messages.some(m=>m.direction==='user'&&['queued','running'].includes(m.job_state));
 const lastImage=[...messages].reverse().find(m=>m.direction==='user'&&m.kind==='image'&&m.status!=='unsent');
 return <><Heading title="LINE 模擬">離線測試對話流程，與正式 LINE 共用同一套規則；不連線、不使用金鑰、不傳送真實訊息。</Heading>
 <div className="sim-layout"><section className="panel sim-controls" aria-label="工程設定">
 <h2>工程設定（手機畫面外）</h2>
 <div className="tabs" role="radiogroup" aria-label="平台樣式">{[['ios','iOS 樣式'],['android','Android 樣式']].map(([k,v])=><button key={k} role="radio" aria-checked={platform===k} className={platform===k?'active':''} onClick={()=>changePlatform(k)}>{v}</button>)}</div>
 <small>切換樣式只改外觀；不清空對話、不重送、不重新推論。</small>
 <Field label="模型產物"><select value={artifact} onChange={e=>setArtifact(e.target.value)}><option value="">尚未選擇（可測試「無可用模型」）</option>{(artifacts.data||[]).map((a:Obj)=><option value={a.id} key={a.id}>{a.model} / {names[a.task]||a.task} / {a.id.slice(-8)} {a.reports?.length?'已評估':'未評估'}</option>)}</select></Field>
 <label className="check"><input type="checkbox" checked={development} onChange={e=>setDevelopment(e.target.checked)}/>允許未評估模型，僅供開發測試</label>
 <Field label="合成使用者"><select value={session} onChange={e=>setSession(e.target.value)}>{['demo-1','demo-2','demo-3'].map(x=><option key={x}>{x}</option>)}</select></Field>
 <Field label="運算裝置"><select value={device} onChange={e=>setDevice(e.target.value)}><option value="0">GPU</option><option value="cpu">CPU</option></select></Field>
 <Field label="下一個事件的情境"><select value={scenario} onChange={e=>setScenario(e.target.value)}>{['',...(menu.data?.scenarios||[])].map((k:string)=><option value={k} key={k}>{SCENARIO_NAMES[k]||k}</option>)}</select></Field>
 <Field label="事件時間偏移（秒）" hint="模擬接收後經過的時間；≥45 秒時回覆改走 push。"><input type="number" min={0} max={3600} value={offset} onChange={e=>setOffset(+e.target.value)}/></Field>
 <div className="actions vertical">
 <button className="secondary" onClick={()=>act(()=>send({type:'follow'}),'加入好友事件已送出')}>模擬加入好友</button>
 <button className="secondary" disabled={!last} onClick={()=>act(()=>post(last!),'已用相同事件 ID 重送，檢查去重')}>重送上一個事件（相同 ID）</button>
 <button className="secondary" disabled={!lastImage} onClick={()=>act(()=>api('/simulation/events','POST',{session,type:'unsend',message_id:lastImage?.payload?.message_id}).then(()=>transcript.refresh()),'已收回上一張照片')}>收回上一張照片</button>
 <button className="secondary danger" onClick={()=>{if(confirm('清除此合成使用者的模擬對話？'))act(()=>api('/simulation/'+session,'DELETE').then(()=>{setOlder([]);setFailed([]);transcript.refresh();events.refresh()}),'模擬對話已清除')}}>清除對話</button></div>
 {menu.data&&<div className="callout"><b>研究同意（模擬）</b><p>{menu.data.consent_offer?'分析後會詢問研究使用同意（草稿版本 '+menu.data.consent_offer.version+'）。模擬同意只建立測試素材，不等於真人授權。':'模擬器的研究同意目前關閉。'}</p></div>}
 <details><summary>可驗證範圍與限制</summary><ul><li>離線涵蓋：文字、加入好友、照片、Flex 結果卡、quick reply、postback 同意／拒絕、撤回研究同意、收回、重送去重、忙碌、佇列滿、無模型、模型不支援、圖片損毀／過大／格式錯誤、逾時、推論失敗、傳送失敗與 push 路徑。</li><li>「已送出（模擬）」只代表本機 transport 已記錄，不是 LINE 已讀或送達回執。</li><li>仍需整合驗證：HTTPS／TLS 與公開網址、正式帳號與 Channel 設定、Webhook 重送實際行為、平台配額、真實 iOS／Android LINE App 外觀。</li><li>{menu.data?.reference?.limits}</li><li>參考資料：{(menu.data?.reference?.sources||[]).join('；')}（查閱 {menu.data?.reference?.checked_on}）</li></ul></details>
 </section>
 <section className={'phone line-phone '+platform} aria-label={(platform==='ios'?'iOS':'Android')+' 樣式 LINE 對話模擬'}>
 <div className="status-bar"><span>{platform==='ios'?'9:41':'09:41'}</span><span className="status-icons" aria-hidden="true">{platform==='ios'?'▮▮▮ ◔':'◔ ▮▮▮'}</span></div>
 <header className="phone-head"><button className="plain back" aria-label="返回（模擬）">{platform==='ios'?'‹':'←'}</button><div className="title"><b>Phlebitis 研究展示</b><small>本機模擬 · {session}</small></div><span className="badge">SIM</span></header>
 <div className="chat" ref={chat} aria-live="polite">
 {olderCursor&&<button className="plain load-older" onClick={loadOlder}>載入較早訊息</button>}{olderError&&<p role="alert">{olderError}</p>}
 {transcript.error&&<p role="alert">{transcript.error} <button onClick={()=>transcript.refresh()}>重試</button></p>}
 {!transcript.data&&!transcript.error&&<div className="system-note">載入對話…</div>}
 {transcript.data&&!messages.length&&!failed.length&&<div className="system-note">傳送文字或照片開始模擬。照片與結果暫存一小時；未同意研究使用不會保存為研究資料。</div>}
 {messages.map(m=>m.direction==='user'?<div className="row user" key={m.id}><div className="meta">{m.status!=='sending'&&<small>{USER_STATUS[m.status]||m.status}</small>}<small>{time(m.created)}</small></div><div className={'bubble user'+(m.status==='unsent'?' unsent':'')}>{m.status==='unsent'?'訊息已收回':m.kind==='image'?<ResultImage src={'/api/v1/assets/'+m.payload.asset+'/image'} alt="使用者傳送的照片" expired="照片已過期（一小時暫存）"/>:m.payload.text}</div>{m.status==='sending'&&<small className="sending">傳送中…</small>}</div>
 :<div className={'row bot'+(m.status==='withdrawn_by_unsend'?' dim':'')} key={m.id}><span className="avatar" aria-hidden="true">P</span><div className="bubble bot"><LineMessage message={m.payload}/></div><div className="meta"><small>{time(m.created)}</small>{m.status==='failed_simulated'&&<small className="error">傳送失敗（模擬）</small>}</div></div>)}
 {failed.map(f=><div className="row user" key={f.body.event_id}><div className="meta"><small className="error">傳送失敗</small><button className="plain" onClick={()=>act(()=>post(f.body),'已重試（相同事件 ID）')}>重試</button></div><div className="bubble user failed">{f.body.type==='image'?'（照片）':f.body.text||f.body.display||f.body.type}</div><small className="error">{f.error}</small></div>)}
 {pendingAnalysis&&<div className="row bot"><span className="avatar" aria-hidden="true">P</span><div className="bubble bot typing" aria-label="分析中">分析中<span>…</span></div></div>}
 </div>
 {quick.length>0&&<div className="quick-reply" role="group" aria-label="快速回覆">{quick.map((q:Obj,i:number)=><button key={i} onClick={()=>action(q.action)}>{q.action.label}</button>)}</div>}
 <div className="composer"><button className="plain icon" aria-label={menuOpen?'收合圖文選單':'展開圖文選單'} aria-expanded={menuOpen} onClick={()=>setMenuOpen(!menuOpen)}>{menuOpen?'⌄':'☰'}</button>
 <label className="plain icon" aria-label="選擇照片">＋<input type="file" hidden accept="image/jpeg,image/png,image/webp" onChange={e=>{const f=e.target.files?.[0];if(f)act(async()=>{const a=await api('/assets','POST',f);return send({type:'image',asset:a.id})},'照片已送出，等待本地分析');e.target.value=''}}/></label>
 <input aria-label="訊息" placeholder="輸入訊息" value={text} onChange={e=>setText(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'&&text.trim()){sendText(text.trim());setText('')}}}/>
 <button className="send" disabled={!text.trim()} onClick={()=>{sendText(text.trim());setText('')}} aria-label="傳送">{platform==='ios'?'↑':'➤'}</button></div>
 {menuOpen&&menu.data&&<RichMenu menu={menu.data} onAction={t=>sendText(t)}/>}
 {!menuOpen&&menu.data&&<button className="chat-bar" onClick={()=>setMenuOpen(true)}>{menu.data.menu.chatBarText} ▴</button>}
 </section></div>
 <section className="panel"><details><summary>事件與分析除錯（工程資訊，不顯示給病患）</summary><p>傳送狀態與推論狀態分開記錄；分期模型的類別與各類分數只在這裡顯示，LINE 回覆只呈現疑似／未達門檻。</p><SimulationTimeline events={events.data?.items||[]}/></details></section></>;
}
