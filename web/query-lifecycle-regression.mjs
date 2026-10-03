// Synthetic fixture only. Visibility events are simulated, not an OS background-tab test.
import {chromium,expect} from '@playwright/test';
import fs from 'node:fs';
const browser=await chromium.launch({channel:'msedge',headless:true});
const page=await browser.newPage(),checks=[],errors=[],requests=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('request',r=>{if(r.url().includes('/api/v1/'))requests.push(r.url())});
const count=path=>requests.filter(u=>new URL(u).pathname==='/api/v1'+path).length;
const check=name=>{checks.push({name,passed:true});console.log('PASS '+name)};
const visibility=async hidden=>page.evaluate(value=>{
 Object.defineProperty(document,'hidden',{configurable:true,get:()=>value});
 document.dispatchEvent(new Event('visibilitychange'));
},hidden);
try {
 await page.goto('http://127.0.0.1:8877/#overview');
 await page.locator('.stat').first().waitFor();
 await visibility(true);requests.length=0;await page.waitForTimeout(4500);
 expect(count('/overview')).toBe(0);check('visibility hidden stops overview polling');
 await page.evaluate(()=>dispatchEvent(new CustomEvent('workbench-resources-changed',{detail:{scopes:['/overview']}})));
 await page.waitForTimeout(200);expect(count('/overview')).toBe(0);check('hidden invalidation does not issue a request');
 const refreshed=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/v1/overview');
 await visibility(false);await refreshed;await page.waitForTimeout(100);
 expect(count('/overview')).toBe(1);check('visibility restore refreshes overview once');
 requests.length=0;
 await page.evaluate(()=>dispatchEvent(new CustomEvent('workbench-resources-changed',{detail:{scopes:['models']}})));
 await page.waitForTimeout(200);expect(count('/overview')).toBe(0);check('unrelated scope does not refresh overview');
 const jobsLoaded=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/v1/jobs-query');
 await page.goto('http://127.0.0.1:8877/#models?tab=jobs');
 await jobsLoaded;
 await page.waitForTimeout(200);requests.length=0;await page.waitForTimeout(6500);
 expect(count('/jobs-query')).toBe(0);expect(count('/overview')).toBe(0);
 check('terminal-only jobs and inactive overview stop polling');
 expect(errors).toEqual([]);
} finally {
 fs.mkdirSync('../runtime/performance',{recursive:true});
 fs.writeFileSync('../runtime/performance/query-lifecycle-results.json',JSON.stringify({visibility:'simulated document visibility events',checks,errors},null,2));
 await browser.close();
}
