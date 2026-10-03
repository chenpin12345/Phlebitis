import React,{useEffect,useRef} from 'react';

export function Dialog({title,children,onClose}:{title:string,children:React.ReactNode,onClose:()=>void}){
 const ref=useRef<HTMLDialogElement>(null);
 useEffect(()=>{const previous=document.activeElement as HTMLElement|null;ref.current?.showModal();ref.current?.querySelector<HTMLButtonElement>('[data-safe]')?.focus();return()=>{ref.current?.close();previous?.focus()}},[]);
 const keyboard=(e:React.KeyboardEvent<HTMLDialogElement>)=>{if(e.key==='Enter'&&(e.target as HTMLElement).tagName==='INPUT')e.preventDefault();if(e.key==='Tab'){const items=Array.from(e.currentTarget.querySelectorAll<HTMLElement>('button,input,select,textarea,a[href],summary,[tabindex]')).filter(n=>!n.hasAttribute('disabled')&&n.tabIndex>=0&&n.getClientRects().length);const first=items[0],last=items.at(-1);if(!items.length){e.preventDefault();e.currentTarget.focus()}else if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()}}};
 return <dialog ref={ref} className="managed-dialog" aria-label={title} onCancel={e=>{e.preventDefault();onClose()}} onKeyDown={keyboard}><header><h2>{title}</h2><button type="button" data-safe className="secondary" onClick={onClose}>關閉／取消</button></header>{children}</dialog>
}
