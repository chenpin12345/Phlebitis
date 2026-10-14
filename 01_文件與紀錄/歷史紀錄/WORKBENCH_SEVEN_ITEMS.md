# 七項工作台改善：實作與驗收紀錄

日期：2026-09-29。範圍：使用者的七項修改需求與「可用資料為醫院已確認圖片，不標示舊資料／人工審查未紀錄」補充。

## 已完成的修改

| 項目 | 程式碼確認的根因／修改前 | 修改後與主要位置 |
|---|---|---|
| 1. 圖片及座標 | 主圖固定正方形 SVG、`preserveAspectRatio=none`，指標以整個容器計算；縮圖裁切。後端已處理 EXIF，部分 LabelMe 尺寸錯誤被靜默忽略。 | `web/src/review.tsx` 的共用 BoxEditor 使用真實預覽比例及 SVG 反矩陣，留白不可畫框；支援拖曳、移動、縮放、數值及方向鍵。`extras.tsx` 的案例編輯器共用。`api.py` 顯示座標問題；載入錯誤不提供可儲存的編輯器。 |
| 2. 已審查與篩選 | 原本只有三個儲存狀態，未區分目前有效的人工決定與訓練資格，UI 使用共用操作者。 | `views.py` 定義五種查詢視角與一致的資格；`review.tsx` 提供審查者、結果、臺北日期篩選；伺服器全資料篩選及分頁。操作者採自行填寫的研究代稱，明示未登入驗證。`dataset.py` 記錄有效決定、修訂與前後標註；補件／重開移出可用資料。 |
| 3. 訓練曲線 | 工作頁只有單一粗略曲線，缺值會補成零；尚無獨立曲線頁。 | `presentation.py` 讀取 YOLO CSV、分類 JSONL 和歷史圖片，處理非有限值、重複 epoch、部分寫入和超出範圍紀錄。`monitor.tsx` 顯示實際存在的指標、原始曲線、可關閉平滑線、數值表及已記錄的 checkpoint。DINO 不捏造 epoch；回歸測試不當數值回歸。 |
| 4. 工作監測 | 結果、要求／有效參數預設顯示 JSON；工作類型不易區分。 | 導覽更名「工作監測」，新增類型篩選、摘要、階段、按類型呈現的結果、設定值／實際值表、時間軸及日誌搜尋。缺少有效參數顯示未提供，未知類型保留欄位。原始紀錄需主動展開。 |
| 5. 設定、維護與稽核 | 套件、到期清單直接 JSON；稽核只取最近 200 筆，無後端完整篩選。 | `maintenance.tsx` 改表格／摘要與清理影響明細；`views.query_audit` 支援日期、操作者、操作、關聯 ID、真實結果、穩定排序與分頁。`storage.py` 新紀錄帶格式版本、身分來源及結果；`jobs.py` 明確記錄提交與完成等不同事件。 |
| 6. 總覽導覽 | 三張圖片卡片均為 `#data`；資料頁每次預設待審，頁面狀態無分類參數。 | `main.tsx` 使用 `#data?view=approved` 等穩定識別碼；分類及篩選由 hash URL 管理，明確入口清除殘留篩選。`ui.tsx` 取消舊請求並檢查請求序號，支援重新整理、上一頁／下一頁。已核對個案卡片維持個案語意。 |
| 7. 模型產物與設定 | 「產物與設定」直接展開整份 JSON。 | `ArtifactDetails` 提供版本摘要、登錄產物、實際可讀狀態／大小、設定表格、評估摘要及可控制的下載。分開要求值、實際值、目前推論設定；只有進階與明確匯出入口才提供原始設定。未新增設定直接修改功能。 |

共用基礎元件位於 `web/src/ui.tsx`，包括可讀欄位、缺值、進階檢視、分頁、操作者及可取消的查詢。沿用 React、FastAPI、SQLite、CSV 和 SVG，未新增框架、登入系統或模型版本。

## 真實資料唯讀核對

- 全部 91 張：可用 24、待人工審查 62、排除 5；總覽與查詢清單一致。
- 24 張醫院已確認圖片保持可用，未標示「舊資料／人工審查未紀錄」。個案分組是否核對仍遵守原本規則。
- 目前可追溯的有效人工通過／排除紀錄為 0，因此「已審查」目前為 0；6 筆 migration-audit 紀錄屬於技術處理，不冒充醫院審查。
- 已讀取 6 個登錄版本、15 個工作／歷史曲線來源。既有 `yolo11n_23eff4760fee46bd` 通過完整性檢查並在 CPU 載入單一 phlebitis 類別；未訓練、預測或評估病人照片。
- 證據：`verification/real-data-readonly.json`。唯讀檢查使用 `create_app(testing=True)`，不啟動排程器。

## 原始標註的既有問題與處理方式

13 張照片原始尺寸為 4032×3024，LabelMe 宣告 3024×4032，帶 EXIF 6。這證實尺寸不一致，但不能僅憑尺寸判定舊框是在哪個座標系繪製。因此未批次旋轉或重寫。

影響 ID：`1c93ec3f9dd23952`、`38a38819d08a1ab3`、`3a7c22eac0405d85`、`4d45089aa4b82972`、`7a21aef867e7e68a`、`874c58837ce24626`、`99a42dfba53ae32f`、`9d8776ef89eefb65`、`9fa99755cc7fb4b0`、`abe2af900b85ba30`、`d5b206933959f6db`、`dfa700627cf45953`、`e0606569ad61a3d7`。其中 10 張待審、3 張排除。

後續人工處理：查看正向預覽並對照原始 LabelMe，勾選已核對、重新標註，儲存後重載確認。API 要求明確的 `coordinate_resolution=redraw`，不可默默用空框覆蓋。新歷史保存前後座標內容（不複製 LabelMe 的 imageData）；原圖保留，既有來源檔及不可變快照維持追溯。若需恢復，依歷史的原始尺寸／座標重新提交審查，保留修訂鏈，不能直接修改已封存快照。

## 資料格式與 API 相容性

本次不批次遷移 manifest，不替舊紀錄補造人員、時間或結果。新增能力為加法：

- 審查 JSON 歷史 `schema_version=2` 增加 decision、source、coordinate_resolution、annotation_before／after。沿用既有交易備份、復原與 revision 衝突檢查。
- 新快照每個 member 增加 `review_revision`；沒有可追溯決定時為 null。舊快照不重寫。後續實質審查變更仍標記舊快照 superseded，不悄悄改動內容。
- SQLite 表格結構不變；新 audit.detail 增加 `_audit.schema_version=2`、identity、outcome。舊資料缺 outcome 顯示未知，local_operator 顯示未記錄；沒有登入驗證的宣稱。
- 審查 API 新增可選 decision／coordinate_resolution，原有 status 仍受驗證。一般舊呼叫仍可用；有已知座標問題的圖片需明確確認才能覆寫標註。
- 保留 `/data`、`/audit`、`/jobs`、`/artifacts` 既有回傳外型。新增 `/data-query`、`/audit-query`、`/curve-sources`、`/curve-history`、`/curve-image`、`/jobs/{id}/curves`。
- 模型新增 `/artifacts/{id}/detail`、`settings?key=`、`file?key=`、`export`。僅允許登錄在該版本的檔案、檢查路徑邊界與下載雜湊；設定內容一律套用敏感欄位遮罩，不讀取 `.env`。
- 新訓練保存真實 checkpoint 選用事件；舊實驗缺此紀錄顯示未記錄，不反推最佳 epoch。EfficientNet 的後續實驗會保存實際套用參數。
- 日期篩選採臺北日期的起日 00:00（含）至迄日次日 00:00（不含）；DB 時間仍是 UTC epoch。稽核排序為 at DESC、id DESC，分頁固定最大紀錄 ID。

## 已執行的驗證

### Python 與建置

```powershell
.\.venv\Scripts\python.exe -m pytest -q
npm.cmd --prefix .\web run build
.\.venv\Scripts\python.exe -m scripts.check_workbench_readonly
```

Python 回歸測試 **76 項全部通過**（26.37 秒），涵蓋既有功能及新增資料／API 契約。TypeScript `tsc --noEmit` 和 Vite 正式建置通過。只有既有 Starlette／httpx 棄用提醒，沒有測試失敗。

新增測試：`tests/test_workbench_views.py`。涵蓋審查狀態與 revision、跨頁篩選／未知人員、資料資格、讀寫競態、不可變快照、四種比例與 EXIF 儲存往返、13 張問題所代表的尺寸不符案例、非有限及重複指標、歷史圖片、稽核時區／同時刻排序／分頁、設定遮罩、下載、匯出和模型載入路徑。Checkpoint 事件使用輕量替身驗證保存規則，沒有完整訓練。

### 瀏覽器驗收

隔離伺服器只建立合成圖片、指標、模型檔案與 SQLite。沒有載入真實病人資料，不啟動訓練排程器，沒有呼叫清理操作。

終端機一：

```powershell
.\.venv\Scripts\python.exe -c "import runpy; runpy.run_path('tests/workbench_fixture.py', run_name='__main__')"
```

終端機二：

```powershell
node .\web\workbench-regression.mjs
```

使用本機 Edge／Playwright，27 項檢查通過、0 個前端 pageerror：

- 三張總覽卡片檢查實際 image IDs；殘留篩選、深連結、重新整理、上一頁／下一頁與舊請求競態。
- 四種比例、EXIF、留白拒絕畫框、拖曳／移動／縮放／儲存重載、鍵盤與圖片載入失敗。
- 已審查篩選、無符合條件結果。
- 產物一般展開沒有 JSON，設定表格、權重下載、明確原始設定匯出、進階主動展開。
- 偵測／分類／DINO／只有圖片的歷史曲線；模擬執行中的實驗定時更新，切換與離頁停止原輪詢。
- 工作失敗、缺實際參數、未知工作類型及日誌搜尋。
- 環境表格、沒有到期資料、稽核篩選與分頁重設。
- 1440、820、390 寬度及資料／模型產物／設定／曲線頁無整頁水平溢位，403 不顯示過期資料。

結果檔：`verification/browser-results.json`。畫面已實際開圖檢視：`review-desktop.png`、`review-390.png`、`artifact-readable.png`、`artifact-narrow.png`、`curves.png`；其餘畫面同在 verification 目錄。截圖內容全部為測試資料，不是醫院模型效能。

## 未執行及適用範圍

- 依要求未執行昂貴的完整訓練、正式部署、真實資料清除、LINE 手機傳送或模型版本替換。
- 本次驗證包括一個既有 YOLO11n 真實權重載入；沒有逐一重新訓練／載入全部五種方案。長時間 GPU 訓練及續訓仍需在實際訓練時觀察。
- 13 張既有標註問題已識別並提供可追溯修正流程；病灶位置仍須人工逐張核對，不以工程修復代替醫院標註。
- 醫院照片、個案分組與臨床可靠性不是此次 UI 測試可驗證的項目。

## 啟動更新版本

若舊服務仍執行，先在它的終端機按 Ctrl+C，再重新啟動：

```powershell
.\.venv\Scripts\python.exe -m src workbench --port 8765
```

開啟 http://127.0.0.1:8765 後重新整理頁面。若該 port 已有其他服務，可改 8766。前端已建置，不必每日重新安裝依賴。

修改前的原始碼備份：`runtime/code_backups/20260928-223530`。此專案當時沒有 Git repository，故保留檔案備份供人工比較，未覆蓋既有模型／資料。
