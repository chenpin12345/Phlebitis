# data

正式照片清單 `manifest.csv` 與照片、標註。只有 `approved/` 的照片能進入訓練快照。

| 位置 | 內容 |
|---|---|
| `manifest.csv` | 所有照片的正式清單（不要手動編輯；修改前副本在 `04_備份/修改前副本/manifest/`） |
| `approved/`、`pending_review/`、`excluded/` | 可用、待人工審查、排除的照片與標註 |
| `reviews/`、`label_evidence/` | 每次人工審查的紀錄；規則預填與確認的證據 |
| `snapshots/` | 不可變的資料快照 |
| `yolo/` | 2026-11 以前建立的舊快照，工作紀錄仍指向這裡，不要改名 |
| `imports/` | 每張匯入照片的來源紀錄 |
| `migrations/` | 批次修改資料的紀錄 |
| `image_sources.json` 等 | 顯示名稱、重複判斷、快照狀態、抽查結果 |
| `thermal/` | 熱像儀 CSV（尚未用於模型） |

詳細規則見 `01_文件與紀錄/操作與交付說明/DATA.md`。
