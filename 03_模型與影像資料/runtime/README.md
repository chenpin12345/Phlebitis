# runtime

程式執行時的狀態，不納入版本控制。

| 位置 | 內容 |
|---|---|
| `workbench/workbench.sqlite3` | 工作台資料庫（工作、匯入、垃圾桶、通知、設定）；每日備份與完整備份都會用 SQLite 線上備份複製它 |
| `imports/` | 匯入收據、官方權重可信摘要（`trusted-official/`）、暫存（`staging/`）、岡山高醫補入暫存（`external/`） |
| `cache/` | 縮圖與特徵快取 |
| `performance/` | 瀏覽器與查詢效能量測結果 |
| `*.lock` | 程式鎖；工作台執行中不要刪 |
