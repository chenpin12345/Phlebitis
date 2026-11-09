# runs

每次訓練、評估與預測各自的輸出，舊紀錄不覆寫，也不會自動成為使用中的模型。

- `workbench/jobs/<工作ID>/`：工作台訓練工作的設定、日誌、checkpoint 與產物。
- `workbench/evaluations/<工作ID>/`：評估報告與錯誤照片。
- `latest_comparison.json`：舊 CLI 三折比較的指向。

失敗、取消或超過 30 天的工作輸出可在「設定與維護 → 磁碟用量」送到垃圾桶。完整備份預設不含這一區（可在設定中勾選）。
