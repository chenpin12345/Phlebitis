# 皮膚影像 AI 的公平性與代表性：膚色、年齡、部位、刺青、毛髮，與本專案的 metadata／次群體分析策略

> 存取日期：所有來源皆於 2026-10-30 存取。
> 來源分級：[A] 官方／標準／報告指引；[B] 系統性回顧／統合分析／頂級期刊；[C] 一般同儕審查；[D] 預印本；[E] 部落格／論壇／新聞（僅作輔助）。
> 驗證層級標示：**〔全文已開〕**＝本輪實際開啟原文或 PubMed 摘要並核對數字；**〔搜尋摘要〕**＝僅從搜尋結果摘要取得，未開啟全文，數字引用前須再核對。
> 結論標示：**研究證據顯示**／**業界慣例**／**本報告推論**。
> 專案脈絡：台灣研究原型（非診斷）；手臂／手背 IV 置管部位照片；目前約 120 張／14 位病人，未來約 1,000 張平衡資料；來源為義大醫院（高雄）＋民眾經 LINE 上傳；SQLite 存 metadata；僅本機運算；不自動訓練；模型建議需人工確認。

---

## Q1. 皮膚科 AI 在深色皮膚上的表現落差：證據有多強？

### Takeaway
研究證據顯示：公開皮膚影像資料集極少記錄膚色（Wen 2022：僅 2.1% 影像有 FST），而在獨立、經切片證實的多元膚色資料集（DDI）上，三個已發表模型整體 ROC-AUC 從原報告 0.88–0.94 掉到 0.56–0.67，且 FST V–VI 又比 FST I–II 更差；但用多元資料微調後落差可消失。這些證據全部來自「腫瘤／一般皮膚病分類」，不是發炎／紅斑偵測。

### Cited Findings
- **DDI（Daneshjou et al. 2022, Sci Adv 8(31):eabq6147, doi:10.1126/sciadv.abq6147）[B]〔全文已開〕**：656 張影像（剔除 13 張低品質）；FST I–II 208 張、III–IV 241 張、V–VI 207 張；每個病例一張影像，病人數未另列。 — [PMC9374341](https://pmc.ncbi.nlm.nih.gov/articles/PMC9374341/)
  - 整體 ROC-AUC：ModelDerm 0.65（95% CI 0.61–0.70，原報告 0.93–0.94）；DeepDerm 0.56（0.51–0.61，原報告 0.88）；HAM10000 模型 0.67（0.62–0.71，原報告 0.92）。 — [PMC9374341](https://pmc.ncbi.nlm.nih.gov/articles/PMC9374341/)
  - FST I–II vs V–VI ROC-AUC：ModelDerm 0.64 vs 0.55；DeepDerm 0.61 vs 0.50；HAM10000 0.72 vs 0.57。 — [PMC9374341](https://pmc.ncbi.nlm.nih.gov/articles/PMC9374341/)
  - 敏感度 FST I–II vs V–VI：ModelDerm 0.41 vs 0.12（P=0.0025）；DeepDerm 0.69 vs 0.23（P=5.65×10⁻⁶）。 — [PMC9374341](https://pmc.ncbi.nlm.nih.gov/articles/PMC9374341/)
  - 皮膚科醫師（相對於切片標籤）敏感度 FST I–II vs V–VI：0.72 vs 0.59（P=8.8×10⁻⁶）；常見疾病子集 0.93 vs 0.62。即「人類專家也有膚色落差」。 — [PMC9374341](https://pmc.ncbi.nlm.nih.gov/articles/PMC9374341/)
  - 在 DDI 上微調後：DeepDerm FST I–II 0.73 vs V–VI 0.76；HAM10000 0.77 vs 0.78 — 落差消失。 — [PMC9374341](https://pmc.ncbi.nlm.nih.gov/articles/PMC9374341/)
  - 該文亦引用：Fitzpatrick17k 抽查 504 張中僅 69% 看起來確實符合標示疾病。 — [PMC9374341](https://pmc.ncbi.nlm.nih.gov/articles/PMC9374341/)
- **Wen et al. 2022（Lancet Digit Health 4(1):e64–e74, doi:10.1016/S2589-7500(21)00252-1）系統性回顧 [B]〔PubMed 摘要已開〕**：21 個公開資料集、106,950 張影像；有年齡 76.4%、性別 77.5%、部位 74.4%，但**有族裔資料僅 1,415 張（1.3%）、有 FST 資料僅 2,236 張（2.1%）**；14 個有報告國別的資料集中 11 個（79%）完全來自歐洲／北美／大洋洲；結論為深色膚型「substantial under-representation」。 — [PubMed 34772649](https://pubmed.ncbi.nlm.nih.gov/34772649/)
  - 二手訪談稿稱有 FST 的影像中僅 10 張 FST V、1 張 FST VI，且數字與摘要略有出入（1,585／2,436 vs 1,415／2,236）。以摘要為準。[E]〔搜尋摘要〕 — [MedicalResearch.com 訪談](https://medicalresearch.com/dermatology-datasets-used-for-ai-lack-diversity-and-completeness/)
- **Fitzpatrick17k（Groh et al. 2021, CVPR Workshop ISIC, arXiv:2104.09957）[C]〔ar5iv 全文已開（2026-10-31 存取）〕**：16,577 張臨床影像（兩個圖譜），114 種疾病，以群眾標註 FST（2–5 位標註者，對照 312 張皮膚科醫師金標準）。分組數：**FST 1–2：7,755 張；3–4：6,089 張；5–6：2,168 張；unknown：565 張**（約 47%／37%／13%／3%；原文未給單一型別數）。以 1–2 型訓練的模型在 3–4 型表現優於 5–6 型；以 5–6 型訓練者在 3–4 型優於 1–2 型，即「模型在與訓練膚型相近者最準」。**ITA vs FST：即使最佳 ITA 方法，約三分之一影像與人工 FST 相差超過 1 級；最佳 ±1 級一致率 70.38%**（經驗映射、YCbCr 遮罩）。 — [ar5iv 2104.09957](https://ar5iv.labs.arxiv.org/html/2104.09957) — [CVF Open Access](https://openaccess.thecvf.com/content/CVPR2021W/ISIC/html/Groh_Evaluating_Deep_Neural_Networks_Trained_on_Clinical_Images_in_Dermatology_CVPRW_2021_paper.html)；[arXiv 2104.09957](https://arxiv.org/abs/2104.09957)
- **Groh et al. 2024（Nat Med, doi:10.1038/s41591-023-02728-3）[B]〔搜尋摘要；nature.com 全文被導向登入〕**：約 390 位皮膚科醫師與約 459–460 位基層醫師、39 國、364 張影像、46 種疾病；正確率皮膚科 38%、基層 19%；**兩組在深色皮膚上都低約 4 個百分點**；DLS 輔助使正確率提升 >33%，但**對基層醫師反而擴大了膚色間落差**。新聞稿另稱基層提升 69%，與摘要框架不一致，引用時以原文為準。 — [MIT Media Lab 頁面](https://www.media.mit.edu/publications/deep-learning-aided-decision-support-for-diagnosis-of-skin-disease-across-skin-tones/)；[Kellogg 研究頁](https://www.kellogg.northwestern.edu/academics-research/research/detail/2024/deep-learning-aided-decision-support-for-diagnosis-of-skin/)；[ScienceDaily [E]](https://sciencedaily.com/releases/2024/02/240206144931.htm)
- **Kinyanjui et al. 2020（MICCAI, "Fairness of Classifiers Across Skin Tones in Dermatology"）[C]〔搜尋摘要〕**：以 ITA 估計膚色，發現 ISIC 2018 與 SD-198 兩個基準資料集都低度代表與深色皮膚相關的 ITA 範圍。 — [作者 PDF](https://rpand002.github.io/data/MICCAI_2020.pdf)；[arXiv 1910.13268](https://arxiv.org/abs/1910.13268)
- **Kalb et al. 2023（MICCAI FAIMI workshop, arXiv:2308.09640）[D/C]〔搜尋摘要〕**：先前以 ITA 做膚色公平性分析的研究之間「high disagreement」；ITA 分箱門檻無共識；ITA（顏色）→ Fitzpatrick（日曬反應）的映射高度不確定；ISIC18 多樣性不足，不適合當公平性測試平台。 — [arXiv 2308.09640](https://arxiv.org/abs/2308.09640v1)
- **Adamson & Smith 2018（JAMA Dermatol）**：本輪搜尋未取得此文頁面，**未找到可靠證據（未驗證）**；其內容（以淺膚色為主之訓練資料可能加劇健康不平等的觀點文章）僅屬撰寫者既有知識，不得作為已驗證引用。

### Inferences
- 本報告推論：DDI 的「微調後落差消失」支持一個實務結論——落差主要源自**訓練資料組成**而非任務本身不可能，因此本專案應優先投資「資料收集多樣性 + 分層評估」，而不是事後演算法修正。
- 本報告推論：Groh 2024 顯示「AI 輔助提升整體正確率」與「縮小群體落差」是兩件事。本專案採「人工確認模型建議」設計，仍須分層報告「人+AI」的表現，不可只報整體。
- 本報告推論：現有證據幾乎都是**歐美資料、以 FST I–II vs V–VI 對比**；台灣資料以 FST III–IV 為主，落差可能較小或呈現不同型態，不能直接套用上述數字，只能當成「需要檢查」的理由。

### Gaps
- Adamson & Smith 2018 原文、Groh 2024 全文細節本輪未能開啟核對（Groh 2021 分組數已於第二輪核對）。
- TRIPOD+AI 全文 PDF 已下載但為壓縮串流，無法擷取條文，公平性相關條目仍未核對。
- 未找到任何以「東亞 FST III–IV vs 東南亞 IV–V」為對比的皮膚 AI 表現研究。

---

## Q2. 紅斑在深色皮膚上較難看見：壓傷第一期、蜂窩性組織炎與靜脈炎

### Takeaway
研究證據顯示：壓傷第一期（以「不可反白紅斑」為定義核心）在深色皮膚上的記錄比例明顯偏低（13% vs 淺色 38%），被普遍解讀為「看不到」而非「沒發生」；NPIAP 立場是單靠視診不可靠，需加觸診／溫度／水腫／皮下水分等。**靜脈炎專屬的膚色證據：未找到可靠證據**；但所有靜脈炎量表都含紅斑，因此推論上同樣有風險。

### Cited Findings
- **Black J, Cox J, Capasso V, et al. NPIAP 觀點文章，WCET J 2023;43(3):18–29 [C]（代表 NPIAP 立場）〔全文已開〕**：
  - Van Gilder 等（1989–2005 盛行率資料）：第一期壓傷占比在深色皮膚「much lower (13%)」，中等膚色 32%、淺色 38%；作者認為可能反映偵測困難。 — [WCET Journal](https://journals.cambridgemedia.com.au/wcetcn/volume-43-number-3/current-perspectives-pressure-injuries-persons-dark-skin-tones-national-pressure-injury-advisory-panel)
  - NPIAP 早期工作小組（Henderson 1997）假設：「Very darkly pigmented skin does not have visible blanching」，因此第一期徵象納入溫度變化（熱或涼）、水腫、硬結。 — [同上](https://journals.cambridgemedia.com.au/wcetcn/volume-43-number-3/current-perspectives-pressure-injuries-persons-dark-skin-tones-national-pressure-injury-advisory-panel)
  - 「visual inspection alone is unreliable」；色素、濕度、溫度、觀察者敏銳度、**照明**都影響主觀評估。 — [同上](https://journals.cambridgemedia.com.au/wcetcn/volume-43-number-3/current-perspectives-pressure-injuries-persons-dark-skin-tones-national-pressure-injury-advisory-panel)
  - 皮下水分（SEM）掃描：統合分析中位數比視診早 5 天；雙臂研究（n=175，48 位非白人）敏感度 86.8%、特異度 88%；深色皮膚世代研究提早約 1 週（OR 5.3）。長波紅外線熱影像可用於淺／深膚色。 — [同上](https://journals.cambridgemedia.com.au/wcetcn/volume-43-number-3/current-perspectives-pressure-injuries-persons-dark-skin-tones-national-pressure-injury-advisory-panel)
  - 膚色工具評論：Fitzpatrick 為日曬敏感度工具，對曝曬皮膚不可靠、最好用於未曝曬處；Munsell 在醫療上效度／信度測試極少；Konishi 的 Skin Tone Colour Scale 被稱為臨床最完整；英國皮膚科醫學會推薦 Eumelanin Human Skin Colour Scale（Dadzie，以反射式 melanin index 分類）。該文未討論 Monk。 — [同上](https://journals.cambridgemedia.com.au/wcetcn/volume-43-number-3/current-perspectives-pressure-injuries-persons-dark-skin-tones-national-pressure-injury-advisory-panel)
  - Bennett 1995：該文僅以文獻引用方式提及（工作小組成立背景），**本輪未找到 Bennett 原文數字**。
- **Oozageer Gunowa N, Hutchinson M, Brooke J, Jackson D. J Clin Nurs 2018;27(17–18):3266–3275, doi:10.1111/jocn.14062 [C]〔搜尋摘要〕**：性質為 literature review（非正式系統性回顧），檢索 1990–2016/07，納入 11 篇；結論：深色皮膚者較易發生**較高期別**壓傷，推測現行皮膚評估方法對深色皮膚效果較差、早期損傷未被辨識；相關指引與證據缺乏。 — [PubMed 28887872](https://pubmed.ncbi.nlm.nih.gov/28887872/)；[Kingston 作者稿](https://eprints.kingston.ac.uk/id/eprint/39175)
- **靜脈炎量表**：Ray-Barruel 等系統性回顧（Griffith 典藏）指出紅斑是**唯一出現在所有靜脈炎量表中的症狀**；沒有任何量表經嚴謹心理計量驗證。[B]〔搜尋摘要〕 — [Infusion phlebitis assessment measures: a systematic review](https://research-repository.griffith.edu.au/items/99944d18-a28b-5ffd-8e70-ac00cee44f86)
  - PIVC 靜脈炎徵象的評分者間一致性普遍偏低，只有壓痛與兩個量表達可接受一致性。[C]〔搜尋摘要〕 — [USC 典藏：Inter-rater agreement on PIVC-associated phlebitis signs](https://research.usc.edu.au/esploro/outputs/journalArticle/Inter-rater-agreement-on-PIVC-associated-phlebitis-signs/99450063702621)
  - 僅一個非同儕審查的考試解說頁提到「深色皮膚紅斑較難察覺，需加評溫熱、水腫、靜脈變硬、疼痛」。[E] — [NPrep](https://nprep.in/question-answer/all-are-true-about-the-grades-of-phlebitis-except-sWcppqJ4POJMk1t8SDjS_)
- **靜脈炎專屬「膚色 × 偵測率」研究：未找到可靠證據。**
- **蜂窩性組織炎在有色皮膚上的表現**：本輪未取得具體研究，**未找到可靠證據（本輪未驗證）**。

### Inferences
- 本報告推論：靜脈炎量表全部依賴紅斑 → 以「照片紅斑」為主要訊號的模型，在膚色較深者（例如部分東南亞移工、原住民族）可能系統性低估。照片模型天生無法取得溫度／硬結／壓痛，所以 metadata 必須同時記錄**護理師床邊觸診的硬結、溫熱、疼痛、條索狀靜脈**，作為不依賴顏色的標註依據，並分析「紅斑不明顯但其他徵象陽性」的案例比例是否隨膚色變化。
- 本報告推論：壓傷文獻中「記錄比例偏低」的現象提醒：若本專案的 ground truth 來自護理視診，**標籤本身在深色皮膚上就可能有偽陰性**，模型與標籤會「一起錯」，分層指標看起來還很好。需在標註流程中加入非視覺徵象欄位與第二評估者。

### Gaps
- 無靜脈炎膚色研究；無台灣或東南亞族群的紅斑可見度研究。
- Bennett 1995 原文、蜂窩性組織炎在有色皮膚的誤診研究本輪未查到原文。

---

## Q3. 如何測量／記錄膚色：Fitzpatrick、Monk、ITA° 與其限制

### Takeaway
業界慣例：皮膚 AI 研究多用 FST，但 FST 是「日曬反應」量表而非膚色量表，且常被誤用為種族代理；Monk 10 階是為電腦視覺設計的膚色描述量表，但在臨床／東亞族群缺乏驗證；ITA° 可從影像計算，但對照明與白平衡極敏感、分箱門檻無共識。本報告推論：最穩健做法是**同時**記錄兩種以上（人工 Monk 或 FST ＋ 有色卡校正後在未受累皮膚計算的 ITA°），並報告其一致性。

### Cited Findings
- **Fitzpatrick 的批評**：
  - Ware et al. 2020（Cutis, "Racial Limitations of Fitzpatrick Skin Type"）[C]〔搜尋摘要〕：FST 原為評估光療時燒傷傾向，卻常被拿來描述先天膚色與族裔；呼籲勿混淆種族／族裔與 FST，並發展更臨床相關的有色皮膚描述方法。 — [MDedge 原文頁](https://www.mdedge.com/dermatology/article/216697/pigmentation-disorders/racial-limitations-fitzpatrick-skin-type/page/0/1)
  - Okoji UK, Taylor SC, Lipoff JB. Br J Dermatol 2021;185(1):198–199, "Equity in skin typing: why it is time to replace the Fitzpatrick scale" [C]〔僅書目資料，未取全文〕 — [Drexel 典藏](https://researchdiscovery.drexel.edu/esploro/outputs/journalArticle/Equity-in-skin-typing-why-it/991022199999804721)
  - NPIAP 觀點文章：FST 對曝曬皮膚不可靠，最好用於未曝曬部位。[C]〔全文已開〕 — [WCET J 2023](https://journals.cambridgemedia.com.au/wcetcn/volume-43-number-3/current-perspectives-pressure-injuries-persons-dark-skin-tones-national-pressure-injury-advisory-panel)
- **Monk Skin Tone（MST）Scale（Google × Ellis Monk, 2022）[E/業界]〔搜尋摘要〕**：10 階、開源、CC BY 4.0；2022/05 Google I/O 發表；美國約 3,000 人調查，多數認為 10 階與 40 階一樣能代表自己膚色；Google 明確警告不要把色階等同種族。 — [Google 部落格](https://blog.google/technology/ai/monk-skin-tone-scale/)
  - 本輪**未找到** Monk 在臨床皮膚科或東亞族群的信度／效度研究（未找到可靠證據）。
- **ITA°（Individual Typology Angle）**：
  - Kinyanjui 2020 用 ITA 估計資料集膚色分布。[C] — [MICCAI 2020 PDF](https://rpand002.github.io/data/MICCAI_2020.pdf)
  - Kalb 2023：ITA 分箱門檻無共識、ITA→FST 映射不確定、不同研究結果高度不一致。[D] — [arXiv 2308.09640](https://arxiv.org/abs/2308.09640v1)
  - Groh 2021：最佳 ITA 方法 ±1 級 FST 一致率僅 70.38%，約 1/3 影像相差 >1 級。[C]〔全文已開〕 — [ar5iv 2104.09957](https://ar5iv.labs.arxiv.org/html/2104.09957)
  - Krishnapriya, King & Bowyer 2021（臉部辨識領域）：人工 FST 評分者間不一致難以消除；**影像中沒有校正物件時自動評估特別困難**。[C]〔搜尋摘要〕 — [arXiv 2308.09640 相關搜尋頁](https://ar5iv.labs.arxiv.org/html/2308.09640)（該文引用 Krishnapriya；Krishnapriya 原文本輪未開）
  - 2026 預印本：以色度計監督訓練的皮膚鏡影像 ITA 與色度計值高度一致；模型與群眾 FST 標註的線性加權 kappa 0.53，群眾標註者間 0.66。[D]〔搜尋摘要〕 — [arXiv 2602.10265](https://arxiv.org/html/2602.10265v1)
  - ITA 公式（Chardon 1991：ITA° = arctan[(L* − 50)/b*] × 180/π）與 6 級分類門檻：屬撰寫者既有知識，**本輪未開啟 Chardon 原文驗證**。
- **FST 評分者間信度**：
  - 哥倫比亞 Biomédica 2008 研究（光型量表）：標準化前加權 kappa 0.31／0.40，標準化訓練後 0.77／0.82。[C]〔搜尋摘要〕 — [Biomédica](https://revistabiomedica.org/index.php/biomedica/article/download/59/60/237)
  - 以影像標 FST：3 位皮膚科醫師之間的一致性與「醫師 vs 群眾」相當（具體 kappa 本輪未取得）。[D]〔搜尋摘要〕 — [arXiv 2207.02942](https://arxiv.org/pdf/2207.02942v1.pdf)
  - 二手彙整稱 Groh 2021 群眾 FST 完全正確率 38–59%、差一級以內 71–85%；**未在原文核對**。[E] — [Emergentmind](https://www.emergentmind.com/topics/fitzpatrick-skin-type-fst-scale)
- **照明／相機對膚色量測的影響**：
  - 2023 J Biophotonics：角度影響 a*、b*、L*；距離只影響 L*；RAW（DNG）比 JPG 變異小。[C]〔搜尋摘要〕 — [LU 典藏](https://research.lu.lv/en/publications/effect-of-camera-distance-and-angle-on-color-of-diverse-skin-tone/)
  - 2020 Sensors（犬皮膚，智慧手機＋ColorChecker 校正）：同機 ΔE 0.1、跨機 ΔE 2.0–3.9；紅斑指數估計誤差 0.5–3%。[C]（動物模型，僅作代理）〔搜尋摘要〕 — [PMC7662536](https://pmc.ncbi.nlm.nih.gov/articles/PMC7662536/)
  - 2025 預印本（FST III–IV）：線性色彩校正使色差下降 67–77%（ΔE<2.3），但作者警告「色彩看起來準確」不代表臨床生物指標可靠。[D]〔搜尋摘要〕 — [arXiv 2512.21988](https://arxiv.org/pdf/2512.21988v2)

### Inferences
- 本報告推論：民眾 LINE 上傳的照片無法控制白平衡、光源、壓縮（LINE 會再壓縮），所以**來自 LINE 的影像不宜計算 ITA 作為主要膚色變數**，最多作為輔助；醫院端拍攝若能放置灰卡／色卡，ITA 才有意義。
- 本報告推論：「照明 × 膚色」是交互作用：較深膚色在暖光／低光下紅斑對比更低。因此 metadata 必須記錄光源類型與有無色卡，分析時把「光源」與「膚色」一起分層，否則會把照明問題誤判為膚色問題（或反之）。
- 業界慣例：皮膚 AI 公平性研究主要用 FST；電腦視覺／消費產品轉向 Monk；ITA 多用於自動估計大型資料集。

### Gaps
- 無 Monk 量表在台灣／東亞臨床影像的信度研究；無「FST 在東亞人自評 vs 臨床評估」一致性的本輪查證資料。
- Chardon 1991、Krishnapriya 2021 原文未開。

---

## Q4. 其他共變項：年齡、老年紫斑／抗凝血劑瘀青、毛髮、刺青、部位、水腫／肥胖

### Takeaway
研究證據顯示：公開資料集約 3/4 有記錄年齡、性別、部位（Wen 2022），但對刺青、毛髮、瘀青等「干擾物」幾乎無系統研究。老年紫斑好發於前臂伸側與手背——恰好是本專案的 IV 部位——且抗凝血劑會讓它更明顯，是靜脈炎紅斑的重要「長得像」干擾。刺青對皮膚 AI 的影響：**未找到可靠證據**。

### Cited Findings
- 年齡／性別／部位記錄率：76.4%／77.5%／74.4%（21 個公開資料集）。[B]〔PubMed 摘要已開〕 — [PubMed 34772649](https://pubmed.ncbi.nlm.nih.gov/34772649/)
- **老年紫斑（senile/actinic purpura）**：DermNet 稱 >50 歲者逾 10% 有之，男女相當；病灶在**前臂伸側與手背**；在機構住民是皮膚撕裂傷的危險因子；良性、反覆出現。[C/參考資料]〔搜尋摘要〕 — [DermNet](https://pro.dermnetnz.org/topics/senile-purpura)
  - MSD Manual：因慢性日曬、老化與藥物造成真皮結締組織萎縮、血管脆弱。[C/參考資料]〔搜尋摘要〕 — [MSD Manual Professional](https://www.msdmanuals.com/professional/hematology/bleeding-due-to-abnormal-blood-vessels/senile-purpura)
  - 抗凝血劑／阿斯匹靈不致病但讓病灶更大更明顯（Medbullets 等教育網站）。[E]〔搜尋摘要〕 — [Medbullets](https://im.medbullets.com/dermatology/322037/senile-purpura)
- **刺青**：搜尋未找到任何檢驗刺青對皮膚病灶 AI 表現影響的研究——**未找到可靠證據**。
- **毛髮**：本輪未取得專門研究——**未找到可靠證據**（皮膚鏡文獻常把毛髮列為「artifact」，但本輪未開原文）。
- **身體部位（手背 vs 前臂）**：未找到 IV 部位影像 AI 依部位分層的研究——**未找到可靠證據**。
- **肥胖／水腫**：未找到與影像紅斑偵測相關之研究——**未找到可靠證據**；NPIAP 文章將水腫列為深色皮膚第一期壓傷的非視覺徵象。[C] — [WCET J 2023](https://journals.cambridgemedia.com.au/wcetcn/volume-43-number-3/current-perspectives-pressure-injuries-persons-dark-skin-tones-national-pressure-injury-advisory-panel)

### Inferences（本報告推論）
- 老年紫斑與抗凝血劑瘀青（紫紅色、在手背／前臂）、置管失敗後的血腫、膠布刺激性紅斑、消毒劑染色（優碘）都是靜脈炎紅斑的「假陽性來源」。若高齡、使用抗凝血劑者在陽性組比例較高，模型可能學到「有瘀青＝靜脈炎」的捷徑。必須記錄這些干擾物並做「有／無干擾物」的分層與錯誤分析。
- 手背皮膚薄、靜脈淺、易瘀青，前臂毛髮較多、皮下組織較厚；部位與膚色（手背較常日曬、較深）也相關。部位必須當作分層變數，且平衡資料時要按部位平衡。
- 刺青、濃密毛髮：證據不足，建議**先記錄、後判斷**（有／無、是否覆蓋 ROI），初期作為排除或品質旗標，而非主要分析變數。
- 水腫會改變皮膚光澤與顏色對比；肥胖者靜脈較深、置管部位可能不同。記錄 BMI（醫院端可得）與水腫有／無。

### Gaps
- 刺青、毛髮、部位、水腫對皮膚 AI 的定量影響：本輪皆未找到可靠研究。
- 台灣老年紫斑盛行率、抗凝血劑使用率：未查。

---

## Q5. 報告指引與法規：STANDING Together、TRIPOD+AI、CLAIM 2024、FDA、TFDA

### Takeaway
業界慣例（且已成為頂刊預期）：STANDING Together（2024/12 Lancet Digit Health）提供 29 項資料集多樣性文件化與使用建議；TRIPOD+AI（BMJ 2024）27 項；FDA 2025 年 1 月草案要求評估測試資料的多樣性與次群體表現。TFDA 2020 AI/ML 醫材軟體指引存在，但本輪**無法擷取其關於資料代表性的條文**。本專案為研究原型，不需查驗登記，但依這些指引設計 metadata 可避免日後重工。

### Cited Findings
- **STANDING Together**：Alderman JE, et al. "Tackling algorithmic bias and promoting transparency in health datasets: the STANDING Together consensus recommendations." Lancet Digit Health 2025;7(1):e64–e88, doi:10.1016/S2589-7500(24)00224-3（2024-12-18 線上）。修正式 e-Delphi：194 位參與者、25 國、32 個候選項、3 輪＋1 次會議；>350 人、58 國提供意見；最終 **29 項建議**，分「資料集文件化（給 curator）」與「資料集使用（辨識與減少演算法偏誤）」兩部分；作者強調是促進主動檢討而非勾選清單。另有 NEJM AI 同步版本（doi:10.1056/AIp2401088），**未直接核對**。[A]〔搜尋摘要〕 — [EASE 摘要頁](https://ease.org.uk/2025/02/tackling-algorithmic-bias-and-promoting-transparency-in-health-datasets-the-standing-together-consensus-recommendations/)；[Swansea 典藏 PDF](https://cronfa.swan.ac.uk/Record/cronfa68621/Download/68621__33229__2d70771f35904f9c979cdb14da62d05a.pdf)；[Google Research](https://research.google/pubs/standing-together-standards-for-data-diversity-inclusivity-and-generalisability-in-health-datasets/)
- **TRIPOD+AI**：Collins GS, Moons KGM, et al. BMJ 2024（2024-04-16），27 項主清單＋13 項摘要清單，適用回歸與機器學習預測模型。[A]〔搜尋摘要〕；**哪幾項涉及公平性／次群體，本輪未核對原文**。 — [BMJ](https://www.bmj.com/node/1095803)；[LMU 典藏全文 PDF bmj-2023-078378](https://epub.ub.uni-muenchen.de/116670/1/bmj-2023-078378.full.pdf)
- **CLAIM 2024 更新（Tejani 等，Radiology: AI）**：本輪搜尋**未能驗證**；CLAIM 2020 原版存在（Radiology: AI）。 — [CASRAI 指引彙整 [E]](https://casrai.org/guides/ai-reporting-guidelines-consort-ai-tripod-ai-decide-ai)
- **FDA 草案指引** "Artificial Intelligence-Enabled Device Software Functions: Lifecycle Management and Marketing Submission Recommendations"（2025-01-07, docket FDA-2024-D-4488，非約束性草案）：審查將評估測試資料的「quality, diversity, and quantity」；測試建議包含 subgroup performance assessment。[A]〔搜尋摘要；FDA 原文未開〕；指引中是否明文提及膚色——**未找到可靠證據**。 — [FDA 指引頁](https://fda.gov/regulatory-information/search-fda-guidance-documents/artificial-intelligence-enabled-device-software-functions-lifecycle-management-and-marketing)；[Federal Register](https://www.govinfo.gov/content/pkg/FR-2025-01-07/html/2024-31543.htm)；[King & Spalding 摘要 [E]](https://www.kslaw.com/insights/articles/fda-releases-draft-guidance-on-submission-recommendations-for-ai-enabled-device-software-functions)
- **TFDA**「人工智慧/機器學習技術之醫療器材軟體查驗登記技術指引」：2020-09-11 公告，參考美、日、韓與 IMDRF；審查人員得要求指引外之安全效能資料；不定期更新。[A]〔搜尋摘要；PDF 已下載但無法擷取文字〕 — [TFDA 網站](https://www.fda.gov.tw/tc/siteListContent.aspx?id=34961)；[北榮轉載 PDF](https://wd.vghtpe.gov.tw/DMC/files/%E4%BA%BA%E5%B7%A5%E6%99%BA%E6%85%A7%E6%A9%9F%E5%99%A8%E5%AD%B8%E7%BF%92%E6%8A%80%E8%A1%93%E4%B9%8B%E9%86%AB%E7%99%82%E5%99%A8%E6%9D%90%E8%BB%9F%E9%AB%94%E6%9F%A5%E9%A9%97%E7%99%BB%E8%A8%98%E6%8A%80%E8%A1%93%E6%8C%87%E5%BC%95.pdf)
  - TFDA 指引是否明文要求族群／膚色代表性：**未找到可靠證據（本輪未能讀取原文）**。

### Inferences
- 本報告推論：對研究原型而言，最低限度應做到 STANDING Together 的「文件化」部分：在資料集說明（datasheet）中描述人口組成（含膚色測量方法與缺漏率）、收集場域（醫院 vs LINE）、已知未被代表的群體、以及「此資料集不適合用於何種族群／情境」。
- 本報告推論：發表時以 TRIPOD+AI（若定位為預測模型）或 CLAIM（若定位為影像 AI）為報告清單，並在補充資料中附分層表。

### Gaps
- TRIPOD+AI 與 CLAIM 2024 的公平性相關條目原文、FDA 草案中膚色字樣、TFDA 指引代表性條文，本輪均未讀到原文。
- WHO、IMDRF 關於 AI 偏誤的文件本輪未搜尋（時間限制）。

---

## Q6. 台灣資料集的 metadata 擷取與次群體分析建議（含 14 位 vs 約 200 位病人的可行性）

### Takeaway
本報告推論：現階段（14 位病人、約 120 張）**任何次群體指標都沒有意義**，只能做描述性計數與逐例錯誤檢視；到約 200 位病人、約 1,000 張時，二元分層（如手背 vs 前臂、≥65 歲 vs <65、有 vs 無抗凝血劑、醫院 vs LINE）若每層陽性病人 ≥約 30 人，可報告帶 95% CI 的描述性分層敏感度／特異度，但膚色較深族群（東南亞移工、原住民族）很可能仍不足，除非刻意招募。

### Cited Findings
- 公開資料集普遍缺膚色、族裔（FST 2.1%、族裔 1.3%），且年齡／性別／部位約 3/4 有記錄 → 「先記錄」本身就已超越多數資料集。[B] — [PubMed 34772649](https://pubmed.ncbi.nlm.nih.gov/34772649/)
- DDI 每層約 200 張影像就能顯示 AUC 0.5–0.7 的 CI 寬度約 ±0.08–0.10（如 HAM10000 FST V–VI 0.57，CI 0.48–0.67）。[B] — [PMC9374341](https://pmc.ncbi.nlm.nih.gov/articles/PMC9374341/)
- FST 人工評分在標準化訓練後 kappa 可由 0.3–0.4 升到 0.8 左右 → 評分前需訓練與雙人評。[C] — [Biomédica 2008](https://revistabiomedica.org/index.php/biomedica/article/download/59/60/237)
- 照片拍攝角度、距離、格式影響顏色量測 → 拍攝規範要固定。[C] — [J Biophotonics 2023](https://research.lu.lv/en/publications/effect-of-camera-distance-and-angle-on-color-of-diverse-skin-tone/)
- 靜脈炎量表評分者間一致性低 → 標籤本身就有雜訊，應以雙人標註並記錄一致性。[C] — [USC 典藏](https://research.usc.edu.au/esploro/outputs/journalArticle/Inter-rater-agreement-on-PIVC-associated-phlebitis-signs/99450063702621)

### Inferences（本報告推論；具體建議）

**A. SQLite metadata 欄位建議（病人層級 / 影像層級分開存）**

病人層級（每位病人一次；可隨住院更新）：
| 欄位 | 值域 | 來源 | 備註 |
|---|---|---|---|
| age_band | <40／40–64／65–79／≥80 | 病歷 | 存年齡區間而非生日，降低可識別性 |
| sex | M／F／其他 | 病歷 | |
| skin_tone_monk_clin | 1–10 | 護理師／研究者對**未受累、未日曬的上臂內側**評估，持 Monk 色卡 | 雙人獨立評一部分以算 kappa |
| skin_tone_fst_self | I–VI／不知道 | 病人自評（日曬反應問句） | 與臨床評估並列，不互相取代 |
| ita_uninvolved | 連續值（°）＋ 是否有色卡 | 影像計算：未受累皮膚 patch、經灰卡／色卡校正 | 無色卡者標記為低信度，不納入主分析 |
| ancestry_self（選填） | 台灣漢人／原住民族／東南亞（越、印尼、菲、泰…）／其他／不願回答 | 自填 | 僅用於描述代表性；明確告知目的；可拒答 |
| anticoagulant_antiplatelet | 無／抗血小板／抗凝血／兩者 | 用藥紀錄 | |
| steroid_use | 有／無 | 用藥紀錄 | 皮膚變薄、易瘀青 |
| bmi_band、edema_limb | 區間／有無 | 病歷／護理評估 | |

影像層級（每張照片）：
| 欄位 | 說明 |
|---|---|
| body_site | 手背／腕／前臂／肘窩／其他；左右 |
| source | 醫院（指定手機型號）／LINE 民眾上傳 |
| device_model、has_color_card、light_source（日光燈／自然光／閃光燈／暖光）、lux_estimate（可選） | 照明×膚色交互作用分析必需 |
| confounders | 多選：老年紫斑／瘀青、血腫、膠布痕／刺激紅斑、優碘染色、刺青（是否覆蓋置管點）、濃密毛髮、疤痕、敷料遮擋 |
| nonvisual_signs | 護理師床邊：疼痛、壓痛、溫熱、硬結、條索狀靜脈、腫脹（各有／無）——與照片同時間點 |
| label_rater_1、label_rater_2、label_final、rater_agreement | 雙人標註與仲裁 |
| quality_flag | 模糊、過曝、ROI 被遮 |

**B. 次群體分析的可行性（以 Wilson 95% CI 估算；計算為本報告自行推算）**
- 單層若只有 5 位陽性病人、觀察敏感度 80%：95% CI 約 38%–96% → 無資訊量。
- 10 位陽性：約 49%–94% → 仍幾乎無法區分「好」與「差」。
- 30 位陽性：約 63%–91% → 可做描述性比較，但只能偵測很大的落差（>20–25 個百分點）。
- 同一病人多張照片高度相關：**有效樣本數接近病人數而非照片數**；CI 必須以病人為單位做 cluster bootstrap，資料切分也必須以病人為單位（同一人不可同時出現在訓練與測試）。

**在 14 位病人（現在）——沒有意義的分析：**
- 任何依膚色（Monk／FST／ITA／族裔）的分層 AUC、敏感度、特異度。
- 依年齡、抗凝血劑、部位、照明、來源的分層指標或交互作用。
- 任何「公平性差距」數值（equalized odds、demographic parity 等）及其顯著性檢定。
- 以照片數（約 120）當樣本數計算 CI。

**在 14 位病人——可做且應做的：**
- 描述性計數表：每個變數的分布與缺漏率（例如「Monk 5–7：12 人；8 以上：0 人」），明確揭露「目前完全沒有深膚色資料」。
- 逐例錯誤分析（qualitative）：每一張假陽性／假陰性都檢視是否與瘀青、膠布痕、照明、膚色有關。
- 驗證 metadata 流程本身：雙人 Monk 評分的一致性（即使樣本小，可發現評分說明是否需修正）、色卡是否實際被放入照片。

**到約 200 位病人／約 1,000 張（未來）——變得可行的：**
- 二元分層的描述性指標＋95% CI（病人層級 bootstrap）：手背 vs 前臂；<65 vs ≥65 歲；有 vs 無抗凝血／抗血小板；醫院 vs LINE；有 vs 無色卡；有 vs 無干擾物（瘀青、膠布痕）。前提：每層陽性病人至少約 30 位（若陽性率約 30%，200 位病人約 60 位陽性，二元分層勉強可行）。
- 膚色：以 Monk 合併為 2–3 組（例如淺／中／較深）報告描述性指標；**若「較深」組陽性病人 <約 20–30 位，只報計數與點估計並標示「樣本不足，不作結論」**。在台灣以 FST III–IV 為主的族群中，若不刻意招募，深膚色組極可能不足。
- 「膚色 × 照明」交互作用：即使 200 位也只適合做探索性圖示（例如各組別的 ROI 紅斑對比度分布），不做檢定。
- 多變項邏輯迴歸（錯誤 ~ 膚色 + 部位 + 年齡 + 抗凝血 + 來源，以病人為 cluster）：約 60 個事件下大約只能放 4–6 個變項，作探索用途。

**C. 資料平衡與招募**
- 「約 1,000 張平衡資料」不應只平衡陽性／陰性，也應設定**每個膚色組、部位、來源的最低病人數目標**（例如每組至少 30 位病人），並在義大醫院主動納入移工與原住民族病人（需 IRB 核准的招募說明，提供印尼文、越南文、菲律賓文、泰文版本）。
- 預先註冊（寫在研究計畫）要分析的次群體與最小樣本門檻，避免事後挑選。
- 資料集說明文件依 STANDING Together 精神寫明：膚色測量方法、各組人數、缺漏率、已知限制（如「深膚色樣本不足，不可推論於此族群」）。

### Gaps
- 台灣移工與原住民族的實際膚色分布、在義大醫院住院病人中的比例：本輪未查。
- 「每層最少多少病人」沒有共識性標準；上述 30 位陽性為本報告依 CI 寬度推算之經驗值，非指引規定。

---

## Q7. 在台灣蒐集族裔／膚色 metadata 的隱私考量（個資法）

### Takeaway
研究證據（法規文本）顯示：台灣個資法第 6 條特種個資為病歷、醫療、基因、性生活、健康檢查、犯罪前科——**種族／族裔不在列**（與 GDPR 不同）；但本專案的照片與臨床欄位本身就是醫療／病歷相關特種個資，學術研究例外須「必要」且「無從識別特定當事人」。個資法近年有修正並設個人資料保護委員會（籌備處），條文須至全國法規資料庫確認現行版本。

### Cited Findings
- 個資法第 6 條：病歷、醫療、基因、性生活、健康檢查、犯罪前科原則上不得蒐集、處理或利用；第 1 項第 4 款允許公務機關或學術研究機構基於醫療、衛生目的，為統計或學術研究所必要，且資料經處理後或依其揭露方式無從識別特定當事人。[A]〔搜尋摘要，引自國發會 110.01.07 發法字第1092001961號函所引條文〕 — [臺北市法規查詢：國發會函](https://laws.gov.taipei/law/Interpretation/RelatedLaw/FE347658)
- 法務部 107.09.04 法律字第10703512280號函：醫療影像中特種個資去識別化後，符合第 6 條第 1 項但書時，可認為未逾越原蒐集目的；去識別後若已非個人資料，對外提供不受個資法規範。[A]〔搜尋摘要〕 — [臺北市法規查詢](https://laws.gov.taipei/law/Interpretation/ContentExport/FE315623?type=5)
- 搜尋結果出現「個人資料保護委員會籌備處」115 年函，顯示主管機關與條文可能已變動，需確認現行條文。[A]〔搜尋摘要〕 — [臺北市法規查詢](https://laws.gov.taipei/Law/Interpretation/RelatedLaw/FE396001)

### Inferences（本報告推論）
- 族裔雖非特種個資，但與手部照片（刺青、疤痕、戒指、指甲）＋年齡＋住院日期組合後，在小樣本（特別是少數的移工或原住民族病人）中**再識別風險高**。建議：族裔欄位選填、可拒答；只存粗分類；統計表中任何格子 <5 人時不對外發表該格（或合併）。
- 族裔與移工身分可能涉及敏感社會處境（如居留身分），問卷只問「祖源／自我認同」與膚色，不問國籍或居留身分；用於描述資料代表性的目的需寫入 IRB 與知情同意書。
- 膚色（Monk／ITA）是從照片衍生的測量，比自填族裔更不具識別性，**優先以膚色量測而非族裔作為公平性分析主變數**，族裔僅作代表性描述。
- LINE 民眾上傳：需明確同意書、避免臉部與可識別背景入鏡、上傳後在本機去除 EXIF（GPS、時間、機型——機型可另以欄位保留）。本專案「僅本機運算」符合資料最小化方向。

### Gaps
- 2025 年後個資法修正版第 6 條條文、個資會對研究用醫療影像的最新解釋：本輪未開啟全國法規資料庫核對。
- 人體研究法、IRB 對族裔資料蒐集的具體要求：本輪未查。
