# 本地訓練、評估與模型選定

## 環境

本機已確認 NVIDIA RTX 5050 Laptop GPU、約 8 GB VRAM。使用 Python 3.12、PyTorch 2.13.0+cu130、torchvision 0.28.0+cu130。具體版本見 environment.json 及 requirements.lock.txt。

工作台支援 EfficientNet-B0 及 DINOv2 ViT-S/14＋logistic regression，都是整張照片分類。YOLO 已在 2026-11 移除，當時成績見[YOLO 歷史成績](../驗證報告/YOLO歷史成績.md)。各方案實作、參數、續訓和評估差異見 [工作台手冊](WORKBENCH.md)。

CUDA 不可用時會明確失敗，不會自動改用 CPU；要用 CPU 請在建立實驗時選擇。

## 任務、快照與標籤方案

快照在「模型與實驗 → 新增快照」建立。該分頁也列出既有快照與狀態（有效、已被取代、已撤回）；「建立實驗」只列出有效快照。

每個快照固定以下內容（`dataset_version.json` 的 schema 3）：

- 一個任務：`binary_classification` 或 `stage_classification`；
- 類別對照與方案版本：`binary_v1`（negative=0、positive=1）或 `stage_v1`（normal=0、stage1=1、stage2=2）；
- 成員、分組、審查版本與證據雜湊。

```
.\.venv\Scripts\python.exe -m src build --demo --task stage_classification
```

- 分類快照的正規化影像每張只存一份，各折只列出成員。
- 新快照放在 `data/snapshots/`；2026-11 以前的快照留在舊位置，工作紀錄照舊讀取。
- 類別或分組不足時會清楚拒絕，不會複製樣本或偽造分組。

沒有方案欄位的舊模型**永遠解讀為二分類**；positive=1 不會被當成第一期。schema 2 的舊快照不能再使用。

模型與方案的對應：

- EfficientNet-B0 與 DINOv2 可用於二分類或分期。分期時輸出三類 softmax，以最高分類別判定；DINOv2 分期只支援 lbfgs（多項式邏輯斯迴歸）。

評估指標依任務而不同：

- 分期評估提供混淆矩陣、各類 precision／recall／F1、macro F1、樣本數，以及未能判定數。
- 二分類評估沿用敏感度與特異度。
- 偵測評估另報 mAP。

不同任務或不同標籤方案的報告不會並列比較。LINE 只向病患顯示「疑似／未達門檻」；分期類別與各類分數只在工作台與模擬器的工程資訊中顯示。

## 建立資料及訓練

訓練都在工作台操作，命令列只有資料檢查與建立快照：

    .\.venv\Scripts\python.exe -m src audit
    .\.venv\Scripts\python.exe -m src build --folds 3 --repeats 5
    .\.venv\Scripts\python.exe -m src build --task stage_classification --folds 2 --repeats 5

規則：

- `--demo` 只作流程展示，不能當正式成績。
- 前瞻名單裡的測試與校準病人不會進訓練快照。
- 建快照時會擋下：沒有病人分組、同一病人或近似照片跨折、某一折沒有正常病人。
- 訓練跑滿固定輪數，驗證折不用來挑模型。
- 二分類的門檻用訓練折內的預測決定，評估時不會重挑。
- 每個模型都要和基線（多數類、色彩直方圖、DINOv2 最近鄰）一起比較；基線不能啟用。
- 隨機標籤對照只驗證流程，模型不能啟用。
- 目前第一期只有 2 位病人，分期只能用 2 折。

## 中斷續訓與評估

續訓與評估都在工作台操作。續訓鎖定原快照與參數；訓練完成後會自動排入評估，報告放在 `runs/workbench/evaluations/`。模型不會自動啟用，要由人在「模型版本」切換。

## 匯入在別處訓練的模型

在別台電腦或 Colab 訓練的模型可以匯入，但**不能直接放 `.pt` 檔**：`.pt`／`.pth` 是 pickle 格式，開啟時可以執行檔案中的任意程式碼。

1. 在訓練的那台電腦，用本專案程式把**自己訓練的**權重轉成 safetensors 模型包：

       .\.venv\Scripts\python.exe scripts\model_package.py export --model efficientnet_b0 --weights D:\訓練\model.pt --out D:\匯出\efficientnet_外部A --training-data "訓練資料的來源、日期、張數、是否依個案分組"

   另加 `--label-scheme binary_v1` 或 `stage_v1`。
2. 把輸出資料夾複製到 `05_匯入區/models/`，在「模型與實驗 → 匯入模型」預覽並確認。
3. 工作台依官方架構重建模型、以 strict 方式載入權重，登錄成新的、未評估的版本（`extra.source = external`）。架構或類別數不符時拒絕。
4. 用本專案的快照評估。**沒有完整評估之前，本地模擬與 LINE 都不能啟用**。

外部模型可能用過本專案評估集裡的照片訓練，評估分數因此可能偏高；`--training-data` 請寫清楚，模型說明卡會顯示。細節見 [05_匯入區/models/README.md](../../05_匯入區/models/README.md)。

## 預測與 LINE

    .\.venv\Scripts\python.exe -m src predict data/approved/images --allow-demo

命令列使用「本地模擬」模型（`models/references/local.json`），結果 JSON 存在 runs/prediction_...。LINE 使用 `models/references/line.json`。兩者都只做整張照片分類，不標出位置。

程式使用作業系統鎖避免訓練、命令列預測與 LINE 同時占用 GPU。請停止 LINE 再訓練；啟動 LINE 前等候訓練完成。

## 測試

    .\.venv\Scripts\python.exe -m pytest -q
