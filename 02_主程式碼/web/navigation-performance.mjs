// Read-only measurements on the synthetic fixture. Both versions use this file.
import {chromium,expect} from '@playwright/test';
import fs from 'node:fs';
const tag=process.argv[2],port=process.argv[3];if(!tag||!['8877','8878'].includes(port))throw Error('Fixture only');
const base='http://127.0.0.1:'+port,browser=await chromium.launch({channel:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1050}}),results={tag,flows:{},errors:[]};
page.on('pageerror',e=>results.errors.push(e.message));
const stats=a=>({n:a.length,median:a.toSorted((a,b)=>a-b)[Math.floor(a.length/2)],p95:a.toSorted((a,b)=>a-b)[Math.ceil(a.length*.95)-1]});
async function flow(name,prepare,act,target){
 const times=[],requests=[],duplicates=[],failed=[],cancelled=[],bytes=[],images=[];
 for(let i=0;i<20;i++){
  await page.goto('about:blank');await prepare();await page.waitForLoadState('networkidle');
  const counts=new Map();let n=0,b=0,bad=0,cancel=0;const bodies=[];
  const req=r=>{if(r.url().includes('/api/')){n++;counts.set(r.url(),(counts.get(r.url())||0)+1)}};
  const fail=r=>{if(r.failure()?.errorText.includes('ABORTED'))cancel++;else bad++};
  const response=r=>{if(r.url().includes('/api/')){if(r.status()>=400)bad++;bodies.push(r.body().then(x=>b+=x.length).catch(()=>{}))}};
  page.on('request',req);page.on('requestfailed',fail);page.on('response',response);
  const t=performance.now();const ready=page.waitForResponse(r=>r.url().includes(target)&&r.ok());await act();await ready;
  await page.locator('.thumb').first().waitFor();await expect(page.locator('.thumb').first()).toBeEnabled();times.push(performance.now()-t);
  await page.locator('.thumb img').first().evaluate(im=>im.complete&&im.naturalWidth?true:new Promise(resolve=>{im.onload=()=>resolve(true);im.onerror=()=>resolve(false)}));images.push(performance.now()-t);
  await page.waitForTimeout(500);await Promise.allSettled(bodies);
  requests.push(n);duplicates.push([...counts.values()].reduce((sum,v)=>sum+Math.max(0,v-1),0));failed.push(bad);cancelled.push(cancel);bytes.push(b);
  page.off('request',req);page.off('requestfailed',fail);page.off('response',response);
 }
 results.flows[name]={actionable:stats(times),first_image:stats(images),requests:stats(requests),duplicate_requests:stats(duplicates),failed:stats(failed),cancelled:stats(cancelled),bytes:stats(bytes)};
 console.log('DONE '+name);
}
try{
 await flow('repeat_entry',async()=>{await page.goto(base+'/#models?tab=catalog')},()=>page.getByRole('link',{name:'資料審查',exact:true}).click(),'/data-query?');
 await flow('switch_category',()=>page.goto(base+'/#data?view=pending_review'),()=>page.getByRole('button',{name:/^可用資料/}).click(),'view=approved');
 await flow('pagination',()=>page.goto(base+'/#data?view=pending_review'),()=>page.getByRole('button',{name:'下一頁',exact:true}).click(),'page=2');
}finally{fs.mkdirSync('../runtime/performance',{recursive:true});fs.writeFileSync('../runtime/performance/'+tag+'-navigation.json',JSON.stringify(results,null,2));await browser.close()}
