// Isolated fixture only. Never submit mutations or launch training.
import {chromium} from '@playwright/test';
import fs from 'node:fs';
const tag=process.argv[2]||'after',port=process.argv[3]||'8877';if(!['8877','8878'].includes(port))throw Error('Fixture ports only');const base='http://127.0.0.1:'+port;
const browser=await chromium.launch({channel:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1050}});
const stats=a=>({n:a.length,median:a.toSorted((a,b)=>a-b)[Math.floor(a.length/2)],p95:a.toSorted((a,b)=>a-b)[Math.ceil(a.length*.95)-1]});
const result={tag,at:new Date().toISOString(),api:{},pages:{},errors:[]};
page.on('pageerror',e=>result.errors.push(e.message));
try {
 for(const path of ['/overview','/data-query','/data-query?view=approved','/models','/artifacts','/jobs','/reports-query','/curve-sources','/cases','/audit-query','/trash']){
  const times=[];let bytes=0;const timings=[];
  for(let i=0;i<50;i++){const t=performance.now();const r=await page.request.get(base+'/api/v1'+path);bytes=(await r.body()).length;timings.push(r.headers()['server-timing']||null);if(!r.ok())throw Error(path+':'+r.status());times.push(performance.now()-t)}
  result.api[path]={...stats(times),bytes,timings};
 }
 for(const route of ['data?view=pending_review','data?view=approved','models?tab=catalog','models?tab=jobs','models?tab=compare','models?tab=registry','models?tab=curves','settings','trash','cases','simulator','overview']){
  const times=[],counts=[],sizes=[],images=[];let failed=0;
  for(let i=0;i<20;i++){
   let count=0,bytes=0;const response=async r=>{if(r.url().includes('/api/')){count++;try{bytes+=(await r.body()).length}catch{}}};const failure=()=>failed++;
   await page.goto('about:blank');page.on('response',response);page.on('requestfailed',failure);const t=performance.now();await page.goto(base+'/#'+route);await page.locator('.shell').waitFor();
   if(route.startsWith('data'))await page.locator('.thumb').first().waitFor();else await page.waitForLoadState('networkidle');
   times.push(performance.now()-t);if(route.startsWith('data')){await page.locator('.thumb img').first().evaluate(im=>im.complete&&im.naturalWidth?true:new Promise(resolve=>{im.onload=()=>resolve(true);im.onerror=()=>resolve(false)}));images.push(performance.now()-t)}await page.waitForTimeout(50);counts.push(count);sizes.push(bytes);page.off('response',response);page.off('requestfailed',failure);
  }
  result.pages[route]={...stats(times),requests:stats(counts),bytes:stats(sizes),first_image:images.length?stats(images):null,failed};
 }
}finally{fs.mkdirSync('../runtime/performance',{recursive:true});fs.writeFileSync('../runtime/performance/'+tag+'.json',JSON.stringify(result,null,2));await browser.close()}
