# 偏倚風險工具（PROBAST+AI、PROBAST、QUADAS-2/-3/-C/-AI）與靜脈炎影像 AI 專案自評

存取日期：除另註明外，所有來源皆於 2026-10-30 存取。
來源分級：[A] 官方工具／報告標準；[B] 系統性回顧／頂級期刊；[C] 其他同儕審查文獻；[D] 預印本；[E] 部落格／程式碼／二手彙整（僅作佐證）。
標示：〔研究證據〕＝有來源的事實；〔慣例〕＝工具指引或領域慣例；〔推論〕＝本筆記作者將工具套用到本專案所作的判斷。
題目內容皆為改寫（paraphrase），不是原文。

---

## Q1. PROBAST+AI 是什麼？結構、題目、開發與評估兩部分、適用性、公平性

### Takeaway
PROBAST+AI（Moons et al., BMJ 2025;388:e082505）取代 PROBAST-2019。它把「模型開發品質（quality）」和「模型評估偏倚風險（risk of bias）」分成兩部分。兩部分都有 4 個領域；開發部分有 16 題信號問題，評估部分有 18 題，另有 6 個適用性項目（每部分 3 個，只評前三個領域）。公平性與演算法偏倚是「貫穿各領域」的考量，**沒有獨立的公平性題目**。新增的 AI 相關題目涵蓋前處理、類別不平衡、資料洩漏，以及重抽樣時是否重複所有開發步驟。

### Cited Findings
- 引用：Moons KGM, Damen JAA, Kaul T, Hooft L, Andaur Navarro C, Dhiman P, Beam AL, Van Calster B, Celi LA, Denaxas S, Denniston AK, Ghassemi M, Heinze G, Kengne AP, Maier-Hein L, Liu X, Logullo P, McCradden MD, Liu N, Oakden-Rayner L, Singh K, Ting DS, Wynants L, Yang B, Reitsma JB, Riley RD, Collins GS, van Smeden M. *PROBAST+AI: an updated quality, risk of bias, and applicability assessment tool for prediction models using regression or artificial intelligence methods.* BMJ 2025;388:e082505. doi:10.1136/bmj-2024-082505。2025-03-24 刊出。[A] — [BMJ](https://www.bmj.com/content/388/bmj-2024-082505)；全文 PDF（Oxford ORA 開放取用）[ORA](https://ora.ox.ac.uk/objects/uuid:8b15c087-459b-43fa-ad03-1f66ed6ba370/files/s1g05fd94g)
- 已在全文中核實的結構：4 個領域、34 題信號問題（開發 16、評估 18）、6 個適用性項目（開發 3、評估 3）。前三個領域在兩部分共用相同題目；領域 4（分析）在開發部分有 5 題，在評估部分有 7 題。[A] — [ORA PDF, p7](https://ora.ox.ac.uk/objects/uuid:8b15c087-459b-43fa-ad03-1f66ed6ba370/files/s1g05fd94g)
- 開發過程：Delphi 第三輪有 131 人回覆（邀請 299 人）；2023-10-17 召開共識會議，26/29 人出席。PROBAST-2019 原有 20 題，Delphi 初始候選題 26 題。[A] — [ORA PDF](https://ora.ox.ac.uk/objects/uuid:8b15c087-459b-43fa-ad03-1f66ed6ba370/files/s1g05fd94g)
- 「Quality」與「risk of bias」的區分：模型只會被開發一次，所以開發部分評的是「製造過程的品質」，品質差是紅旗。評估部分評的是表現估計值（apparent / internal / external validation）是否系統性偏離真實表現。偏倚也不同於不精確（imprecision：評估樣本小導致信賴區間寬）。[A] — [ORA PDF, p9](https://ora.ox.ac.uk/objects/uuid:8b15c087-459b-43fa-ad03-1f66ed6ba370/files/s1g05fd94g)
- 作答選項：Y / PY / N / PN / NI / NA。Y 或 PY 代表低疑慮。N 不會自動讓整個領域判為高風險，需由評估者判斷。領域與整體評等為 low / high / unclear。[A] — [ORA PDF, p10](https://ora.ox.ac.uk/objects/uuid:8b15c087-459b-43fa-ad03-1f66ed6ba370/files/s1g05fd94g)
- 整體判斷可降級：例如沒有外部驗證時，領域 4 可能判高風險。但若模型在大型資料集上開發、做了內部驗證，且其他三個領域都是低疑慮，可改判整體低風險。[A] — [ORA PDF, p11](https://ora.ox.ac.uk/objects/uuid:8b15c087-459b-43fa-ad03-1f66ed6ba370/files/s1g05fd94g)
- 只做開發的研究通常仍要填兩部分，因為通常也會報告 apparent 或內部驗證表現。每個不同模型都要分別評估。[A] — [ORA PDF, p11](https://ora.ox.ac.uk/objects/uuid:8b15c087-459b-43fa-ad03-1f66ed6ba370/files/s1g05fd94g)
- 適用性的定義：領域 1 的資料／場域，領域 2 的預測因子定義、**前處理**、評估方式或時間，領域 3 的結果定義、評估方式或時間，任一項與評估者的問題或預期用途不符，即有適用性疑慮。[A] — [ORA PDF, p10](https://ora.ox.ac.uk/objects/uuid:8b15c087-459b-43fa-ad03-1f66ed6ba370/files/s1g05fd94g)
- 公平性：Box 1 把公平性定義為模型不因年齡、性別、種族、社經地位等使群體受不利；演算法偏倚指沒有正當理由下，預測對某些群體有利或不利。公平性「嵌入於四個領域的信號問題中」，並引用 STANDING Together 的資料多樣性標準。作者也指出，公平性問題未必能靠探索性資料分析發現，最終要到部署時才能評估。[A] — [ORA PDF, Box 1/Box 2/Discussion](https://ora.ox.ac.uk/objects/uuid:8b15c087-459b-43fa-ad03-1f66ed6ba370/files/s1g05fd94g)
- Box 1 的資料洩漏定義：開發階段的資料不慎進入評估（測試）階段，通常會使表現估計過於樂觀。評估資料應與訓練、模型選擇、超參數調整所用的資料不同，且參與者不重疊。[A] — [ORA PDF, Box 1](https://ora.ox.ac.uk/objects/uuid:8b15c087-459b-43fa-ad03-1f66ed6ba370/files/s1g05fd94g)

**PROBAST+AI 題目清單（改寫；題號依 BMJ Table 2）** [A] — [ORA PDF, Table 2](https://ora.ox.ac.uk/objects/uuid:8b15c087-459b-43fa-ad03-1f66ed6ba370/files/s1g05fd94g)

| 領域 | 開發部分（品質） | 評估部分（偏倚風險） |
|---|---|---|
| 1 參與者與資料來源 | 1.1 資料來源是否恰當；1.2 研究設計是否恰當；1.3 納入／排除後的資料集是否具代表性 | 同左（1.1–1.3） |
| 2 預測因子 | 2.1 所有參與者的預測因子定義與評估方式是否一致；2.2 所有參與者的**前處理**是否一致；2.3 評估預測因子時是否不知道結果資料；2.4 模型中的預測因子在預定使用時點是否可取得 | 同左（2.1–2.4） |
| 3 結果 | 3.1 結果定義與評估是否恰當；3.2 所有參與者的結果定義與評估方式是否一致；3.3 評估結果時是否未使用或不知道預測因子資料；3.4 預測因子評估與結果評估的時間間隔是否恰當 | 同左（3.1–3.4） |
| 4 分析 | 4.1 是否有證據顯示樣本數合理；4.2 連續與類別預測因子是否處理恰當；4.3 缺失或設限資料是否處理恰當；4.4 若有處理類別不平衡，模型或預測是否重新校準；4.5 是否有處理過擬合的方法 | 4.1 是否避免只用 apparent performance；4.2 是否有證據顯示樣本數合理；4.3 缺失或設限資料是否處理恰當；4.4 若有處理類別不平衡，評估資料是否未經不平衡校正；4.5 若有切分訓練與測試集，是否有證據避免資料洩漏；4.6 若用重抽樣評估，是否在重抽樣中重複所有開發步驟；4.7 預測表現是否評估恰當（如校準、鑑別、淨效益） |
| 適用性 | 領域 1–3 各一項 | 領域 1–3 各一項 |

### Inferences
- 〔推論〕跟影像 AI 專案最相關的新題目是：2.2（前處理一致性：裝置、壓縮、裁切、品質閘門）、4.4（類別不平衡與重新校準）、4.5（洩漏）、4.6（重抽樣是否包含所有調參與模型選擇步驟，也就是巢狀 CV）、4.7（校準）。
- 〔推論〕使用者以為的「新的公平性或資料處理題目」，並沒有以獨立題號存在。公平性透過 1.1、1.3（多樣性、代表性）與適用性來體現；資料處理透過 2.2 與 4.3–4.6 體現。

### Gaps
- 補充表 3、4（Explanation and Elaboration Light）的逐題說明沒有取得（BMJ 補充檔未抓到）。因此「影像資料的預測因子如何定義」、「分組資料／一位病人多張影像」的官方逐題指引**未找到可靠證據**。PROBAST+AI 正文沒有提到 clustering 或 multiple records per patient。
- 文中說每一題都考量公平性，但哪幾題具體寫了公平性的 bullet，需要看補充表 4。
- PROBAST+AI 本身沒有提供評分者間信度或可用性資料。這點由一篇評論指出，見搜尋摘要 [E]。

---

## Q2. PROBAST-2019、QUADAS-2、QUADAS-3、QUADAS-C、QUADAS-AI：引用、領域與題目、現況

### Takeaway
PROBAST-2019 有 4 個領域、20 題，已被 PROBAST+AI 取代。QUADAS-2（2011）有 4 個領域：病人選擇、指標檢測、參考標準、流程與時間。**QUADAS-3 已於 2026-02-17 刊於 Annals of Internal Medicine**，領域改為參與者、指標檢測、目標疾病、分析；流程與時間領域由「分析」取代，並新增「理想試驗」作為比較基準與「估計值層級」的評估。QUADAS-AI 目前只有 2021 年的 Nature Medicine 立場文與 2024 年的 JMIR 研究計畫書，到 2026-10-30 為止**未找到已發表的最終 QUADAS-AI 工具**。

### Cited Findings
**PROBAST-2019**
- Wolff RF, Moons KGM, Riley RD, et al. *PROBAST: a tool to assess the risk of bias and applicability of prediction model studies.* Ann Intern Med 2019;170(1):51–58. doi:10.7326/M18-1376。4 個領域（participants、predictors、outcome、analysis），共 20 題信號問題。[A] — 書目經機構典藏核實：[MSKCC record](https://synapse.mskcc.org/synapse/works/139781)；PROBAST+AI 也說 PROBAST-2019 有 20 題：[ORA PDF](https://ora.ox.ac.uk/objects/uuid:8b15c087-459b-43fa-ad03-1f66ed6ba370/files/s1g05fd94g)。ACP 原文頁回傳 403，未能直接讀取。
- Moons KGM, Wolff RF, Riley RD, et al. *PROBAST … Explanation and elaboration.* Ann Intern Med 2019;170(1):W1–W33。PROBAST+AI 指出這份 E&E 仍是主要的背景教學文件。[A] — [Utrecht repository](https://dspace.library.uu.nl/handle/1874/390220)；[ORA PDF](https://ora.ox.ac.uk/objects/uuid:8b15c087-459b-43fa-ad03-1f66ed6ba370/files/s1g05fd94g)
- PROBAST-2019 有兩題對非迴歸模型關聯性低：以單變項分析選預測因子，以及模型權重是否與多變項結果一致。[B] — [Andaur Navarro 2021, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8527348)
- PROBAST-2019 的 20 題清單（改寫，依筆者對原始工具的記憶整理；原文頁 403 未能逐字核對，請視為〔慣例〕且待核實）：
  - D1：1.1 資料來源恰當（如世代、RCT、巢狀病例對照）；1.2 納入與排除恰當。
  - D2：2.1 預測因子定義與評估一致；2.2 評估預測因子時不知道結果；2.3 預測因子在使用時點可取得。
  - D3：3.1 結果判定恰當；3.2 結果定義預先指定或採標準定義；3.3 結果定義不含預測因子；3.4 結果定義一致；3.5 判定結果時不知道預測因子；3.6 時間間隔恰當。
  - D4：4.1 有結果的人數足夠（EPV）；4.2 連續與類別預測因子處理恰當；4.3 所有納入者都進入分析；4.4 缺失資料處理恰當；4.5 避免以單變項分析選預測因子；4.6 考慮資料複雜性（設限、競爭風險、對照抽樣）；4.7 評估了相關表現指標；4.8 考慮過擬合與樂觀偏差；4.9 預測因子與權重和多變項結果相符。
  - 數量為 2+3+6+9=20，與已核實的總數 20 相符。

**QUADAS-2**
- Whiting PF, Rutjes AWS, Westwood ME, Mallett S, Deeks JJ, Reitsma JB, Leeflang MMG, Sterne JAC, Bossuyt PMM. *QUADAS-2: a revised tool for the quality assessment of diagnostic accuracy studies.* Ann Intern Med 2011;155(8):529–536. doi:10.7326/0003-4819-155-8-201110180-00009。4 個領域：patient selection、index test、reference standard、flow and timing。[A] — [Bristol research record](https://research-information.bris.ac.uk/en/publications/quadas-2-a-revised-tool-for-the-quality-assessment-of-diagnostic/)；[BORIS Bern](https://boris-portal.unibe.ch/handle/20.500.12422/78041)
- 信號問題（改寫）。以下 9 題已透過一篇套用 QUADAS-2 的回顧表格核實（Sun et al., Onco Targets Ther 2015）：
  - D1：連續或隨機收案；避免病例對照設計；避免不當排除。
  - D2：判讀指標檢測時不知道參考標準結果。
  - D3：參考標準可能正確分類目標疾病；判讀參考標準時不知道指標檢測結果。
  - D4：指標檢測與參考標準的間隔恰當；所有人都接受參考標準；所有人都進入分析。
  - 來源：[C] — [PMC table](https://pmc.ncbi.nlm.nih.gov/articles/PMC4467645/table/t1-ott-8-1291)
  - 該表沒有列出官方工具另外兩題：D2「若使用閾值，是否預先指定」，D4「所有人是否接受相同的參考標準」。這兩題依筆者對 Whiting 2011 的記憶補上，標為待核實〔慣例〕。官方應為 11 題。
  - 適用性：D1–D3 各一項（病人、指標檢測、目標疾病是否與回顧問題相符）。
- NIHR/Bristol 的實務評分附錄：病例對照設計答 N；排除超過 10% 即視為不當排除（這是該附錄自訂的規則，不是工具本身的規定）。[C] — [NIHR HTA appendix](https://journalslibrary.nihr.ac.uk/sites/journalslibrary/files/journal_data/hta25420/NIHR129546-app2b.pdf)

**QUADAS-3（新，2026）**
- Whiting et al. *QUADAS-3: A Revised Tool for the Quality Assessment of Diagnostic Test Accuracy Studies.* Ann Intern Med 2026;179(4):548–555。2026-02-17 線上刊出。doi:10.7326/ANNALS-25-02104。同日刊出 E&E：doi:10.7326/ANNALS-25-04943。[A] — [Bristol research record](https://research-information.bris.ac.uk/en/publications/quadas-3-a-revised-tool-for-the-quality-assessment-of-diagnostic-/)；[Bristol QUADAS-3 tool page](https://www.bristol.ac.uk/population-health-sciences/projects/quadas/quadas-3/quadas-3-tool/)。卷期頁碼與 DOI 取自搜尋摘要所引的機構紀錄，UCL 頁面回傳 403。
- 以下內容直接讀自官方工具檔 QUADAS-3 v1.2（.docx，Bristol）[A] — [QUADAS-3 v1.2 docx](https://www.bristol.ac.uk/media-library/sites/social-community-medicine/quadas/QUADAS-3%201.2.docx)
  - 共 6 個階段：(1) 寫下綜合問題；(2) 定義「理想檢測準確度試驗」；(3) 畫研究流程圖；(4) 挑選要評估的準確度估計值；(5) 逐領域評估偏倚與適用性；(6) 整體判斷。
  - 作答選項：Y/PY/PN/N/NI。領域判斷：low / high / insufficient information (II)。
  - 整體判斷規則：任一領域為 high，整體即為 high；全部為 low，整體才為 low；有 II 且無 high，整體為 II。
  - D1 參與者（題號為筆者依順序編）：1.1 單一入口設計（single-gate，非病例對照）；1.2 前瞻收案；1.3 連續或隨機樣本；1.4 樣本能代表預期使用族群。
  - D2 指標檢測：2.1 依建議方式執行與判讀；2.2 判讀時不知道參考標準；2.3 判讀時可用的資訊與實務相同；2.4 若有閾值，是否為標準或預先指定。
  - D3 目標疾病：3.1 參考標準能充分區分有病與無病；3.2 所有人都評估了目標疾病；3.3 所有人用相同方式評估；3.4 參考標準未納入指標檢測；3.5 參考標準依建議方式執行與判讀；3.6 判讀參考標準時不知道指標檢測結果；3.7 參考標準閾值為標準或預先指定；3.8 兩者時間間隔恰當。
  - D4 分析（官方題號）：4.1 所有參與者都進入分析；4.2 缺失資料處理恰當；4.3 **分析單位與理想試驗相符**；4.4 敏感度與特異度的計算方法恰當。
  - 適用性只評 D1–D3。
  - 理想試驗範本的要求包括：前瞻收入連續或隨機的單一族群、閾值預先指定、參考標準獨立於指標檢測、所有人都進入分析、分析單位恰當、樣本數足以得到精確的敏感度與特異度。
- 有二手彙整網站稱開發者現在建議以 QUADAS-3 取代 QUADAS-2 [E]，未在官方頁直接核實。 — [paperguide glossary](https://paperguide.ai/research-glossary/quadas-2-quality-assessment-of-diagnostic-accuracy-studies/)

**QUADAS-C**
- Yang B, Mallett S, Takwoingi Y, et al. *QUADAS-C: a tool for assessing risk of bias in comparative diagnostic accuracy studies.* Ann Intern Med 2021;174(11):1592–1599. doi:10.7326/M21-2234。
  - 它是 QUADAS-2 的延伸，用於同一研究內比較兩種以上檢測，沿用 4 個領域並加上比較相關的題目。
  - 不涵蓋適用性，也不能單獨使用。Cochrane 列為選用工具。
  - 來源：[B] — [Birmingham record](https://research.birmingham.ac.uk/en/publications/quadas-c-a-tool-for-assessing-risk-of-bias-in-comparative-diagnos)；[Cochrane Methods news](https://methods.cochrane.org/news/quadas-c-optional-risk-bias-tool-cochrane-reviews-diagnostic-test-accuracy-addressing)；[Bristol QUADAS-C](https://www.bristol.ac.uk/population-health-sciences/projects/quadas/quadas-c/)

**QUADAS-AI**
- Sounderajah V, Ashrafian H, et al. *A quality assessment tool for artificial intelligence-centered diagnostic test accuracy studies: QUADAS-AI.* Nat Med 2021;27(10):1663–1665. doi:10.1038/s41591-021-01517-0。
  - 文中指出，已發表的 AI 診斷準確度系統性回顧中，有 94% 未使用 AI 專用的品質評估工具。
  - 作者提議做成 QUADAS-2 與 QUADAS-C 的 AI 延伸版，而不是另起獨立工具。
  - 來源：[A/B] — [UCL accepted manuscript](https://discovery.ucl.ac.uk/10137255/1/Sounderajah%20QUADAS_AI%20position%20statement%20accepted.pdf)。Nature 頁面被重導到登入頁，94% 取自搜尋摘要。
- Guni A, Sounderajah V, Whiting P, Bossuyt P, Darzi A, Ashrafian H. *Revised Tool for the Quality Assessment of Diagnostic Accuracy Studies Using AI (QUADAS-AI): Protocol for a Qualitative Study.* JMIR Res Protoc 2024;13:e58202. doi:10.2196/58202。
  - 開發分三階段：組織、題目產生（mapping review、meta-research、專家調查、病人參與、修正式 Delphi 以 75% 為共識門檻、名義團體會議、20–30 人試用）、推廣。
  - 原定 2024 年底定稿，2025 Q1 發表。
  - 若 QUADAS-3 草稿已可用，會以 QUADAS-3 為基礎。
  - 來源：[A] — [PMC11447435](https://pmc.ncbi.nlm.nih.gov/articles/PMC11447435/)

### Inferences
- 〔推論〕到 2026-10，QUADAS-AI 很可能尚未定稿，或者已發表但這次搜尋沒找到。實務上，評估 AI 診斷準確度可用 QUADAS-3（若要比較 AI 與人類讀者，再加 QUADAS-C），再補上 PROBAST+AI 的 AI 題目（洩漏、前處理、重抽樣）作為自訂的額外題目。
- 〔推論〕QUADAS-3 的 D4.3「分析單位」正好對應本專案「一位病人多張照片」的問題。這是 QUADAS-2 沒有明確列出的題目。

### Gaps
- 最終 QUADAS-AI 工具：**未找到可靠證據**（兩次搜尋：一般搜尋與 extended 搜尋都只找到計畫書）。
- QUADAS-2 官方 PDF 原文：Bristol QUADAS-2 頁面回傳 404，沒有逐字核對 11 題。
- PROBAST-2019 原文頁回傳 403，20 題清單的逐題文字未能直接核對。
- QUADAS-2 的評分者間信度證據這次沒有搜尋，屬於缺口。

---

## Q3. PROBAST+AI 專案自評表（現況，與擴充到約 1,000 張照片、50–300 位病人後的變化）

### Takeaway
〔推論〕以目前狀態（14 位病人，二元任務只有 9 張 normal 照片，參考標準是單一標註者看同一張照片，部分標籤由檔名規則自動產生，便利或病例富集樣本，在同一組 CV folds 上反覆調參，沒有校準，沒有外部驗證），開發品質與評估偏倚風險**四個領域都偏高，整體為 High**；三個適用性領域也都是 High concern。擴充到約 1,000 張後，樣本數相關題目可望改善。但如果仍刻意做三類平衡、仍是單一標註者看照片、仍沒有床邊臨床評估與外部驗證，領域 1、3 和 4.4／4.7 仍會是高風險。

### Cited Findings（自評依據的工具條文與方法學證據）
- PROBAST+AI 題目與判斷規則，見 Q1。[A] — [ORA PDF](https://ora.ox.ac.uk/objects/uuid:8b15c087-459b-43fa-ad03-1f66ed6ba370/files/s1g05fd94g)
- 樣本數：Riley RD et al. *Calculating the sample size required for developing a clinical prediction model.* BMJ 2020;368:m441. doi:10.1136/bmj.m441。提出以限制過擬合與精確估計關鍵參數為目標的樣本數準則，取代單純的 EPV≥10；R 套件 pmsampsize 實作了這些準則。[A/B] — [NDORMS record](https://www.ndorms.ox.ac.uk/publications/1096912/modal)；[pmsampsize manual](https://cran.r-universe.dev/pmsampsize/doc/manual.html) [E]
- PROBAST+AI 的參考文獻也列出 van Smeden 等人「EPV 1:10 沒有依據」的研究。[A] — [ORA PDF refs 27–31](https://ora.ox.ac.uk/objects/uuid:8b15c087-459b-43fa-ad03-1f66ed6ba370/files/s1g05fd94g)
- 外部驗證樣本數另有 Riley 等人的「Evaluation of clinical prediction models part 3」，只核實到題名，數字未核實。[B] — [UMC Utrecht record](https://researchinformation.umcutrecht.nl/en/publications/evaluation-of-clinical-prediction-models-part-3-calculating-the-s/)
- 資料洩漏的實證：Yagis et al., Sci Rep 2021;11:22544。腦 MRI 以切片層級（slice-level）切分 CV 時，準確度被高估約 29–55 個百分點；在隨機標籤資料上，slice-level 切分得到約 96% 的假準確度，受試者層級切分約 50%（機率水準）。作者指出小資料集受影響最大。[C] — [DOAJ record](https://doaj.org/article/ba8c3daef34b44d98cdadf6e89dba3e3)。該研究使用受試者層級切分作為對照；外部驗證：不適用。
- 校準：PROBAST+AI 把校準列為表現評估要件（4.7），並引用「Calibration: the Achilles heel of predictive analytics」。[A] — [ORA PDF](https://ora.ox.ac.uk/objects/uuid:8b15c087-459b-43fa-ad03-1f66ed6ba370/files/s1g05fd94g)

### Inferences — 自評表（全部為〔推論〕）

影像任務的對應方式：「參與者」對應病人與注射部位；「預測因子」對應影像像素、前處理（裁切、縮放、壓縮、品質閘門、augmentation）與任何 metadata；「結果」對應 phlebitis 與 normal，或 normal／stage 1／stage 2 的標籤。答案縮寫：Y／PY／PN／N／NI／NA；ROB 欄為該題指向的風險。

**A. 模型開發部分（品質）**

| 題 | 現況答案 | 風險 | 理由 | 改進行動 | 擴充到約 1,000 張、50–300 位病人時 |
|---|---|---|---|---|---|
| 1.1 資料來源恰當 | PN | High | 混合義大醫院照片與 LINE 公開上傳照片，裝置、光線、壓縮各不同。若「來源」與「類別」相關（例如 normal 多來自某一來源），模型可能學到捷徑（shortcut learning）。 | 每張照片記錄來源與裝置；做「來源 × 標籤」交叉表；分來源報告表現；新資料依同一攝影規範前瞻收集。 | 若改為單一或多院前瞻、標準化攝影，可升為 PY |
| 1.2 研究設計恰當 | N | High | 便利或病例富集樣本，不是連續收入有 PIVC 的病人；normal 只有 9 張。 | 前瞻、連續收入所有 PIVC，依預定時點拍照（可參考 NCT07889895 的設計）。 | 「刻意三類平衡」本質上是病例對照或富集設計，仍為 N 或 PN；需另外保留一個自然盛行率的連續樣本作為測試集 |
| 1.3 納入或排除後具代表性 | N | High | 只有 14 位病人；品質閘門會剔除照片，而被剔除的照片可能和嚴重度或光線有關；二元任務 47:9 失衡。 | 畫流程圖（收集 → 剔除及原因 → 分析）；做「含被剔除照片」的敏感度分析；記錄年齡、性別、膚色（Fitzpatrick）等以檢視公平性。 | 人數增加後代表性可改善；膚色與年齡分布仍需報告 |
| 適用性 D1 | — | High concern | 目標使用族群（住院 PIVC 病人？居家？）沒有定義；只有台灣單院加網路照片；而且是研究原型。 | 先寫 PICOTS 與預期用途（篩檢輔助還是分期）。 | 視多院與族群而定 |
| 2.1 預測因子定義與評估一致 | PN | High | 拍攝裝置、距離、角度、光線不一；LINE 照片經過重新壓縮。 | 訂定攝影 SOP（距離、色卡、光源）；記錄 EXIF。 | 若有 SOP，可升為 PY |
| 2.2 前處理一致 | PN／NI | Unclear–High | 同一套程式碼，但輸入的原始品質不同；品質閘門門檻是否在全資料上調整，目前不清楚。 | 前處理參數只能在訓練 fold 內決定；固定並記錄版本。 | 同左 |
| 2.3 評估預測因子時不知道結果 | PN | High | YOLO 框或裁切由知道分期的人標註；檔名或資料夾隱含標籤（檔名規則），若進入任何特徵或抽樣流程會造成洩漏。 | 推論時用全圖或自動 ROI；去除檔名與 metadata；裁切人員不看標籤。 | 同左 |
| 2.4 使用時點可取得 | Y（全圖）／PN（需人工框） | Low／High | 床邊拍照即可取得；但若模型依賴人工框或裁切，部署時不一定有。 | 部署流程只用自動可得的輸入。 | — |
| 適用性 D2 | — | High concern | 臨床實際的拍攝條件不同。 | 在預期場域與裝置上測試。 | — |
| 3.1 結果定義與評估恰當 | N | High | 參考標準是單一標註者看照片做視覺分期，沒有說明使用的量表（VIP 或 INS）；部分標籤由檔名規則自動產生；沒有臨床檢查（觸痛、硬索、溫度）。照片看不到疼痛與觸診發現。 | 改用床邊 VIP 或 INS 評估（由護理師在拍照當下記錄）作為參考標準；明訂量表與切點（例如 VIP≥2）。 | 若加入床邊 VIP 與 2 位以上獨立標註者，可升為 PY |
| 3.2 結果定義與評估一致 | N | High | 標籤有兩條來源路徑（檔名規則與人工審閱），判定標準可能不同。 | 全部照片由同一套流程重新標註；報告兩條路徑的一致性。 | 同左 |
| 3.3 評估結果時未使用預測因子資料 | N | High | 結果（分期）完全來自同一張照片，也就是模型的輸入，等同由預測因子推得結果。詳見 Q4 的「incorporation」討論。 | 參考標準至少要加入照片以外的資訊（床邊評估、病歷紀錄）；或明確定義任務為「重現人類讀照片」，並據此降低宣稱。 | 若改為床邊評估，可升為 PY |
| 3.4 時間間隔恰當 | Y（同一張照片）／NI（相對於臨床狀態） | Low／Unclear | 間隔為 0，但這只代表「與標註者一致」，不代表與臨床狀態一致。 | 床邊評估要在拍照 ±1 小時內完成並記錄時間。 | — |
| 適用性 D3 | — | High concern | 目標疾病是「照片上可見的分期」，不是臨床靜脈炎（例如 VIP≥2）。 | 對齊臨床定義。 | — |
| 4.1 樣本數合理 | N | High | 14 位病人；二元任務少數類只有 9 張照片，有效樣本更接近病人數。DINOv2-small 的嵌入有 384 維，接邏輯迴歸時候選預測因子約 384 個，EPV 遠小於 1。EfficientNet-B0 凍結骨幹的特徵約 1280 維。 | 用 Riley 準則或 pmsampsize 估算；降維或加強正則化；以病人數規劃樣本。 | 每類達 100 位以上病人時可能升為 PY，仍需正式計算 |
| 4.2 預測因子處理 | NA／PY | Low | 像素特徵不適用；但分期是有序結果，目前當作名目多類處理。 | 考慮有序模型（ordinal logistic、CORAL），或報告加權 kappa。 | — |
| 4.3 缺失資料處理 | PN | High | 品質閘門剔除等同缺失，沒有報告也沒有分析。 | 報告剔除率與各類別剔除率；做敏感度分析。 | 同左 |
| 4.4 處理類別不平衡後是否重新校準 | N（若用了 class weight 或過抽樣）／NA | High | 沒有做任何校準。 | 先做 temperature scaling 或 Platt scaling，再依目標盛行率做先驗校正。 | 刻意平衡三類後，更需要依真實盛行率重新校準 |
| 4.5 處理過擬合 | PN | High | 凍結骨幹與正則化是正面做法；但在同一組 CV folds 上反覆嘗試模型與超參數，會造成模型選擇的樂觀偏差。 | 預先登錄分析計畫；用巢狀 CV；限制候選模型數量；報告所有試過的組合。 | 同左 |
| **開發整體品質** | — | **High concern** | 四個領域都是 High。 | — | 最可能先改善的是 D4.1；D1 與 D3 取決於設計是否改變 |

**B. 模型評估部分（偏倚風險）**（領域 1–3 同上表；以下只列領域 4）

| 題 | 現況答案 | 風險 | 理由 | 改進行動 | 擴充後 |
|---|---|---|---|---|---|
| 4.1 避免只用 apparent performance | Y | Low | 用病人層級的 StratifiedGroupKFold 3-fold CV。 | — | — |
| 4.2 評估樣本數合理 | N | High | 每個 fold 只有約 4–5 位病人；保留的測試集約 14–18 張照片，而且只來自 2–3 位病人。 | 改報病人層級或群集 bootstrap 的信賴區間；把結果標為探索性。 | 外部驗證最好每類有足夠事件數（依 Riley 等人的驗證樣本數準則計算） |
| 4.3 缺失資料 | PN | High | 品質閘門剔除了照片，且未報告。 | 同開發部分。 | — |
| 4.4 評估資料未經不平衡校正 | PY（現況為自然混合）／PN（未來刻意平衡） | Low／High | 若測試集被刻意平衡，算出的 PPV、NPV、準確度無法套用到真實盛行率。 | 保留一個自然盛行率的測試集；或依目標盛行率重新加權。 | 刻意三類平衡的測試集會被判 PN |
| 4.5 避免切分洩漏 | PY／NI | Unclear | 病人層級切分是正確的；但 LINE 照片的病人 ID 是否可靠、左右手是否被當成不同 ID、是否有近似重複照片，都還不清楚。 | 用感知雜湊（perceptual hash）去重；確保同一病人的所有照片和左右手都在同一 fold；稽核 ID 對應。 | 人數變多後更要自動稽核 |
| 4.6 重抽樣中重複所有開發步驟 | N | High | 模型與超參數選擇、品質閘門門檻、決策閾值都在相同 folds 上反覆調整，沒有巢狀化。 | 巢狀 CV，或鎖定一個測試集並只評估一次。 | 同左 |
| 4.7 表現評估恰當 | PN | High | 有 balanced accuracy、macro F1、混淆矩陣與 Wilson 或 bootstrap 信賴區間；但沒有 AUC 或 C 統計量、沒有校準、沒有淨效益（net benefit）；信賴區間沒有考慮同一病人多張照片的群集。 | 加入 AUC、校準圖與校準斜率、Brier 分數、決策曲線；用病人層級的群集 bootstrap。 | 同左 |
| **評估整體偏倚風險** | — | **High** | — | — | 若有外部驗證、床邊參考標準、自然盛行率測試集與巢狀 CV，可望降為 Low 或 Unclear |

- 〔推論〕Wilson 信賴區間示例：保留測試集 16 張中對 15 張（93.8%），Wilson 95% CI 約為 0.72–0.99（筆者自行計算）。而且這還沒有考慮群集；病人只有 2–3 位，真實的不確定性更大。
- 〔推論，公式依筆者記憶，未在本次核實全文〕Riley 2020 中「精確估計整體結果比例」這一條準則：n ≈ (1.96/0.05)² × φ(1−φ)。若 φ≈9/56≈0.16，n 約需 207 位「獨立單位」，遠超過現有的 14 位病人。

### Gaps
- PROBAST+AI 如何處理「影像作為預測因子」、「每人多張影像」，官方 E&E Light 的逐題指引沒有取得。
- Riley 外部驗證樣本數準則的具體數字（例如事件數下限）沒有核實全文。

---

## Q4. QUADAS-2（輔以 QUADAS-3）簡評：把系統當成指標檢測，與參考標準比較

### Takeaway
〔推論〕若把模型視為指標檢測、把「標註者看照片的分期」視為參考標準，QUADAS-2 四個領域的偏倚風險都是 High，D1 與 D3 的適用性也是 High。主要問題有：病例富集的光譜偏倚（spectrum bias）；參考標準不完美，且與指標檢測共用同一資訊來源；兩條標籤路徑造成差別驗證（differential verification）；品質閘門剔除；分析單位是照片而不是病人。

### Cited Findings
- QUADAS-2 與 QUADAS-3 題目，見 Q2。[A] — [QUADAS-3 v1.2](https://www.bristol.ac.uk/media-library/sites/social-community-medicine/quadas/QUADAS-3%201.2.docx)；[C] [PMC table](https://pmc.ncbi.nlm.nih.gov/articles/PMC4467645/table/t1-ott-8-1291)
- QUADAS-3 的理想試驗要求：參考標準解讀獨立於指標檢測；採組合式參考標準時，指標檢測不可是其組成；所有人都進入分析；分析單位恰當。[A] — [QUADAS-3 v1.2](https://www.bristol.ac.uk/media-library/sites/social-community-medicine/quadas/QUADAS-3%201.2.docx)
- 皮膚癌 App 的 QUADAS-2 回顧（Freeman 2020）發現的典型問題，與本專案高度相似：研究小、選擇性收案、無法評估的影像比例高、差別驗證。[B] — [doi.org/10.1136/bmj.m127](https://www.doi.org/10.1136/bmj.m127)

### Inferences（全部為〔推論〕）

| QUADAS-2 領域 | 信號問題答案 | ROB | 適用性 | 關鍵說明 |
|---|---|---|---|---|
| D1 病人選擇 | 連續或隨機：N；避免病例對照：N（富集收案，normal 樣本少且可能來自不同來源；未來刻意三類平衡，本質上就是多入口設計）；避免不當排除：PN（品質閘門） | High | High | 光譜偏倚：富集樣本通常讓敏感度與特異度看起來更好，因為極端病例比較多、模糊病例比較少。真實臨床常見的模糊早期紅腫可能被低估。 |
| D2 指標檢測 | 不知道參考標準：Y（演算法自動判讀）；閾值預先指定：N（argmax 或決策閾值是在同一組 folds 上反覆調出來的） | High | High（拍攝條件不同） | QUADAS-3 的 2.3「判讀時可用資訊與實務相同」：若訓練時使用人工裁切，答案為 PN。 |
| D3 參考標準 | 正確分類：N（單一標註者、未說明量表、檔名規則、沒有臨床檢查、沒有評分者間一致性）；判讀時不知道指標檢測結果：PY（標註早於建模）。但若有人根據模型錯誤回頭改標籤，就變成 PN，且會偏高。 | High | High | 見下方 incorporation 討論。 |
| D4 流程與時間 | 間隔：Y；所有人接受參考標準：Y；接受相同參考標準：N（檔名規則與人工審閱兩條路徑，屬差別驗證）；所有人進入分析：N（閘門剔除） | High | — | QUADAS-3 的 4.3：分析單位是照片，而臨床決策單位是病人或注射部位，因此同病人的照片之間有相關，信賴區間會太窄。 |

**關於 incorporation bias 的討論（〔推論〕，以〔慣例〕定義為基礎）**
- 依 QUADAS-3 的 3.4，古典的 incorporation bias 是指「指標檢測的結果成為參考標準的一部分」。本專案中，參考標準並沒有使用模型的輸出，所以嚴格依字面，3.4 可答 Y。
- 但參考標準與指標檢測讀的是**同一張照片**，資訊來源完全相同。因此：
  - (a) 研究估計的是「模型與這位標註者讀照片的一致程度」（reader-replacement 任務），不是對臨床靜脈炎的準確度。
  - (b) 照片看不到的徵象，例如疼痛、觸痛、可觸及的硬索（這些是 VIP 量表的一部分），兩者都會同樣遺漏，錯誤是相關的，因此相對於真實疾病的準確度會被高估或無法得知。
  - (c) 對 PROBAST+AI 而言，3.3「評估結果時未使用預測因子資料」應答 N，因為結果正是由預測因子（影像）判定的。
- 檔名規則自動標籤的問題比較接近**資料洩漏或捷徑風險**，而不是 incorporation：如果檔名、資料夾或拍攝批次和類別相關，而某種影像特徵（例如解析度、壓縮、EXIF）又和批次相關，模型可能學到批次而不是病灶。
- 單一標註者又沒有評分者間一致性時，無法區分「模型錯」還是「標籤錯」。分期任務的標籤噪音通常集中在 stage 1 與 stage 2 的邊界。
- 缺乏盲化：標註者知道照片的來源（醫院或 LINE）與檔名，可能影響判讀。這屬於參考標準判讀時多了額外資訊，對應 QUADAS-3 的 3.5 與 3.6。

### Gaps
- 沒有找到以 QUADAS-2 評估「參考標準為同一影像的人類判讀」的正式官方指引，屬於**未找到可靠證據**。這只是常見的影像 AI 情境，工具文件沒有專門討論。

---

## Q5. 實證：系統性回顧以 PROBAST 或 QUADAS-2 評估 AI 研究的結果，以及工具本身的限制

### Takeaway
多個頂級期刊的系統性回顧一致發現，AI 或 ML 預測與影像模型多數為高偏倚風險，最常失敗的是**分析領域**（樣本數或 EPV 不足、過擬合、缺失資料、校準缺失），其次是參與者領域。不過 PROBAST 的評分者間一致性偏低，且很多「高風險」其實反映的是報告不足，引用時要保留這個但書。

### Cited Findings
- **Nagendran M, et al. Artificial intelligence versus clinicians: systematic review of design, reporting standards, and claims of deep learning studies. BMJ 2020;368:m689.** [B]
  - 81 項非隨機研究中，58 項整體為高偏倚風險（以 PROBAST 評估）。
  - 61/81 項在摘要宣稱 AI 不劣於或優於臨床人員。
  - 深度學習 RCT 只有 10 項紀錄（2 項已發表、8 項進行中）。
  - 29 項 TRIPOD 條目中有 12 項的遵循率低於 50%。
  - 來源：[next.sciencegate (doi 10.1136/bmj.m689)](https://next.sciencegate.app/document/10.1136/bmj.m689)；[ORA PDF](https://ora.ox.ac.uk/objects/uuid:e86e3d5b-40f4-4264-bc3a-3bef7a738dc1/files/s2v23vt47j)。數字來自摘要或搜尋摘要。
  - 病人層級切分與外部驗證的比例：本次未核實。
- **Andaur Navarro CL, et al. Risk of bias in studies on prediction models developed using supervised machine learning techniques: systematic review. BMJ 2021;375:n2281.** [B]
  - 納入 152 項研究（2018–2019 年）：診斷 58、預後 94。共做 171 次 PROBAST 評估。
  - 148/171（87%，95% CI 81–91%）為高風險。
  - 分析領域最常為高風險：開發模型 128/152（84%），外部驗證 14/19（74%）。
  - 參與者領域高風險：24%（開發）、16%（外部驗證）。預測因子領域：9%。結果領域多為「不清楚」（43%）。
  - 每個候選預測因子的事件數不足：85/152（56%）。缺失資料處理不當：41%。過擬合處理不當：39%。
  - 表現指標評估恰當的只有 10%，資訊缺失 60%，常缺校準圖，且過度使用準確度。
  - 外部驗證：只有 19/152（13%）在同一研究內做了外部驗證。
  - 作者認為 PROBAST 需要為 ML 增加資料產生、特徵選擇、過擬合方面的題目。
  - 來源：[PMC8527348](https://pmc.ncbi.nlm.nih.gov/articles/PMC8527348)
- **Wynants L, et al. Prediction models for diagnosis and prognosis of covid-19: systematic review and critical appraisal. BMJ 2020;369:m1328（living review）.** [B]
  - 某次更新版本中：412 項研究、731 個模型或驗證；545 個高風險、32 個不清楚、29 個低風險。
  - 125 個診斷模型中有 75 個以醫學影像為基礎。
  - 最常見的高風險原因：樣本數不足（67%）與表現評估不當或不完整（56%）。
  - 數字依版本不同而異，此處取自搜尋摘要，引用時請註明版本。
  - 來源：[BMJ](https://bmj.com/content/369/bmj.m1328)
- **Roberts M, et al. Common pitfalls and recommendations for using machine learning to detect and prognosticate for COVID-19 using chest radiographs and CT scans. Nat Mach Intell 2021;3:199–217. doi:10.1038/s42256-021-00307-0.** [B]
  - 2,212 項研究篩出 62 項，結論是沒有任何一個模型具潛在臨床用途。
  - 舉例：有資料集把兒童影像放在非 COVID 類、成人影像放在 COVID 類，模型因此學到年齡而非疾病。這是來源與標籤混淆造成捷徑的典型例子，與本專案「醫院照片與 LINE 照片」的情境類似。
  - 來源：[Cambridge news](https://www.cam.ac.uk/research/news/machine-learning-models-for-diagnosing-covid-19-are-not-yet-suitable-for-clinical-use)；[Dundee record](https://discovery.dundee.ac.uk/en/publications/common-pitfalls-and-recommendations-for-using-machine-learning-to/)
- **Freeman K, et al. Algorithm based smartphone apps to assess risk of skin cancer in adults: systematic review of diagnostic accuracy studies. BMJ 2020;368:m127（勘誤 m645）.** [B]
  - 9 項研究評估 6 個 App，使用 QUADAS-2。
  - 研究規模小、方法學品質差：選擇性收案、無法評估的影像比例高、差別驗證。
  - SkinVision 合併 2 項研究（n=252，61 個惡性或癌前病灶），敏感度 80%、特異度 78%。
  - 來源：[doi.org/10.1136/bmj.m127](https://www.doi.org/10.1136/bmj.m127)；[PubMed 32041693](https://pubmed.ncbi.nlm.nih.gov/32041693/)
- **Haggenmüller S, et al. Skin cancer classification via convolutional neural networks: systematic review of studies involving human experts. Eur J Cancer 2021;156:202–216. doi:10.1016/j.ejca.2021.06.049.** [B]
  - 19 項研究都顯示 CNN 不劣於或優於臨床人員。
  - 但幾乎都在高度人工的情境，只用可疑病灶的單張影像。
  - 來源：[LIH research portal](https://researchportal.lih.lu/en/publications/skin-cancer-classification-via-convolutional-neural-networks-syst/)
- **Dhiman P, et al. BMC Med Res Methodol 2023**：119 項預測模型研究中，只有 9 項（8%）提供樣本數依據。[B/C] — [DOAJ](https://doaj.org/article/3a6129ed94174161ad89c5c14fff47aa)（取自搜尋摘要）
- **工具限制：評分者間信度**
  - Langenhuijsen LFS, et al. J Clin Epidemiol 2023;159:159–173. doi:10.1016/j.jclinepi.2023.04.012。這是 139 篇系統性回顧的後設回顧。PROBAST 的 Cohen's kappa 偏低：領域層級約 0.04–0.26，信號問題層級約 −0.14 至 0.49。上下限取自編碼受損的搜尋摘要，引用前請核對全文。[B] — [UMC Utrecht record](https://researchinformation.umcutrecht.nl/en/publications/systematic-metareview-of-prediction-studies-demonstrates-stable-t/)
  - Kaiser I, et al. J Clin Med 2023（黑色素瘤預測研究）：訓練前的多評分者 Gwet AC1 為 0.071–0.535，接受專門訓練後為 0.294–0.780。[C] — [PMC10003882](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10003882/)
  - Kaul et al., J Clin Epidemiol 2025（doi:10.1016/j.jclinepi.2025.111732）報告，事先規劃評分方式並召開共識會議後，評分者間信度較高。這只見於二手彙整頁 [E]，未核實。
- PROBAST+AI 作者自己承認曾參考 PROBAST 評分者間一致性偏低的研究（參考文獻 43、44）。[A] — [ORA PDF](https://ora.ox.ac.uk/objects/uuid:8b15c087-459b-43fa-ad03-1f66ed6ba370/files/s1g05fd94g)
- QUADAS-AI 立場文指出，94% 的 AI 診斷準確度系統性回顧沒有使用 AI 專用的品質工具。[A/B] — [UCL accepted manuscript](https://discovery.ucl.ac.uk/10137255/1/Sounderajah%20QUADAS_AI%20position%20statement%20accepted.pdf)

### Inferences
- 〔推論〕本專案的弱點（樣本數、過擬合與調參、校準、缺失或剔除、便利樣本）正好落在文獻中最常失敗的領域，所以自評結果為 High 符合預期，不代表本專案特別差。
- 〔推論〕反面證據：許多「高風險」判定來自報告不足（NI）和評分者間不一致，所以 PROBAST 判 High 不等於表現估計必然錯誤。對本專案而言，主動揭露（流程圖、剔除、調參次數）就能把 NI 轉成可判斷的答案。
- 〔推論〕Roberts 與 Freeman 都顯示「來源與標籤混淆」和「無法評估的影像」是影像 AI 的特有問題，應列為本專案的優先檢查項目。

### Gaps
- 各回顧中「病人層級切分」的比例：以上回顧都沒有在本次核實的摘要中報告，**未找到可靠證據**。Nagendran 2020 的外部驗證比例也未核實。
- QUADAS-2 的評分者間信度研究未搜尋。

---

## Q6. 靜脈炎或 IV 注射部位影像 AI 的文獻

### Takeaway
到 2026-10-30，**沒有找到已發表、同儕審查的「以照片辨識或分期靜脈炎」的深度學習研究**（未找到可靠證據）。最接近的是土耳其一項已完成、但沒有發表結果的前瞻註冊研究（NCT07889895，n=461，手機照片，以 VIP≥2 為參考標準）。其他已發表的靜脈炎 ML 研究都使用臨床或 EHR 資料，而不是影像。

### Cited Findings
- **NCT07889895** "Predicting Peripheral Intravenous Catheter-Related Phlebitis With AI-Based Models"。[C／註冊紀錄]
  - 主辦單位：Kutahya Health Sciences University（土耳其）。前瞻觀察世代研究，n=461（實際），狀態為 Completed。
  - 開始 2025-07-15，主要完成 2026-02-15，完成 2026-09-13，首次公開 2026-10-22。
  - 以手機拍攝注射部位；參考標準為 VIP 量表（0–5），phlebitis 定義為 VIP≥2；由專家護理師與一位醫師判讀。
  - 切分為 train/validation/test，但**沒有說明是病人層級還是影像層級**，也**沒有提到外部驗證**。指標包含 calibration。
  - 沒有結果，也沒有連結的出版品。註冊資料有日期不一致的情形。
  - 偏倚風險：〔推論〕前瞻收案加 VIP 參考標準優於本專案；但切分單位不明（PROBAST+AI 4.5 答 NI），只有內部驗證。
  - 來源：[ClinicalTrials.gov API](https://clinicaltrials.gov/api/v2/studies/NCT07889895)；[Study page](https://clinicaltrials.gov/study/NCT07889895)
- 非影像的靜脈炎 ML 研究：
  - Lee S, Cho I, Kim EM. Deep Learning for Predicting Phlebitis in Patients with Intravenous Catheters. Stud Health Technol Inform 2024（PMID 39049337），使用 EHR 資料。[C]
  - Yasuda H, et al. J Crit Care Med 2024（PMID 39108413），使用 ICU、病人與導管特徵。[C]
  - Welvaars K, et al. BMC Med Inform Decis Mak 2025（PMID 40866970），心臟科住院病人，開發後做前瞻驗證。[C]
  - 以上都不使用照片；資料來源依摘要片段判斷。
  - 來源：[PubMed search](https://pubmed.ncbi.nlm.nih.gov/?term=phlebitis+AND+%28deep+learning+OR+convolutional+OR+%22artificial+intelligence%22+OR+%22machine+learning%22%29)；[PMC11295139 (Yasuda)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11295139/)
- 超音波（不是照片）：Fujita Health University 團隊有以 FCN 偵測血栓或皮下水腫，以及自動量測靜脈的研究（BMJ Open 2022，998 張超音波影像，739 張訓練、259 張測試）。目標不是靜脈炎本身，細節取自搜尋摘要。[C] — [Fujita pure (vein measurement)](https://pure.fujita-hu.ac.jp/en/publications/automatic-vein-measurement-by-ultrasonography-to-prevent-peripher/)；[Fujita pure (thrombus/edema)](https://pure.fujita-hu.ac.jp/en/publications/automated-ultrasonographic-detection-of-thrombus-and-subcutaneous-2/)

### Inferences
- 〔推論〕本專案可能是少數以照片做靜脈炎分期的嘗試，有新穎性；但也因此沒有前例可比較，更需要依 PROBAST+AI 與 TRIPOD+AI 透明報告。
- 〔推論〕NCT07889895 的設計（前瞻、VIP≥2、多位判讀者）可以作為本專案擴充到約 1,000 張時的參考範本；若日後該研究發表結果，可作為外部比較對象。

### Gaps
- Google Scholar 與中文文獻（台灣護理期刊、華藝）沒有搜尋，可能有會議論文或學位論文沒有涵蓋。
- PubMed 結果第 2 頁（3 筆）沒有檢視。
- 已發表的照片型靜脈炎深度學習研究：**未找到可靠證據**。
