# 02_主程式碼（開發說明）

這一頁給要修改程式的人。只是使用工作台的話，看根目錄的 [README](../README.md) 與 [HANDOVER](../01_文件與紀錄/操作與交付說明/HANDOVER.md) 就夠了。

## 環境

- Windows、Python 3.12、Node.js 22 以上；NVIDIA GPU（沒有 GPU 也能用 CPU，但要在工作台明確選擇）。
- 安裝或修復：雙擊根目錄 `setup.bat`（等同 `scripts\setup-workbench.ps1`；沒有 GPU 加 `-CpuOnly`）。只安裝到本資料夾的 `.venv` 與 `web\node_modules`，不動資料。
- Python 一律用 `.\.venv\Scripts\python.exe`（這台電腦的 `python` 指令是 WindowsApps 的空殼）。
- 套件版本鎖在 `requirements.lock.txt`。

## 啟動與命令列

```powershell
.\.venv\Scripts\python.exe -m src workbench --port 8765   # 等同根目錄 start.bat
.\.venv\Scripts\python.exe -m src doctor                  # GPU、套件與工作區檢查
.\.venv\Scripts\python.exe -m src --help                  # 所有指令
```

| 指令 | 用途 |
|---|---|
| `doctor` | GPU、套件版本與工作區檢查（結果也寫到 `01_文件與紀錄/驗證報告/environment.json`） |
| `workbench` | 啟動工作台（port 8765） |
| `audit` | 檢查 manifest 與標註是否一致 |
| `review` | 人工確認一張照片的狀態並同步搬移檔案 |
| `build`／`predict` | 建立分類快照；用本地模擬模型分析照片 |
| `imports` | 05_匯入區與外部來源的匯入（scan／commit／status／retry／external-scan／external-commit／apply-rules） |
| `serve`／`menu` | LINE webhook（port 8000）與圖文選單素材 |
| `migrate-tasks` | 把舊資料列改成單一工作區（可重複執行） |

指令中的 `data/...`、`runs/...` 等相對路徑以 `03_模型與影像資料` 為準。

## 程式結構

| 資料夾 | 內容 |
|---|---|
| `src/` | 後端。`paths.py` 讀 `../workspace-layout.json` 找到 01–05 各區；`common.py` 是共用工具 |
| `src/workbench/` | 工作台管理 API 與所有功能模組（清單見 [src/workbench/README.md](src/workbench/README.md)） |
| `src/data/`、`src/imports/` | 資料清單、審查、快照；05_匯入區匯入 |
| `src/inference/`、`src/line_bot/`、`src/training/` | 共用推論；LINE；舊 CLI 訓練 |
| `web/` | React／TypeScript 介面（見 [web/README.md](web/README.md)） |
| `tests/` | pytest 自動測試與 8877 合成 fixture（見 [tests/README.md](tests/README.md)） |
| `scripts/` | 安裝、啟動、檢查與一次性工具（見 [scripts/README.md](scripts/README.md)） |
| `configs/` | 訓練、服務、外部來源與研究同意設定（見 [configs/README.md](configs/README.md)） |

## 修改程式的規則

1. **改之前先確認 git 是乾淨的**，改完一個主題就 commit 一次（工作區根目錄是 git repo；只在本機，不要推到公開遠端）。
2. **改完跑 `scripts\check.ps1`**：排版檢查（black、prettier）、全部 pytest、網頁建置。`-Fix` 會先自動排版。
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check.ps1
   ```
3. **測試不能碰正式資料**：用 `tests/workbench_fixture.configure(tmp_path, monkeypatch)` 建立隔離環境；新的資料庫讀寫一律透過 `jobs.db()`。新的資料位置要仿 `common.code_path()`／`backup_root()`：正式資料根目錄對應到 03／04／05，測試的暫存根目錄寫在自己底下。
4. **介面改動**遵守 `web/src/style.css` 開頭的規則：只有一個強調色；狀態一定是「形狀＋文字」；中文字重只用 400／700；圓角 ≤ 8px；頁面標題用名詞，不放英文小標或口號（研究報告：`01_文件與紀錄/研究報告/reports/`）。
5. **改了網頁要重新建置**：`cd web; npm run build`（工作台提供的是 `web/dist`）。
6. **資料庫結構變更**：在 `src/workbench/migrations/` 新增 `vN_<名稱>.py` 並加到 `STEPS`；先用 `common.database_backup()` 備份。
7. **不要放寬安全邊界**：匯入路徑檢查、CSRF、localhost 限制、模型雜湊核對、垃圾桶保護規則都有測試，失敗時修程式而不是改測試。

## 測試

```powershell
.\.venv\Scripts\python.exe -m pytest -q        # 全部自動測試，約 3 分鐘
```

瀏覽器回歸測試（Edge headless，只操作 8877 的合成 fixture）：

```powershell
# 終端機 1：啟動 fixture（每跑一套前都重新啟動，因為測試會改 fixture 狀態）
.\.venv\Scripts\python.exe -c "import os,runpy,sys;sys.path[:0]=['.','tests'];sys.argv=['workbench_fixture.py','8877'];runpy.run_path('tests/workbench_fixture.py',run_name='__main__')"
# 終端機 2
cd web; node workbench-regression.mjs   # 其他：trash-regression、cleanup-regression、features-regression、import-regression、query-lifecycle-regression
```

量測結果寫到 `03_模型與影像資料/runtime/performance/`；驗收截圖寫到 `01_文件與紀錄/驗證報告/`。

真實 LINE 帳號、HTTPS 與手機收圖的設定見 [LINE.md](../01_文件與紀錄/操作與交付說明/LINE.md)。自動測試使用模擬 LINE，不會傳訊息給真實使用者。
