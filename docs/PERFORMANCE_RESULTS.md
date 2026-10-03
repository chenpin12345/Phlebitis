# 本輪實作與驗收結果

日期：2026-10-03（Asia/Taipei）。本報告區分程式碼證據、隔離測試與未驗證事項；不把合成資料或介面中的指標當成醫療模型準確率。

## 1. 根因與修改

**程式碼確認：**舊 `src/workbench/views.py` 的清單先全量 `audit()`／照片 SHA-256／逐圖審查歷程查找，再分頁；總覽也使用這條路徑。這解釋資料量增長時的讀取成本，但沒有重現使用者原本「一直載入」的完整現場，因此不能宣稱是該症狀唯一根因。

| 範圍 | 實作與位置 |
|---|---|
| 資料清單／總覽 | `queries/data_index.py`：背景完整性檢查、跨程序鎖、來源 revision 核對、SQLite 篩選計數分頁；GET 不全量讀原圖。總覽與清單於一致讀取交易使用相同定義。 |
| 模型／報告 | `queries/reports.py`、`queries/files.py`、`registry.py`：報告摘要與樣本索引、批次 metadata 讀取，模型清單不逐模型重掃全部報告。安全關鍵模型操作仍驗證來源。 |
| 工作／曲線 | `jobs.py`、`queries/curves.py`、`presentation.py`：活動工作 SQL、待 reconcile 事件、摘要分頁、按需有界日誌、背景歷史来源索引、增量曲線讀取。 |
| 請求 | `web/src/shared/query.ts`、`shared/ui.tsx`：enabled、同 GET 合併、取消與舊回應隔離、15 秒逾時、最多兩次暫時失敗重試、可見性及範圍失效；修改不自動重送。 |
| 圖片 | `queries/images.py`：320／1800 px EXIF 一致轉換、伺服器衍生快取、每程序併發限制、同 key 合併、1 GiB LRU；每次存取仍檢查来源限制，瀏覽器 no-store。 |
| 匯入 | `src/imports/service.py`、`routes/imports.py`、`src/__main__.py`、`features/imports/ImportPanel.tsx`：同一服務提供 inbox、網頁與 CLI，預覽／分頁／冪等／收據／中斷恢復。 |
| 程式整理 | `main.tsx` 僅啟動；`app` 管路由版面，`shared` 管共同能力，`features` 分功能；舊平面入口保留相容匯出。正式資料根目錄不搬動。 |

**量測確認：**以下同機、同合成資料前後比較顯示資料清單與主要頁面改善。部分本來很小的 API 耗時增加，並未一律變快。

## 2. 量測方法與限制

- Windows 11、Python 3.12.10、16 個邏輯處理器；瀏覽器為本機 Edge／Playwright、1440×1050。未控制作業系統檔案快取，不稱為冷磁碟測試。
- 網路 API：同一套 42 張合成圖片 fixture，每個端點 50 次，量測包含 HTTP 回應與讀取 body；前後服務分別為保存的舊程式與現行程式。
- 頁面：每條路徑 20 次，進入前先離開至 about:blank，避免同 URL 導覽無動作造成虛假的極低數字。資料頁等待首張縮圖控制項；其他頁等待 networkidle，含 500 ms 安靜時間，不能與純可操作時間混為一談。
- 初始頁面請求／bytes 只計該量測視窗，不含稍後捲動才載入的圖片。重返／分類／翻頁另以固定 500 ms 視窗記錄請求、取消、失敗及重複。
- 擴大規模使用 91／910 張小型合成圖片、54／495 筆工作、18／153 份報告，不能代表 177 MiB 真實原圖的影像解碼或首次驗證成本。
- p95 使用 nearest-rank；API 50 次、頁面 20 次只代表本輪短期樣本，不代表長期線上 SLA。
- 舊 `before-clean`／`after-clean` 的頁面結果含同 URL 無動作問題，**不採用**。本報告只採 `before-final`／`after-final` 與最終 navigation、scale 結果。

### HTTP API（毫秒；各 n=50）

| API | 修改前 median / p95 | 修改後 median / p95 | 回應 bytes 前 → 後 |
|---|---:|---:|---:|
| `/overview` | 202.2 / 234.6 | 31.4 / 41.5 | 1856 → 1366 |
| `/data-query` | 173.2 / 202.7 | 16.6 / 27.5 | 15315 → 15626 |
| `/data-query?view=approved` | 170.6 / 197.1 | 18.9 / 28.1 | 3317 → 3628 |
| `/models` | 47.8 / 51.2 | 50.9 / 65.4 | 1884 → 1884 |
| `/artifacts` | 17.5 / 20.7 | 30.8 / 39.5 | 7679 → 3225 |
| `/jobs` | 27.9 / 31.2 | 14.0 / 24.1 | 1648 → 1648 |
| `/reports-query` | 21.1 / 23.1 | 31.4 / 44.1 | 3798 → 3798 |
| `/curve-sources` | 38.9 / 42.3 | 16.4 / 21.4 | 549 → 549 |
| `/cases` | 8.6 / 10.3 | 9.9 / 15.9 | 2 → 2 |
| `/audit-query` | 11.6 / 12.9 | 13.3 / 18.2 | 5557 → 5557 |
| `/trash` | 9.4 / 10.5 | 11.2 / 16.7 | 67 → 67 |

上述 `/jobs`、`/cases` 為保留相容性的舊端點；新版前端使用分頁摘要端點。部分小型端點增加 SQLite／生命週期查詢成本，但本次各清單 p95 均低於 500 ms。報告、模型清單尚有目錄 stat 掃描，不能宣稱成本與規模完全無關。

### 頁面（毫秒；各 n=20）

| 頁面 | 前 median / p95 | 後 median / p95 | 初始請求中位數 前 → 後 | bytes 中位數 前 → 後 |
|---|---:|---:|---:|---:|
| 待人工審查 | 955.3 / 980.9 | 236.7 / 327.6 | 33 → 8 | 43630 → 21218 |
| 可用資料 | 958.1 / 979.4 | 187.2 / 245.4 | 9 → 8 | 9332 → 9498 |
| 模型目錄 | 868.3 / 896.4 | 714.6 / 745.4 | 6 → 2 | 13169 → 1984 |
| 工作監測 | 879.6 / 913.0 | 680.6 / 695.5 | 6 → 2 | 13169 → 1003 |
| 評估比較 | 965.2 / 1008.5 | 808.5 / 852.6 | 14 → 8 | 21198 → 8288 |
| 模型版本 | 897.9 / 927.7 | 701.1 / 724.9 | 6 → 3 | 13169 → 3327 |
| 訓練曲線 | 903.4 / 930.9 | 678.8 / 687.9 | 7 → 2 | 13718 → 649 |
| 設定與維護 | 912.0 / 2702.1 | 763.3 / 893.2 | 7 → 6 | 8174 → 6318 |
| 垃圾桶 | 842.1 / 865.6 | 688.9 / 712.4 | 4 → 3 | 2023 → 167 |
| 案例與回歸 | 861.0 / 977.1 | 721.9 / 753.1 | 5 → 4 | 9639 → 3383 |
| LINE 模擬 | 1028.5 / 1063.7 | 727.9 / 789.9 | 5 → 4 | 11493 → 4749 |
| 總覽 | 820.1 / 864.6 | 696.1 / 751.5 | 2 → 2 | 1956 → 1466 |

修改後這批頁面量測沒有 pageerror 或 requestfailed。舊版工作監測與模型版本各有 20 個 requestfailed；舊工具未細分原因，因此不將它們全說成伺服器失敗。資料審查本輪達到主要內容約 2 秒內可操作的初始目標。

### 重返、分類與分頁（毫秒；各 n=20）

| 流程 | 可操作前 median / p95 | 可操作後 median / p95 | 首圖後 median / p95 | 請求中位數前 → 後 |
|---|---:|---:|---:|---:|
| 重返資料審查 | 284.5 / 299.0 | 145.4 / 165.3 | 201.6 / 235.9 | 31 → 31 |
| 切換分類 | 296.2 / 315.8 | 144.7 / 180.8 | 209.8 / 254.7 | 7 → 7 |
| 翻頁 | 263.2 / 296.1 | 138.8 / 148.4 | 193.5 / 204.5 | 6 → 6 |

上述三種正常流程的重複、失敗、取消請求均為 0；另外的快速切換／取消測試才會刻意製造取消。

### 擴大規模（TestClient／函式，非 HTTP 網路量測；各 n=50）

| 規模 | 舊清單函式 median / p95 ms | 索引函式 median / p95 ms | 清單 API median / p95 ms |
|---|---:|---:|---:|
| 91 圖／80138 bytes／54 工作／18 報告 | 348.89 / 378.95 | 2.83 / 3.63 | 6.20 / 8.12 |
| 910 圖／284300 bytes／495 工作／153 報告 | 1061.52 / 1245.08 | 2.88 / 3.93 | 4.98 / 6.47 |

| API | 91 圖 p95 ms | 910 圖 p95 ms |
|---|---:|---:|
| `/overview` | 19.83 | 16.36 |
| `/jobs-query` | 5.79 | 6.63 |
| `/reports-query` | 28.33 | 50.73 |
| `/artifacts` | 21.03 | 66.46 |
| `/curve-sources` | 11.19 | 16.14 |
| `/cases-query` | 3.60 | 4.04 |
| `/audit-query` | 9.82 | 4.07 |
| `/trash` | 8.17 | 3.38 |

`EXPLAIN QUERY PLAN` 確認分類使用 `data_classification(status,eligible,id)`，活動工作使用 `jobs_state_created`。原始結果另存 first_ms、bytes、查詢計畫。

### 首次程序啟動（各 n=1）

包含隔離 fixture 建立、套件 import 與服務啟動；作業系統檔案快取未清空，不是磁碟冷啟動。單次樣本不能推論長期分布。

| 版本 | 程序到 session 可用 ms | 首頁資料清單可見 ms | 首圖可見 ms |
|---|---:|---:|---:|
| before | 1123.0 | 439.3 | 460.2 |
| after | 1302.9 | 254.0 | 283.9 |

原始結果：`runtime/performance/startup-results.json`；重現工具：`web/startup-performance.mjs`。測試工具初版的連線判斷及 Windows 子程序清理已修正，未使用失敗執行的數字。

### 伺服器階段

以下取修改後 `/data-query` 的 Server-Timing；階段可巢狀重疊，不可加總為總耗時。

| 階段 | n | median / p95 ms |
|---|---:|---:|
| total | 50 | 12.83 / 20.27 |
| db_connect | 50 | 0.76 / 1.31 |
| sql | 50 | 4.17 / 8.70 |
| stat_scan | 50 | 0.75 / 1.54 |
| data_query | 50 | 9.61 / 17.30 |

暖清單沒有 hash／圖片轉換／資料鎖等待項目，因為這些操作不在該讀取路徑。原圖雜湊、圖片處理及鎖等待已加量測點；未觸發的階段不虛構成測量值 0。舊版沒有完整分階段計時，不能補造修改前鎖等待數字。

## 3. 測試與畫面

| 驗證 | 結果 |
|---|---|
| pytest 全套 | **123 passed**，74.78 秒；1 個既有 Starlette/httpx 棄用警告，沒有失敗。 |
| TypeScript／Vite | `npm run build` 通過；JS `index-DkpOZlAa.js`，350.23 kB／gzip 110.47 kB。 |
| 工作台瀏覽器 | 27 項通過，包含審查、圖片／座標、導覽、設定、曲線、下載／匯出。 |
| 垃圾桶瀏覽器 | 14 項通過；移入、還原、永久刪除只用 fixture。 |
| 匯入瀏覽器 | 10 項通過；照片、拒絕損毀、模型不啟用、窄畫面、焦點、有限重試、15 秒逾時。 |
| 查詢生命週期 | 5 項通過；模擬 document visibility 事件、恢復補查、範圍失效、終態停止輪詢。這不是作業系統實際切到背景的測試。 |

瀏覽器合計 **56 項**。另外執行 12 種頁面各 20 次、3 種導覽各 20 次，以及 API／規模量測。已查看窄螢幕匯入及模型產物畫面；截圖中的資料與模型分數全是合成 fixture，不能當成真實醫療模型成果。

### 測試隔離修正與稽核紀錄

本輪最後比對發現兩項原有測試直接呼叫正式根目錄的 `create_app(testing=True)`；testing 旗標不代表隔離。它們在之前多次 pytest 中共新增 **16 筆 request_failed 稽核**，來源是 `/experiments` 與 `/experiments/batch` 的 422 驗證拒絕，並非新訓練。

已修正 `tests/test_workbench.py`、`tests/test_workbench_acceptance.py` 使用隔離 fixture，並保留這 16 筆紀錄，沒有偷偷清除。最後重跑全部 123 項時，正式 jobs 49、audit 154、cases 4 及 events／assets／flags／resource_lifecycle 均逐筆相同；原本的 138 筆稽核亦保留。

## 4. 資料、遷移及相容性

- SQLite v2 增加資料／檔案投影、匯入紀錄、reconcile 及查詢索引；v3 增加報告摘要與樣本表。兩者採版本判斷、跨程序鎖、交易、遷移前一致性備份。不是每次連線都重做 migration。
- manifest／審查／快照／模型／報告仍為各自權威來源；query index 可以重建，imports、垃圾桶及稽核日誌不可當快取丟棄。
- 保留旧 API；新增摘要、分頁、按需日誌與匯入 API。操作沿用 Host／Origin／CSRF，不掛載於 LINE 公開服務。
- 圖片、資料快照、模型版本、references、dataset.yaml、runs 與 archive 不作整批路徑遷移。未修改 YOLO 版本或醫院可用圖片的呈現語意。
- 新照片預設待人工審查、未知標籤；模型只接受服務端可核對來源，未知格式不反序列化。匯入不自動建立實驗、訓練、評估或切換引用。

操作與目錄責任、照片／模型包格式、CLI、重試及索引重建見 [PERFORMANCE_IMPORTS.md](PERFORMANCE_IMPORTS.md)。

## 5. 限制與尚未驗證

1. 未重現使用者原先永久停在 loading 的現場；已移除可證實的全量讀取瓶頸，並驗證逾時、失敗、取消與重試，但不把推測寫成根因。
2. 真實 91 張／約 177 MiB 資料只保留先前函式量測作背景；本輪完整 API／瀏覽器前後比較使用合成資料，沒有宣稱真實資料的冷啟動或 p95 達標。
3. 未下載或載入真實新模型、未跑 GPU 訓練或官方 LINE。官方來源下載使用模擬 client 驗證；離線缺乏可信來源會拒絕，不能藉副檔名通過。
4. stat 無法即時發現刻意保留中繼資料的外部改檔；每天內容檢查及關鍵操作完整驗證仍保留。大模型／大量原圖首次檢查會花時間。
5. 報告清單仍需檔案 stat；照片提交前的重核與既有目的檔衝突檢查可能持有資料寫入鎖。一般索引 GET 不等待這個鎖，但極大匯入的寫入延遲尚未量測。
6. 瀏覽器可見性測試使用事件模擬，沒有完成所有瀏覽器、真實 Windows 休眠恢復、跨程序高併發與網路磁碟故障的壓力驗證。

本輪功能與列出的隔離驗證已交付；以上未驗證範圍不能計作「整份 plan 的所有情境均已 100% 驗證」。

## 6. 回復與證據

程式及 SQLite 基準：`runtime/code_backups/performance-imports-20261002-221129/`。停止服務後才回退程式；已有新匯入時不可用舊資料庫覆蓋正式內容與收據。索引及圖片快取可重建，研究資料與操作歷史不可刪除來回復。

原始證據：

- `runtime/performance-final-pytest.xml`
- `runtime/performance/final-test-production-guard.json`、`production-row-preservation.json`
- `runtime/performance/before-final.json`、`after-final.json`
- `runtime/performance/before-final-navigation.json`、`after-final-navigation.json`
- `runtime/performance/scaled-queries.json`
- `docs/verification/browser-results.json`、`trash-browser-results.json`
- `runtime/performance/import-browser-results.json`、`query-lifecycle-results.json`
- `runtime/performance/import-narrow.png`、`docs/verification/artifact-narrow.png`

重現工具：`scripts/benchmark_queries.py`、`web/performance-check.mjs`、`web/navigation-performance.mjs`、三個功能 regression 腳本及 `web/query-lifecycle-regression.mjs`。破壞性驗收不得改指向正式服務。

