# 本地訓練、評估與模型選定

## 環境

本機已確認 NVIDIA RTX 5050 Laptop GPU、約 8 GB VRAM。使用 Python 3.12、PyTorch 2.13.0+cu130、torchvision 0.28.0+cu130、Ultralytics 8.4.161。具體版本見 environment.json 及 requirements.lock.txt。

舊 CLI 保留 YOLO11n；工作台另支援 YOLO11s、YOLO26s、EfficientNet-B0 及 DINOv2 ViT-S/14＋logistic regression。各方案實作、參數、續訓和評估差異見 [工作台手冊](WORKBENCH.md)。預訓練權重與訓練後產物不可混用。

YOLO 預設 imgsz=640、batch=4、最多120 epochs、patience=25、seed=42、workers=0、amp=false。工作台可明確開啟 AMP 並同意框架自檢下載；分類有各自設定。CUDA 不可用會報錯，只有明確選擇 CPU 才用 CPU。

## 建立資料及訓練

    .\.venv\Scripts\python.exe -m src audit
    .\.venv\Scripts\python.exe -m src build --demo
    .\.venv\Scripts\python.exe -m src train --demo --epochs 2
    .\.venv\Scripts\python.exe -m src train --demo --fold 0
    .\.venv\Scripts\python.exe -m src train --demo --fold 0 --no-color

最後兩個指令為保守增強與關閉色彩擾動的比較。使用相同資料版本、折數、種子及最多輪數。可用 --batch 2 降低顯示記憶體需求。

若要完成所有折的實驗，分別執行 --fold 0、--fold 1、--fold 2，報告各折結果及變動，不只挑最高分。正式個案資訊確認後 build/train 不加 --demo；未核對資料會被阻擋。

資料集每次建立都有新版本；預設 train 使用最新資料集。重現舊實驗時用 --dataset 指定該次 experiment.json 記錄的資料集。移動專案位置後需重建虛擬環境並重新 build，不能沿用舊機器的資料集絕對路徑。

## 中斷續訓

    .\.venv\Scripts\python.exe -m src train --demo --resume runs/實驗名稱/weights/last.pt

續訓必須使用相同資料清單與原始切分；程式會自動讀取原實驗的資料集。沒有新 epoch 的已完成模型不能用 resume 再開一輪。中斷發生於第一個 checkpoint 寫出之前，則需重新開始。

YOLO 完整訓練會留下 best.pt、last.pt、results.csv、曲線與 experiment.json。工作台續訓鎖定原快照與參數；修改即時審查備註不改動完整歷史快照。EfficientNet 保存分類 state 與 optimizer checkpoint；DINOv2 solver 重新擬合，無 checkpoint 續訓。

## 評估與選定

    .\.venv\Scripts\python.exe -m src evaluate --weights runs/實驗名稱/weights/best.pt --fold 0
    .\.venv\Scripts\python.exe -m src select --weights runs/實驗名稱/weights/best.pt --evaluation runs/評估名稱

evaluate 產出：
- detection_metrics：Precision、Recall、mAP50、mAP50–95 等框選指標。
- image_level：是否出現任何框的影像層級 TP/FN/FP/TN、召回與正常影像誤報率。
- error_examples：沒有框的陽性照片與有框的正常照片。
- validation：PR、混淆矩陣與標註／預測對照。
- images：各影像的分組、輸出框數與推論時間。

影像層級有框不代表框的位置一定正確，因此須連同定位指標及預測對照查看。七張或十幾張照片上的數字會大幅波動，不能直接外推醫院使用表現。

AP 評估使用 conf=0.001；展示預設 conf=0.5。更改展示門檻後，請以相同 --confidence 重跑 evaluate，再 select；不能把門檻數值當作嚴重度。

select 只接受同一份權重的評估紀錄，保存權重雜湊與模型版本，不自動把任何新訓練的模型切換上線。

## 預測與 LINE

    .\.venv\Scripts\python.exe -m src predict data/approved/images --allow-demo

預測圖片與 JSON 存在 runs/prediction_...。LINE 與命令列共用同一個分析模組。

程式使用作業系統鎖避免訓練、命令列預測與 LINE 同時占用 GPU。請停止 LINE 再訓練；啟動 LINE 前等候訓練完成。

## 測試

    .\.venv\Scripts\python.exe -m pytest -q
    .\.venv\Scripts\python.exe scripts/check_resume.py

第二個指令會實際開始一個四輪小訓練，在第一個 checkpoint 中斷，再恢復至第四輪；不是一般單元測試，會產生 runs 紀錄。


## 一次完成三折設定比較

    .\.venv\Scripts\python.exe scripts/run_experiments.py --demo

逐折執行 baseline 與 no_color，共六次訓練及評估。每次最多 120 輪，使用相同初始權重及種子；模型版本維持 YOLO11n。比較紀錄位置由 runs/latest_comparison.json 指向。

選定規則事先固定：僅比較 fold 0 的兩個設定，選 mAP50–95 較高者，平手選正常影像誤報率較低者。其他兩折完整列出結果及波動，不以最高分折代替獨立測試集。選定只是本地研究展示用模型，不表示通過臨床效能門檻。

本機影像、分組與資料量尚不足以支持實際醫療判斷。程式實作完成與模型辨識能力達標是兩個不同的驗收項目。
