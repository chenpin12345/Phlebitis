# 03_模型與影像資料

已經進入系統的資料。**不要用檔案總管直接修改或刪除這裡的檔案**：照片與標註請透過工作台「資料審查」，刪除請透過「垃圾桶」。新進的照片與模型先放 `../05_匯入區/`。

| 資料夾 | 內容 |
|---|---|
| `data/` | 照片清單 `manifest.csv`、照片與標註（approved／pending_review／excluded）、審查紀錄、標籤證據、資料快照（`snapshots/`） |
| `models/` | 官方基礎權重（`pretrained/`）、不可變模型版本（`versions/`）、本地模擬與 LINE 的模型引用（`references/`）、舊 CLI 選定權重（`selected/`） |
| `runs/` | 訓練、評估與預測的輸出（`runs/workbench/jobs`、`evaluations`） |
| `runtime/` | 工作台資料庫、程式鎖、快取、匯入暫存與收據、效能量測 |
| `archive/` | 原始資料與舊版程式的封存（唯讀，不參與訓練） |

這一區的內容不納入 git（只有 README）。備份方式見 `../04_備份/README.md`：每日備份只含紀錄，照片與模型要用外接硬碟的完整備份。
