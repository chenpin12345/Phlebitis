type Obj=Record<string,any>;
import {Badge,Empty,Heading} from '../../shared/app-ui';
const AREA_ROWS=[['det','YOLO 框選區','框選病灶或確認無病灶'],['cls','其他模型分類區','合作醫院照片依檔名自動分類']];
export function Overview({data,error}:any){
 return <><Heading title="總覽">資料、模型與工作的目前狀態。</Heading>{error&&<div className="notice error">{error}</div>}
 {!data?<Empty>載入中…</Empty>:<>
  <section className="panel"><div className="panel-head"><h2>資料進度</h2><a href="#data">前往資料審查</a></div>
   {data.areas?<div className="table-wrap area-overview"><table><thead><tr><th>工作區</th><th className="num">已完成</th><th className="num">待處理</th><th className="num">排除</th><th>進度</th><th>內容</th></tr></thead><tbody>
    {AREA_ROWS.map(([k,t,s])=>{const a=data.areas[k];const usable=a.progress.total-a.progress.excluded;const ratio=a.progress.ratio?Math.round(a.progress.ratio*100):0;return <tr key={k}>
     <td><a className="area-card" href={'#data?area='+k}>{t}</a><small>{s}</small></td><td className="num">{a.progress.confirmed}</td><td className="num">{a.counts.pending}</td><td className="num">{a.progress.excluded}</td>
     <td><div className="meter" role="img" aria-label={`已完成 ${ratio}%`}><span style={{width:ratio+'%'}}/></div><small>{a.progress.confirmed} / {usable}（{ratio}%）</small></td>
     <td>{k==='cls'?<>正常 {a.labels.normal||0}・第一期 {a.labels.stage1||0}・第二期 {a.labels.stage2||0}</>:<>已框選 {a.labels.boxes||0}・無病灶 {a.labels.no_target||0}・未處理 {a.labels.not_annotated||0}</>}</td></tr>})}
   </tbody></table></div>:<Empty>資料索引建立中。</Empty>}</section>
  <div className="two-col">
   <section className="panel"><h2>可用於訓練</h2>
    <table className="kv"><tbody>
     <tr><th>二分類</th><td className="num">{data.task_counts?.binary_classification??0}</td><td>陽性 {data.approved_labels.positive||0}・正常 {data.approved_labels.negative||0}</td></tr>
     <tr><th>分期</th><td className="num">{data.task_counts?.stage_classification??0}</td><td>正常 {data.stage_labels?.normal||0}・第一期 {data.stage_labels?.stage1||0}・第二期 {data.stage_labels?.stage2||0}</td></tr>
     <tr><th>病灶偵測</th><td className="num">{data.task_counts?.detection??0}</td><td>框選區已完成的照片</td></tr>
    </tbody></table>
    {!data.verified_subjects&&<p className="callout info">個案身分尚未核對：建立快照與訓練必須選擇「研究展示」，結果不能視為正式泛化評估。</p>}
   </section>
   <section className="panel"><div className="panel-head"><h2>最近工作</h2><a href="#models?tab=jobs">全部工作</a></div>
    {data.jobs.length?<table><tbody>{data.jobs.slice(0,6).map((j:Obj)=><tr key={j.id}><td>{j.config.name||j.config.model||j.kind}<small className="mono">{j.id.slice(0,8)}</small></td><td><Badge value={j.state}/></td></tr>)}</tbody></table>:<Empty>尚無工作。先建立資料快照，再開始第一個實驗。</Empty>}
    <p className="muted">已登錄 {data.artifacts} 個模型版本；新模型不會自動用於 LINE。</p>
   </section>
  </div></>}</>
}
