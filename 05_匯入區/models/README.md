# 模型包

每個模型包一個資料夾，例如 `models/efficientnet_外部A/`，裡面一定要有 `package.json`（列出每個檔案的 SHA-256）。匯入後是一個**新的、未評估的版本**，不會自動用於本地模擬或 LINE。

匯入方式：工作台 → 模型與實驗 →「匯入模型」→ 選模型包 → 掃描並預覽 → 確認。

## 可以匯入的四種模型包

| 用途 | `source.type` | 適用情況 | 匯入後 |
|---|---|---|---|
| 外部訓練的模型 | `external` | 在別台電腦或 Colab 自己訓練的模型 | 工作台重建模型、登錄為新版本；**一定要用本專案資料評估後才能啟用** |
| 本專案模型的副本 | `project_artifact` | 把本專案已登錄的版本搬到另一台電腦 | 新版本，內容與設定必須和來源完全相同 |
| 官方基礎權重 | `official` | EfficientNet／DINOv2 官方權重 | 放進受保護的基礎權重區 |
| 續訓 checkpoint | `project_job` | 本專案訓練工作的完整續訓檔 | 只能續訓，不能啟用為推論模型 |

## 外部訓練的模型（最常用）

**為什麼不能直接放 `.pt`？** `.pt`／`.pth` 是 Python pickle 格式，開啟時可以執行檔案裡藏的任意程式碼。所以工作台**不開啟任何外來的 `.pt`**，只接受純數字權重：`.safetensors`、`.json`、`.npz`（不允許 pickle）。

做法：

1. 在**訓練模型的那台電腦**上，用本專案的程式把自己訓練的權重轉成模型包：

   ```
   .\.venv\Scripts\python.exe scripts\model_package.py export --model efficientnet_b0 --weights D:\訓練\model.pt --out D:\匯出\efficientnet_外部A --training-data "岡山高醫 2026-09 照片 80 張，依個案分組，未含本專案驗證集"
   ```

   - `--model`：`efficientnet_b0`、`dinov2_small`
   - EfficientNet：`--weights` 給 `state_dict` 的 `.pt`，並加 `--label-scheme binary_v1`（二分類）或 `stage_v1`（分期三類）。
   - DINOv2：`--weights` 給含 `config.json`、`model.safetensors`、`classifier.npz` 的資料夾。
   - `--training-data` 必填：寫清楚用了哪些照片訓練。若和本專案的評估照片重疊，評估分數會偏高。
2. 把輸出的資料夾複製到這裡（`05_匯入區\models\`）。
3. 到工作台匯入。工作台會依官方架構重建模型、以 `strict` 方式載入權重；架構或類別數不符就拒絕，不會登錄。
4. 到「模型與實驗」用本專案資料評估這個版本。**沒有完整評估之前，不能啟用**（本地模擬與 LINE 都不行）。

自己修改了模型包裡的檔案後，執行 `scripts\model_package.py manifest <資料夾>` 重新計算 SHA-256。

範本：`../範本/package.json`。模型檔不納入 git。
