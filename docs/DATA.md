# 資料分類與標註審查

## 分類原則

只有 data/approved 的照片能進入資料集。其他目錄不會被遞迴當成訓練來源。data/manifest.csv 是正式清單，圖片與標註必須和它一致。

- approved：沿用既有矩形標註或原來源「圖片/一般」的明確分類。這是來源分類與格式核對，不代表重新完成臨床覆核。
- pending_review/annotation：標註缺漏、衝突或同名拍攝的不同檔案版本，待人確認。
- pending_review/unknown_source：來源、正常／病灶狀態不明。
- pending_review/duplicate_variant：初次遷移時辨識的同名不同編碼候選。
- excluded/unclear：原專案已列為「不清楚的」影像，包括其他資料夾中的相同拍攝副本。
- excluded/blurry、unreadable、other：分別用於已確認失焦、無法讀取及其他原因。

沒有標註不等於正常。明確核對為正常後，可採用空白 YOLO 標註作為負樣本。待確認影像不會被自動補成負樣本。

## 本次分類

原始根目錄項目已搬到 archive/legacy，遷移清單記錄原始位置、大小及 SHA-256。原始 JPG、JSON、TXT、CSV 與壓縮包均保留。

同一份位元組內容合併成一筆照片紀錄。清單 original_paths 保留所有來源位置。同名但內容不同的照片不視為新增獨立個案；優先保留原 YOLODataset 版本，其餘待確認。同名不代表必然相同照片，因此沒有刪除。

本次整理後是 91 筆不同內容的 RGB 檔案：24 筆可用（15 筆病灶、9 筆一般），62 筆待確認，5 筆排除。原 YOLODataset 的 17 份框選標註中包含相同內容的照片，所以去重後的數量不同。數量變更後以 audit 輸出為準。

三份原本不清楚的拍攝有不同編碼副本，所以排除區實際有 5 個不同內容檔案。歷史 migration_complete.json 記錄初次遷移數量；後續重複候選調整記錄在 data/reviews。

## 審查清單欄位

| 欄位 | 意義 |
|---|---|
| image_id / sha256 | 穩定圖片識別與完整性驗證 |
| image_path / annotation_path / yolo_path | 目前圖片、原始標註、YOLO 標註位置 |
| status / label_state | 使用狀態與 positive／negative／unknown |
| candidate_group | 從檔名推測的分組，不能當成已確認病人身分 |
| subject_id / group_verified | 經提供者確認的匿名個案編號與確認狀態 |
| reviewer / reason / updated_at | 核對人、原因與處理時間 |
| original_paths | 原始來源的 JSON 陣列 |

不要只用檔案總管搬動 active 資料。請使用 review 指令同步清單和檔案；審查後舊資料集會失效，必須重新 build。

例：確認既有病灶標註及匿名個案：

    .\.venv\Scripts\python.exe -m src review 圖片ID --status approved --label positive --reviewer 核對者 --reason "已核對來源與標註" --subject-id case001

例：確認正常照片：

    .\.venv\Scripts\python.exe -m src review 圖片ID --status approved --label negative --reviewer 核對者 --reason "資料提供者確認為正常" --subject-id case002

例：隔離不適合訓練的照片：

    .\.venv\Scripts\python.exe -m src review 圖片ID --status excluded --category blurry --label unknown --reviewer 核對者 --reason "拍攝失焦"

待確認的陽性照片需先用 LabelMe 補矩形標註，再透過 --annotation 指定專案內 JSON 路徑。允許標籤 Phlebits、phlebitis、靜脈炎，統一轉為類別 0；其他類別或非矩形將被拒絕。

## 方向、編碼與資料切分

建立訓練資料時，僅對產生的副本進行 EXIF 方向校正、RGB 轉換及 JPEG 品質 95 重新編碼，並同步旋轉／翻轉框座標。原始檔案保持不變。紀錄同時保存原圖雜湊與產生副本雜湊，避免訓練框架自行修復 JPG 後破壞重現性。

三折資料各自含 train/val；同一分組不會同時出現在同一折的兩邊。不同折重用照片是交叉驗證的正常行為。正式資料需核實匿名個案；展示模式使用候選代碼，不能排除不同代碼其實屬於同一病人的可能性。

目前沒有獨立、未用於調參的臨床測試集。之後新增個案時應另保留獨立測試資料，不能把最高分驗證折當成最終測試結果。

逐張待辦與圖片連結見 [審查待辦](DATA_REVIEW.md)。
