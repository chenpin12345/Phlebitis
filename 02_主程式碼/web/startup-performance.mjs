// Isolated synthetic servers only. This measures a new process, not a cold OS file cache.
import {chromium} from '@playwright/test';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import net from 'node:net';
import fs from 'node:fs';
import path from 'node:path';
const project=path.resolve('..'),python=path.join(project,'.venv/Scripts/python.exe');
const baseline=path.join(project,'runtime/code_backups/performance-imports-20261002-221129');
const results=[],browser=await chromium.launch({channel:'msedge',headless:true});
try {
 for(const [tag,root,port] of [['before',baseline,8878],['after',project,8877]]){
  const probe=net.createServer();probe.listen(port,'127.0.0.1');await once(probe,'listening');await new Promise(resolve=>probe.close(resolve));
  const t=performance.now(),child=spawn(python,['tests/workbench_fixture.py',String(port)],{cwd:root,env:{...process.env,PYTHONPATH:root},windowsHide:true,stdio:['ignore','pipe','pipe']});
  let log='';for(const stream of [child.stdout,child.stderr])stream.on('data',b=>{log=(log+b.toString()).slice(-5000)});
  const exited=once(child,'exit');
  try{
   const base='http://127.0.0.1:'+port;
   let last='not connected';
   for(;;){if(child.exitCode!==null)throw Error(log);try{const r=await fetch(base+'/api/v1/session',{signal:AbortSignal.timeout(1000)});last='HTTP '+r.status;if(r.ok)break}catch(e){last=e.message+': '+(e.cause?.message||'')}if(performance.now()-t>120000)throw Error('Fixture startup timeout: '+last+' '+log);await new Promise(resolve=>setTimeout(resolve,50))}
   const process_to_session_ms=performance.now()-t,page=await browser.newPage({viewport:{width:1440,height:1050}});console.log(tag+' session ready');
   const start=performance.now();await page.goto(base+'/#data?view=pending_review');await page.locator('.thumb').first().waitFor();
   const list_visible_ms=performance.now()-start;
   await page.locator('.thumb img').first().evaluate(im=>im.complete&&im.naturalWidth?true:new Promise(resolve=>{im.onload=()=>resolve(true);im.onerror=()=>resolve(false)}));
   results.push({tag,n:1,process_to_session_ms,list_visible_ms,first_image_ms:performance.now()-start,includes_fixture_creation:true,os_cache:'uncontrolled'});await page.close();
  }finally{if(process.platform==='win32'){const stop=spawn('taskkill',['/PID',String(child.pid),'/T','/F'],{windowsHide:true,stdio:'ignore'});await once(stop,'exit')}else child.kill();await exited;}
 }
}finally{await browser.close();fs.writeFileSync(path.join(project,'runtime/performance/startup-results.json'),JSON.stringify(results,null,2));console.log(JSON.stringify(results))}
