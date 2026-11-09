# models

| 位置 | 內容 |
|---|---|
| `pretrained/` | 五種方案的官方基礎權重與來源紀錄（`imported/` 是匯入的基礎權重或 checkpoint） |
| `versions/<id>/` | 訓練或匯入後登錄的模型版本，登錄後不再改變；`artifact.json` 記錄檔案雜湊、設定與來源（外部訓練的模型 `extra.source = external`） |
| `references/` | `local.json`（本地模擬使用中）、`line.json`（LINE 使用中）；換模型只改這裡，而且要先有完整評估 |

不要手動改這裡的檔案；刪除模型版本請透過垃圾桶（使用中的模型會被擋下）。
