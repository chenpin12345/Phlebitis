# tests

自動測試只用合成影像、暫存資料夾與模擬 LINE；不讀寫正式資料，不傳訊息給真實 LINE 帳號。

```powershell
.\.venv\Scripts\python.exe -m pytest -q            # 全部，約 3 分鐘
.\.venv\Scripts\python.exe -m pytest -q tests\test_full_backup.py   # 單一檔案
```

## 隔離規則（新增測試前必讀）

- 工作台 API 測試一律用 `workbench_fixture.configure(tmp_path, monkeypatch)` 建立隔離環境；不要對正式資料根目錄呼叫 `create_app(testing=True)`（`testing=True` 只停用背景工作，不是資料隔離）。
- 新的資料庫讀寫透過 `jobs.db()`（fixture 會換成暫存資料庫）。
- 會寫檔的位置要仿 `common.code_path()`／`backup_root()`／`inbox_root()`：正式資料根目錄才對應到 04／05，暫存根目錄寫在自己底下。`test_full_backup.py` 檢查測試不會寫進正式的 `04_備份`。

## 主要測試檔

| 檔案 | 範圍 |
|---|---|
| `test_data.py`、`test_tasks.py`、`test_areas.py`、`test_multiclass.py`、`test_holdout.py` | manifest、審查、任務規則、單一工作區、分期、獨立測試集 |
| `test_performance_imports.py`、`test_external_import.py` | 05_匯入區的照片與模型包、岡山高醫外部來源、路徑安全 |
| `test_external_models.py` | 外部訓練模型的重建、拒絕 .pt、評估前不可啟用 |
| `test_full_backup.py`、`test_batch1_tools.py` | 完整備份（增量、舊版本、30 天清理、核對、還原、提醒）、每日備份 |
| `test_trash*.py`、`test_cleanup_views.py`、`test_lifecycle.py` | 垃圾桶與資源生命週期 |
| `test_workbench*.py`、`test_worker_launch.py` | 管理 API、背景工作 |
| `test_line.py`、`test_conversation.py`、`test_inference.py` | LINE 與推論 |
| `test_batch2_*` … `test_batch5_*` | 2026-10-17 的功能批次 |
| `test_paths.py` | 工作區 01–05 位置、正式／測試分流、工作區檢查 |
| `test_docs_links.py` | 所有 Markdown 文件的相對連結都存在 |

## 瀏覽器回歸測試

在 `web/` 內以 Edge headless 操作 8877 的合成 fixture（`workbench_fixture.py`），步驟見 [02_主程式碼/README.md](../README.md#測試)。每跑一套前重新啟動 fixture。結果與截圖寫到 `01_文件與紀錄/驗證報告/`，量測寫到 `03_模型與影像資料/runtime/performance/`。
