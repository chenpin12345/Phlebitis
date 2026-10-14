import React,{useState,useEffect,useRef} from 'react';

type AllIds={ids:string[],total:number,limit:number};

// Explicit selection that can span pages: the header box selects every row matching the
// current filter (fetched from the server), not only the visible page.
export function useSelection(resetKey:string){
 const [selected,setSelected]=useState<string[]>([]),[note,setNote]=useState('');
 useEffect(()=>{setSelected([]);setNote('')},[resetKey]);
 const has=(id:string)=>selected.includes(id);
 const toggle=(id:string,on:boolean)=>setSelected(on?(has(id)?selected:[...selected,id]):selected.filter(x=>x!==id));
 const clear=()=>{setSelected([]);setNote('')};
 return {selected,setSelected,has,toggle,clear,note,setNote};
}

export function SelectAllBox({selection,total,fetchAll,label}:{selection:ReturnType<typeof useSelection>,total:number,fetchAll:()=>Promise<AllIds>,label:string}){
 const ref=useRef<HTMLInputElement>(null);const [busy,setBusy]=useState(false);
 const count=selection.selected.length,all=total>0&&count>=total;
 useEffect(()=>{if(ref.current)ref.current.indeterminate=count>0&&!all},[count,all]);
 // Checked immediately while the full id list loads, so the click gets instant feedback.
 return <input ref={ref} type="checkbox" aria-label={label} disabled={!total} aria-busy={busy} checked={all||busy} onChange={async e=>{if(busy)return;
  if(!e.target.checked){selection.clear();return}
  setBusy(true);
  try{const r=await fetchAll();selection.setSelected(r.ids);selection.setNote(r.total>r.ids.length?`符合條件共 ${r.total} 筆，單次最多選取 ${r.limit} 筆。`:'')}
  catch(err){selection.setNote((err as Error).message)}
  finally{setBusy(false)}}}/>;
}

export function SelectionStatus({selection,total}:{selection:ReturnType<typeof useSelection>,total:number}){
 const count=selection.selected.length;
 return <span className="selection-status">已選取 {count} 筆{count&&count>=total?'（全部符合條件）':''}{selection.note&&<small className="muted"> {selection.note}</small>}</span>;
}
