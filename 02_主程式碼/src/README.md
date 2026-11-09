# src：後端原始碼

在 `02_主程式碼` 內以 `.\.venv\Scripts\python.exe -m src <指令>` 執行（`__main__.py` 列出所有指令）。

| 位置 | 責任 |
|---|---|
| `paths.py` | 讀 `../../workspace-layout.json`，提供 01–05 各區位置（`STORE_ROOT`、`BACKUP_ROOT`、`INBOX_ROOT`…） |
| `common.py` | 資料根目錄 `ROOT`、JSON／CSV／雜湊工具，以及正式／測試分流的位置函式（`code_path`、`backup_root`、`inbox_root`） |
| `workspace_check.py` | `doctor` 與設定頁的工作區檢查 |
| `data/` | manifest、審查交易、標註轉換、任務與標籤規則、快照與分組、檔名規則 |
| `imports/` | 05_匯入區的照片與模型包匯入（`service.py`）；岡山高醫等外部來源（`external.py`） |
| `inference/` | 共用推論：圖片解碼、方向校正、結果格式 |
| `environment.py` | 環境檢查（`doctor`） |
| `line_bot/` | LINE webhook、簽章、訊息、圖文選單、排隊 |
| `workbench/` | 工作台後端（見 [workbench/README.md](workbench/README.md)） |
| `lock.py`、`telemetry.py` | GPU 互斥鎖、效能量測 |
