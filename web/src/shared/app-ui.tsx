import React from 'react';
import {mask} from './ui';
type Obj=Record<string,any>;
export const statusNames:Obj={approved:'可用資料',pending_review:'待人工審查',excluded:'排除',positive:'陽性',negative:'陰性',unknown:'未確認',queued:'等待資源',running:'執行中',cancelling:'停止中',cancelled:'已取消',failed:'失敗',interrupted:'已中斷',succeeded:'完成',ready:'權重已備妥',missing_weights:'尚缺權重',suspected:'疑似陽性',not_detected:'未達陽性門檻',quality_rejected:'品質不足',needs_review:'需人工確認'};
export const pct=(v:any)=>v==null?'N/A':(v*100).toFixed(1)+'%';
export function Badge({value}:{value:string}){return <span className={'badge '+value}>{statusNames[value]||value}</span>}
export function Empty({children}:any){return <div className="empty">{children}</div>}
export function Field({label,children,hint}:any){return <label className="field"><span>{label}</span>{React.isValidElement(children)?React.cloneElement(children as React.ReactElement<any>,{'aria-label':label}):children}{hint&&<small>{hint}</small>}</label>}
export function download(name:string,data:any){const u=URL.createObjectURL(new Blob([JSON.stringify(mask(data),null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=u;a.download=name;a.click();URL.revokeObjectURL(u);}
export function Heading({eyebrow,title,children,actions}:any){return <div className="heading"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{children}</p></div>{actions&&<div className="actions">{actions}</div>}</div>}
