// Renders the LINE message structures this project actually sends (from src/line_bot/messages.py).
// Anything else is shown as explicitly unsupported instead of being silently dropped.
import {useState} from 'react';
type Obj=Record<string,any>;
const SIZES:Obj={xxs:'.62rem',xs:'.7rem',sm:'.78rem',md:'.9rem',lg:'1.05rem',xl:'1.2rem',xxl:'1.4rem'};
const SPACING:Obj={none:0,xs:'2px',sm:'4px',md:'8px',lg:'12px',xl:'16px',xxl:'20px'};

function FlexNode({node}:{node:Obj}){
 if(node?.type==='box'){
  return <div className={'flex-box '+(node.layout==='horizontal'?'horizontal':'vertical')} style={{gap:SPACING[node.spacing]??0}}>{(node.contents||[]).map((c:Obj,i:number)=><FlexNode key={i} node={c}/>)}</div>;
 }
 if(node?.type==='text'){
  return <p className={'flex-text'+(node.wrap?' wrap':'')} style={{fontWeight:node.weight==='bold'?700:400,fontSize:SIZES[node.size]||SIZES.md,color:node.color||undefined}}>{node.text}</p>;
 }
 return <p className="unsupported">不支援的 Flex 元件：{String(node?.type)}</p>;
}

export function LineMessage({message}:{message:Obj}){
 if(message.type==='text')return <div className="line-text">{message.text}</div>;
 if(message.type==='image')return <ResultImage src={message.originalContentUrl}/>;
 if(message.type==='flex'){
  const c=message.contents||{};
  if(c.type!=='bubble')return <div className="unsupported">不支援的 Flex 容器：{String(c.type)}（altText：{message.altText}）</div>;
  return <div className="flex-bubble" aria-label={message.altText}>{c.body?<FlexNode node={c.body}/>:<p className="unsupported">bubble 沒有 body</p>}</div>;
 }
 return <div className="unsupported">不支援的訊息類型：{String(message.type)}</div>;
}

export function ResultImage({src,alt='模型分析結果圖',expired='結果圖已過期或已撤回（一小時暫存）'}:{src:string,alt?:string,expired?:string}){
 const [failed,setFailed]=useState(false);
 return failed?<div className="unsupported">{expired}</div>:<img className="line-image" src={src} alt={alt} onError={()=>setFailed(true)}/>;
}

export function quickItems(message?:Obj){return (message?.quickReply?.items||[]) as Obj[]}
