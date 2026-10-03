import {useEffect,useRef,useState} from 'react';

export class RequestError extends Error {constructor(message:string,public status=0){super(message)}}
type Entry={controller:AbortController,promise:Promise<any>,users:number};
const pending=new Map<string,Entry>();
export function scope(path:string){if(/^\/(data|snapshot)/.test(path))return 'data';if(/^\/(models|artifacts|templates)/.test(path))return 'models';if(/^\/(reports|compar)/.test(path))return 'reports';if(/^\/(jobs|curve)/.test(path))return 'jobs';if(path.startsWith('/trash'))return 'trash';if(path.startsWith('/simulation'))return 'simulation';if(path.startsWith('/cases'))return 'cases';return path.split('?')[0]}
export function invalidate(scopes:string[]){dispatchEvent(new CustomEvent('workbench-resources-changed',{detail:{scopes}}))}
function acquire(path:string,load:(signal:AbortSignal)=>Promise<any>){
 let entry=pending.get(path);
 if(!entry){const controller=new AbortController();entry={controller,users:0,promise:Promise.resolve()};const item=entry;
  item.promise=(async()=>{for(let attempt=0;;attempt++){try{return await load(controller.signal)}catch(e){if(controller.signal.aborted||attempt>=2||(!(e instanceof TypeError)&&!(e instanceof RequestError&&e.status>=500)))throw e;await new Promise<void>((resolve,reject)=>{const done=()=>{controller.signal.removeEventListener('abort',abort);resolve()};const timer=setTimeout(done,500*2**attempt+Math.random()*200);const abort=()=>{clearTimeout(timer);reject(new DOMException('Aborted','AbortError'))};controller.signal.addEventListener('abort',abort,{once:true})})}}})().finally(()=>{if(pending.get(path)===item)pending.delete(path)});pending.set(path,item);
 }
 entry.users++;const item=entry;let released=false;
 return {promise:item.promise,release:()=>{if(released)return;released=true;if(--item.users===0){if(pending.get(path)===item)pending.delete(path);item.controller.abort()}}};
}
export function useQuery(path:string,load:(signal:AbortSignal)=>Promise<any>,interval=0,finished?:(data:any)=>boolean,options:{enabled?:boolean}={}){
 const enabled=options.enabled!==false;
 const [state,set]=useState<{path:string,data:any,error:string,updatedAt:number|null,loading:boolean}>({path,data:null,error:'',updatedAt:null,loading:false});
 const refreshRef=useRef<()=>Promise<any>>(async()=>undefined),loadRef=useRef(load),finishedRef=useRef(finished);loadRef.current=load;finishedRef.current=finished;
 useEffect(()=>{
  let live=true,sequence=0,timer:ReturnType<typeof setTimeout>|undefined,release:(()=>void)|undefined,inFlight:Promise<any>|null=null,dirty=false;
  const refresh=()=>{
   if(!enabled||!live||document.hidden)return Promise.resolve(undefined);
   if(inFlight)return inFlight;
   if(timer)clearTimeout(timer);const generation=++sequence;
   set(old=>old.path===path?{...old,loading:true}:{path,data:null,error:'',updatedAt:null,loading:true});
   const entry=acquire(path,signal=>loadRef.current(signal));release=entry.release;
   inFlight=entry.promise.then(data=>{if(live&&generation===sequence)set({path,data,error:'',updatedAt:Date.now(),loading:false});return data}).catch(e=>{if(live&&generation===sequence&&(e as Error).name!=='AbortError')set(old=>({path,data:old.path===path&&!(e instanceof RequestError&&[401,403].includes(e.status))?old.data:null,error:(e as Error).message,updatedAt:old.path===path?old.updatedAt:null,loading:false}));return undefined}).then(data=>{entry.release();if(generation!==sequence)return data;inFlight=null;if(live&&dirty){dirty=false;void refresh()}else if(live&&data&&interval&&!document.hidden&&!finishedRef.current?.(data))timer=setTimeout(refresh,interval);return data});
   return inFlight;
  };
  refreshRef.current=refresh;
  const visible=()=>{if(document.hidden){if(timer)clearTimeout(timer);++sequence;release?.();inFlight=null}else void refresh()};
  const changed=(event:Event)=>{const scopes=(event as CustomEvent).detail?.scopes as string[]|undefined;if(scopes&&(scopes.includes(scope(path))||scopes.includes('*'))){if(inFlight)dirty=true;else void refresh()}};
  document.addEventListener('visibilitychange',visible);addEventListener('workbench-resources-changed',changed);void refresh();
  return()=>{live=false;++sequence;if(timer)clearTimeout(timer);release?.();document.removeEventListener('visibilitychange',visible);removeEventListener('workbench-resources-changed',changed)};
 },[path,interval,enabled]);
 const matching=enabled&&state.path===path;
 return {data:matching?state.data:null,error:matching?state.error:'',loading:matching?state.loading:false,updatedAt:matching?state.updatedAt:null,refresh:()=>refreshRef.current()};
}
