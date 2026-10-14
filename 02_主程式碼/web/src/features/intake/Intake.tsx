import {useEffect,useRef,useState} from 'react';
import {api,useData,useHash,route,names,when,Empty,Pager,operatorName,TASKS} from '../../shared/ui';
import {Heading} from '../../shared/app-ui';
import {TrashAction} from '../trash/Trash';
type Obj=Record<string,any>;

const FILTERS:[string,string,[string,string][]][]=[
 ['source','來源',[['line','LINE'],['simulator','模擬器（測試）']]],
 ['state','處理狀態',[['received','待審查'],['reviewed','已確認'],['needs_changes','要求補件'],['rejected','不採用'],['promoted','已轉入資料審查'],['withdrawn','已撤回']]],
 ['usage','授權／用途',[['active','有效研究授權'],['test_only','模擬（測試素材）'],['withdrawn','已撤回']]],
 ['label','人工標籤',[['normal','正常'],['stage1','第一期'],['stage2','第二期'],['positive','陽性'],['negative','陰性'],['unknown','未確認']]],
];

function Prediction({value}:{value:Obj|null}){
 if(!value)return <span className="muted">無模型輸出</span>;
 return <span className="prediction" title="模型預測僅供參考，不是標籤">參考：{({suspected:'疑似陽性',not_detected:'未達門檻',quality_rejected:'品質不足',needs_review:'需人工確認'} as Obj)[value.status]||value.status}{value.predicted_class&&value.label_scheme==='stage_v1'?' · 類別 '+(names[value.predicted_class]||value.predicted_class):''}{value.prediction_score!=null?' · 分數 '+Number(value.prediction_score).toFixed(3)+'（未校準）':''}</span>;
}

function Thumb({item}:{item:Obj}){
 const [failed,setFailed]=useState(false);
 if(item.usage_state==='withdrawn'||item.cleanup_state==='done'||item.cleanup_state==='purged'||item.resource_state!=='active')return <div className="thumb-placeholder">{item.usage_state==='withdrawn'?'已撤回':'不可檢視'}</div>;
 return failed?<div className="thumb-placeholder">無法載入</div>:<img loading="lazy" src={'/api/v1/intake/'+item.id+'/image'} alt="研究收件照片" width={160} height={120} onError={()=>setFailed(true)}/>;
}

function Detail({item,act,onChanged}:{item:Obj,act:any,onChanged:()=>void}){
 const [form,setForm]=useState<Obj>({state:item.state==='received'||item.state==='promoted'||item.state==='withdrawn'?'reviewed':item.state,binary_label:item.binary_label,stage_label:item.stage_label,quality:item.quality,subject_alias:item.subject_alias,subject_confirmed:!!item.subject_alias,note:item.note||''});
 const busy=useRef(false);const patch=(k:string,v:any)=>setForm(f=>({...f,[k]:v}));
 const once=async(fn:()=>Promise<any>)=>{if(busy.current)throw Error('上一個操作仍在處理，請勿重複提交');busy.current=true;try{return await fn()}finally{busy.current=false}};
 const locked=item.state==='promoted'||item.usage_state==='withdrawn';
 const setStage=(v:string)=>setForm(f=>({...f,stage_label:v,binary_label:({normal:'negative',stage1:'positive',stage2:'positive',positive_unstaged:'positive'} as Obj)[v]||f.binary_label}));
 return <section className="panel intake-detail"><h2>收件 {item.id.slice(0,12)}</h2>
 <div className="callout">{item.simulated?'模擬資料：模擬授權不等於真人研究授權，只能測試流程，正式訓練會排除。':'LINE 研究授權照片：仍須人工確認品質、標籤與個案關係後，才可明確轉入資料審查。'}</div>
 <dl className="facts"><dt>接收時間</dt><dd>{when(item.received_at)}</dd><dt>同意版本</dt><dd>{item.consent_version} · {when(item.consent_at)}</dd><dt>授權狀態</dt><dd>{names[item.usage_state]}{item.consent_withdrawn_at?' · 撤回於 '+when(item.consent_withdrawn_at):''}</dd><dt>保存期限</dt><dd>保存至撤回為止（無自動到期）</dd><dt>模型輸出</dt><dd><Prediction value={item.prediction}/></dd>{item.cleanup&&<><dt>實體清理</dt><dd>{({pending:'排隊中',retry:'等待重試',done:'已完成'} as Obj)[item.cleanup.state]||item.cleanup.state}{item.cleanup.error?' · '+item.cleanup.error:''} · 嘗試 {item.cleanup.attempts} 次</dd></>}{item.promoted_image_id&&<><dt>資料審查</dt><dd><a href={'#data?view=all'}>{item.promoted_image_id}</a>（待資料審查核准）</dd></>}</dl>
 <h3>轉入後的任務資格預估</h3><ul className="reasons">{TASKS.map(([k,v])=><li key={k}><b>{v}</b>：{item.tasks[k].length?item.tasks[k].join('；'):'人工確認完成，轉入並於資料審查核准後可用'}</li>)}</ul>
 <fieldset disabled={locked}><legend>人工確認（不使用模型預測作為標籤）</legend><div className="form-grid">
 <label className="field">處理結果<select value={form.state} onChange={e=>patch('state',e.target.value)}><option value="reviewed">已確認</option><option value="needs_changes">要求補件</option><option value="rejected">不採用</option></select></label>
 <label className="field">二分類<select value={form.binary_label} onChange={e=>patch('binary_label',e.target.value)}><option value="unknown">未確認</option><option value="negative">正常（陰性）</option><option value="positive">陽性</option></select></label>
 <label className="field">分期<select value={form.stage_label} onChange={e=>setStage(e.target.value)}>{['unknown','normal','stage1','stage2','positive_unstaged'].map(k=><option key={k} value={k}>{names[k]||'未確認'}</option>)}</select></label>
 <label className="field">影像品質<select value={form.quality} onChange={e=>patch('quality',e.target.value)}><option value="">未評估</option><option value="acceptable">可用</option><option value="limited">勉強可用</option><option value="unusable">不可用</option></select></label>
 <label className="field">個案研究編號（化名）<input maxLength={40} value={form.subject_alias} onChange={e=>patch('subject_alias',e.target.value)} placeholder="例如 L-0012"/><small>不可填姓名、病歷號或 LINE 名稱。</small></label>
 <label className="check"><input type="checkbox" checked={form.subject_confirmed} onChange={e=>patch('subject_confirmed',e.target.checked)}/>已依研究紀錄核對個案編號</label>
 <label className="field wide">備註<textarea maxLength={1000} value={form.note} onChange={e=>patch('note',e.target.value)}/></label></div>
 <button disabled={!operatorName()} onClick={()=>act(()=>once(()=>api('/intake/'+item.id,'PUT',{...form,revision:item.revision}).then(onChanged)),'人工確認已儲存')}>儲存確認</button>{!operatorName()&&<small> 請先在「設定與維護」填寫操作者名稱。</small>}</fieldset>
 <div className="actions"><button className="secondary" disabled={item.state!=='reviewed'||locked} onClick={()=>act(()=>once(()=>api('/intake/'+item.id+'/promote','POST',{revision:item.revision}).then(r=>{onChanged();return r})),'已轉入資料審查（待核准，尚未進入任何訓練）')}>轉入資料審查</button>
 <button className="secondary danger" disabled={item.usage_state==='withdrawn'} onClick={()=>{const reason=prompt('撤回原因（例如：參與者以電話要求撤回）');if(reason)act(()=>once(()=>api('/intake/'+item.id+'/withdraw','POST',{reason}).then(onChanged)),'已立即停止研究使用；實體清理已排入背景工作')}}>記錄撤回</button>
 <TrashAction targets={[{type:'research_photo',id:item.id}]} onDone={onChanged}/></div></section>;
}

export function Intake({act}:{act:any}){
 const {params}=useHash();const page=Math.max(1,Number(params.get('page'))||1);
 const query=new URLSearchParams({page:String(page),size:'20'});for(const [k] of FILTERS)if(params.get(k))query.set(k,params.get(k)!);for(const k of ['start','end'])if(params.get(k))query.set(k,params.get(k)!);
 const list=useData('/intake?'+query.toString());const config=useData('/intake/consent-config');const [selected,setSelected]=useState('');
 useEffect(()=>setSelected(''),[query.toString()]);
 const change=(key:string,value:string)=>{const next:Obj=Object.fromEntries(query);delete next.size;next.page='1';if(value)next[key]=value;else delete next[key];route('intake',next)};
 const item=(list.data?.items||[]).find((x:Obj)=>x.id===selected);
 return <><Heading title="LINE 研究收件">已授權的照片經人工確認後才轉入研究資料。拒絕授權不影響照片分析；模型預測只供參考。</Heading>
 {config.data&&<div className="callout">真實 LINE 研究同意：{config.data.line_enabled&&config.data.line_offer?'已開放（核定版本 '+config.data.current_version+'）':'未開放（需在 configs/research_consent.json 設定 line_enabled 並標記核定版本）'} · 模擬器：{config.data.simulator_enabled?'可測試（模擬授權不等於真人授權）':'關閉'} · 保存政策：保存至撤回為止</div>}
 <section className="panel"><div className="form-grid">{FILTERS.map(([k,label,options])=><label className="field" key={k}>{label}<select value={params.get(k)||''} onChange={e=>change(k,e.target.value)}><option value="">全部</option>{options.map(([v,t])=><option key={v} value={v}>{t}</option>)}</select></label>)}{[['start','接收起日'],['end','接收迄日']].map(([k,label])=><label className="field" key={k}>{label}（臺北時間）<input type="date" value={params.get(k)||''} onChange={e=>change(k,e.target.value)}/></label>)}</div></section>
 {list.error&&<p role="alert">{list.error} <button onClick={()=>list.refresh()}>重試</button></p>}
 {!list.data?(!list.error&&<Empty>載入研究收件…</Empty>):<><Pager page={page} total={list.data.total} size={20} onPage={(p:number)=>route('intake',{...Object.fromEntries(query),page:String(p)})}/>
 <div className="review-layout"><section className="gallery" aria-label="研究收件清單">{list.data.items.map((x:Obj)=><button key={x.id} className={'thumb '+(selected===x.id?'selected':'')} onClick={()=>setSelected(x.id)}><Thumb item={x}/><div><b>{x.simulated?'模擬':'LINE'} · {when(x.received_at)}</b><small>{names[x.state]} · 授權{names[x.usage_state]}</small><small>標籤：{names[x.stage_label]&&x.stage_label!=='unknown'?names[x.stage_label]:names[x.binary_label]||'未確認'}{x.subject_alias?' · '+x.subject_alias:''}</small><small><Prediction value={x.prediction}/></small></div></button>)}{!list.data.items.length&&<Empty>目前沒有符合條件的研究收件。LINE 使用者明確同意研究使用後才會出現在這裡；可先在「LINE 模擬」測試同意流程。</Empty>}</section>
 <div>{item?<Detail key={item.id+':'+item.revision} item={item} act={act} onChanged={list.refresh}/>:<section className="panel"><Empty>選擇左側收件，進行品質、標籤與個案確認。</Empty></section>}</div></div></>}</>;
}
