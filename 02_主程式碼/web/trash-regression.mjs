import {fileURLToPath} from 'node:url';
// Destructive UI actions below target only tests/workbench_fixture.py on 8877.
import {chromium, expect} from '@playwright/test';
import fs from 'node:fs';
const base = 'http://127.0.0.1:8877',
  out = new URL('../../01_文件與紀錄/驗證報告/verification/', import.meta.url);
const browser = await chromium.launch({channel: 'msedge', headless: true});
const page = await browser.newPage({viewport: {width: 1440, height: 1000}}),
  checks = [],
  errors = [];
page.on('pageerror', e => errors.push(e.message));
const check = name => {
  checks.push({name, passed: true});
  console.log('PASS ' + name);
};
const shot = name => page.screenshot({path: fileURLToPath(new URL('trash-' + name + '.png', out)), fullPage: true});
const get = async path => {
  const r = await page.request.get(base + '/api/v1' + path);
  expect(r.ok()).toBeTruthy();
  return r.json();
};
const session = await get('/session');
const post = async (path, body) => {
  const r = await page.request.post(base + '/api/v1' + path, {data: body, headers: {'X-CSRF-Token': session.csrf}});
  expect(r.ok(), await r.text()).toBeTruthy();
  return r.json();
};
const close = () => page.getByRole('dialog').getByRole('button', {name: '關閉／取消'}).click();
try {
  await page.goto(base + '/#settings');
  await page.getByLabel('操作者（自行填寫）', {exact: true}).fill('垃圾桶驗收');
  // The operator field stays out of the header; the only header input is the global search (batch 1, D4).
  await expect(page.locator('.topbar input:not([type=search])')).toHaveCount(0);
  await expect(page.locator('.topbar')).not.toContainText('GPU');
  await expect(page.locator('nav a').last()).toHaveAttribute('href', '#trash');
  check('operator relocated and trash last in navigation');
  await page.goto(base + '/#data');
  await expect(page.getByText('建立資料快照', {exact: true})).toHaveCount(0);
  await page.goto(base + '/#models');
  await expect(page.locator('.main-tabs button')).toHaveText([
    '模型目錄',
    '新增快照',
    '建立實驗',
    '工作監測',
    '評估比較',
    '模型版本',
    '訓練曲線',
  ]);
  await page.goto(base + '/#models?tab=snapshots');
  await page.getByRole('heading', {name: '建立資料快照', exact: true}).waitFor();
  await page.getByRole('button', {name: '建立快照', exact: true}).click();
  await page.getByRole('link', {name: '用此快照建立實驗 →', exact: true}).first().click();
  await expect(page).toHaveURL(/tab=new&task=binary_classification/);
  // Batch 4: 三折全部執行 is on by default; this check is about choosing one fold by hand.
  await page.getByLabel(/全部折都執行/).uncheck();
  const dataset = page.getByLabel('資料快照與驗證折', {exact: true});
  await expect(dataset).toHaveValue('');
  const options = await dataset.locator('option').evaluateAll(nodes => nodes.map(n => n.value).filter(Boolean));
  expect(options.length).toBe(3);
  await dataset.selectOption(options[1]);
  await expect(dataset).toHaveValue(options[1]);
  await expect(page.locator('main pre')).toHaveCount(0);
  check('snapshot tab, explicit creation, link to experiment and manual fold selection');
  await shot('experiment');

  await page.goto(base + '/#models?tab=compare&model=efficientnet_b0');
  await page.getByRole('heading', {name: '模型評估比較'}).waitFor();
  const reports = await get('/reports-query?model=efficientnet_b0');
  expect(reports.total).toBe(2);
  await expect(page.getByRole('button', {name: /^efficientnet_b0 · .*／fold/})).toHaveCount(2);
  await expect(page.locator('main')).not.toContainText('OOF');
  const enlarge = page.getByRole('button', {name: '放大評估圖片 history_00', exact: true});
  await enlarge.click();
  const modal = page.getByRole('dialog', {name: '歷史評估圖片'});
  await expect(modal).toBeVisible();
  await expect(modal.getByRole('button', {name: '關閉／取消'})).toBeFocused();
  const img = modal.locator('img');
  await expect(img).toHaveAttribute('src', /\/reports\/[67]{32}\/images\/history_00$/);
  await expect.poll(() => img.evaluate(i => i.complete && i.naturalWidth)).toBeGreaterThan(0);
  const geometry = await img.evaluate(i => ({
    fit: getComputedStyle(i).objectFit,
    w: i.naturalWidth,
    h: i.naturalHeight,
  }));
  expect(geometry.fit).toBe('contain');
  expect(geometry.w / geometry.h).toBe(2);
  await page.keyboard.press('Tab');
  expect(await modal.evaluate(d => d.contains(document.activeElement))).toBe(true);
  await page.keyboard.press('Escape');
  await expect(modal).toHaveCount(0);
  await expect(enlarge).toBeFocused();
  await page.reload();
  await expect(page).toHaveURL(/image=history_00/);
  await page.getByText('同一張圖片的模型結果', {exact: true}).waitFor();
  check('repeated reports kept, historical thumbnails, modal keyboard and URL selection');
  await shot('comparison');
  await page.getByRole('button', {name: '下一頁', exact: true}).last().click();
  await expect(page.getByRole('button', {name: /^放大評估圖片 /})).toHaveCount(4);
  await page.getByText('此報告保存的圖片不存在；未使用目前圖片替代。', {exact: true}).waitFor();
  check('sample pagination and missing historical image with no manifest fallback');
  await page.goto(base + '/#models?tab=compare&model=removed_model');
  await page.getByText('此模型沒有符合條件的評估報告。', {exact: true}).waitFor();
  await page.reload();
  await expect(page.getByLabel('模型方案篩選')).toHaveValue('removed_model');
  await expect(page.getByLabel('模型方案篩選').locator('option:checked')).toHaveText('removed_model（已移除的舊模型）');
  await page.goBack();
  await expect(page.getByLabel('模型方案篩選')).toHaveValue('efficientnet_b0');
  check('empty exact filter, removed model label, refresh and browser back');
  await page.route('**/api/v1/reports-query?*', async r => {
    if (new URL(r.request().url()).searchParams.get('model') === 'efficientnet_b0')
      await new Promise(resolve => setTimeout(resolve, 500));
    await r.continue().catch(() => {});
  });
  await page.getByLabel('模型方案篩選').selectOption('dinov2_small');
  await expect(page.getByRole('button', {name: /^dinov2_small · .*／fold/})).toHaveCount(1);
  await page.waitForTimeout(700);
  await expect(page.getByRole('button', {name: /^efficientnet_b0 · .*／fold/})).toHaveCount(0);
  await page.unroute('**/api/v1/reports-query?*');
  check('model switch rejects stale report response');

  await page.goto(base + '/#models?tab=jobs&job=' + '1'.repeat(32));
  const detailPanel = page.locator('.jobs-layout > section').nth(1);
  await detailPanel.getByRole('button', {name: '移至垃圾桶', exact: true}).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  const toast = page.locator('.toast').filter({hasText: '已移至垃圾桶 1 項'});
  await toast.waitFor();
  await expect.poll(async () => (await get('/jobs')).some(j => j.id === '1'.repeat(32))).toBe(false);
  await toast.getByRole('button', {name: '復原', exact: true}).click();
  await page.locator('.toast').filter({hasText: '已還原 1 項'}).waitFor();
  await expect.poll(async () => (await get('/jobs')).some(j => j.id === '1'.repeat(32))).toBe(true);
  check('one-click move without a preview dialog, undo from the toast');
  const bulk = page.locator('.selection-bar').getByRole('button', {name: '移至垃圾桶', exact: true});
  await expect(bulk).toBeDisabled();
  const jobTotal = (await get('/jobs-query')).total;
  await page.getByRole('checkbox', {name: '選取全部符合條件的工作', exact: true}).click();
  await expect(page.locator('.selection-bar')).toContainText('已選取 ' + jobTotal + ' 筆（全部符合條件）');
  await page.getByRole('checkbox', {name: '選取全部符合條件的工作', exact: true}).click();
  await page.getByRole('checkbox', {name: '選取工作 ' + '1'.repeat(32), exact: true}).check();
  await expect(page.locator('.selection-bar')).toContainText('已選取 1 筆');
  check('job list checkbox and cross-page select all');
  await bulk.click();
  await page.locator('.toast').filter({hasText: '已移至垃圾桶 1 項'}).first().waitFor();
  await expect.poll(async () => (await get('/jobs')).some(j => j.id === '1'.repeat(32))).toBe(false);
  await page.goto(base + '/#trash?type=job');
  const row = page
    .locator('tbody tr')
    .filter({has: page.getByRole('checkbox', {name: '選取 ' + '1'.repeat(32), exact: true})});
  await expect(row).toHaveCount(1);
  await row.getByText('資源明細', {exact: true}).click();
  await expect(row).toContainText('欄位內容估計');
  await expect(page.locator('main pre')).toHaveCount(0);
  await shot('job-capacity');
  await page.reload();
  await expect(page.getByRole('combobox', {name: '類型', exact: true})).toHaveValue('job');
  await row.getByRole('button', {name: '還原', exact: true}).click();
  await page.getByRole('button', {name: '確認還原', exact: true}).click();
  await expect
    .poll(async () => (await get('/jobs')).some(j => j.id === '1'.repeat(32) && j.state === 'succeeded'))
    .toBe(true);
  check('job move/restore preserves ID, execution state, capacity and deep link');

  const terminal = (await get('/jobs-query?size=100')).items
    .filter(j => ['succeeded', 'failed', 'cancelled', 'interrupted'].includes(j.state) && j.id !== '1'.repeat(32))
    .slice(0, 3);
  expect(terminal.length).toBe(3);
  await page.goto(base + '/#models?tab=jobs');
  for (const j of terminal) await page.getByRole('checkbox', {name: '選取工作 ' + j.id, exact: true}).check();
  await page.locator('.selection-bar').getByRole('button', {name: '移至垃圾桶', exact: true}).click();
  await expect.poll(async () => (await get('/trash?type=job')).total).toBe(3);
  await page.keyboard.press('Escape');
  await page.goto(base + '/#trash?type=job');
  await page.getByRole('checkbox', {name: '選取全部符合條件的項目', exact: true}).check();
  await expect(page.locator('.selection-bar').first()).toContainText('已選取 3 筆（全部符合條件）');
  await page.locator('.selection-bar').first().getByRole('button', {name: '永久刪除', exact: true}).click();
  await expect(page.getByLabel('永久刪除確認文字')).toHaveCount(0);
  const purge = page.getByRole('button', {name: '永久刪除 3 項', exact: true});
  await purge.waitFor();
  await shot('purge-confirmation');
  await purge.click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await page.getByText(/永久刪除已完成：3 成功／0 失敗/).waitFor({timeout: 30000});
  await expect.poll(async () => (await get('/trash?type=job')).total).toBe(0);
  expect((await get('/jobs-query?size=100')).items.some(j => terminal.some(x => x.id === j.id))).toBe(false);
  check('trash select-all across pages, purge confirmed once without typing, runs in background and is announced');

  const artifact = (await get('/artifacts'))[0];
  await post('/artifacts/activate', {artifact: artifact.id, target: 'local', allow_unevaluated: true});
  await post('/artifacts/activate', {artifact: artifact.id, target: 'local', allow_unevaluated: true});
  await page.goto(base + '/#models?tab=registry');
  await page.getByRole('button', {name: '移至垃圾桶', exact: true}).click();
  await page
    .getByRole('dialog')
    .getByText(/本地模擬正在使用此模型/)
    .waitFor();
  await expect(page.getByRole('dialog').getByText(/這一批目前沒有任何變更/)).toBeVisible();
  await expect(page.getByRole('button', {name: /只移入其餘/})).toHaveCount(0);
  await close();
  await page.goto(base + '/#settings');
  await page.getByRole('button', {name: '預覽解除此引用', exact: true}).click();
  await page.getByRole('dialog').getByLabel('請輸入「解除回復引用」').fill('解除回復引用');
  await page.getByRole('button', {name: '確認解除', exact: true}).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  const chain = (await get('/references')).find(r => r.target === 'local');
  expect(chain.nodes.length).toBe(1);
  expect(chain.nodes[0].artifact).toBe(artifact.id);
  check('reference blockers and explicit historical release preserve current model');

  for (const [hash, ready] of [
    ['trash', '垃圾桶目前是空的。'],
    ['models?tab=compare&model=efficientnet_b0', '模型評估比較'],
    ['models?tab=snapshots', '建立資料快照'],
  ]) {
    await page.goto(base + '/#' + hash);
    await page.getByText(ready, {exact: true}).waitFor();
    for (const width of [1440, 820, 390]) {
      await page.setViewportSize({width, height: 950});
      expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1)).toBe(false);
    }
    await shot(
      hash.startsWith('trash') ? 'empty-narrow' : hash.includes('compare') ? 'comparison-narrow' : 'experiment-narrow'
    );
    check('responsive no overflow ' + hash);
  }
  await page.route('**/api/v1/trash?*', r => r.fulfill({status: 403, json: {detail: '隔離測試：權限不足'}}));
  await page.goto(base + '/#trash');
  await page.getByText('隔離測試：權限不足', {exact: true}).waitFor();
  await expect(page.getByRole('checkbox', {name: '選取當頁全部項目'})).toHaveCount(0);
  check('trash permission error with no stale rows');
  expect(errors).toEqual([]);
} catch (error) {
  await shot('failure');
  console.error(await page.locator('[role="alert"]').allTextContents());
  throw error;
} finally {
  fs.writeFileSync(new URL('trash-browser-results.json', out), JSON.stringify({checks, errors}, null, 2));
  await browser.close();
}
console.log(JSON.stringify({passed: checks.length, errors}));
