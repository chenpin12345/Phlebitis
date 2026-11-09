# 驗證報告

| 位置 | 內容 | 由誰產生 |
|---|---|---|
| `WORKBENCH_ACCEPTANCE.md`、`PERFORMANCE_RESULTS.md` | 工作台與效能的驗收紀錄 | 人工撰寫 |
| `來源檢查結果.md`、`來源檢查結果.json` | M2.5 來源檢查，含 10/31 成績的判斷 | 人工撰寫、`source_audit.py` |
| `environment.json` | 最近一次環境檢查（GPU、套件、工作區） | `python -m src doctor` |
| `resume-check.json` | 續訓檢查 | `scripts/check_resume.py` |
| `workbench-smoke.json` | 五模型實際訓練驗收 | `scripts/smoke_workbench.py`、`finish_workbench_acceptance.py` |
| `workbench-*.png`、`workbench-browser-evidence.json` | 主要流程截圖與瀏覽器證據 | `web/browser-smoke.mjs`（舊測試，操作正式工作台；2026-09-28 之後未再執行） |
| `verification/` 上層的 json／png | 最近一次瀏覽器回歸結果與截圖 | `web/*-regression.mjs`、`scripts/check_workbench_readonly.py` |
| `verification/<日期>_<主題>/` | 一次性的紀錄（每次整理、補入、批次的報告與證據） | 人工整理 |

程式產生的檔案每次執行都會覆寫成最新結果；要保留某次結果時，把它複製到 `verification/<日期>_<主題>/`。

截圖與紀錄都來自合成的 8877 fixture，除了 `verification/2026-10-13_岡山高醫補入/` 與 `real-data-readonly.json` 這類明確標示使用正式資料的紀錄。
