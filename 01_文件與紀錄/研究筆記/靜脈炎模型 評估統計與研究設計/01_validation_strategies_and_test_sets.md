# 驗證策略、獨立測試集與外部驗證：極小、叢集化醫療影像分類資料（靜脈炎照片）

> 研究筆記 01。存取日期（所有來源）：2026-10-30。
> 專案前提：研究原型、非臨床診斷。現況約 120 張照片 / 14 位病人（binary：47 陽性、9 normal；staging：normal 9 / stage1 23 / stage2 24；約 24 張有病灶框）。每位病人貢獻多張照片（不同日期、左右手）。標註：醫院照片依檔名規則自動標記，LINE 公開上傳照片人工複核，單一標註者，無 inter-rater agreement。未來目標約 1,000 張，三類平衡，約 50/200/300+ 位病人。
>
> 來源分級：[A] 官方 / 法規 / 報告標準（TRIPOD+AI、TRIPOD-Cluster）；[B] 系統性回顧 / 統合分析 / 頂級期刊或會議；[C] 其他同儕審查；[D] 預印本；[E] 部落格 / 程式碼 / 官方軟體文件（scikit-learn 文件依指示標 [E]）。
> 結論標籤：**[研究證據]** = 有文獻直接支持；**[業界慣例]** = 常見作法或經驗法則；**[推論]** = 本筆記根據文獻與本專案條件所做的推論。
> 「病人層級切分 / 外部驗證」欄位：說明每個被引用的實證研究有沒有依病人切分、有沒有外部驗證。
> 計算值：Wilson CI、Buderer 樣本數、Newcombe C-statistic SE、design effect 都是本筆記用 Python 自行計算（腳本見文末附錄說明），屬 **[推論/計算]**，公式來源另外標示。

---

## Q1. n=14 位病人、照片叢集化時，各種驗證法的偏差與變異比較（grouped k-fold、repeated grouped CV、nested CV、LOGO、bootstrap .632/.632+、Harrell optimism bootstrap）

### Takeaway
14 位病人的情況下，**每一種**重抽樣估計都會有極大的變異。Varoquaux（2018）在 n=100 時的誤差棒已約 ±10%，而且 fold 之間的標準誤會低估真實不確定性。Bengio & Grandvalet（2004）證明 k-fold CV 的變異**不存在**通用的不偏估計量。因此現階段的重點不是挑出「最準」的估計方法，而是：(1) 一律以病人為單位切分；(2) 重複多次、用 pooled 預測呈現分布；(3) 預先固定超參數，或用 nested CV 避免選模偏差；(4) 只報告「可行性訊號」，不報告「效能數字」。Bootstrap 類方法（.632+、Harrell optimism）必須**以病人為抽樣單位**，而且要**依類別分層抽病人**，否則很多 bootstrap 樣本會完全沒有 normal 病人。

### Cited Findings

**CV 變異與小樣本（整體）**
- [B][研究證據] Varoquaux G. (2018) "Cross-validation failure: Small sample sizes lead to large error bars." *NeuroImage* 180(Pt A):68–77. doi:10.1016/j.neuroimage.2017.06.061；預印本 arXiv:1706.07581。重點：
  - 神經影像常見的樣本數會造成很大的誤差棒，約「±10% for 100 samples」。
  - 跨 fold 計算的標準誤遠小於真實誤差棒。
  - 小樣本的缺點在「測試預測模型」時特別嚴重，因為無法靠大效應量彌補。
  - 誤差棒很大時，看起來的準確度提升可能只是 overfitting 加上發表誘因。
  - 實證性質：模擬加上公開 fMRI 資料；以受試者為單位評估；無外部驗證設計。
  - 來源：[arXiv](https://arxiv.org/pdf/1706.07581)、[ar5iv 全文](https://ar5iv.arxiv.org/html/1706.07581)
- [B][研究證據] Bengio Y, Grandvalet Y. (2004) "No Unbiased Estimator of the Variance of K-Fold Cross-Validation." *JMLR* 5:1089–1105。主定理：不存在對所有分布都有效的 k-fold CV 變異不偏估計量。忽略訓練/測試重疊所造成誤差相關性的 naive 估計量，可能嚴重低估變異。屬理論論文，不涉及病人切分 / 外部驗證。[JMLR](https://jmlr.org/papers/v5/grandvalet04a.html)
- [C][研究證據] Vabalas A, Gowen E, Poliakoff E, Casson AJ. (2019) "Machine learning algorithm validation with a limited sample size." *PLoS ONE* 14(11):e0224365. doi:10.1371/journal.pone.0224365。重點：
  - 模擬顯示，在「特徵選擇 / 調參與評估使用同一 CV」的流程下，K-fold CV 在小樣本會產生強烈偏差，到 1,000 個樣本時偏差仍存在。
  - Nested CV 與 train/test split 不論樣本大小都產生穩健、不偏的估計。
  - 在合併的訓練加測試資料上做特徵選擇，造成的偏差遠大於調參。
  - 文獻回顧發現，自閉症 ML 研究的樣本越小，報告的準確度越高。
  - 實證性質：模擬資料，無病人叢集，無外部驗證。
  - 來源：[PMC6837442](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6837442/)
  - 注意：此處的「K-fold 有偏差」是指流程中有資訊洩漏（選模 / 選特徵在外層），不是指 CV 本身。

**Bootstrap .632 / .632+**
- [B][研究證據] Efron B, Tibshirani R. (1997) "Improvements on Cross-Validation: The .632+ Bootstrap Method." *JASA* 92(438):548–560. doi:10.1080/01621459.1997.10474007。
  - 摘要：CV 幾乎不偏但變異可能很高；bootstrap 估計可視為 CV 的平滑版本；在 24 個模擬實驗中 .632+ 規則勝過一般 CV；對象是 0-1 loss 分類。
  - [PDF（UW 課程鏡像）](https://sites.stat.washington.edu/courses/stat527/s13/readings/EfronTibshirani_JASA_1997.pdf)
  - **驗證限制**：PDF 為掃描影像，本次無法擷取原文公式。下列公式依標準教科書記憶，**需對照原文確認**：
    - Err(.632) = 0.368·err̄ + 0.632·Err(1)
    - γ = no-information error rate
    - R = (Err(1) − err̄)/(γ − err̄)
    - Err(.632+) = (1−w)·err̄ + w·Err(1)，其中 w = 0.632/(1 − 0.368·R)
- [B][研究證據，經二手摘要] Molinaro AM, Simon R, Pfeiffer RM. (2005) "Prediction error estimation: a comparison of resampling methods." *Bioinformatics* 21(15):3301–3307. doi:10.1093/bioinformatics/bti499。
  - LOOCV 與 10-fold CV 對 LDA 的偏差最小。
  - LOOCV、5/10-fold CV、.632+ 的 MSE 最低。
  - **.632+ 在小樣本且訊號雜訊比高時偏差相當大。**
  - 樣本增加時各方法差異縮小。
  - 重抽樣流程內包含特徵選擇。
  - 實證性質：模擬加微陣列 / 蛋白體資料，每位受試者一筆觀測（無叢集）。
  - 註：本次只讀到摘要與二手摘要，未讀全文。[UCSF](https://cancer.ucsf.edu/node/197791)、[NCI 技術報告](https://brb.nci.nih.gov/techreport/prederr_rev_0407.pdf)
- [C][研究證據，經二手摘要] Kohavi R. (1995) "A Study of Cross-Validation and Bootstrap for Accuracy Estimation and Model Selection." *IJCAI-95*, pp.1137–1145（頁碼來源不一，另有 1137–1143）。
  - 二手摘要結論：用於模型選擇時，10-fold stratified CV 最佳。
  - 同年博士論文另指出 repeated 5-fold 在偏差與變異之間有良好折衷。
  - 這兩點需對照原文。無病人叢集。
  - [mlanthology](https://mlanthology.org/ijcai/1995/kohavi1995ijcai-study)

**Nested CV 與選模偏差**
- [C][研究證據] Varma S, Simon R. (2006) "Bias in error estimation when using cross-validation for model selection." *BMC Bioinformatics* 7:91。
  - 在 CV 外層調參時，CV 估計值集中在比真實誤差更小的位置。
  - Nested CV 給出「almost unbiased」的真實誤差估計。
  - 實證性質：模擬（null / non-null）加微陣列；無病人叢集議題。
  - [PMC1397873](https://pmc.ncbi.nlm.nih.gov/articles/PMC1397873)
- [C][研究證據] Krstajic D, Buturovic LJ, Leahy DE, Thomas S. (2014) "Cross-validation pitfalls when selecting and assessing regression and classification models." *J Cheminform* 6:10. doi:10.1186/1758-2946-6-10。
  - 列出四個陷阱：在 CV 之外選變數；只憑單次 CV 選模；把 CV 誤差當成預測誤差估計；只報告單次 nested CV 誤差。
  - 建議：選模用 repeated grid-search CV，評估用 **repeated nested CV**。
  - 分層：選模時不需要，評估時建議分層。
  - [PMC3994246](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3994246/)
- [C][研究證據；與上兩篇部分衝突] Wainer J, Cawley G. (2021) "Nested cross-validation when selecting classifiers is overzealous for most practical applications." *Expert Syst Appl* 182:115222（預印本 arXiv:1809.09446）。
  - 用 12 種演算法、115 個二元分類資料集實驗。
  - 「flat CV」（同一層 CV 同時調參與估計）的估計值有偏差，但用來**選演算法**時，所選演算法的實際品質與 nested CV 相近。
  - 前提是演算法的超參數相對少。
  - 實證性質：無病人叢集；資料集多大於本專案。
  - [UEA eprint](https://ueaeprints.uea.ac.uk/id/eprint/80048)
  - **調和**：Wainer & Cawley 談的是「選哪個演算法」；Varma & Simon / Vabalas 談的是「報告的效能數字是否偏樂觀」。要報告數字就需要 nested 或預先固定超參數；只是要挑模型，flat CV 可接受。

**Grouped splitter 官方行為**
- [E][官方文件] scikit-learn `StratifiedGroupKFold`：
  - 「Each group will appear exactly once in the test set across all folds」。
  - 在不重疊 group 的限制下盡量保持類別比例；「when there is a small number of groups containing a large number of samples the stratification will not be possible and the behavior will be close to GroupKFold」。
  - `shuffle=True` 時「can only shuffle groups that have approximately the same y class distribution, no global shuffle will be performed」。
  - 文件還寫道：「Stratification on the class label solves an engineering problem rather than a statistical one」。
  - 頁面列出 RepeatedKFold / RepeatedStratifiedKFold，**沒有** repeated 的 group 版本。
  - [scikit-learn docs](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html)

**叢集資料的 bootstrap**
- [A] TRIPOD-Cluster（叢集資料預測模型的報告指引，19 項 checklist）：適用於病人巢套於醫院 / 研究等叢集資料，並說明 bootstrap 與 CV 是最常見的內部驗證方法。本次只讀到摘要層級。[PMC9903176](https://pmc.ncbi.nlm.nih.gov/articles/PMC9903176)
- [D] 有預印本提出「cluster bootstrap optimism correction」，用於縱向資料的懲罰迴歸校準，與「每位病人多筆觀測」最接近。本次未讀全文。[arXiv:2101.04426](https://arxiv.org/pdf/2101.04426v1)
- [E] 實務說明頁指出 Harrell 式 optimism correction 假設觀測獨立，叢集 / 時序資料應改用 block（cluster）bootstrap。屬非同儕審查，僅作支持。[metricgate](https://metricgate.com/docs/apparent-vs-optimism-corrected/)
- [B][研究證據] Steyerberg & Harrell（2016，詳見 Q4）：「Bootstrapping is the preferred approach for validation of prediction models」，以及「In such small samples, internal validation is essential, and apparent performance estimates are severely optimistic」。[PMC5578404](https://pmc.ncbi.nlm.nih.gov/articles/PMC5578404/)

### Inferences

**各方法在 14 位病人下的比較**（皆為 **[推論]**，綜合以上文獻）

| 方法 | 偏差 | 變異 | 14 位病人下的可行性與陷阱 |
|---|---|---|---|
| StratifiedGroupKFold（3-fold，單次） | 訓練集只有約 9–10 位病人，偏悲觀（訓練資料比最終模型少約 1/3） | 極高；結果高度依賴哪幾位病人落在同一 fold | 依文件，「少量 group、大量樣本」時分層會退化成接近 GroupKFold。9 張 normal 若集中在少數病人，某些 fold 可能沒有 normal → specificity 無法定義 |
| Repeated StratifiedGroupKFold（多個 seed） | 同上 | 平均值的變異降低，但**不會**降低「資料本身只有 14 位病人」造成的不確定性（Varoquaux；Bengio & Grandvalet） | sklearn 沒有內建 repeated 版本，要手動換 `random_state`。`shuffle` 只會打亂類別分布相近的 group，所以不同 seed 可能產生**相同的分割**，必須去重並記錄 distinct partitions 數 |
| LOGO（leave-one-patient-out，14 folds） | 偏差最小（訓練用 13/14 位病人） | 各 fold 之間高度相關，整體估計變異高；每個 fold 只有 1 位病人，**每個 fold 的** sensitivity / specificity / BA 多數無法定義 | 可行，但**必須 pool 全部 out-of-fold 預測**再計算指標（見 Q2）。可另外呈現「每位病人的正確率」分布作為描述性輸出。部署上確定性高（無隨機性），可重現 |
| Nested CV | 對「調參後的整套流程」近乎不偏（Varma & Simon；Vabalas） | 更高：外層 3–5 folds × 內層只有約 7–9 位病人，內層選參近乎隨機 | 14 位病人時內層幾乎沒有資訊。實務上**建議預先固定超參數**（例如 logistic regression C 固定、EfficientNet 只訓練 linear head），以 flat 流程評估，並在報告中聲明「無調參」 |
| Bootstrap .632 / .632+（病人層級） | .632+ 在小樣本、強訊號下可能有偏差（Molinaro 2005） | 通常低於 CV（Efron & Tibshirani 1997） | 必須以病人為抽樣單位。14 位病人時，每位病人不被抽中的機率為 (13/14)^14 ≈ 0.354。若 normal 照片只來自 k 位病人，一個 bootstrap 樣本完全沒有 normal 病人的機率為 ((14−k)/14)^14：k=2 約 0.116，k=3 約 0.034 → 需要**依類別分層抽病人**或丟棄退化樣本並記錄。γ（no-information rate）原定義於 0-1 loss，套用在 balanced accuracy 屬自行延伸 |
| Harrell optimism bootstrap（病人層級） | 對迴歸類模型低偏差（Steyerberg 2001，見 Q4） | 低 | 對「凍結 backbone 特徵加 logistic regression」（DINOv2 + LR、EfficientNet 線性 head）**計算上可行**：特徵抽一次，200–500 次 bootstrap 只重訓 head。對 unfreeze 最後一個 block 的微調太耗時。apparent performance 需在「全部照片」上計算 |

- **[推論]** 現階段（14 位病人）建議組合：
  - (a) 主分析：LOGO 或 repeated SGKF（≥20–50 個不同 seed，去重後的 distinct partitions），**pooled** OOF 預測 → BA、normal FPR、macro-F1、confusion matrix。
  - (b) 敏感度分析：patient-level stratified cluster bootstrap 的 optimism-corrected BA（只用於凍結特徵加線性 head）。
  - (c) 全部超參數預先固定、寫進 protocol。
  - (d) 報告「方法之間的差異」時，承認各方法的 CI 會大幅重疊。
- **[推論]** 因為 Varoquaux 指出 fold 間 SE 會低估不確定性，CI 不應由「fold 分數的 SD」計算。應改用：(i) pooled OOF 預測再做**病人層級 cluster bootstrap**（重抽病人、保留其所有照片）計算 CI；或 (ii) 病人層級 Wilson（以病人為單位彙總）作為保守下界。本專案現行的 Wilson CI 若以照片為單位，會因叢集而**過窄**（見 Q4 design effect 計算）。
- **[推論]** 照片的「病人內相關」對 bootstrap 的意義：同一位病人的照片在訓練與測試間互相洩漏 = Q3 所說的 leakage。所以「照片層級 bootstrap / .632+」在本資料上會產生與 image-level split 相同的樂觀偏差，必須避免。

### Gaps
- 未找到可靠證據直接比較「病人層級 cluster bootstrap .632+」與「grouped CV」在小樣本、每人多張影像情境下的偏差 / 變異（只找到 cluster bootstrap optimism 的預印本，以及 TRIPOD-Cluster 的一般說明）。
- Efron & Tibshirani 1997 原文公式與「24 個模擬實驗」細節，本次只能從摘要確認；PDF 無法擷取文字。
- Molinaro 2005 與 Kohavi 1995 只讀到摘要 / 二手摘要。Kohavi 的建議（10-fold vs repeated 5-fold）兩個來源不一致，未能以原文調和。
- Varoquaux 是否明確建議「repeated random splits 優於 LOO」：未在本次讀到的段落中確認，未找到可靠證據。

---

## Q2. Pooled vs. 各 fold 平均的指標（Forman & Scholz 2010），以及 LOGO 下指標無法定義的問題

### Takeaway
F1 這類非線性指標若在各 fold 分別計算再平均，會產生偏差。Forman & Scholz 建議把各 fold 的 TP/FP/FN pool 起來再計算。本專案有些病人或 fold 完全沒有 normal 照片，per-fold specificity / BA / macro-F1 會無法定義或極不穩定。因此**pooled OOF 預測是唯一可行的主要計算方式**；per-fold 數值只能作為穩定性的描述。

### Cited Findings
- [C][研究證據] Forman G, Scholz M. (2010) "Apples-to-Apples in Cross-Validation Studies: Pitfalls in Classifier Performance Measurement." *ACM SIGKDD Explorations* 12(1):49–57. doi:10.1145/1882471.1882479（另有 2009 年 HP 技術報告版本）。
  - 討論 F-measure 與 AUC 跨 fold 計算的歧義，特別是平均各 fold F 值的問題。
  - 二手摘要（Raschka FAQ [E]）指出，作者比較三種 F1 計算方式後，以「pooled TP/FP/FN」計算的 F1 偏差最小。
  - 實證性質：文字分類基準資料，無病人叢集。
  - 來源：[PDF](https://www.dcc.fc.up.pt/~ines/aulas/1516/DM1/Papers/v12-1-p49-forman-sigkdd.pdf)、[Crossref](https://api.crossref.org/works/10.1145%2F1882471.1882479)、[Raschka FAQ [E]](https://sebastianraschka.com/faq/docs/computing-the-f1-score.html)
- [B][研究證據] Varoquaux（2018）：fold 間標準誤低估真實誤差棒。所以「平均 ± fold SD」即使換成 pooled 計算，也不能用 fold SD 當 CI。[arXiv](https://arxiv.org/pdf/1706.07581)

### Inferences
- **[推論]** 本專案的具體規則：
  1. 每個 split 方案（每個 seed，或 LOGO）收集**每張照片恰好一個** OOF 預測，再 pool 計算 BA、normal FPR、macro-F1、confusion matrix。
  2. Repeated CV 有 R 個 seed，就得到 R 個 pooled 指標 → 報告其中位數與範圍（這反映的是「分割的隨機性」，**不是**抽樣不確定性）。
  3. 抽樣不確定性用病人層級 cluster bootstrap，重抽 pooled OOF 預測（以病人為單位）。
  4. Per-fold 指標只在該 fold 同時有兩類（binary），或三類都有（staging）時才列出，並標示為「描述性」。
- **[推論]** LOGO 下每個 fold 只有一位病人，該病人可能只有陽性照片 → per-fold specificity 是 0/0。所以 LOGO **只能**用 pooled。可以另外呈現「每位病人的照片正確率」，揭露模型是否只在特定病人上失敗。這屬於病人層級的錯誤分析，不是效能估計。
- **[推論]** Staging（有序三類）的 macro-F1 也應從 pooled 3×3 confusion matrix 計算。另可加報 linear / quadratic weighted kappa 或 ordinal MAE（屬業界慣例，本筆記未查證其小樣本行為）。
- **[推論]** 若同一張照片在 repeated CV 中有多個 OOF 預測（每個 seed 一個），**不要**把所有 seed 的預測混在一起算一個 confusion matrix 再算 CI，那樣會把有效 n 灌成 R 倍。

### Gaps
- 未讀到 Forman & Scholz 全文中針對 balanced accuracy / macro-F1 多類別情境的明確建議；以上規則是從 F1 的結論延伸。
- 未找到可靠證據說明在「pooled OOF + cluster bootstrap」下，CI 覆蓋率在 14 個 cluster 時是否足夠（cluster 數過少時 bootstrap CI 覆蓋率通常不足，但本次未找到具體文獻數字）。

---

## Q3. 病人層級資料洩漏：依影像 vs 依病人切分造成的效能高估證據

### Takeaway
多個醫療影像領域（腦 MRI、OCT、數位病理、皮膚影像資料集）都顯示，依影像 / 切片 / 磁磚切分會嚴重高估效能：準確度膨脹約 5% 到 55%，隨機標籤的資料甚至可以做到約 96% 準確度。本專案每位病人有多張照片（同一手臂、相近日期、同一燈光與背景），屬於高相似度叢集，**依病人切分是必要條件，不是可選項**。即使依病人切分，同一位病人的不同 episode / 不同手也不能分到訓練與測試兩邊。

### Cited Findings
- [C][研究證據] Yagis E, et al. (2021) "Effect of data leakage in brain MRI classification using 2D convolutional neural networks." *Sci Rep* 11:22544. doi:10.1038/s41598-021-01681-w。
  - 3D MRI 依 2D 切片切分的 CV，使測試準確度提高：OASIS / ADNI 約 29–30%，PPMI 48%，本地 Versilia PD 資料 55%。
  - 隨機標籤的 OASIS 衍生資料：切片層級切分約 96% 準確度，受試者層級切分 50%（機率水準）。
  - 作者指出「especially for small datasets」扭曲最嚴重。
  - **病人層級切分：有（作為對照）；外部驗證：無。**
  - [PMC8604922](https://pmc.ncbi.nlm.nih.gov/articles/PMC8604922)
- [C][研究證據] Tampu IE, Eklund A, Haj-Hosseini N. (2022) "Inflation of test accuracy due to data leakage in deep learning-based classification of OCT images." *Sci Data* 9:580。
  - 在三個公開 OCT 資料集比較 per-image 與 per-volume/subject 切分。
  - 已發表版本：不當切分使 MCC 膨脹 0.07–0.43，準確度膨脹 5–30%。
  - **版本差異**：arXiv v1 寫 3.9–26 個百分點，應引用已發表版本。
  - 作者也提醒，即使 per-volume 切分也可能不足以避免重疊。
  - **病人層級切分：有（作為對照）；外部驗證：無。**
  - [PMC9500039](https://pmc.ncbi.nlm.nih.gov/articles/PMC9500039)、[PubMed 36138025](https://pubmed.ncbi.nlm.nih.gov/36138025/)
- [C][研究證據] Bussola N, Marcolini A, Maggio V, Jurman G, Furlanello C. (2021) "AI slipping on tiles: data leakage in digital pathology." In: *Pattern Recognition. ICPR International Workshops*, LNCS 12661:167–182. doi:10.1007/978-3-030-68763-2_13（arXiv:1909.06539）。
  - 在 GTEx、Heart Failure、BreakHis 三個資料集（373 位受試者、543 張切片、約 27,000 個磁磚）比較 tile-wise 與 patient-wise 切分。
  - 釋出 histolab 套件以建立無洩漏流程。
  - 後續文獻引用「最多 41% 膨脹」，**本次未在原文中確認此數字**。
  - **病人層級切分：有（作為對照）；外部驗證：無。**
  - [arXiv](https://arxiv.org/pdf/1909.06539)
- [B][研究證據] Roberts M, et al. (2021) "Common pitfalls and recommendations for using machine learning to detect and prognosticate for COVID-19 using chest radiographs and CT scans." *Nat Mach Intell* 3:199–217. doi:10.1038/s42256-021-00307-0。
  - 檢索到 2,212 篇研究，初篩後 415 篇，品質篩選後 62 篇納入。
  - 結論：「none of the models identified are of potential clinical use due to methodological flaws and/or underlying biases」。
  - 常見問題包括「Frankenstein datasets」（資料集重複合併），以及以兒童影像作為非 COVID 對照所造成的混淆。
  - 屬系統性回顧，本身無病人切分 / 外部驗證。
  - [Cambridge 新聞](https://www.cam.ac.uk/research/news/machine-learning-models-for-diagnosing-covid-19-are-not-yet-suitable-for-clinical-use)、[dblp](https://dblp1.uni-trier.de/rec/journals/natmi/RobertsDTGYUAEM21.html)
- [B][研究證據] Kapoor S, Narayanan A. (2023) "Leakage and the reproducibility crisis in machine-learning-based science." *Patterns* 4(9):100804. doi:10.1016/j.patter.2023.100804。
  - 發表版本：17 個領域、共 294 篇論文受洩漏影響。**版本差異**：2022 年 arXiv 版本寫 329 篇。
  - 修正錯誤後，複雜 ML 模型不再明顯優於數十年前的 logistic regression。
  - 提出「model info sheets」以偵測與預防洩漏。
  - [PMC10499856](https://pmc.ncbi.nlm.nih.gov/articles/PMC10499856)
- [C/D][研究證據；皮膚影像] Abhishek K, Jain A, Hamarneh G. "Investigating the Quality of DermaMNIST and Fitzpatrick17k Dermatological Image Datasets."（arXiv:2401.14497；搜尋結果稱已被 *Scientific Data* 2025 接受，**本次未驗證期刊版 DOI**）。
  - DermaMNIST（源自 HAM10000）中，同一病灶的影像同時出現在 train / val / test。
  - HAM10000 與 Fitzpatrick17k 都有近乎重複的影像（以 embedding cosine 相似度門檻約 0.90 / 0.95 篩選，再人工確認）。
  - Fitzpatrick17k 過去的 benchmark 沒有獨立的 held-out test。
  - 作者釋出修正版 DermaMNIST-C / -E。
  - **膨脹幅度的具體數字本次未取得。**
  - **病灶 / 病人層級切分：修正版有；外部驗證：無。**
  - [arXiv HTML v2](https://arxiv.org/html/2401.14497v2)

### Inferences
- **[推論]** 本專案的洩漏風險比上述研究更高：
  - 同一位病人的連續日期照片背景、光線、手機都相同，類似 OCT 相鄰切片的「近重複」。
  - 醫院照片的標籤來自檔名規則：若檔名或拍攝流程與類別相關（例如某一類多在特定病房拍攝），模型可能學到拍攝情境而不是病灶（參見 Q5 Zech 的 hospital-system shortcut）。
- **[推論]** 切分單位應為「病人 ID」。若 LINE 公開照片無法可靠對應到病人，應以「上傳者 / 上傳批次」為 group 的保守代理，並做近重複偵測（例如 DINOv2 embedding cosine > 0.95 人工檢查），比照 Abhishek et al. 的方法。
- **[推論]** 建議做一次「洩漏量化」實驗作為方法學附錄：同一模型分別以 image-level 與 patient-level 切分，報告兩者的 BA 差距。這能向讀者直接展示為何採用 patient-level 切分，且屬低成本。

### Gaps
- 未找到直接針對「臨床照片（非皮膚鏡）/ 傷口 / 靜脈注射部位照片」的 image-level vs patient-level 洩漏量化研究。未找到可靠證據。
- Bussola 的「41%」以及 Abhishek et al. 的膨脹幅度，未從原文確認。

---

## Q4. 只有 14–18 張照片（約 4 位病人）的獨立測試集能下什麼結論？未來 50/200/300+ 位病人時的測試集大小與 holdout 策略

### Takeaway
14–18 張、約 4 位病人的 holdout，若其中 normal 只有 2–5 張，specificity 的 95% Wilson CI 寬度約 0.59–0.81（例如 4/5 → 0.38–0.96），**而且這還假設照片互相獨立**。考慮病人內相關後，有效樣本更小。這樣的 holdout 無法支持任何效能結論，只能做「流程煙霧測試」。Steyerberg & Harrell 明確反對小樣本隨機 split-sample（「Split sample approaches only work when not needed」）。外部驗證的經驗法則是 ≥100 events 加 ≥100 non-events（Collins 2016 等），校準曲線則為 ≥200/200。Riley 等（2021 Stat Med；2024 BMJ）主張依精確度目標量身計算，並提供 pmvalsampsize。

### Cited Findings

**Split-sample 的效率**
- [B][研究證據] Steyerberg EW, Harrell FE Jr, Borsboom GJ, Eijkemans MJ, Vergouwe Y, Habbema JD. (2001) "Internal validation of predictive models: efficiency of some procedures for logistic regression analysis." *J Clin Epidemiol* 54(8):774–781. doi:10.1016/S0895-4356(01)00341-9。
  - 從 GUSTO-I（n=40,830；2,851 死亡）抽 n=572–9,165 的樣本（EPV 5–80），8 個預測因子的 logistic 模型。
  - Split-sample 的估計過度悲觀且變異大。
  - 10% 的 CV 偏差與變異都低，但不適用所有指標。
  - Bootstrap 的估計穩定、偏差低，作者推薦 bootstrap。
  - 實證性質：病人層級（每人一筆）；無外部驗證。
  - [EUR repository](https://repub.eur.nl/pub/74159)
- [B][研究證據] Steyerberg EW, Harrell FE Jr. (2016) "Prediction models need appropriate internal, internal-external, and external validation." *J Clin Epidemiol* 69:245–247（2015 年線上發表）。doi:10.1016/j.jclinepi.2015.04.005。原文引述：
  - 「Split sample approaches only work when not needed.」
  - 「We hence strongly advise against random split sample approaches in small development samples.」
  - 「[S]plits by hospital in a multicenter study or by calendar time are attractive options when developing prediction models, with the final model developed on all available data.」
  - 本文**沒有**提出 100 events 門檻。
  - [PMC5578404](https://pmc.ncbi.nlm.nih.gov/articles/PMC5578404/)

**外部驗證樣本數**
- [B][研究證據] Collins GS, Ogundimu EO, Altman DG. (2016) "Sample size considerations for the external validation of a multivariable prognostic model: a resampling study." *Stat Med* 35(2):214–226. doi:10.1002/sim.6787。
  - 對 6 個已發表的預後模型做重抽樣，每種樣本數抽 10,000 次。
  - 結論：外部驗證至少需要 100 events，理想上 200 個以上。
  - 實證性質：病人層級；本身就是外部驗證研究。
  - [PMC4738418](https://pmc.ncbi.nlm.nih.gov/articles/PMC4738418)
- [B][研究證據] Riley RD, Snell KIE, Archer L, Ensor J, Debray TPA, van Calster B, van Smeden M, Collins GS. (2024) "Evaluation of clinical prediction models (part 3): calculating the sample size required for an external validation study." *BMJ* 384:e074821. doi:10.1136/bmj-2023-074821。
  - 經驗法則：c statistic 與 calibration slope 需「at least 100 events and 100 non-events」（引用 Vergouwe 2005、Collins 2016、Van Calster 2016）；calibration plot / curve 需 200 events 加 200 non-events。作者批評這些法則不夠針對特定模型與情境。
  - 二元結果的實例（ISARIC 4C，prevalence 0.43，C=0.77）：O/E 需 423 人（182 events）；calibration slope（CI 寬 0.3）需 949 人（408 events）；c statistic（CI 寬 0.1）需 347 人（149 events）。最低需求為 949 人。若 calibration slope 的 CI 寬度改為 0.2，需求升至 2,137 人。
  - **內部不一致**：O/E 目標 CI 寬度內文寫 0.22，示範程式碼寫 `oeciwidth(.12)`。
  - 軟體：pmvalsampsize（Stata / R）。
  - 文中未討論叢集。
  - [PMC11778934](https://pmc.ncbi.nlm.nih.gov/articles/PMC11778934/)
- [B][研究證據] Riley RD, et al. (2021) "Minimum sample size for external validation of a clinical prediction model with a binary outcome." *Stat Med* 40(19):4230–4251. doi:10.1002/sim.9025。
  - 計算需要目標 SE（CI 寬度）、預期事件比例、預期失校準與線性預測值的變異。
  - 摘要中的實例需 9,835 人（177 events），由 calibration slope 主導。
  - **數字取自摘要，未讀全文。**
  - [Keele eprint](https://eprints.keele.ac.uk/id/eprint/9707)
- Snell et al. 2021（*J Clin Epidemiol*，模擬式外部驗證樣本數）：**本次未搜尋驗證，不引用 DOI**。

**診斷準確度樣本數**
- [C][研究證據] Buderer NMF. (1996) "Statistical methodology: I. Incorporating the prevalence of disease into the sample size calculation for sensitivity and specificity." *Acad Emerg Med* 3(9):895–900. doi:10.1111/j.1553-2712.1996.tb03538.x。
  - 輸入：可接受的精確度、預期 Se / Sp、目標族群盛行率。
  - Se 與 Sp 分別計算，取較大者為總樣本數。
  - 依 R 套件 SampleSizeDiagnostics 文件 [E] 的描述，本次未讀原文。
  - [CRAN 文件](https://erised.las.iastate.edu/CRAN/web/packages/SampleSizeDiagnostics/SampleSizeDiagnostics.pdf)
- [C][研究證據] Flahault A, Cadilhac M, Thomas G. (2005) "Sample size calculation should be performed for design accuracy in diagnostic test studies." *J Clin Epidemiol* 58(8):859–862. doi:10.1016/j.jclinepi.2004.12.009。
  - 提供二元診斷測試的樣本數表。
  - 後續方法學論文指出：Se / Sp 接近 1 時，常態近似會低估所需樣本數（Flahault 的表格基於精確二項）。
  - 本次未讀全文。
  - [UNIGE archive](https://archive-ouverte.unige.ch/unige:47147)

**本筆記自行計算（[推論/計算]；Wilson 公式為標準 score interval；Buderer 公式 n = z²·p(1−p)/d²；Newcombe C-statistic SE 公式依 Riley 2024 所引用的 Newcombe 法）**

Wilson 95% CI（**假設照片獨立**）：

| 觀察值 | 點估計 | 95% CI | 寬度 |
|---|---|---|---|
| 1/2 | 0.50 | 0.095–0.905 | 0.81 |
| 2/2 | 1.00 | 0.342–1.000 | 0.66 |
| 3/4 | 0.75 | 0.301–0.954 | 0.65 |
| 4/5 | 0.80 | 0.376–0.964 | 0.59 |
| 5/5 | 1.00 | 0.566–1.000 | 0.43 |
| 9/9（全部 normal） | 1.00 | 0.701–1.000 | 0.30 |
| 7/9 | 0.78 | 0.453–0.937 | 0.48 |
| 10/12 | 0.83 | 0.552–0.953 | 0.40 |
| 12/14 | 0.86 | 0.601–0.960 | 0.36 |
| 14/16 | 0.875 | 0.640–0.965 | 0.33 |
| 42/47 | 0.89 | 0.774–0.954 | 0.18 |
| 85/100 | 0.85 | 0.767–0.907 | 0.14 |
| 90/100 | 0.90 | 0.826–0.945 | 0.12 |
| 170/200 | 0.85 | 0.794–0.893 | 0.10 |
| 255/300 | 0.85 | 0.805–0.886 | 0.08 |
| 270/300 | 0.90 | 0.861–0.929 | 0.07 |

Buderer 每類所需的**獨立單位**數（95% CI 半寬 d）：

| 預期 Se 或 Sp | d=0.05 | d=0.075 | d=0.10 | d=0.15 |
|---|---|---|---|---|
| 0.80 | 246 | 110 | 62 | 28 |
| 0.85 | 196 | 88 | 49 | 22 |
| 0.90 | 139 | 62 | 35 | 16 |

總樣本數 = 每類所需數 ÷ 該類比例。例如三類平衡時，binary 的 normal 比例為 1/3，所以 Sp 需 49 個 normal 單位時，總數約 147。

Newcombe 法計算 C-statistic（AUC）達到 95% CI 寬度所需的**獨立單位**數（φ = 陽性比例）：

| C | φ | CI 寬 0.1：總數（events） | CI 寬 0.2：總數（events） |
|---|---|---|---|
| 0.85 | 0.5 | 233（117） | 60（30） |
| 0.85 | 0.667 | 262（175） | 67（45） |
| 0.90 | 0.667 | 178（119） | 46（31） |
| 0.80 | 0.667 | 340（227） | 86（58） |

叢集 design effect DE = 1 + (m−1)·ICC（m = 每位病人平均照片數）：
- 現況：120 張、m≈8.6。ICC 為 0.1 / 0.3 / 0.5 / 0.8 時，有效 n ≈ 68 / 37 / 25 / 17。
- 未來 1,000 張、300 位病人（m≈3.3）：有效 n ≈ 813 / 592 / 465 / 352。
- 未來 1,000 張、50 位病人（m=20）：有效 n ≈ 345 / 149 / 95 / 62。
- ICC 值是假設，本專案尚未估計。

### Inferences
- **[推論] 現況 holdout（約 4 位病人、14–18 張）能下的結論**：
  - 只能確認「流程能跑、沒有明顯崩壞（例如全部預測為同一類）」。
  - 不能比較模型、不能報告 Se / Sp，也不能宣稱「通過獨立測試」。
  - 若 9 張 normal 集中於 2–3 位病人，隨機抽 4 位病人作為 holdout，很可能 holdout 有 0 張 normal（specificity 無法定義），或者訓練集剩下極少 normal。
  - 依 Steyerberg & Harrell，建議**現階段取消固定 holdout**，全部病人進 LOGO / repeated SGKF。若保留 holdout，應改名為「流程煙霧測試集」，並在報告中說明不具統計意義。
- **[推論] 本專案現行「以照片計算的 Wilson CI」過窄**：以 m≈8.6、ICC 0.3 為例，有效樣本約為照片數的 1/3。建議改用病人層級 cluster bootstrap CI，或至少在報告中註明「CI 假設照片獨立，實際應更寬」。
- **[推論] 未來測試集大小（換算成病人數）**：
  - 目標：binary 的 Sp（normal FPR）95% CI 半寬 ≤0.10，預期 Sp=0.85 → 約 49 個獨立 normal 單位。
  - 以病人為單位、每人 normal 照片 m 張、ICC 未知時，保守估計所需 normal 照片 ≈ 49 × DE。m=3、ICC=0.5 時 DE=2 → 約 98 張 normal 照片、約 33 位 normal 病人。
  - 半寬 ≤0.075 → 約 88 個獨立單位；半寬 ≤0.05 → 約 196 個獨立單位。
  - 外部驗證若要符合 Collins / Riley 經驗法則（≥100 events 加 ≥100 non-events），且以病人為單位，**需約 100 位 normal 病人加 100 位靜脈炎病人**。這遠超過 300 位病人總規模中能撥給測試的量，所以 300+ 位病人時仍應以 internal-external CV 為主，外部驗證集以「精確度目標」計算，並誠實報告 CI。
- **[推論] Holdout vs「全部進 CV，再做外部驗證」**：
  - 50 位病人：不設 holdout（Steyerberg 2001 / 2016），用 repeated grouped CV 加 cluster bootstrap。
  - 200 位病人：可設一個**時間上**的 holdout（最後收案的約 25–30% 病人，約 50–60 位），作為「temporal validation」。這比隨機 holdout 更有資訊量，因為它同時檢驗時間漂移（Steyerberg & Harrell 建議依時間切分）。
  - 300+ 位病人：internal-external CV，依來源（醫院 vs LINE）、拍攝裝置、時間區段輪流留出，加上另一院的外部集。
- **[推論]** 三類 staging 的樣本數要以「最小類別」計算：macro 指標受最小類別支配，每一類都需要達到上述每類單位數。

### Gaps
- Riley 2021 Stat Med 全文公式、pmvalsampsize 的 Python 版本是否存在：未驗證（已知 Stata / R 版本）。
- Snell et al. 2021 模擬法、Vergouwe 2005、Van Calster 2016 原文：本次未查證，故不引用其數字。
- Buderer 與 Flahault 原文表格：未讀全文。Se / Sp 接近 1 時應用精確二項（Clopper-Pearson）或 Flahault 表格；本筆記的計算用常態近似，在 p≥0.9 時可能低估。
- 尚無本專案照片的 ICC 估計，需要資料累積後計算（例如以病人為 random effect 的 logistic GLMM 估計模型分數的病人內相關）。

---

## Q5. 外部驗證設計（不同醫院、攝影者、裝置、時間、LINE vs 醫院來源）與醫療影像 AI 的外部驗證效能下降證據

### Takeaway
放射影像 DL 的系統性回顧顯示，81% 的演算法外部驗證效能下降，49% 下降 ≥0.05，24% 下降 ≥0.10（Yu 2022）。皮膚 AI 在多元膚色資料集上的 ROC-AUC 從約 0.88–0.94 掉到 0.56–0.67（Daneshjou 2022）。Zech 2018 的 CNN 能以 >99.9% 正確率辨識影像來自哪一家醫院，並利用不同醫院的盛行率差異「作弊」。本專案的 LINE vs 醫院來源**同時改變了影像來源與標註方法**，是天然的 domain split，但也可能是混淆來源。TRIPOD+AI（2024）要求完整報告開發與評估的資料使用方式。

### Cited Findings
- [B][研究證據] Yu AC, Mohajer B, Eng J. (2022) "External Validation of Deep Learning Algorithms for Radiologic Diagnosis: A Systematic Review." *Radiol Artif Intell* 4(3):e210064. doi:10.1148/ryai.210064。
  - 納入 2015 年至 2021 年 4 月 PubMed 的 83 篇研究、86 個演算法。
  - 70/86（81%）外部效能至少有些下降；42/86（49%）下降 ≥0.05；21/86（24%）下降 ≥0.10。
  - 沒有任何研究特徵（包括機構數、開發資料量）與內外部效能差距顯著相關。
  - 少數外部效能「上升」的案例可能是資料洩漏，或外部資料過於簡單（例如公開乳房超音波資料集）。
  - 屬系統性回顧，納入研究的病人切分情況不一。
  - [PMC9668941](https://pmc.ncbi.nlm.nih.gov/articles/9668941)、[RSNA](https://pubs.rsna.org/doi/epdf/10.1148/ryai.210064)
  - 相關：Kelly et al. 2022 *Eur Radiol* 的「外部驗證平均下降 6%（77 篇研究）」只見於搜尋摘要，**本次未驗證**。
- [B][研究證據] Zech JR, Badgeley MA, Liu M, Costa AB, Titano JJ, Oermann EK. (2018) "Variable generalization performance of a deep learning model to detect pneumonia in chest radiographs: A cross-sectional study." *PLoS Med* 15(11):e1002683. doi:10.1371/journal.pmed.1002683。
  - 資料：NIH、Mount Sinai（MSH）、Indiana（IU）三家機構，共 158,323 張胸部 X 光。
  - 5 組自然比較中，有 3 組內部效能優於外部。
  - MSH+NIH 合併訓練：內部 AUC 0.931（0.927–0.936），外部 IU AUC 0.815（0.745–0.885）。
  - MSH 肺炎盛行率 34.2%，NIH 與 IU 分別為 1.2% 與 1.0%。單純依醫院排序就能在 MSH-NIH 合併資料上得到 AUC 0.861。
  - CNN 能直接辨識醫院來源：NIH 99.95%（22,050/22,062），MSH 99.98%（8,386/8,388）。
  - 兩個訓練站點盛行率相同時，外部 IU 效能一致（P=0.88）。
  - **病人層級切分：有；外部驗證：有（跨機構）。**
  - 本次讀到的是摘要與書目記錄。[DOAJ](https://doaj.org/article/86bad117ffd645d7bd86f36b7db6dd6f)
- [B][研究證據；皮膚] Daneshjou R, et al. (2022) "Disparities in dermatology AI performance on a diverse, curated clinical image set." *Sci Adv* 8(32):eabq6147. doi:10.1126/sciadv.abq6147。**卷期更正**：issue 32，不是 31。
  - DDI 資料集：656 張影像（FST I–II 208、III–IV 241、V–VI 207），每個 case 一張，病理確認，來自 Stanford Clinics 2010–2020。
  - ROC-AUC 從原始測試到 DDI：ModelDerm 0.93–0.94（文獻值）→ 0.65（0.61–0.70）；DeepDerm 0.88 → 0.56（0.51–0.61）；HAM10000 模型 0.92 → 0.67（0.62–0.71）。
  - 由以上計算，絕對下降約 0.25–0.32。二手摘要所稱「27–36%」為相對下降；預印本寫 29–40%。
  - 所有模型在深膚色與罕見疾病上都較差；皮膚科醫師亦同。用 DDI 微調可縮小膚色差距。
  - **病人層級：每 case 一張，不涉切分；外部驗證：對 ModelDerm / HAM10000 模型屬外部，DeepDerm 訓練資料含 Stanford 資料，不完全外部。**
  - [PMC9374341](https://pmc.ncbi.nlm.nih.gov/articles/PMC9374341/)、[PubMed 35960806](https://pubmed.ncbi.nlm.nih.gov/35960806/)
- [B][研究證據] Steyerberg & Harrell（2016）：依醫院或日曆時間切分（internal-external）是開發時的理想選擇，最終模型以全部資料建立；許多失敗的外部驗證本可由嚴謹的內部驗證預見（依二手摘要）。[PMC5578404](https://pmc.ncbi.nlm.nih.gov/articles/PMC5578404/)
- [A][報告標準] Collins GS, Moons KGM, et al. (2024) "TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine learning methods." *BMJ* 385:e078378. doi:10.1136/bmj-2023-078378。
  - 27 項 checklist，另有 13 項摘要版 checklist。
  - 取代 TRIPOD 2015（「should no longer be used」）。
  - 涵蓋開發與評估（含外部驗證）研究。
  - 本次未讀到逐條項目內容（例如內部驗證方法、資料切分說明的具體條號）。
  - [BMJ](https://www.bmj.com/node/1095803)、[Birmingham](https://research.birmingham.ac.uk/en/publications/tripodai-statement-updated-guidance-for-reporting-clinical-predic/)
- [A] TRIPOD-Cluster：叢集資料（病人巢套於醫院）的報告指引，19 項。[PMC9903176](https://pmc.ncbi.nlm.nih.gov/articles/PMC9903176)
- [B][研究證據] Riley 2024 BMJ：外部驗證資料應代表目標族群與情境（case mix、結果風險、預測因子的測量與時間）。[PMC11778934](https://pmc.ncbi.nlm.nih.gov/articles/PMC11778934/)

### Inferences
- **[推論] LINE vs 醫院作為 domain split 的雙面性**：
  - 優點：不同攝影者、裝置、光線、背景，屬天然的外部性檢驗（類似 Zech 的跨機構）。
  - 風險：LINE 照片是人工複核標註，醫院照片是檔名規則自動標註 → 「來源」與「標註雜訊型態」完全共變。若兩個來源的類別分布不同（例如 normal 多來自 LINE），模型可能學到來源特徵（Zech：CNN 辨識醫院達 99.9%）。
  - 建議先做三件事：(1) 列出 source × class 交叉表；(2) 用凍結 DINOv2 特徵加 LR 預測「來源」，若 AUC 接近 1，表示來源可被輕易辨識，需特別控制；(3) 分別報告 source-stratified 指標。
- **[推論] 本專案外部驗證設計層次**（由易到難）：
  1. 同院時間驗證（temporal）：最後收案時段的病人。
  2. 來源驗證：醫院訓練 → LINE 測試，以及反向。
  3. 裝置 / 攝影者驗證：記錄手機型號、拍攝者 ID 作為 group。
  4. 跨院外部驗證：另一家醫院、不同護理團隊，需要倫理審查與資料協議，照片不上雲。
- **[推論]** 外部驗證集應有**獨立標註**（最好兩位標註者加一致性 kappa），否則外部效能下降無法區分「模型泛化差」與「標註定義不同」。單一標註者是本專案目前最大的外部效度限制之一。
- **[推論]** 依 Yu 2022 的分布，即使內部驗證做得好，預期外部效能下降 ≥0.05 的機率約一半。所以研究報告中的內部效能應明確標示「尚未外部驗證」。這與本專案「不做臨床宣稱」的原則一致。

### Gaps
- 未找到靜脈炎 / 輸液部位照片分類的外部驗證文獻。未找到可靠證據。
- TRIPOD+AI 逐條內容（例如資料切分、叢集處理、外部驗證報告的條號）本次未讀全文；CLAIM、FDA、TFDA 等法規文件本次未查證。
- Kelly 2022 Eur Radiol 數字未驗證。

---

## Q6. 驗證策略決策表草案（依病人數）與可直接使用的虛擬碼

### Takeaway
病人數決定可用的驗證層級：
- 14 位：只能做內部重抽樣，結果屬「可行性訊號」。
- 50 位：repeated grouped CV 加病人層級 bootstrap，仍不設 holdout。
- 200 位：加入時間 holdout（temporal validation）。
- 300+ 位：internal-external CV（依來源 / 時間 / 裝置），加上依精確度目標計算的跨院外部驗證集。

所有層級都以病人為切分與 bootstrap 單位，以 pooled OOF 預測計算指標。

### Cited Findings
- 決策表的依據已在 Q1–Q5 引用：Steyerberg 2001、Steyerberg & Harrell 2016（反對小樣本 split-sample、推薦 bootstrap 與 internal-external）；Collins 2016、Riley 2024（外部驗證 ≥100/100 經驗法則與量身計算）；Varoquaux 2018（小樣本誤差棒）；Krstajic 2014（repeated / nested CV）；Forman & Scholz 2010（pooled）；scikit-learn 文件（StratifiedGroupKFold 行為，無 repeated 版本）。來源連結見各節。

### Inferences

**決策表（[推論]，以本專案條件為準）**

| 病人數（約略照片數） | 建議主驗證法 | 獨立測試集 | 外部 / 準外部驗證 | 主要指標與 CI | 能做的結論 |
|---|---|---|---|---|---|
| **14**（約 120 張） | LOGO **或** repeated StratifiedGroupKFold（3-fold，≥20–50 seeds，去重 partitions）；超參數預先固定、不調參；敏感度分析：病人層級分層 cluster bootstrap optimism（只限凍結特徵加線性 head） | **不設**；若保留，僅作煙霧測試並註明 | LINE vs 醫院 source × class 交叉表、來源可辨識度檢查（只做描述） | pooled BA、normal FPR、macro-F1、confusion matrix；病人層級 cluster bootstrap 95% CI；註明 CI 極寬 | 「方法可行、有初步訊號」；不能比較模型，不能報告 Se / Sp 為效能 |
| **50**（約 300–500 張） | repeated SGKF 5-fold（≥50 seeds）**加上** 病人層級 bootstrap .632+ / optimism 作為對照；若要調參，用 nested（外 5 × 內 3–4），並只在少數超參數上調 | 不設（依 Steyerberg 2001 / 2016） | 來源互換驗證（醫院 → LINE，以及反向），屬探索性 | 同上，加報 per-source 指標；staging 加 weighted kappa | 可初步比較 2–3 個預設模型，但 CI 仍寬（normal 約 15–20 位病人時，Sp 半寬約 0.10–0.15） |
| **200**（約 700–1,000 張） | 開發集內 repeated SGKF 5-fold 加 nested（如需調參） | **時間 holdout**：最後收案約 25–30% 病人（約 50–60 位）；凍結模型後只評估一次 | 時間驗證加來源驗證；開始收集裝置 / 攝影者 ID | 指標同上，CI 用病人層級 bootstrap；normal FPR 半寬目標 ≤0.10（約 49 個獨立 normal 單位 × DE） | 「內部與時間驗證」層級的研究結果；仍需外部驗證 |
| **300+**（≥1,000 張，三類平衡） | Internal-external CV：輪流留出一個來源 / 時間區段 / 裝置群（Steyerberg & Harrell） | 時間 holdout（可保留）加**跨院外部集** | 跨院外部驗證，樣本數依 pmvalsampsize / Buderer 精確度目標計算；經驗法則 ≥100 位 normal 病人加 ≥100 位靜脈炎病人（Collins / Riley），做不到時報告實際 CI | 同上，加 calibration（若輸出機率）、per-site 異質性 | 可撰寫符合 TRIPOD+AI 的驗證研究，仍屬研究原型 |

**虛擬碼（[推論]，Python / scikit-learn；可直接改寫進現有評估流程）**

```python
# ---- 共用 ----
import numpy as np
from sklearn.model_selection import StratifiedGroupKFold, LeaveOneGroupOut
from sklearn.metrics import balanced_accuracy_score, f1_score, confusion_matrix

def pooled_metrics(y, yhat, normal_label=0):
    """以 pooled OOF 預測計算指標（Forman & Scholz：先 pool 再算）"""
    cm = confusion_matrix(y, yhat)
    neg = (y == normal_label)
    fpr_normal = np.mean(yhat[neg] != normal_label) if neg.any() else np.nan
    return dict(ba=balanced_accuracy_score(y, yhat),
                macro_f1=f1_score(y, yhat, average="macro"),
                normal_fpr=fpr_normal, cm=cm)

def fit_predict(X_tr, y_tr, X_te):
    """固定超參數；例如 DINOv2 特徵 + LogisticRegression(C=1.0, class_weight='balanced')"""
    ...

# ---- 1) Repeated StratifiedGroupKFold（sklearn 無內建 repeated 版本 → 手動換 seed、去重）----
def repeated_sgkf(X, y, groups, n_splits=3, seeds=range(50)):
    seen, results = set(), []
    for s in seeds:
        cv = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=s)
        splits = list(cv.split(X, y, groups))
        key = frozenset(frozenset(np.unique(groups[te])) for _, te in splits)
        if key in seen:              # shuffle 只打亂類別分布相近的 group → 常出現重複分割
            continue
        seen.add(key)
        oof = np.full(len(y), -1)
        for tr, te in splits:
            assert not set(groups[tr]) & set(groups[te])   # 病人不重疊
            oof[te] = fit_predict(X[tr], y[tr], X[te])
        results.append(pooled_metrics(y, oof))
    return results, len(seen)        # 報告 distinct partitions 數，以及指標的中位數與範圍

# ---- 2) LOGO：每 fold 一位病人 → 只能 pooled ----
def logo(X, y, groups):
    oof = np.full(len(y), -1)
    for tr, te in LeaveOneGroupOut().split(X, y, groups):
        oof[te] = fit_predict(X[tr], y[tr], X[te])
    per_patient_acc = {g: np.mean(oof[groups == g] == y[groups == g]) for g in np.unique(groups)}
    return pooled_metrics(y, oof), per_patient_acc, oof

# ---- 3) 病人層級 cluster bootstrap CI（對 pooled OOF 預測重抽病人）----
def cluster_bootstrap_ci(y, yhat, groups, metric, B=2000, rng=np.random.default_rng(0)):
    pats = np.unique(groups); idx_by_p = {p: np.where(groups == p)[0] for p in pats}
    vals = []
    for _ in range(B):
        samp = rng.choice(pats, size=len(pats), replace=True)
        idx = np.concatenate([idx_by_p[p] for p in samp])
        if len(np.unique(y[idx])) < len(np.unique(y)):   # 缺類別 → 指標無定義，記錄並略過
            continue
        vals.append(metric(y[idx], yhat[idx]))
    return np.percentile(vals, [2.5, 97.5]), len(vals)   # 回報有效 bootstrap 次數

# ---- 4) 病人層級、依類別分層的 .632+ bootstrap（誤差 = 1 - BA，屬自行延伸）----
def patient_strata(y, groups):
    # 每位病人的層：例如「是否有任何 normal 照片」，確保每個 bootstrap 樣本都有 normal 病人
    return {p: int((y[groups == p] == 0).any()) for p in np.unique(groups)}

def boot632plus(X, y, groups, B=200, rng=np.random.default_rng(0)):
    err = lambda yt, yp: 1 - balanced_accuracy_score(yt, yp)
    yhat_app = fit_predict(X, y, X); err_app = err(y, yhat_app)   # apparent（訓練）誤差
    strata = patient_strata(y, groups); pats = np.array(list(strata))
    oob_err = []
    for _ in range(B):
        samp = np.concatenate([rng.choice(pats[[strata[p] == s for p in pats]],
                                          size=sum(strata[p] == s for p in pats), replace=True)
                               for s in set(strata.values())])     # 分層抽病人
        tr = np.concatenate([np.where(groups == p)[0] for p in samp])
        oob_p = np.setdiff1d(pats, samp)
        te = np.where(np.isin(groups, oob_p))[0]
        if len(te) == 0 or len(np.unique(y[te])) < 2:
            continue
        oob_err.append(err(y[te], fit_predict(X[tr], y[tr], X[te])))
    err1 = np.mean(oob_err)
    # no-information rate γ：預測與標籤獨立時的期望誤差（以排列標籤近似）
    gamma = np.mean([err(rng.permutation(y), yhat_app) for _ in range(200)])
    R = np.clip((err1 - err_app) / (gamma - err_app), 0, 1) if gamma > err_app else 0
    w = 0.632 / (1 - 0.368 * R)
    return (1 - w) * err_app + w * err1, len(oob_err)

# ---- 5) Harrell optimism bootstrap（病人層級；只用於凍結特徵 + 線性 head）----
def optimism_corrected(X, y, groups, metric, B=200, rng=np.random.default_rng(0)):
    apparent = metric(y, fit_predict(X, y, X))
    pats = np.unique(groups); opt = []
    for _ in range(B):
        samp = rng.choice(pats, size=len(pats), replace=True)
        idx = np.concatenate([np.where(groups == p)[0] for p in samp])
        if len(np.unique(y[idx])) < len(np.unique(y)):
            continue
        m_boot = metric(y[idx], fit_predict(X[idx], y[idx], X[idx]))   # 在 bootstrap 樣本上的表現
        m_orig = metric(y, fit_predict(X[idx], y[idx], X))             # 在原始全部資料上的表現
        opt.append(m_boot - m_orig)
    return apparent - np.mean(opt), len(opt)
```

- **[推論] 實作注意**：
  - (a) `groups` 用病人 ID；LINE 照片無 ID 時，以上傳者 / 批次加近重複聚類作為代理。
  - (b) 任何前處理（標準化、PCA、特徵選擇、閾值選擇）都必須在每個 fold 的訓練部分內擬合（Vabalas、Krstajic）。
  - (c) 決策閾值（例如為了壓低 normal FPR）若要調整，應在內層決定，否則屬選模洩漏。
  - (d) 所有被略過的 bootstrap 次數（缺類別）都要記錄並報告。
  - (e) 依專案原則，以上流程只產出報告，由人工確認，不自動訓練或部署。

### Gaps
- 未找到文獻驗證「以 1−BA 取代 0-1 loss」的 .632+ 性質；本筆記的 γ 以排列近似，屬自行延伸，需模擬檢查。
- 決策表中「50 位病人時 Sp 半寬約 0.10–0.15」是以每位 normal 病人約 1 個獨立單位的粗略推論，實際取決於 ICC 與 normal 病人數。
- scikit-learn `LeaveOneGroupOut` 文件頁本次未開啟驗證（該類別在 sklearn 中存在，屬常識性 API）；StratifiedGroupKFold 文件已驗證。

---

### 附錄：計算方法說明
- Wilson score interval：z = 1.959964，標準公式。
- Buderer：n_class = z²·p(1−p)/d²（常態近似；p 接近 1 時會低估）。
- Newcombe C-statistic SE（Riley 2024 引用之方法）：SE(C) = sqrt{ C(1−C)[1 + (n/2−1)(1−C)/(2−C) + (n/2−1)C/(1+C)] / (n²·φ(1−φ)) }，以逐步增加 n 直到 2·1.96·SE ≤ 目標寬度。公式依記憶實作，**與 pmvalsampsize 的輸出交叉核對前，應視為近似值**。
- Design effect：DE = 1 + (m−1)·ICC（Kish 標準公式；ICC 值為假設情境，不是本專案估計值）。
- 計算腳本：`C:\Users\user\AppData\Local\Temp\claude\C--Users-user-Desktop-Phlebitis\4d6b4eb5-4adf-4ba8-bb06-eea9dfa28acc\scratchpad\ci.py`（scratchpad，非專案檔案）。
