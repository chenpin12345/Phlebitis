import {fileURLToPath} from 'node:url';
// Only run against tests/workbench_fixture.py: never use the real workbench port.
import {chromium,expect} from '@playwright/test';
import fs from 'node:fs';
const base='http://127.0.0.1:8877';
const out=new URL('../../01_文件與紀錄/驗證報告/verification/',import.meta.url);fs.mkdirSync(out,{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1050}});
const errors=[],checks=[];page.on('pageerror',e=>errors.push(e.message));
const check=(name,details={})=>{checks.push({name,passed:true,...details});console.log('PASS '+name)};
const json=async path=>{const r=await page.request.get(base+'/api/v1'+path);expect(r.ok()).toBeTruthy();return r.json()};
const screenshot=async name=>page.screenshot({path:fileURLToPath(new URL(name+'.png',out)),fullPage:true});
const VIEW_NAMES={pending:'待處理',confirmed:'已完成',excluded:'排除',all:'全部'};
async function assertArea(area,view){const expected=await json(`/data-area?area=${area}&view=${view}&size=24`);await expect(page.locator('.thumb')).toHaveCount(expected.items.length);expect(await page.locator('.thumb').evaluateAll(nodes=>nodes.map(n=>n.dataset.imageId))).toEqual(expected.items.map(r=>r.image_id));await expect(page.getByRole('tab',{name:new RegExp('^'+VIEW_NAMES[view])})).toHaveAttribute('aria-selected','true');await expect(page.locator('.area-tab.active')).toContainText(area==='det'?'YOLO 病灶框選區':'其他模型分類區');return expected}
async function imagePoint(x,y){return page.locator('svg.annotation').evaluate((s,{x,y})=>{const v=s.viewBox.baseVal,p=new DOMPoint(x*v.width,y*v.height).matrixTransform(s.getScreenCTM());return {x:p.x,y:p.y}},{x,y})}
async function openDetection(id){await page.goto(base+`/#data?area=det&view=all&image=${id}`);await page.locator('.segmented').first().waitFor()}
async function openClassify(id){await page.goto(base+`/#data?area=cls&view=all&image=${id}`);await page.locator('.segmented').first().waitFor()}
async function saved(text){await page.getByRole('alert').filter({hasText:text}).waitFor()}
async function drag(x1,y1,x2,y2){const a=await imagePoint(x1,y1),b=await imagePoint(x2,y2);await page.mouse.move(a.x,a.y);await page.mouse.down();await page.mouse.move(b.x,b.y,{steps:6});await page.mouse.up()}
try{
 await page.goto(base);await page.getByRole('heading',{name:'總覽',exact:true}).waitFor();
 await page.goto(base+'/#settings');await page.getByLabel('操作者（自行填寫）',{exact:true}).fill('瀏覽器測試');
 for(const area of ['det','cls']){
  await page.goto(base+'/#data?area=cls&view=excluded');
  await page.getByRole('link',{name:'總覽',exact:true}).click();
  await page.locator(`a.area-card[href="#data?area=${area}"]`).click();
  await assertArea(area,'pending');check('overview area card opens '+area+' with actual image IDs');
 }
 await page.goto(base+'/#data?area=det&view=confirmed');await assertArea('det','confirmed');
 await page.reload();await assertArea('det','confirmed');
 await page.getByRole('tab',{name:/^排除/}).click();await assertArea('det','excluded');
 await page.goBack();await assertArea('det','confirmed');await page.goForward();await assertArea('det','excluded');
 await page.locator('.area-tab',{hasText:'其他模型分類區'}).click();await assertArea('cls','pending');await page.goBack();await assertArea('det','excluded');
 check('deep link, reload, back/forward and area switch preserve view and actual data');
 const shape=async()=>page.locator('.area-page').evaluate(p=>[...p.children].map(e=>e.tagName+'.'+e.className.replace(/area-(det|cls)/,'')));
 await page.goto(base+'/#data?area=det');await page.locator('.list-card').waitFor();const detShape=await shape();
 await page.goto(base+'/#data?area=cls');await page.locator('.list-card').waitFor();expect(await shape()).toEqual(detShape);check('both areas share one layout structure');
 // Race: a stale pending response cannot overwrite the explicit confirmed route.
 await page.route('**/api/v1/data-area?*',async r=>{const q=new URL(r.request().url()).searchParams;if(q.get('view')==='pending'&&q.get('size')==='24')await new Promise(resolve=>setTimeout(resolve,500));await r.continue().catch(()=>{})});
 await page.goto(base+'/#data?area=det&view=pending');await page.getByRole('tab',{name:/^已完成/}).click();await assertArea('det','confirmed');await page.waitForTimeout(600);await assertArea('det','confirmed');await page.unroute('**/api/v1/data-area?*');check('stale data request rejected');
 for(const [id,ratio] of [['a_landscape',160/90],['b_portrait',90/160],['c_square',1],['d_exif',90/160]]){
  await openDetection(id);await page.locator('svg.annotation image').waitFor();
  const geometry=await page.locator('svg.annotation').evaluate(s=>{const m=s.getScreenCTM(),v=s.viewBox.baseVal;return {sx:m.a,sy:m.d,ratio:v.width/v.height,mode:s.getAttribute('preserveAspectRatio')}});
  expect(geometry.sx).toBeCloseTo(geometry.sy,6);expect(geometry.ratio).toBeCloseTo(ratio,6);expect(geometry.mode).toBe('xMidYMid meet');
  await page.setViewportSize({width:820,height:960});const small=await page.locator('svg.annotation').evaluate(s=>({sx:s.getScreenCTM().a,sy:s.getScreenCTM().d}));expect(small.sx).toBeCloseTo(small.sy,6);await page.setViewportSize({width:1440,height:1050});
  check('aspect ratio and responsive alignment: '+id);
 }
 // d_exif is a confirmed no-lesion image in the YOLO area; draw a lesion there without touching classification.
 const clsBefore=(await json('/data/d_exif/annotation?area=cls')).labels;
 await page.locator('svg.annotation').scrollIntoViewIfNeeded();await page.getByRole('button',{name:'新增矩形',exact:true}).click();
 const svgBounds=await page.locator('svg.annotation').boundingBox();await page.mouse.click(svgBounds.x+2,svgBounds.y+2);expect(await page.locator('.box-fields').count()).toBe(0);
 await drag(.2,.2,.5,.5);await expect(page.getByLabel('框 1 中心 X',{exact:true})).toHaveValue('0.35');
 await page.getByRole('button',{name:'選取／移動',exact:true}).click();await drag(.35,.35,.45,.45);
 await expect(page.getByLabel('框 1 中心 X',{exact:true})).toHaveValue('0.45');await drag(.6,.6,.7,.8);
 const coords=await Promise.all(['中心 X','中心 Y','寬','高'].map(k=>page.getByLabel('框 1 '+k,{exact:true}).inputValue()));
 await expect(page.getByRole('radio',{name:'已框選病灶'})).toHaveAttribute('aria-checked','true');
 await page.getByRole('button',{name:'儲存並完成',exact:true}).click();await saved('YOLO 區已儲存');
 expect((await json('/data/d_exif/annotation?area=cls')).labels).toEqual(clsBefore);check('YOLO boxes do not change the classification area');
 await openClassify('d_exif');await expect(page.locator('svg.annotation')).toHaveCount(0);await expect(page.locator('.preview img')).toBeVisible();
 await page.getByRole('radio',{name:'第一期'}).click();await page.getByRole('button',{name:'儲存並完成',exact:true}).click();await saved('其他模型分類區已儲存');
 await openDetection('d_exif');await page.locator('svg.annotation').waitFor();
 for(let i=0;i<4;i++)expect(Number(await page.getByLabel('框 1 '+['中心 X','中心 Y','寬','高'][i],{exact:true}).inputValue())).toBeCloseTo(Number(coords[i]),5);
 check('classification shows no boxes; its change keeps YOLO boxes; EXIF coordinates survive reload',{coords});await screenshot('review-desktop');
 await page.goto(base+'/#data?area=det&view=confirmed&reviewer=瀏覽器測試');await expect(page.locator('.thumb')).toHaveCount(1);
 await page.goto(base+'/#data?area=det&view=excluded&reviewer=瀏覽器測試');await expect(page.locator('.thumb')).toHaveCount(0);await page.getByText('這個分類目前沒有符合條件的照片。',{exact:true}).waitFor();check('reviewer filter and empty state per area');
 await page.goto(base+'/#data?area=det&view=all&image=a_landscape');await page.locator('svg.annotation').waitFor();await page.locator('h1').click();await page.keyboard.press('ArrowRight');await expect(page).toHaveURL(/image=(?!a_landscape)/);check('keyboard arrows move between photos');

 // Regular artifact expansion is readable; advanced JSON remains unmounted.
 await page.goto(base+'/#models?tab=registry');await page.getByText('產物與設定',{exact:true}).click();await page.getByRole('heading',{name:'版本摘要',exact:true}).waitFor();
 const artifact=page.locator('.artifact-details');await expect(artifact.locator('pre')).toHaveCount(0);await artifact.getByRole('button',{name:'查看設定',exact:true}).click();await artifact.getByRole('heading',{name:'設定檔：settings.json'}).waitFor();await expect(artifact.locator('pre')).toHaveCount(0);await expect(artifact).toContainText('[已遮罩]');await expect(artifact).not.toContainText('fixture-secret');
 const downloadPromise=page.waitForEvent('download');await artifact.getByRole('link',{name:'下載',exact:true}).click();const download=await downloadPromise;expect(download.suggestedFilename()).toBe('best.pt');
 const exportPromise=page.waitForEvent('download');await artifact.getByRole('link',{name:'匯出原始設定',exact:true}).last().click();expect((await exportPromise).suggestedFilename()).toBe('model-settings.json');
 await screenshot('artifact-readable');await artifact.getByText('產物指紋與登錄明細',{exact:true}).click();await expect(artifact.locator('pre')).toHaveCount(0);check('artifact tables, settings, weight download, explicit raw export and advanced view');
 await page.goto(base+'/#models?tab=curves&experiment='+'1'.repeat(32));await page.locator('.metric-chart').first().waitFor();await expect(page.locator('.metric-chart')).toHaveCount(3);await expect(page.locator('.metric-chart').filter({hasText:'val/box_loss'})).toContainText('缺值保留斷線');
 await page.getByLabel('顯示輔助平滑曲線（原始曲線保留）').check();await screenshot('curves');
 await page.getByLabel('選擇實驗').selectOption('2'.repeat(32));await expect(page.locator('.metric-chart')).toHaveCount(3);await expect(page.locator('.metric-chart h3')).toHaveText(['train_loss','val_accuracy','val_loss']);
 await page.getByLabel('選擇實驗').selectOption('3'.repeat(32));await page.getByText('此方案擷取特徵後擬合分類器，沒有逐 epoch 訓練曲線。').waitFor();
 const options=await page.getByLabel('選擇實驗').locator('option').evaluateAll(os=>os.map(o=>o.value));await page.getByLabel('選擇實驗').selectOption(options.find(o=>o.startsWith('legacy_')));await page.getByText('框架產生的歷史曲線圖片',{exact:true}).click();await expect(page.locator('img.artifact-image')).toBeVisible();check('detection, classification, DINO and image-only historical curves');
 let polling=0;page.on('request',req=>{if(req.url().includes('/curve-history'))polling++});await page.goto(base+'/#overview');await page.waitForTimeout(2800);expect(polling).toBe(0);check('curve polling stops on page exit');
 await page.goto(base+'/#models?tab=jobs&job='+'2'.repeat(32));await page.getByRole('heading',{name:'訓練 · 失敗'}).waitFor();await page.getByText('設定值／實際使用值',{exact:true}).click();await expect(page.locator('main')).toContainText('未提供');await expect(page.locator('main pre:visible')).toHaveCount(0);
 await page.getByText('階段時間軸與日誌',{exact:true}).click();await page.getByLabel('搜尋日誌').fill('no-match');await expect(page.locator('main')).toContainText('無符合條件的日誌');check('failed job readable, actual values missing, log search');
 await page.goto(base+'/#models?tab=jobs&job='+'5'.repeat(32));await page.getByRole('heading',{name:'future_job · 失敗'}).waitFor();check('unknown job type fallback');
 await page.goto(base+'/#settings');await page.getByText('目前沒有到期資料',{exact:true}).waitFor();await page.getByRole('heading',{name:'套件版本'}).waitFor();await expect(page.locator('main pre:visible')).toHaveCount(0);await page.getByLabel('操作類型',{exact:true}).selectOption('enqueue');await expect(page.locator('main')).toContainText('共 37 筆');await page.getByRole('button',{name:'下一頁',exact:true}).click();await expect(page.locator('main')).toContainText('第 2 / 2 頁');await page.getByLabel('操作者',{exact:true}).selectOption('測試乙');await page.getByText('沒有符合條件的操作紀錄。',{exact:true}).waitFor();await expect(page.locator('main')).toContainText('第 1 / 1 頁');check('maintenance tables and audit filtering/pagination reset');await screenshot('maintenance');
 for(const width of [1440,820,390]){await page.setViewportSize({width,height:950});await openDetection('a_landscape');await page.locator('svg.annotation').waitFor();const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);expect(overflow).toBe(false);await screenshot('review-'+width);check('responsive review no page overflow '+width)}
 // Loading/error path uses no wrong-size editor and can't submit annotations.
 await page.route('**/api/v1/data/b_portrait/image',r=>r.abort());await openDetection('b_portrait');await page.getByText('圖片無法載入，請重新整理或檢查原檔。',{exact:true}).waitFor();await expect(page.getByRole('button',{name:'儲存並完成'})).toBeDisabled();await expect(page.locator('svg.annotation')).toHaveCount(0);check('failed image disables editing');
 // Running fixture and rapid experiment switching, without starting a training worker.
 let liveRequests=0;
 await page.route('**/api/v1/curve-history?*',async r=>{const source=new URL(r.request().url()).searchParams.get('source');if(source==='2'.repeat(32)){liveRequests++;const response=await r.fetch();const d=await response.json();await r.fulfill({json:{...d,state:'running'}})}else await r.continue()});
 await page.goto(base+'/#models?tab=curves&experiment='+'2'.repeat(32));await page.locator('.metric-chart').first().waitFor();await expect.poll(()=>liveRequests,{timeout:7000}).toBeGreaterThanOrEqual(2);
 await page.getByLabel('選擇實驗').selectOption('1'.repeat(32));await expect(page.locator('.metric-chart h3')).toHaveText(['metrics/mAP50(B)','train/box_loss','val/box_loss']);
 const stopped=liveRequests;await page.waitForTimeout(2800);expect(liveRequests).toBe(stopped);await page.unroute('**/api/v1/curve-history?*');check('running experiment refresh and selection stops prior polling');
 // Keyboard geometry access, separate from pointer drag tests.
 await openDetection('a_landscape');const rect=page.getByRole('img',{name:'圖片與標註編輯器'}).getByLabel('選取框 1');await rect.focus();await page.keyboard.press('ArrowRight');await expect(page.getByLabel('框 1 中心 X',{exact:true})).toHaveValue('0.501');check('keyboard rectangle movement');
 for(const [hash,ready] of [['models?tab=registry','產物與設定'],['settings','目前沒有到期資料'],['models?tab=curves&experiment='+'1'.repeat(32),'訓練曲線']]){
  await page.goto(base+'/#'+hash);if(hash.includes('registry')){await page.getByText(ready,{exact:true}).click();await page.getByRole('heading',{name:'版本摘要'}).waitFor();await page.getByRole('button',{name:'查看設定'}).click()}else if(hash==='settings')await page.getByText(ready,{exact:true}).waitFor();else await page.locator('.metric-chart').first().waitFor();
  for(const width of [390,820]){await page.setViewportSize({width,height:950});expect(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)).toBe(false)}
  await screenshot(hash.startsWith('settings')?'maintenance-narrow':hash.includes('registry')?'artifact-narrow':'curves-narrow');check('narrow page no overflow '+hash.split('&')[0]);
 }
 // Offline simulator: switching iOS/Android keeps the same conversation and never re-sends.
 await page.goto(base+'/#simulator');let posts=0;page.on('request',r=>{if(r.method()==='POST'&&r.url().endsWith('/simulation/events'))posts++});
 await page.getByLabel('訊息',{exact:true}).fill('拍照說明');await page.keyboard.press('Enter');await page.locator('.line-phone .bubble.bot').first().waitFor();const bubbles=await page.locator('.line-phone .bubble').count();
 await page.getByRole('radio',{name:'Android 樣式'}).click();await expect(page.locator('.line-phone.android')).toHaveCount(1);await page.waitForTimeout(1600);expect(await page.locator('.line-phone .bubble').count()).toBe(bubbles);expect(posts).toBe(1);
 await page.getByRole('button',{name:'展開圖文選單'}).click();await expect(page.locator('.rich-area')).toHaveCount(4);await expect(page.locator('.quick-reply button')).toHaveCount(4);await screenshot('simulator-android');check('simulator platform switch keeps state; rich menu and quick reply render');
 await page.goto(base+'/#intake');await page.getByText(/目前沒有符合條件的研究收件/).waitFor();await page.goto(base+'/#cases');await expect(page).toHaveURL(/#models$/);await expect(page.getByRole('button',{name:'回歸測試'})).toHaveCount(0);check('intake empty state, legacy cases link and no regression tab');
 await page.route('**/api/v1/data-area?*',r=>r.fulfill({status:403,json:{detail:'測試權限不足'}}));await page.goto(base+'/#data?area=det&view=confirmed');await page.getByText('測試權限不足',{exact:true}).waitFor();await expect(page.locator('.thumb')).toHaveCount(0);check('permission error remains visible and never shows stale data');
 expect(errors).toEqual([]);
}catch(error){await screenshot('failure');console.error(await page.locator('[role="alert"]').allTextContents());throw error}finally{fs.writeFileSync(new URL('browser-results.json',out),JSON.stringify({checks,errors},null,2));await browser.close()}
console.log(JSON.stringify({passed:checks.length,errors}));
