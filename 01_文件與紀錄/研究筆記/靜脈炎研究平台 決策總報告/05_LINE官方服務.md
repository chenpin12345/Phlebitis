# 第 5 段：靜脈炎 LINE 官方服務設計 —— 報告摘錄與整合筆記

> 來源報告：`C:/Users/user/Desktop/Phlebitis/reports/靜脈炎 LINE 官方服務設計.md`（2,895 行，已從 L1 讀到 L2895）。報告標題：「讓 reply 扛成本、讓本機守照片：靜脈炎 LINE 研究服務設計」。
> 輔助查閱：`research_notes/靜脈炎 LINE 官方服務設計/` 01–08 號筆記（用 grep 核對「2 秒」、MINI App 日期、錯誤通知日期、推論時間、Cloudflare TLS 等不清楚的地方）。
> 本筆記中的「L###」是原報告的行號。報告自述撰寫日是 2026-10-31，查閱日都落在 2026-10-30 至 10-31（L23）。本筆記撰寫日是 2026-11-01。
> 報告的分級：[A] 官方文件、主管機關、報告規範；[B] 系統性回顧、統合分析、頂尖期刊或會議；[C] 一般同儕審查；[D] 預印本；[E] 部落格、官方範例程式碼、論壇、新聞、廠商文件，只能作輔助（L27–33）。
> 報告的用語標記：**研究證據顯示**＝有 [A]–[C] 明文支持；**業界慣例**＝常見實務、本輪沒有同儕審查佐證；**本報告推論**＝作者推導，需實測或交 IRB 判斷（L41–45）。筆記中的「僅搜尋摘要」「未逐字核對」「未找到可靠證據」，報告都保留原標記、沒有升級（L47）。⚠＝與不可違反原則衝突或可能衝突（L49–51）。
> **文件日期通則：** LINE Developers 文件頁（包括 `index.html.md` 版）**都沒有標示最後更新日**，報告一律記為「頁面未標更新日」並附查閱日（L35–37、L2010、L2606）。以下凡寫「LINE 頁面」都適用這條規則。
> **NEW 補查：** 報告中沒有發現自相矛盾的 LINE 數字，所以**沒有另上 developers.line.biz 補查，本筆記沒有 NEW 項目**。內部不一致的地方列在 J 節。

---

## A. 各主題的關鍵結論

### Takeaway
報告的核心結論是：只要採「全 reply」設計，每月 100、1,000、10,000 次分析的 LINE 訊息費都是 NT$0（L3）。真正的風險有四項（L5–11）：(1) 走聊天傳的照片一定會先暫存在 LY Corporation 的伺服器 ⚠；(2) webhook 必須極快回 200（錯誤統計頁摘要寫約 2 秒）；(3) LINE 縮圖與重新編碼會造成 domain shift；(4) 在 14 位個案的規模下，任何「新模型較好」的統計結論都不成立，而自動擴大的金絲雀發布違反「不自動上線」⚠。報告另有三項提醒：台灣 2026-11-01 調價（L13）；撤回同意的條文應更正為《人體研究法》第 14 條第 1 項第 6 款，不是第 19 條（L15）；LIFF SDK v2.20.0–v2.31.0 有安全問題，約 2026-11-24 起限制使用（L17）。

### Cited Findings

#### A1. Webhook、簽章、重送、reply token、loading animation、併發（第 1 節，L113–291）
- **結論（L117–125）**：handler 只做三件事：用 raw bytes 做 HMAC-SHA256 驗簽（X-Line-Signature）→ 以 `webhookEventId` 為唯一鍵寫入 SQLite → 立刻回 200。下載、品質檢查、YOLO 與分類推論全部交給背景 worker。worker 在一分鐘內用 reply token 回覆，推論期間顯示 loading animation。只有 token 逾時或失效時，才改走「查看結果」postback（免費）或 push（計費）。事件可能重複、亂序，也可能一次多個或空陣列，所以每個事件各建一個 job，同一使用者的 job 依 `timestamp` 序列化，GPU 全域只開一個推論 worker。類型：設計屬本報告推論；官方要求屬研究證據顯示 [A]。
- **簽章**（研究證據顯示，[A]，L129–136）：以 channel secret 為金鑰，對 request body 做 HMAC-SHA256，結果以 base64 編碼放在 `x-line-signature`。官方要求以 UTF-8 驗證，原文 "Don't modify data prior to verifying the signature on any request."。官方列出的常見錯誤：先 `json.loads` 再序列化、pretty-print、跳脫字元誤解、proxy 改寫 body、誤用 HMAC-SHA1、用錯 channel 的 secret、另一位管理員已重發 secret。簽章缺漏或不符時「不處理事件、以錯誤結束」。LINE Platform 的 IP 不公開，應靠驗簽，不要做 IP 限制。出處：[Verify webhook signature](https://developers.line.biz/en/docs/messaging-api/verify-webhook-signature/)、[Development guidelines](https://developers.line.biz/en/docs/messaging-api/development-guidelines/)，兩頁都未標更新日，查閱 2026-10-31。
- **官方 SDK**（[E] 官方 SDK，L138）：v3 的 `WebhookParser.parse()` 先驗簽再 `json.loads`，用 `hmac.compare_digest` 做常數時間比對；未知事件型別包成 `UnknownEvent`（[webhook.py](https://github.com/line/line-bot-sdk-python/blob/master/linebot/v3/webhook.py)）。3.x 與 2.x 不相容，往後只維護 `linebot.v3`，需要 Python ≥ 3.10（[SDK README](https://github.com/line/line-bot-sdk-python)）。3.0.0 的釋出日期：**未找到可靠證據**。官方 FastAPI 範例用 `headers['X-Line-Signature']` 直接索引，header 缺漏時會拋 KeyError 變成 500，「不能照抄」（[fastapi-echo/main.py](https://github.com/line/line-bot-sdk-python/blob/master/examples/fastapi-echo/main.py)，[E]，L212）。
- **回應與非同步**（[A]，L140–148）：原文 "The bot server must return status code `200` after it receives the HTTP POST request"；LINE 可能送來 `events` 為空陣列的 POST 以確認連線；原文 "We recommend that you process webhook events asynchronously."（[REF](https://developers.line.biz/en/reference/messaging-api/)、[RECV](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)）。錯誤統計頁把 `request_timeout` 描述為「已送出但沒有回應」，頁面摘要寫 bot server 沒有在 2 秒內回應（[ERRSTAT](https://developers.line.biz/en/docs/messaging-api/check-webhook-error-statistics/)）。這個「2 秒」來自 WebFetch 的頁面摘要，**上線前應打開原頁逐字確認**；RECV 與 REF 都沒有明列逾時秒數（L148；01 號筆記 L101、L143 相同）。
- **重送與去重**（[A]，L150–161）：重送預設關閉，要在 Console 的 Messaging API 分頁手動開啟，只在 bot 沒有回 2xx 時重送。原文 "The number and interval of the webhook redelivery aren't disclosed"，而且可能不經通知變更。重送不保證送達；重送量暴增影響平台時，LINE 可能強制關閉重送。重送事件和原事件只差在 `deliveryContext.isRedelivery`，`webhookEventId`（ULID）不變。官方建議以 `webhookEventId` 偵測重複，因為網路路由也可能造成重複送達。bot 長期收不到 webhook 時，平台可能暫停發送（[RECV](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)）。時間線：2022-03-07 日文公告「2022 年 4 月上旬起新增 Webhook 再送機能」（[ja/38](https://developers.line.biz/ja/news/38/)，[A]，日期取自搜尋摘要）。
- **Reply token**（[A]，L163–172）：原文 "Reply tokens can only be used once."、"Reply tokens must be used within one minute after receiving the webhook."，時限可能不經通知變更。過期或已用過的 token 回 400 "Invalid reply token"，訊息不會送出。重送事件中的 reply token "can be used except in certain cases"，certain cases 的內容**未找到可靠證據**。`mode: standby` 的事件不帶 reply token，bot 不應發訊息（[REF › Send reply message](https://developers.line.biz/en/reference/messaging-api/#send-reply-message)、[RECV](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)）。
- **Loading animation**（[A]，L174–183）：`POST https://api.line.me/v2/bot/chat/loading/start`；`loadingSeconds` 5–60 秒、須為 5 的倍數、預設 20；只支援一對一聊天；時間到或 OA 送出新訊息時消失；只有使用者正在看聊天畫面時才顯示；一律回 202，包括使用者已封鎖或刪除帳號的情況；速率上限 100 req/s；需要 LINE iOS／Android 13.16.0 以上（[Use loading indicator](https://developers.line.biz/en/docs/messaging-api/use-loading-indicator/)、[REF](https://developers.line.biz/en/reference/messaging-api/#display-a-loading-indicator)）。2024-04-17 推出，日期取自 news URL 路徑（[news](https://developers.line.biz/en/news/2024/04/17/loading-indicator/)）。限制：一篇 [E] 實測遇過 API 回成功、畫面卻沒顯示（[classmethod](https://dev.classmethod.jp/articles/try-to-use-line-messaging-api-of-indicating-loading-animation/)，L210）。
- **事件順序與內容**（[A]，L185–193）：原文 "the order of webhook events you receive can be different from the order the events occurred"，以 `timestamp` 判斷先後；一次 POST 可含多個事件；`destination` 是接收方 bot 的 user ID；imageSet 的多張圖以未定義順序送達；bot 必須容忍非破壞性變更（新增欄位、新增 enum 值、屬性順序改變）。
- **Push 冪等**（[A]，L195–203）：`X-Line-Retry-Key` 只適用於 push、multicast、narrowcast、broadcast；格式是自產 UUID，首次請求就要帶，首次請求後 24 小時內有效；重複的 key 回 409 並附 `x-line-accepted-request-id`；只在 500 或網路逾時時重試；retry key 只防重複、不保證送達（[Retrying API request](https://developers.line.biz/en/docs/messaging-api/retrying-api-request/)）。
- **限制與未知數**（L205–213）：沒有正式 SLA 數字（未找到可靠證據）；重送不可靠；重送事件的 token 不一定能用，而且往往已超過一分鐘；佇列設計「先持久化、再回 2xx、背景處理、冪等消費」屬**業界慣例**；單次 webhook 最多幾個事件、429 是否帶 `Retry-After`：**未找到可靠證據**。
- **適用性**（L215–219）：現在（14 位個案）適用，因為 Windows 單機會停機、重開機、跑 Windows Update。推論需要好幾秒（品質檢查、YOLO、EfficientNet 或 DINOv2），**絕不能在 handler 內同步執行**。未來（約 1,000 張或每月上萬次）更重要，GPU 佇列可能讓 job 逼近一分鐘時限，應依「剩餘 token 壽命」排序並啟用 postback 退路（本報告推論）。
- **實作要點**（本報告推論，L221–271）：FastAPI 虛擬碼——取 raw bytes、body >1,000,000 回 413、header 用 `.get` 缺漏回 400、`compare_digest`、驗簽後才 parse、同一 transaction `INSERT OR IGNORE`、`mode == "active"` 才建 job、目標 <100 ms 回 200；webhook-svc 的 `docs_url`／`redoc_url`／`openapi_url` 設 None。資料表：`webhook_events`（PK `webhook_event_id`，加 `is_redelivery`、`type`、`timestamp`、`received_at`、`status`）；`jobs`（UUID、`webhook_event_id` UNIQUE、`reply_token`（加密或只放記憶體）、`webhook_received_at`、`status`、`attempts`、`next_attempt_at`、`retry_key`；status 值 queued、downloading、inferring、replied、pushed、postback_offered、failed、dead）。SQLite 開 WAL，用 `UPDATE … WHERE status='queued' … RETURNING` 搶佔；啟動時把卡在 downloading 或 inferring 的 job 收回成 queued。worker 流程：loading（`loadingSeconds` 20–30）→ Get content → 品質檢查 → 推論 → 若 `now - webhook_received_at < 約 50 秒` 就 reply（最多 5 個物件：結果卡、紅旗提醒、quick reply），否則走第 8 節退路。排程：單一 GPU worker、token 最早到期者優先、同一使用者依 `timestamp`、standby 只記錄不回覆、未知事件只記錄並略過、不回非 2xx。**影子模型在 reply 送出之後才在同一 worker 的低優先佇列執行，失敗不影響主流程，也不計入主要 KPI**（L267–269）。
- **驗證**（L273–281）：簽章單元測試（emoji、`\n`、CRLF、跳脫字元、錯 secret、缺 header，預期 400 不出現 500）；同一 `webhookEventId` 送 3 次只產生 1 個 job；worker 在 inferring 階段被殺後重跑且只回覆一次；人為延遲 65 秒，驗證走 postback 或 push 退路並記錄 400；Console 開 Error statistics aggregation 一週，`request_timeout` 應為 0；每日以 `GET /v2/bot/message/delivery/reply?date=` 對帳，差異應為 0（通常隔日才算完）；先在工作台的 LINE 模擬器跑，再用一個測試帳號真機測試。
- **風險表**（L285–291）：另一位管理員重發 secret →「400 激增」告警加輪替 runbook；proxy 改寫 body → Console Verify 與含 emoji 的測試；GPU 排隊 → 「最舊 queued job >45 秒」告警加 postback；重送灌水統計 → 以 `webhook_event_id` 去重並排除 `isRedelivery`；reply 遇 5xx 或逾時無法確定是否送達（reply 不支援 retry key）→ 記 `x-line-request-id`，一分鐘後標「未知」、不重送。

#### A2. 台灣計費與額度（第 2 節，L295–430）
- **結論**（[A]，研究證據顯示，L297–309）：台灣 LINE OA **明文規定 Reply API、一對一聊天、自動回應、AI 自動回應、加入好友歡迎訊息都不計費**。Push、Multicast、Broadcast、Narrowcast 按「收訊人數」計算則數；一次請求放 1 到 5 個訊息物件都只算 1 則。新價（2026-11-01 起，皆未稅）：輕用量 NT$0／200 則／不可加購；中用量 NT$1,000（原 NT$800）／3,000 則／不可加購；高用量 NT$1,400（原 NT$1,200）／6,000 則／前 50,000 則每則 NT$0.2、第 50,001 則起每則 NT$0.15。
- **調價公告**（[A]，L313–326）：公告日 2026-09-01，生效日 2026-11-01（[S2](https://tw.linebiz.com/column/LINEOA-2026-Price-Plan/)，dateModified 2026-09-01，查閱 2026-10-30）。原文「下方金額說明皆為未稅價格」。中用量「不可加購；如需發送更多訊息，需升級為高用量方案」。原文「超過免費訊息則數後，才會依上述級距計算加購訊息費用」。過渡規定：2026-10-27 之後仍使用中、高用量即視為同意新價；信用卡自動續繳者 11 月 1 日依新價扣款；系統維護期間「變更訊息則數上限」等功能暫停，時段為 2026-10-28 08:00 至 2026-11-02，以及 2026-11-24 08:00 至 2026-11-25；「付費週期部分沒有調整」。
- **官方計算機程式碼**（[A]，L328–330）：`moderateFreeNew26 = 1000`、`highFreeNew26 = 1400`；公式 `min(extra,50000)*0.2 + max(0,extra-50000)*0.15`（[S5 cal.js](https://vos.line-scdn.net/lbstw-static/assets/frontend/js-20260924-modified/cal.js)，版本路徑 2026-09-24，查閱 2026-10-31）。
- **舊價**（2026-10-31 以前，[A]，L332–340）：輕用量 NT$0／200；中用量 NT$800／3,000、不可加購；高用量 NT$1,200／6,000，6,001 至 25,000 則每則 0.2 元，之後逐級遞減至 0.066 元（[S3 FAQ](https://tw.linebiz.com/faq/oa-price/message-price-list/)、S5）。
- **計費規則**（[A]，L342–369）：不計費項目原文「一對一聊天訊息、自動回應訊息、加入好友的歡迎訊息、Messaging API 中的 Reply API 功能」（[S1](https://tw.linebiz.com/service/account-solutions/line-official-account/)，頁面資源版本 2026-09-24，查閱 2026-10-30）；2026 公告另列 AI 自動回應（S2）。原文 "The number of messages is counted by the number of people you send a message to."、"The number of message objects in a request doesn't affect the number of messages sent."；傳給已封鎖者或不存在的 user ID 不計費（[Pricing](https://developers.line.biz/en/docs/messaging-api/pricing/)，頁面未標更新日，查閱 2026-10-30）。後台群發每次最多 3 個對話框，Push API 每次最多 5 個；多頁訊息最多 9 頁只算 1 個對話框（[S4](https://tw.linebiz.com/faq/oa-price/how-to-calculate-message-expense/)）。計費時區原文「系統計算的時區為日本時區（GMT+9:00），台灣時間 23:00 起傳送的訊息會被計算到隔日」（S1）。超額原文 "When you exceed the limit of messages that can be sent in a month, an error response will be returned and the messages won't be sent."，回 429 "You have reached your monthly limit."；有時即使還有剩餘則數也可能收到 429，進行中的 narrowcast 也可能暫時扣光額度。監控：`GET /v2/bot/message/quota`（含 OA Manager 發送）、`GET /v2/bot/message/quota/consumption`（`totalUsage` 為 approximate）。
- **限制**（L387–392）：loading animation 是否計費，官方沒有明文說免費，本報告推論不計費（**未找到可靠證據**）。認證帳號（藍盾）、企業帳號（綠盾）、LINE Login、LIFF、LINE MINI App 在台灣的費用：**未找到可靠證據**。5% 營業稅是估算假設，**未經本次官方來源查證**。聊天記錄：工商時報說未升級帳號只保留近 6 個月，「聊天進階方案」每月 NT$100 可保存 5 年（[工商時報 2026-04-15](https://www.ctee.com.tw/news/20260415701121-430502)，[E]）；官方服務頁只寫「儲存2024年1月1日起的聊天記錄」（S1）。本報告推論：研究紀錄不能依賴 OA Manager，必須由本機自行保存。
- **適用性與實作**（L394–416）：每月 push ≤200 → 輕用量 NT$0；201–3,000 → 中用量 NT$1,000；>3,000 → 高用量 NT$1,400 起。實作：**不要先回「請稍候」**（會用掉唯一的 reply token）；逾時退路用 postback（postback 事件帶新的 reply token，[A]）；圖文選單放「我的最近結果」postback；每天以 quota 與 consumption 檢查，接近上限時自動降級為只走 postback；不要重試額度 429；月底台灣時間 23:00 以後的 push 算下個月；2026-11-24 08:00 至 11-25 維護期間方案異動暫停。
- **風險**（L426–430）：系統預設用 push 補發時，輕用量第 201 則起失敗（例如每月 1,000 次分析時有 800 則送不出，本報告推論）；一次最多 5 個物件，只顯示最後一則訊息的 quick reply（[Use quick replies](https://developers.line.biz/en/docs/messaging-api/using-quick-reply/)，[A]）；方案被誤改 → 每月檢查，改方案須研究主持人核准。

#### A3. 圖片內容 API、限制、EXIF、壓縮（第 3 節，L434–576）
- **結論**（L436–445）：`GET https://api-data.line.me/v2/bot/message/{messageId}/content` 取得的內容會「一段時間後自動刪除」，期限不公開，官方也承認可能被縮小。所以收到 webhook 就立刻下載，原樣保存 bytes 並算 SHA-256；推論只用完整檔、不用 preview；`external` 直接拒收；EXIF 與 GPS 沒有官方說法，一律自行檢查並移除 GPS。LINE 預設標準畫質把長邊縮到約 1,478 px 並重新編碼，屬系統性差異，評估必須依來源分層。
- **官方行為**（[A]，[REF Markdown 版](https://developers.line.biz/en/reference/messaging-api/index.html.md)，頁面未標更新日，查閱 2026-10-31，L449–459）：原文 "Content is automatically deleted after a certain period from when the message was sent"；"Content sent by users may be transformed internally, such as shrinking."；202 表示準備中，404 表示不存在，410 "The content is gone" 表示 unsend；preview 原文 "converted to a smaller data size than the original content"，對非影像呼叫回 400；Transcoding 只適用影片與音訊，對圖片回 400；`contentProvider.type = line` 用 Get content，`external` 原文 "isn't provided by LY Corporation"；`imageSet` 的 `index` 從 1 起算，原文 "The webhooks are delivered in an undefined order"；Get content 在 rate limit 表中沒有專屬一列，推定適用 Other 2,000 req/s，但官方沒有直接寫；**單檔大小上限：未找到可靠證據**。
- **網域變更**（[A]，L461–463）：api.line.me 改為 api-data.line.me，2019-11-08 公告，要求 2020-04-30 前更新（[News](https://developers.line.biz/en/news/tags/messaging-api)）。
- **LINE App 傳圖畫質**（[E] 實測，只測 iPhone，L465–476）：[app-liv](https://app-liv.jp/articles/121899)（最後更新 2025-11-06，iPhone XS MAX）原圖 3024×4032、2.54 MB；標準 1108×1478、283 KB；高畫質 1774×2364、744 KB；原始畫質 3024×4032、1.9 MB。[appllio](https://appllio.com/line-send-original-size-photos)（2025-03-02，iPhone 11 Pro Max）原圖 3.7 MB；標準 1109×1479、604 KB；高畫質 1774×2365、1.5 MB；原始畫質下 10 MB 的圖降為 5.3 MB，6 到 7 MB 的圖無損送出。Android 12（AQUOS sense6）約 349 KB，沒有像素數。**Bot 透過 Get content 收到的像素是否等於傳送端選的畫質，沒有公開實測。** 相簿原始畫質上限 20 MB、1 億像素，這是相簿規格、不是聊天傳送（[LINE Help](https://help.line.me/line/smartphone/sp?contentId=20000248&lang=en)，[A]，僅搜尋摘要）。
- **相機、HEIC、EXIF**（L478–486）：內建相機是否套用美肌、濾鏡或不同壓縮：**未找到可靠證據**。以「檔案」方式傳 .heic 會原樣送出（[fileconv](https://fileconv.pages.dev/en/blog/heic-share-tips)，[E]，單一來源）；以「照片」方式傳是否轉 JPEG、色彩描述檔是否轉換：**未找到可靠證據**。EXIF 沒有官方聲明；[E] 說法不一（[dime.jp](https://dime.jp/genre/1974458/) 說會刪位置，僅搜尋摘要，而且說的是 App 對 App 傳送）；Orientation 處理方式：**未找到可靠證據**。
- **對模型表現的證據**（L488–499）：Young et al. 2021（[C]）：旋轉、亮度、對比、水平翻轉下，6.5%–22% 的病灶預測翻轉，VAMC-T 為 15.8%；同次就診補拍的照片有 30%（24/79）預測不一致；TTA 沒有改善 AUROC；7 組測試資料中 5 組是外部驗證；**文中沒有說明是否以病人為單位切分**；沒有測 JPEG 或模糊（[PMC7820258](https://pmc.ncbi.nlm.nih.gov/articles/PMC7820258/)）。Dodge & Karam 2016（[C／會議]）：對模糊與雜訊敏感，對一般品質範圍的 JPEG 相對穩健，屬自然影像（[arXiv](https://arxiv.org/abs/1604.04004)）。Afifi & Brown ICCV 2019（[B]）：白平衡錯誤會降低 DNN 表現，一般色彩擴增無法模擬，作者提出 WB emulation。數位病理壓縮比 24:1 以內穩健，用低品質影像訓練可改善（[PMC7113072](https://pmc.ncbi.nlm.nih.gov/articles/PMC7113072/)，[C]）。遠距皮膚科病人自拍：「品質足夠」62.2%、「有助決策」55.1%；另一研究 91.2% 品質足夠，主因失焦（[C]，僅摘要）。照片判斷靜脈炎的 AI 只找到試驗登錄 [NCT07889895](https://clinicaltrials.gov/study/NCT07889895)，**尚無結果**。直接研究「經 LINE 或 WhatsApp 傳送後皮膚或傷口 AI 表現」的論文：**未找到可靠證據**。
- **反面證據**（L501–505）：某些 JPEG 品質因子的訓練與推論組合反而有害（TUM／MICCAI 2022 workshop，[C]，僅搜尋摘要），所以「用模擬壓縮做擴增」不保證有效；大多數證據不是皮膚臨床照片，紅斑分期對色彩誤差的敏感度：**未找到可靠證據**；Android 的像素數與品質因子：**未找到可靠證據**。
- **適用性**（L507–516）：現在（約 120 張、14 人）有條件適用。立即下載、原樣保存、metadata、去 GPS 可以馬上做；依來源分層的評估幾乎沒有檢定力，只適合描述性比較，以及「同一張照片模擬 LINE 壓縮後預測是否翻轉」的壓力測試；**不能下「LINE 照片表現較差」的結論**（本報告推論）。未來（約 1,000 張、三類平衡）可以做分層指標加 CI、leave-source-out，前提是**以病人為單位切分**，同一病人不同日期、不同手（LH、RH、LL、RL）都放在同一側。
- **實作**（本報告推論與業界慣例，L520–557）：串流下載並設上限（例如 20 MB）；遇 202 或 5xx 時指數退避 3 次；原樣寫檔，**不要先用 PIL 重存**。metadata 欄位：`sha256`、`message_id`、`imageSet.id/index/total`、`contentProvider.type`、`webhook timestamp`、`user_pid`；`magic_format`、`width/height`、`bytes`、`jpeg_qf_est`；`exif_present`、`orientation`、`has_gps`（只存布林值）；`source_channel`（hospital_camera／line_oa／line_file）。工作副本：`Image.open(buf, formats=["JPEG","PNG"])` → `verify()` → 重開 `load()`；把 `DecompressionBombWarning` 升級為錯誤，**不可**設 `MAX_IMAGE_PIXELS=None`（[Pillow 13.0.0](https://pillow.readthedocs.io/en/stable/reference/Image.html)，[A]）；`ImageOps.exif_transpose`、去 GPS、以隨機 UUID 另存，模型只讀工作副本；原始 bytes 可能含 GPS，要加密並限制存取。Laplacian 先縮到固定長邊（例如 1,024 px）再算。先做實測矩陣，再把醫院原檔縮到實測長邊、以實測品質因子重新編碼，當作擴增與壓力測試；[E] 的 1478 與 2364 只作初始值；**訓練一律由人工啟動**。WB emulation 擴增（Afifi 的 WB_color_augmenter，或色溫與 tint 抖動）。imageSet 每張各自分析、各自用自己的 reply token 回覆，以 `imageSet.id` 加 `index` 重組。unsend（410）觸發這張照片的研究資料刪除，和撤回同意的統計分開記錄（RECV [A]：官方建議從顯示與儲存中移除）。
- **驗證**（L559–563）：無病人的含 GPS 測試照（建議放灰卡）；至少 2 台 iOS 加 2 台不同品牌 Android；各用標準、高、原始畫質傳「照片」，再用「檔案」各傳一次；記錄像素、QF、EXIF（GPS、DateTimeOriginal、Make/Model、Orientation）與色彩描述檔；翻轉率以病人為單位彙總；每次評估依 `source_channel` 分層並附 n 與 Wilson CI。
- **風險排序**（本報告推論，L565–576）：色偏與白平衡第一、模糊第二、解析度下降第三、JPEG 量化第四（對 224 px 分類器影響可能最小）。

#### A4. Rich menu、Flex、quick reply、LIFF、MINI App 與拍照引導（第 4 節，L579–825）
- **結論**（L581–595）：選介面之前要先決定**照片可不可以經過 LINE 平台**。如果 IRB 允許而且同意書揭露，最快的組合是：per-user rich menu 分「同意前」與「同意後」兩套；quick reply 放「拍照」（camera）與「從相簿選」（cameraRoll）；伺服器收到照片後自動做品質檢查並回覆。如果照片不得經過任何第三方，就走 LIFF（或未認證的 MINI App）直接上傳到我方 HTTPS，LINE 只負責入口、通知與 ID token。約 1,000 張時建議統一走 LIFF，SDK 必須 **v2.31.1 以上**；MINI App 的認證流程不適合研究原型。拍照引導方面，證據最一致的是**即時品質回饋加重拍**，只給書面指示效果不一致。
- **Rich menu**（[A]，查閱 2026-10-31，頁面未標更新日，L599–635）：JPEG 或 PNG；寬 800–2500 px；高 ≥250 px；寬高比 ≥1.45；≤1 MB；設定後圖片不能替換。每帳號以 API 最多建立 1,000 個 rich menu、1,000 個 alias；每個選單最多 20 個點擊區；`chatBarText` 最多 14 字元；批次綁定一次最多 500 個 user ID。優先序：per-user（API）> API 預設 > OA Manager 預設。per-user **立即生效**；API 預設要等使用者重開聊天室，原文「It may take up to a minute」；原文 "Rich menus aren't displayed on LINE for PC"。`richmenuswitch` 只能用在 rich menu，點擊後以 postback 回傳 `newRichMenuAliasId`，`label` 最多 20 字元，無障礙功能會朗讀。alias 切換時看到的是優先序最高的 per-user 選單，所以對已切換過的使用者，清除預設選單沒有效果。速率（token bucket，以 channel 計）：建立 rich menu、刪除 rich menu、刪除 alias、查詢批次狀態 100 次／小時（OA Manager 操作不計入）；批次取代或解除 3 次／小時；取得清單 10 次／秒；個別綁定或解除 2,000 次／秒。01 號筆記概述為「建立或刪除」，04 號筆記逐條核對官方表格，**以官方表格為準**。2024–2026 年規格是否變更：**未找到可靠證據**。
- **Flex Message**（[A]，L637–648）：bubble JSON ≤30 KB；carousel ≤50 KB、最多 12 個 bubble；**`altText` 必填、最多 1,500 字元**；同一則會因 OS、LINE 版本、解析度、語言與字型而呈現不同；`scaling: true` 讓字級跟著 LINE 字體設定縮放，需 LINE iOS／Android 13.6.0 以上（PC 7.17.0 以上）；`adjustMode: shrink-to-fit` 是 best-effort；`filler` 已標示 deprecated。筆記衝突裁決：08 號把 altText 1,500 標為 [E]，04 號以官方 Markdown grep 驗證為 [A]，報告採 **[A]**；文字訊息上限 5,000 字元只有 [E] 廠商文件一致記載，維持 [E]。
- **Quick reply**（[A]，查閱 2026-10-30 至 31，L650–658）：每則最多 13 個按鈕；一次回多則時只顯示最後一則的 quick reply；camera、cameraRoll、location **只能用在 quick reply**；一般按鈕點擊後消失，camera 與 cameraRoll 保留到使用者實際送出資料；只支援 iOS 與 Android，文件沒有列 PC；camera 的 label 最多 20 字元。
- **LIFF**（[A]，L660–694）：最新版 **v2.31.2（2026-10-07）**；v2.31.1 安全修正（2026-09-30）；官方原文 "LIFF v2.20.0 - v2.31.0 have been deprecated because an issue with potential security implications was identified"，預定 "around November 24, 2026" 限制舊版（[release notes](https://developers.line.biz/en/docs/liff/release-notes/)；news [2026-09-30](https://developers.line.biz/en/news/2026/09/30/release-liff-2-31-1/)、[2026-10-20](https://developers.line.biz/en/news/2026/10/20/liff-sdk-issue/)，news 頁需 JS 渲染，未讀到全文）。2019-11-11 公告、2020-02-05 生效：Messaging API channel 不能再新增 LIFF app，LIFF 要建在 LINE Login channel 上，每個 channel 最多 30 個；endpoint 必須是 https、不含 URL fragment；尺寸 Compact／Tall／Full；LIFF URL 會經 LY 的 LIFF 伺服器轉址到開發者 endpoint。LIFF 瀏覽器在 iOS 是 WKWebView、Android 是 Android WebView；官方列的不支援項目只有 theme-color、download 屬性、加入主畫面、Service Workers，**`<input type="file">`、`capture`、getUserMedia 都不在清單上**。[E] 實務：Android 14 上 `accept="image/*"` 只開相簿（zenn.dev）；iOS 17 上 `capture` 沒有開相機（Stack Overflow mirror）。身分：`liff.getIDToken()` 需要 `openid`，JWT 有效 1 小時；官方原文 "Don't send the details of the user profile obtained with liff.getDecodedIDToken() and liff.getProfile() to the server"；把 ID token 傳到伺服器，以 `POST /oauth2/v2.1/verify` 驗證；傳 access token 則用 `GET /oauth2/v2.1/verify` 加 `GET /v2/profile`。
- **LINE MINI App**（[A]，L696–713）：任何人都能建立未認證 MINI App，但功能受限、header 顯示 endpoint 網域；台灣或泰國原文 "only LINE MINI App channels under a certified provider can apply for the verification review"，台灣透過 LINE Biz-Solutions 申請；MINI Apps 分頁只在日本；只能用 Full 尺寸，不能隱藏 action button。時間線：2023-12-13 LIFF URL 改為 `miniapp.line.me`（經搜尋摘要轉述）；2025-02-12 宣布 LIFF 將整合進 MINI App，建議新 LIFF app 以 MINI App 建立；2025-10-01 起可在網頁瀏覽器使用（04 號筆記 L149：2025-09-26 公告、2025-10-01 生效）。整合完成日期：**未找到可靠證據**。從 LINE Login channel 建的 LIFF 事後不能遷移成 MINI App（Classmethod，[E]，未在官方 FAQ 驗證，L738）。
- **拍照引導證據**（L715–731）：O'Connor JAMA Dermatol 2017（40 對親子 RCT，[C]）：3 步驟指示對診斷一致性**沒有顯著效果**（85% 對 80%，P=.68），品質分數略高（9.5 對 8.9，P=.04）。Liu 2024（[C] 回溯，**反證**）：沒有指示時 113 組中 103 組（91.2%）品質足夠。Saade 2025（360 人，[C]）：一致性病人自拍 79%、簡短訓練後 84%、住院醫師 87%。Gunter 2016（9 人，[C]）：只有 5 人能獨立完成，**拍傷口照片是最困難的步驟**，年長、肥胖、部位難拍者最吃力。Vodrahalli JAMA Dermatol 2023 TrueImage 2.0（98 人單臂，[C]）：即時品質回饋加重拍，照片品質不佳的病人數減少 68.0%。Zhang JMIR mHealth 2021（21 人收案、15 人分析，[C]，作者有專利 COI）：色卡偵測率有回饋 0.96、無回饋 0.86。BAD 病人衛教（[A]，2025-04）：素色背景、光線均勻、先全景再 1–2 張近拍、可請信任的人代拍、"Don't add any filters or edits"。ISIC Delphi 33 項建議（[A/C]，只讀摘要）。靜脈炎或 IV 部位自拍研究：**未找到可靠證據**。
- **路線比較**（本報告推論，L741–759）：A（rich menu + quick reply 拍照／相簿）：照片經 LINE 暫存；「不上第三方雲端」⚠ 嚴格解讀不符、寬鬆解讀須揭露；開發量低；只能事後重拍；metadata 需多輪 postback；長者最熟悉；相機風險低。B（rich menu + LIFF 上傳頁）：瀏覽器直傳；較符合原則，前提是 TLS 在本機終止；開發量中；可放範例圖、預覽、即時品質檢查；一張表單收齊 metadata；多一層網頁；相機風險中、須實機測試。**現在：A 有條件適用**（IRB 允許並揭露）；IRB 不允許時改用簡化版 B（一張範例圖、`<input type=file accept="image/*">`、2–3 個必填欄位）。**未來（約 1,000 張）：B 適用。** 認證 MINI App：兩階段都不建議。
- **實作**（本報告推論，L763–802）：預設選單（同意前）放研究說明、開始同意、隱私說明、聯絡窗口，**不放上傳按鈕**；同意後以 Link rich menu to user 切到同意後選單（上傳照片、拍照說明、我的上傳紀錄、撤回同意）；撤回時 unlink。`richmenuswitch` 只用於同階段分頁，**不能當作同意門檻**，rich menu 只是介面、不是存取控制，**伺服器每次收到照片都要重查同意狀態**。上傳流程：點「上傳照片」→ bot 回 3 個拍照重點加【拍照】【從相簿選】【看範例】（≤4 鈕）→ 收到後回「已收到第 N 張」加【再拍一張】【完成】。Flex 結果卡標題寫「研究模型分類結果（非醫療診斷）」；全部 `wrap: true`、`scaling: true`、寬度用 flex；altText 等於第一行全文；**結果卡不放照片縮圖**，因為 Flex image 需要 HTTPS URL，LINE 用戶端會向我方取圖，等於把研究照片 URL 暴露給 LINE 平台。LIFF：SDK ≥2.31.1（建議 2.31.2）；LINE Login channel 必須與 Messaging API channel **在同一個 provider**；`<input type="file" accept="image/*">` 加 `capture="environment"` 的「直接拍照」按鈕，不把 getUserMedia 自製取景框當唯一路徑；上傳附 ID token，伺服器 `POST /oauth2/v2.1/verify`，比對 `aud`、`exp`、`sub`。拍照引導：3–4 個配圖要點，附好例子與壞例子；全景加 IV 近拍，距離約一個手掌寬；建議家人代拍；關濾鏡與美顏、不開閃光燈、手臂放素色毛巾上。PC 版提示「請用手機 LINE 操作」。
- **驗證**（L804–816）：3–5 位長者或照顧者前測（參考 Macefield 2023 的認知訪談、Gunter 2016 的 ISO 9241-11），指標是獨立完成率與可標註照片比例；實機矩陣（iOS 多版本、Android 多品牌、LINE 13.6.0+ 與 13.16.0+、最大字級、Flex、quick reply、LIFF file input 與 capture）；統計「品質檢查不合格後重拍成功的比例」。

#### A5. 同意、撤回、follow／unfollow／封鎖（第 5 節，L829–976）
- **法條更正**（[A]，L833–839）：「得隨時撤回同意之權利及撤回之方式」規定在**《人體研究法》第 14 條第 1 項第 6 款**，**第 19 條沒有提到撤回**。第 19 條三項：(1) 研究結束或保存期限屆至，研究材料應即銷毀，但經當事人同意或已去連結者除外；(2) 未去連結材料超出原同意範圍使用，須重新審查並取得同意；(3) 未去連結材料提供到境外，須書面同意、審查會通過並經主管機關核准（[全文](https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=L0020176)、[第 19 條](https://law.moj.gov.tw/LawClass/LawSingle.aspx?pcode=L0020176&flno=19)，最新修正 108-01-02，查閱 2026-10-31）。
- **設計建議**（L841–847）：分層同意（第一層 Flex 摘要卡，第二層完整說明加 2–3 題是非題）；append-only 紀錄，記錄文件版本、內容 SHA-256、UTC 伺服器時間並串成雜湊鏈；撤回後立即停止使用，刪除照片與可連結資料；在模型登錄表上標記受影響模型，**等下一次人工排程訓練時再排除**；**封鎖（unfollow）不自動視為撤回**，但要暫停收集並提供 LINE 以外的撤回管道。
- **eConsent 證據**（L851–869）：Cohen JMIR 2023（[B] 系統性回顧）：37 篇出版物、35 項研究、13,281 人；10 項高效度研究中 6 項發現至少部分概念的理解顯著較佳；滿意度較高或相當；完成時間較長；作者含 AstraZeneca 員工（COI）。FDA／OHRP "Use of Electronic Informed Consent… Q&A" 2016-12 定稿，本輪沒有找到新版（[A]），身分驗證細節來自 RAPS（[E]）。台灣：衛福部層級「人體研究電子同意指引」**未找到**；臺大醫院〈網路研究倫理審查指引〉（2020-09）允許以「我同意」點選鍵代替簽名，並要求告知傳輸可能被第三方截取的風險，「網路研究自評表」要求留存附時間戳記的同意紀錄（[A-機構]，經搜尋摘要確認）；《人體研究法》第 12 條第 2 項：同意的方式與內容須經審查會核准，也就是電子同意形式本身要經 IRB 核准（[A]）。
- **LINE 帳號事件**（[A]，L871–880）：follow 在「加好友或解除封鎖」時發送，可以回覆；unfollow 在封鎖時發送，官方只標示 follow 可以回覆（RECV）。`follow.isUnblocked` 可區分新加入與解除封鎖（[SDK PR #597](https://github.com/line/line-bot-sdk-python/pull/597)，[E]／官方 SDK），導入日期**未找到可靠證據**。對封鎖者的推送不會送達、不計則數（[Send messages](https://developers.line.biz/en/docs/messaging-api/sending-messages)、[Pricing](https://developers.line.biz/en/docs/messaging-api/pricing/)）。
- **已訓練模型與撤回**（L882–887）：FTC Everalbum（2021）要求刪除**未經明示同意取得**的資料與用它開發的模型（[E] 二手）；EDPB Opinion 28/2024（2024-12-17）認為 AI 模型不當然匿名，對**違法處理**資料開發的模型監理機關可要求銷毀（[E] 二手）；machine unlearning 綜述 Xu et al. ACM CSUR 2023（[B]）；「合法同意期間訓練、之後撤回」要求立即重訓的監理意見：**未找到可靠證據**。
- **LINE 健康資料條款**（L889–893）：User Data Policy 頁回 403 未能讀取；LINE 隱私權政策提到被指定為可能含特別敏感資訊的官方帳號，內容不會用於機器學習（[LINE privacy](https://terms.line.me/line_communication_privacy?lang=en)，[A]，經搜尋摘要）；LINE 是否禁止 OA 收集健康資料：**未找到可靠證據**，需人工查閱。
- **限制**（L895–901）：webhook 只能證明「某 provider 範圍內的 userId 在某時點按了某個 postback」，**不能證明真實身分、年齡或是否本人**（推論，依 [Get user IDs](https://developers.line.biz/en/docs/messaging-api/getting-user-ids/)）；聊天機器人內 eConsent 或 quiz 的效果：**未找到可靠證據**；台灣研究同意紀錄的最低保存年限：**未找到可靠證據**；雜湊鏈沒有法院或 IRB 採認案例，要防整串重算須外部錨定；FTC、EDPB 原文沒有直接讀取。
- **適用性**（L903–909）：現在 14 位個案中撤回 1 人約佔 7%，照片可能佔 5–15%，影響大；撤回時應**立即凍結受影響模型**（標記「不得再部署或匯出」），下次人工訓練時排除，不自動重訓。把封鎖誤判為撤回，誤刪一人就損失約 7%。未來撤回一人通常不到 1–2%，可依排程處理（例如每季人工重訓一次）。SISA 分片訓練（Bourtoule et al., IEEE S&P 2021，**本輪未驗證引用細節**）對小專案效益有限。
- **實作**（本報告推論，L913–961）：`consent_documents`（不可變；`doc_id`、`version`、`lang`、`irb_approval_no`、`effective_from_utc`、`content_canonical`（NFC、統一換行、去尾端空白）、`sha256`、`quiz_json`、`flex_json_sha256`、`liff_bundle_sha256`）。`consent_events`（append-only，用 SQLite trigger 拒絕 UPDATE 與 DELETE；`event_id`、`seq`、`subject_pid`、`event_type`、`doc_id`、`doc_sha256`、`channel`、`server_received_utc`、`line_event_timestamp_ms`、`webhook_event_id`、`id_token_verified`、`enrollment_code_hash`、`prev_hash`、`row_hash`；event_type 為 presented、quiz_answered、consented、declined、withdrawn、reconsented、unfollow_observed、follow_observed、data_purged、unsend_purged；`row_hash = SHA256(prev_hash ‖ canonical_json(row))`）。每天把最新 `row_hash` 匯出到離線媒體或寫進 IRB 紀錄，作為外部錨定。分層同意 5 步：Flex 摘要 4–6 點 → 「閱讀完整說明」開自有 HTTPS 網頁或 LIFF → 2–3 題是非題（例：「本服務會告訴我是否得了靜脈炎？（否）」），答錯就說明再答，**不以分數排除** → 自我聲明（年滿 18 歲或依 IRB、本人或法定代理人）→ 「我同意」postback 的 `data` 帶 `consent_version` 與 `doc_sha256` 前綴。未成年與代理同意不開放 LINE 自助，改走面對面流程（須經 IRB 核可）。撤回 6 步（全程不自動訓練）：(1) 寫 `withdrawn`、回確認、unlink rich menu、把 `subject_pid` 與照片 hash 加入 `exclusion_list`；(2) 背景刪除工作（不是訓練工作）在 N 小時內刪照片、縮圖、EXIF、可連結的標註列、`line_link` 列、尚未進訓練快照的照片，寫入 `data_purged` 並附被刪檔案的 SHA-256 清單；(3) 快照 manifest 以 exclusion list 過濾，舊快照標 `contains_withdrawn=true`；(4) `model_registry` 標 `contains_withdrawn_subjects` 與 `flagged_at`，被標記模型不得新部署，現役模型是否下線由人員決定；(5) 下次人工訓練用乾淨快照，人員簽核後才替換；(6) 備份（04_備份）中的照片依保留期限輪替清除或另行標記。可保留（須事先寫入同意書並經 IRB 核准）：只連假名 ID 的同意與撤回事件、已發表的彙總統計。報告**不主張照片可以「去連結」後保留**，因為身體影像、刺青、痣難以達到第 4 條第 3 款「永久不能以任何方式連結、比對」的標準。事件處理：unfollow → `unfollow_observed`、狀態 `paused`（停止推播與收件）、不刪資料；follow 且 `isUnblocked=true` → 回「歡迎回來，您的研究同意狀態為：…」，版本更新時要求重新同意；unsend → 刪除該照片。同意書須寫明「封鎖不等於撤回」，並提供電話或 email 撤回管道；IRB 偏保守時可設「封鎖 X 天未解除即視為撤回」，但須事先寫入同意書。改版：舊版同意者不自動沿用；重大變更要重新同意，重新同意前上傳的照片不得進研究集。
- **驗證**（L963–967）：稽核演練（重建看了哪一版、何時同意、何時撤回，驗雜湊鏈與外部錨定）；撤回演練（同意 → 上傳 3 張 → 撤回，驗照片已刪、`line_link` 已刪、exclusion list 已更新、快照與模型已標記、撤回後上傳被拒收）；封鎖演練。

#### A6. 身分、各 provider 的 userId、化名化（第 6 節，L980–1060）
- **結論**（L982–991）：userId 格式 `U[0-9a-f]{32}`，**以 provider 為範圍發放**：同一 provider 下各 channel 相同，換 provider 就不同，所以它是長期穩定的間接識別碼，**不應當研究個案代碼，也不應寫進匯出資料集**。建議：隨機 `study_id` 當主鍵；userId 只存在受存取控制的連結表，查找用 keyed HMAC；醫院病人用研究人員當面發的**一次性登錄碼**綁定，不用 Account Link 或病人登入頁；LINE Login 只用 `openid`、不申請 email。
- **證據**（[A]，L993–1018）：原文 "User IDs are issued different values for each provider, even for the same user"、"the user ID is the same regardless of the channel type"；userId 不同於顯示名稱與可搜尋的 LINE ID；使用者未同意存取 profile 時 webhook 不帶 user ID；Get follower IDs 只限認證或 premium 帳號（[Get user IDs](https://developers.line.biz/en/docs/messaging-api/getting-user-ids/)）。只有請求 `openid` 才回 ID token（[LINE Login v2.1 reference](https://developers.line.biz/en/reference/line-login/)）；email 要另外在 Console 申請，即使已授權，驗證回應的 scope 也不會列出 email（[Integrate LINE Login](https://developers.line.biz/en/docs/line-login/integrate-line-login/index.html.md)）。Account Link：link token 單次使用、10 分鐘有效；nonce 10–255 字元，建議至少 128 bits 安全亂數；官方警告攻擊者可能 "send a URL to a user to link the attacker's LINE account"；必須讓使用者「at all times」都能解除連結（[Linking user accounts](https://developers.line.biz/en/docs/messaging-api/linking-accounts/)）。台灣去識別化：以 CNS 29100 與 CNS 29191 為驗證依據（[行政院](https://www.ey.gov.tw/Page/9277F759E41CCD91/af28eb4c-7030-49bb-889d-f0a0fed6a4d5)，[A]），CNS 29191 公布年份各來源不一；國發會 108 年函釋：**通過驗證不當然排除個資法適用**（[臺北市法規函釋](https://laws.gov.taipei/Law/Interpretation/Content/FE372646)，[A]）；《人體研究法》第 4 條第 3 款「去連結」為「永久不能以任何方式連結、比對」。
- **限制**（L1020–1024）：userId 何時改變（例如刪除後重建帳號）：**未找到可靠證據**，本報告推論重建後會得到新 userId；個資法現行條文沒有「假名化」一詞，也沒有找到法定定義；登錄碼也可能被轉給他人。
- **適用性與實作**（本報告推論，L1026–1045）：義大醫院 14 位病人的個案碼先轉成 `study_id`，以前綴區分來源（`H-` 醫院、`P-` 一般民眾）；小樣本下 `study_id` 加收案日期、醫院、部位就可能被院內人員再識別，所以匯出時把日期粗化到週或月並移除 EXIF。`study_id` 格式為 `S-` 加 8 位 base32 隨機字元。`user_pid = HMAC-SHA256(pepper, userId)`，pepper 存 Windows Credential Manager，不進 git、不和 DB 同一備份位置；log 與分析只用 `user_pid` 前 16 個十六進位字元。`line_link` 放在獨立 SQLite 檔，以 NTFS ACL 限 bot 服務帳號讀取，用 SQLCipher 或應用層 AES-GCM 加密；撤回時刪除這一列。登錄碼：伺服器產生、熵 ≥40 bits（例如 8 碼 Crockford base32），DB 只存 SHA-256；有效 24–72 小時、單次使用、錯 5 次鎖定；綁定成功回「已加入研究，研究編號末兩碼 xx」並寫 `enrolled_via_code`；碼對應 `study_id`、**不對應病歷號**；`study_id ↔ 義大個案碼` 對照表由院內研究人員保管，不進 bot 伺服器。LIFF 或 LINE Login channel 必須和 Messaging API channel 在同一 provider，否則 ID token 的 `sub` 對不上 webhook 的 userId。
- **驗證**（L1047–1051）：匯出資料集掃描不應有 `U[0-9a-f]{32}`，也不應有 GPS；登錄碼的重放、逾期、5 次鎖定、重用測試；LIFF `sub` 與 webhook userId 經 HMAC 後應相同。

#### A7. 資安：token、對外暴露、隔離、速率限制、log 遮罩（第 7 節，L1063–1238）
- **結論**（L1065–1071）：token 用 **v2.1**（自訂效期，最長 30 天），或 **stateless**（15 分鐘）並以 JWT assertion 換發，兩者都靠 RSA assertion signing key。不建議 long-lived（沒有期限），也不建議 stateless 的 `client_id + client_secret` 版（等於把 channel secret 變成「可以換 token 的密碼」）。RSA 私鑰與 channel secret 放 Windows Credential Manager 或 DPAPI 加密檔，不進 repo。對外暴露：首選 **Tailscale Funnel**（TLS 在本機終止、不開入站埠）；次選自架 Caddy 或 nginx 加 Let's Encrypt 與固定 IP；只走聊天、不做上傳頁的話，Cloudflare Tunnel 也可接受。分三個行程：公開 webhook 服務、只綁本機的管理 API、推論 worker；log 遮罩所有 token、簽章、replyToken、完整 userId 與照片。
- **跨筆記衝突裁決：tunnel 業者看不看得到照片**（L1073–1080，原文要點）：路線 A 的 webhook 只帶 JSON（userId、訊息 ID、replyToken、使用者打的文字、時間戳），照片由後端主動向 `api-data.line.me` 下載，從 PC 直接出去、不經 tunnel，所以 tunnel 業者看得到 webhook JSON、看不到照片，但 webhook JSON 本身仍是個資。路線 B 的照片一定經過 tunnel，Cloudflare 與 ngrok 在 edge 終止 TLS、看得到明文 ⚠。本報告推論補充：如果 PC 裝了全系統出站代理或 VPN，主動下載照片的連線也可能經過第三方，筆記沒有涵蓋，部署時要自行確認。
- **四種 token**（[A]，[Channel access token](https://developers.line.biz/en/docs/basics/channel-access-token/)，頁面未標更新日；[LINE Tips 2026-07-23](https://developers.line.biz/en/tips/2026/07/23/using-multiple-api-tools/)；查閱 2026-10-31，L1084–1099）：v2.1（JWT）最長 30 天、每 channel 30 個、超過時 API 回錯誤、可用 `POST /oauth2/v2.1/revoke` 撤銷；Stateless 15 分鐘、不限數量、**不可撤銷**；Short-lived 30 天、30 個、超過時最舊的失效、可用 `POST /v2/oauth/revoke` 撤銷；Long-lived 無期限、1 個、重發時舊的失效（可讓舊 token 最多延長 24 小時）、可撤銷。官方建議：v2.1 與 short-lived 在有效期內重複使用、到期前自動重發；疑似外洩立即撤銷；每個開發團隊最多發 2 個 token 以便不中斷輪替。「Build a bot」頁建議改用使用者自訂效期的 token；使用 long-lived 時可在 Security 分頁以 IP 或 CIDR 限制 API 呼叫來源（[Build a bot](https://developers.line.biz/en/docs/messaging-api/building-bot/)）。**沒有讀到棄用公告**；long-lived 與 short-lived 是否棄用、stateless 推出日期：**未找到可靠證據**。
- **v2.1 JWT 規格**（[A]，L1101–1107）：RSA 2048、RS256，在 Console 註冊公鑰後取得 `kid`；`iss` 與 `sub` 都是 channel ID，`aud` 是 `https://api.line.me/`；assertion 最長 30 分鐘，換到的 token 最長 30 天（`token_exp`）（[Issue v2.1](https://developers.line.biz/en/docs/messaging-api/generate-json-web-token/)）。[line-openapi channel-access-token.yml](https://raw.githubusercontent.com/line/line-openapi/main/channel-access-token.yml)（[A]）：stateless 端點 `POST /oauth2/v3/token` 接受 `client_id + client_secret`，**所以 channel secret 外洩的影響不只是 webhook 可以被偽造**。
- **Webhook TLS**（[A]，L1109–1116）：必須 HTTPS，支援 TLS 1.2 與 1.3，**不支援 TLS 1.1 以下**；公開 CA 憑證（Let's Encrypt 可、self-signed 不可）、憑證鏈完整；已棄用 cipher suite「可能在近期無預警停用」；一個 channel 只能設一個 webhook URL（[SSL/TLS spec](https://developers.line.biz/en/docs/messaging-api/ssl-tls-spec-of-the-webhook-source/)、Build a bot）。
- **對外暴露方式**（L1118–1126）：Cloudflare Tunnel 由本機 `cloudflared` 建立只出不進的連線（[Connect networks](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)，[A]，文件日期 2026-08-04）；「Cloudflare 在 edge 終止 TLS、看得到明文」只有 [E]（[Nextcloud 論壇](https://help.nextcloud.com/t/is-cloudflare-tunnel-safe-privacy-focused/150268)、[Pangolin](https://pangolin.net/news/building-a-peer-to-edge-peer-reverse-proxy)），**本輪沒有找到 Cloudflare 官方明文**。ngrok Traffic Inspector 可記錄 HTTP 請求並提供 "full capture mode and replay"，保存期限 Free 24 小時、Hobbyist 與 Pay-as-you-go 72 小時、加購後最長 90 天（[ngrok](https://ngrok.com/docs/obs/traffic-inspection/)，[A]）；full capture 是否預設開啟：**未找到可靠證據**。Tailscale Funnel（[A]，last validated 2026-01-20）：仍是 beta、所有方案可用；**TLS 在使用者自己的裝置上終止**，relay「無法解密」；只能用 443、8443、10000 埠，網域固定 `*.ts.net`；頻寬上限不可調、官方沒有公布數字。
- **Log 與影像**（[A]，L1128–1132）：OWASP 列出不得直接寫入 log 的資料（access token、密碼、加密金鑰、DB 連線字串、敏感個資），並建議 JSON 結構化以防 CR/LF 注入（[OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)）。重送事件帶**相同的 replyToken**，所以 log 中的 replyToken 在有效期內可被重用。Pillow 13.0.0：超過 `MAX_IMAGE_PIXELS` 警告、超過兩倍拋錯，`formats=` 可限制格式；預設約 89,478,485 **本輪沒有驗證**。
- **限制**（L1134–1141）：無法用 IP 白名單擋 webhook；簽章不含時間戳或 nonce、**不防重放**，要靠 `webhookEventId` 去重；secret 重發後是否立即失效：**未找到可靠證據**；Funnel 仍是 beta、有頻寬上限、ts.net 網域可能降低信任；Windows 服務帳號、NTFS ACL、BitLocker（Home 版只有「裝置加密」）、keyring 與 DPAPI 的一手文件沒有抓取，屬**業界慣例**；OWASP API Security Top 10 2023 原文沒有抓取，類別名稱來自既有知識。
- **適用性**（L1143–1156）：現在不論哪條路徑，短效 token、log 遮罩、三行程都應該做。只走聊天：Funnel、自架反代或 Cloudflare Tunnel（須接受 Cloudflare 看得到 webhook JSON 並寫進資料流說明）；有 LIFF 上傳頁：**只能用 Funnel 或自架反代** ⚠。**ngrok 不建議**：Inspector 在雲端保存請求內容，包括 replyToken ⚠。未來可用小型 VPS 做 TCP passthrough 加 WireGuard 回本機，TLS 仍在本機終止（本報告推論）。
- **實作**（本報告推論，L1160–1219）：架構為 `Internet → (Tailscale Funnel / Caddy / cloudflared) → 127.0.0.1:8001 webhook-svc`（只允許 `POST /webhook/<隨機字串>`、其他回 404、body ~1 MB 上限回 413、先驗 HMAC 再寫 SQLite 再回 200）；`127.0.0.1:8000 admin-api + React`（不經任何 tunnel、防火牆封入站）；worker 出站到 api.line.me 與 api-data.line.me（httpx `follow_redirects=False`、網域 allowlist）。webhook-svc 與 admin 必須是**兩個不同的 FastAPI app**，webhook-svc 關閉 `/docs`、`/redoc`、`/openapi.json`；三個行程用非管理員帳號，經 NSSM、WinSW 或工作排程器啟動；`New-NetFirewallRule` 封 8000 與 8001 入站；`icacls` 限縮 DB、照片、秘密檔；BitLocker 或裝置加密，外接備份碟也加密（業界慣例）。Token 生命週期：產生 RSA 2048 並註冊公鑰；啟動時用 JWT 換例如 7 天的 v2.1 token，到期前重發並撤銷舊 token；signing key 每 6–12 個月輪替（本報告推論值）；LINE 是否允許同時註冊多把公鑰，本輪沒有驗證。外洩 runbook 7 步：撤銷所有 token → 重發 channel secret → 輪替 RSA 金鑰 → 更新本機秘密並重啟 → Console Verify 加 `POST /v2/bot/channel/webhook/test` → 檢查 log 有無異常推播 → 通報 IRB 與計畫主持人。Log 遮罩：`logging.Filter` 以 regex 遮罩 `Bearer\s+\S+`、`"replyToken"\s*:\s*"[^"]+"`、`x-line-signature`、`U[0-9a-f]{32}`、JWT 三段格式；uvicorn `--no-access-log`，改用自己的 middleware，只記方法、路徑、狀態碼、耗時、body 長度、驗簽結果、事件數、`user_pid`；httpx 與 requests logger 設 WARNING；全域 exception handler 不附 request 物件；**不使用雲端 APM 或錯誤追蹤（例如 Sentry）⚠**，只寫本機 `RotatingFileHandler`。重放防護：`webhookEventId` UNIQUE、保留 7–30 天；`timestamp` 與現在差超過 1 小時且 `isRedelivery=false` 時記為可疑並不處理，重送事件放寬到 24 小時（本報告建議值，LINE 沒有公布重送時間窗）。速率限制：per-userId 在驗簽後、於 worker 端計算，例如每天最多 10 張，超過只回一則說明、不下載也不推論；per-IP 只放在 tunnel 或反代層，擋驗簽前的洪水。相依套件：hash 鎖版（requirements hash 或 `uv.lock`）、定期 `pip-audit`、追蹤 line-bot-sdk、Pillow、FastAPI、uvicorn、cloudflared、tailscale、Caddy 的公告。**OneDrive ⚠**：專案位於 `C:\Users\user\Desktop\…`，若 OneDrive「桌面備份」已開啟，照片與 DB 會被同步到雲端，**請實際檢查**；建議放在不受同步的路徑，例如 `C:\PhlebitisData\`。
- **驗證**（L1221–1228）：外部掃描只應看到 443，`/docs` 與管理路徑回 404；TLS 只允許 1.2 與 1.3；一週 log grep `U[0-9a-f]{32}`、`Bearer`、`replyToken` 應為 0；以偽造簽章打本機端點（**不要對 LINE 做壓力測試，官方禁止**，[GUIDE](https://developers.line.biz/en/docs/messaging-api/development-guidelines/)）；decompression bomb 應被拒絕；實際走一次外洩 runbook。

#### A8. 可靠性與營運（第 8 節，L1242–1396）
- **結論**（L1244–1252）：沒開重送時，停機期間的 webhook 不會補送；開了也只在「一段時間」內重送且不保證；文字訊息只能透過 webhook 取得，照片會被刪除；停機後通知使用者只能用 push（計費）。所以要服務化並自動重啟、開啟重送與錯誤統計、用 SQLite 佇列加重試加 dead-letter。LINE 統計粒度粗、有延遲、有隱私門檻（Insight 每小時 60 次、約 1 天後才有資料、人數 <20 回 null），研究指標（收件數、同意率、品質不足比例、預測分布、撤回次數）**一律由本機自建計算**，LINE 數字只用於對帳與觀察好友數、封鎖趨勢。
- **Rate limit**（每 channel、每 endpoint 分別計算，[A]，L1256–1268）：narrowcast、broadcast、各類統計與 insight、test webhook 60 次／小時；audience 60 次／分鐘；Set／Get webhook endpoint 1,000 次／分鐘；multicast 200 次／秒；loading animation 100 次／秒；發行 short-lived token 370 次／秒；其他端點 2,000 次／秒；超過回 `429 Too Many Requests`。
- **狀態碼**（[A]，L1270–1281）：400 請求錯誤；401 token 無效；403 沒有權限；404 例如使用者不存在、未同意、不是好友或已封鎖；409 retry key 已被接受；413 請求超過 2 MB；429 超過 rate、併發或訊息額度；500 伺服器錯誤。
- **LINE 不提供 log**（[A]，L1283）：開發者要自行記錄 API 請求的 `x-line-request-id`、時間、方法、endpoint、狀態碼，以及收到 webhook 的來源 IP、時間、路徑和自己回的狀態碼（GUIDE）。
- **錯誤統計與通知**（[A]，L1285–1288）：Error statistics aggregation 要手動開啟、**不回溯**、時區 UTC+9、可下載 TSV；錯誤分為 `could_not_connect`、`request_timeout`、`error_status_code`、`unclassified`；「Errors」欄是 60 秒內同一狀態碼的次數（ERRSTAT）。錯誤通知 email 只開放給「已提交申請的法人用戶」，同一狀態碼 5 分鐘內合併成一封，重送停止時也寄信（[ERRNOTI](https://developers.line.biz/en/docs/partner-docs/error-notification/)）；改為重送停止也寄信的確切日期：**未找到可靠證據**（01 號筆記 L116 記為「2023 年某日」）。
- **發送數、Insight、狀態頁**（[A]，L1290–1305）：`GET /v2/bot/message/delivery/reply?date=yyyyMMdd`，原文 "Normally, the counting process is completed within the next day"；consumption 是近似值。Insight：followers 約 1 天延遲、每小時 60 次；人口統計約 3 天延遲，可觸及目標人數須 ≥20，帳號須在日本、泰國或**台灣**建立；互動統計少於 20 時回 null、資料只更新 14 天。狀態頁 [LINE API Status](https://api.line-status.info/) 涵蓋 Messaging API、LINE Developers、LIFF、LINE Login，不涵蓋 LINE App 本身，可用 RSS 或 ATOM 訂閱；事故先在狀態頁發布，細節確認後才發 news（[說明](https://developers.line.biz/en/docs/basics/line-api-status/)，來自搜尋摘要與頁面標題，**建議逐字確認**）。
- **限制**（L1307–1312）：重送次數與期間、平台暫停 webhook 的條件與恢復方式、錯誤統計的保存期限與延遲、狀態頁的歷史事故頻率與 SLA：**未找到可靠證據**；429 的 `Retry-After`：**未找到可靠證據**；reply 不支援 retry key，無法安全重試；單機 webhook 可用性的實證研究沒有檢索，監控設計屬業界慣例與本報告推論。
- **失敗處理矩陣**（本報告推論與業界慣例，L1324–1337）：Get content 202 或 5xx → 指數退避 3 次，仍失敗就標 dead、告警、以 reply 請使用者重傳；410 → 刪資料、不回覆；reply 400 "Invalid reply token" → 依研究政策，額度內允許時帶 `X-Line-Retry-Key`（= job UUID）發 push，否則只記「未回覆」，等使用者點「我的最近結果」時以 reply 補上；push 500 或逾時 → 同一 retry key 在 24 小時內重試；push 409 → 視為已送出；push 429（額度）→ 不重試、改走 postback；push 429（rate）→ 指數退避；401 → 立即換發 token 並告警；403 → 告警；LINE 平台事故 → 比對 RSS，區分我方故障或平台故障。
- **停機後**（L1339–1343）：收到重送事件而 token 已失效時，只對「已同意研究、且有未完成照片」的使用者補發 push，每人最多一則，文案「系統先前中斷，請重新上傳」；預防做法是在圖文選單與自動回覆中說明「研究服務可能中斷，不是緊急醫療管道」。
- **告警與健康檢查**（L1345–1359）：最舊 queued job >45 秒；驗簽失敗突增；"Invalid reply token" 比例升高；worker 心跳 >60 秒；磁碟低於門檻；連續 N 次 5xx 或 429；GPU 不可用（`torch.cuda.is_available()` 為 false）。告警走 email 或 Windows 通知，**不要用研究帳號的 LINE push**（計費、會和受測者混在一起），一定要用 LINE 就另開 channel；告警內容不得含照片或 userId。`/healthz` 只綁本機，回報 DB 可寫、佇列深度、最舊 job 等待時間、GPU 狀態、worker 最後心跳。
- **統計分工**（L1361–1368）：研究 KPI 只用自建表、以 `webhook_event_id` 去重；每日排程一次抓前一日（UTC+9）的 reply／push 發送數與 followers，`unready` 隔天補抓；儀表板**不可每次刷新都呼叫 Insight**；對外報告比照 Insight 的 20 人門檻做 small cell suppression。
- **Windows 主機與原則**（L1370–1380）：開機自動啟動、crash 後自動重啟、Windows Update 維護時段、關閉休眠、UPS、tunnel 斷線自動重連。監控只發告警，**不觸發自動訓練或自動上線**，唯一例外是第 9 節的「自動回滾到上一個已核准模型」。
- **驗證**（L1384–1387）：停機 10 分鐘演練；mock 429 確認降級為 postback；連續 14 天對帳；從原始事件表重算 KPI，應與儀表板一致。

#### A9. 影子模式、金絲雀、A/B（第 9 節，L1400–1592）
- **結論**（L1402–1417）：**本專案不做面向使用者的 A/B 測試，也不做依流量比例的金絲雀。** 金絲雀等於讓部分真實民眾收到候選模型的判讀，屬「上線」，而且是準隨機分派；業界金絲雀通常依指標**自動擴大流量**，直接違反「不自動上線」⚠。替代階段：(1) 在凍結、以病人為單位切分的測試集做離線評估；(2) 影子模式（候選模型在背景跑、只記錄不回覆，目前已有）；(3) 審閱者端金絲雀（結果只給內部審閱者看、對模型身分盲化）；(4) 依預先寫好的門檻由負責人簽核切換。**自動化只允許往後退**：自動回滾到上一個 approved 模型，或自動降級為固定回覆「需人工確認」。以約 120 張、14 位個案的規模，**任何「候選模型較好」或「不劣」的統計結論都不成立**。
- **證據**（L1421–1434）：Kwong Front Digit Health 2022（[C]，單中心前瞻）：嬰兒阻塞性腎水腫模型 2020 年 8 月到 12 月 silent trial，資料漂移（年齡、患側、影像格式）使 AUC 從 0.90 掉到 0.50，修正後在兩個獨立資料集回到 0.85–0.91，過程發生在模型影響病人之前。Tikhomirov Nature Health 2026（[B]，只讀到二手摘要；「納入 75 篇」來自 [E]）：silent trial 做法高度不一致，**沒有正式指引**。DECIDE-AI：17 項 AI 特定項目加 10 項通用項目（Vasey Nat Med 2022，[A]）。GMLP 十項原則 2025 年由 IMDRF 定稿為 N88（[A]），最直接的是第 4、5、8、10 項（訓練與測試集獨立、參考標準、臨床相關條件下測試、部署後監測），定稿逐字用語沒有核對。PCCP 三部分：修改描述、修改協定、影響評估（[A]）；定稿日期**來源衝突**：律所報導 2024-12-03 或 12-04，FDA 頁目前顯示 "Issue date: August 2025"，報告寫成「2024 年 12 月定稿，FDA 頁面目前列為 2025 年 8 月版」。WHO 2021 年 AI 倫理治理指引、2024-01-18 LMM 指引（[A]）。A/B effect：16 項研究顯示民眾可接受全面實施卻反對 A/B 隨機分派（Meyer PNAS 2019，[B]）；Data Colada 重新分析認為在其檢驗的 7 個情境中效應消失（[E]）。Facebook 情緒感染實驗以服務條款代替知情同意，PNAS 主編發布 Expression of Concern（[C]）。《人體研究法》第 4 條定義人體研究包含「取得、調查、分析、運用……醫學等有關資訊之研究」，第 5 條要求先經倫理審查委員會審查通過，主管機關公告免審者除外（[A]）。
- **金絲雀業界做法**（L1436–1439）：原文 "a partial and time-limited deployment of a change in a service and its evaluation"；指標要少、以使用者可見的 SLI 為主、明顯變差時自動暫停或回滾；原文 "Deployments should be performed by computers, not humans"（Google SRE Workbook，業界慣例）。Breck ML Test Score 2017（[C]）：ML 系統需要可除錯性、回滾與監測。
- **樣本量**（L1441–1471）：Riley BMJ 2024（[B]）：盛行率 0.43、c 統計量 0.77、校準斜率 CI 寬度 0.3 需要 949 人（408 個事件）；經驗法則是事件與非事件各至少 100–200 個；沒有討論群集效應。McNemar 用 Connor 公式 N = [z_{α/2}√p_d + z_β√(p_d − δ²)]² / δ²（二手說明一致，Connor 1987 原文未取得）。**本報告計算（不是文獻數字）**：normal 9 張判對 8 → 0.889，CI 0.565–0.980，寬 0.415；14 位病人中 12 位正確 → 0.857，0.601–0.960，寬 0.359；stage 2 的 24 張判對 20 → 0.833，0.641–0.933，寬 0.292；120 張判對 108 → 0.900，0.833–0.942，寬 0.109；每類約 333 張判對 300 → 0.901，0.864–0.929，寬 0.064；1,000 張判對 900 → 0.900，0.880–0.917，寬 0.037。McNemar（α=0.05、檢定力 80%）所需配對數：(p10, p01) = (0.10, 0.05) 約 469；(0.08, 0.03) 約 343；(0.06, 0.03) 約 783；(0.15, 0.05) 約 155。三法則：120 張嚴重錯誤（stage 2 判為 normal）為 0 時，真實錯誤率 95% 上界仍約 2.5%。三類 kappa（假設真實值約 0.80 模擬）：n=14 時 95% 區間 0.46–1.00，n=1,000 時 0.77–0.83。**以上都假設照片彼此獨立**；同一病人多張照片高度相關，有效樣本量更接近病人數，實際 CI 更寬。
- **部署失敗案例**（L1473–1479）：Epic 敗血症模型外部驗證 AUC 0.63（95% CI 0.62–0.64），開發者報告 0.76–0.83（Wong JAMA IM 2021，[B]，數字來自多個二手來源）；密西根敗血症警示因 COVID-19 族群改變，2020 年 4 月停用（Finlayson NEJM 2021，[C]）；Google 糖網系統在泰國 11 家診所遇到品質門檻與真實環境衝突（Beede CHI 2020，[C]），「超過五分之一影像被拒」只見於新聞、**沒有在原文核對**；皮膚癌 App 系統性回顧：照片由臨床人員拍，實際使用者表現可能更差（Freeman BMJ 2020，[B]）；症狀檢查器首位診斷正確率 34%（Semigran BMJ 2015，[B]）。PSI 門檻 <0.1 穩定、0.1–0.25 需檢查、>0.25 重大變化，屬啟發式（[E]）。
- **限制**（L1485–1491）：影子模式沒有即時參考標準，**兩模型一致不代表兩個都對**；GMLP 與 PCCP 是醫材監理框架，本專案目前不是醫材上市申請，只能當最佳實務參考；台灣 TFDA 的 AI/ML 醫材變更管理指引本題沒有檢索；不劣界限 Δ 沒有文獻依據，須由臨床人員決定；「自動回滾是否可接受」沒有找到明確討論的監理文件。
- **適用性**（L1495–1516）：現在可以做工程驗證（能載入、延遲與記憶體可接受、輸出格式正確）、描述性比較（一致率、混淆矩陣、分歧清單，標為探索性）、分歧案例送人工盲審。**不能**宣稱候選模型較準或不劣；如果現在就換模型，理由只能是工程或治理需要，文件中須寫明「沒有統計證據支持效能較佳」。未來（約 1,000 張、每類約 333 張）每類敏感度 CI 寬約 ±3 個百分點；不一致比例約 15% 時可偵測約 5 個百分點的配對差異；前提是以病人為單位切分、至少 2 位獨立標註者並報告一致性、各來源子群樣本足夠、門檻事先註冊。**IRB**：影子模式本身就屬「分析個人醫學資訊」，可能需要 IRB 審查，至少要由 IRB 判定是否免審；同意書要揭露「照片可能由第二個研究模型在背景分析」。
- **實作**（本報告推論，L1520–1576）：模型登錄表以 SHA-256 為模型身分、登錄後不可覆寫；狀態 candidate、approved、active、retired、rejected、flagged_withdrawn；記錄來源、授權、訓練快照、評估報告路徑、核准者與日期；外部 safetensors 只能以 candidate 登錄，在專案資料上完整評估後才能晉升。設定檔的 `active_model_id` 與 `shadow_model_id` 指向登錄表 ID；啟動時驗雜湊，不符就拒絕載入並降級為「需人工確認」；只有 approved 可設為 active，由程式強制。熱備：上一個 approved 保持在記憶體或可在數秒內載入。自動回滾觸發（只限工程 guardrail）：推論錯誤率或逾時率超過門檻、模型檔雜湊不符、輸出不合法、短時間內超過 X% 的照片判成同一類；觸發後通知負責人並由人工確認是否維持。稽核：每次回覆記錄 `model_id`、雜湊、分數（只存研究 DB、不顯示給民眾）；每次切換或回滾記錄操作者（自動回滾記為 system 加原因）；append-only。影子轉上線門檻（每項須人工簽核）：(1) 離線評估附 95% CI；(2) 累積達預設配對數並涵蓋足夠時間；(3) 分歧案例完成盲化標註；(4) 準確率差的 95% CI 下界 > −Δ，且 stage 2 敏感度不低於現行模型；(5) 各子群沒有明顯退化，「需人工確認」比例的變化有合理解釋；(6) 負責人簽核後進入加強監測期。每週監測：預測類別分布（PSI 或卡方，附原始計數）、分數分布（KS，只看相對變化）、輸入特徵（亮度、解析度、檔案大小、來源）、需人工確認比例、抽樣審閱結果（標示標註完成率）、影子與現行模型的分歧率。已發出錯誤結果：是否以 push 重新聯絡由人工決定，使用事先審定的模板、不提供新判讀、記錄發送清單，須事先寫進 IRB 計畫書。
- **風險**（L1584–1592）：把一致率誤當正確率；候選模型讓低信心比例大降，可能是過度自信（分數未校準）；醫院照片結果外推到 LINE 照片（Freeman 2020 的教訓）；⚠ 自動晉升 → 程式強制只有 approved 能設為 active；影子拖累主流程 → reply 後低優先執行。

#### A10. 回覆文案與轉介（第 10 節，L1595–1738）
- **結論**（L1597–1610）：**免責聲明擋不住過度依賴**。研究證據顯示通用免責聲明幾乎無法阻止過度相信 AI 健康建議；比較有效的是在**每一則結果訊息裡**直接寫出不確定性、具體下一步、紅旗症狀、何時要找人。**措辭不改變法規定位**：算不算醫療器材看預期用途與功能，本專案分析照片並輸出靜脈炎分期，**無法靠措辭變成「非醫材」**；措辭只能減少誤解、讓使用者該求助時求助；法規定位要由 IRB 處理，必要時諮詢 TFDA。文案原則：第一行寫行動；一則只講一件事；不給民眾看分數或期別；「正常」寫成「沒有看到明顯紅腫」並照樣附紅旗；分「住院中」與「已回家」；緊急寫「撥 119」、不寫 1922。
- **免責聲明證據**（L1614–1620）：Denecke & Gabarron Front Artif Intell 2026（[C]）：115 份問卷、15 個情境；有免責聲明時願意尋求第二意見約 50%–89%，沒有時約 41%–89%；作者形容 "modest and inconsistent"；受試者無法穩定辨認錯誤建議；建議改用標準化不確定性說明、提示第二意見、紅旗升級、針對症狀的警告；限制是探索性、量的是自評意圖。arXiv 2608.07493（[D]，n=52，僅搜尋摘要）：部分人把免責聲明解讀為「誠實」反而更信任。JMIR 2025;e66083（[C]，僅搜尋摘要）：告知「醫師使用 AI 協助診斷」會降低信任與求助意願。直接量測使用者是否讀懂免責聲明的研究：**未找到可靠證據**。
- **法規**（L1622–1625）：FDA 2026-01-06 修訂 CDS 指引，仍只處理給醫療專業人員用的軟體，沒有新增消費者端政策；第 1 項標準排除「擷取、處理或分析醫療影像」的軟體（Covington、Cooley，[E→轉述 A]，FDA 原文 PDF 沒有核對）。食藥署《醫用軟體分類分級參考指引》：綜合考量「產品功能、用途、使用方法與工作原理」，首先確認是否符合《醫療器材管理法》第 3 條定義（mdcpp 轉載副本，[A，第三方副本]，沒有從 fda.gov.tw 核對）。
- **健康識能**（L1627–1635）：AHRQ Toolkit 第 3 版 2024-03-01，23 項工具，含 teach-back（[A]）；CDC CCI 20 題、90 分以上通過，檢核單一主要訊息、主要訊息放最前、行動呼籲具體（[A]）；口語機率詞：33 篇研究、145 個詞彙，數值解讀差異極大（Andreadis JGIM 2021，[B]）；傳達不確定性只讓信任小幅下降，數字範圍幾乎不影響來源信任，口語不確定下降較多（van der Bles PNAS 2020，[B]，n=5,780，英國、教育程度偏高）；視覺輔助改善風險理解（Zipkin 2014，[B]）；台灣 20 歲以上 30.1% 健康識能不足或有限（國健署 2021，聯合新聞網轉述，[A 經新聞轉述]）；65 歲以上約 53.2% 識能不佳（國衛院論壇，僅搜尋摘要），兩者量表不同不能直接比較；聊天機器人介入效果「正向或混合」、研究品質偏低（Milne-Ives 2020、Singh 2023，[B]）。
- **就醫觸發**（L1637–1650）：Jackson VIP：1 分一項輕微徵象、持續觀察；2 分兩項徵象、**更換注射部位**；4 分可觸及靜脈索；5 分前述徵象加**發燒**（Solventum、ivteam，[A/業界]，各轉載版措辭不一）。NHS Lothian v2.0（2020-02，[A]，已讀全文）："please inform a nurse or doctor immediately"；拔針後感染 "most common within the 48 hours after removal"。East & North Herts：留置處紅腫或有分泌物「當天」看家醫（[A/業界]，僅搜尋摘要）。台灣衛教「勿自行冰敷、熱敷或按摩」（康健，[E]），和部分英國「冰敷、抬高」不同。1922 是疾管署傳染病諮詢與疫情通報專線（[A]），不適合；119 是緊急救護（[E]）；台灣是否有類似 NHS 111 的專線：**未找到可靠證據**。INS 第 9 版（2024）病人衛教需付費、未取得；CDC 2011 後的周邊導管更新：**未找到可靠證據**。
- **限制**（L1654–1657）：紅旗中的「紅線往上延伸」「寒顫」「胸痛、呼吸困難」依一般醫學常識推論，**沒有在 [A] 來源逐條核對，必須由臨床人員審定**；台灣醫學中心正式的周邊靜脈留置針衛教單：**未找到可直接引用的版本**，建議向合作醫院護理部索取。
- **實作**（本報告推論，L1669–1715）：四段結構（結論或行動／≤3 點原因或做法／紅旗或下一步／一行小字說明是研究）。避免的字：診斷、確診、判定為、治療、處方、用藥建議、保證、準確率 xx%、AI 醫師；改用「研究系統在照片中看到……的樣子」。不顯示未校準分數與期別，只存研究 DB 供人工檢視。分流：quick reply 問「你現在在醫院嗎？」；住院中 → 按鈴告訴護理師；已回家 → 當天聯絡打針的醫院，加「拔針後 2 天內每天看一下」。分層：第 0 層（任何結果）一律附紅旗；第 1 層（stage 1）「請告訴護理師看一下」；第 2 層（stage 2）「請現在就告訴護理師」；第 3 層（紅旗：發燒、紅線延伸、流膿、整隻手臂腫、止不住的出血、胸痛、呼吸困難、意識改變）住院中立即按鈴、在家立即就醫、危急撥 119。不提供冷敷、熱敷、按摩或用藥建議。teach-back quick reply：【我會告訴護理師】【我看不懂】【找真人】。每則用中文版 CCI 自評 ≥90，再找 5–8 位長者或照顧者做理解測試。
- **驗證與風險**（L1719–1738）：上線前 CCI 評分、長者用自己的話複述「接下來要做什麼」並計正確率；上線後追蹤「我看不懂」點擊率、紅旗回覆後點「我會告訴護理師」的比例、抽樣訪談。風險：「正常」讓人以為不用注意 → 一定附紅旗並說明照片看不出痛不痛、硬不硬；使用者等回覆而延誤就醫 → 每則寫「緊急時不要等我們」並註明不是 24 小時有人看；措辭被認定為診斷宣稱 → 法規顧問審閱用字清單。

#### A11. 無障礙與多語（第 11 節，L1742–1885）
- **結論**（L1744–1758）：LINE 是台灣最常用的通訊軟體，但 70 歲以上上網率只有 53.80%，流程必須允許**照顧者代傳**。Bot 端能控制的：關鍵訊息用純文字；Flex altText 能單獨看懂；`scaling: true`；按鈕 ≤3–4 個且以動詞開頭；每則約 120 字以內。多語：先用 profile `language` 預選，但第一則一定附手動切換按鈕；只翻譯**固定模板**，由專業譯者翻譯並回譯；台語提供**真人預錄語音**。**不可使用任何雲端翻譯、雲端 ASR 或雲端 TTS ⚠**；語音辨識只能用本機模型，而且第一階段不讓 ASR 自動判讀。
- **證據**（L1762–1809）：TWNIC 2025（[A]，電訪 n=2,142）：80.10% 以 LINE 為最常用通訊軟體，上網者中 90.26%；70 歲以上上網率 53.80%（2024 年 50.20%）；有上網需求但沒人協助者中 51.72% 想上網處理「醫療服務」；依年齡交叉的 LINE 使用率因 PDF 表格無法解析，**未取得**。Get profile 的 `language` 是 BCP 47，使用者未同意 LINE 隱私權政策時不出現（@line/bot-sdk 11.0.0 型別、[User consent](https://developers.line.biz/en/docs/messaging-api/user-consent/)，[A]）。Bot 可收音訊（`type: audio`），Get content 下載後同樣會被自動刪除（[A]）。LINE 字體分小、中、大、特大，只影響聊天室文字（T 客邦，[E]）。LINE 與 VoiceOver、TalkBack 的相容性：**未找到可靠證據**。WCAG 2.2 SC 2.5.8 觸控目標至少 24×24 CSS px（[A]）；Apple 44×44 pt、Material 48×48 dp（[E] 二手）；長者 App 設計系統性回顧 28 條指引，「簡化」與「加大控制項尺寸與間距」最重要（[B]，僅搜尋摘要）；長者偏好字級 ≥14 pt（OzCHI 2024，[C]，僅搜尋摘要）。本機台語 ASR：數位發展部 Taiwan Tongues ASR CE（開源，國語、台語、客語、英語，CTranslate2，[A/E]）；Breeze-ASR-26（約一萬小時**合成**台語語音微調，模型頁自稱華語版模型在台語錯誤率 30.71%–76.85%，自報、未獨立驗證，[E]）；MR Breeze ASR 25 主打台灣華語口音與中英混合、不是台語專用（[E]）；NUTN-KWS 台語 Whisper 微調（[E]）；長者自然口語與醫療用詞的獨立評測：**未找到可靠證據**。移工：2023 年（112 年）底社福移工約 23.4 萬人（勞動部，[A]，僅搜尋摘要）；2026 年 6 月底 231,175 人（Manstrong 引勞動力發展署，[E]）；口徑不同；依國籍細分的官方數字**未取得**，「印尼籍最多」未經官方細表核對。教育部台羅拼音方案 2024-08-26（113 年）修正（[A]）；「多數長者會講台語但不會讀台羅或漢字」：**沒有全國性數據**。機器翻譯：Google Translate 翻 100 份急診出院指示，西班牙文 92%、中文 81% 準確，不準確句中可能造成臨床顯著傷害的比例西文 2%、中文 8%（Khoong JAMA IM 2019，[C]）；7 種語言整體保留原意 82.5%，亞美尼亞文 55%（PubMed 33674922，[C]，依搜尋摘要）；印尼文與越南文醫療翻譯準確度：**未找到可靠證據**。
- **限制與適用性**（L1811–1821）：「約 120 字」「按鈕不超過 4 個」是推論；`language` 是手機語言設定、不等於閱讀偏好；台語 ASR 對長者準確度不明，可能導致錯誤分流。現在有條件適用：純文字、代傳、精簡按鈕可立即做；多語與台語語音等合作醫院確認語言需求後再做。未來照顧者（含移工）比例可能上升，優先翻譯印尼文、越南文、英文。
- **實作**（本報告推論，L1825–1870）：`language` 預選對照：zh-TW → 華語；id → 印尼文；vi → 越南文；en、fil、tl → 英文；沒有欄位 → 華語。第一則附【中文】【English】【Bahasa Indonesia】【Tiếng Việt】並記住選擇。代傳時回覆語言以傳訊者為準，但「告訴護理師」那段附一行華語，方便看護拿給護理師看。只翻約 10–15 則固定模板：專業譯者 → 另一位譯者回譯 → 雙語醫護或母語照顧者審查 → 至少 5 位目標使用者理解測試；同意書一定由專業譯者翻；**執行期間完全不做翻譯**，使用者自由輸入一律轉真人。台語：文字維持華語，由台語母語醫護錄 T5 與 T6 模板語音，以 Audio message 送出，不用雲端 TTS。語音訊息：回「我們收到您的語音，會請研究人員聽」並轉真人；ASR 只做研究評估、本機執行；語音和照片一樣立即下載、本機保存，並在同意書載明。Flex 按鈕高度 ≥48 dp 或 44 pt；不能只用顏色表達狀態。PC 版不顯示圖文選單、不支援 quick reply，要告知使用者。
- **驗證與風險**（L1872–1885）：手機系統字級調到最大後閱讀每則模板；只看 altText 時仍能理解；回譯比對；母語者評估台語語音。⚠ 雲端翻譯、ASR、TTS → 預譯模板、預錄語音、本機模型；自由輸入 → 轉真人；照顧者與病人身分混淆 → 同意流程區分「本人」與「代傳者」。

### Inferences
- 報告每一節都用同一套結構：結論、證據整理、反面證據與限制、適用性（現在／未來）、實作要點、驗證方法、風險與緩解。所有工程設計、工作量、文案、費用試算都屬**本報告推論**；只有 LINE 官方規則與法條屬 [A]。
- 第 1 節與第 8 節合起來，等於一份「LINE 平台不保證的事」清單：重送、時限、保存期、log、SLA 都不保證。報告的設計哲學是「研究端自建一切紀錄，LINE 只當傳輸與對帳來源」。

### Gaps
- 報告自己列出的「未找到可靠證據」請見 G 節與 J 節，本節不重複。

---

## B. 建議總表

### Takeaway
報告有兩張建議表：摘要的「最值得先做的 12 項」（依效益 ÷ 工作量排序，L97–110），以及「本段總表」27 列（L1893–1921）。工作量與最少資料需求都標為本報告推論的粗估（L95、L1891）。報告的時程用語是「現在／50 位個案後／200 位個案後（約 1,000 張）／不建議」，其中「200 位個案後」在 L1913 被括註為「約 1,000 張」，所以任務模板中的「約 1,000 張時」對應這一欄。

### Cited Findings

**B1. 摘要排序表（L97–110，原文欄位：排序、建議、證據等級、前置條件、工作量、效益）**

| 排序 | 建議 | 證據等級 | 前置條件 | 工作量（人日） | 效益 | 時程（報告是否給） |
|---|---|---|---|---|---|---|
| 1 | webhook 改為「驗簽 → `INSERT OR IGNORE`（以 `webhookEventId` 去重）→ 回 200 → SQLite job 佇列 → 單一 GPU worker」，並在 Console 開啟 webhook redelivery 與 Error statistics aggregation | [A] 官方要求與建議；佇列設計屬業界慣例 | 已有的驗簽程式碼 | 1–2 | 高 | 總表：現在 |
| 2 | reply 優先：收到照片就呼叫 loading animation，背景推論完成後用原 reply token 一次回覆；逾時就改回「結果處理中＋『查看結果』postback」，不預設用 push；**不要先回「請稍候」** | [A]（reply 免費、一分鐘、單次；postback 帶新 reply token） | 項目 1 | 0.5–1 | 高（費用 NT$0） | 總表：現在 |
| 3 | 收到 image 事件就立即 Get content，原樣保存 bytes 與 SHA-256，記錄 `contentProvider`、`imageSet`、來源與裝置 metadata；`external` 直接拒收；Pillow 以 `formats=` 限制格式並保留 bomb 防護；另存移除 GPS 並套用 `exif_transpose` 的工作副本 | [A]（自動刪除、410、shrinking）＋推論 | 項目 1 | 1 | 高 | 總表：現在 |
| 4 | 記錄遮罩：token、secret、`x-line-signature`、replyToken、完整 userId、照片 bytes、webhook 原始 body 都不寫 log；token 改用 v2.1 或 stateless（JWT 版）；秘密存 Windows Credential Manager | [A] OWASP、LINE；儲存方式屬業界慣例 | 無 | 1–2 | 高 | 總表：現在 |
| 5 | 文案改寫：第一行就是行動；每則結果都附紅旗清單；分「住院中」與「已回家」；「正常」寫成「沒有看到明顯紅腫」；不呈現分數或期別 | [C]／[B]／[A] 衛教單＋推論 | 臨床護理審定 | 2（不含審定） | 高 | 總表：現在 |
| 6 | 圖文選單依同意狀態做 per-user 切換；伺服器每次收到照片時再查一次同意狀態 | [A] | 同意紀錄表 | 1 | 中高 | 總表：現在 |
| 7 | 同意與撤回紀錄 append-only，記錄文件版本、SHA-256 與 UTC；撤回流程含 exclusion list、刪除工作、模型登錄表標記；**不自動重訓** | [A] 法條＋推論 | IRB 核定同意書 | 2–3 | 高 | 總表：現在 |
| 8 | 化名化：`study_id` 為主鍵；userId 只存獨立連結表或以 HMAC 處理；醫院病人用一次性登錄碼綁定 | [A] userId 以 provider 為範圍＋推論 | 項目 7 | 1–2 | 中高 | 總表：現在 |
| 9 | 對外暴露改用 Tailscale Funnel 或自架反向代理，只轉送 `/webhook`；管理介面只綁 127.0.0.1；確認照片目錄不在 OneDrive 同步範圍 | [A] Tailscale、LINE TLS 規格；Cloudflare edge 解密屬 [E] | 網域與憑證 | 1–2 | 中高 | 總表：現在 |
| 10 | 實測 LINE 傳圖矩陣：iOS 與 Android 各測標準、高畫質、原始畫質，記錄 Bot 實際收到的像素、QF 與 EXIF | 無公開實測（未找到可靠證據） | 測試帳號、無病人的測試照 | 1 | 中高 | 總表：現在 |
| 11 | 模型上線分階段：影子 → 只給審閱者看的金絲雀 → 人工簽核切換；只允許自動「回滾」到上一個已核准模型，或自動降級為「需人工確認」 | [C] silent trial；[A] GMLP／PCCP；推論 | 模型登錄表 | 2–3 | 中 | 總表：登錄表與回滾現在；效能型切換 200 位個案後 |
| 12 | LIFF 上傳頁（建議在未來約 1,000 張的階段做）：SDK ≥ v2.31.1；伺服器以 ID token 驗證身分 | [A] | IRB 決定照片路線 | 5–8 | 中（現在）、高（未來） | 總表：若 IRB 不允許照片經 LINE 則現在（簡化版），否則 50 位個案後（與本列括註「約 1,000 張」不一致，見 J 節） |

主要風險欄：摘要表沒有提供，請以 B2 為準。

**B2. 本段總表（L1893–1921，逐列照錄；「前置條件」欄採原表「最少資料需求」）**

| 方法或設計 | 證據等級 | 前置條件（最少資料需求） | 工作量（人日） | 預期效益 | 主要風險 | 時程 |
|---|---|---|---|---|---|---|
| 驗簽 → 以 webhookEventId 去重寫入 → 回 200 → SQLite 佇列 | [A]／業界慣例 | 無 | 1–2 | 高 | 驗簽前讀過 body 或改寫 body | 現在 |
| 開啟 redelivery 與 Error statistics aggregation | [A] | 無 | 0.1 | 中 | 重送不保證送達 | 現在 |
| reply 優先、loading animation、postback 退路 | [A] | 無 | 0.5–1 | 高 | GPU 排隊導致 token 逾時 | 現在 |
| 立即 Get content、原樣保存加 SHA-256、metadata、Pillow 防護 | [A]＋推論 | 無 | 1 | 高 | 內容在下載前被刪除 | 現在 |
| LINE 傳圖實測矩陣（iOS／Android × 三種畫質） | 無公開實測 | 測試帳號與無病人測試照 | 1 | 中高 | 結果可能隨 App 版本改變 | 現在 |
| 依來源設定 Laplacian 門檻（縮到固定長邊） | 推論 | 現有照片 | 0.5 | 中 | 門檻需要重新校正 | 現在 |
| 模擬 LINE 退化的擴增與翻轉壓力測試 | [C] 間接 | 現有照片＋實測參數 | 1–2 | 中 | 特定品質因子組合可能有害 | 壓力測試：現在；訓練擴增：50 位個案後 |
| log 遮罩、v2.1／stateless JWT token、Credential Manager | [A] OWASP、LINE；業界慣例 | 無 | 1–2 | 高 | 遺漏第三方套件的 log | 現在 |
| 三行程隔離、只對外開放 /webhook、ACL、BitLocker、避開 OneDrive | [A]／業界慣例 | 無 | 1–2 | 高 | Windows Home 的加密功能有限 | 現在 |
| Tailscale Funnel 或自架反向代理（TLS 在本機終止） | [A] | 網域 | 1–2 | 中高 | Funnel 仍是 beta、有頻寬上限 | 現在 |
| 依同意狀態切換 per-user rich menu，並在伺服器端檢查同意 | [A] | 無 | 1 | 中高 | 把選單誤當成存取控制 | 現在 |
| 分層同意、append-only 加雜湊鏈的同意紀錄 | [A] 法條、[B] eConsent、推論 | IRB 核定的同意書 | 2–3 | 高 | IRB 是否接受點選同意 | 現在 |
| 撤回流程：exclusion list、刪除、標記模型，不自動重訓 | [A] 法條、推論 | 無 | 1–2 | 高 | 備份中殘留資料 | 現在 |
| 封鎖不等於撤回，狀態改為 paused，並提供 LINE 以外的撤回管道 | [A] 事件、推論 | 無 | 0.5 | 中 | IRB 可能偏好保守做法 | 現在 |
| study_id、HMAC userId、獨立連結表、一次性登錄碼 | [A]、推論 | 無 | 1–2 | 中高 | 碼被轉交他人 | 現在 |
| 文案重寫（行動優先、紅旗、住院與在家分流） | [C]／[B]／[A] 衛教 | 臨床審定 | 2，另加審定 | 高 | 紅旗清單未經臨床審定 | 現在 |
| 長者與照顧者可用性前測（3–5 人） | [C] | 3–5 位受試者 | 2–3 | 中高 | 樣本小 | 現在 |
| 影子模式、分歧盲審、模型登錄表、只自動回滾 | [C] silent trial、[A] GMLP／PCCP | 分歧案例 | 2–3 | 中 | 一致率被誤讀為正確率 | 登錄表與回滾：現在；效能型切換：200 位個案後 |
| 預先註冊不劣性門檻與 McNemar 配對檢定 | [B]／[C] | 數百對配對 | 1–2 | 中 | 群集效應讓 CI 變寬 | 200 位個案後（約 1,000 張） |
| 漂移監測（PSI、KS、輸入特徵、抽樣審閱） | [C]／[E] | 基準期資料 | 2 | 中 | 小樣本時 PSI 不穩定 | 50 位個案後 |
| LIFF 上傳頁（SDK ≥2.31.1，ID token 驗證） | [A] | IRB 決定照片路線 | 5–8 | 中（現在）、高（未來） | WebView 的相機相容性 | 若 IRB 不允許照片經 LINE：現在（簡化版）；否則 50 位個案後 |
| 自建統計與每日對帳、Insight 每日排程抓取 | [A]、推論 | 無 | 1–2 | 中 | 小格數再識別 | 現在 |
| 多語固定模板、專業翻譯與回譯 | [C] 翻譯風險 | 語言需求調查 | 3–5，另加翻譯費 | 中 | 譯文誤差 | 50 位個案後 |
| 台語預錄語音（T5、T6） | 推論 | 母語錄音者 | 1 | 低到中 | 錄音內容不符合方言差異 | 50 位個案後 |
| 本機台語 ASR 研究評估 | [E] 模型卡 | 語音樣本與同意 | 3–5 | 低 | 錯誤分流 | 200 位個案後（只做研究評估） |
| 認證 LINE MINI App | [A] | certified provider | 不建議 | 低 | 商業流程門檻 | 不建議 |
| 面向使用者的 A/B 測試或比例金絲雀 | [B] 倫理爭議、⚠ 違反原則 | — | 不建議 | — | 違反「不自動上線」，需另經 IRB 審查 | 不建議 |

### Inferences
- 總表沒有任何一列標為「約 1,000 張時」，只用「200 位個案後（約 1,000 張）」表示。正文則常用「未來（約 1,000 張）」描述適用性（L219、L516、L593、L757、L1505）。整合時可把這兩者視為同一個時點，但請注意 LIFF 的時程不一致（見 J 節）。
- 總表中「現在」佔大多數，而且都是工程項目；所有效能比較都被推到 200 位個案後。這和報告結語一致：現階段只有工程面能被可靠證明（L2598、L2895）。

### Gaps
- 摘要表沒有「主要風險」與「時程」欄；總表沒有「前置條件」欄（只有「最少資料需求」）。上表已註明欄位對應方式。
- 以下項目在正文有建議、但沒有列入任一建議表，所以報告沒有提供工作量、效益與時程：OneDrive 路徑搬遷（併入第 9 列）、外洩 runbook 演練、per-userId 每日上限、ngrok 禁用、Windows 主機設定（UPS、休眠、Update 時段）、拍照引導內容（範例圖）。

---

## C. LINE 規則速查與變動時間線

### Takeaway
報告的「交付二：LINE 規則速查表」（L2008–2055）列出 40 餘條規則。除特別註明外，LINE Developers 頁面都「頁面未標更新日」，查閱日 2026-10-30 至 10-31。近年確定的變動有：2019-11 api-data 網域、2019-11／2020-02 LIFF 改到 LINE Login channel、2021-10-01 LIFF v1 終止、2022-04 webhook 重送上線、2023-12 MINI App URL、2024-04-17 loading animation、2025-02-12 LIFF 將整合進 MINI App、2025-10-01 MINI App 可在網頁瀏覽器使用、2026-09-30 LIFF v2.31.1、2026-10-07 LIFF v2.31.2、2026-11-01 台灣調價、約 2026-11-24 舊版 LIFF 限制使用。

### Cited Findings

**C1. 規則速查表（照錄 L2012–2055；「本文補充」欄是正文其他節同一主題的數字，附行號）**

| 規則或限制 | 數值 | 官方網址 | 文件日期 | 近年變動 | 本文補充 |
|---|---|---|---|---|---|
| Webhook 簽章 | HMAC-SHA256（channel secret 為 key）、base64、raw body、UTF-8 | [SIG](https://developers.line.biz/en/docs/messaging-api/verify-webhook-signature/) | 頁面未標更新日 | 未見 | 不含時間戳或 nonce，不防重放（L1137） |
| Webhook 回應 | 回 200；建議非同步；可能收到空 events | [REF](https://developers.line.biz/en/reference/messaging-api/) | 頁面未標更新日 | 未見 | RECV 寫 2xx 即視為成功（01 號筆記 L138） |
| request_timeout 判定 | 約 2 秒沒有回應（取自頁面摘要，**需要逐字確認**） | [ERRSTAT](https://developers.line.biz/en/docs/messaging-api/check-webhook-error-statistics/) | 頁面未標更新日 | 未見 | 報告目標 <100 ms（L242）；清單目標 p99 <200 ms（L2485） |
| Webhook 重送 | 預設關閉；只在非 2xx 時重送；次數與間隔不公開；不保證送達 | [RECV](https://developers.line.biz/en/docs/messaging-api/receiving-messages/) | 頁面未標更新日 | **2022-03-07 公告，2022-04 上旬上線**（[ja/38](https://developers.line.biz/ja/news/38/)，日期取自搜尋摘要） | 可能被平台強制關閉；長期收不到時平台可能暫停發送（L154、L157） |
| 去重鍵 | `webhookEventId`（ULID），重送時不變 | REF | 頁面未標更新日 | 與重送功能同時推出 | 差異只在 `deliveryContext.isRedelivery`（L155） |
| 事件順序 | 不保證，以 `timestamp` 判斷 | RECV | 頁面未標更新日 | 未見 | 一次可多事件；imageSet 順序未定義（L188–190） |
| Reply token | 只能用一次；1 分鐘內有效；可能不經通知變更；standby 沒有 token | [REF reply](https://developers.line.biz/en/reference/messaging-api/#send-reply-message) | 頁面未標更新日 | 歷史變更：未找到可靠證據 | 過期回 400 "Invalid reply token"；重送時 "can be used except in certain cases"（L168–169） |
| 每次請求的訊息物件 | reply 與 push 最多 5 個 | REF | 頁面未標更新日 | 未見 | 只顯示最後一則的 quick reply（L429）；物件數不影響計費（L347） |
| Loading animation | 5–60 秒、5 的倍數、預設 20；只限一對一；一律回 202；100 req/s；需 LINE 13.16.0+ | [LOAD](https://developers.line.biz/en/docs/messaging-api/use-loading-indicator/) | 頁面未標更新日 | **2024-04-17 推出** | 只在使用者正在看聊天畫面時顯示；OA 送出新訊息時消失（L179–180） |
| Retry key | 只限 push、multicast、narrowcast、broadcast；自產 UUID；24 小時；重複回 409 | [RETRY](https://developers.line.biz/en/docs/messaging-api/retrying-api-request/) | 頁面未標更新日 | 未見 | 只在 500 或網路逾時時重試；不保證送達（L200–201） |
| Rate limit | 其他端點 2,000/s；multicast 200/s；loading 100/s；統計與 insight 60/h；webhook 端點設定 1,000/min | [REF rate](https://developers.line.biz/en/reference/messaging-api/#rate-limits) | 頁面未標更新日 | 未見 | 另有 audience 60/min、short-lived token 發行 370/s、test webhook 60/h；以 channel、endpoint 分別計（L1256–1268） |
| Rich menu 速率 | 建立、刪除 rich menu，刪除 alias，查詢批次狀態 100/h；批次取代 3/h；取得清單 10/s | 同上 | 頁面未標更新日 | 未見 | 個別綁定或解除 2,000/s；OA Manager 操作不計（L628–631） |
| Get content | api-data.line.me；一段時間後自動刪除（期限不公開）；可能被縮小；202 準備中；410 已收回 | [Get content](https://developers.line.biz/en/reference/messaging-api/#get-content) | 頁面未標更新日 | **網域改為 api-data：2019-11-08 公告，2020-04-30 前須完成** | 404 不存在；preview 較小；transcoding 對圖片回 400；推定 2,000/s（L453–458） |
| contentProvider | `line` 用 Get content；`external` 只給 URL | REF | 頁面未標更新日 | 未見 | `external` "isn't provided by LY Corporation"（L456） |
| imageSet | id、index（從 1 起）、total；送達順序未定義 | 同上 | 頁面未標更新日 | 未見 | — |
| Get content 檔案大小上限 | **未找到可靠證據** | — | — | — | 報告建議自設上限，例如 20 MB（L524） |
| Rich menu 圖片 | JPEG 或 PNG；寬 800–2500；高 ≥250；比 ≥1.45；≤1 MB；設定後不能更換 | [Upload image](https://developers.line.biz/en/reference/messaging-api/#upload-rich-menu-image) | 頁面未標更新日 | 2024–2026 年：未找到變更紀錄 | — |
| Rich menu 數量 | 1,000 個選單；1,000 個 alias；每個選單 20 區；chatBarText 14 字；批次綁定 500 人 | [Rich menu object](https://developers.line.biz/en/reference/messaging-api/#rich-menu-object) | 頁面未標更新日 | 同上 | — |
| Rich menu 優先序 | per-user（API）> 預設（API）> 預設（OA Manager）；per-user 立即生效；API 預設最多約 1 分鐘；PC 版不顯示 | [Overview](https://developers.line.biz/en/docs/messaging-api/rich-menus-overview/) | 頁面未標更新日 | 未見 | 已切換過的使用者，清除預設選單無效（L622） |
| richmenuswitch | 只能用在 rich menu；label ≤20 字 | [Switch action](https://developers.line.biz/en/reference/messaging-api/#richmenu-switch-action) | 頁面未標更新日 | 未見 | 回傳 postback `newRichMenuAliasId`；會被朗讀（L620） |
| Flex Message | bubble ≤30 KB；carousel ≤50 KB、≤12 bubble；**altText 必填 ≤1,500 字元（[A]）**；scaling 需 13.6.0+；filler deprecated | [Flex ref](https://developers.line.biz/en/reference/messaging-api/#flex-message) | 頁面未標更新日 | filler 棄用日期：未查 | scaling 在 PC 需 7.17.0+；shrink-to-fit 是 best-effort（L642–643） |
| 文字訊息長度 | 5,000 字元（**[E]**，未經官方核對） | [Pushwoosh](https://docs.pushwoosh.com/zh/developer/api-reference/line-api/index.md) | — | — | — |
| Quick reply | 最多 13 個；camera、cameraRoll、location 只能在 quick reply；只支援 iOS、Android | [Quick reply](https://developers.line.biz/en/docs/messaging-api/using-quick-reply/) | 頁面未標更新日 | 未見 | camera label ≤20 字；camera 與 cameraRoll 按鈕保留到使用者送出（L654–656） |
| LIFF SDK | 最新 v2.31.2（2026-10-07）；**v2.20.0–v2.31.0 已棄用，約 2026-11-24 起限制** | [LIFF RN](https://developers.line.biz/en/docs/liff/release-notes/) | release notes 本身有日期 | **2026-09-30、2026-10-20** | news 頁需 JS 渲染，未讀到全文（L670） |
| LIFF channel | 只能加在 LINE Login channel；每 channel ≤30；endpoint 須 https | [Adding LIFF](https://developers.line.biz/en/docs/liff/registering-liff-apps/) | 頁面未標更新日 | **Messaging API channel 不再支援：2019-11-11 公告，2020-02-05 生效**；LIFF v1 於 2021-10-01 終止 | 不能含 URL fragment；Compact／Tall／Full；URL 經 LY 的 LIFF 伺服器轉址（L675–677） |
| LIFF ID token | 需 openid；有效 1 小時；伺服器以 `POST /oauth2/v2.1/verify` 驗證 | [LIFF user data](https://developers.line.biz/en/docs/liff/using-user-profile/) | 頁面未標更新日 | 未見 | 不要把 getDecodedIDToken／getProfile 的內容送到伺服器（L691） |
| LIFF 瀏覽器 | （速查表沒有這一列） | [Differences](https://developers.line.biz/en/docs/liff/differences-between-liff-browser-and-external-browser/) | 頁面未標更新日 | — | 不支援 theme-color、download、加入主畫面、Service Workers；file input、capture、getUserMedia 不在不支援清單上（L681） |
| LINE MINI App | 未認證版人人可建；台灣與泰國的認證只限 certified provider；只能用 Full | [MINI intro](https://developers.line.biz/en/docs/line-mini-app/discover/introduction/) | 頁面未標更新日 | **2023-12-13 改用 miniapp URL；2025-02-12 宣布整合 LIFF；2025-10-01 起可在網頁瀏覽器使用** | MINI Apps 分頁只在日本；不能隱藏 action button（L700–701） |
| userId | 以 provider 為範圍；`U[0-9a-f]{32}`；Get follower IDs 只限認證或 premium | [User IDs](https://developers.line.biz/en/docs/messaging-api/getting-user-ids/) | 頁面未標更新日 | 未見 | 未同意 profile 時 webhook 不帶 user ID（L999） |
| Account Link | link token 單次、10 分鐘；nonce 10–255 字元、建議 ≥128 bits；須可隨時解除 | [Linking](https://developers.line.biz/en/docs/messaging-api/linking-accounts/) | 頁面未標更新日 | 未見 | — |
| follow／unfollow | follow（加好友或解除封鎖）可回覆；unfollow 表示封鎖；`isUnblocked`（SDK [E]） | RECV | 頁面未標更新日 | isUnblocked 導入日期：未找到可靠證據 | 對封鎖者推送不送達、不計費（L880） |
| Channel access token | v2.1 ≤30 天、30 個；stateless 15 分鐘、不限量、不可撤銷；short-lived 30 天、30 個；long-lived 無期限、1 個 | [CAT](https://developers.line.biz/en/docs/basics/channel-access-token/) | 頁面未標更新日；[Tips 2026-07-23](https://developers.line.biz/en/tips/2026/07/23/using-multiple-api-tools/) | 棄用公告：未找到可靠證據 | v2.1 assertion ≤30 分鐘、RS256、RSA 2048；stateless v3 端點接受 client_secret（L1103–1107） |
| Webhook TLS | TLS 1.2 或 1.3；公開 CA；不接受自簽；不公開 LINE IP；一個 channel 一個 webhook URL | [TLS spec](https://developers.line.biz/en/docs/messaging-api/ssl-tls-spec-of-the-webhook-source/) | 頁面未標更新日 | 舊 cipher「可能在近期無預警停用」 | — |
| 錯誤統計 | 須手動開啟；不回溯；UTC+9；可匯出 TSV | ERRSTAT | 頁面未標更新日 | 未見 | 四類錯誤；Errors 欄為 60 秒內同狀態碼次數（L1287） |
| 錯誤通知 email | 只限已申請的法人用戶；同狀態碼 5 分鐘內合併 | [ERRNOTI](https://developers.line.biz/en/docs/partner-docs/error-notification/) | 頁面未標更新日 | 2023 年加入「重送停止也通知」（確切日期：未找到可靠證據） | — |
| Insight API | 60 次／小時；約 1 天延遲（人口統計約 3 天）；<20 人回 null；支援台灣帳號 | REF Insight | 頁面未標更新日 | 未見 | 互動統計只更新 14 天（L1301） |
| 計費（台灣） | 輕 NT$0／200；中 **NT$1,000**（舊 800）／3,000、不可加購；高 **NT$1,400**（舊 1,200）／6,000，加購 0.2 元，第 50,001 則起 0.15 元；未稅 | [S2](https://tw.linebiz.com/column/LINEOA-2026-Price-Plan/) | **2026-09-01** | **2026-11-01 生效**；前一次調整為 2023 年（日期只見 [E]） | 舊高用量 6,001–25,000 則 0.2 元，之後遞減到 0.066 元（L338） |
| 不計費項目 | Reply API、一對一聊天、自動回應、AI 自動回應、歡迎訊息 | [S1](https://tw.linebiz.com/service/account-solutions/line-official-account/)、S2 | S1 為 2026-09-24 版資源；S2 為 2026-09-01 | 未見 | loading 不計費屬推論（L389） |
| 計數方式 | 依收訊人數；物件數不影響；對封鎖者或無效 ID 不計 | [Pricing](https://developers.line.biz/en/docs/messaging-api/pricing/) | 頁面未標更新日 | 未見 | 後台群發 3 框；Push 5 框；多頁訊息 ≤9 頁算 1 框（L354–355） |
| 計費時區 | GMT+9（台灣 23:00 以後算隔日） | S1 | 同上 | 未見 | — |
| 額度用盡 | 429 "You have reached your monthly limit."，不會送出 | REF | 頁面未標更新日 | 未見 | 有時有剩餘也可能 429；quota／consumption API（L367–375） |
| 狀態頁 | api.line-status.info，可訂閱 RSS 或 ATOM | [STATUS](https://developers.line.biz/en/docs/basics/line-api-status/) | 頁面未標更新日 | 未見 | 不涵蓋 LINE App 本身（L1305） |
| language 欄位 | BCP 47；未同意隱私權政策時不提供 | [User consent](https://developers.line.biz/en/docs/messaging-api/user-consent/) | 頁面未標更新日 | 未見 | — |
| 請求大小 | （速查表沒有這一列）413 = 請求超過 2 MB | REF Status codes | 頁面未標更新日 | — | L1279 |
| 台灣維護時段 | （速查表沒有這一列）2026-10-28 08:00 至 2026-11-02；2026-11-24 08:00 至 2026-11-25 | S2 | 2026-09-01 | — | 期間「變更訊息則數上限」與方案異動暫停（L325、L415） |

**C2. 變動時間線（從各節整理，依日期排序）**

| 日期 | 事件 | 等級與出處（報告所述） |
|---|---|---|
| 2018-11-09 | 預告「官方帳號 2.0」三方案以量計價 | TechNews，[E]（L382） |
| 2019-11-08 | api.line.me 改為 api-data.line.me 公告，須在 2020-04-30 前更新 | LINE News，[A]（L463） |
| 2019-11-11 公告、2020-02-05 生效 | Messaging API channel 不能再新增 LIFF app | Adding a LIFF app，[A]（L674） |
| 2020-03-01 | 新版官方帳號全面啟用：輕 0 元／500 則；中 800 元／4,000 則；高 4,000 元／25,000 則 | INSIDE [E]；與 S5 原始區塊一致 [A]（L383） |
| 2021-10-01 | LIFF v1 終止 | 只見於速查表 L2038（04 號筆記 L102，[A]） |
| 2022-03-07 公告、2022-04 上旬 | Webhook 重送上線 | ja/38，[A]，日期取自搜尋摘要（L161） |
| 2023（日期未確認） | 台灣免費則數下調、中用量不可加購、高用量月費降為 1,200 元 | 數字 S3 [A]；日期只有 FIRST LINE [E]「更新時間為 2023年9月」（L384） |
| 2023（日期未確認） | 錯誤通知改為重送停止也寄信 | ERRNOTI；確切日期未找到可靠證據（L1288、L2047） |
| 2023-12-13 | MINI App 的 LIFF URL 改為 `miniapp.line.me` | Console guide，經搜尋摘要轉述（L709） |
| 2024-04-17 | Loading animation 推出 | news URL 路徑（L183） |
| 2025-02-12 | 宣布 LIFF 將整合進 MINI App | News，[A]（L710） |
| 2025-09-26 公告、2025-10-01 生效 | MINI App 可在網頁瀏覽器使用 | specifications、News 2025-09-26（L711、L2654） |
| 2026-07-23 | LINE Tips：單一 OA 多工具使用 API 的注意事項（token 來源之一） | [A]（L1084） |
| 2026-09-01 | 台灣調價公告 | S2，[A] |
| 2026-09-24 | S1 頁面資源版本、S5 cal.js 版本路徑 | [A] |
| 2026-09-30 | LIFF v2.31.1 安全修正 | release notes，[A] |
| 2026-10-07 | LIFF v2.31.2（最新） | release notes，[A] |
| 2026-10-20 | LIFF SDK issue news | News（未讀到全文） |
| 2026-10-27 | 之後仍使用中、高用量即視為同意新價 | S2 |
| 2026-10-28 08:00 至 2026-11-02 | 台灣系統維護時段 | S2 |
| **2026-11-01** | **台灣新價生效（中 1,000、高 1,400）** | S2 |
| 2026-11-24 08:00 至 2026-11-25 | 台灣系統維護時段 | S2 |
| 約 2026-11-24 | LIFF v2.20.0–v2.31.0 開始限制使用 | release notes 原文 "around November 24, 2026" |

### Inferences
- 對本專案影響最大、而且最近才變的兩件事是 2026-11-01 調價（全 reply 設計不受影響）與約 2026-11-24 的 LIFF 舊版限制（只影響路線 B）。其他規則近年都沒有變動紀錄，但多數 LINE 頁面沒有更新日，「未見變動」不等於「確定沒變」。

### Gaps
- Reply token 時限、rich menu 規格、filler 棄用日期、isUnblocked 導入日期、token 類型棄用：報告都沒有找到變動紀錄或日期。
- 2 秒 request_timeout 與狀態頁說明都只來自頁面摘要，需要逐字確認。

---

## D. 特別交付內容

### Takeaway
報告提供四份交付：(1) 建議架構（元件、信任邊界、路線 A 的文字時序圖、路線 B 的差異、停機回復）；(2) 費用試算（5 種對話設計 × 100／1,000／10,000 次，新舊兩套價格）；(3) F0–F8 對話流程與文案；(4) 上線前技術檢查清單。全部屬**本報告推論**，依據前述官方規則（L1926、L2063、L2148）。

### Cited Findings

#### D1. 建議架構（交付一，L1924–2004）

**元件**（L1930–1939）

| 元件 | 位置與職責 | 不做的事 |
|---|---|---|
| 對外入口 | 首選 Tailscale Funnel；次選 Caddy 或 nginx 加 Let's Encrypt 與固定 IP；若只走聊天路徑也可用 Cloudflare Tunnel。TLS 1.2／1.3，公開 CA 憑證。只轉送 `POST /webhook/<隨機字串>`，路線 B 另加 `POST /upload` 與 LIFF 靜態頁 | 不轉送管理路徑；路線 B 不用 Cloudflare 或 ngrok ⚠ |
| webhook-svc（127.0.0.1:8001） | 限制 body 大小 → 驗簽 → `INSERT OR IGNORE` 寫入 webhook_events 與 jobs → 回 200 | 不推論、不下載照片、不記錄 body 與簽章、不掛管理路由 |
| upload-svc（路線 B，可與 webhook-svc 同一行程、不同 router） | 驗 ID token（`POST /oauth2/v2.1/verify`）→ 查同意狀態 → 串流接收照片並設上限 → 寫檔與 SHA-256 → 建 job | 不信任前端傳來的 profile |
| SQLite（WAL） | webhook_events、jobs、photos、consent_documents、consent_events（append-only）、model_registry、replies_audit、exclusion_list；`line_link` 放在**另一個加密的 SQLite 檔** | 研究分析用的 DB 不存明文 userId |
| worker（單一 GPU 行程） | 搶佔 job → loading → Get content → 格式驗證與 bomb 防護 → 原檔與工作副本 → 品質檢查 → YOLO 與分類 → reply → 影子模型（低優先） | 不做訓練；影子結果不回覆使用者 |
| 秘密保存 | Windows Credential Manager（DPAPI）保存 RSA 私鑰、channel secret、HMAC pepper | 不放 .env、repo、log、備份 |
| admin-api 與 React（127.0.0.1:8000） | 標註、審閱、模型登錄與切換（須人工簽核）、統計、LINE 模擬器 | 不經任何 tunnel |
| 監控 | `/healthz`（只綁本機）、告警（email 或 Windows 通知）、訂閱 api.line-status.info RSS、每日對帳 | 不觸發自動訓練或自動上線 |

**信任邊界**（L1943–1950）

| 邊界 | 跨越的資料 | 信任程度 |
|---|---|---|
| ① 使用者裝置 → LINE 平台 | 路線 A 的照片 ⚠ | 第三方暫存，期限不公開 |
| ② LINE 平台 → 對外入口 → webhook-svc | webhook JSON | 只有驗簽通過後才信任 |
| ③ worker → api-data.line.me | 出站 HTTPS 下載照片 | 內容視為不可信，必須驗證 |
| ④ 使用者瀏覽器（LIFF）→ 對外入口 → upload-svc | 路線 B 的照片 | 入口的 TLS 終止點必須在本機 |
| ⑤ 本機行程 ↔ SQLite、檔案系統 | — | 以 NTFS ACL 隔離 |
| ⑥ admin（localhost）↔ 研究人員 | — | 需要登入 |

**文字時序圖（路線 A，照錄 L1954–1991）**

```
參與者：U=使用者 LINE App；P=LINE Platform；G=對外入口(Funnel/反代)；W=webhook-svc；D=SQLite；K=worker(GPU)；L=api-data.line.me/api.line.me

0. 前置：U 已加好友 → follow 事件 → W 存事件 → K 以 reply 送 T1 同意摘要卡（免費）
   U 完成同意（postback 或 LIFF）→ D 寫入 consent_events → K 呼叫 Link rich menu to user（換成同意後選單）

1. U 點【拍照】(quick reply camera action) → 拍照 → 傳送
2. P → G → W：POST /webhook（events[] 含 image message、replyToken、webhookEventId、timestamp、deliveryContext.isRedelivery）
3. W：驗 HMAC(raw body)
     ├─ 失敗 → 回 400、記錄 sig_fail 計數（告警閾值）→ 結束
     └─ 成功 → 對每個 event：INSERT OR IGNORE webhook_events
           ├─ 重複（rowcount=0）→ 略過
           ├─ mode=standby → 只記錄
           ├─ 使用者未同意，或狀態為 withdrawn/paused → 建立「回覆說明」job（不下載照片）
           └─ 正常 → INSERT jobs(status=queued, webhook_received_at=now)
4. W → P：HTTP 200（目標 <100 ms；錯誤統計將約 2 秒無回應計為 request_timeout）
5. K：取最早到期的 queued job → POST /v2/bot/chat/loading/start {chatId, loadingSeconds:30}（202；不保證顯示）
6. K → L：GET /v2/bot/message/{id}/content（Bearer 短效 token）
     ├─ 202 / 5xx → 退避重試 ≤3 次 → 失敗：status=dead、告警；以 reply 送「請重新上傳」
     ├─ 410 → 使用者已收回 → 刪除資料，不回覆
     └─ 200 → 串流寫檔（上限）→ SHA-256 → magic bytes → Pillow(formats, bomb=error) → exif_transpose＋去 GPS 工作副本
7. K：品質檢查（Laplacian，縮到固定長邊後計算；過暗/過亮比例）
     └─ 不合格（「拒絕」模式）→ 跳到 9，送 T3「請重拍」
8. K：推論（YOLO→分類；active_model_id 必須通過雜湊驗證，否則降級為「需人工確認」）
     ├─ 低信心 → T4「已請研究人員再看」，並建立人工審閱任務
     └─ 正常 → 依結果選 T5（stage 1/2，住院版或在家版）或 T5b（未見明顯紅腫）
9. K：檢查 now − webhook_received_at
     ├─ < 約 50 s → POST /v2/bot/message/reply（replyToken；≤5 個訊息物件：結果文字＋紅旗＋quick reply）
     │      ├─ 200 → status=replied；loading 自動消失；replies_audit 寫入 model_id、hash
     │      ├─ 400 Invalid reply token → 跳到 10
     │      └─ 5xx/逾時 → 記錄 x-line-request-id；1 分鐘後標為 unknown，不重送
     └─ ≥ 約 50 s → 跳到 10
10. 退路（依研究政策，二擇一）：
     a) 預設：結果存入 D；等使用者點選單【我的最近結果】(postback) → 用新的 replyToken 以 reply 送出（免費）
     b) 例外且需核准：push，帶 X-Line-Retry-Key=job.retry_key（24 小時內可安全重試；額度不足回 429 → 改走 a）
11. K（reply 之後、低優先）：shadow_model_id 推論 → 只記錄比較；失敗不影響主流程
12. 每日：比對自建 replied/pushed 數與 LINE delivery API；檢查 consumption 與 quota；檢視 Error statistics
```

**路線 B（LIFF）差異**（L1993–1997）：步驟 1–4 改為 U 開啟 `https://liff.line.me/{liffId}`，經 LY 的 LIFF 伺服器轉址 → G → upload-svc；`liff.init()` 取得 ID token，連同照片 POST 到 `/upload`；upload-svc 驗 ID token，檢查 `aud`、`exp`、`sub`，`sub` 經 HMAC 後應等於 `user_pid`。步驟 6 不需要 Get content。結果直接顯示在 LIFF 頁上，不耗用訊息額度；回到聊天室後可用 postback 查看。

**停機與回復**（L1999–2004）：重啟時把 downloading 或 inferring 的 job 回收為 queued；重送以 `webhookEventId` 去重；token 失效依步驟 10；長時間停機後只能依人工核准補發 push，每人最多一則。

**失敗處理**：詳見 A8 的失敗處理矩陣（L1324–1337）與 A1 的風險表（L285–291）。

#### D2. 費用試算（交付三，L2059–2143）

**假設**（本報告推論，輸入來源 S2、S5、Pricing，查閱 2026-10-30 至 31，L2061–2071）：(1) 每次分析對應 1 位使用者的一對一聊天，每次 push 只發給一個 userId、最多 5 個物件，所以 1 次 push 計 1 則；(2) reply、postback 觸發的 reply、loading 都不計費，其中 loading 不計費屬推論；(3) 設計 C 假設每人每月平均 5 次分析，所以 100、1,000、10,000 次對應 20、200、2,000 人（假設、非來源數字）；(4) 對封鎖者或無效 ID 的訊息假設為 0；(5) 每個情境選能容納則數的最便宜方案，中用量上限 3,000、不可加購；(6) 含稅以 5% 估算，**未經本次官方來源查證**；(7) 只算 LINE 訊息費，不含伺服器、電費、GPU、網域、VPS；LINE Login、LIFF、MINI App 是否另收費，**未找到可靠證據**。

**對話設計**（L2075–2081）：A 全 reply（建議），照片 → loading → reply，逾時給「查看結果」postback，每次分析 0 則 push；B 推論後主動 push 結果，1 則；C push「已收到」再 push 結果，另加每人每月 1 則提醒，2 則加每人每月 1 則；D 以 A 為主、5% 逾時用 push 補發（推論），0.05 則；E LIFF 上傳、頁內顯示結果、回聊天室用 postback 加 reply（推論），0 則。

**每月計費則數**（L2085–2091）

| 設計 | 100 次 | 1,000 次 | 10,000 次 |
|---|---|---|---|
| A | 0 | 0 | 0 |
| B | 100 | 1,000 | 10,000 |
| C | 2×100+20 = 220 | 2×1,000+200 = 2,200 | 2×10,000+2,000 = 22,000 |
| D | 5 | 50 | 500 |
| E | 0 | 0 | 0 |

**2026-11-01 起新價（未稅，NT$）——主要依據**（L2095–2106）

| 設計／量級 | 最低可行方案 | 計算 | 月費（未稅） | 含 5% 稅（估） | 每次分析成本 |
|---|---|---|---|---|---|
| A／100、1,000、10,000 | 輕用量 | 0 | **0** | 0 | 0 |
| B／100 | 輕用量（100 ≤ 200） | 0 | **0** | 0 | 0 |
| B／1,000 | 中用量（≤ 3,000） | 1,000 | **1,000** | 1,050 | 1.00 |
| B／10,000 | 高用量 | 1,400 + (10,000−6,000)×0.2 | **2,200** | 2,310 | 0.22 |
| C／100 | 中用量（220 > 200） | 1,000 | **1,000** | 1,050 | 10.00 |
| C／1,000 | 中用量（2,200 ≤ 3,000） | 1,000 | **1,000** | 1,050 | 1.00 |
| C／10,000 | 高用量 | 1,400 + (22,000−6,000)×0.2 | **4,600** | 4,830 | 0.46 |
| D／100、1,000 | 輕用量（5、50 ≤ 200） | 0 | **0** | 0 | 0 |
| D／10,000 | 中用量（500 > 200） | 1,000 | **1,000** | 1,050 | 0.10 |
| E／全部 | 輕用量 | 0 | **0** | 0 | 0 |

**2026-10-31 以前舊價（比較用）**（L2110–2119）：A、E 全部 0；B／100 為 0；B／1,000 中用量 800（差額 +200）；B／10,000 高用量 1,200 + 4,000×0.2 = 2,000（+200）；C／100 中用量 800（+200）；C／1,000 中用量 800（+200）；C／10,000 高用量 1,200 + 16,000×0.2 = 4,400（+200）；D／10,000 中用量 800（+200）。

**固定方案可行性（新價）**（L2123–2133，✗＝超額 push 回 429、送不出）：A、E（0 則）三方案都 ✓（中、高為多付）；B-100 都 ✓；B-1,000 輕用量 ✗（第 201 則起失敗，約 800 則結果送不出），中、高 ✓；B-10,000 輕 ✗、中 ✗（第 3,001 則起失敗）、高 ✓ NT$2,200；C-100（220）輕 ✗（超出 20 則），中、高 ✓；C-10,000（22,000）輕 ✗、中 ✗、高 ✓ NT$4,600；D-10,000（500）輕 ✗（超出部分應自動降級為 postback），中、高 ✓。

**敏感度**（本報告推論，L2137–2143）：C 拿掉月提醒後，100 次只需 200 則，剛好等於輕用量上限、完全沒有緩衝，多一則（例如停機後補發）就 429；高用量每多 1 則 NT$0.2，當月加購滿 50,000 則後每則 NT$0.15；每月 10,000 次時 C 比 A 每年多約 NT$55,200（4,600 × 12，未稅）；每月 push ≤200 就維持 NT$0，超過時把 push 補發自動降級為 postback 也能維持 NT$0；月底 23:00（台灣）以後的 push 計入下個月，在額度邊緣時可能讓下個月提早用完。

#### D3. 對話流程與文案範本（交付四，L2146–2454）

**上線前四道關卡**（L2150–2153）：臨床護理專家審定（特別是紅旗清單與時間承諾）、IRB 核准（同意書與撤回說明）、法規顧問審閱（確認沒有診斷宣稱）、長者與照顧者理解測試。標記：〈〉是變數，【】是 quick reply 或 postback 按鈕。共同格式：第一行寫結論或要做的事 → 最多 3 點說明 → 紅旗或下一步 → 最後一行小字註明是研究；純文字送出，改用 Flex 時 altText 填第一行全文；每則約 120–150 字以內（L2157–2164）。

**跨筆記衝突處理**（L2166–2167）：08 號筆記的同意範本寫「照片只用在研究，存在〈醫院〉的電腦，不會給其他公司」，但 04、05、06 號筆記都指出走聊天路徑時照片一定會先暫存在 LINE 伺服器，臺大指引也要求告知「傳輸可能被第三方截取」，照原文寫「不會給其他公司」**會構成不實陳述**，所以 F1 改為揭露版，並依路線 A 或 B 提供兩種寫法。

**流程總覽**（L2169–2177）：(1) 加好友（follow）→ reply 送 F0 歡迎與語言 → F1 同意摘要，此時是預設選單、沒有上傳按鈕；(2) 點【先看完整說明】→ 開同意頁（自有 HTTPS 或 LIFF）→ 2–3 題是非題 → 自我聲明 →【我同意】；(3) 寫 `consent_events`，把選單換成同意後版本，送 F2；(4) 傳照片後依結果送 F3 品質不足、F4 需人工確認、F5 建議告訴護理師或就醫、F5b 沒有看到明顯紅腫；(5) **任何時候**回報紅旗都送 F6；(6) 點【撤回同意】→ F7a 確認 → 再確認後送 F7；(7) 封鎖（unfollow）**不回覆**（無法回覆），狀態設 `paused`，解除封鎖（follow 且 `isUnblocked=true`）送 F8。

**文案全文（照錄）**

F0 歡迎與語言（L2181–2185）：
```
您好，這裡是〈研究團隊名稱〉的打針部位照片研究帳號。
請先選擇語言。
【中文】【English】【Bahasa Indonesia】【Tiếng Việt】
```
設計理由：`language` 欄位只能當預設值（未同意隱私權政策時不存在，手機語言也不一定是閱讀偏好）；語言以照顧者常用語言為優先。

F1 同意摘要，第一層（L2194–2208）：
```
這是「打針部位照片研究」，不是看病。
研究結果不能代替醫師或護理師的判斷。

參加的話，會請您傳手臂打針部位的照片：
1. 〈路線 A〉照片會先經過 LINE 公司的伺服器傳送並暫存一段時間，
   研究團隊下載後存在研究團隊自己的電腦，不放到其他雲端服務。
   〈路線 B〉照片直接傳到研究團隊自己的電腦，不經過 LINE 聊天室。
2. 您隨時可以退出，退出後馬上生效；之前的照片怎麼處理，寫在完整說明裡。
3. 不參加或退出，都不會影響您的治療。
4. 封鎖這個帳號不等於退出；要退出請按選單「撤回同意」或打〈電話〉。

有問題可以找真人：〈研究聯絡電話〉
【先看完整說明】【我是幫家人傳】【我不參加】
```
設計理由（L2212–2218）：第一行說明「是研究不是看病」；切成四點（AHRQ）；據實揭露照片經過 LINE；撤回立即生效、不影響治療；封鎖不等於退出並提供 LINE 以外管道；「我是幫家人傳」處理代傳（70 歲以上上網率 53.80%）；這一則**不放「我同意」按鈕**，要求先進第二層，避免「跳過關鍵資訊」取得同意，依據是 [E] 來源中 IRB 審查慣例的建議。

F1b 第二層完整說明頁上的確認問題（L2222–2230）：
```
請回答 3 個小問題（答錯沒關係，會再說明一次）：
1. 這個服務會告訴我「我有沒有得靜脈炎」嗎？　○會　○不會（正解：不會）
2. 我可以隨時退出嗎？　○可以　○不可以（正解：可以）
3. 打針的地方很痛、很紅時，我應該等這個帳號回覆嗎？　○要等　○不用等，直接告訴護理師（正解：不用等）
□ 我已年滿 18 歲（或依 IRB 核定），是照片中手臂的本人，或其法定代理人。
□ 我是代傳的家人或看護，病人本人／法定代理人已同意。
【我同意參加】
```
設計理由：簡化版 teach-back（AHRQ），答錯不排除；第 3 題針對 automation bias；LINE 無法驗證年齡或本人，所以用自我聲明；按下【我同意】時 postback 帶 `consent_version` 與 `doc_sha256`，寫入 append-only 紀錄。

F2 上傳照片說明（L2242–2249）：
```
請拍「打針的地方」，照這樣拍：
1. 在亮的地方拍，不要開閃光燈，不要用濾鏡或美顏。
2. 手機離手臂大約一個手掌遠。
3. 整個貼布和周圍皮膚都要拍進去。
4. 一次傳一張就好；自己拍不到，可以請家人幫忙。

拍好直接傳到這裡。
【拍照】【從相簿選】【看範例圖】【我現在在醫院】
```
設計理由：步驟化（CDC CCI、AHRQ）；「一個手掌遠」取代公分；不要濾鏡（BAD、色偏風險）；請家人幫忙（Gunter 2016）；【拍照】【從相簿選】是 camera 與 cameraRoll，只能放 quick reply、會保留到送出；第四顆收集住院或在家；quick reply 最多 4 顆。範例圖 altText：「範例：手臂打針處，貼布在畫面中間的照片」。

F3 品質不足，請重拍（L2266–2275）：
```
這張照片看不清楚，請再拍一次。
原因：〈太暗／太模糊／打針的地方不在畫面裡〉

小提醒：到亮一點的地方，手拿穩再拍。

不管照片結果如何，如果打針的地方很痛、變紅、腫起來：
在醫院請直接按鈴告訴護理師；在家請聯絡幫您打針的醫院。
【重新拍照】【看拍照範例】【我不會拍，找真人】
```
設計理由：第一行是要做的事；不責怪使用者；給具體原因（Vodrahalli 2023、Zhang 2021 顯示即時回饋加重拍最有效）；沒有結果時仍附基本紅旗；【重新拍照】是 camera action；原因只用固定詞彙。

F4 需人工確認（模型低信心）（L2288–2298）：
```
這張照片，研究系統沒辦法判斷，已經請研究人員再看一次。
我們會在〈例如：上班時間 24 小時內〉回覆您。

等待的時候，如果打針的地方痛、紅、腫、變硬，或流膿、發燒：
・在醫院：現在就按鈴告訴護理師，不用等我們。
・已經回家：請聯絡幫您打針的醫院或診所。

這是研究系統，不是醫師的判斷。
【好，我知道了】【我在醫院】【我已經回家】
```
設計理由：直接寫「沒辦法判斷」，不用「可能」「也許」（van der Bles 2020、Andreadis 2021）；具體等待時間，**這個承諾必須依實際研究人力確認**；「不用等我們」避免延誤；人工回覆可用 OA Manager 一對一聊天（免費）。

F5 建議告訴護理師或就醫（stage 1 或 stage 2），住院版（L2312–2322）：
```
請告訴護理師看一下您打針的地方。〈stage 2 時：請現在就按鈴。〉

研究系統在照片中看到〈發紅／腫起來〉的樣子。
這不是診斷，要由護理師親自看才算數。

如果有下面任何一種，請馬上按鈴：
・越來越痛　・紅的範圍變大　・摸起來硬硬的、像一條線
・流膿或滲水　・發燒、發冷
【我會告訴護理師】【我看不懂】【找真人】
```
在家或門診版（L2326–2336）：
```
建議今天聯絡幫您打針的醫院或診所，請他們看一下。

研究系統在照片中看到〈發紅／腫起來〉的樣子。
這不是診斷，要由醫師或護理師親自看才算數。
拔針後 2 天內，仍要每天看一下打針的地方。

如果發燒、發冷、紅線往上延伸，或整隻手臂腫起來，
請馬上去醫院；很嚴重時撥 119。
【我會聯絡醫院】【我看不懂】【找真人】
```
設計理由（L2340–2348）：第一行是行動；寫「看到……的樣子」，不寫「您有第 2 期靜脈炎」，期別與分數只存研究 DB；stage 1 與 2 只差在第一行的緊急程度（對應 VIP：1 項徵象觀察、2 項徵象更換部位）；紅旗最多 5 項、口語化（「像一條線」＝可觸及靜脈索；「發燒」對應 VIP 5 分）；在家版加「拔針後 2 天內」（NHS Lothian 48 小時）；不給冷熱敷（台英衛教不一致，且屬治療建議）；不寫 1922；**「紅線往上延伸、寒顫」尚未經 [A] 逐條核對，須由臨床人員審定**；【我看不懂】送更簡化版或轉真人。

F5b 沒有看到明顯紅腫（L2352–2361）：
```
這張照片中，研究系統沒有看到明顯的紅或腫。
但照片看不出痛不痛、硬不硬，請繼續注意。

只要打針的地方痛、紅、腫、變硬、流膿，或發燒，
在醫院請按鈴告訴護理師；在家請聯絡醫院或診所。

這是研究系統，不是醫師的判斷。
【好，我知道了】
```
設計理由：不寫「沒有靜脈炎」；明說照片的限制；紅旗照樣列出。

F6 緊急轉介（使用者用文字或按鈕回報紅旗，或系統偵測到關鍵字）（L2371–2380）：
```
這可能需要馬上處理，請不要等研究系統回覆。

・在醫院：現在按床邊的呼叫鈴，找護理師。
・在家：請立刻去急診。
・如果呼吸困難、胸痛、昏昏沉沉叫不醒，或流血止不住：請立刻撥 119。

這個帳號沒有人 24 小時看訊息，緊急時請不要只傳訊息給我們。
【我在醫院，去按鈴】【撥打 119】
```
設計理由：第一行「不要等」；誠實說明沒有 24 小時值守；119 是救護專線（[E]）；【撥打 119】用 URI action `tel:119`，**在 LINE 裡的實際行為需要實機測試**；胸痛、呼吸困難是一般急症常識，須臨床審定；留置針脫落的止血方式（按壓 2–5 分鐘，依 NHS Lothian）另放 F6b（報告沒有給 F6b 全文）。

F7a 撤回前確認（L2393–2397）：
```
您要退出照片研究嗎？
退出後，我們不會再使用您之後傳的照片。
【確定退出】【先不要】
```
設計理由：防止誤觸，用 postback 送出，回覆不計費。

F7 撤回同意確認（L2403–2413）：
```
已收到，您已退出照片研究，馬上生效。

・從現在起，我們不會再使用您之後傳的照片。
・您之前的照片：〈依 IRB 核定的同意書：將在 N 天內刪除〉。
・退出不會影響您的治療。

如果改變主意，隨時可以按【重新參加】。
有問題請找：〈研究聯絡電話〉
【重新參加】【我還有問題，找真人】
```
設計理由：第一行先確認結果；分別說明「之後」與「之前」的資料，必須與同意書及第 5 節一致；08 號筆記原寫「已去識別的研究資料無法再分開，會保留」，報告**不建議**把照片寫成可去連結後保留，只有在 IRB 核准、而且確實是不含照片的彙總統計時才寫入這種說法；重申不影響治療；提供重新參加的途徑。送出 F7 的同時：unlink 選單、寫 `withdrawn`、加入 exclusion list、排入刪除工作、標記模型，**不觸發自動訓練**（L2423）。

F7c 撤回後又傳照片（L2427–2431）：
```
您已退出研究，這張照片不會被使用或保存。
如果想重新參加，請按【重新參加】。
【重新參加】【找真人】
```
設計理由：撤回立即生效的技術意義，就是之後的照片一律不下載、不推論。

F8 解除封鎖後回來（follow 且 `isUnblocked=true`）（L2437–2441）：
```
歡迎回來。您的研究狀態是：〈參加中／已退出〉。
〈同意書已更新時：研究說明有更新，請先看新的說明再決定是否繼續。〉
【看研究說明】【撤回同意】
```
設計理由：封鎖期間是 `paused`、不是撤回；告知目前狀態；版本更新時要求重新同意。

多語與無障礙備註（L2449–2454）：模板交專業譯者翻成英文、印尼文、越南文，再回譯與母語照顧者測試；F5、F6 優先錄台語真人語音；**不使用雲端翻譯、ASR、TTS（⚠）**；每則用中文版 CDC CCI 自評 ≥90。

#### D4. 上線前技術檢查清單（交付五，L2458–2520，照錄要點；原文「勾選前，請在本平台實際測試，並把結果記錄下來」）

**安全**（L2464–2479）
- [ ] raw bytes 做 HMAC、`compare_digest`；header 缺漏回 400 不變 500；單元測試涵蓋 emoji 與 CRLF。
- [ ] 驗簽後才解析 JSON；不用 Pydantic body 參數；沒有 middleware 改寫 body。
- [ ] webhook-svc 與 admin 是兩個獨立 app；`/docs`、`/redoc`、`/openapi.json` 關閉；對外只開 `POST /webhook/<隨機字串>`，其他回 404。
- [ ] admin 只綁 127.0.0.1，防火牆擋 8000、8001 入站，admin 需要登入。
- [ ] 對外 TLS 只允許 1.2 與 1.3、公開 CA、鏈完整；**有 LIFF 上傳路徑時 TLS 終止點必須在本機**（Funnel 或自架反代），不能用 Cloudflare 或 ngrok ⚠。
- [ ] 不使用 ngrok；非用不可時 Traffic Inspector full capture 必須關閉並經書面確認 ⚠。
- [ ] token 用 v2.1 或 stateless（JWT 版）；不用 long-lived，也不用 `client_secret` 版 stateless。
- [ ] RSA 私鑰、channel secret、HMAC pepper 存 Credential Manager；不在 repo、`.env`、log、備份。
- [ ] 外洩 runbook 已寫好並演練。
- [ ] log 遮罩測試：一週 log 搜尋 `U[0-9a-f]{32}`、`Bearer`、`replyToken`、`x-line-signature` 都是 0；uvicorn access log 關閉；httpx logger 為 WARNING。
- [ ] 沒有雲端 APM 或錯誤追蹤 ⚠。
- [ ] 圖片下載有上限；Pillow `formats=`；DecompressionBomb 視為錯誤；`external` 拒收；httpx `follow_redirects=False` 並限制網域。
- [ ] 以標準使用者帳號執行；NTFS ACL 限縮；BitLocker 或裝置加密，外接備份碟也加密。
- [ ] **照片與 DB 路徑不在 OneDrive 同步範圍內，已實際確認 ⚠**。
- [ ] 相依套件以 hash 鎖版，`pip-audit` 0 個高風險；有 LIFF 時 SDK ≥2.31.1。
- [ ] 研究表沒有明文 userId；`line_link` 在另一個加密 DB；匯出資料集沒有 userId 與 GPS。

**可靠性**（L2483–2493）
- [ ] Console 已開「Use webhook」「Webhook redelivery」「Error statistics aggregation」，有截圖。
- [ ] `webhookEventId` 去重：送 3 次只產生 1 個 job。
- [ ] webhook p99 <200 ms；一週 `request_timeout` 為 0。
- [ ] SQLite WAL；啟動回收卡住的 job；指數退避；失敗進 dead 並告警。
- [ ] 同一使用者依 `timestamp`；GPU worker 只有一個；最早到期優先。
- [ ] 收到 image 立刻 Get content；202、5xx、410 都有處理。
- [ ] token 逾時退路：預設 postback「查看結果」；push 須核准並附 retry key；額度 429 不重試。
- [ ] 實測過延遲 65 秒、worker 被強制終止、停機 10 分鐘。
- [ ] 設為 Windows 服務、開機自動啟動、崩潰自動重啟；關休眠；Update 維護時段；UPS；tunnel 自動重連。
- [ ] 選單分同意前與同意後，以 per-user link 切換；伺服器每張照片都重查同意。
- [ ] unfollow 改 `paused`；follow 讀 `isUnblocked`；unsend 刪資料；`mode=standby` 不回覆。

**監控**（L2497–2503）
- [ ] `/healthz`（只綁本機）回報 DB 可寫、佇列深度、最舊 job 等待、GPU、worker 心跳。
- [ ] 告警：最舊 job >45 秒、驗簽失敗暴增、Invalid reply token 比例升高、心跳 >60 秒、磁碟不足、連續 5xx 或 429、GPU 不可用；email 或 Windows 通知，不含個資。
- [ ] 每天比對回覆數與 LINE 的 reply、push 發送數，記錄 `consumption` 與 `quota`；確認方案是「輕用量」。
- [ ] 每天排程抓一次 Insight followers；儀表板不每次刷新都呼叫 Insight。
- [ ] 訂閱 api.line-status.info RSS。
- [ ] 研究 KPI（收件數、同意率、品質不足比例、預測分布、撤回次數）只用自建表、排除重送；對外報告遮蔽小格數。
- [ ] 每週模型監控：預測分布、分數分布、輸入特徵、需人工確認比例、抽樣審閱、影子分歧率。

**回滾與模型治理**（L2507–2514）
- [ ] 登錄表以 SHA-256 識別，狀態機強制只有 approved 能設為 active；外部 safetensors 只能先登錄為 candidate。
- [ ] 啟動時驗雜湊，不符就降級為「需人工確認」。
- [ ] 上一個 approved 熱備，回滾演練在數秒內完成並留紀錄。
- [ ] 自動回滾只由工程 guardrail 觸發（錯誤或逾時、雜湊不符、輸出不合法、類別分布極端），觸發後通知負責人並由人工確認；**沒有自動晉升、沒有自動訓練** ⚠。
- [ ] 影子在 reply 後才執行，失敗不影響主流程；同意書已揭露影子分析。
- [ ] 影子轉上線的書面門檻已寫好並由負責人簽核；**現階段（14 位個案）不做任何依效能決定的切換**。
- [ ] 撤回演練通過：照片刪除、連結斷開、exclusion list 更新、快照與模型標記。
- [ ] 若需聯絡曾收到錯誤結果的使用者，模板事先審定、發送前人工核准，並寫入 IRB 計畫書。

**內容與合規**（非技術，但上線前必須完成，L2518–2520）
- [ ] IRB 已決定照片走 A 或 B，同意書已揭露照片會經過 LINE（A）或 LIFF 的資料流（B），並決定封鎖、撤回、保存期限的處理方式。
- [ ] F0–F8 已經過臨床審定、IRB 與法規顧問審閱，CCI ≥90，完成長者理解測試。
- [ ] 已人工查閱 LINE OA 條款與 User Data Policy 中的健康資料規定（本輪**未找到可靠證據**）。

### Inferences
- 架構裡唯一會自動「寫入對使用者有影響的結果」的路徑，是 worker 在步驟 8–9 自動把 active 模型的分類結果以 F5／F5b 回覆給使用者。報告用「措辭、紅旗、不顯示分數與期別」來處理，但沒有把它標成 ⚠，也沒有要求人工先確認再回覆（見 E 節）。
- 費用試算的結論很穩健：只要不使用 push，任何量級都是 NT$0；推論時間與 GPU 排隊只會影響「逾時改走 postback」的比例，不會影響費用。

### Gaps
- F6b（止血說明）只描述內容，沒有給全文。
- 時序圖用 T1、T3、T4、T5、T5b 編號，交付四用 F0–F8，兩套編號沒有明確對照（見 J 節）。
- 費用表沒有計入可能的聊天記錄進階方案（工商時報 [E] 說每月 NT$100），因為報告主張研究紀錄由本機保存。

---

## E. 可能與其他段落或原則衝突、有張力的地方

### Takeaway
報告自己標出 9 項 ⚠ 原則衝突並給了替代方案（L2852–2866）。另外有幾處和其他段落（法規／隱私／IRB／醫材界線、評估、推論延遲、壓縮與模型品質）直接相關，還有一處報告沒有標成 ⚠、但可能與「模型建議須人工確認」原則有張力：系統會自動把模型結果回覆給民眾。

### Cited Findings

**E1. 「研究照片不上傳第三方雲端」——報告怎麼處理 LINE 本身的傳輸**
- L5：「**經聊天傳的照片一定會先暫存在 LY Corporation（LINE）的伺服器**，官方只說『一段時間後自動刪除』，沒有公布期限……如果嚴格解讀『研究照片不上傳第三方雲端』，這條路線本身就違反原則。替代方案是用 LIFF 頁面把照片直接上傳到本機，並讓 TLS 在本機終止。」
- L63：「如果 IRB 把原則解讀為『不得經過任何第三方伺服器』，這條路線本質上不符合原則。如果解讀為『研究端不主動上傳到第三方雲端儲存或 AI 服務』，同意書就必須揭露『照片經 LINE 傳輸並暫存於 LINE 伺服器』。」
- 報告的立場：把它定為 **IRB 層級的決定**，應最先送 IRB 討論，而不是等工程完成後再補揭露（L2596）；路線 A 在信任邊界表標為「① 第三方暫存，期限不公開 ⚠」（L1945）；同意書 F1 必須據實揭露（L2166–2167、L2199–2201）。
- 其他會讓 LINE 或第三方接觸研究資料的路徑：
  - Flex 結果卡放照片縮圖會把研究照片 URL 暴露給 LINE 平台，所以「結果卡不放照片縮圖」（L784）。
  - LINE 官方承認內容可能被縮小（L452）；LINE 隱私權政策說被指定為可能含敏感資訊的 OA，內容不會用於機器學習（L892，經搜尋摘要）。
  - OA Manager 會保存聊天記錄（官方頁「儲存2024年1月1日起的聊天記錄」；工商時報 [E] 說未升級只保留 6 個月）。報告只從「研究紀錄不能依賴它」的角度討論（L392），**沒有把 LINE 保存聊天記錄當作原則問題討論**（本筆記推論：文字訊息與研究人員人工回覆都會留在 LINE）。
  - 語音訊息與照片一樣會經過 LINE（L1774、L1862）。
  - LIFF URL 會經 LY 的 LIFF 伺服器轉址（L677、L1995），但照片本身直接上傳到我方。
- **tunnel 或 proxy 可能保存資料**：
  - ngrok Traffic Inspector 保存請求，Free 24 小時、Hobbyist 與 Pay-as-you-go 72 小時、加購最長 90 天，包括 replyToken ⚠（L1121、L1154）。
  - Cloudflare 在 edge 終止 TLS、看得到明文，只有 [E] 來源（L1120）；只走聊天時 Cloudflare 看得到 webhook JSON，必須寫進資料流說明（L1151）。
  - Tailscale Funnel 的 relay「無法解密」（L1124）。
  - 若 PC 裝了全系統出站代理或 VPN，照片下載也可能經過第三方，須自行確認（L1080）。
  - 雲端 APM（例如 Sentry）⚠（L1199）；OneDrive 桌面備份 ⚠（L1217–1219）；雲端翻譯、ASR、TTS ⚠（L1758）。

**E2. 「不自動訓練」「不自動上線」**
- 撤回後不自動重訓，改為標記模型、由人工排程（L846、L905、L976、L2423）。
- LINE 退化擴增「訓練一律由人工啟動」（L545）。
- 金絲雀：L1406 原文「業界的金絲雀通常會依指標**自動擴大流量**，這直接違反『不自動上線』原則 ⚠」。Google SRE 原文 "Deployments should be performed by computers, not humans"（L1438）與原則正面衝突。
- 報告允許的唯一自動化是**自動回滾**與**自動降級**為「需人工確認」（L1415、L1380）。報告也承認「『自動回滾是否可接受』：沒有找到明確討論這一點的監理文件」（L1491）。
- 預算接近上限時「自動降級為只走 postback」（L414）屬營運自動化，不涉及模型。

**E3. 「模型建議須人工確認」與「寫入前須人工確認」——張力（本筆記推論，報告沒有標 ⚠）**
- 時序圖步驟 8–9：推論正常就依結果選 T5 或 T5b，直接用 reply 送給使用者（L1979–1982）。也就是 **active 模型的分類結果會自動送到民眾手上，沒有人工先確認**；只有低信心時才走 F4「已請研究人員再看」（L1978）。報告用「不顯示分數或期別」「研究系統在照片中看到……的樣子」「每則附紅旗」來降低風險（L1683–1685），但沒有把「自動回覆模型結果」本身列為原則衝突。整合時要與其他段落對照：專案原則中的「模型建議須人工確認」是否涵蓋對民眾的自動回覆。
- 其他會自動寫入的動作：webhook 事件與 jobs、consent_events（由使用者 postback 觸發）、rich menu 自動 link 與 unlink、unsend 自動刪除照片（L955）、撤回後由背景刪除工作「在 N 小時內」刪除照片（L936，屬自動刪除，不經人工確認）、自動回滾後「要求人工確認是否維持回滾」（L1546）。另外，報告列出一個 IRB 可選的做法「封鎖 X 天未解除即視為撤回」（L957），這會變成自動撤回。
- 報告有人工確認的寫入：模型切換與晉升（L1554–1562）、push 補發（L1394「補發必須人工核准」）、聯絡曾收到錯誤結果的使用者（L1576）、方案變更（L430）、現役模型是否因撤回而下線（L938）。

**E4. 「不宣稱診斷能力」與醫材界線（和第 6 段法規／IRB 重疊）**
- L1601：「一個軟體算不算醫療器材，看的是預期用途與功能。本專案分析照片並輸出靜脈炎分期，**無法靠措辭變成『非醫材』**……法規定位要由 IRB 處理，必要時諮詢 TFDA。」
- L85：依二手法律評論，FDA CDS 指引第 1 項標準排除分析醫療影像的軟體（[E→轉述 A]）。
- 文案裡的避免用字清單（L1680）、結果卡標題「研究模型分類結果（非醫療診斷）」（L781）、F5 寫「這不是診斷」（L2316）。
- 衝突候選：如果第 6 段把本系統定位為「研究工具、非醫材」，必須和本段「措辭不改變法規定位」的說法對齊。TFDA 的 AI/ML 醫材變更管理指引本題沒有檢索（L1489）。

**E5. 法規與 IRB（第 6 段）**
- 法條更正：撤回權在《人體研究法》第 14 條第 1 項第 6 款，不在第 19 條（L15、L833–837）。**如果其他段落寫成第 19 條，應以本段為準，或兩段一起回原文核對。**
- 第 19 條第 3 項：未去連結的材料提供到境外，須書面同意、審查會通過並經主管機關核准（L837）。本筆記推論：照片暫存在 LINE（LY Corporation）伺服器，是否構成「提供境外」，報告**沒有討論**，可能是第 6 段需要處理的題目。
- 第 12 條第 2 項：電子同意的形式本身要經 IRB 核准（L869）；臺大指引要求告知傳輸可能被第三方截取（L868）。
- 去連結標準：照片「難以達到第 4 條第 3 款『永久不能以任何方式連結、比對』的標準」，報告不主張照片可去連結後保留（L947、L2419）。
- 影子模式「本身就屬於『分析個人醫學資訊』，可能需要 IRB 審查」（L1516）。
- 未成年與代理同意不開放 LINE 自助（L931）；年齡門檻「18 歲（或依 IRB 核定）」（L928）。
- 研究同意紀錄的最低保存年限：**未找到可靠證據**（L899）。
- 個資法沒有「假名化」一詞（L1023）；通過 CNS 驗證不當然排除個資法（L1017）。

**E6. 評估（和評估段落重疊）**
- 本報告計算的 Wilson CI、McNemar 配對數、kappa 區間都**假設照片彼此獨立**，實際有效樣本量更接近病人數（L1471）。
- 必須以病人為單位切分，同一病人不同日期、不同手都放同一側（L516、L1510）。
- 影子模式「兩個模型一致不代表兩個都對」（L1487）。
- 不劣界限 Δ 須由臨床人員決定（L1490）。
- normal 類只有 9 張（L89）。如果其他段落引用的類別數不同，需要對齊。

**E7. 推論延遲與 reply token 時限**
- Reply token 1 分鐘；worker 在 `now − webhook_received_at < 約 50 秒` 時才 reply（L257、L1981）；告警設在最舊 job >45 秒（L289）；loading 設 20–30 秒（L253）或 30 秒（L1970）。
- 報告對推論時間的假設：L217「推論需要好幾秒（品質檢查、YOLO、EfficientNet 或 DINOv2）」；01 號筆記說「推論只需數秒」「推論預估在 60 秒內」（筆記 L198、L208）。**報告沒有給實測延遲數字。** 如果其他段落（例如採用 DINOv2 大模型或多模型集成、TTA）讓單張推論加上排隊接近 50 秒，就會大量走 postback 退路。
- 影子模型在 reply 之後才跑，不吃 token 時間，但會佔用同一個 GPU worker 的低優先佇列（L267–269）。

**E8. 照片壓縮與模型品質（和資料／模型段落重疊）**
- LINE 標準畫質長邊約 1,478 px、高畫質約 2,364 px（[E]），醫院原檔多半更高（L77）；Laplacian 分數隨解析度改變，同一門檻不能套兩種來源（L79）；要縮到固定長邊（例如 1,024 px）再算（L541）。
- 不能下「LINE 照片表現較差」的結論（L514）；退化擴增須先做實測矩陣（L545），而且某些 JPEG 品質因子組合可能有害（L503）。
- 「JPEG 量化對 224 px 的分類器影響可能最小」（L572），本報告推論。如果其他段落採用更高解析度輸入，這個推論需要重新評估。

**E9. 其他原則對照（報告自檢表 L2856–2866，照錄）**：照片暫存在 LINE → 交 IRB 並揭露，或改走 LIFF；Cloudflare 或 ngrok 傳照片 → Funnel 或自架反代；ngrok Inspector → 不使用；雲端 APM → 本機 log；OneDrive 同步 → 改用不同步路徑；比例金絲雀、自動晉升 → 人工簽核分階段，只允許自動回滾；撤回後自動重訓 → 標記後人工排程；雲端翻譯、ASR、TTS → 預譯模板、預錄語音、本機模型；面向使用者的 A/B → 不建議。另外，外部 safetensors 一律只能以 candidate 登錄（L2868）。

**E10. 管理介面隔離（和專案設定一致）**：admin 只綁 127.0.0.1:8000、不經任何 tunnel、需要登入，webhook-svc 是另一個 FastAPI app（L1167、L1171、L1938、L1950、L2466–2467）。這與專案背景「管理 UI 綁 localhost 並與公開 LINE 服務分開」一致，沒有衝突。

### Inferences
- 最需要跨段落協調的三點是：(1) LINE 傳輸是否違反「不上傳第三方雲端」，以及是否構成第 19 條第 3 項的境外提供（第 6 段）；(2) 自動回覆模型結果是否需要人工確認（原則層級）；(3) 《人體研究法》條號（第 14 條 vs 第 19 條）。

### Gaps
- 報告沒有討論 LY Corporation 伺服器所在地，也沒有討論是否構成跨境傳輸。
- 報告沒有實測推論延遲。
- OA Manager 聊天記錄保存與原則的關係，報告沒有討論。

---

## F. 需要使用者做的決定

### Takeaway
報告結語指出三件「需要早做決定、而且之後很難改」的事（L2590–2596）：照片走 LINE 聊天還是 LIFF 直傳（IRB 層級，連帶決定對外暴露方案與介面組合，應最先送 IRB）；同意、撤回與模型治理的紀錄如何設計才經得起稽核；回覆文案能否把「研究系統」和「就醫行動」清楚分開。正文另外有很多需要人決定的參數。

### Cited Findings
1. **照片路線 A 或 B**，以及 IRB 怎麼解讀「不上傳第三方雲端」（L63、L583、L2518、L2592–2596）。
2. **對外暴露方案**：Tailscale Funnel（beta、ts.net 網域、頻寬上限不明）／自架 Caddy 或 nginx（要網域、固定 IP）／Cloudflare Tunnel（只限路線 A，須接受 Cloudflare 看得到 webhook JSON）；ngrok 不建議（L1069、L1149–1154）。
3. **逾時退路政策**：預設 postback；push 是否作為「例外且需核准」，以及核准流程（L1330、L1987–1988）。
4. **F4 的人工回覆時間承諾**（例如「上班時間 24 小時內」），必須依實際研究人力確認（L2303）。
5. **撤回後之前照片的刪除期限 N 天**、刪除工作的 N 小時（L936、L2407）；備份保留期限（L940）。
6. **封鎖政策**：「封鎖不等於撤回」，或 IRB 偏保守時的「封鎖 X 天未解除即視為撤回」（L957）。
7. **年齡門檻與代理同意**：18 歲或依 IRB；未成年與代理同意是否只走面對面（L928–931）。
8. **撤回時現役模型是否下線**（「由人員決定」，L938）；撤回後的人工重訓頻率（例如每季，L909）。
9. **可保留資料的範圍**（同意事件、彙總統計），須事先寫入同意書（L942–947）。
10. **醫院病人綁定方式**：一次性登錄碼（報告建議）而不是 Account Link 或病人登入頁；登錄碼有效期 24–72 小時（L1040–1044）。
11. **channel access token 類型**：v2.1（例如 7 天）或 stateless JWT 版；signing key 輪替週期 6–12 個月（L1180–1181）。
12. **per-userId 每日照片上限**（例如 10 張，L1208）。
13. **研究資料的存放路徑**：移出 OneDrive 範圍，例如 `C:\PhlebitisData\`，並實際檢查 OneDrive 桌面備份是否開啟（L1219）。
14. **OA 方案**：維持「輕用量」，改方案須研究主持人核准（L430、L2499）。
15. **現在是否換 active 模型**：只能基於工程或治理理由，並寫明沒有統計證據（L1503）。
16. **不劣界限 Δ** 與影子轉上線門檻的數值（配對數、時間長度），由臨床人員與負責人預先註冊（L1490、L1554–1562）。
17. **是否重新聯絡曾收到錯誤結果的使用者**（人工決定，須寫入 IRB 計畫書，L1576）。
18. **自動回滾觸發門檻的 X%**、錯誤率與逾時率門檻（L1541–1544）。
19. **語言範圍**：等合作醫院確認受試者語言需求後，再決定是否做印尼文、越南文、英文與台語語音（L1819–1821）。
20. **紅旗清單內容與「紅線往上延伸、寒顫」等項目**，由臨床護理專家審定；向合作醫院護理部索取正式衛教單（L1656–1657、L2347）。
21. **品質檢查的「拒絕」模式**是否啟用（時序圖 L1976 寫「不合格（『拒絕』模式）」）。
22. **IRB 送審的同意書內容**，包括影子分析的揭露（L1516、L2511）。
23. **是否做 LIFF**：只有在 IRB 不允許照片經過 LINE 時「現在」做簡化版，否則延後（L755、L1915）。
24. **一般民眾（`P-` 前綴）是否也收案**（L1028 提到這種前綴，但沒有說明收案範圍）。

### Inferences
- 第 1、2、22 項必須先決定，因為它們決定架構、同意書與 IRB 送審；其他多數是可以在 IRB 核准前預設、之後再調整的參數。

### Gaps
- 報告沒有給這些決定的建議預設值的地方：N 天、X 天、X%、Δ、配對數門檻、F4 等待時間。

---

## G. 不確定或時效性高的結論

### Takeaway
時效性最高的是：台灣調價（**2026-11-01 已在今天生效**）、台灣維護時段（今天 2026-11-01 仍在 2026-10-28 08:00 至 2026-11-02 的時段內）、LIFF 舊版限制（約 2026-11-24）。不確定性最高的是：2 秒 webhook 逾時、Get content 保存期與大小上限、EXIF 處理、LINE 傳圖到 Bot 的實際像素，以及所有在 14 位個案下的模型結論。

### Cited Findings

**時效性**
- 報告撰寫時寫「自 2026-11-01（明天）起」（L13）；今天 2026-11-01 新價已生效。2026-10-27 之後仍使用中、高用量即視為同意新價（L323）。
- 維護時段：2026-10-28 08:00 至 2026-11-02，以及 2026-11-24 08:00 至 2026-11-25（L325、L415）。
- LIFF v2.20.0–v2.31.0 預定 "around November 24, 2026" 限制使用；最新 v2.31.2（2026-10-07）（L666–668）。
- LIFF 整合進 MINI App 沒有完成日期（L713）。
- Reply token 時限、重送行為「可能不經通知變更」（L153、L167）；舊 cipher「可能在近期無預警停用」（L1113）。
- Tailscale Funnel 仍是 beta（L1123）。
- FDA CDS 指引 2026-01-06 修訂（L1624）；PCCP 日期有衝突（L1427）。
- 傳圖畫質實測可能隨 App 版本改變（L1899）。

**不確定（報告保留「未找到可靠證據」或「需確認」的項目）**
- `request_timeout`「約 2 秒」只來自頁面摘要（L69、L148、L2016）。
- Get content 保存天數與檔案大小上限、EXIF 處理、內建相機是否套用濾鏡（L2831–2833）。
- Bot 透過 Get content 收到的像素是否等於傳送端選的畫質：沒有公開實測（L474）；Android 各品牌數據：未找到（L505）。
- LIFF、LINE MINI App、LINE Login 是否收費；loading animation 是否計費（推論不計費）（L389–390、L2834）。
- LINE 是否禁止 OA 收集健康資料（L893、L2835）。
- 重送事件中 reply token 不可用的具體情況（L169、L2836）。
- 台灣研究同意紀錄的最低保存年限（L899、L2837）。
- 單次 webhook 最多幾個事件、429 是否帶 `Retry-After`（L213、L1310）。
- 2023 年調價的確切生效日只有 [E]（L384）。
- 5% 營業稅未經查證（L391）。
- 狀態頁內容來自搜尋摘要（L1305）。
- Cloudflare edge 解密沒有官方明文（L1120）；ngrok full capture 是否預設開啟（L1121）。
- secret 重發後是否立即失效（L1138）；LINE 是否允許多把公鑰（L1181）。
- userId 何時改變（L1022）。
- 紅旗清單部分項目沒有 [A] 核對（L1656）。
- `tel:119` 在 LINE 裡的行為需要實機測試（L2387）。
- LIFF 中 `capture` 與 file input 的行為只有 [E] 實務回報（L685–686、L737）。

**在 14 位個案下不可靠的結論**（L2884–2893，照錄）：LINE 照片與醫院照片的表現差異；候選模型「較好」或「不劣」（normal 類只有 9 張，CI 寬約 0.42）；品質門檻是否恰當；「LINE 退化擴增」是否有效；任何子群比較；撤回一人對模型的影響是否可忽略（約 7% 受試者，不能忽略）。這些都要等到約 1,000 張、三類平衡、以病人為單位切分、兩位以上標註者之後才能回答。現有規模下可靠的只有工程驗證：簽章、去重、時限、log 遮罩、回滾演練。

### Inferences
- 整合報告若在 2026-11-01 之後發表，應把「明天調價」改寫成「已於 2026-11-01 生效」；並在約 2026-11-24 前確認 LIFF 版本（如果採路線 B）。

### Gaps
- 本筆記沒有重新查證任何 LINE 頁面（見開頭的 NEW 說明），所以上述「需逐字確認」項目仍然待確認。

---

## H. 名詞對照表（照錄 L2526–2585）

| 中文 | 英文 | 說明 |
|---|---|---|
| 官方帳號 | LINE Official Account（LINE OA） | 商家或機構帳號 |
| 訊息 API | Messaging API | Bot 收發訊息的介面 |
| 網路掛鉤 | Webhook | LINE 主動 POST 事件到 bot 伺服器 |
| 簽章驗證 | Signature validation（X-Line-Signature） | HMAC-SHA256 |
| 重送 | Webhook redelivery | 預設關閉 |
| 事件識別碼 | webhookEventId | ULID 格式，用來去重 |
| 回覆權杖 | Reply token | 只能用一次，1 分鐘內有效 |
| 回覆／推播 | Reply／Push message | Reply 不計費，Push 計費 |
| 群發／分眾 | Broadcast／Narrowcast／Multicast | 計費 |
| 讀取動畫 | Loading animation（loading indicator） | 5–60 秒 |
| 重試鍵 | Retry key（X-Line-Retry-Key） | 24 小時內保證冪等 |
| 冪等 | Idempotency | 重複執行結果相同 |
| 取得內容 | Get content | 下載使用者傳的二進位檔 |
| 內容來源 | contentProvider | line／external |
| 圖文選單 | Rich menu | 聊天室下方的選單 |
| 選單別名 | Rich menu alias | 用於切換分頁 |
| 彈性訊息 | Flex Message | 可自訂版面的卡片 |
| 替代文字 | altText | 通知列與無障礙朗讀使用的文字 |
| 快速回覆 | Quick reply | 訊息下方的按鈕列 |
| 回傳動作 | Postback action | 按鈕點擊後回傳資料，並附新的 reply token |
| LINE 前端框架 | LIFF（LINE Front-end Framework） | 在 LINE 內開啟網頁 |
| LINE 迷你應用 | LINE MINI App | 預定與 LIFF 整合 |
| LINE 登入 | LINE Login（OpenID Connect） | 取得 ID token |
| 身分權杖 | ID token（JWT） | 有效 1 小時 |
| 帳號連結 | Account Link | link token 加 nonce |
| 提供者 | Provider | userId 的發放範圍 |
| 頻道存取權杖 | Channel access token（v2.1／stateless／short-lived／long-lived） | — |
| 頻道密鑰 | Channel secret | 用於驗簽 |
| 斷言簽章金鑰 | Assertion signing key | RSA 2048，用於 JWT |
| 反向代理 | Reverse proxy | Caddy、nginx |
| 通道服務 | Tunnel（Cloudflare Tunnel、ngrok、Tailscale Funnel） | 對外暴露方式 |
| TLS 終止 | TLS termination | 在哪裡解密 |
| 速率限制 | Rate limit | 超過時回 429 |
| 死信 | Dead-letter | 多次失敗的工作 |
| 影子模式 | Shadow mode／silent trial | 只記錄，不回覆 |
| 金絲雀發布 | Canary release | 部分、限時部署 |
| A/B 測試 | A/B test | 隨機分派 |
| 回滾 | Rollback | 回到上一個版本 |
| 預先定義變更控制計畫 | PCCP（Predetermined Change Control Plan） | FDA 指引 |
| 良好機器學習實務 | GMLP（Good Machine Learning Practice） | IMDRF N88 |
| 資料集漂移 | Dataset shift／data drift | — |
| 族群穩定指數 | PSI（Population Stability Index） | 啟發式指標 |
| 電子知情同意 | eConsent | — |
| 回授法 | Teach-back | 確認使用者是否理解 |
| 化名化 | Pseudonymization | 仍屬個人資料 |
| 去連結 | Delinking（人體研究法第 4 條第 3 款） | 永久不能連結 |
| 機器遺忘 | Machine unlearning | — |
| 自動化偏誤 | Automation bias | 過度依賴系統 |
| 健康識能 | Health literacy | — |
| 清晰溝通指標 | CDC Clear Communication Index（CCI） | 90 分以上為通過 |
| 靜脈炎量表 | VIP（Visual Infusion Phlebitis）scale | 0–5 分 |
| 觸控目標尺寸 | Target size（WCAG 2.5.8） | 至少 24×24 CSS px |
| 語音辨識 | ASR（Automatic Speech Recognition） | — |
| 語音合成 | TTS（Text-to-Speech） | — |
| 解壓縮炸彈 | Decompression bomb | Pillow 的防護機制 |
| 伺服器端請求偽造 | SSRF（Server-Side Request Forgery） | — |
| 網域失配 | Domain shift | 訓練資料與實際使用資料的分布不同 |
| 白平衡 | White balance（WB） | — |

正文中出現、但不在對照表的術語（補充，本筆記整理）：金絲雀（canary）；loading animation；去重；品質因子（QF）；邊緣節點（edge）；「需人工確認」；審閱者端金絲雀；small cell suppression（小格數抑制）；外部錨定；一次性登錄碼（enrollment code）；exclusion list；model registry（模型登錄表）；silent trial；Wilson 信賴區間；McNemar 檢定；三法則；leave-source-out 驗證；Test-time augmentation（TTA）；WB emulation；store-and-forward 遠距皮膚科；certified provider；未認證 MINI App；Error statistics aggregation；Traffic Inspector；DPAPI；Windows Credential Manager。

---

## I. 參考文獻（照錄 L2604–2809，依報告分組）

依來源等級分組。查閱日期都在 2026-10-30 至 2026-10-31 之間。LINE Developers 的文件頁都沒有標示更新日，作者一律記為 LY Corporation（LINE Developers）。

### [A] 官方文件、主管機關、標準與報告規範

**LINE Developers：Messaging API 與 Webhook**
- LY Corporation. Receiving messages (webhook). LINE Developers. https://developers.line.biz/en/docs/messaging-api/receiving-messages/ （頁面未標更新日；查閱 2026-10-31）
- LY Corporation. Verify webhook signature. https://developers.line.biz/en/docs/messaging-api/verify-webhook-signature/ （頁面未標更新日；查閱 2026-10-31）
- LY Corporation. Display a loading animation. https://developers.line.biz/en/docs/messaging-api/use-loading-indicator/ （頁面未標更新日；查閱 2026-10-31）
- LY Corporation. Development guidelines. https://developers.line.biz/en/docs/messaging-api/development-guidelines/ （頁面未標更新日；查閱 2026-10-31）
- LY Corporation. Retrying an API request. https://developers.line.biz/en/docs/messaging-api/retrying-api-request/ （頁面未標更新日；查閱 2026-10-31）
- LY Corporation. Check webhook error statistics. https://developers.line.biz/en/docs/messaging-api/check-webhook-error-statistics/ （頁面未標更新日；查閱 2026-10-31）
- LY Corporation. Error notification. https://developers.line.biz/en/docs/partner-docs/error-notification/ （頁面未標更新日；查閱 2026-10-31）
- LY Corporation. Messaging API reference（含 Markdown 版 index.html.md）. https://developers.line.biz/en/reference/messaging-api/ ；https://developers.line.biz/en/reference/messaging-api/index.html.md （頁面未標更新日；查閱 2026-10-30／31）
- LY Corporation. LINE API Status. https://developers.line.biz/en/docs/basics/line-api-status/ ；https://api.line-status.info/ （頁面未標更新日；查閱 2026-10-31）
- LY Corporation. Messaging API pricing. https://developers.line.biz/en/docs/messaging-api/pricing/ （頁面未標更新日；查閱 2026-10-30）
- LY Corporation. Send messages. https://developers.line.biz/en/docs/messaging-api/sending-messages （頁面未標更新日；查閱 2026-10-31）
- LY Corporation. SSL/TLS specification of the webhook source. https://developers.line.biz/en/docs/messaging-api/ssl-tls-spec-of-the-webhook-source/ （頁面未標更新日；查閱 2026-10-31）
- LY Corporation. Build a bot. https://developers.line.biz/en/docs/messaging-api/building-bot/ （頁面未標更新日；查閱 2026-10-31）

**LINE Developers：使用者介面元件**
- LY Corporation. Rich menus overview. https://developers.line.biz/en/docs/messaging-api/rich-menus-overview/ ；Use per-user rich menus. https://developers.line.biz/en/docs/messaging-api/use-per-user-rich-menus/ ；Switch between tabs on rich menus. https://developers.line.biz/en/docs/messaging-api/switch-rich-menus/ （頁面未標更新日；查閱 2026-10-31）
- LY Corporation. Send Flex Messages. https://developers.line.biz/en/docs/messaging-api/using-flex-messages/ ；Flex Message layout. https://developers.line.biz/en/docs/messaging-api/flex-message-layout/ （頁面未標更新日；查閱 2026-10-31）
- LY Corporation. Use quick replies. https://developers.line.biz/en/docs/messaging-api/using-quick-reply/ （頁面未標更新日；查閱 2026-10-30／31）

**LINE Developers：LIFF 與 LINE MINI App**
- LY Corporation. LIFF release notes. https://developers.line.biz/en/docs/liff/release-notes/ （各版本條目有日期，最新為 v2.31.2，2026-10-07；查閱 2026-10-30／31）
- LY Corporation. Adding a LIFF app to your channel. https://developers.line.biz/en/docs/liff/registering-liff-apps/ ；LIFF overview. https://developers.line.biz/en/docs/liff/overview/ ；Differences between the LIFF browser and external browser. https://developers.line.biz/en/docs/liff/differences-between-liff-browser-and-external-browser/ ；LIFF API reference. https://developers.line.biz/en/reference/liff/ ；Using user data in LIFF apps and servers. https://developers.line.biz/en/docs/liff/using-user-profile/ （頁面未標更新日；查閱 2026-10-30／31）
- LY Corporation. Introducing LINE MINI App. https://developers.line.biz/en/docs/line-mini-app/discover/introduction/ ；Submitting LINE MINI App. https://developers.line.biz/en/docs/line-mini-app/submit/submission-guide/ ；LINE MINI App specifications. https://developers.line.biz/en/docs/line-mini-app/discover/specifications/ ；Console guide. https://developers.line.biz/en/docs/line-mini-app/discover/console-guide/ （頁面未標更新日；查閱 2026-10-31）

**LINE Developers：身分、使用者資料與帳號連結**
- LY Corporation. Get user IDs. https://developers.line.biz/en/docs/messaging-api/getting-user-ids/ ；Linking user accounts. https://developers.line.biz/en/docs/messaging-api/linking-accounts/ ；Consent on getting user profile information. https://developers.line.biz/en/docs/messaging-api/user-consent/ （頁面未標更新日；查閱 2026-10-30／31）
- LY Corporation. LINE Login v2.1 API reference. https://developers.line.biz/en/reference/line-login/ ；Integrating LINE Login with your web app. https://developers.line.biz/en/docs/line-login/integrate-line-login/index.html.md （頁面未標更新日；查閱 2026-10-31）

**LINE Developers：Channel access token**
- LY Corporation. Channel access token. https://developers.line.biz/en/docs/basics/channel-access-token/ ；Issue channel access token v2.1. https://developers.line.biz/en/docs/messaging-api/generate-json-web-token/ （頁面未標更新日；查閱 2026-10-31）
- LY Corporation. Points to check when using the Messaging API from multiple tools with a single LINE Official Account（Tips）. 2026-07-23. https://developers.line.biz/en/tips/2026/07/23/using-multiple-api-tools/ （查閱 2026-10-31）
- LY Corporation. line-openapi: channel-access-token.yml（main 分支）. https://raw.githubusercontent.com/line/line-openapi/main/channel-access-token.yml （未標日期；查閱 2026-10-31）

**LINE Developers：News 公告**
- LY Corporation. News ja/38：Webhook 再送機能（2022-03-07 公告；日期取自搜尋摘要）. https://developers.line.biz/ja/news/38/
- LY Corporation. News 2024-04-17：loading animation. https://developers.line.biz/en/news/2024/04/17/loading-indicator/
- LY Corporation. News（Messaging API 標籤；api-data 網域變更，2019-11-08）. https://developers.line.biz/en/news/tags/messaging-api
- LY Corporation. News 2025-02-12（LINE MINI App 與 LIFF 整合）. https://developers.line.biz/en/news/2025/02/12/line-mini-app/ ；News 2025-09-26（MINI App 網頁瀏覽器）. https://developers.line.biz/en/news/2025/09/26/mini-app-browser/
- LY Corporation. News 2026-09-30（LIFF v2.31.1）. https://developers.line.biz/en/news/2026/09/30/release-liff-2-31-1/ ；News 2026-10-20（LIFF SDK vulnerability）. https://developers.line.biz/en/news/2026/10/20/liff-sdk-issue/ （兩頁需 JS 渲染，未讀到全文）

**LINE 說明中心與條款**
- LY Corporation. LINE Help：Creating/editing albums. https://help.line.me/line/smartphone/sp?contentId=20000248&lang=en ；Photos/videos help. https://help.line.me/line/smartphone/sp?contentId=20000236&lang=en （搜尋摘要；查閱 2026-10-31）
- LY Corporation. LINE Developers Terms and policies. https://developers.line.biz/en/terms-and-policies/ ；LINE communication privacy. https://terms.line.me/line_communication_privacy?lang=en （查閱 2026-10-31）

**LINE Biz-Solutions 台灣**
- LINE Biz-Solutions 台灣. LINE 官方帳號服務與費用說明頁（S1；頁面資源版本 2026-09-24）. https://tw.linebiz.com/service/account-solutions/line-official-account/ （查閱 2026-10-30）
- LINE Biz-Solutions 台灣. 2026年 LINE 官方帳號方案價格調整（S2）. 2026-09-01. https://tw.linebiz.com/column/LINEOA-2026-Price-Plan/ （查閱 2026-10-30）
- LINE Biz-Solutions 台灣. FAQ：訊息費用的計價方式？（S3）. https://tw.linebiz.com/faq/oa-price/message-price-list/ ；FAQ：收費訊息如何計算？（S4）. https://tw.linebiz.com/faq/oa-price/how-to-calculate-message-expense/ （無日期；查閱 2026-10-30）
- LINE Biz-Solutions 台灣. 費用計算機程式 cal.js（S5；版本路徑 2026-09-24）. https://vos.line-scdn.net/lbstw-static/assets/frontend/js-20260924-modified/cal.js （查閱 2026-10-31）
- LINE Biz-Solutions 台灣. LINE MINI App. https://tw.linebiz.com/service/other-solutions/line-mini-app/ （查閱 2026-10-31）

**台灣法規、主管機關與機構文件**
- 全國法規資料庫. 人體研究法（最新修正 民國 108-01-02）. https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=L0020176 ；第 19 條. https://law.moj.gov.tw/LawClass/LawSingle.aspx?pcode=L0020176&flno=19 （查閱 2026-10-31）
- 臺大醫院研究倫理委員會. 網路研究倫理審查指引（2020-09）；AF-143-02 網路研究自評表. https://www.ntuh.gov.tw/ （完整網址見第 5 節；經搜尋摘要；查閱 2026-10-31）〔第 5 節完整網址：https://www.ntuh.gov.tw/ckfinder_file/RECO/files/02.%E6%A8%99%E6%BA%96%E4%BD%9C%E6%A5%AD%E6%B5%81%E7%A8%8B/%E5%8F%B0%E5%A4%A7%E9%86%AB%E9%99%A2%E7%B6%B2%E8%B7%AF%E7%A0%94%E7%A9%B6%E5%80%AB%E7%90%86%E5%AF%A9%E6%9F%A5%E6%8C%87%E5%BC%95202009.pdf〕
- 行政院. 個資去識別化驗證（CNS 29100／29191）新聞稿（民國 104 年）. https://www.ey.gov.tw/Page/9277F759E41CCD91/af28eb4c-7030-49bb-889d-f0a0fed6a4d5 （查閱 2026-10-31）
- 國家發展委員會函釋（民國 108 年）. 臺北市法規查詢系統 FE372646. https://laws.gov.taipei/Law/Interpretation/Content/FE372646 （查閱 2026-10-31）
- 衛生福利部. 1922 防疫專線. https://www.mohw.gov.tw/cp-88-218-1.html （查閱 2026-10-30）
- 教育部. 臺灣台語羅馬字拼音方案使用手冊（113-08-26 修正）. https://language.moe.gov.tw/files/people_files/tshiutsheh_1130826.pdf （查閱 2026-10-30）
- 勞動部. 外籍工作者統計（112 年底）. https://www.mol.gov.tw/media/aklhtid2/12-外籍工作者.pdf （僅搜尋摘要；查閱 2026-10-30）
- 食品藥物管理署. 醫用軟體分類分級參考指引（第三方轉載副本）. https://mdcpp.com/doc/materialDownload/ （完整網址見第 10 節；未從 fda.gov.tw 核對；查閱 2026-10-30）〔第 10 節完整網址：https://mdcpp.com/doc/materialDownload/%E5%8F%B0%E6%B9%BE-%E5%8C%BB%E7%96%97%E8%BD%AF%E4%BB%B6%E5%88%86%E7%B1%BB%E5%92%8C%E5%88%86%E7%BA%A7%E5%8F%82%E8%80%83%E6%8C%87%E5%8D%97.pdf〕
- 國家衛生研究院論壇. 我國高齡長者健康識能之決定因子與其健康結果（[A/C]）. https://forum.nhri.edu.tw/ （完整網址見第 10 節；僅搜尋摘要；查閱 2026-10-30）〔第 10 節完整網址：https://forum.nhri.edu.tw/wp-content/uploads/108-4.%E6%88%91%E5%9C%8B%E9%AB%98%E9%BD%A1%E9%95%B7%E8%80%85%E5%81%A5%E5%BA%B7%E8%AD%98%E8%83%BD%E4%B9%8B%E6%B1%BA%E5%AE%9A%E5%9B%A0%E5%AD%90%E8%88%87%E5%85%B6%E5%81%A5%E5%BA%B7%E7%B5%90%E6%9E%9C-%E5%96%AE%E9%A0%81%E6%AA%A2%E8%A6%96.pdf〕
- 國民健康署 2021 國民健康訪問調查（經新聞轉述）：聯合新聞網. https://udn.com/news/story/7266/9827044 （查閱 2026-10-30）
- 財團法人台灣網路資訊中心（TWNIC）. 2025 台灣網路報告. 2025. https://report.twnic.tw/2025/en/assets/download/TWNIC_TaiwanInternetReport_2025_CH_all.pdf （查閱 2026-10-30）
- 數位發展部數位產業署. Taiwan Tongues ASR CE（[A/E]）. https://github.com/adi-gov-tw/Taiwan-Tongues-ASR-CE （查閱 2026-10-30）

**國際主管機關、標準與報告規範**
- U.S. FDA & HHS OHRP. Use of Electronic Informed Consent in Clinical Investigations: Questions and Answers（Final）. 2016-12. https://www.fda.gov/regulatory-information/search-fda-guidance-documents/use-electronic-informed-consent-clinical-investigations-questions-and-answers （查閱 2026-10-31）
- U.S. FDA. Good Machine Learning Practice for Medical Device Development: Guiding Principles（頁面 2025-12-19 更新）. https://www.fda.gov/medical-devices/artificial-intelligence-enabled-medical-devices/good-machine-learning-practice-medical-device-development-guiding-principles ；IMDRF/AIML WG/N88 FINAL:2025. https://imdrf.org/sites/default/files/2025-02/IMDRF_AIML%20WG_GMLP_N88%20Final.pdf （查閱 2026-10-30）
- U.S. FDA. Marketing Submission Recommendations for a Predetermined Change Control Plan for AI-Enabled Device Software Functions（2024-12 定稿；頁面現列 2025-08）. https://www.fda.gov/regulatory-information/search-fda-guidance-documents/marketing-submission-recommendations-predetermined-change-control-plan-artificial-intelligence （查閱 2026-10-30）
- WHO. Ethics and governance of AI for health: Guidance on large multi-modal models. 2024-01-18. https://www.who.int/publications-detail-redirect/9789240084759 （查閱 2026-10-30）
- Vasey B, et al. DECIDE-AI reporting guideline. Nat Med 2022;28(5):924–933. DOI 10.1038/s41591-022-01772-9. https://ora.ox.ac.uk/objects/uuid:f3d4d76c-cfc7-40dc-a5c3-4f3a460c5901 （查閱 2026-10-30）
- OWASP. Logging Cheat Sheet. https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html （頁面未標更新日；查閱 2026-10-31）
- W3C. Understanding SC 2.5.8 Target Size (Minimum), WCAG 2.2. https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html （查閱 2026-10-30）
- AHRQ. Health Literacy Universal Precautions Toolkit, 3rd ed.（Pub. No. 23-0075）. 2024-03-01. https://www.ahrq.gov/health-literacy/improve/precautions/toolkit.html （查閱 2026-10-30）
- CDC. Clear Communication Index FAQ／User Guide. https://www.cdc.gov/ccindex/tool/faq.html （查閱 2026-10-30）

**廠商官方文件**
- Cloudflare. Connect networks（Cloudflare Tunnel）. 2026-08-04. https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/ （查閱 2026-10-31）
- ngrok. Traffic Inspection. https://ngrok.com/docs/obs/traffic-inspection/ （頁面未標日期；查閱 2026-10-31）
- Tailscale. Tailscale Funnel. Last validated 2026-01-20. https://tailscale.com/kb/1223/funnel （查閱 2026-10-31）
- Pillow. PIL.Image（Pillow 13.0.0）. https://pillow.readthedocs.io/en/stable/reference/Image.html （查閱 2026-10-31）
- LINE @line/bot-sdk 11.0.0 型別定義（userProfileResponse）. https://unpkg.com/@line/bot-sdk@11.0.0/dist/messaging-api/model/userProfileResponse.d.ts （查閱 2026-10-30）

**臨床衛教、量表、共識與試驗登錄**
- NHS Lothian. Discharge home with cannula in situ（v2.0）. 2020-02. https://policyonline.nhslothian.scot/wp-content/uploads/2023/03/Discharge_home_with_Cannula_in_situ.pdf （查閱 2026-10-30）
- East and North Hertfordshire NHS Trust. Blood Transfusion Aftercare advice（V4）. 2025-03. https://www.enherts-tr.nhs.uk/wp-content/uploads/2019/10/Blood-Transfusion-Aftercare-advice-for-patients-V4-03.2025.pdf （僅搜尋摘要；查閱 2026-10-30）
- York Hospitals NHS. Cannula leaflet. https://yorkhospitals.nhs.uk/seecmsfile/?id=2747 ；Northampton General. Caring for my cannula. https://www.northamptongeneral.nhs.uk/Publications/Leaflets/IPC/Caring-for-my-cannula.aspx （僅搜尋摘要；查閱 2026-10-30）
- Jackson A. Visual Infusion Phlebitis（VIP）Score（[A/業界]）. Solventum. https://assets.solventum.com/is/content/mmmspinco/VIP-Scorecard-for-VHP-websitepdf ；ivteam. https://ivteam.com/vipsn.pdf （查閱 2026-10-30）
- British Association of Dermatologists. Teledermatology（病人衛教，2025-04）. https://www.skinhealthinfo.org.uk/condition/teledermatology （查閱 2026-10-31）
- ISIC Delphi consensus. JAMA Dermatol 2017;153(2):207–213. DOI 10.1001/jamadermatol.2016.3949. https://pubmed.ncbi.nlm.nih.gov/27892996/ （[A/C]；僅讀摘要；查閱 2026-10-31）
- ClinicalTrials.gov. NCT07889895. https://clinicaltrials.gov/study/NCT07889895 （僅登錄資料；查閱 2026-10-31）

### [B] 系統性回顧、統合分析、頂尖期刊或會議
- Cohen E, et al. Comparative Effectiveness of eConsent: Systematic Review. J Med Internet Res 2023;e43883. https://jmir.org/2023/1/e43883/PDF （查閱 2026-10-31）
- Xu H, Zhu T, Zhang L, Zhou W, Yu PS. Machine Unlearning: A Survey. ACM Comput Surv 2023;56(1):Art 9. DOI 10.1145/3603620. https://opus.lib.uts.edu.au/handle/10453/176647 （查閱 2026-10-31）
- Afifi M, Brown MS. What Else Can Fool Deep Learning? Addressing Color Constancy Errors on Deep Neural Network Performance. ICCV 2019. https://openaccess.thecvf.com/content_ICCV_2019/html/Afifi_What_Else_Can_Fool_Deep_Learning_Addressing_Color_Constancy_Errors_ICCV_2019_paper.html （查閱 2026-10-31）
- Tikhomirov L, Semmler C, Prizant, et al. A scoping review of silent trials for medical artificial intelligence. Nature Health 2026. DOI 10.1038/s44360-025-00048-z（只讀到二手摘要）. https://adelaide.edu.au/about/news/2026/calls-for-global-guidelines-for-safer-ai-use-in-medicine--/ （查閱 2026-10-30）
- Meyer MN, Heck PR, Holtzman GS, et al. Objecting to experiments that compare two unobjectionable policies or treatments. PNAS 2019;116(22):10723–10728. DOI 10.1073/pnas.1820701116. https://pmc.ncbi.nlm.nih.gov/articles/PMC6561206 （查閱 2026-10-30）
- Riley RD, et al. Evaluation of clinical prediction models (part 3): calculating the sample size required for an external validation study. BMJ 2024;384:e074821. DOI 10.1136/bmj-2023-074821. https://pmc.ncbi.nlm.nih.gov/articles/PMC11778934/ （查閱 2026-10-30）
- Wong A, et al. External Validation of a Widely Implemented Proprietary Sepsis Prediction Model. JAMA Intern Med 2021. DOI 10.1001/jamainternmed.2021.2626. https://jamanetwork.com/journals/jamainternalmedicine/fullarticle/2781313 （原文未開啟；查閱 2026-10-30）
- Freeman K, et al. Algorithm based smartphone apps to assess risk of skin cancer in adults: systematic review. BMJ 2020;368:m127. DOI 10.1136/bmj.m127. https://pubmed.ncbi.nlm.nih.gov/32041693/ （查閱 2026-10-30）
- Semigran HL, Linder JA, Gidengil C, Mehrotra A. Evaluation of symptom checkers for self diagnosis and triage: audit study. BMJ 2015;351:h3480. https://www.bmj.com/node/900623 （查閱 2026-10-30）
- Andreadis K, et al. Imprecision and preferences in interpretation of verbal probabilities in health: a systematic review. J Gen Intern Med 2021. DOI 10.1007/s11606-021-07050-7. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8642516/ （查閱 2026-10-30）
- van der Bles AM, van der Linden S, Freeman ALJ, Spiegelhalter DJ. The effects of communicating uncertainty on public trust in facts and numbers. PNAS 2020;117(14):7672–7683. DOI 10.1073/pnas.1913678117. https://sciencedaily.com/releases/2020/03/200323152106.htm （查閱 2026-10-30）
- Zipkin DA, et al. Evidence-based risk communication: a systematic review. Ann Intern Med 2014;161(4):270–280. https://pubmed.ncbi.nlm.nih.gov/25133362/ （查閱 2026-10-30）
- Milne-Ives M, et al. The Effectiveness of AI Conversational Agents in Health Care: Systematic Review. J Med Internet Res 2020;22(10):e20346. DOI 10.2196/20346. https://jmir.org/2020/10/e20346/PDF （查閱 2026-10-30）
- Singh B, et al. Systematic review and meta-analysis of the effectiveness of chatbots on lifestyle behaviours. npj Digit Med 2023;6:118. DOI 10.1038/s41746-023-00856-1. https://www.nature.com/articles/s41746-023-00856-1.pdf （查閱 2026-10-30）
- Design Guidelines of Mobile Apps for Older Adults: Systematic Review. JMIR mHealth uHealth 2023. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10557006/ （僅搜尋摘要；查閱 2026-10-30）

### [C] 一般同儕審查論文
- Young AT, et al. Stress testing reveals gaps in clinic readiness of image-based diagnostic artificial intelligence models. npj Digit Med 2021;4:10. DOI 10.1038/s41746-020-00380-6. https://pmc.ncbi.nlm.nih.gov/articles/PMC7820258/ （查閱 2026-10-31；**文中未說明是否以病人為單位切分**）
- Dodge S, Karam L. Understanding how image quality affects deep neural networks. QoMEX 2016（arXiv:1604.04004）. https://arxiv.org/abs/1604.04004 （查閱 2026-10-31）
- 數位病理影像壓縮對 CNN 的影響（壓縮比 24:1 以內穩健）. https://pmc.ncbi.nlm.nih.gov/articles/PMC7113072/ （查閱 2026-10-31）
- Deep learning on lossily compressed pathology images: adverse effects（MICCAI 2022 workshop）. https://portal.fis.tum.de/en/publications/deep-learning-on-lossily-compressed-pathology-images-adverse-effe/ （僅搜尋摘要；查閱 2026-10-31）
- Quality and perceived usefulness of patient-submitted store-and-forward teledermatology images（JAMA Dermatol 2022）. https://escholarship.org/content/qt1vs9c5n5/qt1vs9c5n5.pdf ；JMIR Dermatol 2022;e37517. https://derma.jmir.org/2022/3/e37517/ （僅摘要；查閱 2026-10-31）
- Kwong JCC, et al. The silent trial – the bridge between bench-to-bedside clinical AI applications. Front Digit Health 2022;4:929508. DOI 10.3389/fdgth.2022.929508. https://www.frontiersin.org/articles/10.3389/fdgth.2022.929508/full （查閱 2026-10-30）
- Breck E, et al. The ML Test Score: A Rubric for ML Production Readiness. IEEE Big Data 2017. https://research.google/pubs/pub46555/ （查閱 2026-10-30）
- Finlayson SG, Subbaswamy A, et al. The Clinician and Dataset Shift in Artificial Intelligence. NEJM 2021;385(3):283–286. DOI 10.1056/NEJMc2104626. https://www.pubmed.gov/34260843/ （查閱 2026-10-30）
- Beede E, et al. A Human-Centered Evaluation of a Deep Learning System Deployed in Clinics for the Detection of Diabetic Retinopathy. CHI 2020. DOI 10.1145/3313831.3376718. https://research.google/pubs/a-human-centered-evaluation-of-a-deep-learning-system-deployed-in-clinics-for-the-detection-of-diabetic-retinopathy/ （查閱 2026-10-30）
- Kramer ADI, Guillory JE, Hancock JT. Experimental evidence of massive-scale emotional contagion through social networks. PNAS 2014;111(24):8788–8790（含 Editorial Expression of Concern）. https://pmc.ncbi.nlm.nih.gov/articles/PMC4115552 （查閱 2026-10-30）
- O'Connor DM, et al. JAMA Dermatol 2017;153(12):1243–1248. DOI 10.1001/jamadermatol.2017.4280. https://pubmed.ncbi.nlm.nih.gov/29141082/ （查閱 2026-10-31）
- Liu et al. Patient photographs taken without instructions are of sufficient quality for clinical decision-making in teledermatology. Dermatol Online J 2024;30(3). DOI 10.5070/D330363877. https://pubmed.ncbi.nlm.nih.gov/39090050/ （查閱 2026-10-31）
- Saade et al. Int J Telemed Appl 2025:5789165. DOI 10.1155/ijta/5789165. https://pubmed.ncbi.nlm.nih.gov/41041428/ （查閱 2026-10-31）
- Macefield et al. J Tissue Viability 2023;32(1):94–101. DOI 10.1016/j.jtv.2023.01.001. https://pubmed.ncbi.nlm.nih.gov/36681617/ （查閱 2026-10-31）
- Gunter et al. JMIR mHealth uHealth 2016;4(3):e113. DOI 10.2196/mhealth.6023. https://pubmed.ncbi.nlm.nih.gov/27683059/ （查閱 2026-10-31）
- Vodrahalli et al. TrueImage 2.0. JAMA Dermatol 2023;159(5):496–503. DOI 10.1001/jamadermatol.2023.0091. https://pubmed.ncbi.nlm.nih.gov/36920380/ （查閱 2026-10-31）
- Zhang et al. JMIR mHealth uHealth 2021;9(7):e26149. DOI 10.2196/26149. https://pubmed.ncbi.nlm.nih.gov/34328440/ （作者有專利利益衝突；查閱 2026-10-31）
- Denecke K, Gabarron E. Front Artif Intell 2026;9. DOI 10.3389/frai.2026.1785085. https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2026.1785085/full （查閱 2026-10-30）
- JMIR 2025;e66083（告知病人醫師使用 AI 對信任的影響）. https://www.jmir.org/2025/1/e66083 （僅搜尋摘要；查閱 2026-10-30）
- Khoong EC, et al. Assessing the use of Google Translate for Spanish and Chinese translations of emergency department discharge instructions. JAMA Intern Med 2019. https://pmc.ncbi.nlm.nih.gov/articles/6450297 （查閱 2026-10-30）
- A Pragmatic Assessment of Google Translate for Emergency Department Instructions. J Gen Intern Med 2021. https://pubmed.ncbi.nlm.nih.gov/33674922/ （作者未核對、依搜尋摘要；查閱 2026-10-30）
- Design for Older People: Improving the Usability of Mobile Apps through Targeted Design Recommendations. OzCHI 2024. https://outbox.eait.uq.edu.au/uqsville/OzCHI2024/ （僅搜尋摘要；查閱 2026-10-30）
- Connor RJ. Sample size for testing differences in proportions for the paired-sample design. Biometrics 1987;43(1):207–211（原文未取得；公式依 [E] 二手說明一致）.

### [D] 預印本
- The Transparency Trap: How AI Disclaimers Create Overconfidence in High-Stakes Decisions. arXiv 2608.07493, 2026（n=52；僅搜尋摘要）. https://arxiv.org/pdf/2608.07493 （查閱 2026-10-30）

### [E] 技術部落格、官方範例程式碼、論壇、新聞（只能輔助）

**LINE 官方 SDK 與範例**
- line/line-bot-sdk-python：webhook.py、README、examples/fastapi-echo、PR #597、releases. https://github.com/line/line-bot-sdk-python （查閱 2026-10-31）

**LINE 傳圖畫質與 LIFF 行為實測**
- Classmethod. loading animation 實測（2024-04）. https://dev.classmethod.jp/articles/try-to-use-line-messaging-api-of-indicating-loading-animation/ ；LIFF／LINE Login／MINI App 差異. https://dev.classmethod.jp/articles/liff-line-login-mini-app-differences/ ；isUnblocked 實作. https://dev.classmethod.jp/articles/try-to-distinguish-between-add-friends-and-unblocking/ （查閱 2026-10-31）
- app-liv. LINE 傳圖畫質實測（最後更新 2025-11-06）. https://app-liv.jp/articles/121899 ；appllio（2025-03-02）. https://appllio.com/line-send-original-size-photos （查閱 2026-10-31）
- fileconv（HEIC 以檔案方式傳送）. https://fileconv.pages.dev/en/blog/heic-share-tips ；dime.jp. https://dime.jp/genre/1974458/ （搜尋摘要；查閱 2026-10-31）
- zenn.dev（Android 14 file input 行為）. https://zenn.dev/bltsdc/articles/52fd898281d48c ；Stack Overflow mirror（iOS 17 capture 問題）. https://backiee.wasmer.app/http_Stackoverflow_com/questions/79630177/ios-17-camera-capture-not-working-in-next-js-with-input-type-file-capture （查閱 2026-10-31）

**台灣 LINE 官方帳號方案沿革**
- INSIDE（2020-03-02）. https://www.inside.com.tw/article/19061-line-new-fee-brand ；TechNews（2018-11-09）. https://technews.tw/?p=411309 ；FIRST LINE（標示 2023 年 9 月更新）. https://help.firstline.cc/feature/channels/line/pricing ；工商時報（2026-04-15）. https://www.ctee.com.tw/news/20260415701121-430502 （查閱 2026-10-30）

**資安與 tunnel**
- Nextcloud 論壇（Cloudflare Tunnel 隱私討論）. https://help.nextcloud.com/t/is-cloudflare-tunnel-safe-privacy-focused/150268 ；Pangolin. https://pangolin.net/news/building-a-peer-to-edge-peer-reverse-proxy （查閱 2026-10-31）

**法規與倫理的二手評論**
- World Privacy Forum（FTC Everalbum）. https://worldprivacyforum.org/posts/ftc-proposes-precedent-setting-face-recognition-settlement-photo-app-company-must-delete-consumers-photos-and-the-algorithmic-models-it-developed-using-the-photos ；Matheson（EDPB Opinion 28/2024）. https://www.matheson.com/insights/edpb-publishes-eagerly-anticipated-opinion-on-ai-models/ ；RAPS（eConsent Q&A）. https://www.raps.org/resource/electronic-informed-consent-final-q-a-spells-out.html （查閱 2026-10-31）
- Covington（2026-01）. https://www.cov.com/en/news-and-insights/insights/2026/01/5-key-takeaways-from-fdas-revised-clinical-decision-support-cds-software-guidance ；Cooley（2026-01-20）. https://www.cooley.com/news/insight/2026/2026-01-20-automation-bias-and-clinical-practice-fda-makes-incremental-updates-to-clinical-decision-support-software-guidance （查閱 2026-10-30）
- Data Colada（A/B effect 重新分析）. https://datacolada.org/?p=4489 （查閱 2026-10-30）

**工程實務與統計工具**
- Google. SRE Workbook: Canarying Releases（業界文件）. https://sre.google/workbook/canarying-releases/ （查閱 2026-10-30）
- R scorecard::perf_psi. https://search.r-project.org/CRAN/refmans/scorecard/html/perf_psi.html ；MetricGate（McNemar 樣本量）. https://metricgate.com/docs/sample-size-mcnemar-paired ；pwrss. https://rdrr.io/cran/pwrss/man/proportions.mcnemar.html （查閱 2026-10-30）

**台灣衛教與 LINE 使用說明**
- Hello醫師（119 撥打方式）. https://helloyishi.com.tw/healthy-habits/first-aid/how-to-call-an-ambulance/ ；康健知識庫. https://kb.commonhealth.com.tw/library/576.html ；T 客邦（LINE 字體設定）. https://www.techbang.com/posts/81324-how-do-ios-users-change-the-line-font-size （查閱 2026-10-30）

**介面設計規範的二手整理**
- frontendchecklist（Apple 與 Material 觸控尺寸轉述）. https://frontendchecklist.io/rules/accessibility/touch-targets （查閱 2026-10-30）

**台語語音辨識模型**
- MediaTek Research. MR Breeze ASR 25. https://www.mediatek.com/zh-tw/press-room/mediatek-research-unveils-mr-breeze-asr-25-an-open-source-ai-model-for-taiwanese-speech ；Speech-AI-Research-Center. Breeze-ASR-26. https://huggingface.co/Speech-AI-Research-Center/Breeze-ASR-26 ；NUTN-KWS. Whisper-Taiwanese-model-v0.5. https://huggingface.co/NUTN-KWS/Whisper-Taiwanese-model-v0.5 （查閱 2026-10-30）

**移工統計與 LINE 訊息上限**
- Manstrong（引勞動力發展署，2026-06 移工統計）. https://www.manstrong.com.tw/news-detail/taiwan-migrant-workers-2026 ；Pushwoosh LINE API（文字訊息 5,000 字元）. https://docs.pushwoosh.com/zh/developer/api-reference/line-api/index.md （查閱 2026-10-30）

**正文引用、但參考文獻清單沒有列出的來源**（本筆記整理，供寫作者查找）：SDK README https://github.com/line/line-bot-sdk-python 、webhook.py https://github.com/line/line-bot-sdk-python/blob/master/linebot/v3/webhook.py 、fastapi-echo https://github.com/line/line-bot-sdk-python/blob/master/examples/fastapi-echo/main.py 、PR #597 https://github.com/line/line-bot-sdk-python/pull/597 （都已概括在 [E]「line/line-bot-sdk-python」條目內）；Bourtoule et al., IEEE S&P 2021（SISA，**本輪未驗證引用細節**，沒有網址，L909）。

---

## J. 自我檢查結果與承認的缺口

### Takeaway
報告最後有六項自我檢查（L2813–2895）。本筆記核對後，發現幾處報告內部不一致或含糊的地方，但都不是 LINE 規則數字互相矛盾，所以沒有做 NEW 補查。

### Cited Findings

**J1. 報告自己的檢查（照錄要點）**
1. **關鍵數字都有來源與日期**（L2815–2822）：價格（新舊兩套）、免費則數、加購級距、reply token 一分鐘、loadingSeconds 5–60、rate limit、retry key 24 小時、rich menu 與 Flex 上限、LIFF 版本與限制日期、token 效期與上限、TLS 規格、Insight 門檻都附 [A] 網址與查閱日；LINE 頁面一律註明「頁面未標更新日」；2 秒逾時已標示需逐字確認；2023 年調價日期只有 [E]；5% 營業稅是未查證假設；Wilson CI、McNemar 樣本量、費用試算都標為本報告計算或推論。
2. **沒有編造文獻**（L2824–2837）：所有來源都出自八份研究筆記、沒有新增；保留原標記。保留「未找到可靠證據」的例子：Get content 保存天數與大小上限、EXIF 處理、內建相機是否套用濾鏡、LIFF 與 MINI App 是否收費、LINE 是否禁止 OA 收集健康資料、重送事件中 reply token 不可用的情況、台灣研究同意紀錄最低保存年限。
3. **筆記間衝突的裁決**（L2841–2850）：tunnel 業者看不看得到照片 → 依路徑而定（第 7 節）；altText 1,500 的等級 → 採 [A]（第 4 節）；06 號筆記說 reply token 時限與 rate limit「未找到」→ 以 01、02 號的 [A] 為準；ID token 驗證端點的方法 → ID token 用 POST、access token 用 GET（依 04 號 [A]）；08 號同意範本「不會給其他公司」→ 改為揭露（交付四）；06 號主張「佇列長時改用 push」→ 改為預設 postback（與 02 號一致）；rich menu 速率表寫法不同 → 以官方表格為準；PCCP 定稿日期 → 兩個日期並列。
4. **每項建議都對照了原則**（L2852–2868）：⚠ 清單見 E9。
5. **已區分研究證據、業界慣例、本報告推論**（L2870–2880）：屬業界慣例、沒有同儕審查佐證的有：佇列、冪等、dead-letter 設計；Windows 秘密保存；防火牆與 ACL；金絲雀做法；PSI 門檻。工作量估計與所有文案屬本報告推論。
6. **14 位個案下不可靠的結論**（L2882–2895）：見 G 節。

**J2. 本筆記發現的內部不一致或含糊處**
- **LIFF 時程不一致**：摘要表第 12 項寫「建議在未來約 1,000 張的階段做」（L110），第 4.1 與 4.4 節寫約 1,000 張時統一走 LIFF（L593、L757）；總表則寫「若 IRB 不允許照片經 LINE：現在（簡化版）；否則 50 位個案後」（L1915）。依 L1913，「200 位個案後」約等於 1,000 張，所以「50 位個案後」和「約 1,000 張」並不相同。整合時應寫明兩種說法並存。
- **模板編號兩套**：時序圖用 T1（同意摘要卡）、T3（請重拍）、T4（已請研究人員再看）、T5（stage 1/2）、T5b（未見明顯紅腫）（L1957–1979）；第 11 節與總表說「T5 與 T6 模板」錄台語語音（L1856、L1918）；交付四用 F0–F8，並說「F5、F6 優先錄製台語真人語音版」（L2452）。T 與 F 之間沒有明確對照；從內容看，T1≈F1、T3≈F3、T4≈F4、T5≈F5、T5b≈F5b、T6≈F6（本筆記推論）。
- **loadingSeconds**：worker 流程寫 20–30（L253），時序圖寫 30（L1970），02 號筆記寫 20–60。不衝突，只是範圍不同。
- **MINI App 網頁瀏覽器日期**：速查表寫 2025-10-01 起（L2040），參考文獻列的是 News 2025-09-26（L2654）。04 號筆記 L149 確認是 2025-09-26 公告、2025-10-01 生效，兩者一致。
- **錯誤通知的 2023 年**：第 8 節寫「確切日期未找到可靠證據」（L1288），速查表寫「2023 年加入」（L2047）；01 號筆記 L116 記為「2023 年某日」、來源是搜尋摘要。年份只有搜尋摘要支持。
- **LIFF v1 2021-10-01 終止**只出現在速查表（L2038），正文沒有提到；04 號筆記 L102 標為 [A]。
- **報告自述「所有來源都出自八份研究筆記，沒有新增」**（L2826），但正文的 Bourtoule SISA 標「本輪未驗證引用細節」、而且沒有出現在參考文獻（L909）。
- **時間基準**：報告以 2026-10-31 為「今天」，所以 L13 寫「明天」調價；本筆記撰寫日為 2026-11-01，新價已生效。

**J3. 報告承認的主要缺口（彙整）**
- 主要文件沒有 webhook 逾時秒數，也沒有 SLA。
- 重送的次數、間隔、期間、暫停條件都不公開。
- Get content 保存期與大小上限；Bot 實際收到的畫質；Android 數據；EXIF；HEIC；色彩描述檔。
- LINE 對健康資料的條款（User Data Policy 回 403）。
- 台灣研究同意紀錄保存年限；衛福部電子同意指引；假名化的法定定義。
- LINE 與 VoiceOver、TalkBack 的相容性；年齡交叉的 LINE 使用率。
- 印尼文、越南文醫療翻譯準確度；台語 ASR 對長者的準確度。
- 靜脈炎或 IV 部位自拍與 AI 的研究（只有一項試驗登錄，尚無結果）。
- 台灣是否有類似 NHS 111 的專線；INS 2024 衛教內容；台灣醫學中心正式衛教單。
- TFDA AI/ML 醫材變更管理指引（沒有檢索）；FDA CDS 原文 PDF 沒有核對。
- Windows 一手文件（服務帳號、ACL、BitLocker、DPAPI）與 OWASP API Top 10 2023 原文沒有抓取。
- FTC、EDPB 原文沒有直接讀取。

### Inferences
- 對整合者來說，本段最可靠的部分是 LINE 官方規則（[A]，但頁面沒有更新日）與台灣價格（[A]，有公告日）；最不可靠的是傳圖畫質（[E]、只測 iPhone）與所有模型效能相關的推論。

### Gaps
- 本筆記沒有對 developers.line.biz 做 NEW 補查，因為報告中沒有 LINE 數字自相矛盾。上面「需逐字確認」的項目（2 秒逾時、狀態頁說明、2023 年錯誤通知），如果整合報告要引用為確定值，建議整合前再開原頁核對。
