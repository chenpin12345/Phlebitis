# 08 回覆措辭、健康識能、就醫建議、無障礙與多語（LINE 靜脈炎照片研究原型）

> 研究日期／存取日期：2026-10-30～31（以下統一標「存取 2026-10-30」）。
> 來源分級：[A] 官方/主管機關/標準；[B] 系統性回顧/頂級期刊；[C] 同儕審查研究；[D] 預印本；[E] 部落格/廠商/新聞/論壇（僅作輔助）。
> 標記：**研究證據顯示**＝有 [A]–[C] 來源支持；**業界慣例**＝官方或多數實務文件的做法、但非實證研究；**本報告推論**＝作者據以上資料推導，未經實證。
> 原則：本系統是研究原型，不做臨床診斷；任何雲端翻譯／雲端語音辨識都與「照片／資料不送第三方雲端」原則衝突，已逐處標示並提出本地替代方案。
> 本輪工具額度有限：凡僅取得搜尋摘要、未開啟原文者，均在條目中標示「（僅搜尋摘要）」。

---

## Q1. 非診斷措辭：免責聲明是否有效？法規怎麼看？

### Takeaway
研究證據顯示「通用免責聲明」本身幾乎無法防止使用者過度依賴 AI 健康建議；比較有效的是針對症狀的具體警示、明示不確定性、主動建議第二意見與紅旗升級。法規上，決定是否為醫療器材的是「預期用途與功能」（分析醫療影像、針對特定疾病輸出），不是免責文字；措辭只能降低誤解，不能把一個分析傷口照片並輸出「靜脈炎第幾期」的軟體變成非醫材。

### Cited Findings
**免責聲明效果／過度信任（automation bias）**
- [C] Denecke & Gabarron（2026, *Frontiers in Artificial Intelligence* 9, 2026-07-29 刊出）：線上橫斷調查，115 份完成問卷，15 個 AI 聊天機器人情境（胸痛、皮疹、頭痛伴視覺異常、胃灼熱、兒童高燒）；有免責聲明情境中「願意尋求第二意見」約 50%–89%，無免責聲明約 41%–89%，效果「modest and inconsistent」；受試者無法一致辨識不正確建議（作者連結到可能的 automation bias）；準確度是信任的最強預測因子，語氣影響有限。作者結論：免責聲明 "may not effectively prevent over-reliance on chatbot advice"，建議改用標準化不確定性溝通、第二意見提示、紅旗症狀升級、症狀特定警告。限制：情境未完全交叉隨機，屬探索性、自評意圖非實際行為。— [Frontiers 10.3389/frai.2026.1785085](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2026.1785085/full)（2026，存取 2026-10-30）
- [D] arXiv 2608.07493「The Transparency Trap: How AI Disclaimers Create Overconfidence in High-Stakes Decisions」（2026，單一學生作者，n=52）：標準化 AI 免責聲明不足以防止過度依賴，部分受試者把免責聲明解讀為「誠實」而更信任。屬預印本、樣本小，僅作輔助（僅搜尋摘要）。— [arXiv 2608.07493](https://arxiv.org/pdf/2608.07493)（2026，存取 2026-10-30）
- [C] JMIR 2026 預註冊調查實驗（e97882；作者據搜尋摘要為 Landrum 等，未逐字核對）：同一健康建議標示為「人類護理師」比「AI 護理師」或 ChatGPT 被評為更可信；但訊息內容（直覺 vs 反直覺）影響與來源標籤相當，且在高風險情境差距放大；作者認為訊息設計與受眾特性可能比來源標籤更重要（僅搜尋摘要）。— [JMIR 2026;e97882](https://www.jmir.org/2026/1/e97882/)；[PubMed 42330316](https://pubmed.ncbi.nlm.nih.gov/42330316/)（2026，存取 2026-10-30）
- [C] JMIR 2025 隨機網路調查實驗（e66083）：告知病人「醫師使用 AI 協助診斷」一致降低信任與求助意願（與聊天機器人免責聲明不同議題，但顯示「AI」標籤本身會改變行為）（僅搜尋摘要）。— [JMIR 2025;e66083](https://www.jmir.org/2025/1/e66083)（2025，存取 2026-10-30）
- [C] JMIR 2026 LLM 輸出評估（e84668）：模型隨問題緊急度提高而增加免責聲明與轉介，<1% 回應完全沒有免責聲明或轉介；此為模型輸出分析，不涉使用者反應（僅搜尋摘要）。— [JMIR 2026;e84668](https://www.jmir.org/2026/1/e84668)；[PMC12991190](https://pmc.ncbi.nlm.nih.gov/articles/PMC12991190/)（2026，存取 2026-10-30）
- 未找到可靠證據：直接量測「使用者是否閱讀／理解症狀檢查器免責聲明」的研究（搜尋結果多為廠商頁面；Buoy 使用者問卷 2022 JMIR e36322 只顯示使用者自評「易懂、有用」）。— [JMIR 2022;e36322](https://jmir.org/2022/8/e36322)（2022，存取 2026-10-30）

**FDA（美國）— 僅簡述**
- [E→轉述 A] FDA 於 2026-01-06 發布修訂版《Clinical Decision Support Software》最終指引，取代 2022 版；多個法律事務所稱 2026-01-29 曾重新發布（原因未確認）。主要變動：單一建議在臨床上唯一適當時可適用執法裁量；「時間急迫」限制由 Criterion 3 移到 Criterion 4。**指引仍只處理「給醫療專業人員（HCP）」的 CDS，沒有新增消費者／病人端政策，也未處理 AI**。— [Covington 2026-01](https://www.cov.com/en/news-and-insights/insights/2026/01/5-key-takeaways-from-fdas-revised-clinical-decision-support-cds-software-guidance)；[Cooley 2026-01-20](https://www.cooley.com/news/insight/2026/2026-01-20-automation-bias-and-clinical-practice-fda-makes-incremental-updates-to-clinical-decision-support-software-guidance)（2026，存取 2026-10-30）
- [E→轉述 A] Criterion 1 排除「擷取、處理或分析醫療影像或訊號」的軟體——這類軟體不在 CDS 排除範圍內（即仍可能是 device function）。— [Covington 2026-01](https://www.cov.com/en/news-and-insights/insights/2026/01/5-key-takeaways-from-fdas-revised-clinical-decision-support-cds-software-guidance)（2026，存取 2026-10-30）
- [E→轉述 A] 同日（2026-01-06）修訂《General Wellness》指引（上一版 2019）：以非侵入感測「estimate, infer, or output physiologic parameters」且輸出「intended solely for wellness uses」者可視為一般健康產品；此類產品可發出「建議進一步評估」的通知。— [Jones Day 2026-01](https://www.jonesday.com/en/insights/2026/01/a-relaxing-2026-fda-updates-general-wellness-and-clinical-decision-support-software-guidance)（2026，存取 2026-10-30）
- FDA 官方 PDF 於搜尋結果中出現（[fda.gov/media/191560](https://www.fda.gov/media/191560/download)），本輪未開啟原文核對。

**TFDA（台灣）— 僅簡述**
- [A，第三方副本] 食藥署《醫用軟體分類分級參考指引》：原 104 年公告，配合 110-05-01《醫療器材管理法》施行修訂；並非所有醫用軟體都是醫療器材，判定須綜合「產品功能、用途、使用方法與工作原理」，首要確認是否符合醫材法第 3 條定義（第 3 條含「診斷、治療、緩解或直接預防人類疾病」等用途）。本輪僅取得第三方網站副本摘要，未從 fda.gov.tw 核對原文。— [mdcpp 轉載副本](https://mdcpp.com/doc/materialDownload/%E5%8F%B0%E6%B9%BE-%E5%8C%BB%E7%96%97%E8%BD%AF%E4%BB%B6%E5%88%86%E7%B1%BB%E5%92%8C%E5%88%86%E7%BA%A7%E5%8F%82%E8%80%83%E6%8C%87%E5%8D%97.pdf)（存取 2026-10-30）

### Inferences
- **本報告推論**：本系統「分析手臂照片並輸出靜脈炎期別」在 FDA 架構下同時觸及 Criterion 1（影像分析）且面向一般民眾（非 HCP），也不屬「僅供 wellness」——因此**不能靠措辭達成非醫材地位**；措辭的功能是「降低誤解、促成正確求助」，而法規定位需由研究計畫（IRB、TFDA 諮詢）處理（細節由其他章節涵蓋）。
- **本報告推論（措辭原則）**：
  1. 用「照片中可能看到的徵象」「研究模型的結果」取代「你有靜脈炎」「診斷」「確診」「治療」「建議用藥」。
  2. 不只放一段通用免責聲明（證據顯示效果不一致），而是把「不確定性＋具體下一步＋紅旗」寫進每一則結果訊息本身（呼應 Denecke & Gabarron 建議）。
  3. 每則結果都附「不論結果為何，只要出現 X、Y、Z 就告訴護理師／就醫」——讓「正常」結果不被誤讀為「安全，不用理會」（降低 false reassurance）。
  4. 「正常」結果要特別小心：寫成「照片中沒有看到明顯的紅腫」而非「沒有靜脈炎」。
  5. 「這不是疾病機率」的分數不呈現給一般民眾（見 Q2：數字若無校正會誤導）；只呈現分類與行動。
- 建議避免的字詞（**本報告推論**，依醫材法第 3 條用語與 FDA device function 概念）：診斷、確診、判定為、治療、處方、用藥建議、保證、準確率 xx%、AI 醫師。

### Gaps
- 未找到直接研究「健康聊天機器人免責聲明閱讀率／理解率」的 [B]/[C] 研究（未找到可靠證據）。
- FDA 2026 CDS / General Wellness 指引原文未逐字開啟；2026-01-29 重新發布原因未確認。
- TFDA 醫用軟體指引最新官方版（含是否有 115 年修訂）與「AI/ML 醫療器材」相關指引原文未於本輪核對。
- 中文使用者對「研究模型」「僅供參考」字樣的理解，未找到台灣本地研究。

---

## Q2. 健康識能與風險溝通：怎麼寫才看得懂、做得到？

### Takeaway
研究證據顯示：一則訊息只放一個主要訊息與一個明確行動、用簡單字詞、加上可回饋確認（teach-back）的設計最符合健康識能「普遍預防」原則；口語機率詞（「可能」「很可能」）個體解讀差異極大，若要表達不確定性，用具體的「我們看不清楚／需要人看」與行動，比用模糊機率詞或未校正分數更安全。台灣約三成成人健康識能不足或有限，長者更高。聊天機器人介入的效果證據為「正向或混合、研究品質偏低」。

### Cited Findings
**健康識能工具／原則**
- [A] AHRQ《Health Literacy Universal Precautions Toolkit, 3rd Edition》：AHRQ Publication No. 23-0075，2024-03-01；含 23 項工具，涵蓋口語與書面溝通、自我管理等；teach-back 為其中一項工具（工具編號「Tool #5」來自第三方摘要，未核對）。另有第三方摘要稱 21 項，與 AHRQ 官方 23 項衝突，以官方為準。— [AHRQ Toolkit 頁](https://www.ahrq.gov/health-literacy/improve/precautions/toolkit.html)；[3rd ed PDF](https://www.ahrq.gov/sites/default/files/publications2/files/health-literacy-universal-precautions-toolkit-3rd-edition.pdf)（2024，存取 2026-10-30）
- [A] CDC Clear Communication Index：20 題、每題 0/1，換算 100 分，90 分以上為通過；第一題檢查是否「只有一個主要訊息」，並檢查主要訊息是否放在最前面；行動呼籲（call to action）須是給主要受眾的具體行為步驟。— [CDC CCI FAQ](https://www.cdc.gov/ccindex/tool/faq.html)；[CDC CCI User Guide](https://Cdc.gov/ccindex/pdf/clear-communication-user-guide.pdf)（存取 2026-10-30）
- [C] JMIR 2026（e83935）以簡體中文版 CCI 評 30 個中國省級 CDC 網站，平均 53.84 分，遠低於 90 分門檻（顯示中文衛教素材也可用 CCI 評估）（僅搜尋摘要）。— [JMIR 2026;e83935](https://www.jmir.org/2026/1/e83935)（2026，存取 2026-10-30）
- [A] 美國國家醫學院（NAM 2014）健康識能原則：只放「必須知道」而非「最好知道」的內容。— [NAM Perspectives 2014](https://nam.edu/perspectives-2014-health-literacy-principles-guidance-for-making-information-understandable-useful-and-navigable/)（2014，存取 2026-10-30）
- [A] 衛福部社家署《政府宣導素材應注意之可及性格式》（2023）：考量字體大小、使用淺顯易懂文字，使視障與心智障礙者可近用（僅搜尋摘要）。— [naer.edu.tw PDF](https://www.naer.edu.tw/upload/1/14/doc/4108/政府宣導素材應注意之可及性格式.pdf)（2023，存取 2026-10-30）

**數字 vs 文字、圖示陣列**
- [B] Zipkin DA 等（2014）, "Evidence-based risk communication: a systematic review", *Ann Intern Med* 161(4):270–280：視覺輔助（icon arrays、長條圖）改善理解與滿意度；絕對風險比相對風險更準確被理解；研究異質性高，無單一最佳方法。（注意：此文刊於 Annals of Internal Medicine，非 Medical Decision Making。）— [PubMed 25133362](https://pubmed.ncbi.nlm.nih.gov/25133362/)；[Harvard HCP 摘要](https://hcp.hms.harvard.edu/publication/evidence-based-risk-communication-systematic-review)（2014，存取 2026-10-30）
- [C] Zikmund-Fisher 等（2014）*Med Decis Making* 34(4):443–453：擬人化圖示提高風險回憶，但對低數字素養者幫助有限。— [EconPapers](https://econpapers.repec.org/RePEc:sae:medema:v:34:y:2014:i:4:p:443-453)（2014，存取 2026-10-30）
- [B] Andreadis K 等（2021）*J Gen Intern Med*（doi:10.1007/s11606-021-07050-7）系統性回顧：33 篇研究、145 個口語機率詞；病人對口語機率詞的數值解讀高度變異，且常與專家／歐盟藥品標示標準不符（9 篇子集中一般人估值遠高於標準）；多數病人偏好有數字的風險資訊（單獨或與文字並用）。— [Springer](https://link.springer.com/doi/10.1007/s11606-021-07050-7)；[PMC8642516](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8642516/)（2021，存取 2026-10-30）
- [C] Harris 等（2022, UCL）：耳鼻喉外科醫師與一般人對口語機率詞解讀皆有相當變異，一般人更大；作者警告在「低但差異很大」的機率情境勿用口語機率詞。— [UCL Discovery PDF](https://discovery.ucl.ac.uk/10142315/1/HarrisEtAl_2022_JEPApp_surgeons.pdf)（2022，存取 2026-10-30）

**溝通不確定性**
- [B] van der Bles AM, van der Linden S, Freeman ALJ, Spiegelhalter DJ（2020）"The effects of communicating uncertainty on public trust in facts and numbers", *PNAS* 117(14):7672–7683, doi:10.1073/pnas.1913678117：5 個實驗（含 BBC 網站田野實驗；總 n=5,780）；傳達不確定性讓人感知到不確定，但信任只小幅下降；**數字範圍**對來源信任幾乎無顯著影響，**口語不確定性**對數字與來源信任下降較多；樣本為英國、教育程度偏高。— [PNAS 摘要轉述（ScienceDaily）](https://sciencedaily.com/releases/2020/03/200323152106.htm)；[CiNii 書目](https://cir.nii.ac.jp/crid/1360576123220091264)（2020，存取 2026-10-30）

**台灣健康識能數據**
- [A，經新聞轉述] 國健署 2021 年「國民健康訪問調查」：20 歲以上受訪者 30.1% 健康識能不足或有限；識能不足者有兩項以上慢性病比例 56%，良好者 15%（新聞引述，未見國健署原始報告）。— [聯合新聞網](https://udn.com/news/story/7266/9827044)；[Uho 優活](https://www.uho.com.tw/article-70542.html)（2025/2026 新聞，存取 2026-10-30）
- [A/C] 國衛院論壇文件：以台灣健康素養量表（THLS）調查，約 53.2% 高齡長者（65 歲以上）健康識能不佳（僅搜尋摘要，未開原文；量表與 2021 調查不同，不可直接比較）。— [國衛院論壇 PDF](https://forum.nhri.edu.tw/wp-content/uploads/108-4.%E6%88%91%E5%9C%8B%E9%AB%98%E9%BD%A1%E9%95%B7%E8%80%85%E5%81%A5%E5%BA%B7%E8%AD%98%E8%83%BD%E4%B9%8B%E6%B1%BA%E5%AE%9A%E5%9B%A0%E5%AD%90%E8%88%87%E5%85%B6%E5%81%A5%E5%BA%B7%E7%B5%90%E6%9E%9C-%E5%96%AE%E9%A0%81%E6%AA%A2%E8%A6%96.pdf)（存取 2026-10-30）
- [C] 慈濟護理文章：臺灣約 25%–30% 成年民眾有健康識能不足問題（僅搜尋摘要）。— [慈濟護理 PDF](https://nursing.tzuchi.com.tw/images/pdf/21-3/n16.pdf)（存取 2026-10-30）

**聊天機器人介入效果（系統性回顧）**
- [B] Laranjo L 等（2018）"Conversational agents in healthcare: a systematic review", *JAMIA* 25(9):1248–1258, doi:10.1093/jamia/ocy072；範圍為接受自由自然語言輸入的代理人；PROSPERO CRD42017065917（本輪僅核對書目，未讀結果細節）。— [UNSW 頁](https://npesu.unsw.edu.au/publication/conversational-agents-healthcare-systematic-review)；[Ovid](https://www.ovid.com/journals/jamia/pdf/10.1093/jamia/ocy072~conversational-agents-in-healthcare-a-systematic-review)（2018，存取 2026-10-30）
- [B] Milne-Ives M 等（2020）"The Effectiveness of Artificial Intelligence Conversational Agents in Health Care: Systematic Review", *JMIR* 22(10):e20346, doi:10.2196/20346：納入 31 篇（14 篇聊天機器人）；可用性 27/30、滿意度 26/31 表現好；有效性正向或混合 23/30；許多研究品質有限；使用者質性回饋比量化結果更混合；建議研究成本效益、隱私與安全。— [JMIR](https://jmir.org/2020/10/e20346/PDF)；[DOAJ](https://doaj.org/article/a00041a063e546299ab6af5e54158373)（2020，存取 2026-10-30）
- [B] Singh B 等（2023）"Systematic review and meta-analysis of the effectiveness of chatbots on lifestyle behaviours", *npj Digit Med* 6:118（doi:10.1038/s41746-023-00856-1）：19 篇（多為 RCT），3,567 人；聊天機器人對身體活動（SMD 0.28；中高強度 0.53）、蔬果攝取、睡眠有效；文字型／AI 聊天機器人在蔬果攝取上優於語音型；多數試驗品質低。— [Nature PDF](https://www.nature.com/articles/s41746-023-00856-1.pdf)（2023，存取 2026-10-30）

### Inferences
- **本報告推論**：每則 LINE 回覆採「一個主要訊息（第一行）→ 一個明確行動 → 紅旗清單（≤5 項）→ 小字說明研究性質」的四段式；第一行就是行動或結論（CCI：主要訊息置頂）。
- **本報告推論**：不向民眾顯示未校正分數或「可能性 xx%」；因（1）分數未校正、不是疾病機率；（2）口語機率詞解讀變異極大（Andreadis 2021）；改用「三類行動」：照片看不清楚請重拍／照片中看到可能需要注意的徵象，請告訴護理師／需要研究人員再看。若研究需要呈現不確定性，van der Bles 2020 支持用明確陳述（「這張照片模型不確定，已請人員複查」）比模糊口語詞較不傷信任。
- **本報告推論（teach-back 在 LINE 的變形）**：在「建議告訴護理師」訊息後加快速回覆按鈕「我會去告訴護理師」「我不在醫院」「我看不懂」——以選項回饋取代開放式複述，既可確認理解也可分流；「我看不懂」觸發更簡化版本或人工聯繫。
- **本報告推論**：因台灣約三成成人、更多長者健康識能不足，所有固定文案應以 CCI（中文化）自評 ≥90 分、並邀請 5–8 位長者／照顧者做理解測試後再定稿。
- 聊天機器人能否改善「及早通報靜脈炎」這類結果：**未找到可靠證據**；現有回顧多為生活型態／心理健康，且品質偏低——研究設計上應把「使用者收到建議後是否通知護理師」列為結果指標（**本報告推論**）。

### Gaps
- van der Bles 等 2019 *Royal Society Open Science*（題名 "Communicating uncertainty about facts, numbers and science"）本輪未再搜尋核對書目，引用前需核對 DOI。
- Trevena 等（IPDAS 風險溝通）本輪未搜尋，未核對。
- PEMAT（AHRQ Patient Education Materials Assessment Tool）可理解性／可行動性門檻：本輪搜尋未取得原文（未找到可靠證據，需另查 AHRQ PEMAT 頁）。
- 國健署「健康識能友善」素材製作指引或中文可讀性公式的官方文件：本輪未找到（未找到可靠證據）；需至 hpa.gov.tw 健康識能專區查詢。
- 國健署 2021 調查的原始報告與量表名稱未核對。

---

## Q3. 何時建議告訴護理師／就醫／急診：臨床依據的觸發條件

### Takeaway
業界慣例（多家 NHS 醫院衛教單）一致：留置針部位出現疼痛、紅、腫，**住院中要立刻告訴護理師**；拔除後問題最常見於 48 小時內，回家後若出現疼痛、紅、腫、流膿要找醫師；有感染徵象（紅腫、流液）英國衛教單要求「當天」看家醫科。VIP 量表把「一項輕微徵象」列為觀察、「兩項以上」即應更換部位，發燒（pyrexia）屬最高級。台灣緊急情況撥 119；1922 是疾管署傳染病專線，與靜脈炎無直接關係，不應放入文案。

### Cited Findings
- [A/業界] Jackson VIP（Visual Infusion Phlebitis）量表（Andrew Jackson, Rotherham；常引 1998 *Nursing Times* 94(4):68–71，部分版本標 1997/© 1999）：0＝健康，持續觀察；1＝僅一項：注射處輕微疼痛**或**輕微發紅→可能初期徵象，觀察；2＝兩項：疼痛、紅斑、腫脹→早期靜脈炎，**更換注射部位（resite）**；3＝中期（各版本對徵象描述不一），更換並考慮治療；4＝沿導管路徑疼痛、紅、硬／腫、**可觸及靜脈索**→進展期或血栓性靜脈炎開始；5＝4 的所有徵象＋**發燒**→進展性血栓性靜脈炎，開始治療。不同轉載版本措辭不一，正式使用前應核對原文。— [Solventum VIP Scorecard](https://assets.solventum.com/is/content/mmmspinco/VIP-Scorecard-for-VHP-websitepdf)；[ivteam VIP](https://ivteam.com/vipsn.pdf)（存取 2026-10-30）
- [A] NHS Lothian 衛教單（v2.0, 2020-02）：住院／帶留置針回家期間「If you have any pain, swelling or redness at the site please inform a nurse or doctor immediately」；留置針脫出時用乾淨紗布按壓至止血（2–5 分鐘或更久），止不住要聯絡單位、可能需回院；**拔除後感染「most common within the 48 hours after removal」**，持續觀察疼痛、紅、腫並就醫；文末列 NHS 24 (111) 與 999。— [NHS Lothian PDF](https://policyonline.nhslothian.scot/wp-content/uploads/2023/03/Discharge_home_with_Cannula_in_situ.pdf)（2020，存取 2026-10-30；已讀全文）
- [A/業界] York 醫院衛教單：任何時候疼痛，或留置針周圍腫、紅或任何異常，「tell a nurse straight away」，可能需拔除改打其他靜脈（僅搜尋摘要）。— [York Hospitals](https://yorkhospitals.nhs.uk/seecmsfile/?id=2747)（存取 2026-10-30）
- [A/業界] Northampton General 衛教單：拔除後若注射處腫、痛、紅或有分泌物，告訴護理師或家醫（僅搜尋摘要）。— [Northampton General](https://www.northamptongeneral.nhs.uk/Publications/Leaflets/IPC/Caring-for-my-cannula.aspx)（存取 2026-10-30）
- [A/業界] East & North Herts 輸血後衛教（V4, 2025-03）：留置針處紅腫或有分泌物可能為感染徵象，須「當天」看家醫，可能需要抗生素；非上班時間撥 NHS 111；疼痛腫脹也可能是瘀青，可冰敷抬高（僅搜尋摘要）。— [ENHerts PDF](https://www.enherts-tr.nhs.uk/wp-content/uploads/2019/10/Blood-Transfusion-Aftercare-advice-for-patients-V4-03.2025.pdf)（2025，存取 2026-10-30）
- [A] CDC/HICPAC O'Grady NP 等（2011）《Guidelines for the Prevention of Intravascular Catheter-Related Infections》（全文 PubMed 21511081；建議摘要版 *Clin Infect Dis* 2011 May;52(9):1087–99）；成人周邊導管「僅於臨床指徵時更換」被列為未解決議題，兒童則建議臨床指徵時更換。本輪**未找到 2017 年後針對周邊導管的更新**（未找到可靠證據）。— [PubMed 21511081](https://pubmed.ncbi.nlm.nih.gov/21511081/)；[PubMed 21467014](https://pubmed.ncbi.nlm.nih.gov/21467014/)（2011，存取 2026-10-30）
- [A] INS《Infusion Therapy Standards of Practice, 9th Edition》, *J Infus Nurs* 2024;47(1S Suppl 1):S1–S285（書目已核對）；靜脈炎／滲漏章節與病人衛教內容為付費內容，本輪未能取得原文。— [PubMed 38211609](https://www.pubmed.gov/38211609/)（2024，存取 2026-10-30）
- [C] 台灣護理文獻（airiti, 2015）：出現熱、痛、紅、可觸及靜脈索狀硬化時應立即更換周邊靜脈導管及輸液管路（僅搜尋摘要）。— [airiti 2015](https://www.airitilibrary.com/Article/Detail/15606619-201503-201505120023-201505120023-11-17)（存取 2026-10-30）
- [E] 康健知識庫（台灣衛教）：感染性靜脈炎為注射部位發硬合併紅、腫、熱、痛、灼熱感，可能沿血管變硬發紅壓痛；勿拉扯點滴、勿自行拔針，任何異常通知醫護；**勿自行冰敷、熱敷或按摩**（與部分英國衛教「冰敷抬高」不一致——台灣文案不宜給冷熱敷指示）。— [康健知識庫](https://kb.commonhealth.com.tw/library/576.html)（存取 2026-10-30）
- [A] 1922 為疾管署 24 小時免付費傳染病諮詢與疫情通報專線（亦可 0800-001922）——屬傳染病／防疫用途，非一般就醫諮詢。— [衛福部](https://www.mohw.gov.tw/cp-88-218-1.html)；[疾管署](https://www.cdc.gov.tw/MailBox)（存取 2026-10-30）
- [E] 119 為內政部消防署 24 小時緊急報案專線（救護車、火警）；手機無訊號可撥 112（依提示轉接 119）。— [Hello醫師](https://helloyishi.com.tw/healthy-habits/first-aid/how-to-call-an-ambulance/)（存取 2026-10-30）

### Inferences
- **本報告推論（觸發條件分層，供文案與規則使用；需臨床護理專家審定）**：
  - 第 0 層「任何結果都附的固定提醒」：注射處痛、紅、腫、變硬、摸到一條硬硬的血管、流膿或滲液、敷料濕或滲血、點滴不順／手臂冰冷腫脹（滲漏疑慮）→ **住院中：按呼叫鈴告訴護理師**；**已回家：當天聯絡原醫院或就醫**。
  - 第 1 層（模型輸出 stage 1，或使用者勾選 1 項輕微徵象）→ 「請告訴護理師看一下」，非緊急。
  - 第 2 層（模型輸出 stage 2，或 ≥2 項徵象）→ 「請盡快（現在）告訴護理師」（VIP≥2 臨床上即建議更換部位）。
  - 第 3 層（紅旗：發燒／發冷寒顫、紅線沿手臂往上延伸、流膿、整隻手臂腫、止不住的出血、胸痛或呼吸困難、意識改變）→ 住院中立即按鈴；在家立即就醫，**情況危急撥 119**。（紅線延伸、寒顫、胸痛呼吸困難為本報告依感染／血栓常識推論，未在本輪 [A] 來源逐條核對，需臨床審定。）
- **本報告推論**：明確區分「住院中」與「已出院／門診」兩種情境——第一次互動或每次上傳時以快速回覆按鈕詢問「你現在在醫院嗎？」，因為兩者的行動完全不同（按鈴 vs 自行就醫）；並把「拔針後 48 小時內仍要觀察」納入出院／門診版本（Lothian）。
- **本報告推論**：文案不給冷熱敷、按摩、用藥建議（台灣衛教來源與英國來源不一致，且屬治療建議）。
- **本報告推論**：不在文案中列 1922；台灣沒有對應 NHS 111 的全國非急症醫療諮詢號碼可引用（**未找到可靠證據**），故建議「聯絡為你打針的醫院／診所」，並由合作醫院提供其電話。
- 重要：模型判為「正常」時，絕不可省略第 0 層提醒（避免安全感錯置）。

### Gaps
- INS 2024 第 9 版靜脈炎、滲漏（infiltration/extravasation）的病人衛教原文未取得。
- 台灣醫學中心正式「周邊靜脈留置針／靜脈炎」衛教單 PDF 本輪未找到可直接引用版本（未找到可靠證據）；建議向合作醫院護理部索取其現行版本作為文案依據。
- 「post-infusion phlebitis 於拔除後 48 小時內出現」的 [B]/[C] 研究數據本輪未搜尋（僅有 Lothian 衛教單 [A] 陳述「感染最常見於拔除後 48 小時內」）。
- CDC 2011 指引之後是否有周邊導管的官方更新：未找到可靠證據。

---

## Q4. 無障礙與長者使用者

### Takeaway
LINE 是台灣最主要的即時通訊軟體（全體 80.10% 最常用），但 70 歲以上上網率只有 53.80%，許多長者需家屬代操作，因此流程必須允許「照顧者代傳」。LINE 內建字體放大幅度有限、主要依賴手機系統設定，Bot 端能控制的是：純文字訊息優先、Flex Message 必填 altText、按鈕大、選項少。LINE Bot 能接收語音訊息（audio 事件），台語語音辨識已有可本地部署的開源模型，但精確度需自行驗證，且不得送雲端 ASR。

### Cited Findings
**台灣長者與 LINE**
- [A] TWNIC《2025 台灣網路報告》（電訪 2025-07-28～09-01，加權，n=2,142）：即時通訊使用率 88.13%；**80.10% 民眾以 LINE 為最常用即時通訊軟體（上網者中 90.26%）**，FB Messenger 5.21%。上網率：60–69 歲 85%；**70 歲以上 53.80%**（2024 年 50.20%）。未上網者中 26.30% 表示「因年紀大而不想使用網路」；有上網需求但無人協助者中，51.72% 想上網處理「醫療服務」。（按年齡交叉的 LINE 使用率表格在 PDF 附錄，本輪無法可靠解析。）— [TWNIC 2025 全文 PDF](https://report.twnic.tw/2025/en/assets/download/TWNIC_TaiwanInternetReport_2025_CH_all.pdf)（2025，存取 2026-10-30；已以 pdftotext 讀取）

**LINE 平台能力**
- [A] LINE Messaging API Get profile 回應的 `language`：「User's language, as a BCP 47 language tag. Not included in the response if the user hasn't yet consented to the LINE Privacy Policy.」（LINE 官方 SDK @line/bot-sdk 11.0.0 型別定義，引自官方 API 說明）。— [unpkg @line/bot-sdk 11.0.0](https://unpkg.com/@line/bot-sdk@11.0.0/dist/messaging-api/model/userProfileResponse.d.ts)（存取 2026-10-30）
- [A] LINE 文件：取得使用者 profile 需使用者同意；同意只能在 LINE iOS／Android 版進行，未同意時 webhook 與 API 回應不含 profile 資訊。— [LINE Developers: Consent on getting user profile information](https://developers.line.biz/en/docs/messaging-api/user-consent/)（存取 2026-10-30）
- [A] Webhook 音訊訊息物件：`type: audio`、`id`、`duration`（選填，毫秒）、`contentProvider.type`（`line` 可用 Get content 取得二進位；`external`）。Get content：「Content is automatically deleted after a certain period from when the message was sent」，不保證保存期限；另有「確認影片／音訊準備狀態」端點。發送端亦有 Audio message 物件。— [LINE Messaging API reference（Markdown 版）](https://developers.line.biz/en/reference/messaging-api/index.html.md)（存取 2026-10-30）
- [E] Flex Message `altText` 上限 1,500 字元、未包 `type: flex` 與 altText 會 400 錯誤；altText 顯示於推播通知與聊天列表（日本技術部落格，未在 LINE 官方頁核對）。文字訊息上限 5,000 字元（多家廠商文件一致；KARTE 列 2,000 可能為其自身限制）。— [issoh.co.jp](https://www.issoh.co.jp/md/tech/11046)；[Pushwoosh LINE API](https://docs.pushwoosh.com/zh/developer/api-reference/line-api/index.md)；[Treasure Data](https://docs.treasure.ai/products/marketing-cloud/engage-studio/channels/line/line-oa-message-types)（存取 2026-10-30）
- [E] LINE 字體設定：設定→聊天→字體大小（小／中／大／特大），iOS 可選「按照 iPhone 設定」；此設定只影響聊天室訊息文字；內建「特大」放大有限，更大需靠 iOS 系統文字大小（可用控制中心限定 LINE）；Android 版好友列表等需靠手機系統設定。— [T 客邦](https://www.techbang.com/posts/81324-how-do-ios-users-change-the-line-font-size)；[SOGI](https://www.sogi.com.tw/articles/line/6261184)（存取 2026-10-30）
- LINE 與 VoiceOver／TalkBack 相容性官方說明：**未找到可靠證據**（搜尋無 LINE 官方說明中心頁面）。

**觸控目標、字級**
- [A] WCAG 2.2 SC 2.5.8 Target Size (Minimum)（AA）：指標輸入目標至少 24×24 CSS px（例外：間距、等效控制、行內、user agent、必要）；W3C 建議重要控制可採更嚴格的 2.5.5（AAA）。— [W3C Understanding 2.5.8](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html)（存取 2026-10-30）
- [E] Apple HIG 控制項預設目標 44×44 pt；Material Design 建議觸控目標至少 48×48 dp（約 9 mm）；WCAG 2.5.5 AAA 為 44×44 CSS px（均為二手來源轉述，未開官方頁）。— [frontendchecklist](https://frontendchecklist.io/rules/accessibility/touch-targets)；[Adrian Roselli](https://adrianroselli.com/2019/06/target-size-and-2-5-5.html)（存取 2026-10-30）
- [B] JMIR mHealth uHealth 2023 系統性回顧（Design Guidelines of Mobile Apps for Older Adults; PMC10557006）：基於 60 歲以上使用者可用性測試，歸納 28 條指引，「simplify」與「加大互動控制項尺寸與間距」最重要（僅搜尋摘要）。— [PMC10557006](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10557006/)（2023，存取 2026-10-30）
- [B] 2025 *Aging Clinical and Experimental Research* 系統性回顧（PMC12350549）：篩 1,556 筆、納 132 篇；強調簡化導覽、放大文字與觸控目標、語音互動、容錯介面（僅搜尋摘要）。— [PMC12350549](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12350549/)（2025，存取 2026-10-30）
- [C] OzCHI 2024 論文：長者偏好行動 App 最小 14 pt、無襯線字體（僅搜尋摘要）。— [OzCHI 2024 PDF](https://outbox.eait.uq.edu.au/uqsville/OzCHI2024/Long%20Papers/Design%20for%20Older%20People%20-%20Improving%20the%20Usability%20of%20Mobile%20Apps%20through%20Targeted%20Design%20Recommendations.pdf)（2024，存取 2026-10-30）

**台語語音辨識（本地可部署選項）**
- [E/模型卡] MediaTek Research MR Breeze ASR 25：基於 Whisper，Apache 2.0 開源，主打台灣華語口音與中英混合（非台語專用）。— [MediaTek 新聞稿](https://www.mediatek.com/zh-tw/press-room/mediatek-research-unveils-mr-breeze-asr-25-an-open-source-ai-model-for-taiwanese-speech)（存取 2026-10-30）
- [E/模型卡] Speech-AI-Research-Center BreezeASR（Taigi／Breeze-ASR-26 頁）：以約一萬小時**合成**台語語音微調 Whisper；模型頁稱華語版 ASR25 在台語上錯誤率 30.71%–76.85%，故需台語專用模型（僅搜尋摘要；自報數據，未獨立驗證）。— [Hugging Face Breeze-ASR-26](https://huggingface.co/Speech-AI-Research-Center/Breeze-ASR-26)（存取 2026-10-30）
- [A/E] 數位發展部數位產業署「Taiwan Tongues ASR CE」：開源，支援國語、台語、客語、英語，本地多語混合辨識，提供 CTranslate2 推論模型；由台灣大哥大執行維護（114 年計畫成果）。— [GitHub adi-gov-tw/Taiwan-Tongues-ASR-CE](https://github.com/adi-gov-tw/Taiwan-Tongues-ASR-CE)（存取 2026-10-30）
- [E/模型卡] 臺南大學 NUTN-KWS Whisper-Taiwanese-model-v0.5（whisper-large-v3-turbo 微調，約 90 小時含教育部辭典語料）；linshoufan whisper-small-nan-tw（Common Voice 閩南語）。— [HF NUTN-KWS](https://huggingface.co/NUTN-KWS/Whisper-Taiwanese-model-v0.5)；[HF linshoufan](https://huggingface.co/linshoufan/linshoufan-whisper-small-nan-tw)（存取 2026-10-30）

### Inferences
- **本報告推論（Bot 端可控的無障礙設計）**：
  1. 關鍵訊息一律用**純文字訊息**（可被系統字級與螢幕閱讀器處理），Flex／圖文選單只作輔助；Flex 的 `altText` 必須寫成完整可行動的一句話（因推播通知與聊天列表只顯示 altText），例：「照片太暗，請在亮處重拍一次」而非「分析結果」。
  2. 快速回覆按鈕 ≤3–4 個、標籤 2–6 字、動詞開頭（「重新拍照」「我在醫院」「找真人」）；Flex 按鈕高度以 ≥48 dp／44 pt 為目標（超過 WCAG 2.5.8 的 24 px 下限）。
  3. 一則訊息 ≤ 約 120 個中文字為目標（長者螢幕放大後仍可一屏讀完；此數字為推論，無直接證據）。
  4. 不以顏色作唯一訊號（紅／綠燈），每個狀態都有文字。
  5. 允許「照顧者代傳」：同意流程需區分「本人」與「代傳者」（70+ 上網率僅 53.8%）。
- **本報告推論（語音）**：LINE Bot 可接收長者錄的語音訊息；若要辨識，**只能用本地部署模型**（Taiwan Tongues ASR CE、Breeze 系列、NUTN 模型），**不可**使用 LINE 以外的雲端 ASR（違反資料不出境／不給第三方雲端原則）。但目前台語 ASR 對長者口音、醫療用詞的錯誤率未知，且錯誤辨識可能導致錯誤分流——建議第一階段**不以 ASR 自動判讀**，而是：收到語音即回「我們收到您的語音，會請研究人員聽」並轉人工，或提供固定按鈕選項；ASR 僅作研究評估。注意 Get content 內容會被 LINE 自動刪除，若研究要保存語音需在同意書載明並本地保存。
- **本報告推論**：Bot 回覆可附**預錄真人台語語音**（Audio message）作為固定模板的朗讀版，避免雲端 TTS。

### Gaps
- TWNIC 依年齡別的 LINE 使用率（60+/65+）數值：PDF 附錄表格無法可靠解析（未取得具體數字）。
- LINE 官方對 VoiceOver／TalkBack 支援程度、Flex Message 是否被螢幕閱讀器朗讀 altText 或內容：未找到可靠證據（需實機測試）。
- LINE 官方 altText 1,500 字元與文字 5,000 字元上限未在官方頁核對。
- NCC 或其他官方對長者使用 LINE 聊天機器人的調查：未找到。
- 台語 ASR 模型在長者自然語音、醫療情境的獨立評測：未找到可靠證據。
- Apple HIG／Material 官方頁未直接開啟（僅二手轉述）。

---

## Q5. 多語：台語書寫、英文、東南亞語，以及 LINE 語言設定

### Takeaway
LINE profile 的 `language` 欄位可作為預設回覆語言的線索，但未同意 LINE 隱私政策者不會回傳，且手機語言不等於閱讀偏好，因此必須提供手動切換。台灣社福移工約 23 萬人（2026 年中），多為家庭看護工，主要來自印尼；照顧者版本應優先做印尼文、越南文、英文（菲律賓）。書寫台語（台羅或漢字）多數長者「會講不會讀」的說法普遍，但未找到全國性數據；不宜用書寫台語作主要文案，改用華語文字＋台語真人錄音。機器翻譯醫療指示有實證的誤譯風險，且雲端翻譯違反資料原則，應採「固定模板＋專業翻譯＋回譯／母語者審查」。

### Cited Findings
**LINE 語言**
- [A] Get profile `language`：BCP 47 語言標籤；使用者未同意 LINE 隱私政策時不回傳（見 Q4）。— [unpkg @line/bot-sdk 11.0.0](https://unpkg.com/@line/bot-sdk@11.0.0/dist/messaging-api/model/userProfileResponse.d.ts)；[LINE consent 文件](https://developers.line.biz/en/docs/messaging-api/user-consent/)（存取 2026-10-30）

**移工／看護工人數**
- [A] 勞動部年度統計：112 年底產業及社福移工 75.3 萬人，其中社福移工 23.4 萬人（僅搜尋摘要）。— [勞動部 12 外籍工作者 PDF](https://www.mol.gov.tw/media/aklhtid2/12-外籍工作者.pdf)（存取 2026-10-30）
- [A] 政府資料開放平臺「115 年產業及社福移工勞工人數」資料集（2026-03-25 上架），依國籍列產業／社福人數；資料集 177127。— [data.gov.tw 新聞](https://data.gov.tw/news/32041)；[資料集 177127](https://data.gov.tw/dataset/177127)（存取 2026-10-30）
- [E，引勞動部] 2026 年 1 月底在臺移工突破 87 萬；社福移工 22 萬 7,730 人，其中看護工 20 萬 9,221 人。— [PIDI 2026-03-09](https://www.pidi.com.tw/post/2026-03-09-01)（存取 2026-10-30）
- [E，引勞動力發展署] 2026 年 6 月底移工 89 萬 5,115 人；社福移工 231,175 人（家庭看護工 212,209、養護看護工 16,537）；國籍：印尼 335,391、越南 301,885、菲律賓 185,315、泰國 72,515（全產業合計）。— [Manstrong 2026](https://www.manstrong.com.tw/news-detail/taiwan-migrant-workers-2026)（存取 2026-10-30）
- 注意：上述 [E] 數字口徑不同（在臺人數 vs 有效聘僱許可），且「看護工依國籍」細分未取得；看護工以印尼籍為最大宗為業界普遍說法，本輪未取得官方細表核對。

**台語書寫**
- [A] 教育部「臺灣閩南語羅馬字拼音方案」原 95-10-14 公告，113-08-26 修正並改稱「臺灣台語羅馬字拼音方案」。— [教育部台羅使用手冊 113 修訂](https://language.moe.gov.tw/files/people_files/tshiutsheh_1130826.pdf)（2024，存取 2026-10-30）
- [A] 教育部「臺灣閩南語推薦用字」96–98 年分 3 批公告，共 700 字詞（另一較早文件稱 400 字詞，係前兩批；以 700 為最新）（僅搜尋摘要）。— [教育部語言網 D004](https://language.moe.gov.tw/001/Upload/files/site_content/M0001/mina/D/D004.pdf)（存取 2026-10-30）
- 「多數長者會說台語但不會讀台羅／台語漢字」：**未找到可靠的全國性數據**；只有清大博士論文（國中生語言狀況）、大學生態度調查與觀點文章（[清大 ETD](https://etd.lib.nthu.edu.tw/detail/9d54cfa08232c5951d4ac54ef7487268)、[關鍵評論網](https://www.thenewslens.com/article/39000)）。

**機器翻譯醫療指示的風險**
- [C] Khoong EC 等（2019, *JAMA Intern Med*）：100 份急診出院指示 647 句以 Google Translate 譯為西文／中文，準確 92%／81%；不準確譯句中具臨床顯著傷害可能者西文 2%、中文 8%；錯誤與醫療術語、長句、口語相關（例："hold the kidney medicine" 被譯成「繼續服用」）。作者建議搭配人工並提供英文原文。— [ScienceDaily 2019](https://www.sciencedaily.com/releases/2019/02/190225123451.htm)；[PMC6450297](https://pmc.ncbi.nlm.nih.gov/articles/6450297)（2019，存取 2026-10-30）
- [C] （2021, *J Gen Intern Med*；作者未於本輪核對）"A Pragmatic Assessment of Google Translate for Emergency Department Instructions"：20 句常見出院指示 × 7 語言，整體保留原意 82.5%（330/400），西文 94%、亞美尼亞文 55%；結論：不應依賴於病人指示。— [PubMed 33674922](https://pubmed.ncbi.nlm.nih.gov/33674922/)（2021，存取 2026-10-30；題名與數據依搜尋摘要）
- [C] Kong 等（2025, *BMJ Qual Saf*）：ChatGPT-4 與 Google Translate 譯急診指示，句級準確率西文 97%/96%、中文 95%/90%（僅搜尋摘要）。— [BMJ Qual Saf 35(3):150](https://qualitysafety.bmj.com/content/35/3/150)（存取 2026-10-30）

### Inferences
- **本報告推論（語言選擇流程）**：
  1. 首次互動以 `language` 欄位預選（zh-TW→華語；id→印尼文；vi→越南文；en/fil/tl→英文；無欄位→華語），**但第一則訊息一定附「語言」切換按鈕**（中文／English／Bahasa Indonesia／Tiếng Việt），並記住使用者選擇。手機語言設定為英文的本地人很多，不能只靠欄位。
  2. 「照顧者代傳」情境：移工看護可能幫雇主（長者）傳照片——回覆語言應以「傳訊者」為準，但「告訴護理師／家屬」的段落可附一行華語，方便看護直接拿給護理師看（**本報告推論**）。
- **本報告推論（台語）**：不以台羅或台語漢字作主要書寫版本（長者閱讀能力未知、無數據支持其可讀性）；改提供**預錄的台語真人語音**（固定模板，數量少、可由台語母語醫護錄製），文字維持華語。若要試台語文字，限於少數高頻口語（如「緊共護理師講」）並做長者理解測試。
- **本報告推論（翻譯品質）**：只翻譯**固定模板**（約 10–15 則），不做即時機器翻譯；流程：專業譯者翻譯→另一位譯者回譯→雙語醫護／母語照顧者審查→5 位以上目標使用者理解測試；同意書（consent）必須專業翻譯。**任何雲端翻譯 API（Google/DeepL/LLM 雲端）都會把使用者訊息送到第三方，違反原則**；本地替代：預譯模板（零執行期翻譯）；若需處理使用者自由輸入，僅轉人工，或在研究評估中測試本地開源翻譯模型（不用於對使用者的即時回覆）。
- **本報告推論**：短句、避免醫療術語與否定句雙重否定，可降低翻譯錯誤（Khoong 2019 顯示錯誤與術語、長句相關）。

### Gaps
- 社福移工依國籍細分（印尼／越南／菲律賓看護工各多少）之官方數字：本輪未直接從勞動統計查詢網取得。
- 長者「會講台語但不會讀台語文」的量化數據：未找到可靠證據。
- 印尼文、越南文醫療文案的機器翻譯準確度研究（Khoong 2019 只有西、中文；JGIM 2021 的 7 種語言未含印尼、越南）：未找到可靠證據。
- LINE `language` 欄位在台灣使用者中的實際分布：無資料。

---

## Q6（交付項）. 繁體中文回覆模板草案（全部為「本報告推論」）

### Takeaway
以下 7 組模板依 Q1–Q5 證據設計：第一行即主要訊息／行動（CDC CCI）、一則一事、短句、避免「診斷／治療／機率」字眼、每則結果都附紅旗與「住院中 vs 在家」分流、按鈕動詞開頭且 ≤4 個。**全部標記為本報告推論**，上線前必須經臨床護理專家、IRB、法規顧問審閱，並做長者與照顧者理解測試（teach-back／快速回覆確認）。

### Cited Findings
- 設計依據已列於 Q1（免責聲明效果有限、需具體警示）[C]、Q2（CCI 單一主要訊息與行動 [A]、口語機率詞變異 [B]、不確定性陳述 [B]、AHRQ teach-back [A]）、Q3（NHS 衛教單紅旗與 48 小時 [A]、VIP 分級 [A/業界]、119 [E]）、Q4（altText、按鈕尺寸 [A]/[E]）、Q5（翻譯風險 [C]）。本節不新增來源。

### Inferences

> 共通格式（本報告推論）：〔第一行：結論或行動〕→〔為什麼／怎麼做，≤3 點〕→〔紅旗或下一步〕→〔小字：研究性質一句〕。【】為快速回覆按鈕；〈〉為變數。

**T1 同意請求（首次加入／首次上傳前）**
```
您好，這是〈醫院/研究團隊〉的「打針部位照片研究」。
這是研究，不是看病，結果不能代替醫師或護理師。

參加的話，會請您傳手臂打針部位的照片：
1. 照片只用在研究，存在〈醫院〉的電腦，不會給其他公司。
2. 您隨時可以退出，也可以要求刪除照片。
3. 不參加，完全不影響您的治療。

完整說明請看：〈同意書連結〉
有問題可以找真人：〈研究聯絡電話〉

【我同意參加】【先看完整說明】【我不參加】【我是幫家人傳】
```
理由：第一段先講「這是研究、不是看病」（Q1）；三點分段（chunking，AHRQ）；「不影響治療」為受試者保護常規；「我是幫家人傳」處理照顧者代傳（Q4：70+ 上網率 53.8%）；資料不給其他公司對應無第三方雲端原則；完整同意書需專業翻譯（Q5）。

**T2 拍照上傳說明**
```
請拍「打針的地方」，照這樣拍：
1. 在亮的地方拍，不要開閃光燈。
2. 手機離手臂大約一個手掌遠。
3. 整個貼布和周圍皮膚都要拍進去。
4. 一次傳一張就好。

拍好直接傳到這裡。

【怎麼拍？看範例圖】【我現在在醫院】【我已經回家】
```
理由：可行動步驟、數字清單、每句一事（CCI／AHRQ）；「一個手掌遠」以具體參照取代公分（**本報告推論**）；同時收集「住院 vs 在家」情境供後續分流（Q3）。範例圖的 altText 需寫「範例：手臂打針處、貼布在畫面中間的照片」。

**T3 照片品質不足，請重拍**
```
這張照片看不清楚，請再拍一次。
原因可能是：〈太暗／太模糊／打針的地方不在畫面裡〉

小提醒：到亮一點的地方，手拿穩再拍。

不管照片結果如何，如果打針的地方很痛、變紅、腫起來，
在醫院請直接按鈴告訴護理師。

【重新拍照】【看拍照範例】【我不會拍，找真人】
```
理由：第一行就是行動；不責怪使用者（「照片看不清楚」而非「您拍錯」）；具體原因＋具體改善；即使重拍也附最小紅旗提醒，避免使用者因為「沒有結果」而延誤（Q1/Q3）。

**T4 需要人工複查（模型不確定）**
```
這張照片，研究系統沒辦法判斷，已經請研究人員再看一次。
我們會在〈時間，例如：上班時間 24 小時內〉回覆您。

等待的時候，請注意：
如果打針的地方痛、紅、腫、變硬，或流膿、發燒，
・在醫院：現在就按鈴告訴護理師，不用等我們。
・已經回家：請聯絡幫您打針的醫院或診所。

這是研究系統，不是醫師的判斷。

【好，我知道了】【我在醫院】【我已經回家】
```
理由：用明確的不確定性陳述而非「可能」「也許」（van der Bles 2020：口語不確定性較傷信任；Andreadis 2021：機率詞解讀變異）；明說等待時間；強調「不用等我們」以防系統延誤真正求助（Q1 automation bias）；「好，我知道了」作為簡易 teach-back 確認（Q2）。

**T5 建議告訴護理師／就醫（模型輸出 stage 1 或 stage 2）**
住院版：
```
請告訴護理師看一下您打針的地方。〈stage 2 時：請現在就按鈴。〉

研究系統在照片中看到〈發紅／腫起來〉的樣子。
這不是診斷，要由護理師親自看才算數。

如果有下面任何一種，請馬上按鈴：
・越來越痛　・紅的範圍變大　・摸起來硬硬的、像一條線
・流膿或滲水　・發燒、發冷

【我會告訴護理師】【我看不懂】【找真人】
```
在家／門診版：
```
建議今天聯絡幫您打針的醫院或診所，請他們看一下。

研究系統在照片中看到〈發紅／腫起來〉的樣子。
這不是診斷，要由醫師或護理師親自看才算數。
打針的地方拔針後 2 天內，仍要每天看一下。

如果發燒、發冷、紅線往上延伸，或整隻手臂腫起來，
請馬上去醫院；很嚴重時撥 119。

【我會聯絡醫院】【我看不懂】【找真人】
```
理由：第一行即行動（CCI）；「照片中看到…的樣子」取代「您有靜脈炎第 2 期」（Q1）；不顯示分數或期別給民眾（Q2；期別可存研究資料庫供人工檢視）；紅旗 ≤5 項、口語化（「像一條線」＝palpable cord，「發燒」＝VIP 5）；在家版納入拔針後 48 小時觀察（Lothian）；不給冷熱敷建議（台灣衛教「勿自行冰熱敷」）；「我會告訴護理師／我看不懂」為快速回覆式 teach-back（AHRQ）。stage 1 與 stage 2 差別只在第一行緊急度（VIP：1 項＝觀察、2 項＝更換部位）。

**T5b 「正常」結果（補充，避免錯誤安心）**
```
這張照片中，研究系統沒有看到明顯的紅或腫。
但照片看不出痛不痛、硬不硬，請繼續注意。

只要打針的地方痛、紅、腫、變硬、流膿，或發燒，
在醫院請按鈴告訴護理師；在家請聯絡醫院或診所。

這是研究系統，不是醫師的判斷。
【好，我知道了】
```
理由：寫「沒有看到明顯…」而非「沒有靜脈炎」；明說照片的限制（疼痛、硬度、發燒無法從照片判斷）；紅旗不省略（Q1/Q3）。

**T6 緊急轉介（使用者文字／按鈕回報紅旗，或系統偵測關鍵字）**
```
這可能需要馬上處理，請不要等研究系統回覆。

・在醫院：現在按床邊的呼叫鈴，找護理師。
・在家：請立刻去急診。
・如果呼吸困難、胸痛、昏昏沉沉叫不醒、或流血止不住：
  請立刻撥 119。

這個帳號沒有人 24 小時看訊息，緊急時請不要只傳訊息給我們。

【我在醫院，去按鈴】【撥打 119】
```
理由：第一行即「不要等」（防 automation bias 與延誤）；明說帳號非 24 小時監看（研究原型的真實限制，避免使用者以為有人在看）；119 為台灣救護專線（[E] 來源），不列 1922（屬傳染病專線，Q3）；「撥打 119」按鈕可用 LINE URI action `tel:119`（**本報告推論**，需實機測試）；胸痛呼吸困難等條目為一般急症常識、非靜脈炎特異，需臨床審定。止血：留置針脫出按壓 2–5 分鐘（Lothian）可在 T6b 單獨說明，避免本則過長。

**T7 撤回同意確認**
```
已收到，您已退出照片研究。

・從現在起，我們不會再使用您之後傳的照片。
・您之前的照片：〈依同意書：將在 N 天內刪除／已去識別的研究資料無法再分開，會保留〉。
・退出不會影響您的治療。

如果改變主意，隨時可以按【重新參加】。
有問題請找：〈研究聯絡電話〉

【重新參加】【我還有問題，找真人】
```
理由：第一行確認結果；明說「之後」與「之前」資料的處理（需與同意書、個資處理一致，細節見 05_consent 章節）；重申不影響治療；提供可逆路徑。

**多語與無障礙實作備註（本報告推論）**
- 上述 8 則為「固定模板」：專業翻譯成英文、印尼文、越南文，回譯＋母語照顧者測試；台語提供真人預錄語音版（T5、T6 優先）。不使用雲端翻譯或雲端 TTS／ASR。
- 每則以純文字送出；若加 Flex 卡片，altText = 第一行全文。
- 字數控制：每則 ≤ 約 120–150 字；長者測試時請受測者以手機系統最大字級閱讀。
- 用 CDC CCI（中文自譯版）逐則評分，目標 ≥90；記錄於研究文件。

### Gaps
- 以上模板未經任何使用者測試、臨床審定或法規審閱。
- 「24 小時內回覆」「拔針後 2 天」等時間承諾需依研究人力與合作醫院流程確認。
- 台灣是否有可放入文案的「非急症醫療諮詢」全國專線：未找到可靠證據（故模板寫「聯絡幫您打針的醫院或診所」）。
- LINE `tel:` URI action 在 iOS／Android LINE 內的實際行為未驗證。
