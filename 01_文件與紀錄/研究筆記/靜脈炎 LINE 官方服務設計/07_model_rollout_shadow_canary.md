# 模型上線策略：影子模式（silent trial）、金絲雀、A/B 測試、回滾——健康相關 AI 與醫療聊天機器人的做法與倫理界線

> 研究日期：2026-10-30（部分查核延續至 2026-10-31）。所有來源存取日均為 2026-10-30～31。
> 專案背景：台灣研究原型（非臨床診斷）；民眾經 LINE 官方帳號上傳手臂/手部 IV 部位照片，系統回覆 normal / stage 1 / stage 2，信心低時回「需人工確認」。現有「影子模式」：回覆送出後，候選模型在背景分析同一張照片，只記錄比較、不回覆。
> 原則檢核基準：不自動訓練、不自動部署（換模型須人核准）、模型建議須人確認、外部模型須在專案資料上完整評估、不捏造標註或效能宣稱、不宣稱診斷。
> 證據分級：[A] 官方/監管/標準/報告指引；[B] 系統性回顧/頂級期刊；[C] 同儕審查；[D] 預印本；[E] 部落格/新聞/論壇（僅佐證）。
> 標記：**研究證據顯示** / **業界慣例** / **本報告推論**。「（未於本輪開啟原文驗證）」表示書目資訊來自既有知識或二手摘要，引用前需再核。

---

## Q1. 臨床 AI 的 silent trial / 影子評估：證據與官方指引

### Takeaway
研究證據顯示 silent trial（模型在真實前瞻資料上即時運行、但結果不給使用者看）能在不影響照護的情況下抓到資料漂移——Kwong 2022 的案例中模型 AUC 從 0.90 掉到 0.50，修正後才回到 0.85–0.91；但 2026 年的範圍回顧指出 silent trial 做法高度不一致、尚無正式指引。監管文件（GMLP、PCCP）都要求「先驗證、再上線、上線後監測」且變更須有預先定義的協定與人為控管，與本專案「影子模式＋人核准切換」方向一致。

### Cited Findings
- **研究證據顯示** Kwong JCC 等，"The silent trial – the bridge between bench-to-bedside clinical AI applications"，*Frontiers in Digital Health* 2022;4:929508，2022-08-16 出版，DOI 10.3389/fdgth.2022.929508，PMID 36052317。[C] — [Frontiers 全文](https://www.frontiersin.org/articles/10.3389/fdgth.2022.929508/full)；[DOAJ](https://doaj.org/article/0a018e50dd4b46928b30848f00f881e6)
  - 定義：silent trial 在前瞻病人上即時評估 AI，終端使用者對預測「盲」，預測不影響照護。
  - 案例：嬰兒阻塞性腎水腫預測模型，silent trial 2020-08～2020-12；初始模型在 silent trial 資料 AUC 0.90→0.50，原因為資料漂移（病人年齡、患側、影像格式改變）；修正後在兩個獨立 silent trial 資料集 AUC 0.85–0.91。
  - 另發現病人不了解 AI 會如何輔助照護，回饋到以病人為中心的介面設計。
  - 結論：silent trial 是模型開發與臨床試驗之間的橋樑，建議在全規模臨床試驗前納入。
- **研究證據顯示** Tikhomirov L, Semmler C, Prizant 等，"A scoping review of silent trials for medical artificial intelligence"，*Nature Health*，DOI 10.1038/s44360-025-00048-z（2026-02 發布）。二手報導稱篩選 891 篇、納入 75 篇（2015–2025），發現試驗設計、資料蒐集與結果指標差異極大，部分研究的指標缺乏臨床意義，且**目前無正式 silent trial 指引**；共同作者 McCradden 主持的 CANAIRI 計畫正在制定指引。[B，但本輪只讀到二手摘要；納入篇數來自 [E]] — [Adelaide University 新聞](https://adelaide.edu.au/about/news/2026/calls-for-global-guidelines-for-safer-ai-use-in-medicine--/)；[Newswise](https://www.newswise.com/articles/calls-for-global-guidelines-for-safer-ai-use-in-medicine)；[ownyourai 摘要 [E]](https://ownyourai.com/?p=43638)；[mivision [E]](https://mivision.com.au/?p=55174116)
- **[A] DECIDE-AI**（AI 決策支援系統早期臨床評估報告指引）：Vasey B 等，*Nat Med* 2022;28(5):924–933，DOI 10.1038/s41591-022-01772-9（勘誤 DOI 10.1038/s41591-022-01951-8）；同時刊於 *BMJ* 2022;377:e070904，DOI 10.1136/bmj-2022-070904。含 17 項 AI 特定報告項目（28 子項）＋10 項通用項目。 — [Oxford ORA](https://ora.ox.ac.uk/objects/uuid:f3d4d76c-cfc7-40dc-a5c3-4f3a460c5901)；[Bristol 研究資訊](https://research-information.bris.ac.uk/en/publications/reporting-guideline-for-the-early-stage-clinical-evaluation-of-de-2/)
- **[A] SPIRIT-AI / CONSORT-AI**（2020，AI 介入的臨床試驗計畫書與報告擴充）：Cruz Rivera S 等 *Nat Med* 2020;26:1351–1363（DOI 10.1038/s41591-020-1037-7）；Liu X 等 *Nat Med* 2020;26:1364–1374（DOI 10.1038/s41591-020-1034-x）。（未於本輪開啟原文驗證；DOI 引用前請再核） — [SPIRIT-AI DOI](https://doi.org/10.1038/s41591-020-1037-7)；[CONSORT-AI DOI](https://doi.org/10.1038/s41591-020-1034-x)
  - 本報告推論：SPIRIT-AI/CONSORT-AI 針對**隨機對照試驗**；本專案目前不做 RCT，較相關的是 DECIDE-AI（早期、小規模、真實環境評估）與 silent trial 文獻。
- **[A] FDA/Health Canada/MHRA GMLP 10 項指導原則（2021-10）**，2025-01 由 IMDRF 正式定稿為 **IMDRF/AIML WG/N88 FINAL:2025**〈Good machine learning practice for medical device development: Guiding principles〉；定稿版相對 2024-07 草案僅小幅修改（新增可重現結果的要求）。 — [FDA GMLP 頁面（2025-12-19 更新）](https://www.fda.gov/medical-devices/artificial-intelligence-enabled-medical-devices/good-machine-learning-practice-medical-device-development-guiding-principles)；[IMDRF N88 PDF](https://imdrf.org/sites/default/files/2025-02/IMDRF_AIML%20WG_GMLP_N88%20Final.pdf)；[RAPS 報導](https://www.raps.org/resource/imdrf-finalizes-good-machine-learning-practice-so.html)
  - 10 項原則的標題（依 2021 FDA 版，本輪 IMDRF PDF 下載逾時、未逐字核對定稿用語）：(1) 全生命週期運用跨領域專業；(2) 良好軟體工程與資安實務；(3) 臨床研究參與者與資料集代表目標族群；(4) 訓練集與測試集獨立；(5) 參考資料集基於最佳可得方法；(6) 模型設計配合可得資料並反映預期用途；(7) 著重「人－AI 團隊」表現；(8) 測試在臨床相關條件下證明效能；(9) 提供使用者清楚、必要的資訊；(10) 已部署模型受到效能監測，再訓練風險受到管理。
- **[A] FDA PCCP 定稿指引**："Marketing Submission Recommendations for a Predetermined Change Control Plan for Artificial Intelligence-Enabled Device Software Functions"，Docket FDA-2022-D-2628。PCCP 三要素：修改描述（description of modifications）、修改協定（modification protocol：如何開發、驗證、實施變更）、影響評估（impact assessment）。定稿範圍從 ML 擴及所有 AI-enabled 裝置；不得用於 Special 510(k)；指引不具拘束力。 — [FDA 指引頁](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/marketing-submission-recommendations-predetermined-change-control-plan-artificial-intelligence)；[Ropes & Gray 2024-12](https://ropesgray.com/en/insights/alerts/2024/12/fda-finalizes-guidance-on-predetermined-change-control-plans-for-ai-enabled-device)；[Foley 2025-01](https://www.foley.com/insights/publications/2025/01/fda-final-guidance-ai-device-software-predetermined-change-control-plan/)
  - **來源衝突**：律所報導定稿日期為 2024-12-03 或 12-04（彼此不一）；FDA 官方頁面本輪顯示 "Issue date: August 2025"（頁面內容更新 2025-08-18），可能為再版或頁面更新日期。引用時建議寫「2024 年 12 月定稿（FDA 頁面現列 2025 年 8 月版）」並以 FDA 頁面為準。
- **[A] Health Canada**〈Pre-market guidance for machine learning-enabled medical devices〉定稿 2025-02-05，涵蓋 GMLP、資料管理、測試、臨床驗證、透明度、上市後監測，並允許 PCCP；FDA、Health Canada、MHRA 另於 2023-10 共同發布 PCCP 5 項指導原則。 — [Health Canada](https://www.canada.ca/en/health-canada/services/drugs-health-products/medical-devices/application-information/guidance-documents/pre-market-guidance-machine-learning-enabled-medical-devices.html)；[BLG 2025-02 [E]](https://www.blg.com/en/insights/2025/02/health-canadas-evolving-regulatory-framework-for-machine-learning-enabled-medical-devices)；[Smart & Biggar [E]](https://smartbiggar.ca/insights/publication/medical-devices-updates-annual-performance-report-new-guiding-principles-for-pccps-for-machine-learning-enabled-medical-devices-and-regulatory-enrolment-processes)
- **[A] WHO**：《Ethics and governance of artificial intelligence for health》（2021-06）；《Ethics and governance of AI for health: Guidance on large multi-modal models》（2024-01-18，98 頁，>40 項建議，含大規模部署後獨立第三方稽核與影響評估、自動化偏誤風險）。本輪**未找到** 2025 年 WHO LMM 指引更新版的可靠證據。 — [WHO LMM 指引頁](https://www.who.int/publications-detail-redirect/9789240084759)；[WHO 新聞稿 2024-01-18](https://www.who.int/news/item/18-01-2024-who-releases-ai-ethics-and-governance-guidance-for-large-multi-modal-models)

### Inferences
- **本報告推論**：本專案的「影子模式」在概念上等同 Kwong 所稱 silent trial 的弱化版——差別在於本專案影子模型的預測**沒有即時的參考標準（ground truth）**，只有「與現行模型是否一致」。一致率不等於正確率，必須搭配人工審閱（見 Q4）。
- **本報告推論**：GMLP 原則 (4)(5)(8)(10) 與本專案原則直接對應：外部 safetensors 模型須在病人層級切分、獨立於訓練集的專案測試集上評估（原則 4、8）；單一標註者的參考標準屬弱參考標準（原則 5），任何效能宣稱都需註明；上線後監測（原則 10）。
- **本報告推論**：PCCP 的「修改協定」概念可借用為專案內部文件：在換模型**之前**就寫好「候選模型需通過哪些門檻、誰簽核、失敗如何回滾」，這與「不自動部署、人核准切換」相容——PCCP 本身並不要求自動部署，而是要求變更事先被定義與驗證。
- 本專案非醫療器材上市申請，上述監管文件為「最佳實務參考」，非法規義務；但若未來朝醫療器材發展（台灣 TFDA 有 AI/ML 醫療器材相關指引，本報告未檢索），應另行查核。

### Gaps
- IMDRF N88 PDF 本輪下載逾時，10 項原則定稿逐字用語未核對。
- Tikhomirov 等 *Nature Health* 範圍回顧的原文未開啟；「75 篇」為二手摘要數字。
- 未找到 MHRA 專門針對 silent/shadow deployment 的文件（MHRA AI Airlock 等未檢索）。
- 台灣 TFDA 對 AI/ML 醫材變更管理的指引未在本題範圍內檢索。

---

## Q2. 在健康情境對使用者做 A/B 測試的倫理

### Takeaway
把真實使用者隨機分派到不同模型、讓他們收到不同的健康相關判讀，屬於以人為對象、蒐集個人醫學資訊並系統性分析的研究——在台灣幾乎必然落入《人體研究法》第 4 條「人體研究」定義，原則上需事先經倫理審查委員會（IRB）審查；美國 Common Rule 也以「系統性調查、意在產生可概化知識」界定研究。Meyer 等 2019 顯示民眾常反對 A/B 實驗（即使兩組做法都可接受），Facebook 情緒感染研究則是以服務條款代替知情同意引發爭議的典型案例。本報告建議：本專案**不進行面向使用者的 A/B 測試**，模型比較一律在影子模式＋人工審閱中完成。

### Cited Findings
- **研究證據顯示** Meyer MN, Heck PR, Holtzman GS, Anderson SM, Cai W, Watts DJ, Chabris CF，"Objecting to experiments that compare two unobjectionable policies or treatments"，*PNAS* 2019;116(22):10723–10728（DOI 10.1073/pnas.1820701116）。16 項研究顯示：民眾常可接受某政策/治療全面實施，卻反對以 A/B 方式隨機分派——作者稱為「A/B effect」；自第 2 項研究起預先註冊。[B] — [PMC6561206](https://pmc.ncbi.nlm.nih.gov/articles/PMC6561206)
  - **爭議**：Data Colada 重新分析指出統計問題，稱修正後在其檢驗的 7 個情境中實驗厭惡消失；作者另回應 Mislavsky 等的批評，堅持 A/B effect 非假象。本輪未找到作者對 Data Colada 的回應。 — [Data Colada [E]](https://datacolada.org/?p=4489)；[PMC6883814（作者回應）](https://pmc.ncbi.nlm.nih.gov/articles/PMC6883814)
- **研究證據顯示（警示案例）** Kramer ADI, Guillory JE, Hancock JT，Facebook 情緒感染實驗，*PNAS* 2014（vol 111(24):8788–8790）。論文主張與 Facebook 資料使用政策一致、使用者註冊即構成知情同意；PNAS 主編 Inder Verma 發布 Editorial Expression of Concern，指出依 Common Rule，取得知情同意與允許退出為多數情況的最佳實務，Facebook 的資料蒐集可能未完全符合。批評者認為服務條款不能取代具體知情同意，且缺乏 IRB 審查。 — [PMC4115552](https://pmc.ncbi.nlm.nih.gov/articles/PMC4115552)；[Retraction Watch 2014-07-03 [E]](https://retractionwatch.com/2014/07/03/rapid-mood-swing-pnas-issues-expression-of-concern-for-controversial-facebook-study/)；[Harvard JOLT Digest [E]](https://jolt.law.harvard.edu/digest/facebooks-experiment-of-emotional-contagion-raises-concerns)
- **[A] 台灣《人體研究法》**（108-01-02 修正版）：
  - 第 4 條第 1 款：「人體研究」指從事取得、調查、分析、運用人體檢體或個人之生物行為、生理、心理、遺傳、醫學等有關資訊之研究。
  - 第 5 條第 1 項：研究主持人實施研究前，應擬定計畫，經倫理審查委員會審查通過始得為之；但屬主管機關公告得免審查之研究案件範圍者不在此限。
  - 第 8 條：審查分一般與簡易程序，得簡易審查之範圍以主管機關公告者為限。 — [全國法規資料庫 L0020176](https://law.moj.gov.tw/LawClass/LawAll.aspx?PCode=L0020176)；[中研院 IRB 函釋目錄](https://irb.sinica.edu.tw/pages/2274)
- **[A] 美國 Common Rule** 45 CFR 46.102：研究指「系統性調查（含研究發展、測試與評估），設計用以發展或貢獻可概化知識」。（未於本輪開啟原文驗證） — [eCFR 45 CFR 46](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-A/part-46)

### Inferences
- **本報告推論（何時變成需 IRB 的人體研究）**：
  1. 只要專案蒐集民眾 IV 部位照片並分析、用於評估模型（包括影子模式比較、日後納入訓練），就已在「取得、分析、運用個人醫學有關資訊」的範疇——**影子模式本身也可能需要 IRB**（或至少需經 IRB 判定是否免審），不只 A/B 測試。是否符合衛福部免審公告範圍須由 IRB 判定，不宜自行認定。
  2. 若把使用者**隨機分派**到不同模型（A/B）而讓兩組收到不同判讀，則多了「介入」成分：回覆內容可能影響使用者是否就醫，風險高於影子模式，應以一般程序審查思考，需明確知情同意（不能以 LINE 加好友或服務條款代替——Facebook 案例教訓）。
  3. 平衡點（equipoise）：只有在兩個模型都已通過相同離線門檻、且無證據顯示何者較佳時，隨機分派才有倫理正當性；若已知候選模型較差或未經評估，則隨機分派讓部分使用者暴露於已知較差服務，不符 equipoise。
- **本報告推論**：Meyer 的 A/B effect（即使有統計爭議）提示：即使兩組都「合理」，公開後民眾仍可能反感，對以 LINE 接觸大眾的研究原型而言是信任風險。影子模式（使用者只收到現行已核准模型的回覆）在倫理上明顯優於 A/B。
- **原則檢核**：不做面向使用者的 A/B → 符合「不自動部署」「人核准切換」；影子模式需在隱私告知/同意文件中揭露「照片可能由第二個研究模型背景分析」→ 符合不宣稱診斷且透明。

### Gaps
- 未取得衛福部「得免倫理審查委員會審查之人體研究案件範圍」公告全文（搜尋只得到投影片與函釋目錄），本報告無法判定本專案是否可免審——**須詢問合作醫院 IRB**。
- 未檢索《個人資料保護法》對健康照片（特種個資：病歷、醫療）的要求（可能由其他研究筆記涵蓋）。
- 未找到針對「醫療聊天機器人 A/B 測試」的專門倫理指引或案例研究。

---

## Q3. 金絲雀發布（canary）與漸進式交付：業界做法、與「不自動部署」的衝突、人為把關替代方案

### Takeaway
業界慣例（Google SRE）把金絲雀定義為「對服務的一部分做部分且限時的部署並評估」，以少數 SLI 指標與對照組比較、明顯較差時自動暫停並回滾；Google 甚至主張「部署應由電腦而非人執行」——這與本專案「不自動部署」直接衝突。本報告推論的替代方案是：**前進（換上新模型）一律人核准；後退（回到上一個已核准模型或回覆「需人工確認」）可以自動化**，因為後退只會回到已經人核准的狀態。

### Cited Findings
- **業界慣例 [E/A-業界文件]** Google SRE Workbook〈Canarying Releases〉：
  - 金絲雀是「a partial and time-limited deployment of a change in a service and its evaluation」，其餘為對照組；評估結果決定是否繼續推出。
  - 金絲雀規模宜小（錯誤預算衝擊與曝露比例成正比）但要有代表性；持續時間要夠長以看到代表性樣本；建議一次只跑一個金絲雀。
  - 指標宜少（約不超過十來個），優先使用使用者可見的 SLI（錯誤率、延遲），避免 CPU 等雜訊指標；以 SLO 等絕對量作為 guardrail，避免金絲雀與對照同時退化而沒被發現；指標須分開看金絲雀與對照，前後比較易受時段效應干擾。
  - 部署應依金絲雀 vs 對照錯誤率差異自動反應：明顯較差時暫停並回滾或升級給人處理。
  - 發布工程原則：可重現建置、自動化建置/測試/部署（"Deployments should be performed by computers, not humans"）、小變更、以 feature flag 分離變更速率。 — [Google SRE Workbook: Canarying Releases](https://sre.google/workbook/canarying-releases/)
- **[C] Breck 等 "The ML Test Score"**（IEEE Big Data 2017）：28 項可行測試與評分；主張訓練好的模型需要可除錯性、**回滾**與監測等生產實務。 — [Google Research pub46555](https://research.google/pubs/pub46555/)；[PDF](https://research.google.com/pubs/archive/aad9f93b86b7addfea4c419b9100c6cdd26cacea.pdf)

### Inferences
- **本報告推論：為何不能直接套用 percentage-traffic canary**
  1. 在本專案，金絲雀＝讓一部分真實民眾收到候選模型的判讀 → 這是「上線」且是隨機/準隨機分派（見 Q2），需 IRB 並違反「人核准才換模型」的精神（除非每一階段都人核准）。
  2. SRE 金絲雀的 guardrail 是**即時可觀測**的（錯誤率、延遲）；分類正確率需要人工標註、有標註延遲，無法在金絲雀期間即時判斷「新模型比較差」→ 自動擴大流量的依據不存在。
  3. 小流量下樣本更少：本專案流量本來就小，5% 金絲雀幾乎無統計資訊。
- **本報告推論：人為把關的階段式替代方案**（每一個「前進」箭頭都需人簽核並寫入稽核紀錄）
  - 階段 0｜離線評估：候選模型（含外部 safetensors）在凍結的專案測試集（病人層級切分）評估，產出報告；人審閱。
  - 階段 1｜影子模式（現有）：候選模型背景推論、只記錄；不影響回覆。
  - 階段 2｜「審閱者端金絲雀」（reviewer-facing canary）：候選模型的結果**只顯示給內部審閱者**（如研究護理人員），與現行模型並列、對模型身分盲化，用於累積人工標註；使用者仍只看到現行模型回覆。
  - 階段 3｜人核准切換：由專案負責人依預先寫好的門檻（Q4）簽核，把設定檔的 `active_model_id` 指向新模型；舊模型保持熱備（Q6）。
  - 不建議階段「x% 使用者收到新模型」。
- **本報告推論：自動化的允許範圍**
  - ✅ 可接受（推論）：**自動回滾到上一個已核准模型**或**自動降級為「需人工確認」固定回覆**（kill switch），觸發條件限於工程性 guardrail：推論錯誤/逾時率、模型檔雜湊不符、輸出不合法、預測分布極端異常（例如短時間內 >X% 都判同一類）。理由：後退只回到已人核准狀態、降低曝露，符合 SRE 自動回滾精神，又不違反「不自動部署新模型」。觸發後須通知負責人並記錄。
  - ❌ 不可接受：依指標自動擴大候選模型流量、自動晉升候選模型、自動以新資料再訓練。
  - ⚠️ 灰色地帶：自動回滾是否需事後人確認「維持回滾」——建議要（推論）。
- **原則檢核**：上述方案無自動訓練、無自動部署新模型；切換須人簽核；自動化只用於安全後退 → 符合。

### Gaps
- 未找到臨床 AI 領域明確討論「自動回滾是否可接受」的監管文件；FDA PCCP 原文中關於回滾/監測的具體段落本輪未讀到（FDA 頁面摘要未涵蓋）。
- 未檢索其他業界來源（如 Argo Rollouts、Flagger、Kayenta 文件）對 ML 模型金絲雀的細節。

---

## Q4. 何時從影子切換到上線：統計準則，及「現在（14 位病人）」vs「未來（~1,000 張、三類平衡）」

### Takeaway
研究證據顯示外部驗證所需樣本量通常是數百到上千（Riley 等 BMJ 2024 範例需 949 人／408 事件；常見經驗法則為至少 100–200 事件與非事件），且小樣本會產生寬信賴區間與誤導性結論。以本專案目前約 120 張、14 位病人（normal 僅 9 張），**任何「候選模型較好/不劣」的統計結論都不成立**；影子模式現階段只能用於工程驗證與蒐集「需人工審閱的分歧案例」。未來約 1,000 張、三類平衡時，可預先註冊不劣性門檻、以配對比較（McNemar）判斷，但仍受單一標註者與病人層級相關性限制。

### Cited Findings
- **研究證據顯示 [B]** Riley RD 等，"Evaluation of clinical prediction models (part 3): calculating the sample size required for an external validation study"，*BMJ* 2024;384:e074821（DOI 10.1136/bmj-2023-074821）：
  - 外部驗證樣本量應以「效能估計夠精確」為目標，分別計算 O/E、校準斜率、c statistic、淨效益所需樣本，取最大者。
  - 範例（盛行率 0.43、c=0.77）：O/E 需 423 人；校準斜率（CI 寬 0.3）需 **949 人（408 事件）**；c statistic（CI 寬 0.1）需 347 人。
  - 經驗法則（含 Collins 等 2016）：c statistic 與校準斜率至少 100 事件＋100 非事件、校準圖 200＋200；作者認為經驗法則忽略模型與情境，可能不足；100 人的樣本對校準結果「太小」；許多已發表的外部驗證研究（含機器學習模型）樣本太小。
  - 軟體：pmvalsampsize（Stata/R）。文章未討論群集（clustering）。 — [PMC11778934](https://pmc.ncbi.nlm.nih.gov/articles/PMC11778934/)
  - 注意：此文架構針對機率輸出的預測模型；本專案分數未校準，校準相關準則暫不適用，但「樣本太小→CI 太寬→結論誤導」的論點直接適用。
- **[C] Riley 等 Stat Med 2021**（二元結果外部驗證最小樣本量，DOI 10.1002/sim.9025）與 **Collins, Ogundimu, Altman Stat Med 2016**（外部驗證樣本量重抽樣研究）。（未於本輪開啟原文驗證；Collins 2016 經 Riley 2024 引用為經驗法則來源） — [Riley 2024 PMC（引用處）](https://pmc.ncbi.nlm.nih.gov/articles/PMC11778934/)
- **[C] 配對比例（McNemar）樣本量**：Connor RJ，"Sample size for testing differences in proportions for the paired-sample design"，*Biometrics* 1987;43(1):207–211。只有不一致配對（discordant pairs）攜帶差異資訊；所需配對數 N = [z_{α/2}·√p_d + z_β·√(p_d − δ²)]² / δ²，其中 p_d = p10 + p01（不一致比例）、δ = p10 − p01。不一致比例須由先導資料估計。（公式來自多個二手計算器頁面一致敘述；原文未取得） — [MetricGate 說明](https://metricgate.com/docs/sample-size-mcnemar-paired)；[R pwrss::power.exact.mcnemar 文件](https://rdrr.io/cran/pwrss/man/proportions.mcnemar.html)

#### 本報告計算（以上公式/Wilson 區間，Python 計算，非文獻數字）
| 情境 | 觀察 | 95% Wilson CI | CI 寬度 |
|---|---|---|---|
| normal 類 9 張中判對 8 | 0.889 | 0.565–0.980 | 0.415 |
| 14 位病人層級 12/14 | 0.857 | 0.601–0.960 | 0.359 |
| stage 2 類 24 張中判對 20 | 0.833 | 0.641–0.933 | 0.292 |
| 120 張中判對 108 | 0.900 | 0.833–0.942 | 0.109 |
| 未來每類 ~333 張，判對 300 | 0.901 | 0.864–0.929 | 0.064 |
| 1,000 張判對 900 | 0.900 | 0.880–0.917 | 0.037 |

- 「三法則」（0 事件時 95% 上界 ≈ 3/n）：若 120 張中嚴重錯誤（stage 2 被判 normal）為 0，真實率上界仍約 2.5%；1,000 張時約 0.3%。
- McNemar（α=0.05 雙尾、檢定力 80%，Connor 公式）所需**配對張數**：p10=0.10/p01=0.05（差 5 個百分點）→ 約 469；p10=0.08/p01=0.03 → 約 343；p10=0.06/p01=0.03 → 約 783；p10=0.15/p01=0.05 → 約 155。
- Cohen's kappa（三類、真實 κ≈0.80 的模擬，3,000 次）95% 區間：n=14 → 0.46–1.00；n=56 → 0.65–0.92；n=120 → 0.71–0.89；n=1,000 → 0.77–0.83。
- 上述皆假設照片獨立；實際上同一病人多張照片高度相關，**有效樣本量更接近病人數**（本報告推論），CI 會比表中更寬。

### Inferences
- **本報告推論：影子比較的關鍵統計觀念**
  1. **一致 ≠ 正確**：兩模型一致率高（或 kappa 高）只表示彼此相似，可能一起錯。
  2. **只需人工審閱分歧案例就能估計「準確率差」**：若兩模型預測相同，兩者同對或同錯，對準確率差無貢獻；準確率差 = (候選對而現行錯 − 現行對而候選錯) / N，只取決於分歧案例。這正是 McNemar 的結構。→ 實務：把所有影子分歧案例送人工標註（對模型身分盲化），即可做配對檢定。
  3. 但要估計**絕對**準確率（及各類敏感度），仍需對「一致案例」抽樣審閱。
  4. 不劣性框架：事先設定不劣界限 Δ（例如 5 個百分點；數值需由臨床共識決定，本報告不代定），以「準確率差的 95% CI 下界 > −Δ」為通過條件；不要用「p>0.05 所以沒差」當作等效。
  5. 子群：至少依來源（醫院收集 vs LINE 民眾自拍）、拍攝條件分別報告；任一子群表現明顯變差即不通過。
  6. 「需人工確認」比例本身是指標：候選模型若把低信心比例大幅降低，可能是過度自信而非變好（分數未校準時尤其要注意）。
- **現在（~120 張、14 位病人、單一標註者）能/不能下的結論**
  - ❌ 不能：宣稱候選模型「較準」或「不劣」；報告任何單一數字的準確率而不附寬 CI；做子群比較（normal 只有 9 張）。
  - ✅ 能：工程驗證（候選模型可載入、延遲、記憶體、無崩潰、輸出格式正確）；描述性比較（一致率、混淆矩陣、分歧案例清單），**明確標示為探索性**；把分歧案例送人工審閱以累積標註。
  - 切換決策若在此時發生，只能基於工程或治理理由（例如舊模型有已知錯誤），且文件須寫明「無統計證據支持效能較佳」。
- **未來（~1,000 張、三類平衡 ~333/類）**
  - 每類敏感度 CI 寬度約 ±3 個百分點；整體準確率 CI 寬度約 0.04；可偵測約 5 個百分點的配對差異（若不一致比例約 15%）。
  - 仍需：病人層級切分（避免同病人跨訓練/測試的資料洩漏）、≥2 名獨立標註者並報告標註者間一致性（GMLP 原則 5）、來源子群各自有足夠樣本、預先註冊門檻。
- **本報告推論：建議的「影子→上線」書面門檻（全部須人簽核）**
  1. 候選模型通過階段 0 離線評估（凍結測試集、病人層級切分），報告附 95% CI。
  2. 影子期至少累積預先設定的配對數（依上方 McNemar 計算；現階段資料量不可能達到 → 現階段不做效能型切換）與至少涵蓋一段時間（避免只看單一時段）。
  3. 所有分歧案例完成盲化人工標註。
  4. 準確率差 95% CI 下界 > −Δ；stage 2 敏感度不低於現行模型（安全優先）。
  5. 子群無明顯退化；「需人工確認」比例變化有合理解釋。
  6. 負責人簽核並記錄於稽核紀錄；切換後進入加強監測期（Q5）。
- **原則檢核**：無自動晉升；無自動訓練；不捏造效能（所有數字附 CI 與樣本數）；不做診斷宣稱 → 符合。

### Gaps
- Connor 1987 原文、Riley 2021 Stat Med、Collins 2016 原文未於本輪開啟。
- 未找到專門針對「影像分類器影子比較」的樣本量文獻；也未找到處理「同病人多張照片」群集效應的分類器驗證樣本量專文（Riley BMJ 2024 未討論群集）。
- 不劣界限 Δ 的臨床合理值無文獻依據，需專案臨床人員決定。

---

## Q5. 切換後的監測：資料漂移、預測分布漂移、標註延遲

### Takeaway
研究證據顯示臨床 AI 在真實部署後會因資料集漂移而失效（Epic 敗血症模型外部驗證 AUC 僅 0.63；密西根大學的敗血症警示模型於 2020-04 因疫情造成族群改變而停用），漂移來源可分為技術、族群/場域、行為三類。業界慣例以 PSI、KS 檢定等監測輸入與預測分布，但這些只是「觸發調查」的啟發式，不是效能證據；本專案因標註延遲，應以「預測分布＋需人工確認比例＋定期抽樣人工審閱」三者並行。

### Cited Findings
- **研究證據顯示 [C]** Finlayson SG, Subbaswamy A 等，"The Clinician and Dataset Shift in Artificial Intelligence"，*NEJM* 2021;385(3):283–286（Correspondence），DOI 10.1056/NEJMc2104626，PMID 34260843：資料集漂移＝訓練資料與模型實際使用資料不同；密西根大學醫院一個敗血症警示模型因 COVID-19 相關族群變化產生偽警示，於 2020-04 停用；將漂移原因分為技術變化、族群與場域變化、行為變化，並提供辨識與緩解檢核表；主張需警覺的臨床人員與 AI 治理團隊。 — [PubMed 34260843](https://www.pubmed.gov/34260843/)；[作者提供 PDF](https://sgfin.github.io/assets/dataset_shift/Finlayson_Dataset_Shift_NEJM.pdf)
- **研究證據顯示 [B]** Wong A 等，"External Validation of a Widely Implemented Proprietary Sepsis Prediction Model in Hospitalized Patients"，*JAMA Intern Med* 2021（DOI 10.1001/jamainternmed.2021.2626）：密西根醫學中心回溯性外部驗證，38,455 次住院（2018-12～2019-10）；住院層級 AUC 0.63（95% CI 0.62–0.64），敏感度 33%、特異度 83%、PPV 12%、NPV 95%；警示涵蓋 18% 住院病人，仍漏掉 67% 敗血症；遠低於 Epic 與 UCHealth 報告的 0.76–0.83。限制：單一學術醫學中心。（數字經多個二手來源一致；原文本輪未開啟） — [JAMA Netw 全文頁](https://jamanetwork.com/journals/jamainternalmedicine/fullarticle/2781313)；[Hospital Pharmacy Europe [E]](https://hospitalpharmacyeurope.com/news/infectious-disease/commonly-used-sepsis-model-fails-to-identify-over-two-thirds-of-patients-with-the-condition/)；[MedCity News [E]](https://medcitynews.com/2021/06/popular-sepsis-prediction-model-works-substantially-worse-than-claimed-researchers-find)
- **業界慣例 [E]** PSI（Population Stability Index）= Σ (實際% − 預期%) × ln(實際% / 預期%)；常用門檻 <0.1 穩定、0.1–0.25 輕/中度變化需檢查、>0.25 重大變化（一般歸於 Siddiqi 2006 信用評分卡書籍）；這些是啟發式，分箱方式與樣本量會顯著影響 PSI 值。 — [R scorecard::perf_psi 文件](https://search.r-project.org/CRAN/refmans/scorecard/html/perf_psi.html)；[arXiv 2006.11835](https://arxiv.org/pdf/2006.11835)
- **[C] Breck 等 2017 ML Test Score**：監測是生產就緒的核心考量之一。 — [Google Research](https://research.google/pubs/pub46555/)
- **[C] Sculley D 等 "Hidden Technical Debt in Machine Learning Systems"，NeurIPS 2015**：ML 系統的隱性技術債（如資料相依、回饋迴路、設定債）。（未於本輪開啟原文驗證） — [NeurIPS proceedings](https://papers.nips.cc/paper/5656-hidden-technical-debt-in-machine-learning-systems)
- **[A] GMLP 原則 10**：已部署模型受到效能監測，再訓練風險受到管理。 — [FDA GMLP 頁面](https://www.fda.gov/medical-devices/artificial-intelligence-enabled-medical-devices/good-machine-learning-practice-medical-device-development-guiding-principles)

### Inferences
- **本報告推論：本專案監測項目（以週為單位彙整）**
  1. 預測類別分布（normal/stage1/stage2/需人工確認）對比基準期：PSI 或卡方檢定；小樣本時 PSI 不穩定，搭配原始計數一起看。
  2. 分數分布：KS 檢定比較信心分數分布；**分數未校準**，只看相對變化，不解讀為機率。
  3. 輸入特徵漂移（不需標註）：影像亮度、解析度、長寬比、檔案大小、是否偵測到手臂等；對應 Finlayson 的「技術變化」（新手機、LINE 壓縮改變）。
  4. 「需人工確認」比例與人工審閱結果。
  5. 定期抽樣人工審閱（含一致案例），以估計真實效能——這是唯一能回答「還準不準」的指標；需處理**標註延遲**（審閱完成前無法得知效能，報表需標示「標註完成率」）。
  6. 若影子模式持續運行，現行與候選模型的分歧率本身也是漂移訊號。
- **本報告推論**：監測觸發的動作只能是「通知人→人調查→人決定是否回滾/重新評估」；不可觸發自動再訓練（原則：不自動訓練）。觸發工程 guardrail（Q3）時可自動回滾到上一個已核准模型。
- **原則檢核**：監測不會自動改變模型 → 符合。

### Gaps
- 未找到皮膚/傷口照片類臨床 AI 部署後漂移的具體研究。
- Siddiqi 2006 原書未核對；PSI 門檻在醫療影像情境的適用性無文獻。

---

## Q6. 回滾策略

### Takeaway
業界慣例與 ML 生產實務（SRE、ML Test Score）都把「可快速回滾」視為必要能力：可重現建置、小變更、feature flag 分離變更。本報告推論本專案應以不可變模型登錄（版本＋雜湊）＋設定檔指向「已核准模型 ID」＋舊模型熱備＋稽核紀錄實作；若已發出錯誤結果，是否重新聯絡使用者由人決定，並以不含診斷宣稱的固定模板處理。

### Cited Findings
- **業界慣例** 可重現建置、小而自含的變更較易回滾、以 feature flags 分離變更速率、依金絲雀 vs 對照自動回滾或升級給人。 — [Google SRE Workbook: Canarying Releases](https://sre.google/workbook/canarying-releases/)
- **[C]** ML 模型需要可除錯性、回滾與監測等生產實務。 — [Breck 等 2017 ML Test Score](https://research.google/pubs/pub46555/)
- **[A]** IMDRF N88 定稿相對草案新增「可重現結果」要求。 — [RAPS](https://www.raps.org/resource/imdrf-finalizes-good-machine-learning-practice-so.html)
- **[A]** FDA PCCP 要求事先定義修改協定與影響評估（含驗證、實施方式）；標示應告知使用者裝置使用機器學習且有 PCCP、更新可能改變效能。 — [Foley 2025-01 [E]](https://www.foley.com/insights/publications/2025/01/fda-final-guidance-ai-device-software-predetermined-change-control-plan/)；[FDA 指引頁](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/marketing-submission-recommendations-predetermined-change-control-plan-artificial-intelligence)

### Inferences
- **本報告推論：實作清單**
  1. **模型登錄（registry）**：每個模型檔（含外部 safetensors）以 SHA-256 雜湊為身分；登錄後不可覆寫；記錄來源、授權、訓練資料版本、評估報告路徑、核准者與日期、狀態（candidate / approved / active / retired / rejected）。
  2. **設定指標**：單一設定值 `active_model_id`（與 `shadow_model_id`）指向登錄中的 ID；啟動時驗證雜湊相符，不符即拒絕載入並降級為「需人工確認」回覆。只有狀態為 approved 的模型可被設為 active（程式強制）。
  3. **舊模型熱備**：切換後至少保留上一個 approved 模型在記憶體或可秒級載入，回滾＝改回設定值。
  4. **稽核紀錄**：每次回覆記錄 model_id、雜湊、分數、時間；每次切換/回滾記錄操作者（自動回滾記為 system＋觸發原因）、理由、前後 ID。append-only。
  5. **回滾演練**：定期在測試環境演練回滾。
  6. **錯誤結果的處理（推論）**：若事後發現某模型版本系統性給出錯誤判讀（例如 stage 2 判成 normal），由負責人決定是否以 LINE 推播重新聯絡受影響使用者；訊息應為事先審定的模板（說明先前結果可能不正確、建議依原本醫療建議或洽醫護人員），不提供新的診斷，並記錄發送清單。重新聯絡本身屬於「代表專案發訊」，需人工核准，且宜事先寫進 IRB 計畫書與隱私告知。
- **原則檢核**：所有切換需人核准；自動化僅限回滾與降級；雜湊確保外部模型未經評估不得上線 → 符合。

### Gaps
- 本輪未檢索 LINE Messaging API 推播的條件（使用者需仍為好友、訊息配額/費用），重新聯絡的可行性需另查 LINE 官方文件。
- 未找到醫療 AI 實際「事後通知使用者先前結果錯誤」的案例或指引。

---

## Q7. 失敗案例：未經（或經）silent/前瞻評估的 AI 在真實世界的表現

### Takeaway
研究證據一再顯示「實驗室表現」不能移轉到真實使用：Google 糖尿病視網膜病變系統在泰國 11 家診所遇到影像品質門檻與真實環境衝突；皮膚癌 App 系統性回顧發現研究小、品質差，且由臨床人員拍照，真實使用者表現可能更差；症狀檢查器僅 34% 首位診斷正確；Epic 敗血症模型外部驗證遠低於開發者宣稱。反例是 Kwong 的 silent trial 在任何病人受影響前就抓到 AUC 0.90→0.50 的漂移。這些案例直接支持本專案「影子模式＋人核准」的設計，也提示民眾自拍照片的品質問題可能是最大風險。

### Cited Findings
- **研究證據顯示 [C]** Beede E 等，"A Human-Centered Evaluation of a Deep Learning System Deployed in Clinics for the Detection of Diabetic Retinopathy"，CHI 2020（DOI 10.1145/3313831.3376718）：在泰國 11 家診所觀察與訪談護理人員，搭配前瞻準確度研究；核心發現是模型的資料品質門檻與資源受限環境實際產生的資料品質之間的緊張關係；作者主張在廣泛部署前結合以人為中心的研究與前瞻評估。 — [Google Research 頁面](https://research.google/pubs/a-human-centered-evaluation-of-a-deep-learning-system-deployed-in-clinics-for-the-detection-of-diabetic-retinopathy/)
  - 「超過五分之一影像被拒」為新聞報導數字（轉載 MIT Technology Review），**未在原文中核對**（ACM 全文本輪 403）。 — [轉載部落格 [E]](https://chhsu135.blogspot.com/2020/04/a-human-centered-evaluation-of-deep.html)；[Fudzilla [E]](https://fudzilla.com/news/50735-ai-is-brilliant-the-lab-but-pants-in-real-life)
  - 外部驗證狀態：本研究本身就是前瞻部署評估（非回溯），重點是社會技術因素而非模型準確度。
- **研究證據顯示 [B]** Freeman K 等，"Algorithm based smartphone apps to assess risk of skin cancer in adults: systematic review of diagnostic accuracy studies"，*BMJ* 2020;368:m127（DOI 10.1136/bmj.m127），2020-02-10：納入 9 項研究、6 個 App；6 項以組織病理或追蹤驗證（725 病灶）、3 項以專家建議驗證（407 病灶）；研究小且方法品質差；SkinScan 在一項 15 病灶研究中黑色素瘤敏感度 0%；SkinVision 在 3 項以專家建議為參考的研究中表現差；結論：目前 App 不能被依賴偵測所有黑色素瘤或其他皮膚癌，CE 標章流程未提供足夠保護。**關鍵限制**：病灶選擇與拍照由臨床人員而非 App 使用者執行，作者推測實際使用者情境表現更差。 — [DOI](https://www.doi.org/10.1136/bmj.m127)；[PubMed 32041693](https://pubmed.ncbi.nlm.nih.gov/32041693/)
- **研究證據顯示 [B]** Semigran HL, Linder JA, Gidengil C, Mehrotra A，"Evaluation of symptom checkers for self diagnosis and triage: audit study"，*BMJ* 2015;351:h3480：23 個症狀檢查器、45 個標準化病人情境；首位診斷正確 34%（95% CI 31–37%）、前 20 名內 58%；適當分流建議 57%（95% CI 52–61%）；緊急 80%、非緊急 55%、自我照護 33%；各產品分流正確率 33–78%；分流建議普遍偏保守。外部效度限制：使用情境腳本而非真實病人。 — [BMJ](https://www.bmj.com/node/900623)；[AHRQ PSNet](https://psnet.ahrq.gov/issue/evaluation-symptom-checkers-self-diagnosis-and-triage-audit-study)
- **研究證據顯示** Epic 敗血症模型（Wong 2021，見 Q5）：開發者報告 AUC 0.76–0.83 vs 外部驗證 0.63；推測原因之一是以帳單碼定義結果、以臨床介入時間定義發病時間（二手報導）。 — [MedCity News [E]](https://medcitynews.com/2021/06/popular-sepsis-prediction-model-works-substantially-worse-than-claimed-researchers-find)
- **研究證據顯示（成功攔截）** Kwong 2022 silent trial：AUC 0.90→0.50 在影響病人前被發現並修正（見 Q1）。 — [Frontiers](https://www.frontiersin.org/articles/10.3389/fdgth.2022.929508/full)
- **研究證據顯示** 密西根大學敗血症警示模型因疫情族群變化於 2020-04 停用（Finlayson 2021，見 Q5）。 — [PubMed 34260843](https://www.pubmed.gov/34260843/)

### Inferences
- **本報告推論：對本專案的對應教訓**
  1. Beede：模型品質門檻 vs 真實照片品質 → 本專案 LINE 自拍照（光線、角度、模糊、壓縮）很可能是主要失敗來源；「需人工確認」比例高是可預期的，不應為了降低它而放寬門檻。
  2. Freeman：由臨床人員拍照的研究會高估真實使用者表現 → 本專案醫院收集照片與 LINE 民眾照片必須分開報告效能；醫院資料上的結果不能直接宣稱適用於 LINE。
  3. Semigran：消費者端工具分流準確度有限且變異大 → 回覆文字應維持「研究原型、非診斷、請依醫護人員建議」。
  4. Wong/Epic：開發者自評 vs 外部驗證落差 → 外部 safetensors 模型的原始宣稱效能不可沿用，必須在專案資料上重評（符合專案原則）。
  5. Kwong：silent trial 能在無害情況下抓到漂移 → 支持保留並強化影子模式。
- **資料洩漏 / 外部驗證狀態整理**：Wong 2021＝回溯性外部驗證（單中心）；Beede 2020＝前瞻部署＋質性研究；Freeman 2020＝系統性回顧（納入研究品質差、非預期使用者拍攝）；Semigran 2015＝情境腳本稽核；Kwong 2022＝前瞻 silent trial（單中心）。本輪未發現上述研究有被指出資料洩漏問題。

### Gaps
- Beede 2020 原文中的影像拒收比例、上傳延遲等具體數字未核對（ACM 403）。
- 未找到「傷口/靜脈炎照片 AI」部署失敗或 silent trial 的已發表案例。
- 未檢索較新（2023–2026）的皮膚科 AI App 真實世界評估或 LLM 醫療聊天機器人部署失敗研究。
