# src/workbench/queries：讀取用投影與快取

把資料清單、報告、檔案與訓練曲線投影到 SQLite 或快取，讓列表頁不用每次重算。這些都可以刪掉重建；正式紀錄仍是 manifest、快照與報告檔。**不能**用它們來決定是否允許載入模型、訓練或刪除。

`data_index.py`（資料審查列表）、`reports.py`（報告摘要）、`files.py`、`images.py`（縮圖快取）、`curves.py`（訓練曲線）、`legacy.py`（舊曲線）、`records.py`（案件與事件）。
