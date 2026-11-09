# 機率校準（Calibration）與保形預測（Conformal Prediction）在極小、病人群聚之靜脈炎照片資料上的適用性

> 研究筆記，供報告撰寫者轉為繁體中文章節。查證日期（access date）：2026-10-31（任務指定基準日 2026-10-30；所有網頁於 2026-10-31 實際存取）。
> 標記：**[研究證據]** = 文獻／官方文件明載；**[業界做法]** = 函式庫預設或官方範例；**[本報告推論]** = 作者推理；**[本報告計算]** = 以 scipy 1.x（專案 .venv）自行計算，可重現（腳本存於 session scratchpad：`cov.py`、`sim.py`）。
> 來源分級：[A] 官方文件／指引；[B] 頂級期刊／會議同儕審查；[C] 其他同儕審查；[D] 預印本；[E] 部落格、範例程式、論壇。
> 專案資料基準：二分類 56 張已標記（陽性 47、正常 9）；分期 56 張（正常 9／第一期 23／第二期 24）；共 14 位病人；同一病人多張（不同日期、左右側）→ 病人內不可交換（non-exchangeable）。「~120 張」中其餘未標記或未入此任務。

---

## 問題一：機率校準（Temperature / Platt / Isotonic / Beta / Dirichlet / Vector-Matrix scaling；OOF 校準；校準指標與小樣本偏誤；先驗偏移）

### Takeaway
NOW（56 張、9 張正常、14 位病人）：只有**參數極少的方法**（temperature scaling 1 參數；Platt 2 參數）在技術上可擬合，且必須用「病人分組交叉驗證的 out-of-fold（OOF）分數」來擬合；但校準本身**無法被可信地驗證**（ECE 偏誤約 0.12、校準斜率 95% 區間約 0.6–1.9，見計算），因此 UI 仍應維持「非疾病機率」。Isotonic、Dirichlet、matrix scaling 在此規模不可用。FUTURE（~1,000 張、三類平衡）：temperature／vector scaling／Dirichlet（含 ODIR 正則化）可行；isotonic 仍屬邊緣（官方文件建議 ≫1000 才用）；校準斜率可估到約 ±0.13，但仍需「病人數」而非「照片數」足夠，且須以醫院與 LINE 分開報告。

### Cited Findings

**1.1 方法與證據**
- [研究證據][B] Guo, Pleiss, Sun, Weinberger（ICML 2017, PMLR 70:1321–1330）：現代深度網路比舊網路更「過度自信」；depth、width、weight decay、BatchNorm 影響校準；**temperature scaling（Platt scaling 的單參數變體）是所比較方法中最有效者**。資料集為 CIFAR／ImageNet 等數千至數萬張驗證集，非小樣本醫學資料。— [arXiv 1706.04599](https://arxiv.org/abs/1706.04599v1)；[mlanthology](https://mlanthology.org/icml/2017/guo2017icml-calibration)（存取 2026-10-31）
- [研究證據][B] Kull, Perello-Nieto 等（NeurIPS 2019）Dirichlet calibration：原生多類別、為 beta calibration 之推廣；**temperature scaling 是其特例（權重矩陣為縮放單位矩陣、偏差為 0）**；提出 ODIR（Off-Diagonal and Intercept Regularisation）以抑制過擬合；結論稱加 ODIR 後 matrix scaling 與 Dirichlet 在許多 DNN 上優於 temperature scaling。審稿者質疑 ODIR 夠強時 matrix scaling 退化為 vector scaling、增益有限。— [NeurIPS 2019 abstract](https://proceedings.neurips.cc/paper/2019/hash/8ca01ea920679a0fe3728441494041b9-Abstract.html)；[MetaReview](https://papers.neurips.cc/paper_files/paper/2019/file/8ca01ea920679a0fe3728441494041b9-MetaReview.html)（存取 2026-10-31）
- [研究證據][B] Niculescu-Mizil & Caruana（ICML 2005, doi:10.1145/1102351.1102430）：比較 Platt 與 isotonic；**資料稀少時 isotonic 較易過擬合、表現差於 Platt**。本次僅自鏡像頁面與索引確認此敘述，**未取得論文中精確交叉點樣本數**（常被轉述的「約 1000」實際出處見下一條 scikit-learn 文件）。— [mlanthology](https://mlanthology.org/icml/2005/niculescumizil2005icml-predicting)（存取 2026-10-31）
- [研究證據][A] scikit-learn 1.9.1 官方文件：`CalibratedClassifierCV(estimator, *, method='sigmoid'|'isotonic'|'temperature', cv=None, n_jobs=None, ensemble='auto')`；`'temperature'` 於 **1.8 版新增**，以 `softmax(logits/T)` 原生支援多類別、T 以 log loss 最佳化；sigmoid／isotonic 原生只支援二分類，多類別以 OvR 再正規化。官方原文："Isotonic calibration is not recommended when the number of calibration samples is too low (≪1000) since it then tends to overfit." 對極不平衡資料建議 sigmoid（多一個截距參數）。— [CalibratedClassifierCV API](https://scikit-learn.org/stable/modules/generated/sklearn.calibration.CalibratedClassifierCV.html)（存取 2026-10-31）
- [研究證據][A] 同上文件之 `ensemble`：`True` → 每折以訓練資料擬合分類器、以該折測試資料擬合校準器，最終為 n_cv 組（分類器＋校準器）之平均機率；`False` → 以 `cross_val_predict` 取得無偏 OOF 預測擬合**單一**校準器，預測時用全資料重訓之分類器；`'auto'` → 若為 `FrozenEstimator` 用 False，否則 True（1.6 版變更）。`cv` 可傳整數、splitter，或 (train, test) 索引 iterable。已訓練模型以 `FrozenEstimator` 包裝時「all provided data is used for calibration. The user has to take care manually that data for model fitting and calibration are disjoint.」**官方 API 頁面未記載 `groups` 參數**；`fit(X, y, sample_weight=None, **fit_params)` 的 fit_params 是傳給底層分類器。— 同上
- [研究證據][B] Kumar, Liang, Ma（NeurIPS 2019 "Verified Uncertainty Calibration"）：Platt／temperature scaling 的真實校準誤差比報告的大，且現行方法無法量測其校準誤差；histogram binning 需 O(B/ε²) 樣本、scaling 方法 O(1/ε²)；提出 scaling-binning（O(1/ε²+B)）；CIFAR-10 校準誤差比 histogram binning 低 35%、ImageNet 低 5 倍（B=100）。— [NeurIPS proceedings](https://papers.nips.cc/paper/8635-verified-uncertainty-calibration)；[arXiv 1909.10155](https://arxiv.org/pdf/1909.10155.pdf)（存取 2026-10-31）
- [研究證據][B] Roelofs, Cain, Shlens, Mozer（AISTATS 2022, PMLR 151:4036–4054）：**主流 ECE_bin 有偏誤，且對「完美校準」模型偏誤最大**；等量分箱（equal-mass）偏誤小於等寬分箱；建議 debiased estimator 與 ECE_sweep（在保持單調下取最多箱數）。— [PMLR](https://proceedings.mlr.press/v151/roelofs22a.html)（存取 2026-10-31）
- [研究證據][B] Van Calster, McLernon, van Smeden, Wynants, Steyerberg（STRATOS；BMC Medicine 2019;17:230, doi:10.1186/s12916-019-1466-7）：校準階層 mean／weak（截距＋斜率）／moderate（彈性校準曲線）／strong（不切實際）；截距目標 0（負＝高估）、斜率目標 1（<1＝預測過於極端）；**彈性校準曲線建議至少「200 位有事件 + 200 位無事件」**（引 Van Calster 2016）；**小資料集只評估 weak calibration（截距與斜率）是可辯護的**；明確**反對 Hosmer–Lemeshow 檢定**；不同中心／地區盛行率不同會造成校準失準，模型在高盛行率處開發會在低盛行率處高估風險；校準差時先更新截距，驗證樣本夠大才整體重配；建議在地持續監測。未提及 ECE。— [PMC6912996](https://pmc.ncbi.nlm.nih.gov/articles/PMC6912996/)（存取 2026-10-31）
- [研究證據][B] Riley 等（Statistics in Medicine 2021;40(19):4230–4251, doi:10.1002/sim.9025）：外部驗證最小樣本數的封閉式公式，目標為精確估計 O/E、校準斜率、C 統計量與 net benefit；範例（事件率 0.018）需 **9,835 人（177 事件）**，且**由校準斜率準則驅動**。— [Keele eprint](https://eprints.keele.ac.uk/id/eprint/9707)；[zendy doi page](https://zendy.io/title/10.1002/sim.9025)（存取 2026-10-31）
- [研究證據][B] Mehrtash, Wells, Tempany, Abolmaesumi, Kapur（IEEE TMI 2020;39(12):3868–3878, doi:10.1109/TMI.2020.3006437）：醫學影像**分割** FCN 過度自信；比較 cross-entropy 與 Dice loss；**模型集成（ensembling）一致改善校準**；亦用於預測分割品質與偵測 OOD。屬分割而非分類、資料規模遠大於本專案。— [PMC7704933](https://pmc.ncbi.nlm.nih.gov/articles/PMC7704933)（存取 2026-10-31）
- [研究證據][B] Ovadia 等（NeurIPS 2019 "Can you trust your model's uncertainty?"）：post-hoc 校準在 i.i.d. 下有效，但**在輕微資料偏移下就可能失效**；temperature scaling 在標準測試集的改善**常在偏移資料上變得更糟**；模型隨偏移變得「自信地錯」；deep ensembles 最穩健（官方部落格建議約 5 個成員）。— [NeurIPS abstract](https://papers.nips.cc/paper/2019/hash/8558cb408c1d76621371888657d2eb1d-Abstract.html)；[Google Research blog [E]](https://research.google/blog/can-you-trust-your-models-uncertainty/)（存取 2026-10-31）
- [研究證據][B] Saerens, Latinne, Decaestecker（Neural Computation 2002;14(1):21–41, doi:10.1162/089976602753284446）：類別先驗改變時，以 EM 估計新先驗並重新縮放分類器輸出、無需重訓；調整後準確率優於原始。前提為「label shift」（p(x|y) 不變）且原始輸出已校準。— [ULB PDF](https://dipot.ulb.ac.be/dspace/bitstream/2013/68391/1/Decaestecker_NeuralComp02.pdf)；[mlanthology](https://mlanthology.org/neco/2002/saerens2002neco-adjusting)（存取 2026-10-31）
- 未於本次會話重新查證連結（只列書目、不給 DOI，報告中若引用請標「未查證」）：Platt 1999（"Probabilistic outputs for support vector machines…", Advances in Large Margin Classifiers）；Zadrozny & Elkan 2002（KDD, isotonic 多類別）；Kull, Silva Filho, Flach 2017（AISTATS, beta calibration, PMLR 54）；Nixon 等 2019（CVPR Workshops, "Measuring calibration in deep learning"）。
- 皮膚科影像校準專門研究：**本次未找到可靠證據**（未搜尋到具名、可查證的皮膚科分類校準研究；Lu 等 AAAI 2022 是保形預測而非校準，見問題二）。

**1.2 計算範例 [本報告計算]（假設照片彼此獨立 → 對群聚資料屬「樂觀」下界）**
- 完美校準模型在 n=56、陽性約 0.84 的模擬（2,000 次）：**10 等寬箱 ECE 平均 0.124（真值 0）**；Logistic 校準斜率中位數 1.05，**95% 區間 [0.59, 1.92]**。→ 即使模型完美校準，也觀察不出來。
- 同模擬 n≈1,000、平衡：ECE 平均 0.030（真值 0），斜率 95% 區間 [0.89, 1.15]。
- 正常類 9 張的偽陽（false-alarm）率 Wilson 95% CI：0/9 → [0, 0.299]；1/9 → [0.020, 0.435]；2/9 → [0.063, 0.547]；Clopper–Pearson 0/9 → [0, 0.336]。FUTURE 正常 333 張：0/333 → [0, 0.011]；17/333（5.1%）→ [0.032, 0.080]。
- 參數數（K=3 分期）：temperature 1；Platt（二分類）2；beta calibration 3；vector scaling 2K=6；matrix scaling／Dirichlet K(K+1)=12；isotonic 為非參數（每個階梯都是自由度）。NOW 正常類只有 9 張 → 12 參數的 Dirichlet 每參數 <1 個正常樣本。

### Inferences
**方法卡（NOW vs FUTURE）[本報告推論，依上列證據]**

| 方法 | 參數 | NOW（56 張／9 正常／14 病人） | FUTURE（~1,000 張平衡） | 主要風險 |
|---|---|---|---|---|
| Temperature scaling | 1 | 可擬合（最佳選擇），但效果無法驗證 | 首選基線 | 只修正整體信心、不改排序；偏移下可能更糟（Ovadia） |
| Platt（二分類 sigmoid） | 2 | 勉強；截距受 47:9 不平衡影響、正常類 9 張 | 可行 | 截距會吸收醫院資料的盛行率，搬到 LINE 時失準 |
| Beta calibration | 3 | 不建議 | 二分類可行 | 過擬合 |
| Vector scaling | 6 | 不可行 | 可行 | — |
| Matrix / Dirichlet（+ODIR） | 12 | 不可行 | 可行（需 ODIR／L2） | 每類 ~333 張才勉強；需病人分組選 λ |
| Isotonic | 非參數 | 不可行 | 邊緣（官方 ≪1000 不建議；每類僅 333） | 階梯狀、過擬合、平手值多 |
| Histogram binning | B | 不可行 | 不建議單用；可用 scaling-binning | 樣本效率差（Kumar） |
| Deep ensemble（5 成員） | — | 可做（3 折模型本就是集成） | 建議 | 計算成本；仍非保證 |

**OOF 校準接線方式（scikit-learn / PyTorch）[本報告推論＋業界做法]**
- scikit-learn（DINOv2 frozen + LogisticRegression）：因官方 API 未載 `groups`，**最穩妥的做法是預先算好病人分組切分，並以 iterable 傳給 `cv`**：
```python
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.calibration import CalibratedClassifierCV
splits = list(StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=0).split(X, y, groups=patient_id))
cal = CalibratedClassifierCV(LogisticRegression(C=..., max_iter=5000),
                             method="sigmoid",      # NOW；FUTURE 多類別可用 "temperature"
                             cv=splits, ensemble=False)  # False：用全部 OOF 擬合單一校準器
cal.fit(X, y)
```
  - 為何 `ensemble=False`：NOW 若 `ensemble=True`，每個校準器只看到一折（約 19 張、約 3 張正常）→ 極不穩定；False 用全部 56 個 OOF 點擬合單一校準器。風險：預測時用的「全資料重訓模型」與產生 OOF 的折模型不同，分數分佈可能更尖（訓練點更多）→ 校準器輕微不匹配。[本報告推論]
  - 切記：**不可**用 `cv=3`（整數）——那會用 `StratifiedKFold`，同病人照片同時出現在訓練與校準折 → 病人洩漏、校準器學到過度自信的分數。
  - 驗證層級必須「巢狀」：外層病人折（評估）→ 外層訓練集內再做內層病人 OOF → 擬合校準器 → 套到外層測試折。NOW：外層 3 折時內層只剩約 9 位病人、約 37 張、約 6 張正常 → 校準器估計極不穩，報告須標示「實驗性」。
- PyTorch（EfficientNet-B0）：收集病人分組 CV 的 OOF logits `z_oof (N×K)`、標籤 `y_oof`，以 NLL 擬合溫度：
```python
logT = torch.zeros(1, requires_grad=True)
opt = torch.optim.LBFGS([logT], lr=0.1, max_iter=200)
def closure():
    opt.zero_grad(); loss = F.cross_entropy(z_oof / logT.exp(), y_oof); loss.backward(); return loss
opt.step(closure); T = logT.exp().item()   # 以 log 參數化確保 T>0
```
  - 若改用類別加權訓練（處理 47:9），logits 已偏向少數類，溫度不會修正此偏移 → 需另行以截距（Platt／vector scaling bias）或先驗修正處理。[本報告推論]
- netcal 函式庫（TemperatureScaling、BetaCalibration、Histogram/ENIR、ECE/ACE/MCE 等）：**本次未查證其官方文件與目前版本**，報告中僅可作為「可選工具」提及。

**校準指標在小樣本的呈現方式 [本報告推論，依 Roelofs／Van Calster／Kumar]**
- NOW：只報 Brier score 與 log loss（皆為 proper scoring rules）＋**病人層級 bootstrap CI**（重抽病人而非照片）；校準只報 weak calibration（截距、斜率）並附 CI；可視化用「個別點 + 平滑曲線 + CI 帶」而非 10 箱 reliability diagram；**不報 ECE 或必須同時報其偏誤**（完美校準在 n=56 仍會得 ~0.12）。不做 Hosmer–Lemeshow。
- FUTURE：可報 equal-mass ECE（或 ECE_sweep／debiased ECE）＋ Brier ＋ 斜率／截距（每來源分開）；彈性校準曲線需每來源每類 ≥200 事件與 ≥200 非事件才符合 Van Calster 建議——~1,000 張分兩來源後仍可能不足，應如實寫出。

**醫院 vs LINE 的類別先驗偏移 [本報告推論]**
- 醫院資料陽性比例高（47/56≈0.84），LINE 公眾上傳的盛行率未知且可能低很多 → 依 Van Calster，校準後機率在 LINE 端會**系統性高估**靜脈炎機率。
- 可選修正：(a) 截距更新（需 LINE 端有標記樣本）；(b) Saerens EM 先驗調整（無需標記，但假設 p(x|y) 不變——手機拍攝條件不同使此假設大概率不成立）。
- **與不可違反原則的衝突**：任何「依線上資料自動調整先驗／溫度」都等同自動更新模型，違反「不自動訓練、不自動部署」；只能離線、人工審核、版本化後再手動上線。

**預期效益**：NOW 校準的實際效益主要是「讓信心分數不那麼極端，使 needs-human-review 門檻較合理」，**不能**讓分數成為疾病機率；FUTURE 可讓分數在同來源資料內近似頻率意義，但跨來源仍需分開驗證。

### Gaps
- Niculescu-Mizil & Caruana 2005 中 isotonic 優於 Platt 的精確樣本數交叉點：本次未取得全文，未找到可靠證據；「約 1000」僅能引 scikit-learn 文件的「≪1000」。
- Riley 等關於「校準所需事件數」對**影像分類**的適用性：Riley 公式針對臨床預測模型；影像 CNN 輸出的校準樣本數準則未找到可靠證據。
- netcal、beta calibration（Kull 2017）、Platt 1999、Nixon 2019 之連結／DOI 本次未查證。
- scikit-learn 是否已可透過 metadata routing 把 `groups` 傳給 `CalibratedClassifierCV` 的內部 splitter：官方 API 頁未記載，未查證；故建議預先計算 splits。
- 皮膚科／照片型臨床影像的校準研究：未找到可靠證據。
- 群聚資料下 Brier／ECE 之偏誤校正：未找到可靠證據（只能用病人層級 bootstrap）。

---

## 問題二：保形預測（Split / Cross-conformal / Mondrian / APS-RAPS-LAC / 階層資料 / 醫學應用 / 回覆對映 / 風險控制 / 小 n 的保證意義）

### Takeaway
保形預測的保證是**邊際（marginal）**、**對可交換單位**成立；本專案的可交換單位是「病人」而非「照片」。NOW 若依 Dunn 等（JASA 2023）每位病人只抽一張做校準，可用校準點 ≤14（若真的 hold-out 20% 病人則只有約 3 點 → 最小可達 α=0.25、且覆蓋率 90% 區間 0.37–0.98），保證幾乎無資訊量；**正常類只有 9 張，class-conditional（Mondrian）最小 α=0.10、在病人層級更不可能**。因此 NOW 只能把保形預測當「實驗性的分流規則」而非「保證」。FUTURE 若校準病人數 ≥~70（每病人一張）才接近 Angelopoulos & Bates 表中 ε=0.05 的精度，~200 病人以上才穩定；且醫院 vs LINE 偏移會破壞可交換性。

### Cited Findings

**2.1 核心公式與小樣本性質**
- [研究證據][D→廣泛引用教材] Angelopoulos & Bates "A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification"（arXiv 2107.07511；後以 "Conformal Prediction: A Gentle Introduction" 刊於 Foundations and Trends in ML——**期刊卷期與 DOI 本次未查證**）：
  - q̂ 為校準分數 s_1..s_n 的 **⌈(n+1)(1−α)⌉/n 經驗分位**；預測集 C(x) = {y : s(x,y) ≤ q̂}；
  - 保證：**1−α ≤ P(Y_test ∈ C(X_test)) ≤ 1−α + 1/(n+1)**（上界需分數無平手；離散 Y 需隨機化平手，教材註明實務常忽略）；假設校準與測試點 i.i.d.（可交換即可）；
  - Sec 3.2：**條件於校準集的覆蓋率為隨機量，服從 Beta(n+1−l, l)，l = ⌊(n+1)α⌋**；粗略建議校準點約 1,000；表（δ=0.1、α=0.1）：ε=0.1 → n=22；ε=0.05 → n=102；ε=0.01 → 2,491；ε=0.005 → 9,812；ε=0.001 → 244,390；
  - Sec 3.1：一般情況下條件覆蓋（conditional coverage）不可能達成；90% 邊際覆蓋可同時對某子群 100%、對另一子群 0%；
  - Sec 2.1 APS：依 softmax 由大到小累加直到包含真實標籤；RAPS 細節引用 [4]；Sec 4.2 class-conditional：在每類內分別校準 q̂^(k)；Sec 4.3 conformal risk control：E[ℓ(C(X),Y)] ≤ α（有界、單調損失）；Learn then Test 可控制非單調風險。
  — [ar5iv HTML](https://ar5iv.labs.arxiv.org/html/2107.07511)；[arXiv abs](https://arxiv.org/abs/2107.07511)（存取 2026-10-31）
- [研究證據][B] Barber, Candès, Ramdas, Tibshirani "Predictive inference with the jackknife+"（Annals of Statistics 2021;49(1):486–507, doi:10.1214/20-AOS1965）：jackknife+ 使用留一殘差與留一預測；原始 jackknife 無此保證、覆蓋率甚至可能趨近 0；演算法穩定時 jackknife 與 jackknife+ 近乎精確覆蓋。**最壞情況保證為 1−2α（本次僅由二手摘要與既有知識確認，原文定理未逐字查證）**；CV+ 為 K 折版本。— [doi](https://www.doi.org/10.1214/20-AOS1965)；[arXiv 1905.02928](https://arxiv.org/abs/1905.02928)（存取 2026-10-31）
- [研究證據][B] Romano, Sesia, Candès "Classification with Valid and Adaptive Coverage"（NeurIPS 2020, arXiv 2006.02544）：提出 APS 分數，並把 split conformal、CV+、jackknife+ 套用到分類；目標為邊際有效且近似條件覆蓋。— [NeurIPS](https://proceedings.neurips.cc/paper/2020/hash/244edd7e85dc81602b7615cd705545f5-Abstract.html)（存取 2026-10-31）
- [研究證據][D/B] Angelopoulos, Bates, Malik, Jordan "Uncertainty Sets for Image Classifiers using Conformal Prediction"（arXiv 2009.14193；作者 repo 標 ICLR 2021，**本次搜尋結果未直接確認 ICLR 出處**）：RAPS 對排名在 k_reg 之後的每個類別加常數懲罰 λ；λ=0 即 APS；ImageNet α=10% 時 APS 平均集合大小 19、RAPS 約 2；摘要稱集合常小 5–10 倍。PyTorch 實作：github.com/aangelopoulos/conformal_classification。— [arXiv](https://arxiv.org/abs/2009.14193v5)；[GitHub [E]](https://github.com/aangelopoulos/conformal_classification/)（存取 2026-10-31）
- [研究證據][B] Ding, Angelopoulos, Bates, Jordan, Tibshirani "Class-Conditional Conformal Prediction with Many Classes"（NeurIPS 2023, arXiv 2306.09335）：每類資料少時 classwise（Mondrian）校準**變異很大**；提出 clustered conformal（把分數分佈相似的類別併群校準），保證 cluster-conditional 覆蓋；classwise 在 iNaturalist 稀有類會產生過大集合。— [NeurIPS](https://proceedings.neurips.cc/paper_files/paper/2023/hash/cb931eddd563f8d473c355518ce8601c-Abstract.html)（存取 2026-10-31）
- [研究證據][B] Tibshirani, Barber, Candès, Ramdas "Conformal Prediction Under Covariate Shift"（NeurIPS 2019, arXiv 1904.06019）：若測試與訓練共變量分佈的概似比已知或可估計，**加權保形預測**可在共變量偏移下維持覆蓋。— [NeurIPS](https://papers.nips.cc/paper/8522-conformal-prediction-under-covariate-shift)（存取 2026-10-31）
- [研究證據][B] Angelopoulos, Bates, Fisch, Lei, Schuster "Conformal Risk Control"（ICLR 2024 spotlight, arXiv 2208.02814）：把保形預測推廣為控制任意有界單調損失的期望值；選門檻使期望損失 ≤ α，緊至 O(1/n)；範例包括 false negative rate。— [ICLR proceedings](https://proceedings.iclr.cc/paper_files/paper/2024/hash/f3549ef9b5ff520a7e41ff3cc306ab2b-Abstract-Conference.html)（存取 2026-10-31）
- [研究證據][B] Geifman & El-Yaniv "Selective Classification for Deep Neural Networks"（NeurIPS 2017, arXiv 1705.08500）：給定已訓練分類器，學一個拒絕函數，使「被接受樣本」的錯誤率 ≤ r* 的機率 ≥ 1−δ；以 softmax response（最大 softmax）設門檻；以 risk-coverage curve 描述；ImageNet top-5 以 99.9% 機率保證 2% 錯誤、約 60% 覆蓋。— [NeurIPS PDF](https://papers.NeurIPS.cc/paper_files/paper/2017/file/4a8423d5e91fda00bb7e46540e2b0cf1-Paper.pdf)（存取 2026-10-31）

**2.2 群聚／階層資料（核心）**
- [研究證據][B] Dunn, Wasserman, Ramdas "Distribution-Free Prediction Sets for Two-Layer Hierarchical Models"（JASA 2023;118(544):2491–2502；arXiv 1809.07441 v4, 2022-02-24）：
  - 假設：各群分佈 P_1..P_k i.i.d. 來自 meta-分佈 Π；群內觀測 i.i.d. 來自 P_j；當有群有多個觀測時，**全資料與新觀測不可交換**（正是本專案「一位病人多張照片」情境，論文動機即「每位病人多次量測」）；
  - **Single subsampling**（每群抽一個觀測再做 conformal）：**有限樣本覆蓋 ≥ 1−α**，目標為「新群（新病人）中的新觀測」；監督式需 **k > 1/α − 1** 群才可得非平凡集合（α=0.1 → 約 ≥10 群）；
  - **Repeated subsampling**：保證 ≥ 1−2α，但論文稱實務上覆蓋接近 1−α；
  - **CDF pooling**：僅**漸近**覆蓋（k→∞）；
  - 建議：可接受漸近覆蓋 → CDF pooling（覆蓋與集合大小平衡佳）；需有限樣本保證 → repeated subsampling；
  - 對「既有群（舊病人）的新觀測」另有定理（Theorems 11–12），需該群觀測數 n_1 > 1/α − 1，非 subsampling 方法。
  — [arXiv v4](https://arxiv.org/abs/1809.07441v4)；[ar5iv](https://ar5iv.labs.arxiv.org/html/1809.07441)；[RePEc 卷期頁](https://ideas.repec.org/a/taf/jnlasa/v118y2023i544p2491-2502.html)（存取 2026-10-31）
- [研究證據][D] Lee, Barber, Willett "Distribution-free inference with hierarchical data"（arXiv 2306.06342 v3, 2024-03）：導出「階層可交換性」，據此推廣 conformal 與 jackknife+ 到群組／重複量測資料；提出 **second-moment coverage** 以更好控制條件誤覆蓋率。**正式期刊出處本次未確認 → 標 [D]**。— [arXiv](https://arxiv.org/html/2306.06342v3)（存取 2026-10-31）

**2.3 醫學應用（含病人層級洩漏與外部驗證檢核）**
- [研究證據][B] Olsson 等 "Estimating diagnostic uncertainty in artificial intelligence assisted pathology using conformal prediction"（**Nature Communications 2022;13:7761**——注意：任務簡述寫「BJC」，經查實為 Nat Commun，未找到同名 BJC 論文）：STHLM3 研究，訓練 7,788 片切片／1,192 名男性、測試 3,059 片／676 名男性；在「非典型前列腺組織」子集，加保形預測後癌症偵測錯誤 **3（2%） vs 無保形 44（25%）**，並標記 143（80%）為不可靠。**病人層級洩漏**：訓練與測試以「男性」區分（病人不重疊），洩漏風險低；**外部驗證**：本次摘要未確認，需讀全文。資料量為本專案 ~100 倍。— [Nat Commun PDF](https://www.nature.com/articles/s41467-022-34945-8.pdf)；[Tampere research portal](https://researchportal.tuni.fi/en/publications/estimating-diagnostic-uncertainty-in-artificial-intelligence-assi/)（存取 2026-10-31）
- [研究證據][B] Lu, Lemay, Chang, Höbel, Kalpathy-Cramer "Fair Conformal Predictors for Applications in Medical Imaging"（AAAI 2022;36:12008–12016, arXiv 2109.04392）：訪談放射科醫師找出 rule-in／rule-out 用例；在**皮膚病灶照片**資料上評估；group-conditional（依膚色）conformal 對惡性病灶給出更適應的覆蓋。**病人層級洩漏與外部驗證：摘要未說明，未查證**。— [AAAI OJS](https://ojs.aaai.org/index.php/AAAI/article/view/21459)；[code [E]](https://github.com/clu5/aaai22)（存取 2026-10-31）
- [研究證據][D] Lu, Angelopoulos, Pomerantz "Improving Trustworthiness of AI Disease Severity Rating in Medical Imaging with Ordinal Conformal Prediction Sets"（arXiv 2207.02238, 2022-07；**會議／工作坊出處本次未確認**）：腰椎 MRI 脊椎狹窄分級；提出 **Ordinal APS**，**預測集永遠是連續嚴重度區間**；409 筆 MRI 檢查上覆蓋緊、集合小；大集合對應較多影像偽影或腫瘤 → 可引導醫師注意。**病人層級洩漏／外部驗證：摘要未說明**。— [arXiv](https://arxiv.org/abs/2207.02238v1)（存取 2026-10-31）

**2.4 函式庫（接線）**
- [業界做法][E] MAPIE v1.x（scikit-learn-contrib）：`SplitConformalClassifier(estimator, confidence_level, conformity_score="lac", prefit=True, ...)`，流程 `fit` → `conformalize` → `predict_set`；`CrossConformalClassifier` 用 `fit_conformalize` → `predict_set`（每點由未見過該點的模型預測）；分數可用字串（"lac"、"aps" 等）或 `BaseClassificationScore` 物件。注意 **`confidence_level` = 1−α**（v1 前的 `alpha` 介面已改）。**是否支援 `groups` 傳入 CrossConformal 的 splitter：本次未查證**。— [MAPIE source (stable)](https://mapie.readthedocs.io/en/stable/_modules/mapie/classification.html)；[v1.2.1](https://mapie.readthedocs.io/en/v1.2.1/_modules/mapie/classification.html)（存取 2026-10-31）
- [業界做法][E] crepes：標準與 **Mondrian** conformal classifiers／regressors／predictive systems；可自訂 Mondrian 類別函數；`crepes.martingales` 用於**檢驗可交換性**。具體 API（WrapClassifier、calibrate、bins 等）與版本本次首頁未列出、未查證。— [crepes docs](https://crepes.readthedocs.io/en/latest/)（存取 2026-10-31）
- [業界做法][A/E] TorchCP（JMLR vol. 26, 2025；LGPL-3.0）：predictors `SplitPredictor`、`ClassConditionalPredictor`、`ClusteredPredictor`、加權（covariate shift）predictor；scores LAC、APS、RAPS、SAPS、TopK、Margin、kNN、Entmax；1.2.x 加入 p-value 與 conformal predictive distributions；**無內建 temperature scaling 工具**（僅引用 ConfTS 相關論文）。— [GitHub](https://github.com/ml-stat-Sustech/TorchCP)（存取 2026-10-31）

**2.5 數值範例 [本報告計算]**（split conformal、連續分數、無平手；C = 條件於校準集之覆蓋率 ~ Beta(k, n+1−k)，k=⌈(n+1)(1−α)⌉；**最小可達 α = 1/(n+1)**；k>n 時 q̂=+∞ → 集合恆為全部類別）

| 校準點 n（可交換單位） | α | k | E[C] | C 的 5%–95% | P(C < 1−α−0.05) |
|---|---|---|---|---|---|
| 3（≈20% hold-out 病人，每人 1 張） | 0.10 / 0.20 | 4>n | 平凡集合 | — | — |
| 3 | 0.25 | 3 | 0.750 | 0.368–0.983 | 0.343 |
| 9（正常類照片數） | 0.10 | 9 | 0.900 | 0.717–0.994 | 0.232 |
| 14（全部病人，每人 1 張，OOF） | 0.05 | 15>n | 平凡集合 | — | — |
| 14 | 0.10 | 14（=最大分數） | 0.933 | 0.807–0.996 | 0.103 |
| 14 | 0.20 | 12 | 0.800 | 0.615–0.939 | 0.281 |
| 18（held-out 照片數，但非可交換） | 0.10 | 18 | 0.947 | 0.847–0.997 | 0.054 |
| 20 | 0.10 | 19 | 0.905 | 0.784–0.982 | 0.176 |
| 40 | 0.10 | 37 | 0.902 | 0.817–0.965 | 0.130 |
| 56（全部照片，若誤當可交換） | 0.05 | 55 | 0.965 | 0.918–0.994 | 0.020 |
| 56 | 0.10 | 52 | 0.912 | 0.844–0.964 | 0.063 |
| 56 | 0.20 | 46 | 0.807 | 0.716–0.886 | 0.139 |
| 67 | 0.10 | 62 | 0.912 | 0.849–0.960 | 0.051 |
| 100 | 0.10 | 91 | 0.901 | 0.848–0.945 | 0.055 |
| 200 | 0.10 | 181 | 0.900 | 0.864–0.933 | 0.015 |
| 333（FUTURE 每類） | 0.10 | 301 | 0.901 | 0.873–0.927 | 0.002 |
| 1000 | 0.10 | 901 | 0.900 | 0.884–0.915 | <0.001 |

- 雙邊精度 P(|C−0.9| ≤ 0.05)：n=14 → 0.385；n=18 → 0.344；n=56 → 0.789。n=14 時 P(|C−0.9| ≤ 0.10) = 0.956。
- 我以「P(1−α−ε ≤ C ≤ 1−α+ε) ≥ 0.9」計算得 ε=0.1 → n=11、ε=0.05 → n=90，與教材表（22、102）**不一致**；推測教材採不同準則（例如含有限測試集或其他定義），**本報告未能查清差異來源**，撰寫時應引用教材原表，並把本表標為「自行計算、準則為條件覆蓋之 Beta 分佈」。
- 在有限測試集 m 上觀察到的經驗覆蓋還要再加二項變異（Beta-Binomial）：n=14、m=14、α=0.1 → 經驗覆蓋 SD ≈ 0.090；α=0.2 → 0.144；n=56、m=18、α=0.1 → 0.076；n=333、m=333、α=0.1 → 0.023。→ NOW 在 3 折中每折觀察到 0.7 或 1.0 的覆蓋都是「正常波動」。
- Dunn single subsampling 所需校準病人數 k > 1/α − 1：α=0.1 → ≥10 位；α=0.2 → ≥5 位；α=0.25 → ≥4 位。NOW 若 hold-out 20%（≈3 位病人）→ 任何 α<0.25 都無法得到非平凡集合。
- Conformal risk control（正常照片偽陽率，損失 ∈[0,1]，B=1）：λ̂ = inf{λ : (n/(n+1))·R̂_n(λ) + B/(n+1) ≤ α} ⇒ 經驗偽陽率需 ≤ (α(n+1) − 1)/n。n_normal=9：α=0.1 → 需 **0/9**；α=0.2 → ≤1/9。n_normal=30：α=0.1 → ≤2/30。n_normal=333：α=0.1 → ≤32/333。（以照片為單位仍違反群聚；病人層級的正常病人數更少。）

### Inferences
**(a) 分數函數選擇 [本報告推論]**
- 二分類：LAC（s = 1 − p̂_y）即可；APS／RAPS 在 2 類時差異很小。
- 三分期（正常 < 一期 < 二期，具順序）：優先 **Ordinal APS**（Lu 2022）或「只允許連續區間」的 LAC 變體，避免出現 {正常, 二期} 這種不連續、臨床無意義的集合；RAPS 的正則化在 K=3 時意義不大。
- 先做 temperature scaling 再做 conformal：覆蓋保證不受影響（conformal 對任何分數都有效），只影響集合大小／適應性。

**(b) 病人層級 split conformal 偽代碼 [本報告推論，依 Dunn 2023 single/repeated subsampling]**
```python
# 前提：模型已以「非校準病人」訓練完成（或以病人分組 CV 取得 OOF 機率 P_oof）
def conformal_qhat(scores, alpha):
    n = len(scores); k = math.ceil((n + 1) * (1 - alpha))
    return np.inf if k > n else np.sort(scores)[k - 1]      # 第 k 小

def patient_level_qhat(P, y, pid, alpha, B=200, rng=np.random.default_rng(0)):
    # single subsampling：每位病人隨機抽 1 張；repeated：重複 B 次
    qs = []
    for b in range(B):
        idx = [rng.choice(np.where(pid == p)[0]) for p in np.unique(pid)]
        s = 1 - P[idx, y[idx]]                                 # LAC 分數
        qs.append(conformal_qhat(s, alpha))
    return qs   # B=1 → 有限樣本 ≥1−α；repeated 需依 Dunn 的 p 值合併規則（保證 ≥1−2α），不可直接取中位數當作有保證
def predict_set(p_test, qhat):
    return [c for c in range(len(p_test)) if 1 - p_test[c] <= qhat]
```
- 注意：「取 B 個 q̂ 的中位數」是常見捷徑，但**不是** Dunn 證明的程序；若要宣稱保證，需依其 repeated-subsampling 定義（平均 p 值 ×2）實作——本次未逐式查證該定義的全部細節，實作前需讀原文 Sec 4。
- MAPIE／TorchCP／crepes 皆**以樣本為單位**，不會自動處理病人群聚；必須在呼叫前自行做「每病人一張」的子抽樣，或把 `groups` 切分傳給 CV（MAPIE 支援度未查證）。

**(c) 預測集 → 回覆類型對映 [本報告推論]**
| 預測集 | 回覆 | 說明 |
|---|---|---|
| 單一 {靜脈炎} 或 {一期}/{二期} | result（研究參考結果） | 仍需「非臨床診斷」字樣；附「研究原型、校準樣本極少」 |
| 單一 {正常} | result，但 NOW 建議改為 needs human review | 正常類僅 9 張，任何「正常」判斷的偽陰風險無法估計（Wilson 上界 0.30–0.44） |
| {一期, 二期} | result「疑似靜脈炎、分期不確定」或 needs human review | 視產品政策 |
| 含「正常」且含任一期 | needs human review | 涵蓋「有／無」兩種臨床決策 |
| 全部類別（含 q̂=+∞ 的平凡集合） | needs human review | NOW α 過小時必然發生 |
| 空集合 ∅（LAC 在 q̂ 小時可能出現） | please retake / cannot judge | **空集合不是 OOD 偵測的保證**；應另設影像品質閘門（模糊、曝光、未見手臂）與 YOLO 偵測失敗規則，兩者都觸發 please retake |
- 選擇性分類（Geifman 2017）可作為等價替代：以 max-softmax（或校準後機率）設門檻、畫 risk-coverage curve；NOW 只能描述性畫出（病人層級 bootstrap 帶），不可宣稱「以 1−δ 機率錯誤率 ≤ r*」。
- 控制「正常照片偽陽率」：用 conformal risk control 或 Learn-then-Test 選「判為靜脈炎」的門檻；NOW 的 9 張正常（實際病人更少）使 α=0.1 需要 0/9 偽陽 → 實務上會把門檻推到幾乎不判陽 → **NOW 不可行**；FUTURE 正常 ~333 張（若來自 ≥~50 位病人）才有意義。

**(d) 保證在本專案的「實際意義」[本報告推論]**
- 保證是**對新病人平均**的邊際覆蓋，不是「這一張照片有 90% 機率正確」；也不是 per-class、per-source 覆蓋（除非 Mondrian）。
- NOW：(i) 照片不可交換 → 以 56 張當校準點的保證在形式上**不成立**（同病人分數高度相關，有效樣本數接近 14 甚至更小）；(ii) 以病人為單位 n≤14，α=0.1 時 q̂ = 最大校準分數，任何比校準集更差的新病人都會得到全類別集合；覆蓋率 5–95% 區間 0.81–1.00（α=0.1）或 0.62–0.94（α=0.2）；(iii) 若要同時保留 hold-out 測試病人，校準病人只剩約 3 位 → 不可用。
- 分佈偏移：醫院 → LINE 是共變量偏移（拍攝裝置、光線、膚色、角度）＋標籤偏移（盛行率）；依 Tibshirani 2019 需可估計的概似比才能加權，這需要**有標記的 LINE 資料**或至少大量未標記 LINE 影像訓練域分類器；NOW 不可行。
- 監測：shadow mode（只記錄、不回覆）收集 LINE 案例＋事後專家標記，以 crepes martingales 檢驗可交換性、按月報告經驗覆蓋＋CI；**不可自動依監測結果重設 q̂**（違反不自動部署原則），重設需人工審核與版本紀錄。

**(e) 與不可違反原則的衝突標記 [本報告推論]**
- 「coverage guarantee」字樣易被誤讀為臨床準確率保證 → 違反「不宣稱臨床診斷」；UI／報告應寫「研究用不確定性分流規則，基於 n 位病人校準，覆蓋率估計區間 x–y」。
- 自動重新校準、自動 weighted conformal 權重更新 → 違反「不自動訓練／部署」。
- 所有函式庫皆可純本機執行（MAPIE、crepes、TorchCP 不需雲端），與「全部本機運算」無衝突。

**NOW vs FUTURE 摘要**
- NOW：可做「病人分組 OOF → 每病人抽 1 張 → split conformal（α=0.2 或 0.25）」作為**實驗性分流**；同時報「若誤以照片為單位」的對照，示範兩者差異；不做 Mondrian、不做 CRC。最低資料：α=0.2 需 ≥5 位校準病人（Dunn），α=0.1 需 ≥10 位。
- FUTURE：~1,000 張若來自足夠病人（建議校準病人 ≥70 以達教材 ε≈0.05 精度量級；本報告計算 n=67 時 P(C<0.85)=0.051），可做：Ordinal APS + 病人層級 split／repeated subsampling；Mondrian 對「正常」類（每類 ≥~70 位病人才有意義）或 Ding 2023 的 clustered conformal；以 CRC 控制正常偽陽率；醫院、LINE 分開校準（Mondrian by source）並分開報告。

### Gaps
- Angelopoulos & Bates 在 Foundations and Trends in ML 的正式卷期與 DOI：本次未查證。
- RAPS 的 ICLR 2021 出處：搜尋結果未直接確認（作者 repo 有標示，但未逐字查證）。
- Lu 2022 ordinal conformal 的正式出處（會議／工作坊）：未確認，標 [D]。
- Lee, Barber, Willett 2023 正式期刊出處：未確認。
- Jackknife+／CV+ 精確保證式（含 CV+ 的附加項）：未逐字查證原文定理。
- **「群聚資料上的 cross-conformal／CV+ 分類」是否有正式保證**：未找到可靠證據（Lee 等 2023 推廣了 jackknife+ 到階層資料，但本次未讀到分類 CV+ 的具體定理）。
- Vovk 2003（Mondrian）、Vovk, Gammerman, Shafer 2005 書、Löfström 2015、Lei 等 2018 JASA、Learn-then-Test（Angelopoulos 等 2021 arXiv 2110.01052）：本次未查證連結，引用時標「未查證」。
- 皮膚科 conformal 的病人層級切分與外部驗證細節（Lu AAAI 2022）：未讀全文、未確認。
- 教材 n(ε) 表的準則與本報告 Beta 計算不一致的原因：未查清。
- MAPIE v1 是否接受 `groups`；crepes 目前版本與 API：未查證。

---

## 問題三：小樣本結論——NOW 可信什麼、FUTURE 可信什麼、如何呈現

### Takeaway
NOW（14 位病人、9 張正常）：校準與保形預測都**只能作為方法演示與實驗性分流規則**，任何「已校準」「90% 覆蓋保證」字樣都不可信也不應出現；最誠實的呈現是病人層級的經驗覆蓋與集合大小（每折＋CI）、Brier／log loss 附病人 bootstrap CI，並把「正常」判斷一律送人工複核。FUTURE（~1,000 張三類平衡）：若病人數足夠（關鍵是病人數，而非照片數），temperature／vector／Dirichlet(ODIR) 校準與病人層級 split conformal（Ordinal APS）可提供有意義的「同來源內」保證；跨醫院／LINE 仍須分開驗證與 shadow mode 監測。

### Cited Findings
- 條件覆蓋為 Beta(n+1−l, l) 隨機量，教材建議校準約 1,000 點，δ=0.1、α=0.1、ε=0.05 需 n=102 — [Angelopoulos & Bates, ar5iv](https://ar5iv.labs.arxiv.org/html/2107.07511)（存取 2026-10-31）
- 群聚資料需每群子抽樣才有有限樣本保證，監督式需群數 k > 1/α − 1 — [Dunn, Wasserman, Ramdas, arXiv/JASA](https://ar5iv.labs.arxiv.org/html/1809.07441)（存取 2026-10-31）
- 小資料只評估 weak calibration 可辯護；校準曲線需 ≥200 事件＋≥200 非事件；不用 Hosmer–Lemeshow；不同場域盛行率不同會失準、需在地監測 — [Van Calster 2019, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC6912996/)（存取 2026-10-31）
- ECE_bin 對完美校準模型偏誤最大 — [Roelofs 2022, PMLR](https://proceedings.mlr.press/v151/roelofs22a.html)（存取 2026-10-31）
- 校準在資料偏移下會失效、temperature scaling 可能讓偏移資料更差 — [Ovadia 2019, NeurIPS](https://papers.nips.cc/paper/2019/hash/8558cb408c1d76621371888657d2eb1d-Abstract.html)（存取 2026-10-31）
- 外部驗證樣本數由校準斜率準則主導（範例 177 事件／9,835 人）— [Riley 2021, Stat Med](https://eprints.keele.ac.uk/id/eprint/9707)（存取 2026-10-31）
- isotonic 在 ≪1000 校準樣本時不建議 — [scikit-learn 1.9.1](https://scikit-learn.org/stable/modules/generated/sklearn.calibration.CalibratedClassifierCV.html)（存取 2026-10-31）
- 醫學影像保形預測成功案例的資料規模（Olsson：訓練 1,192 人、測試 676 人；Lu ordinal：409 檢查）遠大於本專案 — [Olsson 2022 Nat Commun](https://www.nature.com/articles/s41467-022-34945-8.pdf)；[Lu 2022 arXiv](https://arxiv.org/abs/2207.02238v1)（存取 2026-10-31）

### Inferences
**可信度判定表 [本報告推論＋計算]**

| 項目 | NOW 可信嗎 | FUTURE 可信嗎（前提：足夠病人數、單一來源內） |
|---|---|---|
| Temperature scaling（病人 OOF 擬合） | 可「做」，不可「驗證」；不改變 UI「非疾病機率」字樣 | 可，報 NLL／Brier 改善＋斜率 CI |
| Platt／beta | Platt 勉強；beta 否 | 可 |
| Isotonic、Dirichlet、matrix | 否 | Dirichlet(ODIR)／vector 可；isotonic 邊緣 |
| ECE 數值 | 否（偏誤 ≈0.12 量級） | equal-mass／debiased ECE 可，附 CI |
| 校準斜率／截距 | 只能報、CI 極寬（≈0.6–1.9） | 可（≈±0.13） |
| Split conformal 覆蓋「保證」 | 否（病人 ≤14、hold-out 僅約 3） | 可（校準病人 ≥~70；每病人一張或 repeated subsampling） |
| Mondrian／class-conditional（正常類） | 否（正常 9 張；最小 α 0.10，病人層級更差） | 需正常類校準病人 ≥~70，否則用 clustered conformal |
| Conformal risk control（正常偽陽率） | 否（α=0.1 需 0/9 偽陽） | 可（正常病人數足夠時） |
| 跨來源（醫院 → LINE）保證 | 否 | 否，除非有 LINE 標記資料做分源校準或加權 |

**建議的呈現方式（給報告與 UI）[本報告推論]**
1. 一律標「實驗性（experimental）／研究原型」；分數維持「非疾病機率」說明；NOW 不在 UI 顯示「已校準機率」或「覆蓋率保證」。
2. 報表內容：每個病人折的經驗覆蓋（以病人為單位計，每病人一票或每病人平均）＋平均集合大小＋單例比例＋空集合比例；以**病人層級 bootstrap** 給 95% CI；並附本報告的 Beta 理論區間表，讓讀者看到「0.7–1.0 之間的波動是正常的」。
3. 同時列出「照片為單位（錯誤做法）」vs「病人為單位（正確做法）」的結果對照，作為方法學教育素材，並明說前者高估可信度。
4. 正常類：NOW 報 false-alarm 率時一律附 Wilson CI（例：0/9 → 0–30%）；任何「正常」回覆送人工複核。
5. FUTURE：醫院與 LINE 分開報告校準與覆蓋；LINE 先以 shadow mode 收集、人工標記後才可納入校準；任何 q̂／溫度更新需人工審核、版本化、留存驗證紀錄（符合不自動訓練／部署原則）。
6. 最低資料門檻（本報告建議，非文獻標準）：「可宣稱 α=0.2 的病人層級覆蓋」→ 校準病人 ≥5（形式上）但實質建議 ≥40；「可宣稱 α=0.1 且 ±5% 精度」→ 校準病人 ≥~70–100；「可評估彈性校準曲線」→ 每來源每類 ≥200 事件＋≥200 非事件（Van Calster）。

**FUTURE 情境的關鍵不確定性**：~1,000 張若仍只來自少數病人（例如 50 位），可交換單位只有 50（校準約 10–20 位）→ 結論幾乎與 NOW 相同。**照片數增加不等於校準能力增加**；報告必須明確要求記錄並報告病人數。

### Gaps
- 未找到針對「每位病人多張照片、病人數 <20」的影像分類校準或保形預測實證研究（未找到可靠證據）；所有 NOW 結論來自理論推導＋本報告計算。
- 靜脈炎照片 AI 的校準／保形預測研究：未找到可靠證據（本次未專門搜尋，屬其他研究者範圍可能涵蓋）。
- 病人層級 bootstrap 對極少群（14 群）的 CI 覆蓋表現本身也不可靠；文獻證據未查。

### 參考文獻總表（皆存取於 2026-10-31）
| # | 等級 | 書目 | 連結／DOI | 查證狀態 |
|---|---|---|---|---|
| 1 | A | scikit-learn developers. CalibratedClassifierCV, v1.9.1 documentation | https://scikit-learn.org/stable/modules/generated/sklearn.calibration.CalibratedClassifierCV.html | 已讀 |
| 2 | B | Guo C, Pleiss G, Sun Y, Weinberger KQ. On calibration of modern neural networks. ICML 2017, PMLR 70:1321–1330 | https://arxiv.org/abs/1706.04599 | 書目已確認 |
| 3 | B | Kull M, Perello-Nieto M, Kängsepp M, Silva Filho T, Song H, Flach P. Beyond temperature scaling: Dirichlet calibration. NeurIPS 2019 | https://proceedings.neurips.cc/paper/2019/hash/8ca01ea920679a0fe3728441494041b9-Abstract.html | 書目已確認（作者全名單部分確認） |
| 4 | B | Niculescu-Mizil A, Caruana R. Predicting good probabilities with supervised learning. ICML 2005. doi:10.1145/1102351.1102430 | https://mlanthology.org/icml/2005/niculescumizil2005icml-predicting | 書目確認，全文未讀 |
| 5 | B | Kumar A, Liang P, Ma T. Verified uncertainty calibration. NeurIPS 2019 | https://papers.nips.cc/paper/8635-verified-uncertainty-calibration | 摘要已確認 |
| 6 | B | Roelofs R, Cain N, Shlens J, Mozer MC. Mitigating bias in calibration error estimation. AISTATS 2022, PMLR 151:4036–4054 | https://proceedings.mlr.press/v151/roelofs22a.html | 摘要已確認 |
| 7 | B | Van Calster B, McLernon DJ, van Smeden M, Wynants L, Steyerberg EW. Calibration: the Achilles heel of predictive analytics. BMC Med 2019;17:230. doi:10.1186/s12916-019-1466-7 | https://pmc.ncbi.nlm.nih.gov/articles/PMC6912996/ | 全文已讀 |
| 8 | B | Riley RD, et al. Minimum sample size for external validation of a clinical prediction model with a binary outcome. Stat Med 2021;40(19):4230–4251. doi:10.1002/sim.9025 | https://eprints.keele.ac.uk/id/eprint/9707 | 摘要已確認 |
| 9 | B | Mehrtash A, Wells WM, Tempany CM, Abolmaesumi P, Kapur T. Confidence calibration and predictive uncertainty estimation for deep medical image segmentation. IEEE TMI 2020;39(12):3868–3878. doi:10.1109/TMI.2020.3006437 | https://pmc.ncbi.nlm.nih.gov/articles/PMC7704933 | 摘要已確認 |
| 10 | B | Ovadia Y, et al. Can you trust your model's uncertainty? NeurIPS 2019 | https://papers.nips.cc/paper/2019/hash/8558cb408c1d76621371888657d2eb1d-Abstract.html | 摘要已確認 |
| 11 | B | Saerens M, Latinne P, Decaestecker C. Adjusting the outputs of a classifier to new a priori probabilities. Neural Comput 2002;14(1):21–41. doi:10.1162/089976602753284446 | https://mlanthology.org/neco/2002/saerens2002neco-adjusting | 書目已確認 |
| 12 | D（教材） | Angelopoulos AN, Bates S. A gentle introduction to conformal prediction and distribution-free uncertainty quantification. arXiv:2107.07511 | https://arxiv.org/abs/2107.07511 | 內容已讀（ar5iv）；期刊版卷期未查證 |
| 13 | B | Dunn R, Wasserman L, Ramdas A. Distribution-free prediction sets for two-layer hierarchical models. JASA 2023;118(544):2491–2502 | https://arxiv.org/abs/1809.07441v4 | 定理已讀（ar5iv） |
| 14 | D | Lee Y, Barber RF, Willett R. Distribution-free inference with hierarchical data. arXiv:2306.06342 | https://arxiv.org/abs/2306.06342 | 摘要已確認 |
| 15 | B | Barber RF, Candès EJ, Ramdas A, Tibshirani RJ. Predictive inference with the jackknife+. Ann Stat 2021;49(1):486–507. doi:10.1214/20-AOS1965 | https://www.doi.org/10.1214/20-AOS1965 | 書目已確認；定理未逐字查 |
| 16 | B | Romano Y, Sesia M, Candès EJ. Classification with valid and adaptive coverage. NeurIPS 2020 | https://proceedings.neurips.cc/paper/2020/hash/244edd7e85dc81602b7615cd705545f5-Abstract.html | 摘要已確認 |
| 17 | D/B | Angelopoulos AN, Bates S, Malik J, Jordan MI. Uncertainty sets for image classifiers using conformal prediction. arXiv:2009.14193（ICLR 2021，出處未直接確認） | https://arxiv.org/abs/2009.14193v5 | 摘要已確認 |
| 18 | B | Ding T, Angelopoulos AN, Bates S, Jordan MI, Tibshirani RJ. Class-conditional conformal prediction with many classes. NeurIPS 2023 | https://proceedings.neurips.cc/paper_files/paper/2023/hash/cb931eddd563f8d473c355518ce8601c-Abstract.html | 摘要已確認 |
| 19 | B | Tibshirani RJ, Barber RF, Candès EJ, Ramdas A. Conformal prediction under covariate shift. NeurIPS 2019 | https://papers.nips.cc/paper/8522-conformal-prediction-under-covariate-shift | 摘要已確認 |
| 20 | B | Angelopoulos AN, Bates S, Fisch A, Lei L, Schuster T. Conformal risk control. ICLR 2024 | https://proceedings.iclr.cc/paper_files/paper/2024/hash/f3549ef9b5ff520a7e41ff3cc306ab2b-Abstract-Conference.html | 摘要已確認 |
| 21 | B | Geifman Y, El-Yaniv R. Selective classification for deep neural networks. NeurIPS 2017 | https://papers.NeurIPS.cc/paper_files/paper/2017/file/4a8423d5e91fda00bb7e46540e2b0cf1-Paper.pdf | 摘要已確認 |
| 22 | B | Olsson H, et al. Estimating diagnostic uncertainty in AI assisted pathology using conformal prediction. Nat Commun 2022;13:7761 | https://www.nature.com/articles/s41467-022-34945-8.pdf | 摘要已確認（非 BJC） |
| 23 | B | Lu C, Lemay A, Chang K, Höbel K, Kalpathy-Cramer J. Fair conformal predictors for applications in medical imaging. AAAI 2022;36:12008–12016 | https://ojs.aaai.org/index.php/AAAI/article/view/21459 | 摘要已確認 |
| 24 | D | Lu C, Angelopoulos AN, Pomerantz S. Improving trustworthiness of AI disease severity rating in medical imaging with ordinal conformal prediction sets. arXiv:2207.02238 | https://arxiv.org/abs/2207.02238v1 | 摘要已確認 |
| 25 | E | MAPIE (scikit-learn-contrib) classification module, stable/v1.2.1 | https://mapie.readthedocs.io/en/stable/_modules/mapie/classification.html | 搜尋摘要確認簽名 |
| 26 | E | crepes documentation | https://crepes.readthedocs.io/en/latest/ | 首頁已讀 |
| 27 | A/E | TorchCP (JMLR 26, 2025) GitHub | https://github.com/ml-stat-Sustech/TorchCP | README 已讀 |
| — | 未查證 | Platt 1999；Zadrozny & Elkan 2002；Kull, Silva Filho, Flach 2017 (beta calibration)；Nixon et al. 2019；Vovk 2003 / Vovk, Gammerman, Shafer 2005；Löfström 2015；Lei et al. 2018 JASA；Angelopoulos et al. Learn then Test (arXiv 2110.01052)；netcal | — | 本次未查證連結，引用時須標註 |
