# 資料分類與標註審查

## 分類原則

只有 data/approved 的照片能進入資料集。其他目錄不會被遞迴當成訓練來源。data/manifest.csv 是正式清單，圖片與標註必須和它一致。

- approved：沿用既有矩形標註或原來源「圖片/一般」的明確分類。這是來源分類與格式核對，不代表重新完成臨床覆核。
- pending_review/annotation：標註缺漏、衝突或同名拍攝的不同檔案版本，待人確認。
- pending_review/unknown_source：來源、正常／病灶狀態不明。
- pending_review/duplicate_variant：初次遷移時辨識的同名不同編碼候選。
- excluded/unclear：原專案已列為「不清楚的」影像，包括其他資料夾中的相同拍攝副本。
- excluded/blurry、unreadable、other：分別用於已確認失焦、無法讀取及其他原因。

沒有標註不等於正常。待確認影像不會被自動補成負樣本。

## 本次分類

原始根目錄項目已搬到 archive/legacy，遷移清單記錄原始位置、大小及 SHA-256。原始 JPG、JSON、TXT、CSV 與壓縮包均保留。

同一份位元組內容合併成一筆照片紀錄。清單 original_paths 保留所有來源位置。同名但內容不同的照片不視為新增獨立個案；優先保留原 YOLODataset 版本，其餘待確認。同名不代表必然相同照片，因此沒有刪除。

本次整理後是 91 筆不同內容的 RGB 檔案：24 筆可用（15 筆病灶、9 筆一般），62 筆待確認，5 筆排除。原 YOLODataset 的 17 份框選標註中包含相同內容的照片，所以去重後的數量不同。數量變更後以 audit 輸出為準。

三份原本不清楚的拍攝有不同編碼副本，所以排除區實際有 5 個不同內容檔案。歷史 migration_complete.json 記錄初次遷移數量；後續重複候選調整記錄在 data/reviews。

## 審查清單欄位

| 欄位 | 意義 |
|---|---|
| image_id / sha256 | 穩定圖片識別與完整性驗證 |
| image_path / annotation_path | 目前圖片、舊病灶框標註位置（保留，不再使用） |
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

## 任務化標籤與資格（2026-10 起）

規則集中於 `src/data/tasks.py`，查詢索引、快照建立、訓練前檢查與 API 都使用同一份規則。

| 概念 | 保存位置 | 說明 |
|---|---|---|
| 二分類 | `label_state` | positive／negative／unknown，沿用舊語意 |
| 分期 | `stage_label`（`stage_v1`） | normal／stage1／stage2；空白＝未確認。使用者提供之規則，非已驗證臨床分級 |
| 品質／用途 | `quality_state`／`usage_state` | unusable、test_only、withdrawn 均不可訓練 |
| 證據與歷程 | `data/label_evidence/<id>.json` | 規則預填、人工審查、收件確認，各附來源與規則版本 |
| 顯示名稱 | `data/image_sources.json` | 來源檔名別名；改名不改 manifest，不使快照失效 |

舊資料列沒有分期時，已核准陰性視為 normal（證據標為 legacy_binary）。

- 每張照片列出兩個任務（二分類、分期）各自的可用狀態與不能使用的原因。
- 「可用資料」與「待人工審查」可以加上任務篩選。
- 已知限制：剛儲存的變更，任務資格要等背景完整性檢查完成才會更新；頁面上有提示。

## 單一工作區（2026-11 起）

資料審查只有一個工作區：整張照片分類（`cls_review`，正常／第一期／第二期／陽性未分期）。病灶框選已隨 YOLO 移除。

- `status` 只表示檔案存放位置：已確認 → approved；排除 → excluded；其餘 → pending_review。
- 有「待處理／已完成／排除」頁籤，以及標籤、來源、審查者篩選與進度條。
- 完成後可按「建立訓練快照」。
- 舊病灶框檔案原樣留在 `annotations/`，跟著照片一起搬移，但系統不再讀取。

### 遷移

`python -m src migrate-tasks` 把舊資料列改為單一工作區，可重複執行：

- 寫入前先把 manifest 複製到 `04_備份/修改前副本/manifest/`，並在 `data/migrations/` 留下紀錄；
- 接著套用已授權的檔名規則；
- 最後替非岡山高醫但檔名相同格式的照片加入「預填」，仍需人工確認。

### 岡山高醫照片依檔名自動分類（授權，免逐張審核）

專案負責人 2026-10-14 授權使用檔名規則，2026-10-16 更新為 `gangshan_filename_v3`：LH／RH／LL／RL 只是部位，分期取部位後的數字（0＝正常、1＝第一期、2＝第二期）；檔名可用 11 位數開頭。授權紀錄在 `02_主程式碼/configs/import_sources.json`。

- 直接依檔名完成分類。
- 每次套用都寫入審查紀錄，來源標記為 `authorized_filename_rule`。
- 人工結果、與既有標籤衝突者、已排除照片（04「不清楚」）都不會被覆蓋。
- 匯入外部來源後會自動套用；維護時可用 `python -m src imports apply-rules` 手動重跑（介面不再提供按鈕）。

## 外部來源（岡山高醫）

### 每日新增照片

1. 把新照片放進 `05_匯入區\岡山高醫\`，可以建新的子資料夾（例如 `17\`）。檔名維持 `日期_病歷號_部位_分期_序號.jpg`，部位為 LH／RH／LL／RL。（2026-10-17 以前這個資料夾在桌面，已整個搬到 05_匯入區。）
2. 資料審查 →「外部來源比對與補入」。只有一個來源時會自動選好，接著按「掃描並比對」。
3. 輸入「確認匯入」並送出。

已匯入過的照片以 SHA-256 判斷，不會重複匯入。新照片會自動完成分類並自動分組。完成畫面會顯示本次新增張數和待框選張數。

外部資料夾只能透過 `configs/import_sources.json` 明列，並以唯讀方式掃描；路徑可寫相對於工作區根目錄（目前是 `05_匯入區/岡山高醫`），整個工作區複製到別台電腦後不用改。要補入的照片先複製到 `03_模型與影像資料/runtime/imports/external/`，再走一般匯入流程。CLI 指令：

```
.\.venv\Scripts\python.exe -m src imports external-scan --source gangshan
.\.venv\Scripts\python.exe -m src imports external-commit --id <操作ID>
```

網頁入口在「資料審查 → 外部來源比對與補入」。比對規則如下：

- 以 SHA-256 判斷是否重複；不同的檔案再比對 EXIF 校正後的像素雜湊，近似重複只列為候選。
- 已存在的照片只補記顯示名稱。
- 缺少的照片走既有匯入流程補入。
- 檔名分期只作為「規則預填」，需人工逐張或批次確認（批次確認會略過有衝突或有同名不同內容版本的照片）。

第一次補入的結果見 [補入紀錄](../驗證報告/verification/2026-10-13_岡山高醫補入/gangshan-import-2026-10-13.md)。

## 其他來源的照片

放在 `05_匯入區/photos/<批次名稱>/`，到資料審查按「匯入照片」→ 掃描並預覽 → 確認。不套用岡山高醫檔名規則，匯入後一律是「待人工審查」，標註只當作候選。詳見 `05_匯入區/README.md`。
