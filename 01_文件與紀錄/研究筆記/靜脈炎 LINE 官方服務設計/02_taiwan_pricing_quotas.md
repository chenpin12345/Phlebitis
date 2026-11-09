# 台灣 LINE 官方帳號（LINE OA）訊息方案、計費規則與研究原型成本估算（截至 2026-10-30）

> 範圍：台灣地區 LINE 官方帳號 + Messaging API，用於「使用者上傳 IV 注射部位照片 → 回覆靜脈炎照片分類結果（僅研究用途，非臨床診斷）」的研究原型。
> 存取日：2026-10-30（部分官方頁面原始碼於 2026-10-31 補抓）。
> **重要時間點：台灣方案價格於 2026-11-01 調整（公告日 2026-09-01）。本筆記同時列出「至 2026-10-31 止」與「自 2026-11-01 起」兩套價格；之後營運應以 2026-11-01 新價為準。**
> 證據標記：研究證據顯示＝官方/一手文件明載；業界慣例＝第三方/新聞整理；本報告推論＝依引用輸入自行計算或推論。

### 來源清單（分級、日期）

| 代號 | 等級 | 來源 | 文件日期 / 更新日期 |
|---|---|---|---|
| S1 | [A] | LINE Biz-Solutions 台灣「LINE 官方帳號」服務/費用說明頁 https://tw.linebiz.com/service/account-solutions/line-official-account/ | 頁面無明示日期；靜態資源路徑標記 `js-20260924-modified`（2026-09-24 版） |
| S2 | [A] | 台灣官方公告「2026年 LINE 官方帳號方案價格調整」 https://tw.linebiz.com/column/LINEOA-2026-Price-Plan/ | datePublished / dateModified：2026-09-01 |
| S3 | [A] | 台灣官方 FAQ「訊息費用的計價方式？」 https://tw.linebiz.com/faq/oa-price/message-price-list/ | 無日期（內容仍為 2026-10-31 前價格，頂部附 2026/11/1 調整提示） |
| S4 | [A] | 台灣官方 FAQ「收費訊息如何計算？」 https://tw.linebiz.com/faq/oa-price/how-to-calculate-message-expense/ | 無日期 |
| S5 | [A] | 台灣官網費用計算機程式 cal.js（S1 頁面載入） https://vos.line-scdn.net/lbstw-static/assets/frontend/js-20260924-modified/cal.js | 路徑版本 2026-09-24；內含三代計價公式（原始版／2026-10-31 前／2026-11-01 起） |
| S6 | [A] | LINE Developers「Messaging API pricing」 https://developers.line.biz/en/docs/messaging-api/pricing/ | 頁面無日期 |
| S7 | [A] | LINE Developers「Messaging API reference」 https://developers.line.biz/en/reference/messaging-api/ （以 index.html.md 版本全文檢索） | 頁面無日期 |
| S8 | [A] | LINE Developers「Display a loading animation」 https://developers.line.biz/en/docs/messaging-api/use-loading-indicator/ | 頁面無日期 |
| S9 | [A] | LINE Developers「Messaging API overview」 https://developers.line.biz/en/docs/messaging-api/overview/ | 頁面無日期 |
| S10 | [E] | INSIDE〈LINE 官方帳號「以量計價」新制 3 月上路，引發大規模跳槽風〉 https://www.inside.com.tw/article/19061-line-new-fee-brand | 2020-03-02 |
| S11 | [E] | TechNews〈LINE 公開 2019 年商務溝通三大趨勢，「官方帳號 2.0 計畫」整併藍圖首度揭曉〉 https://technews.tw/?p=411309 | 2018-11-09 |
| S12 | [E] | FIRST LINE 說明文件〈LINE 訊息費用怎麼算〉 https://help.firstline.cc/feature/channels/line/pricing | 表格標示「更新時間為 2023年9月」 |
| S13 | [E] | Omnichat 部落格 https://blog.omnichat.ai/tw/line-2-0-official-account-pricing/ 、 https://blog.omnichat.ai/line-pricing-sep2023/ | 全文無法擷取，僅有搜尋摘要（不作為主要依據） |
| S14 | [E] | 工商時報/中時新聞網〈記事本影片掰了！LINE大砍3實用功能 本月實施〉 https://www.ctee.com.tw/news/20260415701121-430502 | 2026-04-15 |

---

## Q1. 台灣現行 LINE 官方帳號方案：月費、免費訊息數、加購價格、稅、最近調價日期與調價時間軸

### Takeaway
研究證據顯示：台灣仍為「輕用量／中用量／高用量」三方案；免費訊息則數 200／3,000／6,000 不變；**自 2026-11-01 起**中用量月費 NT$800→NT$1,000、高用量 NT$1,200→NT$1,400（皆未稅），高用量加購改為兩級距（第 1–50,000 則 NT$0.2、第 50,001 則起 NT$0.15）；輕用量與中用量**不可加購**。最近一次調價公告日 2026-09-01、生效日 2026-11-01。

### Cited Findings
**現行（自 2026-11-01 起）方案 — 研究證據顯示**
- 公告標題「2026年 LINE 官方帳號方案價格調整」，發布日 2026/09/01；「於2026年11月1日起，您的官方帳號價格方案內容，將會有以下調整」 — [S2 [A]](https://tw.linebiz.com/column/LINEOA-2026-Price-Plan/)
- 公告註明「下方金額說明皆為未稅價格」 — [S2 [A]](https://tw.linebiz.com/column/LINEOA-2026-Price-Plan/)；服務頁亦載「※ 所有費用皆不含稅」 — [S1 [A]](https://tw.linebiz.com/service/account-solutions/line-official-account/)
- 方案表（S2 原文數字）：

| 方案 | 固定月費（未稅）舊 → 新 | 每月免費訊息 | 加購 |
|---|---|---|---|
| 輕用量 | NT$0 → NT$0（不變） | 200 則 | 不可加購（S3 未列加購；S2 表格無加購） |
| 中用量 | NT$800 → **NT$1,000** | 3,000 則 | 「不可加購；如需發送更多訊息，需升級為高用量方案」 |
| 高用量 | NT$1,200 → **NT$1,400** | 6,000 則 | 「可依實際需求加購，0.2元/則起降，採階梯式累進計價」 |
  — [S2 [A]](https://tw.linebiz.com/column/LINEOA-2026-Price-Plan/)
- 高用量加購新級距：當月加購第 1～50,000 則 0.2 元／則；第 50,001 則起 0.15 元／則；「超過免費訊息則數後，才會依上述級距計算加購訊息費用」；累進計價，「前 50,000 則仍以每則 0.2 元計算」 — [S2 [A]](https://tw.linebiz.com/column/LINEOA-2026-Price-Plan/)
- 官方計算機程式碼（2026-11-01 起區塊）與公告一致：`moderateFreeNew26 = 1000`、`highFreeNew26 = 1400`、`extraMessages26 = max(0, textNumber - 6000)`、`extraCost26 = min(extra, 50000)*0.2 + max(0, extra-50000)*0.15`；≤200 則判為輕用量、201–3,000 則判為中用量 — [S5 [A]](https://vos.line-scdn.net/lbstw-static/assets/frontend/js-20260924-modified/cal.js)
- 「各方案原有的免費訊息則數維持不變，輕用量、中用量及高用量方案每月分別提供 200 則、3,000 則及 6,000 則免費訊息」 — [S2 [A]](https://tw.linebiz.com/column/LINEOA-2026-Price-Plan/)
- 中、高用量（付費方案）會「結合更多 OA PLUS 好友經營、電商與實用商務功能」；服務頁註「官方帳號 OA Plus 需為付費官方帳號方可免費啟用」 — [S2 [A]](https://tw.linebiz.com/column/LINEOA-2026-Price-Plan/)；[S1 [A]](https://tw.linebiz.com/service/account-solutions/line-official-account/)
- 過渡規定：「如果您在2026年10月27日後仍繼續使用中用量或高用量方案，即視為您同意」；不同意者須於 2026-10-27 前改為輕用量；信用卡自動續繳者「2026 年 11 月的方案費用將於 11 月 1 日依新版價格進行自動扣款」；系統維護期間 2026-10-28 08:00 至 2026-11-02、2026-11-24 08:00 至 2026-11-25（部分方案/付款功能暫停，含「變更訊息則數上限」） — [S2 [A]](https://tw.linebiz.com/column/LINEOA-2026-Price-Plan/)
- 「付費週期部分沒有調整，和過往相同」 — [S2 [A]](https://tw.linebiz.com/column/LINEOA-2026-Price-Plan/)
- 每月穩定 7 萬則以上可透過「LINE 商家俱樂部會員計畫」申請「訊息費折抵」 — [S2 [A]](https://tw.linebiz.com/column/LINEOA-2026-Price-Plan/)

**至 2026-10-31 止的方案（2023 年起適用）— 研究證據顯示**
- 官方 FAQ（截至存取日仍顯示舊價）：輕用量「月費免費 0 元」「免費訊息則數：200 則」；中用量「月費 800 元」「3,000 則」「不可加購訊息…請先…升級至高用量方案」；高用量「1,200 元」「6,000 則」「加購訊息調整為每則從 0.2 元起降…採階梯式累進計價」 — [S3 [A]](https://tw.linebiz.com/faq/oa-price/message-price-list/)
- 官方計算機「至2026/10/31止」區塊（`moderateFreeNew = 800`、`highFreeNew = 1200`）之高用量加購級距（以當月總則數計）：6,001–25,000 則 0.2；25,001–35,000 則 0.165；35,001–45,000 則 0.154；45,001–65,000 則 0.143；65,001–105,000 則 0.132；105,001–185,000 則 0.121；185,001–345,000 則 0.1045；345,001–665,000 則 0.1034；665,001–825,000 則 0.099；825,001–1,305,000 則 0.0946；1,305,001–2,585,000 則 0.0858；2,585,001–3,525,000 則 0.077；3,525,001–5,145,000 則 0.066（更高級距程式碼輸出遭截斷，未讀取） — [S5 [A]](https://vos.line-scdn.net/lbstw-static/assets/frontend/js-20260924-modified/cal.js)

**2020 年（LINE@ 整併後）初版方案 — 研究證據顯示（官方程式碼）＋ 新聞佐證**
- 官方計算機中仍保留的「original」區塊：≤500 則為輕用量；中用量 `moderateFree = 800`，超過 4,000 則後每則 0.2；高用量 `highFree = 4000`（月費 NT$4,000），超過 25,000 則後 25,001–35,000 則 0.15、35,001–45,000 則 0.14、45,001–65,000 則 0.13、65,001–105,000 則 0.12、105,001–185,000 則 0.11、185,001–345,000 則 0.095、345,001–665,000 則 0.094、665,001–825,000 則 0.09、825,001–1,305,000 則 0.086、1,305,001–2,585,000 則 0.078、2,585,001–3,525,000 則 0.07、3,525,001–5,145,000 則 0.06、5,145,001–8,025,000 則 0.05… — [S5 [A]](https://vos.line-scdn.net/lbstw-static/assets/frontend/js-20260924-modified/cal.js)
- 新聞：新版官方帳號「3 月 1 日全面啟用」，LINE@ 帳號於 1/14–2/29 陸續升級；低用量免費群發 500 則、不可加購；中用量 4,000 則、NT$800、可加購；高用量 25,000 則、NT$4,000、可加購 — [S10 [E]](https://www.inside.com.tw/article/19061-line-new-fee-brand)（2020-03-02；與 S5 原始區塊一致）
- 2018-11 預告：「官方帳號 2.0」將推 3 種月費方案（輕/中/高用量），依受眾人數計價、不綁年約、所有帳號免費使用 Messaging API，預計 2019 Q2 在台推出 — [S11 [E]](https://technews.tw/?p=411309)

**調價時間軸（整理）**

| 時間 | 事件 | 數字 | 證據 |
|---|---|---|---|
| 2018-11-09 | 宣布「官方帳號 2.0」三方案以量計價 | 未公布金額 | [S11 [E]] |
| 2019（Q2 起）～2020-03-01 | LINE@ 整併為新版官方帳號，2020-03-01 全面啟用 | 輕 0/500 則；中 800/4,000 則（加購 0.2）；高 4,000/25,000 則（加購 0.15 起遞減） | [S10 [E]]；[S5 [A]] 原始區塊 |
| 2023 年（第三方稱 2023 年 9 月） | 免費則數全面下調、中用量不可加購、高用量月費降為 1,200、加購單價上調 | 輕 0/200；中 800/3,000（不可加購）；高 1,200/6,000（加購 0.2 起遞減） | 數字：[S3 [A]]、[S5 [A]]；日期僅見 [S12 [E]]（「更新時間為 2023年9月」）與 S13 搜尋摘要 |
| 2026-09-01 公告 → 2026-11-01 生效 | 中、高用量月費調漲；高用量加購改兩級距 | 輕 0/200；中 1,000/3,000（不可加購）；高 1,400/6,000（0.2 / 0.15） | [S2 [A]]、[S5 [A]] |

- 其他 2026 變動（非訊息價格）：工商時報報導官方帳號聊天記錄未升級者僅保留近 6 個月，「聊天進階方案」每月 NT$100 可保存 5 年 — [S14 [E]](https://www.ctee.com.tw/news/20260415701121-430502)；官方服務頁註「聊天記錄留存時間：儲存2024年1月1日起的聊天記錄」 — [S1 [A]](https://tw.linebiz.com/service/account-solutions/line-official-account/)（兩者描述角度不同，聊天進階方案價格在官方頁文字中未找到）

**其他地區（簡述）**
- 日本（LINE Developers 範例）：Communication Plan 免費／200 則；Light Plan JPY 5,000／5,000 則（不可加購）；Standard Plan JPY 15,000／30,000 則，加購「Up to JPY 3/message」，皆未稅 — [S6 [A]](https://developers.line.biz/en/docs/messaging-api/pricing/)
- 泰國：官方定價頁連結為 https://lineforbusiness.com/th/service/line-oa-features/broadcast-message（本次未擷取數字） — [S6 [A]](https://developers.line.biz/en/docs/messaging-api/pricing/)

### Inferences
- 本報告推論：2023 版高用量加購級距恰為 2020 版對應級距 ×1.1（0.15→0.165、0.14→0.154、0.13→0.143、0.12→0.132、0.11→0.121、0.095→0.1045、0.094→0.1034、0.09→0.099、0.086→0.0946、0.078→0.0858、0.07→0.077、0.06→0.066），與第三方所稱「推播費用調高約 1 成」相符（S5 [A] 數字；S13 [E] 摘要）。
- 本報告推論：2026-11-01 起高用量加購**最低單價為 0.15 元**，對大量發送者而言等同取消 2023 版 0.1 元以下的深度折扣；但本研究原型（≤數萬則/月）只落在 0.2 元級距，受影響主要是月費 +NT$200。
- 本報告推論（含稅換算）：官方金額皆「未稅」。若以台灣一般營業稅 5% 估算，中用量新價約 NT$1,050、高用量約 NT$1,470；**5% 稅率未於本次官方來源中查證，僅為估算假設**，實際以 LINE 開立之電子發票為準。

### Gaps
- 2023 年調價的**官方公告原文與確切生效日**：未找到可靠證據（只有 [E] 來源稱 2023 年 9 月；官方 FAQ/計算機只給數字無日期）。
- 2019–2020 之間台灣是否另有中間版價格：未找到可靠證據。
- 2023 版高用量最高級距（>5,145,000 則）單價：程式碼輸出截斷，未讀取；FIRST LINE 稱「0.2 – 0.011」，與官方程式碼可讀部分（最低已讀 0.066）無法對照，疑為筆誤（S12 [E]）。
- 2024、2025 年台灣訊息價格：未找到任何調整證據（官方 2026 公告的「舊價」即為 2023 版數字，推論 2024–2025 無訊息價格變動，但無正式聲明）。
- 官方服務頁的方案價格表為圖片，文字擷取無法讀取；已改以同頁計算機 JS 與公告頁文字核對。

---

## Q2. 哪些訊息計費：Reply / Push / Multicast / Broadcast / Narrowcast、計數方式、Loading animation、1:1 聊天、自動回應；群發 vs 個別訊息

### Takeaway
研究證據顯示：台灣官方明列 **Reply API、一對一聊天、自動回應、AI 自動回應、加入好友歡迎訊息「免付費」**；Push / Multicast / Broadcast / Narrowcast 計入則數。計數單位是「收訊人數」，**一次請求內的訊息物件數（Push/Reply 最多 5 個對話框）不影響則數**。Loading animation 不屬訊息發送方法，官方文件未列為計費項目。

### Cited Findings
- 台灣官方：「不計入訊息費用的項目：一對一聊天訊息、自動回應訊息、加入好友的歡迎訊息、Messaging API 中的 Reply API 功能」；計費「訊息適用於群發訊息、分眾訊息、API訊息 (部分審核功能的API訊息費用不在此內)」；「群發或分眾訊息，皆根據發送訊息的目標好友數計算訊息費用」 — [S1 [A]](https://tw.linebiz.com/service/account-solutions/line-official-account/)
- 2026 公告 Q2「哪些訊息類型不列入計費？」：加入好友的歡迎訊息、一對一聊天訊息、自動回應訊息、AI 自動回應訊息、Messaging API 的 Reply API — [S2 [A]](https://tw.linebiz.com/column/LINEOA-2026-Price-Plan/)
- LINE Developers：計入則數的發送方法為 Push、Multicast、Broadcast、Narrowcast；不計入的為 Reply messages — [S6 [A]](https://developers.line.biz/en/docs/messaging-api/pricing/)
- 計數規則：「The number of messages is counted by the number of people you send a message to.」例：一次 push 4 個 message objects 到 5 人聊天室＝5 則；「The number of message objects in a request doesn't affect the number of messages sent.」傳給封鎖者或不存在的 user ID 不計 — [S6 [A]](https://developers.line.biz/en/docs/messaging-api/pricing/)
- 台灣官方 FAQ（群發 vs Push API）：「一則群發訊息最多可以有3個對話框…一個圖文訊息只算一個對話框，一個多頁訊息(最多9個分頁)也只算一個對話框」；「商家在電腦版後台每次發送群發訊息，最多可一次發送 3 則對話串框、透過 Push API…每次可以發送 5 則對話串框」；群發時可在「推測目標好友數」看到會發出幾則 — [S4 [A]](https://tw.linebiz.com/faq/oa-price/how-to-calculate-message-expense/)
- Reply / Push 請求 `messages` 陣列「Max: 5」 — [S7 [A]](https://developers.line.biz/en/reference/messaging-api/)
- 計費時區：「系統計算的時區為日本時區(GMT+9:00)，台灣時間23:00起傳送的訊息會被計算到隔日」 — [S1 [A]](https://tw.linebiz.com/service/account-solutions/line-official-account/)
- Loading animation：`POST https://api.line.me/v2/bot/chat/loading/start`，僅限一對一聊天；`loadingSeconds` 可為 5–60（5 的倍數），預設 20；收到 OA 新訊息或時間到即消失；使用者未在聊天畫面時不顯示；需 LINE iOS/Android 13.16.0 以上；成功回 202；速率限制 100 requests/second — [S7 [A]](https://developers.line.biz/en/reference/messaging-api/)；[S8 [A]](https://developers.line.biz/en/docs/messaging-api/use-loading-indicator/)
- Reply token：「can only be used once」；「must be used within one minute after receiving the webhook. Use beyond one minute isn't guaranteed to work」；時限「subject to change without notice」 — [S7 [A]](https://developers.line.biz/en/reference/messaging-api/)
- Postback event 物件含 reply token（「Reply token used to send reply message to this event」） — [S7 [A]](https://developers.line.biz/en/reference/messaging-api/)
- 「Get the target limit for sending messages this month」回傳數「includes the number of messages sent from LINE Official Account Manager」（即後台群發與 API 共用額度） — [S7 [A]](https://developers.line.biz/en/reference/messaging-api/)

### Inferences
- 本報告推論：Loading animation 不是 message object 發送，不在 S6 的計費清單（push/multicast/broadcast/narrowcast）中，因此**不消耗訊息則數**；官方文件未以文字明說「免費」，屬推論。
- 本報告推論：「群發」（OA Manager 群發／Broadcast API）與「個別訊息」（Push API 對單一 userId）在計費上本質相同——都按收訊人數計；差別在於一次可帶 3 個（後台）vs 5 個（Push API）對話框、以及對象選擇方式。對本原型，「1 位使用者 1 次 push（含 ≤5 個對話框）＝ 1 則」。
- 本報告推論：OA Manager 手動 1:1 聊天回覆不計費（S1/S2 明載）——研究團隊人工處理個案時應走 1:1 聊天而非 push。
- 本報告推論：每月額度以日本時間重置，台灣時間每月最後一天 23:00 後發出的 push 會計入下個月。

### Gaps
- Loading animation 是否計費：官方未有明文，未找到可靠證據（推論為不計）。
- 「部分審核功能的API訊息費用不在此內」所指的審核功能 API 範圍與價格：未找到可靠證據。
- LINE 通知型訊息（Notification Message）在台灣的價格：本次未查。

---

## Q3. 免費額度用完時會發生什麼（429 錯誤）、相關 API

### Takeaway
研究證據顯示：超過當月免費（或加購上限）則數時，計費類發送（push/multicast/broadcast/narrowcast）回傳 **HTTP 429，錯誤訊息「You have reached your monthly limit.」，訊息不送出**；Reply 不受影響（不計則數）。可用 `GET /v2/bot/message/quota` 與 `GET /v2/bot/message/quota/consumption` 監控。

### Cited Findings
- 「When you exceed the limit of messages that can be sent in a month, an error response will be returned and the messages won't be sent.」 — [S6 [A]](https://developers.line.biz/en/docs/messaging-api/pricing/)
- 狀態碼表：429 Too Many Requests 原因包含「Exceeded the number of free messages」「Exceeded your maximum number of additional messages allowed to be sent」（另含 rate limit、並行作業上限） — [S7 [A]](https://developers.line.biz/en/reference/messaging-api/)
- 錯誤訊息表：「You have reached your monthly limit.」對應超出免費則數或超出加購上限；並註明有時尚有剩餘則數也可能出現（FAQ 連結 #why-do-i-get-429-error-during-message-delivery） — [S7 [A]](https://developers.line.biz/en/reference/messaging-api/)
- Narrowcast 進行中可能暫時扣光剩餘則數，此時其他訊息回 429「You have reached your monthly limit.」 — [S7 [A]](https://developers.line.biz/en/reference/messaging-api/)
- `GET https://api.line.me/v2/bot/message/quota`：回 `type`（`none`/`limited`）與 `value`（當月目標上限＝免費＋加購）；含 OA Manager 發送量 — [S7 [A]](https://developers.line.biz/en/reference/messaging-api/)
- `GET https://api.line.me/v2/bot/message/quota/consumption`：回 `totalUsage`（當月已發送則數） — [S7 [A]](https://developers.line.biz/en/reference/messaging-api/)
- 加購需在 OA Manager 選擇可加購方案並「set a maximum number of additional messages」；月中升級可增加當月免費則數 — [S6 [A]](https://developers.line.biz/en/docs/messaging-api/pricing/)
- 台灣 FAQ 題目「為有效控制預算，我該如何管理官方帳號中加購訊息的費用上限？」存在（答案未擷取） — [S1/FAQ 目錄 [A]](https://tw.linebiz.com/faq/oa-price/)

### Inferences
- 本報告推論：輕用量/中用量因「不可加購」，超額時一律 429 失敗；高用量則在達到自設加購上限時才 429。研究原型應以 quota/consumption API 做預檢，並在 429 時改為「等待使用者點『查看結果』再以 reply 送出」的退路，而不是重試 push。

### Gaps
- LINE FAQ「為何仍有剩餘則數卻收到 429」的完整說明：developers FAQ 檔案中未檢索到對應段落（只見 reference 引用），未擷取全文。

---

## Q4. 認證/進階帳號、LINE Login、LIFF、Mini App 在台灣的費用

### Takeaway
未找到可靠的台灣官方費用證據。官方服務頁只列出帳號類型（一般／認證藍盾／企業綠盾），未載明費用；本原型不需認證帳號即可使用 Messaging API。

### Cited Findings
- 帳號類型：一般官方帳號、認證官方帳號（藍盾）、企業官方帳號（綠盾）；「免費開設帳號」 — [S1 [A]](https://tw.linebiz.com/service/account-solutions/line-official-account/)
- 2018 年預告「所有帳號都可免費使用 Messaging API、無須額外審核」 — [S11 [E]](https://technews.tw/?p=411309)
- 月費「不包括素材製作費或API開發費用」 — [S1 [A]](https://tw.linebiz.com/service/account-solutions/line-official-account/)
- 專屬 ID 為另購項目（FAQ「如何購買官方帳號的專屬ID？」） — [S1 [A]](https://tw.linebiz.com/service/account-solutions/line-official-account/)

### Inferences
- 業界慣例：LINE Login / LIFF 開發者文件未見按次收費機制（本次未查證，不作結論）。

### Gaps
- 認證帳號（藍盾）申請費、企業帳號費用：未找到可靠證據。
- LINE Login、LIFF、LINE MINI App 在台灣是否收費：本次未取得官方文字，未找到可靠證據。
- 聊天進階方案官方價格：官方頁文字未載；僅 [E] 報導 NT$100/月（S14）。

---

## Q5. 成本控制對話設計

### Takeaway
研究證據顯示 Reply 不計費、一次最多 5 個訊息物件、reply token 需在約 1 分鐘內使用一次；因此「推論結果在 1 分鐘內以 reply 回覆」可做到 **0 則計費**；推論較久時用「查看結果」按鈕（postback 取得新 reply token）取代 push。

### Cited Findings
- Reply 不計入則數 — [S6 [A]](https://developers.line.biz/en/docs/messaging-api/pricing/)；Reply API 免付費 — [S2 [A]](https://tw.linebiz.com/column/LINEOA-2026-Price-Plan/)
- Reply token 一次性、1 分鐘內使用、時限可能無預警改變 — [S7 [A]](https://developers.line.biz/en/reference/messaging-api/)
- Reply 一次最多 5 個 message objects — [S7 [A]](https://developers.line.biz/en/reference/messaging-api/)
- 官方建議在準備 reply 時顯示 loading animation 告知使用者等待 — [S7 [A]](https://developers.line.biz/en/reference/messaging-api/)；[S8 [A]](https://developers.line.biz/en/docs/messaging-api/use-loading-indicator/)
- Postback event 含 reply token — [S7 [A]](https://developers.line.biz/en/reference/messaging-api/)
- 自動回應訊息、AI 自動回應、歡迎訊息、1:1 聊天不計費 — [S2 [A]](https://tw.linebiz.com/column/LINEOA-2026-Price-Plan/)

### Inferences（本報告推論，設計建議）
1. 收到圖片 webhook → 立即呼叫 loading animation（例如 `loadingSeconds` 20–60）→ 推論若在可靠時限內完成（建議以 <30–40 秒為目標，保留網路延遲餘裕），以同一 reply token 一次回覆「結果卡（Flex）＋研究用途免責聲明＋快速回覆按鈕」等最多 5 個物件。**不要先回「請稍候」**——那會用掉唯一的 reply token，導致結果只能 push。
2. 若推論可能超時：先不回覆、只顯示 loading；超過門檻則用 reply 回一則「結果處理中」並附「查看結果」postback 按鈕；使用者點擊時取得新 reply token 再回結果（0 push）。
3. Rich menu「我的最近結果」按鈕（postback）→ reply，取代主動 push 通知。
4. 只有真正非使用者觸發的通知（如研究提醒、問卷）才用 push；集中成每月 1 次、每次 1 個請求內多個對話框（仍計 1 則/人）。
5. 研究人員人工追蹤個案用 OA Manager 1:1 聊天（免費）。
6. 以 `quota`/`consumption` API 設預算警戒；設定高用量「加購上限」防止費用失控；接近上限時自動降級為 postback+reply 模式。
7. 注意月結以日本時間計，台灣時間月底 23:00 後的 push 計入次月。

### Gaps
- Reply token 在實務上的實際有效時間分布：官方明言不保證、可能變動，未找到量化證據。

---

## Q6. 成本估算表：每月 100 / 1,000 / 10,000 次照片分析（全部為本報告推論）

### Takeaway
本報告推論：設計 A（全 reply）在任何量級都可留在**輕用量 NT$0**；設計 B（每次 1 push）在 2026-11-01 新價下為 NT$0 / NT$1,000 / NT$2,200（未稅）；設計 C（每次 2 push＋每月提醒）為 NT$1,000 / NT$1,000 / NT$4,600（未稅）。

### Cited Findings（計算輸入）
- 方案輸入：輕 NT$0/200 則/不可加購；中 NT$1,000（舊 800）/3,000 則/不可加購；高 NT$1,400（舊 1,200）/6,000 則/加購第 1–50,000 則 0.2 元 — [S2 [A]](https://tw.linebiz.com/column/LINEOA-2026-Price-Plan/)；舊高用量 6,001–25,000 則 0.2 元 — [S5 [A]](https://vos.line-scdn.net/lbstw-static/assets/frontend/js-20260924-modified/cal.js)
- Reply 不計；push 按收訊人數計；一次請求 ≤5 物件仍計 1 則 — [S6 [A]](https://developers.line.biz/en/docs/messaging-api/pricing/)
- 不可加購方案超額時 429、訊息不送出 — [S6 [A]](https://developers.line.biz/en/docs/messaging-api/pricing/)；[S7 [A]](https://developers.line.biz/en/reference/messaging-api/)

### Inferences（本報告推論）

**假設**
- 每次分析對應 1 位使用者的 1:1 聊天；所有 push 為單一 userId 的 Push API，每次請求 ≤5 個物件 → 1 push = 1 則。
- 設計 A：照片→loading→reply 結果（必要時 postback「查看結果」→reply）；push = 0。
- 設計 B：每次分析 1 則 push（推論完成後主動送結果，含結果＋說明於同一請求）。
- 設計 C：每次分析 2 則 push（收件確認＋結果，分兩次請求）＋每位活躍使用者每月 1 則提醒 push。**使用者數假設：平均每人每月 5 次分析** → 20 / 200 / 2,000 人（此比例為假設，非來源數字）。
- 封鎖者與無效 ID 不計（S6），此處假設 0。稅前金額；含稅欄以 5% 營業稅假設估算（稅率未經本次官方來源查證）。
- 選擇「能涵蓋則數的最便宜方案」；中用量上限 3,000 則不可加購。

**每月計費則數**

| 設計 | 100 次 | 1,000 次 | 10,000 次 |
|---|---|---|---|
| A 全 reply | 0 | 0 | 0 |
| B 1 push/次 | 100 | 1,000 | 10,000 |
| C 2 push/次＋每人月提醒 | 2×100+20 = 220 | 2×1,000+200 = 2,200 | 2×10,000+2,000 = 22,000 |

**自 2026-11-01 起（新價，未稅，NT$）**

| 設計 / 量級 | 最低可行方案 | 計算 | 月費用（未稅） | 含 5% 稅估算 | 每次分析成本 |
|---|---|---|---|---|---|
| A / 100 | 輕用量 | 0 | 0 | 0 | 0 |
| A / 1,000 | 輕用量 | 0 | 0 | 0 | 0 |
| A / 10,000 | 輕用量 | 0 | 0 | 0 | 0 |
| B / 100 | 輕用量（100 ≤ 200） | 0 | 0 | 0 | 0 |
| B / 1,000 | 中用量（≤3,000） | 1,000 | 1,000 | 1,050 | 1.00 |
| B / 10,000 | 高用量 | 1,400 + (10,000−6,000)×0.2 = 1,400 + 800 | 2,200 | 2,310 | 0.22 |
| C / 100 | 中用量（220 > 200） | 1,000 | 1,000 | 1,050 | 10.00 |
| C / 1,000 | 中用量（2,200 ≤ 3,000） | 1,000 | 1,000 | 1,050 | 1.00 |
| C / 10,000 | 高用量 | 1,400 + (22,000−6,000)×0.2 = 1,400 + 3,200 | 4,600 | 4,830 | 0.46 |

**至 2026-10-31 止（舊價，未稅，NT$；供比較）**

| 設計 / 量級 | 方案 | 計算 | 月費用 |
|---|---|---|---|
| A / 全部 | 輕用量 | 0 | 0 |
| B / 100 | 輕用量 | 0 | 0 |
| B / 1,000 | 中用量 | 800 | 800 |
| B / 10,000 | 高用量 | 1,200 + 4,000×0.2 | 2,000 |
| C / 100 | 中用量 | 800 | 800 |
| C / 1,000 | 中用量 | 800 | 800 |
| C / 10,000 | 高用量 | 1,200 + 16,000×0.2 | 4,400 |

**「固定在某方案」時的可行性矩陣（新價；✗＝超出部分 push 會 429 失敗）**

| 情境（則數） | 輕用量 NT$0（200） | 中用量 NT$1,000（3,000） | 高用量 NT$1,400（6,000＋加購） |
|---|---|---|---|
| A 任何量（0） | ✓ NT$0 | ✓ NT$1,000（浪費） | ✓ NT$1,400（浪費） |
| B-100（100） | ✓ NT$0 | ✓ NT$1,000 | ✓ NT$1,400 |
| B-1,000（1,000） | ✗ 第 201 則起失敗（800 則結果送不出） | ✓ NT$1,000 | ✓ NT$1,400 |
| B-10,000（10,000） | ✗ | ✗ 第 3,001 則起失敗 | ✓ NT$2,200 |
| C-100（220） | ✗ 超 20 則 | ✓ NT$1,000 | ✓ NT$1,400 |
| C-1,000（2,200） | ✗ | ✓ NT$1,000 | ✓ NT$1,400 |
| C-10,000（22,000） | ✗ | ✗ | ✓ NT$4,600 |

**敏感度（本報告推論）**
- 設計 C 若去掉每月提醒，100 次＝200 則，剛好落在輕用量上限（NT$0），但無任何緩衝；任何額外 push（例如重送）就會 429。
- 設計 B/C 在高用量下，每多 1 則 push 邊際成本 NT$0.2（未稅），直到當月加購 50,000 則；之後 NT$0.15。
- 與設計 A 相比，設計 C 在 10,000 次/月時每年多出約 NT$4,600×12 = NT$55,200（未稅）。
- 混合設計（多數 reply、僅少量 push 通知）只要每月 push ≤200 則即可維持 NT$0。

### Gaps
- 使用者人數/每人分析次數比例為假設，需以實際研究招募數據替換。
- 含稅金額之 5% 稅率未於本次官方來源查證。
- 未計入伺服器、模型推論、儲存等非 LINE 成本（不在本題範圍）。
