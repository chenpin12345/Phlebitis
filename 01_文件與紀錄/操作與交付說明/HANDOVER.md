# 接手說明（HANDOVER）

接手這個專題的人請先讀完這一頁。更新：2026-10-17。

## 1. 這個專案是什麼

- 用手機拍的靜脈炎照片，在**本機**做資料整理、人工審查與標註、訓練兩種整張照片分類模型（EfficientNet-B0、DINOv2）、評估比較，並模擬 LINE 回覆。
- 是研究原型，**不是臨床診斷工具**，不提供嚴重度分級。
- 所有操作都在網頁工作台 http://127.0.0.1:8765 （只有這台電腦能連）。

### 目前狀態（2026-10-17）

| 項目 | 狀態 |
|---|---|
| 照片 | 60 張，全部來自岡山高醫且檔名符合醫院格式：可用 32、排除 28（即時數字看工作台「總覽」） |
| 病人分組 | 32 張已依檔名病歷號分組，共 8 位病人；正常照片只來自 3 位，二分類只能當流程驗證 |
| 醫師核准 | 所有照片已由兩位醫師核准，系統內不再登錄 |
| 模型 | 25 個模型版本；本地模擬使用 `efficientnet_b0_68f1a9c4ee1d4439`；**LINE 尚未指定模型** |
| 模型效果 | **尚未達實用要求**。2026-10-31 的分類成績疑似受來源影響，要等 M2.5 的來源檢查 |
| LINE | 程式完成；真實帳號、HTTPS 與手機收圖**尚未驗收** |
| 備份 | 每日自動備份已開啟；照片與模型的完整備份需要外接硬碟（尚未做過） |

## 2. 接手第一天

- [ ] 雙擊根目錄 `start.bat`，確認瀏覽器打開工作台。（換電腦時先執行 `setup.bat`）
- [ ] 「設定與維護 → 環境檢查 → 工作區」每一項都是「正常」；命令列也可以在 `02_主程式碼` 執行 `.\.venv\Scripts\python.exe -m src doctor`。
- [ ] 接上外接硬碟，「設定與維護 → 完整備份」設定位置，按「立即完整備份」。
- [ ] 讀第 5 節「安全規則」。
- [ ] 瀏覽一次每個頁面：總覽 → 資料審查 → 模型與實驗 → LINE 模擬 → LINE 研究收件 → 設定與維護 → 垃圾桶。
- [ ] 要改程式的話：讀 [02_主程式碼/README.md](../../02_主程式碼/README.md)，先跑一次 `scripts\check.ps1` 確認全部通過。
- [ ] 查看模型說明卡上的漏報、誤報，再決定下一階段要蒐集哪些資料。

## 3. 架構

```
   瀏覽器 http://127.0.0.1:8765（只限本機）
                │
   web：React／TypeScript 介面 ─────────── 02_主程式碼/web/src/features/<頁面>/
                │  /api/v1（只接受 localhost、CSRF 保護）
   src/workbench：FastAPI 管理 API ──────── 背景工作、模型版本、備份、垃圾桶、LINE 模擬
     │             │              │
   src/data      src/imports    src/workbench/adapters.py + worker.py
   審查、快照     05_匯入區匯入   五種模型的訓練與評估（獨立背景程序，一次一個 GPU 工作）
     │             │              │
     └──────► 03_模型與影像資料（data / models / runs / runtime） ◄──┘
                │
   src/inference：共用推論 ──► src/line_bot：LINE webhook（port 8000，和管理 API 完全分開）
```

- 管理 API（8765）只聽本機；LINE 入口（8000）看不到也控制不了管理資料。
- 長時間的訓練／評估是獨立的 Windows 背景程序，網頁關掉或重開不會重複啟動，也不會中斷。
- 資料檔（manifest、標註、審查紀錄）是正式紀錄；SQLite 資料庫是工作狀態與加速用的索引。

## 4. 名詞

| 名詞 | 意思 |
|---|---|
| manifest | `03_模型與影像資料/data/manifest.csv`，所有照片的正式清單。**不要手動編輯**，透過工作台或 `review` 指令修改 |
| approved／pending_review／excluded | 照片的存放狀態：可用／待人工審查／排除。只有 approved 的照片能進訓練 |
| 資料審查 | 只有一個工作區：整張照片分類。病灶框選已隨 YOLO 移除，舊框檔案保留但不使用 |
| 任務與標籤方案 | `binary_classification`（正常／陽性，`binary_v1`）、`stage_classification`（正常／第一期／第二期，`stage_v1`） |
| 快照 | `data/snapshots/<版本>/`（2026-11 以前的留在舊位置）：固定的成員、雜湊、分組與三折切分。訓練一定要指定快照，之後修改照片不會影響已建立的快照 |
| 流程展示（demo） | 只驗證流程的快照與訓練；結果不能當正式成績 |
| 獨立測試集 | 建立實驗時勾選，固定保留約 20% 照片不參與訓練，訓練後另外評估一次 |
| 模型版本 | `models/versions/<id>/`，登錄後不再改變 |
| 模型引用 | `models/references/local.json`（本地模擬用）與 `line.json`（LINE 用）。換模型只改引用，要先有完整評估 |
| 外部來源（岡山高醫） | `05_匯入區/岡山高醫/`：唯讀掃描，依檔名規則預填分類，詳見 [DATA.md](DATA.md) |
| 舊來源名稱 | 2026-11 全部改成岡山高醫；研究決策、研究筆記、簡報和舊截圖保留原樣，裡面的舊名都以岡山高醫為準 |
| 外部模型 | 在別處訓練、以 safetensors 匯入的模型；評估前不能啟用 |
| 垃圾桶 | 所有刪除都先移到垃圾桶；永久刪除要在垃圾桶頁明確確認 |
| fixture（8877） | 測試用的合成工作台（`tests/workbench_fixture.py`），瀏覽器回歸測試只在它上面跑 |

## 5. 安全規則（一定要遵守）

1. **不自動訓練、不自動啟用模型**：訓練、評估、切換模型都要人按按鈕。系統的「建議」也只是建議，要人工確認。
2. **不傳送真實 LINE 訊息**：開發與測試只用「LINE 模擬」。真實 LINE 要另外完成帳號、HTTPS 與手機驗收。
3. **岡山高醫原始照片唯讀**：`05_匯入區/岡山高醫/` 的檔案程式只讀不改、不搬、不刪。
4. **刪除只透過垃圾桶**：不要用檔案總管直接刪 `03_模型與影像資料` 裡的東西；垃圾桶會檢查使用中的模型與相依資料。
5. **不直接修改 manifest、快照、模型版本**：雜湊不符時系統會拒絕訓練或載入。
6. **不開啟外來的 `.pt`／`.pth`**：pickle 檔案開啟時可以執行任意程式碼。外部模型一律轉成 safetensors 再匯入（[05_匯入區/models/README.md](../../05_匯入區/models/README.md)）。
7. **病人影像不外流**：不上傳雲端或公開網站；git 只在本機，推到遠端前要先確認沒有照片、床號與日期。
8. **管理工作台不要對外開放**：不要把 port 8765 接到公開網路或 HTTPS tunnel。
9. **測試不碰正式資料**：自動測試一律用暫存資料夾或 8877 fixture（詳見 [tests/README.md](../../02_主程式碼/tests/README.md)）。

## 6. 常見任務去哪裡做

| 想做的事 | 在工作台 | 相關程式 | 說明文件 |
|---|---|---|---|
| 審查照片、框病灶、分期 | 資料審查 | `src/data/dataset.py`、`tasks.py` | [DATA.md](DATA.md) |
| 補入岡山高醫新照片 | 資料審查 → 外部來源比對與補入 | `src/imports/external.py` | [05_匯入區/README.md](../../05_匯入區/README.md) |
| 匯入其他照片 | 資料審查 → 匯入照片 | `src/imports/service.py` | 同上 |
| 建快照、訓練、評估、比較 | 模型與實驗 | `src/workbench/adapters.py`、`jobs.py`、`worker.py` | [TRAINING.md](TRAINING.md) |
| 匯入外部訓練的模型 | 模型與實驗 → 匯入模型 | `src/workbench/external_models.py`、`scripts/model_package.py` | [05_匯入區/models/README.md](../../05_匯入區/models/README.md) |
| 選本地模擬或 LINE 用的模型 | 模型與實驗 → 模型版本 | `src/workbench/registry.py` | [WORKBENCH.md](WORKBENCH.md) |
| 試 LINE 對話 | LINE 模擬 | `src/workbench/simulation.py`、`src/line_bot/conversation.py` | [LINE.md](LINE.md) |
| 處理 LINE 收到的研究照片 | LINE 研究收件 | `src/workbench/intake.py` | [RESEARCH_INTAKE.md](RESEARCH_INTAKE.md) |
| 刪除或還原 | 垃圾桶 | `src/workbench/trash.py` | [WORKBENCH.md](WORKBENCH.md) |
| 備份與還原 | 設定與維護 | `src/workbench/backup.py`、`full_backup.py` | [04_備份/README.md](../../04_備份/README.md) |
| 改訓練或服務參數 | — | `02_主程式碼/configs/*.json` | [configs/README.md](../../02_主程式碼/configs/README.md) |
| 改畫面 | — | `web/src/features/<頁面>/`、`web/src/style.css` | [web/README.md](../../02_主程式碼/web/README.md) |
| 改資料庫結構 | — | `src/workbench/migrations/` | [src/workbench/README.md](../../02_主程式碼/src/workbench/README.md) |

## 7. 程式地圖

| 位置 | 責任 |
|---|---|
| `src/paths.py`、`src/common.py` | 依 `workspace-layout.json` 找 01–05 各區；JSON／CSV／雜湊工具 |
| `src/workspace_check.py` | `doctor` 與設定頁的工作區檢查 |
| `src/data/` | manifest、審查交易、標註轉換、任務規則、快照與分組 |
| `src/imports/` | 05_匯入區的照片與模型包匯入；岡山高醫外部來源 |
| `src/inference/`、`src/environment.py` | 圖片解碼與方向校正；環境檢查 |
| `src/line_bot/` | LINE 簽章、訊息、圖文選單、排隊與限時圖片 |
| `src/workbench/` | 管理 API、五模型 adapter、背景工作、模型版本、評估、模擬、研究收件、垃圾桶、備份（模組清單見其 [README](../../02_主程式碼/src/workbench/README.md)） |
| `src/lock.py` | 跨程序與整台電腦的 GPU 互斥 |
| `web/src/` | React 介面：`app/` 入口、`features/<頁面>/`、`shared/` 共用元件 |
| `tests/` | 自動測試（約 330 項）與 8877 fixture |
| `scripts/` | 安裝、啟動、檢查（`check.ps1`）、模型包（`model_package.py`）等腳本 |

## 8. 對外介面

- `POST /webhook`：LINE 簽章驗證後接收事件；沒有讓任何人直接呼叫模型的公開接口。
- `GET /health`：服務與模型是否就緒、展示旗標與排隊數量。
- `GET /results/{token}.jpg`：限時結果圖片，逾時回傳 410。
- 命令列 `python -m src`：doctor、workbench、audit、build、review、train、evaluate、select、predict、serve、menu、imports、migrate-tasks。

結果狀態有 suspected、not_detected、needs_review、quality_rejected，執行錯誤另外記錄。分類模型不產生假的框，severity 固定沒有值。

## 9. 資料變更與重現

- 新快照保存自己的成員、圖片與標註雜湊。修改備註不會讓快照失效；修改標註或個案會讓相關快照標記「不適用」，歷史仍可追溯。
- 不要修改產生的圖片或標註；雜湊不符時拒絕訓練。
- 不覆寫舊報告：原成果報告（`研究報告/成果報告NEW.docx`）可能對應不同的資料版本，新結果放到新的驗收紀錄。
- 未取得新資料前，不要以多次調參後的最高分宣稱準確率。

## 10. 已知限制與下一步

- 沒有自動病人識別、臨床分級模型、NIS／FHIR 寫入、熱像融合或正式上線認證。
- 檔名推得的分組（candidate_group）只是候選，仍待資料提供者確認。
- 嚴重度分級要先定義標準並取得可靠標註；不能把模型分數換算成嚴重度。
- LINE 會經過外部平台；若影像必須留在院內網路，應改用院內上傳入口。
- 院內研究版本：保留 `src/inference` 的模型介面，再加上匿名案件對應、操作稽核、人工覆核、部署監控與院方要求的保存方式。

## 11. 常見問題

| 狀況 | 處理 |
|---|---|
| 環境檢查「需處理」 | 依該列的提示處理；多數是資料夾被改名或沒執行 `setup.bat` |
| CUDA 顯示 false | 執行 `doctor`，確認安裝的是 GPU 版 torch 與 NVIDIA 驅動 |
| Training or LINE inference is already running | 先停止另一個訓練或 LINE 程序（一次只能一個 GPU 工作） |
| 舊快照 Manifest changed | 建立新快照 |
| 模型不能啟用 | 先用本專案資料完成評估；外部模型一定要評估 |
| 匯入失敗「來源於預覽後變更」 | 檔案還在複製中或被改過；等複製完成後重新掃描 |
| 找不到完整備份位置 | 外接硬碟沒接上，或磁碟代號變了；到設定頁重新指定 |
| No LINE credentials | 在根目錄 `.env` 填金鑰（範本 `.env.example`），不要寫進程式 |
| LINE Verify 失敗 | 檢查服務、HTTPS 網址與 Channel secret；`PUBLIC_BASE_URL` 要和 LINE 後台一致 |
| 正常照片也出現框 | 把案例放進經同意的人工審查流程；不要未經確認就加入訓練 |

更多文件：[INDEX.md](../INDEX.md)。變更歷程：[變更紀錄.md](../變更紀錄.md)。
