# src/imports：匯入服務

網頁與 CLI（`python -m src imports …`）共用。流程一律是「掃描 → 預覽 → 人工確認 → 暫存、驗證 → 寫入」，不執行模型包內的程式、不刪除來源檔案。

- `service.py`：`05_匯入區/photos/<批次>/` 的照片與 `05_匯入區/models/<模型包>/` 的模型包。路徑檢查以 05_匯入區為邊界，拒絕捷徑、junction、共享硬連結與越界路徑；紀錄中的來源路徑寫成 `inbox/...`，由 `common.inbox_root()` 對應到實際位置。
- `external.py`：`configs/import_sources.json` 明列的外部來源（岡山高醫）。唯讀掃描，要補入的照片先複製到 `03_模型與影像資料/runtime/imports/external/`，再交給 `service.py`。
- 外部訓練的模型由 `src/workbench/external_models.py` 重建。

測試：`tests/test_performance_imports.py`、`test_external_import.py`、`test_external_models.py`；瀏覽器：`web/import-regression.mjs`。
