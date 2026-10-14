# 工作台實作與驗收紀錄

日期：2026-09-28。範圍：`ASTRA_WORKBENCH_PROMPT.md` 所列本地工作台；真實 LINE 帳號及手機串接依使用者決定延後。

## 完成項目

| 工作 | 實作與證據 |
|---|---|
| 原 CLI／資料保留 | audit：91張、24可用／62待審／5排除、0錯誤；CLI help 與原測試繼續可用 |
| 逾時與通知失敗 | 假 predictor 同時推論數保持1；通知失敗不釋放仍在運算的資源 |
| 審查與快照 | revision、單寫入者、失敗復原、EXIF矩形往返、備註與不可變快照分離、篡改拒絕 |
| 作業管理 | 背景程序、重啟對帳、重送去重、PID重用防護、取消、原設定續訓；續訓寫新目錄 |
| 五模型 | 五條路徑均有實際有限訓練／擬合、登錄、真實評估、重新載入與模擬推論 |
| 指標與版本 | 二元準確率與分母、拒答覆蓋率、AP分欄、同圖比較（OOF 入口於 2026-10-01 移除，歷史報告保留）、設定改變不沿用報告、原子引用 |
| 分類契約 | EfficientNet凍結BN不更新；DINO訓練折標準化、CLS特徵快取版本隔離、pipeline重新載入 |
| LINE 模擬 | 文字／圖片、合成使用者、事件重播／去重／撤回、失敗情境、傳送與推論狀態分離 |
| 案例與期限 | 授權回收、案例revision、人工標籤、回歸、待審／獨立資料匯入、30天／1小時、撤回與受管理副本清理 |
| 網頁與環境 | React／TypeScript六工作區、Windows啟動入口、限定專案依賴、手冊與目錄README |

## 自動化測試

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

最終結果：**62 passed**。一項 Starlette TestClient 的 httpx 相容層棄用提示，不影響本次測試。包含原18項測試；其中「修改即時 manifest 使所有快照失效」的舊規則改成新快照保留完整性，另測試實質審查變更撤銷及快照篡改。

測試檔：`tests/test_workbench.py`、`test_workbench_acceptance.py`、`test_lifecycle.py` 與既有資料／LINE測試。全機鎖測試須在没有其他模型運算時執行；曾與瀏覽器推論並行而被互斥鎖正確拒絕，改為循序驗收後通過。

```powershell
cd web
npm.cmd run build
node browser-smoke.mjs
```

TypeScript＋Vite正式建置成功。Edge headless實際操作了總覽、資料審查草稿矩形、模型頁、DINO隱藏epochs、未選資料集錯誤、評估疊圖、模擬文字與圖片、合成研究案例保存／撤回、API失敗提示及390px手機版面。頁面JavaScript錯誤0；操作證據見 [workbench-browser-evidence.json](workbench-browser-evidence.json)。原資料的矩形草稿沒有儲存。

網頁驗收曾發現忙碌時撤回先改期限、後取得運算鎖的中間狀態。已改為先取得計算與資料寫入鎖再修改期限；新增回歸測試並重跑完整瀏覽器流程通過。測試只撤回本次生成的合成幾何圖片，沒有刪除既有病患或封存資料。

環境 `pip check`：**No broken requirements found**。Python依賴固定於 `requirements.lock.txt`；前端固定於 `web/package-lock.json`。CUDA／CPU版torch由原 `setup.ps1` 管理。

## 五模型真實有限訓練

共同資料快照：`demo_20260927T142542132755Z`、fold0、train17／val7；驗證為4陽性＋3陰性，個案尚未核對。YOLO輸入320、batch小量、2epochs；EfficientNet2epochs；DINO固定主幹＋有限迭代分類器。**這是流程smoke test，沒有證明收斂、臨床效能或新病人泛化。**

| 方案 | 真實流程 | 本次驗證影像準確率 |
|---|---|---|
| YOLO11n | 訓練→保存→評估→重載→模擬通過 | 43%（3/7） |
| YOLO11s | 同上 | 29%（2/7） |
| YOLO26s | 真實26s，實際L1 loss，完整路徑通過 | 43%（3/7） |
| EfficientNet-B0 | 固定主幹＋分類頭，完整路徑通過 | 71%（5/7） |
| DINOv2 ViT-S/14 | 官方特徵＋logistic regression，完整路徑通過 | 57%（4/7） |

訓練、評估與模擬job ID、各產物名稱和TP/FN/FP/TN見 [workbench-smoke.json](workbench-smoke.json)。每個工作保存自己的要求／有效參數、日誌及產物；早期權重下載失敗及取消也保留追蹤，重試後成功，不以其他模型代替。

這組數值與舊成果報告85%不能直接比較：舊報告該值是Precision範圍；這裡是僅7張驗證影像的Accuracy，且資料與訓練配置不同。分類的mAP顯示不適用。這些短程結果不可用來宣稱哪個模型最適合部署。

## 保存與原資料核對

- 重新核對封存：**166個檔案，0雜湊差異**，見 [workbench-archive-check.json](workbench-archive-check.json)。
- 原 `models/selected/best.pt` 與原metadata雜湊一致；新增模型皆為候選，沒有建立LINE active reference，也沒有傳真實訊息。
- 既有91筆資料分類與原始圖不變。研究回收的新增案例明確標為合成，驗收後撤回。
- 固定回歸工作保留人工標籤、功能、容許條件、耗時與基準差異；合成案例不能作模型效能證據。實際回歸執行見 [workbench-regression-evidence.json](workbench-regression-evidence.json)。

## 仍需真實資料／外部環境完成的工作

1. LINE Channel secret、access token、公網HTTPS与實際手機驗收尚未進行。管理端不可接公開通道。
2. 現有24張approved的個案身分仍待資料提供者核對；目前無足夠已核對外部資料建立正式獨立測試集。
3. 五模型短程訓練只驗證功能。正式模型效能、品質拒答規則、跨個案泛化與所需資料量尚未驗證；不提供嚴重度分級。
4. 現有GPU環境已驗收；完整安裝腳本未在另一台全新Windows電腦實跑。公開登入管理與多人部署不在本地單機範圍。

操作方式、架構、保存政策與限制見 [WORKBENCH.md](WORKBENCH.md)。
