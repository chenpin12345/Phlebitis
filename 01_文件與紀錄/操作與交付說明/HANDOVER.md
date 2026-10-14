# 接手人員交接與架構

## 操作順序

README → 操作與交付說明/WORKBENCH.md → start.bat（工作區根目錄） → 資料審查 → 快照 → 模型與實驗 → 評估 → 本地模擬。
舊 CLI 的 audit/build/train/evaluate/select/predict/serve 仍保留；真實 LINE 設定及手機驗收延後。

避免直接執行 archive/legacy 裡的舊程式；它們保留原始路徑與參數，只供歷史查閱。

## 程式責任

| 模組 | 責任 |
|---|---|
| src/data | 搬移追蹤、標註轉換、人工審查、雜湊核對及分組 |
| src/training | GPU 環境、訓練、續訓、驗證及選定模型 |
| src/inference | 圖片解碼、方向校正、偵測與結果格式 |
| src/line_bot | LINE 簽章、訊息與選單、排隊、限時圖片 |
| src/workbench | 獨立管理 API、五模型、工作排程、版本、案例、模擬與保存政策 |
| web | React／TypeScript 管理介面，建置後由本機 API 提供 |
| src/common.py | 專案範圍路徑、JSON/CSV 與雜湊工具 |
| src/lock.py | 跨程序及 Windows 全機模型運算互斥 |

## 對外介面

- POST /webhook：LINE 簽章驗證後接收事件；不提供任意人直接呼叫模型的公開接口。
- GET /health：服務與模型是否就緒、展示旗標與排隊數量。
- GET /results/{token}.jpg：限時框選圖片，逾時回傳 410。
- 命令列 python -m src：doctor、audit、build、review、train、evaluate、select、predict、serve、menu。

結果狀態包含 suspected、not_detected、needs_review、quality_rejected，執行錯誤獨立處理。結果記錄 task_type、模型與推論設定；分類不產生偽造 boxes，severity 固定沒有值。管理 API 只在 localhost:8765；LINE 公開入口8000無法存取管理資料或控制 API。

## 資料變更與重現

新快照保存自己的成員、圖片與標註雜湊。備註修改不會讓完整快照失效；實质標註或個案變更使關聯快照標記不適用，歷史仍可追溯。不要直接修改產生的圖片或標註；雜湊不符仍拒絕訓練。舊 schema 快照保留原有完整性檢查。

目前沒有自動病人識別、臨床分級模型、NIS/FHIR 寫入、熱像融合或正式上線認證。檔名群組仍待提供者確認。未取得新資料前，不以多次調參的最高分宣稱準確率。

原成果報告保存在 docs，內容可能對應不同資料版本；不覆寫舊報告，新的結果放到獨立驗收紀錄。

## 未來院內研究版本

保留 src/inference，共用模型介面即可換成院內網頁或身分驗證服務。另加匿名案件對應、操作稽核、人工覆核、部署監控及院方要求的資料保存方式。

LINE 路徑會經過外部平台；若影像需留在內網，應改用內網上傳入口。嚴重度分級須先定義標準及可靠標註；不能把 YOLO 信心分數換算成嚴重度。

## 常見問題

- CUDA false：執行 doctor，確認安裝 GPU 版 torch 與 NVIDIA 驅動；不需要改 YOLO 版本。
- Training or LINE inference is already running：先停止另一個訓練／LINE 程序。
- 舊快照 Manifest changed：建立新快照；新 schema 不依賴即時 manifest，但篡改、撤銷或刪除仍會拒絕。
- Selected weights missing：先 evaluate、select。
- No LINE credentials：在本機填 .env，不將金鑰放到程式。
- LINE Verify 失敗：檢查服務、HTTPS 網址及 Channel secret；PUBLIC_BASE_URL 與後台網域要一致。
- 正常照片也出現框：將案例納入經同意的人工審查流程；不要未經確認就加入訓練。


## 本次交付的使用範圍

使用者已選擇先完成本地版本，LINE 帳號與 HTTPS 設定稍後補。本機可直接選圖分析及重新訓練；不需要為了操作本地預測先建立 LINE 帳號。

本地預測入口：根目錄「啟動本地預測.cmd」。
圖文選單素材：01_文件與紀錄/LINE選單/rich-menu.png。
資料核對待辦：操作與交付說明/DATA_REVIEW.md。
本次實際訓練與模型限制：歷史紀錄/IMPLEMENTATION.md。

已完成的程式功能，不等同於已完成正式病人分組核對或模型效能達標。新接手者應先查看模型卡與驗證中的漏報、誤報，再決定下一階段資料蒐集方式。
