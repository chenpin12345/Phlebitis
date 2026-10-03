import {invalidate} from '../../shared/query';
import React,{useState,useEffect,useRef} from 'react';
import {api,useData,Empty,Pager,when,Fields,route} from '../../shared/ui';
import {Dialog} from '../../shared/dialog';

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
