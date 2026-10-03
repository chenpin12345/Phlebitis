// Destructive UI actions below target only tests/workbench_fixture.py on 8877.
import {chromium,expect} from '@playwright/test';
import fs from 'node:fs';
const base='http://127.0.0.1:8877',out=new URL('../docs/verification/',import.meta.url);
const browser=await chromium.launch({channel:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1000}}),checks=[],errors=[];
page.on('pageerror',e=>errors.push(e.message));
const check=name=>{checks.push({name,passed:true});console.log('PASS '+name)};
const shot=name=>page.screenshot({path:new URL('trash-'+name+'.png',out).pathname.replace(/^\/([A-Za-z]:)/,'$1'),fullPage:true});
const get=async path=>{const r=await page.request.get(base+'/api/v1'+path);expect(r.ok()).toBeTruthy();return r.json()};
const session=await get('/session');
const post=async(path,body)=>{const r=await page.request.post(base+'/api/v1'+path,{data:body,headers:{'X-CSRF-Token':session.csrf}});expect(r.ok(),await r.text()).toBeTruthy();return r.json()};
const close=()=>page.getByRole('dialog').getByRole('button',{name:'關閉／取消'}).click();
try{
 await page.goto(base+'/#settings');await page.getByLabel('操作者（自行填寫）',{exact:true}).fill('垃圾桶驗收');
 await expect(page.locator('.topbar input')).toHaveCount(0);await expect(page.locator('.topbar')).not.toContainText('GPU');
 await expect(page.locator('nav a').last()).toHaveAttribute('href','#trash');check('operator relocated and trash last in navigation');
 await page.goto(base+'/#data');await expect(page.getByText('建立資料快照',{exact:true})).toHaveCount(0);
 await page.goto(base+'/#models?tab=new');await page.getByText('建立資料快照',{exact:true}).click();
 const dataset=page.getByLabel('資料快照與驗證折',{exact:true});await expect(dataset).toHaveValue('');
 await page.getByRole('button',{name:'建立快照',exact:true}).click();
 await page.getByText(/目前資料選取未自動變更/).waitFor();await expect(dataset).toHaveValue('');
 const options=await dataset.locator('option').evaluateAll(nodes=>nodes.map(n=>n.value).filter(Boolean));expect(options.length).toBe(3);
 await dataset.selectOption(options[1]);await expect(dataset).toHaveValue(options[1]);
 await expect(page.locator('main pre')).toHaveCount(0);check('snapshot entry moved, explicit creation and manual fold selection');await shot('experiment');

 await page.goto(base+'/#models?tab=compare&model=yolo11n');await page.getByRole('heading',{name:'模型評估比較'}).waitFor();
 const reports=await get('/reports-query?model=yolo11n');expect(reports.total).toBe(2);
 await expect(page.getByRole('button',{name:/^yolo11n · .*／fold/})).toHaveCount(2);
 await expect(page.locator('main')).not.toContainText('OOF');
 const enlarge=page.getByRole('button',{name:'放大評估圖片 history_00',exact:true});await enlarge.click();
 const modal=page.getByRole('dialog',{name:'歷史評估圖片'});await expect(modal).toBeVisible();await expect(modal.getByRole('button',{name:'關閉／取消'})).toBeFocused();
 const img=modal.locator('img');await expect(img).toHaveAttribute('src',/\/reports\/[67]{32}\/images\/history_00$/);
 const geometry=await img.evaluate(i=>({fit:getComputedStyle(i).objectFit,w:i.naturalWidth,h:i.naturalHeight}));expect(geometry.fit).toBe('contain');expect(geometry.w/geometry.h).toBe(2);
 await page.keyboard.press('Tab');expect(await modal.evaluate(d=>d.contains(document.activeElement))).toBe(true);
 await page.keyboard.press('Escape');await expect(modal).toHaveCount(0);await expect(enlarge).toBeFocused();
 await page.reload();await expect(page).toHaveURL(/image=history_00/);await page.getByText('同一張圖片的模型結果',{exact:true}).waitFor();
 check('repeated reports kept, historical thumbnails, modal keyboard and URL selection');await shot('comparison');
 await page.getByRole('button',{name:'下一頁',exact:true}).last().click();await expect(page.getByRole('button',{name:/^放大評估圖片 /})).toHaveCount(4);
 await page.getByText('此報告保存的圖片不存在；未使用目前圖片替代。',{exact:true}).waitFor();
 check('sample pagination and missing historical image with no manifest fallback');
 await page.getByLabel('模型方案篩選').selectOption('dinov2_small');await page.getByText('此模型沒有符合條件的評估報告。',{exact:true}).waitFor();await page.reload();await expect(page.getByLabel('模型方案篩選')).toHaveValue('dinov2_small');
 await page.goBack();await expect(page.getByLabel('模型方案篩選')).toHaveValue('yolo11n');check('empty exact filter, refresh and browser back');
 await page.route('**/api/v1/reports-query?*',async r=>{if(new URL(r.request().url()).searchParams.get('model')==='yolo11n')await new Promise(resolve=>setTimeout(resolve,500));await r.continue().catch(()=>{})});
 await page.getByLabel('模型方案篩選').selectOption('efficientnet_b0');await expect(page.getByRole('button',{name:/^efficientnet_b0 · .*／fold/})).toHaveCount(1);await page.waitForTimeout(700);await expect(page.getByRole('button',{name:/^yolo11n · .*／fold/})).toHaveCount(0);await page.unroute('**/api/v1/reports-query?*');check('model switch rejects stale report response');

 await page.goto(base+'/#models?tab=jobs&job='+'1'.repeat(32));await page.getByRole('button',{name:'移至垃圾桶',exact:true}).click();
 await expect(page.getByRole('dialog').getByRole('button',{name:'關閉／取消'})).toBeFocused();await page.keyboard.press('Enter');await expect(page.getByRole('dialog')).toHaveCount(0);expect((await get('/jobs')).some(j=>j.id==='1'.repeat(32))).toBe(true);
 check('safe initial focus and Enter cancels without deleting');
 await page.getByRole('button',{name:'移至垃圾桶',exact:true}).click();await page.getByRole('button',{name:'確認移至垃圾桶',exact:true}).click();
 await expect.poll(async()=> (await get('/jobs')).some(j=>j.id==='1'.repeat(32))).toBe(false);
 await page.goto(base+'/#trash?type=job');const row=page.locator('tbody tr').filter({has:page.getByRole('checkbox',{name:'選取 '+'1'.repeat(32),exact:true})});await expect(row).toHaveCount(1);
 await row.getByText('資源明細',{exact:true}).click();await expect(row).toContainText('欄位內容估計');await expect(page.locator('main pre')).toHaveCount(0);await shot('job-capacity');
 await page.reload();await expect(page.getByRole('combobox',{name:'類型',exact:true})).toHaveValue('job');await row.getByRole('button',{name:'還原',exact:true}).click();await page.getByRole('button',{name:'確認還原',exact:true}).click();await expect.poll(async()=> (await get('/jobs')).some(j=>j.id==='1'.repeat(32)&&j.state==='succeeded')).toBe(true);
 check('job move/restore preserves ID, execution state, capacity and deep link');

 await page.goto(base+'/#settings');await page.getByLabel('操作類型',{exact:true}).selectOption('legacy');await page.getByRole('checkbox',{name:'選取當頁稽核',exact:true}).check();
 const selected=(await get('/audit-query?action=legacy')).items.map(a=>a.id);expect(selected.length).toBe(1);
 await page.getByRole('button',{name:'移至垃圾桶',exact:true}).first().click();await page.getByRole('button',{name:'確認移至垃圾桶',exact:true}).click();
 await expect.poll(async()=> (await get('/audit-query?action=legacy')).total).toBe(0);
 await page.goto(base+'/#trash?type=audit');await page.getByRole('checkbox',{name:'選取當頁全部項目',exact:true}).check();await page.getByRole('button',{name:'永久刪除',exact:true}).first().click();
 const purge=page.getByRole('button',{name:'確認永久刪除',exact:true});await expect(purge).toBeDisabled();await page.getByLabel('永久刪除確認文字').fill('錯誤');await expect(purge).toBeDisabled();await page.getByLabel('永久刪除確認文字').fill('永久刪除');await expect(purge).toBeEnabled();await shot('purge-confirmation');await purge.click();
 await expect.poll(async()=> (await get('/trash?type=audit')).total).toBe(0);expect((await get('/audit')).some(a=>selected.includes(a.id))).toBe(false);
 await page.goto(base+'/#trash');await page.getByText('垃圾桶目前是空的。',{exact:true}).waitFor();check('audit explicit batch selection, typed purge and exact deletion');

 const artifact=(await get('/artifacts'))[0];await post('/artifacts/activate',{artifact:artifact.id,target:'local',allow_unevaluated:true});await post('/artifacts/activate',{artifact:artifact.id,target:'local',allow_unevaluated:true});
 await page.goto(base+'/#models?tab=registry');await page.getByRole('button',{name:'移至垃圾桶',exact:true}).click();await page.getByText(/local 目前使用引用此模型/).waitFor();await expect(page.getByRole('button',{name:'確認移至垃圾桶'})).toBeDisabled();await close();
 await page.goto(base+'/#settings');await page.getByRole('button',{name:'預覽解除此引用',exact:true}).click();await page.getByRole('dialog').getByLabel('請輸入「解除回復引用」').fill('解除回復引用');await page.getByRole('button',{name:'確認解除',exact:true}).click();await expect(page.getByRole('dialog')).toHaveCount(0);
 const chain=(await get('/references')).find(r=>r.target==='local');expect(chain.nodes.length).toBe(1);expect(chain.nodes[0].artifact).toBe(artifact.id);check('reference blockers and explicit historical release preserve current model');

 for(const [hash,ready] of [['trash','垃圾桶目前是空的。'],['models?tab=compare&model=yolo11n','模型評估比較'],['models?tab=new','建立資料快照']]){
  await page.goto(base+'/#'+hash);await page.getByText(ready,{exact:true}).waitFor();
  for(const width of [1440,820,390]){await page.setViewportSize({width,height:950});expect(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)).toBe(false);}
  await shot(hash.startsWith('trash')?'empty-narrow':hash.includes('compare')?'comparison-narrow':'experiment-narrow');check('responsive no overflow '+hash);
 }
 await page.route('**/api/v1/trash?*',r=>r.fulfill({status:403,json:{detail:'隔離測試：權限不足'}}));await page.goto(base+'/#trash');await page.getByText('隔離測試：權限不足',{exact:true}).waitFor();await expect(page.getByRole('checkbox',{name:'選取當頁全部項目'})).toHaveCount(0);check('trash permission error with no stale rows');
 expect(errors).toEqual([]);
}catch(error){await shot('failure');console.error(await page.locator('[role="alert"]').allTextContents());throw error}
finally{fs.writeFileSync(new URL('trash-browser-results.json',out),JSON.stringify({checks,errors},null,2));await browser.close()}
console.log(JSON.stringify({passed:checks.length,errors}));
