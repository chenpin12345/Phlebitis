# src/workbench/routes：管理 API 路由

只由本機工作台（`api.py`）掛載，沿用同源與 CSRF 保護；公開的 LINE 服務不會掛載這些路由。

- `imports.py`：照片與模型匯入（批次、預覽、提交、重試、紀錄）。
- `intake.py`：LINE 研究收件與離線 LINE 模擬器。
- `tools.py`：下一步、通知、搜尋、磁碟用量、設定、每日備份、完整備份、岡山高醫新照片、旗標、抽查、建議框。

其餘路由直接寫在 `api.py`。
