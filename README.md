# 靜脈炎影像研究展示系統

本專案提供本地網頁工作台：資料審查、本地 NVIDIA GPU 訓練、模型評估、圖片分析與 LINE 模擬。保留 **YOLO11n** 基線，依工作台需求新增 YOLO11s、YOLO26s、EfficientNet-B0 與 DINOv2 ViT-S/14 分類器，**不提供嚴重度分級**。

## 啟動網頁工作台

雙擊 **啟動研究工作台.cmd**，開啟 **http://127.0.0.1:8765**。這不會自動訓練，也不需要 LINE 金鑰。

```powershell
.\.venv\Scripts\python.exe -m src workbench --port 8765
```

換電腦時先執行 `scripts/setup-workbench.ps1`，完成 Python 與網頁依賴安裝。操作、架構、參數與保存政策見 [工作台手冊](docs/WORKBENCH.md)，實際驗收見 [工作台驗收紀錄](docs/WORKBENCH_ACCEPTANCE.md)。

## 目前模型狀態

既有六組 YOLO11n GPU 訓練與選定權重保留。**目前辨識效果尚未達實用要求**：原選定模型在該折驗證中漏掉4張病灶照片，3張正常照片有1張誤報。五模型工作台已完成有限訓練與模擬流程驗收，短程驗收不代表模型效能達標，也沒有自動更換 LINE 使用中模型。歷史結果見 [執行紀錄](docs/IMPLEMENTATION.md)。

## 先從這裡開始

在專案資料夾開啟 PowerShell。已建立環境的這台電腦可直接執行：

    .\.venv\Scripts\python.exe -m src doctor
    .\.venv\Scripts\python.exe -m src audit
    .\.venv\Scripts\python.exe -m src --help

換電腦或需要重建環境時：

    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1

## 直接分析照片

完成模型選定後，可雙擊根目錄的 **啟動本地預測.cmd**，選一張照片。結果資料夾會自動開啟，包含框選 JPG 及 JSON。此操作不需 LINE 金鑰，也不會重新訓練模型。

命令列方式：

    .\.venv\Scripts\python.exe -m src predict "照片完整路徑.jpg" --allow-demo

本地結果會保存在 runs，請由操作者管理保存期限；LINE 的一小時暫存規則不適用於手動命令列輸出。

## 本地訓練

目前個案編號尚未經提供者確認，所以必須明確選擇展示模式。這不表示標註全是錯誤，而是評估不能宣稱能泛化到新病人。

    .\.venv\Scripts\python.exe -m src build --demo
    .\.venv\Scripts\python.exe -m src train --demo --epochs 2
    .\.venv\Scripts\python.exe -m src train --demo

第一行建立固定種子的三折資料。第二行只驗證流程；第三行最多 120 輪，若連續 25 輪未改善會提早停止。每次輸出位於不同的 runs 資料夾。正式個案核對完成後，移除 --demo；未核對完成的資料會被阻擋。

- 完整操作：[訓練與評估](docs/TRAINING.md)
- 資料分類及人工審查：[資料管理](docs/DATA.md)
- LINE 金鑰、HTTPS、選單設定：[LINE 操作](docs/LINE.md)
- 接手人員必讀：[交接與架構](docs/HANDOVER.md)
- 本次執行結果：[實作與驗收紀錄](docs/IMPLEMENTATION.md)

## 資料夾用途

| 資料夾 | 用途 |
|---|---|
| src | 資料處理、訓練、預測與 LINE 程式 |
| configs | 訓練與服務參數 |
| scripts | Windows 操作腳本 |
| data/approved | 已按來源證據接納的照片與標註 |
| data/pending_review | 缺標註、來源不明或重複候選，暫不訓練 |
| data/excluded | 不清楚、損壞或其他已排除照片 |
| data/yolo | 僅從 approved 產生的分組資料集 |
| data/thermal | 熱像儀 CSV，未加入第一版模型 |
| models/pretrained | 五種方案的官方基礎權重與來源 |
| models/versions、models/references | 不可變模型版本、本地與 LINE 分離的引用 |
| models/selected | 明確選定的展示權重與來源資訊 |
| runs | 每次訓練、預測、評估的結果 |
| runtime | LINE 暫存、任務資料庫與程式鎖 |
| archive | 原始資料及舊版程式的可追溯封存 |
| tests | 資料隔離、服務流程與錯誤處理測試 |
| web | React／TypeScript 工作台介面 |
| src/workbench | 五模型 adapter、管理 API、背景工作、回歸與資料生命週期 |
| docs | 操作文件、原成果報告與驗收紀錄 |

## LINE 展示

模型選定後，依 docs/LINE.md 設定本機 .env，啟動：

    .\.venv\Scripts\python.exe -m src serve

服務只監聽本機 127.0.0.1:8000，需要 HTTPS 通道才能收到 LINE webhook。展示時保持電腦連網及清醒，停止訓練再啟動 LINE 服務。尚未填入 LINE 金鑰時，服務會清楚拒絕啟動。

## 執行測試

    .\.venv\Scripts\python.exe -m pytest -q

自動測試使用模擬 LINE，不會向真實使用者傳訊息。真實手機收圖回覆需完成 LINE 帳號設定後驗收。
