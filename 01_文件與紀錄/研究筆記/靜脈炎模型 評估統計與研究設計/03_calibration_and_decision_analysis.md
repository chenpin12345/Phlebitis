# Calibration assessment under small samples and decision curve analysis / threshold selection for a small clustered phlebitis photo classifier

> 研究筆記（Research notes）。所有來源查閱日期：2026-10-30。
> 來源分級：[A] 官方/法規/報告規範；[B] 系統性回顧、頂級期刊/會議；[C] 其他同儕審查；[D] 預印本；[E] 部落格/文件/程式碼（僅輔助）。
> 結論標籤：**[研究證據]** = 直接來自引用文獻；**[業界慣例]** = 常見做法、非嚴格證據；**[推論]** = 本筆記作者依文獻及專案情境推導。
> 「未於本次會話開啟原文」= 只看過摘要、目錄或搜尋摘要，數字需由讀者再核對。
> 專案資料快照（委託方提供）：約 120 張照片，14 位病人；已標註二元資料為 47 陽性 / 9 正常（共 56 張）；分期資料為 normal 9 / stage1 23 / stage2 24（共 56 張）。每位病人有多張照片。未來約 1,000 張，三類刻意平衡。

---

## Q1. Calibration evaluation: the hierarchy, metrics (reliability diagram, ECE, Brier, slope/intercept, CITL, ICI) and their small-sample limits

### Takeaway
校準有四個層級：mean（calibration-in-the-large）、weak（intercept + slope）、moderate（flexible calibration curve）、strong。方法學文獻建議以 moderate 為目標，但只有在樣本大時才做得到。常被引用的經驗法則是「事件與非事件各至少約 200 例」才能畫精確的彈性校準曲線；Riley 等人已批評這個數字既不貼合特定模型，也常常不夠。小樣本時只評估 weak calibration 是站得住腳的。ML 界常用的 binned ECE 有系統性偏差，偏差大小隨樣本數與分箱方式而變。目前資料只有 9 張正常照片，任何一層的校準都無法精確估計。

### Cited Findings
**Calibration hierarchy and definitions**
- [B][研究證據] Van Calster B, Nieboer D, Vergouwe Y, De Cock B, Pencina MJ, Steyerberg EW. A calibration hierarchy for risk models was defined: from utopia to empirical data. *J Clin Epidemiol* 2016;74:167-76. doi:10.1016/j.jclinepi.2015.12.005 (PMID 26772608).
  - 定義 mean、weak、moderate、strong 四層。
  - moderate calibration 的定義是「預測風險 R% 的病人中，實際事件率為 R%」。
  - strong calibration 要求每一種 covariate pattern 都校準，作者認為不切實際，並證明 moderate calibration 可確保決策不會有害。
  - 摘要原文："flexible calibration assessment in small validation samples is problematic"。
  - 建議在模型開發與外部驗證時以 moderate calibration 為目標。
  - 來源：[PubMed](https://pubmed.ncbi.nlm.nih.gov/26772608/)
- [B][研究證據] Van Calster B, McLernon DJ, van Smeden M, Wynants L, Steyerberg EW; STRATOS Topic Group 6. Calibration: the Achilles heel of predictive analytics. *BMC Med* 2019;17:230. doi:10.1186/s12916-019-1466-7。各層對應的評估方法：
  - Mean：比較平均預測風險與整體事件率（calibration-in-the-large）。
  - Weak：看 calibration intercept（目標 0；負值代表高估）和 calibration slope（目標 1；<1 代表預測過於極端，>1 代表過於保守）。
  - Moderate：用 flexible calibration curve 評估。
  - Strong：作者稱為 "a utopic goal"。
  - 來源：[PMC6912996](https://pmc.ncbi.nlm.nih.gov/articles/PMC6912996/)

**Sample size for calibration curves — verifying the "200/200" figure**
- [B][研究證據] Van Calster 2019 原文："a minimum of 200 patients with and 200 patients without the event has been suggested" for a precise calibration curve。
  - 同一篇也指出，小資料集只評估 weak calibration 是 defensible 的。
  - 來源：[PMC6912996](https://pmc.ncbi.nlm.nih.gov/articles/PMC6912996/)
  - 注意：2016 hierarchy 論文的摘要沒有寫出 200/200 這個數字，全文是否寫明未查證（見 Gaps）。
- [B][研究證據] Riley RD et al. Evaluation of clinical prediction models (part 3): calculating the sample size required for an external validation study. *BMJ* 2024;384:e074821。
  - 提到經驗法則「至少 200 events 與 200 non-events」可畫含 calibration curve 的校準圖。
  - 但批評這類法則 "not specific to either the model or the clinical setting"。
  - 來源：搜尋摘要所載 [Birmingham repository PDF of part 2/3 series](https://research.birmingham.ac.uk/files/220429945/bmj-2023-074820.full.pdf)；未於本次會話開啟 part 3 全文。
- [C][研究證據] Snell KIE et al. External validation of clinical prediction models: simulation-based sample size calculations were more reliable than rules-of-thumb. *J Clin Epidemiol* 2021。
  - 模擬顯示要精確估計校準，常常需要多於 200 events/non-events。
  - 來源：[PMC8352630](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8352630/)（依搜尋摘要）
- [B][研究證據] Riley RD et al. Minimum sample size for external validation of a clinical prediction model with a binary outcome. *Stat Med* 2021;40(19):4230-4251. doi:10.1002/sim.9025。
  - 給出 O/E、calibration slope、C statistic、net benefit 精確度的封閉解。
  - 文中範例需要 9,835 人（177 events）才能精確估計校準與鑑別度，最受限的是 calibration slope 準則。
  - 同一範例在 8% 閾值下估計 net benefit 需要 6,443 人（116 events）。
  - 這些數字只適用於該範例的事件比例與模型，不能直接套用。
  - 來源：[Keele eprint](https://eprints.keele.ac.uk/id/eprint/9707)（依搜尋摘要）
- [B][研究證據] Riley RD, Archer L, Snell KIE, Ensor J, Dhiman P, Martin GP, Bonnett LJ, Collins GS. Evaluation of clinical prediction models (part 2): how to undertake an external validation study. *BMJ* 2024;384:e074820。
  - 建議在預測值全範圍檢查校準，使用含 smoothed flexible calibration curve 的校準圖。
  - 來源：[Birmingham repository PDF](https://research.birmingham.ac.uk/files/220429945/bmj-2023-074820.full.pdf)；依搜尋摘要，未於本次會話開啟全文。

**Hosmer–Lemeshow test**
- [B][研究證據] Van Calster 2019："we recommend against using the Hosmer–Lemeshow test to assess calibration"。
  - 理由：它用人工風險分層；P 值說不出錯誤校準的方向與幅度；檢定力低。
  - 來源：[PMC6912996](https://pmc.ncbi.nlm.nih.gov/articles/PMC6912996/)

**Loess-based calibration curves and ICI**
- [B][研究證據] Austin PC, Steyerberg EW. The Integrated Calibration Index (ICI) and related metrics for quantifying the calibration of logistic regression models. *Stat Med* 2019. doi:10.1002/sim.8281。
  - ICI 是 loess 平滑校準曲線與對角線之間的加權平均絕對差，權重是預測值的分布。
  - 延伸自 Harrell 的 Emax（最大絕對差）。
  - 同時提出 E50、E90（絕對差的中位數與第 90 百分位）。
  - 來源：[Erasmus repository](https://repub.eur.nl/pub/117945)、[PMC6771733](https://pmc.ncbi.nlm.nih.gov/articles/PMC6771733)（依搜尋摘要）

**ECE and its estimation bias**
- [B][研究證據] Guo C, Pleiss G, Sun Y, Weinberger KQ. On Calibration of Modern Neural Networks. ICML 2017, PMLR 70:1321-1330。
  - 發現現代深度網路有錯誤校準。
  - 用 ECE / reliability diagram 評估，並提出 temperature scaling。
  - 來源：[PMLR](https://proceedings.mlr.press/v70/guo17a.html)、[arXiv 1706.04599](https://arxiv.org/abs/1706.04599v1)
- [B][研究證據] Roelofs R, Cain N, Shlens J, Mozer MC. Mitigating Bias in Calibration Error Estimation. AISTATS 2022, PMLR 151:4036-4054。發現：
  - binned ECE 有統計偏差，而且模型校準得越完美，偏差越大。
  - equal-mass bins 的偏差小於 equal-width bins。
  - 提出 ECE_sweep：在保持校準函數單調的前提下取最多 bin 數。
  - 也推薦一個 debiased estimator（Kumar 2019 的變體，搭配 equal-mass bins）。
  - 來源：[PMLR](https://proceedings.mlr.press/v151/roelofs22a.html)、[arXiv 2012.08668](https://arxiv.org/abs/2012.08668v3)
- [B][研究證據] Kumar A, Liang PS, Ma T. Verified Uncertainty Calibration. NeurIPS 2019。
  - 指出 binning-based ECE 估計不準確。
  - 提出 debiased estimator，所需樣本比標準 binned estimator 少。
  - 提出 scaling-binning calibrator：先做參數化 scaling，再對輸出分箱。
  - 來源：[arXiv 1909.10155](https://arxiv.org/pdf/1909.10155)、[NeurIPS](https://papers.nips.cc/paper/8635-verified-uncertainty-calibration)、[code](https://github.com/p-lambda/verified_calibration) [E]

### Inferences
- [推論] 以本專案現有資料（二元 9 張 normal、14 位病人）而言：
  - moderate calibration（flexible curve、ICI）和 equal-mass reliability diagram 都只能當描述性圖，不能下結論。
  - 9 張 normal 不到經驗法則 200 non-events 的 5%。
  - 加上同一病人多張照片相關，有效樣本更小。設計效應 DEFF = 1 + (m−1)·ICC，m 為每位病人平均照片數。
- [推論] ECE 不適合作為本專案的主要校準指標，原因有三：
  1. 小 n 時 binned ECE 的偏差相對其值很大（Roelofs 2022）；
  2. ECE 只看 top-label confidence，不區分方向，也看不出是高估還是低估；
  3. 數值依賴 bin 數與分箱方式。
  若一定要報告（例如與 ML 文獻比較）：用 equal-mass bins、少量 bins（例如 5）、報告 bin 數，並附 patient-level bootstrap CI。
- [推論] Brier score 和 scaled Brier 是 strictly proper scoring rule，不需分箱，小樣本下比 ECE 更可解釋。但它們混合了鑑別度與校準，不能單獨代表校準。
- [推論] Brier 相關公式。這些是標準定義，原始文獻 Murphy 1973 *J Appl Meteorol* 未於本次會話開啟：
  - Brier = (1/n) Σ (p_i − y_i)²
  - Scaled Brier = 1 − Brier / [ȳ(1−ȳ)]
  - Murphy 分解：Brier = Reliability − Resolution + Uncertainty
  - 小樣本時 Reliability 項需要分箱，同樣有 binning bias。
- [推論] calibration slope 和 intercept 估計式（標準 logistic recalibration framework，與 Van Calster 2019 對 slope/intercept 的解讀一致）：
  - slope：配適 logit P(y=1) = a + b·logit(p̂)，b 即 slope。
  - intercept（CITL）：固定 b=1，以 logit(p̂) 為 offset 配適 a。
  - 在 9 個 non-events 下，slope 的 95% CI 會非常寬，常常跨過 0.5–2，無法判斷 over/underfitting。

### Gaps
- Van Calster 2016 全文是否明寫「至少 200 events 與 200 non-events」：本次只看到摘要，未能證實。可確認的是 Van Calster 2019（BMC Med）寫明 "has been suggested"，Riley 2024 part 3 引用並批評此法則。
- Nixon et al. 2019 "Measuring calibration in deep learning"（CVPR-W / arXiv）：本次只確認引用存在，未取得摘要。其提出的 adaptive / static / classwise calibration error 等細節未於本次查證。
- Błasiok & Nakkiran 的 "smooth ECE"（kernel-smoothed reliability diagram）與 Błasiok/Gopalan 等人的 distance-to-calibration 理論：未於本次查證，未找到可靠證據可引用。
- Murphy (1973) Brier 分解原文：未於本次開啟。
- TRIPOD+AI（Collins GS et al., BMJ 2024）中校準與臨床效用的條目：本次未開啟原文，條目編號未核實。

---

## Q2. Recalibration methods (Platt, isotonic, temperature, vector/matrix, Dirichlet) and their data needs; multiclass/ordinal calibration

### Takeaway
參數越少的校準器越適合小資料：temperature scaling 1 個參數，Platt / logistic recalibration 2 個，vector scaling 2K 個，matrix 或 Dirichlet 為 K²+K 個；isotonic 是非參數。所有校準器都需要一組獨立於訓練與測試的 calibration set。以本專案而言，現在任何 recalibration 都會把 9 個 normal 樣本用在第三個用途上，不可行。

### Cited Findings
- [B][研究證據] Guo et al. 2017：temperature scaling 是 "a single-parameter variant of Platt Scaling"，在多數資料集上對校準 "surprisingly effective"。
  - 由於 T 不改變 argmax，temperature scaling 不改變 accuracy（Guo 2017 原理，由公式可得）。
  - 來源：[PMLR](https://proceedings.mlr.press/v70/guo17a.html)
- [B][研究證據] Kull M et al. Beyond temperature scaling: Obtaining well-calibrated multi-class probabilities with Dirichlet calibration. NeurIPS 2019。
  - Dirichlet calibration 等價於：對未校準機率取 log → 一層線性層 → softmax。
  - 是二元 beta calibration 的多類延伸，學到的參數可揭示原模型的偏差。
  - 主要收益在 classwise calibration；在 21 個資料集、11 種非神經分類器上測試。
  - 來源：[NeurIPS proceedings](https://proceedings.neurips.cc/paper/2019/hash/8ca01ea920679a0fe3728441494041b9-Abstract.html)、[arXiv 1910.12656](https://arxiv.org/pdf/1910.12656.pdf)
- [B][研究證據] Kumar et al. 2019：scaling-binning calibrator 結合參數化 scaling 的樣本效率與 binning 的可驗證性。
  - 在 CIFAR-10 / ImageNet 的多類實驗中，校準誤差比 histogram binning 低 35%。
  - 來源：[arXiv 1909.10155](https://arxiv.org/pdf/1909.10155)
- [B][研究證據] van den Goorbergh et al. 2022（詳見 Q3）：在不平衡修正之後做 logistic recalibration，可把 median intercept 拉回 −0.07 至 0.03。
  - 但作者認為「修正 + 再校準」只有在能改善鑑別度時才值得，而該研究沒有發現鑑別度改善。
  - 來源：[JAMIA](https://academic.oup.com/jamia/article/29/9/1525/6605096)
- [B][研究證據] Van Calster 2019：更新模型可先只改 intercept（修正 calibration-in-the-large）；完整重新配適只有在驗證樣本相對大時才會改善校準。
  - 來源：[PMC6912996](https://pmc.ncbi.nlm.nih.gov/articles/PMC6912996/)

### Inferences
- [推論] 未來（約 1,000 張、三類平衡、約數十至上百位病人）的校準器優先順序：
  1. **temperature scaling**：EfficientNet softmax 用，1 個參數。
  2. **logistic recalibration（Platt）**：DINOv2 + LR 的二元輸出用，2 個參數。
  3. **intercept-only 先驗修正**：見 Q3，0 個需估計參數，只需要外部盛行率。
  4. **vector scaling / Dirichlet（有正則化）**：只在 calibration set 每類至少有數百張、且來自足夠多病人時才考慮。
  5. **isotonic regression**：一般認為在小 calibration set 上會過擬合，會產生階梯狀、許多並列的 0/1 機率。此為 [業界慣例]，本次未查證到原始實證文獻，見 Gaps。
- [推論] 三類 ordinal（normal / stage1 / stage2）：
  - 多類 temperature scaling 會保留類別排序，但不保證各類校準。
  - 實務上可分別評估兩個累積二元事件的校準：P(stage ≥1) 與 P(stage ≥2)，各畫一張 reliability plot。這樣直接對應臨床決策「有無靜脈炎」與「是否嚴重」。
- [推論] calibration set 必須以病人為單位切分，與訓練集和測試集都不重疊。
  - 在 CV 中，校準器要在每個 outer fold 的訓練部分內，用 inner patient-level split 或 out-of-fold 預測來配適，不能碰 outer test fold。
- [推論] DINOv2 + LR：logistic regression 本身在其訓練分布上大致是 mean-calibrated（logistic 最大概似的性質）。
  - 但若用 class_weight='balanced' 或平衡抽樣，就會破壞這個性質（見 Q3）。
  - 若使用 L2 正則化且 C 很小，預測會被壓向中間，slope 會 >1。

### Gaps
- Van Hoorde et al. 2015（polytomous risk model calibration）、Vaicenavicius et al. 2019 AISTATS（multiclass calibration evaluation）：本次未查證，未找到可靠證據可引用。
- 「isotonic regression 在小樣本過擬合」的原始實證（常引用 Niculescu-Mizil & Caruana 2005 ICML）：本次未開啟。
- 各校準器的最低樣本量：沒有找到具體、經驗證的數字建議（未找到可靠證據）。

---

## Q3. Effect of class-balanced training/sampling and class weights; prior (prevalence) shift correction

### Takeaway
這是對本專案最關鍵的一點。van den Goorbergh et al. 2022 證明：以重抽樣（RUS、ROS、SMOTE）修正不平衡，會造成嚴重的風險高估，calibration intercept 遠小於 0；SMOTE 與 ROS 還會讓 slope <1。這些修正不會提升 AUROC。若要得到較平衡的 sensitivity/specificity，直接移動閾值就能做到，而且不扭曲機率。未來三類刻意平衡收集（設計上的盛行率而非重抽樣）在原理上造成同樣的問題：樣本盛行率 ≠ 母體盛行率，必須做 prior shift 修正，或不把輸出當作機率。

### Cited Findings
- [B][研究證據] van den Goorbergh R, van Smeden M, Timmerman D, Van Calster B. The harm of class imbalance corrections for risk prediction models: illustration and simulation using logistic regression. *JAMIA* 2022;29(9):1525-1534. doi:10.1093/jamia/ocac093。
  - **方法**：比較 RUS、ROS、SMOTE（k=5）與不修正。案例為 IOTA 卵巢腫瘤資料（3,369 人，盛行率 20%）；模擬 24 個情境、每情境 2,000 次。
  - **案例結果**：未修正時 calibration intercept 約 0.05–0.06；修正後介於 −1.32（SMOTE + SLR）至 −1.50（RUS + SLR），代表強烈高估。
  - **模擬結果**：修正後 intercept 在 1% 盛行率時 ≤ −4.5、10% 時 ≤ −2.1、30% 時 ≤ −0.7。SMOTE 與 ROS 的 slope <1。
  - **AUROC**：修正沒有提升 AUROC；RUS 常更差。
  - **閾值**：未修正模型在 0.5 閾值下 sensitivity 只有 29–31%。修正或移動閾值都能得到較平衡的結果（sensitivity 69–75%、specificity 74–78%），而移動閾值不扭曲機率。
  - **Net benefit**：修正後的模型 net benefit 下降，閾值 ≥0.3 時變成負值。
  - **結論**：摘要原文 "Outcome imbalance is not a problem in itself, imbalance correction may even worsen model performance."
  - **限制**：只研究 logistic regression。作者明言神經網路、weighting、cost-sensitive learning 需要另行研究。
  - 來源：[JAMIA](https://academic.oup.com/jamia/article/29/9/1525/6605096)
- [C][研究證據] Saerens M, Latinne P, Decaestecker C. Adjusting the outputs of a classifier to new a priori probabilities: a simple procedure. *Neural Computation* 2002;14(1):21-41. doi:10.1162/089976602753284446。
  - 若訓練資料與部署資料的類別先驗不同，模型的 posterior 估計就不適用於部署資料。
  - 可在不重新訓練的情況下，把輸出 rescale 到新先驗。
  - 新先驗未知時，可用 EM 演算法同時估計新先驗並調整輸出；作者證明此程序最大化新資料的概似。
  - 來源：[UCLouvain record](https://research.dial.uclouvain.be/entities/publication/ff0a9d02-c8d6-4e6a-8320-5665e5cb85ba)、[mlanthology](https://mlanthology.org/neco/2002/saerens2002neco-adjusting)（依摘要）
- [B][研究證據] Van Calster 2019：疾病盛行率在不同醫療中心之間不同，在高盛行率環境開發的模型會高估低盛行率環境的風險。
  - 該文案例中，開發資料盛行率 31%，驗證世代 44%。
  - 來源：[PMC6912996](https://pmc.ncbi.nlm.nih.gov/articles/PMC6912996/)

### Inferences
- [推論] 已知先驗時的二元修正公式（Bayes 定理，Saerens 2002 的已知先驗特例）。設 π_s 為訓練/校準樣本中的盛行率，π_t 為目標族群盛行率：
  `logit(p_t) = logit(p_s) + log(π_t/(1−π_t)) − log(π_s/(1−π_s))`
  多類版本：`p_t(k) ∝ p_s(k) · π_t(k)/π_s(k)`，再重新正規化。
  - 前提是 label shift 假設成立：P(x|y) 在兩個環境不變。若不同醫院、不同拍攝條件導致外觀改變，此假設不成立。
- [推論] 本專案現況：二元資料陽性比例 47/56 ≈ 84%，遠高於臨床上靜脈留置部位的靜脈炎盛行率（實際數字本筆記未查證）。
  - 未來平衡資料的比例為 1/3 : 1/3 : 1/3。
  - 因此模型輸出不論是否在樣本內校準，都不等於「臨床上這張照片是靜脈炎的機率」。
- [推論] EfficientNet 若使用 class-weighted cross-entropy 或 balanced sampler，其效果在原理上類似重抽樣：把決策邊界與機率往少數類推。
  - 依 van den Goorbergh 的邏輯，應優先「不加權訓練 + 調整閾值」。
  - 若必須加權（例如為了訓練穩定），之後必須再校準或做先驗修正。
  - 這點對 CNN 尚無直接實證，屬推論。
- [推論] 已知 π_t 時，prior shift 修正只需要調整 intercept（logit 平移），不需要額外資料去估計參數。這是未來資料量下最可行的「機率化」步驟。
  - 但 π_t 必須來自可靠的臨床流行病學資料，例如院內 PIVC 靜脈炎發生率稽核。

### Gaps
- 類別權重或 balanced sampler 對 CNN softmax 校準影響的直接醫學影像實證：本次未查到，未找到可靠證據。
- 台灣或院內周邊靜脈導管靜脈炎盛行率（作為 π_t）：不在本筆記範圍，未查證。

---

## Q4. Is calibration meaningful for this project now (14 patients, 9 normal photos)? What to report, when to attempt calibration, and should the UI wording stay?

### Takeaway
現在做「校準評估」的推論價值接近零，做「校準修正」則不可行。可以報告的只有：patient-level cluster bootstrap 的 Brier / scaled Brier（附很寬的 CI）、描述性 reliability plot（標明不可推論）、以及 O/E。UI 文字「不是疾病機率」應保留，而且有文獻支持。未來在病人數足夠、取得外部盛行率之前，都應維持這個說法。

### Cited Findings
- [B][研究證據] 小樣本中的 flexible calibration 評估有問題（Van Calster 2016 摘要）；小資料只評估 weak calibration 是 defensible 的（Van Calster 2019）。
  - 來源：[PubMed 26772608](https://pubmed.ncbi.nlm.nih.gov/26772608/)、[PMC6912996](https://pmc.ncbi.nlm.nih.gov/articles/PMC6912996/)
- [B][研究證據] 200 events / 200 non-events 只是經驗法則，實際所需樣本常更多；應以 Riley 的 closed-form 計算依模型與情境量身決定。
  - 來源：[Riley 2021 Stat Med (Keele)](https://eprints.keele.ac.uk/id/eprint/9707)、[Snell 2021 PMC8352630](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8352630/)
- [B][研究證據] 錯誤校準會導致錯誤期待與錯誤決策：高估造成過度治療，低估造成治療不足。
  - Van Calster 2019 舉例：在 20% 閾值下，QRISK2 選出每 1,000 名男性中的 110 人，錯誤校準的 NICE Framingham 選出 206 人。
  - 來源：[PMC6912996](https://pmc.ncbi.nlm.nih.gov/articles/PMC6912996/)

### Inferences
- [推論] 現在可以報告的內容（全部標為 exploratory）：
  1. **Brier 與 scaled Brier**：以病人為重抽樣單位做 cluster bootstrap，給 95% CI。只有 14 個 cluster 時，percentile bootstrap 的覆蓋率本身就不可靠，應明寫此限制。
  2. **O/E 或 calibration-in-the-large**：只有描述意義，因為 84% 的樣本盛行率是收案造成的。
  3. **描述性 reliability plot**：用 equal-mass bins（≤5 bins），標出每 bin 的 n 與病人數，加上 cluster bootstrap 帶，並在圖上寫明「n 過小，不可推論校準」。
  4. **預測分數分布圖**：依真實類別分開，用 histogram 或 strip plot。這通常比 reliability plot 更誠實。
- [推論] 現在不應報告或不應宣稱的內容：
  - 不報告 ECE 的單一數值排名、不報告 Hosmer–Lemeshow。
  - 不宣稱「模型已校準」，不做 Platt / isotonic / temperature 等再校準並宣稱改善。
  - 不報告 calibration slope 的點估計而不附 CI。
- [推論] 何時可以嘗試校準評估：
  - 至少在 patient-level 獨立測試集中，各相關二元事件都有相當數量的事件與非事件，並以 Riley 2021 / pmsampsize 類方法依目標 CI 寬度計算。
  - 以 200/200 經驗法則對照：未來約 1,000 張、每類約 333 張，在「有無靜脈炎」的二元事件上照片數接近門檻。但照片之間有病人內相關，有效樣本遠低於照片數。
  - 因此即使到了約 1,000 張，也只適合評估 weak calibration（intercept + slope）。moderate calibration 需要 cluster-aware 方法，並取決於病人數。
- [推論] UI 文字「not a disease probability / 不是疾病機率」應保留，理由有三：
  1. 未經校準；
  2. 樣本盛行率是人為的（84% 或 1/3）；
  3. 病人數極少。
  即使未來做了樣本內校準，也只是「在研究樣本分布下的校準」，仍不是臨床疾病機率，除非另外做了先驗修正並經外部驗證。
  - 建議改成更具體的說法，例如「模型信心分數（研究用，非疾病機率）」，或不顯示百分比，只顯示類別與「需人工判讀」。

### Gaps
- 叢集資料（病人內多張照片）的校準曲線樣本量公式：未找到可靠的專門文獻。Riley 等人的公式假設觀測彼此獨立。
- 14 個 cluster 下 cluster bootstrap 覆蓋率的實證表現：本次未查證。

---

## Q5. Decision curve analysis (net benefit): formulas, interpretation, calibration/prevalence requirements, CIs, ordinal outcomes, Python implementation

### Takeaway
Net benefit 的公式是 NB = TP/n − FP/n × pt/(1−pt)。threshold odds pt/(1−pt) 等於「偽陽性的傷害 ÷ 真陽性的好處」。DCA 需要兩樣東西：校準良好的機率，以及真實的盛行率。在富集樣本、病例對照樣本或人為平衡的樣本上，必須以外部盛行率修正。Kerr 等人提醒，DCA 不能用來「找出最佳閾值」，而且它假設每個人的效益與成本相同。以本專案的樣本量，DCA 現階段最多只能作為方法示範。

### Cited Findings
- [B][研究證據] Vickers AJ, van Calster B, Steyerberg EW. A simple, step-by-step guide to interpreting decision curve analysis. *Diagn Progn Res* 2019;3:18. doi:10.1186/s41512-019-0064-7。
  - 給出等價形式 NB = sensitivity × prevalence − (1 − specificity) × (1 − prevalence) × w，其中 w 是 threshold odds。
  - 閾值機率定義為「值得介入的最低疾病機率」。
  - "treat all" 與 "treat none" 曲線是必要的參照策略。
  - 建議把 y 軸理解為 benefit、x 軸理解為 preference。
  - 來源：[PMC6777022](https://pmc.ncbi.nlm.nih.gov/articles/6777022)、[BMC PDF](https://diagnprognres.biomedcentral.com/track/pdf/10.1186/s41512-019-0064-7)（依搜尋摘要）
- [B][研究證據] Van Calster B, Wynants L, Verbeek JFM, et al. Reporting and interpreting decision curve analysis: a guide for investigators. *Eur Urol* 2018。
  - 建議只在「臨床合理的閾值範圍」內呈現 net benefit。
  - 來源：引用見 [PMC6777022](https://pmc.ncbi.nlm.nih.gov/articles/6777022) 的相關文獻；本次未開啟 Eur Urol 原文，卷頁與 DOI 未核實。
- [B][研究證據] Kerr KF, Brown MD, Zhu K, Janes H. Assessing the clinical impact of risk prediction models with decision curves: guidance for correct interpretation and appropriate use. *J Clin Oncol* 2016;34(21):2534-40。
  - 決策曲線不能用來找出建議介入的最佳風險閾值。
  - 決策曲線呈現的是「每位病人預期效益與成本都相同」的族群中的表現。若子族群的效益與成本不同，應畫子族群專屬的曲線。
  - 同一團隊後續提倡 opt-out decision curves；並建議加上 CI，避免過度解讀曲線上的起伏。
  - 來源：[PMC4962736](https://pmc.ncbi.nlm.nih.gov/articles/PMC4962736)（依搜尋摘要）
- [B][研究證據] Pfeiffer RM, Gail MH. Estimating the decision curve and its precision from three study designs. *Biometrical Journal*（2020；不同來源列為 2019 或 2020）。doi:10.1002/bimj.201800240。
  - 若已知發生率或盛行率，病例對照資料也能估計 NB。
  - full-cohort 估計法不假設模型已校準，對錯誤校準相對穩健；假設模型校準良好的估計法比較精確，但模型若錯誤校準會產生嚴重偏差。
  - 以 influence function 估計變異數，並提出 bootstrap 同時信賴帶（simultaneous confidence bands）。
  - 來源：[PMC8620346](https://pmc.ncbi.nlm.nih.gov/articles/PMC8620346)（依搜尋摘要）
- [C][研究證據] Rousson V, Zumbrunn T. Decision curve analysis revisited: overall net benefit, relationships to ROC curve analysis, and application to case-control studies. *BMC Med Inform Decis Mak* 2011;11:45. doi:10.1186/1472-6947-11-45。
  - 無法從資料得到真實盛行率時（病例對照），可修改計算程序，以外部盛行率套用 DCA。
  - 來源：[PMC3148204](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3148204/)
- [B][研究證據] Riley 2021 Stat Med 把 net benefit 的精確度納入 external validation 樣本量計算；其範例在 8% 閾值下需 6,443 人（116 events）。
  - 來源：[Keele eprint](https://eprints.keele.ac.uk/id/eprint/9707)
- [B][研究證據] van den Goorbergh 2022：不平衡修正（不經再校準）會讓 NB 下降，閾值 ≥0.3 時變成負值。這直接說明錯誤校準會傷害臨床效用。
  - 來源：[JAMIA](https://academic.oup.com/jamia/article/29/9/1525/6605096)
- [E] Python 套件 `dcurves`（MSKCC Epi-Biostat，PyPI）：
  - 最新版 1.1.7，2025-10-24 發佈。
  - 提供 `dca()`（計算 net benefit 與 interventions avoided，支援二元與存活結果）與 `plot_graphs()`。
  - 範例參數：`data, outcome, modelnames, thresholds`。舊版 0.0.3 用 `thresh_vals`、`predictors`，API 已改變。
  - PyPI 頁面沒有提到 prevalence（病例對照）參數或 bootstrap CI。R 版 dcurves 在 CRAN。
  - 來源：[PyPI dcurves](https://pypi.org/project/dcurves/)、[CRAN dcurves refman](https://cloud.r-project.org/web/packages/dcurves/refman/dcurves.html)
- [B] Vickers AJ, Elkin EB. Decision curve analysis: a novel method for evaluating prediction models. *Med Decis Making* 2006 是 DCA 的原始論文。Vickers, Van Calster & Steyerberg. Net benefit approaches to the evaluation of prediction models, molecular markers, and diagnostic tests. *BMJ* 2016 有 MSKCC 收錄紀錄：[MSKCC Synapse](https://synapse.mskcc.org/synapse/works/90307)。
  - 兩篇的 DOI、卷頁未於本次開啟原文核實。

### Inferences
- [推論] 公式整理。符號：n = 總數；π = 盛行率；w = pt/(1−pt)：
  - 模型：NB(pt) = TP/n − FP/n · w = Se·π − (1−Sp)(1−π)·w
  - Treat all：NB_all = π − (1−π)·w
  - Treat none：NB_none = 0
  - 富集或平衡樣本：Se 和 Sp 在樣本中估計（不受盛行率影響，前提是 spectrum 相同），π 改用外部值 π_t。
  - 但「哪些照片被判為陽性」取決於 p̂ ≥ pt，而 p̂ 也必須先做 prior shift 修正到 π_t（Q3 公式）。否則 pt 與 p̂ 不在同一機率尺度上，NB 會偏差。這一點與 Pfeiffer & Gail 的「需校準假設」一致。
- [推論] 閾值與成本：pt/(1−pt) = C_FP / C_FN，其中 C_FN 為漏掉一例的損失、C_FP 為一次假警報的損失（Vickers & Elkin 原理，屬標準決策理論）。
  - 若團隊判斷「漏掉一例靜脈炎的後果相當於 9 次不必要的拔管或複查」，則 pt = 1/(1+9) = 0.10。
  - 若相當於 19 次，則 pt = 0.05。
  - 因此本專案合理的 DCA 範圍應在低閾值區，例如 pt ∈ [0.02, 0.30]。精確範圍應由護理與臨床專家以「多少次假警報可換一次正確偵測」的方式訪談決定。
  - 對 LINE chatbot 的研究原型而言，「介入」可以定義為「提示護理人員現場評估」，其傷害很低，所以 pt 偏低是合理的。
- [推論] Ordinal 結果：未找到 ordinal DCA 的標準方法（見 Gaps）。實務作法是對臨床有意義的二元切點分別做 DCA：
  - (a) any phlebitis（stage ≥1）vs normal，對應「需要評估或處置」；
  - (b) stage 2 vs 其他，對應「需要立即拔管」或依院內 protocol。
  - 兩者的 pt 與成本比應分別訪談決定。
- [推論] CI：用 patient-level cluster bootstrap 對整條曲線做 pointwise 或 simultaneous band（Pfeiffer & Gail 提供理論）。
  - 以現在的 14 位病人、9 張 normal，NB 曲線的 CI 會極寬，不應據以做任何「模型有臨床效用」的陳述。
- [推論] 在 3-fold patient-level CV 中做 DCA：把各 fold 的 out-of-fold 預測合併後計算一條曲線（pooled OOF）。
  - 前提是每個 fold 的校準器或先驗修正只在該 fold 的訓練部分內估計。
  - 應明說這是 internal validation，不是外部驗證。

### Gaps
- Ordinal（多級）結果的 DCA 標準方法：未找到可靠證據。
- Vickers 等人「NB 的 CI 與假設檢定」專文（約 2023 年 *Diagn Progn Res*）：本次未查證。
- Kerr, Marsh & Janes 的 best-practice 專文：只從搜尋摘要得知其主張「加 CI 避免過度解讀起伏」，未取得原文卷頁。
- Vickers & Elkin 2006、Vickers 2016 BMJ、Van Calster 2018 Eur Urol 的 DOI：本次未逐一開啟核實。
- `dcurves` Python 是否支援外部 prevalence 參數（R 版有 `prevalence` 參數的說法本次未核實）：未確認。實作時可自行用上述公式計算。

---

## Q6. Threshold selection when FN is costlier than FP: cost-based, sensitivity-constrained, Neyman–Pearson, reject option; selection without touching the test set; instability on tiny samples

### Takeaway
有三種有原則的作法：
1. **成本導向**：pt = C_FP / (C_FP + C_FN)，需要校準過的機率。
2. **約束導向**：先固定 sensitivity ≥ 目標值，再最大化 specificity。Neyman–Pearson 分類提供「以高機率保證漏診率 ≤ α」的有限樣本版本，但需要足夠的陽性 hold-out 樣本。
3. **Reject option**：中間地帶回答「需人工判讀」，以 risk–coverage curve 評估。

閾值必須在 CV 的訓練部分內（nested）選出，不能用測試集選。以目前每類只有數十張、14 位病人，選出的閾值極不穩定，應報告其跨 fold 或 bootstrap 的變異。

### Cited Findings
- [B][研究證據] Tong X, Feng Y, Li JJ. Neyman-Pearson classification algorithms and NP receiver operating characteristics. *Science Advances* 2018;4(2):eaao1659. doi:10.1126/sciadv.aao1659。
  - NP 範式：在 type I error ≤ 使用者指定的 α（例如 5%）的條件下，最小化 type II error。
  - 提出適用於所有 scoring-type 分類器（logistic regression、SVM、random forest 等）的 umbrella algorithm。
  - 提出 NP-ROC bands，用於資料驅動地選擇 α 與比較 NP 分類器。
  - R 套件為 `nproc`。
  - 來源：[PMC5804623](https://pmc.ncbi.nlm.nih.gov/articles/PMC5804623)、[CRAN nproc](https://cran.nics.utk.edu/cran/web/packages/nproc/index.html)
- [B][研究證據] Geifman Y, El-Yaniv R. Selective Classification for Deep Neural Networks. NeurIPS 2017, pp. 4878–4887。
  - 從已訓練的網路建構 selective classifier，使用者指定想要的風險水準，方法找出對應的拒答規則（risk–coverage 取捨）。
  - 來源：[arXiv 1705.08500](https://arxiv.org/abs/1705.08500)、[mlanthology](https://mlanthology.org/neurips/2017/geifman2017neurips-selective)
- [B][研究證據] van den Goorbergh 2022：要提高 sensitivity，移動閾值的效果與不平衡修正相當，而且不扭曲機率。閾值選擇應反映臨床上的誤分類成本。
  - 來源：[JAMIA](https://academic.oup.com/jamia/article/29/9/1525/6605096)
- [B][研究證據] Kerr 2016：決策曲線本身不能用來找最佳閾值；閾值應來自臨床偏好，即效益與成本的權衡。
  - 來源：[PMC4962736](https://pmc.ncbi.nlm.nih.gov/articles/PMC4962736)

### Inferences
- [推論] NP 的映射與樣本需求：
  - 在本專案中，「要控制的錯誤」是漏診。把 NP 的 class 0 定義為「靜脈炎（陽性）」，則 type I error = 漏診率。
  - Umbrella algorithm 以 hold-out 陽性樣本的分數順序統計量選閾值。要以機率 ≥ 1−δ 保證漏診率 ≤ α，最少需要 n_pos ≥ ln δ / ln(1−α) 個獨立的 hold-out 陽性樣本（順序統計量的推導）。
  - α = δ = 0.05 時需 ≥ 59 個；α = 0.05、δ = 0.10 時需 ≥ 45 個。
  - 此最小樣本量公式依 NP 文獻的順序統計量原理推導，本次未在 Tong 2018 原文核實具體數字。
  - 現有 47 張陽性還要拆成訓練與 hold-out，又因病人內相關而不獨立，所以 NP 保證目前不可得。
- [推論] 用二項分布精確 CI（Clopper–Pearson 單側 97.5%）說明不穩定性：
  - 47 張陽性全部判對時，sensitivity 的 95% 下界約為 0.025^(1/47) ≈ 0.925。
  - 9 張 normal 全部判對時，specificity 的下界約為 0.025^(1/9) ≈ 0.66。
  - 以上未計入叢集效應；計入後下界更低。
  - 換言之，以目前資料，「sensitivity ≥ 0.95」無法被證實，只能被觀察到。
- [推論] Youden index（max Se + Sp − 1）隱含的假設是：在樣本盛行率下，FN 與 FP 等價（相對成本與盛行率掛鉤）。這不符合「漏診較嚴重」的臨床立場。
  - 在人為平衡的樣本上，Youden 點更沒有臨床意義。
  - 不建議作為主要閾值方法。這是推論，本次未查到專門批評 Youden 的原始文獻。
- [推論] 建議的閾值策略（研究原型）：
  1. **主要閾值 t_hi**：在 inner CV 的 out-of-fold 分數上，取滿足 Se ≥ 0.95 的最大閾值（Se 以病人層級或照片層級定義，需事先寫明）。再於 outer fold 評估實際的 Se 與 Sp。
  2. **人工判讀帶**：設定 t_lo < t_hi。分數 ≥ t_hi 判「疑似靜脈炎」；< t_lo 判「未見明顯靜脈炎」；介於兩者之間判「需人工判讀」。t_lo 的選法是讓自動判為陰性的群組中漏診數 ≤ 預設值，等價於高 NPV 的約束。
  3. **評估方式**：用 risk–coverage curve（coverage = 未被拒答的比例；risk = 已回答者的錯誤率，或專看漏診率）及 Geifman 式的 selective risk。
  4. 因為 FN 代價較高，拒答帶應該不對稱地往陰性側延伸：寧可多送人工，也不輕易自動回答「正常」。
- [推論] 避免資料洩漏：
  - 閾值、拒答帶、temperature 或先驗修正等所有後處理參數，都必須在每個 outer fold 的訓練病人內，以 inner patient-level CV 或 OOF 預測決定。
  - Outer test fold 與 held-out test set 只能用來評估。
  - 若最終要部署單一閾值：在全部開發資料上用 OOF 預測重新選一次，報告的效能則是 nested CV 的估計，加上（若有）held-out test 的結果。
- [推論] 閾值穩定性要報告：
  - 每個 outer fold 選出的 t_hi 與 t_lo；
  - patient-level bootstrap 下 t_hi 的分布；
  - 用該分布計算 outer fold 上 Se 的變異。
  - 若 t_hi 的跨 fold 範圍很大（例如 0.2–0.8 的 softmax 分數），就說明閾值尚未可用於任何正式情境。

### Gaps
- Chow 1970（reject option 的最佳拒答規則，*IEEE Trans Inf Theory*）：本次未開啟原文。
- 專門批評 Youden index 用於不對稱成本情境的方法學文獻：本次未查到可靠來源。
- 小樣本或叢集資料下閾值選擇不穩定性的醫學影像實證：未找到可靠證據。
- NP umbrella algorithm 在叢集（病人內多張照片）資料下的保證：未找到文獻。直覺上應以病人為單位，例如每位病人取一張或取病人層級分數。

---

## Q7. Python pseudo-code (implementation sketch)

### Takeaway
以下程式碼是依前述文獻公式寫成的實作草稿，屬 **[推論]**，不是任何論文的官方程式碼。所有重抽樣都以病人（group）為單位。正式使用前應以模擬資料做單元測試。

### Cited Findings
- 公式來源：
  - net benefit：[Vickers 2019 PMC6777022](https://pmc.ncbi.nlm.nih.gov/articles/6777022)
  - calibration slope 與 intercept 的解讀：[Van Calster 2019 PMC6912996](https://pmc.ncbi.nlm.nih.gov/articles/PMC6912996/)
  - equal-mass bins：[Roelofs 2022](https://proceedings.mlr.press/v151/roelofs22a.html)
  - 先驗修正：[Saerens 2002](https://mlanthology.org/neco/2002/saerens2002neco-adjusting)
  - DCA 套件：[dcurves](https://pypi.org/project/dcurves/) [E]

### Inferences
```python
import numpy as np
import statsmodels.api as sm
from scipy.special import logit, expit

EPS = 1e-6
def _clip(p): return np.clip(p, EPS, 1 - EPS)

# ---------- 1. Patient-level (cluster) bootstrap helper ----------
def cluster_bootstrap(stat_fn, y, p, groups, B=2000, seed=0):
    """Resample PATIENTS with replacement; keep all photos of each sampled patient.
    With only ~14 clusters the percentile CI is itself unreliable -> report that caveat."""
    rng = np.random.default_rng(seed)
    uniq = np.unique(groups)
    idx_by_g = {g: np.where(groups == g)[0] for g in uniq}
    stats = []
    for _ in range(B):
        gs = rng.choice(uniq, size=len(uniq), replace=True)
        idx = np.concatenate([idx_by_g[g] for g in gs])
        if len(np.unique(y[idx])) < 2:      # degenerate resample (no normals!) -> skip
            continue
        stats.append(stat_fn(y[idx], p[idx]))
    stats = np.array(stats)
    return np.nanpercentile(stats, [2.5, 97.5], axis=0), len(stats)

# ---------- 2. Brier and scaled Brier ----------
def brier(y, p):
    return np.mean((p - y) ** 2)

def scaled_brier(y, p):
    ref = y.mean() * (1 - y.mean())          # Brier of always predicting prevalence
    return 1 - brier(y, p) / ref             # 1 = perfect, 0 = no better than prevalence

# ---------- 3. Calibration intercept (CITL) and slope ----------
def calibration_intercept_slope(y, p):
    lp = logit(_clip(p))
    # slope: y ~ a + b*lp
    fit_s = sm.GLM(y, sm.add_constant(lp), family=sm.families.Binomial()).fit()
    slope = fit_s.params[1]
    # intercept (calibration-in-the-large): y ~ a + offset(lp)
    fit_i = sm.GLM(y, np.ones_like(lp), family=sm.families.Binomial(), offset=lp).fit()
    citl = fit_i.params[0]
    return citl, slope   # targets: 0 and 1 (Van Calster 2019)
# CI: use cluster_bootstrap(lambda y,p: calibration_intercept_slope(y,p), ...) - expect very wide.
# Also report O/E = y.mean() / p.mean() (mean calibration).

# ---------- 4. Reliability diagram, equal-mass bins + cluster bootstrap band ----------
def reliability_equal_mass(y, p, n_bins=5):
    order = np.argsort(p)
    bins = np.array_split(order, n_bins)     # equal-mass (quantile) bins
    mean_pred = np.array([p[b].mean() for b in bins])
    obs_frac  = np.array([y[b].mean() for b in bins])
    counts    = np.array([len(b) for b in bins])
    return mean_pred, obs_frac, counts
# Band: bootstrap patients; in each resample recompute the bins and the observed fraction;
# plot the 2.5-97.5% envelope. Annotate each bin with n photos / n patients and add the text
# "descriptive only - sample too small for calibration inference".

# ---------- 5. ECE (equal-mass bins; report with caveats) ----------
def ece_equal_mass(y, p, n_bins=5):
    mp, of, c = reliability_equal_mass(y, p, n_bins)
    return np.sum(c / c.sum() * np.abs(mp - of))
# Caveats: biased (largest when the model is well calibrated; Roelofs 2022); depends on n_bins;
# not comparable across sample sizes. Prefer Brier + slope/intercept.

# ---------- 6. Prior-shift correction (known target prevalence) ----------
def prior_shift(p, pi_sample, pi_target):
    return expit(logit(_clip(p)) + logit(pi_target) - logit(pi_sample))
# multiclass: q = P * (pi_t/pi_s); q /= q.sum(1, keepdims=True)

# ---------- 7. Net benefit curve with treat-all / treat-none, external prevalence ----------
def net_benefit_curve(y, p, thresholds, prevalence=None):
    """prevalence=None -> cohort formula (TP/n - FP/n*w).
    prevalence=pi_t   -> Se/Sp estimated in the sample, combined with external pi_t
                         (case-control / enriched / balanced designs; Rousson & Zumbrunn 2011,
                          Pfeiffer & Gail). p must already be on the target-prevalence scale
                          (apply prior_shift first) so that thresholding at pt is coherent."""
    out = []
    pi = y.mean() if prevalence is None else prevalence
    for pt in thresholds:
        w = pt / (1 - pt)
        pos = p >= pt
        se = (pos & (y == 1)).sum() / max((y == 1).sum(), 1)
        sp = (~pos & (y == 0)).sum() / max((y == 0).sum(), 1)
        nb_model = se * pi - (1 - sp) * (1 - pi) * w
        nb_all = pi - (1 - pi) * w
        out.append((pt, nb_model, nb_all, 0.0))
    return np.array(out)
# Plot only a clinically justified range (e.g. 0.02-0.30 for "miss is worse than false alarm").
# CI: cluster_bootstrap over patients, computing the curve per resample.
# Cross-check against dcurves.dca(...) (pip install dcurves) for the cohort case.

# ---------- 8. Threshold under a sensitivity constraint, nested inside patient-level CV ----------
from sklearn.model_selection import StratifiedGroupKFold

def pick_threshold_min_sens(y, p, min_sens=0.95):
    """Largest threshold whose sensitivity is >= min_sens (maximizes specificity under the constraint)."""
    cands = np.unique(p)[::-1]
    for t in cands:                          # descending: first hit = largest feasible t
        if ((p >= t) & (y == 1)).sum() / (y == 1).sum() >= min_sens:
            return t
    return cands[-1]

def nested_threshold_eval(X, y, groups, fit_predict, min_sens=0.95, seed=0):
    """fit_predict(X_tr, y_tr, X_te) -> scores for X_te (includes any calibrator fit on X_tr only)."""
    outer = StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=seed)
    rows = []
    for tr, te in outer.split(X, y, groups):
        # inner OOF scores on the outer-training patients only
        inner = StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=seed + 1)
        oof = np.full(len(tr), np.nan)
        for itr, ite in inner.split(X[tr], y[tr], groups[tr]):
            oof[ite] = fit_predict(X[tr][itr], y[tr][itr], X[tr][ite])
        t = pick_threshold_min_sens(y[tr], oof, min_sens)
        s_te = fit_predict(X[tr], y[tr], X[te])        # refit on all outer-train patients
        pos = s_te >= t
        se = (pos & (y[te] == 1)).sum() / max((y[te] == 1).sum(), 1)
        sp = (~pos & (y[te] == 0)).sum() / max((y[te] == 0).sum(), 1)
        rows.append(dict(threshold=t, sens=se, spec=sp,
                         n_pos=(y[te] == 1).sum(), n_neg=(y[te] == 0).sum()))
    return rows   # report every fold's threshold: their spread IS the instability finding
# With ~9 normals total, an outer fold may hold 2-4 normals -> spec is in steps of 25-50%.
# Repeat with several seeds (repeated nested CV) and report the distribution, not the best seed.

# ---------- 9. Reject option ("needs human review") and risk-coverage ----------
def risk_coverage(y, p, t_lo, t_hi):
    auto = (p < t_lo) | (p >= t_hi)
    coverage = auto.mean()
    pred = (p >= t_hi)
    fn_auto = ((~pred) & auto & (y == 1)).sum()       # misses among auto-answered
    err_auto = ((pred != (y == 1)) & auto).sum() / max(auto.sum(), 1)
    return coverage, err_auto, fn_auto
# Sweep t_lo (keeping t_hi fixed from the sensitivity constraint) to draw the risk-coverage curve;
# choose t_lo inside the inner CV such that auto-"normal" answers contain <= k misses.
```

- [推論] 實作注意事項：
  - 在目前資料下，`cluster_bootstrap` 會常常抽到不含 normal 的 resample。應記錄有效重抽次數，並把「有多少比例的 resample 無法計算」本身當作不穩定的證據回報。
  - softmax 三類輸出轉二元時，可用 P(any phlebitis) = P(stage1) + P(stage2)，以及 P(stage2)。兩個事件分別評估。
  - 所有閾值與校準參數都應寫入實驗紀錄，例如 metadata JSON，以符合「不自動部署」原則。閾值變更需人工審核。

### Gaps
- 以上程式碼未在真實資料上執行驗證。
- `dcurves` 的實際函式簽名（1.1.x）需以官方文件 mskcc-epi-bio.github.io/dcurves 核對；本次只看過 PyPI 頁面。
