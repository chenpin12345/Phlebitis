import React,{useEffect,useRef} from 'react';

export function Dialog({title,children,onClose}:{title:string,children:React.ReactNode,onClose:()=>void}){
 const ref=useRef<HTMLDialogElement>(null);
 useEffect(()=>{const previous=document.activeElement as HTMLElement|null;ref.current?.showModal();ref.current?.querySelector<HTMLButtonElement>('[data-safe]')?.focus();return()=>{ref.current?.close();previous?.focus()}},[]);
 return <dialog ref={ref} className="managed-dialog" aria-label={title} onCancel={e=>{e.preventDefault();onClose()}} onKeyDown={e=>{if(e.key==='Enter'&&(e.target as HTMLElement).tagName==='INPUT')e.preventDefault()}}><header><h2>{title}</h2><button type="button" data-safe className="secondary" onClick={onClose}>關閉／取消</button></header>{children}</dialog>
}
