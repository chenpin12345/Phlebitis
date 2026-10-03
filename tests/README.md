# tests

使用合成影像與模擬 LINE 的自動測試；不對真實 LINE 帳號傳訊息。

工作台 API 測試必須使用 `workbench_fixture.configure(tmp_path, monkeypatch)` 或明確隔離所有資料來源，不得直接對正式根目錄建立 `create_app(testing=True)`。`testing=True` 只停用部分背景工作，並不是資料隔離保證。

效能與匯入回歸見 `test_performance_imports.py`；測試、瀏覽器及量測結果見 `docs/PERFORMANCE_RESULTS.md`。破壞性測試僅操作 fixture。
