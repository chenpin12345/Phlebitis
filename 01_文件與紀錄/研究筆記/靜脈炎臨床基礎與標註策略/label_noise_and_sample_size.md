# 標籤雜訊訓練方法與小型醫學影像分類器的樣本數規劃 / CI 寬度

> 研究日期：2026-10-30（網路來源存取日期皆為 2026-10-30）。來源分級：[A] 官方/標準/報告指引；[B] 系統性回顧/頂級期刊；[C] 一般同儕審查；[D] 預印本；[E] 部落格/程式文件（僅輔助）。
> 結論標記：**研究證據顯示** / **業界慣例** / **本報告推論**。計算結果一律標為 **本報告推論 (computed)**，腳本與完整輸出附於本檔「Part 2-D」。
> 專案前提（由委託方提供）：研究原型、非診斷；約 120 張照片 / 14 位病人；二元任務 positive 47 / normal 9；分期 normal 9 / stage 1 23 / stage 2 24；病人層級 StratifiedGroupKFold 3-fold；選用 held-out 約 25–30% 病人（≈14–18 張）。模型：EfficientNet-B0 凍結骨幹、DINOv2-small 凍結 + logistic regression、YOLO 偵測。原則：不自動訓練/部署；不自動寫入偽標籤；cleanlab 標記只能送人工複核，不得自動改標。
> 注意：二元與分期任務各僅 56 張有標籤（47+9 / 9+23+24），與「約 120 張」不一致；以下計算以委託方給定的 9 張 normal 為準。

---

## Part 1-A：標籤雜訊方法的機制與公式（label smoothing、co-teaching 系列、DivideMix、robust loss、confident learning、ordinal soft labels）

### Takeaway
多數「抗雜訊」深度學習方法（co-teaching、DivideMix、ELR、GCE/SCE）的設計前提是：大量樣本、端到端訓練深網路、利用「先學乾淨樣本再記憶雜訊樣本」的 memorization 動態、且常需已知或可估的雜訊率；本專案（56 張有標籤、9 張 normal、凍結骨幹 + 線性頭）幾乎不滿足這些前提。真正可移植的是：label smoothing / ordinal soft label（改目標分佈）、class weight、以及 confident-learning 式的 out-of-fold 不一致檢查（僅供人工複核）。

### Cited Findings
- **Label smoothing 定義與效果**：以「hard label 與標籤均勻分佈混合」的軟目標訓練，可改善泛化、學習速度與 calibration；但以 LS 訓練的 teacher 會使知識蒸餾效果顯著變差，因 LS 讓同類樣本在倒數第二層聚成緊密群集，抹除了 logits 中類別間相似度資訊。— [C] Müller, Kornblith, Hinton, "When does label smoothing help?" NeurIPS 2019 (arXiv 1906.02629) [https://arxiv.org/abs/1906.02629](https://arxiv.org/abs/1906.02629)（存取 2026-10-30）
  - 公式（標準寫法，**業界慣例**）：y_LS = (1 − ε)·y_onehot + ε/K，K = 類別數；常見 ε = 0.1。（Szegedy et al. 2016 原始出處本輪未開啟核對。）
- **Label smoothing 與標籤雜訊**：Lukasik et al. 指出 LS 雖等同於「對標籤加入對稱雜訊」、看似會加劇雜訊，但實驗上在標籤雜訊下與既有 loss-correction 方法表現相當，作者並將 LS 連結到 label-noise 文獻中的 loss-correction 家族；在雜訊資料上蒸餾時，平滑 teacher 反而有幫助。— [C] Lukasik, Bhojanapalli, Menon, Kumar, "Does label smoothing mitigate label noise?" ICML 2020, PMLR 119:6448–6458 [https://proceedings.mlr.press/v119/lukasik20a.html](https://proceedings.mlr.press/v119/lukasik20a.html)（搜尋摘要層級，存取 2026-10-30）
- **Co-teaching**：同時訓練兩個網路，每個 mini-batch 各自挑出「可能乾淨」的樣本交給對方更新；其依據是深網路的 memorization effect（先學乾淨、後學雜訊）。— [C] Han et al., "Co-teaching: Robust training of deep neural networks with extremely noisy labels," NeurIPS 2018 (arXiv 1804.06872) [https://arxiv.org/abs/1804.06872](https://arxiv.org/abs/1804.06872)（存取 2026-10-30）
  - 原論文的保留比例排程 R(T) = 1 − min(T·τ/T_k, τ)（τ = 雜訊率）屬本報告依原論文常見寫法轉述，本輪 ar5iv 全文因速率限制未能核對 → 見 Gaps。
  - 2025 年醫學影像基準論文明確指出：sample-selection 方法「assume access to the noise rate, which is rarely available in deployment」，因此實務價值有限。— [D] Ma et al., LNMBench, arXiv 2512.09315 (2025-12-10) [https://arxiv.org/html/2512.09315](https://arxiv.org/html/2512.09315)（存取 2026-10-30）
- **GCE (Lq loss)**：MAE 被提出作為 CCE 的抗雜訊替代，但作者顯示 MAE 在深網路與困難資料集上可能表現很差；GCE 是同時泛化 MAE 與 CCE 的損失家族，實驗僅在 CIFAR-10/100、Fashion-MNIST 合成雜訊上。— [C] Zhang & Sabuncu, NeurIPS 2018 (arXiv 1805.07836) [https://arxiv.org/abs/1805.07836](https://arxiv.org/abs/1805.07836)（存取 2026-10-30）
  - 公式（**本報告依原論文常見寫法轉述，未逐字核對全文**）：L_q = (1 − p_y^q)/q，q→0 趨近 CCE，q = 1 等於 MAE（常用 q = 0.7）。
- **Confident learning / cleanlab**：估計「觀察（雜訊）標籤 × 未知真實標籤」的聯合分佈，建立在 class-conditional noise 假設上；輸入為預測機率與雜訊標籤，計數成 confident joint 後找出/剪除疑似錯標；在 CIFAR 上勝過 7 種方法，並應用於 ImageNet 找出錯標。— [C] Northcutt, Jiang, Chuang, JAIR 70:1373–1411 (2021), doi 10.1613/jair.1.12125 [https://jair.org/index.php/jair/article/view/12125](https://jair.org/index.php/jair/article/view/12125)；[https://arxiv.org/abs/1911.00068v4](https://arxiv.org/abs/1911.00068v4)（搜尋摘要，存取 2026-10-30）
- **cleanlab `find_label_issues` 文件**：「Returned label issues are most accurate when they are computed based on out-of-sample pred_probs」，並建議以交叉驗證取得；`filter_by` 選項含 `prune_by_noise_rate`（預設）、`prune_by_class`、`both`、`confident_learning`、`predicted_neq_given`、`low_normalized_margin`、`low_self_confidence`；`min_examples_per_class`（預設 1）用來避免在稀有類別刪掉太多資料；回傳布林遮罩或依品質分數排序的索引。文件語氣是「filter/prune」，**並未**建議人工複核。— [E] cleanlab docs, cleanlab.filter [https://docs.cleanlab.ai/stable/cleanlab/filter.html](https://docs.cleanlab.ai/stable/cleanlab/filter.html)（存取 2026-10-30）
- **Ordinal soft labels (SORD)**：把序位類別轉成軟機率分佈，搭配一般 cross-entropy 即可學到類內/類間序位關係，不需改架構，與專門的序位迴歸方法競爭力相當（任務：影像品質排序、年齡估計、地平線、深度）。— [C] Díaz & Marathe, "Soft Labels for Ordinal Regression," CVPR 2019, doi 10.1109/CVPR.2019.00487 [https://openaccess.thecvf.com/content_CVPR_2019/html/Diaz_Soft_Labels_for_Ordinal_Regression_CVPR_2019_paper.html](https://openaccess.thecvf.com/content_CVPR_2019/html/Diaz_Soft_Labels_for_Ordinal_Regression_CVPR_2019_paper.html)（搜尋摘要，存取 2026-10-30）
  - 公式（**本報告依原論文常見寫法轉述**）：y_i = exp(−φ(r_t, r_i)) / Σ_k exp(−φ(r_t, r_k))，φ 例如 α·(r_t − r_i)²。
- **綜述**：Song et al. 回顧 62 種深度網路抗雜訊訓練方法並分為五大類。— [B] Song, Kim, Park, Shin, Lee, "Learning from noisy labels with deep neural networks: A survey," IEEE TNNLS 34(11):8135–8153, doi 10.1109/TNNLS.2022.3152527 [https://arxiv.org/abs/2007.08199](https://arxiv.org/abs/2007.08199)（搜尋摘要，存取 2026-10-30）

### Inferences
- **本報告推論**：本專案的 ordinal 分期（normal < stage 1 < stage 2）可用 SORD 式軟標籤取代 one-hot。以 φ = α·|Δ|² 舉例：α = 1 時，真實為 stage 1 的目標分佈 ≈ [0.21, 0.58, 0.21]；真實為 normal 的目標 ≈ [0.72, 0.27, 0.01]（exp(0)=1, exp(−1)=0.368, exp(−4)=0.018，正規化）。這把「normal 誤判為 stage 2」的懲罰設得比「誤判為 stage 1」更重，符合臨床上相鄰期別本來就難以區分的雜訊結構（相鄰期別錯標的機率較高）。
- **本報告推論**：label smoothing 與 SORD 只改「目標分佈」，不依賴 memorization 動態或雜訊率，對 56 張樣本仍可使用；但其效益不應預期大於 CV 誤差（見 Part 2-E，±10–25%）。
- **本報告推論**：cleanlab 文件傾向「刪除」，與專案規則（只能人工複核、不得自動改標/刪除）衝突；使用時應僅呼叫 `find_label_issues(..., return_indices_ranked_by='self_confidence')` 產生排序清單送人工複核，不使用 `cleanlab.classification.CleanLearning` 的自動剪除再訓練流程。

### Gaps
- Szegedy 2016（Inception-v3 原始 LS）、Co-teaching+（Yu et al. 2019）、DivideMix（Li et al. 2020）、SCE（Wang et al. 2019）、bootstrapping loss（Reed et al. 2015）、ELR（Liu et al. 2020）、mixup（Zhang et al. 2018）本輪皆**未開啟原文核對**（第二輪全文擷取遭速率限制中斷）；co-teaching R(T) 與 GCE 公式細節亦未逐字核對。報告撰寫者若需引用這些方法的具體公式/超參數，應註明「未核對」或另行核對。

---

## Part 1-B：醫學影像中的證據，含失敗/負面/增益可忽略的證據

### Takeaway
**研究證據顯示**：在真實（非合成）醫學影像雜訊上，現有抗雜訊方法表現常不如或僅等同於普通 cross-entropy；sample-selection 方法對類別不平衡敏感；且「少量乾淨標籤」可與「大量雜訊標籤」打平。對小資料專案，投資在標註品質（雙人判讀/仲裁）比換演算法更有證據支持。

### Cited Findings
- **Karimi et al. 2020 回顧 + 三個醫學資料集實驗**：[B] Karimi, Dou, Warfield, Gholipour, "Deep learning with noisy labels: exploring techniques and remedies in medical image analysis," Med Image Anal 65:101759 (2020), doi 10.1016/j.media.2020.101759 [https://ar5iv.labs.arxiv.org/html/1912.02911](https://ar5iv.labs.arxiv.org/html/1912.02911)（全文前 100k 字元，存取 2026-10-30）
  - 作者指出 label-noise 方法的進展「largely unnoticed」於醫學影像社群（abstract，見 [https://arxiv.org/abs/1912.02911v4](https://arxiv.org/abs/1912.02911v4)）。
  - TSC 腦部病灶（165 scans / 88 subjects；僅 12 scans 重新仔細標註為乾淨集，153 為雜訊集；初讀約 18% 病灶被漏標）：iterative label cleaning 最佳（3D U-Net lesion-count F1 0.819、DSC 0.605 vs baseline 0.747 / 0.584）；data re-weighting（忽略高 loss 樣本）F1 0.802。
  - 關鍵句：「a small dataset with clean labels can be as good as a large dataset with noisy labels」——12 scans 乾淨集訓練 F1 0.743，約等於 153 scans 雜訊集的 0.747。
  - **負面證據**：MAE 與 iMAE loss 讓 3D U-Net 分割變差（F1 0.695 / 0.657 vs DSC loss 0.747）；Faster-RCNN 偵測則 MAE 提升 F1 +0.041。
  - Gleason2019 病理（6 位病理師，Cohen κ ≈ 0.40–0.60）：annotator confusion estimation 在高/低分級分類準確率最佳（0.80）。
  - 胎兒腦分割：最低雜訊下，雜訊 baseline（DSC 0.889）勝過小約 40 倍的乾淨集訓練（0.878）。
  - 回顧部分：胸部 X 光中「label smoothing can lead to improvements of up to 0.08」AUC（相對於直接忽略雜訊樣本）；引用研究指出「co-teaching was less effective as the label noise increased」；皮膚病灶分類中 re-weighting 類方法報告約 2–10% 增益。
- **LNMBench（2025 醫學影像雜訊標籤基準）**：[D] Ma, Hou, Zhang, Zhou, Ge, Xie, Ju, arXiv 2512.09315 [https://arxiv.org/html/2512.09315](https://arxiv.org/html/2512.09315)（存取 2026-10-30）
  - 比較 10 種方法 + CE：T-Revision、VolMinNet、SCE、CDR、Co-teaching、Co-teaching+、CoDis、JoCoR、DISC、DivideMix（**未**含 GCE、ELR、獨立 label smoothing）。
  - 結論原句：「Current LNL methods perform poorly on real-world medical datasets, in some cases even underperforming standard CE model.」
  - Kaggle DR+（真實雜訊）：CE best 70.73，**沒有任何方法勝過 CE**（CDR 70.19、SCE 66.13）。DRTiD（3,100 張，5 級 DR）：Co-teaching 以驗證集選模的準確率 36.86，低於 CE 的 46.36（last-5-epoch）。CheXpert：SCE 48.96 最佳，sample-selection 方法表現差。
  - 類別不平衡：DermaMNIST（10,015 張，7 類）Idn-20% 下 CE 80.60、Co-teaching 74.36、DISC 80.35——sample-selection / semi-supervised 方法**低於 CE**；作者：「the effectiveness of sample selection-based methods is sensitive to class imbalance」。
  - 驗證集選模落差：很多方法「best」與「validation-selected」差距大（例：CE PathMNIST Sym-20% 94.40 → 91.34）。
  - 本基準最小資料集也有 3,100 張，**沒有**分析小訓練集情境。
- **DivideMix 在 DermaMNIST 的特異度崩潰**：一篇 2026 年預印本報告 DivideMix 與 UNICON 呈現 sensitivity > 0.97 但 specificity 下降，作者解讀為 prediction collapse。— [D] arXiv 2604.23875 "Risk-Aware Robust Learning: Reducing Clinical Risk under Label Noise in Medical Image Classification" [https://arxiv.org/html/2604.23875](https://arxiv.org/html/2604.23875)（**僅搜尋摘要，未開啟全文**，存取 2026-10-30）
- 皮膚病灶 ISIC 的 co-teaching 變體（例如 ISIC-2017 約 3,582 張訓練、合成雜訊）報告勝過其他方法，但皆為提出新方法的作者自評。— [C] Springer IJCARS 2022 "Robust co-teaching learning with consistency-based noisy label correction" [https://link.springer.com/article/10.1007/s11548-022-02799-6](https://link.springer.com/article/10.1007/s11548-022-02799-6)；[D] arXiv 1901.07759 [https://arxiv.org/pdf/1901.07759](https://arxiv.org/pdf/1901.07759)（皆搜尋摘要層級）

### Inferences
- **本報告推論**：本專案 normal 僅 9 張；若 3-fold CV 每折訓練約 6 張 normal、batch size 16，co-teaching 每 batch 期望 normal 數 < 2，再丟掉 τ 比例的「大 loss」樣本，極可能把少數類（正是最難、loss 最大的 normal 或邊界期別）當雜訊丟掉——這正是 LNMBench 觀察到的「對類別不平衡敏感」機制的極端版。DivideMix 需以 GMM 將 loss 分佈切成乾淨/雜訊兩群再做 MixMatch 半監督，每類數個樣本無法穩定擬合 GMM；且其產生的偽標籤違反「未經人工確認不得寫入偽標籤」原則（即使只在記憶體內使用，也屬於以模型自產標籤訓練）。
- **本報告推論**：最符合證據的路線是 Karimi 的「小而乾淨」：對有疑義的照片做雙人獨立判讀 + 仲裁，而不是演算法去雜訊。
- **未找到可靠證據**：在 < 200 張訓練影像的醫學影像分類任務上，直接比較 co-teaching / DivideMix / GCE 與 CE 的對照研究。

### Gaps
- 未找到明確以「小資料集（數十至數百張）」為條件的抗雜訊方法失敗研究；目前的負面證據來自數千張以上的基準（LNMBench）與 Karimi 的實驗，外推到 56 張屬推論。
- 2604.23875 僅見搜尋摘要，數字未核對。

---

## Part 1-C：凍結骨幹 + 線性/logistic 頭時，哪些方法仍適用

### Takeaway
**本報告推論**：凍結 DINOv2 / EfficientNet-B0 特徵 + logistic regression 是凸最佳化、無 memorization 動態可利用，co-teaching / DivideMix / ELR / 早停類方法失去理論依據；仍適用的是 (1) class weight、(2) label smoothing / ordinal soft label（需以樣本權重技巧實作）、(3) 以病人分組 out-of-fold 預測機率做 cleanlab 式不一致排序（只送人工複核）、(4) 強正則化（調 C）。

### Cited Findings
- 抗雜訊方法共同依據「memorization effect」（深網路先學乾淨樣本）。— [C] Han et al. 2018 [https://arxiv.org/abs/1804.06872](https://arxiv.org/abs/1804.06872)
- cleanlab 需要 out-of-sample pred_probs（建議交叉驗證），與分類器種類無關。— [E] [https://docs.cleanlab.ai/stable/cleanlab/filter.html](https://docs.cleanlab.ai/stable/cleanlab/filter.html)
- LS 的效益包含 calibration 改善。— [C] Müller et al. 2019 [https://arxiv.org/abs/1906.02629](https://arxiv.org/abs/1906.02629)

### Inferences
- **本報告推論（實作方式）**：
  1. **Class weight**：sklearn `LogisticRegression(class_weight='balanced')`；二元 47:9 時 normal 權重 ≈ 56/(2·9)=3.11，positive ≈ 56/(2·47)=0.60。PyTorch 線性頭以 `CrossEntropyLoss(weight=...)` 對應。（**業界慣例**）
  2. **Label smoothing / SORD 用在 sklearn LR**：sklearn LR 不接受軟標籤；可把每張照片複製 K 份，各帶類別 k 與 `sample_weight = y_soft[k]` 後擬合（多項式 LR 的加權 log-loss 等價於軟目標 cross-entropy）。若線性頭以 PyTorch 實作，`CrossEntropyLoss(label_smoothing=ε)` 或直接餵機率目標。
  3. **cleanlab 式複核**：用與正式評估相同的 patient-level StratifiedGroupKFold 產生 OOF pred_probs → `find_label_issues(labels, pred_probs, return_indices_ranked_by='self_confidence')` → 產出複核清單（照片 ID、給定標籤、模型機率、排名）→ 人工判讀後由人寫入。**禁止** `CleanLearning` 自動剪除再訓練。9 張 normal、3-fold 下每折模型只看過約 6 張 normal，pred_probs 本身很不穩定；清單應視為「優先複核順序」而非錯標判定。可重複多次不同 seed 的分組 CV，報告每張被標記的頻率。
  4. **GCE / SCE 套在線性頭**：技術上可行（PyTorch 自訂 loss），但 GCE 在 q>0 時非凸、且無「先學乾淨」動態可依賴；以 56 張樣本無法可靠地證明其增益大於 CV 誤差，**不建議**作為優先項。
  5. **EfficientNet-B0 解凍最後一個 stage**：此時才部分恢復 memorization 動態，early stopping 有意義；但早停所需驗證集必須是病人層級分組、且與報告用測試集分離，否則就是 Vabalas 指出的偏差（Part 2-E）。
  6. **Mixup**：在特徵空間（feature-level mixup）對線性頭可實作，但會在少數類之間產生合成樣本；本輪未找到其在凍結特徵小資料上的證據 → **未找到可靠證據**。

### Gaps
- 未找到「凍結基礎模型特徵 + 線性頭」情境下比較抗雜訊損失的研究。
- sklearn class_weight / LogisticRegression 文件本輪未開啟。

---

## Part 2-A：學習曲線外推與訓練樣本數

### Takeaway
**研究證據顯示**：學習曲線常以 inverse power law（acc(n) = a − b·n^(−c)）擬合並外推，但需要有一定量的已標註樣本與夠大的測試集才能看見曲線；Beleites 指出測試不確定性會「淹沒」學習曲線，而訓練所需樣本遠少於可靠測試所需樣本。醫學影像 ML 很少正式做樣本數規劃（Balki：22 篇中僅 4 篇討論方法）。

### Cited Findings
- **Figueroa et al. 2012**：以小量標註資料建立學習曲線，用 nonlinear weighted least squares 擬合 inverse power law，預測更大樣本時的表現與信賴區間；在臨床文本與波形分類上，依資料集與抽樣方式，需 80–560 個標註樣本才能讓外推的 mean absolute error 與 RMSE < 0.01；加權法優於未加權法。— [C] BMC Med Inform Decis Mak 12:8 (2012) [https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3307431/](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3307431/)（搜尋摘要，存取 2026-10-30）
- **Cho et al. 2015**：CNN 對軸向 CT 做 6 類解剖部位分類，訓練集每類 5、10、20、50、100、200 張，測試 6,000 張（MGH PACS），以學習曲線預測給定訓練量下的準確率。次級摘要站稱「約 4,092 張/類可達近乎完美」——**此數字未能在原文核對，勿引用**。— [D] arXiv 1511.06348 [https://arxiv.org/pdf/1511.06348](https://arxiv.org/pdf/1511.06348)（搜尋摘要，存取 2026-10-30）
- **Beleites et al. 2013**：研究每類約 5–25 個獨立樣本的小樣本情境；有限測試集的隨機不確定性可掩蓋學習曲線；驗證一個「好但不完美」的分類器通常需要約 75–100 個測試樣本；測試樣本數應依目標 CI 寬度或要比較的模型來定；測試需要的樣本遠多於訓練；建議起步至少每類 75 例再依表現修正。— [C] Anal Chim Acta 760:25–33 (2013), doi 10.1016/j.aca.2012.11.007 [https://arxiv.org/abs/1211.1323](https://arxiv.org/abs/1211.1323)（搜尋摘要，存取 2026-10-30）
- **Balki et al. 2019 系統性回顧**：Medline/Embase 1946–2018，167 篇中納入 22 篇；僅 4 篇討論樣本數決定方法，18 篇以探索性分析測試樣本數對表現的影響；呼籲標準化報告。— [B] Can Assoc Radiol J 70(4):344–353, doi 10.1016/j.carj.2019.06.002 [https://www.pubmed.gov/31522841/](https://www.pubmed.gov/31522841/)（搜尋摘要，存取 2026-10-30）

### Inferences
- **本報告推論 (computed，合成資料示範，非專案資料)**：設真實曲線 acc(n) = 0.85 − 1.0·n^(−0.5)，在 n = 10, 20, 30, 40, 56 各加上「測試集 19 張」等級的二項雜訊後擬合 inverse power law，外推到 n = 500：真值 0.805，2,000 次模擬外推中位數 0.773，95% 範圍 [0.596, 0.953]。也就是說，**以目前規模擬合學習曲線外推的不確定性約 ±18 個百分點**，不足以做決策；學習曲線在本階段只適合作「定性檢查是否仍在上升」。
- **本報告推論**：做學習曲線時，每個訓練量的評估都要用病人分組 OOF，並以重複不同 seed 平均；子抽樣也必須以病人為單位。

### Gaps
- Rokem 等人的子抽樣研究本輪未找到/未開啟。
- Figueroa 加權法的權重公式本輪未開啟全文核對。

---

## Part 2-B：預測模型開發/驗證樣本數（Riley）與診斷準確度樣本數（Buderer 等）

### Takeaway
**研究證據顯示**：Riley 系列（BMJ）主張以模型/情境量身計算取代經驗法則，外部驗證的經典經驗法則是至少 100 events + 100 non-events（c statistic）、200 + 200（calibration plot），但作者認為這些法則有問題；以 Riley 的 covid 範例，calibration slope 的精度需求主導，達 949 人。診斷準確度則用 Buderer 式：n = z²·Sp(1−Sp)/d²（對 normal），再依盛行率換算總數。本專案的規模比這些門檻小一到兩個數量級。

### Cited Findings
- **Riley et al. 2024（BMJ 2024;384:e074821，外部驗證樣本數）**：四項準則——O/E（calibration-in-the-large）、calibration slope、c statistic、standardised net benefit；假設 95% CI 寬 ≈ 2×1.96×SE；範例目標 CI 寬：c statistic 0.1、calibration slope 0.3、net benefit 0.2、O/E 0.22（Stata 範例程式卻寫 `oeciwidth(.12)`，文中與程式不一致）。經驗法則「at least 100 events and 100 non-events」與 calibration plot 200+200，被作者評為「problematic」。covid-19 範例（盛行率 0.43、c 0.77）：O/E 需 423 人、calibration slope 949 人（408 events）、c statistic 347 人、net benefit@0.1 38 人、@0.3 407 人；calibration slope CI 寬改為 0.2 時需 2,137 人；5% 缺失時膨脹為 999 人。該文**未**涵蓋 sensitivity/specificity，也**未**處理 clustering。— [B] [https://pmc.ncbi.nlm.nih.gov/articles/PMC11778934/](https://pmc.ncbi.nlm.nih.gov/articles/PMC11778934/)（存取 2026-10-30）
- 套件 `pmvalsampsize`（R/Stata）實作上述方法，目前只支援二元結果。— [E] [https://cran.r-universe.dev/pmvalsampsize/doc/manual.html](https://cran.r-universe.dev/pmvalsampsize/doc/manual.html)（搜尋摘要）
- 延伸到 threshold-based 指標（sensitivity、specificity、PPV、NPV、F1）的預印本：Whittle et al. 2024, arXiv 2406.19673。— [D] [https://web3.arxiv.org/pdf/2406.19673](https://web3.arxiv.org/pdf/2406.19673)（**僅搜尋摘要提及，未開啟**）
- **Riley et al. 2020（BMJ，開發樣本數）**：目標是讓模型方程式在新個體上可靠，準則為最小化 overfitting 並精確估計關鍵參數；`pmsampsize` 預設 shrinkage 0.9（係數需縮 10%）；二元結果可用 C-statistic 與盛行率近似 Cox-Snell R²；文件範例 C 0.89、盛行率 0.174、24 個候選參數。— [B] [https://dspace.library.uu.nl/handle/1874/457642](https://dspace.library.uu.nl/handle/1874/457642)；[E] [https://rdrr.io/cran/pmsampsize/man/pmsampsize.html](https://rdrr.io/cran/pmsampsize/man/pmsampsize.html)（搜尋摘要）
- **Buderer 1996**：依臨床可接受精度、假設的 sensitivity/specificity 與目標族群盛行率計算樣本數。— [C] Acad Emerg Med 3(9):895–900, doi 10.1111/j.1553-2712.1996.tb03538.x（搜尋摘要）；R 套件 SampleSizeDiagnostics 實作，取 sensitivity 與 specificity 兩者所需樣本數的較大者。— [E] [https://cran.r-project.org/web/packages/SampleSizeDiagnostics/refman/SampleSizeDiagnostics.html](https://cran.r-project.org/web/packages/SampleSizeDiagnostics/refman/SampleSizeDiagnostics.html)（搜尋摘要）
  - 公式（**業界慣例**的 Buderer 寫法，原文本輪未開啟）：n_disease = z²·Se(1−Se)/d²，N = n_disease/prev；n_normal = z²·Sp(1−Sp)/d²，N = n_normal/(1−prev)。

### Inferences
- **本報告推論 (computed)**，Buderer 式 normal 數（iid 照片 → 套 DE 2.2 [m=5, ICC 0.3]）：
  | 假設 Sp | 半寬 d | n_normal（iid） | ×DE 2.2 照片數 |
  |---|---|---|---|
  | 0.90 | ±0.05 | 139 | 305 |
  | 0.90 | ±0.10 | 35 | 77 |
  | 0.95 | ±0.05 | 73 | 161 |
  | 0.80 | ±0.10 | 62 | 136 |
- **本報告推論**：pmsampsize 的「開發」準則針對有明確候選參數的回歸模型；凍結特徵 + LR 的參數數為 384（DINOv2-small）×類別數，遠超樣本數，正式套用會得到不可達的數字——只能作為「目前資料量遠未達穩定開發門檻」的定性說明；本專案更適合採用 Riley/Buderer 的**評估精度**觀點：先定 CI 寬度目標，再推算所需測試病人數。
- **Obuchowski、Flahault 2005**：本輪未檢索到 → Gaps。

### Gaps
- Flahault et al. 2005（J Clin Epidemiol）與 Obuchowski 的 clustered ROC / 樣本數文獻本輪未開啟。
- Riley 2024 Figure 3 的 SE 公式為圖片，未擷取。

---

## Part 2-C：CI 寬度公式（Wilson、balanced accuracy、FPR、macro-F1、per-class recall）與群集校正

### Takeaway
小 n 比例用 Wilson（或 Jeffreys）區間，Wald 不可靠；同一病人多張照片相關，必須以 n_eff = n / [1 + (m−1)·ICC] 校正，或直接做病人層級 cluster bootstrap。m = 5、ICC = 0.3 時 DE = 2.2，相當於有效樣本少一半以上。

### Cited Findings
- Brown, Cai, DasGupta 2001：Wald 區間覆蓋率「chaotic」且教科書的安全建議不可信；小 n 推薦 Wilson 或等尾 Jeffreys，大 n 推薦 Agresti–Coull；大 n 時三者相近；Wilson interval 源自 Wilson (1927)。— [B] Stat Sci 16(2):101–133, doi 10.1214/ss/1009213286 [https://projecteuclid.org/euclid.ss/1009213286](https://projecteuclid.org/euclid.ss/1009213286)（搜尋摘要，存取 2026-10-30）
- Varoquaux 指出相關觀測（correlated observations）會讓實際誤差界比二項近似更大。— [B] [https://ar5iv.labs.arxiv.org/html/1706.07581](https://ar5iv.labs.arxiv.org/html/1706.07581)

### Inferences（公式，**業界慣例**；數值為 **本報告推論 (computed)**）
- **Wilson 95%**（z = 1.96，p̂ = x/n）：
  center = (p̂ + z²/(2n)) / (1 + z²/n)
  half-width = [z / (1 + z²/n)] · sqrt( p̂(1−p̂)/n + z²/(4n²) )
  x = 0 時上界 = z²/(n + z²)。
- **Clopper–Pearson**：下界 Beta(α/2; x, n−x+1)，上界 Beta(1−α/2; x+1, n−x)。**Jeffreys**：Beta(·; x+0.5, n−x+0.5) 分位數。
- **Normal-photo FPR** = FP_normal / n_normal = 1 − specificity（只在 normal 照片上計算）→ 直接用 Wilson，n 用 n_eff。
- **Per-class recall** = TP_c / n_c → Wilson on n_eff,c。
- **Balanced accuracy**：二元 BA = (Se + Sp)/2，Var ≈ [Se(1−Se)/n_eff,pos + Sp(1−Sp)/n_eff,neg]/4；三類 BA = 平均 recall，Var ≈ Σ_c r_c(1−r_c)/n_eff,c / 9（假設各類由不同病人構成而近似獨立；若同一病人跨類別，需 cluster bootstrap）。
- **Macro-F1**：無簡單封閉式（F1 牽涉 FP 跨類別），用**病人層級** cluster bootstrap（以病人為單位重抽，≥2,000 次，percentile 或 BCa）。
- **群集校正**：DE = 1 + (m−1)·ICC；n_eff = n / DE。模擬驗證（beta-binomial，p = 0.8，m = 5，ICC = 0.3）：10/20/40 位病人時，經驗 SD 0.0832 / 0.0597 / 0.0416，DE 公式 SD 0.0839 / 0.0593 / 0.0420，iid 公式 SD 0.0566 / 0.0400 / 0.0283 → **DE 公式準確，iid 低估約 32%**。
- **n = 100 張照片的 n_eff**：
  | m（張/病人） | ICC 0.2 | ICC 0.5 | ICC 0.8 |
  |---|---|---|---|
  | 5 | DE 1.80 → n_eff 55.6 | DE 3.00 → 33.3 | DE 4.20 → 23.8 |
  | 8.5（目前） | DE 2.50 → 40.0 | DE 4.75 → 21.1 | DE 7.00 → 14.3 |
- **本報告推論**：目前每位病人約 8.5 張，即使 ICC 只有 0.2，有效樣本也只剩 40%；**每位病人拍越多張，邊際資訊越少**——未來收案時「多病人、每人少張」比「少病人、每人多張」有效得多。

### Gaps
- 未找到靜脈炎或皮膚照片情境下「同一病人照片間分類正確與否的 ICC」實測值；0.2/0.5/0.8 為情境假設。可在現有 OOF 預測上以病人為群估計（但 14 人估 ICC 本身極不穩定）。
- statsmodels `proportion_confint` 文件本輪未開啟（專案 venv 也未安裝 statsmodels；本報告以 scipy.stats.beta 自行實作）。

---

## Part 2-D：Worked examples (a)–(d)（全部為 本報告推論 (computed)）

### Takeaway
目前 9 張 normal：即使 0 次誤報，Wilson 95% 上界仍為 29.9%（CP 33.6%）；1/9 誤報時區間 [2.0%, 43.5%]。要讓 0 誤報時上界 ≤ 10% 需 ≥ 35 張「有效」normal 照片，≤ 5% 需 ≥ 73 張；換算群集後（m = 5、ICC 0.5）約 21 位與 44 位 normal 病人。若真實 FPR = 5%，要以 80% 把握讓上界 ≤ 10%，需約 217 張有效 normal 照片。

### Cited Findings
- 計算方法依據 Wilson / Clopper-Pearson / Jeffreys（Brown, Cai, DasGupta 2001 [B] [https://projecteuclid.org/euclid.ss/1009213286](https://projecteuclid.org/euclid.ss/1009213286)）與 Buderer 1996 [C]（見 Part 2-B）。
- 環境：專案 venv Python（scipy 1.18.1、numpy 2.5.2），腳本 `C:\Users\user\AppData\Local\Temp\claude\C--Users-user-Desktop-Phlebitis\65222311-7d94-4b7e-9464-8d7c78613042\scratchpad\ci_calc.py`（暫存區，完整程式碼附於本節末），亂數種子 20261030。

### Inferences

**(a) 目前：9 張 normal 照片的 FPR 95% CI**
| 誤報 | 點估計 | Wilson | 寬度 | Clopper-Pearson | Jeffreys |
|---|---|---|---|---|---|
| 0/9 | 0.000 | [0.000, 0.299] | 0.299 | [0.000, 0.336] | [0.000, 0.238] |
| 1/9 | 0.111 | [0.020, 0.435] | 0.415 | [0.003, 0.482] | [0.012, 0.414] |
| 2/9 | 0.222 | [0.063, 0.547] | 0.484 | [0.028, 0.600] | [0.049, 0.544] |

若 9 張 normal 來自少數病人（ICC 0.5）：
| normal 病人數 k | m | DE | n_eff | 0 誤報上界 | 1/9 觀察的 CI |
|---|---|---|---|---|---|
| 9 | 1.0 | 1.00 | 9.00 | 0.299 | [0.020, 0.435] |
| 5 | 1.8 | 1.40 | 6.43 | 0.374 | [0.016, 0.498] |
| 3 | 3.0 | 2.00 | 4.50 | 0.461 | [0.012, 0.569] |
| 2 | 4.5 | 2.75 | 3.27 | 0.540 | [0.009, 0.633] |

Held-out 25–30% 病人（≈ 14–18 張）時，normal 可能只有 2–3 張：0/2 的 Wilson 上界 = 3.84/5.84 = 0.658；0/3 = 3.84/6.84 = 0.561——held-out 集對 FPR 幾乎沒有資訊量，**本報告推論**：目前階段應以 pooled patient-level OOF（全部 9 張 normal）報告 FPR，並明列 held-out 結果僅供參考。

**(b) 未來：約 1,000 張、3 類平衡（≈333/類）、5 張/病人（≈200 人）、ICC 0.3（DE = 1 + 4×0.3 = 2.2）**
| 測試比例 | 測試病人 | 照片/類 | n_eff/類 | recall 0.7 | recall 0.8 | recall 0.9 |
|---|---|---|---|---|---|---|
| 20% | 40 | 66.7 | 30.3 | [0.522, 0.833] ±0.155（iid ±0.108） | [0.628, 0.905] ±0.138（iid ±0.095） | [0.745, 0.965] ±0.110（iid ±0.073） |
| 25% | 50 | 83.3 | 37.9 | [0.541, 0.822] ±0.140（iid ±0.097） | [0.648, 0.897] ±0.124（iid ±0.085） | [0.765, 0.961] ±0.098（iid ±0.065） |
| 30% | 60 | 100.0 | 45.5 | [0.556, 0.813] ±0.129（iid ±0.088） | [0.663, 0.891] ±0.114（iid ±0.078） | [0.779, 0.958] ±0.089（iid ±0.060） |

→ 即使 1,000 張，30% held-out 的 per-class recall 仍約 ±11–13 個百分點；忽略群集會低估半寬約 1/3。

**(c) 依總病人數 N 的期望 95% 半寬（所有病人經 pooled OOF 各評估一次）**
假設：FPR = 0.10（Sp 0.90）、二元 Se = 0.85、各類 recall = 0.80；比例用 Wilson on n_eff，BA 用 Wald on n_eff。BA2 = 二元 balanced accuracy、BA3 = 三類 balanced accuracy。**若改用 held-out 25%，請查 0.25N 那一列**（例：N = 200 → 看 N = 50 列）。

情境 1：目前樣態（m = 8.5、ICC 0.3、DE 3.25、normal 佔 16% = 9/56，其餘兩期各半）
| N 病人 | 照片 | normal 照片 | n_eff normal | FPR ± | 每期 recall ± | BA2 ± | BA3 ± |
|---|---|---|---|---|---|---|---|
| 14 | 119 | 19.1 | 5.9 | 0.246 | 0.189 | 0.137 | 0.143 |
| 30 | 255 | 41.0 | 12.6 | 0.172 | 0.133 | 0.093 | 0.098 |
| 50 | 425 | 68.3 | 21.0 | 0.133 | 0.104 | 0.072 | 0.076 |
| 100 | 850 | 136.6 | 42.0 | 0.093 | 0.074 | 0.051 | 0.054 |
| 200 | 1700 | 273.2 | 84.1 | 0.065 | 0.053 | 0.036 | 0.038 |
| 300 | 2550 | 409.8 | 126.1 | 0.053 | 0.043 | 0.030 | 0.031 |
（N = 14 列以「16% normal」外推為 19 張 normal；實際只有 9 張，故實際 FPR 半寬比表中更大，見 (a)。）

情境 2：未來平衡（m = 5、3 類各 1/3），ICC 敏感度
| N 病人 | 照片 | ICC 0.2 (DE 1.8) FPR± / recall± / BA2± / BA3± | ICC 0.3 (DE 2.2) | ICC 0.5 (DE 3.0) | ICC 0.8 (DE 4.2) |
|---|---|---|---|---|---|
| 14 | 70 | 0.170 / 0.203 / 0.107 / 0.126 | 0.188 / 0.221 / 0.118 / 0.139 | 0.217 / 0.250 / 0.138 / 0.162 | 0.252 / 0.284 / 0.163 / 0.192 |
| 30 | 150 | 0.115 / 0.144 / 0.073 / 0.086 | 0.128 / 0.158 / 0.081 / 0.095 | 0.150 / 0.182 / 0.094 / 0.111 | 0.177 / 0.211 / 0.111 / 0.131 |
| 50 | 250 | 0.089 / 0.113 / 0.056 / 0.067 | 0.098 / 0.124 / 0.062 / 0.074 | 0.115 / 0.144 / 0.073 / 0.086 | 0.137 / 0.168 / 0.086 / 0.102 |
| 100 | 500 | 0.062 / 0.081 / 0.040 / 0.047 | 0.069 / 0.089 / 0.044 / 0.052 | 0.081 / 0.104 / 0.052 / 0.061 | 0.096 / 0.122 / 0.061 / 0.072 |
| 200 | 1000 | 0.044 / 0.057 / 0.028 / 0.033 | 0.048 / 0.063 / 0.031 / 0.037 | 0.056 / 0.074 / 0.036 / 0.043 | 0.067 / 0.087 / 0.043 / 0.051 |
| 300 | 1500 | 0.035 / 0.047 / 0.023 / 0.027 | 0.039 / 0.052 / 0.025 / 0.030 | 0.046 / 0.060 / 0.030 / 0.035 | 0.054 / 0.071 / 0.035 / 0.041 |

Macro-F1（3 類、各 recall 0.80、錯誤平均分到其他兩類、m = 5、ICC 0.3；模擬抽樣分佈，4,000 次）：
| 病人/類 | 照片/類 | 平均 macro-F1 | SD | 中央 95% 範圍 | ± |
|---|---|---|---|---|---|
| 3 | 15 | 0.798 | 0.091 | [0.603, 0.955] | 0.176 |
| 5 | 25 | 0.798 | 0.069 | [0.652, 0.920] | 0.134 |
| 10 | 50 | 0.798 | 0.050 | [0.699, 0.887] | 0.094 |
| 20 | 100 | 0.799 | 0.035 | [0.729, 0.863] | 0.067 |
| 40 | 200 | 0.800 | 0.024 | [0.753, 0.845] | 0.046 |
| 67 | 335 | 0.800 | 0.018 | [0.764, 0.835] | 0.036 |

**(d) 要讓 normal FPR 的 95% 上界 ≤ 10% 或 ≤ 5% 需要多少 normal 照片/病人**
觀察到 0 次誤報時（iid 有效照片數）：
| 目標上界 | Rule of three (3/n) | Wilson | Clopper-Pearson 雙尾 95% | CP 單尾 95% |
|---|---|---|---|---|
| ≤ 10% | 30 | 35 | 36 | 29 |
| ≤ 5% | 60 | 73 | 72 | 59 |
（Rule of three 對應的是**單尾** 95% 上界，所以數字接近 CP 單尾；若報告的是雙尾 95% CI，應用 Wilson/CP 雙尾的 35/73。Wilson 0 事件封閉式：n ≥ z²(1/U − 1) → 3.8416×9 = 34.6 → 35；3.8416×19 = 73。）

若真實 FPR 不為 0，以 80% 把握（assurance）讓上界 ≤ 目標：
| 真實 FPR | 目標上界 | Wilson n | CP n |
|---|---|---|---|
| 1% | ≤ 5% | 142 | 142 |
| 2% | ≤ 5% | 311 | 312 |
| 2% | ≤ 10% | 69 | 70 |
| 5% | ≤ 10% | 217 | 231 |

群集換算（normal 照片來自 normal 病人；所需照片 = n_eff × DE，病人 = 照片/m）：
| 需要的 n_eff | m | ICC 0.2 | ICC 0.5 | ICC 0.8 |
|---|---|---|---|---|
| 35（≤10%） | 5 | 63 張 / 13 人 | 105 張 / 21 人 | 147 張 / 30 人 |
| 35（≤10%） | 8.5 | 88 張 / 11 人 | 166 張 / 20 人 | 245 張 / 29 人 |
| 73（≤5%） | 5 | 131 張 / 27 人 | 219 張 / 44 人 | 307 張 / 62 人 |
| 73（≤5%） | 8.5 | 182 張 / 22 人 | 347 張 / 41 人 | 511 張 / 61 人 |

**本報告推論**：(1) 病人數下限主要由 ICC 決定而不是由 m 決定（ICC 高時每人多拍幾乎無用）；(2) 「0 誤報」是最樂觀情境，若真實 FPR ≈ 5%，要宣稱 FPR < 10% 需要數百張有效 normal 照片；(3) 目前 9 張 normal 下，任何「FPR 低」的說法都必須附上「上界約 30%」。

<details><summary>完整腳本 ci_calc.py（本報告推論 (computed)）</summary>

```python
"""CI-width / sample-size worked examples for phlebitis research notes (2026-10-30).
All numbers are 本報告推論 (computed). No real model outputs are used.
"""
import math
import numpy as np
from scipy import stats
from scipy.optimize import curve_fit

Z = stats.norm.ppf(0.975)  # 1.959964


def wilson(x, n, z=Z):
    if n <= 0:
        return (float('nan'),) * 2
    p = x / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, c - h), min(1.0, c + h)


def clopper_pearson(x, n, a=0.05):
    lo = 0.0 if x == 0 else stats.beta.ppf(a / 2, x, n - x + 1)
    hi = 1.0 if x == n else stats.beta.ppf(1 - a / 2, x + 1, n - x)
    return lo, hi


def jeffreys(x, n, a=0.05):
    lo = 0.0 if x == 0 else stats.beta.ppf(a / 2, x + 0.5, n - x + 0.5)
    hi = 1.0 if x == n else stats.beta.ppf(1 - a / 2, x + 0.5, n - x + 0.5)
    return lo, hi


def deff(m, icc):
    return 1 + (m - 1) * icc


def wilson_halfwidth_eff(p, n_eff):
    """Wilson CI half-width evaluated at observed p with effective n (non-integer ok)."""
    lo, hi = wilson(p * n_eff, n_eff)
    return (hi - lo) / 2


print("=" * 70)
print("(a) Current: 9 normal photos, FPR = FP/9")
print("=" * 70)
for x in (0, 1, 2):
    w = wilson(x, 9); cp = clopper_pearson(x, 9); j = jeffreys(x, 9)
    print(f"{x}/9  point={x/9:.3f}  Wilson=[{w[0]:.3f},{w[1]:.3f}] width={w[1]-w[0]:.3f}  "
          f"CP=[{cp[0]:.3f},{cp[1]:.3f}]  Jeffreys=[{j[0]:.3f},{j[1]:.3f}]")
# If the 9 normal photos come from few patients, n_eff shrinks
print("\n  Cluster sensitivity: 9 normal photos, if from k patients (m=9/k), ICC 0.5")
for k in (9, 5, 3, 2):
    m = 9 / k; de = deff(m, 0.5); ne = 9 / de
    lo, hi = wilson(1 / 9 * ne, ne)
    lo0, hi0 = wilson(0, ne)
    print(f"  k={k} patients m={m:.1f} DE={de:.2f} n_eff={ne:.2f}  0 FP upper={hi0:.3f}  1/9 obs -> [{lo:.3f},{hi:.3f}]")

print("\n" + "=" * 70)
print("(b) Future: ~1000 photos, 3 balanced classes, 5 photos/patient (~200 patients), ICC 0.3")
print("=" * 70)
m, icc = 5, 0.3
de = deff(m, icc)
print(f"DE = 1+(m-1)*ICC = 1+4*0.3 = {de:.2f}")
for frac in (0.20, 0.25, 0.30):
    n_pat = 200 * frac
    n_photos_class = 1000 * frac / 3
    ne = n_photos_class / de
    row = []
    for p in (0.7, 0.8, 0.9):
        lo, hi = wilson(p * ne, ne)
        lo_naive, hi_naive = wilson(p * n_photos_class, n_photos_class)
        row.append(f"p={p}: [{lo:.3f},{hi:.3f}] ±{(hi-lo)/2:.3f} (naive ±{(hi_naive-lo_naive)/2:.3f})")
    print(f"test={frac:.0%}: {n_pat:.0f} patients, {n_photos_class:.1f} photos/class, n_eff/class={ne:.1f}")
    for r in row:
        print("    " + r)

print("\n" + "=" * 70)
print("(c) Table: total N patients, expected 95% half-widths (all patients evaluated once via pooled OOF CV)")
print("    Assumptions: FPR=0.10 (spec 0.90), binary sens=0.85; per-class recall=0.80; 3 balanced classes;")
print("    BA(3-class)=mean of 3 recalls each 0.80; Wald on n_eff for BA; Wilson on n_eff for proportions")
print("=" * 70)


def table(N_list, m, icc, normal_frac, label):
    print(f"\n-- {label}: m={m} photos/patient, ICC={icc}, normal fraction={normal_frac:.2f}, DE={deff(m, icc):.2f}")
    print(f"{'N':>4} {'photos':>7} {'normal':>7} {'n_eff_norm':>10} {'FPR±':>7} {'recall±':>8} {'BA2±':>7} {'BA3±':>7}")
    for N in N_list:
        photos = N * m
        de = deff(m, icc)
        n_norm = photos * normal_frac
        ne_norm = n_norm / de
        fpr_hw = wilson_halfwidth_eff(0.10, ne_norm)
        n_pos = photos * (1 - normal_frac)
        ne_pos = n_pos / de
        # per-class recall: class size = photos/3 if balanced, else use stage sizes approx
        n_cls = photos / 3 if abs(normal_frac - 1 / 3) < 0.01 else photos * (1 - normal_frac) / 2
        ne_cls = n_cls / de
        rec_hw = wilson_halfwidth_eff(0.80, ne_cls)
        # binary BA = (sens+spec)/2 ; var = (var_sens + var_spec)/4
        var_ba2 = (0.85 * 0.15 / ne_pos + 0.9 * 0.1 / ne_norm) / 4
        ba2_hw = Z * math.sqrt(var_ba2)
        # 3-class BA = mean of recalls
        n_c = [n_norm / de, n_pos / 2 / de, n_pos / 2 / de]
        var_ba3 = sum(0.8 * 0.2 / x for x in n_c) / 9
        ba3_hw = Z * math.sqrt(var_ba3)
        print(f"{N:>4} {photos:>7.0f} {n_norm:>7.1f} {ne_norm:>10.1f} {fpr_hw:>7.3f} {rec_hw:>8.3f} {ba2_hw:>7.3f} {ba3_hw:>7.3f}")


Ns = [14, 30, 50, 100, 200, 300]
table(Ns, 8.5, 0.3, 9 / 56, "Current-like: imbalanced (normal 9/56 = 16%)")
table(Ns, 5, 0.3, 1 / 3, "Future: balanced 3 classes")
for icc in (0.2, 0.5, 0.8):
    table(Ns, 5, icc, 1 / 3, f"Future balanced, ICC sensitivity {icc}")
print("\nNote: a held-out test set of 25% of patients => replace N by 0.25N (e.g. N=200 -> 50 test patients row).")

print("\n" + "=" * 70)
print("ICC / n_eff examples: n=100 photos, m=5 or 8.5")
print("=" * 70)
for m_ in (5, 8.5):
    for icc_ in (0.2, 0.5, 0.8):
        print(f"m={m_} ICC={icc_}: DE={deff(m_, icc_):.2f}, n_eff={100/deff(m_, icc_):.1f}")

print("\n" + "=" * 70)
print("(d) Normal photos needed so that upper 95% bound of FPR <= 10% or <= 5%")
print("=" * 70)


def min_n_zero(target, method):
    for n in range(1, 5000):
        if method == 'rule3':
            ub = 3 / n
        elif method == 'wilson':
            ub = wilson(0, n)[1]
        elif method == 'cp':
            ub = clopper_pearson(0, n)[1]
        elif method == 'cp_one_sided':
            ub = 1 - 0.05 ** (1 / n)
        if ub <= target:
            return n


for t in (0.10, 0.05):
    print(f"target upper <= {t:.0%} with 0 FP observed: rule-of-3 n={min_n_zero(t,'rule3')}, "
          f"Wilson n={min_n_zero(t,'wilson')}, CP two-sided 95% n={min_n_zero(t,'cp')}, "
          f"CP one-sided 95% n={min_n_zero(t,'cp_one_sided')}")


def assurance_n(true_p, target, method='wilson', power=0.8):
    """smallest n s.t. P(upper bound <= target) >= power when true FPR=true_p."""
    for n in range(5, 6000):
        prob = 0.0
        for x in range(0, n + 1):
            ub = wilson(x, n)[1] if method == 'wilson' else clopper_pearson(x, n)[1]
            if ub <= target:
                prob += stats.binom.pmf(x, n, true_p)
            else:
                break
        if prob >= power:
            return n, prob


for true_p, t in ((0.02, 0.10), (0.05, 0.10), (0.02, 0.05), (0.01, 0.05)):
    for meth in ('wilson', 'cp'):
        n, pr = assurance_n(true_p, t, meth)
        print(f"true FPR={true_p:.0%}, want upper<= {t:.0%} with 80% assurance ({meth}): n={n} (P={pr:.3f})")

print("\n  Convert photos -> patients with clustering (normal photos from normal patients):")
for n_eff_req in (35, 73):
    for m_ in (5, 8.5):
        for icc_ in (0.2, 0.5, 0.8):
            n_ph = n_eff_req * deff(m_, icc_)
            print(f"  n_eff={n_eff_req} m={m_} ICC={icc_}: photos={n_ph:.0f}, patients={math.ceil(n_ph/m_)}")

print("\n  Buderer (1996) style: n_normals = z^2 * Sp(1-Sp) / d^2")
for sp, d in ((0.9, 0.05), (0.9, 0.10), (0.95, 0.05), (0.8, 0.10)):
    n = Z * Z * sp * (1 - sp) / d ** 2
    print(f"  Sp={sp} d=±{d}: n_normals={math.ceil(n)} (photos if iid); with DE 2.2 -> {math.ceil(n*2.2)}")

print("\n" + "=" * 70)
print("Simulation check of DE formula: beta-binomial clusters, p=0.8, m=5, ICC=0.3")
print("=" * 70)
rng = np.random.default_rng(20261030)
p, m_, icc_ = 0.8, 5, 0.3
ab = 1 / icc_ - 1
a, b = p * ab, (1 - p) * ab
for k in (10, 20, 40):
    est = []
    for _ in range(20000):
        pi = rng.beta(a, b, size=k)
        est.append(rng.binomial(m_, pi).sum() / (k * m_))
    sd_emp = np.std(est)
    sd_formula = math.sqrt(p * (1 - p) / (k * m_ / deff(m_, icc_)))
    print(f"k={k} patients ({k*m_} photos): empirical SD={sd_emp:.4f}, DE-formula SD={sd_formula:.4f}, iid SD={math.sqrt(p*(1-p)/(k*m_)):.4f}")

print("\n" + "=" * 70)
print("Macro-F1 sampling SD (3 classes, each recall 0.80, errors split evenly), clustered test sets")
print("=" * 70)


def macro_f1(cm):
    f1s = []
    for c in range(cm.shape[0]):
        tp = cm[c, c]; fp = cm[:, c].sum() - tp; fn = cm[c, :].sum() - tp
        f1s.append(0 if tp == 0 else 2 * tp / (2 * tp + fp + fn))
    return np.mean(f1s)


for k_per_class in (3, 5, 10, 20, 40, 67):
    vals = []
    for _ in range(4000):
        cm = np.zeros((3, 3), int)
        for c in range(3):
            pi = rng.beta(a, b, size=k_per_class)
            for pp in pi:
                correct = rng.binomial(m_, pp)
                wrong = m_ - correct
                cm[c, c] += correct
                others = [o for o in range(3) if o != c]
                w1 = rng.binomial(wrong, 0.5)
                cm[c, others[0]] += w1; cm[c, others[1]] += wrong - w1
        vals.append(macro_f1(cm))
    vals = np.array(vals)
    lo, hi = np.percentile(vals, [2.5, 97.5])
    print(f"{k_per_class} patients/class ({k_per_class*m_} photos/class): mean macroF1={vals.mean():.3f}, "
          f"SD={vals.std():.3f}, central 95% range=[{lo:.3f},{hi:.3f}] (±{(hi-lo)/2:.3f})")

print("\n" + "=" * 70)
print("Learning-curve extrapolation demo (SYNTHETIC curve, not project data)")
print("acc(n) = a - b*n^(-c), true a=0.85, b=1.0, c=0.5; observed noise SD from binomial on test n=19")
print("=" * 70)


def ipl(n, a_, b_, c_):
    return a_ - b_ * np.power(n, -c_)


true = (0.85, 1.0, 0.5)
ns = np.array([10, 20, 30, 40, 56], float)
preds_500 = []
for _ in range(2000):
    y = ipl(ns, *true)
    y = np.clip(y + rng.normal(0, np.sqrt(y * (1 - y) / 19)), 0, 1)
    try:
        popt, _ = curve_fit(ipl, ns, y, p0=(0.8, 1, 0.5), bounds=([0, 0, 0.01], [1, 10, 3]), maxfev=5000)
        preds_500.append(ipl(500, *popt))
    except Exception:
        pass
preds_500 = np.array(preds_500)
print(f"true acc at n=500: {ipl(500, *true):.3f}; extrapolated from n<=56: median={np.median(preds_500):.3f}, "
      f"2.5-97.5%=[{np.percentile(preds_500,2.5):.3f},{np.percentile(preds_500,97.5):.3f}]")
```

原始輸出存於 `C:\Users\user\AppData\Local\Temp\claude\C--Users-user-Desktop-Phlebitis\65222311-7d94-4b7e-9464-8d7c78613042\scratchpad\ci_out.txt`（主控台編碼使「±」顯示為亂碼，數值已轉錄於上方各表）。
</details>

### Gaps
- 所有 recall/FPR/ICC 假設值皆為情境設定，非專案實測；不得作為專案效能宣稱。
- BA 的 Wald 近似在 n_eff < 10 時不可靠（N = 14 列僅供量級參考）；正式報告應用病人層級 cluster bootstrap。

---

## Part 2-E：小測試集造成過度樂觀/不穩定估計的證據

### Takeaway
**研究證據顯示**：n = 100 時 CV 準確率誤差約 ±10%，n = 30 約 ±15%；跨折標準誤會嚴重低估真實誤差；小樣本研究傾向報告更高準確率，K-fold CV（含調參/特徵選擇未巢狀化）在小 n 下有強烈正偏差，而巢狀 CV 或 train/test 分割則無偏。醫學影像資料集遠小於推動電腦視覺突破的資料集，各階段都會滲入偏差。

### Cited Findings
- **Varoquaux 2018**：二元分類信賴界 n = 30 為 ±15%、n = 100 為 ±10%、n = 300 為 ±6%、n = 1000 為 ±3%（相關觀測時可能更大）；二項最佳情況下 100 次約 ±7%；75% 期望準確率的 5–95% 界：n = 30 為 60.0–86.7%、n = 100 為 68.0–82.0%、n = 300 為 71.0–79.0%。以 1.64×SEM 當 95% 界會低估實際誤差（LOO 低估因子 0.73，50 次 20% 隨機分割 0.26）；LOO n = 100 時 SEM 給 ±7.4%，實際 ±10.3%。把 Haxby 資料標籤反轉（真實 50%）後，只用 4 個 session 時分數可達約 71%。642 篇研究樣本數中位數 89。— [B] NeuroImage 180(Pt A):68–77 (2018), doi 10.1016/j.neuroimage.2017.06.061 [https://ar5iv.labs.arxiv.org/html/1706.07581](https://ar5iv.labs.arxiv.org/html/1706.07581)（存取 2026-10-30）
- **Varoquaux & Cheplygina 2022**：在資料集選擇、方法、評估指標、發表策略每一步都可能滲入偏差；醫學影像資料集遠小於電腦視覺突破所用的資料集；以發表為導向的誘因阻礙進展。— [B] npj Digit Med 5:48 (2022), doi 10.1038/s41746-022-00592-y [https://pmc.ncbi.nlm.nih.gov/articles/PMC9005663](https://pmc.ncbi.nlm.nih.gov/articles/PMC9005663)（搜尋摘要，存取 2026-10-30）
- **Vabalas et al. 2019**：自閉症 ML 研究中樣本越小、報告準確率越高；模擬顯示 K-fold CV 在小樣本下產生強烈偏差，n = 1000 時仍存在；巢狀 CV 與 train/test 分割不論樣本數皆無偏；在合併訓練+測試資料上做特徵選擇造成的偏差遠大於調參。— [C] PLoS ONE 14(11):e0224365 (2019) [https://pmc.ncbi.nlm.nih.gov/articles/PMC6837442](https://pmc.ncbi.nlm.nih.gov/articles/PMC6837442)（搜尋摘要，存取 2026-10-30）
- Beleites 2013：測試不確定性會掩蓋學習曲線；驗證好但不完美的分類器約需 75–100 個測試樣本。— [C] [https://arxiv.org/abs/1211.1323](https://arxiv.org/abs/1211.1323)
- LNMBench：最佳 epoch 與驗證集選模的準確率差距大（例：94.40 → 91.34），即「看測試集挑最佳點」會高估。— [D] [https://arxiv.org/html/2512.09315](https://arxiv.org/html/2512.09315)

### Inferences
- **本報告推論**：本專案 56 張 / 14 人、3-fold、DE ≈ 3.25 → n_eff ≈ 17 張；依 Varoquaux 的量級，任何單次 CV 分數的實際不確定性可能 ≥ ±20 個百分點；**跨 3 折的 SD 不能當 CI**。
- **本報告推論（報告規範）**：(1) 只報 pooled patient-level OOF 的指標 + Wilson（比例）與病人層級 cluster bootstrap（BA、macro-F1）CI；(2) 所有選擇（class weight、ε、C、閾值、模型選擇）必須在內層 CV 完成（巢狀），或事先固定；(3) 重複分組 CV（多個 seed）報告分數分佈以呈現「分組運氣」造成的變異；(4) 在比較兩模型時，差距小於上表半寬時應寫「無法區分」；(5) 未經校準分數不得解讀為機率，cleanlab 的 self-confidence 排序也應僅作相對排序使用。

### Gaps
- Varoquaux & Cheplygina 2022、Vabalas 2019 僅有搜尋摘要層級，具體數字（如 Vabalas 偏差大小）未開啟全文核對。
- 未找到靜脈炎或其他皮膚照片小資料集（< 20 位病人）的評估不穩定度實證研究。
