# 本地研究工作台操作與交接

更新：2026-10-01。本文件對應 `ASTRA_WORKBENCH_PROMPT.md` 的五模型擴充；2026-09-25 的 YOLO11n 紀錄保留為歷史資料。

## 啟動

2026-10-03 增量更新：前端已依功能拆分；資料審查採衍生 SQLite 索引，新增 inbox 照片／模型預覽與匯入。操作、責任與恢復方式見 [PERFORMANCE_IMPORTS.md](PERFORMANCE_IMPORTS.md)。啟動方式、資料根目錄與 LINE 分離架構保留。

這台電腦雙擊根目錄 **啟動研究工作台.cmd**，然後開啟 **http://127.0.0.1:8765**。
保留終端機視窗；Ctrl+C 停止網頁服務。開啟網頁不會自動訓練、切換模型或傳送 LINE 訊息。

```powershell
.\.venv\Scripts\python.exe -m src workbench --port 8765
```

換電腦時，安裝 Python 3.12、Node.js 22 以上，再執行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-workbench.ps1
```

安裝程式只使用專案 `.venv` 與 `web/node_modules`。新環境沿用 `setup.ps1` 的 PyTorch CUDA 安裝方式；既有可用環境保留 torch。沒有 NVIDIA GPU 的新環境可加 `-CpuOnly`，並在工作台明確選擇 CPU。日常啟動不需要 npm、不會再次下載套件。

若 port 被占用，可直接查看原工作台，或改 `--port 8766`。不要把管理 port 8765 接到公開 HTTPS tunnel。LINE 入口另用 `python -m src serve --port 8000`，帳號與手機驗收依原決定延後。

## 七個工作區

1. **總覽**：資料分類、已核對個案數、工作狀態。只有開始訓練或分析才占用計算資源。
2. **資料審查**：圖片方向已校正。新增、移動、縮放或刪除矩形，確認正負標籤，填審查者與原因再儲存。陰性不可有框；核准陽性必須有框。未知標籤不會被當陰性。
3. **模型與實驗**：模型目錄、建立實驗、工作監測、評估比較、模型版本、訓練曲線六個分頁。
4. **LINE 模擬**：選模型產物、合成使用者、裝置和情境，傳文字或照片。只有假傳送器，沒有真實 LINE 發送。
5. **案例與回歸**：有授權和用途才能回收圖片。人工確認後可加入待審區，或將真正外部新個案預留作獨立測試。
6. **設定與維護**：操作者（自行填寫、未經登入驗證）、運算鎖與 GPU／套件、到期清理預覽、LINE 接案停止、目前及歷史模型引用、操作稽核。
7. **垃圾桶**：工作、模型版本及稽核的移入／還原、容量、永久刪除預覽、逐項結果與中斷恢復；詳見 `TRASH_IMPLEMENTATION.md`。

## 資料分類、版本與個案

| 位置 | 用途與可否訓練 |
|---|---|
| `data/approved` | 經人工確認的可用圖片與標註 |
| `data/pending_review` | 缺標註、來源待查、重複候選；不參與訓練 |
| `data/excluded` | 模糊、不清楚、無法解碼或其他排除原因；不參與訓練 |
| `data/yolo/<版本>` | 固定圖片、標註、成員、群組與雜湊的不可變快照 |
| `data/independent_test` | 明確預留的外部資料；不拿來訓練或自動選模 |
| `archive` | 原始與歷史封存；不作執行入口 |

目前仍為 91 筆：24 approved、62 pending、5 excluded；24 approved 的個案身分尚未核對。這些資料只能明確選擇研究展示模式。新增資料前仍應查看網頁即時統計。

備註修改不會破壞快照。實質標註或個案修改會保留舊版本並標記不適用；撤回／到期刪除相關副本時標記不可重現。篡改快照圖片或標註會被完整性檢查拒絕。並行審查採 revision 檢查、單一寫入鎖和復原日誌；遇到衝突須重新載入。

預設三折分組。折數／種子可透過 API 設定，須有足夠群組與正負類別。既有 24 張不強制切出獨立測試集。分類和偵測共用已确认正負標籤的快照，分類使用完整圖片，不使用病灶真實框裁切。

## 建立、停止與續訓

在「模型與實驗 → 建立實驗 → 建立資料快照」建立快照；新快照不會自動選取或建立工作。再手動選模型、fold、GPU 或 CPU、訓練參數及研究展示確認。開始前可展開「送出前檢視每個工作設定」。比較佇列最多五種不同模型，固定同一切分，依序執行。重複送出相同 idempotency key 不重複建立工作。

| 方案 | 預設策略與輸出 |
|---|---|
| YOLO11n／11s | 官方預訓練微調、病灶框；120 epochs 上限、patience 25 |
| YOLO26s | 真實官方 YOLO26s；實際 loss 包含 L1，沒有 YOLO11 DFL；可選 NMS／端到端推論 |
| EfficientNet-B0 | 固定主幹及 BatchNorm，只訓練分類頭；可選最後階段解凍，20 epochs／patience 5 |
| DINOv2 ViT-S/14 | 官方凍結 backbone、eval、CLS 特徵384維；只擬合 logistic regression，沒有 epoch 續訓 |

分類使用 RGB、完整圖片 padding 至224與 ImageNet normalization。DINOv2 標準化只 fit 當折 train；模型、均值、尺度和分類器以受控本地檔案保存。快取依圖片內容、權重、前處理和 pooling 隔離。

YOLO optimizer=auto 時不接受 lr0／momentum。AMP 預設關閉；勾選時明示框架可能下載 YOLO26n 做 AMP 自檢，實際訓練仍使用所選模型。`nbs` 是框架名義 batch，並非任意 gradient accumulation。要求參數和實際有效參數都保存在工作詳情。

每個長工作是獨立 Windows 背景程序，PID、建立時間、命令及 job ID 共同識別。狀態包含 queued、running、cancelling、cancelled、failed、interrupted、succeeded。重新整理／網頁重啟不會重複啟動訓練；已運行 worker 可繼續並被接回。停止先合作式取消，超過30秒才終止已確認歸屬的程序樹。資源鎖直到運算結束才釋放。

續訓要求原設定、原快照及完整 checkpoint；沒有完整 checkpoint 就建立新實驗。以產物權重開始新實驗與續訓分開。新工作輸出保存在新目錄，不覆蓋前一次實驗。DINOv2 solver 只能重新擬合。

全機一次一個模型計算。若 LINE 正在占用資源，在設定頁按「停止新接案並釋放模型」，現有案件完成後才釋放；重啟 LINE 服務才恢復接案。

## 評估、比較與模型引用

訓練成功先登錄候選模型，再排入評估。卡片顯示待評估／評估中／成功／失敗／不適用，未評估時沒有假分數。影像準確率是 `(TP+TN)/(TP+TN+FP+FN)`，附正確張數／有效張數；少於20張用整數百分比，其餘一位小數。

Precision、Recall、Specificity、F1、balanced accuracy、正常圖誤報率、多數類基準和拒答覆蓋率分開顯示。分母為零顯示 N/A。缺圖、解碼或推論失敗會使報告不完整，不能和完整資料排名。單張模型分數不是準確率、疾病機率或嚴重度。

偵測 AP 用低 conf 掃描，影像二元判斷用保存的接受門檻；兩者分欄。分類 mAP 不適用。同圖比較中的金色框為人工框、青綠框為模型框。训练集擬合表現使用 eval／無隨機增強，僅作過擬合檢查，不當驗證分數。

OOF 表單、專用 API 與彙整函式已移除；原有報告、fold 切分及指標公式保留。評估比較可精確篩選模型方案，不合併同一模型的多次評估；圖片來自當次報告，缺圖不替換為目前資料。模型、報告、圖片與頁碼保存在網址。

模型版本保存在 `models/versions`，`models/references/local.json` 與 `line.json` 分開。選用本地模擬不等於啟用 LINE。更改判斷／品質設定會複製新版本並重新評估；舊報告不被冒用。切換或回復只更新完整驗證後的原子引用。真實 LINE 啟用由操作者明確按鈕確認，本次未執行。

## 模擬與固定回歸

結果狀態為 suspected、not_detected、needs_review、quality_rejected；執行錯誤另記。分類不產生偽造框。低信心候選和品質規則需明確開啟；品質預設只提示，尚無可靠目標內容辨識。

模擬器可重播／重送、連續上傳、撤回、佇列已滿、缺模型、下載失敗、逾時、通知失敗和 reply／push。事件面板保存 trace、設定、输入雜湊、候選框、結果、耗時與回覆 payload；`delivery_unconfirmed` 不自動重試。手機呈現是瀏覽器近似，真實 LINE 客戶端未驗收。

已確認案例可指定預期狀態、可選耗時上限及對話重播。API 另接受 `score_range: [0,1]` 等容許範圍。對話 JSON 範例：

```json
[
  {"type":"unsend","message_id":"sample","at":100,"expected":"cancelled"},
  {"type":"reserve","event_id":"event-1","message_id":"sample","at":101,"expected":"cancelled"}
]
```

支援 reserve、unsend、complete、text；每個事件可指定 at、event_id、message_id、user、expected。案例每次修改有 revision。人工標籤、功能一致性、分數容許範圍與耗時分開記錄；相同案例版本相對上一次回歸列出 improved／regressed／unchanged。歷史模型輸出不自動當真實標籤。

手動在案例頁觸發，或在有人工已確認案例時由成功評估自動排入。CI／命令列：

```powershell
.\.venv\Scripts\python.exe scripts/run_regression.py --artifact 模型版本ID --device cpu
```

功能失敗或執行錯誤回傳非零。回歸案例不是獨立測試，絕不自動部署。

## 保存與安全邊界

- LINE 原圖僅供記憶體分析；結果圖一小時。原既有 CLI 手動輸出由操作者管理。
- 模擬上傳與結果一小時，自動清理；不自動加入訓練。
- 新授權研究回收預設30天，須有用途和授權紀錄。到期後不可讀取；設定頁先看清理預覽，再明確清理。可提前撤回。
- 清理僅處理受管理副本，涵蓋關聯資料快照、特徵快取、評估疊圖及訓練／驗證圖片；模型權重與數值報告保留並標明重現限制。不能保證清除外部 LINE 副本，也不等於模型反學習。
- 既有病患資料、封存和模型不套用新30天期限。本次刪除驗收只操作合成測試資料。
- 管理 app 限 localhost Host／Origin、CSRF、上傳大小、解碼像素與受控路徑；無遠端登入部署功能。不要公開管理 app。
- 模型來源限定官方下載和受控本地版本；雜湊是完整性核對，不是任意模型反序列化安全保證。

## 架構與檔案

| 路徑 | 責任 |
|---|---|
| `web/src/main.tsx`、`extras.tsx`、`style.css` | React／TypeScript 六區介面 |
| `src/workbench/api.py`、`contracts.py` | 獨立管理 API、輸入契約與瀏覽器防護 |
| `jobs.py`、`worker.py`、`src/lock.py` | 持久工作、程序對帳、取消、單機計算互斥 |
| `adapters.py`、`metrics.py`、`registry.py` | 五模型實作、評估、不可變版本與引用 |
| `simulation.py` | 共用 LINE 規則、假傳送、固定案例回歸 |
| `research.py`、`lifecycle.py`、`storage.py` | 授權回收、匯入、撤回、SQLite 與稽核 |
| `src/data` | 審查交易、EXIF／LabelMe／YOLO、資料快照 |
| `src/line_bot` | 真實 LINE adapter；與管理 app 隔離 |
| `runtime/workbench` | 工作台 SQLite、短期／研究資產與 DINO 特徵 |
| `runs/workbench/jobs`、`evaluations` | 各工作要求、日誌、checkpoints 與評估 |

實際驗收證據見 [WORKBENCH_ACCEPTANCE.md](WORKBENCH_ACCEPTANCE.md)。

## 2026-09-29 七項改善

圖片比例、已審查篩選、曲線、工作監測、維護稽核、總覽導覽及模型產物呈現已更新。完整變更、相容性與驗收證據見 [七項改善紀錄](WORKBENCH_SEVEN_ITEMS.md)。
