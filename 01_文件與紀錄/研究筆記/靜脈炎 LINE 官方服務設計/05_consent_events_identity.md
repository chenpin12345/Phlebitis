# 研究同意、撤回、LINE 帳號事件與身分設計（LINE 官方帳號研究原型，台灣）

> 範圍：本節只處理「同意／撤回／LINE 事件／身分與假名化」的設計面。法規細節由另一節負責，此處只摘要與設計直接相關者。
> 標示：來源等級 [A] 官方/主管機關/標準、[B] 系統性回顧/頂級期刊會議、[C] 同儕審查、[D] 預印本、[E] 部落格/範例碼/論壇（僅輔助）。
> 存取日期：搜尋於 2026-10-30 開始、因額度中斷後於 2026-10-31 完成；下列每筆來源的存取日期標為實際存取日 2026-10-31。
> 證據層次用語：**研究證據顯示**（有文獻）／**業界慣例**（官方文件或常見實作）／**本報告推論**（作者推理，需 IRB/法務確認）。
> 數據規模：目前約 120 張照片／14 位病人；未來約 1,000 張。撤回 1 位病人 ≈ 1/14 ≈ 7% 的受試者（照片占比依該人張數而定）。

---

## A1. 電子／遠距知情同意（eConsent）實務與證據；FDA/OHRP 2016 指引；台灣是否有電子同意指引

### Takeaway
研究證據顯示 eConsent 的理解度與滿意度「不劣於、部分優於」紙本，但證據品質參差；FDA/OHRP 2016 年 12 月最終版 Q&A 仍為現行美國指引（未找到取代版）。台灣**未找到**衛福部層級的「人體研究電子同意指引」；可找到的是醫院 IRB 層級文件（臺大醫院〈網路研究倫理審查指引〉2020-09），允許以「我同意」點選鍵代替簽名並要求留存帶時間戳記的同意紀錄。

### Cited Findings
- **FDA/OHRP 指引**：「Use of Electronic Informed Consent in Clinical Investigations: Questions and Answers」，Final，2016 年 12 月（Federal Register 2016-12-15），Docket FDA-2015-D-0390，由 FDA 與 HHS OHRP 共同準備；FDA 頁面「Content current as of 05/05/2020」。— [A] [FDA guidance page](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/use-electronic-informed-consent-clinical-investigations-questions-and-answers)（doc 2016-12；存取 2026-10-31）；OHRP 對應頁 [HHS OHRP](https://www.hhs.gov/ohrp/regulations-and-policy/guidance/use-electronic-informed-consent-questions-and-answers/)（本次 WebFetch 回 403，未能讀取全文）。
- 最終版相較 2015 草案，在全部 16 題 Q&A 均有釐清，其中包括「如何驗證電子簽署者身分」；身分驗證 Q&A 與 21 CFR Part 11 對簽署者身分驗證的要求相關。— [E] [RAPS 報導](https://www.raps.org/resource/electronic-informed-consent-final-q-a-spells-out.html)（doc 2016-12；存取 2026-10-31；二手報導）
- 機構實作：Yale HRPP eConsent 指引（2025-03-31）引用該 Q&A，建議以 email 驗證、安全登入憑證或生物辨識驗證身分；WVU REDCap 指引描述遠距簽署時以視訊檢視證件為標準做法。— [E/機構文件] [Yale eConsent Guidance 2025-03-31](https://research-support.yale.edu/sites/default/files/2025-08/eConsent%20Guidance_FINAL_20250331.pdf)；[WVU REDCap eConsent guide 2022-08](https://human.research.wvu.edu/files/d/352b8595-f6a7-490a-b6fe-24353040c3d2/econsenting-using-redcap-start-guide-aug2022.pdf)（存取 2026-10-31；僅經搜尋摘要，未讀全文）
- **系統性回顧**：Cohen et al., JMIR 2023「Comparative Effectiveness of eConsent: Systematic Review」：納入 37 篇出版物／35 項研究、共 13,281 名參與者；20 項研究比較 eConsent 與紙本的理解度（10 項「高效度」），其中高效度研究有 6 項報告至少部分概念的理解顯著較佳；比較可接受度的 8 項研究（631 人）均報告滿意度較高或相當（僅 1 項為高效度）；eConsent 的完成時間（cycle time）較長，作者推測反映較高參與度。作者群含 AstraZeneca 員工（利益衝突需註記）。— [B] [JMIR 2023;e43883](https://jmir.org/2023/1/e43883/PDF)（doc 2023；存取 2026-10-31）
- 低資源情境系統性回顧（2025，PMC12596901）：多媒體、離線平板、網頁、AI 輔助 e-consent 一致改善理解與滿意度、減少文件錯誤（摘要層級資訊，未逐研究設計拆分）。— [B] [Bridging the Gap… PMC12596901](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12596901/)（doc 2025；存取 2026-10-31）
- IRB 審查慣例（廠商整理）：IRB 應以受試者實際看到的互動形式（含超連結）審查，而非截圖；不應設計可跳過關鍵研究資訊的 skip logic；需考量數位可近性。— [E] [Castor blog 2021-07-16](https://www.castoredc.com/blog/how-to-prepare-irb-submission-remote-econsent-study/)；[Advarra blog](https://www.advarra.com/blog/regulatory-and-ethical-considerations-for-econsent-in-research/)（存取 2026-10-31）
- **台灣**：臺大醫院研究倫理委員會〈網路研究倫理審查指引〉（2020-09）：網路研究應確保自主參與、知情同意、隱私與風險衡量；網頁可設「我同意」點選鍵以電子方式代替簽名；需告知資料傳輸可能被第三方截取之風險。臺大另有「網路研究自評表」（AF-143-02），要求線上工具能留存同意紀錄並附時間戳記；以電子方式回覆即視為同意者，須申請免除書面同意。— [A-機構] [臺大醫院網路研究倫理審查指引 202009](https://www.ntuh.gov.tw/ckfinder_file/RECO/files/02.%E6%A8%99%E6%BA%96%E4%BD%9C%E6%A5%AD%E6%B5%81%E7%A8%8B/%E5%8F%B0%E5%A4%A7%E9%86%AB%E9%99%A2%E7%B6%B2%E8%B7%AF%E7%A0%94%E7%A9%B6%E5%80%AB%E7%90%86%E5%AF%A9%E6%9F%A5%E6%8C%87%E5%BC%95202009.pdf)；[AF-143-02 網路研究自評表](https://www.ntuh.gov.tw/ckfinder_file/RECO/files/06.%E6%96%87%E4%BB%B6%E4%B8%8B%E8%BC%89(%E6%96%B0%E6%A1%88)/AF-143-02_1%E7%B6%B2%E8%B7%AF%E7%A0%94%E7%A9%B6%E8%87%AA%E8%A9%95%E8%A1%A8.doc)（存取 2026-10-31；經搜尋摘要確認，未逐頁精讀）
- 人體研究法第 12 條第 2 項：研究計畫應依「審查會審查通過之同意方式及內容」取得同意 → 電子同意形式本身須經 IRB 核准。— [A] [全國法規資料庫 人體研究法](https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=L0020176)（最新修正 民國 108-01-02；存取 2026-10-31）

### Inferences
- 本報告推論：在 LINE 情境，最接近臺大「網路研究」模式（點選同意 + 時間戳紀錄 + 申請免除書面同意簽名），而非 FDA Part 11 等級電子簽章；本專案非 FDA 管轄臨床試驗，但 FDA/OHRP Q&A 可作設計參考（分層呈現、理解度檢核、提供同意書副本、版本管理）。
- 本報告推論：建議「分層同意」：第 1 層 Flex 卡摘要 4–6 點（研究目的、拍什麼、非診斷、資料存放於本地不上第三方雲、可隨時撤回且立即生效、聯絡人），第 2 層 LIFF 完整說明書；同意前 2–3 題是非題（teach-back），例如「本服務會告訴我是否得了靜脈炎？（否）」「我可以隨時撤回嗎？（可）」，答錯顯示說明後重答，不以分數排除。
- 業界慣例 vs 研究證據：quiz/teach-back 在 eConsent 系統常見，但本次未找到專門針對「聊天 App 內 quiz」效果的高品質研究。

### Gaps
- 未找到衛福部或醫事司發布的「人體研究電子同意」正式指引（兩輪搜尋：中文「人體研究 電子同意 指引」、「臺大 電子簽署 遠距 線上同意」）。北榮 IRB eConsent SOP：未找到可靠證據。
- FDA/OHRP Q&A 全文（含身分驗證題號與具體措辭）因 403 未能直接讀取；細節取自二手報導。
- 2024 年 FDA/OHRP「Key Information and Facilitating Understanding in Informed Consent」草案是否影響 eConsent：本次未檢索，未驗證。
- 專門針對 LINE/WhatsApp 等聊天機器人 eConsent 的實證研究：未找到可靠證據。

---

## A2. 在 LINE 內實作同意：LIFF 頁 vs Flex Message + postback；可證明什麼、限制；何時需簽名或 LINE Login ID token

### Takeaway
LINE webhook 能提供的證據只有「某個 provider-scoped userId 在某時點按了某個 postback」；它**不能證明真實身分、年齡或是否為本人**。若 IRB 要求較強的「同意者為本人」證據或需與醫院病人身分綁定，應在 LIFF/LINE Login（openid scope 取得 ID token 並於伺服器驗證）之上，再加研究人員當面發放的一次性登錄碼。

### Cited Findings
- userId 透過 webhook event 的 `source` 物件取得；「若使用者未同意存取其 profile，webhook 不含 user ID」。— [A] [LINE Developers: Get user IDs](https://developers.line.biz/en/docs/messaging-api/getting-user-ids/)（存取 2026-10-31）
- LINE Login v2.1：只有在請求 `openid` scope 時才會回傳 ID token（JWT）。— [A] [LINE Login v2.1 API reference](https://developers.line.biz/en/reference/line-login/)（存取 2026-10-31；經搜尋摘要）
- 取得 email 需先在 LINE Developers Console（Basic settings → OpenID Connect）申請 Email address permission；驗證回應的 `scope` 欄位即使已授權也不會列出 email，應檢查 ID token 中的 `email` claim。— [A] [Integrating LINE Login with your web app](https://developers.line.biz/en/docs/line-login/integrate-line-login/index.html.md)（存取 2026-10-31）
- 人體研究法第 12 條第 1 項：研究對象以「有意思能力之成年人」為限，例外為研究顯有益於特定人口群或無法以其他研究對象取代者；第 14 條要求以研究對象「或其關係人、法定代理人、監護人、輔助人」可理解之方式告知。— [A] [人體研究法](https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=L0020176)（存取 2026-10-31）
- 遠距 eConsent 的身分驗證會因不在場而複雜化；FDA/OHRP 最終版 Q&A 有專題處理身分驗證。— [E] [RAPS](https://www.raps.org/resource/electronic-informed-consent-final-q-a-spells-out.html)（存取 2026-10-31）

### Inferences
- 本報告推論（設計比較）：
  - **Flex Message + postback**：最簡單；postback `data` 帶 `consent_version` 與 `doc_hash` 前綴即可；但使用者看到的長文受 Flex 版面限制，「顯示了什麼全文」較難證明（只能證明伺服器送出了哪個 Flex JSON）。
  - **LIFF 頁**：可完整呈現分層說明書、捲動到底才啟用按鈕、quiz、送出時由 LIFF 取得 ID token 送後端驗證（後端呼叫 LINE verify endpoint，比對 `aud`=channel ID、`exp`、`sub`），以 `sub` 對應 Messaging API userId（同 provider 時相同，見 C1）。LIFF 頁由本地 FastAPI 提供則需對外 HTTPS（如 tunnel），需另評估。
  - 建議：**一般民眾**用 Flex 摘要 → LIFF 全文 + quiz → 同意；**醫院病人**加上研究人員當面發的一次性登錄碼（見 C4）。
- 本報告推論：無法驗證年齡 → 同意頁須有「我已年滿 18 歲（或依 IRB 核定年齡）且為照片中手臂的本人」自我聲明；未成年與代理同意（法定代理人）在 LINE 自助流程中**不開放**，改走研究人員面對面流程。此為設計選擇，須 IRB 核可。台灣成年年齡 18 歲（民法 2023 起）為一般法律常識，本次未擷取條文驗證。
- 本報告推論：若 IRB 要求「簽名」，LINE 內無法產生具法律效力的手寫/數位簽章；可改為 LIFF 手寫簽名板 + 存 PNG + hash，或維持紙本簽署（醫院病人）並以登錄碼綁定。

### Gaps
- LINE Login ID token verify endpoint 的 HTTP 方法（POST vs GET）來源不一致，需以官方文件為準；本次未直接讀官方頁全文。
- 台灣 IRB 對「LINE 點選同意」是否接受為免除書面同意之形式：未找到具體案例或公告。

---

## A3. 可稽核的同意紀錄：版本、SHA-256 內容雜湊、UTC 伺服器時間、append-only 事件日誌、雜湊鏈；欄位與保存期限

### Takeaway
業界慣例（eConsent 平台、臺大自評表要求「留存同意紀錄並附時間戳記」）是保存「哪一版文件 + 何時 + 誰（識別碼）+ 做了什麼」。SHA-256 內容雜湊與 hash chaining 屬本報告推論的強化做法，無法規明文要求，但成本低、能證明「受試者看到的是哪一份確切文字」並偵測竄改。

### Cited Findings
- 臺大網路研究自評表要求線上工具能留存同意紀錄並附時間戳記。— [A-機構] [AF-143-02](https://www.ntuh.gov.tw/ckfinder_file/RECO/files/06.%E6%96%87%E4%BB%B6%E4%B8%8B%E8%BC%89(%E6%96%B0%E6%A1%88)/AF-143-02_1%E7%B6%B2%E8%B7%AF%E7%A0%94%E7%A9%B6%E8%87%AA%E8%A9%95%E8%A1%A8.doc)（存取 2026-10-31）
- 人體研究法第 14 條第 1 項第 8 款規定須告知研究材料之保存期限；第 19 條第 1 項：研究材料於研究結束或該保存期限屆至後「應即銷毀」，但經當事人同意或已去連結者不在此限。— [A] [人體研究法第 19 條](https://law.moj.gov.tw/LawClass/LawSingle.aspx?pcode=L0020176&flno=19)（存取 2026-10-31）
- LINE webhook 可能重送（redelivery 預設關閉，啟用後非 2xx 會重送），可能重複或亂序，應以 `webhookEventId` 去重、以 `timestamp` 排序；應先驗證請求簽章再處理事件。— [A] [LINE: Receive messages (webhook)](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)（存取 2026-10-31）
- 2024 年台灣期刊文章描述某醫院導入同意書電子簽署，簽署紀錄保留過程數據與時序。— [C] [airiti 16086961-N202403260006-00004](https://www.airitilibrary.com/Article/Detail/16086961-N202403260006-00004)（存取 2026-10-31；僅摘要）

### Inferences
- 本報告推論：建議資料結構（SQLite）
  - `consent_documents`（不可變）：`doc_id`, `version`（語意化，如 `2026.11-v1`）, `lang`, `irb_approval_no`, `effective_from_utc`, `retired_at_utc`, `content_canonical`（正規化後的確切顯示文字：NFC、統一換行、去尾端空白）, `sha256`（對 content_canonical 的 UTF-8 bytes）, `quiz_json`, `flex_json_sha256`/`liff_bundle_sha256`。
  - `consent_events`（append-only，只 INSERT；以 SQLite trigger 拒絕 UPDATE/DELETE）：`event_id`(UUIDv4), `seq`(單調遞增), `subject_pid`（假名 ID，見 C3，不存原始 userId）, `event_type`（presented / quiz_answered / consented / declined / withdrawn / reconsented / unfollow_observed / follow_observed / data_purged）, `doc_id`, `doc_sha256`, `channel`（flex / liff / staff）, `server_received_utc`（伺服器時間，ISO-8601 Z）, `line_event_timestamp_ms`（LINE 提供，供比對）, `webhook_event_id`, `id_token_verified`(bool), `enrollment_code_hash`（如有）, `prev_hash`, `row_hash = SHA256(prev_hash || canonical_json(row))`。
  - 每日將最新 `row_hash` 匯出到離線媒體或寫入紙本/IRB 紀錄（外部錨定），否則 hash chain 只能防「部分改寫」不能防「整串重算」。
- 本報告推論：撤回後**同意事件本身保留**（證明曾同意與何時撤回是研究合規所需），但只連結假名 ID；保存期限依 IRB 核定之計畫保存期限（人體研究法第 14 條第 1 項第 8 款告知內容），本次未找到法定最低年限。
- 本報告推論：同意版本更新時，舊版同意者不自動沿用新版；重大變更觸發 reconsent，在 reconsent 前新上傳照片不得進入研究集。

### Gaps
- 台灣法規對研究同意紀錄最低保存年限：未找到可靠證據（醫療法病歷保存 7 年屬另一範疇，未於本次驗證）。
- 雜湊鏈作為同意紀錄完整性證據之法院/IRB 採認案例：未找到。

---

## A4. 撤回：哪些必須刪、哪些可保留；已訓練模型如何處理（machine unlearning、監理機關觀點、手動流程）

### Takeaway
**重要更正**：人體研究法第 19 條**沒有**規定撤回同意；撤回權規定在第 14 條第 1 項第 6 款（應告知「得隨時撤回同意之權利及撤回之方式」），第 19 條是研究材料「研究結束或保存期限屆至應即銷毀，但經同意或已去連結者不在此限」。對已訓練模型，監理實務（FTC 演算法刪除、EDPB 2024 意見）針對的是**違法取得**資料；對於合法同意後才撤回的情形，未找到要求「立即重訓/刪模型」的明確監理意見。建議：撤回立即停止使用並刪除照片與可連結資料、排除於未來所有訓練快照、標記受影響模型、於下一次**人工排程**重訓時移除。

### Cited Findings
- 人體研究法第 14 條第 1 項第 6 款：須告知「研究對象得隨時撤回同意之權利及撤回之方式」；第 14 條第 2 項：取得同意不得以強制、利誘或其他不正當方式為之。— [A] [人體研究法全文](https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=L0020176)（修正 108-01-02；存取 2026-10-31）
- 人體研究法第 19 條三項分別為：(1) 研究結束或保存期限屆至應即銷毀，經當事人同意或已去連結者除外；(2) 未去連結之材料逾原書面同意範圍使用，須重新審查與告知同意；(3) 未去連結材料提供境外須書面同意、審查會通過及主管機關核准。條文**未提及撤回同意**。— [A] [人體研究法第 19 條](https://law.moj.gov.tw/LawClass/LawSingle.aspx?pcode=L0020176&flno=19)（存取 2026-10-31）
- 第 4 條第 3 款「去連結」：研究材料經編碼或其他方式處理後，使其與可辨識研究對象之個資「永久不能以任何方式連結、比對」。— [A] 同上全文
- 衛福部檢體相關規範（人體生物資料庫/檢體管理脈絡）：提供者可終止同意；終止同意後原則上應銷毀檢體，已去連結者不在此限。— [A] [衛福部 dl-16083](https://mohw.gov.tw/dl-16083-47cccd6d-7bd9-4812-b7a1-4661aa3062ca.html)（存取 2026-10-31；經搜尋摘要，未讀全文，適用範圍為檢體，照片類比屬推論）
- GDPR Art. 7(3)：資料主體有權隨時撤回同意，撤回不影響撤回前基於同意之處理的合法性；Art. 17：刪除權（含撤回同意且無其他法律依據時）。— [A] [GDPR (EUR-Lex)](https://eur-lex.europa.eu/eli/reg/2016/679/oj)（2016；本次未重新擷取全文，依條文通行內容，作為參考）
- **FTC Everalbum（2021-05 定案）**：要求刪除未經明示同意取得之資料，以及「全部或部分」使用該生物特徵資料開發的模型或演算法（"Affected Work Product"）；FTC 此前於 2019 Cambridge Analytica 案即使用，其後 WW/Kurbo、Rite Aid 案亦用。— [E] [World Privacy Forum](https://worldprivacyforum.org/posts/ftc-proposes-precedent-setting-face-recognition-settlement-photo-app-company-must-delete-consumers-photos-and-the-algorithmic-models-it-developed-using-the-photos)；[Weil 2021 alert](https://www.weil.com/-/media/mailings/2021/q2/ftc-orders-destruction-of-algorithms-created-from-unlawfully-acquired-datax.pdf)；[DWT 2022-03 (Kurbo)](https://www.dwt.com/blogs/privacy--security-law-blog/2022/03/ftc-coppa-disgorgement)（存取 2026-10-31；二手法律評論，FTC 原始命令未直接讀取）
- **EDPB Opinion 28/2024（2024-12-17 通過）**：AI 模型不當然視為匿名，需逐案評估且門檻高；對以違法處理資料開發之模型，監理機關可採包括刪除違法處理資料、嚴重時銷毀整個模型等矯正措施。— [E] [Matheson](https://www.matheson.com/insights/edpb-publishes-eagerly-anticipated-opinion-on-ai-models/)；[Clyde & Co 2025-03](https://www.clydeco.com/en/insights/2025/03/artificial-intelligence-and-data-protection-the-ed)；[European Papers](https://www.europeanpapers.eu/europeanforum/protecting-personal-data-in-context-of-ai-models)（存取 2026-10-31；EDPB 原文未直接讀取）
- **Machine unlearning 綜述**：Xu, Zhu, Zhang, Zhou, Yu, "Machine Unlearning: A Survey", ACM Computing Surveys 56(1), Art. 9, 2023, DOI 10.1145/3603620。— [B] [UTS OPUS record](https://opus.lib.uts.edu.au/handle/10453/176647)；[NSF PAR](https://par.nsf.gov/biblio/10520867)（存取 2026-10-31）。另 Nguyen et al. "A Survey of Machine Unlearning"（[arXiv 2209.02299](https://arxiv.org/pdf/2209.02299v4)，[D]，正式出版場域來源不一致）。
- 評論指出模型中的訓練資料常難以或無法單獨刪除，故演算法刪除可能等同銷毀整個模型，甚至模型鏈。— [E] [Mintz 2023-07-11](https://www.mintz.com/insights-center/viewpoints/2191/2023-07-11-ftc-lurking-ai-washington-report)（存取 2026-10-31）

### Inferences
- 本報告推論（必刪 vs 可留）：
  - **立即刪除**：原始照片與縮圖、EXIF、標註中可連結到該人的列、LINE 對話內容、userId 與 pseudonym 的連結表列、尚未進入任何訓練快照的待審照片。
  - **可保留（需在同意書事先寫明並經 IRB 核准）**：同意/撤回事件紀錄（只連假名 ID）、已發表之彙總統計、已去連結且無法回溯的資料（依第 19 條但書邏輯；但照片本身含身體影像，是否能「永久不能連結」須審慎，本報告傾向**不主張照片可去連結保留**）。
  - 「撤回前已完成之分析結果不必撤回」與 GDPR Art 7(3) 精神一致，但台灣法未明文，應寫進同意書並由 IRB 核定。
- 本報告推論（模型）：合法同意期間訓練的模型非 FTC/EDPB 案例所指的「違法取得」，故**未找到**要求立即重訓的依據；但影像模型可能記憶少量樣本，小資料集風險較高。
  - 現況（14 位病人、約 120 張）：撤回 1 人約占受試者 7%，且照片可能占 5–15%（依張數），對模型與驗證集影響大 → 建議撤回即**凍結**受影響模型為「不得再部署/匯出」，並在下一次人工訓練排除。
  - 未來（~1,000 張）：單人影響通常 <1–2%，可依排程（例如每季人工重訓）處理；SISA 類分片訓練（Bourtoule et al.，IEEE S&P 2021，本次未驗證引用細節）可降低重訓成本，但對小型專案效益有限。
- 本報告推論（手動流程，符合「不自動訓練」）：
  1. 使用者撤回 → 立即寫 `withdrawn` 事件、回覆確認訊息、將該 subject 加入 `exclusion_list`（以 pseudonym + 照片 hash）。
  2. 背景工作（非訓練）在 N 小時內刪除照片檔與可連結資料，寫 `data_purged` 事件（含刪除檔案的 SHA-256 清單，不含內容）。
  3. 所有 dataset snapshot manifest 以 exclusion_list 過濾；舊 snapshot 標為 `contains_withdrawn=true`，不得再用於訓練。
  4. 模型登錄表 `model_registry` 加欄位 `trained_on_snapshot`, `contains_withdrawn_subjects`(count), `flagged_at`；被標記模型不得新部署，現役模型由人員決定是否下線。
  5. 下一次人工排程訓練時以乾淨 snapshot 重訓，人員簽核後才替換；備份（04_備份）中的照片也須依保留期限輪替清除或另行標記。
- 撤回立即生效的技術意義：撤回後的上傳一律拒收（回覆提示），已排程推播停止。

### Gaps
- 台灣主管機關（衛福部、個資保護委員會籌備處）對「撤回後已訓練 AI 模型」的官方見解：未找到可靠證據。
- ICO（英國）對 unlearning / 刪除權與模型的具體指引：本次未檢索到原文，未驗證。
- EDPB Opinion 28/2024 與 FTC 命令原文未直接讀取，以上為二手評論。

---

## B1. LINE follow / unfollow（封鎖）事件、payload、isUnblocked、對封鎖者推播、是否視為撤回

### Takeaway
LINE 官方文件：follow 事件在「加好友或解除封鎖」時送出且可回覆；unfollow 事件在「封鎖」時送出（僅 1 對 1 聊天）。follow 事件帶 `follow.isUnblocked` 布林值區分新加入與解除封鎖（官方 SDK PR #597 加入）；對封鎖者推播不會送達且不計入訊息數。是否把封鎖視為撤回是設計選擇（本報告推論：**不自動視為撤回**，但暫停收集並提供明確撤回途徑）。

### Cited Findings
- Follow event：「When a user adds your LINE Official Account as a friend, or unblocks your LINE Official Account.」可回覆；僅 1 對 1 聊天。Unfollow event：「When a user blocks your LINE Official Account.」僅 1 對 1。頁面僅標示 follow 可回覆。— [A] [LINE: Receive messages (webhook)](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)（存取 2026-10-31）
- `isUnblocked`：line-bot-sdk-python PR #597「Add isUnblocked flag to Follow Webhook event」；payload 例：`"follow": {"isUnblocked": true}`。— [E/官方 SDK] [GitHub PR #597](https://github.com/line/line-bot-sdk-python/pull/597)；Classmethod 日文實作文 [dev.classmethod.jp](https://dev.classmethod.jp/articles/try-to-distinguish-between-add-friends-and-unblocking/)（存取 2026-10-31）
- 對封鎖者：Messaging API 送訊文件說明，已封鎖官方帳號或 userId 不存在的使用者屬「不會收到訊息」者，不計入已送出訊息數。LINE notification messages API 文件明載對封鎖者請求回 HTTP 200 但不送達。— [A] [LINE: Send messages](https://developers.line.biz/en/docs/messaging-api/sending-messages)；[LINE notification messages tech specs](https://developers.line.biz/en/docs/partner-docs/line-notification-messages/technical-specs/)（存取 2026-10-31）
- 驗證 userId：呼叫 Get profile，200 表示有效；其他狀態表示無效、無法傳訊。— [A] [Get user IDs](https://developers.line.biz/en/docs/messaging-api/getting-user-ids/)（存取 2026-10-31）
- Webhook 重送可能重複/亂序 → 用 `webhookEventId` 去重、`timestamp` 判斷順序（對 follow/unfollow 快速切換很重要）。— [A] [Receive messages](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)

### Inferences
- 本報告推論：unfollow 事件無法回覆（官方頁只標示 follow 可回覆；reply token 是否出現於 unfollow 未在本次讀到的頁面明載），因此**不能在封鎖當下徵詢**「是否也要撤回研究同意」。
- 本報告推論（建議）：
  - unfollow → 寫 `unfollow_observed` 事件；狀態設為 `paused`（停止推播、不再接收），**不刪除**已同意資料，因為封鎖原因多元（嫌通知太多等），把封鎖當撤回可能違反受試者意願且不可逆；但同意書須明文告知「封鎖不等於撤回；撤回請使用選單『撤回同意』或聯絡研究團隊（電話/email）」，並提供 LINE 以外的撤回管道（因封鎖後無法在 LINE 內溝通）。
  - 若 IRB 或研究團隊偏好保守做法，可選「封鎖 X 天未解除 → 視為撤回」，但須在同意書事先寫明；此為設計選項。
  - follow 且 `isUnblocked=true` → 不重新註冊，回覆「歡迎回來，你的研究同意狀態為：…」；若同意版本已更新則要求 reconsent。
  - 對 `paused` 使用者不推播（推播也不會送達）；以 Get profile 非 200 作為輔助判斷。
- 本報告推論：未自動視為撤回時，現況 14 位病人中任何一人封鎖都不影響資料；若採自動撤回，誤刪 1 人即損失約 7% 受試者。

### Gaps
- `follow.isUnblocked` 正式導入日期（LINE Developers News 公告日）：未找到可靠證據（只找到 SDK PR，未讀到官方 news 日期）。
- 推播給封鎖者的 Messaging API push endpoint 確切 HTTP 狀態碼：官方 Messaging API 參考頁未讀到；notification messages API 為 200。建議實測。
- unfollow 事件 payload 是否含 replyToken：本次讀到的官方頁未明載（參考頁內容被折疊）；需直接查 Messaging API reference #unfollow-event。
- 封鎖後 userId 是否改變：未找到官方明文；依 userId 為 provider 範圍固定識別碼之說明推論不變。

---

## B2. LINE 對官方帳號營運者的使用者資料條款；是否禁止收集敏感/醫療資料

### Takeaway
未能取得 LINE 官方帳號使用條款、LINE User Data Policy 或台灣 OA 審核準則中「醫療/敏感資料」條文原文（官方頁 403 或搜尋未命中）。目前可確認：LY Corporation 有「LINE User Data Policy」規範開發者處理使用者資料；LINE 隱私權政策提到被指定為可能含特別敏感資訊的官方帳號內容不用於機器學習。是否禁止健康資料收集：**未找到可靠證據**，須人工查閱。

### Cited Findings
- LINE Developers「Terms and policies」頁列出 LINE Developers Agreement 與 LINE User Data Policy（開發者使用 SDK/API 處理使用者資料應遵守之規則）。— [A] [LINE Developers Terms and policies](https://developers.line.biz/en/terms-and-policies/)（存取 2026-10-31；User Data Policy 頁 403 未能讀取）
- LINE 隱私權政策：被 LINE 指定為可能含特別敏感資訊之官方帳號的內容，不會用於機器學習。— [A] [LINE communication privacy / Regarding Usage of Your Information](https://terms.line.me/line_communication_privacy?lang=en)（存取 2026-10-31；經搜尋摘要）
- 2014 年 BusinessConnect 營運指引（可能已過時）：取得的 MID 等 LINE 資訊僅能用於取得該資訊的帳號。— [E] [Slideshare 2014-12-15](https://www2.slideshare.net/dhvgen/enline-business-connect-operational-guidelines-20141215-1)（存取 2026-10-31）

### Inferences
- 本報告推論：照片經 LINE 傳輸時會經過 LINE 伺服器（內容取得 API 由 LINE 提供），「照片不上傳第三方雲」的承諾應精確表述為「研究端儲存與運算不使用第三方雲；傳輸經 LINE 平台」，同意書須揭露。
- 本報告推論：OA 介紹文字、自動回覆避免「診斷」「治療」用語，以降低觸及 LINE 廣告/內容審查中醫療宣稱類規範的風險（具體規範未驗證）。

### Gaps
- LINE 台灣官方帳號審核準則／使用條款中對醫療業種、健康資料之限制：兩輪搜尋（中文「LINE 官方帳號 審核準則 禁止 醫療」、英文「LINE Official Account Terms… sensitive」）均未找到原文。**建議人工開啟 tw.linebiz.com 與 terms.line.me 確認。**
- LINE User Data Policy 對「使用者封鎖/撤回後須刪除資料」的要求：未讀到原文。

---

## C1. LINE userId 的性質

### Takeaway
userId 格式 `U[0-9a-f]{32}`，**以 provider 為範圍發放**：同一使用者在同一 provider 下的 LINE Login 與 Messaging API channel 取得相同 userId；不同 provider 下則不同，無法跨 provider 比對。

### Cited Findings
- 「User IDs are issued different values for each provider, even for the same user」；同一 provider 下「the user ID is the same regardless of the channel type」；格式 `U[0-9a-f]{32}`；與顯示名稱、可供搜尋的 LINE ID 不同。— [A] [LINE: Get user IDs](https://developers.line.biz/en/docs/messaging-api/getting-user-ids/)（存取 2026-10-31）
- Get follower IDs 僅限 verified 或 premium 帳號。— [A] 同上
- Messaging API 參考：沒有 API 可取得自己的 userId（開發者在 Console 查看）。— [A] [Messaging API reference](https://developers.line.biz/en/reference/messaging-api/)（存取 2026-10-31）

### Inferences
- 本報告推論：LIFF/LINE Login channel 必須與 Messaging API channel 放在**同一 provider**，否則 ID token 的 `sub` 對不上 webhook 的 userId。
- 本報告推論：userId 對同一 provider 是長期穩定、可跨時間串連的識別碼，屬「間接識別」個資，不應作為研究受試者代碼或寫入匯出資料集。

### Gaps
- userId 何種情況會改變（例如使用者刪除並重建 LINE 帳號）：官方未明載，未找到可靠證據（推論：重建帳號會是新的 userId）。

---

## C2. LINE Login（v2.1, OIDC）與 Account Link 的用途與風險

### Takeaway
LINE Login v2.1 以 `openid` scope 取得 ID token，可在伺服器端驗證使用者身分（僅證明「控制此 LINE 帳號」）；email 需另申請。Account Link 用 10 分鐘一次性 link token + 高熵 nonce，將外部服務帳號綁到 LINE userId；官方文件明確警告自行實作的攻擊：攻擊者把連結傳給他人以綁定攻擊者的 LINE 帳號。

### Cited Findings
- Link token：POST `/bot/user/{userId}/linkToken`；「for one-time use only and valid for 10 minutes」。— [A] [LINE: Linking user accounts](https://developers.line.biz/en/docs/messaging-api/linking-accounts/)（存取 2026-10-31）
- Nonce：單次使用、難以預測，10–255 字元；建議安全亂數 ≥128 bits、Base64 編碼；不要用可預測值如服務端 user ID；nonce 需與服務端 user ID 一起保存，重導向至 `https://access.line.me/dialog/bot/accountLink?linkToken=…&nonce=…`。— [A] 同上
- accountLink 事件含 userId 與 nonce，`result` 為 `ok` 或 `failed`；link token 過期或已用則不送 webhook。— [A] 同上
- 風險：自行實作可能讓攻擊者「send a URL to a user to link the attacker's LINE account」；Messaging API 會檢查發起者是否為該 LINE 帳號真正擁有者。— [A] 同上
- 必須讓使用者「at all times」可解除連結，並在連結時告知可解除。— [A] 同上
- ID token 僅在請求 `openid` 時回傳；email 需申請權限且 verify 回應 scope 不列 email。— [A] [LINE Login v2.1 reference](https://developers.line.biz/en/reference/line-login/)；[Integrate LINE Login](https://developers.line.biz/en/docs/line-login/integrate-line-login/index.html.md)（存取 2026-10-31）

### Inferences
- 本報告推論：本專案**不需要 email scope**（最小化原則）；只用 `openid`（必要時 `profile` 也可省略）。
- 本報告推論：Account Link 原設計用於「已有會員系統」；本專案沒有病人登入系統，若為綁定醫院個案而建置「醫院病人登入頁」反而擴大攻擊面。較安全替代：研究人員當面發的一次性登錄碼（C4）。
- 本報告推論：若仍用 Account Link，nonce 必須單次使用並在 accountLink `ok` 後作廢、比對 nonce 對應之服務端帳號、連結結果在 LINE 內回覆讓使用者確認「已綁定研究編號 S-xxxx 的末兩碼」。

### Gaps
- LINE 對 Account Link 用於醫療/研究場景的限制：未找到。

---

## C3. 能否用 LINE userId 當受試者代碼；假名化設計；台灣去識別化與 ISO/IEC 標準

### Takeaway
不建議以 userId 當受試者代碼。建議：隨機研究 ID（study_id）作為所有研究資料主鍵；userId 只存在於受存取控制的連結表，或只存其**keyed HMAC**（金鑰離線保管）。依個資法實務與國發會函釋，「通過去識別化驗證」不當然排除個資法；可回復連結的假名化資料仍是個資，只有達「無從直接或間接識別」才不適用。

### Cited Findings
- 我國以 CNS 29100、CNS 29191 作為個資去識別化驗證依據（行政院新聞稿，民國 104 年）；財政部財政資訊中心為首例驗證（104-11-30）。— [A] [行政院新聞](https://www.ey.gov.tw/Page/9277F759E41CCD91/af28eb4c-7030-49bb-889d-f0a0fed6a4d5)（存取 2026-10-31；CNS 29191 公布年份有來源不一致，見 Gaps）
- 國發會民國 108 年函釋：經濟部標準檢驗局訂定「個人資料去識別化過程驗證要求及控制措施」；通過驗證之資料是否仍適用個資法，應視去識別化後是否已達無從直接或間接識別特定個人而定，**通過驗證並不當然排除個資法適用**。— [A] [臺北市法規 函釋 FE372646](https://laws.gov.taipei/Law/Interpretation/Content/FE372646)（存取 2026-10-31）
- CNS 20889（對應 ISO/IEC 20889，隱私增強資料去識別化術語與技術分類）2020 年制定。— [A] [標準檢驗局文件](https://www.bsmi.gov.tw/wSite/public/Data/f1590545010778.pdf)（存取 2026-10-31；經搜尋摘要）
- 人體研究法第 4 條第 3 款「去連結」定義為永久不能以任何方式連結、比對。— [A] [人體研究法](https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=L0020176)
- EDPB：模型不當然匿名，門檻高（類推：保留連結表的假名化資料亦非匿名）。— [E] [Matheson](https://www.matheson.com/insights/edpb-publishes-eagerly-anticipated-opinion-on-ai-models/)（存取 2026-10-31）

### Inferences
- 本報告推論（建議架構）：
  - `study_id`：隨機（如 `S-` + 8 位 base32），所有照片、標註、模型 manifest 僅用 study_id。
  - `pid = HMAC-SHA256(pepper, userId)`：用於 webhook 到來時查找 study_id，避免資料庫內存放明文 userId；pepper 存於離線/作業系統保護的金鑰檔，不入 git、不入備份同一位置。
  - 但推播/回覆仍需明文 userId → 折衷：`line_link` 表（userId ↔ study_id）獨立 SQLite 檔、OS 層權限限制、可加密（如 SQLCipher 或應用層 AES-GCM），只有 bot 服務帳號可讀；研究分析人員只拿到 study_id 資料。
  - 撤回時刪除 `line_link` 列 → 研究資料與 LINE 帳號斷鏈（配合 A4 刪照片）。
  - 用語區分：**假名化**（可用金鑰/連結表回復；仍是個資）vs **去連結/匿名化**（人體研究法第 4 條：永久不能連結）。照片本身是身體影像，含刺青、痣、手錶等，即使移除連結表也未必匿名。
- 本報告推論：小樣本（14 位病人）時，study_id + 收案日期 + 醫院 + 部位，就可能讓研究團隊或院內人員再識別；匯出資料集應粗化日期（週/月）並移除 EXIF。

### Gaps
- ISO/IEC 27559:2022（去識別化框架）之 CNS 對應或國發會採用情形：未找到可靠證據。
- 台灣個資法對「假名化」的法定定義：本次未找到（個資法現行條文未用「假名化」一詞；是否有修法草案未驗證）。
- CNS 29191 公布年份：行政院稿稱 104 年，另一報導用語不同，存在不一致。

---

## C4. 將 LINE 上傳連結到醫院個案編號（如義大個案碼）

### Takeaway
不要在聊天中索取身分證字號、病歷號或姓名生日。建議由研究人員在病床邊/門診完成紙本或面對面同意後，給予**一次性、短效、高熵的登錄碼**（QR 或 6–8 碼），受試者在 LIFF/postback 輸入，後端把 LINE（pseudonym）綁到研究 study_id；醫院個案碼與 study_id 的對照表只存在院內研究端、不經 LINE。

### Cited Findings
- Account Link 官方警告的攻擊模式（他人誘騙綁定攻擊者帳號）與 nonce 應高熵、單次使用的要求，同樣適用任何「碼→帳號」綁定設計。— [A] [LINE: Linking user accounts](https://developers.line.biz/en/docs/messaging-api/linking-accounts/)（存取 2026-10-31）
- 人體研究法第 19 條第 2、3 項：未去連結材料逾原同意範圍使用須重新審查/同意；提供境外須書面同意與核准 → 綁醫院個案即屬「未去連結」，用途應限縮於同意範圍。— [A] [人體研究法第 19 條](https://law.moj.gov.tw/LawClass/LawSingle.aspx?pcode=L0020176&flno=19)（存取 2026-10-31）
- 臺大醫院將已簽署受試者同意書上傳 EMR 供臨床照護查詢（說明醫院端同意文件與病歷系統的既有連結做法）。— [A-機構] [臺大「受試者同意書上傳 EMR」說明 2022-02](https://www.ntuh.gov.tw/ckfinder_file/RECO/files/05.%E5%9F%B7%E8%A1%8C%E8%87%A8%E5%BA%8A%E8%A9%A6%E9%A9%97%E9%87%8D%E8%A6%81%E8%A8%8A%E6%81%AF/%E3%80%90%E5%85%AC%E5%91%8A%E9%99%84%E4%BB%B6%E3%80%91%E8%87%BA%E5%A4%A7%E9%86%AB%E9%99%A2%E3%80%8C%E5%8F%97%E8%A9%A6%E8%80%85%E5%90%8C%E6%84%8F%E6%9B%B8%E4%B8%8A%E5%82%B3%20EMR%E3%80%8D%E7%B3%BB%E7%B5%B1%E9%A0%81%E9%9D%A2%E4%BD%BF%E7%94%A8%E8%AA%AA%E6%98%8E%20Feb2022.pdf)（存取 2026-10-31）

### Inferences
- 本報告推論（登錄碼規格）：伺服器端產生 ≥ 40 bits 熵的碼（例如 8 碼 Crockford base32），只存其 SHA-256；有效 24–72 小時、單次使用、輸入錯誤 5 次鎖定；綁定成功後回覆「已加入研究，研究編號末兩碼 xx」，並寫 `enrolled_via_code` 事件。登錄碼對應 study_id，**不**對應病歷號；study_id ↔ 義大個案碼對照表留在院內研究人員保管（紙本或加密檔），不進 LINE bot 伺服器。
- 本報告推論：風險—病人把碼轉給家屬代傳照片（代理上傳）；設計上允許「家屬代為拍照」但同意者須為病人本人或法定代理人，於現場流程中確認並記錄。
- 本報告推論：現況義大 14 位病人資料位於匯入區（05_匯入區），既有個案碼應先轉為 study_id 再進研究資料庫，保持與 LINE 招募民眾同一套 ID 空間但以前綴區分來源（例如 `H-` 醫院、`P-` 民眾）。

### Gaps
- 台灣醫院 IRB 對「LINE 綁定病人研究編號」的審查先例：未找到。
- 義大醫院 IRB 對外部通訊軟體收案的院內規定：未找到（需向該院 IRB 查詢）。
