// Only run against tests/workbench_fixture.py on 8877: never the real workbench port.
import {chromium,expect} from '@playwright/test';
const base='http://127.0.0.1:8877';
const browser=await chromium.launch({channel:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1000}}),checks=[],errors=[];
page.on('pageerror',e=>errors.push(e.message));
const check=name=>{checks.push(name);console.log('PASS '+name)};
const get=async path=>(await page.request.get(base+'/api/v1'+path)).json();
try{
 await page.goto(base+'/#overview');await page.locator('.area-overview .area-card').first().waitFor();
 await expect(page.locator('main > .stats')).toHaveCount(0);await expect(page.getByText('任一區已完成')).toHaveCount(0);await expect(page.getByText('已核對個案')).toHaveCount(0);
 check('overview has no summary stat cards');

 await page.goto(base+'/#data?area=cls&view=all');await page.locator('.toolbar-card').waitFor();
 await expect(page.getByRole('button',{name:'重新套用合作醫院檔名規則'})).toHaveCount(0);
 await expect(page.getByRole('link',{name:'以此區建立訓練快照 →'})).toHaveAttribute('href',/tab=snapshots&task=stage_classification/);
 check('classification area has no re-apply button; snapshot shortcut opens the snapshot tab');

 await page.goto(base+'/#models?tab=regression');await expect(page.locator('.main-tabs button.active')).toHaveText('模型目錄');
 await page.goto(base+'/#models?tab=snapshots&task=binary_classification');await expect(page.getByRole('combobox',{name:'訓練任務',exact:true})).toHaveValue('binary_classification');
 await page.getByRole('heading',{name:'既有快照'}).waitFor();
 await page.goto(base+'/#models?tab=new');await expect(page.getByRole('heading',{name:'建立資料快照'})).toHaveCount(0);await expect(page.getByRole('link',{name:'前往新增快照 →'})).toBeVisible();
 check('regression tab removed; snapshot tab carries the task; experiment form links to it');

 await page.goto(base+'/#settings');const audit=page.getByRole('checkbox',{name:'選取全部符合條件的稽核',exact:true});await audit.waitFor();
 const total=(await get('/audit-query')).total;await audit.check();
 await expect(page.locator('.selection-bar').first()).toContainText('已選取 '+total+' 筆（全部符合條件）');
 const visible=await page.locator('tbody input[type=checkbox]:checked').count();expect(visible).toBeLessThanOrEqual(30);
 await page.locator('tbody input[type=checkbox]').first().uncheck();await expect(page.locator('.selection-bar').first()).toContainText('已選取 '+(total-1)+' 筆');
 expect(await audit.evaluate(i=>i.indeterminate)).toBe(true);await audit.check();await expect(page.locator('.selection-bar').first()).toContainText('已選取 '+total+' 筆');await audit.uncheck();await expect(page.locator('.selection-bar').first()).toContainText('已選取 0 筆');
 check(`audit header selects all ${total} matching rows across pages, indeterminate after unchecking one`);

 const job=(await get('/jobs-query')).items.find(j=>!['queued','running','cancelling'].includes(j.state));
 await page.goto(base+'/#models?tab=jobs');await page.getByRole('checkbox',{name:'選取工作 '+job.id,exact:true}).check();
 await page.locator('.selection-bar').getByRole('button',{name:'移至垃圾桶',exact:true}).click();await page.getByRole('button',{name:'確認移至垃圾桶',exact:true}).click();
 await expect.poll(async()=>(await get('/jobs-query?size=100')).items.some(j=>j.id===job.id)).toBe(false);

 await page.goto(base+'/#trash');const history=page.locator('section.panel').filter({has:page.getByRole('heading',{name:'管理操作紀錄'})});
 await history.getByRole('combobox',{name:'資源類型',exact:true}).selectOption('job');await history.getByRole('combobox',{name:'動作',exact:true}).selectOption('move');
 await expect(history.locator('tbody tr')).toHaveCount(1);await expect(history.locator('tbody tr')).toContainText('工作紀錄');
 await history.getByRole('combobox',{name:'動作',exact:true}).selectOption('purge');await history.getByText('沒有符合篩選條件的操作。').waitFor();
 await history.getByRole('combobox',{name:'動作',exact:true}).selectOption('move');await history.getByRole('checkbox',{name:'選取全部符合條件的操作紀錄',exact:true}).check();
 await history.getByRole('button',{name:'永久刪除選取紀錄'}).click();const dialog=page.getByRole('dialog');
 await dialog.getByText(/可刪除 1 筆/).waitFor();const confirm=dialog.getByRole('button',{name:'確認永久刪除'});await expect(confirm).toBeDisabled();
 await dialog.getByLabel('操作紀錄刪除確認文字').fill('永久刪除操作紀錄');await confirm.click();
 await expect(history.locator('tbody tr')).toHaveCount(0);
 expect((await get('/trash?type=job')).items.some(i=>i.id===job.id)).toBe(true);
 check('operation history filters by resource type and action; selected records are deleted after typed confirmation; trash item kept');

 // All operation records: create a few, header select-all, then delete every deletable record.
 for(const j of (await get('/jobs-query')).items.filter(j=>!['queued','running','cancelling'].includes(j.state)).slice(0,3)){
  await page.goto(base+'/#models?tab=jobs');await page.getByRole('checkbox',{name:'選取工作 '+j.id,exact:true}).check();
  await page.locator('.selection-bar').getByRole('button',{name:'移至垃圾桶',exact:true}).click();await page.getByRole('button',{name:'確認移至垃圾桶',exact:true}).click();
  await expect.poll(async()=>(await get('/jobs-query?size=100')).items.some(x=>x.id===j.id)).toBe(false);
  await page.keyboard.press('Escape');await expect(page.getByRole('dialog')).toHaveCount(0);
 }
 await page.goto(base+'/#trash');
 const allOps=(await get('/trash/operation-history')).total;expect(allOps).toBeGreaterThan(0);
 await history.getByRole('checkbox',{name:'選取全部符合條件的操作紀錄',exact:true}).check();await expect(history.locator('.selection-bar')).toContainText('已選取 '+allOps+' 筆（全部符合條件）');
 await history.getByRole('button',{name:'永久刪除選取紀錄'}).click();await dialog.getByText(new RegExp('選取 '+allOps+' 筆，可刪除')).waitFor();
 await dialog.getByLabel('操作紀錄刪除確認文字').fill('永久刪除操作紀錄');await dialog.getByRole('button',{name:'確認永久刪除'}).click();
 await expect.poll(async()=>(await get('/trash/operation-history')).total).toBeLessThan(allOps);
 const left=await get('/trash/operation-history');expect(left.items.every(o=>o.state!=='completed')).toBe(true);
 check(`operation history select-all (${allOps}) and permanent deletion of every completed record`);

 // Named snapshot, snapshot checkbox → trash, named experiment.
 await page.goto(base+'/#models?tab=snapshots');await page.getByLabel('快照名稱').fill('瀏覽器測試快照');await page.getByRole('checkbox',{name:'允許未核對個案，僅供研究展示'}).check();
 await page.getByRole('button',{name:'建立快照',exact:true}).click();await page.getByText(/已建立 「瀏覽器測試快照」/).waitFor();
 const snap=(await get('/snapshot-options')).find(s=>s.name==='瀏覽器測試快照');expect(snap).toBeTruthy();
 await expect(page.locator('tbody tr').filter({hasText:'瀏覽器測試快照'})).toHaveCount(1);
 await page.goto(base+'/#models?tab=new&task=detection');await expect(page.getByLabel('資料快照與驗證折',{exact:true}).locator('option',{hasText:'瀏覽器測試快照'})).toHaveCount(snap.folds.length);
 await expect(page.getByLabel('實驗名稱（選填）')).toBeVisible();
 await page.goto(base+'/#models?tab=snapshots');const snapCount=(await get('/snapshot-options')).filter(s=>s.purpose!=='independent_test').length;
 await page.getByRole('checkbox',{name:'選取全部快照',exact:true}).check();await expect(page.locator('.selection-bar')).toContainText('已選取 '+snapCount+' 筆（全部符合條件）');await page.getByRole('checkbox',{name:'選取全部快照',exact:true}).uncheck();
 await page.getByRole('checkbox',{name:'選取快照 '+snap.version,exact:true}).check();await page.locator('.selection-bar').getByRole('button',{name:'移至垃圾桶',exact:true}).click();await page.getByRole('button',{name:'確認移至垃圾桶',exact:true}).click();
 await expect.poll(async()=>(await get('/snapshot-options')).some(s=>s.version===snap.version)).toBe(false);
 await expect(page.locator('tbody tr').filter({hasText:'瀏覽器測試快照'})).toHaveCount(0);
 expect((await get('/trash?type=snapshot')).items.map(i=>i.id)).toContain(snap.version);
 check('named snapshot shown in list and experiment dropdown; snapshot checkbox moves it to the trash; experiment name field present');

 for(const width of [390,820]){await page.setViewportSize({width,height:900});for(const hash of ['models?tab=snapshots','models?tab=jobs','trash','overview']){await page.goto(base+'/#'+hash);await page.waitForTimeout(300);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)}}
 check('no horizontal overflow at 390 and 820 on changed pages');
}finally{
 console.log(JSON.stringify({passed:checks.length,errors}));await browser.close();
}
if(errors.length)process.exit(1);
