# AI 報告指引（Reporting Guidelines）與本地 ML 研究平台應自動記錄的欄位

存取日期（所有來源）：2026-10-30。來源分級：[A] 官方報告指引原文／官方 checklist；[B] 系統性回顧／頂尖期刊；[C] 其他同儕審查；[D] 預印本；[E] 部落格／程式碼／二手報導（僅作輔助）。
結論標示：【研究證據】= 出自引用文獻；【慣例】= 指引共識／領域慣例；【推論】= 本筆記針對本專案的判斷。
平台現況判斷依據：委派任務提供的專案描述，加上對 `02_主程式碼/src` 的一次快速 grep（看到 `seed`、`EXIF`、`research_consents`、`usage_revocations`、`shadow` 等表／欄位；未看到 Fitzpatrick/Monk、annotator、label_source、git commit 等欄位）。「已記錄」是依據這些資訊的【推論】，沒有逐一核對資料庫 schema。

### 來源清單（後文以 S 編號引用）

- **S1 [A]** Collins GS, Moons KGM, Dhiman P, et al. TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine learning methods. *BMJ* 2024;385:e078378. 2024-04-16 線上刊出。doi:10.1136/bmj-2023-078378. https://www.bmj.com/content/385/bmj-2023-078378 ；全文 PDF（Oxford ORA）https://ora.ox.ac.uk/objects/uuid:414e5fb8-5575-4b67-b94d-a0833a7cc58a/files/smp48sf448
- **S2 [A]** Tejani AS, Klontzas ME, Gatti AA, Mongan JT, Moy L, Park SH, Kahn CE Jr; CLAIM 2024 Update Panel. Checklist for Artificial Intelligence in Medical Imaging (CLAIM): 2024 Update. *Radiol Artif Intell* 2024;6(4):e240300（2024-05-29）。doi:10.1148/ryai.240300. https://pmc.ncbi.nlm.nih.gov/articles/PMC11304031
- **S3 [A]** Sounderajah V, Guni A, Liu X, Collins GS, Karthikesalingam A, Markar SR, Golub RM, Denniston AK, Shetty S, Moher D, Bossuyt PM, Darzi A, Ashrafian H; STARD-AI Steering Committee. The STARD-AI reporting guideline for diagnostic accuracy studies using artificial intelligence. *Nat Med* 2025，2025-09-15 線上刊出。doi:10.1038/s41591-025-03953-8；PMID 40954311。EQUATOR 頁面：https://www.equator-network.org/reporting-guidelines/the-stard-ai-reporting-guideline-for-diagnostic-accuracy-studies-using-artificial-intelligence/ ；作者接受稿（Univ. Birmingham）：https://pure-oai.bham.ac.uk/ws/files/282528526/STARD_AI_accepted.pdf 。卷期頁（31(10):3283–3289）只出現在搜尋摘要中，EQUATOR 頁面沒有列出，**未獨立驗證**。
- **S4 [A]** Daneshjou R, Barata C, Betz-Stablein B, et al. Checklist for Evaluation of Image-Based Artificial Intelligence Reports in Dermatology: CLEAR Derm Consensus Guidelines From the International Skin Imaging Collaboration Artificial Intelligence Working Group. *JAMA Dermatol* 2022;158(1):90–96. doi:10.1001/jamadermatol.2021.4915. https://pmc.ncbi.nlm.nih.gov/articles/PMC9845064/
- **S5 [A]** Vasey B, Nagendran M, Campbell B, et al.; DECIDE-AI expert group. Reporting guideline for the early stage clinical evaluation of decision support systems driven by artificial intelligence: DECIDE-AI. *BMJ* 2022;377:e070904（2022-05-18）。doi:10.1136/bmj-2022-070904. https://www.bmj.com/content/377/bmj-2022-070904 。同時刊於 *Nat Med*（doi:10.1038/s41591-022-01772-9，https://www.nature.com/articles/s41591-022-01772-9 ，連結被導向登入頁，內容未讀取）。
- **S6 [A]** Liu X, Cruz Rivera S, Moher D, Calvert MJ, Denniston AK; SPIRIT-AI and CONSORT-AI Working Group. Reporting guidelines for clinical trial reports for interventions involving artificial intelligence: the CONSORT-AI extension. *BMJ* 2020;370:m3164. https://www.bmj.com/content/370/bmj.m3164.full.pdf （內容經搜尋摘要確認）
- **S7 [A]** Cruz Rivera S, Liu X, Chan A-W, Denniston AK, Calvert MJ; SPIRIT-AI and CONSORT-AI Working Group. Guidelines for clinical trial protocols for interventions involving artificial intelligence: the SPIRIT-AI extension. *BMJ* 2020;370:m3210（另刊 *Lancet Digit Health* 2020;2(10):e549–e560）。https://discovery.ucl.ac.uk/10111371/1/bmj.m3210.full.pdf （內容經搜尋摘要確認）
- **S8 [A]** Park SH, Suh CH, Lee JH, Kahn CE Jr, Moy L. Minimum Reporting Items for Clear Evaluation of Accuracy Reports of Large Language Models in Healthcare (MI-CLEAR-LLM). *Korean J Radiol* 2024;25(10):865–868. doi:10.3348/kjr.2024.0843. https://koreascience.kr/article/JAKO202431172125985.page?lang=en
- **S9 [A]** MI-CLEAR-LLM: 2025 Updates. *Korean J Radiol* 2025;26(12):1123–1132（Yonsei 機構典藏記錄）。https://ir.ymlib.yonsei.ac.kr/handle/22282913/210022?mode=full 。**DOI 與全文未驗證。**
- **S10 [A]** Gallifant J, et al.（通訊作者 Bitterman DS）. The TRIPOD-LLM reporting guideline for studies using large language models. *Nat Med* 2025;31(1):60–69. doi:10.1038/s41591-024-03425-5. https://pubmed.ncbi.nlm.nih.gov/39779929/
- **S11 [A]** Hernandez-Boussard T, et al. MINIMAR (MINimum Information for Medical AI Reporting). *JAMIA* 2020;27(12):2011–2015. doi:10.1093/jamia/ocaa088（完整作者名單未在本次搜尋中直接確認）。EQUATOR：https://www.equator-network.org/?p=18915
- **S12 [A]** Norgeot B, Quer G, Beaulieu-Jones BK, et al. Minimum information about clinical artificial intelligence modeling: the MI-CLAIM checklist. *Nat Med* 2020;26(9):1320–1324. doi:10.1038/s41591-020-1041-y. https://link.springer.com/article/10.1038/s41591-020-1041-y ；生成式模型更新提案 [D]：https://arxiv.org/abs/2403.02558v1
- **S13 [A/C]** Olczak J, et al. Presenting artificial intelligence, deep learning, and machine learning studies to clinicians and healthcare stakeholders: an introductory reference with a guideline and a Clinical AI Research (CAIR) checklist proposal. *Acta Orthop* 2021;92(5):513–525. doi:10.1080/17453674.2021.1918389. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8519529/ ；EQUATOR 收錄：https://www.equator-network.org/?p=21378
- **S14 [B]** Kolbinger FR, et al. Reporting guidelines in medical artificial intelligence: a systematic review and meta-analysis. *Commun Med* 2024;4:71. https://www.nature.com/articles/s43856-024-00492-0.pdf （內容經搜尋摘要確認）
- **S15 [B]** Koçak B, Köse F, Keleş A, Şendur A, Meşe İ, Karagülle M. Adherence to the Checklist for Artificial Intelligence in Medical Imaging (CLAIM): an umbrella review with a comprehensive two-level analysis. *Diagn Interv Radiol* 2025;31(5):440–455. doi:10.4274/dir.2025.243182. https://dirjournal.org/articles/doi/dir.2025.243182
- **S16 [B]** Nagendran M, et al. Artificial intelligence versus clinicians: systematic review of design, reporting standards, and claims of deep learning studies. *BMJ* 2020（數字取自搜尋摘要；**DOI／URL 未直接驗證**）。
- **S17 [B]** Daneshjou R, et al. Lack of transparency and potential bias in artificial intelligence data sets and algorithms: a scoping review. *JAMA Dermatol* 2021;157(11). doi:10.1001/jamadermatol.2021.3129. https://pmc.ncbi.nlm.nih.gov/articles/PMC9379852 （數字經搜尋摘要／二手報導確認，PMC 全文未直接讀取）

---

## Q1. 各指引的適用範圍、研究類型，以及對本專案「現在 vs 未來」的適用性

### Takeaway
本專案目前在做的是**影像預測模型的開發加上內部驗證**（patient-level 交叉驗證）。這類研究的主要指引是 **TRIPOD+AI**（研究設計主軸）和 **CLAIM 2024**（醫學影像 AI 細節），**CLEAR Derm** 則是皮膚影像領域的補充。之後若有預先指定的 held-out 或外部測試集，而且研究問題是「診斷準確度」，就要加上 **STARD-AI**。**DECIDE-AI** 只在模型輸出實際影響照護決策（live、小規模臨床評估）時才適用；它的原文明確排除 shadow mode。CONSORT-AI/SPIRIT-AI 只適用於 RCT，目前不適用。MI-CLEAR-LLM 與 TRIPOD-LLM 只在流程用到 LLM 時才適用，目前不適用。

### Cited Findings

**TRIPOD+AI (S1)**
- 適用於「開發」預測模型、「評估（驗證）」模型表現，或兩者兼有的研究，不論用迴歸或任何機器學習方法；每個項目都標註 D（只用於開發）、E（只用於評估）或 D;E（兩者）。【研究證據】 — [S1 BMJ](https://www.bmj.com/content/385/bmj-2023-078378)；[S1 PDF](https://ora.ox.ac.uk/objects/uuid:414e5fb8-5575-4b67-b94d-a0833a7cc58a/files/smp48sf448)
- 共 27 個主項目，含子項目合計 52 項：標題 1、摘要 2、引言 3–4、方法 5–17、開放科學 18、病人與公眾參與（PPI）19、結果 20–24、討論 25–27；另有 TRIPOD+AI for Abstracts checklist。 — [S1 PDF](https://ora.ox.ac.uk/objects/uuid:414e5fb8-5575-4b67-b94d-a0833a7cc58a/files/smp48sf448)
- TRIPOD+AI 取代 TRIPOD 2015（「should no longer be used」）；特別強調公平性（fairness）；新增開放科學（18a–f）與 PPI（19）。若資料有群聚結構（多院區），應另參考 TRIPOD-Cluster。 — [S1 PDF](https://ora.ox.ac.uk/objects/uuid:414e5fb8-5575-4b67-b94d-a0833a7cc58a/files/smp48sf448)
- BMJ 2024-04-16 刊出，2024-04-18 有一則更正。 — [S1 BMJ](https://www.bmj.com/content/385/bmj-2023-078378)

**CLAIM 2024 (S2)**
- 用於醫學影像 AI 研究（分類、偵測、分割等），2024 版共 44 項（2020 版為 42 項：刪除舊 item 11「資料字典」，新增 item 13「影像擷取協定」）。每項可勾 Yes / No / N/A，並鼓勵註明頁碼與行號。Delphi 小組招募 73 人，72 人完成兩輪。 — [S2 PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11304031)。2020 版 42 項的數字取自搜尋摘要，S2 頁面本身沒有寫出。
- 用詞調整：以「reference standard」取代 ground truth／gold standard；以「internal testing / external testing」取代「validation」。不涵蓋 radiomics／pathomics 這類影像生物標記研究。 — [S2 PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11304031)
- CLAIM 雖然出自放射科期刊，但項目屬於一般「影像 AI」通則（資料、reference standard、partition、模型、訓練、評估）。皮膚與手臂照片沒有 DICOM 擷取協定，item 13 要改寫成相機與拍攝條件。【推論】

**STARD-AI (S3)，確認為 2025 年刊出**
- 2025-09-15 刊於 *Nature Medicine* 線上版（PMID 40954311）。 — [S3 EQUATOR](https://www.equator-network.org/reporting-guidelines/the-stard-ai-reporting-guideline-for-diagnostic-accuracy-studies-using-artificial-intelligence/)
- 共 40 個編號項目：在 STARD 2015 基礎上修改 4 項（1、3、7、25），新增 14 項 AI 專屬項目（6、11、12、13、14、15b、15d、23、28、29、35、39、40a、40b），合計「18 new or modified items」。附有 STARD for Abstracts。 — [S3 accepted manuscript](https://pure-oai.bham.ac.uk/ws/files/282528526/STARD_AI_accepted.pdf)
- Delphi 第一輪邀請 528 人、240 人回應、209 人完成；第二輪 203 人回應、143 人完成；2021-11-01 召開 22 人的共識會議。 — [S3 accepted manuscript](https://pure-oai.bham.ac.uk/ws/files/282528526/STARD_AI_accepted.pdf)
- 範圍：AI「診斷準確度」研究，涵蓋影像、病理、EHR、多模態，也包含輸出為診斷分類的 LLM。原文明確區分：若研究重點是**多變項預測模型的開發或評估**，TRIPOD+AI 或 TRIPOD-LLM 更合適；影像 AI 模型的開發與驗證可考慮 CLAIM；「診斷準確度是主要焦點」時才用 STARD-AI。作者可同時參考多份指引，但以研究主目的選定主指引。 — [S3 accepted manuscript](https://pure-oai.bham.ac.uk/ws/files/282528526/STARD_AI_accepted.pdf)
- STARD-AI 強調的資料處理項目包括：資料層與受試者層的納入／排除條件（7）、資料來源（11）、標註（12）、擷取裝置與軟體版本（13）、擷取協定與前處理（14）、資料切分（15b）、測試集特性（25）、資料是否代表目標族群（28）；開放科學方面有商業利益（39）、資料與程式碼（40a）、輸出可稽核（40b）。 — [S3 accepted manuscript](https://pure-oai.bham.ac.uk/ws/files/282528526/STARD_AI_accepted.pdf)

**CLEAR Derm (S4)**
- 皮膚科影像 AI 報告與評估清單，共 25 項，分 4 個領域：Data（1–15）、Technique（16–19）、Technical Assessment（20–23）、Application（24–25）。由 ISIC AI 工作小組 19 位成員以兩輪電子討論形成共識，2021-06-07 於 ISIC 年會通過。 — [S4 PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC9845064/)
- 內容包含影像偽影（品質、筆跡、部位）、膚色評估方法及其限制、多廠牌影像、OOD（分布外）影像處理，以及以病理確認惡性標籤。 — [S4 PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC9845064/)
- 本專案影像是手臂／手部皮膚的照片，屬於「image-based AI in dermatology」的近鄰。惡性病理確認（item 18）不適用，但膚色、拍攝偽影、多裝置、OOD 等項目直接適用。【推論】

**DECIDE-AI (S5)**
- 適用於 AI 決策支援系統的**早期、小規模、live 臨床評估**，也就是 AI 建議實際影響病人照護的情境。重點放在小規模臨床效用、安全、人因，以及為大型試驗做準備。不限研究設計，作者類比 IDEAL 2a/2b 階段。 — [S5 BMJ](https://www.bmj.com/content/377/bmj-2022-070904)
- 共 17 個 AI 專屬項目（含 28 個子項目，以阿拉伯數字編號）加上 10 個通用項目（以羅馬數字 I–X 編號）。專家群為 18 國 151 人；Delphi 第一輪 123 人、第二輪 138 人完成；共識會議 16 人。 — [S5 BMJ](https://www.bmj.com/content/377/bmj-2022-070904)
- **明確不涵蓋**：前臨床、in silico、離線或「shadow mode」評估（決策不影響病人）；大型比較效能試驗；方法學品質與偏誤風險；法規要求。 — [S5 BMJ](https://www.bmj.com/content/377/bmj-2022-070904)

**CONSORT-AI / SPIRIT-AI (S6, S7)**
- CONSORT-AI 在 CONSORT 2010 之外新增 14 項，用於 AI 介入的 RCT 報告；SPIRIT-AI 在 SPIRIT 2013 之外新增 15 項，用於 RCT 試驗計畫書。29 個候選項目中，26 項同時適用兩者，3 項只適用 CONSORT-AI。 — [S6](https://www.bmj.com/content/370/bmj.m3164.full.pdf)；[S7](https://discovery.ucl.ac.uk/10111371/1/bmj.m3210.full.pdf)（經搜尋摘要確認）

**MI-CLEAR-LLM (S8, S9)**
- 2024 版共 6 項，用於 LLM 在醫療領域的「準確度評估」報告，涵蓋 LLM 識別、隨機性處理、prompt 細節、測試資料等。 — [S8 KoreaScience](https://koreascience.kr/article/JAKO202431172125985.page?lang=en)
- **有 2025 更新**：「MI-CLEAR-LLM: 2025 Updates」，*Korean J Radiol* 2025;26(12):1123–1132。依機構記錄摘要，更新版仍聚焦 LLM 的規格、存取、調整與應用方式，並加入文獻中的報告範例。 — [S9 Yonsei](https://ir.ymlib.yonsei.ac.kr/handle/22282913/210022?mode=full)；具體項目變動**未找到可靠證據**（沒有讀到全文）。

**TRIPOD-LLM (S10)**
- TRIPOD+AI 針對 LLM 的延伸版，2025 年 1 月刊於 *Nat Med*，定位為 living document，並提供互動網站產生 checklist。項目數有衝突：PubMed 摘要寫 19 個主項目、50 個子項目，Utrecht 典藏記錄寫 14 個主項目、32 個子項目。 — [S10 PubMed](https://pubmed.ncbi.nlm.nih.gov/39779929/)；衝突來源：[Utrecht 典藏](https://dspace.library.uu.nl/handle/1874/460546)（可能是不同版本，未解決）

**MINIMAR、MI-CLAIM、CAIR／CLEF**
- MINIMAR（JAMIA 2020）界定理解預測目標、目標族群、隱藏偏誤與可推廣性所需的最少資訊。 — [S11 EQUATOR](https://www.equator-network.org/?p=18915)
- MI-CLAIM（Nat Med 2020）以六個步驟（研究設計、資料與最佳化、模型表現、模型檢視、可重現性等）列出臨床 AI 建模的最少資訊；2024 年有生成式模型更新提案（arXiv 預印本 [D]）。 — [S12](https://link.springer.com/article/10.1038/s41591-020-1041-y)；[arXiv 2403.02558](https://arxiv.org/abs/2403.02558v1)
- CAIR（Acta Orthop 2021）是給臨床讀者的 Clinical AI Research checklist 提案，附效能指標指引；作者自述是「進入更廣泛共識程序前」的提案，因此共識強度低於 TRIPOD+AI／CLAIM。已收錄於 EQUATOR。 — [S13 PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8519529/)；[EQUATOR](https://www.equator-network.org/?p=21378)
- 「CLEF」作為醫療 AI 報告指引：**未找到可靠證據**（搜尋沒有對應結果，可能與 CAIR 混淆）。

**EQUATOR Network**
- EQUATOR 將 STARD-AI 歸類為「Artificial intelligence/Machine learning studies」及「Diagnostic and prognostic studies」，並連結 TRIPOD+AI。 — [S3 EQUATOR](https://www.equator-network.org/reporting-guidelines/the-stard-ai-reporting-guideline-for-diagnostic-accuracy-studies-using-artificial-intelligence/)
- 系統性回顧（2024）整理出 26 份醫療 AI 報告指引，發佈者包括學術機構、政府、期刊與企業。其中 12 份針對特定醫學領域，20 份針對前臨床或轉譯研究而非前瞻臨床評估。 — [S14 Commun Med](https://www.nature.com/articles/s43856-024-00492-0.pdf)

### 適用性總表【推論】

| 指引 | 研究類型 | 對本專案現在 | 未來 |
|---|---|---|---|
| TRIPOD+AI | 預測模型開發／評估（D/E） | **主要指引**（現在是 D + 內部 CV 評估） | 外部測試時用 E 項目 |
| CLAIM 2024 | 醫學影像 AI 開發／測試 | **主要指引**（影像細節） | 持續適用 |
| CLEAR Derm | 皮膚影像 AI | **領域補充**（膚色、偽影、OOD） | 持續適用 |
| STARD-AI | AI 診斷準確度 | 部分（若把 held-out test 定位為準確度研究） | 預先指定的外部或前瞻測試集時成為主指引 |
| DECIDE-AI | 早期 live 臨床評估 | 不適用（shadow mode 被明確排除） | 若院內護理師實際看到並使用模型建議，即適用 |
| CONSORT-AI / SPIRIT-AI | RCT 報告／計畫書 | 不適用 | 僅在做隨機試驗時 |
| MI-CLEAR-LLM / TRIPOD-LLM | LLM 研究 | 不適用（流程沒有 LLM） | 若加入 LLM（例如 LINE 對話生成、報告撰寫）就適用 |
| MINIMAR / MI-CLAIM / CAIR | 一般性最少資訊 | 可作交叉檢查，不需另外填寫 | — |

### Inferences
- 【推論】LINE 回覆若把模型結果顯示給民眾，就不完全是「shadow」。但 DECIDE-AI 的情境是臨床決策支援（使用者多為醫療人員），民眾自我拍照取得回覆屬於邊界情況。目前「第二模型 shadow 比對」本身確定在 DECIDE-AI 排除範圍內；第一模型對民眾的回覆屬於有使用者暴露的 live 輸出，建議至少記錄 DECIDE-AI 10a（暴露次數）、11（修改紀錄）、13（錯誤）所需欄位，供未來使用。
- 【推論】目前樣本約 120 張、14 位病人、3-fold CV、沒有外部測試。以 STARD-AI 或 TRIPOD+AI 的 E 項目來看，「外部評估」只能如實寫「未做」（CLAIM 33 要求說明理由）。

### Gaps
- 沒有讀到 STARD-AI 正式版的卷期頁；31(10):3283–3289 只來自搜尋摘要。
- 沒有取得 MI-CLEAR-LLM 2025 更新的全文與 DOI，也沒有取得 TRIPOD-LLM 的最終 checklist（項目數衝突未解決）。
- 沒有直接讀取 MINIMAR、MI-CLAIM 的逐項清單（只有摘要層級資訊）。
- EQUATOR 的 DECIDE-AI 頁面在預期 URL 回傳 404；沒有統計 EQUATOR 目前收錄的 AI 指引總數。

---

## Q2. 逐項 checklist 與本平台分類（TRIPOD+AI、CLAIM 2024、STARD-AI、CLEAR Derm、DECIDE-AI）

### Takeaway
各指引的項目大致分成三種情況：
- **平台大致已經能產出**：資料切分、效能指標與信賴區間、混淆矩陣、錯誤分析、同意狀態。
- **可以自動記錄但目前缺少**：裝置與 EXIF、拍攝日期區間、軟體版本、權重雜湊、所有 run（包含失敗的）、閾值選擇程序、流程圖計數、各 partition 的人口學與膚色、標註者與標註時間、Wilson/bootstrap 方法參數。
- **需要人工撰寫**：倫理、資金、利益衝突、PPI、預期用途、限制、預註冊。

最大的結構性缺口是三件事：單一標註者無法回報 inter-rater 變異（CLAIM 18）；沒有膚色欄位（CLEAR Derm 8、TRIPOD+AI 公平性項目）；沒有外部測試（CLAIM 33、STARD-AI 29）。

### Cited Findings
以下各表的「項目」欄是官方 checklist 的**簡短改寫**（非原文）；「分類」欄是本筆記的【推論】。分類代碼：
- **已**：已記錄（依專案描述推定）
- **部分**：部分記錄
- **未**：未記錄但可自動記錄
- **人**：需人工補充
- **N/A**：目前不適用

#### 2a. TRIPOD+AI（27 個主項目、52 個子項目）— 項目來源 [S1 PDF Table 2](https://ora.ox.ac.uk/objects/uuid:414e5fb8-5575-4b67-b94d-a0833a7cc58a/files/smp48sf448)

| # | D/E | 項目（改寫） | 分類 | 說明 |
|---|---|---|---|---|
| 1 | D;E | 標題標明是開發或評估預測模型，以及目標族群與結果 | 人 | |
| 2 | D;E | 摘要（另見 Abstracts checklist） | 人 | |
| 3a | D;E | 醫療情境（診斷或預後）、理由、既有模型 | 人 | |
| 3b | D;E | 目標族群、在照護路徑中的用途、預期使用者 | 人 | 可由 model card 預填 |
| 3c | D;E | 已知的社會人口群體健康不平等 | 人 | |
| 4 | D;E | 研究目的：開發、驗證或兩者 | 人 | |
| 5a | D;E | 開發與評估資料各自的來源、理由、代表性 | 部分 | 來源（E-Da/LINE）已有；代表性需人工 |
| 5b | D;E | 資料收集的起訖日期 | 未 | 需要拍攝與收件日期的區間 |
| 6a | D;E | 研究場域、中心數與地點 | 部分 | site 欄位 |
| 6b | D;E | 受試者納入條件 | 未/人 | 需要 eligibility log |
| 6c | D;E | 治療（例如留置針與處置）如何處理 | 人/N/A | |
| 7 | D;E | 資料前處理與品質檢查，以及在各族群間是否一致 | 部分 | 品質閘門已有；缺各族群比較 |
| 8a | D;E | 結果定義、時間範圍、評估方式與一致性 | 部分 | 分期規則存在，版本未記錄 |
| 8b | D;E | 主觀評估者的資格與人口特徵 | 未 | annotator 資料表 |
| 8c | D;E | 結果評估的盲化 | 未 | 標註時是否看得到模型建議 |
| 9a | D;E | 初始預測因子的選擇（影像模型即為輸入定義） | 人 | |
| 9b | D;E | 預測因子的定義與測量方式（影像擷取） | 未 | 裝置、EXIF |
| 9c | D;E | 預測因子評估者資格（拍攝者） | 未 | photographer_type |
| 10 | D;E | 樣本數如何決定，以及是否足夠 | 人 | |
| 11 | D;E | 缺失資料處理，以及排除資料的原因 | 未 | 排除原因代碼 |
| 12a | D | 資料用途與切分方式 | 已 | patient-level SGKF；需確認 seed 有存 |
| 12b | D | 預測因子處理（resize、正規化） | 部分 | 前處理雜湊 |
| 12c | D | 模型類型、建模步驟、超參數調整、內部驗證 | 部分 | 需記錄所有 run |
| 12d | D | 跨群聚（醫院）異質性 | 未 | 依 source 分層的指標 |
| 12e | D;E | 效能指標與圖表（含校準、臨床效用） | 部分 | 缺校準 |
| 12f | E | 模型更新（重新校準） | N/A | |
| 12g | E | 評估時預測值如何計算（程式、API） | 已/部分 | 推論引擎版本 |
| 13 | D;E | class imbalance 處理方式 | 未 | 訓練設定 JSON |
| 14 | D;E | 公平性處理方法與理由 | 人/未 | 需要子群欄位 |
| 15 | D | 模型輸出形式，以及閾值如何決定 | 未 | threshold_selection 表 |
| 16 | D;E | 開發與評估資料的差異 | 未 | 外部模型匯入時尤其需要 |
| 17 | D;E | IRB 或倫理委員會、知情同意或豁免 | 部分/人 | 同意紀錄已有；IRB 字號需人工 |
| 18a | D;E | 資金來源 | 人 | |
| 18b | D;E | 利益衝突 | 人 | |
| 18c | D;E | 計畫書在哪裡取得 | 人 | |
| 18d | D;E | 註冊資訊 | 人 | |
| 18e | D;E | 資料可取得性 | 人 | |
| 18f | D;E | 分析程式碼可取得性 | 部分 | git commit hash |
| 19 | D;E | 病人與公眾參與 | 人 | |
| 20a | D;E | 受試者流程（含有／無結果的人數），建議用流程圖 | 未 | 流程計數 |
| 20b | D;E | 整體與各來源特徵、缺失量、各族群差異 | 未 | |
| 20c | E | 評估資料與開發資料的分布比較 | 未 | |
| 21 | D;E | 各分析（開發、調參、評估）的人數與事件數 | 部分 | 各 fold 計數 |
| 22 | D | 完整模型（程式碼、物件）以及取用限制 | 部分 | 權重雜湊、授權 |
| 23a | D;E | 效能估計與 CI，包括子群 | 部分 | 有 CI；缺子群 |
| 23b | D;E | 跨群聚異質性結果 | 未 | |
| 24 | E | 模型更新結果 | N/A | |
| 25 | D;E | 整體詮釋，包含公平性 | 人 | |
| 26 | D;E | 限制：樣本、過擬合、缺失、可推廣性 | 人 | |
| 27a | D | 實作時如何處理品質不佳或缺失的輸入 | 已/部分 | 品質閘門與拒收紀錄 |
| 27b | D | 使用者互動方式與所需專業程度 | 人 | |
| 27c | D;E | 未來研究方向、可應用性 | 人 | |

#### 2b. CLAIM 2024（44 項）— 項目來源 [S2 PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11304031)

| # | 項目（改寫） | 分類 | 說明 |
|---|---|---|---|
| 1 | 標題或摘要標明 AI 方法 | 人 | |
| 2 | 結構化摘要，含公開可取得性 | 人 | |
| 3 | 背景，以及 AI 的預期角色 | 人 | |
| 4 | 預先設定的目的與假說 | 人/未 | 可建立 analysis 預註冊表 |
| 5 | 前瞻或回溯 | 人 | E-Da 為回溯；LINE 為前瞻收集 |
| 6 | 研究目標、預期用途、預測類型 | 人 | |
| 7 | 資料來源，以及與目標族群的契合度 | 部分 | |
| 8 | 納入／排除條件與病例如何找到 | 未 | eligibility log |
| 9 | 前處理步驟與軟體，達可重現程度 | 部分 | pipeline hash、版本 |
| 10 | 前處理中的子集選擇 | 未 | 品質閘門排除、裁切 |
| 11 | 去識別化與隱私法規遵循 | 部分/人 | EXIF 去除、假名化 |
| 12 | 缺失資料處理與偏誤 | 未 | |
| 13 | 影像擷取協定參數（2024 新增） | 未 | 相機型號、光源、距離 |
| 14 | reference standard 定義與標註指引 | 部分/人 | 分期規則需版本化 |
| 15 | reference standard 選擇理由與限制 | 人 | 檔名規則屬於代理標籤 |
| 16 | 標註者來源、人數、資格、訓練 | 未 | |
| 17 | 測試集標註程序、指示、軟體版本 | 未 | |
| 18 | inter-rater／intra-rater 變異的測量與處理 | 未（結構缺口） | 單一標註者，只能做 intra-rater 重標 |
| 19 | 切分方式與比例 | 已 | |
| 20 | 切分層級（病人或影像） | 已 | patient-level |
| 21 | 測試集大小如何決定 | 部分/人 | |
| 22 | 模型架構，達可重建程度 | 部分 | |
| 23 | 軟體、框架與版本 | 未 | 自動擷取 pip freeze |
| 24 | 參數初始化與遷移學習來源 | 部分 | 預訓練權重來源與雜湊 |
| 25 | 訓練程序、資料增強、停止條件、超參數 | 部分 | |
| 26 | 最終模型如何從候選中選出 | 未 | 必須保留所有 run |
| 27 | 集成方法的組成 | N/A/未 | |
| 28 | 指標，以及與既有模型比較 | 已/部分 | |
| 29 | 不確定性與檢定方法、統計軟體版本 | 部分 | Wilson/bootstrap 參數 |
| 30 | 對假設與初始條件的穩健性 | 未 | 多 seed 重跑 |
| 31 | 可解釋性方法與其驗證 | 部分 | 有 Grad-CAM；缺驗證 |
| 32 | 內部測試表現，以及與訓練表現的一致性 | 部分 | train vs val 指標 |
| 33 | 外部測試，或沒有做的理由 | 人（目前沒有外部測試） | |
| 34 | 臨床試驗註冊 | N/A | |
| 35 | 納入與排除的病人／影像數，建議流程圖 | 未 | 流程計數 |
| 36 | 各 partition 的人口學與臨床特徵 | 未 | |
| 37 | 各 partition 與子群的最終表現及不確定性 | 部分 | |
| 38 | 診斷估計值與 CI、校準、class imbalance | 部分 | 缺校準 |
| 39 | 錯誤分析：混淆矩陣與誤判案例 | 已 | error gallery |
| 40 | 限制 | 人 | |
| 41 | 實務意涵與轉譯障礙 | 人 | |
| 42 | 完整計畫書或技術細節位置 | 人 | |
| 43 | 軟體、模型、資料的取得方式與條件 | 人/部分 | |
| 44 | 資金與獨立性 | 人 | |

#### 2c. STARD-AI（40 個編號項目；* 新增、† 修改）— 項目來源 [S3 accepted manuscript Table 2](https://pure-oai.bham.ac.uk/ws/files/282528526/STARD_AI_accepted.pdf)

註：PDF 文字層的項目編號與內文錯位一行，以下編號依正文明列的「新增項目編號」及「資料處理項目對應」重新對齊；15c 與 15d 的內容對應屬【推論】，建議日後以 Supplementary Table 2 核對。

| # | 項目（改寫） | 分類 |
|---|---|---|
| 1† | 標題或摘要標明為 AI 診斷準確度研究，並報告至少一個準確度指標 | 人 |
| 2 | 結構化摘要（STARD for Abstracts） | 人 |
| 3† | 背景：預期用途、是否為新的 index test、如何整合進工作流程 | 人 |
| 4 | 目的與假說 | 人 |
| 5 | 前瞻或回溯 | 人 |
| 6* | 倫理委員會核准，或說明不需核准的理由 | 人 |
| 7† | 受試者層與資料層的納入與排除條件（依套用順序） | 未（eligibility log 含順序） |
| 8 | 潛在受試者如何被找到 | 部分（LINE 或醫院） |
| 9 | 找到受試者的地點與日期 | 未（日期區間） |
| 10 | 連續、隨機或便利樣本 | 人（LINE 屬於自選便利樣本） |
| 11* | 資料來源：常規收集、專為研究收集，或來自公開資料庫 | 部分 |
| 12* | 標註者是誰（經驗、背景）、如何標註（同一臨床情境或事後） | 未 |
| 13* | 擷取裝置（廠牌型號）與 index test 軟體版本 | 未（EXIF、版本） |
| 14* | 擷取協定與前處理，達可重現程度 | 部分 |
| 15a | index test 細節 | 部分 |
| 15b* | index test 開發過程：訓練、驗證、測試、外部評估及各自樣本數 | 部分 |
| 15c | index test 陽性閾值或類別的定義與理由，區分預先指定與探索性 | 未（threshold 表） |
| 15d* | 指定的終端使用者，以及所需專業程度 | 人 |
| 16a | reference standard 細節 | 部分/人 |
| 16b | reference standard 選擇理由 | 人 |
| 16c | reference standard 閾值或類別，區分預先指定與探索性 | 人/未（分期規則版本） |
| 17a | index test 判讀者是否看得到臨床資訊與 reference 結果 | 未/N/A（模型只吃影像，但需記錄） |
| 17b | reference 評估者是否看得到 index test 結果 | 未（標註時是否顯示模型建議） |
| 18 | 準確度估計與比較方法 | 部分 |
| 19 | 不確定（indeterminate）結果如何處理 | 未（品質不足或無法判定的代碼） |
| 20 | index 與 reference 的缺失資料處理 | 未 |
| 21 | 變異性分析，區分預先指定與探索性 | 未（analysis 預註冊表） |
| 22 | 預定樣本數與決定方式 | 人 |
| 23* | 錯誤分析、演算法偏誤與公平性評估 | 部分（error gallery 已有；缺子群） |
| 24 | 受試者流程圖 | 未（流程計數） |
| 25† | 訓練、驗證、測試集的人口學、臨床與技術特徵 | 未 |
| 26a | 有目標狀況者的嚴重度分布 | 部分（stage 1/2 分布） |
| 26b | 無目標狀況者的其他診斷分布 | 未（例如瘀青、過敏、紅疹等 negative 子類） |
| 27 | index test 與 reference 之間的時間間隔與介入 | 未（拍攝時間與分期時間） |
| 28* | 資料是否代表預期使用族群的目標狀況分布 | 人/未（盛行率對照） |
| 29* | 外部評估資料與訓練、驗證、測試集的差異 | N/A（目前）/未 |
| 30 | index test 結果與 reference 的交叉表 | 已（混淆矩陣） |
| 31 | 準確度估計與精確度（95% CI） | 已 |
| 32 | 執行 index test 或 reference 的不良事件 | 人/N/A |
| 33 | 限制 | 人 |
| 34 | 實務意涵與預期用途 | 人 |
| 35* | 倫理考量與公平性 | 人 |
| 36 | 註冊編號 | 人 |
| 37 | 計畫書取得位置 | 人 |
| 38 | 資金 | 人 |
| 39* | 商業利益 | 人 |
| 40a* | 資料與程式碼可取得性，以及再利用限制 | 人/部分 |
| 40b* | 輸出是否儲存、可稽核、可供評估 | 已/部分（逐張預測、快照；需不可變更） |

#### 2d. CLEAR Derm（25 項）— 項目來源 [S4 PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC9845064/)

| # | 領域 | 項目（改寫） | 分類 | 說明 |
|---|---|---|---|---|
| 1 | Data | 影像模態（臨床照、皮膚鏡等） | 未/人 | 手機照或相機照 |
| 2 | Data | 影像偽影（品質、筆跡、部位） | 部分 | 品質閘門；缺偽影標記（膠布、敷料、針頭、筆跡） |
| 3 | Data | 擷取技術細節 | 未 | EXIF、光源、距離 |
| 4 | Data | 前處理 | 部分 | |
| 5 | Data | 合成影像公開 | N/A | 若做增強或合成需記錄 |
| 6 | Data | 使用了哪些公開影像來源 | N/A/部分 | 外部模型的訓練資料 |
| 7 | Data | 病人地點、性別、族裔，以及取得方式 | 未 | |
| 8 | Data | 膚色評估方法與限制 | 未（結構缺口） | Fitzpatrick 或 Monk 加上評估者 |
| 9 | Data | 病人資訊或 metadata 造成的偏誤 | 人 | |
| 10 | Data | train/val/test 定義 | 已 | |
| 11 | Data | 各 partition 樣本數 | 已/部分 | |
| 12 | Data | 外部測試集 | 未做 | |
| 13 | Data | 多廠牌或多裝置影像 | 未 | 依 device 分層 |
| 14 | Data | 類別分布與不平衡處理 | 部分 | |
| 15 | Data | OOD 影像評估與處理 | 部分 | 品質閘門；缺「非手臂、非 IV 部位」偵測紀錄 |
| 16 | Technique | 標註方法描述與理由 | 部分/人 | 檔名規則或人工 |
| 17 | Technique | 使用公認診斷標籤與本體 | 人 | 指明採用的 phlebitis scale（例如 VIP 或 INS） |
| 18 | Technique | 惡性病灶以病理確認 | N/A | |
| 19 | Technique | 演算法開發細節，達可重現程度 | 部分 | |
| 20 | Tech. Assess. | 他人如何公開評估本演算法 | 人 | |
| 21 | Tech. Assess. | 效能指標的選擇理由 | 人 | |
| 22 | Tech. Assess. | 與專家、照護標準、既有演算法比較 | 未/人 | 外部模型匯入比較已有 |
| 23 | Tech. Assess. | 演算法偏誤評估 | 未 | 需子群欄位 |
| 24 | Application | 預期用途、使用者、目標狀況 | 人 | model card |
| 25 | Application | 對醫療團隊、病人、弱勢族群的影響 | 人 | |

#### 2e. DECIDE-AI（17 個 AI 專屬項目，以阿拉伯數字編號；10 個通用項目，以羅馬數字編號）— 項目來源 [S5 BMJ Table 2](https://www.bmj.com/content/bmj/377/bmj-2022-070904.full.pdf)。**全部屬於未來的 live 評估**，目前分類標為「未來」，並註明現在就能先準備的欄位。

| # | 項目（改寫） | 現在可先準備 |
|---|---|---|
| 1 | 標題：早期臨床評估 AI 決策支援 | 人 |
| I | 結構化摘要（用途、演算法、場域、病人與使用者數、安全、人因） | 人 |
| 2a | 目標病況、現行標準、目標病人族群 | 人 |
| 2b | 預期使用者、照護路徑整合、預期影響 | 人 |
| II | 研究目的 | 人 |
| III | 計畫書、註冊、倫理 | 人 |
| 3a | 病人招募與病人層、資料層納入條件，以及人數決定 | 未（eligibility log） |
| 3b | 使用者招募與人數 | 未 |
| 3c | 使用者對 AI 的熟悉與訓練 | 人 |
| 4a | AI 系統版本、演算法類型、訓練族群與前臨床表現 | 已/部分（model registry） |
| 4b | 輸入資料的取得、輸入流程、前處理、缺失或低品質處理 | 部分（品質閘門） |
| 4c | 輸出形式，以及如何呈現給使用者 | 未（回覆模板版本） |
| 5a | 評估場域 | 人 |
| 5b | 臨床流程、使用時機、最終決策由誰做出 | 人 |
| IV | 主要與次要結果 | 人 |
| 6a | 重大錯誤或故障的定義與辨識方式 | 未（incident log） |
| 6b | 病人安全風險的辨識與降低 | 人/未 |
| 7 | 人因方法與框架 | 人 |
| V | 統計方法與預先指定的子群分析 | 未（analysis 預註冊） |
| 8 | 倫理目標的方法，例如演算法公平性 | 人 |
| VI | 病人參與 | 人 |
| 9a | 病人基線特徵與輸入資料缺失 | 部分（使用統計：品質失敗率） |
| 9b | 使用者基線特徵 | 未 |
| 10a | 使用者暴露次數、使用次數、對預定實作的遵循 | 部分（receipts 使用統計） |
| 10b | 對臨床流程造成的改變 | 人 |
| VII | 預先指定結果，包括比較組 | 未來 |
| VIII | 子群差異 | 未 |
| 11 | 研究期間對 AI 系統或硬體的修改：時間、理由、前後結果 | 未（model deployment changelog） |
| 12 | 人機一致性：使用者與 AI 不一致的次數與原因，以及是否因 AI 改變判斷 | 未（記錄人類確認時的 accept/override 與原因） |
| 13a | 重大錯誤或故障的發生率、原因、可否修正 | 未 |
| 13b | 病人安全風險與傷害（含間接傷害） | 人/未 |
| 14a | 可用性評估 | 人 |
| 14b | 使用者學習曲線 | 未（使用者別、時間序列的一致率） |
| 15 | 結果是否支持預期用途 | 人 |
| 16 | 安全性概況與錯誤的意涵 | 人 |
| IX | 優點與限制 | 人 |
| 17 | 資料與程式碼可取得性 | 人 |
| X | 利益衝突與資金 | 人 |

### Inferences
- 【推論】各指引最常重疊的「可自動化」核心可以歸成 10 組，見 Q3 的欄位對照：資料來源與日期、納入／排除流程計數、裝置與擷取、前處理版本、標註來源與標註者、切分與 seed、模型與版本、閾值程序、逐張預測與指標 CI、子群（膚色）。
- 【推論】專案原則「人工確認模型建議」本身就是 DECIDE-AI 12（人機一致性）的資料來源。只要在確認時記錄 accept／override 與原因，未來即可直接產出。
- 【推論】E-Da 標籤來自檔名規則，在 STARD／CLAIM 的語言中屬於「reference standard 取自既有臨床紀錄，事後轉錄」（STARD-AI 12 要求說明是同一臨床情境還是事後標註）。這必須在報告中明確說明，並記錄規則版本。

### Gaps
- STARD-AI 的 15c、15d 與 17a/b 子項對齊是依 PDF 文字層推定；官方 Supplementary Table 2 沒有取得。
- DECIDE-AI 13a 的 (iv) 子項文字在 PDF 抽取時被截斷。
- 沒有對照本專案的實際 DB schema 逐欄確認「已記錄」的判斷，只依任務描述與一次 grep。

---

## Q3. 建議平台自動記錄的欄位（schema 草案）與對應指引項目

### Takeaway
建議新增或補強約 15 張表或欄位群。核心原則有四個：
- 每張影像有不可變的 provenance 與 label 歷史。
- 每次 run（含失敗與中止的）都有完整環境指紋。
- 評估結果可追溯到資料快照、切分和閾值選擇程序。
- 為公平性與 STARD／CLAIM 流程圖預留子群（膚色）和流程計數。

下列對應的項目編號引自 Q2 各表（來源 S1–S5）；欄位設計本身是【推論】。

### Cited Findings
- 指引明確要求的資料處理細節包括：資料層與受試者層的納入／排除條件、資料來源、標註者與方式、裝置與軟體版本、擷取協定與前處理、資料切分、測試集特性、代表性、輸出可稽核。 — [S3](https://pure-oai.bham.ac.uk/ws/files/282528526/STARD_AI_accepted.pdf)
- CLAIM 要求列出訓練與推論所用的軟體、框架與版本（23），說明最終模型如何從候選中選出（26），以及報告納入與排除數量並建議用流程圖（35）。 — [S2](https://pmc.ncbi.nlm.nih.gov/articles/PMC11304031)
- TRIPOD+AI 要求說明閾值如何決定（15）、資料收集日期（5b）、各分析的人數與事件數（21），以及子群效能與 CI（23a）。 — [S1](https://ora.ox.ac.uk/objects/uuid:414e5fb8-5575-4b67-b94d-a0833a7cc58a/files/smp48sf448)
- CLEAR Derm 要求膚色評估方法與限制（8）、多廠牌影像（13）、OOD 處理（15）、偽影（2）。 — [S4](https://pmc.ncbi.nlm.nih.gov/articles/PMC9845064/)
- DECIDE-AI 要求記錄研究期間的系統修改與時間（11）、人機一致性與使用者偏離 AI 的原因（12）、錯誤或故障的發生率與原因（13a），以及使用者暴露次數（10a）。 — [S5](https://www.bmj.com/content/bmj/377/bmj-2022-070904.full.pdf)

### 欄位草案【推論】（SQLite 風格；`→` 後為支持的指引項目）

**1. `image_provenance`**（每張影像一列，建立後不可修改）
- `image_id`、`sha256`、`patient_pseudo_id`（群組鍵）、`source`（E-Da／LINE／external_import）、`upload_channel`（batch_import／line_webhook／manual）、`received_at`
- `capture_datetime`（EXIF DateTimeOriginal，取不到則為 NULL 並標註）、`device_make`、`device_model`、`capture_software`、`width`、`height`、`exif_present`、`exif_stripped_at`
- `photographer_type`（nurse／patient／family／unknown）、`body_site`（左右、手背、前臂、肘窩）
- `catheter_day`（若取得，需人工）、`original_filename_hash`（不存原檔名明文）
- → TRIPOD+AI 5a/5b/6a/9b/9c；STARD-AI 9/11/13/14；CLAIM 7/13；CLEAR Derm 1/3/13

**2. `eligibility_log`**（每個納入／排除決策一列，可重建流程圖）
- `image_id`、`patient_pseudo_id`、`stage`（participant／data／quality／consent）、`rule_id`、`rule_version`、`decision`（include／exclude）、`reason_code`、`decided_by`（auto／user_id）、`decided_at`
- → STARD-AI 7†/24；TRIPOD+AI 6b/11/20a；CLAIM 8/10/35；DECIDE-AI 3a

**3. `quality_gate_result`**
- `image_id`、`gate_version`、`laplacian_var`、`dark_ratio`、`bright_ratio`、`thresholds_json`、`passed`、`override_by`、`override_reason`
- `artifact_flags`（膠布、敷料、筆跡、反光、針頭、非目標部位，可人工勾選）、`ood_flag`
- → CLEAR Derm 2/15；TRIPOD+AI 7/27a；STARD-AI 14/19；CLAIM 9/10；DECIDE-AI 4b/9a

**4. `label_event`**（版本化，只追加不覆寫）
- `label_id`、`image_id`、`task`（binary／ordinal／bbox）、`value`、`bbox_json`
- `label_scheme`（例如分期定義名稱與版本）、`label_source`（filename_rule／manual_review／imported）、`rule_id`、`rule_version`
- `annotator_id`、`annotator_role`、`annotator_experience_years`、`annotated_at`、`capture_to_label_interval`
- `model_suggestion_visible`（bool）、`model_suggestion_value`、`accepted_suggestion`（bool）、`override_reason`
- `indeterminate`（bool）、`is_current`、`supersedes_label_id`
- → STARD-AI 12*/16a–c/17b/19/27；CLAIM 14–18；TRIPOD+AI 8a–c；CLEAR Derm 16/17；DECIDE-AI 12/14b
- 建議另建 `relabel_round`：隔一段時間對約 20% 子集做盲化重標，以計算 intra-rater κ（CLAIM 18）。

**5. `consent_snapshot`**
- `consent_id`、`consent_text_version`、`granted_at`、`revoked_at`
- 每次 run 時另存 `status_at_use`，記錄於 run 與影像的對應表中
- → TRIPOD+AI 17；STARD-AI 6；CLAIM 11

**6. `subject_attributes`**（選填，需同意；用於子群與公平性）
- `patient_pseudo_id`、`age_band`、`sex`
- `skin_tone_scale`（Fitzpatrick I–VI 或 Monk 1–10）、`skin_tone_value`、`skin_tone_method`（self_report／rater／colorimetric_ITA）、`skin_tone_rater_id`
- `confounders`（刺青、毛髮、色素沉著）
- → CLEAR Derm 7/8/9/23；TRIPOD+AI 3c/7/14/20b/23a；STARD-AI 23*/25†；CLAIM 36/37

**7. `dataset_snapshot`**
- `snapshot_id`、`created_at`、`manifest_hash`（image_id 加 label_id 清單）、`counts_json`（依 class、source、device、skin tone）、`date_range_start`、`date_range_end`、`eligibility_rule_versions`
- → TRIPOD+AI 5b/20b/21；STARD-AI 9/24/25/26a；CLAIM 35/36

**8. `split_assignment`**
- `snapshot_id`、`strategy`（StratifiedGroupKFold）、`n_folds`、`seed`、`group_key`、`image_id`、`fold`、`role`（train／val／test／holdout）、`holdout_locked_at`、`leakage_check_passed`
- → CLAIM 19/20/21；TRIPOD+AI 12a；STARD-AI 15b*；CLEAR Derm 10/11

**9. `experiment_run`**（所有 run，包括失敗、中止、被取代的）
- 身分與狀態：`run_id`、`created_at`、`finished_at`、`status`（completed／failed／aborted／superseded）、`failure_message`、`purpose`（exploratory／confirmatory）
- 模型：`architecture`、`pretrained_source`、`pretrained_sha256`、`hyperparams_json`、`augmentation_json`、`class_imbalance_method`、`early_stopping_json`
- 環境指紋：`preprocess_pipeline_hash`、`code_git_commit`、`code_dirty`、`env_freeze`（torch、torchvision、ultralytics、timm、scikit-learn、opencv、numpy、python、CUDA、GPU、OS）、`seeds_json`
- 產出與選擇：`weights_sha256`、`selected_as_final`、`selection_reason`
- → CLAIM 22–27/30；TRIPOD+AI 12b/12c/13/18f/22；STARD-AI 13*/15a/15b；CLEAR Derm 19

**10. `threshold_selection`**
- `run_id`、`task`、`threshold`、`method`（Youden／fixed_FPR／prespecified）、`selected_on`（inner_val／fold_val）、`prespecified`（bool）、`selected_at`、`target_constraint`（例如 normal FPR ≤ x）
- → TRIPOD+AI 15；STARD-AI 15c；CLAIM 38

**11. `prediction`**（逐張，不可修改）
- `run_id`、`image_id`、`fold`、`role`、`probs_json`、`pred_label`、`threshold_used`、`gradcam_path`、`gradcam_sha256`、`inference_ms`、`quality_passed`
- → STARD-AI 30/31/40b*；CLAIM 37–39；TRIPOD+AI 23a

**12. `metric_result`**
- `run_id`、`subgroup_key`、`subgroup_value`、`metric`（balanced_acc／normal_FPR／macro_F1／ECE…）、`value`、`ci_low`、`ci_high`、`ci_method`（Wilson／bootstrap）、`bootstrap_B`、`bootstrap_seed`、`n`
- → TRIPOD+AI 12e/23a/23b；STARD-AI 18/31；CLAIM 29/37/38；CLEAR Derm 21/23

**13. `analysis_plan`**（預註冊）
- `analysis_id`、`description`、`prespecified`、`registered_at`（必須早於結果產生）、`linked_run_ids`
- → STARD-AI 15c/16c/21（區分預先指定與探索性）；CLAIM 4；DECIDE-AI V/VIII

**14. `external_model_import`**
- `model_id`、`source_url_or_party`、`license`、`declared_training_data`、`declared_population`、`safetensors_sha256`、`imported_at`、`local_eval_run_ids`
- → STARD-AI 29*/39*；TRIPOD+AI 16/20c；CLEAR Derm 6/22

**15. 部署、shadow 與事件紀錄**
- `deployment_changelog`：`model_version`、`active_from`、`active_to`、`reason`、`approved_by` → DECIDE-AI 11、4a
- `shadow_log`：`image_id`、`primary_model_version`、`shadow_model_version`、`primary_output`、`shadow_output`、`agree`、`reply_template_version`、`ts` → DECIDE-AI 4c/10a/11/12（為未來準備）；STARD-AI 40b
- `incident_log`：`type`（misclassification_reported／system_error／harm_report）、`severity`、`cause`、`correctable`、`ts` → DECIDE-AI 6a/13a/16
- `usage_daily`（已存在：收件、同意率、品質失敗率、預測分布、撤回）→ DECIDE-AI 9a/10a

**16. `study_metadata`**（人工欄位，但由平台集中保存並匯出成 checklist 草稿）
- `irb_id`、`protocol_url`、`registration`、`funding`、`coi`、`ppi_statement`
- `intended_use`、`intended_users`、`out_of_scope`（「非臨床診斷」）
- `reference_standard_rationale`、`sample_size_rationale`、`limitations`
- → TRIPOD+AI 3a–4/10/17–19/25–27；STARD-AI 1–6/15d/22/33–39；CLAIM 1–6/15/40–44；CLEAR Derm 24/25；DECIDE-AI III/VI/X
- `model_card`：由 9、11、12、14 自動彙整，加上本表的人工欄位。

### Inferences
- 【推論】優先順序建議：
  1. 先做 `experiment_run` 全紀錄（含失敗的）、`label_event` 版本化、`eligibility_log` 流程計數，以及 EXIF 裝置與日期擷取。成本低，覆蓋 CLAIM、STARD-AI、TRIPOD 最多項目。
  2. 再做 `threshold_selection`、`analysis_plan` 預註冊，以及 `metric_result` 的子群。
  3. 膚色欄位與 intra-rater 重標需要人力與同意設計，排在最後。
- 【推論】EXIF 對 provenance 很有價值，但也是隱私風險（GPS）。建議只擷取白名單欄位（Make、Model、DateTimeOriginal、Software、影像尺寸），其餘丟棄，並記錄 `exif_stripped_at`。
- 【推論】單一標註者是無法用自動化解決的報告缺口（CLAIM 18、TRIPOD+AI 8b）。平台能做的是支援盲化重標（intra-rater）與未來第二標註者的流程。

### Gaps
- 沒有找到直接討論「本地 ML 平台應自動記錄哪些欄位以符合報告指引」的權威文獻；欄位設計全部是本筆記依 checklist 推導的【推論】。

---

## Q4. 遵循度證據與指引的限制（反證）

### Takeaway
已發表的影像 AI 研究平均只遵循約三分之二的 CLAIM 項目。缺失最多的正好是可以自動化的項目：缺失資料、樣本數、不確定性、流程、人口學、失敗分析。皮膚 AI 資料集只有約一成報告膚色。另一方面，醫療 AI 報告指引已多達 26 份以上，彼此重疊且共識強度不一；遵循 checklist 不等於方法學品質好。

### Cited Findings
- CLAIM 傘狀回顧：納入 33 篇回顧（1,458 筆研究評估）；研究層分析涵蓋 421 篇獨特研究，median CLAIM 分數 26，median compliance 68%，平均約三分之一的項目被省略。遵循率低於 50% 的有 11 項（依舊版 CLAIM 編號）：去識別化、缺失資料、樣本數、統計顯著性與不確定性、可解釋性、受試者流程、人口學、診斷準確度估計、失敗分析、註冊、計畫書取得。發表年份與期刊分位是獨立預測因子；CLAIM 發表後遵循率上升（P = 0.004）。85% 的回顧由多位評分者評估，但只有 11% 評估了評分者間信度。 — [S15 DIR 2025](https://dirjournal.org/articles/doi/dir.2025.243182) [B]
- 深度學習與臨床醫師比較的研究：81 篇中 58 篇偏誤風險高；29 個 TRIPOD 項目中有 12 項遵循率低於 50%；資料與程式碼分別有 95% 和 93% 無法取得。 — S16 Nagendran et al., BMJ 2020（數字來自搜尋摘要，URL 未驗證）[B]
- 皮膚 AI 範圍回顧（2015–2020，70 篇研究）：只有 14 篇（20.0%）描述族裔或種族，只有 7 篇（10.0%）提供膚色資訊；超過 100 萬張影像中只有約四分之一公開。 — [S17 PMC9379852](https://pmc.ncbi.nlm.nih.gov/articles/PMC9379852)（經搜尋摘要與二手報導確認）[B]
- 指引數量過多：系統性回顧找到 26 份醫療 AI 報告指引，廣度與共識嚴謹度差異大，多數針對前臨床或轉譯研究；只有少數 AI 研究完全遵循最佳實務；作者呼籲建立共通標準。 — [S14 Commun Med 2024](https://www.nature.com/articles/s43856-024-00492-0.pdf) [B]
- 指引自身的限制聲明：DECIDE-AI 明言「遵循本指引不應被解讀為方法學品質的指標」，報告指引只是最少報告建議，不是研究執行指引。 — [S5 BMJ](https://www.bmj.com/content/377/bmj-2022-070904) [A]。STARD-AI 也自稱是「minimum set of essential items」。 — [S3](https://pure-oai.bham.ac.uk/ws/files/282528526/STARD_AI_accepted.pdf) [A]
- 以 MINIMAR 和 MI-CLAIM 評估 29 篇出血性中風 AI 研究，整體遵循率分別約 47.6% 和 46.0%（搜尋摘要；原文 URL 未直接驗證）。 — 搜尋結果指向 SKKU 典藏 https://pure.skku.edu/en/publications/need-for-transparency-and-clinical-interpretability-in-hemorrhagi/ [C]（**未直接讀取**）
- LLM 研究對 MI-CLEAR-LLM 的遵循：基本 LLM 識別資訊報告尚可，隨機性、prompt、測試資料常常沒有報告（2025 年同刊的遵循度研究，經搜尋摘要）。 — [S9 相關記錄](https://ir.ymlib.yonsei.ac.kr/handle/22282913/210022?mode=full)（間接）[C]

### Inferences
- 【推論】最常缺漏的項目（缺失資料、流程、人口學、不確定性、失敗分析）幾乎都能由平台自動產生。這正好支持「平台自動記錄」的策略：自動化可以把本專案的報告完整度推到文獻平均（約 68%）以上。不過遵循度高不代表偏誤風險低，偏誤風險要另外用 PROBAST+AI／QUADAS-AI 等工具評估（不在本筆記範圍）。
- 【推論】為了避免被多份 checklist 拖累，建議只選一份主指引：開發與內部驗證階段用 TRIPOD+AI，CLAIM 2024 與 CLEAR Derm 當補充；用 Q3 的欄位一次滿足交集，不要為每份指引各維護一套資料。這與 STARD-AI「依主目的選定指引、可交叉參照」的建議一致（【慣例】，[S3](https://pure-oai.bham.ac.uk/ws/files/282528526/STARD_AI_accepted.pdf)）。

### Gaps
- 沒有找到 TRIPOD+AI（2024）或 STARD-AI（2025）發表後的遵循度研究；TRIPOD 的數據來自 2015 版時代的研究。
- 沒有找到針對 CLEAR Derm 整體遵循率的量化回顧；搜尋摘要提到一篇深色皮膚色素病灶回顧，以 CLEAR Derm 25 項評分且多項不足，但出處沒有驗證，因此不列入。
- 沒有找到專門討論靜脈炎或輸液部位影像 AI 的報告品質研究（未找到可靠證據）。
