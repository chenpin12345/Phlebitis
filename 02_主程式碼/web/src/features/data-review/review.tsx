import {ImportPanel,ExternalImport} from '../imports/ImportPanel';
import {ReviewHistory} from '../../shared/readable';
import React,{useEffect,useRef,useState} from 'react';
import {api,useData,useHash,route,names,when,Empty,operatorName,DisplayName} from '../../shared/ui';

export function BoxEditor({src,boxes,setBoxes,onReady}:any){
 const svg=useRef<SVGSVGElement>(null),drag=useRef<any>(null);const [loaded,setLoaded]=useState(''),[imageUrl,setImageUrl]=useState(''),[error,setError]=useState(''),[size,setSize]=useState([1,1]),[selected,select]=useState(-1),[mode,setMode]=useState('select');
 const ready=loaded===src&&!error;const w=1000,h=1000*size[1]/size[0];
 useEffect(()=>{let active=true,url='';const controller=new AbortController();setLoaded('');setError('');select(-1);drag.current=null;onReady?.(false);const probe=new Image();probe.onload=()=>{if(active&&probe.naturalWidth&&probe.naturalHeight){setSize([probe.naturalWidth,probe.naturalHeight]);setImageUrl(url);setLoaded(src);onReady?.(true)}};fetch(src,{signal:AbortSignal.any([controller.signal,AbortSignal.timeout(15000)])}).then(r=>{if(!r.ok)throw Error('圖片無法載入');return r.blob()}).then(blob=>{if(active){url=URL.createObjectURL(blob);probe.src=url}}).catch(e=>{if(active&&e.name!=='AbortError'){setError('圖片無法載入，請重新整理或檢查原檔。');onReady?.(false)}});probe.onerror=()=>{if(active){setError('圖片無法解碼');onReady?.(false)}};return()=>{active=false;controller.abort();probe.onload=null;probe.onerror=null;if(url)URL.revokeObjectURL(url)}},[src]);

 const point=(e:React.PointerEvent,clamp=false)=>{const matrix=svg.current?.getScreenCTM();if(!matrix)return null;const p=new DOMPoint(e.clientX,e.clientY).matrixTransform(matrix.inverse());const x=p.x/w,y=p.y/h;if(!clamp&&(x<0||x>1||y<0||y>1))return null;return [Math.max(0,Math.min(1,x)),Math.max(0,Math.min(1,y))]};
 const start=(e:React.PointerEvent,index=-1,resize=false)=>{if(!ready)return;e.preventDefault();e.stopPropagation();const p=point(e);if(!p)return;svg.current!.setPointerCapture(e.pointerId);if(index>=0&&mode==='select'){select(index);drag.current={start:p,original:[...boxes[index]],index,resize}}else if(mode==='draw'){drag.current={start:p,index:boxes.length,new:true};select(boxes.length);setBoxes([...boxes,[0,p[0],p[1],0,0]])}};
 const move=(e:React.PointerEvent)=>{const d=drag.current,p=point(e,true);if(!d||!p)return;const [x,y]=p;const next=boxes.map((b:number[])=>[...b]);if(d.new){const [sx,sy]=d.start;next[d.index]=[0,(x+sx)/2,(y+sy)/2,Math.abs(x-sx),Math.abs(y-sy)]}else if(d.resize){const b=d.original,left=b[1]-b[3]/2,top=b[2]-b[4]/2,bw=Math.min(1-left,Math.max(.002,x-left)),bh=Math.min(1-top,Math.max(.002,y-top));next[d.index]=[0,left+bw/2,top+bh/2,bw,bh]}else{const b=d.original;next[d.index]=[0,Math.max(b[3]/2,Math.min(1-b[3]/2,b[1]+x-d.start[0])),Math.max(b[4]/2,Math.min(1-b[4]/2,b[2]+y-d.start[1])),b[3],b[4]]}setBoxes(next)};
 const end=()=>{drag.current=null;setBoxes(boxes.filter((b:number[])=>b[3]>.001&&b[4]>.001))};
 return <div className="box-editor">
 {!ready&&<Empty>{error||'圖片載入中…'}</Empty>}
 <div className="toolbar"><button disabled={!ready} className="secondary" aria-pressed={mode==='select'} onClick={()=>setMode('select')}>選取／移動</button><button disabled={!ready} className="secondary" aria-pressed={mode==='draw'} onClick={()=>setMode('draw')}>新增矩形</button><button className="secondary" disabled={!ready||selected<0} onClick={()=>{setBoxes(boxes.filter((_:any,i:number)=>i!==selected));select(-1)}}>刪除選取框</button></div>
 {ready&&<svg ref={svg} className="annotation" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="xMidYMid meet" role="img" aria-label="圖片與標註編輯器" onPointerDown={e=>start(e)} onPointerMove={move} onPointerUp={end} onPointerCancel={end}><image href={imageUrl} width={w} height={h} preserveAspectRatio="xMidYMid meet"/>{boxes.map((b:number[],i:number)=><g key={i}><rect tabIndex={0} aria-label={`選取框 ${i+1}`} x={(b[1]-b[3]/2)*w} y={(b[2]-b[4]/2)*h} width={b[3]*w} height={b[4]*h} fill="transparent" stroke={selected===i?'#ffc56e':'#32eed5'} strokeWidth={3} vectorEffect="non-scaling-stroke" onFocus={()=>select(i)} onPointerDown={e=>start(e,i)} onKeyDown={e=>{const delta:Record<string,number[]>={ArrowLeft:[-.001,0],ArrowRight:[.001,0],ArrowUp:[0,-.001],ArrowDown:[0,.001]};if(delta[e.key]){e.preventDefault();const [dx,dy]=delta[e.key];setBoxes(boxes.map((a:number[],j:number)=>j===i?[0,Math.max(b[3]/2,Math.min(1-b[3]/2,b[1]+dx)),Math.max(b[4]/2,Math.min(1-b[4]/2,b[2]+dy)),b[3],b[4]]:a))}}}/>{selected===i&&<rect x={(b[1]+b[3]/2)*w-8} y={(b[2]+b[4]/2)*h-8} width={16} height={16} fill="#ffc56e" onPointerDown={e=>start(e,i,true)}/>}</g>)}</svg>}
 <p className="muted">完整顯示照片，留白不可建立標註。方向已由伺服器校正；選取框可用方向鍵微調，或使用下方數值欄位。</p>
 {boxes.map((b:number[],i:number)=><fieldset className="box-fields" key={i} disabled={!ready}><legend>框 {i+1}</legend>{['中心 X','中心 Y','寬','高'].map((label,k)=><label className="field" key={label}>{label}<input aria-label={`框 ${i+1} ${label}`} type="number" step=".001" min={0} max={1} value={+b[k+1].toFixed(6)} onChange={e=>setBoxes(boxes.map((a:number[],j:number)=>j===i?a.map((v,l)=>l===k+1?+e.target.value:v):a))}/></label>)}</fieldset>)}
 </div>
}

type Obj=Record<string,any>;
export const AREAS:Obj={
 det:{title:'YOLO 病灶框選區',short:'YOLO 框選',icon:'▣',task:'detection',desc:'給 YOLO 偵測模型使用。每張照片需框選病灶，或確認無病灶（負樣本）。合作醫院檔名為正常的照片已自動設為無病灶。',
  done:'已框選／已確認',labels:[['boxes','已框選病灶'],['no_target','確認無病灶'],['not_annotated','尚未處理']],labelKey:'detection'},
 cls:{title:'其他模型分類區',short:'其他模型分類',icon:'◧',task:'stage_classification',desc:'給 EfficientNet、DINOv2 等整圖分類模型使用，不需框選。合作醫院照片已依檔名自動分類，其他照片可人工指定。',
  done:'已分類',labels:[['normal','正常'],['stage1','第一期'],['stage2','第二期'],['positive_unstaged','陽性・分期未知'],['unknown','未確認']],labelKey:'stage'},
};
const VIEWS:[string,string][]=[['pending','待處理'],['confirmed','已完成'],['excluded','排除'],['all','全部']];
const STATE_NAMES:Obj={pending:'待處理',confirmed:'已完成',excluded:'排除'};
const SOURCE_NAMES:Obj={yida:'合作醫院',import:'匯入',other:'其他來源'};
const labelName=(area:string,value:string)=>Object.fromEntries(AREAS[area].labels)[value]||value;
const typing=(t:EventTarget|null)=>t instanceof Element&&(['INPUT','TEXTAREA','SELECT'].includes(t.tagName)||(t as HTMLElement).isContentEditable||!!t.closest('svg,[role=radiogroup]'));

function useOperator(){const [name,setName]=useState(operatorName());useEffect(()=>{const f=()=>setName(operatorName());addEventListener('storage',f);addEventListener('focus',f);return()=>{removeEventListener('storage',f);removeEventListener('focus',f)}},[]);return name}

function AreaSwitch({area,onChange}:{area:string,onChange:(a:string)=>void}){
 const det=useData('/data-area?area=det&view=all&size=1',0),cls=useData('/data-area?area=cls&view=all&size=1',0);
 const info:Obj={det:det.data,cls:cls.data};
 return <nav className="area-switch" aria-label="訓練工作區">{(['det','cls'] as const).map(k=>{const p=info[k]?.progress;return <button key={k} className={'area-tab '+(area===k?'active':'')} aria-pressed={area===k} onClick={()=>onChange(k)}>
  <span className="area-text"><b>{AREAS[k].title}</b><small>{p?`已完成 ${p.confirmed}／待處理 ${info[k].counts.pending}`:'讀取中…'}</small></span></button>})}</nav>;
}

function Progress({progress}:{progress:Obj|undefined}){
 if(!progress)return null;const usable=progress.total-progress.excluded;const pct=progress.ratio==null?0:Math.round(progress.ratio*100);
 return <div className="area-progress" role="group" aria-label="完成進度"><div className="bar" role="progressbar" aria-valuemin={0} aria-valuemax={usable} aria-valuenow={progress.confirmed}><span style={{width:pct+'%'}}/></div><small>已完成 {progress.confirmed} / {usable} 張（{progress.ratio==null?'—':pct+'%'}）{progress.excluded?` · 另有 ${progress.excluded} 張排除`:''}</small></div>;
}

function IndexBadge({index,onRecheck}:{index:Obj|undefined,onRecheck:()=>void}){
 if(!index)return null;const state=({ready:'已檢查',checking:'檢查中',pending:'待檢查',stale:'待更新',failed:'檢查失敗'} as Obj)[index.state]||index.state;
 return <span className={'status-pill '+index.state} title={'完整性檢查：'+state+(index.checked_at?' · '+when(index.checked_at):'')}>
  <span className="dot" aria-hidden="true"/>{state}{index.state==='checking'&&index.total!=null?` ${index.processed??0}/${index.total}`:''}{index.state==='ready'&&index.checked_at?' · '+new Date(index.checked_at*1000).toLocaleTimeString('zh-TW',{hour:'2-digit',minute:'2-digit',hour12:false}):''}
  <button className="plain" onClick={onRecheck} aria-label="重新檢查完整性">↻</button></span>;
}

function Reasons({tasks}:{tasks:Obj|null|undefined}){
 if(!tasks)return <p className="muted">訓練資格待背景檢查完成。</p>;
 return <ul className="eligibility">{Object.entries(tasks).map(([k,v]:any)=><li key={k} className={v.eligible?'ok':'no'}><b>{names[k]||k}</b>{v.eligible?'：可用於訓練':'：'+v.reasons.join('；')}</li>)}</ul>;
}

function SaveBar({busy,disabled,reason,setReason,onSave,operator,hint}:any){
 return <div className="save-bar"><label className="field">審查原因（必填）<input maxLength={1000} value={reason} onChange={e=>setReason(e.target.value)}/></label>
  {!operator&&<p className="muted">請先在「設定與維護」填寫操作者名稱。</p>}{hint&&<p className="muted">{hint}</p>}
  <div className="actions"><button disabled={busy||disabled||!reason.trim()||!operator} onClick={()=>onSave('approve')}>儲存並完成</button>
  <button className="secondary" disabled={busy||!reason.trim()||!operator} onClick={()=>onSave('needs_changes')}>存為待處理</button>
  <button className="secondary danger" disabled={busy||!reason.trim()||!operator} onClick={()=>onSave('exclude')}>此區排除</button></div></div>;
}

function EditorHead({d,ident,area}:any){
 return <header className="image-title"><h2 className="break"><DisplayName row={d} fallback={ident}/></h2>
  <div className="meta-row"><span className={'state-badge '+d.state}>{STATE_NAMES[d.state]}</span>{d.rule_applied&&<span className="source-badge">依合作醫院檔名自動{area==='cls'?'分類':'設定'}（授權規則）</span>}<small>image_id：{ident}</small></div>
  {d.aliases?.length>0&&<details><summary>來源檔名（{d.aliases.length}）</summary><ul>{d.aliases.map((a:any,i:number)=><li key={i}>{a.relative_path}<small> · {a.source}</small></li>)}</ul></details>}
  {d.name_variants?.length>0&&<p className="muted">另有同名但內容不同的版本：{d.name_variants.join('、')}（兩個版本都保留，可能是同一次拍攝）。</p>}</header>;
}

function History({d}:{d:Obj}){
 return <details><summary>此區的證據與審查歷程</summary>{d.evidence?.length>0&&<div className="table-wrap"><table><thead><tr><th>時間</th><th>來源</th><th>內容</th></tr></thead><tbody>{d.evidence.map((e:any,i:number)=><tr key={i}><td>{when(e.at)}</td><td>{({rule_prefill:'檔名預填',rule_applied:'授權檔名規則',review:'人工審查',intake_review:'收件確認'} as Obj)[e.method]||e.method}{e.rule_version?' · '+e.rule_version:''}</td><td>{[e.value&&names[e.value],e.stage&&names[e.stage],e.detection&&names[e.detection]].filter(Boolean).join(' · ')||'—'}{e.relative_path?' · '+e.relative_path:''}</td></tr>)}</tbody></table></div>}
  {d.history.length?d.history.map((h:any,i:number)=><section key={i}><h4>{when(h.after?.updated_at)} · {h.source==='authorized_filename_rule'?'授權檔名規則':h.after?.reviewer||'未記錄'}</h4><p>{h.after?.reason}</p><ReviewHistory history={h}/></section>):<Empty>此區尚無審查歷程</Empty>}</details>;
}

function YoloEditor({ident,act,onSaved}:any){
 const info=useData('/data/'+ident+'/annotation?area=det');const operator=useOperator();
 const [boxes,setBoxes]=useState<number[][]>([]),[state,setState]=useState('not_annotated'),[ready,setReady]=useState(false),[redraw,setRedraw]=useState(false),[reason,setReason]=useState('完成病灶框選'),[busy,setBusy]=useState(false);
 useEffect(()=>{if(info.data){setBoxes(info.data.boxes);setState(info.data.labels.detection);setRedraw(false)}},[info.data?.revision]);
 if(info.error)return <p role="alert">{info.error} <button onClick={()=>info.refresh()}>重試</button></p>;if(!info.data)return <Empty>載入照片與框選…</Empty>;
 const d=info.data;
 const save=(decision:string)=>{setBusy(true);act(()=>api('/data/'+ident+'/detection','PUT',{decision,detection:state,boxes:state==='boxes'?boxes:[],reviewer:operator,reason,revision:d.revision,coordinate_resolution:redraw?'redraw':null,category:''}).then(r=>{onSaved(decision==='approve');return r}),'YOLO 區已儲存（不影響其他模型分類區）').finally(()=>setBusy(false))};
 return <><EditorHead d={d} ident={ident} area="det"/>
  {d.coordinate_warning&&<div className="callout warning"><b>原始標註座標需要確認</b><p>{d.coordinate_warning}</p><label className="check"><input type="checkbox" checked={redraw} onChange={e=>setRedraw(e.target.checked)}/>我已核對，使用此正向照片重新框選</label></div>}
  {d.import_candidates?.length>0&&<details><summary>匯入的候選框（尚未確認）</summary>{d.import_candidates.map((c:any,i:number)=><p key={i}>{c.name} · {c.reason||''}{c.boxes&&<button className="secondary" disabled={!ready} onClick={()=>{setBoxes(c.boxes);setState('boxes')}}>載入候選框</button>}</p>)}</details>}
  <div className="segmented" role="radiogroup" aria-label="偵測狀態">{AREAS.det.labels.map(([k,v]:any)=><button key={k} role="radio" aria-checked={state===k} className={state===k?'active':''} onClick={()=>setState(k)}>{v}</button>)}</div>
  <BoxEditor src={'/api/v1/data/'+ident+'/image'} boxes={state==='boxes'?boxes:[]} setBoxes={(b:number[][])=>{setBoxes(b);if(b.length)setState('boxes')}} onReady={setReady}/>
  <SaveBar busy={busy} operator={operator} reason={reason} setReason={setReason} onSave={save} disabled={!ready||state==='not_annotated'||(state==='boxes'&&!boxes.length)||(!!d.coordinate_warning&&state==='boxes'&&!redraw)} hint={state==='not_annotated'?'「尚未處理」只能存為待處理；完成前請框選病灶或確認無病灶。':''}/>
  <Reasons tasks={d.tasks}/><History d={d}/></>;
}

function ClassifyEditor({ident,act,onSaved}:any){
 const info=useData('/data/'+ident+'/annotation?area=cls');const operator=useOperator();
 const [stage,setStage]=useState('unknown'),[quality,setQuality]=useState(''),[subject,setSubject]=useState(''),[reason,setReason]=useState('人工確認分類'),[busy,setBusy]=useState(false),[failed,setFailed]=useState(false);
 useEffect(()=>{if(info.data){const l=info.data.labels;setStage(l.stage||'unknown');setQuality(l.quality||'');setSubject(info.data.row.subject_id||'');setFailed(false)}},[info.data?.revision]);
 if(info.error)return <p role="alert">{info.error} <button onClick={()=>info.refresh()}>重試</button></p>;if(!info.data)return <Empty>載入照片與分類…</Empty>;
 const d=info.data;const hint=d.stage_suggestion;
 const binary=({normal:'negative',stage1:'positive',stage2:'positive',positive_unstaged:'positive'} as Obj)[stage]||'unknown';
 const save=(decision:string)=>{setBusy(true);act(()=>api('/data/'+ident+'/classification','PUT',{decision,label:binary,stage,quality,reviewer:operator,reason,revision:d.revision,subject_id:subject,clear_subject:!!d.row.subject_id&&!subject,category:''}).then(r=>{onSaved(decision==='approve');return r}),'其他模型分類區已儲存（不影響 YOLO 區）').finally(()=>setBusy(false))};
 return <><EditorHead d={d} ident={ident} area="cls"/>
  <figure className="preview">{failed?<Empty>圖片無法載入，請重新整理或檢查原檔。</Empty>:<img src={'/api/v1/data/'+ident+'/image'} alt="待分類照片（已校正方向，不顯示任何框）" onError={()=>setFailed(true)}/>}</figure>
  {hint&&!hint.confirmed&&<div className={'callout '+(hint.conflict?'warning':'')}><b>檔名預填：{names[hint.value]}</b>（{hint.rule}）{hint.conflict?<ul>{hint.conflict_reasons.map((r:string,i:number)=><li key={i}>{r}</li>)}</ul>:<button className="secondary" onClick={()=>setStage(hint.value)}>套用預填</button>}</div>}
  <div className="segmented" role="radiogroup" aria-label="分類標籤">{AREAS.cls.labels.map(([k,v]:any)=><button key={k} role="radio" aria-checked={stage===k} className={stage===k?'active':''} onClick={()=>setStage(k)}>{v}</button>)}</div>
  <div className="form-grid compact"><label className="field">影像品質<select value={quality} onChange={e=>setQuality(e.target.value)}><option value="">未評估</option><option value="acceptable">可用</option><option value="limited">勉強可用</option><option value="unusable">不可用</option></select></label>
  <label className="field">個案研究編號（化名）<input value={subject} maxLength={100} onChange={e=>setSubject(e.target.value)}/><small>不可由檔名代碼推定，請勿填姓名。</small></label></div>
  <SaveBar busy={busy} operator={operator} reason={reason} setReason={setReason} onSave={save} disabled={failed||stage==='unknown'} hint={stage==='unknown'?'選擇分類後才能完成；也可存為待處理。':'二分類由分期推得：正常＝陰性，第一／二期與陽性未分期＝陽性。'}/>
  <Reasons tasks={d.tasks}/><History d={d}/></>;
}

function StageBatch({items,act,onDone}:any){
 const candidates=items.filter((r:any)=>r.stage_suggestion&&!r.stage_suggestion.conflict&&!r.stage_suggestion.confirmed&&r.state!=='excluded');
 const operator=useOperator();const [picked,setPicked]=useState<string[]>([]),[reason,setReason]=useState('確認檔名預填分期'),[result,setResult]=useState<any[]|null>(null);
 if(!candidates.length)return <p className="slot-note muted">本頁沒有待確認的檔名預填。合作醫院照片已依授權規則自動分類。</p>;
 return <details className="slot-note"><summary>批次確認檔名預填（本頁 {candidates.length} 張，非合作醫院來源）</summary><div className="batch-list">{candidates.map((r:any)=><label className="check" key={r.image_id}><input type="checkbox" checked={picked.includes(r.image_id)} onChange={e=>setPicked(e.target.checked?[...picked,r.image_id]:picked.filter(x=>x!==r.image_id))}/><DisplayName row={r}/> → {names[r.stage_suggestion.value]}</label>)}</div>
  <div className="toolbar"><button className="secondary" onClick={()=>setPicked(candidates.map((r:any)=>r.image_id))}>全選本頁</button><input aria-label="確認原因" value={reason} onChange={e=>setReason(e.target.value)}/>
  <button disabled={!picked.length||!reason.trim()||!operator} onClick={()=>act(async()=>{const map=Object.fromEntries(candidates.map((r:any)=>[r.image_id,r]));const res=await api('/data/stage-confirm','POST',{reviewer:operator,reason,items:picked.map(id=>({image_id:id,revision:map[id].revision,stage:map[id].stage_suggestion.value,approve:true}))});setResult(res.results);setPicked([]);onDone();return res},'批次確認已處理')}>確認 {picked.length} 張</button></div>
  {result&&<ul>{result.map((r:any)=><li key={r.image_id}>{r.image_id}：{r.ok?'已確認':'未處理 — '+r.error}</li>)}</ul>}</details>;
}

export function DataReview({act}:any){
 const {params}=useHash();
 const area=params.get('area')==='cls'?'cls':'det';const view=VIEWS.some(v=>v[0]===params.get('view'))?params.get('view')!:'pending';
 const label=params.get('label')||'',source=params.get('source')||'',reviewer=params.get('reviewer')||'',page=Math.max(1,Number(params.get('page'))||1),selected=params.get('image')||'';
 const query=new URLSearchParams({area,view,page:String(page),size:'24'});if(label)query.set('label',label);if(source)query.set('source',source);if(reviewer)query.set('reviewer',reviewer);
 const rows=useData('/data-area?'+query.toString(),1000,d=>d?.index?.state==='ready'||d?.index?.state==='failed');
 const go=(next:Obj,keep=true)=>{const base:Obj=keep?{area,view,label,source,reviewer,page:String(page),image:selected}:{area};const merged={...base,...next};route('data',Object.fromEntries(Object.entries(merged).filter(([,v])=>v!==''&&v!=null)) as Obj)};
 const items:Obj[]=rows.data?.items||[];
 const select=(id:string)=>go({image:id});
 const step=(delta:number)=>{if(!items.length)return;const i=items.findIndex(x=>x.image_id===selected);const next=items[Math.min(items.length-1,Math.max(0,(i<0?0:i+delta)))];if(next)select(next.image_id)};
 const nextPending=()=>{const i=items.findIndex(x=>x.image_id===selected);const after=[...items.slice(i+1),...items.slice(0,Math.max(0,i))].find(x=>x.state==='pending'&&x.image_id!==selected);if(after)select(after.image_id);else if(rows.data&&page*rows.data.size<rows.data.total)go({page:String(page+1),image:''});else go({image:''})};
 useEffect(()=>{const f=(e:KeyboardEvent)=>{if(typing(e.target)||e.altKey||e.ctrlKey||e.metaKey)return;if(e.key==='ArrowRight'){e.preventDefault();step(1)}if(e.key==='ArrowLeft'){e.preventDefault();step(-1)}};addEventListener('keydown',f);return()=>removeEventListener('keydown',f)});
 const meta=AREAS[area];const counts=rows.data?.counts||{};const labelCounts=rows.data?.labels||{};
 const snapshotTask=area==='det'?'detection':'stage_classification';
 return <div className={'area-page area-'+area}>
  <AreaSwitch area={area} onChange={a=>go({area:a},false)}/>
  <section className="panel area-header"><div className="area-title"><h2>{meta.title}</h2><p>{meta.desc}</p></div>
   <Progress progress={rows.data?.progress}/>
   <div className="view-pills" role="tablist" aria-label="處理狀態">{VIEWS.map(([k,v])=><button key={k} role="tab" aria-selected={view===k} className={view===k?'active':''} onClick={()=>go({view:k,page:'1',image:''})}>{v}<span>{counts[k]??'…'}</span></button>)}</div></section>
  <section className="panel toolbar-card"><div className="filters">
   <label className="field">{area==='det'?'框選狀態':'分類標籤'}<select value={label} onChange={e=>go({label:e.target.value,page:'1',image:''})}><option value="">全部</option>{meta.labels.map(([k,v]:any)=><option key={k} value={k}>{v}（{labelCounts[k]??0}）</option>)}</select></label>
   <label className="field">來源<select value={source} onChange={e=>go({source:e.target.value,page:'1',image:''})}><option value="">全部來源</option>{Object.entries(SOURCE_NAMES).map(([k,v])=><option key={k} value={k}>{v}</option>)}</select></label>
   <label className="field">最近審查者<select value={reviewer} onChange={e=>go({reviewer:e.target.value,page:'1',image:''})}><option value="">全部</option><option value="__unknown__">未記錄</option>{(rows.data?.reviewers||[]).map((r:string)=><option key={r}>{r}</option>)}</select></label></div>
   <div className="tool-actions"><IndexBadge index={rows.data?.index} onRecheck={()=>api('/data-index/rebuild','POST').then(rows.refresh)}/><ImportPanel kind="photos"/><ExternalImport/>
    <a className="button secondary" href={'#models?tab=snapshots&task='+snapshotTask}>以此區建立訓練快照 →</a></div></section>
  <section className="panel list-card"><div className="list-head"><span>共 <b>{rows.data?.total??'…'}</b> 筆{label?' · '+labelName(area,label):''}{source?' · '+SOURCE_NAMES[source]:''}</span>
   <div className="pager"><button className="secondary" disabled={!rows.data?.items?.some((x:Obj)=>x.state==='pending')} onClick={nextPending}>下一張待處理</button><span>第 {page} / {Math.max(1,Math.ceil((rows.data?.total||0)/24))} 頁</span><button className="secondary icon-btn" aria-label="上一頁" disabled={page<=1} onClick={()=>go({page:String(page-1),image:''})}>‹</button><button className="secondary icon-btn" aria-label="下一頁" disabled={!rows.data||page*24>=rows.data.total} onClick={()=>go({page:String(page+1),image:''})}>›</button></div></div>
   {area==='cls'?<StageBatch items={items} act={act} onDone={rows.refresh}/>:<p className="slot-note muted">{!rows.data?'讀取中…':counts.pending?`還有 ${counts.pending} 張待處理。第一／二期照片需框選病灶；正常照片已依檔名設為無病灶負樣本。`:'所有照片皆已處理。'}</p>}
   {rows.error&&<p role="alert"><span>{rows.error}</span> <button onClick={()=>rows.refresh()}>重試</button></p>}
   {!rows.data?(!rows.error&&<Empty>載入資料…</Empty>):<div className="review-layout"><section className="gallery" aria-label={meta.title+'圖片清單'}>{items.map(r=><button data-image-id={r.image_id} className={'thumb '+(selected===r.image_id?'selected':'')} key={r.image_id} onClick={()=>select(r.image_id)}>
     <img loading="lazy" src={'/api/v1/data/'+r.image_id+'/image?thumbnail=true'} width={160} height={120} alt={r.display_name||r.image_id}/>
     <div><b><DisplayName row={r}/></b><span className="card-meta"><span className={'state-badge '+r.state}>{STATE_NAMES[r.state]}</span><span className="chip">{labelName(area,r.labels[meta.labelKey])}</span><span className="chip source">{SOURCE_NAMES[r.source]}</span></span></div></button>)}
     {!items.length&&<Empty>{view==='pending'?'此區目前沒有待處理的照片。':'這個分類目前沒有符合條件的照片。'}</Empty>}</section>
    <section className="panel editor-panel">{selected?(area==='det'?<YoloEditor key={'det'+selected} ident={selected} act={act} onSaved={(done:boolean)=>{rows.refresh();if(done)nextPending()}}/>:<ClassifyEditor key={'cls'+selected} ident={selected} act={act} onSaved={(done:boolean)=>{rows.refresh();if(done)nextPending()}}/>)
     :<Empty>選擇左側照片開始{area==='det'?'框選':'分類'}。可用鍵盤 ← → 切換照片。</Empty>}</section></div>}</section>
 </div>;
}
