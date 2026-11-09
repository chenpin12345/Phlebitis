# 讓 reply 扛成本、讓本機守照片：靜脈炎 LINE 研究服務設計

**結論先講。** 這個研究原型的 LINE 服務可以把每月訊息費壓到 **NT$0**，不論每月分析 100、1,000 還是 10,000 次。做法是：使用者傳照片後，系統先顯示 loading animation，在背景完成推論，再用同一個 reply token 一次回覆結果。台灣官方明文規定 **Reply API 不計費**，**reply token 只能用一次，而且必須在收到 webhook 後一分鐘內使用**（[S2 台灣官方公告](https://tw.linebiz.com/column/LINEOA-2026-Price-Plan/)；[Messaging API reference](https://developers.line.biz/en/reference/messaging-api/#send-reply-message)）。真正的風險在別處，主要有四項。

第一，**經聊天傳的照片一定會先暫存在 LY Corporation（LINE）的伺服器**，官方只說「一段時間後自動刪除」，沒有公布期限，而且承認內容「可能在內部被轉換，例如縮小（shrinking）」（[Messaging API reference](https://developers.line.biz/en/reference/messaging-api/index.html.md)）。如果嚴格解讀「研究照片不上傳第三方雲端」，這條路線本身就違反原則。替代方案是用 LIFF 頁面把照片直接上傳到本機，並讓 TLS 在本機終止。

第二，webhook 必須在極短時間內回 200。錯誤統計頁把 `request_timeout` 描述為約 2 秒內沒有回應。系統必須「先驗簽、寫入 SQLite、回 200，再交給背景 worker」，並以 `webhookEventId` 去重。

第三，LINE 傳圖時的縮圖與重新編碼會造成和醫院原檔之間的系統性差異（domain shift）。

第四，在 14 位個案的規模下，任何「新模型較好」的統計結論都不成立。把金絲雀發布（canary）自動擴大到使用者，也違反「不自動上線」原則。

**價格方面要注意：台灣 LINE 官方帳號自 2026-11-01（明天）起，中用量月費由 NT$800 調為 NT$1,000，高用量由 NT$1,200 調為 NT$1,400**（皆未稅）。輕用量維持 NT$0、每月 200 則免費。只要本服務維持「全 reply」設計，就不受這次調價影響。

**法規方面要更正一點：撤回同意的權利規定在《人體研究法》第 14 條第 1 項第 6 款**，不在第 19 條。第 19 條規範的是研究材料的銷毀、保存、逾越原同意範圍的再利用，以及提供境外。

**LIFF SDK v2.20.0 至 v2.31.0 有安全問題，官方預定約 2026-11-24 起限制使用。** 若要做 LIFF，必須使用 v2.31.1 以上版本。

---

## 閱讀說明：來源分級、日期與用語

本報告只整理 2026-10-30 至 2026-10-31 完成的八份研究筆記。查閱工作中途遇到工具額度限制，所以分兩天完成。今天是 2026-10-31，以下所有「查閱日」都落在這兩天內。

**來源分級**

| 等級 | 內容 |
|---|---|
| [A] | 官方文件或主管機關（LINE Developers、LINE Biz-Solutions 台灣、全國法規資料庫、FDA、IMDRF、WHO、W3C、AHRQ、CDC、NHS 衛教單等），以及報告規範 |
| [B] | 系統性回顧、統合分析、頂尖期刊或會議論文 |
| [C] | 一般同儕審查論文 |
| [D] | 預印本 |
| [E] | 技術部落格、官方範例程式碼、論壇、新聞、廠商文件，只能作輔助 |

**文件日期**

LINE Developers 的文件頁（包括 `index.html.md` 原始 Markdown 版）**都沒有標示最後更新日**。本報告一律寫成「頁面未標更新日」，並附上查閱日。

**用語標記**

| 標記 | 意思 |
|---|---|
| **研究證據顯示** | 有 [A] 到 [C] 來源明文支持 |
| **業界慣例** | 常見工程或臨床實務，但本輪沒有同儕審查文獻佐證 |
| **本報告推論** | 作者根據引用資料推導，需要在本平台實測或交給 IRB 判斷 |

筆記中標為「僅搜尋摘要」「未逐字核對」「未找到可靠證據」的項目，本報告**保留原標記，不升級**。

**原則衝突標記**

凡與專案不可違反的原則衝突，或可能衝突，都以 ⚠ 標出，並附上本機替代方案。這些原則是：不自動訓練、不自動上線、模型建議須人工確認、不宣稱診斷能力、研究照片不上傳第三方雲端。

---

## 本段摘要

### 五大風險：成本不是問題，資料流、時限與小樣本才是

**風險一：照片的資料流（⚠ 原則衝突）**

在聊天路線中，使用者透過 quick reply 的相機或相簿按鈕傳照片，照片會以 LINE 訊息的形式先存在 LINE 平台，研究端再以 Get content 下載。官方不保證保存期限（[Get content](https://developers.line.biz/en/reference/messaging-api/#get-content)，[A]）。

如果 IRB 把原則解讀為「不得經過任何第三方伺服器」，這條路線本質上不符合原則。如果解讀為「研究端不主動上傳到第三方雲端儲存或 AI 服務」，同意書就必須揭露「照片經 LINE 傳輸並暫存於 LINE 伺服器」。

另一條路線是 LIFF 上傳頁：瀏覽器直接把照片上傳到我方伺服器，照片不經過 LINE 訊息平台。不過，如果用 Cloudflare Tunnel 或 ngrok 對外暴露，TLS 會在業者的邊緣節點（edge）解密，照片的明文會經過第三方。改用 Tailscale Funnel，或自架反向代理並在本機終止 TLS，就能避免這個問題。官方文件明載 Tailscale Funnel 的 TLS 在使用者自己的裝置上終止（[Tailscale Funnel](https://tailscale.com/kb/1223/funnel)，[A]）。

**風險二：webhook 時限與事件重複**

錯誤統計頁將 `request_timeout` 描述為 bot 伺服器約 2 秒內沒有回應（[ERRSTAT](https://developers.line.biz/en/docs/messaging-api/check-webhook-error-statistics/)，[A]）。這個數字來自頁面摘要，主要文件沒有明列，建議上線前逐字核對原頁。

重送（redelivery）**預設關閉**，重送的次數與間隔**官方不公開**，而且不保證送達。即使沒有重送，網路因素也可能讓同一事件送達兩次（[RECV](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)，[A]）。

如果在 handler 內同步推論，就會逾時、觸發重送，導致重複收件與重複推論。

**風險三：LINE 傳圖的縮圖與重新編碼**

官方承認內容「may be transformed internally, such as shrinking」（[A]）。兩篇獨立的 iPhone 實測顯示，標準畫質的長邊約為 1,478 到 1,479 px，高畫質約為 2,364 到 2,365 px（[app-liv](https://app-liv.jp/articles/121899)；[appllio](https://appllio.com/line-send-original-size-photos)，[E]）。醫院相機的原檔多半解析度更高。

Laplacian 模糊分數會隨解析度改變，所以同一個門檻不能同時套用在兩種來源上（本報告推論）。EXIF 與 GPS 會不會被保留，**沒有任何官方聲明或針對 Bot 的公開實測**。

**風險四：只放免責聲明，擋不住過度依賴**

一項 115 人的調查顯示，免責聲明對「尋求第二意見」意願的影響「modest and inconsistent」（[Denecke & Gabarron 2026](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2026.1785085/full)，[C]）。

另外，法規上判斷是不是醫療器材，看的是預期用途與功能，不是免責文字。依二手法律評論，FDA 的 CDS 指引第 1 項標準把分析醫療影像的軟體排除在 CDS 豁免範圍之外（[Covington](https://www.cov.com/en/news-and-insights/insights/2026/01/5-key-takeaways-from-fdas-revised-clinical-decision-support-cds-software-guidance)，[E→轉述 A]）。

**風險五：小樣本與上線決策（⚠ 原則衝突）**

目前 normal 類只有 9 張。假設判對 8 張，95% Wilson 信賴區間是 0.565 到 0.980，寬度約 0.42（本報告計算，見第 9 節）。

金絲雀發布在業界通常依指標自動擴大流量（[Google SRE Workbook](https://sre.google/workbook/canarying-releases/)），這直接違反「不自動上線」原則。

### 最值得先做的建議（依「預期效益 ÷ 工作量」排序）

工作量（人日）都是本報告推論的粗估。

| 排序 | 建議 | 證據等級 | 前置條件 | 工作量 | 效益 |
|---|---|---|---|---|---|
| 1 | webhook 改為「驗簽 → `INSERT OR IGNORE`（以 `webhookEventId` 去重）→ 回 200 → SQLite job 佇列 → 單一 GPU worker」，並在 Console 開啟 webhook redelivery 與 Error statistics aggregation | [A] 官方要求與建議；佇列設計屬業界慣例 | 已有的驗簽程式碼 | 1–2 | 高 |
| 2 | 改為 reply 優先：收到照片就呼叫 loading animation，背景推論完成後用原 reply token 一次回覆。逾時就改回「結果處理中＋『查看結果』postback」，不預設用 push。**不要先回「請稍候」**，那會用掉唯一的 reply token | [A]（reply 免費、一分鐘、單次；postback 帶新 reply token） | 項目 1 | 0.5–1 | 高（費用 NT$0） |
| 3 | 收到 image 事件就立即下載 Get content，原樣保存 bytes 與 SHA-256，記錄 `contentProvider`、`imageSet`、來源與裝置 metadata；`external` 類型直接拒收；Pillow 以 `formats=` 限制格式，保留 decompression bomb 防護；另存一份移除 GPS 並套用 `exif_transpose` 的工作副本 | [A]（自動刪除、410、shrinking）＋推論 | 項目 1 | 1 | 高 |
| 4 | 記錄遮罩：token、secret、`x-line-signature`、replyToken、完整 userId、照片 bytes、webhook 原始 body 都不寫入 log；token 改用 v2.1 或 stateless（JWT 版）；秘密存在 Windows Credential Manager | [A] OWASP、LINE；儲存方式屬業界慣例 | 無 | 1–2 | 高 |
| 5 | 文案改寫：第一行就是行動；每則結果都附紅旗清單，並分「住院中」與「已回家」兩種版本；「正常」結果寫成「沒有看到明顯紅腫」；不呈現分數或期別 | [C]／[B]／[A] 衛教單＋推論 | 臨床護理審定 | 2（不含審定） | 高 |
| 6 | 圖文選單（rich menu）依同意狀態做 per-user 切換；伺服器在每次收到照片時再檢查一次同意狀態 | [A] | 同意紀錄表 | 1 | 中高 |
| 7 | 同意與撤回紀錄採 append-only，並記錄文件版本、SHA-256 與 UTC 時間；撤回流程包括 exclusion list、刪除工作、在模型登錄表上標記；**不自動重訓** | [A] 法條＋推論 | IRB 核定同意書 | 2–3 | 高 |
| 8 | 化名化：`study_id` 作為主鍵；userId 只存在獨立的連結表，或以 HMAC 處理；醫院病人用一次性登錄碼綁定 | [A] userId 以 provider 為範圍＋推論 | 項目 7 | 1–2 | 中高 |
| 9 | 對外暴露改用 Tailscale Funnel 或自架反向代理，只轉送 `/webhook`；管理介面維持只綁 127.0.0.1；確認照片目錄不在 OneDrive 同步範圍 | [A] Tailscale、LINE TLS 規格；Cloudflare edge 解密屬 [E] | 網域與憑證 | 1–2 | 中高 |
| 10 | 實測 LINE 傳圖矩陣：iOS 與 Android，各測標準、高畫質、原始畫質，記錄 Bot 實際收到的像素、品質因子（QF）與 EXIF | 無公開實測（未找到可靠證據） | 測試帳號、無病人的測試照 | 1 | 中高 |
| 11 | 模型上線分階段：影子模式 → 只給審閱者看的金絲雀 → 人工簽核切換；只允許自動「回滾」到上一個已核准模型，或自動降級為「需人工確認」 | [C] silent trial；[A] GMLP／PCCP；推論 | 模型登錄表 | 2–3 | 中 |
| 12 | LIFF 上傳頁（建議在未來約 1,000 張的階段做）：SDK 版本 ≥ v2.31.1；伺服器以 ID token 驗證身分 | [A] | IRB 決定照片路線 | 5–8 | 中（現在）、高（未來） |

---
## 1. Webhook 在兩秒內只做三件事：驗簽、寫入、回 200

### 1.1 結論

webhook handler 只做三件事：

1. 拿原始位元組（raw bytes）做 HMAC-SHA256 簽章驗證（X-Line-Signature）。
2. 以 `webhookEventId` 為唯一鍵，把事件寫進 SQLite。
3. 立刻回 200。

下載照片、品質檢查、YOLO 與分類推論全部交給背景 worker。worker 完成後，用 reply token 在一分鐘內回覆。推論期間顯示 loading animation。只有 token 逾時或失效時，才改走「查看結果」postback（免費）或 push（計費）。

事件可能重複、可能亂序，也可能一次送來好幾個事件或空陣列。因此每個事件各自建一個 job，同一位使用者的 job 依 `timestamp` 序列化處理，GPU 全域只開一個推論 worker。

### 1.2 證據整理

**簽章驗證**（研究證據顯示，[A]）

- 簽章是以 channel secret 為金鑰，對 request body 做 HMAC-SHA256，結果以 base64 編碼放在 `x-line-signature` header。
- 官方要求以 UTF-8 驗證，原文是 "Don't modify data prior to verifying the signature on any request."
- 官方列出的常見錯誤：先 `json.loads` 再序列化、pretty-print、跳脫字元誤解、proxy 改寫 body、誤用 HMAC-SHA1、用錯 channel 的 secret、另一位管理員已重發 secret。
- 簽章缺漏或不符時「不處理事件、以錯誤結束」。LINE Platform 的 IP 不公開，所以應該靠驗簽，不要做 IP 限制。

出處：[Verify webhook signature](https://developers.line.biz/en/docs/messaging-api/verify-webhook-signature/)、[Development guidelines](https://developers.line.biz/en/docs/messaging-api/development-guidelines/)。兩頁都未標更新日，查閱 2026-10-31。

官方 SDK v3 的 `WebhookParser.parse()` 先驗簽，再 `json.loads`，並用 `hmac.compare_digest` 做常數時間比對。無法辨識的事件型別會包成 `UnknownEvent`，不會讓解析中斷（[line-bot-sdk-python webhook.py](https://github.com/line/line-bot-sdk-python/blob/master/linebot/v3/webhook.py)，[E] 官方 SDK）。SDK README 說明 3.x 與 2.x 不相容、往後只維護 `linebot.v3`、需要 Python ≥ 3.10（[SDK README](https://github.com/line/line-bot-sdk-python)，[E]）。3.0.0 的釋出日期**未找到可靠證據**。

**回應與非同步處理**（[A]）

- 官方原文："The bot server must return status code `200` after it receives the HTTP POST request"。
- LINE 可能送來 `events` 為空陣列的 POST，用來確認連線。
- 官方原文："We recommend that you process webhook events asynchronously."

出處：[Messaging API reference](https://developers.line.biz/en/reference/messaging-api/)、[Receiving messages](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)。

錯誤統計頁把 `request_timeout` 描述為「已送出但沒有回應」，頁面摘要寫 bot server 沒有在 2 秒內回應（[ERRSTAT](https://developers.line.biz/en/docs/messaging-api/check-webhook-error-statistics/)）。這個「2 秒」來自 WebFetch 對頁面的摘要，**上線前應打開原頁逐字確認**。RECV 與 REF 都沒有明列逾時秒數。

**重送與去重**（[A]）

- 重送預設關閉，要在 Console 的 Messaging API 分頁手動開啟。只有 bot 沒有回 2xx 時才會重送。
- 官方原文："The number and interval of the webhook redelivery aren't disclosed"，而且可能不經通知變更。
- 重送不保證送達。如果重送量暴增影響平台，LINE 可能強制關閉重送。
- 重送事件和原事件只差在 `deliveryContext.isRedelivery`。`webhookEventId`（ULID 格式）不變。
- 官方建議以 `webhookEventId` 偵測重複，因為網路路由也可能造成重複送達。
- 如果 bot 長期收不到 webhook，平台可能暫停發送。

出處：[RECV](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)。

重送功能的時間線：2022-03-07 日文公告「2022 年 4 月上旬起新增 Webhook 再送機能」（[LINE news ja/38](https://developers.line.biz/ja/news/38/)，[A]）。這個日期來自搜尋摘要，筆記沒有逐頁讀取。

**Reply token**（[A]）

- 原文："Reply tokens can only be used once."
- 原文："Reply tokens must be used within one minute after receiving the webhook."
- 這個時限可能不經通知變更。
- 使用過期或已用過的 token 會回 400 "Invalid reply token"，訊息不會送出。
- 重送事件中的 reply token "can be used except in certain cases"，但 certain cases 的內容**未找到可靠證據**。
- `mode: standby` 的事件不帶 reply token，bot 不應該發訊息。

出處：[REF › Send reply message](https://developers.line.biz/en/reference/messaging-api/#send-reply-message)、[RECV](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)。

**Loading animation**（[A]）

- 端點：`POST https://api.line.me/v2/bot/chat/loading/start`。
- `loadingSeconds` 介於 5–60 秒，必須是 5 的倍數，預設 20。只支援一對一聊天。
- 時間到，或 OA 送出新訊息時，動畫就消失。
- 只有使用者正在看聊天畫面時才會顯示。
- API 一律回 202，包括使用者已封鎖或已刪除帳號的情況。
- 速率上限 100 req/s。需要 LINE iOS／Android 13.16.0 以上版本。

出處：[Use loading indicator](https://developers.line.biz/en/docs/messaging-api/use-loading-indicator/)、[REF › Display a loading animation](https://developers.line.biz/en/reference/messaging-api/#display-a-loading-indicator)。這項功能在 2024-04-17 推出，日期取自 news URL 路徑（[LINE news 2024-04-17](https://developers.line.biz/en/news/2024/04/17/loading-indicator/)）。

**事件順序與內容**（[A]）

- 原文："the order of webhook events you receive can be different from the order the events occurred"，應以 `timestamp` 判斷先後。
- 一次 POST 可能包含多個事件。
- `destination` 是接收方 bot 的 user ID。
- imageSet 中的多張圖片會以未定義的順序送達。
- bot 必須容忍非破壞性變更，例如新增欄位、新增 enum 值、屬性順序改變。

出處：[RECV](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)、[REF](https://developers.line.biz/en/reference/messaging-api/)、[GUIDE](https://developers.line.biz/en/docs/messaging-api/development-guidelines/)。

**Push 冪等**（[A]）

- `X-Line-Retry-Key` 只適用於 push、multicast、narrowcast、broadcast。
- 格式是自行產生的 UUID，首次請求就要帶上，在首次請求後 24 小時內有效。
- 重複的 key 回 409，並附 `x-line-accepted-request-id`。
- 只在 500 或網路逾時時重試。
- retry key 只防止重複，不保證送達。

出處：[Retrying API request](https://developers.line.biz/en/docs/messaging-api/retrying-api-request/)。

### 1.3 反面證據與限制

- **逾時秒數不明確。** 主要文件沒有寫逾時秒數，只有錯誤統計頁的「約 2 秒」摘要。也沒有找到正式的 SLA 數字（未找到可靠證據）。
- **重送不可靠。** 重送不保證送達，可能被平台強制關閉，次數與期間也不公開。所以開了重送，仍不能把它當成「停機也不會漏件」的保證。
- **重送事件的 reply token 不一定能用。** 官方說在 certain cases 不可用，卻沒有列出是哪些情況。即使可用，重送往往已經超過一分鐘。
- **loading animation 的 202 不代表使用者看到動畫。** 一篇 [E] 日文實測曾遇到 API 回傳成功、畫面卻沒顯示，清除快取後才恢復（[classmethod](https://dev.classmethod.jp/articles/try-to-use-line-messaging-api-of-indicating-loading-animation/)）。
- **佇列設計沒有學術文獻佐證。** 「先持久化、再回 2xx、背景處理、冪等消費」是 webhook 消費端的常見模式，屬於**業界慣例**，本輪沒有找到同儕審查文獻。
- **官方範例有缺陷。** 官方 FastAPI 範例用 `headers['X-Line-Signature']` 直接索引，header 缺漏時會拋出未處理的 KeyError，最後變成 500（[fastapi-echo/main.py](https://github.com/line/line-bot-sdk-python/blob/master/examples/fastapi-echo/main.py)，[E]）。不能照抄。
- **未知數。** 單次 webhook 最多包含幾個事件，**未找到可靠證據**。429 回應是否帶 `Retry-After`，也**未找到可靠證據**。

### 1.4 對本專案的適用性

**現在（14 位個案）：適用。** 流量極低，rate limit 不是瓶頸。但這台 Windows 單機會停機、重開機、跑 Windows Update，所以重送與去重不可省略。推論需要好幾秒（品質檢查、YOLO、EfficientNet 或 DINOv2），**絕不能在 handler 內同步執行**。

**未來（約 1,000 張，或每月上萬次分析）：適用，且更重要。** 若出現尖峰，GPU 佇列會讓部分 job 逼近一分鐘的 token 時限。這時要依「剩餘 token 壽命」排定優先順序，並啟用 postback 退路（本報告推論）。

### 1.5 實作要點

這個流程對應 FastAPI、SQLite 與 line-bot-sdk v3。以下虛擬碼是本報告推論。

```python
# webhook-svc：獨立 FastAPI app，只註冊這一條路由；docs_url=None, redoc_url=None, openapi_url=None
@app.post("/webhook/{random_path}")
async def callback(request: Request):
    raw = await request.body()                       # 1) 取原始 bytes；不要用 Pydantic body 參數
    if len(raw) > 1_000_000: raise HTTPException(413)
    sig = request.headers.get("x-line-signature")    # 2) 用 .get，缺漏就回 400，避免 KeyError 變 500
    if not sig or not hmac.compare_digest(
        base64.b64encode(hmac.new(SECRET, raw, sha256).digest()).decode(), sig):
        log.warning("sig_fail")                      # 不記 body、不記簽章
        raise HTTPException(400)
    payload = json.loads(raw)                        # 3) 驗簽通過後才 parse
    with db:                                         # 4) 同一個 transaction
        for ev in payload.get("events", []):         #    空陣列直接略過
            cur = db.execute("INSERT OR IGNORE INTO webhook_events(webhook_event_id, ...) VALUES (?, ...)", ...)
            if cur.rowcount == 1 and ev.get("mode") == "active":
                db.execute("INSERT INTO jobs(id, webhook_event_id, user_pid, message_id, reply_token_enc, webhook_received_at, status) VALUES (...,'queued')")
    return Response(status_code=200)                 # 5) 立刻回 200（目標 <100 ms）
```

**資料表**

- `webhook_events`：`webhook_event_id` 為 PRIMARY KEY，另存 `is_redelivery`、`type`、`timestamp`、`received_at` 與 `status`。
- `jobs`：欄位包括 UUID、`webhook_event_id` UNIQUE、`reply_token`（存放時加密，或只放記憶體）、`webhook_received_at`、`status`、`attempts`、`next_attempt_at`、`retry_key`。`status` 的值為 queued、downloading、inferring、replied、pushed、postback_offered、failed、dead。
- SQLite 開 WAL 模式。worker 用 `UPDATE … WHERE status='queued' … RETURNING` 搶佔 job。程序啟動時，把卡在 downloading 或 inferring 的 job 收回成 queued。

**worker 流程**

1. 呼叫 loading animation，`loadingSeconds` 設 20–30。
2. 下載 Get content。
3. 做品質檢查。
4. 推論。
5. 若 `now - webhook_received_at < 約 50 秒`，用 reply 回覆，最多 5 個訊息物件：結果卡、紅旗提醒、quick reply。
6. 否則改走第 8 節的退路。

**排程**

- 單一 GPU worker。佇列依「token 最早到期者優先」排序。
- 同一位使用者的 job 依 `timestamp` 排序。
- 收到 `mode=standby` 的事件只記錄、不回覆。
- 未知事件型別只記錄並略過，不回非 2xx。

**影子模型**

影子模型在 reply 送出之後才在同一個 worker 的低優先佇列執行。它的失敗不影響主流程，也不計入主要 KPI。

完整的時序圖見本報告「交付一」。

### 1.6 驗證方法

1. **簽章單元測試。** 測試資料包含 emoji、`\n`、CRLF、跳脫字元的 body，以及錯誤的 secret 和缺漏的 header。預期結果分別是 400 與 400，不會出現 500。
2. **重複事件測試。** 同一個 `webhookEventId` 送三次，只會產生一筆 job。
3. **停機回復演練。** worker 在 inferring 階段被強制結束，重啟後 job 會被收回並重跑，而且只回覆一次。
4. **時限測試。** 人為延遲推論 65 秒，驗證會走 postback 或 push 退路，並記錄 400 "Invalid reply token"。
5. **Console 檢查。** 開啟 Error statistics aggregation 一週，`request_timeout` 應為 0。
6. **每日對帳。** 自建的 replied 數與 `GET /v2/bot/message/delivery/reply?date=` 回傳數比對，差異應為 0。這個 API 通常隔日才算完（[REF](https://developers.line.biz/en/reference/messaging-api/)）。
7. **整合測試。** 先在工作台內的 LINE 模擬器跑完整流程（不發送真實訊息），再用一個測試帳號做真機測試。

### 1.7 風險與緩解

| 風險 | 緩解 |
|---|---|
| 另一位管理員重發 channel secret，導致驗簽全部失敗 | 把「400 激增」設為告警條件，並寫一份 secret 輪替 runbook（第 7 節） |
| 反向代理或 tunnel 改寫 body | 部署後用 Console 的 Verify 與 test webhook 端點確認；測試資料包含 emoji |
| GPU 排隊太久，token 過期 | 告警條件設為「最舊 queued job 超過 45 秒」；啟用 postback 退路 |
| 重送造成研究統計灌水 | 所有收件統計以 `webhook_event_id` 去重，並排除 `isRedelivery` 的事件 |
| reply 遇到 5xx 或逾時，無法確定是否已送達（reply 不支援 retry key） | 記錄 `x-line-request-id`；一分鐘後把狀態標為「未知」，不重送 |

---

## 2. 台灣計費：Reply 免費、push 按人數計，2026-11-01 起月費調漲

### 2.1 結論

台灣 LINE 官方帳號（LINE Official Account，LINE OA）**明文規定 Reply API、一對一聊天、自動回應、AI 自動回應、加入好友歡迎訊息都不計費**。Push、Multicast、Broadcast、Narrowcast 則按「收訊人數」計算則數。一次請求裡放 1 到 5 個訊息物件，都只算 1 則。

自 **2026-11-01** 起，三個方案的月費與免費則數（皆未稅）：

| 方案 | 月費 | 每月免費則數 | 加購 |
|---|---|---|---|
| 輕用量 | NT$0 | 200 則 | 不可加購 |
| 中用量 | NT$1,000（原 NT$800） | 3,000 則 | 不可加購 |
| 高用量 | NT$1,400（原 NT$1,200） | 6,000 則 | 前 50,000 則每則 NT$0.2，第 50,001 則起每則 NT$0.15 |

本服務只要採用「全 reply」設計，每月 100、1,000、10,000 次分析都能維持在**輕用量 NT$0**。

### 2.2 證據整理

**調價公告**（[A]）

- 公告日期 2026-09-01，生效日 2026-11-01（[S2 台灣官方公告](https://tw.linebiz.com/column/LINEOA-2026-Price-Plan/)，dateModified 2026-09-01）。
- 原文註明「下方金額說明皆為未稅價格」。
- 免費則數維持 200、3,000、6,000 則。
- 中用量「不可加購；如需發送更多訊息，需升級為高用量方案」。
- 高用量加購分兩級：當月加購的第 1 到 50,000 則每則 0.2 元，第 50,001 則起每則 0.15 元。原文寫「超過免費訊息則數後，才會依上述級距計算加購訊息費用」。

**過渡規定**（[A]，同一份公告）

- 2026-10-27 之後仍使用中用量或高用量方案，即視為同意新價格。
- 信用卡自動續繳者，11 月 1 日依新價扣款。
- 系統維護期間「變更訊息則數上限」等功能暫停。維護時段為 2026-10-28 08:00 至 2026-11-02，以及 2026-11-24 08:00 至 2026-11-25。
- 「付費週期部分沒有調整」。

**官方計算機程式碼**（[A]）

台灣官網的計算機 JS 中，2026-11-01 起的區塊為 `moderateFreeNew26 = 1000`、`highFreeNew26 = 1400`，加購的公式是 `min(extra,50000)*0.2 + max(0,extra-50000)*0.15`，與公告一致（[S5 cal.js](https://vos.line-scdn.net/lbstw-static/assets/frontend/js-20260924-modified/cal.js)，版本路徑標記為 2026-09-24）。

**舊價**（2026-10-31 以前）

| 方案 | 月費 | 免費則數 | 加購 |
|---|---|---|---|
| 輕用量 | NT$0 | 200 則 | 不可加購 |
| 中用量 | NT$800 | 3,000 則 | 不可加購 |
| 高用量 | NT$1,200 | 6,000 則 | 6,001 至 25,000 則每則 0.2 元，之後逐級遞減至 0.066 元 |

出處：[S3 官方 FAQ](https://tw.linebiz.com/faq/oa-price/message-price-list/)、[S5 cal.js](https://vos.line-scdn.net/lbstw-static/assets/frontend/js-20260924-modified/cal.js)，[A]。

**不計費與計費項目**（[A]）

- 台灣官方列出的不計費項目：「一對一聊天訊息、自動回應訊息、加入好友的歡迎訊息、Messaging API 中的 Reply API 功能」（[S1](https://tw.linebiz.com/service/account-solutions/line-official-account/)）。2026 年的公告另外列出 AI 自動回應訊息（[S2](https://tw.linebiz.com/column/LINEOA-2026-Price-Plan/)）。
- LINE Developers 列出的計費方式為 Push、Multicast、Broadcast、Narrowcast，Reply 不計。
- 原文："The number of messages is counted by the number of people you send a message to."
- 原文："The number of message objects in a request doesn't affect the number of messages sent."
- 傳給已封鎖使用者或不存在的 user ID 不計費。

出處：[Messaging API pricing](https://developers.line.biz/en/docs/messaging-api/pricing/)。

**群發與個別訊息**（[A]）

- 後台群發每次最多 3 個對話框。Push API 每次最多 5 個對話框。
- 一則多頁訊息最多 9 頁，只算 1 個對話框。

出處：[S4 官方 FAQ](https://tw.linebiz.com/faq/oa-price/how-to-calculate-message-expense/)。

**計費時區**（[A]）

原文：「系統計算的時區為日本時區（GMT+9:00），台灣時間 23:00 起傳送的訊息會被計算到隔日」（[S1](https://tw.linebiz.com/service/account-solutions/line-official-account/)）。

**超額**（[A]）

- 原文："When you exceed the limit of messages that can be sent in a month, an error response will be returned and the messages won't be sent."
- 超額時回 429，訊息為 "You have reached your monthly limit."
- 官方註明，有時即使還有剩餘則數也可能收到 429。進行中的 narrowcast 也可能暫時扣光剩餘額度。

出處：[Messaging API pricing](https://developers.line.biz/en/docs/messaging-api/pricing/)、[REF](https://developers.line.biz/en/reference/messaging-api/)。

**監控 API**（[A]）

- `GET /v2/bot/message/quota` 回傳當月上限，包含 OA Manager 發送的訊息。
- `GET /v2/bot/message/quota/consumption` 回傳 `totalUsage`，官方說這是近似值（approximate）。

出處：[REF](https://developers.line.biz/en/reference/messaging-api/)。

**調價時間線**

| 時間 | 內容 | 出處 |
|---|---|---|
| 2018-11-09 | 預告「官方帳號 2.0」三方案以量計價 | [TechNews](https://technews.tw/?p=411309)，[E] |
| 2020-03-01 | 新版官方帳號全面啟用。輕用量 0 元／500 則；中用量 800 元／4,000 則；高用量 4,000 元／25,000 則 | [INSIDE](https://www.inside.com.tw/article/19061-line-new-fee-brand)，[E]；與 [S5](https://vos.line-scdn.net/lbstw-static/assets/frontend/js-20260924-modified/cal.js) 的原始區塊一致，[A] |
| 2023 | 免費則數下調、中用量不可加購、高用量月費降為 1,200 元 | 數字見 [S3](https://tw.linebiz.com/faq/oa-price/message-price-list/)，[A]；日期只有 [E] 來源，[FIRST LINE](https://help.firstline.cc/feature/channels/line/pricing) 寫「更新時間為 2023年9月」。官方公告原文與確切生效日**未找到可靠證據** |
| 2026-09-01 公告，2026-11-01 生效 | 中用量與高用量月費調漲；高用量加購改為兩級距 | [S2](https://tw.linebiz.com/column/LINEOA-2026-Price-Plan/)，[A] |

### 2.3 反面證據與限制

- **loading animation 是否計費。** 官方沒有明文說「免費」。本報告推論它不計費，理由是它不是訊息發送 API，也不在計費清單內。這一點**未找到可靠證據**。
- **其他費用。** 認證帳號（藍盾）、企業帳號（綠盾）、LINE Login、LIFF、LINE MINI App 在台灣的費用：**未找到可靠證據**。
- **營業稅。** 5% 營業稅是本報告的估算假設，**未經本次官方來源查證**。實際以 LINE 開立的電子發票為準。
- **聊天記錄保存。** 工商時報報導，未升級的官方帳號只保留近 6 個月聊天記錄，「聊天進階方案」每月 NT$100 可保存 5 年（[工商時報 2026-04-15](https://www.ctee.com.tw/news/20260415701121-430502)，[E]）。官方服務頁只寫「儲存2024年1月1日起的聊天記錄」（[S1](https://tw.linebiz.com/service/account-solutions/line-official-account/)）。兩者描述角度不同，官方頁沒有列出進階方案價格。本報告推論：研究紀錄不能依賴 OA Manager 的聊天記錄，必須由本機自行保存。

### 2.4 對本專案的適用性

**現在：適用。** 採全 reply 設計就能留在輕用量 NT$0。研究團隊人工追蹤個案時，用 OA Manager 的一對一聊天，這部分免費。

**未來：適用。** 即使每月 10,000 次分析，只要每月 push 不超過 200 則，仍然是 NT$0。

如果研究設計需要主動提醒，例如每月問卷，push 的數量就決定方案：

| 每月 push 則數 | 方案 | 月費（新價） |
|---|---|---|
| 不超過 200 | 輕用量 | NT$0 |
| 201 至 3,000 | 中用量 | NT$1,000 |
| 超過 3,000 | 高用量 | NT$1,400 起 |

### 2.5 實作要點

1. **不要先回「請稍候」。** 那會用掉唯一的 reply token，結果就只能改用 push。
2. **逾時退路用 postback，不用 push。** 退路先用 reply 回一則「結果處理中」，附「查看結果」postback 按鈕。postback 事件帶有新的 reply token（[REF](https://developers.line.biz/en/reference/messaging-api/)，[A]）。
3. **讓使用者主動查詢。** 圖文選單放「我的最近結果」postback 按鈕，取代主動推播。
4. **預算警戒。** 每天以 `quota` 與 `consumption` 檢查額度，接近上限時自動降級為只走 postback。在輕用量方案下，push 超過 200 則就會回 429，不要重試 429。
5. **月底時區。** 台灣時間每月最後一天 23:00 以後發出的 push，會算到下個月。
6. **方案異動的維護時段。** 2026-11-24 08:00 至 11-25 是官方維護時段，期間方案異動與「變更訊息則數上限」功能會暫停（[S2](https://tw.linebiz.com/column/LINEOA-2026-Price-Plan/)）。

### 2.6 驗證方法

- 每月 1 日（日本時間）匯出 `consumption`。
- 每日以 `GET /v2/bot/message/delivery/push?date=` 取得 push 發送數，與本機紀錄的 push 數對帳。
- 若採全 reply 設計，push 數應長期為 0 或接近 0。
- 在 OA Manager 確認方案為「輕用量」，並截圖存檔，作為研究成本紀錄。

### 2.7 風險與緩解

| 風險 | 緩解 |
|---|---|
| 系統預設用 push 補發，在輕用量下第 201 則起失敗，例如每月 1,000 次分析時有 800 則送不出（本報告推論） | 退路一律用 postback；push 只限人工核准的例外 |
| 以為 reply 的訊息物件數會影響費用 | 不會影響費用，但一次最多 5 個訊息物件，而且只會顯示最後一則訊息的 quick reply（[Use quick replies](https://developers.line.biz/en/docs/messaging-api/using-quick-reply/)，[A]） |
| 方案被誤改為中用量或高用量，自動依新價扣款 | 每月檢查方案；改方案前須經研究主持人核准 |

---

## 3. 圖片內容：一收到就原樣保存，並把 LINE 縮圖當成一種 domain shift

### 3.1 結論

用 `GET https://api-data.line.me/v2/bot/message/{messageId}/content` 取得的內容，會在「一段時間後自動刪除」，期限不公開。官方也承認內容可能被縮小。因此：

- **收到 webhook 就立刻下載，原樣保存 bytes 並計算 SHA-256。**
- 推論只用完整檔，不用 preview。
- `external` 類型的圖片直接拒收。
- EXIF 和 GPS 是否被保留沒有官方說法，一律自行檢查，並移除 GPS。

LINE 預設的標準畫質會把長邊縮到約 1,478 px，而且重新編碼。這是醫院原檔與 LINE 照片之間的系統性差異。評估時必須依來源分層。

### 3.2 證據整理

**Get content 的官方行為**（[A]，出自 [Messaging API reference 的 Markdown 版](https://developers.line.biz/en/reference/messaging-api/index.html.md)，頁面未標更新日，查閱 2026-10-31）

- 原文："Content is automatically deleted after a certain period from when the message was sent"，期限不保證。
- 原文："Content sent by users may be transformed internally, such as shrinking."
- 內容準備中回 202；內容不存在回 404；使用者收回訊息（unsend）時回 410 "The content is gone"。
- Preview 端點 `/content/preview` 原文為 "converted to a smaller data size than the original content"。對非影像訊息呼叫會回 400。
- Transcoding 端點只適用於影片與音訊，對圖片呼叫會回 400。
- `contentProvider.type = line` 表示使用者傳送，要用 Get content 取得。`external` 表示圖片是 URL，伺服器 "isn't provided by LY Corporation"。
- `imageSet` 只在一次同時傳多張時出現，`index` 從 1 起算，原文 "The webhooks are delivered in an undefined order"。
- Get content 在 rate limit 表中沒有專屬的一列。依表格推定它適用「Other API endpoints 2,000 req/s」，但官方沒有直接寫。
- 單檔大小上限：**未找到可靠證據**。

**網域變更**

部分端點的網域從 api.line.me 改為 api-data.line.me，2019-11-08 公告，要求 2020-04-30 前更新（[LINE Developers News](https://developers.line.biz/en/news/tags/messaging-api)，[A]）。

**LINE App 的傳圖畫質**（[E] 實測，兩篇都只測 iPhone）

| 實測 | 原圖 | 標準畫質 | 高畫質 | 原始畫質（ORIGINAL） |
|---|---|---|---|---|
| [app-liv](https://app-liv.jp/articles/121899)（最後更新 2025-11-06），iPhone XS MAX | 3024×4032、2.54 MB | 1108×1478、283 KB | 1774×2364、744 KB | 3024×4032、1.9 MB |
| [appllio](https://appllio.com/line-send-original-size-photos)（2025-03-02），iPhone 11 Pro Max | 3024×4032、3.7 MB | 1109×1479、604 KB | 1774×2365、1.5 MB | 10 MB 的圖仍降為 5.3 MB；6 到 7 MB 的圖則無損送出 |

appllio 另外記錄到 Android 12（AQUOS sense6）收到的檔案約 349 KB，但沒有給像素數。

兩篇的長邊數字幾乎一致，可信度相對較高。但 **Bot 透過 Get content 收到的像素，是否等於傳送端選的畫質，沒有任何公開實測**。

相簿的原始畫質上限 20 MB、1 億像素，這是「相簿」功能的規格，不是聊天傳送（[LINE Help](https://help.line.me/line/smartphone/sp?contentId=20000248&lang=en)，[A]，僅搜尋摘要）。

**內建相機與相簿的差異**

LINE 聊天室內建相機是否預設套用美肌、濾鏡或不同的壓縮方式：**未找到可靠證據**。

以「檔案」方式傳送 .heic 時會原樣送出（[fileconv](https://fileconv.pages.dev/en/blog/heic-share-tips)，[E]，單一來源）。以「照片」方式傳送時是否轉成 JPEG、色彩描述檔是否轉換：**未找到可靠證據**。

**EXIF**

沒有 LINE 官方聲明。[E] 文章說法不一：有的說 LINE 會刪除位置資訊（[dime.jp](https://dime.jp/genre/1974458/)，僅搜尋摘要），而且說的是 App 對 App 的傳送，不能直接推到 Messaging API。Orientation 的處理方式：**未找到可靠證據**。

**對模型表現的研究證據**

- 皮膚科模型在旋轉、亮度、對比、水平翻轉之下，有 6.5% 到 22% 的病灶預測翻轉；VAMC-T 資料集為 15.8%。同一次就診補拍的照片，有 30%（24/79）預測不一致。Test-time augmentation 沒有改善 AUROC（[Young et al., npj Digit Med 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC7820258/)，[C]）。
  - 7 組測試資料中有 5 組是刻意選自不同情境的外部驗證。
  - **文中沒有說明是否以病人為單位切分**，資料洩漏風險無法排除。
  - 沒有測 JPEG 壓縮或模糊。
- 4 個 ImageNet 分類網路對模糊與雜訊敏感，對一般品質範圍的 JPEG 相對穩健（[Dodge & Karam, QoMEX 2016](https://arxiv.org/abs/1604.04004)，[C／會議]）。這是自然影像，不是醫學影像。
- 白平衡錯誤造成的色偏會降低 DNN 表現，一般的色彩擴增無法模擬這種誤差。作者提出 WB emulation 擴增（[Afifi & Brown, ICCV 2019](https://openaccess.thecvf.com/content_ICCV_2019/html/Afifi_What_Else_Can_Fool_Deep_Learning_Addressing_Color_Constancy_Errors_ICCV_2019_paper.html)，[B]）。
- 數位病理的 CNN 在壓縮比 24:1 以內仍穩健；用低品質影像訓練，可改善同等壓縮下的表現（[PMC7113072](https://pmc.ncbi.nlm.nih.gov/articles/PMC7113072/)，[C]）。
- 遠距皮膚科中病人自拍照片的品質：皮膚科醫師認為「品質足夠」的比例是 62.2%，「有助決策」是 55.1%。另一項研究中 91.2% 的照片品質足夠，不佳的主因是失焦（[eScholarship](https://escholarship.org/content/qt1vs9c5n5/qt1vs9c5n5.pdf)；[JMIR Dermatol 2022](https://derma.jmir.org/2022/3/e37517/)，[C]，僅摘要）。
- 以照片判斷靜脈炎的 AI：只找到一項臨床試驗登錄，**尚無結果**（[NCT07889895](https://clinicaltrials.gov/study/NCT07889895)，[A] 登錄資料）。
- 直接研究「經 LINE 或 WhatsApp 傳送後，皮膚或傷口 AI 表現」的同儕審查論文：**未找到可靠證據**。

### 3.3 反面證據與限制

- **壓縮也可能有害。** 有研究顯示，訓練與推論時某些 JPEG 品質因子的組合，反而對病理分類不利（[TUM portal，MICCAI 2022 workshop](https://portal.fis.tum.de/en/publications/deep-learning-on-lossily-compressed-pathology-images-adverse-effe/)，[C]，僅搜尋摘要）。「用模擬壓縮做擴增」不保證有效。
- **大部分證據不是皮膚臨床照片。** 證據來自自然影像、病理與皮膚鏡；紅斑分期對色彩誤差有多敏感，**未找到可靠證據**。
- **實測樣本窄。** 兩篇畫質實測都是 iPhone。Android 各品牌在各種畫質下的像素數與 JPEG 品質因子：**未找到可靠證據**。

### 3.4 對本專案的適用性

**現在（約 120 張、14 人）：有條件適用。** 「立即下載、原樣保存、記錄 metadata、移除 GPS」可以馬上做，效益高。但依來源（醫院或 LINE）分層的評估幾乎沒有統計檢定力，因為來源差異可能和病人差異、分期分布混雜在一起。現在只適合兩種分析：

- 描述性比較。
- 「同一張照片，模擬 LINE 壓縮後，預測是否翻轉」的壓力測試，做法參考 Young 2021。

不能下「LINE 照片表現較差」的結論（本報告推論）。

**未來（約 1,000 張、三類平衡）：適用。** 這時可以做依來源與裝置分層的指標並附信賴區間，也可以做 leave-source-out 驗證。前提是**以病人為單位切分**，同一位病人不同日期、不同手（LH、RH、LL、RL）的照片都必須放在同一側。

### 3.5 實作要點

以下是本報告推論與業界慣例。

**1. 保存**

收到 webhook 就呼叫 Get content，用串流方式讀取並設上限，例如 20 MB。LINE 的圖片大小上限本輪沒有查到。遇到 202 或 5xx 時，用指數退避重試 3 次。bytes 原樣寫檔，**不要先用 PIL 重存**。同時記錄以下欄位：

| 欄位類別 | 欄位 |
|---|---|
| 識別 | `sha256`、`message_id`、`imageSet.id/index/total`、`contentProvider.type`、`webhook timestamp`、`user_pid`（HMAC 後的 userId） |
| 檔案 | `magic_format`、`width/height`、`bytes`、`jpeg_qf_est`（以 JPEG 量化表估計） |
| EXIF | `exif_present`、`orientation`、`has_gps`（布林值，不存座標） |
| 來源 | `source_channel`，值為 hospital_camera、line_oa 或 line_file |

**2. 工作副本**

用 Pillow 開啟時加 `Image.open(buf, formats=["JPEG","PNG"])`，接著 `verify()`，再重新開檔 `load()`。把 `DecompressionBombWarning` 升級為錯誤，**不可**設 `MAX_IMAGE_PIXELS=None`（[Pillow 13.0.0 docs](https://pillow.readthedocs.io/en/stable/reference/Image.html)，[A]）。然後做 `ImageOps.exif_transpose`，移除 GPS，以隨機 UUID 命名另存。模型只讀工作副本。

原始 bytes 可能含 GPS，要依 IRB 或資料管理計畫加密，並限制存取。

**3. 品質門檻依來源調整**

Laplacian variance 先把影像縮到固定長邊（例如 1,024 px）再計算，避免 LINE 的約 1,478 px 和醫院的約 4,032 px 分數無法比較。

**4. LINE 退化擴增**

先完成實測矩陣（見 3.6），再把醫院原檔縮到實測的長邊，並以實測的品質因子重新編碼，當成訓練擴增與壓力測試資料。[E] 文章的 1478 與 2364 只作為初始值。**訓練一律由人工啟動**，符合「不自動訓練」原則。

**5. 色彩**

訓練時加入 WB emulation 擴增（Afifi 的 WB_color_augmenter，或色溫與 tint 抖動）。拍照指引寫明不用濾鏡、不編輯。

**6. imageSet**

一次傳多張時，每張各自分析、各自用自己的 reply token 回覆。以 `imageSet.id` 加 `index` 重組，不依到達順序。

**7. 收回訊息**

收到 unsend 事件（Get content 回 410）時，觸發這張照片的研究資料刪除流程，與「撤回同意」的統計分開記錄（[RECV](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)，[A]，官方建議從顯示與儲存中移除）。

### 3.6 驗證方法

1. **實測矩陣。** 在沒有病人的環境下，用含 GPS 的測試照（建議同時放灰卡）實測。設備至少 2 台 iOS 加 2 台 Android（不同品牌）。每台各用標準畫質、高畫質、原始畫質傳送「照片」，再以「檔案」方式各傳一次。記錄 Bot 收到的像素、品質因子、EXIF 欄位（GPS、DateTimeOriginal、Make/Model、Orientation）與色彩描述檔。
2. **翻轉率壓力測試。** 把現有醫院照片依實測參數模擬 LINE 退化，計算預測翻轉率，以病人為單位彙總。
3. **分層報告。** 每次評估都依 `source_channel` 分層，並標示樣本數與 Wilson 信賴區間。

### 3.7 風險與緩解

| 風險 | 緩解 |
|---|---|
| 色偏或白平衡影響紅斑判讀（ICCV 證據，iOS 與 Android 色彩流程不同） | WB 擴增；拍照指引；評估依裝置分層 |
| 模糊 | 自動品質檢查加上重拍回覆 |
| 解析度下降，影響 YOLO 小目標與 Laplacian 門檻 | 依來源設定門檻 |
| JPEG 量化 | 對 224 px 的分類器影響可能最小 |
| GPS 外洩 | 只在工作副本移除；原檔加密 |
| 內容在下載前就被刪除 | 立即下載；失敗時回覆請使用者重傳 |

風險排序是本報告推論：色偏與白平衡第一，模糊第二，解析度下降第三，JPEG 量化第四。

---
## 4. 使用者介面：照片走哪條路，決定介面組合

### 4.1 結論

選介面組合之前，要先決定一件事：**照片可不可以經過 LINE 平台傳輸**。

如果 IRB 允許，而且同意書會揭露這一點，現階段最快的組合是：

- 圖文選單（rich menu）依使用者切換，分成「同意前」與「同意後」兩套；
- quick reply 提供「拍照」（camera action）和「從相簿選」（cameraRoll action）兩個按鈕；
- 伺服器在收到照片後自動做品質檢查並回覆。

如果照片不得經過任何第三方，上傳就必須改走 LIFF 頁面（或未認證的 LINE MINI App），直接傳到我方的 HTTPS 伺服器。此時 LINE 只負責入口、通知與身分驗證（ID token）。

未來規模到約 1,000 張時，建議統一走 LIFF 上傳頁。LIFF SDK 必須使用 **v2.31.1 以上版本**。LINE MINI App 的認證流程不適合研究原型。

拍照引導方面，證據最一致的做法是**即時品質回饋並讓使用者重拍**。只給書面指示，效果並不一致。

### 4.2 證據整理

**圖文選單（rich menu）**

以下規格與限制均為 [A]，查閱 2026-10-31，頁面未標更新日：

- 圖片格式：JPEG 或 PNG。寬 800–2500 px，高 ≥250 px，寬高比 ≥1.45，檔案 ≤1 MB。已設定的圖片不能替換。
- 數量上限：每個帳號用 API 最多建立 1,000 個 rich menu、1,000 個 alias。
- 每個選單最多 20 個點擊區。`chatBarText` 最多 14 字元。
- 批次綁定一次最多 500 個 user ID。

出處：[Upload rich menu image](https://developers.line.biz/en/reference/messaging-api/#upload-rich-menu-image)、[Rich menu object](https://developers.line.biz/en/reference/messaging-api/#rich-menu-object)、[Create rich menu alias](https://developers.line.biz/en/reference/messaging-api/#create-rich-menu-alias)、[Link rich menu to multiple users](https://developers.line.biz/en/reference/messaging-api/#link-rich-menu-to-users)。

顯示優先序由高到低是：

1. 以 API 綁定給個別使用者的選單（per-user）
2. 以 API 設定的預設選單
3. 在 OA Manager 設定的預設選單

per-user 選單**立即生效**。API 預設選單要等使用者重新開啟聊天室才會生效，而且「It may take up to a minute」。原文寫 "Rich menus aren't displayed on LINE for PC"。

出處：[Rich menus overview](https://developers.line.biz/en/docs/messaging-api/rich-menus-overview/)、[Use per-user rich menus](https://developers.line.biz/en/docs/messaging-api/use-per-user-rich-menus/)，[A]。

`richmenuswitch` 動作只能用在 rich menu，不能用在 Flex Message 或 quick reply。點擊後會以 postback 事件回傳 `newRichMenuAliasId`。`label` 最多 20 字元，裝置開啟無障礙功能時會被朗讀（[Rich menu switch action](https://developers.line.biz/en/reference/messaging-api/#richmenu-switch-action)，[A]）。

透過 alias 切換時，使用者看到的是優先序最高的 per-user 選單，所以對已經切換過的使用者，清除預設選單沒有效果（[Switch rich menus](https://developers.line.biz/en/docs/messaging-api/switch-rich-menus/)，[A]）。

速率限制採 token bucket，以 channel 為單位：

| 操作 | 上限 |
|---|---|
| 建立 rich menu、刪除 rich menu、刪除 alias、查詢批次狀態 | 100 次／小時（在 OA Manager 操作不計入） |
| 批次取代或解除 | 3 次／小時 |
| 取得選單清單 | 10 次／秒 |
| 個別使用者綁定或解除 | 2,000 次／秒 |

出處：[REF › Rate limits](https://developers.line.biz/en/reference/messaging-api/#rate-limits)，[A]。01 號筆記把這一項概述為「rich menu 與 alias 的建立或刪除」，04 號筆記則逐條核對了官方表格，**以官方表格為準**。

2024 至 2026 年間 rich menu 規格是否有變更：**未找到可靠證據**。

**Flex Message**

- bubble 的 JSON 上限 30 KB，carousel 上限 50 KB，carousel 最多 12 個 bubble。
- **`altText` 必填，最多 1,500 字元**（[Flex Message reference](https://developers.line.biz/en/reference/messaging-api/#flex-message)，[A]）。
- 官方說明同一則 Flex Message 會因作業系統、LINE 版本、解析度、語言與字型而呈現不同（[Send Flex Messages](https://developers.line.biz/en/docs/messaging-api/using-flex-messages/)，[A]）。
- `scaling: true` 可讓字級跟著 LINE 的字體設定縮放，需要 LINE iOS／Android 13.6.0 以上（PC 7.17.0 以上）。
- `adjustMode: shrink-to-fit` 是 best-effort，不保證生效。
- `filler` 元件已標示為 deprecated。

出處：[Flex Message layout](https://developers.line.biz/en/docs/messaging-api/flex-message-layout/)，[A]。

> **筆記間衝突的處理：altText 上限。** 08 號筆記把「altText 上限 1,500 字元」標為 [E]（日本技術部落格，未經官方核對）。04 號筆記已用官方 reference 的 Markdown 原文 grep 驗證，屬 [A]。本報告採較強的來源，**1,500 字元為 [A]**。至於文字訊息上限 5,000 字元，目前只有 [E] 廠商文件一致記載，維持 [E]。

**Quick reply**

- 每則訊息最多 13 個按鈕。一次回覆多則訊息時，只顯示最後一則的 quick reply。
- camera、cameraRoll、location 三種動作**只能用在 quick reply**。
- 一般按鈕點擊後就消失；camera 與 cameraRoll 按鈕會保留，直到使用者實際送出資料。
- 只支援 LINE for iOS 與 Android，文件沒有列 PC。
- camera 動作的 label 最多 20 字元。

出處：[Use quick replies](https://developers.line.biz/en/docs/messaging-api/using-quick-reply/)、[Camera action](https://developers.line.biz/en/reference/messaging-api/#camera-action)，[A]，查閱 2026-10-30 至 31。

**LIFF**

版本時間線（[LIFF release notes](https://developers.line.biz/en/docs/liff/release-notes/)，[A]，查閱 2026-10-30 至 31）：

| 日期 | 事件 |
|---|---|
| 2026-10-07 | 最新版 **v2.31.2** |
| 2026-09-30 | v2.31.1 安全修正 |
| — | 官方原文："LIFF v2.20.0 - v2.31.0 have been deprecated because an issue with potential security implications was identified"，並預定 "around November 24, 2026" 限制使用舊版 |

相關 news：[2026-09-30](https://developers.line.biz/en/news/2026/09/30/release-liff-2-31-1/)、[2026-10-20](https://developers.line.biz/en/news/2026/10/20/liff-sdk-issue/)。news 頁面需要 JS 渲染，未讀到全文。

其他官方規定（[A]）：

- 2019-11-11 公告、2020-02-05 生效：Messaging API channel 不能再新增 LIFF app。LIFF 要建在 LINE Login channel 上，每個 channel 最多 30 個。
- endpoint 必須是 https，不能含 URL fragment。
- 尺寸有 Compact、Tall、Full 三種。
- LIFF URL 會經過 LY 的 LIFF 伺服器轉址到開發者的 endpoint。

出處：[Adding a LIFF app](https://developers.line.biz/en/docs/liff/registering-liff-apps/)。

LIFF 瀏覽器在 iOS 是 WKWebView，在 Android 是 Android WebView。官方列出的不支援項目只有：theme-color、download 屬性、加入主畫面、Service Workers。**`<input type="file">`、`capture` 和 getUserMedia 都不在不支援清單上**（[LIFF browser 與外部瀏覽器差異](https://developers.line.biz/en/docs/liff/differences-between-liff-browser-and-external-browser/)，[A]）。

實務回報（[E]）：

- Android 14 上 `accept="image/*"` 只會開相簿（[zenn.dev](https://zenn.dev/bltsdc/articles/52fd898281d48c)）。
- iOS 17 上 `capture` 沒有開啟相機，問題未解（[Stack Overflow mirror](https://backiee.wasmer.app/http_Stackoverflow_com/questions/79630177/ios-17-camera-capture-not-working-in-next-js-with-input-type-file-capture)）。

身分驗證相關規定（[A]）：

- `liff.getIDToken()` 需要 `openid` scope，JWT 有效 1 小時。
- 官方原文要求 "Don't send the details of the user profile obtained with liff.getDecodedIDToken() and liff.getProfile() to the server"。
- 應該把 ID token 傳給伺服器，由伺服器呼叫 `POST /oauth2/v2.1/verify` 驗證。如果傳的是 access token，則用 `GET /oauth2/v2.1/verify` 加上 `GET /v2/profile`。

出處：[Using user data in LIFF apps and servers](https://developers.line.biz/en/docs/liff/using-user-profile/)、[liff.getIDToken()](https://developers.line.biz/en/reference/liff/#get-id-token)。

**LINE MINI App**

- 任何人都可以建立「未認證 MINI App」，但部分功能受限，header 會顯示 endpoint 的網域。
- 服務地區在台灣或泰國時，「only LINE MINI App channels under a certified provider can apply for the verification review」。台灣要透過 LINE Biz-Solutions 申請。
- MINI Apps 分頁只在日本提供。
- 只能用 Full 尺寸，不能隱藏 action button。

出處：[Introducing LINE MINI App](https://developers.line.biz/en/docs/line-mini-app/discover/introduction/)、[Submitting LINE MINI App](https://developers.line.biz/en/docs/line-mini-app/submit/submission-guide/)，[A]。

時間線：

| 日期 | 事件 | 出處 |
|---|---|---|
| 2023-12-13 | MINI App 的 LIFF URL 改為 `miniapp.line.me` | [Console guide](https://developers.line.biz/en/docs/line-mini-app/discover/console-guide/)，經搜尋摘要轉述 |
| 2025-02-12 | 官方宣布 LIFF 將整合進 MINI App，建議新的 LIFF app 以 MINI App 建立 | [News 2025-02-12](https://developers.line.biz/en/news/2025/02/12/line-mini-app/) |
| 2025-10-01 | MINI App 可在網頁瀏覽器中使用 | [MINI App specifications](https://developers.line.biz/en/docs/line-mini-app/discover/specifications/) |

整合的完成日期：**未找到可靠證據**。

**拍照引導**

| 研究 | 設計與規模 | 主要結果 |
|---|---|---|
| [O'Connor et al., JAMA Dermatol 2017](https://pubmed.ncbi.nlm.nih.gov/29141082/) | 40 對親子，1:1 隨機分組，[C] 小型 RCT | 給 3 步驟拍照指示，對診斷一致性**沒有顯著效果**（85% 對 80%，P=.68），影像品質分數略高（9.5 對 8.9，P=.04） |
| [Liu et al., Dermatol Online J 2024](https://pubmed.ncbi.nlm.nih.gov/39090050/) | [C] 回溯研究，**反證** | 沒有任何指示時，113 組照片中有 103 組（91.2%）品質足夠 |
| [Saade et al., Int J Telemed Appl 2025](https://pubmed.ncbi.nlm.nih.gov/41041428/) | 360 人，[C] | 診斷一致性：病人自拍 79%、簡短訓練後 84%、住院醫師拍攝 87% |
| [Gunter et al., JMIR mHealth 2016](https://pubmed.ncbi.nlm.nih.gov/27683059/) | 9 人可用性測試，[C] 極小樣本 | 只有 5 人能獨立完成；**拍傷口照片是最困難的步驟**；年長、肥胖、部位難拍的人最吃力 |
| [Vodrahalli et al., JAMA Dermatol 2023](https://pubmed.ncbi.nlm.nih.gov/36920380/)，TrueImage 2.0 | 98 位成人，單臂試驗，[C] | 即時品質回饋並讓使用者重拍，照片品質不佳的病人數減少 68.0% |
| [Zhang et al., JMIR mHealth 2021](https://pubmed.ncbi.nlm.nih.gov/34328440/) | 21 人收案、15 人納入分析，[C]，作者有專利申請的利益衝突 | 有即時回饋的一組，色卡偵測率 0.96，沒有回饋的一組 0.86 |

指引類資料：

- 英國皮膚科醫學會（BAD）的病人衛教：素色背景、光線均勻、先拍一張全景再拍 1–2 張近拍、可請信任的人代拍、"Don't add any filters or edits"（[BAD Teledermatology](https://www.skinhealthinfo.org.uk/condition/teledermatology)，[A]，2025-04 製作）。
- ISIC Delphi 共識提出 33 項建議（[PubMed 27892996](https://pubmed.ncbi.nlm.nih.gov/27892996/)，[A/C]，只讀到摘要）。

針對靜脈炎或 IV 部位自拍照片的研究：**未找到可靠證據**。

### 4.3 反面證據與限制

- **自拍品質的證據互相拉扯。** Liu 2024 顯示不給指示時多數照片也夠用，O'Connor 2017 顯示指示不影響診斷一致性。書面指引的增益小而且不穩定。
- **即時回饋的研究規模小。** 兩項研究都是單臂設計或小型可行性研究。
- **LIFF 開相機的行為沒有官方保證。** 只有 [E] 實務回報，而且 iOS 與 Android 的行為不同。
- **LIFF 的未來不確定。** LIFF 預定整合進 MINI App，但沒有時程。從 LINE Login channel 建立的 LIFF，事後不能遷移成 MINI App（[Classmethod](https://dev.classmethod.jp/articles/liff-line-login-mini-app-differences/)，[E]，未在官方 FAQ 原文驗證）。
- **PC 版不支援。** rich menu 與 quick reply 在 PC 版都不顯示或不支援。

### 4.4 對本專案的適用性

| 面向 | A：rich menu + quick reply 拍照／相簿 | B：rich menu + LIFF 上傳頁 |
|---|---|---|
| 照片路徑 | 經 LINE 訊息平台暫存，再由 Get content 下載 | 瀏覽器直接上傳到我方伺服器 |
| 「不上第三方雲端」原則 | ⚠ 嚴格解讀下不符合；寬鬆解讀下必須在同意書揭露 | 較符合，前提是 TLS 在本機終止（見第 7 節） |
| 開發量 | 低 | 中（前端、ID token 驗證、上傳 API） |
| 拍照引導 | 只能在拍照前後說明，加上事後重拍 | 可放範例圖、上傳前預覽、即時品質檢查 |
| 收集 metadata（部位、左右手、留置天數） | 需要多輪 postback，容易中斷 | 一張表單一次收齊 |
| 長者友善度 | 最熟悉的操作方式 | 多一層網頁 |
| 相機相容性風險 | 低 | 中，必須實機測試 |

（本報告推論）

**現在：A 有條件適用**，條件是 IRB 允許並揭露。IRB 不允許時，改用**簡化版的 B**：只有一張範例圖、`<input type=file accept="image/*">`，加 2–3 個必填欄位。

**未來（約 1,000 張）：B 適用。** 加入分步驟引導、上傳前在使用者端做品質檢查、metadata 表單與上傳失敗重試。quick reply 只保留為「開啟上傳頁」和「重拍提醒」的捷徑。

**認證 MINI App：兩個階段都不建議。** 台灣需要先成為 certified provider，對受邀的研究對象沒有實益。

### 4.5 實作要點

以下為本報告推論。

**兩套圖文選單**

- 預設選單（同意前）：說明研究、開始同意、隱私說明、聯絡窗口。**不放上傳按鈕。**
- 同意後：伺服器呼叫 Link rich menu to user，切換成「同意後選單」，內容是上傳照片、拍照說明、我的上傳紀錄、撤回同意。
- 撤回時 unlink，使用者回到預設選單。
- `richmenuswitch` 只用來做同一階段內的分頁，**不能當作同意門檻**。rich menu 只是介面，不是存取控制。伺服器每次收到照片都要重新檢查同意狀態。
- 部署時一次建立 2–4 個選單即可，速率上限不會成為問題。

**上傳流程（路線 A）**

1. 使用者點選單的「上傳照片」（postback）。
2. bot 回覆拍照的 3 個重點，附 quick reply：【拍照】【從相簿選】【看範例】。按鈕不超過 4 個。
3. 收到照片後回覆「已收到第 N 張」，附 quick reply：【再拍一張】【完成】。

**Flex 結果卡**

- 結果卡標題寫「研究模型分類結果（非醫療診斷）」。
- 全部 text 設 `wrap: true`，開啟 `scaling: true`，寬度用 flex 而不是固定 px。
- altText 寫成能單獨看懂的一句話，等於第一行全文。
- **結果卡不放照片縮圖。** Flex 的 image 需要 HTTPS URL，LINE 用戶端會向我方伺服器取圖，等於把研究照片的 URL 暴露給 LINE 平台。

**路線 B（LIFF）**

- SDK 鎖定 ≥2.31.1，建議 2.31.2。
- 用 LINE Login channel，而且必須**與 Messaging API channel 放在同一個 provider**（見第 6 節）。
- 用 `<input type="file" accept="image/*">`，另外提供 `capture="environment"` 的「直接拍照」按鈕。不要把 getUserMedia 自製取景框當成唯一路徑。
- 上傳時附 ID token，伺服器呼叫 `POST /oauth2/v2.1/verify` 驗證，並比對 `aud`、`exp`、`sub`。

**拍照引導內容**

- 只給 3–4 個配圖的要點，附一張「好例子」和一張「壞例子」。
- 請使用者拍一張能看出部位的全景，再拍一張 IV 部位近拍，距離約一個手掌寬。
- 建議請家人代拍。
- 關閉濾鏡和美顏，不開閃光燈，手臂放在素色毛巾上。

**PC 版提示**

在說明中寫明「請用手機 LINE 操作」。

### 4.6 驗證方法

- **可用性前測。** 找 3–5 位長者或照顧者做前測，方法參考 Macefield 2023 的認知訪談和 Gunter 2016 的 ISO 9241-11 觀察。指標是「獨立完成率」與「可標註照片比例」。
- **實機矩陣。** 測試以下組合：

  | 維度 | 項目 |
  |---|---|
  | 裝置 | iOS（多個版本）、Android（多個品牌） |
  | LINE 版本 | 涵蓋 13.6.0 以上（`scaling` 需求）與 13.16.0 以上（loading animation 需求） |
  | 字級 | 最大字級 |
  | 介面元件 | Flex、quick reply、LIFF 的 file input 與 capture |

- **量化品質檢查的效果。** 統計「自動品質檢查判定不合格後，重拍成功的比例」。

### 4.7 風險與緩解

| 風險 | 緩解 |
|---|---|
| ⚠ 路線 A 的照片暫存在 LINE | 交由 IRB 決定，同意書揭露，必要時改用 B |
| LIFF 使用到已被棄用的 SDK | 在建置流程中檢查 SDK 版本號 |
| 未認證 MINI App 的 header 顯示 tunnel 網域，降低信任 | 使用研究單位可辨識的網域 |
| 選單切換延遲 | 使用 per-user 綁定，不改預設選單 |

---

## 5. 同意、撤回與帳號事件：留下可稽核的紀錄，但封鎖不等於撤回

### 5.1 結論

**更正：** 研究對象「得隨時撤回同意之權利及撤回之方式」規定在**《人體研究法》第 14 條第 1 項第 6 款**。**第 19 條沒有提到撤回**。第 19 條的三項分別規定：

1. 研究結束或保存期限屆至時，研究材料應即銷毀，但經當事人同意或已去連結者除外；
2. 未去連結的材料若超出原同意範圍使用，須重新審查並取得同意；
3. 未去連結的材料若要提供到境外，須有書面同意、審查會通過，並經主管機關核准。

出處：[人體研究法全文](https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=L0020176)、[第 19 條](https://law.moj.gov.tw/LawClass/LawSingle.aspx?pcode=L0020176&flno=19)，[A]，最新修正 108-01-02，查閱 2026-10-31。

設計建議：

- **分層同意**：第一層是 Flex 摘要卡，第二層是完整說明與 2–3 題是非題。
- 同意紀錄採 append-only，記錄文件版本、內容的 SHA-256、UTC 伺服器時間，並串成雜湊鏈。
- 撤回後立即停止使用，刪除照片與可連結的資料。
- 在模型登錄表上標記受影響的模型，**等下一次人工排程訓練時再排除**。
- **封鎖（unfollow）不自動視為撤回**，但要暫停收集，並提供 LINE 以外的撤回管道。

### 5.2 證據整理

**電子同意（eConsent）的效果**

[Cohen et al., JMIR 2023](https://jmir.org/2023/1/e43883/PDF)（[B] 系統性回顧）的內容如下：

- 納入 37 篇出版物，涵蓋 35 項研究、13,281 人。
- 10 項高效度研究中，有 6 項發現至少部分概念的理解顯著較佳。
- 滿意度較高或相當。
- 完成時間較長。
- 作者群含 AstraZeneca 員工，有利益衝突。

**美國的電子同意指引**

FDA 與 OHRP 的 "Use of Electronic Informed Consent… Q&A" 於 2016 年 12 月定稿，本輪沒有找到取代它的新版（[FDA](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/use-electronic-informed-consent-clinical-investigations-questions-and-answers)，[A]）。其中身分驗證的細節來自二手報導（[RAPS](https://www.raps.org/resource/electronic-informed-consent-final-q-a-spells-out.html)，[E]）。

**台灣的電子同意規範**

- 衛福部層級的「人體研究電子同意指引」：**未找到**。
- 臺大醫院〈網路研究倫理審查指引〉（2020-09）允許以「我同意」點選鍵代替簽名，並要求告知傳輸可能被第三方截取的風險。「網路研究自評表」要求留存附時間戳記的同意紀錄（[臺大指引](https://www.ntuh.gov.tw/ckfinder_file/RECO/files/02.%E6%A8%99%E6%BA%96%E4%BD%9C%E6%A5%AD%E6%B5%81%E7%A8%8B/%E5%8F%B0%E5%A4%A7%E9%86%AB%E9%99%A2%E7%B6%B2%E8%B7%AF%E7%A0%94%E7%A9%B6%E5%80%AB%E7%90%86%E5%AF%A9%E6%9F%A5%E6%8C%87%E5%BC%95202009.pdf)，[A-機構]，經搜尋摘要確認）。
- 《人體研究法》第 12 條第 2 項：同意的方式與內容須經審查會核准。換句話說，電子同意的形式本身就要經 IRB 核准（[A]）。

**LINE 的帳號事件**（[A]）

- follow 事件在「加好友或解除封鎖」時發送，可以回覆。
- unfollow 事件在封鎖時發送，官方只標示 follow 可以回覆。

出處：[RECV](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)。

`follow.isUnblocked` 可以區分新加入與解除封鎖（[SDK PR #597](https://github.com/line/line-bot-sdk-python/pull/597)，[E]／官方 SDK）。這個欄位在官方 news 的導入日期：**未找到可靠證據**。

對封鎖者的推送不會送達，也不計入則數（[Send messages](https://developers.line.biz/en/docs/messaging-api/sending-messages)、[Pricing](https://developers.line.biz/en/docs/messaging-api/pricing/)，[A]）。

**已訓練模型如何處理撤回**

- 美國 FTC 在 Everalbum 案（2021）要求刪除**未經明示同意取得**的資料，以及用這些資料開發的模型（[World Privacy Forum](https://worldprivacyforum.org/posts/ftc-proposes-precedent-setting-face-recognition-settlement-photo-app-company-must-delete-consumers-photos-and-the-algorithmic-models-it-developed-using-the-photos)，[E] 二手）。
- EDPB Opinion 28/2024（2024-12-17）認為 AI 模型不當然是匿名的；對於**違法處理**資料所開發的模型，監理機關可以要求銷毀（[Matheson](https://www.matheson.com/insights/edpb-publishes-eagerly-anticipated-opinion-on-ai-models/)，[E] 二手）。
- 機器遺忘（machine unlearning）的綜述見 [Xu et al., ACM Computing Surveys 2023, DOI 10.1145/3603620](https://opus.lib.uts.edu.au/handle/10453/176647)，[B]。
- 對於「合法同意期間訓練、之後才撤回」的情形，要求立即重訓的監理意見：**未找到可靠證據**。

**LINE 對健康資料的條款**

- LINE User Data Policy 頁回 403，未能讀取。
- LINE 隱私權政策提到，被指定為可能含特別敏感資訊的官方帳號，其內容不會用於機器學習（[LINE privacy](https://terms.line.me/line_communication_privacy?lang=en)，[A]，經搜尋摘要）。
- LINE 是否禁止官方帳號收集健康資料：**未找到可靠證據**，需要人工查閱 tw.linebiz.com 與 terms.line.me。

### 5.3 反面證據與限制

- **LINE 能證明的事有限。** webhook 只能證明「某個 provider 範圍內的 userId 在某個時間點按了某個 postback」，**不能證明真實身分、年齡或是否為本人**（推論，依據 [Get user IDs](https://developers.line.biz/en/docs/messaging-api/getting-user-ids/)，[A]）。
- **沒有直接證據。** 聊天機器人內的 eConsent 或是非題（quiz）效果：**未找到可靠證據**。
- **保存年限沒有法定下限。** 台灣法規對研究同意紀錄的最低保存年限：**未找到可靠證據**。
- **雜湊鏈的效力。** 雜湊鏈作為完整性證據，沒有找到法院或 IRB 採認的案例。雜湊鏈也只能防止部分改寫，若要防止整串被重新計算，需要外部錨定。
- **二手來源。** FTC 與 EDPB 的原文沒有直接讀取，上述內容都來自二手評論。

### 5.4 對本專案的適用性

**現在：適用，但要特別小心撤回的影響。** 14 位個案中撤回 1 人，約佔受試者的 7%，照片可能佔 5–15%，對模型與驗證集的影響都很大。撤回時應**立即凍結受影響的模型**：標記為「不得再部署或匯出」，下次人工訓練時排除。不要自動重訓，以符合原則。

如果把封鎖誤判為撤回，誤刪一人就損失約 7% 的受試者。

**未來：適用。** 撤回一人的影響通常不到 1–2%，可以依排程處理，例如每季由人工重訓一次。SISA 類分片訓練（Bourtoule et al., IEEE S&P 2021，**本輪未驗證引用細節**）可以降低重訓成本，但對小型專案效益有限。

### 5.5 實作要點

以下為本報告推論。

**資料表**

- `consent_documents`（不可變）：`doc_id`、`version`、`lang`、`irb_approval_no`、`effective_from_utc`、`content_canonical`、`sha256`、`quiz_json`、`flex_json_sha256`、`liff_bundle_sha256`。`content_canonical` 先做 NFC 正規化、統一換行、去除尾端空白。
- `consent_events`（append-only，用 SQLite trigger 拒絕 UPDATE 與 DELETE）：`event_id`、`seq`、`subject_pid`、`event_type`、`doc_id`、`doc_sha256`、`channel`、`server_received_utc`、`line_event_timestamp_ms`、`webhook_event_id`、`id_token_verified`、`enrollment_code_hash`、`prev_hash`、`row_hash`。
  - `event_type` 的值：presented、quiz_answered、consented、declined、withdrawn、reconsented、unfollow_observed、follow_observed、data_purged、unsend_purged。
  - `row_hash = SHA256(prev_hash ‖ canonical_json(row))`。
- 每天把最新的 `row_hash` 匯出到離線媒體，或寫進 IRB 紀錄，作為外部錨定。

**分層同意流程**

1. Flex 摘要卡，內容 4–6 點。
2. 點「閱讀完整說明」，開啟自有 HTTPS 網頁或 LIFF。
3. 回答 2–3 題是非題，例如「本服務會告訴我是否得了靜脈炎？（否）」。答錯就顯示說明再答一次，**不以分數排除**任何人。
4. 自我聲明：「我已年滿 18 歲（或依 IRB 核定的年齡），且為照片中手臂的本人，或其法定代理人。」
5. 點「我同意」postback，`data` 帶上 `consent_version` 與 `doc_sha256` 的前綴。

未成年與代理同意不開放在 LINE 自助流程中完成，改走研究人員面對面流程。這是設計選擇，須經 IRB 核可。

**撤回流程（全程不自動訓練）**

1. 寫入 `withdrawn` 事件，回覆確認訊息，unlink rich menu，把 `subject_pid` 與照片 hash 加入 `exclusion_list`。
2. 背景刪除工作（不是訓練工作）在 N 小時內刪除照片、縮圖、EXIF、可連結的標註列、`line_link` 對照列，以及尚未進入訓練快照的照片，然後寫入 `data_purged`，附上被刪檔案的 SHA-256 清單。
3. 所有資料集快照的 manifest 以 exclusion list 過濾，舊快照標記 `contains_withdrawn=true`。
4. `model_registry` 標記 `contains_withdrawn_subjects` 與 `flagged_at`。被標記的模型不得新部署；現役模型是否下線由人員決定。
5. 下一次人工訓練時改用乾淨的快照，人員簽核後才替換模型。
6. 備份（04_備份）中的照片依保留期限輪替清除，或另行標記。

**可保留的資料（須事先寫進同意書並經 IRB 核准）**

- 同意與撤回事件，只連結假名 ID。
- 已發表的彙總統計。

本報告**不主張照片可以「去連結」後保留**。照片含身體影像、刺青、痣，難以達到第 4 條第 3 款「永久不能以任何方式連結、比對」的標準。

**帳號事件的處理**

| 事件 | 處理 |
|---|---|
| unfollow | 寫入 `unfollow_observed`，狀態設為 `paused`（停止推播與收件），不刪資料 |
| follow 且 `isUnblocked=true` | 回覆「歡迎回來，您的研究同意狀態為：…」；若同意書版本已更新，要求重新同意 |
| unsend | 刪除該張照片 |

同意書必須寫明「封鎖不等於撤回」，並提供電話或 email 撤回管道，因為封鎖之後就無法在 LINE 內溝通。如果 IRB 偏好保守做法，可以設定「封鎖 X 天未解除即視為撤回」，但必須事先寫入同意書。

**同意書改版**

舊版的同意者不自動沿用新版。重大變更時要求重新同意，在重新同意之前上傳的照片不得進入研究集。

### 5.6 驗證方法

- **稽核演練。** 隨機抽一位受試者，從 `consent_events` 重建「看了哪一版文字（用 SHA-256 比對）、何時同意、何時撤回」，並驗證雜湊鏈連續、與外部錨定相符。
- **撤回演練。** 用測試帳號完成同意、上傳 3 張照片、撤回，然後驗證：照片檔已刪除、`line_link` 已刪除、exclusion list 已更新、快照已標記、模型已標記、撤回後的上傳被拒收。
- **封鎖演練。** 封鎖後狀態變為 `paused`、資料保留；解除封鎖後收到歡迎訊息。

### 5.7 風險與緩解

| 風險 | 緩解 |
|---|---|
| 同意者不是本人，或未成年 | 自我聲明；醫院病人改用一次性登錄碼（第 6 節） |
| 同意書版本與顯示內容不一致 | 以 SHA-256 綁定，並在 CI 檢查 Flex JSON 的 hash |
| 刪除不完整，備份與日誌中仍有殘留 | 刪除清單涵蓋備份，日誌不記錄照片 |
| ⚠ 撤回後自動重訓 | 禁止；改為標記模型並由人工排程 |

---

## 6. 身分與帳號連結：userId 只當路由鍵，不當受試者代碼

### 6.1 結論

LINE userId 的格式是 `U[0-9a-f]{32}`。它**以 provider 為範圍發放**：同一位使用者在同一個 provider 底下的各個 channel 拿到相同的 userId，換一個 provider 就不同。這代表它是長期穩定的間接識別碼，**不應該拿來當研究個案代碼，也不應該寫進匯出資料集**。

建議做法：

- 所有研究資料用隨機的 `study_id` 當主鍵。
- userId 只存在受存取控制的連結表裡，查找時用 keyed HMAC。
- 醫院病人用研究人員當面發的**一次性登錄碼**綁定，不用 Account Link 或病人登入頁。
- LINE Login 只用 `openid` scope，不申請 email。

### 6.2 證據整理

**userId 的性質**（[A]，出自 [Get user IDs](https://developers.line.biz/en/docs/messaging-api/getting-user-ids/)）

- 官方原文："User IDs are issued different values for each provider, even for the same user"，在同一個 provider 底下則 "the user ID is the same regardless of the channel type"。
- userId 和顯示名稱、可搜尋的 LINE ID 都不同。
- 使用者沒有同意存取 profile 時，webhook 不帶 user ID。
- Get follower IDs 只開放給認證帳號或 premium 帳號。

**LINE Login 與 email**（[A]）

- 只有在請求 `openid` 時才會回傳 ID token（[LINE Login v2.1 reference](https://developers.line.biz/en/reference/line-login/)）。
- 取得 email 需要另外在 Console 申請。即使已授權，驗證回應的 scope 也不會列出 email（[Integrate LINE Login](https://developers.line.biz/en/docs/line-login/integrate-line-login/index.html.md)）。

**Account Link**（[A]，出自 [Linking user accounts](https://developers.line.biz/en/docs/messaging-api/linking-accounts/)）

- link token 只能用一次，有效 10 分鐘。
- nonce 長度 10–255 字元，官方建議用至少 128 bits 的安全亂數，不要用可預測的值。
- 官方警告自行實作時的攻擊情境：攻擊者可能 "send a URL to a user to link the attacker's LINE account"。
- 必須讓使用者「at all times」都能解除連結。

**台灣的去識別化規範**

- 以 CNS 29100 與 CNS 29191 作為驗證依據（[行政院](https://www.ey.gov.tw/Page/9277F759E41CCD91/af28eb4c-7030-49bb-889d-f0a0fed6a4d5)，[A]）。CNS 29191 的公布年份，各來源記載不一致。
- 國發會民國 108 年函釋：**通過驗證不當然排除個資法的適用**（[臺北市法規函釋](https://laws.gov.taipei/Law/Interpretation/Content/FE372646)，[A]）。
- 《人體研究法》第 4 條第 3 款對「去連結」的定義是「永久不能以任何方式連結、比對」（[A]）。

### 6.3 反面證據與限制

- **userId 何時會改變**（例如使用者刪除後重建帳號），官方沒有寫明：**未找到可靠證據**。本報告推論重建帳號後會得到新的 userId。
- **法規用語。** 個資法現行條文沒有「假名化」這個詞，本輪也沒有找到假名化的法定定義。
- **登錄碼也可能被冒用。** Account Link 的攻擊模式同樣適用於「碼對應帳號」的綁定設計：病人可能把碼轉給他人。

### 6.4 對本專案的適用性

**現在：適用。** 義大醫院 14 位病人的現有個案碼應先轉成 `study_id`，再進研究資料庫，並以前綴區分來源，例如 `H-` 代表醫院、`P-` 代表一般民眾。小樣本下，`study_id` 加上收案日期、醫院與部位，就可能被院內人員再識別，所以匯出時要把日期粗化到週或月，並移除 EXIF（推論）。

**未來：適用。** 隨著個案增加，連結表的存取控制與稽核會更重要。

### 6.5 實作要點

以下為本報告推論。

- **`study_id`**：格式為 `S-` 加 8 位 base32 隨機字元。照片、標註、模型 manifest 都只用 `study_id`。
- **`user_pid`**：`HMAC-SHA256(pepper, userId)`。pepper 存在 Windows Credential Manager，不進 git，也不和 DB 放在同一個備份位置。log 與分析只用 `user_pid` 的前 16 個十六進位字元。
- **`line_link` 表**：記錄 `userId ↔ study_id`。放在獨立的 SQLite 檔，以 NTFS ACL 限制只有 bot 服務帳號能讀，並以 SQLCipher 或應用層 AES-GCM 加密。研究分析人員只拿得到以 `study_id` 為鍵的資料。撤回時刪除這一列，研究資料就和 LINE 帳號斷開。
- **一次性登錄碼**：
  - 伺服器產生，熵至少 40 bits，例如 8 碼 Crockford base32。資料庫只存 SHA-256。
  - 有效 24–72 小時，只能用一次，輸入錯誤 5 次就鎖定。
  - 綁定成功後回覆「已加入研究，研究編號末兩碼 xx」，並寫入 `enrolled_via_code` 事件。
  - 登錄碼對應 `study_id`，**不對應病歷號**。
  - `study_id ↔ 義大個案碼` 的對照表由院內研究人員保管，不進 LINE bot 的伺服器。
- **同一個 provider**：LIFF 或 LINE Login channel 必須和 Messaging API channel 放在同一個 provider 底下，否則 ID token 的 `sub` 對不上 webhook 的 userId。

### 6.6 驗證方法

- 匯出資料集掃描：不應出現符合 `U[0-9a-f]{32}` 的字串，也不應有 EXIF 中的 GPS。
- 登錄碼測試：重放、逾期、錯誤 5 次鎖定、已用過再用。
- 確認同一個 provider：用 LIFF 取得的 `sub` 與 webhook 的 userId 進行 HMAC 後應該相同。

### 6.7 風險與緩解

| 風險 | 緩解 |
|---|---|
| 醫院病人被冒名綁定 | 當面發碼；綁定後回覆末兩碼讓病人確認 |
| 家屬代傳照片 | 允許代拍；但同意者必須是病人本人或法定代理人，在現場流程中確認並記錄 |
| pepper 外洩，導致可反查 userId | 存在 Credential Manager，與備份分開保存 |
| 為綁定醫院個案建置病人登入頁，擴大攻擊面 | 不建；改用登錄碼 |

---
## 7. 資安：用 JWT 換短效 token，照片流量的 TLS 只在本機解開

### 7.1 結論

**Token 選擇。** channel access token 建議用 **v2.1**（使用者自訂效期，最長 30 天），或用 **stateless**（15 分鐘）並以 JWT assertion 換發。兩者都靠 RSA assertion signing key 取得。不建議用 long-lived token，它沒有期限。也不建議用 stateless 的 `client_id + client_secret` 版本，那等於把 channel secret 變成「可以換 token 的密碼」。RSA 私鑰和 channel secret 都放在 Windows Credential Manager，或用 DPAPI 加密的檔案保存，不進 repo。

**對外暴露。** 首選 Tailscale Funnel，TLS 在本機終止，而且不需要開放任何入站埠。次選是自架 Caddy 或 nginx，搭配 Let's Encrypt 憑證與固定 IP。只走聊天、不做上傳頁的話，Cloudflare Tunnel 也可以接受。

**隔離與 log。** 系統分成三個行程：公開的 webhook 服務、只綁本機的管理 API、推論 worker。log 遮罩所有 token、簽章、replyToken、完整 userId 和照片。

> **跨筆記衝突的裁決：tunnel 業者看不看得到照片？**
>
> 06 號筆記說「照片位元組不會經過 tunnel 業者」，04 號筆記說「用 Cloudflare 或 ngrok，照片明文會經過第三方」。兩者都對，差別在於照片走哪條路徑：
>
> - **聊天路徑（路線 A）**：webhook 只帶 JSON，內容是 userId、訊息 ID、replyToken、使用者打的文字、時間戳記。照片由後端主動向外連線到 `api-data.line.me` 下載，這條連線從 PC 直接出去，不經 tunnel（[Receive messages](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)，[A]）。所以 tunnel 業者看得到 webhook JSON，看不到照片。不過 webhook JSON 本身仍是個人資料：userId 是穩定識別碼，文字裡可能有症狀描述。
> - **LIFF 或網頁上傳路徑（路線 B）**：照片從瀏覽器直接上傳到我方的公開端點，一定會經過 tunnel。Cloudflare 與 ngrok 會在各自的 edge 終止 TLS，看得到明文 ⚠。
>
> 本報告推論的補充：如果 PC 另外裝了全系統的出站代理或 VPN，主動下載照片的連線也可能經過第三方。這一點筆記沒有涵蓋，部署時要自行確認。

### 7.2 證據整理

**四種 token**（[Channel access token](https://developers.line.biz/en/docs/basics/channel-access-token/)，[A]，頁面未標更新日；[LINE Tips 2026-07-23](https://developers.line.biz/en/tips/2026/07/23/using-multiple-api-tools/)，[A]）

| 類型 | 效期 | 每個 channel 上限 | 超過上限時 | 能否撤銷 |
|---|---|---|---|---|
| v2.1（JWT） | 最長 30 天 | 30 | API 回錯誤 | 可，`POST /oauth2/v2.1/revoke` |
| Stateless | 15 分鐘 | 不限 | — | **不可** |
| Short-lived | 30 天 | 30 | 最舊的一個失效 | 可，`POST /v2/oauth/revoke` |
| Long-lived | 無期限 | 1 | 舊的失效（重發時可讓舊 token 最多延長 24 小時） | 可 |

官方建議：

- v2.1 與 short-lived 在有效期內重複使用，到期前自動重發。
- 疑似外洩的 token 立即撤銷。
- 每個開發團隊最多發 2 個 token，方便不中斷地輪替。

「Build a bot」頁建議改用使用者自訂效期的 token。如果使用 long-lived token，可以在 Security 分頁用 IP 或 CIDR 限制哪些伺服器能呼叫 API（[Build a bot](https://developers.line.biz/en/docs/messaging-api/building-bot/)，[A]）。本輪讀到的頁面**沒有任何棄用公告**。long-lived 與 short-lived token 是否會棄用：**未找到可靠證據**。stateless token 的推出日期：**未找到可靠證據**。

**v2.1 的 JWT 規格**（[Issue channel access token v2.1](https://developers.line.biz/en/docs/messaging-api/generate-json-web-token/)，[A]）

- 金鑰：RSA 2048，演算法 RS256。在 Console 註冊公鑰後取得 `kid`。
- payload：`iss` 與 `sub` 都是 channel ID，`aud` 是 `https://api.line.me/`。
- JWT assertion 本身最長 30 分鐘，換到的 token 最長 30 天（`token_exp`）。

各端點的規格來自 [line-openapi channel-access-token.yml](https://raw.githubusercontent.com/line/line-openapi/main/channel-access-token.yml)（[A]）。其中 stateless 端點 `POST /oauth2/v3/token` 接受 `client_id + client_secret`，**這表示 channel secret 外洩的影響不只是 webhook 可以被偽造**。

**Webhook 的 TLS 規格**（[A]）

- 必須是 HTTPS，支援 TLS 1.2 與 1.3，**不支援 TLS 1.1 以下**。
- 憑證要由公開 CA 簽發，Let's Encrypt 可以，self-signed 不行。憑證鏈要完整。
- 已棄用的 cipher suite「可能在近期無預警停用」。
- 一個 channel 只能設定一個 webhook URL。

出處：[SSL/TLS spec](https://developers.line.biz/en/docs/messaging-api/ssl-tls-spec-of-the-webhook-source/)、[Build a bot](https://developers.line.biz/en/docs/messaging-api/building-bot/)。

**各對外暴露方式**

- **Cloudflare Tunnel**：由本機的 `cloudflared` 建立只出不進的連線，防火牆可以封鎖所有入站流量（[Cloudflare Connect networks](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)，[A]，文件日期 2026-08-04）。「Cloudflare 在 edge 終止 TLS、看得到明文」這一點來自 [E] 來源（[Nextcloud 論壇](https://help.nextcloud.com/t/is-cloudflare-tunnel-safe-privacy-focused/150268)、[Pangolin](https://pangolin.net/news/building-a-peer-to-edge-peer-reverse-proxy)），**本輪沒有找到 Cloudflare 官方的明文說明**。
- **ngrok**：Traffic Inspector 可以記錄 HTTP 請求，並提供 "full capture mode and replay"。保存期限為 Free 方案 24 小時、Hobbyist 與 Pay-as-you-go 72 小時，加購後最長 90 天（[ngrok Traffic Inspection](https://ngrok.com/docs/obs/traffic-inspection/)，[A]）。full capture 是否預設開啟：**未找到可靠證據**。
- **Tailscale Funnel**（[Tailscale Funnel](https://tailscale.com/kb/1223/funnel)，[A]，last validated 2026-01-20）：
  - 目前是 beta，所有方案都可用。
  - **TLS 在使用者自己的裝置上終止**，relay「無法解密」經過的資料。
  - 只能使用 443、8443、10000 埠，網域固定為 `*.ts.net`。
  - 頻寬上限不可調整，官方沒有公布數字。

**Log 與影像處理**（[A]）

- OWASP 列出不得直接寫入 log 的資料：access token、密碼、加密金鑰、DB 連線字串、敏感個資。OWASP 也建議使用 JSON 結構化格式，以防 CR/LF 注入（[OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)）。
- 重送事件帶著**相同的 replyToken**（[RECV](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)）。因此 log 裡的 replyToken 在有效期內可以被重用。
- Pillow 13.0.0：像素數超過 `MAX_IMAGE_PIXELS` 時發出警告，超過兩倍時拋出錯誤；`formats=` 可以限制要嘗試的格式（[Pillow](https://pillow.readthedocs.io/en/stable/reference/Image.html)）。預設值約為 89,478,485，但這個數字**本輪沒有驗證**。

### 7.3 反面證據與限制

- **無法用 IP 白名單擋 webhook。** LINE 不公開來源 IP，只能靠簽章驗證。
- **簽章不防重放。** 簽章不含時間戳記或 nonce，必須另外靠 `webhookEventId` 去重。
- **secret 重發後是否立即失效**：官方只寫「舊 secret 失效」，沒有說明時序，**未找到可靠證據**。
- **Tailscale Funnel 的限制**：仍是 beta、有頻寬上限、網域固定為 ts.net（在未認證 MINI App 的 header 中可能降低信任感）。
- **Windows 相關設定的一手文件本輪沒有抓取**，包括服務帳號、NTFS ACL、BitLocker（Home 版只有「裝置加密」）、keyring 與 DPAPI。這些內容屬於**業界慣例**。
- **OWASP API Security Top 10 2023 的原文本輪沒有抓取**。以下引用的類別名稱來自既有知識。

### 7.4 對本專案的適用性

**現在：適用。** 不論走哪條照片路徑，token 改用短效 token、做 log 遮罩、拆成三個行程，都應該做。

**對外暴露的選擇：**

| 情境 | 可用方案 |
|---|---|
| 只走聊天路徑 | Tailscale Funnel、自架反向代理，或 Cloudflare Tunnel（必須接受 Cloudflare 看得到 webhook JSON，並寫進資料流說明） |
| 有 LIFF 上傳頁 | **只能用 Funnel 或自架反向代理** ⚠ |

**ngrok：不建議。** Inspector 會在雲端保存請求內容，包括 replyToken ⚠。

**未來：適用。** 流量變大後，可以考慮小型 VPS，以 TCP passthrough 加 WireGuard 回到本機。TLS 仍在本機終止，VPS 可以提供 DDoS 緩衝（本報告推論）。

### 7.5 實作要點

**架構**（本報告推論）

```
Internet → (Tailscale Funnel / Caddy / cloudflared) → 127.0.0.1:8001  webhook-svc
                ├─ 只允許 POST /webhook/<隨機字串>，其他路徑回 404
                ├─ body 上限 ~1 MB（超過回 413）
                ├─ 先驗 HMAC，再寫入 SQLite，再回 200
127.0.0.1:8000  admin-api + React（不經任何 tunnel；防火牆封鎖入站）
worker 行程：出站 → api.line.me / api-data.line.me（httpx follow_redirects=False、網域 allowlist）
```

- webhook-svc 與 admin 必須是**兩個不同的 FastAPI app**。webhook-svc 關閉 `/docs`、`/redoc`、`/openapi.json`。
- 三個行程都用非系統管理員的標準使用者帳號執行，透過 NSSM、WinSW 或工作排程器啟動。
- 用 `New-NetFirewallRule` 封鎖 8000 與 8001 的入站連線。
- 用 `icacls` 把 DB、照片目錄、秘密檔限縮為只有服務帳號與 Administrators 能存取。
- 整機啟用 BitLocker 或裝置加密，外接備份碟也要加密（業界慣例）。

**Token 生命週期**

1. 產生 RSA 2048 金鑰對，公鑰註冊到 Console。
2. 啟動時用 JWT 換一個例如 7 天效期的 v2.1 token，到期前自動重發，並撤銷舊 token。
3. assertion signing key 每 6–12 個月輪替一次（本報告推論值）。LINE 是否允許同時註冊多把公鑰，本輪沒有驗證。

**外洩應變 runbook**

1. 撤銷所有 token。
2. 在 Console 重發 channel secret。
3. 輪替 RSA 金鑰。
4. 更新本機保存的秘密，重啟服務。
5. 用 Console 的 Verify 與 `POST /v2/bot/channel/webhook/test` 確認運作正常。
6. 檢查 log 是否有異常推播。
7. 通報 IRB 與計畫主持人。

**Log 遮罩**

- 掛一個 `logging.Filter`，用 regex 遮罩以下內容：`Bearer\s+\S+`、`"replyToken"\s*:\s*"[^"]+"`、`x-line-signature`、`U[0-9a-f]{32}`、JWT 的三段格式。
- uvicorn 使用 `--no-access-log`，改由自己的 middleware 記錄。只記：方法、路徑、狀態碼、耗時、body 長度、驗簽結果、事件數、`user_pid`。
- httpx 與 requests 的 logger 設為 WARNING。
- 全域 exception handler 不附 request 物件。
- **不使用雲端 APM 或錯誤追蹤服務**（例如 Sentry）⚠，只寫本機的 `RotatingFileHandler`。

**重放防護**

- `webhookEventId` 設 UNIQUE 約束，保留 7–30 天。
- 事件 `timestamp` 與現在相差超過 1 小時，而且 `isRedelivery=false` 時，記為可疑並不處理。重送事件放寬到 24 小時（本報告建議值，LINE 沒有公布重送時間窗）。

**速率限制**

- per-userId：在驗簽之後、於 worker 端計算，例如每天最多 10 張照片。超過上限只回一則說明，不下載也不推論。
- per-IP：只放在 tunnel 或反向代理層，用來擋驗簽之前的洪水攻擊。

**相依套件**

- 用 hash 鎖定版本（`requirements.txt` 加 hash，或 `uv.lock`）。
- 定期執行 `pip-audit`。
- 追蹤 line-bot-sdk、Pillow、FastAPI、uvicorn、cloudflared、tailscale、Caddy 的安全公告。

**OneDrive** ⚠

專案目前位於 `C:\Users\user\Desktop\…`。如果 OneDrive 的「桌面備份」已開啟，照片與 DB 會被同步到雲端。**請實際檢查這個設定。** 研究照片與 DB 建議放在不受同步的路徑，例如 `C:\PhlebitisData\`。

### 7.6 驗證方法

- 從外部掃描公開埠：只應看到 443。`/docs` 與管理路徑應回 404。
- TLS 檢查：只允許 TLS 1.2 與 1.3，cipher suite 符合 LINE 的 current 清單。
- log 稽核：對一週的 log 用 grep 檢查 `U[0-9a-f]{32}`、`Bearer`、`replyToken`，結果應為 0 筆。
- 洪水測試：用偽造簽章的請求打本機端點（**不要對 LINE 做壓力測試**，官方禁止，見 [GUIDE](https://developers.line.biz/en/docs/messaging-api/development-guidelines/)），確認回 400、不寫 DB、CPU 正常。
- 解壓縮炸彈測試：送入 decompression bomb 檔案，應被拒絕。
- 外洩應變演練：照 runbook 實際走一次。

### 7.7 風險與緩解

| 風險 | 緩解 |
|---|---|
| channel secret 外洩：攻擊者可偽造事件、經 stateless 端點換到 token | 改用 JWT 版 token；依 runbook 處理 |
| ⚠ tunnel 業者在 edge 解密 | 照片流量改用 Funnel 或自架反向代理 |
| ⚠ ngrok Inspector 保存請求 | 不使用 ngrok |
| ⚠ OneDrive 同步照片 | 改放到不受同步的路徑，備份到 BitLocker 加密的外接碟 |
| 家用網路遭 DDoS | 使用 Funnel，或日後加上 VPS passthrough |

---

## 8. 可靠性與營運：LINE 不給 log，研究指標全部自己算

### 8.1 結論

**停機的後果。** 沒有開啟重送時，停機期間的 webhook 不會補送。開啟重送後，也只會在「一段時間」內重送，且不保證送達。文字訊息只能透過 webhook 取得，照片則會在一段時間後被 LINE 刪除。停機後要通知使用者只能用 push，而 push 要計費。所以要做到三件事：

- 服務化並設定自動重啟；
- 開啟重送與錯誤統計；
- 用 SQLite 佇列、重試與 dead-letter 處理失敗的工作。

**LINE 端的統計工具有限。** LINE 提供的統計粒度粗、有延遲，還有隱私門檻：Insight API 每小時只能呼叫 60 次、約 1 天後才有資料、人數少於 20 時回傳 null。因此收件數、同意率、品質不足比例、預測分布、撤回次數這些研究指標**一律由本機自建計算**。LINE 的數字只用於對帳，以及觀察好友數與封鎖趨勢。

### 8.2 證據整理

**Rate limit**（每個 channel、每個 endpoint 分別計算，[REF › Rate limits](https://developers.line.biz/en/reference/messaging-api/#rate-limits)，[A]）

| 端點 | 上限 |
|---|---|
| narrowcast、broadcast、各類統計與 insight、test webhook | 60 次／小時 |
| audience | 60 次／分鐘 |
| Set／Get webhook endpoint | 1,000 次／分鐘 |
| multicast | 200 次／秒 |
| loading animation | 100 次／秒 |
| 發行 short-lived token | 370 次／秒 |
| 其他端點 | 2,000 次／秒 |

超過上限時回 `429 Too Many Requests`。

**狀態碼**（[REF › Status codes](https://developers.line.biz/en/reference/messaging-api/#status-codes)，[A]）

| 狀態碼 | 意義 |
|---|---|
| 400 | 請求錯誤 |
| 401 | token 無效 |
| 403 | 沒有權限 |
| 404 | 例如使用者不存在、未同意、不是好友或已封鎖 |
| 409 | 相同的 retry key 已被接受 |
| 413 | 請求超過 2 MB |
| 429 | 超過 rate、併發或訊息額度 |
| 500 | 伺服器錯誤 |

LINE 不提供 log，開發者要自行記錄以下內容：API 請求的 `x-line-request-id`、時間、方法、endpoint 與狀態碼；收到的 webhook 的來源 IP、時間、路徑，以及自己回的狀態碼（[GUIDE](https://developers.line.biz/en/docs/messaging-api/development-guidelines/)，[A]）。

**錯誤統計與錯誤通知**（[A]）

- Error statistics aggregation 要手動開啟，**不會回溯**開啟前的資料。時區是 UTC+9，可以下載 TSV。錯誤分為 `could_not_connect`、`request_timeout`、`error_status_code`、`unclassified` 四類，「Errors」欄是 60 秒內同一狀態碼的錯誤次數（[ERRSTAT](https://developers.line.biz/en/docs/messaging-api/check-webhook-error-statistics/)）。
- 錯誤通知 email 只開放給「已提交申請的法人用戶」。同一狀態碼在 5 分鐘內的錯誤合併成一封信。重送停止時也會寄信（[ERRNOTI](https://developers.line.biz/en/docs/partner-docs/error-notification/)）。改為重送停止時也寄信的確切日期：**未找到可靠證據**。

**發送數與額度 API**（[REF](https://developers.line.biz/en/reference/messaging-api/)，[A]）

- `GET /v2/bot/message/delivery/reply?date=yyyyMMdd`：官方原文 "Normally, the counting process is completed within the next day"。
- `quota/consumption` 回傳的數字是近似值。

**Insight API**（[REF › Insight](https://developers.line.biz/en/reference/messaging-api/)，[A]）

| API | 資料延遲 | 限制 |
|---|---|---|
| followers | 約 1 天 | 每小時 60 次 |
| 人口統計 | 約 3 天 | 可觸及目標人數須達 20 人以上；帳號須在日本、泰國或**台灣**建立 |
| 互動統計 | — | 少於 20 時回傳 null；資料只更新 14 天 |

**狀態頁**

官方狀態頁是 [LINE API Status](https://api.line-status.info/)，涵蓋 Messaging API、LINE Developers、LIFF、LINE Login，不涵蓋 LINE App 本身。可以用 RSS 或 ATOM 訂閱。事故先在狀態頁發布，細節確認後才發 news（[LINE API Status 說明](https://developers.line.biz/en/docs/basics/line-api-status/)，[A]）。這部分內容來自搜尋摘要與頁面標題，**建議逐字確認**。

### 8.3 反面證據與限制

- **不公開的數字。** 重送的次數與期間、平台「暫停 webhook」的條件與恢復方式、錯誤統計的保存期限與延遲、狀態頁的歷史事故頻率與 SLA：都**未找到可靠證據**。
- **Retry-After header。** 429 回應是否附帶 `Retry-After`：**未找到可靠證據**。
- **reply 無法安全重試。** reply 不支援 retry key，遇到 5xx 或逾時時，無法確定訊息是否已經送出。
- **缺乏可靠性文獻。** 單機 webhook 服務可用性的實證研究，本輪沒有檢索。以下的監控設計屬於**業界慣例與本報告推論**。

### 8.4 對本專案的適用性

**現在：適用。** 流量小，rate limit 不是瓶頸。但單機 Windows 的停機風險很高。

**未來：適用。** 量大時要加強 GPU 佇列監控。每日對帳的價值也更高。

### 8.5 實作要點

以下為本報告推論與業界慣例。

**失敗處理矩陣**

| 情境 | 處理方式 |
|---|---|
| Get content 回 202 或 5xx | 指數退避重試 3 次，仍失敗就標為 dead、告警，並以 reply 請使用者重傳 |
| Get content 回 410 | 使用者已收回訊息：刪除資料，不回覆 |
| reply 回 400 "Invalid reply token" | 依研究政策：若額度內允許，帶 `X-Line-Retry-Key`（= job UUID）發 push；否則只記錄「未回覆」，待使用者點選單「我的最近結果」時再以 reply 補上 |
| push 回 500 或逾時 | 用同一個 retry key 在 24 小時內重試 |
| push 回 409 | 視為已送出 |
| push 回 429（額度用盡） | 不重試，改走 postback |
| push 回 429（rate limit） | 指數退避 |
| 401 | token 失效：立即換發 token 並告警 |
| 403 | 方案或權限問題：告警 |
| LINE 平台事故 | 比對 api-line-status RSS，區分是我方故障還是平台故障 |

**停機後的處理**

收到重送事件、而 reply token 已失效時，只對「已同意研究、且有未完成照片」的使用者補發 push，每人最多一則。文案為「系統先前中斷，請重新上傳」。

預防性的做法：在圖文選單與自動回覆中說明「研究服務可能中斷，不是緊急醫療管道」。

**告警條件**

- 最舊的 queued job 超過 45 秒
- 驗簽失敗數突增
- "Invalid reply token" 比例升高
- worker 心跳超過 60 秒沒更新
- 磁碟剩餘空間低於門檻
- 連續 N 次 LINE API 5xx 或 429
- GPU 不可用（`torch.cuda.is_available()` 為 false）

告警通道用 email 或 Windows 通知。不要用研究帳號的 LINE push 告警，那會計費，也會和受測者混在同一個帳號。若一定要用 LINE，另開一個 channel。告警內容不得含照片或 userId。

**健康檢查**

`/healthz` 只綁本機，回報以下項目：DB 是否可寫、佇列深度、最舊 job 的等待時間、GPU 狀態、worker 最後心跳時間。

**統計：LINE 官方 API 與自建資料的分工**

| 用途 | 來源 |
|---|---|
| 研究 KPI | 只用自建資料表，以 `webhook_event_id` 去重 |
| 每日排程 | 一次抓取前一日（UTC+9）的 reply／push 發送數與 followers；狀態為 `unready` 時隔天再補抓 |
| 儀表板 | **不可每次刷新都呼叫 Insight API**（上限每小時 60 次） |
| 對外報告 | 比照 Insight 的 20 人門檻，對小格數做抑制（small cell suppression） |

**Windows 主機設定**

- 開機自動啟動，crash 後自動重啟。
- 設定 Windows Update 的維護時段。
- 關閉休眠。
- 使用 UPS。
- tunnel 斷線後自動重連。

**監控與原則**

監控只發告警，**不觸發自動訓練或自動上線**。唯一的例外是第 9 節列出的「自動回滾到上一個已核准模型」。

### 8.6 驗證方法

- **停機演練**：暫停服務 10 分鐘，確認重送是否補件、去重是否正確、告警是否發出。
- **429 模擬**：在 mock 環境中讓 API 回 429，確認系統降級為 postback 模式。
- **對帳**：連續 14 天比對自建 replied 數與 LINE 的 reply 發送數。
- **KPI 重算**：從原始事件表重新計算一次研究 KPI，應與儀表板一致。

### 8.7 風險與緩解

| 風險 | 緩解 |
|---|---|
| 長期停機導致 webhook 被平台暫停 | 服務化、告警，並訂閱狀態頁 |
| 補發 push 用光額度 | 補發必須人工核准，每人上限一則 |
| 統計重複計算 | 去重，並排除重送事件 |
| 告警洩漏個資 | 告警只放計數，不放識別資訊 |

---

## 9. 模型上線：影子模式交給人審閱，前進要人簽核，只有回滾可以自動

### 9.1 結論

**本專案不做面向使用者的 A/B 測試，也不做依流量比例的金絲雀發布。**

在本專案中，金絲雀等於讓一部分真實民眾收到候選模型的判讀。這是「上線」，而且是準隨機分派。業界的金絲雀通常會依指標**自動擴大流量**，這直接違反「不自動上線」原則 ⚠。

替代做法分成以下幾個階段：

1. **離線評估**：在凍結的、以病人為單位切分的測試集上評估。
2. **影子模式**：候選模型在背景跑，只記錄、不回覆使用者。這是目前已有的機制。
3. **審閱者端金絲雀**：候選模型的結果只給內部審閱者看，審閱時對模型身分盲化。
4. **人工簽核切換**：依預先寫好的門檻，由負責人簽核後才切換。

**自動化只允許往後退**：可以自動回滾到上一個已核准模型，或自動降級為固定回覆「需人工確認」。

以目前約 120 張照片、14 位個案的規模，**任何「候選模型較好」或「不劣於現行模型」的統計結論都不成立**。

### 9.2 證據整理

**Silent trial 與指引**

- **Silent trial 的實例**：嬰兒阻塞性腎水腫模型在 2020 年 8 月到 12 月進行 silent trial。資料漂移（病人年齡、患側、影像格式改變）使 AUC 從 0.90 掉到 0.50，修正後在兩個獨立資料集上回到 0.85–0.91。整個過程發生在模型影響病人之前（[Kwong et al., Front Digit Health 2022](https://www.frontiersin.org/articles/10.3389/fdgth.2022.929508/full)，[C]，單中心前瞻研究）。
- **範圍回顧**：silent trial 的做法高度不一致，目前**沒有正式指引**（[Tikhomirov et al., Nature Health 2026](https://adelaide.edu.au/about/news/2026/calls-for-global-guidelines-for-safer-ai-use-in-medicine--/)，[B]，本輪只讀到二手摘要；「納入 75 篇」來自 [E]）。
- **DECIDE-AI** 報告指引：17 項 AI 特定項目加 10 項通用項目（[Vasey et al., Nat Med 2022, DOI 10.1038/s41591-022-01772-9](https://ora.ox.ac.uk/objects/uuid:f3d4d76c-cfc7-40dc-a5c3-4f3a460c5901)，[A]）。
- **GMLP 十項原則**：2025 年由 IMDRF 定稿為 N88（[FDA GMLP](https://www.fda.gov/medical-devices/artificial-intelligence-enabled-medical-devices/good-machine-learning-practice-medical-device-development-guiding-principles)；[IMDRF N88](https://imdrf.org/sites/default/files/2025-02/IMDRF_AIML%20WG_GMLP_N88%20Final.pdf)，[A]）。與本專案關係最直接的是第 4、5、8、10 項：訓練集與測試集獨立、參考標準、在臨床相關條件下測試、部署後監測。定稿版的逐字用語本輪沒有核對。
- **PCCP（預先定義的變更控制計畫）**：包含三個部分，分別是修改描述、修改協定、影響評估（[FDA PCCP](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/marketing-submission-recommendations-predetermined-change-control-plan-artificial-intelligence)，[A]）。定稿日期有**來源衝突**：律師事務所報導為 2024-12-03 或 12-04，FDA 官方頁目前顯示 "Issue date: August 2025"。本報告寫作「2024 年 12 月定稿，FDA 頁面目前列為 2025 年 8 月版」。
- **WHO**：2021 年發布 AI 倫理治理指引，2024-01-18 發布大型多模態模型（LMM）指引（[WHO](https://www.who.int/publications-detail-redirect/9789240084759)，[A]）。

**A/B 測試的倫理**

- **A/B effect**：16 項研究發現，民眾可以接受某項政策全面實施，卻反對用 A/B 方式隨機分派（[Meyer et al., PNAS 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC6561206)，[B]）。這個結論有爭議：Data Colada 重新分析後，認為在其檢驗的 7 個情境中效應消失（[Data Colada](https://datacolada.org/?p=4489)，[E]）。
- **Facebook 情緒感染實驗**：以服務條款代替知情同意，PNAS 主編因此發布 Expression of Concern（[PMC4115552](https://pmc.ncbi.nlm.nih.gov/articles/PMC4115552)，[C]）。
- **台灣法規**：《人體研究法》第 4 條把人體研究定義為「取得、調查、分析、運用……醫學等有關資訊之研究」。第 5 條規定研究須先經倫理審查委員會審查通過，主管機關公告免審的範圍除外（[人體研究法](https://law.moj.gov.tw/LawClass/LawAll.aspx?PCode=L0020176)，[A]）。

**金絲雀發布的業界做法**

- 金絲雀是 "a partial and time-limited deployment of a change in a service and its evaluation"。指標要少，並以使用者可見的 SLI 為主。發現明顯變差時自動暫停或回滾。這份文件也主張 "Deployments should be performed by computers, not humans"（[Google SRE Workbook](https://sre.google/workbook/canarying-releases/)，業界慣例）。
- ML 系統需要可除錯性、回滾與監測（[Breck et al., ML Test Score 2017](https://research.google/pubs/pub46555/)，[C]）。

**樣本量**

- 外部驗證的樣本量範例：當盛行率 0.43、c 統計量 0.77，要讓校準斜率的 CI 寬度為 0.3，需要 949 人（408 個事件）。常見的經驗法則是事件與非事件各至少 100–200 個（[Riley et al., BMJ 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11778934/)，[B]）。這篇沒有討論群集效應。
- McNemar 檢定的配對樣本量用 Connor 公式計算：N = [z_{α/2}√p_d + z_β√(p_d − δ²)]² / δ²（[MetricGate](https://metricgate.com/docs/sample-size-mcnemar-paired)；[pwrss](https://rdrr.io/cran/pwrss/man/proportions.mcnemar.html)，二手說明一致；Connor 1987 原文未取得）。

**本報告計算**（以 Wilson 區間與 Connor 公式在 Python 中計算，**不是文獻數字**）

| 情境 | 觀察值 | 95% Wilson CI | CI 寬度 |
|---|---|---|---|
| normal 9 張判對 8 張 | 0.889 | 0.565–0.980 | 0.415 |
| 14 位病人中 12 位正確 | 0.857 | 0.601–0.960 | 0.359 |
| stage 2 的 24 張判對 20 張 | 0.833 | 0.641–0.933 | 0.292 |
| 120 張判對 108 張 | 0.900 | 0.833–0.942 | 0.109 |
| 未來每類約 333 張，判對 300 張 | 0.901 | 0.864–0.929 | 0.064 |
| 1,000 張判對 900 張 | 0.900 | 0.880–0.917 | 0.037 |

McNemar 檢定（α=0.05、檢定力 80%）所需的配對張數：

| p10 | p01 | 所需配對數 |
|---|---|---|
| 0.10 | 0.05 | 約 469 |
| 0.08 | 0.03 | 約 343 |
| 0.06 | 0.03 | 約 783 |
| 0.15 | 0.05 | 約 155 |

其他計算：

- **三法則**：如果 120 張中嚴重錯誤（stage 2 被判為 normal）為 0，真實錯誤率的 95% 上界仍約 2.5%。
- **三類 kappa**：假設真實值約 0.80 做模擬，n=14 時 95% 區間為 0.46–1.00；n=1,000 時為 0.77–0.83。

**以上計算都假設照片彼此獨立。** 同一位病人的多張照片高度相關，有效樣本量更接近病人數，實際的 CI 會更寬。

**部署後的失敗案例**

- Epic 敗血症模型在外部驗證中 AUC 只有 0.63（95% CI 0.62–0.64），開發者報告的是 0.76–0.83（[Wong et al., JAMA Intern Med 2021](https://jamanetwork.com/journals/jamainternalmedicine/fullarticle/2781313)，[B]，單中心回溯性外部驗證；數字來自多個二手來源）。
- 密西根大學的敗血症警示模型因 COVID-19 造成族群改變，在 2020 年 4 月停用（[Finlayson et al., NEJM 2021](https://www.pubmed.gov/34260843/)，[C]）。
- Google 糖尿病視網膜病變系統在泰國 11 家診所實地部署，遇到模型的影像品質門檻與真實環境之間的衝突（[Beede et al., CHI 2020](https://research.google/pubs/a-human-centered-evaluation-of-a-deep-learning-system-deployed-in-clinics-for-the-detection-of-diabetic-retinopathy/)，[C]）。「超過五分之一影像被拒」這個數字只見於新聞，**沒有在原文核對**。
- 皮膚癌 App 的系統性回顧：照片由臨床人員拍攝，實際使用者的表現可能更差（[Freeman et al., BMJ 2020](https://pubmed.ncbi.nlm.nih.gov/32041693/)，[B]）。
- 症狀檢查器的首位診斷正確率只有 34%（[Semigran et al., BMJ 2015](https://www.bmj.com/node/900623)，[B]，情境腳本稽核）。

**漂移監測的業界慣例**

PSI 常見的判讀門檻是：小於 0.1 視為穩定，0.1 到 0.25 需要檢查，大於 0.25 表示重大變化。這只是啟發式規則，結果會受分箱方式與樣本量影響（[R scorecard](https://search.r-project.org/CRAN/refmans/scorecard/html/perf_psi.html)，[E]）。

### 9.3 反面證據與限制

- 影子模式沒有即時的參考標準，**兩個模型一致不代表兩個都對**，它們可能一起錯。
- silent trial 沒有正式指引。
- GMLP 與 PCCP 是醫療器材的監理框架。本專案目前不是醫材上市申請，這些文件只能當作最佳實務參考。台灣 TFDA 針對 AI/ML 醫材變更管理的指引，本題沒有檢索。
- 不劣界限 Δ 沒有文獻可以依據，必須由臨床人員決定。
- 「自動回滾是否可接受」：沒有找到明確討論這一點的監理文件。

### 9.4 對本專案的適用性

**現在（14 位個案）**

可以做：

- 工程驗證：候選模型能載入、延遲與記憶體可接受、輸出格式正確。
- 描述性比較：一致率、混淆矩陣、分歧案例清單，並明確標為探索性。
- 把分歧案例送人工盲審，累積標註。

**不能**宣稱候選模型「較準」或「不劣」。如果現在就要換模型，理由只能是工程或治理上的需要，例如舊模型有已知錯誤，而且文件中必須寫明「沒有統計證據支持效能較佳」。

**未來（約 1,000 張，每類約 333 張）**

每類敏感度的 CI 寬度約為 ±3 個百分點。如果不一致比例約 15%，可以偵測約 5 個百分點的配對差異。但前提仍然包括：

- 以病人為單位切分；
- 至少 2 位獨立標註者，並報告標註者間一致性；
- 各來源子群都有足夠樣本；
- 門檻事先註冊。

**IRB 與同意書**

影子模式本身就屬於「分析個人醫學資訊」，可能需要 IRB 審查，至少要由 IRB 判定是否可以免審。同意書要揭露「照片可能由第二個研究模型在背景分析」。

### 9.5 實作要點

以下為本報告推論。

**模型登錄表（model registry）**

- 以 SHA-256 作為模型身分，登錄後不可覆寫。
- 狀態分為 candidate、approved、active、retired、rejected、flagged_withdrawn。
- 記錄來源、授權、訓練資料快照、評估報告路徑、核准者與日期。
- 外部 safetensors 模型只能以 candidate 狀態登錄，必須在專案資料上完整評估之後才能晉升。

**設定指標與載入**

- 設定檔裡的 `active_model_id` 和 `shadow_model_id` 指向登錄表中的 ID。
- 啟動時驗證雜湊。不符時拒絕載入，並降級為「需人工確認」。
- 只有狀態為 approved 的模型可以設為 active，由程式強制檢查。

**熱備**

上一個 approved 模型保持在記憶體中，或可在數秒內載入。回滾就是把設定值改回去。

**自動回滾的觸發條件**（只限工程性 guardrail）

- 推論錯誤率或逾時率超過門檻
- 模型檔雜湊不符
- 輸出不合法
- 短時間內超過 X% 的照片都判成同一類

觸發後通知負責人，並要求人工確認是否維持回滾。

**稽核紀錄**

- 每次回覆都記錄 `model_id`、雜湊、分數（只存在研究資料庫，不顯示給民眾）。
- 每次切換或回滾都記錄操作者（自動回滾記為 system 加上原因）。
- 紀錄為 append-only。

**影子轉上線的書面門檻**（每一項都需要人工簽核）

1. 通過離線評估，並附 95% CI。
2. 累積達到預先設定的配對數，並涵蓋足夠長的時間。
3. 所有分歧案例完成盲化標註。
4. 準確率差的 95% CI 下界大於 −Δ，而且 stage 2 的敏感度不低於現行模型。
5. 各子群沒有明顯退化，「需人工確認」比例的變化有合理解釋。
6. 負責人簽核，之後進入加強監測期。

**監測**

每週檢視以下項目：

- 預測類別分布：PSI 或卡方檢定，並附原始計數。
- 分數分布：KS 檢定，只看相對變化。
- 輸入特徵：亮度、解析度、檔案大小、來源。
- 「需人工確認」的比例。
- 抽樣人工審閱結果，並標示標註完成率。
- 影子模型與現行模型的分歧率。

**已發出錯誤結果的處理**

是否以 push 重新聯絡受影響的使用者，由人工決定。訊息使用事先審定的模板，不提供新的判讀，並記錄發送清單。這項流程需要事先寫進 IRB 計畫書。

### 9.6 驗證方法

- **回滾演練**：在測試環境中把 active 指到一個故意損壞的模型，確認雜湊不符時會拒絕載入並降級；再把設定值改回，確認可在數秒內恢復。
- **分歧審閱流程**：從影子資料中抽出分歧案例，送盲審介面標註，產出 McNemar 報告。現階段的報告必須標示為探索性。
- **權限測試**：確認程式拒絕把非 approved 的模型設為 active。

### 9.7 風險與緩解

| 風險 | 緩解 |
|---|---|
| 把一致率誤當正確率 | 審閱分歧案例，並抽樣審閱一致案例 |
| 候選模型讓低信心比例大幅下降，看起來進步，其實可能是過度自信（分數未校準） | 列為需要解釋的指標 |
| 醫院照片上的結果被拿來外推到 LINE 照片 | 依來源分開報告（Freeman 2020 的教訓） |
| ⚠ 自動晉升模型 | 程式強制只有 approved 模型能設為 active |
| 影子模型的失敗拖累主要回覆流程 | 影子模型在 reply 送出後、以低優先序執行 |

---
## 10. 回覆內容：每則都要先講行動，再列紅旗

### 10.1 結論

**免責聲明擋不住過度依賴。** 研究證據顯示，一段通用的免責聲明幾乎無法阻止使用者過度相信 AI 健康建議。比較有效的做法是在**每一則結果訊息裡**直接寫出四樣東西：不確定性、具體的下一步、紅旗症狀、何時要找人。

**措辭不改變法規定位。** 一個軟體算不算醫療器材，看的是預期用途與功能。本專案分析照片並輸出靜脈炎分期，**無法靠措辭變成「非醫材」**。措辭的作用只有兩個：減少誤解，讓使用者在該求助時求助。法規定位要由 IRB 處理，必要時諮詢 TFDA。

**文案原則：**

- 第一行就寫行動。
- 一則訊息只講一件事。
- 不給民眾看分數或期別。
- 「正常」結果寫成「沒有看到明顯紅腫」，並且照樣附上紅旗清單。
- 分「住院中」與「已回家」兩種版本。
- 緊急情況寫「撥 119」，不寫 1922。

### 10.2 證據整理

**免責聲明與過度信任**

- [Denecke & Gabarron, Front Artif Intell 2026](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2026.1785085/full)（[C]）：115 份問卷，15 個情境。有免責聲明時，願意尋求第二意見的比例約 50% 到 89%；沒有時約 41% 到 89%。作者形容效果 "modest and inconsistent"。受試者無法穩定辨認出錯誤的建議。作者建議改用標準化的不確定性說明、提示尋求第二意見、紅旗升級，以及針對症狀的警告。
  - 限制：屬探索性研究，量的是自評意圖，不是實際行為。
- [arXiv 2608.07493](https://arxiv.org/pdf/2608.07493)（[D]，n=52，僅搜尋摘要）：部分受試者把免責聲明解讀為「誠實」，反而更信任。
- [JMIR 2025;e66083](https://www.jmir.org/2025/1/e66083)（[C]，僅搜尋摘要）：告知病人「醫師使用 AI 協助診斷」，會降低病人的信任與求助意願。
- 直接量測使用者「有沒有讀、讀不讀得懂」免責聲明的研究：**未找到可靠證據**。

**法規（簡述）**

- FDA 於 2026-01-06 修訂 CDS 指引。指引仍只處理給醫療專業人員使用的軟體，沒有新增消費者端政策。第 1 項標準排除「擷取、處理或分析醫療影像」的軟體（[Covington](https://www.cov.com/en/news-and-insights/insights/2026/01/5-key-takeaways-from-fdas-revised-clinical-decision-support-cds-software-guidance)；[Cooley](https://www.cooley.com/news/insight/2026/2026-01-20-automation-bias-and-clinical-practice-fda-makes-incremental-updates-to-clinical-decision-support-software-guidance)，[E→轉述 A]）。FDA 原文 PDF 本輪沒有核對。
- 食藥署《醫用軟體分類分級參考指引》：判定時綜合考量「產品功能、用途、使用方法與工作原理」，首先確認是否符合《醫療器材管理法》第 3 條的定義（[mdcpp 轉載副本](https://mdcpp.com/doc/materialDownload/%E5%8F%B0%E6%B9%BE-%E5%8C%BB%E7%96%97%E8%BD%AF%E4%BB%B6%E5%88%86%E7%B1%BB%E5%92%8C%E5%88%86%E7%BA%A7%E5%8F%82%E8%80%83%E6%8C%87%E5%8D%97.pdf)，[A，第三方副本]）。本輪沒有從 fda.gov.tw 核對原文。

**健康識能**

- AHRQ《Health Literacy Universal Precautions Toolkit》第 3 版，2024-03-01 出版，共 23 項工具，其中包含 teach-back（[AHRQ](https://www.ahrq.gov/health-literacy/improve/precautions/toolkit.html)，[A]）。
- CDC Clear Communication Index：20 題，90 分以上為通過。檢核項目包括：只有一個主要訊息、主要訊息放在最前面、行動呼籲具體（[CDC CCI](https://www.cdc.gov/ccindex/tool/faq.html)，[A]）。
- 口語機率詞（例如「可能」）：33 篇研究、145 個詞彙的系統性回顧發現，病人對這些詞的數值解讀差異極大（[Andreadis et al., JGIM 2021](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8642516/)，[B]）。
- 傳達不確定性只會讓信任小幅下降。用數字範圍表達，對來源信任幾乎沒有影響；用口語表達不確定，信任下降較多（[van der Bles et al., PNAS 2020](https://sciencedaily.com/releases/2020/03/200323152106.htm)，[B]，總 n=5,780，英國樣本、教育程度偏高）。
- 視覺輔助能改善風險理解（[Zipkin et al., Ann Intern Med 2014](https://pubmed.ncbi.nlm.nih.gov/25133362/)，[B]）。
- 台灣數據：20 歲以上有 30.1% 健康識能不足或有限（國健署 2021 年調查，[聯合新聞網](https://udn.com/news/story/7266/9827044) 轉述，[A 經新聞轉述]）。65 歲以上約 53.2% 識能不佳（[國衛院論壇](https://forum.nhri.edu.tw/wp-content/uploads/108-4.%E6%88%91%E5%9C%8B%E9%AB%98%E9%BD%A1%E9%95%B7%E8%80%85%E5%81%A5%E5%BA%B7%E8%AD%98%E8%83%BD%E4%B9%8B%E6%B1%BA%E5%AE%9A%E5%9B%A0%E5%AD%90%E8%88%87%E5%85%B6%E5%81%A5%E5%BA%B7%E7%B5%90%E6%9E%9C-%E5%96%AE%E9%A0%81%E6%AA%A2%E8%A6%96.pdf)，僅搜尋摘要）。兩者使用的量表不同，不能直接比較。
- 聊天機器人介入的效果「正向或混合」，研究品質偏低（[Milne-Ives et al., JMIR 2020](https://jmir.org/2020/10/e20346/PDF)；[Singh et al., npj Digit Med 2023](https://www.nature.com/articles/s41746-023-00856-1.pdf)，[B]）。

**就醫的觸發條件**

- **Jackson VIP 量表**：
  - 1 分：一項輕微徵象，持續觀察。
  - 2 分：兩項徵象，**更換注射部位**。
  - 4 分：可觸及靜脈索。
  - 5 分：前述徵象再加上**發燒**。

  出處：[Solventum VIP Scorecard](https://assets.solventum.com/is/content/mmmspinco/VIP-Scorecard-for-VHP-websitepdf)；[ivteam VIP](https://ivteam.com/vipsn.pdf)，[A/業界]。各轉載版本的措辭不一致。
- **NHS Lothian 衛教單**（v2.0，2020-02，[A]，已讀全文）：注射部位痛、腫、紅時，"please inform a nurse or doctor immediately"；拔針後的感染 "most common within the 48 hours after removal"（[NHS Lothian](https://policyonline.nhslothian.scot/wp-content/uploads/2023/03/Discharge_home_with_Cannula_in_situ.pdf)）。
- **East & North Herts 衛教單**：留置針處紅腫或有分泌物時，「當天」就要看家醫（[ENHerts](https://www.enherts-tr.nhs.uk/wp-content/uploads/2019/10/Blood-Transfusion-Aftercare-advice-for-patients-V4-03.2025.pdf)，[A/業界]，僅搜尋摘要）。
- **台灣衛教**：「勿自行冰敷、熱敷或按摩」（[康健知識庫](https://kb.commonhealth.com.tw/library/576.html)，[E]）。這點和部分英國衛教「冰敷、抬高」的建議不同。
- **緊急電話**：1922 是疾管署的傳染病諮詢與疫情通報專線（[衛福部](https://www.mohw.gov.tw/cp-88-218-1.html)，[A]），不適合放在本服務的文案中。119 是緊急救護專線（[Hello醫師](https://helloyishi.com.tw/healthy-habits/first-aid/how-to-call-an-ambulance/)，[E]）。台灣是否有類似英國 NHS 111 的全國非急症醫療諮詢專線：**未找到可靠證據**。
- **專業標準**：INS 第 9 版（2024）的病人衛教內容需付費，未能取得。CDC 2011 年之後針對周邊導管的更新：**未找到可靠證據**。

### 10.3 反面證據與限制

- 免責聲明的研究多是情境問卷，量的是意圖而非實際行為，樣本也小。
- van der Bles 2020 的樣本是英國人、教育程度偏高，推論到台灣長者有限。
- 紅旗清單中的「紅線往上延伸」「寒顫」「胸痛、呼吸困難」，是依一般醫學常識推論的，**沒有在本輪的 [A] 來源中逐條核對**，必須由臨床人員審定。
- 台灣醫學中心正式的「周邊靜脈留置針」衛教單：**未找到可直接引用的版本**。建議向合作醫院護理部索取。

### 10.4 對本專案的適用性

**現在：適用。** 這些文案改寫成本低、效益高。但上線前必須經過臨床護理專家、IRB 與法規顧問審閱。

**未來：適用。** 可以把「使用者收到建議後，是否真的通知了護理師」列為研究的結果指標。聊天機器人能否改善靜脈炎的早期通報，目前**未找到可靠證據**。

### 10.5 實作要點

以下為本報告推論。

**訊息結構**

每則訊息分四段：

1. 第一行：結論或行動。
2. 原因或做法，不超過 3 點。
3. 紅旗清單或下一步。
4. 一行小字說明這是研究。

**用字**

- 避免的字：診斷、確診、判定為、治療、處方、用藥建議、保證、準確率 xx%、AI 醫師。
- 改用的說法：「研究系統在照片中看到……的樣子」。

**不顯示分數或期別**

不向民眾顯示未校準的分數，也不顯示期別。這些資料只存在研究資料庫，供人工檢視。

**分流**

用 quick reply 問「你現在在醫院嗎？」，依答案分成兩種處理：

| 情境 | 建議行動 |
|---|---|
| 住院中 | 按鈴告訴護理師 |
| 已回家 | 當天聯絡打針的醫院；文案加上「拔針後 2 天內每天看一下」 |

**分層觸發**

| 層級 | 觸發條件 | 文案 |
|---|---|---|
| 第 0 層 | 任何結果 | 一律附紅旗清單 |
| 第 1 層 | stage 1 | 「請告訴護理師看一下」 |
| 第 2 層 | stage 2 | 「請現在就告訴護理師」 |
| 第 3 層 | 紅旗，例如發燒、紅線延伸、流膿、整隻手臂腫、止不住的出血、胸痛、呼吸困難、意識改變 | 住院中立即按鈴；在家立即就醫；危急時撥 119 |

**不給的建議**

不提供冷敷、熱敷、按摩或用藥建議。

**用 quick reply 做理解確認（teach-back）**

在建議訊息後加三個 quick reply 按鈕：【我會告訴護理師】【我看不懂】【找真人】。使用者點「我看不懂」時，送出更簡化的版本，或轉給真人處理。

**文案檢核**

每則固定文案先用中文版 CCI 自評，目標 90 分以上。再找 5 到 8 位長者或照顧者做理解測試。

完整文案見「交付四」。

### 10.6 驗證方法

**上線前**

- 每則文案的 CCI 評分。
- 長者理解測試：請受試者用自己的話說出「接下來要做什麼」，計算正確率。

**上線後**

- 「我看不懂」按鈕的點擊率。
- 收到紅旗回覆的使用者中，點選「我會告訴護理師」的比例。
- 抽樣訪談。

### 10.7 風險與緩解

| 風險 | 緩解 |
|---|---|
| 「正常」結果讓使用者以為不用再注意 | 正常結果也一定附紅旗清單，並說明照片看不出「痛不痛、硬不硬」 |
| 使用者等系統回覆而延誤就醫 | 每則都寫「緊急時不要等我們」，並註明帳號不是 24 小時有人看 |
| 措辭被認定為診斷宣稱 | 由法規顧問審閱用字清單 |

---

## 11. 無障礙與多語：純文字優先、照顧者可代傳，翻譯與語音都在本機處理

### 11.1 結論

**長者與照顧者。** LINE 是台灣最常用的即時通訊軟體，但 70 歲以上的上網率只有 53.80%。流程因此必須允許**照顧者代傳**。

**Bot 端能控制的無障礙設計：**

- 關鍵訊息用純文字送出；
- Flex 卡片的 altText 必須能單獨看懂；
- 開啟 `scaling: true`；
- 按鈕不超過 3–4 個，標籤以動詞開頭；
- 每則訊息約 120 字以內。

**多語。** 先用 LINE profile 的 `language` 欄位預選語言，但第一則訊息一定要附手動切換按鈕。翻譯只針對**固定模板**，由專業譯者翻譯並回譯審查。台語提供**真人預錄語音**。

**禁止雲端服務。** 不可使用任何雲端翻譯、雲端語音轉文字（ASR）或雲端語音合成（TTS）⚠。如果要做語音辨識，只能用本機部署的模型，而且第一階段不讓 ASR 自動判讀。

### 11.2 證據整理

**台灣長者與 LINE**

[TWNIC《2025 台灣網路報告》](https://report.twnic.tw/2025/en/assets/download/TWNIC_TaiwanInternetReport_2025_CH_all.pdf)（[A]，電訪 n=2,142）：

- 80.10% 的民眾以 LINE 為最常用的即時通訊軟體；在上網者中這個比例是 90.26%。
- 70 歲以上的上網率是 53.80%，2024 年是 50.20%。
- 有上網需求但沒有人協助的人當中，51.72% 想上網處理「醫療服務」。
- 依年齡交叉的 LINE 使用率：PDF 附錄表格無法可靠解析，**未取得數字**。

**LINE 平台能力**

- Get profile 的 `language` 欄位使用 BCP 47 標籤。使用者還沒同意 LINE 隱私權政策時，這個欄位不會出現（[@line/bot-sdk 11.0.0 型別定義](https://unpkg.com/@line/bot-sdk@11.0.0/dist/messaging-api/model/userProfileResponse.d.ts)；[User consent](https://developers.line.biz/en/docs/messaging-api/user-consent/)，[A]）。
- Bot 可以接收音訊訊息（`type: audio`），用 Get content 下載，下載後的內容同樣會被自動刪除（[REF md](https://developers.line.biz/en/reference/messaging-api/index.html.md)，[A]）。
- Flex 的 `scaling` 與 altText 上限 1,500 字元，見第 4 節，[A]。
- LINE 的字體設定分小、中、大、特大四級，只影響聊天室文字。要放得更大，得靠手機系統的字級設定（[T 客邦](https://www.techbang.com/posts/81324-how-do-ios-users-change-the-line-font-size)，[E]）。
- LINE 與 VoiceOver、TalkBack 的相容性：**未找到可靠證據**。

**觸控目標與介面設計**

- WCAG 2.2 SC 2.5.8 規定觸控目標至少 24×24 CSS px（[W3C](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html)，[A]）。
- Apple HIG 建議 44×44 pt，Material Design 建議 48×48 dp（[frontendchecklist](https://frontendchecklist.io/rules/accessibility/touch-targets)，[E] 二手轉述）。
- 一篇長者行動 App 設計的系統性回顧歸納出 28 條指引，其中「簡化」與「加大控制項尺寸與間距」最重要（[PMC10557006](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10557006/)，[B]，僅搜尋摘要）。
- 長者偏好行動 App 的字級至少 14 pt（[OzCHI 2024](https://outbox.eait.uq.edu.au/uqsville/OzCHI2024/Long%20Papers/Design%20for%20Older%20People%20-%20Improving%20the%20Usability%20of%20Mobile%20Apps%20through%20Targeted%20Design%20Recommendations.pdf)，[C]，僅搜尋摘要）。

**可在本機部署的台語語音辨識模型**

- 數位發展部「Taiwan Tongues ASR CE」：開源，支援國語、台語、客語、英語，提供 CTranslate2 推論模型（[GitHub](https://github.com/adi-gov-tw/Taiwan-Tongues-ASR-CE)，[A/E]）。
- Breeze-ASR-26：以約一萬小時的**合成**台語語音微調。模型頁自稱華語版模型在台語上的錯誤率是 30.71% 到 76.85%，這是自報數字，未經獨立驗證（[Hugging Face](https://huggingface.co/Speech-AI-Research-Center/Breeze-ASR-26)，[E]）。
- MR Breeze ASR 25 的主打是台灣華語口音與中英混合，不是台語專用（[MediaTek](https://www.mediatek.com/zh-tw/press-room/mediatek-research-unveils-mr-breeze-asr-25-an-open-source-ai-model-for-taiwanese-speech)，[E]）。
- NUTN-KWS 的台語 Whisper 微調模型（[HF](https://huggingface.co/NUTN-KWS/Whisper-Taiwanese-model-v0.5)，[E]）。
- 這些模型在長者自然口語與醫療用詞上的獨立評測：**未找到可靠證據**。

**移工照顧者**

- 2023 年（112 年）底，社福移工約 23.4 萬人（[勞動部](https://www.mol.gov.tw/media/aklhtid2/12-外籍工作者.pdf)，[A]，僅搜尋摘要）。
- 2026 年 6 月底，社福移工 231,175 人（[Manstrong](https://www.manstrong.com.tw/news-detail/taiwan-migrant-workers-2026)，[E] 引用勞動力發展署）。
- 各來源的統計口徑不同。看護工依國籍細分的官方數字**未取得**，「印尼籍最多」是業界普遍說法，未經官方細表核對。

**台語書寫**

- 教育部的「臺灣台語羅馬字拼音方案」於 2024-08-26（113 年）修正（[教育部](https://language.moe.gov.tw/files/people_files/tshiutsheh_1130826.pdf)，[A]）。
- 「多數長者會講台語、但不會讀台羅或台語漢字」這個說法：**沒有找到全國性數據**。

**機器翻譯醫療內容的風險**

- 100 份急診出院指示用 Google Translate 翻成西班牙文與中文，準確率分別是 92% 與 81%。不準確的句子中，可能造成臨床顯著傷害的比例，西班牙文 2%，中文 8%（[Khoong et al., JAMA Intern Med 2019](https://pmc.ncbi.nlm.nih.gov/articles/6450297)，[C]）。
- 7 種語言整體保留原意的比例是 82.5%，其中亞美尼亞文只有 55%（[PubMed 33674922](https://pubmed.ncbi.nlm.nih.gov/33674922/)，[C]，題名與數據依搜尋摘要）。
- 印尼文與越南文的醫療翻譯準確度：**未找到可靠證據**。

### 11.3 反面證據與限制

- 「一則約 120 字」「按鈕不超過 4 個」是推論，沒有直接證據支持。
- LINE profile 的 `language` 是手機的語言設定，不等於使用者的閱讀偏好。
- 台語 ASR 對長者的準確度不明。辨識錯誤可能導致錯誤分流。

### 11.4 對本專案的適用性

**現在：有條件適用。** 純文字優先、照顧者代傳、按鈕精簡，這幾項可以立即做。多語模板與台語語音建議等合作醫院確認受試者的語言需求後再做。

**未來：適用。** 個案數增加後，照顧者（含移工）的比例可能上升。屆時應優先翻譯印尼文、越南文與英文。

### 11.5 實作要點

以下為本報告推論。

**語言選擇**

第一次互動時，依 `language` 欄位預選：

| `language` 欄位 | 預選語言 |
|---|---|
| zh-TW | 華語 |
| id | 印尼文 |
| vi | 越南文 |
| en、fil、tl | 英文 |
| 沒有這個欄位 | 華語 |

第一則訊息附 quick reply：【中文】【English】【Bahasa Indonesia】【Tiếng Việt】，並記住使用者的選擇。

照顧者代傳時，回覆的語言以傳訊者為準，但在「告訴護理師」那一段附上一行華語，方便看護直接拿給護理師看。

**翻譯流程**

只翻譯約 10 到 15 則固定模板，步驟如下：

1. 專業譯者翻譯。
2. 另一位譯者回譯。
3. 雙語醫護人員或母語照顧者審查。
4. 至少 5 位目標使用者做理解測試。

同意書一定要由專業譯者翻譯。**執行期間完全不做翻譯。** 使用者自己打的文字一律轉給真人處理。

**台語**

- 文字維持華語。
- 由台語母語的醫護人員錄製 T5 與 T6 模板的語音版，以 Audio message 送出。
- 不使用雲端 TTS。

**語音訊息**

收到語音時回覆：「我們收到您的語音，會請研究人員聽」，並轉給真人。ASR 只用於研究評估，用本機模型執行。語音和照片一樣要立即下載並保存在本機，而且要在同意書中載明。

**Flex 按鈕**

按鈕高度以 48 dp 或 44 pt 以上為目標。不要只用顏色表達狀態，每種狀態都要有文字。

**PC 版**

在說明中告知使用者：PC 版不顯示圖文選單，也不支援 quick reply。

### 11.6 驗證方法

- 長者測試：把手機系統字級調到最大，請受試者閱讀每則模板。
- 確認通知列只顯示 altText 時，使用者仍能理解訊息。
- 譯文用回譯比對差異。
- 台語語音由母語者評估是否聽得懂。

### 11.7 風險與緩解

| 風險 | 緩解 |
|---|---|
| ⚠ 使用雲端翻譯、ASR 或 TTS | 改用預譯模板、預錄語音、本機模型 |
| 使用者自由輸入的文字無法處理 | 轉給真人 |
| 照顧者與病人身分混淆 | 同意流程區分「本人」與「代傳者」 |

---

## 本段總表

「最少資料需求」與「工作量」皆為本報告推論的粗估。

| 方法或設計 | 證據等級 | 最少資料需求 | 預估工作量（人日） | 預期效益 | 主要風險 | 建議時程 |
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

---
## 交付一：LINE 服務建議架構

本節的架構設計屬於本報告推論，依據的是第 1、3、7、8、9 節引用的官方規則。

### 元件

| 元件 | 位置與職責 | 不做的事 |
|---|---|---|
| 對外入口 | 首選 Tailscale Funnel；次選 Caddy 或 nginx 搭配 Let's Encrypt 與固定 IP；若只走聊天路徑，也可用 Cloudflare Tunnel。TLS 1.2／1.3，憑證由公開 CA 簽發。只轉送 `POST /webhook/<隨機字串>`，路線 B 另加 `POST /upload` 與 LIFF 靜態頁 | 不轉送管理路徑。路線 B 不用 Cloudflare 或 ngrok ⚠ |
| webhook-svc（127.0.0.1:8001） | 依序做：限制 body 大小 → 驗簽 → 以 `INSERT OR IGNORE` 寫入 webhook_events 與 jobs → 回 200 | 不推論、不下載照片、不記錄 body 與簽章、不掛管理路由 |
| upload-svc（路線 B，可與 webhook-svc 同一行程、不同 router） | 驗證 ID token（`POST /oauth2/v2.1/verify`）→ 檢查同意狀態 → 以串流接收照片並設大小上限 → 寫檔與 SHA-256 → 建立 job | 不信任前端傳來的 profile |
| SQLite（WAL 模式） | 主要資料表：webhook_events、jobs、photos、consent_documents、consent_events（append-only）、model_registry、replies_audit、exclusion_list。`line_link` 放在**另一個加密的 SQLite 檔** | 研究分析用的 DB 不存明文 userId |
| worker（單一 GPU 行程） | 依序做：搶佔 job → 呼叫 loading animation → Get content → 驗證格式與 bomb 防護 → 原檔與工作副本 → 品質檢查 → YOLO 與分類 → reply → 影子模型（低優先） | 不做訓練。影子模型的結果不回覆使用者 |
| 秘密保存 | Windows Credential Manager（DPAPI）保存 RSA 私鑰、channel secret、HMAC pepper | 不放 .env、repo、log 或備份 |
| admin-api 與 React（127.0.0.1:8000） | 標註、審閱、模型登錄與切換（需要人工簽核）、統計、LINE 模擬器 | 不經過任何 tunnel |
| 監控 | `/healthz`（只綁本機）、告警（email 或 Windows 通知）、訂閱 api.line-status.info 的 RSS、每日對帳 | 不觸發自動訓練或自動上線 |

### 信任邊界

| 邊界 | 跨越的資料 | 信任程度 |
|---|---|---|
| ① 使用者裝置 → LINE 平台 | 路線 A 的照片 ⚠ | 第三方暫存，期限不公開 |
| ② LINE 平台 → 對外入口 → webhook-svc | webhook JSON | 只有驗簽通過後才信任 |
| ③ worker → api-data.line.me | 以出站 HTTPS 下載照片 | 內容視為不可信，必須驗證 |
| ④ 使用者瀏覽器（LIFF）→ 對外入口 → upload-svc | 路線 B 的照片 | 入口的 TLS 終止點必須在本機 |
| ⑤ 本機行程 ↔ SQLite、檔案系統 | — | 以 NTFS ACL 隔離 |
| ⑥ admin（localhost）↔ 研究人員 | — | 需要登入 |

### 資料流與失敗處理（文字時序圖，路線 A：使用者傳照片 → 回覆）

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

**路線 B（LIFF 上傳）的差異**

- 步驟 1–4 改為：U 開啟 `https://liff.line.me/{liffId}`，經 LY 的 LIFF 伺服器轉址 → G → upload-svc。`liff.init()` 取得 ID token，連同照片 POST 到 `/upload`。upload-svc 驗證 ID token，檢查 `aud`、`exp`、`sub`，`sub` 經 HMAC 後應等於 `user_pid`。
- 步驟 6 不需要 Get content。
- 結果直接顯示在 LIFF 頁面上，不耗用任何訊息額度。使用者回到聊天室後，可點選單用 postback 查看結果。

**停機與回復**

- 服務重新啟動時，把 status 為 downloading 或 inferring 的 job 回收為 queued。
- 重送事件以 `webhookEventId` 去重。
- 若 reply token 已失效，依步驟 10 處理。
- 長時間停機後，只能依人工核准補發 push，每人最多一則。

---

## 交付二：LINE 規則速查表

除特別註明外，LINE Developers 文件頁都沒有標示更新日期，以下記為「頁面未標更新日」，查閱日期為 2026-10-30 至 10-31。

| 規則或限制 | 數值 | 官方網址 | 文件日期 | 近年變動 |
|---|---|---|---|---|
| Webhook 簽章 | HMAC-SHA256（channel secret 為 key）、base64、raw body、UTF-8 | [SIG](https://developers.line.biz/en/docs/messaging-api/verify-webhook-signature/) | 頁面未標更新日 | 未見 |
| Webhook 回應 | 回 200；建議非同步處理；可能收到空 events 陣列 | [REF](https://developers.line.biz/en/reference/messaging-api/) | 頁面未標更新日 | 未見 |
| request_timeout 判定 | 約 2 秒沒有回應（取自頁面摘要，**需要逐字確認**） | [ERRSTAT](https://developers.line.biz/en/docs/messaging-api/check-webhook-error-statistics/) | 頁面未標更新日 | 未見 |
| Webhook 重送 | 預設關閉；只在回應非 2xx 時重送；次數與間隔不公開；不保證送達 | [RECV](https://developers.line.biz/en/docs/messaging-api/receiving-messages/) | 頁面未標更新日 | **2022-03-07 公告，2022-04 上旬上線**（[ja/38](https://developers.line.biz/ja/news/38/)，日期取自搜尋摘要） |
| 去重鍵 | `webhookEventId`（ULID）；重送時不變 | [REF](https://developers.line.biz/en/reference/messaging-api/) | 頁面未標更新日 | 與重送功能同時推出 |
| 事件順序 | 不保證，以 `timestamp` 判斷 | [RECV](https://developers.line.biz/en/docs/messaging-api/receiving-messages/) | 頁面未標更新日 | 未見 |
| Reply token | 只能用一次；收到 webhook 後 1 分鐘內有效；可能不經通知變更；standby 模式沒有 token | [REF reply](https://developers.line.biz/en/reference/messaging-api/#send-reply-message) | 頁面未標更新日 | 歷史變更：未找到可靠證據 |
| 每次請求的訊息物件數 | reply 與 push 最多 5 個 | [REF](https://developers.line.biz/en/reference/messaging-api/) | 頁面未標更新日 | 未見 |
| Loading animation | 5–60 秒，須為 5 的倍數，預設 20；只限一對一聊天；一律回 202；100 req/s；需要 LINE 13.16.0 以上 | [LOAD](https://developers.line.biz/en/docs/messaging-api/use-loading-indicator/) | 頁面未標更新日 | **2024-04-17 推出** |
| Retry key | 只適用 push、multicast、narrowcast、broadcast；自行產生 UUID；24 小時有效；重複回 409 | [RETRY](https://developers.line.biz/en/docs/messaging-api/retrying-api-request/) | 頁面未標更新日 | 未見 |
| Rate limit | 其他端點 2,000/s；multicast 200/s；loading 100/s；統計與 insight 60/h；webhook 端點設定 1,000/min | [REF rate](https://developers.line.biz/en/reference/messaging-api/#rate-limits) | 頁面未標更新日 | 未見 |
| Rich menu 速率 | 建立、刪除 rich menu，刪除 alias，查詢批次狀態：100/h；批次取代：3/h；取得清單：10/s | 同上 | 頁面未標更新日 | 未見 |
| Get content | 位於 api-data.line.me；一段時間後自動刪除（期限不公開）；可能被縮小；202 表示準備中；410 表示已收回 | [Get content](https://developers.line.biz/en/reference/messaging-api/#get-content) | 頁面未標更新日 | **網域改為 api-data：2019-11-08 公告，2020-04-30 前須完成**（[News](https://developers.line.biz/en/news/tags/messaging-api)） |
| contentProvider | `line` 用 Get content 取得；`external` 只給 URL | [REF](https://developers.line.biz/en/reference/messaging-api/) | 頁面未標更新日 | 未見 |
| imageSet | 有 id、index（從 1 起算）、total；webhook 送達順序未定義 | 同上 | 頁面未標更新日 | 未見 |
| Get content 檔案大小上限 | **未找到可靠證據** | — | — | — |
| Rich menu 圖片 | JPEG 或 PNG；寬 800–2500 px；高 ≥250 px；寬高比 ≥1.45；≤1 MB；設定後不能更換 | [Upload image](https://developers.line.biz/en/reference/messaging-api/#upload-rich-menu-image) | 頁面未標更新日 | 2024–2026 年：未找到變更紀錄 |
| Rich menu 數量 | 1,000 個選單；1,000 個 alias；每個選單 20 個區塊；chatBarText 14 字；批次綁定 500 人 | [Rich menu object](https://developers.line.biz/en/reference/messaging-api/#rich-menu-object) | 頁面未標更新日 | 同上 |
| Rich menu 優先序 | 個別使用者（API）> 預設（API）> 預設（OA Manager）；個別使用者立即生效；API 預設最多約 1 分鐘生效；PC 版不顯示 | [Overview](https://developers.line.biz/en/docs/messaging-api/rich-menus-overview/) | 頁面未標更新日 | 未見 |
| richmenuswitch | 只能用在 rich menu；label 最多 20 字 | [Switch action](https://developers.line.biz/en/reference/messaging-api/#richmenu-switch-action) | 頁面未標更新日 | 未見 |
| Flex Message | bubble ≤30 KB；carousel ≤50 KB、最多 12 個 bubble；**altText 必填、≤1,500 字元（[A]）**；scaling 需要 LINE 13.6.0 以上；filler 已標示 deprecated | [Flex ref](https://developers.line.biz/en/reference/messaging-api/#flex-message) | 頁面未標更新日 | filler 棄用日期：未查 |
| 文字訊息長度 | 5,000 字元（**[E]**，未經官方核對） | [Pushwoosh](https://docs.pushwoosh.com/zh/developer/api-reference/line-api/index.md) | — | — |
| Quick reply | 最多 13 個；camera、cameraRoll、location 只能用在 quick reply；只支援 iOS 與 Android | [Quick reply](https://developers.line.biz/en/docs/messaging-api/using-quick-reply/) | 頁面未標更新日 | 未見 |
| LIFF SDK | 最新版 v2.31.2（2026-10-07）；**v2.20.0–v2.31.0 已棄用，約 2026-11-24 起限制使用** | [LIFF RN](https://developers.line.biz/en/docs/liff/release-notes/) | release notes 本身有日期 | **2026-09-30、2026-10-20** |
| LIFF channel | 只能加在 LINE Login channel；每個 channel 最多 30 個；endpoint 須 https | [Adding LIFF](https://developers.line.biz/en/docs/liff/registering-liff-apps/) | 頁面未標更新日 | **Messaging API channel 不再支援：2019-11-11 公告，2020-02-05 生效**；LIFF v1 於 2021-10-01 終止 |
| LIFF ID token | 需要 openid scope；有效 1 小時；伺服器以 `POST /oauth2/v2.1/verify` 驗證 | [LIFF user data](https://developers.line.biz/en/docs/liff/using-user-profile/) | 頁面未標更新日 | 未見 |
| LINE MINI App | 未認證版人人可建；台灣與泰國的認證只限 certified provider；只能用 Full 尺寸 | [MINI intro](https://developers.line.biz/en/docs/line-mini-app/discover/introduction/) | 頁面未標更新日 | **2023-12-13 改用 miniapp URL；2025-02-12 宣布整合 LIFF；2025-10-01 起可在網頁瀏覽器使用** |
| userId | 以 provider 為範圍；格式 `U[0-9a-f]{32}`；Get follower IDs 只限認證或 premium 帳號 | [User IDs](https://developers.line.biz/en/docs/messaging-api/getting-user-ids/) | 頁面未標更新日 | 未見 |
| Account Link | link token 只能用一次、10 分鐘有效；nonce 10–255 字元，建議 ≥128 bits；必須可以隨時解除連結 | [Linking](https://developers.line.biz/en/docs/messaging-api/linking-accounts/) | 頁面未標更新日 | 未見 |
| follow／unfollow | follow（加好友或解除封鎖）可以回覆；unfollow 表示封鎖；`isUnblocked` 欄位（SDK [E]） | [RECV](https://developers.line.biz/en/docs/messaging-api/receiving-messages/) | 頁面未標更新日 | isUnblocked 導入日期：未找到可靠證據 |
| Channel access token | v2.1 ≤30 天、30 個；stateless 15 分鐘、無數量限制、不可撤銷；short-lived 30 天、30 個；long-lived 無期限、1 個 | [CAT](https://developers.line.biz/en/docs/basics/channel-access-token/) | 頁面未標更新日；[Tips 2026-07-23](https://developers.line.biz/en/tips/2026/07/23/using-multiple-api-tools/) | 棄用公告：未找到可靠證據 |
| Webhook TLS | TLS 1.2 或 1.3；公開 CA 憑證；不接受自簽憑證；不公開 LINE 的 IP；一個 channel 只能設一個 webhook URL | [TLS spec](https://developers.line.biz/en/docs/messaging-api/ssl-tls-spec-of-the-webhook-source/) | 頁面未標更新日 | 舊 cipher「可能在近期無預警停用」 |
| 錯誤統計 | 須手動開啟；不回溯；時區 UTC+9；可匯出 TSV | [ERRSTAT](https://developers.line.biz/en/docs/messaging-api/check-webhook-error-statistics/) | 頁面未標更新日 | 未見 |
| 錯誤通知 email | 只限已申請的法人用戶；同一狀態碼 5 分鐘內合併通知 | [ERRNOTI](https://developers.line.biz/en/docs/partner-docs/error-notification/) | 頁面未標更新日 | 2023 年加入「重送停止也通知」（確切日期：未找到可靠證據） |
| Insight API | 60 次／小時；約 1 天延遲（人口統計約 3 天）；人數 <20 時回 null；支援台灣帳號 | [REF Insight](https://developers.line.biz/en/reference/messaging-api/) | 頁面未標更新日 | 未見 |
| 計費（台灣） | 輕用量 NT$0／200 則；中用量 **NT$1,000**（舊 NT$800）／3,000 則，不可加購；高用量 **NT$1,400**（舊 NT$1,200）／6,000 則，加購 0.2 元，第 50,001 則起 0.15 元；以上未稅 | [S2](https://tw.linebiz.com/column/LINEOA-2026-Price-Plan/) | **2026-09-01** | **2026-11-01 生效**；前一次調整為 2023 年（日期僅見 [E]） |
| 不計費項目 | Reply API、一對一聊天、自動回應、AI 自動回應、歡迎訊息 | [S1](https://tw.linebiz.com/service/account-solutions/line-official-account/)、[S2](https://tw.linebiz.com/column/LINEOA-2026-Price-Plan/) | S1 為 2026-09-24 版資源；S2 為 2026-09-01 | 未見 |
| 計數方式 | 依收訊人數計；一次請求內的訊息物件數不影響；對已封鎖者或無效 ID 發送不計 | [Pricing](https://developers.line.biz/en/docs/messaging-api/pricing/) | 頁面未標更新日 | 未見 |
| 計費時區 | GMT+9（台灣時間 23:00 以後算隔日） | [S1](https://tw.linebiz.com/service/account-solutions/line-official-account/) | 同上 | 未見 |
| 額度用盡 | 回 429 "You have reached your monthly limit."，訊息不會送出 | [REF](https://developers.line.biz/en/reference/messaging-api/) | 頁面未標更新日 | 未見 |
| 狀態頁 | api.line-status.info，可訂閱 RSS 或 ATOM | [STATUS](https://developers.line.biz/en/docs/basics/line-api-status/) | 頁面未標更新日 | 未見 |
| 個人資料 language 欄位 | BCP 47 格式；使用者未同意隱私權政策時不提供 | [User consent](https://developers.line.biz/en/docs/messaging-api/user-consent/) | 頁面未標更新日 | 未見 |

---

## 交付三：費用試算表

### 計算假設

以下計算結果全部是本報告推論，輸入來源為 [S2](https://tw.linebiz.com/column/LINEOA-2026-Price-Plan/)、[S5](https://vos.line-scdn.net/lbstw-static/assets/frontend/js-20260924-modified/cal.js)、[Pricing](https://developers.line.biz/en/docs/messaging-api/pricing/)，查閱日 2026-10-30 至 31。

1. 每一次分析都對應 1 位使用者的一對一聊天。每次 push 只發給單一 userId，每次請求最多 5 個訊息物件。因此 1 次 push 計為 1 則。
2. reply、postback 觸發的 reply、loading animation 都不計費。loading animation 不計費這一點屬於推論，官方沒有明文。
3. 設計 C 假設每位使用者每月平均分析 5 次，所以 100、1,000、10,000 次分別對應 20、200、2,000 人。這個比例是假設，不是來源數字。
4. 對已封鎖者或無效 ID 發送的訊息假設為 0 則。
5. 每種情境都選「能容納該則數的最便宜方案」。中用量上限 3,000 則，不可加購。
6. 含稅金額以 5% 營業稅估算。**這個稅率未經本次官方來源查證**，實際以 LINE 開立的電子發票為準。
7. 只計算 LINE 訊息費。伺服器、電費、GPU、網域或 VPS 費用不在範圍內。LINE Login、LIFF、MINI App 是否另外收費，**未找到可靠證據**。

### 對話設計說明

| 設計 | 流程 | 每次分析的 push 則數 |
|---|---|---|
| A：全 reply（建議） | 照片 → loading → reply 結果；逾時就給「查看結果」postback 按鈕 | 0 |
| B：1 push | 推論完成後主動 push 結果 | 1 |
| C：2 push＋月提醒 | push 一則「已收到」，再 push 一則結果，另外每人每月 1 則提醒 | 2，加上每人每月 1 |
| D：reply 為主，5% 用 push 補發（推論） | 設計 A，但 5% 的 job 逾時後以 push 補發 | 0.05 |
| E：LIFF 上傳＋頁內顯示結果（推論） | 結果顯示在 LIFF 頁面；回到聊天室後用 postback 加 reply 查看 | 0 |

### 每月計費則數

| 設計 | 100 次 | 1,000 次 | 10,000 次 |
|---|---|---|---|
| A | 0 | 0 | 0 |
| B | 100 | 1,000 | 10,000 |
| C | 2×100+20 = 220 | 2×1,000+200 = 2,200 | 2×10,000+2,000 = 22,000 |
| D | 5 | 50 | 500 |
| E | 0 | 0 | 0 |

### 自 2026-11-01 起（新價，未稅，NT$）——主要依據

| 設計／量級 | 最低可行方案 | 計算 | 月費用（未稅） | 含 5% 稅（估） | 每次分析成本 |
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

### 至 2026-10-31 止（舊價，未稅，NT$）——比較用

| 設計／量級 | 方案 | 計算 | 月費用 | 與新價差額 |
|---|---|---|---|---|
| A、E／全部 | 輕用量 | 0 | 0 | 0 |
| B／100 | 輕用量 | 0 | 0 | 0 |
| B／1,000 | 中用量 | 800 | 800 | +200 |
| B／10,000 | 高用量 | 1,200 + 4,000×0.2 | 2,000 | +200 |
| C／100 | 中用量 | 800 | 800 | +200 |
| C／1,000 | 中用量 | 800 | 800 | +200 |
| C／10,000 | 高用量 | 1,200 + 16,000×0.2 | 4,400 | +200 |
| D／10,000 | 中用量 | 800 | 800 | +200 |

### 固定在某一方案時的可行性（新價）

✗ 表示超出額度的 push 會回 429，訊息送不出去。

| 情境（每月則數） | 輕用量 NT$0（200 則） | 中用量 NT$1,000（3,000 則） | 高用量 NT$1,400（6,000 則＋加購） |
|---|---|---|---|
| A、E（0） | ✓ | ✓（多付） | ✓（多付） |
| B-100（100） | ✓ | ✓ | ✓ |
| B-1,000（1,000） | ✗ 第 201 則起失敗（約 800 則結果送不出） | ✓ | ✓ |
| B-10,000（10,000） | ✗ | ✗ 第 3,001 則起失敗 | ✓ NT$2,200 |
| C-100（220） | ✗ 超出 20 則 | ✓ | ✓ |
| C-10,000（22,000） | ✗ | ✗ | ✓ NT$4,600 |
| D-10,000（500） | ✗（超出部分應自動降級為 postback，見第 2 節） | ✓ | ✓ |

### 敏感度分析

以下皆為本報告推論。

- **設計 C 拿掉每月提醒：** 100 次分析只需 200 則，剛好等於輕用量的上限，完全沒有緩衝。只要多出任何一則 push，例如停機後的補發，就會收到 429。
- **高用量的邊際成本：** 每多 1 則 push 要 NT$0.2，直到當月加購滿 50,000 則；之後每則 NT$0.15。
- **年度差額：** 每月 10,000 次分析時，設計 C 比設計 A 每年多花約 NT$55,200（4,600 × 12，未稅）。
- **混合設計的安全範圍：** 每月 push 不超過 200 則，就能維持 NT$0。超過時，把 push 補發自動降級為 postback，也能維持 NT$0。
- **月底時區效應：** 計費以日本時區計算。台灣時間月底 23:00 之後發出的 push 會計入下個月，在額度邊緣時可能讓下個月提早用完。

---
## 交付四：對話流程與文案範本

以下所有文案都是**本報告推論**，依據第 5、10、11 節引用的證據設計。正式上線前，必須先經過四道關卡：

- 臨床護理專家審定（特別是紅旗清單與時間承諾）
- IRB 核准（同意書與撤回說明）
- 法規顧問審閱（確認沒有診斷宣稱）
- 長者與照顧者理解測試

**標記說明：**〈〉代表變數，【】代表 quick reply 或 postback 按鈕。

**共同格式：**

1. 第一行寫結論或要對方做的事
2. 接著用最多 3 點說明
3. 再列紅旗症狀或下一步
4. 最後一行用小字註明這是研究

每則都以純文字送出。如果改用 Flex，altText 就填第一行的全文。每則控制在約 120–150 字以內。

> **跨筆記衝突的處理：同意文案中「照片存在哪裡」。**
> 08 號筆記的同意範本寫「照片只用在研究，存在〈醫院〉的電腦，不會給其他公司」。但 04、05、06 號筆記都指出，走聊天路徑時照片一定會先暫存在 LINE 的伺服器，而且臺大的網路研究指引也要求告知「傳輸可能被第三方截取」的風險。如果照原文寫「不會給其他公司」，**會構成不實陳述**。下方的 F1 已改成揭露版本，並依照片路線（A 或 B）提供兩種寫法。

### 對話流程總覽

1. **加好友**（follow 事件）→ 用 reply 送出 F0 歡迎訊息與語言選擇 → 送出 F1 同意摘要。這時使用者看到的是預設圖文選單，選單上沒有上傳按鈕。
2. 使用者點【先看完整說明】→ 開啟同意頁（自有 HTTPS 網頁或 LIFF）→ 回答 2–3 題是非題 → 自我聲明 → 按【我同意】。
3. 系統寫入 `consent_events`，把該使用者的圖文選單換成同意後版本，並送出 F2 拍照說明。
4. 使用者傳照片後，依結果回覆其中一則：F3 品質不足、F4 需人工確認、F5 建議告訴護理師或就醫、F5b 沒有看到明顯紅腫。
5. **任何時候**使用者回報紅旗症狀，都送出 F6 緊急轉介。
6. 使用者點【撤回同意】→ 先送 F7a 確認問題 → 使用者再次確認後送 F7 撤回確認。
7. 使用者封鎖帳號（unfollow）時，**不回覆**（unfollow 事件無法回覆），狀態設為 `paused`。使用者解除封鎖後（follow 事件且 `isUnblocked=true`），送出 F8。

### F0 歡迎與語言

```
您好，這裡是〈研究團隊名稱〉的打針部位照片研究帳號。
請先選擇語言。
【中文】【English】【Bahasa Indonesia】【Tiếng Việt】
```

**設計理由：**

- LINE profile 中的 `language` 欄位只能當作預設值。使用者沒有同意隱私權政策時，這個欄位不存在；而且手機的語言設定也不一定是使用者的閱讀偏好。
- 列出的語言以照顧者常用語言為優先（第 11 節）。

### F1 同意摘要（第一層）

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

**設計理由：**

- 第一行就說明「這是研究，不是看病」，對應第 10 節「行動與性質放在第一行」的原則。
- 內容切成四點，符合 AHRQ 的分段原則。
- 據實揭露照片會經過 LINE（第 4、5、7 節）。
- 寫明「撤回立即生效」與「不影響治療」，這是受試者保護的慣例。
- 寫明「封鎖不等於退出」，並提供 LINE 以外的撤回管道，因為使用者封鎖帳號後就無法在 LINE 內聯絡（第 5 節）。
- 「我是幫家人傳」這個按鈕處理照顧者代傳的情境。70 歲以上族群的上網率只有 53.80%（第 11 節）。
- 這一則**不放「我同意」按鈕**，要求使用者先進入第二層的完整說明，避免用「跳過關鍵資訊」的方式取得同意。依據是 [E] 來源中 IRB 審查慣例的建議：不要設計讓受試者可以跳過關鍵研究資訊的流程。

### F1b 第二層：完整說明頁上的確認問題（網頁或 LIFF）

```
請回答 3 個小問題（答錯沒關係，會再說明一次）：
1. 這個服務會告訴我「我有沒有得靜脈炎」嗎？　○會　○不會（正解：不會）
2. 我可以隨時退出嗎？　○可以　○不可以（正解：可以）
3. 打針的地方很痛、很紅時，我應該等這個帳號回覆嗎？　○要等　○不用等，直接告訴護理師（正解：不用等）
□ 我已年滿 18 歲（或依 IRB 核定），是照片中手臂的本人，或其法定代理人。
□ 我是代傳的家人或看護，病人本人／法定代理人已同意。
【我同意參加】
```

**設計理由：**

- 用是非題做簡化版的 teach-back（AHRQ）。**答錯不會被排除**，只會再說明一次。
- 第 3 題直接針對過度依賴系統的風險（automation bias，第 10 節）。
- LINE 無法驗證年齡或是否為本人，所以改用自我聲明（第 5、6 節）。
- 按下【我同意】時，postback 帶回 `consent_version` 和 `doc_sha256`，系統寫入 append-only 紀錄。

### F2 上傳照片說明

```
請拍「打針的地方」，照這樣拍：
1. 在亮的地方拍，不要開閃光燈，不要用濾鏡或美顏。
2. 手機離手臂大約一個手掌遠。
3. 整個貼布和周圍皮膚都要拍進去。
4. 一次傳一張就好；自己拍不到，可以請家人幫忙。

拍好直接傳到這裡。
【拍照】【從相簿選】【看範例圖】【我現在在醫院】
```

**設計理由：**

- 步驟化，每句只講一件事（CDC CCI 與 AHRQ 原則）。
- 「一個手掌遠」用具體參照取代公分數字。
- 「不要用濾鏡」來自 BAD 的指引，也呼應第 3 節的色偏風險。
- 「請家人幫忙」依據 Gunter 2016：使用者自己拍照是整個流程中最困難的一步。
- 【拍照】和【從相簿選】是 camera action 和 cameraRoll action。這兩種動作只能放在 quick reply，而且按鈕會一直保留到使用者送出照片為止。
- 第四顆按鈕用來收集「住院中或已回家」的情境，後續分流會用到。
- quick reply 最多 4 顆，方便長者閱讀。

範例圖的 altText 寫成：「範例：手臂打針處，貼布在畫面中間的照片」。

### F3 品質不足，請重拍

```
這張照片看不清楚，請再拍一次。
原因：〈太暗／太模糊／打針的地方不在畫面裡〉

小提醒：到亮一點的地方，手拿穩再拍。

不管照片結果如何，如果打針的地方很痛、變紅、腫起來：
在醫院請直接按鈴告訴護理師；在家請聯絡幫您打針的醫院。
【重新拍照】【看拍照範例】【我不會拍，找真人】
```

**設計理由：**

- 第一行就是要使用者做的事。
- 不責怪使用者：寫「照片看不清楚」，而不是「您拍錯了」。
- 給具體原因，研究證據顯示即時品質回饋加上重拍最有效（Vodrahalli 2023、Zhang 2021）。
- 照片不合格、沒有結果時，仍然附上最基本的紅旗提醒，避免使用者因為等不到結果而延誤就醫。
- 【重新拍照】是 camera action。
- 原因的文字依品質檢查結果填入，只用固定詞彙。

### F4 需人工確認（模型低信心）

```
這張照片，研究系統沒辦法判斷，已經請研究人員再看一次。
我們會在〈例如：上班時間 24 小時內〉回覆您。

等待的時候，如果打針的地方痛、紅、腫、變硬，或流膿、發燒：
・在醫院：現在就按鈴告訴護理師，不用等我們。
・已經回家：請聯絡幫您打針的醫院或診所。

這是研究系統，不是醫師的判斷。
【好，我知道了】【我在醫院】【我已經回家】
```

**設計理由：**

- 直接寫「系統沒辦法判斷」，不用「可能」「也許」。研究顯示口語化的不確定說法較傷信任（van der Bles 2020），而且不同人對機率詞的理解差異很大（Andreadis 2021）。
- 寫出具體的等待時間。這個承諾必須依照實際研究人力確認。
- 「不用等我們」用來避免使用者因為依賴系統而延誤（第 10 節）。
- 【好，我知道了】當作簡易的理解確認。
- 人工回覆時，研究人員可以使用 OA Manager 的一對一聊天，這部分不計費（第 2 節）。

### F5 建議告訴護理師或就醫（模型輸出 stage 1 或 stage 2）

**住院版：**

```
請告訴護理師看一下您打針的地方。〈stage 2 時：請現在就按鈴。〉

研究系統在照片中看到〈發紅／腫起來〉的樣子。
這不是診斷，要由護理師親自看才算數。

如果有下面任何一種，請馬上按鈴：
・越來越痛　・紅的範圍變大　・摸起來硬硬的、像一條線
・流膿或滲水　・發燒、發冷
【我會告訴護理師】【我看不懂】【找真人】
```

**在家或門診版：**

```
建議今天聯絡幫您打針的醫院或診所，請他們看一下。

研究系統在照片中看到〈發紅／腫起來〉的樣子。
這不是診斷，要由醫師或護理師親自看才算數。
拔針後 2 天內，仍要每天看一下打針的地方。

如果發燒、發冷、紅線往上延伸，或整隻手臂腫起來，
請馬上去醫院；很嚴重時撥 119。
【我會聯絡醫院】【我看不懂】【找真人】
```

**設計理由：**

- 第一行就是行動（CDC CCI）。
- 寫「照片中看到……的樣子」，不寫「您有第 2 期靜脈炎」。民眾看不到期別和分數，這些只存在研究資料庫裡（第 10 節）。
- stage 1 和 stage 2 只在第一行的緊急程度上有差別，對應 VIP 量表：1 項徵象觀察，2 項徵象更換部位。
- 紅旗最多列 5 項，用口語描述：「像一條線」是可觸及的靜脈索，「發燒」對應 VIP 量表的 5 分。
- 在家版加入「拔針後 2 天內」的提醒（NHS Lothian：感染最常發生在拔針後 48 小時內）。
- 不提供冷敷、熱敷建議，因為台灣與英國的衛教內容不一致，而且冷熱敷屬於治療建議。
- 不寫 1922，那是傳染病專線。
- 「紅線往上延伸、寒顫」**尚未經 [A] 來源逐條核對，需由臨床人員審定**。
- 【我看不懂】點下去後，送出更簡化的版本，或轉給真人。

### F5b 沒有看到明顯紅腫（避免讓人誤以為安全）

```
這張照片中，研究系統沒有看到明顯的紅或腫。
但照片看不出痛不痛、硬不硬，請繼續注意。

只要打針的地方痛、紅、腫、變硬、流膿，或發燒，
在醫院請按鈴告訴護理師；在家請聯絡醫院或診所。

這是研究系統，不是醫師的判斷。
【好，我知道了】
```

**設計理由：**

- 不寫「沒有靜脈炎」。
- 明白說出照片的限制。
- 紅旗清單照樣列出，不省略（第 10 節）。

### F6 緊急轉介（使用者用文字或按鈕回報紅旗，或系統偵測到關鍵字）

```
這可能需要馬上處理，請不要等研究系統回覆。

・在醫院：現在按床邊的呼叫鈴，找護理師。
・在家：請立刻去急診。
・如果呼吸困難、胸痛、昏昏沉沉叫不醒，或流血止不住：請立刻撥 119。

這個帳號沒有人 24 小時看訊息，緊急時請不要只傳訊息給我們。
【我在醫院，去按鈴】【撥打 119】
```

**設計理由：**

- 第一行就是「不要等」。
- 誠實說明帳號沒有 24 小時有人值守。
- 119 是台灣的救護專線（[E] 來源）。
- 【撥打 119】按鈕使用 URI action `tel:119`，在 LINE 裡的實際行為**需要實機測試**。
- 胸痛、呼吸困難等是一般急症常識，不是靜脈炎特有的症狀，需由臨床人員審定。
- 留置針脫落時的止血方式（按壓 2–5 分鐘，依 NHS Lothian）放在另一則 F6b 說明，避免這則訊息太長。

### F7a 撤回前確認

```
您要退出照片研究嗎？
退出後，我們不會再使用您之後傳的照片。
【確定退出】【先不要】
```

**設計理由：**防止誤觸。這則用 postback 送出，回覆不計費。

### F7 撤回同意確認

```
已收到，您已退出照片研究，馬上生效。

・從現在起，我們不會再使用您之後傳的照片。
・您之前的照片：〈依 IRB 核定的同意書：將在 N 天內刪除〉。
・退出不會影響您的治療。

如果改變主意，隨時可以按【重新參加】。
有問題請找：〈研究聯絡電話〉
【重新參加】【我還有問題，找真人】
```

**設計理由：**

- 第一行先確認結果。
- 分別說明「之後」與「之前」的資料怎麼處理，內容必須和同意書、第 5 節的撤回流程一致。
- 08 號筆記原本的寫法是「已去識別的研究資料無法再分開，會保留」。本報告**不建議**把照片寫成可以去連結後保留，因為身體影像很難達到「永久不能連結」的標準（第 5 節）。只有在 IRB 核准、而且資料確實是不含照片的彙總統計時，才寫入這種說法。
- 重申不影響治療。
- 提供重新參加的途徑。

送出 F7 的同時，系統要做這些事：解除綁定的圖文選單（unlink）、寫入 `withdrawn` 事件、加入 exclusion list、排入刪除工作、在模型登錄表標記受影響的模型，**不觸發自動訓練**。

### F7c 撤回後又傳照片

```
您已退出研究，這張照片不會被使用或保存。
如果想重新參加，請按【重新參加】。
【重新參加】【找真人】
```

**設計理由：**撤回立即生效的技術意義，就是之後收到的照片一律不下載、不推論。

### F8 解除封鎖後回來（follow 事件且 `isUnblocked=true`）

```
歡迎回來。您的研究狀態是：〈參加中／已退出〉。
〈同意書已更新時：研究說明有更新，請先看新的說明再決定是否繼續。〉
【看研究說明】【撤回同意】
```

**設計理由：**

- 封鎖期間系統狀態為 `paused`，不是撤回。
- 使用者回來時告知目前的狀態。
- 如果同意書版本已經更新，要求重新同意（第 5 節）。

### 多語與無障礙備註

- 以上模板交由專業譯者翻成英文、印尼文、越南文，再經回譯與母語照顧者測試。
- F5、F6 優先錄製台語真人語音版。
- **不使用雲端翻譯、雲端語音轉文字或雲端語音合成**（⚠）。
- 每則都用中文版 CDC CCI 自評，目標 90 分以上。

---

## 交付五：上線前技術檢查清單

勾選前，請在本平台實際測試，並把結果記錄下來。

### 安全

- [ ] webhook 用 raw bytes 做 HMAC 驗證，比對使用 `compare_digest`。header 缺漏時回 400，不會變成 500。單元測試涵蓋 emoji 與 CRLF。
- [ ] 驗簽通過之後才解析 JSON。沒有使用 Pydantic body 參數。沒有任何 middleware 改寫 body。
- [ ] webhook-svc 與 admin 是兩個獨立的 app。`/docs`、`/redoc`、`/openapi.json` 已關閉。對外只開放 `POST /webhook/<隨機字串>`，其他路徑回 404。
- [ ] admin 只綁 127.0.0.1，防火牆擋下 8000、8001 的入站流量，admin 需要登入。
- [ ] 對外入口的 TLS 只允許 1.2 和 1.3，使用公開 CA 憑證，憑證鏈完整。**如果有 LIFF 上傳路徑，TLS 終止點必須在本機**（Tailscale Funnel 或自架反向代理），不能用 Cloudflare 或 ngrok ⚠。
- [ ] 不使用 ngrok。如果非用不可，Traffic Inspector 的 full capture 必須關閉，並經過書面確認 ⚠。
- [ ] channel access token 使用 v2.1 或 stateless（JWT 版）。沒有使用 long-lived token，也沒有使用 `client_secret` 版的 stateless token。
- [ ] RSA 私鑰、channel secret、HMAC pepper 存放在 Windows Credential Manager。不在 repo、不在 `.env`、不在 log、不在備份裡。
- [ ] 憑證外洩的應變步驟（runbook）已寫好並實際演練過。
- [ ] log 遮罩通過測試：一週的 log 中，搜尋 `U[0-9a-f]{32}`、`Bearer`、`replyToken`、`x-line-signature` 都是 0 筆。uvicorn 的 access log 已關閉。httpx 的 logger 等級設為 WARNING。
- [ ] 沒有使用雲端 APM 或錯誤追蹤服務 ⚠。
- [ ] 圖片下載有大小上限。Pillow 使用 `formats=` 限制格式，DecompressionBomb 視為錯誤。來源為 `external` 的圖片一律拒收。httpx 設定 `follow_redirects=False`，並限制可連線的網域。
- [ ] 服務以標準使用者帳號執行。DB、照片、秘密檔案的 NTFS ACL 已限縮。BitLocker 或裝置加密已啟用，外接備份碟也已加密。
- [ ] **照片與 DB 的路徑不在 OneDrive 同步範圍內**，已實際確認 ⚠。
- [ ] 相依套件以 hash 鎖定版本，`pip-audit` 檢查結果為 0 個高風險項目。如果有 LIFF，SDK 版本至少是 2.31.1。
- [ ] 研究資料表中沒有明文 userId。`line_link` 存放在另一個加密的資料庫檔案。匯出的資料集裡沒有 userId，也沒有 GPS。

### 可靠性

- [ ] Console 已開啟「Use webhook」、「Webhook redelivery」、「Error statistics aggregation」，有截圖存檔。
- [ ] 事件以 `webhookEventId` 去重：同一事件送 3 次，只產生 1 個 job。
- [ ] webhook 的 p99 回應時間低於 200 ms。Console 的錯誤統計在一週內 `request_timeout` 為 0。
- [ ] job 佇列使用 SQLite WAL 模式。服務啟動時會回收卡住的 job。重試採指數退避，失敗的 job 進入 dead 狀態並發出告警。
- [ ] 同一位使用者的 job 依 `timestamp` 排序處理。GPU worker 只有一個。佇列優先處理最早到期的 job。
- [ ] 收到 image 事件後立刻呼叫 Get content。202、5xx、410 三種情況都有對應處理。
- [ ] 有 reply token 逾時的退路：預設改用 postback 的「查看結果」。用 push 需要核准，並附 retry key。額度用盡的 429 不重試。
- [ ] 實際測試過：延遲 65 秒的情況、worker 被強制終止的情況、停機 10 分鐘的情況。
- [ ] Windows 已設為服務、開機自動啟動、崩潰後自動重啟。休眠已關閉，Windows Update 有維護時段，有 UPS，tunnel 會自動重連。
- [ ] 圖文選單分為同意前和同意後兩種，透過 per-user link 切換。伺服器收到每張照片時，都會再次檢查同意狀態。
- [ ] unfollow 事件會把狀態改為 `paused`。follow 事件會讀取 `isUnblocked`。unsend 事件會刪除對應資料。`mode=standby` 的事件不回覆。

### 監控

- [ ] `/healthz`（只綁本機）回報 DB 是否可寫入、佇列深度、最舊 job 的等待時間、GPU 狀態、worker 心跳。
- [ ] 告警條件已設定：最舊 job 超過 45 秒、驗簽失敗暴增、Invalid reply token 比例升高、心跳超過 60 秒、磁碟空間不足、連續出現 5xx 或 429、GPU 不可用。告警透過 email 或 Windows 通知發出，內容不含個人資料。
- [ ] 每天比對系統回覆數和 LINE 的 reply 與 push 發送數，並記錄 `consumption` 與 `quota`。官方帳號方案已確認是「輕用量」。
- [ ] 每天排程抓取一次 Insight 的 followers 資料。儀表板不會每次刷新都呼叫 Insight。
- [ ] 已訂閱 api.line-status.info 的 RSS。
- [ ] 研究 KPI（收件數、同意率、品質不足比例、預測分布、撤回次數）只用自建資料表計算，排除重送事件。對外報告時，人數過少的格子會被遮蔽。
- [ ] 模型監控每週檢視：預測分布、分數分布、輸入特徵、需人工確認的比例、抽樣審閱結果、影子模型的分歧率。

### 回滾與模型治理

- [ ] 模型登錄表以 SHA-256 識別模型，狀態機程式強制規定只有 approved 狀態的模型可以設為 active。外部 safetensors 模型只能先登錄為 candidate。
- [ ] 啟動時驗證模型雜湊，不符時降級為「需人工確認」。
- [ ] 上一個 approved 模型保持熱備，回滾演練可在數秒內完成並留有紀錄。
- [ ] 自動回滾只會因工程 guardrail 觸發（錯誤或逾時、雜湊不符、輸出不合法、類別分布極端）。觸發後通知負責人，並需人工確認是否維持回滾。**沒有自動晉升，也沒有自動訓練** ⚠。
- [ ] 影子模型在 reply 送出後才執行，失敗不影響主流程。同意書已揭露有影子分析。
- [ ] 影子模型轉為正式上線的書面門檻已寫好，並由負責人簽核。現階段（14 位個案）不做任何依效能決定的切換。
- [ ] 撤回流程演練通過：照片已刪除、連結已斷開、exclusion list 已更新、資料快照與模型都已標記。
- [ ] 若需聯絡曾收到錯誤結果的使用者，訊息模板已事先審定，發送前需人工核准，並寫入 IRB 計畫書。

### 內容與合規（非技術，但上線前必須完成）

- [ ] IRB 已決定照片走 A 或 B 路線，同意書已揭露照片會經過 LINE（A 路線）或 LIFF 的資料流（B 路線），並決定好封鎖、撤回、保存期限的處理方式。
- [ ] F0 到 F8 的文案已經過臨床審定、IRB 與法規顧問審閱，CCI 評分 90 以上，並完成長者理解測試。
- [ ] 已人工查閱 LINE 官方帳號條款與 User Data Policy，確認對健康資料的規定（本輪**未找到可靠證據**）。

---

## 名詞對照表

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

---
## 結語

這份研究原本預期 LINE 服務的難題是費用與 API 限制，查完之後發現難題在別處。費用可以靠對話設計壓到 NT$0。真正需要早做決定、而且之後很難改的，是三件事：

1. 照片的資料流要走 LINE 聊天，還是走 LIFF 直傳？
2. 同意、撤回與模型治理的紀錄要怎麼設計，才能經得起稽核？
3. 回覆文案能不能把「研究系統」和「就醫行動」清楚分開？

第一件是 IRB 層級的決定，會連帶決定第 7 節的對外暴露方案，也會決定第 4 節的介面組合。所以應該最先送 IRB 討論，而不是等工程完成後再補揭露。

在 14 位個案的階段，LINE 服務能可靠證明的只有工程面的事：不漏件、不重複、不逾時、不洩漏。模型面的事，例如 LINE 照片和醫院照片的表現差異、候選模型是否較好、品質門檻是否適當，現在都不可靠。等資料累積到約 1,000 張、三類平衡，並且以病人為單位切分之後才能回答。

因此現階段最有價值的投資，是把「收得到、存得對、回得快、可追溯」做紮實，同時讓影子模式與分歧審閱持續累積標註。到了需要做效能型切換的時候，資料與流程就都已經準備好，也不必違反「不自動上線」原則。

---

## 參考文獻

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
- 臺大醫院研究倫理委員會. 網路研究倫理審查指引（2020-09）；AF-143-02 網路研究自評表. https://www.ntuh.gov.tw/ （完整網址見第 5 節；經搜尋摘要；查閱 2026-10-31）
- 行政院. 個資去識別化驗證（CNS 29100／29191）新聞稿（民國 104 年）. https://www.ey.gov.tw/Page/9277F759E41CCD91/af28eb4c-7030-49bb-889d-f0a0fed6a4d5 （查閱 2026-10-31）
- 國家發展委員會函釋（民國 108 年）. 臺北市法規查詢系統 FE372646. https://laws.gov.taipei/Law/Interpretation/Content/FE372646 （查閱 2026-10-31）
- 衛生福利部. 1922 防疫專線. https://www.mohw.gov.tw/cp-88-218-1.html （查閱 2026-10-30）
- 教育部. 臺灣台語羅馬字拼音方案使用手冊（113-08-26 修正）. https://language.moe.gov.tw/files/people_files/tshiutsheh_1130826.pdf （查閱 2026-10-30）
- 勞動部. 外籍工作者統計（112 年底）. https://www.mol.gov.tw/media/aklhtid2/12-外籍工作者.pdf （僅搜尋摘要；查閱 2026-10-30）
- 食品藥物管理署. 醫用軟體分類分級參考指引（第三方轉載副本）. https://mdcpp.com/doc/materialDownload/ （完整網址見第 10 節；未從 fda.gov.tw 核對；查閱 2026-10-30）
- 國家衛生研究院論壇. 我國高齡長者健康識能之決定因子與其健康結果（[A/C]）. https://forum.nhri.edu.tw/ （完整網址見第 10 節；僅搜尋摘要；查閱 2026-10-30）
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

---

## 最後自我檢查

**1. 關鍵數字都有來源與日期。**

- 以下數字都附了 [A] 來源網址與查閱日期：價格（新舊兩套）、免費則數、加購級距、reply token 一分鐘、loadingSeconds 5–60、rate limit、retry key 24 小時、rich menu 與 Flex 的各項上限、LIFF 版本與限制日期、token 效期與上限、TLS 規格、Insight 門檻。
- LINE Developers 頁面一律註明「頁面未標更新日」。
- 2 秒 webhook 逾時這個數字來自頁面摘要，已標示需要逐字確認。
- 2023 年的調價日期只有 [E] 來源，已標示。
- 5% 營業稅是未經查證的假設，已標示。
- Wilson 信賴區間、McNemar 樣本量、費用試算都標為「本報告計算或推論」。

**2. 沒有編造文獻，不確定處都已標示。**

- 所有來源都出自八份研究筆記，沒有新增。
- 筆記中標為「僅搜尋摘要」「未逐字核對」「未找到可靠證據」的項目，都保留原本的標記，沒有升級。

例如以下項目保留「未找到可靠證據」：

- Get content 的保存天數與檔案大小上限
- EXIF 的處理方式
- 內建相機是否套用濾鏡
- LIFF 與 LINE MINI App 是否收費
- LINE 是否禁止官方帳號收集健康資料
- 重送事件中 reply token 不可用的具體情況
- 台灣對研究同意紀錄的最低保存年限

**3. 筆記之間的衝突都已明確裁決。**

| 衝突 | 裁決 | 位置 |
|---|---|---|
| tunnel 業者看不看得到照片 | 依路徑而定：聊天路徑看到的是 webhook JSON；LIFF 上傳路徑才會看到照片 | 第 7 節 |
| altText 1,500 字元的來源等級 | 採 [A] | 第 4 節 |
| 06 號筆記說 reply token 時限與 rate limit「未找到」 | 以 01、02 號筆記的 [A] 來源為準 | — |
| ID token 驗證端點的方法 | 依 04 號筆記的 [A]：ID token 用 POST，access token 用 GET | — |
| 08 號筆記同意範本寫「不會給其他公司」 | 改為揭露照片會經過 LINE | 交付四 |
| 06 號筆記主張「佇列長時改用 push」 | 改為預設 postback，與 02 號筆記一致 | — |
| rich menu 速率表的寫法不同 | 以官方表格為準 | — |
| PCCP 的定稿日期 | 兩個日期並列 | — |

**4. 每項建議都已對照不可違反的原則。**

已標出 ⚠ 並提出替代方案的項目：

| 有衝突的做法 | 替代方案 |
|---|---|
| 照片暫存在 LINE 伺服器 | 交 IRB 決定並揭露，或改走 LIFF 直傳 |
| 用 Cloudflare 或 ngrok 傳照片 | Tailscale Funnel 或自架反向代理 |
| ngrok Inspector | 不使用 |
| 雲端 APM | 本機 log |
| OneDrive 同步 | 改用不同步的路徑 |
| 依比例擴大流量的金絲雀發布、自動晉升模型 | 人工簽核的分階段上線；只允許自動回滾 |
| 撤回後自動重訓 | 標記後由人工排程 |
| 雲端翻譯、語音辨識、語音合成 | 預先翻譯的模板、預錄語音、本機模型 |
| 面向使用者的 A/B 測試 | 不建議 |

另外，外部 safetensors 模型一律只能以 candidate 身分登錄，在本專案資料上完整評估後才能晉升。

**5. 已區分研究證據、業界慣例與本報告推論。**

各節都已標示哪些是研究證據、哪些是業界慣例、哪些是本報告推論。以下屬於**業界慣例**，沒有同儕審查的佐證：

- 佇列、冪等、dead-letter 的設計
- Windows 上的秘密保存
- 防火牆與 ACL 設定
- 金絲雀發布做法
- PSI 門檻

工作量估計與所有文案都屬於**本報告推論**。

**6. 在 14 位個案下仍不可靠的結論，已明確指出。**

以下結論在目前規模下都不能成立：

- LINE 照片與醫院照片的表現差異。依來源分層的評估檢定力不足，結果和病人、分期混雜在一起。
- 候選模型「較好」或「不劣」。目前 normal 類只有 9 張，CI 寬度約 0.42。
- 品質門檻是否恰當。
- 「LINE 退化擴增」是否有效。
- 任何子群比較。
- 撤回一人對模型的影響是否可以忽略。目前撤回一人約等於 7% 的受試者，不能忽略。

這些都要等到資料累積到約 1,000 張、三類平衡、以病人為單位切分，並由兩位以上標註者標註之後，才能回答。

在現有規模下仍然可靠的，只有工程面的驗證：簽章、去重、時限、log 遮罩、回滾演練。
