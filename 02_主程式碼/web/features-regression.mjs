import {fileURLToPath} from 'node:url';
// Batches 1–5 (2026-10-17). Only run against tests/workbench_fixture.py on 8877 (fake detector, no LINE).
import {chromium, expect} from '@playwright/test';
import fs from 'node:fs';
const base = 'http://127.0.0.1:8877',
  out = new URL('../../01_文件與紀錄/驗證報告/verification/', import.meta.url);
fs.mkdirSync(out, {recursive: true});
const browser = await chromium.launch({channel: 'msedge', headless: true});
const page = await browser.newPage({viewport: {width: 1440, height: 1000}}),
  checks = [],
  errors = [];
page.on('pageerror', e => errors.push(e.message));
const check = name => {
  checks.push({name, passed: true});
  console.log('PASS ' + name);
};
const shot = name => page.screenshot({path: fileURLToPath(new URL('features-' + name + '.png', out)), fullPage: true});
const get = async path => {
  const r = await page.request.get(base + '/api/v1' + path);
  expect(r.ok(), await r.text()).toBeTruthy();
  return r.json();
};
const session = await get('/session');
const post = async (path, body) => {
  const r = await page.request.post(base + '/api/v1' + path, {data: body, headers: {'X-CSRF-Token': session.csrf}});
  expect(r.ok(), await r.text()).toBeTruthy();
  return r.json();
};
const noOverflow = async () =>
  expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1)).toBe(false);
try {
  await page.goto(base + '/#settings');
  await page.getByLabel('操作者（自行填寫）', {exact: true}).fill('功能驗收');

  // D2 + overview count fix
  await page.goto(base + '/#overview');
  const steps = page.getByRole('region', {name: '下一步'});
  await steps.getByText(/\d+ 張照片待分類/).waitFor();
  const overview = await get('/overview');
  for (const area of ['cls']) {
    const a = overview.areas[area];
    expect(Object.values(a.confirmed_labels).reduce((x, y) => x + y, 0)).toBe(a.progress.confirmed);
  }
  await expect(page.getByRole('columnheader', {name: '已完成內容'})).toBeVisible();
  await expect(page.locator('.area-overview')).not.toContainText('未處理');
  await steps.getByRole('link', {name: '開始分類'}).click();
  await expect(page).toHaveURL(/#data\?area=cls&view=pending/);
  check('overview next steps and finished-only content counts');
  await page.goto(base + '/#overview');
  await shot('overview');

  // D4 global search with the / shortcut
  await page.locator('main').click();
  await page.keyboard.press('/');
  const search = page.getByRole('combobox', {name: '搜尋照片、工作、模型與快照'});
  await expect(search).toBeFocused();
  await search.fill('p_mismatch');
  const results = page.getByRole('listbox', {name: '搜尋結果'});
  await results.getByRole('option', {name: /p_mismatch/}).waitFor();
  await shot('search');
  await search.press('Enter');
  await expect(page).toHaveURL(/#data\?.*image=p_mismatch/);
  check('global search, keyboard shortcut and navigation');

  // D3 notifications
  const bell = page.getByRole('button', {name: /^通知/});
  await bell.click();
  const panel = page.getByRole('region', {name: '通知'});
  await expect(panel).toBeVisible();
  await bell.click();
  await expect(panel).toHaveCount(0);
  check('notification bell opens and closes');

  // D1 backup, D5 disk usage, preferences
  await page.goto(base + '/#settings?section=backup');
  const backup = page.locator('#section-backup');
  await backup.getByRole('button', {name: '立即備份'}).click();
  await expect(backup.locator('tbody tr').first()).toContainText('手動');
  await backup.getByRole('button', {name: '還原…'}).first().click();
  const restore = page.getByRole('dialog', {name: '從備份還原'});
  await expect(restore).toContainText('還原前會先自動備份目前狀態');
  await restore.getByRole('button', {name: '關閉／取消'}).click();
  check('backup now and restore confirmation dialog');
  const disk = page.locator('#section-disk');
  await disk.getByText('照片與標註').waitFor();
  await disk.getByText('可清理的舊輸出').waitFor();
  const failedJob = disk.getByRole('checkbox', {name: /^選取 efficientnet_b0/});
  await failedJob.first().check();
  await disk.getByRole('button', {name: '移至垃圾桶', exact: true}).click();
  await page.getByText(/已移至垃圾桶 1 項/).waitFor();
  check('disk usage lists old outputs and cleaning goes to the trash');
  await expect(page.getByRole('heading', {name: '上線門檻設定'})).toHaveCount(0);
  for (const t of ['通知設定', '抽查設定'])
    await expect(page.getByRole('heading', {name: t, exact: true})).toBeVisible();
  await page.getByLabel(/開啟抽查/).click();
  await expect.poll(async () => (await get('/settings/workbench')).spot_check.enabled).toBe(true);
  const ratio = page.getByLabel('抽查比例（%）');
  await ratio.fill('10');
  await ratio.press('Enter');
  await expect.poll(async () => (await get('/settings/workbench')).spot_check.ratio).toBe(0.1);
  check('preferences saved');
  await shot('settings');

  // A6 / A3 flags and marks
  await page.goto(base + '/#data?area=cls&view=all');
  const pills = page.getByRole('group', {name: '需要確認的照片'});
  await pills.getByRole('button', {name: /疑似重複/}).waitFor({timeout: 60000});
  await pills.getByRole('button', {name: /品質待確認/}).click();
  await expect(page).toHaveURL(/flag=quality/);
  await expect(page.locator('.thumb .mark-q').first()).toBeVisible();
  await pills.getByRole('button', {name: /疑似重複/}).click();
  await expect(page).toHaveURL(/flag=duplicate/);
  await page.locator('.thumb').first().click();
  const pair = page.locator('.duplicate-pair').first();
  await pair.waitFor();
  expect(await page.locator('.duplicate-pair').count()).toBeLessThanOrEqual(3);
  const before = (await get('/flags/summary')).duplicate_pairs;
  await pair.getByRole('button', {name: '不是重複'}).click();
  await expect.poll(async () => (await get('/flags/summary')).duplicate_pairs).toBe(before - 1);
  check('quality and duplicate filters, marks and a human duplicate decision');
  await shot('flags');

  // A2 shortcuts (classification)
  await page.goto(base + '/#data?area=cls&view=all&image=p_003');
  await page.getByRole('radiogroup', {name: '分類標籤'}).waitFor();
  await page.locator('main h1').click();
  await page.keyboard.press('2');
  await expect(page.getByRole('radio', {name: /第一期/})).toHaveAttribute('aria-checked', 'true');
  await page.keyboard.press('?');
  const help = page.getByRole('dialog', {name: '快捷鍵'});
  await expect(help).toContainText('第二期');
  await help.getByRole('button', {name: '關閉／取消'}).click();
  check('classification shortcuts and help dialog');

  // A5 spot check (fixture has no rule-classified photos) and A4 button hidden without new photos
  await page.goto(base + '/#data?area=cls&view=pending');
  await expect(page.getByRole('button', {name: /岡山高醫新照片/})).toHaveCount(0);
  await page.getByRole('button', {name: /抽查岡山高醫分期/}).click();
  const spot = page.getByRole('dialog', {name: '抽查岡山高醫自動分類'});
  await expect(spot).toContainText('目前沒有依檔名自動分類的照片');
  await spot.getByRole('button', {name: '關閉／取消'}).click();
  check('spot check dialog and hidden new-photo button');
  await page.evaluate(() =>
    document.querySelectorAll('.thumb').forEach(card => {
      card.querySelector('b').textContent = '7ae1c8fd19617279';
      card.querySelectorAll('.card-meta > span').forEach(chip => (chip.textContent = '陽性・分期未知'));
    })
  );
  const overlaps = await page.evaluate(() => {
    const boxes = [...document.querySelectorAll('.thumb')].map(card => card.getBoundingClientRect());
    return boxes.filter((box, i) =>
      boxes.some(
        (other, j) => j > i && other.top < box.bottom - 1 && other.left < box.right - 1 && box.left < other.right - 1
      )
    ).length;
  });
  expect(overlaps).toBe(0);
  check('photo cards with wrapped labels do not overlap');
  await page.goto(base + '/#data?area=cls&view=pending');
  await page.reload();
  await page.getByRole('button', {name: '刪除照片'}).click();
  await page.locator('.thumb').first().click();
  await expect(page.getByText('已選 1 張')).toBeVisible();
  await page.getByRole('button', {name: '移到垃圾桶…'}).click();
  const removal = page.getByRole('dialog', {name: '刪除照片'});
  await expect(removal).toContainText('受影響的快照');
  await removal.getByRole('button', {name: '移到垃圾桶'}).click();
  await expect(removal).toHaveCount(0);
  await page.goto(base + '/#trash');
  await expect(page.getByRole('heading', {name: /^資料照片/})).toBeVisible();
  await page.getByRole('checkbox', {name: '全選資料照片'}).click();
  await expect(page.getByRole('checkbox', {name: /^選取 /}).first()).toBeChecked();
  await page
    .locator('section', {has: page.getByRole('heading', {name: /^資料照片/})})
    .getByRole('button', {name: '還原', exact: true})
    .click();
  await expect(page.getByRole('heading', {name: /^資料照片/})).toHaveCount(0);
  check('photo moved to the trash with an impact preview and restored');

  // M2.5 data trust page
  await page.goto(base + '/#trust');
  await page.getByRole('button', {name: '重新檢查'}).click();
  await expect(page.getByRole('heading', {name: '來源與類別'})).toBeVisible();
  await expect(page.getByRole('heading', {name: '照片尺寸與類別'})).toBeVisible();
  await noOverflow();
  await page.getByRole('button', {name: '資料盤點', exact: true}).click();
  await expect(page.getByRole('heading', {name: '資料盤點'})).toBeVisible();
  await expect(page.getByRole('rowheader', {name: '病人 01'})).toBeVisible();
  await expect(page.getByRole('button', {name: '醫師核准', exact: true})).toHaveCount(0);
  check('data trust page: source check and inventory');
  const dataCard = await (await page.request.get(base + '/api/v1/data-card.md')).text();
  expect(dataCard).toContain('兩位醫師核准');
  expect(dataCard).not.toMatch(/\.jpg/);
  await page.getByRole('button', {name: '前瞻名單', exact: true}).click();
  await page.getByLabel('名單名稱').fill('新病人測試組');
  await page.getByLabel('病歷號（一行一位）').fill('ZZ90\nZZ91');
  await page.getByRole('button', {name: '封存名單'}).click();
  const sealed = page.getByRole('row', {name: /新病人測試組/});
  await expect(sealed).toContainText('2 位');
  await sealed.getByRole('button', {name: '解鎖'}).click();
  await sealed.getByRole('button', {name: /確認解鎖/}).click();
  await expect(sealed).toContainText('已解鎖');
  check('prospective list is sealed and unlocked once; data card has no filenames');

  // B1, B2, B3, B7, B8, C2 (C1 removed)
  await page.goto(base + '/#models?tab=new');
  await expect(page.getByLabel(/全部折都執行/)).toBeChecked();
  check('three-fold option on by default');
  const hold = page.getByLabel(/流程煙霧測試/);
  await expect(hold).not.toBeChecked();
  await hold.check();
  await expect(page.locator('.callout').filter({hasText: '並做一次流程煙霧測試'})).toBeVisible();
  await hold.uncheck();
  await expect(page.locator('.callout').filter({hasText: '並做一次流程煙霧測試'})).toHaveCount(0);
  check('independent test set checkbox (B5), off by default');
  const a = await post('/snapshots', {folds: 3, seed: 42, demo: true, task: 'binary_classification', name: '差異甲'});
  const b = await post('/snapshots', {folds: 3, seed: 7, demo: true, task: 'binary_classification', name: '差異乙'});
  await page.goto(base + '/#models?tab=snapshots');
  await page.reload();
  await page.getByLabel('與其他快照比較 ' + b.version).selectOption(a.version);
  const diff = page.getByRole('dialog', {name: '快照差異'});
  await expect(diff).toContainText('相同');
  await shot('snapshot-diff');
  await diff.getByRole('button', {name: '關閉／取消'}).click();
  check('snapshot difference dialog');
  await page.goto(base + '/#models?tab=compare&model=efficientnet_b0');
  await page.getByText('① 摘要').waitFor();
  await page.getByText(/③ 錯誤分析圖庫/).waitFor();
  await expect(page.getByText('沒有判斷錯誤的照片。')).toBeVisible();
  await expect(page.locator('.ci-table')).toContainText('平衡準確率');
  await page.getByRole('radio', {name: '交叉驗證彙總'}).click();
  await page.getByText(/還沒有交叉驗證的結果/).waitFor();
  check('report summary, error gallery and cross-validation list');
  // M3.5 comparison: a model and a baseline side by side (results are mocked; no training in tests)
  const metric = (key, value, ci) => ({key, name: key, value, ci, method: 'patient_bootstrap'});
  const groupOf = (id, model, baseline, sens, fpr) => ({
    cv_group: id,
    model,
    baseline,
    task: 'binary_classification',
    snapshot: 'verified_binary_x',
    expected_folds: 15,
    name: null,
    complete: true,
    fold_count: 15,
    repeats: 5,
    key_metric: 'balanced_accuracy',
    mean: 0.71,
    sd: 0.05,
    ledger: {settings: 4, runs: 60, results: 60, intact: true},
    evaluated_at: '20261107T000000000000Z',
    folds: [],
    pooled: {
      n: 160,
      photos: 32,
      patients: 8,
      metrics: [
        metric('balanced_accuracy', 0.71, [0.5, 0.9]),
        metric('sensitivity', sens, [0.7, 1]),
        metric('false_positive_rate', fpr, [0.1, 0.8]),
      ],
      lines: [],
      cautions: [],
      matrix: {kind: 'binary', tp: 10, fn: 2, fp: 3, tn: 5},
      calibration: {brier: 0.2, n: 160, bins: [{low: 0.6, high: 0.8, n: 80, score: 0.7, observed: 0.6}]},
      method: 'x',
    },
  });
  await page.route('**/api/v1/report-groups?*', route =>
    route.fulfill({
      json: {
        items: [
          groupOf('a'.repeat(16), 'efficientnet_b0', false, 0.92, 0.4),
          groupOf('b'.repeat(16), 'baseline_colour', true, 0.9, 0.7),
        ],
      },
    })
  );
  await page.reload();
  await page.getByRole('radio', {name: '交叉驗證彙總'}).click();
  await expect(page.getByRole('columnheader', {name: /正常誤報率/})).toBeVisible();
  await expect(page.getByText(/基線 · /)).toBeVisible();
  await expect(page.getByText('8 位／32 張').first()).toBeVisible();
  await expect(page.getByText(/這個快照已試 4 種設定/)).toBeVisible();
  await expect(page.getByRole('img', {name: '可靠度圖'})).toBeVisible();
  await page.setViewportSize({width: 390, height: 900});
  await noOverflow();
  await page.setViewportSize({width: 1440, height: 1000});
  await page.unroute('**/api/v1/report-groups?*');
  check('model and baseline comparison with patients, ledger count and calibration; no overflow at 390px');
  await shot('report');
  await page.goto(base + '/#models?tab=registry');
  const card = page.locator('.model-card-body').first();
  await card.getByText('使用狀態', {exact: true}).waitFor();
  for (const s of ['用途與限制', '訓練資料', '訓練設定'])
    await expect(card.locator('details > summary', {hasText: s})).toBeVisible();
  await expect(card.getByText('研究原型，不可作為臨床診斷。')).toBeHidden();
  await card.locator('summary', {hasText: '用途與限制'}).click();
  await expect(card.getByText('研究原型，不可作為臨床診斷。')).toBeVisible();
  check('model card folds long sections');
  await expect(page.getByRole('heading', {name: /^模型說明卡/}).first()).toBeVisible();
  await expect(page.getByRole('button', {name: '啟用至 LINE…'})).toHaveCount(0);
  await expect(page.getByRole('button', {name: '用於 LINE', exact: true}).first()).toBeVisible();
  const cardLink = await page.getByRole('link', {name: '匯出模型卡'}).first().getAttribute('href');
  const cardText = await (await page.request.get(base + cardLink)).text();
  expect(cardText).toContain('# 模型卡');
  expect(cardText).toContain('兩位醫師核准');
  expect(cardText).not.toMatch(/_(LH|RH|LL|RL)_\d/);
  check('model card without release checklist (C1 removed)');
  await page.getByRole('button', {name: '設為影子模型'}).first().click();
  await page.getByRole('heading', {name: '影子模式', exact: true}).waitFor();
  await page.getByRole('button', {name: '停止影子模式'}).first().click();
  await expect(page.getByRole('button', {name: '設為影子模型'}).first()).toBeVisible();
  check('shadow mode toggle');

  // C3 usage statistics
  await page.goto(base + '/#intake?tab=stats');
  await page.getByRole('heading', {name: '使用統計', exact: true}).waitFor();
  await page.getByRole('radio', {name: '7 天'}).click();
  await expect(page.locator('.usage-stats')).toContainText('完成分析');
  check('LINE usage statistics tab');
  await shot('usage');

  for (const hash of ['overview', 'data?area=cls&view=all', 'settings', 'models?tab=registry', 'intake?tab=stats']) {
    await page.goto(base + '/#' + hash);
    await page.locator('main h1').waitFor();
    for (const width of [1440, 820, 390]) {
      await page.setViewportSize({width, height: 950});
      await page.waitForTimeout(150);
      await noOverflow();
    }
    await page.setViewportSize({width: 1440, height: 1000});
    check('no horizontal overflow ' + hash);
  }
  expect(errors).toEqual([]);
} catch (error) {
  await shot('failure');
  console.error(await page.locator('[role="alert"]').allTextContents());
  throw error;
} finally {
  fs.writeFileSync(new URL('features-browser-results.json', out), JSON.stringify({checks, errors}, null, 2));
  await browser.close();
}
console.log(JSON.stringify({passed: checks.length, errors}));
