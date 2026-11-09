# 標註品質方法學：單一標註者風險、一致性研究設計、檔名規則標籤稽核抽樣、病灶框標註規範

> 研究日期：2026-10-30／31（存取日期同）。來源分級：[A] 官方/標準/報告指引；[B] 系統性回顧/頂級期刊；[C] 一般同儕審查；[D] 預印本；[E] 部落格/程式碼/論壇（僅輔助）。
> 結論標記：**研究證據顯示**（有文獻）／**業界慣例**（常見做法）／**本報告推論**（自行推導或計算）。
> 計算腳本：`C:\Users\user\AppData\Local\Temp\claude\C--Users-user-Desktop-Phlebitis\65222311-7d94-4b7e-9464-8d7c78613042\scratchpad\compute.py`（numpy 2.5.2 / scipy 1.18.1，專案 venv，本機執行，無資料上傳；模擬種子 20261030）。
> 專案背景假設：約 120 張照片／14 位病人（平均 m ≈ 8.57 張/人）；分期 normal 9 / stage 1 23 / stage 2 24（共 56 張有分期）；約 24 張有病灶框（框不含分期）；義大（E-Da）標籤由檔名規則自動推導；LINE 照片人工檢視；單一標註者；未來約 1,000 張、類別平衡。研究原型，非診斷用途。
> 引用透明度說明：標「(全文/頁面已開啟)」者為本次實際開啟閱讀；標「(僅檢索摘要)」者只看到搜尋結果摘要或書目紀錄，報告撰寫者若要逐字引用應再核對原文。教科書標準公式若本次未在原始論文中逐字核對，會註明「標準公式，未於本次核對原文」。

---

## A. 單一標註者風險與評分者間/評分者內一致性研究設計

### Takeaway
研究證據顯示，單一標註者的標籤存在系統性錯漏（例如資深標註者初讀漏掉約 18% 腦部病灶），且測試集標籤錯誤會改變模型排名；以多位標註者加上共識/STAPLE 聚合可明顯降低大錯誤率。本專案三類有序分期（normal/1/2）建議主指標用**二次加權 kappa（2 位評分者）或 Krippendorff's α（ordinal，≥3 位）**，並同時報告百分比一致率、Gwet's AC1 與類別別一致率；以 κ0=0.4 對 κ1=0.7、α=0.05、power 0.8 計，2 位評分者約需 **43–46 張（雙尾）**、3 位約需 **28–31 張**，再依病人群聚（design effect）放大，實務建議 **每位病人最多取 2–3 張、總共 ≥60 張**的一致性子集（本報告推論）。

### Cited Findings

**A1. 標籤雜訊盛行率與單一標註者風險**
- Northcutt 等（NeurIPS 2021 Datasets & Benchmarks track）估計 10 個常用基準資料集的**測試集**平均至少 3.3% 標籤錯誤；ImageNet 驗證集至少 6% 錯誤；以修正後標籤評估時，只要錯標測試樣本比例增加 6%，ResNet-18 就會勝過 ResNet-50（CIFAR-10 上 VGG-11 在增加 5% 時勝過 VGG-19）。研究證據顯示：測試集雜訊會翻轉模型排名。 — [Northcutt et al., arXiv:2103.14749](https://arxiv.org/abs/2103.14749) [B]（頁面已開啟）
- Karimi、Dou、Warfield、Gholipour（Med Image Anal 2020;65:101759, DOI 10.1016/j.media.2020.101759）回顧醫學影像標籤雜訊：指出專家間顯著的觀察者間變異是常見問題；PACS 自動挖掘或規則產生的標籤預期比專家標註更嘈雜；群眾外包與自動產生標籤「通常有很高的雜訊」。 — [Karimi et al. 2020, PMC7484266](https://pmc.ncbi.nlm.nih.gov/articles/PMC7484266/) [B]（全文已開啟前半）
- 同一回顧的實例：結節性硬化症 MRI，一位有經驗的標註者首次判讀找到 306 個病灶，後續重讀在 12 個掃描中再找到 68 個（約 18% 初次遺漏），遺漏者偏小、偏淡、偏孤立——作者稱人類注意力造成「系統性」標籤雜訊。 — [Karimi et al. 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7484266/) [B]
- 同回顧：一般病理醫師 Gleason 分級 Cohen's κ 約 0.40–0.60（引用 Allsbrook 等、Nir 等）。以**單一病理醫師**標籤訓練：癌 vs 良性準確率 0.80、高 vs 低分級 0.65；以多數決/STAPLE 聚合後第一任務達 0.86/0.84；單一醫師標籤產生 7% 大錯誤，多標註者方法 1–3%（標註者混淆矩陣建模最低 1%）。 — [Karimi et al. 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7484266/) [B]
- 同回顧：腦病灶實驗中，12 個乾淨標註掃描訓練的模型與 153 個嘈雜掃描相當（DSC 0.578 vs 0.584）——「小而乾淨」可抵「大而嘈雜」。作者建議取得共識標籤或多位專家標籤並以適當方法聚合；並提醒以 STAPLE 估計的真值作測試標準，從訓練/測試分離角度看「可能不是最佳做法」。 — [Karimi et al. 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7484266/) [B]

**A2. 一致性係數：定義、選用與詮釋**
- Kappa 適用名目或有序量表的信度評估，有未加權與加權兩型；影響 kappa 大小的因素包括**盛行率（prevalence）、偏差（bias，兩評分者邊際分布不同）與非獨立評分**；並提供 kappa 研究樣本數表。 — [Sim & Wright 2005, Phys Ther 85(3):257–268, PubMed 15733050](https://pubmed.ncbi.nlm.nih.gov/15733050/) [C]（僅檢索摘要；表格未開啟）
- 公式（標準公式，未於本次核對原文）：
  - Cohen's κ = (p_o − p_e)/(1 − p_e)，p_e = Σ_j p_{A,j} p_{B,j}。
  - 加權 κ_w = 1 − Σ w_ij o_ij / Σ w_ij e_ij（以不一致權重表示）；K 類有序：線性權重 w_ij = |i−j|/(K−1)，二次權重 w_ij = (i−j)²/(K−1)²。3 類時，相差一級在線性權重下罰 0.5、二次權重下罰 0.25，相差兩級皆罰 1。二次加權 κ 在大樣本下與 ICC 近似等價（Fleiss & Cohen 1973，未於本次開啟）。
  - Fleiss' κ（≥3 位評分者、每項目評分者人數固定）：κ = (P̄ − P̄_e)/(1 − P̄_e)，P_i = (Σ_j n_ij² − k)/(k(k−1))，P̄_e = Σ_j p_j²。
  - Gwet's AC1：AC1 = (p_o − p_e^γ)/(1 − p_e^γ)，p_e^γ = (1/(K−1)) Σ_j π_j(1−π_j)。
  - Krippendorff's α = 1 − D_o/D_e，可用 nominal/ordinal/interval 距離，允許缺值、任意評分者數。
- **Kappa 悖論**：Feinstein & Cicchetti（1990）指出（1）邊際分布失衡時，觀察一致率高但 κ 偏低；（2）不對稱失衡比對稱失衡得到較高 κ。 — [Zec et al. 2017 "High Agreement and High Prevalence: The Paradox of Cohen's Kappa", PMC5712640](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5712640/) [C]（僅檢索摘要）
- Wongpakaran 等（BMC Med Res Methodol 2013;13:61）在 67 位病人人格障礙診斷比較：Cohen's κ 範圍 0–1.000（平均 0.821 ± 0.299），Gwet's AC1 範圍 0.752–1.000（平均 0.953 ± 0.071）；AC1 隨盛行率變動較少、接近百分比一致率。另有學者（Vach 2005）主張 κ 對盛行率的依賴不是問題——此點存在爭議。 — [Wongpakaran et al. 2013](https://bmcmedresmethodol.biomedcentral.com/track/pdf/10.1186/1471-2288-13-61) [C]；爭議見 [FCSM 2013 Xie review](https://www.fcsm.gov/assets/files/docs/J4_Xie_2013FCSM.pdf) [E]（皆僅檢索摘要）
- McHugh（Biochem Med 2012;22(3):276–282）詮釋表：0–0.20 none；0.21–0.39 minimal；0.40–0.59 weak；0.60–0.79 moderate；0.80–0.90 strong；>0.90 almost perfect；並主張健康研究中 **κ < 0.60 即屬一致性不足**，批評傳統分級「讓很少的一致也被描述為 substantial」；最佳建議是**同時計算百分比一致率與 κ**。 — [McHugh 2012, PMC3900052](https://pmc.ncbi.nlm.nih.gov/articles/PMC3900052/) [C]（全文已開啟）
- Landis & Koch（1977）分級（<0 poor；0–0.20 slight；0.21–0.40 fair；0.41–0.60 moderate；0.61–0.80 substantial；0.81–1.00 almost perfect）為業界慣例引用，但屬作者主觀提出、非實證導出（標準知識，本次未開啟原文；McHugh 的批評見上）。
- ICC（Koo & Li 2016, J Chiropr Med 15(2):155–163, DOI 10.1016/j.jcm.2016.02.012）：依 McGraw & Wong 有 10 種形式，必須明確報告 model（one-way random / two-way random / two-way mixed）、type（single / mean of k）、definition（absolute agreement / consistency）。評分者為隨機樣本且欲推論到同類評分者 → two-way random；**test-retest 與 intra-rater 研究建議 two-way mixed、absolute agreement**。詮釋以 **95% CI** 落點：<0.5 poor、0.5–0.75 moderate、0.75–0.9 good、>0.90 excellent；CI 跨帶則報告區間（如 "moderate to good"）。樣本建議**至少 30 個異質樣本、至少 3 位評分者**。 — [Koo & Li 2016, PMC4913118](https://pmc.ncbi.nlm.nih.gov/articles/PMC4913118/) [C]（全文已開啟）
- GRRAS（Kottner et al., J Clin Epidemiol 2011;64(1):96–106, DOI 10.1016/j.jclinepi.2010.03.002）：8 位專家提出 15 項報告要點，涵蓋在標題/摘要註明 inter/intra-rater 研究、受試/項目母體、評分者母體、抽樣方法、評分流程（獨立、盲化）、統計方法與不確定性（CI）等。（同文亦刊於 Int J Nurs Stud 2011;48:661–671。） — [Manchester 研究紀錄](https://research.manchester.ac.uk/en/publications/guidelines-for-reporting-reliability-and-agreement-studies-grras-/) [A]；[McMaster 紀錄](https://experts.mcmaster.ca/scholarly-works/72596) [A]（僅檢索書目/摘要）

**A3. 樣本數**
- Bujang & Baharum（Epidemiol Biostat Public Health 2017;14(2)）以 Flack 等（1988）公式、PASS 軟體、power ≥80%、α<0.05：邊際分布相等時最小樣本數依效果量介於 2–698；若邊際分布不等，多數情境所需樣本「超過兩倍」，建議規劃時以等邊際估算後**乘以 2**。 — [Bujang & Baharum 2017](https://riviste.unimi.it/index.php/ebph/article/view/17614) [C]（僅摘要；PDF 下載後文字層無法解析，表格數值未取得）
- R 套件 kappaSize：`PowerBinary / Power3Cats / Power4Cats / Power5Cats(kappa0, kappa1, props, raters=2..6, alpha=0.05, power=0.80)`，檢定 H0: κ=κ0 vs H1: κ=κ1（雙尾）；另有 `CIBinary/CI3Cats...` 依 CI 寬度估樣本；參考 Rotondi & Donner 2012（J Clin Epidemiol 65:778–784）、Donner & Rotondi 2010、Donner & Eliasziw 1987（Stat Med 6:441–448）。範例 `Power3Cats(kappa0=0.4, kappa1=0.6, props=c(0.30,0.60,0.10))`（頁面未給輸出）。最新版 1.2（2018-11-26）。 — [kappaSize Power3Cats 文件](https://search.r-project.org/CRAN/refmans/kappaSize/html/power3Cats.html) [E]（頁面已開啟）；[PowerBinary 文件](https://search.r-project.org/CRAN/refmans/kappaSize/html/powerBinary.html) [E]（僅檢索摘要）
- Walter, Eliasziw & Donner（Stat Med 1998;17(1):101–110）提出 ICC 研究所需受試數的方法，並指出當信度約 ≥0.40 時，每受試 2–3 次觀察可使總觀察數最少。 — [McMaster 紀錄](https://experts.mcmaster.ca/scholarly-works/1522974) [C]（僅摘要）

**A4. Python／R 工具（業界慣例 [E]，依本人工具知識，未於本次開啟文件頁）**
- `sklearn.metrics.cohen_kappa_score(y1, y2, weights=None|'linear'|'quadratic')`（本機 venv 已有 scikit-learn 1.9.1）。
- `statsmodels.stats.inter_rater`：`cohens_kappa`（含 SE/CI）、`fleiss_kappa`、`aggregate_raters`（本機 venv 未安裝 statsmodels）。
- `pingouin.intraclass_corr(data, targets, raters, ratings)` 回傳 ICC1/ICC2/ICC3/ICC1k/ICC2k/ICC3k 與 CI。
- `krippendorff.alpha(reliability_data, level_of_measurement='nominal'|'ordinal'|'interval')`。
- R：`irr`（kappa2、kappam.fleiss、icc、kripp.alpha）、`irrCAC`（Gwet AC1/AC2）、`kappaSize`。

### Inferences

**A-I1. 指標選擇（本報告推論）**
- 分期三類有序 → 主指標：2 位評分者用**二次加權 κ**（若重視「差一級」也算部分一致）並並列**線性加權 κ**；≥3 位用 **Krippendorff's α（ordinal）**或 Fleiss' κ（名目）。輔助：原始一致率 p_o、**Gwet's AC1/AC2**（因專案 normal 僅 9/56 ≈ 16%，邊際失衡易出現 kappa 悖論）、類別別一致率（positive/negative agreement）、混淆矩陣。
- 二元衍生問題（「是否靜脈炎」）：Cohen's κ + AC1 + PABAK 並列。
- 若有連續量測（紅斑長度 cm）→ ICC(2,1) two-way random, absolute agreement（評分者為護理師母體的隨機樣本）＋ Bland–Altman 一致界限；intra-rater test–retest → ICC(3,1) two-way mixed, absolute agreement（Koo & Li 建議）。
- 門檻（研究原型）：以 McHugh 的 κ ≥ 0.60 為「可接受」最低線，**以 95% CI 下限判定**而非點估計；κ_w ≥ 0.80 為「可直接作為訓練真值」目標（本報告推論，非文獻共識門檻）。

**A-I2. 樣本數：假設檢定法（本報告推論，模擬計算）**
- 方法：exchangeable「kappa 模型」——每張照片以機率 ρ 所有評分者給相同類別（由盛行率 p 抽出），否則各自獨立由 p 抽出；此時成對 Cohen κ = Fleiss κ = ρ。以 4,000 次模擬估計 κ̂ 每單位標準差 σ0（在 κ0 下）與 σ1（在 κ1 下），n = [(z_{1−α/s}·σ0 + z_{1−β}·σ1)/(κ1 − κ0)]²，s=1 或 2（單/雙尾）；再以 1,500 次模擬驗證實際 power（多為 0.77–0.82，故**建議再加 10%**）。限制：未加權 κ、假設兩評分者邊際相同（無偏差）；有偏差或二次加權時數值會不同。
- 結果（α=0.05、power=0.80；n = 照片數，假設照片間獨立）：

| 情境（盛行率） | κ0→κ1 | 2 評分者 單尾/雙尾 | 3 評分者 單尾/雙尾 |
|---|---|---|---|
| 3 類均等 (1/3) | 0.4→0.7 | 32 / 43 | 22 / 28 |
| 3 類專案比例 (0.16/0.41/0.43) | 0.4→0.7 | 36 / 46 | 23 / 31 |
| 3 類均等 | 0.6→0.8 | 57 / 75 | 41 / 53 |
| 3 類專案比例 | 0.6→0.8 | 62 / 84 | 44 / 59 |
| 二元 33% 陽性 | 0.4→0.7 | 56 / 72 | 33 / 42 |
| 二元 16%（normal vs phlebitis） | 0.4→0.7 | 91 / 118 | 62 / 83 |
| 二元 16% | 0.6→0.8 | 158 / 213 | 112 / 147 |
| 3 類專案比例 | 0.0→0.6 | 10 / 12 | 4–5（小樣本漸近法失準，實測 power 僅 0.63–0.71，不建議引用） |

- 觀察：（1）3 類比二元省樣本；（2）盛行率越失衡所需越多（與 Bujang & Baharum「邊際不等需約 2 倍」方向一致）；（3）第 3 位評分者可減約 30% 照片數；（4）檢定 κ0=0（「優於隨機」）幾乎沒有資訊量，**應以 κ0=0.4 或 0.6 作為 H0**。

**A-I3. 樣本數：CI 寬度法（本報告推論）**
- 公式（Cohen 1960 大樣本近似）：SE(κ̂) ≈ √[p_o(1−p_o)/(n(1−p_e)²)] → n = z²·p_o(1−p_o)/[w²(1−p_e)²]，p_o = κ(1−p_e)+p_e，w 為 95% CI 半寬。模擬交叉驗證差異 ≤2。
- 3 類專案比例（p_e = 0.378），預期 κ=0.7：半寬 ±0.10 → **151**；±0.15 → **68**；±0.20 → **38**。預期 κ=0.8：±0.10 → 109；±0.15 → 49；±0.20 → 28。3 類均等（p_e=1/3）κ=0.7：139 / 62 / 35。
- 意義：以目前 56 張分期照片，雙評分者 κ≈0.7 的 95% CI 約 ±0.16–0.17，只能區分「moderate 以上」與否，無法精確定位。

**A-I4. 病人群聚校正（本報告推論）**
- Design effect DE = 1 + (m − 1)·ICC_cluster；m = 120/14 ≈ 8.57。ICC_cluster=0.05 → DE 1.38（120 張有效 ≈ 87）；0.1 → 1.76（≈68）；0.2 → 2.51（≈48）；0.3 → 3.27（≈37）；0.5 → 4.79（≈25）。同一病人左右手、連續日期照片的「難度/一致性」高度相關，ICC_cluster 0.2–0.3 並不意外 → 現有 120 張在一致性研究中可能只相當於 37–48 張獨立照片。
- 對策：一致性子集**每位病人限取 2–3 張**（m=2, ICC 0.3 → DE 1.30；m=3 → DE 1.60），所需照片 = n_indep × DE。例：3 類專案比例、κ0=0.4→0.7、2 評分者雙尾 n=46，m=3、ICC 0.3 → 46×1.6 ≈ **74 張（約 25 位病人）**——超過現有 14 位病人，現階段只能以 m 較大但報告 cluster bootstrap CI（以病人為重抽單位）處理；未來 1,000 張資料再做正式研究。
- 分析時 CI 應以**病人層級 cluster bootstrap**（重抽病人而非照片）計算 κ 的 CI（業界慣例/本報告推論）。

**A-I5. 評分者內（test–retest）設計（本報告推論＋業界慣例）**
- 同一評分者間隔 **≥2–4 週**重評（washout，降低記憶效應；具體天數無本次可引用的實證門檻），照片**隨機重排**、**移除檔名/日期/EXIF 與先前標籤**（在 App 中以匿名 ID 顯示、隱藏 E-Da 檔名推導標籤與模型建議）、相同顯示條件。
- 統計：分期用加權 κ（intra），連續量測用 ICC(3,1) absolute agreement（Koo & Li）。樣本同 A-I2/A-I3。
- 以 GRRAS 15 項為報告骨架；Koo & Li 的 ICC 報告格式（軟體、model/type/definition、ICC+95% CI）。

**A-I6. 評分者人數與裁決流程（本報告推論）**
- 建議：2–3 位受訓護理師獨立盲評（含原單一標註者）＋ 1 位皮膚科/感染科醫師作為裁決者（adjudicator）。流程：①校準訓練（10–15 張不計分照片＋圖示定義表，依 INS/VIP 等分期定義，由臨床基礎組另行提供）→ ②獨立盲評 → ③一致者直接定案；不一致者由裁決者在不知誰標什麼的情況下判定（或 2/3 多數決＋裁決者僅處理三方皆不同者）→ ④記錄裁決理由，回饋更新標註指引 → ⑤報告「裁決前」一致性（真正的信度）與「裁決後」標籤分布。
- Delphi 適用於建立**指引/定義**（多輪匿名回饋至共識），不適合逐張照片；逐張用 majority vote + adjudication；分割遮罩用 STAPLE（Karimi 回顧中 STAPLE/多數決優於單一標註者）。
- App 對應：SQLite 新增 `annotation`（photo_id, rater_id, round, label, box, timestamp, blinded=1）表，一張照片多筆標註、不覆寫；`consensus_label` 另表並記錄來源（auto-filename / single / adjudicated）。模型建議標籤在一致性研究期間必須隱藏，以免錨定效應（anchoring）。

### Gaps
- Sim & Wright 2005 與 Bujang & Baharum 2017 的**具體表格數值**未能取得（期刊 PDF 無可解析文字層），因此 A-I2 數值為本報告模擬，未與其表交叉核對；建議撰寫者以 R `kappaSize::Power3Cats(0.4, 0.7, c(.16,.41,.43), raters=2)` 交叉驗證（本機無 R）。
- Donner & Eliasziw 1992 goodness-of-fit 公式、Cantor 1996、Shoukri 的書本內容本次未開啟。
- 未找到靜脈炎照片分期（或 INS/VIP 量表以照片評估）的評分者間一致性已發表數據——需由臨床基礎組另查。
- Washout 2–4 週無本次可引用的實證依據，屬慣例。
- CLAIM 2024 標註相關條目本次未開啟（未取得條目編號與原文）。

---

## B. 檔名規則推導標籤的稽核抽樣設計

### Takeaway
檔名規則標籤（E-Da）應視為「未驗證的自動標籤」，以隨機（建議依類別×來源×病人分層）抽樣人工覆核估計錯誤率。若目標是證明錯誤率 ≤5%：在**零錯誤**條件下，二項近似需 59 張（rule of three ≈ 3/n），有限母體 N=120 只需 **41 張**、N=1,000 需 **56 張**；若要估計錯誤率 ±5%（預期 p≈5%），N=120 需 46 張、N=1,000 需 69 張；保守 p=50% 時 N=1,000 需 278 張。所有結果應以 Wilson 或 Clopper–Pearson CI 報告，並考慮病人群聚的 design effect（本報告推論）。

### Cited Findings
- Karimi 等指出由 PACS/規則自動產生的標籤預期比專家標註更嘈雜，且「計算機系統產生的標籤明顯不如人類專家準確」——支持對規則標籤進行抽樣稽核。 — [Karimi et al. 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7484266/) [B]
- Northcutt 等以「信心學習＋人工確認」找出錯誤，顯示即使廣泛使用的資料集也有 ≥3.3% 測試集錯誤，錯誤率須以人工驗證樣本估計。 — [Northcutt et al. 2021](https://arxiv.org/abs/2103.14749) [B]
- ISO 2859-1（依屬性抽樣檢驗程序，現行 1999 版）以批量（lot size）與檢驗水準（一般 I/II/III、特殊 S-1~S-4）決定樣本字碼，再由 Table II-A 依 AQL 取 n 與允收數 Ac/拒收數 Re；一般水準 II 為預設。例：批量 5,000 件時一般水準 I/II/III 樣本 80/200/315；40,000 件時 200/500/800。 — [qualityinspection.org](https://qualityinspection.org/inspection-level/) [E]（頁面已開啟；表格為圖片）；標準目錄 [ISO 2859-1:1999 (iTeh)](https://iteh.es/catalog/standards/iso/15ffc59c-9f33-46dc-8518-f4163282a638/iso-2859-1-1999) [A]（僅檢索結果）
- 公式（標準統計公式，未於本次核對原文）：
  - 估計比例樣本數 n0 = z²·p(1−p)/d²；有限母體校正 n = n0 / [1 + (n0 − 1)/N]。
  - Wilson score CI：[p̂ + z²/2n ± z√(p̂(1−p̂)/n + z²/4n²)] / (1 + z²/n)。
  - Clopper–Pearson（exact）：下限 Beta(α/2; x, n−x+1)，上限 Beta(1−α/2; x+1, n−x)。
  - 零錯誤 rule of three：觀察 0/n 時 95% 單尾上限 ≈ 3/n（精確解 1 − 0.05^{1/n}）。
  - 有限母體零錯誤：選最小 n 使 Hypergeom(0; N, D, n) ≤ 0.05，D = ⌊p_u·N⌋+1。
  - 群聚：n_cluster = n × DE，DE = 1 + (m − 1)·ICC。

### Inferences

**B-I1. 估計錯誤率所需樣本（本報告推論，計算）**（95% 信心；FPC 後取整）

| 母體 N | p=0.05, ±5% | p=0.05, ±10% | p=0.10, ±5% | p=0.10, ±10% | p=0.5（保守）, ±5% | p=0.5, ±10% |
|---|---|---|---|---|---|---|
| 60（如 E-Da 子集） | 34 | 15 | 43 | 23 | 53 | 38 |
| 120 | 46 | 16 | 65 | 28 | 92 | 54 |
| 500 | 64 | 18 | 109 | 33 | 218 | 81 |
| 1,000 | 69 | 18 | 122 | 34 | 278 | 88 |

- 注意：p=5%、d=±5% 的常態近似在小 p 下不對稱且下界會 <0，報告應用 Wilson/CP 而非 p̂ ± d。

**B-I2. 「錯誤率是否 ≤ X%」——零失敗驗收（本報告推論，計算）**
- 二項（無限母體）：要 0 錯誤時 95% 上限 ≤5% → n=59（rule of three 給 60）；≤10% → 29；≤3% → 99。
- 有限母體（超幾何，0 錯誤、95% 信心）：

| N | 證明 ≤5% | 證明 ≤10% |
|---|---|---|
| 60 | 31 | 20 |
| 120 | 41 | 24 |
| 500 | 54 | 28 |
| 1,000 | 56 | 28 |

- 已知結果的 CI 範例：0/30 → Wilson 上限 11.4%（CP 11.6%）；0/59 → 6.1%；1/50 → [0.4%, 10.5%]（CP [0.1%, 10.6%]）；2/60 → [0.9%, 11.4%]；3/60 → [1.7%, 13.7%]（CP [1.0%, 13.9%]）；5/100 → [2.2%, 11.2%]；0/120（全查）→ 上限 3.1%（CP 3.0%）。有限母體 N=120、抽 60 張 0 錯 → 95% 上限 4 張（3.3%）；抽 60 張 1 錯 → 7 張（5.8%）；抽 40 張 0 錯 → 7 張（5.8%）。
- 實務結論：**N ≈ 120 時，全面覆核（census）只多花約 60–80 張的工作量，且直接得到真實錯誤數**，比抽樣更合理；抽樣設計主要用於未來 ~1,000 張資料（本報告推論）。

**B-I3. LQAS／單次抽樣計畫（本報告推論，二項計算，非 ISO 表值）**
- 找最小 (n, c) 使 P(允收 | p0=AQL) ≥ 1−α 且 P(允收 | p1=LTPD) ≤ β：
  - AQL 1%、LTPD 10%、α 0.05、β 0.10 → **n=52, c=2**（錯誤 ≤2 張則允收）。
  - AQL 2%、LTPD 10%、α 0.05、β 0.10 → **n=65, c=3**。
  - AQL 1%、LTPD 5%、α 0.05、β 0.10 → **n=132, c=3**。
  - AQL 5%、LTPD 15%、α 0.05、β 0.10 → n=77, c=7。
- 建議用法：每次新批次匯入（例如每 100–200 張 E-Da 照片）跑一次 n=52/c=2 計畫；拒收（≥3 錯）→ 全批人工覆核並修正檔名規則。ISO 2859-1 為製造業連續批設計，對少量批次的小型資料集，直接以上述 OC 曲線計算的 LQAS 更透明（本報告推論）。

**B-I4. 分層與群聚（本報告推論）**
- 分層：類別（normal/1/2）× 來源（E-Da 檔名規則 / LINE 人工）×（可選）日期或規則版本。規則錯誤通常集中於特定檔名樣式（例如 LH/RH/LL/RL 側別、日期格式、分期碼位置），應**依檔名樣式（regex 分支）分層**，每層至少 10–15 張或全查小層。
- 例：未來 N=1,000、6 層（3 類×2 來源，各約 167），保守 n=278 → 比例分配每層約 46 張；若只稽核 E-Da 三層（N≈500）、p 預期 5%、±5% → 64 張，每層約 21–22 張。
- 群聚：同病人照片的檔名錯誤高度相關（同一病人整批錯側別）。若每病人 m=8.6 張、ICC 0.2 → DE 2.51，需樣本放大 2.5 倍；**建議以病人為第一階段抽樣單位（cluster sampling），每病人抽 2–3 張**，DE 降到 1.1–1.6。
- 稽核欄位：photo_id、規則版本、原檔名、規則推導標籤（分期/側別/日期）、覆核者標籤、錯誤類型（分期錯／側別錯／日期錯／非病灶照片）、覆核者、時間。覆核時應**遮蔽檔名推導的標籤**（避免確認偏誤），覆核後再比對。

### Gaps
- ISO 2859-1 Table I（批量→字碼）與 Table II-A 數值本次未能從公開來源以文字取得（網頁為圖片、標準本身付費），故未列字碼對照；如需引用 ISO 表值，須取得原標準。
- 未找到專門針對「醫學影像檔名/中繼資料自動標籤錯誤率」的已發表稽核研究。

---

## C. 病灶框（bounding box）標註規範與一致性量測

### Takeaway
公開醫學偵測資料集（如 DFUC 2020）多採「一病灶一框、由兩位專科臨床人員標註、不一致時共同協議」，對遮擋物（時間戳）採「盡量涵蓋病灶、排除遮擋物」；但很少公開報告框的 inter-annotator IoU。框一致性建議以**匈牙利演算法配對後的每框 IoU（中位數/IQR）、IoU ≥0.5 比例、未配對框（漏標/多標）率**，以及「以 A 為真值評 B 的 mAP@0.5」對稱報告。靜脈炎的紅斑邊界模糊、沿靜脈呈條狀，box 對細長斜向病灶的 IoU 極不穩定，建議同時或改用**多邊形遮罩（Dice）＋關鍵點（穿刺點、索狀物兩端）＋以比例尺換算的長度（cm）**（本報告推論）。

### Cited Findings
- DFUC 2020（Cassidy 等）：以 LabelImg 與 VGG Image Annotator 標註；真值由**兩位糖尿病足專科臨床人員**標註，每個潰瘍一框；兩人不一致時，最終標籤由兩人共同協議決定（非量化一致性指標）；遇時間戳遮擋傷口時，框盡量包含傷口並排除時間戳。 — [DFUC2020 arXiv:2004.11853](https://arxiv.org/pdf/2004.11853) [D]（僅檢索摘要）
- 2022 年 DFU 資料集綜述指出完整的 inter- 與 intra-rater 分析將是提升資料集品質的關鍵——顯示當時仍缺。 — [Development of DFU Datasets: An Overview, arXiv:2201.00163](https://arxiv.org/pdf/2201.00163) [D]（僅檢索摘要）
- VinDr-CXR：訓練集每張影像 3 位放射科醫師標註、測試集 5 位共識，每個異常以矩形框標註；一篇研究報告 3 位個別標註者在 VinDr-CXR 上的 mAP@0.4 分別為 0.121、0.132、0.124（baseline 0.148），反映框層級分歧大。 — [arXiv:2506.13049](https://arxiv.org/pdf/2506.13049) [D]；[arXiv:2303.16507](https://www.arxiv.org/pdf/2303.16507) [D]（皆僅檢索摘要）
- Chest ImaGenome：框由「規則式 NLP＋atlas-based 偵測流程」**自動產生**，另有 500 位病人的人工金標準場景圖。檢索摘要稱人工雙標的 mean IoU > 0.96 且以兩人座標平均作金標準框，但本次開啟的摘要頁未出現此數字，未能核實。 — [Chest ImaGenome arXiv:2108.00316](https://arxiv.org/abs/2108.00316) [D]（摘要頁已開啟）
- 有研究指出人類驗證框時偏寬鬆，IoU < 0.5 的框仍常被接受，固定 IoU 門檻未必符合人類對定位品質的判斷。 — [TU Delft repository](https://repository.tudelft.nl/file/File_c8a6370f-0a12-4db7-8a6f-0c0ff8375331?preview=1) [D]；相關：[Humans disagree with the IoU, arXiv:2207.14221](https://arxiv.org/pdf/2207.14221) [D]（皆僅檢索摘要）
- 非醫學雙標資料：臉部框 mean IoU 約 0.89，手部（小而形變）約 0.66–0.69——小或細長目標的微小偏移會大幅降低 IoU。 — [ChildGaze arXiv:2609.06353](https://arxiv.org/pdf/2609.06353) [D]（僅檢索摘要；非醫學，僅作量級參考）
- 皮膚病灶分割：兩位專科醫師分割一致性 Dice 93.67%；並指出某些用途近似框即足夠。 — [Handling Inter-Annotator Agreement for Automated Skin Lesion Segmentation, arXiv:1906.02415](https://arxiv.org/pdf/1906.02415) [D]（僅檢索摘要）
- 多標註者框資料可用 Krippendorff's α 的框版本（解對應問題後計算 α，KαLOS），作者認為單純 IoU 配對可能錯失真對應。 — 出現在同一檢索結果中，但未能確認對應網址，列為待查（見 Gaps）。
- STAPLE（Warfield 等）與多數決為分割多標註聚合常用法，在 Karimi 回顧實驗中優於單一標註者。 — [Karimi et al. 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7484266/) [B]
- 公式（標準公式，未於本次核對原文）：IoU(A,B) = |A∩B|/|A∪B|；Dice = 2|A∩B|/(|A|+|B|) = 2·IoU/(1+IoU)（例：IoU 0.5 ↔ Dice 0.667；IoU 0.7 ↔ Dice 0.824）。配對：建立成本矩陣 C_ij = 1 − IoU(a_i, b_j)，以匈牙利演算法（`scipy.optimize.linear_sum_assignment`）求最佳一對一配對，IoU < τ（如 0.1 或 0.3）的配對視為未配對。

### Inferences

**C-I1. 靜脈炎病灶框標註規範草案（本報告推論＋業界慣例）**
1. **框什麼**：框住「可見紅斑的外緣」（erythema extent）為主框（class: `phlebitis_lesion`）；若有可見/可觸索狀物（palpable cord）或條紋（streak），另以**折線或兩端關鍵點**標示，不另以框代替。穿刺點以關鍵點 `insertion_site` 標示。理由：分期（如 VIP/INS 量表）依賴紅、腫、痛、索狀物長度等多項特徵，框只能承載位置。
2. **緊或鬆**：tight box——框邊貼紅斑最外側可見邊界，**不刻意外擴 margin**；邊界模糊時以「與周邊正常膚色可分辨的最外點」為準。業界慣例（COCO 類）為 tight box。
3. **多病灶**：彼此分離（間隔 > 約 1 個病灶寬或有明顯正常皮膚隔開）→ 各自一框；沿同一靜脈連續的紅斑 → 一框。
4. **遮擋**：敷料/膠帶/留置針遮擋時，只框**可見**部分（不推測被遮部分），並勾選屬性 `occluded=true`；仿 DFUC 對時間戳「盡量含病灶、排除遮擋物」的做法。整片被遮 → 不框，影像標記 `not_assessable`。
5. **正常照片**：不框；影像層級標 `no_lesion`（明確區分「無病灶」與「未標註」，SQLite 中以 NULL vs 空集合區別）。
6. **框與分期分離**：框目前無分期；建議框層級加 `stage` 欄位（可空）以便未來偵測＋分級；影像層分期取最高者。
7. **模型建議框**：顯示為虛線、預設未確認；人員必須接受/修改/刪除才寫入；記錄 `source=model_suggested|human` 與修改前後座標（可計算模型建議 vs 人工的 IoU 作為監控指標）。
8. 品質控制：校準集 10–15 張附「正確框」示例圖（含模糊邊界、多病灶、遮擋、斜向細長紅斑），每位標註者通過（mean IoU ≥ 0.6 對裁決者）後才正式標註（門檻為本報告推論）。

**C-I2. 框一致性量測方案（本報告推論）**
- 流程：兩位標註者獨立標同一批照片（建議 ≥30 張含病灶照片，Koo & Li 的 ≥30 異質樣本原則；以每病人 ≤2–3 張分散群聚）→ 每張以匈牙利配對 → 報告：
  1. 影像層級「有/無病灶」一致性：κ／AC1。
  2. 框數一致：配對框數、A 獨有、B 獨有（漏標率 = 未配對/總框）。
  3. 配對框 IoU：中位數＋IQR（分布偏斜，勿只報平均）、% IoU ≥0.5、% IoU ≥0.75；cluster bootstrap 95% CI。
  4. 偵測式指標：以 A 為真值算 B 的 AP@0.5，再反過來，取平均（對稱化）；此值可視為模型 mAP 的「人類上限」參考——若人類彼此 AP@0.5 只有 0.6，模型 0.6 已接近天花板。
  5. 中心點距離／框寬高相對誤差（對細長病灶比 IoU 更穩健）。
- 判讀（業界慣例，非醫學實證門檻）：IoU ≥0.5 為 PASCAL/COCO 的偵測正確門檻；文獻中雙標 IoU 量級從約 0.66（小、形變目標）到 >0.84–0.96（結構清楚目標）不等；邊界模糊的紅斑可能落在較低端，故**模型評估宜同時報 AP@0.3 與 AP@0.5**。
- 斜向細長病灶問題：沿前臂 45° 的條狀紅斑，axis-aligned box 大部分是正常皮膚，小的角度/端點差就讓 IoU 大跌 → 是改用 polygon 或 oriented box 的主要理由。

**C-I3. 何時改用分割、關鍵點或量測（本報告推論）**
- **分割（polygon/mask）**：當需要面積、紅斑範圍隨時間變化、或病灶細長斜向時；一致性用 Dice/IoU（每張）、Hausdorff 95；多標註聚合用 STAPLE 或多數決。標註成本約為框的數倍（未取得可引用量化數據）。
- **關鍵點**：穿刺點、索狀物兩端點、紅斑最遠端點——可直接計算長度，且一致性以點距離（mm）＋ICC 衡量，比框更貼近臨床分期條件（如索狀物長度）。
- **量測（cm）**：需在拍攝時放置比例尺/尺標貼紙（或已知尺寸的留置針翼），以像素→cm 換算；一致性用 ICC(2,1) absolute agreement＋Bland–Altman。若無比例尺，LINE 照片的長度不可比較，只能用相對量。
- 建議階段：現階段（24 張有框）先維持 box＋補 `insertion_site` 關鍵點；未來 1,000 張時，在 10–20% 子集加做 polygon 以評估 box 是否足夠。

### Gaps
- 未找到靜脈炎、壓傷（pressure injury）YOLO 資料集或 DFUC 公開的**框層級 inter-annotator IoU 數值**；DFUC 只描述協議流程。
- VinDr-CXR 資料描述論文（Sci Data）中的框一致性數值、Chest ImaGenome 人工框 IoU >0.96 的原文出處，本次未能核實。
- KαLOS（框版 Krippendorff α）的確切論文網址未確認。
- ISIC 分割的跨標註者 Dice 分布、病理 box 一致性研究本次未開啟。
- 框 vs 分割的標註時間成本缺可引用數據。
