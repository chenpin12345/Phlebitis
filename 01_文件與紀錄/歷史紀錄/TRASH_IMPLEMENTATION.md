# 垃圾桶、安全刪除與可讀介面：實作與交接

更新：2026-10-02（Asia/Taipei）。本文件對應使用者核准的垃圾桶 PLAN。原始需求保存在 `TRASH_REQUIREMENTS.md`；較早的七項改善紀錄不是本輪驗收結果。

**交付狀態：本輪本機 PLAN 實作與約定的隔離驗收已完成。** 101 項 pytest、27 項既有瀏覽器檢查、14 項新增瀏覽器檢查、TypeScript 型別檢查與 Vite 建置均通過。外部／破壞性驗證的排除範圍列於文末，不以本輪測試宣稱臨床有效性或涵蓋所有硬體故障。

## 啟動與入口

在專案根目錄執行：

```powershell
.\.venv\Scripts\python.exe -m src workbench --port 8765
```

瀏覽器開啟 `http://127.0.0.1:8765`。程式有更新時，停止自己啟動的舊工作台後重新啟動；連接埠已占用可查看原服務或改為 8766。不要關閉未知程序。

啟動網頁不代表開始訓練。既有排程器仍會接續**先前已提交**的工作；本輪驗收服務停用排程器，沒有提交真實訓練。管理服務只在本機使用，LINE 公開服務沒有新增垃圾桶 API。

## 確認的問題與修改位置

| 原本問題 | 實作 |
|---|---|
| 工作資料列、檔案掃描與模型引用各自判定可用性，沒有共同刪除狀態 | `src/workbench/resources.py` 統一生命週期；`jobs.py`、`registry.py`、`simulation.py`、`api.py` 使用同一狀態 |
| `audit` 一般整數主鍵可能重用刪除後的最大 ID | `migrations.py` 以交易遷移成 AUTOINCREMENT，保留原 ID／時間／內容 |
| 工作冪等鍵隨資料列刪除而消失 | `deleted_job_keys` 保留原工作 ID、種類與要求指紋，重送不重新排隊 |
| 回歸基準直接掃描檔案，可能使用垃圾桶內工作 | 建立工作時固定 baseline，執行前再檢查；既有回歸報告仍保留 |
| `previous` 為多層回復鏈，切換目前版本仍可能引用舊版本 | `trash.py` 檢查完整鏈；設定頁提供獨立預覽／確認解除歷史節點 |
| 工作先標示終止才寫產物歸屬清單 | `worker.py` 改為先記錄產物，再公布終止狀態；活著的 worker 仍阻擋垃圾桶操作 |
| 刪除與其他程序可能競爭；重啟可能誤認其他服務正在執行的刪除 | 生命週期 OS 鎖、每項操作 OS lease、逐檔 journal；重啟只將失去 lease 的操作標為待檢查 |
| 評估圖片指向目前 manifest，而非當時保存的結果 | `report_views.py` 驗證報告成員，僅提供當次報告圖片；缺圖不備援到目前圖片 |
| 一般／進階介面直接顯示 JSON | `ui.tsx`、`readable.tsx`、`monitor.tsx`、`maintenance.tsx` 改為分組表格、歷程與技術明細；原始下載仍保留並遮罩 |

## 完成的使用流程

### 頁首、快照與可讀介面

- 頁首保留位置；自填操作者移至設定頁，繼續使用 localStorage 與 `X-Operator`，不宣稱登入驗證。
- 資料審查不再建立／查詢快照。建立實驗提供折數、種子、研究展示模式及「建立資料快照」。建立後刷新選項，保留目前選取，不自動送出訓練。
- 獨立測試資料仍禁止用於訓練；既有分組與快照完整性規則保留。
- OOF 表單、專用 API 與 aggregate 函式移除；fold、報告和指標公式保留。
- 審查歷程、實驗要求、工作技術資訊、曲線來源、模型產物、環境、稽核及模擬事件皆以用途分組呈現。文字日誌保留；JSON 匯入及明確下載保留。
- 醫院已確認可用圖片未新增「舊資料／人工審查未紀錄」標記；模型版本沒有更換。

### 評估比較

- 模型方案精確篩選；同一 artifact 的多次評估依 report ID 分開。
- 報告、圖片、模型與頁碼保存在 hash URL；後端先篩選再分頁，過期請求不能覆蓋目前選取。
- 歷史縮圖完整等比例顯示；放大視窗支援 Escape、Tab 限制及焦點返回。
- 青綠為預測框、金色為人工框；分類模型不宣稱提供病灶定位。
- 報告保留來源模型／工作狀態；刪除來源不刪歷史報告。授權撤回／到期仍可使影像不可存取。

### 垃圾桶

管理範圍只有工作、模型版本與操作稽核；不清除研究原圖、快照、案例、LINE Store、官方權重、程式、環境、金鑰或資料庫本體。

1. 一般頁選「移至垃圾桶」，核對後端預覽後確認。軟刪除不移動檔案、不釋放空間。
2. 垃圾桶以類型、名稱／摘要／ID、臺北日期、操作者及容量排序查詢，預設 30 筆。當頁全選只選當頁；每批最多 100 個明確 ID。
3. 還原保留原 ID、工作結果與稽核時間；不重新執行、不自動啟用模型。缺檔或內容不符仍受阻。
4. 永久刪除必須重新預覽、輸入「永久刪除」。預覽有效 5 分鐘且綁定管理會話。有阻擋的批次整批拒絕，沒有 force 或默默跳過。
5. 已提交的操作可在「管理操作紀錄」查看，即使資源已不在垃圾桶仍能追溯。關閉頁面不取消操作。

## 資料遷移與相容性

`PRAGMA user_version=1`，首次使用前以 SQLite backup API 保存一致性備份：`runtime/workbench/backups/before-trash-v1.sqlite3`。沒有生命週期紀錄的舊資源視為正常，不批次改寫原始資料。

新增表：`resource_lifecycle`、`trash_previews`、`trash_operations`、`trash_steps`、`deleted_job_keys`。生命週期和工作 succeeded／failed 等狀態分開。所有 SQL INSERT 明確列欄位。

保留工作 request／experiment／effective 等追溯資料、已完成回歸結果，以及獨立保存的評估報告與圖片。模型刪除不連帶刪工作；工作刪除不連帶刪已登錄模型。稽核永久刪除也移除預覽／操作快取中的原事件內容，保留最小摘要與獨立管理事件。外部備份不在此清除範圍。

原工作、模型、稽核列表預設排除垃圾桶；排程器、reconcile 和到期處理使用內部完整查詢。歷史報告仍可讀；執行用途拒絕垃圾桶資源，已永久刪除的資源回應可辨識的 410。

## 容量口徑

| 欄位 | 意義 |
|---|---|
| 檔案資料容量 | 管理範圍內已確認檔案的邏輯 bytes |
| 獨占可清理容量 | 可證明歸屬、沒有共享／保護問題的核准候選檔案 |
| 預估可釋放容量 | 本次選取集合依實體身分去重後的可清理邏輯 bytes |
| 仍保留容量 | 歷史追溯、未知歸屬或不在核准刪除清單的內容 |
| 資料庫內容估計 | 欄位內容位元組估計，不是 SQLite 頁面或實際磁碟占用 |

未知、不完整、無法讀取和未計算不當成 0。背景計算保存時間，超過 30 分鐘標示過期；輪詢讀快取，重新計算需明確操作。授權清理後使相關快取失效。提交及逐檔刪除重新驗證，不依賴快取數字。

實際刪除結果只累計有完成紀錄的檔案數與邏輯 bytes。不測量整顆磁碟的差值，也不宣稱精確回收磁碟配置空間；SQLite 主要形成可重用空間，不執行 VACUUM。

## 安全邊界、恢復與限制

- 有活動依賴、目前模型、任何 previous 引用、待 reconcile 事件或未知共享關係時受阻。獨立複製的衍生模型保留歷史關係。
- 鎖順序為需要時先計算鎖，再生命週期鎖、專用鎖、SQLite 短交易；大型提交雜湊掃描在生命週期／SQLite 鎖外完成，再於鎖內短檢查預留資源。
- Windows 刪除以檔案 handle 驗證身分、大小、時間、雜湊與連結數；固定父目錄 handle 後使用 SetFileInformationByHandle 刪單檔。拒絕硬連結、符號連結、junction、reparse point、越界及內容遭替換的檔案。
- 不遞迴刪整個目錄。未知內容保留，空目錄可能留下；「完成」只代表核准範圍完成。
- 檔案刪除前保存 intent，成功後保存 removed。權限、占用、內容變動、磁碟錯誤或未知缺檔均保留診斷，不宣稱可跨檔案回滾。
- 重啟不自動繼續破壞性操作。待檢查／部分失敗在操作明細手動重試；只處理原清單未完成部分，不擴大範圍。
- 刪檔後、完成 journal 前中斷會形成無法判定的缺檔，維持受阻並要求人工檢查；不以檔案不存在就宣稱成功。
- 非 Windows 平台沒有此輪驗證的 handle 刪除實作，檔案清除明確拒絕；不降級成不安全的路徑刪除。
- 自填操作者不是授權來源；管理 API 沿用 localhost Host／Origin、CSRF 和管理會話邊界。LINE 公開應用不掛載管理 API。
- 垃圾桶不延長圖片授權期限，不阻擋既有撤回／到期規則；備份及 LINE 平台副本不宣稱同步刪除。

## API

所有路由位於 `/api/v1`。新增請求以 `{type: "job" | "model" | "audit", id: "..."}` 指定資源，後端不接受前端傳入刪除路徑／容量／依賴結論。

| 路由 | 用途 |
|---|---|
| GET `/trash`、`/trash/{type}/{id}` | 集合篩選、容量、生命週期與明細 |
| POST `/trash/previews`、GET `/trash/previews/{id}` | move／restore／purge 背景預覽，檔案清單分頁 |
| POST `/trash/operations` | preview ID、確認文字及 Idempotency-Key 提交 |
| GET `/trash/operations/{id}` | 真實結果、累計、逐檔分頁 |
| POST `/trash/operations/{id}/retry` | 原清單剩餘項目的明確重試 |
| GET `/trash/operation-history` | 持久操作列表，資源刪除後仍可查 |
| POST `/trash/capacity` | 明確選取集合的背景重算 |
| GET `/references`；POST `/references/{target}/preview`、`/references/commit` | 完整引用鏈及選定歷史節點解除 |
| GET `/reports-query`、`/reports/{id}/detail`、`/samples`、`/comparison/{image}` | 報告篩選、樣本分頁、選取驗證、相同成員比較 |

原報告與設定匯出仍可下載 JSON；設定和報告下載沿用敏感欄位遮罩。只有已移除的 OOF 專用 API 不再提供。

## 驗證證據

測試使用隔離 SQLite、合成圖片、假的小型權重與模擬 LINE client，沒有完整模型訓練、正式部署或真實訊息。瀏覽器服務固定 8877，停用工作排程器。

執行命令：

```powershell
.\.venv\Scripts\python.exe -m pytest -q --junitxml=docs/verification/pytest-trash.xml
npm.cmd --prefix .\web run build
.\.venv\Scripts\python.exe -X utf8 -c "import runpy; runpy.run_path('tests/workbench_fixture.py', run_name='__main__')"
node .\web\trash-regression.mjs
node .\web\workbench-regression.mjs
```

結果以本次最後的 XML／JSON 檔為準：

| 最終執行 | 結果 |
|---|---|
| 完整 pytest | 101 passed，39.10 秒；1 則既有 Starlette/httpx 棄用警告，無失敗 |
| TypeScript `tsc --noEmit` | 通過 |
| Vite production build | 通過，37 個模組 |
| Edge／Playwright 原有流程 | 27 項通過，0 JavaScript 頁面錯誤 |
| Edge／Playwright 新增流程 | 14 項通過，0 JavaScript 頁面錯誤 |
| 1440／820／390 像素布局 | 受測頁無整頁水平溢位；寬表格在容器內捲動 |
| 測試服務清理 | 8877 隔離服務已停止，沒有啟動訓練 worker |

新增垃圾桶測試包含同時重複提交 move／purge 後取得同一操作 ID，續訓來源也刪除後仍回報原請求工作已刪除，以及固定基準的回歸請求指紋比對。

- `verification/pytest-trash.xml`：完整後端測試。
- `verification/trash-browser-results.json`：新增流程 14 項；涵蓋移入／還原、型別確認永久刪除、引用解除、歷史圖片、焦點、分頁、錯誤、URL 與 1440／820／390 像素布局。
- `verification/browser-results.json`：原有 27 項；涵蓋真實查詢資料的總覽導覽、EXIF 座標、模型下載／設定匯出、曲線、審查與設定布局。
- `verification/trash-purge-confirmation.png`、`trash-job-capacity.png`、`trash-comparison.png`、`trash-comparison-narrow.png`、`trash-experiment.png`、`trash-empty-narrow.png`：隔離畫面；其中指標是合成測試資料，不是專案模型準確率。

原始程式基準保存在 `runtime/code_backups/trash-20260930-124026`。本輪未覆蓋無關研究資料，也未更換 YOLO 版本。

## 未納入此輪驗收

真實資料破壞性清除、完整 GPU 訓練、正式 LINE 手機傳送、正式部署、非 Windows 實體刪除，以及所有硬體層級斷電／儲存裝置故障均未執行。中斷、檔案占用／權限失敗、未知缺檔、重試及跨程序鎖以隔離測試驗證，不宣稱涵蓋所有外部故障。
