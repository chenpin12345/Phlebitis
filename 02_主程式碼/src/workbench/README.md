# src/workbench：工作台後端

`api.py` 的 `create_app()` 建立 FastAPI 管理 API（只聽 127.0.0.1:8765，Host／Origin 限制與 CSRF 保護），其餘模組各負責一個功能。功能代號（A1、D3…）對應 `01_文件與紀錄/驗證報告/verification/2026-10-17_功能批次1-5/`。

## 核心

| 模組 | 責任 |
|---|---|
| `api.py` | 建立 app、掛載路由、背景排程（索引監看、工作管理、每日備份、岡山高醫監看）的啟動與關閉 |
| `contracts.py` | 五種模型的定義（`MODELS`）、實驗與推論設定的資料契約（pydantic） |
| `storage.py` | SQLite 連線（`db()`）、檔案鎖、資料集鎖；開啟時套用 `migrations/` |
| `jobs.py`、`worker.py` | 持久工作：排隊、獨立背景程序、取消、程序對帳 |
| `resources.py` | 資源生命週期（使用中／垃圾桶／已刪除）的唯一判斷來源與運算鎖 |
| `migrations/` | 資料庫升級 v1–v6，依 `STEPS` 順序執行；升級前備份到 `04_備份/修改前副本/資料庫/` |
| `settings.py` | 工作台偏好（通知、每日備份、完整備份、抽查），存在 flags 資料表 |

## 模型

| 模組 | 責任 |
|---|---|
| `adapters.py` | 五種模型的訓練、評估與推論（`ModelPredictor`） |
| `metrics.py` | 評估指標 |
| `registry.py` | 不可變的模型版本、本地模擬／LINE 引用與啟用把關 |
| `external_models.py` | 外部訓練的模型：只收 safetensors，依官方架構重建，評估前不可啟用 |
| `evaluation_views.py`、`report_views.py`、`presentation.py` | 評估的信賴區間、白話摘要、模型說明卡、報告呈現 |
| `shadow.py` | LINE 影子模式（C2）：候選模型默默分析同一批照片 |

## 資料與匯入

| 模組 | 責任 |
|---|---|
| `views.py`、`queries/` | 讀取用的 SQLite 投影與快取（可重建；正式紀錄仍是 manifest 與快照） |
| `flags.py`、`spot_check.py` | 疑似重複與影像品質旗標（A3、A6）；岡山高醫檔名自動分類的抽查（A5） |
| `cards.py` | 模型卡與資料卡匯出，不含檔名與病歷號 |
| `baselines.py` | 三個比較用基線，不能啟用 |
| `ledger.py` | 只增不改的實驗登錄 |
| `source_audit.py` | 資料可信度頁：來源檢查與資料盤點 |
| `source_watch.py` | 偵測 `05_匯入區/岡山高醫/` 的新照片（只讀，不匯入） |
| `intake.py`、`research.py`、`lifecycle.py` | LINE 研究收件、授權研究資料的轉入與保存期限 |
| `managed_files.py` | 允許清單內的檔案盤點與安全刪除 |

## 工具與維護

| 模組 | 責任 |
|---|---|
| `trash.py` | 垃圾桶：預覽、移入、還原、永久刪除與中斷恢復 |
| `backup.py` | 每日自動備份（紀錄 zip，`04_備份/工作台紀錄/`）與還原 |
| `full_backup.py` | 完整備份到外接硬碟：增量複製、舊版本保留 30 天、核對、還原到新資料夾、提醒 |
| `disk.py` | 磁碟用量與可清理的舊輸出（清理一律送垃圾桶） |
| `notifications.py`、`next_steps.py`、`search.py` | 頁首通知、總覽的待辦、全域搜尋 |
| `simulation.py` | LINE 模擬器：與正式 LINE 共用事件規則，只用假傳送 |
| `routes/` | `imports.py`（匯入）、`intake.py`（研究收件與模擬器）、`tools.py`（通知、搜尋、設定、備份等） |

完整操作與政策見 [WORKBENCH.md](../../../01_文件與紀錄/操作與交付說明/WORKBENCH.md)。
