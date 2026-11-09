# 評估指標、病人層級（cluster）信賴區間與兩模型比較檢定：靜脈炎照片分類／分期／偵測專案

> 研究日期／所有來源存取日：2026-10-30。
> 來源分級：[A] 官方／法規／報告標準；[B] 系統性回顧、統合分析、頂尖期刊或會議（Nature Methods、JMLR、NeurIPS、Biometrics、Stat Med、Radiology、BMJ、CMAJ…）；[C] 其他同儕審查；[D] 預印本；[E] 部落格、文件、程式碼、論壇（僅作輔助）。
> 結論標記：**【研究證據】** = 有引用來源直接支持；**【業界慣例】** = 常見做法或軟體預設；**【推論】** = 本筆記依引用證據推導或自行計算。標為 "(computed)" 的數字是用本專案 venv（`02_主程式碼/.venv`，numpy/scipy）在 2026-10-30 算出的示範值，**不是**文獻數字。
> 專案前提：研究原型，不做臨床診斷。目前約 120 張照片，來自 14 位病人。二元任務 47 張陽性對 9 張正常；分期任務 normal 9、stage1 23、stage2 24；約 24 張照片有框；單一標註者。目前評估方式：StratifiedGroupKFold（3 折，以病人分組），可另留約 20% 病人做 held-out（約 14–18 張照片）。臨床立場：漏判（FN）比誤報（FP）嚴重。
> 驗證說明：DOI 有在本次搜尋中看到的才列出；只有書目、沒有核對 DOI 的會標 "DOI not verified this session"。

---

## Q1. Sensitivity/specificity/PPV/NPV 與盛行率：Bayes 轉換、為何 case-enriched 樣本的 PPV/NPV 必須在目標盛行率下重算、靜脈炎發生率範圍

### Takeaway
Sensitivity（Se）與 specificity（Sp）在概念上與盛行率無關。實際上它們會隨病例組成（spectrum）與盛行率而變動：統合研究發現，Se/Sp 在不同盛行率之間可能差 0–40 個百分點。PPV/NPV 則直接取決於盛行率。本資料集照片層級的陽性比例是 47/56 ≈ 84%，遠高於文獻中的靜脈炎發生率（約 4.5%–41%，依定義與族群而異）。所以 PPV/NPV 一律要用 Bayes 公式換算到「目標盛行率情境」（建議至少 3 個情境，例如 5%、20%、31%）再報告，不可直接報樣本內數值。

### Cited Findings
- **Bayes 換算公式與「不可跨族群套用」**：Altman & Bland 指出，sensitivity/specificity 本身不能告訴臨床人員結果正確的機率，所以需要 predictive values；而 predictive values 強烈依賴受測者中疾病的盛行率。疾病越罕見，陰性結果越可信，陽性結果越不可信。Altman DG, Bland JM. *Statistics Notes: Diagnostic tests 2: predictive values.* BMJ 1994;309(6947):102. doi:10.1136/bmj.309.6947.102. [A/B] — [BMJ](https://www.bmj.com/content/309/6947/102.1.long)；[PMC2540558](https://pmc.ncbi.nlm.nih.gov/articles/PMC2540558)
  - 標準公式（教科書公式，與上文一致）：PPV = Se·π / [Se·π + (1−Sp)(1−π)]；NPV = Sp(1−π) / [Sp(1−π) + (1−Se)π]；π 為目標盛行率。
- **Se/Sp 本身也隨盛行率變動**：Leeflang, Rutjes, Reitsma, Hooft, Bossuyt. *Variation of a test's sensitivity and specificity with disease prevalence.* CMAJ 2013;185(11):E537–E544. doi:10.1503/cmaj.121286. [B]。資料為 23 篇統合分析、共 416 篇研究，各 review 的盛行率中位數從 1% 到 77%。有 8 篇（35%）中，盛行率對 Se 或 Sp 有顯著效應（p<0.05）。整體而言盛行率越高 Sp 越低，Se 沒有一致方向。同一 review 內盛行率從最低到最高，Se 或 Sp 變動 0–40 個百分點。作者認為病例組成（spectrum）等機制可能同時造成盛行率差異與準確度變化。— [BORIS (Univ. Bern)](https://boris.unibe.ch/41072/)；[CMAJ related content](https://www.cmaj.ca/content/early/2013/06/24/cmaj.121286/tab-related-content)
  - 後續研究：CMAJ 2023 涵蓋 6,909 篇研究（doi:10.1503/cmaj.221802），發現盛行率與 Se 正相關、與 Sp 負相關。[B] — [CMAJ 2023 (PMC10356012)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10356012)
- **靜脈炎發生率（作為 PPV/NPV 換算的合理盛行率）**：
  - Lv L, Zhang J. *The incidence and risk of infusion phlebitis with peripheral intravenous catheters: A meta-analysis.* J Vasc Access 2020;21(3):342–349（2019 年 9 月先行上線），DOI 據次級來源為 10.1177/1129729819877323（未在出版社頁面核對）。[B]。合併發生率為每 100 條導管 30.7 例（95% CI 27.2–34.2），嚴重靜脈炎 3.6%（95% CI 2.7–4.6）。風險因子包括較長留置時間、抗生素輸注、Teflon 導管。— [ivteam 摘要 [E]](https://ivteam.com/?p=68528)；[UTB catalogue record](https://vufind-test.katalog.k.utb.cz/SummonRecord/FETCH-LOGICAL-c337t-dec754c68dcfd3fdec7ef10a5c713282955fedb5749e125da760032881c5cc902)
  - Marsh N, Webster J, Ullman AJ, Mihala G, Cooke M, Chopra V, Rickard CM. *Peripheral intravenous catheter non-infectious complications in adults: A systematic review and meta-analysis.* J Adv Nurs 2020;76(12). doi:10.1111/jan.14565. [B]。納入 103 篇研究（70 篇觀察性、33 篇 RCT），共 76,977 條導管。**有定義的靜脈炎為 19.3%，未給定義者為 4.5%**；infiltration/extravasation 13.7%。注意：任務提到的「Marsh 2024」其實是另一篇，主題是 infection/failure（Int J Nurs Stud 2024;151:104673），不是靜脈炎發生率。— [Deep Blue (UMich)](https://deepblue.lib.umich.edu/items/7bd38d78-42ee-403e-b99d-67774e5e462c)；[ivteam [E]](https://ivteam.com/intravenous-literature/peripheral-iv-catheter-non-infectious-complications-in-adults/)；[zendy record](https://zendy.io/title/10.1111/jan.14565)
  - 衣索比亞統合分析（2024）：每 100 條導管 41 例（95% CI 22–60）。[B/C] — [Springer](https://link.springer.com/article/10.1007/s44337-024-00113-8)
- **臨床病例組成偏差（spectrum bias）在本專案的意義**：Genders 等的 Radiology 教學文指出，每位病人有多個觀察值時資料就是 clustered，而方法選擇與報告層級應「對應臨床決策問題」。— [Radiology 2012, doi:10.1148/radiol.12120509](https://pubs.rsna.org/doi/10.1148/radiol.12120509) [B]

### Inferences
- **示範（computed）**：本資料照片層級盛行率 π_sample = 47/56 = 0.839。若模型 Se=0.90、Sp=0.80：
  - π=0.045 → PPV 0.175、NPV 0.994
  - π=0.193 → PPV 0.518、NPV 0.971
  - π=0.307 → PPV 0.666、NPV 0.948
  - π=0.41 → PPV 0.758、NPV 0.920
  - π=0.839（樣本本身）→ PPV 0.959、NPV 0.605

  若 Se=0.95、Sp=0.70，π=0.193 時 PPV 只有 0.431。**結論【推論】**：樣本內的 PPV（約 0.96）在任何現實盛行率下都嚴重高估；樣本內的 NPV（約 0.6）則嚴重低估。因此報告應以 Se/Sp（以及正常照片的誤報率 = 1−Sp）為主，PPV/NPV 只用「情境表」呈現。
- 盛行率要分清楚計數單位：文獻多為「每導管」或「每病人」的發生率，模型則是「每張照片」判讀，兩者不同。換算時建議採用「每次評估事件」或「每導管」的情境，並在文中說明假設。【推論】
- 由於 Leeflang 2013 顯示 Sp 會隨病例組成改變，而本資料的正常照片只有 9 張且來自少數病人，Sp 的外推性非常有限。應在 limitations 中明確寫出，並指明未來 1,000 張資料要涵蓋「容易誤判的正常照片」（剛置針、瘀青、膠帶壓痕等）。【推論】
- PPV/NPV 的 CI 可以這樣算：在 cluster bootstrap 的每次重抽中，用重抽得到的 Se/Sp 加上固定 π 算 PPV/NPV，取百分位數。π 本身的不確定性另以情境呈現，不要混入 CI。【推論】

### Gaps
- 未找到台灣本地 PIVC 靜脈炎發生率的系統性回顧（未搜尋到可靠證據）。Lv & Zhang 的 DOI 與頁碼僅由次級來源取得，未在 SAGE 出版社頁面核對。
- 未找到針對「照片層級」靜脈炎盛行率的資料（每次護理評估有多少比例照片呈陽性）。未找到可靠證據。

---

## Q2. 門檻無關與單一數值指標：AUROC vs AUPRC、balanced accuracy、macro-F1、MCC、Cohen's kappa

### Takeaway
小型且類別不平衡的醫學影像分類，建議如下：
- 主指標用與盛行率無關的指標：二元任務在預先固定的操作點上報 Se、Sp（或 balanced accuracy）；門檻無關指標用 AUROC。
- AUPRC 依賴盛行率，而本樣本盛行率被人為放大，所以 AUPRC 不能外推；它也不是「不平衡時一定較好」，McDermott 等 2024 NeurIPS 已證明這點。
- F1 與 kappa 有明確缺陷。MCC 可作輔助；Metrics Reloaded 將 BA 與 MCC 並列為 EC 的替代選項。

### Cited Findings
- **Metrics Reloaded 對影像層級（多類別）分類的建議**（Maier-Hein L, Reinke A, et al. *Metrics reloaded: recommendations for image analysis validation.* Nature Methods 2024;21(2):195–212. doi:10.1038/s41592-023-02151-z）[B]：
  - 有決策規則時，以 Expected Cost（EC）為主；「Accuracy, Balanced Accuracy (BA) and MCC may be viable alternatives」。
  - 類別混淆的嚴重性不等時：「we generally recommend EC as metric」。
  - 指標選擇主要取決於驗證集各類別的盛行率，以及目標族群。
  - 多類別指標可能掩蓋個別類別的差表現，所以建議另報 one-vs-rest 的 per-class F-beta 類指標。
  - multi-threshold 指標預設用 AUROC，理由是它「prevalence-independent」；AP 則被描述為在某些平衡情況下可能較合適。
  - 若需要 calibration，另外加入 calibration 指標。
  - BA 與 EC 被列為可補償類別不平衡、與盛行率無關的選項；有成本效益決策規則時另推薦 Net Benefit。
  - 來源：[PMC11182665](https://pmc.ncbi.nlm.nih.gov/articles/PMC11182665/)；[WRAP record](https://wrap.warwick.ac.uk/183654)
- **AUPRC 支持論點**：Saito T, Rehmsmeier M. *The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets.* PLoS ONE 2015;10(3):e0118432. doi:10.1371/journal.pone.0118432. [C]。在不平衡資料上，ROC 圖的視覺解讀可能誤導；PR 圖能較準確地預測未來的分類表現。情境是負例遠多於正例的生物資訊應用。— [PMC4349800](https://pmc.ncbi.nlm.nih.gov/articles/PMC4349800)
- **AUPRC 反方論點**：McDermott M, Zhang H, Hansen LH, Angelotti G, Gallifant J. *A Closer Look at AUROC and AUPRC under Class Imbalance.* NeurIPS 2024. doi:10.52202/079017-1400；arXiv:2401.06091. [B]。理論分析顯示，AUPRC 在類別不平衡時「並非一般性地優於」AUROC，而且可能放大子族群間的演算法偏差。選擇依據應是模型的目標使用情境，而非不平衡本身。— [arXiv](https://arxiv.org/abs/2401.06091v4)；[NeurIPS poster](https://neurips.cc/virtual/2024/poster/95133)
- **F1 與 accuracy 的缺陷、MCC 的優點**：Chicco D, Jurman G. *The advantages of the Matthews correlation coefficient (MCC) over F1 score and accuracy in binary classification evaluation.* BMC Genomics 2020;21:6. doi:10.1186/s12864-019-6413-7. [C]。重點如下：
  - F1 不使用 TN，而且會隨「哪一類定為陽性」而改變。
  - 不平衡資料上 accuracy 會過度樂觀。
  - MCC 要四格都表現好才會高分，陰陽類互換時值不變。
  - 來源：[BMC Genomics](https://bmcgenomics.biomedcentral.com/articles/10.1186/s12864-019-6413-7)；[PMC6941312](https://pmc.ncbi.nlm.nih.gov/articles/PMC6941312)
- **Cohen's kappa 的批評**：Delgado R, Tibau X-A. *Why Cohen's Kappa should be avoided as performance measure in classification.* PLoS ONE 2019;14(9):e0222916. doi:10.1371/journal.pone.0222916. [C]。多類別情境下 kappa 與 MCC 多數時候相關，但在部分不平衡情況中，較差的分類器反而可能得到較高的 kappa。當混淆矩陣非對角元素的熵趨近 0 時，兩者差異變大。結論是一般不應用 kappa 比較分類器。— [PMC6762152](https://pmc.ncbi.nlm.nih.gov/articles/PMC6762152)

### Inferences
- **(a) 二元任務的指標選擇理由【推論，依上述證據】**：
  1. **Primary**：在事先固定的門檻下（在訓練折內以 Se ≥ 目標值，例如 0.90，選定門檻，並鎖定後才看 test），報告 **Sensitivity**（因 FN 較嚴重），以及 **正常照片誤報率 = 1−Sp**。理由：兩者與盛行率無關，可解讀，也直接對應臨床立場。Balanced accuracy = (Se+Sp)/2 作為單一摘要數字。也可改用以 Se 加權的 EC：EC = π₁·c_FN·(1−Se) + π₀·c_FP·(1−Sp)，π 取等權或目標盛行率，c_FN > c_FP。這是 Metrics Reloaded 在「嚴重度不等」時的建議。
  2. **門檻無關的 secondary**：AUROC，需用 cluster-aware CI（見 Q5）。
  3. **Supporting**：MCC；Se 達 0.90 時的 Sp（"Sp@Se=0.9"）；AUPRC 只在「已換算到目標盛行率」時才報，或者不報。
  4. **不建議當主指標**：accuracy、F1 / macro-F1。理由：F1 忽略 TN，而本專案正常照片只有 9 張，誤報率恰恰是重點；F1 也依賴盛行率（Chicco & Jurman 2020）。Cohen's kappa 同樣不建議（Delgado & Tibau 2019）。
- **本樣本的 AUPRC 特別有問題【推論】**：在陽性比例 84% 的資料上，隨機分類器的 AUPRC 基準約 0.84，看起來很高卻沒有資訊量。若改把「正常」視為陽性類別計算 AUPRC，基準則是 0.16。結論：不要報未換算的 AUPRC。
- **9 張正常照片的統計解析度（computed）**：
  - Sp 只能是 0、1/9、…、9/9，步長 11 個百分點。
  - 9/9 的 Wilson 95% CI 為 0.701–1.000；8/9 為 0.565–0.980；7/9 為 0.453–0.937。
  - Se 方面，44/47 的 Wilson CI 為 0.828–0.978。
  - 上述 CI 尚未考慮 clustering，真實區間只會更寬（見 Q5 模擬）。

### Gaps
- 未找到專門針對「皮膚／傷口照片」比較 AUROC 與 AUPRC 的實證研究。未找到可靠證據。
- Metrics Reloaded 對 AP「may be more suitable」的確切條件（原文措辭是否為 "class balance" 或 "imbalance"）在擷取文字中有歧義。報告引用時請以原文核對。

---

## Q3. 三級分期（normal / stage1 / stage2）的 ordinal 指標與主要指標選擇

### Takeaway
Metrics Reloaded 承認 weighted Cohen's kappa 是醫學影像處理 ordinal 資料時的「state-of-the-art」慣例，但共識小組認為 **Expected Cost（EC，可自訂不對稱成本矩陣）一般更合適**。
- **主要指標建議**：EC，成本矩陣事先登錄，並使低估（under-staging，尤其是漏判 → normal）的成本高於高估；類別先驗取等權（相當於 class-balanced，不受樣本盛行率影響）。也可用 **macro-averaged MAE** 作為等價、易懂的版本。
- **次要指標**：
  - 兩條 cumulative 二元切點的 Se/Sp/AUROC：normal vs ≥stage1，就是本專案的二元偵測任務；≤stage1 vs stage2。
  - Linear 與 quadratic weighted kappa：為了和文獻比較，報告但不作主指標。
  - 完整的 3×3 混淆矩陣。
- 「Adjacent accuracy」在只有 3 級時幾乎沒有鑑別力，不建議使用。

### Cited Findings
- **Metrics Reloaded 對 ordinal 的立場**：Discussion 寫道，weighted Cohen's kappa「is the state-of-the-art metric used in the medical imaging community when handling ordinal data」，並且「allows the user to specify different costs for different class confusions」。但「our consortium deemed the (not widely known) metric EC generally more appropriate」。EC 被描述為源自語音辨識社群、與盛行率無關的指標；類別混淆嚴重度不等時（FP2.5）建議用 EC。— Maier-Hein et al. 2024, Nature Methods, [PMC11182665](https://pmc.ncbi.nlm.nih.gov/articles/PMC11182665/) [B]
- **Kappa 一般性批評**（同樣適用於 weighted kappa 的機率校正結構）：Delgado & Tibau 2019，[PMC6762152](https://pmc.ncbi.nlm.nih.gov/articles/PMC6762152) [C]
- **Ordinal 評估方法**：
  - Cardoso JS, Sousa R. *Measuring the performance of ordinal classification.* IJPRAI 2011;25(8):1173–1195. [C]。主張 MAE/MSE 等於把 ordinal 問題當回歸處理，結果取決於指派給各類別的數值，因此另提出直接由混淆矩陣定義的指標（OCI）。— [INESC TEC repository](https://repositorio.inesctec.pt/items/7df8325e-7f56-4946-9ff6-ef6a6e91e17f/full)（DOI not verified this session）
  - Gaudette L, Japkowicz N. *Evaluation Methods for Ordinal Classification.* Canadian AI 2009, LNCS 5549:207–210. doi:10.1007/978-3-642-01818-3_25. [C]。比較 ordinal 分類中不同誤差指標的效果；後續文獻引用時指出，其 MAE/MSE 比較假設類別間距相等。— [Springer](https://link.springer.com/doi/10.1007/978-3-642-01818-3_25)
- Vanbelle（weighted kappa 的 linear 與 quadratic 權重比較）：本次未取得可核對來源，見 Gaps。

### Inferences
- **公式（標準定義，【推論】整理）**：
  - 混淆矩陣 O（K×K，K=3，列 = 真實 i，行 = 預測 j），N = 總數。
  - **Linear / quadratic weighted kappa**：κ_w = 1 − Σ w_ij·O_ij / Σ w_ij·E_ij，其中 E_ij = (row_i·col_j)/N。
    - Linear：w_ij = |i−j|/(K−1)，K=3 時權重為 0、0.5、1。
    - Quadratic：w_ij = (i−j)²/(K−1)²，K=3 時權重為 0、0.25、1。所以 QWK 對「相鄰錯誤」的懲罰只有兩級錯誤的 1/4。
    - 實作：`sklearn.metrics.cohen_kappa_score(y, yhat, weights="quadratic")`。
  - **Expected Cost**：EC = Σ_i π_i Σ_j c_ij · P(ŷ=j | y=i)，c_ii = 0。π_i 取 1/3（balanced）或目標盛行率。
    - 建議的不對稱成本矩陣（列為真實、行為預測；例子，需事先登錄）：
      - 真 normal → 預測 stage1 c=1，預測 stage2 c=2
      - 真 stage1 → 預測 normal c=3（漏判），預測 stage2 c=1
      - 真 stage2 → 預測 normal c=6（嚴重漏判），預測 stage1 c=2
    - 歸一化：除以「永遠預測成本最低之單一類別」的 EC，得到 normalized EC。小於 1 才代表優於 trivial 分類器。
  - **Macro-averaged MAE**：MAE^M = (1/K) Σ_i mean_{n: y_n=i} |ŷ_n − y_n|，類別編碼為 0/1/2。它與「π 等權、c_ij=|i−j| 的 EC」完全等價，比 MAE 更不受類別比例影響。
  - **Cumulative 二元指標**：
    - 切點 1：y≥1 vs y=0。Se₁ = P(ŷ≥1 | y≥1)，Sp₁ = P(ŷ=0 | y=0)。這就是 phlebitis vs normal。
    - 切點 2：y=2 vs y≤1，同理定義 Se₂、Sp₂。
    - 若模型輸出 ordinal 分數（例如 E[stage] = p1 + 2·p2，或 CORAL/cumulative-link 的累積機率），各切點 AUROC = roc_auc_score((y≥k), score)。
  - **Ordinal 一致性（rank-based）**：Somers' D 或 Kendall τ_b，計算真實分期與連續分數之間的關係，例如 `scipy.stats.somersd`、`kendalltau`。
  - **Adjacent accuracy**：K=3 時只有 normal↔stage2 這種兩級錯誤會被算錯，資訊量極低，不建議使用。
- **為何主指標不選 QWK【推論】**：
  1. Metrics Reloaded 推薦 EC。
  2. QWK 的機率校正項依賴樣本邊際分布，屬於盛行率相依；Delgado & Tibau 的反例機制同樣存在。
  3. 只有 56 張、14 位病人時，QWK 抽樣變異極大。
  4. QWK 的權重是對稱的，無法表達「漏判比過判嚴重」。

  不過 QWK 是業界慣例【業界慣例】，所以列為 secondary，以便與文獻比較。
- **與二元任務的一致性【推論】**：Se₁/Sp₁ 應與二元模型使用同一張表與同一套 CI 程序，方便說明「分期模型是否犧牲了偵測能力」。

### Gaps
- Vanbelle 對 linear vs quadratic weighted kappa 的具體結論（例如 Vanbelle & Albert 2009、Vanbelle 2016 Psychometrika），本次未搜尋核對。未找到可靠證據（本次未驗證）。
- Gaudette & Japkowicz 2009 的確切結論（哪個指標最佳）無全文可核對。
- Macro-MAE 的原始出處（Baccianella, Esuli, Sebastiani 2009）未在本次核對。

---

## Q4. 物件偵測指標：mAP@0.5、mAP@0.5:0.95、FROC、Metrics Reloaded 建議、只有約 24 張框圖時的問題、影像層級 vs 病灶層級、Ultralytics 定義

### Takeaway
Metrics Reloaded 對偵測任務的建議如下：
- 先定義 localization criterion（box IoU 或中心點距離）與 assignment strategy。
- 再以 F-beta（固定門檻）加上 AP 或 FROC（多門檻）評估。FROC 較易解讀，AP 較標準化。
- 偵測任務沒有 TN，因此 Specificity、AUROC 不適用。

Ultralytics 8.4 的 mAP 是 COCO 式 101 點插值 AP，取 10 個 IoU 門檻（0.50:0.05:0.95）的平均；模型選擇用的 fitness **100% 權重放在 mAP50-95**。

對邊界模糊的發紅區域、加上只有約 24 張有框的照片，mAP50-95 主要反映「框畫得多準」，抽樣變異又極大。因此建議：
- 偵測任務的主報告：病灶層級 recall @ 固定 FP/影像（FROC 點），localization 用寬鬆門檻（IoU≥0.3 或「中心點落在 GT 內」）。
- 影像層級報告：任一框就算陽性，用 Se/Sp，與分類任務共用同一套 CI。
- mAP50 只作 secondary；mAP50-95 僅供參考。

### Cited Findings
- **Metrics Reloaded（偵測）**：
  - 物件可用 mask、bounding box 或中心點表示，再搭配對應的匹配標準（例如 Mask IoU）。
  - 沒有連續分數時通常以 counting 指標（F-beta）為主；有連續分數時「we recommend AP or Free-Response Receiver Operating Characteristic (FROC) Score」，FROC 用於「an easy interpretation」，AP 用於「a standardized metric」。
  - TN 未定義，使 Accuracy、Specificity、AUROC 等不適用。
  - 每張影像的物件數可能「extremely small, or even zero」，需要特殊的彙總方式（見其 Suppl. Note 2.4）。
  - 小結構建議用較低的 localization 門檻（FP3.1）。
  - 有一處 assignment 規則以「IoU > 0.5」為例（FP5.4）。
  - 來源：[PMC11182665](https://pmc.ncbi.nlm.nih.gov/articles/PMC11182665/) [B]
- **Ultralytics 官方文件**：
  - mAP50 為「Mean average precision calculated at an intersection over union (IoU) threshold of 0.50」。
  - mAP50-95 為「The average of the mean average precision calculated at varying IoU thresholds, ranging from 0.50 to 0.95」。
  - AP 是 PR 曲線下面積。
  - 來源：[Ultralytics YOLO performance metrics guide](https://docs.ultralytics.com/guides/yolo-performance-metrics/) [E]
- **Ultralytics 8.4 原始碼（本機已安裝版本，2026-10-30 讀取）** [E]：
  - `ultralytics/utils/metrics.py`：`compute_ap` 使用 `method = "interp"` 與 `np.linspace(0, 1, 101)`，即「101-point interp (COCO)」。
  - 回報的 P、R、F1 取自「threshold given by max F1 metric」：`i = smooth(f1_curve.mean(0), 0.1).argmax()`。也就是說，**P/R 是在使驗證集 F1 最大的信心門檻下回報的**，等於在評估資料上調門檻，會產生樂觀偏差。
  - `Metric.fitness`：`w = [0.0, 0.0, 0.0, 1.0]  # weights for [P, R, mAP@0.5, mAP@0.5:0.95]`。
  - `ultralytics/models/yolo/detect/val.py`：`self.iouv = torch.linspace(0.5, 0.95, 10)`。
  - 官方 metrics reference 頁也寫明 fitness 權重為 [0,0,0,1]，並以「steps of 0.05」說明 IoU 間距：[docs reference](https://docs.ultralytics.com/reference/utils/metrics/)

### Inferences
- **24 張框圖時 mAP 的問題【推論】**：
  1. AP 由 PR 曲線計算，每張圖可能只有 1–2 個 GT，所以一兩個框的配對成敗就會讓 AP 跳動很大。
  2. 靜脈炎發紅邊界模糊，加上單一標註者，框的 IoU 本身就有「標註者內變異」，mAP50-95 中高 IoU 門檻（0.75–0.95）主要在量測這種雜訊。
  3. Ultralytics 以 mAP50-95 選 best.pt，會偏向「框邊界與標註習慣一致」的模型，而非「不漏病灶」的模型。建議改以自訂指標選模型，例如 lesion recall @ ≤1 FP/image，或至少改用 mAP50。
  4. Ultralytics 的 P/R 是在 max-F1 門檻下回報，應改為「在訓練／驗證折決定門檻、在 test 套用」。
- **建議的偵測評估規格【推論】**：
  - (i) **病灶層級**：GT 框與預測框以 IoU≥0.3（或中心點落入 GT 框）配對，採 greedy 配對並依信心分數由高到低排序。
    - 報告 FROC 曲線，以及在 0.25、0.5、1、2 FP/image 的 recall。
    - 單一 FROC score = 這些點的平均 recall。這是常見做法（例如 LUNA16 用 1/8–8 FP/scan 七點）【業界慣例，本次未核對 LUNA16 原文】。
  - (ii) **影像層級**：image score = max box confidence，無框時為 0。可計算 AUROC、Se/Sp，並能和分類模型做配對比較（Q6）。
  - (iii) **病人層級**：同一病人任一張照片陽性即判陽性。這只適合作描述性輔助，因為只有 14 位病人。
  - CI 一律以病人層級 cluster bootstrap 計算（Q5）。重抽時把該病人的所有照片與框一起抽，再重算 FROC/AP。
- **只有約 24 張有框照片時**：任何偵測指標的 CI 都會非常寬。應如實報告，不宜做模型間的顯著性檢定（見 Q6 的檢定力計算）。

### Gaps
- Metrics Reloaded Suppl. Note 2.4（物件很少或為 0 時的彙總）全文未取得。
- 沒有找到針對「模糊邊界皮膚病灶」偵測的 IoU 門檻實證研究。未找到可靠證據。
- FROC 的 CI 方法學（例如 JAFROC、Chakraborty）本次未搜尋核對。

---

## Q5. 信賴區間：Wilson / Clopper-Pearson / Newcombe；DeLong；clustered 資料為何 naive bootstrap 低估變異；病人層級 cluster bootstrap 理論與實務；percentile vs BCa；最少需要幾個 cluster

### Takeaway
1. 照片層級的 Wilson 或 naive bootstrap 會把同一病人的多張照片當成獨立樣本，**低估**變異。本專案的模擬（computed）顯示：14 位病人、ICC 0.3 時，名目 95% CI 的實際涵蓋率只有約 75–84%。
2. **病人層級（cluster）bootstrap** 是正確方向（Field & Welsh 2007；Rutter 2000；Genders 2012）。但只有 14 個 cluster 時，percentile cluster bootstrap 本身也偏窄（模擬涵蓋率約 88–90%）。計量經濟學文獻（Cameron, Gelbach & Miller 2008）也顯示少於約 30 個 cluster 時一般的 cluster 推論會過度拒絕。
3. 實務建議：
   - 主要報告用 patient-level percentile bootstrap，B ≥ 2,000，按病人類別分層。
   - 另外報告「design-effect 調整後的 Wilson」作敏感度分析；在模擬中它涵蓋率最接近 95%。
   - 文中明確承認 14 個 cluster 下 CI 可能仍偏窄。
   - BCa 在 cluster 很少時不建議作主方法，因為 acceleration 的 jackknife 只有 14 個點，估計不穩。
   - AUC 可用 Obuchowski 1997 clustered DeLong 作分析式交叉驗證。

### Cited Findings
- **二項比例 CI**：
  - Brown LD, Cai TT, DasGupta A. *Interval Estimation for a Binomial Proportion.* Statistical Science 2001;16(2):101–133. doi:10.1214/ss/1009213286. [B]。小 n 建議 Wilson 或 equal-tailed Jeffreys，較大 n 建議 Agresti–Coull；n>40 時三者非常相近。— [Project Euclid PDF](https://projecteuclid.org/download/pdf_1/euclid.ss/1009213286)；[doi.org](https://www.doi.org/10.1214/SS/1009213286)
  - Clopper-Pearson（exact）較保守，屬標準統計知識，與 Brown 等的比較一致【研究證據，同上】。
- **Clustered 敏感度／特異度**：Genders TSS, Spronk S, Stijnen T, Steyerberg EW, Lesaffre E, Hunink MGM. *Methods for calculating sensitivity and specificity of clustered data: a tutorial.* Radiology 2012;265(3):910–916. doi:10.1148/radiol.12120509. [B]。
  - 每位病人有多個觀察值即屬 clustered，需調整病人內的相關性。
  - 涵蓋的方法：(a) 不同層級分析但忽略相關；(b) variance adjustment；(c) logistic random-effects；(d) GEE。
  - 方法選擇與報告層級應對應臨床決策問題。
  - 來源：[RSNA](https://pubs.rsna.org/doi/10.1148/radiol.12120509)；[Erasmus repub](https://repub.eur.nl/pub/65359)
- **Patient-clustered bootstrap**：Rutter CM. *Bootstrap estimation of diagnostic accuracy with patient-clustered data.* Acad Radiol 2000;7(6):413–419. [C]。
  - 以重抽病人的簡單 bootstrap 估計多部位資料的 Se、Sp、AUC。
  - 模擬中，95% 區間的涵蓋率與分析式方法相當；每位病人部位數多時 bootstrap 略佳。
  - **Percentile 區間優於 normal-approximation bootstrap 區間**。
  - 來源：[KB digital library record](https://ibl.kb.nl/article/0000000012007/7/6/5/lang/uk)；[zhenzhi record](https://data.zhenzhi.com/details/1/906299170)（DOI not verified this session）
- **Cluster bootstrap 理論**：Field CA, Welsh AH. *Bootstrapping clustered data.* JRSS-B 2007;69(3):369–390. doi:10.1111/j.1467-9868.2007.00593.x. [B]。cluster bootstrap 在 transformation model 與 random-effect model 下都能給出一致（consistent）的變異數估計；residual bootstrap 只在 transformation model 下一致。這些是漸近結果。— [RePEc](https://econpapers.repec.org/RePEc:bla:jorssb:v:69:y:2007:i:3:p:369-390)；[ANU](https://researchportalplus.anu.edu.au/en/publications/bootstrapping-clustered-data/)
- **Cluster 太少的問題**：Cameron AC, Gelbach JB, Miller DL. *Bootstrap-based improvements for inference with clustered errors.* Review of Economics and Statistics 2008. [B]。
  - cluster 約 5–30 個時，標準 cluster-robust 檢定會過度拒絕。
  - **pairs cluster bootstrap 在幾乎所有情況下都比 wild cluster bootstrap 不可靠**。
  - wild cluster bootstrap-t 在 cluster 少到 5 個時仍有改善。
  - 來源：[NBER t0344](https://www.nber.org/papers/t0344.pdf)
  - 後續：Canay, Santos & Shaikh 分析 cluster 數「small」（約 8 個）時 wild bootstrap 仍有效的條件 [B]：[PDF](https://home.uchicago.edu/amshaikh/webfiles/wild.pdf)。Webb（2013）提出 ≤12 個 cluster 的修正版本（次級來源描述）。
  - 適用性注意：這些文獻針對迴歸係數。wild bootstrap 需要迴歸殘差結構，不能直接套用到 AUC、kappa 等非線性指標【推論】。
- **Clustered ROC（Obuchowski）**：Obuchowski NA. *Nonparametric analysis of clustered ROC curve data.* Biometrics 1997;53:567–578. doi:10.2307/2533958. [B]。
  - 將 DeLong 等 1988 的 structural components 法延伸到 clustered 資料。
  - 使用 Rao & Scott 的 design effect / effective sample size 概念。
  - 提供兩條相關 ROC 曲線比較的例子。
  - Cleveland Clinic Lerner 有 R 實作。
  - 2020 年 Wu 的論文批評其估計量因同等加權所有配對而非最有效率。
  - 來源：[Lerner clusteredROC help](https://www.lerner.ccf.org/quantitative-health/documents/clusteredROC_help.pdf)；[RePEc Wu 2020](https://ideas.repec.org/a/taf/lstaxx/v49y2020i6p1446-1461.html)
- **Metrics Reloaded**：
  - Table 1 把小測試集列為 pitfall，建議「confidence intervals for all metrics」。
  - 非獨立測試樣本（FP4.5）建議「Respect the hierarchical data structure when aggregating metrics」（引 Liang & Zeger 1986）。
  - 沒有明確推薦 bootstrap 方法。
  - 來源：[PMC11182665](https://pmc.ncbi.nlm.nih.gov/articles/PMC11182665/) [B]

### Inferences

**(b) Metrics and CI computation spec【推論；公式為標準統計定義】**

1. **單位與層級**：主分析單位為照片；CI 的重抽單位為**病人**。每個指標都要註明 n_photos / n_patients，例如「Sp = 8/9 photos from 3 patients」。
2. **比例型指標**（Se、Sp、誤報率、各類 recall）：
   - Wilson 區間：
     - p̂ = x/n，z = 1.96
     - center = (p̂ + z²/2n)/(1 + z²/n)
     - half = z·√(p̂(1−p̂)/n + z²/4n²)/(1 + z²/n)
   - Clopper-Pearson：
     - lo = Beta⁻¹(α/2; x, n−x+1)
     - hi = Beta⁻¹(1−α/2; x+1, n−x)
   - **Cluster 調整版 Wilson（敏感度分析）**：
     - 以病人層級比例 r_k = x_k/m_k 估計 ratio-estimator 變異：Var_cl = s²(r_k)/K（等 m 的簡化版；不等 m 時用 Σ(x_k − p̂·m_k)²·K/((K−1)·N²)）
     - DE = max(1, Var_cl / [p̂(1−p̂)/N])
     - n_eff = N/DE
     - 以 (p̂·n_eff, n_eff) 代入 Wilson 計算
   - 這是 Rao–Scott / effective-sample-size 的思路，Obuchowski 1997 也引用同一概念。
   - 兩個成對比例的差：Newcombe 1998 hybrid score 法（未核對，見 Gaps），或用下方的 paired cluster bootstrap。
3. **AUROC**：
   - DeLong（非 clustered）：
     - placement value V10(X_i) = (1/n₀) Σ_j ψ(X_i, Y_j)，V01(Y_j) = (1/n₁) Σ_i ψ(X_i, Y_j)；ψ = 1 / 0.5 / 0（大於 / 相等 / 小於）
     - Var(AUC) = S10/n₁ + S01/n₀，S 為 placement values 的樣本變異數
   - Clustered 版（Obuchowski 1997）：把 placement values 按病人加總後計算 between-cluster 變異。
     - Var = K₁/((K₁−1)N₁²) Σ_k (V10_k − m_k·Â)² + K₀/((K₀−1)N₀²) Σ_k (V01_k − n_k·Â)² + 2K/((K−1)N₁N₀) Σ_k (V10_k − m_k·Â)(V01_k − n_k·Â)
     - 其中 V10_k = cluster k 內所有陽性照片的 placement 總和，m_k、n_k 為 cluster k 的陽性、陰性照片數。
     - **此式依記憶整理，使用前請以 Obuchowski 1997 原文或 Lerner `clusteredROC` 核對**。
   - 主要報告採 patient-level bootstrap percentile CI；Obuchowski 式作交叉檢核。
4. **多類別／ordinal 指標**（EC、macro-MAE、BA、QWK、MCC）：沒有封閉式 CI，只用 patient-level bootstrap。
5. **Bootstrap 設定**：
   - B = 2,000（點估計），差值檢定用 5,000–10,000。
   - 用 percentile 法；不用 normal approximation（Rutter 2000 指出 percentile 較佳）。
   - BCa 只作敏感度分析：K=14 時 jackknife acceleration 只靠 14 個 leave-one-patient-out 值，不穩定。
   - 以病人「類別組成」分層重抽（見 pseudo-code）。
   - 記錄並報告「重抽中指標未定義（例如沒有正常照片）的比例」。
6. **CV 與 CI 的關係**：
   - 3-fold StratifiedGroupKFold 的「折間 SD」不是 CI。
   - 正確做法是把每個 fold 的 out-of-fold 預測合併（pooled OOF predictions，每張照片恰好一個預測），再對合併預測做 patient-level bootstrap。
   - 這個 CI 只反映「測試樣本」的不確定性，沒有反映「訓練集隨機性」。後者可用 repeated grouped CV（例如重複 5–10 次、不同 seed）的變異來補充說明。
   - held-out 的 14–18 張照片（約 3 位病人）**無法給出有意義的 CI**，建議只作 sanity check，主要結論以 pooled OOF 為準。
7. **門檻**：決策門檻一律在各訓練折內決定，不可在合併後的 OOF 上調。Ultralytics 的 max-F1 P/R 不能當成最終結果。

**模擬證據（computed，本專案 venv，1,000 次模擬，B=500，真實 Se=0.85，病人層級機率 ~ Beta、ICC=ρ）**：

| K 病人 | 每人照片 m | ICC | 照片層級 Wilson 涵蓋率（平均寬度） | 照片層級 bootstrap | **病人層級 bootstrap** | DE 調整 Wilson |
|---|---|---|---|---|---|---|
| 14 | 4 | ≈0 | 0.937 (0.185) | 0.917 | 0.903 (0.174) | 0.944 |
| 14 | 4 | 0.3 | 0.840 (0.183) | 0.810 | 0.883 (0.239) | 0.917 (0.253) |
| 14 | 8 | 0.3 | 0.764 (0.129) | 0.748 | 0.895 (0.210) | 0.915 (0.222) |
| 10 | 4 | 0.3 | 0.868 | 0.844 | 0.896 | 0.919 |
| 30 | 4 | 0.3 | 0.839 | 0.850 | 0.925 | 0.935 |
| 100 | 5 | 0.3 | 0.807 (0.062) | 0.815 | **0.939** (0.091) | 0.942 |

解讀【推論】：
- 照片層級的 CI 在 ICC>0 時明顯涵蓋不足，而且每人照片越多越嚴重（m=8 時只有 76%）。
- 病人層級 bootstrap 在 K=14 時約 88–90%，K=30 約 92.5%，K=100 約 94%。這與「cluster 少時 bootstrap 偏窄」的文獻方向一致。
- 未來約 1,000 張照片若來自 ≥100 位病人，病人層級 bootstrap 就可靠。
- **CI 寬度**：真正的 CI 約比照片層級寬 30–60%。
- 這只是單一資料生成模型下的模擬，不代表一般結論。

**Design effect 示範（computed）**：DE = 1 + (m−1)·ICC
- 56 張 / 14 人（m=4）：ICC 0.3 時 DE 1.9，n_eff ≈ 29.5。
- 120 張 / 14 人（m≈8.6）：ICC 0.3 時 DE 3.27，n_eff ≈ 37。也就是 120 張照片的資訊量只相當於約 37 張獨立照片。
- 1,000 張 / 200 人（m=5）：ICC 0.3 時 n_eff ≈ 455；1,000 張 / 100 人（m=10）時 n_eff ≈ 270。
- 結論：**未來擴充時，增加病人數比增加每人照片數有效得多**。

**Pseudo-code（Python / numpy；【推論】實作）**

```python
import numpy as np

def patient_strata(y, groups):
    """Stratify patients by class composition, e.g. 'only-normal', 'only-positive', 'mixed'.
    Ordinal: use the frozenset of stages present per patient as the stratum key."""
    keys = {}
    for g in np.unique(groups):
        keys[g] = tuple(sorted(set(y[groups == g])))
    strata = {}
    for g, k in keys.items():
        strata.setdefault(k, []).append(g)
    return strata                              # {stratum_key: [patient ids]}

def cluster_bootstrap_ci(y, score_or_pred, groups, metric_fn, B=2000, alpha=0.05,
                         stratified=True, seed=0, max_redraw=50):
    """Patient-level (cluster) percentile bootstrap CI for ANY metric.
    metric_fn(y, s) -> float; must raise ValueError or return np.nan if undefined
    (e.g. specificity with no normal photos, AUROC with one class)."""
    rng = np.random.default_rng(seed)
    idx_by_pt = {g: np.flatnonzero(groups == g) for g in np.unique(groups)}
    strata = patient_strata(y, groups) if stratified else {"all": list(idx_by_pt)}
    point = metric_fn(y, score_or_pred)
    stats, n_undefined = [], 0
    for b in range(B):
        for _ in range(max_redraw):                    # conditional resampling
            pts = np.concatenate([rng.choice(p, size=len(p), replace=True)
                                  for p in strata.values()])
            idx = np.concatenate([idx_by_pt[g] for g in pts])
            try:
                v = metric_fn(y[idx], score_or_pred[idx])
            except ValueError:
                v = np.nan
            if np.isfinite(v):
                break
            n_undefined += 1
        stats.append(v)
    stats = np.asarray(stats, float)
    lo, hi = np.nanpercentile(stats, [100*alpha/2, 100*(1-alpha/2)])
    return dict(point=point, lo=lo, hi=hi, B=B, undefined_redraws=n_undefined,
                n_patients=len(idx_by_pt), n_photos=len(y))
```

**缺類別的處理說明【推論】**：
1. 先**分層**：各「類別組成」的病人群各自重抽同樣人數，確保每次重抽都有正常照片與陽性照片的病人。
2. 若仍有未定義的情況（例如某 stratum 只有 1 位病人），就重抽（conditional bootstrap），並報告重抽次數。
3. 不可把未定義值當成 0 或 1。
4. 若只有 1–2 位病人提供正常照片，就算分層，Sp 的 bootstrap 分布也只是這 1–2 人的組合，實際上幾乎沒有資訊。這種情況應直接寫「Sp 無法可靠估計」，只報 x/n 與 Wilson 加 DE 敏感度分析。

### Gaps
- **最少需要幾個 cluster 才可靠**：未找到針對「診斷準確度指標的 cluster bootstrap」的明確最低 cluster 數門檻研究。計量文獻顯示少於約 30 個 cluster 時一般推論偏差（Cameron et al. 2008）；本筆記的模擬只是示範。網路上「40 clusters」的經驗法則來自部落格，未核實，不採用。
- BCa 在少量 cluster 下的表現：未找到可靠證據（本次未搜尋到專門研究）。
- Newcombe 1998（paired 比例差 CI，Stat Med 17:2635–2650）與 Davison & Hinkley 1997（Bootstrap Methods and Their Application，2.3/3.8 節 hierarchical bootstrap），本次未搜尋核對。
- Genders 2012 全文在付費牆後，只核對了摘要。

---

## Q6. 兩模型比較：DeLong、McNemar（exact/mid-p）、5×2cv、corrected resampled t-test、paired cluster bootstrap／permutation、Bayesian correlated t-test；clustered 資料下的有效性；樣本數與檢定力；多重比較；14 位病人下的最小可偵測差

### Takeaway
- **14 位病人的資料做不出有檢定力的兩模型比較**，只能做描述性比較：報告差值與 patient-level paired bootstrap CI，並預先聲明為 exploratory。
- 檢定方法的選擇：
  - **同一組測試照片上比較兩個「已訓練完成」的模型**：用 paired **cluster** bootstrap 或 **cluster 層級的 sign-flip permutation**（14 位病人可完整列舉 2¹⁴ = 16,384 種排列）。
  - 照片層級的 McNemar 與 DeLong 都假設照片獨立，在 clustered 資料下會過度拒絕，需改用 clustered 版本（Obuchowski 1997 的 clustered DeLong；clustered McNemar，例如 Obuchowski 1998、Durkalski 2003，本次未核對）。
  - **比較「學習演算法」（含訓練變異）**：Nadeau–Bengio corrected resampled t-test 或 Bouckaert–Frank 的 repeated-CV 版本，或 Bayesian correlated t-test。這些方法都要求 CV 以病人分組（grouped）。
  - 多模型比較：Holm（控制 FWER）或 Benjamini–Hochberg（探索性）。Demšar 的 Friedman+Nemenyi 是「多資料集」用的方法，**不適用於單一資料集**。

### Cited Findings
- **Dietterich 1998**：Dietterich TG. *Approximate Statistical Tests for Comparing Supervised Classification Learning Algorithms.* Neural Computation 1998;10(7):1895–1923. doi:10.1162/089976698300017197. [B]。
  - 「兩比例差檢定」與「多次隨機 train/test 切分的 paired t-test」第一型錯誤率高，「should never be used」。
  - 10-fold CV paired t-test 第一型錯誤率略偏高。
  - McNemar 第一型錯誤率低。
  - 5×2cv 第一型錯誤率可接受，檢定力略高於 McNemar。
  - 只能訓練一次的演算法，McNemar 是唯一第一型錯誤可接受的檢定；可訓練 10 次時建議 5×2cv。
  - 來源：[Oregon State PDF](https://web.engr.oregonstate.edu/~tgd/publications/dietterich-approximate-statistical-tests-nc1998.pdf)
- **McNemar 的版本選擇**：Fagerland MW, Lydersen S, Laake P. *The McNemar test for binary matched-pairs data: mid-p and asymptotic are better than exact conditional.* BMC Med Res Methodol 2013;13:91. doi:10.1186/1471-2288-13-91. [C]。
  - 在 9,595 個情境中，mid-p 從未超過名目顯著水準，檢定力接近 asymptotic 檢定。
  - Exact conditional 與連續性校正的 asymptotic 檢定過度保守。
  - 推薦 mid-p；若能容忍偶爾小幅超標，未校正的 asymptotic 檢定亦可。
  - 來源：[doi.org](https://www.doi.org/10.1186/1471-2288-13-91)
- **Corrected resampled t-test**：
  - Nadeau C, Bengio Y. *Inference for the Generalization Error.* Machine Learning 2003;52:239–281. doi:10.1023/A:1024068626366。
  - Bouckaert RR, Frank E. *Evaluating the Replicability of Significance Tests for Comparing Learning Algorithms.* PAKDD 2004, LNCS 3056:3–12. doi:10.1007/978-3-540-24775-3_3。
  - 兩者都由 R 套件 correctR 實作（`resampled_ttest`、`kfold_ttest`、`repkfold_ttest`）。[B]/[C]；文件為 [E]。— [correctR vignette](https://cran.hafro.is/web/packages/correctR/vignettes/correctR.html)
  - 標準公式：t = d̄ / √((1/J + n_test/n_train)·σ̂²_d)，J = 重抽次數。repeated k-fold 版本見 Bouckaert & Frank 2004（公式為標準形式，DOI 由次級文件取得）。
- **Bayesian 比較**：Benavoli A, Corani G, Demšar J, Zaffalon M. *Time for a Change: a Tutorial for Comparing Multiple Classifiers Through Bayesian Analysis.* JMLR 2017;18(77):1–36. [B]。主張以貝氏分析取代 NHST，工具包括 Bayesian correlated t-test（處理 CV 折間相關）、hierarchical correlated t-test、signed-rank test，並可用 ROPE（region of practical equivalence）。Python 套件 `baycomp`。— [JMLR](https://jmlr.org/papers/v18/16-305.html)；[arXiv](https://arxiv.org/pdf/1606.04316)
- **多資料集比較**：Demšar J. *Statistical Comparisons of Classifiers over Multiple Data Sets.* JMLR 2006;7:1–30（書目經 DBLP 列表確認；作者列表在搜尋結果中有疑義，應為 Demšar 單一作者，引用前以 JMLR 頁面核對）。[B] — [DBLP](https://dblp.dagstuhl.de/pid/94/3659.html)
- **AUC 比較**：
  - DeLong ER, DeLong DM, Clarke-Pearson DL. *Comparing the areas under two or more correlated ROC curves.* Biometrics 1988;44:837–845：structural components 法，Obuchowski 1997 將其延伸到 clustered 資料。— [Obuchowski 1997 摘要/引用](https://www.bohrium.com/paper-details/nonparametric-analysis-of-clustered-roc-curve-data/812073859254583296-922)（DeLong DOI not verified this session）
  - Hanley JA, McNeil BJ. *A method of comparing the areas under ROC curves derived from the same cases.* Radiology 1983;148(3):839–843. doi:10.1148/radiology.148.3.6878708. [B]。以 binormal 假設把成對評分的相關轉換成兩條 ROC 面積的相關，用來降低差值的 SE。— [PubMed 6878708](https://pubmed.ncbi.nlm.nih.gov/6878708/)
    - 反證：Song 1997（Biometrics）的模擬指出 Hanley-McNeil 法用於檢定時不合適（依搜尋摘要，未讀原文）。
- **Clustered 資料的檢定**：Obuchowski 1997 的 clustered ROC 法可比較兩條相關、clustered 的 ROC 曲線。[B] — [Lerner clusteredROC](https://www.lerner.ccf.org/quantitative-health/documents/clusteredROC_help.pdf)
- **Connor 1987 McNemar 樣本數**：本次搜尋未找到 Connor 1987 原文頁面，未核對。以下公式為廣泛使用的標準形式，見 Inferences 的 computed 數字。

### Inferences

**(c) Model comparison statistical test guide【推論，依上述證據】**

| 情境 | 建議方法 | clustered 資料下是否有效 | 備註 |
|---|---|---|---|
| 兩個已訓練好的模型，同一批測試照片，比較 Se/Sp/BA/EC 等 | **Paired patient-level bootstrap**：每次重抽同一組病人，計算 Δ = m_A − m_B，取 percentile CI；p 值用 cluster sign-flip permutation | 有效（以病人為獨立單位） | 首選 |
| 同上，指標為二元正確率 | McNemar mid-p（Fagerland 2013） | **照片層級無效**，因為違反獨立性；需改為 clustered McNemar，或改用上列 bootstrap/permutation | Dietterich 1998 的結論是在獨立樣本下得出的 |
| 同上，比較 AUROC | Clustered DeLong（Obuchowski 1997）或 paired cluster bootstrap | 照片層級的 DeLong 會低估 SE | `pROC::roc.test` 不處理 cluster |
| 比較兩種「訓練流程」（含資料切分隨機性） | Repeated grouped k-fold 加上 Nadeau–Bengio / Bouckaert–Frank corrected t；或 Bayesian correlated t-test 加 ROPE | 需 **GroupKFold**，否則有 patient leakage | 5×2cv 在 14 位病人下每折只有 7 人，太少 |
| ≥3 個模型或多個指標 | 兩兩比較後用 Holm（confirmatory）或 BH-FDR（exploratory） | — | Friedman+Nemenyi（Demšar 2006）需要多個資料集，本專案不適用 |
| 「沒有更差」（例如新模型 Se 不低於舊模型） | Non-inferiority：paired cluster bootstrap 的 Δ 下界 > −margin | — | margin 需事先登錄 |

**Cluster sign-flip permutation（paired）pseudo-code**

```python
def paired_cluster_bootstrap(y, pa, pb, groups, metric_fn, B=10000, seed=0, **kw):
    """CI for metric(A) - metric(B) with the SAME resampled patients for both models."""
    rng = np.random.default_rng(seed)
    idx_by_pt = {g: np.flatnonzero(groups == g) for g in np.unique(groups)}
    strata = patient_strata(y, groups)
    point = metric_fn(y, pa) - metric_fn(y, pb)
    d = []
    while len(d) < B:
        pts = np.concatenate([rng.choice(p, len(p), replace=True) for p in strata.values()])
        idx = np.concatenate([idx_by_pt[g] for g in pts])
        try:
            v = metric_fn(y[idx], pa[idx]) - metric_fn(y[idx], pb[idx])
        except ValueError:
            continue                              # count & report skipped draws
        if np.isfinite(v):
            d.append(v)
    d = np.asarray(d)
    lo, hi = np.percentile(d, [2.5, 97.5])
    p_boot = 2 * min((d <= 0).mean(), (d >= 0).mean())   # rough; prefer permutation p
    return dict(delta=point, lo=lo, hi=hi, p_boot=min(1.0, p_boot))

def cluster_permutation_test(y, pa, pb, groups, metric_fn, n_perm=None, seed=0):
    """H0: models A and B are exchangeable within each patient.
    Swap A<->B predictions for ALL photos of a patient jointly (sign-flip at patient level).
    With K<=16 patients, enumerate all 2^K assignments exactly."""
    pts = np.unique(groups); K = len(pts)
    obs = metric_fn(y, pa) - metric_fn(y, pb)
    def stat(flip):
        swap = np.isin(groups, pts[flip])
        a = np.where(swap, pb, pa); b = np.where(swap, pa, pb)
        return metric_fn(y, a) - metric_fn(y, b)
    if n_perm is None and K <= 16:
        flips = ((np.arange(2**K)[:, None] >> np.arange(K)) & 1).astype(bool)
    else:
        rng = np.random.default_rng(seed)
        flips = rng.random((n_perm or 20000, K)) < 0.5
    null = np.array([stat(f) for f in flips])
    p = (np.sum(np.abs(null) >= abs(obs) - 1e-12) + (0 if K <= 16 else 1)) / \
        (len(null) + (0 if K <= 16 else 1))
    return dict(delta=obs, p_value=p, n_perm=len(null))
# Note: for non-additive metrics (AUROC, EC) the swap is still valid under exchangeability;
# patients whose A and B predictions are identical contribute no information.
```

**Permutation 檢定的解析度【computed / 推論】**：
- 14 位病人做完整列舉時，雙尾最小可能 p 值 = 2/16,384 ≈ 0.00012。前提是 14 位病人全部朝同一方向不一致。
- 若只有 d 位病人的兩模型預測有差異，最小 p = 2/2^d：
  - d=5 → 0.0625（**不可能顯著**）
  - d=6 → 0.031
  - d=7 → 0.016
- 照片層級 exact McNemar 若全部不一致對都偏向同一模型，所需不一致數（computed，雙尾 p = 2·0.5^b）為 b=5 → 0.0625，b=6 → 0.031。也就是**至少要 6 個全部同向的不一致對才可能達 p<0.05**。這還沒考慮 clustering；若這 6 張照片來自 2 位病人，有效證據只有 2 個單位。

**樣本數與檢定力（computed，標準公式；Connor 1987 原文未核對）**：
- McNemar 配對樣本數（Connor 式）：n = [z_{α/2}·√ψ + z_β·√(ψ − δ²)]² / δ²，其中 ψ = 不一致比例（p₁₀+p₀₁），δ = p₁₀ − p₀₁。取 α=0.05 雙尾、power 0.8：

  | ψ | δ | 所需照片對數（獨立樣本） |
  |---|---|---|
  | 0.10 | 0.10 | 76 |
  | 0.30 | 0.15 | 102 |
  | 0.20 | 0.10 | 155 |
  | 0.10 | 0.05 | 312 |
  | 0.20 | 0.05 | 626 |

  clustered 資料還要乘上 DE。例如 ICC 0.3、m=5 時 DE=2.2，ψ=0.2、δ=0.1 就需要約 341 張照片。
- AUC 的 SE（Hanley & McNeil 1982 公式）：SE² = [A(1−A) + (n_A−1)(Q₁−A²) + (n_N−1)(Q₂−A²)]/(n_A·n_N)，其中 Q₁ = A/(2−A)，Q₂ = 2A²/(1+A)：
  - A=0.85，47 陽 / 9 陰 → SE 0.057，95% CI 半寬約 0.11（未考慮 clustering）
  - A=0.85，held-out 約 14 陽 / 4 陰 → SE 0.096，半寬約 0.19
  - A=0.85，未來 333/333 → SE 0.015，半寬約 0.03
- **14 位病人下的最小可偵測差（MDD）【推論】**：
  - 單一模型 AUC 的 CI 半寬約 0.11（獨立）。乘上 √DE（DE 約 2–3）後約 0.16–0.19。
  - 兩模型 AUC 差的 SE 取決於兩者相關 r，約為 √(2(1−r))·SE；r=0.5 時約等於單一 SE。所以 80% power 的 MDD 約 2.8 × 0.08–0.10 ≈ **0.2–0.3 AUC**。
  - Se/Sp 方面，以 9 張正常照片、3 位左右的正常病人，**Sp 差異實際上無法檢定**。
  - 結論：現階段任何「模型 A 顯著優於 B」的說法都不可信。只報 Δ 與 cluster CI，並把檢定留給約 1,000 張照片、≥100 位病人的未來資料，同時事先登錄主要比較。
- **多重比較**：
  - Bonferroni：α/m。
  - Holm：p 值由小到大排序，第 i 個與 α/(m−i+1) 比較，一旦不拒絕即停止。Holm 一致地比 Bonferroni 有力，同樣控制 FWER。
  - Benjamini–Hochberg：找最大的 i 使 p_(i) ≤ (i/m)·q，控制 FDR，適合探索性的超參數或模型掃描。
  - Python 實作：`statsmodels.stats.multitest.multipletests(method="holm"|"fdr_bh")`。
  - 建議：預先登錄 1 個 primary comparison（不校正），其餘為 secondary 並用 Holm。上述為標準統計方法【業界慣例】；原始論文本次未核對。
- **Bayesian correlated t-test 的適用性**：可回答「差異落在 ROPE（例如 ±0.02 BA）內的機率」。但其相關係數 ρ 的預設值為 n_test/n_total，並假設各折獨立重訓。在 grouped CV 下仍屬近似，K=14 時後驗非常寬。

### Gaps
- Clustered McNemar 的具體方法（Obuchowski 1998 Stat Med；Durkalski et al. 2003 Stat Med；Eliasziw & Donner 1991），本次未搜尋核對，未列 DOI。
- Connor 1987（Biometrics 43:207–211）原文本次搜尋未找到，所以樣本數公式是以標準形式呈現。
- Obuchowski 的 AUC 比較樣本數方法（例如 Obuchowski & McClish 1997；Obuchowski 1998 Acad Radiol），本次未核對。
- Benjamini & Hochberg 1995、Holm 1979 原文未在本次核對（屬標準方法）。
- Park & Han 2018 Radiology、Obuchowski & Bullen 2018、STARD 2015、TRIPOD+AI 2024 對指標或 CI 的具體條文，本次未在工具預算內搜尋核對。它們是撰寫報告時可補充的 [A]/[B] 來源。
- 小樣本、clustered 醫學影像下 Nadeau–Bengio 校正的實證表現，未找到可靠證據。
