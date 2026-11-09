# scripts

在 `02_主程式碼` 內執行（PowerShell 腳本用 `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\<名稱>.ps1`，Python 腳本用 `.\.venv\Scripts\python.exe scripts\<名稱>.py`）。

## 日常

| 腳本 | 用途 |
|---|---|
| `start-workbench.ps1` | 啟動工作台（根目錄 `start.bat` 呼叫它） |
| `stop-services.ps1` | 停止工作台（8765）與 LINE 服務（8000）（`stop.bat`） |
| `setup-workbench.ps1` | 安裝或修復 Python 環境並建置網頁（`setup.bat`）；`setup.ps1` 是它使用的 PyTorch／CUDA 安裝步驟 |
| `predict-image.ps1` | 選一張照片用選定模型分析（`predict.bat`） |
| `start-line.ps1` | 啟動 LINE webhook（port 8000；需要 `.env` 金鑰） |
| `project.ps1` | 在專案環境執行 `python -m src` 指令的捷徑 |

## 開發與交接

| 腳本 | 用途 |
|---|---|
| `check.ps1` | **改完程式就跑**：排版檢查、全部 pytest、網頁建置；`-Fix` 先自動排版 |
| `check_commit_safety.py`、`githooks/` | pre-commit 鉤子：擋照片、權重、金鑰、病歷號。圖片要進 git 必須列在 `githooks/allowed-images.txt`，只放確認過的合成畫面；測試的檔名範例用 `ZZ` 開頭的合成代碼 |
| `rename_source_ids.py` | 2026-11 來源名稱統一的一次性工具（已執行，保留供追溯）；預設只預覽 |
| `model_package.py` | 外部模型包：`export`（在訓練者電腦把自己的權重轉成 safetensors＋package.json）、`manifest`（重算 SHA-256） |

## 驗收與一次性工具（不是日常操作）

| 腳本 | 用途 |
|---|---|
| `smoke_workbench.py` | **會真的訓練五種模型**的工作台驗收 |
| `check_workbench_readonly.py` | 對正式資料做唯讀驗收（不排程、不訓練） |
| `run_regression.py` | 舊的手動回歸入口（不啟用模型） |
| `benchmark_queries.py` | 大量合成資料下的查詢效能量測 |

驗收結果寫到 `01_文件與紀錄/驗證報告/`，量測寫到 `03_模型與影像資料/runtime/performance/`。
