# LINE Messaging API：Webhook 架構、可靠性與維運（研究原型：IV 部位照片 → 靜脈炎照片分類回覆，僅供研究，非臨床診斷）

> 研究筆記。存取日：2026-10-30 至 2026-10-31，查閱工作在 10-31 完成，因頁面於 10-30 達到工作階段上限。
> 文件日期：本次讀取的 developers.line.biz 文件頁（Receiving messages、Verify webhook signature、Loading indicator、Development guidelines、Retrying API request、Check webhook error statistics、Error notification、Messaging API reference）**頁面上都沒有顯示 "last updated" 日期**。WebFetch 每一頁都回報沒有這個欄位，所以下文標為「文件未標日期」。沒有引用的日期一律不自行推估。
> 來源分級：[A] 官方文件；[E] 部落格、範例碼、論壇、第三方 changelog（僅作輔助）。
> 標記：**官方文件**＝LINE 文件明文。**業界慣例**＝一般工程做法，本次未取得同儕審查文獻，見各節 Gaps。**本報告推論**＝作者依據引用資料的推導。
> 主要 URL 縮寫：
> - RECV = https://developers.line.biz/en/docs/messaging-api/receiving-messages/ [A]
> - SIG = https://developers.line.biz/en/docs/messaging-api/verify-webhook-signature/ [A]
> - LOAD = https://developers.line.biz/en/docs/messaging-api/use-loading-indicator/ [A]
> - GUIDE = https://developers.line.biz/en/docs/messaging-api/development-guidelines/ [A]
> - RETRY = https://developers.line.biz/en/docs/messaging-api/retrying-api-request/ [A]
> - ERRSTAT = https://developers.line.biz/en/docs/messaging-api/check-webhook-error-statistics/ [A]
> - ERRNOTI = https://developers.line.biz/en/docs/partner-docs/error-notification/ [A]
> - REF = https://developers.line.biz/en/reference/messaging-api/ ；機器可讀 Markdown 版為 https://developers.line.biz/en/reference/messaging-api/index.html.md（約 698k 字元，本次分段讀取）[A]
> - STATUS = https://developers.line.biz/en/docs/basics/line-api-status/ [A]
> - SDK = https://github.com/line/line-bot-sdk-python [E，官方 SDK，但依指示分級為 E]

---

## A1. X-Line-Signature 驗證（HMAC-SHA256、raw body、constant-time）與 SDK v3 / FastAPI 實作

### Takeaway
先拿**原始位元組 body**、以 channel secret 為 key 做 HMAC-SHA256，結果 base64 後與 `x-line-signature` 做 constant-time 比對；**驗證通過才可以 parse JSON**。官方 SDK v3 的 `WebhookParser.parse()` 就是先驗證、再 `json.loads`，並使用 `hmac.compare_digest`。官方明文不要用 IP 白名單（LINE 不公開 IP），以簽章驗證取代。

### Cited Findings
- **官方文件**：簽章為「以 channel secret 為 key，對 request body 做 HMAC-SHA256」，放在 `x-line-signature` header。官方範例用 `openssl dgst -sha256 -hmac '<channel secret>' -binary | openssl base64`，可見 header 值是 base64 編碼。— [SIG](https://developers.line.biz/en/docs/messaging-api/verify-webhook-signature/)（文件未標日期；存取 2026-10-31）
- **官方文件**：webhook 以 UTF-8 傳送（`Content-Type: application/json; charset=utf-8`）。官方要求 "When verifying a signature, make sure that the character encoding is UTF-8"，並說明其他編碼可能把 LF 轉成 CRLF，或破壞 emoji、控制字元。— [SIG](https://developers.line.biz/en/docs/messaging-api/verify-webhook-signature/)
- **官方文件**：要對收到的「原樣 body 字串」驗證，"Don't modify data prior to verifying the signature on any request." 官方列出的陷阱如下。
  - 先 `json.loads` 再序列化：引號、空白會改變，簽章不符。
  - pretty-print 後再驗證。
  - 誤解跳脫字元（`\n`、`\\`）：Python 測試請用 raw string `r"..."`，shell 用單引號。
  - proxy、負載平衡器改寫了 header 或 body。
  - 用錯演算法，例如 HMAC-SHA1。
  - 用錯 channel secret：要用與 `destination` 對應的 channel。
  - 另一位 admin 重新發行了 secret，舊 secret 立即失效。
  
  — [SIG](https://developers.line.biz/en/docs/messaging-api/verify-webhook-signature/)
- **官方文件**：簽章缺漏或不符時「不處理事件、以錯誤結束」。LINE Platform 的 IP 不公開，所以應驗簽，不要做 IP 限制。— [SIG](https://developers.line.biz/en/docs/messaging-api/verify-webhook-signature/)；[GUIDE](https://developers.line.biz/en/docs/messaging-api/development-guidelines/) 明文 "we don't disclose the IP addresses of the LINE Platform"，且 IP 可能不經通知變更（文件未標日期；存取 2026-10-31）
- **官方文件**：channel secret 位於 Console 的 Basic settings，需要 Admin 權限。重新發行會讓舊的失效，只有 admin 能重發。— [SIG](https://developers.line.biz/en/docs/messaging-api/verify-webhook-signature/)
- **官方文件**："Be sure to verify the signature before processing webhook event objects." — [RECV](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)；GUIDE 也把驗簽列為 Recommended。
- **SDK [E]**：`linebot.v3` 的 `SignatureValidator` 運作如下。
  - channel secret 以 UTF-8 編碼為 key，對 UTF-8 body 做 HMAC-SHA256，再 base64。
  - 用 `compare_digest`（`hmac.compare_digest`，或 SDK 內建的 `safe_compare_digest` fallback）做 constant-time 比對。
  - `WebhookParser.parse(body, signature)` 先驗簽，失敗就 raise `InvalidSignatureError`，**之後才** `json.loads(body)`。
  - 逐一把 `events` 轉成 `Event.from_dict`。無法辨識的事件型別會包成 `UnknownEvent`，不會讓解析中斷。
  - 參數 `as_payload=True` 時，回傳含 `destination` 的 `WebhookPayload`。
  
  — [SDK webhook.py](https://github.com/line/line-bot-sdk-python/blob/master/linebot/v3/webhook.py)（存取 2026-10-31）
- **SDK [E]**：官方 `examples/fastapi-echo/main.py` 的寫法如下。
  - 讀取 body：`body = await request.body(); body = body.decode()`。
  - 取 header：`signature = request.headers['X-Line-Signature']`。
  - 驗證與解析：`events = parser.parse(body, signature)`；遇到 `InvalidSignatureError` 時 `HTTPException(400)`。
  - 回覆：`AsyncApiClient` + `AsyncMessagingApi.reply_message(ReplyMessageRequest(...))`。
  
  注意：範例用 `headers['X-Line-Signature']` 直接索引，header 缺漏時會出現未處理的 KeyError，變成 500。— [fastapi-echo/main.py](https://github.com/line/line-bot-sdk-python/blob/master/examples/fastapi-echo/main.py)
- **SDK [E]**：README 的說明如下。
  - 原文 "LINE bot sdk 3.x is not compatible with 2.x"。
  - 原文 "We will be maintaining only `linebot.v3` going forward"。
  - 2.x 模組不再更新，但仍可使用。
  - 3.x 由 OpenAPI spec 產生。
  - Requirements 為 "Python >= 3.10"。
  - 範例列有 `fastapi-echo` 與 `aiohttp-echo`（後者標為非同步處理）。
  
  — [SDK README](https://github.com/line/line-bot-sdk-python)（存取 2026-10-31）

### Inferences
- **本報告推論（FastAPI 正確骨架）**：
  1. `raw = await request.body()`，取得 bytes。
  2. `sig = request.headers.get("x-line-signature")`；缺漏就回 400。
  3. 計算 `base64(hmac_sha256(secret_utf8, raw))`，以 `hmac.compare_digest` 比對；失敗回 400 並記錄 log。
  4. 通過後才 `json.loads(raw)`，或交給 `parser.parse(raw.decode("utf-8"), sig)`。
  5. **不要**使用 FastAPI 的 Pydantic body 參數（它會先 parse），也不要在 middleware 讀過 body 後再改寫。
  6. 驗證失敗不要回 2xx，避免把惡意請求當成合法事件。驗證失敗時是否觸發 LINE 重送：只有真的來自 LINE 的請求才會被重送，偽造請求回 400 不會產生副作用。
- **本報告推論**：本專案已實作驗簽。建議補兩件事：(a) 單元測試覆蓋 emoji、`\n`、CRLF body；(b) 加入 reverse proxy 或 tunnel（例如 Cloudflare Tunnel、ngrok）時，確認不會改寫 body。
- **本報告推論**：secret 被重發後驗簽會突然全部失敗，這種「400 激增」應列為告警條件（見 B3）。

### Gaps
- 官方 SIG 頁只提供 openssl 範例，各語言範例指向 SDK 與 REF 的 "Signature validation" 節。本次沒有逐字讀取 REF 該節的 Python 範例碼。
- SDK 3.0.0 的正式釋出日期：**未找到可靠證據**，本次沒有讀到 PyPI 或 release 頁的日期。

---

## A2. Webhook 重送（redelivery）、webhookEventId、去重與錯誤統計

### Takeaway
重送**預設關閉**，要在 Console 的 Messaging API 分頁手動開啟；只有在 bot server **沒有回 2xx** 時才會重送。重送次數、間隔與總期間**官方明確不公開**，也**不保證送達**。重送事件只有 `deliveryContext.isRedelivery` 與原事件不同，`webhookEventId`（ULID）不變。即使沒有重送，也可能因網路因素收到重複事件，所以必須以 `webhookEventId` 去重。

### Cited Findings
- **官方文件**：開啟步驟為 Console → channel → Messaging API 分頁 → 開啟 "Use webhook" → 開啟 "Webhook redelivery"，預設為停用，開啟前要閱讀畫面上的注意事項。— [RECV](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)（文件未標日期；存取 2026-10-31）
- **官方文件**：重送條件為「已開啟重送」且 "The bot server didn't return `2xx` status code for the webhook."— [RECV](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)
- **官方文件**：原文 "The number and interval of the webhook redelivery aren't disclosed"，且可能不經通知變更；重送只持續 "for a certain period of time"。重送**不保證**送達；若重送量暴增並影響平台，LINE 可能強制關閉重送。— [RECV](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)
- **官方文件**：重送事件與原事件內容相同，只有 `deliveryContext.isRedelivery` 不同（`true`＝重送，`false`＝首次送達）。— [RECV](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)；[REF](https://developers.line.biz/en/reference/messaging-api/)
- **官方文件**：`webhookEventId` 的定義原文為 "An ID that uniquely identifies a webhook event. This is a string in ULID format." 重送時不變。官方警告網路路由等問題也可能造成重複送達，建議以 `webhookEventId` 偵測重複。— [REF](https://developers.line.biz/en/reference/messaging-api/)；[RECV](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)
- **官方文件**：webhook 若長期收不到，平台可能暫停發送。原文 "may suspend sending webhooks to your bot server if your bot server fails to receive webhooks for a long time."— [RECV](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)
- **官方文件（錯誤統計）**：
  - 開啟方式：Console → Messaging API 分頁 → "Use webhook" → 開啟 **"Error statistics aggregation"**，結果顯示在 "Webhook errors" 分頁，時間為 UTC+9。
  - 只統計開啟期間，**不會回溯**。可下載 TSV。不包含 webhook URL 驗證請求。
  - 錯誤原因分類：
    - `could_not_connect`：細項含 Connection timeout、DNS Query timeout、TLS handshake failure、Unknown host 等。
    - `request_timeout`：已送出但沒有回應，**頁面摘要寫 bot server 沒有在 2 秒內回應**；webhook 可能仍已被收到。
    - `error_status_code`：非 2xx，細項為 HTTP 狀態碼。
    - `unclassified`。
  - "Errors" 欄位為 60 秒內同一狀態碼的錯誤次數。
  
  — [ERRSTAT](https://developers.line.biz/en/docs/messaging-api/check-webhook-error-statistics/)（文件未標日期；存取 2026-10-31）
- **官方文件（錯誤通知 email）**：
  - 適用對象：「已提交必要申請的法人用戶」的選用功能，其他用戶需洽業務或 Sales partner。
  - 收件人：Basic settings 的 email 與 channel Admin。
  - 兩類信件：(1) 偵測到錯誤，主旨為 "Messaging API: Your bot server returned no response or an error"；(2) 重送停止。後者只在開啟重送時寄送，條件是重送 "a certain period of time" 仍無回應。
  - 同一狀態碼在 5 分鐘（300 秒）內的錯誤合併成一封信。
  
  — [ERRNOTI](https://developers.line.biz/en/docs/partner-docs/error-notification/)（文件未標日期；存取 2026-10-31）
- **變更時間軸**：
  - **2022-03-07**：日文 news 公告「2022 年 4 月上旬起，Messaging API 新增 Webhook 再送機能」，webhook event object 同步變更（新增 `deliveryContext.isRedelivery` 等）。— [LINE news ja/38](https://developers.line.biz/ja/news/38/) [A]（日期來自搜尋摘要，本次沒有逐頁讀取，建議交叉確認）
  - **2023 年某日**：錯誤通知功能改為重送停止時也寄送通知信。— 來源為搜尋摘要，對應 [ERRNOTI](https://developers.line.biz/en/docs/partner-docs/error-notification/)；**確切日期未找到可靠證據**。

### Inferences
- **本報告推論（去重設計，SQLite）**：
  - 建立 `webhook_events(webhook_event_id TEXT PRIMARY KEY, received_at, is_redelivery, user_id, type, message_id, status, raw_json)`。
  - 收到事件後，在**同一個 transaction** 執行 `INSERT OR IGNORE`；影響 0 列代表重複，直接略過。
  - 寫入完成才回 200。照片內容（Get content）與推論交給背景 worker。
  - 研究統計（收件數）以 `webhook_event_id` 去重後計算，避免重送灌水。
- **業界慣例**：以事件 ID 做 idempotency key，加上「先持久化、後確認 2xx、非同步處理」（at-least-once 投遞配合冪等消費者），是 webhook 消費端的常見模式。本次**沒有**取得同儕審查文獻支持，見 Gaps。
- **本報告推論**：研究原型跑在單機 PC，偶有停機、重開機、Windows Update，**建議開啟 webhook redelivery 與 Error statistics aggregation**。代價是必須做好去重，見上方設計。
- **本報告推論**：重送事件的 reply token 不保證可用（見 A4），重送事件的回覆流程應準備以 push 補發的分支（計費）。

### Gaps
- 重送的次數、間隔、最長期間：官方**明文不公開**，任何具體數字都不可引用。
- 錯誤統計資料的保存期間與延遲：ERRSTAT 未說明。
- webhook 冪等設計的同儕審查或權威工程來源：本次沒有檢索到，**未找到可靠證據**，只能標為業界慣例。

---

## A3. Webhook 回應時間要求與非同步處理

### Takeaway
官方要求收到 POST 後回 **200**（RECV 寫 2xx 即視為成功），並**建議非同步處理事件**。主要使用文件沒有明列 webhook 逾時秒數，但錯誤統計頁將 `request_timeout` 描述為**約 2 秒內沒有回應**。實務上應在毫秒級完成「驗簽、寫入 DB、回 200」，推論改到背景執行。

### Cited Findings
- **官方文件**：原文 "The bot server must return status code `200` after it receives the HTTP POST request sent from the LINE Platform." LINE Platform 也可能送出不含事件（`events` 為空陣列）的 POST 以確認連線。— [REF](https://developers.line.biz/en/reference/messaging-api/)（Webhooks › Response / Request body；存取 2026-10-31）
- **官方文件**：原文 "We recommend that you process webhook events asynchronously." — [RECV](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)；REF 寫 "We recommend that you make the event processing asynchronous."
- **官方文件**：`request_timeout`＝「webhook 已送出但沒有回應」，摘要說明為 bot server 沒有在 2 秒內回應。— [ERRSTAT](https://developers.line.biz/en/docs/messaging-api/check-webhook-error-statistics/)。這個「2 秒」來自 WebFetch 對頁面的摘要，**建議撰稿前打開原頁逐字確認**。
- RECV 頁本身「沒有給出明確逾時或回應時間上限」（WebFetch 讀取結果）。— [RECV](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)

### Inferences
- **本報告推論**：本專案的推論（品質檢查 + YOLO + EfficientNet/DINOv2）需要數秒，**絕不能在 webhook handler 內同步執行**，否則會出現 `request_timeout` 並觸發重送，造成重複推論與重複收件。
- **本報告推論**：FastAPI 的 `BackgroundTasks` 與 process 綁在一起，重啟就遺失。建議改用 SQLite job 表，由獨立 worker 輪詢（見 B2）。

### Gaps
- webhook 逾時秒數在主要文件（RECV、REF）沒有明列，只有 ERRSTAT 的 2 秒描述；有無正式 SLA 數字，**未找到可靠證據**。

---

## A4. Reply token：有效期、單次使用、過期行為、重送事件

### Takeaway
reply token **只能用一次**，且**必須在收到 webhook 後一分鐘內使用**，官方註明此時限可能不經通知變更。過期或已使用的 token 回傳 400 "Invalid reply token"，訊息不會送出。重送事件中的 reply token「除特定情況外可用」。`standby` 模式的事件沒有 reply token。

### Cited Findings
- **官方文件**：原文 "Reply tokens can only be used once."；"Reply tokens must be used within one minute after receiving the webhook."；此時限 may change without notice。— [REF › Send reply message](https://developers.line.biz/en/reference/messaging-api/#send-reply-message)（存取 2026-10-31）
- **官方文件**：使用過期或已用過的 token 會回 400，訊息為 "Invalid reply token"；回傳錯誤時訊息不會送出。— [REF](https://developers.line.biz/en/reference/messaging-api/)
- **官方文件**：原文 "The reply token included in a redelivered webhook event object can be used except in certain cases."，細節請見 REF。— [RECV](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)
- **官方文件**：`mode` 為 `standby` 時，事件不含 reply token，bot "shouldn't send any messages"。— [REF](https://developers.line.biz/en/reference/messaging-api/)
- **官方文件**：edit event 的 reply token 與原 message event 的不同。— [REF](https://developers.line.biz/en/reference/messaging-api/)

### Inferences
- **本報告推論**：時限是「收到 webhook 後一分鐘」，重送事件因延遲很可能已逾時。所以回覆流程要先嘗試 reply；遇到 400 Invalid reply token，再依研究政策決定是否以 push 補發（計費），或不補發只記錄。
- **本報告推論**：一張圖片只消耗一個 reply token，一次 reply 最多可以帶多則訊息。每則訊息數上限沒有在本次逐字確認。建議「結果 + 研究免責聲明」放在同一次 reply。

### Gaps
- 「重送事件 reply token 不可用的 certain cases」具體指什麼：RECV 指向 REF，但本次讀取的 REF 片段沒有逐字列出，**未找到可靠證據**。
- reply token 時限的歷史變更（是否曾為「30 秒」等說法）：本次沒有找到官方變更紀錄。

---

## A5. Loading animation API（POST /v2/bot/chat/loading/start）

### Takeaway
`loadingSeconds` 介於 **5–60 秒，必須是 5 的倍數，預設 20 秒**，只支援一對一聊天。以下任一情況發生時動畫消失：到時、或 bot 送出新訊息。只有使用者**正在看聊天畫面**時才會顯示。API 一律回 202，包含使用者沒在看、已封鎖、已刪除帳號的情況。速率上限為 **100 req/s**。於 **2024-04** 推出。

### Cited Findings
- **官方文件**：
  - 請求格式：`POST https://api.line.me/v2/bot/chat/loading/start`，body 帶 `chatId`（user ID）與 `loadingSeconds`。
  - 原文 "You can't specify group chats or multi-person chats"。
  - 消失時機：秒數到期（5–60 秒），或 "when a new message arrives from your LINE Official Account"。
  - 原文 "only displayed when the user is viewing the chat screen"；使用者沒在看聊天畫面時不會有通知，之後打開聊天也不會出現動畫。
  - 顯示中再呼叫一次會延長，剩餘時間被第二次請求的秒數覆寫。
  
  — [LOAD](https://developers.line.biz/en/docs/messaging-api/use-loading-indicator/)（文件未標日期；存取 2026-10-31）
- **官方文件**：`loadingSeconds` 預設 20，接受 5–60、以 5 為級距；錯誤訊息例如 "must be a multiple of five"、"Must be between 5 and 60"。回應原文 "Returns status code `202` and an empty JSON object"；使用者沒在看、已封鎖或已刪除帳號時也回 202，但不顯示動畫。— [REF › Display a loading animation](https://developers.line.biz/en/reference/messaging-api/#display-a-loading-indicator)
- **官方文件**：Rate limit "Display a loading animation: 100 requests per second"。— [REF › Rate limits](https://developers.line.biz/en/reference/messaging-api/#rate-limits)
- **時間軸**：官方 news 標題 "In the Messaging API, you can now display loading animations on the chat screen with users"，URL 路徑日期為 2024/04/17。— [LINE news 2024-04-17](https://developers.line.biz/en/news/2024/04/17/loading-indicator/) [A]（頁面擷取沒有顯示日期，日期取自 URL 與 SDK changelog [E]）
- **[E]**：line-bot-sdk-python release notes 記載新增 loading animation endpoint。— [SDK releases](https://www.github.com/line/line-bot-sdk-python/releases/latest)；日方實測曾遇到 API 回成功但沒有顯示，清除快取後恢復（2024-04 測試）。— [classmethod](https://dev.classmethod.jp/articles/try-to-use-line-messaging-api-of-indicating-loading-animation/) [E]

### Inferences
- **本報告推論**：202 不代表使用者真的看到動畫，**不能**把它當成 UX 保證，也不應記為「已通知使用者」。
- **本報告推論**：推論預估在 60 秒內，所以可以在收到圖片後（寫入 DB 的同時）呼叫 `loadingSeconds=20` 或 30。reply 送出後動畫自動消失，不需要另行關閉。

### Gaps
- 是否有「停止動畫」的 endpoint：本次沒有看到，**未找到可靠證據**。

---

## A6. 推論較慢時的流程設計（三方案取捨與序列圖）

### Takeaway
reply token 有 1 分鐘時限，本專案推論只需數秒，**首選方案 (b)：loading animation → 背景推論 → 用 reply token 回結果**。只有在逾時、重送 token 失效、或排隊過長時，才改用 push（計費）。方案 (c)「先 reply『已收到』、再 push 結果」每張照片都會消耗 push 額度，不建議作為預設。

### Cited Findings
- reply token 一分鐘、單次使用：[REF › Send reply message](https://developers.line.biz/en/reference/messaging-api/#send-reply-message)
- loading animation 5–60 秒，bot 送出訊息即消失，只在使用者看聊天畫面時顯示：[LOAD](https://developers.line.biz/en/docs/messaging-api/use-loading-indicator/)；[REF](https://developers.line.biz/en/reference/messaging-api/#display-a-loading-indicator)
- 官方建議非同步處理 webhook：[RECV](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)
- push 可帶 `X-Line-Retry-Key` 做冪等（24 小時有效）：[RETRY](https://developers.line.biz/en/docs/messaging-api/retrying-api-request/)
- 「Get number of sent reply messages」與「push messages」是兩個分開的計數 endpoint：[REF](https://developers.line.biz/en/reference/messaging-api/)。push 是否計入月額度、台灣方案費率不屬本筆記範圍，見 Gaps。

### Inferences（本報告推論：序列圖）

```
方案 (b) 建議預設
User      LINE Platform        FastAPI /callback        SQLite            GPU worker
 |--image-->|                         |                    |                   |
 |          |--POST webhook---------->| verify sig (raw)   |                   |
 |          |                         |--INSERT OR IGNORE->| (webhookEventId)  |
 |          |                         |--enqueue job------>|                   |
 |          |<--------200 (<~100ms)---|                    |                   |
 |          |                         |-- POST loading/start (20–30s) -------->LINE (202)
 |<-...動畫...|                       |                    |<--poll job--------|
 |          |                         |                    |  GET content (api-data.line.me)
 |          |                         |                    |  quality→YOLO→cls (數秒)
 |          |<------- POST reply (replyToken, 結果+研究用免責) -----------------|
 |<-result--|  (動畫自動消失)          |                    |--mark done--------|
 |          |                         |                    |  shadow model（回覆後，不影響回覆）

方案 (b′) 逾時或失敗分支
 worker: 若 now - webhook_received_at > ~50s，或 reply 回 400 "Invalid reply token"
   → 依研究政策：push（帶 X-Line-Retry-Key = job UUID），或只記錄「未回覆」

方案 (c) 先告知再 push（不建議預設）
 /callback → 立即 reply「已收到，分析中」→ 背景推論 → push 結果（每張照片都計費一次）
```

- **取捨（本報告推論）**：
  - (a) handler 內同步推論再 reply：會超過 2 秒 webhook 逾時並觸發重送，**禁止**。
  - (b) 成本最低（reply 不另計 push）、UX 好，前提是 GPU 排隊加推論能在 1 分鐘內完成。
  - (c) 使用者立即得到確認，但每張照片都用一次 push，也要處理 push 失敗（例如使用者已封鎖）。
- **本報告推論**：以 SQLite 記錄 `webhook_received_at`，worker 依「剩餘 token 壽命」決定排程優先序（最早到期者先處理），讓 reply 成功率最大化。

### Gaps
- 台灣 LINE 官方帳號方案中 reply、push 的計費與額度規則：不在本次查詢範圍，建議由另一份研究筆記確認，此處**未找到可靠證據**。

---

## A7. 事件順序、併發、events 陣列、destination、mode

### Takeaway
**LINE 不保證事件順序**，要用 `timestamp` 判斷。一次 POST 可能含**多個事件**，也可能是**空陣列**（連線確認）。`destination` 是接收方 bot 的 user ID。`mode: standby` 時不應發訊息，事件也沒有 reply token。imageSet 的多張圖片會以**未定義順序**送達。

### Cited Findings
- **官方文件**：原文 "the order of webhook events you receive can be different from the order the events occurred"，請檢查 `timestamp`。— [RECV](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)
- **官方文件**：原文 "A webhook sent from the LINE Platform may contain multiple webhook event objects."；"The LINE Platform may send an empty array that doesn't include a webhook event object to confirm communication." `destination` 的定義原文為 "User ID of a bot that should receive webhook events."— [REF › Webhooks › Request body](https://developers.line.biz/en/reference/messaging-api/)
- **官方文件**：`mode` 的 `active` 表示 channel 啟用中；`standby` 表示等待中，事件不含 reply token，且 bot "shouldn't send any messages"。— [REF](https://developers.line.biz/en/reference/messaging-api/)
- **官方文件**：bot 自身的 user ID 可從 `destination` 取得，或透過 "Get LINE Official Account (bot) info" endpoint。— [RECV](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)
- **官方文件（GUIDE）**：bot server 要能容忍非破壞性變更，包括新增 endpoint、欄位、header、選用參數、event 屬性、enum 值，以及屬性順序、空白與換行的差異。— [GUIDE](https://developers.line.biz/en/docs/messaging-api/development-guidelines/)

### Inferences
- **本報告推論**：
  - 每個事件各自建一個 job。同一使用者的 job 依 `timestamp` 序列化處理（per-user lock 或單一 GPU worker 自然序列化），不同使用者之間可以平行處理，但 GPU 有限，建議全域只開 1 個推論 worker。
  - 未知事件型別要記錄並略過，不可回非 2xx；SDK 的 `UnknownEvent` 已提供這個行為。
  - `mode=standby` 的事件只記錄、不回覆。
  - 空 `events` 陣列直接回 200。

### Gaps
- LINE 單次 webhook 最多含幾個事件：**未找到可靠證據**。

---

## A8. 相關訊息型別：image event、contentProvider、imageSet

### Takeaway
image 事件的 `contentProvider.type` 為 `line` 時，用 Get content 取得二進位；為 `external` 時只提供 URL，不能用 Get content。多張圖片同時送出時帶 `imageSet {id, index(從 1 起), total}`，但各張的 webhook **不保證依 index 順序**送達。使用者傳送的內容會在「一段時間後自動刪除」，期間不公開。

### Cited Findings
- **官方文件**：`contentProvider.type`：`line` 原文 "The image was sent by a LINE user."，可用 Get content；`external` 原文 "The URL of the image file is included in the `contentProvider.originalContentUrl` property."，不能用 Get content。— [REF › Message event › Image](https://developers.line.biz/en/reference/messaging-api/)
- **官方文件**：`imageSet.id` 原文 "Image set ID. Only included when multiple images are sent simultaneously."；`index` 從 1 起算；`total` 為同時送出的張數。原文 "The webhooks are delivered in an undefined order, not in the order of the values in `imageSet.index`."— [REF](https://developers.line.biz/en/reference/messaging-api/)
- **官方文件**：Get content 原文 "Content is automatically deleted after a certain period from when the message was sent"，保存期間不保證。大型影片、音訊在準備中時回 202，可查 transcoding status（`processing`/`succeeded`/`failed`）。— [REF › Get content](https://developers.line.biz/en/reference/messaging-api/#get-content)；RECV 亦說明內容會在一段時間後自動刪除，文字訊息只能經 webhook 取得。
- **官方文件**：unsend 事件發生時，建議把目標訊息從自家顯示與儲存中移除，確保之後無法被看見或使用。— [RECV](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)；[GUIDE](https://developers.line.biz/en/docs/messaging-api/development-guidelines/)

### Inferences
- **本報告推論**：
  - 收到 image 事件後應**盡快**下載內容並存到本機（研究照片不上傳第三方雲端，符合專案原則）。
  - `external` 類型（通常不會出現在一般使用者拍照的情境）應拒收並記錄。
  - imageSet 可設計為「每張各自分析、各自回覆」。若要合併成一則回覆，需等到收齊 `total` 張或逾時；但每張事件都有自己的 reply token，合併回覆會浪費其他 token，也增加逾時風險。
  - unsend 事件應觸發研究資料刪除流程，並與「撤回同意」統計分開記錄。

### Gaps
- Get content 的內容保存期間：官方明文不公開，**未找到可靠證據**。
- Get content 是否有獨立的較低 rate limit：本次讀取的 Get content 節沒有列出；rate limit 表中沒有專列，推定落在 "Other API endpoints: 2,000 req/s"，但**未逐字確認**。

---

## B1. Rate limits、429、X-Line-Retry-Key、狀態碼、x-line-request-id

### Takeaway
多數 endpoint 為 2,000 req/s（每 channel、每 endpoint）；loading animation 100 req/s；統計與 insight 類 60 req/hour。429 代表超過 rate、併發或訊息額度。`X-Line-Retry-Key` **只適用 push、multicast、narrowcast、broadcast**，格式為自行產生的 UUID，**首次請求後 24 小時內有效**；重複的 key 回 409，並附 `x-line-accepted-request-id`。

### Cited Findings
- **官方文件（Rate limits，每 channel、每 endpoint）**：
  - narrowcast/broadcast 發送、delivery 與好友數、人口統計、互動與 insight 統計、test webhook endpoint：**60 requests per hour**
  - audience 相關：60/min
  - Set/Get webhook endpoint：1,000/min
  - rich menu 與 alias 的建立或刪除、batch status：100/hour（在 LINE Official Account Manager 操作的不計）
  - batch 取代或解除使用者 rich menu：3/hour
  - Get rich menu list：10/s
  - multicast、membership、coupon：200/s
  - **Display a loading animation：100/s**
  - Issue short-lived channel access token：370/s
  - **Other API endpoints：2,000/s**
  
  超過時原文 "you will receive an error message saying, `429 Too Many Requests`"。另有 audience 的 "Limit on the number of concurrent operations"。— [REF › Rate limits](https://developers.line.biz/en/reference/messaging-api/#rate-limits)（存取 2026-10-31）
- **官方文件**：Get number of sent reply/push messages 的 rate limit 為 2,000 req/s。— [REF](https://developers.line.biz/en/reference/messaging-api/)
- **官方文件（Status codes）**：
  - 200 OK
  - 400 Bad Request
  - 401 Unauthorized：沒有有效的 channel access token
  - 403 Forbidden：沒有權限，需檢查帳號或方案
  - 404 Not Found：例如無法取得 profile，原因可能是 user ID 不存在、未同意、非好友或已封鎖
  - 409 Conflict：相同 retry key 已被接受
  - 410 Gone
  - 413 Payload Too Large：超過 2MB
  - 415 Unsupported Media Type
  - 429 Too Many Requests：rate、併發或訊息額度超限
  - 500 Internal Server Error
  
  — [REF › Status codes](https://developers.line.biz/en/reference/messaging-api/#status-codes)
- **官方文件（Retry key）**：
  - 只適用 push、multicast、narrowcast、broadcast；用在其他 API 回 400。
  - 格式為自行產生的 hex UUID，原文 "The retry key isn't generated by LINE"。
  - **首次請求就要帶**，沒帶的請求永遠無法安全重試。
  - **有效期為首次請求後 24 小時**。
  - 何時重試：只在 500 或網路逾時時重試；2xx、409、其他 4xx 不重試。
  - 409 回應含 `x-line-accepted-request-id`；push 的 409 body 會回傳原本 `sentMessages` 的 `id` 與 `quoteToken`。
  - 重試內容必須與原請求相同。
  - 每次重試會拿到新的 `x-line-request-id`，也各自計入 rate limit；建議 exponential backoff。
  - retry key 只防重複，**不保證送達**：一旦回 200 就不能再重試，例如使用者已封鎖的情況。
  
  — [RETRY](https://developers.line.biz/en/docs/messaging-api/retrying-api-request/)（文件未標日期；存取 2026-10-31）；[REF › Send push message](https://developers.line.biz/en/reference/messaging-api/#send-push-message)
- **官方文件（日誌）**：LINE 不提供 log，開發者要自行記錄。
  - API 請求：`x-line-request-id`、請求時間、HTTP method、endpoint、狀態碼。
  - 收到的 webhook：來源 IP、接收時間、method、path、自己回的狀態碼。
  - 選擇性記錄：request 與 response body、`x-line-signature`、event object。
  
  — [GUIDE](https://developers.line.biz/en/docs/messaging-api/development-guidelines/)
- **官方文件（禁止事項）**：
  - 不要用大量請求做壓力或運作測試；LINE 不提供壓測服務。
  - 不要對同一使用者大量傳訊。
  - 不要對不存在的 user ID 發請求。
  
  — [GUIDE](https://developers.line.biz/en/docs/messaging-api/development-guidelines/)

### Inferences
- **本報告推論**：研究原型的流量遠低於 2,000/s，rate limit 實際上不是瓶頸。須注意的是 insight 類 60/hour：儀表板不可每次刷新都呼叫，應每日排程抓取一次並快取在 SQLite。
- **本報告推論**：push 的 retry key 用 job 的 UUID，並持久化在 job 列中，讓重開機後仍以同一個 key 重試（須在 24 小時內）。reply 不支援 retry key：reply 遇到 5xx 或逾時時，無法確認是否已送達。可以等待 1 分鐘讓 token 自然失效後，判定為「未知」，並記錄 `x-line-request-id` 供追查。

### Gaps
- 429 是否附 `Retry-After` header：**未找到可靠證據**。
- Reply endpoint 是否有官方建議的重試策略：本次沒有找到。

---

## B2. 伺服器停機時事件的命運、停機後通知、佇列設計

### Takeaway
沒有開重送時，停機期間的 webhook **不會補送**。開啟後只在不公開的「一段時間」內重送，且不保證送達；長期失敗可能被暫停發送。文字訊息內容只能經 webhook 取得。停機後要通知使用者只能用 push（計費），且原 reply token 早已過期。

### Cited Findings
- 重送預設關閉、次數與期間不公開、不保證送達：[RECV](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)
- 長期收不到可能被暫停發送：[RECV](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)
- 原文 "Even if the bot server fails to receive the HTTP POST request sent from the LINE Platform, the bot server can receive this request again."（在重送開啟的脈絡下）— [REF › Webhooks › Response](https://developers.line.biz/en/reference/messaging-api/)
- 文字訊息只能經 webhook 取得，沒有可重新查詢的 API；內容（圖片）會在一段時間後自動刪除：[RECV](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)；[REF › Get content](https://developers.line.biz/en/reference/messaging-api/#get-content)
- 重送停止時寄信通知（僅限已申請錯誤通知的法人用戶）：[ERRNOTI](https://developers.line.biz/en/docs/partner-docs/error-notification/)
- reply token 一分鐘時限：[REF](https://developers.line.biz/en/reference/messaging-api/#send-reply-message)

### Inferences（本報告推論與業界慣例）
- **SQLite job queue 結構（本報告推論）**：
  - `jobs(id UUID PK, webhook_event_id UNIQUE, user_id, message_id, reply_token, webhook_received_at, status{queued, downloading, inferring, replied, pushed, failed, dead}, attempts, next_attempt_at, last_error, retry_key UUID, created_at, updated_at)`
  - 開啟 WAL 模式。worker 用 `UPDATE ... WHERE status='queued' ... RETURNING` 或 transaction 搶占 job。
  - 重試採 exponential backoff 加上上限（例如 Get content 5xx 重試 3 次），超過就標為 `dead` 並告警。
  - process 啟動時，把卡在 `downloading`、`inferring` 的 job 回收為 `queued`。
- **業界慣例**：「持久化 → ack → 背景 worker → 重試 → dead-letter」是處理至少一次投遞的常見模式（未取得同儕審查文獻，見 Gaps）。
- **停機後通知（本報告推論）**：
  - 恢復後若收到重送事件，且 reply token 已失效，依研究政策決定是否 push「系統先前中斷，結果如下／請重新上傳」。每則 push 都計費，建議只對「已同意研究、且有未完成照片」的使用者補發，每人最多 1 則。
  - 預防性做法：在 rich menu 或自動回覆說明「研究服務可能中斷，非緊急醫療管道」，以降低補發需求。

### Gaps
- 平台暫停 webhook 的條件與恢復方式（"for a long time" 是多久）：**未找到可靠證據**。
- 同儕審查的 webhook 可靠性與冪等文獻：本次沒有檢索。

---

## B3. 監控與告警：Console 錯誤統計、發送數與額度 API、Insight API（延遲、門檻）、自建統計

### Takeaway
LINE 端可用的工具：Console 的 Webhook 錯誤統計（需手動開啟，不回溯）、發送數 API（隔日完成計算）、Insight API（約 1 天；人口統計約 3 天、目標可觸及數須 ≥20 人；互動統計 <20 回 null、只更新 14 天；只開放日本、泰國、台灣建立的帳號）、本月額度與用量 API（用量為近似值）。這些數字粒度粗、有延遲、有隱私門檻，**研究指標（收件、同意率、品質退件率、預測分佈、撤回）必須自建**。

### Cited Findings
- **Webhook 錯誤統計**：需開啟 Error statistics aggregation，不回溯，UTC+9，可下載 TSV，錯誤分類為 `could_not_connect`/`request_timeout`/`error_status_code`/`unclassified`。— [ERRSTAT](https://developers.line.biz/en/docs/messaging-api/check-webhook-error-statistics/)
- **Get number of sent reply messages**（`GET /v2/bot/message/delivery/reply?date=yyyyMMdd`，UTC+9）：
  - 只計算經 `/bot/message/reply` 送出的訊息，不含 LINE Official Account Manager 發的。
  - `status` 為 `ready`/`unready`（原文 "Normally, the counting process is completed within the next day"）/`out_of_service`（2018-03-31 之前）。
  - `success` 欄位只在 ready 時出現。rate limit 2,000/s。
  - push、multicast、broadcast 各有同構 endpoint。
  
  — [REF](https://developers.line.biz/en/reference/messaging-api/)
- **Get the target limit for sending messages this month**：`type` 為 `none` 或 `limited`；`value` 只在 limited 時出現。— [REF](https://developers.line.biz/en/reference/messaging-api/)
- **Get number of messages sent this month**（`GET /v2/bot/message/quota/consumption`）：`totalUsage` 為本月已送出的訊息數，含 LINE Official Account Manager 發的。原文 "The number of messages retrieved by this operation is approximate"，精確數字請用 OA Manager 或發送數 API。— [REF](https://developers.line.biz/en/reference/messaging-api/)
- **Get number of message deliveries**：`ready`/`unready`（原文 "usually takes about a day"）/`out_of_service`（2017-03-01 之前）；60 req/hour。— [REF › Insight](https://developers.line.biz/en/reference/messaging-api/)
- **Get number of followers**：同樣三種狀態，2016-11-01 之前為 out_of_service，約 1 天完成計算；非 ready 時 `followers`/`targetedReaches`/`blocks` 為 null；60 req/hour。— [REF › Insight](https://developers.line.biz/en/reference/messaging-api/)
- **Get friend demographics**：
  - 回傳 `available` 旗標。
  - 目標可觸及數須 "20 or more people"。
  - 帳號須在日本（JP）、泰國（TH）或**台灣（TW）**建立。
  - 資料約 "approximately 3 days" 後出現。
  - 60 req/hour。
  
  — [REF › Insight](https://developers.line.biz/en/reference/messaging-api/)
- **Get user interaction statistics**：針對 narrowcast/broadcast 的 `requestId`；<20 回 `null`；只更新 "only 14 days (1,209,600 seconds)"；60 req/hour。Get statistics per unit 的 `to` 最多為 `from` 加 30 天，同樣有 <20 null 與 14 天規則。— [REF › Insight](https://developers.line.biz/en/reference/messaging-api/)

### Inferences
- **本報告推論**：
  - Insight API 的對象是行銷推播（narrowcast/broadcast），與本專案「一對一回覆」的研究指標關聯低。實用的只有 followers（好友、封鎖趨勢）與 reply/push 發送數（與自建 log 對帳）。
  - 建議每日排程一次抓取前一日（UTC+9）的 reply/push 數與 followers，寫入 SQLite；若 `unready` 就隔天補抓。
  - 研究統計一律以自建資料表計算，以 `webhookEventId` 去重，排除 `isRedelivery` 的重複。
  - 每日對帳：「自建 replied 數」對照「LINE reply 發送數」，差異過大即代表 reply 失敗或重複發送。
- **本報告推論**：對研究倫理的意義是 Insight 的 ≥20 人門檻與 null 規則本身就是隱私保護；自建統計在對外報告時也應採用類似的最小格數抑制（small cell suppression）。

### Gaps
- Webhook 錯誤統計的保存期限、刷新延遲：**未找到可靠證據**。
- `quota/consumption` 是否計入 reply：本次讀取片段沒有明列，**未找到可靠證據**。

---

## B4. LINE 平台狀態頁與事故公告

### Takeaway
官方狀態頁是 **LINE API Status（https://api.line-status.info/）**，涵蓋 Messaging API（API 與 Webhook）、LINE Developers 網站與 Console、LIFF、LINE Login，不涵蓋 LINE app 本身。事故先發布在狀態頁，細節釐清後再於 LINE Developers news 發布；提供 RSS、ATOM 訂閱。

### Cited Findings
- **官方文件**：
  - 狀態頁網址 https://api.line-status.info/。
  - 涵蓋範圍：Messaging API（API、Webhook）、LINE Developers（網站、Console）、LIFF、LINE Login；不涵蓋 LINE app。
  - 發布流程：偵測到事故先發布於狀態頁，細節釐清後發布為 LINE Developers news；部分問題只出現在狀態頁。
  - 可透過 "SUBSCRIBE TO UPDATES" 取得 ATOM/RSS。
  - LY Corporation 聲明狀態資訊不保證即時、準確或完整。
  
  — [STATUS](https://developers.line.biz/en/docs/basics/line-api-status/)（文件未標日期；存取 2026-10-31；內容來自搜尋摘要與該頁標題，建議撰稿前打開原頁逐字確認）
- **官方**：FAQ 的 outage-report 標籤頁 — [LINE Developers FAQ outage-report](https://developers.line.biz/en/faq/tags/outage-report/) [A]（本次未讀內文）
- **官方**：如何取得最新 news 的 tips（2026-03-05）— [LINE Developers tips 2026-03-05](https://developers.line.biz/en/tips/2026/03/05/how-to-get-the-latest-news/) [A]（本次未讀內文）

### Inferences
- **本報告推論**：可讓本機監控程式訂閱 api.line-status.info 的 RSS。當自家 webhook 錯誤上升時，先比對 LINE 是否有事故，以區分「我方故障」與「平台故障」。

### Gaps
- 狀態頁的歷史事故頻率與 SLA：**未找到可靠證據**。

---

## B5. 單機 Windows PC 部署的健康檢查與告警設計（業界慣例與本報告推論）

### Takeaway
LINE 不提供 log，自家監控要涵蓋：webhook 入口可達性、驗簽失敗率、job 佇列積壓、reply 成功率與 token 逾時率、GPU 與 worker 存活、磁碟空間。外部通知可用 LINE 端的錯誤統計（錯誤通知 email 只限法人申請者）。

### Cited Findings
- LINE 不提供 log，開發者須自行記錄 API 與 webhook 日誌（欄位見 B1）。— [GUIDE](https://developers.line.biz/en/docs/messaging-api/development-guidelines/)
- 錯誤通知 email 只限已提交申請的法人用戶；Webhook errors 分頁只在開啟 Error statistics aggregation 後出現。— [ERRNOTI](https://developers.line.biz/en/docs/partner-docs/error-notification/)
- 禁止用 LINE 做壓測、禁止大量請求。— [GUIDE](https://developers.line.biz/en/docs/messaging-api/development-guidelines/)
- Set/Get webhook endpoint（1,000/min）與 test webhook endpoint（60/hour）可用來確認 webhook URL 設定。— [REF › Rate limits](https://developers.line.biz/en/reference/messaging-api/#rate-limits)

### Inferences（本報告推論／業界慣例，沒有外部文獻支持）
- **健康檢查**：
  - `/healthz`（僅本機）回報 DB 可寫、queue 深度、最舊 queued job 的年齡、GPU 可用（`torch.cuda.is_available()` 與記憶體）、worker 最後心跳時間。
  - 公開 webhook 服務與 localhost admin UI 分開綁定（專案已採用）。
- **告警條件建議**：
  - 最舊 queued job 超過 45 秒：reply token 即將逾時。
  - 驗簽失敗突增：secret 可能被重發，或遭受攻擊。
  - reply 回 "Invalid reply token" 的比例升高。
  - worker 心跳超過 60 秒。
  - 磁碟剩餘低於門檻。
  - 連續 N 次 LINE API 5xx 或 429。
- **告警通道**：
  - 避免用 LINE push 對研究者告警，因為會計費且與受測帳號混用；建議用 email 或 Windows 通知。
  - 若用 LINE 告警，應使用另一個 channel（本報告推論）。
- **Windows 單機**：
  - 用服務化（NSSM 或工作排程器）設定開機自動啟動與 crash 重啟。
  - 關閉自動重開機時段或排定維護窗。
  - UPS 與電源設定避免休眠。
  - tunnel 或反向代理要自動重連，並不得改寫 body（見 A1）。
- **零自動化原則對齊**：監控只告警，不觸發自動重新訓練或自動部署模型，符合專案原則。shadow model 失敗不得影響主回覆流程，也不計入主 KPI。

### Gaps
- 單機 webhook 服務可用性的實證研究或權威指南：本次**未檢索**，以上屬推論與業界慣例。

---

## 附：變更時間軸（僅列有證據者）

| 日期 | 事件 | 來源 |
|---|---|---|
| 2016-11-01 | followers 統計資料起算日（之前為 out_of_service） | [REF](https://developers.line.biz/en/reference/messaging-api/) [A] |
| 2017-03-01 | message deliveries 統計起算日 | [REF](https://developers.line.biz/en/reference/messaging-api/) [A] |
| 2018-03-31 | reply/push 等發送數計數系統開始運作 | [REF](https://developers.line.biz/en/reference/messaging-api/) [A] |
| 2022-03-07 公告；2022-04 上旬上線 | Webhook 重送機能加入 Messaging API，webhook event object 同步變更（`deliveryContext.isRedelivery`） | [LINE news ja/38](https://developers.line.biz/ja/news/38/) [A]（日期來自搜尋摘要） |
| 2023（日期未確認） | 錯誤通知改為重送停止時也寄信 | 搜尋摘要；[ERRNOTI](https://developers.line.biz/en/docs/partner-docs/error-notification/) [A]，確切日期**未找到可靠證據** |
| 2024-04-17 | 推出 loading animation API | [LINE news](https://developers.line.biz/en/news/2024/04/17/loading-indicator/) [A]（日期取自 URL）；[SDK releases](https://www.github.com/line/line-bot-sdk-python/releases/latest) [E] |
| 3.x（日期未確認） | line-bot-sdk-python 3.x（`linebot.v3`，OpenAPI 生成），與 2.x 不相容，往後只維護 v3；目前需要 Python ≥3.10 | [SDK README](https://github.com/line/line-bot-sdk-python) [E]；3.0.0 釋出日**未找到可靠證據** |

**未找到可靠證據**的時間軸項目：deprecated endpoints 清單、Messaging API 版本號變更、reply token 時限的歷史變更。本次沒有讀到官方 news 的對應公告。
