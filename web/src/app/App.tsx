import {useState,useEffect} from 'react';
type Obj=Record<string,any>;
import {api,useData,setCSRF} from '../shared/ui';
import {Settings} from '../features/maintenance/Settings';
import {TrashPage} from '../features/trash/Trash';
import {Empty} from '../shared/app-ui';
import {Overview} from '../features/overview/Overview';
import {DataPage} from '../features/data-review/DataPage';
import {ModelsPage} from '../features/models/ModelsPage';
import {Simulator} from '../features/simulator/Simulator';
import {Cases} from '../features/cases/Cases';
export function App(){
 const [page,setPage]=useState(location.hash.slice(1).split('?')[0]||'overview'),[notice,setNotice]=useState(''),[error,setError]=useState(''),[ready,setReady]=useState(false);
 const overview=useData('/overview',4000,undefined,{enabled:ready&&page==='overview'});useEffect(()=>{const fn=(e:Event)=>setError((e as CustomEvent).detail);addEventListener('workbench-error',fn);return()=>removeEventListener('workbench-error',fn)},[]);
 useEffect(()=>{api('/session').then(x=>{setCSRF(x.csrf);setReady(true)}).catch(e=>setError(e.message));const fn=()=>setPage(location.hash.slice(1).split('?')[0]||'overview');addEventListener('hashchange',fn);return()=>removeEventListener('hashchange',fn)},[]);
 const act=async(fn:()=>Promise<any>,message='已完成')=>{setError('');setNotice('處理中…');try{const value=await fn();setNotice(message);overview.refresh();return value}catch(e){setNotice('');setError((e as Error).message);return null}};
 const nav=[['overview','總覽','研究流程與目前狀態'],['data','資料審查','圖片、標註與資料版本'],['models','模型與實驗','訓練、評估與模型管理'],['simulator','LINE 模擬','本地對話與事件除錯'],['cases','案例與回歸','人工確認與版本比較'],['settings','設定與維護','環境、保存與操作紀錄'],['trash','垃圾桶','還原、容量與安全刪除']];
 return <div className="shell"><aside className="sidebar"><a className="brand" href="#overview"><span className="mark">P<span>∿</span></span><div>PHLEBITIS<small>LOCAL RESEARCH WORKBENCH</small></div></a><div className="nav-caption">研究工作區</div><nav>{nav.map(([id,label,hint])=><a key={id} href={'#'+id} aria-current={page===id?'page':undefined} className={page===id?'current':''}><b>{label}</b><small>{hint}</small></a>)}</nav><div className="sidebar-foot"><span className="dot"/>本機運算 · 圖片不傳雲端<small>研究展示 / 無嚴重度分級</small></div></aside>
 <div className="workspace"><header className="topbar"><span>Phlebitis <span className="muted">/ {nav.find(x=>x[0]===page)?.[1]}</span></span></header>
 <main><div role="alert" className={error?'notice error':'notice'} hidden={!error&&!notice}>{error||notice}<button className="plain" onClick={()=>{setError('');setNotice('')}} aria-label="關閉通知">×</button></div>
 {!ready?<Empty>{error?<>本地服務尚未連接。<button onClick={()=>api('/session').then(x=>{setCSRF(x.csrf);setReady(true);setError('')}).catch(e=>setError(e.message))}>重新連接</button></>:<>正在連接本地服務…</>}</Empty>:<>{page==='overview'&&<Overview data={overview.data} error={overview.error}/>}{page==='data'&&<DataPage act={act}/>} {page==='models'&&<ModelsPage act={act}/>} {page==='simulator'&&<Simulator act={act}/>} {page==='cases'&&<Cases act={act}/>} {page==='settings'&&<Settings act={act}/>} {page==='trash'&&<TrashPage/>}</>}
 </main><footer>研究展示結果不代表疾病診斷；未偵測到也無法排除疾病。模型分數不代表嚴重度。</footer></div></div>
}
