# configs

| 檔案 | 內容 | 修改時注意 |
|---|---|---|
| `service.json` | 圖片解碼限制、LINE 服務與推論相關設定 | 影響 LINE 與工作台的圖片檢查 |
| `import_sources.json` | 可以讀取的外部照片來源（岡山高醫）、檔名規則與授權紀錄 | `path` 寫相對於工作區根目錄的路徑（目前 `05_匯入區/岡山高醫`）；新增來源或改規則需要專案負責人授權並記錄在 `authorization` |
| `research_consent.json` | LINE 研究收件的同意文字與保存規則 | 見 [RESEARCH_INTAKE.md](../../01_文件與紀錄/操作與交付說明/RESEARCH_INTAKE.md) |

工作台的偏好（通知、備份、抽查比例）不在這裡，而是在「設定與維護」頁，存在資料庫中。
