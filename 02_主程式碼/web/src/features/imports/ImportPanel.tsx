import {invalidate} from '../../shared/query';
import React,{useState,useEffect,useRef} from 'react';
import {api,useData,Empty,Pager,when,Fields,route} from '../../shared/ui';
import {Dialog} from '../../shared/dialog';

const STATES:Record<string,string>={scanning:'掃描中',ready:'預覽就緒',queued:'已提交',running:'匯入中',completed:'完成',failed:'失敗',needs_check:'中斷後待檢查'};
const ACTIONS:Record<string,string>={add:'補入',alias:'補記來源名稱（不重複匯入）',hold:'隔離待人工決定',reject:'不匯入'};

/** Read-only scan of an explicitly configured external folder (e.g. 合作醫院), then import via the normal pipeline. */
export function ExternalImport(){
 const [open,setOpen]=useState(false),[source,setSource]=useState(''),[id,setId]=useState(''),[page,setPage]=useState(1),[error,setError]=useState(''),[busy,setBusy]=useState(false),[confirm,setConfirm]=useState(''),[category,setCategory]=useState('');
 const sources=useData('/imports/external-sources',0,undefined,{enabled:open});
 // A single configured source (合作醫院) is chosen automatically: open → 掃描 → 確認匯入.
 useEffect(()=>{const list=sources.data?.items||[];if(!source&&list.length===1)setSource(list[0].key)},[sources.data]);
 const history=useData('/imports/external-operations',0,undefined,{enabled:open});
 const detail=useData('/imports/operations/'+id+'?page='+page+'&size=100',1000,d=>['ready','completed','failed','needs_check'].includes(d?.state),{enabled:open&&!!id});
 const value=detail.data;const notified=useRef('');useEffect(()=>{if(value?.state==='completed'&&notified.current!==value.id){notified.current=value.id;invalidate(['data','/overview']);void history.refresh()}},[value?.state,value?.id]);
 const action=async(fn:()=>Promise<any>)=>{setBusy(true);setError('');try{const r=await fn();setId(r.id);setPage(1);await detail.refresh()}catch(e){setError((e as Error).message)}finally{setBusy(false)}};
 const items=(value?.items||[]).filter((i:any)=>!category||i.category===category);
 return <><button className="secondary" onClick={()=>setOpen(true)}>外部來源比對與補入</button>{open&&<Dialog title="外部照片來源（唯讀掃描）" onClose={()=>setOpen(false)}>
 <p>只讀取 configs/import_sources.json 明列的資料夾；不搬移、改名、覆寫或刪除來源。以內容雜湊比對：已存在者只補記來源檔名作為顯示名稱，缺少者複製到 inbox 後走既有匯入流程。授權來源（合作醫院）的新照片會依檔名自動完成「其他模型分類區」；正常照片在 YOLO 區自動設為無病灶，第一／二期照片需到 YOLO 區框選。</p><p className="muted">每日新增：把照片放進來源資料夾（可建新子資料夾，檔名維持 日期_床號_LH/RH/LL_分期_序號），再按「掃描並比對」→ 輸入「確認匯入」。已匯入過的照片以內容雜湊判斷，不會重複。</p>
 <label className="field">來源<select value={source} onChange={e=>{setSource(e.target.value);setId('');setConfirm('')}}><option value="">選擇來源</option>{sources.data?.items.map((s:any)=><option key={s.key} value={s.key}>{s.name}（規則 {s.label_rule||'無'}）</option>)}</select></label>
 <button disabled={!source||busy} onClick={()=>action(()=>api('/imports/external-previews','POST',{source}))}>掃描並比對</button>{sources.error&&<p role="alert">{sources.error}</p>}
 <details><summary>最近外部來源操作</summary>{history.data?.items.map((r:any)=><button className="secondary" key={r.id} onClick={()=>{setId(r.id);setPage(1)}}>{r.batch} · {STATES[r.state]||r.state} · {when(r.updated)}</button>)}</details>
 {(error||detail.error)&&<p role="alert">{error||detail.error}</p>}{id&&!value&&<Empty>正在取得狀態…</Empty>}
 {value&&<section aria-live="polite"><h3>狀態：{STATES[value.state]||value.state}{value.phase?' · '+value.phase:''}</h3>{value.state==='scanning'&&value.total!=null&&<p>已處理 {value.processed??0} / {value.total} 個檔案</p>}{value.error&&<p role="alert">{value.error}</p>}
 {value.summary&&<div className="stats compact">{Object.entries(value.summary).map(([k,n]:any)=><button key={k} className={'stat '+(category===k?'selected':'')} onClick={()=>setCategory(category===k?'':k)}><small>{value.category_names?.[k]||k}</small><strong>{n}</strong></button>)}</div>}
 <div className="table-wrap"><table><thead><tr><th>來源檔名（相對路徑）</th><th>比對結果</th><th>處理</th><th>檔名規則</th><th>說明</th></tr></thead><tbody>{items.map((item:any,i:number)=><tr key={i}><td className="break">{item.name}</td><td>{value.category_names?.[item.category]||item.category}</td><td>{ACTIONS[item.action]||item.action}{item.image_id&&<small className="break"> → {item.image_id}</small>}</td><td>{item.label?({normal:'正常',stage1:'第一期',stage2:'第二期',unknown:'無法判定'} as Record<string,string>)[item.label.value]:'—'}</td><td>{item.reason}{item.notes?.map((n:string,k:number)=><p key={k}>{n}</p>)}{item.result&&<p>{item.result}</p>}{item.near&&<p>近似：{item.near.map((x:any)=>x.image_id+'（距離 '+x.distance+'）').join('、')}</p>}</td></tr>)}</tbody></table></div><Pager page={page} total={value.total||0} size={100} onPage={setPage}/>
 {value.state==='ready'&&<><label className="field">輸入「確認匯入」<input value={confirm} onChange={e=>setConfirm(e.target.value)}/></label><button disabled={confirm!=='確認匯入'||busy} onClick={()=>action(()=>api('/imports/external-operations','POST',{preview_id:id,idempotency_key:'external:'+id,confirmation:confirm}))}>確認補入與補記名稱</button></>}
 {value.state==='completed'&&<div className="callout"><b>匯入完成</b><p>本次新增 {(value.items||[]).filter((i:any)=>i.action==='add'&&i.image_id).length} 張（本頁統計）{value.rule_summary?`；分類區本次自動完成 ${value.rule_summary['cls:applied']||0} 張；YOLO 區目前待框選 ${value.rule_summary['det:needs_boxes']||0} 張`:''}。</p><div className="actions"><a className="button secondary" href="#data?area=det&view=pending" onClick={()=>setOpen(false)}>前往 YOLO 框選區 →</a><a className="button secondary" href="#data?area=cls&view=confirmed" onClick={()=>setOpen(false)}>查看分類區 →</a></div></div>}
 {['failed','needs_check'].includes(value.state)&&<button className="secondary" disabled={busy} onClick={()=>action(()=>api('/imports/operations/'+id+'/retry','POST'))}>重試原操作（已完成步驟不重做）</button>}
 </section>}</Dialog>}</>;
}

export function ImportPanel({kind}:{kind:'photos'|'models'}){
 const [open,setOpen]=useState(false),[batch,setBatch]=useState(''),[id,setId]=useState(''),[page,setPage]=useState(1),[error,setError]=useState(''),[busy,setBusy]=useState(false),[confirm,setConfirm]=useState('');
 const batches=useData('/imports/batches?kind='+kind,0,undefined,{enabled:open});
 const detail=useData('/imports/operations/'+id+'?page='+page,1000,d=>['ready','completed','failed','needs_check'].includes(d?.state),{enabled:open&&!!id});
 const [historyPage,setHistoryPage]=useState(1);const history=useData('/imports/operations?kind='+kind+'&page='+historyPage,0,undefined,{enabled:open});
 const value=detail.data;const notified=useRef('');useEffect(()=>{if(value?.state==='completed'&&notified.current!==value.id){notified.current=value.id;invalidate([kind==='photos'?'data':'models','/overview']);void history.refresh()}},[value?.state,value?.id]);
 const action=async(fn:()=>Promise<any>)=>{setBusy(true);setError('');try{const r=await fn();setId(r.id);await detail.refresh()}catch(e){setError((e as Error).message)}finally{setBusy(false)}};
 return <><button className="secondary" onClick={()=>setOpen(true)}>{kind==='photos'?'匯入照片':'匯入模型'}</button>{open&&<Dialog title={kind==='photos'?'從 inbox 匯入照片':'從 inbox 匯入模型'} onClose={()=>setOpen(false)}>
 <p>將來源放入 inbox/{kind}/批次名稱。來源保留，正式複本另占空間；匯入不會自動核准圖片或啟用模型。</p>
 <label className="field">待匯入批次<select value={batch} onChange={e=>{setBatch(e.target.value);setId('');setPage(1);setConfirm('')}}><option value="">選擇批次</option>{batches.data?.items.map((name:string)=><option key={name}>{name}</option>)}</select></label>
 <button className="secondary" disabled={busy} onClick={()=>batches.refresh()}>重新列出批次</button>{batches.error&&<p role="alert">{batches.error}</p>}
 <details><summary>最近匯入紀錄與恢復</summary><Pager page={historyPage} size={30} total={history.data?.total||0} onPage={setHistoryPage}/>{history.data?.items.map((r:any)=><button className="secondary" key={r.id} onClick={()=>{setId(r.id);setPage(1)}}>{r.batch} · {r.state} · {when(r.updated)}</button>)}</details><button disabled={!batch||busy} onClick={()=>action(()=>api('/imports/previews','POST',{kind,batch}))}>掃描並預覽</button>
 {(error||detail.error)&&<p role="alert">{error||detail.error}</p>}
 {id&&!value&&<Empty>正在取得匯入狀態…</Empty>}
 {value&&<section aria-live="polite"><h3>匯入狀態：{({scanning:'掃描中',ready:'預覽就緒',queued:'已提交',running:'匯入中',completed:'完成',failed:'失敗',needs_check:'中斷後待檢查'} as Record<string,string>)[value.state]||value.state}</h3>
 <p>更新時間：{when(value.updated)} · 操作 ID：{value.id}</p>{value.error&&<p role="alert">{value.error}</p>}{value.cleanup_warnings?.length>0&&<div role="status"><p>正式匯入已保存，下列暫存尚未清理：</p><ul>{value.cleanup_warnings.map((w:string)=><li key={w}>{w}</li>)}</ul></div>}
 {value.additional_bytes!=null&&<p>預計新增檔案 {(value.additional_bytes/1024**2).toFixed(2)} MiB；暫存及安全餘裕需要 {(value.required_free_bytes/1024**2).toFixed(2)} MiB 可用空間。</p>}
 <div className="table-wrap"><table><thead><tr><th>來源</th><th>處理方式</th><th>原因／結果</th><th>容量</th></tr></thead><tbody>{value.items?.map((item:any,i:number)=><tr key={i}><td className="break">{item.name}</td><td>{({add:'新增（待確認）',skip:'略過重複',reject:'拒絕'} as Record<string,string>)[item.action]}</td><td>{item.reason}{item.name_conflict&&<p>同名不同內容：配置新的識別碼及檔名，不覆寫。</p>}{item.annotations?.some((a:any)=>a.state!=='provisional')&&<p>候選標註需要人工核對方向或座標。</p>}{item.artifact&&<p className="break">新版本：{item.artifact}</p>}</td><td>{item.bytes==null?'未知':item.bytes.toLocaleString()+' bytes'}</td></tr>)}</tbody></table></div>
 {value.items?.filter((i:any)=>i.package).map((i:any)=><section key={i.name}><h3>模型包設定與用途</h3><Fields value={{purpose:i.package.purpose,model:i.package.model,task:i.task,config:i.package.config,source:i.package.source,evaluation_status:'未評估／未啟用',files:i.files?.map((f:any)=>({source:f.source,bytes:f.bytes,sha256:f.sha256}))}}/></section>)}<Pager page={page} total={value.total} size={30} onPage={setPage}/>
 {value.state==='ready'&&<><label className="field">輸入「確認匯入」<input value={confirm} onChange={e=>setConfirm(e.target.value)}/></label><button disabled={confirm!=='確認匯入'||busy} onClick={()=>action(()=>api('/imports/operations','POST',{preview_id:id,idempotency_key:'import:'+id,confirmation:confirm}))}>確認新增</button></>}
 {['failed','needs_check'].includes(value.state)&&<button className="secondary" disabled={busy} onClick={()=>action(()=>api('/imports/operations/'+id+'/retry','POST'))}>重試原操作</button>}
 {value.state==='completed'&&value.items?.some((i:any)=>i.package?.purpose==='checkpoint')&&<button className="secondary" disabled={busy} onClick={async()=>{setBusy(true);try{const job=await api('/imports/operations/'+id+'/resume','POST');setOpen(false);route('models',{tab:'jobs',job:job.id})}catch(e){setError((e as Error).message)}finally{setBusy(false)}}}>明確提交此 checkpoint 續訓</button>}<p>關閉視窗不會取消已提交的匯入。成功收據保存於 runtime/imports/receipts。</p>
 </section>}
 </Dialog>}</>;
}
