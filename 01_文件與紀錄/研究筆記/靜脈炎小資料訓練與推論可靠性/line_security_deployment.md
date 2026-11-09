# LINE 公開照片服務的惡意輸入／濫用防護，與單一消費級 GPU 的推論部署效能

> 研究筆記（供報告撰寫者轉寫為繁體中文章節）。所有來源存取日期：2026-10-30～2026-10-31（下稱「存取 2026-10-31」）。
> 來源分級：[A] 官方文件／標準；[B] 系統性回顧、頂級期刊／會議同儕審查；[C] 其他同儕審查；[D] 預印本；[E] 部落格、論壇、官方範例碼（僅輔助）。
> 用語區分：「研究證據顯示」＝論文；「業界實務／官方建議」＝官方文件或標準；「本報告推論」＝作者依據前兩者及專案程式碼所作判斷。
> 專案程式碼現況係直接閱讀 `02_主程式碼/src/line_bot/service.py`、`src/inference/engine.py`、`configs/service.json`、`src/imports/external.py`（2026-10-31）所得，標記為〔程式碼現況〕。
> 情境：NOW＝約 120 張照片、14 位病人、低流量；FUTURE＝約 1,000 張、使用者增加。

## 問題一：LINE Messaging API 官方規則（簽章、重送與去重、快速回應、reply token、push/reply 計費、速率限制、取得內容、loading 動畫、封鎖事件）

### Takeaway
LINE 官方文件要求驗證 `x-line-signature`（以 channel secret 對原始 body 做 HMAC-SHA256 再 Base64）、回 200、建議非同步處理事件，並以 `webhookEventId` 去重；reply token 只能用一次且「一分鐘內」使用才有保證；reply 不計入訊息則數而 push 計入，台灣「輕用量」每月僅 200 則免費且不可加購，且 2026/11/1 起中／高用量月費調漲。官方文件**沒有**公布 webhook 逾時秒數、重送次數／間隔，也沒有公布使用者上傳內容的保存期限。

### Cited Findings

**Webhook 簽章與回應**
- [A] 官方要求收到 webhook 後在處理事件前「verify the signature included in the request header」，以確認請求來自 LINE Platform 且未被竄改；細節導向「Verify webhook signature」頁。— [LINE Developers, Receive messages (webhook)](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)（頁面無 last-updated 日期；存取 2026-10-31）
- [A] 簽章：`x-line-signature` 標頭；範例程式以 channel secret 對**原始 request body** 計算 HMAC-SHA256、Base64 編碼後與標頭比對；標頭名稱大小寫不敏感。— [LINE Messaging API reference（Markdown 版）](https://developers.line.biz/en/reference/messaging-api/index.html.md)（無 last-updated 日期；存取 2026-10-31）
- [A] 「The bot server must return status code `200` after it receives the HTTP POST request」；並建議「make the event processing asynchronous」，避免慢處理拖延後續事件。**文件未給出逾時秒數**。— 同上 reference；[Receive messages](https://developers.line.biz/en/docs/messaging-api/receiving-messages/) 亦寫「We recommend that you process webhook events asynchronously」。
- [A] 若長時間收不到 webhook 回應，「The LINE Platform may suspend sending webhooks to your bot server」。— [Receive messages](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)

**重送（redelivery）與去重**
- [A] Webhook 重送**預設關閉**，須在 console 的 Messaging API 分頁開啟「Use webhook」與「Webhook redelivery」；僅在 bot server 未回 2xx 時重送；「The number and interval of the webhook redelivery aren't disclosed」；「Webhook redelivery doesn't guarantee that webhooks will be reliably delivered」。— [Receive messages](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)
- [A] 重送事件與原事件相同，僅 `deliveryContext.isRedelivery` 不同；`webhookEventId` 與 reply token 不變（reply token 在部分情況下仍可用）；同一事件可能送達多次，「To detect duplicates, use `webhookEventId`」；重送可能打亂順序，應以 `timestamp` 判斷先後。— 同上
- [A] `webhookEventId` 為 ULID 格式的唯一識別；`timestamp` 即使在重送時也代表事件發生時間而非重送時間。— [reference](https://developers.line.biz/en/reference/messaging-api/index.html.md)

**Reply token**
- [A] 「Reply tokens can only be used once.」「Reply tokens must be used within one minute after receiving the webhook. Use beyond one minute isn't guaranteed to work.」— [reference（Send reply message 段）](https://developers.line.biz/en/reference/messaging-api/index.html.md)

**Push 重試與冪等**
- [A] `X-Line-Retry-Key`（UUID）僅支援 push、multicast、narrowcast、broadcast；**reply 不支援**（帶上會回 400）。Retry key 自首次請求起 24 小時有效；409 代表同 key 已被接受，應停止重試（回應含 `x-line-accepted-request-id`）；只在 500 或逾時時重試，2xx/409/4xx 不重試；重試內容與收件人須完全相同；應用指數退避（重試也計入速率限制）；retry key 只防重複發送、不保證送達；回 200 後即使使用者已封鎖也不能再重試。— [LINE Developers, Retry failed API requests](https://developers.line.biz/en/docs/messaging-api/retrying-api-request/)（存取 2026-10-31）

**計費與台灣方案**
- [A] 計入訊息則數：push、multicast、broadcast、narrowcast；**不計入：reply**。該頁未列台灣特別規定，並連結台灣頁面。— [LINE Developers, Messaging API pricing](https://developers.line.biz/en/docs/messaging-api/pricing/)（無日期；存取 2026-10-31）
- [A] 台灣官方帳號頁：不計費訊息類型包括一對一聊天訊息、自動回應訊息、加入好友歡迎訊息、Messaging API Reply API；所有費用未稅；系統以日本時間（GMT+9）計日，台灣時間 23:00 起發送的訊息計入次日；頁面標示「LINE 官方帳號價格方案將於 2026/11/1 起調整」。— [LINE Biz 台灣, LINE 官方帳號](https://tw.linebiz.com/service/account-solutions/line-official-account/)（存取 2026-10-31）
- [A] 調價公告（產品新知 2026/09/01；自 2026/11/1 生效；未稅）：

  | 方案 | 月費 至 2026/10/31 | 月費 2026/11/1 起 | 每月免費訊息 | 加購 |
  |---|---|---|---|---|
  | 輕用量 | NT$0 | NT$0 | 200 則 | 不可加購 |
  | 中用量 | NT$800 | NT$1,000 | 3,000 則 | 不可加購（須升級高用量） |
  | 高用量 | NT$1,200 | NT$1,400 | 6,000 則 | 新制：第 1～50,000 則 0.2 元/則；第 50,001 則起 0.15 元/則（舊制「起始 0.2 元，階梯累進」，舊級距切點公告未列） |

  — [LINE Biz 台灣, LINE 官方帳號 2026 價格方案調整公告](https://tw.linebiz.com/column/LINEOA-2026-Price-Plan/)（存取 2026-10-31）。**報告撰寫時（2026-10-31）正處於新舊制交界，章節應以 2026/11/1 新制為準並註明日期。**
- [E] 搜尋結果中第三方整理文章（如約 2020 年報導之輕用量 500 則、高用量 25,000 則等）已過時，不應引用。— 例如 [INSIDE 報導](https://www.inside.com.tw/article/19061-line-new-fee-brand)

**速率限制**
- [A] 每 channel：Display a loading animation 100 req/s；multicast（及 membership、coupon）200 req/s；get rich menu list 10 req/s；issue short-lived channel access token 370 req/s；「Other API endpoints」2,000 req/s；push 段落明列 2,000 req/s；broadcast/narrowcast 60 req/hour；webhook endpoint 設定 1,000 req/min。API 請求超過 2MB 回 413；超過免費訊息數回 429（「Exceeded the number of free messages」）。— [reference](https://developers.line.biz/en/reference/messaging-api/index.html.md)

**取得內容（Get content）**
- [A] `GET /v2/bot/message/{messageId}/content` 位於 `api-data.line.me` 網域；可取得使用者以 LINE 傳送的圖片／影片／音訊二進位（外部提供者內容不可）；「Content is automatically deleted after a certain period from when the message was sent」；檔案格式由回應的 `Content-Type` 標頭指示；「Content sent by users may be transformed internally, such as shrinking」。— [reference](https://developers.line.biz/en/reference/messaging-api/index.html.md)；overview 亦僅稱一段時間後自動刪除，**未給具體天數**。— [Messaging API overview](https://developers.line.biz/en/docs/messaging-api/overview/)
- 送出圖片訊息的大小限制（originalContentUrl 10 MB、preview 1 MB）僅見於第三方整合文件 [E]，本輪未在官方 reference 擷取段落中核實 → 見 Gaps。

**Loading 動畫**
- [A] 僅限一對一聊天；`loadingSeconds` 可為 5、10、…、60（5 的倍數），預設 20；群組或多人聊天回 400；速率 100 req/s。— [reference](https://developers.line.biz/en/reference/messaging-api/index.html.md)

**封鎖／取消追蹤**
- [A] `unfollow` 事件＝「your LINE Official Account is blocked」，僅一對一聊天，含 `timestamp`、`source`、`webhookEventId`，**沒有 replyToken**；`follow` 事件涵蓋加好友或解除封鎖。— [reference](https://developers.line.biz/en/reference/messaging-api/index.html.md)；[Receive messages](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)

**〔程式碼現況〕對照**
- `verify_signature` 以 HMAC-SHA256＋Base64，並用 `hmac.compare_digest` 常數時間比較；webhook body 串流讀取上限 1 MB（超過回 413）；簽章失敗回 401。
- jobs 表以 `event_id`（webhookEventId）為主鍵去重；另有 `unsent` 表處理「收回訊息」與亂序重送。
- `send()`：收到 webhook 後 <45 秒用 reply，否則改用 push 並帶 `X-Line-Retry-Key`（不自動重試）。
- loading 動畫固定 `loadingSeconds: 60`（合法最大值）。
- 取得內容走 `api-data.line.me`，串流累計超過 `max_image_bytes`（10,485,760 bytes）即中止。

### Inferences
- 本報告推論：現行 45 秒切換門檻比官方「一分鐘」保守 15 秒，合理；`job_timeout_seconds=120` 大於 reply 窗口，因此**逾時或排隊久的案件必然改走 push、消耗則數**。
- 本報告推論（計費）：NOW 低流量下，只要多數照片在 45 秒內回覆，push 幾乎不發生；若使用輕用量（200 則/月、不可加購），FUTURE 1,000 張照片、假設 10% 走 push（假設值）＝約 100 則，若集中在單月仍在額度內；但若 GPU 故障或排隊導致大量 push，超額後 API 回 429，使用者會收不到結果。建議：(1) 監控每月 push 用量（reference 提供 message quota consumption 端點）；(2) push 失敗時於使用者下次互動以 reply 補送；(3) FUTURE 若 push 常態化，評估中用量（2026/11/1 起 NT$1,000/月、3,000 則）。
- 本報告推論：webhook 重送預設關閉；目前若伺服器（家用 Windows）短暫離線，事件會**直接遺失**而非重送。若開啟重送，現有 event_id 去重已可承接。開啟與否應寫入研究操作手冊。
- 本報告推論：`unfollow` 無 reply token，不能回覆；可用來觸發「停止推送／標記使用者已封鎖」，但**封鎖不等於撤回研究同意**——若研究計畫書要將封鎖視為撤回，需倫理委員會確認。
- 本報告推論：LINE 說明使用者內容可能被「內部轉換，例如縮小」——模型實際收到的影像可能已被 LINE 壓縮／縮小，研究資料的解析度與壓縮條件並非手機原檔，屬資料來源偏差，應在方法章節說明。

### Gaps
- webhook 逾時秒數：官方文件未公布 → 未找到可靠證據（第三方常見說法未採用）。
- 重送次數與間隔：官方明言不公開。
- 使用者上傳內容在 LINE 平台的保存天數：官方只說「一段時間」→ 未找到可靠證據。
- 收到圖片的 Content-Type 實際分布（是否一律 JPEG）與最大尺寸：官方 reference 擷取段落未載明 → 未找到可靠證據；建議實測記錄 `Content-Type` 與尺寸。
- 一次 push 含多個訊息物件（文字＋圖片）在台灣如何計則數：本輪未核實（建議查 https://tw.linebiz.com/faq/oa-price/how-to-calculate-message-expense/ ）。
- 官方 reference 頁面約 70 萬字元，本輪僅讀取前 30 萬字元；Image message object 的官方大小限制未擷取到。

## 問題二：威脅模型與實際風險等級（惡意影像、洪水攻擊、資源耗盡、重放、對抗樣本、不當內容、VLM 提示注入）

### Takeaway
對此研究原型而言，**最實際的風險是資源耗盡（洪水上傳、GPU 佇列飽和、push 則數被耗盡）與不當／非目標內容（臉、裸露、無關照片）造成的隱私與資料污染**；解碼炸彈與畸形檔已有 Pillow 機制可擋；webhook 重放有簽章＋event_id 去重可擋；對抗樣本在學術上已證實可行、且醫療模型更脆弱，但在「無金錢誘因、無自動決策、低信心交人工」的研究原型中屬低優先風險。

### Cited Findings

**解碼炸彈與畸形檔**
- [A] Pillow 13.0.0：像素數超過 `MAX_IMAGE_PIXELS` 發出 `DecompressionBombWarning`；超過兩倍則丟出 `DecompressionBombError`；可設為 `None` 停用（不應如此）；`Image.open()` 為 lazy 操作，像素資料在處理或 `load()` 時才讀取。— [Pillow docs, Image module](https://pillow.readthedocs.io/en/stable/reference/Image.html)（存取 2026-10-31）
- [A] 預設值：`MAX_IMAGE_PIXELS = int(1024 * 1024 * 1024 // 4 // 3)`＝89,478,485 像素（約 8,950 萬；錯誤門檻約 1.79 億）。— [Pillow 原始碼 src/PIL/Image.py（main 分支）](https://raw.githubusercontent.com/python-pillow/Pillow/main/src/PIL/Image.py)（數值由該式計算）
- [A]（業界標準）OWASP File Upload Cheat Sheet：使用 allowlist 副檔名；「don't trust the Content-Type header as it can be spoofed」；magic bytes 檢查「should not be used on its own」；影像應「decode and re-encode to an allowed image format, explicitly removing unnecessary metadata」，但「Rewriting does not guarantee that all malicious content is removed」；設定檔案大小上限；ZIP bomb／XML bomb 為威脅；檔案存放於 webroot 之外；以應用程式產生的檔名（UUID）取代原檔名；可用防毒／沙箱；引用 ImageTragick 類解析器漏洞，建議更新函式庫、限制格式、資源限制與沙箱。該頁**未提及 polyglot 檔**。— [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)（存取 2026-10-31）

**資源耗盡**
- [A] OWASP API Security Top 10 2023 — API4 Unrestricted Resource Consumption：滿足請求需要頻寬、CPU、記憶體、儲存；「Exploitation can lead to DoS due to resource starvation, but it can also lead to operational costs increase」；執行逾時、記憶體上限、上傳大小上限等「missing or set inappropriately」即屬脆弱。防範：以容器／行程限制記憶體、CPU、重啟次數、檔案描述元；「Define and enforce a maximum size of data on all incoming parameters and payloads」；「Implement a limit on how often a client can interact with the API within a defined timeframe」；對敏感操作節流；「Configure spending limits for all service providers/API integrations」或設帳單警示。— [OWASP API4:2023](https://api-security.owasp.org/editions/2023/en/0xa4-unrestricted-resource-consumption)（存取 2026-10-31）

**對抗樣本**
- [D；後於 ICLR 2014 發表] Szegedy C, Zaremba W, Sutskever I, Bruna J, Erhan D, Goodfellow I, Fergus R.「Intriguing properties of neural networks」：刻意選擇的微小擾動即可翻轉網路預測，且對抗樣本可在不同資料子集訓練的網路間轉移。— [arXiv:1312.6199](https://arxiv.org/abs/1312.6199)（v4 修訂 2014-02-19）
- [D；後於 ICLR 2015 發表] Goodfellow IJ, Shlens J, Szegedy C.「Explaining and Harnessing Adversarial Examples」：主張高維輸入下的線性性質是脆弱主因，提出 FGSM 快速產生對抗樣本，並顯示對抗訓練具正則化效益。— [arXiv:1412.6572](https://arxiv.org/abs/1412.6572)（v3 修訂 2015-03-20）
- [B] Finlayson SG, Bowers JD, Ito J, Zittrain JL, Beam AL, Kohane IS.「Adversarial attacks on medical machine learning」. *Science* 2019;363(6433):1287–1289. doi:10.1126/science.aaw4399（PMID 30898923）——評論醫療 AI 對對抗操縱的易感性，並建議監管機關評估機器學習醫材對此類攻擊的韌性。— [PubMed](https://pubmed.ncbi.nlm.nih.gov/30898923/)；[AHRQ PSNet 摘要](https://psnet.ahrq.gov/issue/adversarial-attacks-medical-machine-learning)
- [C/B] Ma X, Niu Y, Gu L, Wang Y, Zhao Y, Bailey J, Lu F.「Understanding adversarial attacks on deep learning based medical image analysis systems」. *Pattern Recognition* 2021;110:107332. doi:10.1016/j.patcog.2020.107332 ——醫療影像 DNN 比自然影像模型更易受攻擊（反證面）；但這些攻擊可被簡單偵測器以 >98% detection AUC 偵測，作者歸因於擾動擴散到病灶區域以外。— [arXiv:1907.10456](https://arxiv.org/abs/1907.10456)（本輪僅取得摘要層級資訊）

**不當內容、VLM 提示注入**
- 本輪未找到針對「上傳臉部／裸露照片至醫療研究 LINE 帳號」的可靠研究或官方指引 → 未找到可靠證據。
- VLM 提示注入（影像中夾帶文字指令）：本輪未核實相關官方標準頁面 → 未找到可靠證據（OWASP 另有 LLM Top 10，本輪未存取驗證，不引用）。

**〔程式碼現況〕已具備的防護**
- `engine.py` 以 `warnings.simplefilter("error", Image.DecompressionBombWarning)` 將警告升為錯誤；`configs/service.json` 自訂 `max_image_pixels: 25000000`（2,500 萬像素，嚴於 Pillow 預設 8,950 萬）、`max_image_bytes: 10485760`、`allowed_formats: JPEG/PNG/WEBP`、最短邊 <64 拒收；`ImageOps.exif_transpose(...).convert("RGB")`；結果圖以 `plot()` 重新編碼（程式註解：strips original EXIF and never persists the raw image）。
- 每位使用者同時只能有一件 queued/running（`reserve()` 回 `busy`）；全域 `asyncio.Queue(maxsize=queue_size)`，預設 4，滿了以 reply 回「佇列已滿」。
- 結果圖 URL 使用 `secrets.token_urlsafe(32)`（43 字元），TTL 預設 3600 秒，`Cache-Control: private, no-store`、`X-Content-Type-Options: nosniff`；FastAPI 關閉 docs/openapi。
- 外部匯入工具（`src/imports/external.py`）已有 EXIF 校正後的精確像素雜湊與 64-bit difference hash（dHash）近重複偵測；LINE 路徑未見使用。
- 未見每使用者每日／每小時配額。

### Inferences
- 本報告推論（風險排序）：
  1. **高**：洪水／重複上傳 → GPU 佇列飽和、push 額度耗盡（API4 的「DoS＋成本」雙面向）。現有「每人一件＋全域佇列 4」擋住單人並發，但**沒有每日配額**，單一帳號可在上一張完成後立刻再傳。多帳號洪水則無法以 user 層級完全阻擋，只能靠全域佇列上限與封鎖清單。
  2. **高（隱私）**：非目標內容（臉、身體其他部位、證件、病歷文字、裸露）——公開帳號無法控制使用者傳什麼；同意後若照片被保存為研究資料，就形成敏感個資。比對抗樣本更可能發生。
  3. **中**：畸形檔／解碼炸彈——LINE 先處理（可能縮小）圖片，加上 Pillow 機制與 25 MP 上限，實際風險已大幅降低；殘餘風險在 Pillow／libjpeg／libwebp 解析器漏洞 → 保持套件更新。
  4. **低**：webhook 重放——無 channel secret 無法偽造簽章；重放合法請求被 event_id 去重攔下。殘餘風險：channel secret 外洩（`.env` 管理）；簽章不含時間戳，jobs 記錄於 86400 秒後清除（非進行中工作），之後重放舊請求理論上可再被接受 → 可加「`timestamp` 早於 N 分鐘即丟棄」。
  5. **低**：對抗樣本——研究證據顯示可行且醫療模型更脆弱（Ma 2021），Finlayson 2019 的論述著重於監管與有誘因的醫療情境；本原型不做臨床診斷、無給付或決策後果、低信心交人工，攻擊者缺乏誘因。且 Ma 2021 顯示這類擾動可被簡單偵測。較實際的「對抗」型態是**資料污染**：若未來把 LINE 照片納入訓練，惡意或錯誤照片會污染資料——由「不自動訓練、人工確認標註」原則擋住。
  6. **情境性**：VLM 提示注入——目前無 VLM，不適用；若將來導入 VLM，影像內嵌文字可能左右輸出，必須維持「模型輸出不直接作為對使用者的醫療建議」並人工審查。
- 本報告推論：polyglot 檔在本架構風險低，因為 (a) 不以原檔提供下載，(b) 只把解碼後像素送入模型，(c) 結果圖重新編碼。若未來保存原始上傳檔，應保存重新編碼版或存放於非 web 目錄並以 UUID 命名（OWASP）。

### Gaps
- 醫療影像對抗攻擊在「手機拍攝、經 LINE 壓縮」條件下的成功率：未找到可靠證據。
- 不當內容（裸露／臉部）自動偵測模型在地端部署的準確度：本輪未研究 → 未找到可靠證據。
- Ma et al. 2021 期刊版全文實驗細節未讀取。

## 問題三：防護措施的實作建議、適用條件、效益與風險（NOW vs FUTURE），含「不上傳第三方雲端」原則的釐清

### Takeaway
NOW 階段最該補的是**每位使用者每日配額**、**LINE 路徑重用既有 dHash 做「同一張重傳」偵測**、**以測試證明同意閘門在下載之前**，以及**把「不上傳第三方雲端」原則改寫為可稽核的精確定義**（照片必經 LINE 平台；結果圖由 LINE 抓取；若用 Cloudflare Tunnel，代理商在 TLS 終止點可見 webhook 與結果圖）。其餘（尺寸／像素上限、重新編碼、去 EXIF、有界佇列與忙碌回覆、event_id 冪等）程式碼已具備，只需寫入測試與文件。

### Cited Findings
- [A] 限制上傳大小、對客戶端呼叫頻率設限、設支出上限或帳單警示。— [OWASP API4:2023](https://api-security.owasp.org/editions/2023/en/0xa4-unrestricted-resource-consumption)
- [A] 影像重新編碼並移除不必要 metadata；不信任 Content-Type；UUID 命名；存於 webroot 外。— [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
- [A] 以 `webhookEventId` 去重；以 `timestamp` 判斷順序。— [LINE Receive messages](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)
- [E] imagehash（BSD-2-Clause）：支援 average、perceptual（pHash）、difference（dHash）、wavelet、HSV color、crop-resistant hashing；兩雜湊相減即 Hamming 距離，以 `hash1 - hash2 < threshold` 判斷相似；aHash/pHash/dHash/wHash 只看亮度、忽略色彩；hash size 影響敏感度，需依資料調整門檻；4.0 版改變 hex 編碼，舊雜湊不相容（提供 `old_hex_to_hash`）；pHash 需 scipy。— [JohannesBuchner/imagehash](https://github.com/JohannesBuchner/imagehash)（存取 2026-10-31）
- [A] Cloudflare Tunnel：`cloudflared` 建立「outbound-only connections to Cloudflare's global network」，原站不需要 inbound listener，建議防火牆封鎖所有 inbound。— [Cloudflare docs, Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/)（Last updated 2026-08-04）
- [A] Cloudflare 加密模式描述兩段獨立連線：「one between your visitors and Cloudflare, and the other between Cloudflare and your origin server」（Flexible／Off 模式下對原站甚至不加密）。— [Cloudflare docs, SSL/TLS encryption modes](https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/)（Last updated 2026-04-16）
- [A] 取得內容走 `api-data.line.me`（本機主動向 LINE 拉取）；使用者內容保存於 LINE 平台一段時間後自動刪除。— [reference](https://developers.line.biz/en/reference/messaging-api/index.html.md)

**防護措施逐項整理**

| 措施 | 支持依據 | 反證／失效情況 | 適用 | 不適用 | 預期效益 | 接入方式（本專案） | 風險 |
|---|---|---|---|---|---|---|---|
| 每人速率限制（token bucket）＋每日配額 | OWASP API4 [A] | 換 LINE 帳號即可繞過；配額過低傷害正常參與者 | NOW/FUTURE | — | 擋單帳號洪水、保護 push 額度 | 在 `Store.reserve()` 增加「`user_key` 近 24 小時件數 ≤ N」檢查，超過以 reply（免費）告知；`user_key` 已是 HMAC 雜湊，不存原 userId | N 須依研究流程訂定並寫入計畫書 |
| 近重複偵測（dHash/pHash） | imagehash [E]；專案已有 dHash | 只看亮度；裁切／旋轉／不同角度不會判為重複；**同一病人每日追蹤照本就相似 → 誤判風險** | 偵測「同一張重傳」 | 不可用來判定同一病人或拒收追蹤照 | 減少重複 GPU 運算與重複入庫 | 重用 `src/imports/external.py` 的 dHash；僅對同一 `user_key`、短時間內、Hamming 距離≈0 時回覆「已收過」 | 門檻過寬會拒收合法照片；只作提示與統計，不作研究排除依據 |
| 下載前大小上限、解碼前像素上限 | Pillow [A]、OWASP [A] | LINE 已縮圖，攻擊面小 | 皆適用 | — | 防記憶體耗盡 | 已有（10 MB 串流、25 MP、Bomb warning→error） | 無 |
| 重新編碼、去 EXIF/GPS | OWASP [A] | 「Rewriting does not guarantee…」 | 皆適用 | — | 隱私（GPS）、去除夾帶內容 | 結果圖已重編碼；資料集端已有 `exif_transpose_rgb_jpeg95` 正規化；**若保存研究原圖，也應保存重編碼版** | 重編碼改變 JPEG 量化，訓練／推論前處理須一致 |
| event_id 冪等＋timestamp 檢查 | LINE 官方 [A] | event 記錄清除後可再重放 | 皆適用 | — | 防重複處理與重放 | 已有 event_id；建議加 timestamp 上限 | 若開啟重送且長時間離線，恢復後舊事件可能被誤丟（需權衡 N） |
| 有界佇列＋忙碌回覆 | OWASP API4 [A] | 佇列太小於尖峰時拒絕過多 | 皆適用 | — | GPU 不被淹沒；忙碌回覆用 reply（免費） | 已有（queue_size 預設 4，可設 1..20） | 使用者需自行重傳 |
| 同意閘門在下載之前 | 專案原則 | — | 皆適用 | — | 未同意者照片不進入本機 | 以測試證明 `Conversation.handle()` 未同意時不產生 `Enqueue`、`LineClient.image` 不被呼叫（本輪未逐行核對） | 若先下載後判斷即違反原則 |
| 日誌與封鎖清單 | OWASP API4 [A] | 日誌本身可能含個資 | 皆適用 | — | 事後追查、封鎖濫用者 | 只記 `user_key`、event_id、狀態、錯誤型別（`safe_send` 已不記 token/userId/內容） | 封鎖清單須有解除與申訴流程 |
| 不當內容處理 | 未找到可靠證據 | — | — | — | — | NOW：偵測器無候選框即回「未偵測到」且不保存；人工審查發現即刪除並記錄 | 自動 NSFW／人臉模型會增加 VRAM 與誤判，且本身需驗證 |

### Inferences
- 本報告推論（「研究照片不上傳第三方雲端」原則的衝突，**必須在報告中明確標示**）：
  1. 使用者照片**必然**先上傳到 LINE（LY Corporation）平台，並保存「一段時間」（官方未公布）後由本機從 `api-data.line.me` 拉取。這是使用 LINE 的固有條件，不是研究方主動上傳，但應在同意書揭露。
  2. 本機回覆的**結果圖**（照片衍生物，含標註框）以 `PUBLIC_BASE_URL/results/{token}.jpg` 公開 HTTPS 網址提供，由 LINE 平台抓取後轉送使用者——研究照片衍生影像會離開本機並存於 LINE 平台。若要更嚴格，可只回文字結果、不回結果圖（取捨：使用者體驗下降）。
  3. 若以 Cloudflare Tunnel（或 ngrok）對外暴露家用 Windows 機器，依 Cloudflare 文件的兩段連線架構，代理商在其邊緣處理 TLS，**技術上可見 webhook JSON（含 userId、訊息 ID）與結果圖**。原始照片下載方向是本機主動連到 `api-data.line.me`，不經 tunnel。
  4. 建議把原則改寫為：「研究方不將研究照片或其衍生物主動存放於第三方雲端儲存或第三方 AI 服務；必要的傳輸中繼（LINE 平台、TLS 代理）列為已知資料流並於同意書與資料流程圖揭露」。這需研究團隊／IRB 決定，非技術單方可解。
- 本報告推論（暴露方式）：(a) Cloudflare Tunnel：不開 inbound port、隱藏家用 IP，但 TLS 在 Cloudflare 終止；(b) 路由器 port forwarding＋自有網域與憑證：TLS 在本機終止、無中間代理，但暴露家用 IP、需自行維護憑證與防火牆；(c) ngrok：本輪未查證官方文件 → 不作具體陳述。NOW 階段 (a) 營運負擔最低；任一方案皆應寫入資料流程圖。管理介面維持只綁 localhost、不經 tunnel 暴露。
- 本報告推論（NOW vs FUTURE）：
  - NOW：新增「每日配額」與「timestamp 過舊丟棄」即可，成本極低；近重複偵測僅作統計提示；不需要 WAF、Redis 或 Celery。
  - FUTURE：增加 (1) 每月 push 用量監控與警示（對應 OWASP「spending limits／billing alerts」）；(2) 封鎖清單與管理操作紀錄；(3) 不當內容處置 SOP；(4) Pillow 等解析器定期更新；(5) 若使用者多、出現多帳號濫用，再評估 tunnel 層的速率限制（屬第三方功能，須重新檢視資料流原則）。

### Gaps
- `Conversation.handle()` 是否在未同意時完全不下載照片：本輪未逐行驗證。
- ngrok 的 TLS 終止與資料保存政策：未查證 → 未找到可靠證據。
- 每日配額合理數值：無外部證據，應依研究計畫（每位病人每日拍攝次數）訂定。

## 問題四：推論效能——官方速度表、FP16／INT8、ONNX／TensorRT、torch.compile，以及「低流量下是否需要優化」

### Takeaway
官方數據顯示 YOLO11n/s 與 YOLO26n/s 在 T4 TensorRT10 上單張約 1.5–2.5 ms、CPU ONNX 約 39–90 ms；EfficientNet-B0（0.39 GFLOPS）與 DINOv2-small（21 M 參數）也很小。**NOW 與 FUTURE 流量下 GPU 運算都不太可能是瓶頸，LINE 下載／回覆網路與排隊才是**；因此先量測、不急著量化。INT8 PTQ 官方建議至少 500 張校正影像，本專案只有約 120 張，且醫療影像研究顯示 INT8 PTQ 可能造成依架構而異的鑑別力下降與校準偏移 → **NOW 不建議 INT8**；FP16 研究證據顯示接近 FP32，但必須重新驗證信心門檻。

### Cited Findings

**官方速度表（COCO、640 px）**
- [A] YOLO26（頁面建立 2025-09-25，標示「Updated 1 week ago」，無確切日期）：

  | 模型 | mAP50-95 | mAP50-95 (e2e) | CPU ONNX (ms) | T4 TensorRT10 (ms) | Params (M) | FLOPs (B) |
  |---|---|---|---|---|---|---|
  | YOLO26n | 40.9 | 40.1 | 38.9 ± 0.7 | 1.7 ± 0.0 | 2.4 | 5.5 |
  | YOLO26s | 48.6 | 47.8 | 87.2 ± 0.9 | 2.5 ± 0.0 | 9.5 | 20.9 |

  速度以 NMS-free head（`nms=False`）量測；Params/FLOPs 為 fused model；宣稱 YOLO26n 相較 YOLO11n 在 Intel Xeon @2.00 GHz「up to 43% faster CPU ONNX inference」；移除 DFL。— [Ultralytics YOLO26](https://docs.ultralytics.com/models/yolo26/)（存取 2026-10-31）
- [A] YOLO11（頁面建立 2024-09-30）：YOLO11n 39.5 mAP、CPU ONNX 56.1 ± 0.8 ms、T4 TRT10 1.5 ± 0.0 ms、2.6 M、6.5 B；YOLO11s 47.0、90.0 ± 1.2 ms、2.5 ± 0.0 ms、9.4 M、21.6 B。頁面**未說明**批次大小與完整硬體條件。— [Ultralytics YOLO11](https://docs.ultralytics.com/models/yolo11/)
- [A] torchvision EfficientNet-B0（IMAGENET1K_V1）：5,288,548 參數、0.39 GFLOPS、ImageNet acc@1 77.692、檔案 20.5 MB、resize 256（bicubic）→ center crop 224；官方頁未提供延遲數字。— [torchvision efficientnet_b0](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.efficientnet_b0.html)
- [A/E] DINOv2 ViT-S/14 distilled：21 M 參數、ImageNet k-NN 79.0%、linear 81.1%；程式碼與權重 Apache 2.0；README 未提供延遲數字。— [facebookresearch/dinov2](https://github.com/facebookresearch/dinov2)

**匯出與量化（Ultralytics）**
- [A] 匯出頁（建立 2023-11-12，「Updated 1 day ago」）：格式含 ONNX、TensorRT `engine`、OpenVINO 等；**`half` 與 `int8` 已被 `quantize` 取代**（`half=True`→`quantize=16`、`int8=True`→`quantize=8`，舊參數仍可用但有棄用警告）；INT8 校正以 `data=`（dataset YAML）、`fraction`（預設 1.0）、`split`（預設 'val'）指定；以 QAT 訓練的模型不需校正資料；宣稱「up to 5x GPU speedup with TensorRT and 3x CPU speedup with ONNX or OpenVINO」（無測試條件）；INT8「with minimal accuracy loss」（無數字）。— [Ultralytics Export mode](https://docs.ultralytics.com/modes/export/)
- [A] 同頁 QAT 表（COCO val2017、TensorRT 10.16、640、batch 1，mAP50-95）：yolo26n FP32 0.4032／PTQ INT8 0.3934／QAT INT8 0.3935；yolo26s 0.4794／0.4412／0.4711；yolo26m 0.5269／0.4696／0.5137。官方說 PTQ 在 yolo26n 損失 0.010，較大模型損失 0.038–0.057，並提醒其他資料集、格式或 TensorRT 版本結果會不同。— 同上
- [A] TensorRT 整合頁：建議「at least 500 calibration images that are representative of the data」（引述 NVIDIA 實驗，屬指引）；GPU 匯出用 `MINMAX_CALIBRATION`；校正 batch 太小可能造成 INT8 縮放不準；精度降低時 mAP、Precision、Recall「likely to be somewhat worse」；Sigmoid 層保持較高精度，但 INT8 仍可能改變信心值；「TensorRT engines are hardware- and runtime-specific」，應在部署的同一裝置上匯出。— [Ultralytics TensorRT integration](https://docs.ultralytics.com/integrations/tensorrt/)
- [A] 同頁 yolov8n 640 基準：
  - 消費級 GPU（Windows 10.0.19045、ultralytics 8.2.4、TensorRT 10.0.0b6；FAQ 歸屬 RTX 3080）：FP32 1.06 ms、FP16 0.62 ms、INT8 0.52 ms；mAP50-95 0.37／0.37／0.33。
  - A100（TensorRT 8.6.1）：0.52／0.34／0.28 ms；mAP50-95 0.37／0.37／0.33。
  - Jetson Orin NX：6.11／3.18／2.30 ms；0.37／0.37／0.32。
  — 同上（頁面列出 RTX 3080/3060/2060，但擷取內容未逐列標示 GPU，僅能確定上述一組）。

**醫療影像量化研究**
- [C/B]（CHIL 2026 會議論文）Ozdemir OB, Li R.「Bridging the Reliability Gap: INT8 Quantization Effects on Discrimination and Calibration in Medical Imaging」. PMLR 333:952–965：三個公開醫療資料集（BrainMRI、ChestXray、SkinCancer）、八種 ImageNet 預訓練 backbone；**FP16 與 FP32 高度一致**；**INT8 PTQ 可能造成大幅、依架構而異的鑑別力下降與校準偏移**；INT8 QAT 大致恢復浮點行為；主張同時評估準確度、校準（ECE、Brier）與效率。— [PMLR](https://proceedings.mlr.press/v333/ozdemir26a.html)（僅讀摘要）
- [D] Qu C, Zhao R, Yu Y, et al.（2025）「Post-Training Quantization for 3D Medical Image Segmentation: A Practical Study on Real Inference Engines」：8 個 3D 分割模型於 GPU（TensorRT）實作 8-bit 量化，宣稱減少大小與延遲且「without sacrificing model performance」；摘要無數字（反證／對照：與 Ozdemir 的負面結果並存，差異可能來自任務與架構）。— [arXiv:2501.17343](https://arxiv.org/abs/2501.17343)

**Windows 執行環境**
- [A] NVIDIA TensorRT 安裝指南（Last updated 2026-10-28，TensorRT 11.4.1）：提供 Windows x64 與 Arm64 zip 套件；zip 安裝需手動設定 PATH；pip wheel 不含 `trtexec`。— [NVIDIA TensorRT Installation Guide](https://docs.nvidia.com/deeplearning/tensorrt/latest/installing-tensorrt/installing.html)
- [A] ONNX Runtime TensorRT EP：自 ORT 1.22 起只發布 CUDA 12 GPU 套件；有 TensorRT／CUDA 版本對照表；`trt_engine_cache_enable` 可快取引擎（模型、ORT、TensorRT 版本或硬體變更時須清除）；`trt_fp16_enable`、`trt_int8_enable`（並非所有 NVIDIA GPU 支援 INT8）；建議同時註冊 CUDA EP 讓不支援節點回退；首次建立引擎因窮舉 profiling 可能很久（文件中 Stable Diffusion UNet：無快取 384 秒、有快取 9 秒）。頁面未明列支援作業系統。— [ONNX Runtime TensorRT EP](https://onnxruntime.ai/docs/execution-providers/TensorRT-ExecutionProvider.html)
- [A] PyTorch 官方教學「How to use torch.compile on Windows CPU/XPU」：Windows CPU 上 Inductor 需 PyTorch ≥2.5、XPU ≥2.7，需要 C++ 編譯器（範例 MSVC）。— [PyTorch tutorial: inductor_windows](https://docs.pytorch.org/tutorials/prototype/inductor_windows.html)（經搜尋摘要取得）
- [E] 論壇：Windows 上 GPU Inductor 依賴 Triton，官方支援不明；PyTorch 2.9.1 使用者回報 AOTInductor 在 Windows 因 Triton 依賴不支援。— [PyTorch Forums: Windows support timeline for torch.compile](https://discuss.pytorch.org/t/windows-support-timeline-for-torch-compile/182268)；[PyTorch Forums: AOTInductor on Windows](https://discuss.pytorch.org/t/aotinductor-on-windows/224382)

### Inferences
- 本報告推論（是否需要優化）：以官方 T4 TensorRT 1.5–2.5 ms 或 CPU ONNX 39–90 ms 量級來看，即使本機以 PyTorch FP32、不用 TensorRT，偵測＋EfficientNet-B0＋DINOv2-small＋品質檢查＋結果圖繪製的單張 GPU 段落**很可能**在數十到數百毫秒（推估，**未經本機量測，不得當作數據引用**）。使用者感受的總時間包含手機上傳到 LINE → webhook → 本機向 `api-data.line.me` 下載 → 推論 → 回覆 → LINE 推送；GPU 運算不太可能是主要延遲。結論：**先量測再決定**。
- 本報告推論（量測方法）：在 `work()` 內以 `time.perf_counter()` 分段記錄：webhook 收到→出佇列（排隊）、下載、解碼與品質檢查、偵測、分類器、DINOv2、繪圖編碼、LINE 回覆 API 往返；GPU 段落前後 `torch.cuda.synchronize()`；排除暖機首次；報 p50/p95 而非平均；同時記錄實際解析度（LINE 可能已縮圖）與 reply/push 比例。
- 本報告推論（容量）：若 GPU 段落約 100 ms（假設值），單一 worker 每小時可處理上萬張；FUTURE 1,000 張分散於整個研究期間，平均流量極低。真正容量風險是**尖峰同時到達**（例如集中上傳），由有界佇列處理。
- 本報告推論（量化適用性）：
  - **INT8 PTQ — NOW 不適用**：(1) 官方建議 ≥500 張代表性校正影像，本專案約 120 張；(2) 若用同一批照片校正又評估，等於資料洩漏；(3) Ozdemir & Li 2026 顯示 INT8 PTQ 可能造成依架構而異的鑑別力與校準偏移，而本系統依賴「候選門檻、低信心→人工審查」，**校準偏移會直接改變哪些照片被送去人工審查**；Ultralytics 也明言 INT8 可能改變信心值；(4) Ultralytics 自己的 COCO 數據 YOLO26s PTQ 損失 0.038 mAP。
  - **INT8 — FUTURE 仍需謹慎**：即使有 1,000 張，也應另留不與測試集重疊的校正子集，並同時報 AUC／敏感度／ECE；QAT 涉及重新訓練，須遵守「不自動訓練／部署、人工確認」原則。
  - **FP16 — 可選但非必要**：研究證據（Ozdemir & Li）與官方 yolov8n 數據（mAP 不變）顯示 FP16 接近 FP32；仍須在本專案驗證集上確認門檻判定不變。低流量下效益小。
  - **TensorRT engine**：與 GPU、TensorRT／CUDA 版本綁定，換顯卡或升級驅動須重建，首次建置耗時。對單機研究原型而言，維護成本可能高於效益；若使用，僅對偵測器使用，並把 engine 與建置環境版本一併記錄。
  - **ONNX Runtime**：主要價值在「GPU 不可用時的 CPU 後備」（官方 CPU ONNX 39–90 ms 量級顯示 CPU 推論可行）。
  - **torch.compile（Windows）**：GPU 路徑依賴 Triton，Windows 支援不明確 → NOW/FUTURE 都不建議作為依賴。
  - **channels_last、AMP autocast**：本輪未取得針對這些模型的官方加速數據 → 不提供數字；若嘗試，同樣須重新驗證門檻。
- 本報告推論（版本差異）：官方文件已將 `half`/`int8` 改為 `quantize`，專案使用 Ultralytics 8.4；實作前以已安裝版本的匯出說明確認參數名，並在實驗紀錄寫明版本。
- 本報告推論（VRAM 預算）：以參數數 ×4 bytes（FP32）粗估權重：YOLO11s／YOLO26s 約 38 MB、EfficientNet-B0 約 21 MB（與官方 20.5 MB 檔案一致）、DINOv2-small 約 84 MB。主要 VRAM 開銷來自 CUDA context、cuDNN workspace、PyTorch 快取配置器與中間激活值，而非權重；三到四個模型同時常駐於一般消費級 GPU 應可行。**實際數字須以 `torch.cuda.max_memory_allocated()` 與 `nvidia-smi` 量測**（未找到可靠的跨環境通用數據）。

### Gaps
- 本機 GPU 型號與實測延遲：未知，需實測。
- EfficientNet-B0、DINOv2-small 在消費級 GPU 的官方延遲：未找到可靠證據。
- Ozdemir & Li 2026 各 backbone（是否含 EfficientNet-B0）的具體 AUC／ECE 變化：僅讀到摘要。
- Ultralytics 速度表量測條件（batch、是否含前後處理）：官方頁面未說明。
- 針對「小型醫療照片分類器／偵測器」的 INT8 研究：未找到分類任務專門的可靠數字。
- channels_last／AMP 對這些模型的加速：未找到可靠證據。

## 問題五：併發 LINE 照片的佇列設計（立即回 200、背景 worker、reply 過期改 push、影子模型優先順序、VRAM、暖機、健康檢查、GPU 不可用時的降級）

### Takeaway
LINE 官方建議 webhook 回 200 並非同步處理；FastAPI 官方說明 BackgroundTasks 適合輕量工作，重型計算可用 Celery 等，但後者需要 Redis/RabbitMQ。對單機 Windows 研究原型，**現有設計（驗簽→SQLite jobs 表→有界 asyncio.Queue→單一 GPU worker→45 秒內 reply 否則 push）已是合適架構**，不建議引入 Celery/Redis。主要待改：**影子模型目前在同一 worker 內、回覆後同步執行，會擋住下一張照片**，應改為低優先、可丟棄的獨立佇列；並補上 GPU 不可用時的降級與 push 額度保護。

### Cited Findings
- [A] LINE：收到 POST 後必須回 200；建議非同步處理。— [reference](https://developers.line.biz/en/reference/messaging-api/index.html.md)；[Receive messages](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)
- [A] LINE：reply token 單次使用、一分鐘內使用才有保證。— [reference](https://developers.line.biz/en/reference/messaging-api/index.html.md)
- [A] LINE：push 計入訊息則數、reply 不計；台灣輕用量 200 則／月不可加購。— [Messaging API pricing](https://developers.line.biz/en/docs/messaging-api/pricing/)；[LINE Biz 台灣調價公告](https://tw.linebiz.com/column/LINEOA-2026-Price-Plan/)
- [A] LINE：loading 動畫 5–60 秒、一對一、100 req/s。— [reference](https://developers.line.biz/en/reference/messaging-api/index.html.md)
- [A] LINE：push 重試只在 500／逾時、相同 retry key、24 小時內、指數退避。— [Retry failed API requests](https://developers.line.biz/en/docs/messaging-api/retrying-api-request/)
- [A] FastAPI：BackgroundTasks「run *after* returning a response」；可為 `async def` 或 `def`；「If you need to perform heavy background computation and you don't necessarily need it to be run by the same process … you might benefit from using other bigger tools like Celery」，此類工具需要「a message/job queue manager, like RabbitMQ or Redis」。— [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)（存取 2026-10-31）
- [A] ORT TensorRT EP：首次引擎建置（暖機）可能很久；建議註冊 CUDA EP 回退。— [ONNX Runtime TensorRT EP](https://onnxruntime.ai/docs/execution-providers/TensorRT-ExecutionProvider.html)
- [A] OWASP API4：缺少執行逾時、記憶體上限、資源上限即構成弱點。— [OWASP API4:2023](https://api-security.owasp.org/editions/2023/en/0xa4-unrestricted-resource-consumption)

**〔程式碼現況〕佇列設計**
- `webhook()`：串流讀 body（≤1 MB）→ 驗簽 → 解析 → `Conversation.handle()`（去重、busy、收回、同意、撤回）→ `Enqueue` 時 `queue.put_nowait()`；`QueueFull` 時以 reply 回「佇列已滿」→ 立即回 `{"ok": True}`（200）。
- 單一 `work()` 協程：出佇列 → 檢查是否已收回 → loading 動畫（60 秒）→ 下載（10 MB 上限）→ `asyncio.to_thread(predictor.predict)`，以 `wait_for(shield(...), timeout=120)` 限時；逾時回「分析逾時」，但**保留 worker 槽位直到 GPU 執行緒結束**（程式註解：無法強制終止執行緒）→ 寫結果圖 → `send()`（<45 秒 reply，否則 push＋retry key）→ **之後在同一 worker 以 `asyncio.to_thread(shadow_mode.run, ...)` 同步執行影子模型**。
- 啟動時把殘留 queued/running 標記為 interrupted；`line-control.json` 的 `drain`：停止接單、等佇列清空、釋放模型並 `torch.cuda.empty_cache()`；`/health` 回報 ready/draining、模型家族、demo_only、佇列長度；`OperationLock` 讓 LINE 服務與其他 GPU 作業（如訓練）互斥。

### Inferences
- 本報告推論（文字序列圖；✓＝現況已具備，＋＝建議新增）：

```
使用者手機      LINE Platform              本機 FastAPI /webhook           SQLite jobs        GPU worker（主）               Shadow worker（低優先）
   | 傳照片        |                            |                              |                  |                              |
   |-------------->| POST /webhook（附簽章）      |                              |                  |                              |
   |               |--------------------------->| ✓ 驗 x-line-signature         |                  |                              |
   |               |                            | ✓ body ≤1MB、JSON 解析        |                  |                              |
   |               |                            | ✓ event_id 去重 ------------->| INSERT(PK)       |                              |
   |               |                            | ＋ timestamp 過舊即丟棄         |                  |                              |
   |               |                            | ✓ 同意檢查（未同意→不下載，只 reply 同意說明）     |                              |
   |               |                            | ＋ 每人每日配額                 |                  |                              |
   |               |                            | ✓ 每人一件；佇列滿→reply「忙碌」（免費）          |                              |
   |               |<---------- 200 OK ---------| ✓ put_nowait 後立即回 200      |                  |                              |
   |               |<-- POST loading/start (60s) ---------------------------------------------------- | ✓                            |
   |               |<-- GET api-data.line.me/v2/bot/message/{id}/content ---------------------------- | ✓ 串流 ≤10MB                 |
   |               |                            |                              |                  | ✓ 格式白名單、≤25MP、Bomb→錯誤 |
   |               |                            |                              |                  | ✓ 品質檢查→偵測→分類／DINOv2  |
   |               |                            |                              |                  | ✓ 120s 逾時                  |
   |               |                            |                              |<- UPDATE done ---|                              |
   |               |<-- reply（<45s，免費）或 push（≥45s，計則數，X-Line-Retry-Key）------------------ | ✓                            |
   |<- 結果訊息 ---|                            |                              |                  |                              |
   |               |-- GET /results/{token}.jpg（LINE 抓結果圖，經 tunnel）→ ✓ TTL、no-store          |                              |
   |               |                            |                              |                  |-- ＋ put_nowait（有界、可丟棄）->|
   |               |                            |                              |                  |                              | ＋ 主佇列空時才執行；共用 GPU 鎖
   |               |                            |                              |                  |                              | ✓ 只寫比較紀錄，不回覆使用者
```

- 本報告推論（影子模型）：現況影子模型在主 worker 內、回覆之後同步執行——不延遲「這一張」的回覆，但**會延遲下一位使用者**，FUTURE 尖峰時會把更多案件推過 45 秒門檻而改走 push（計費）。建議：第二個有界 `asyncio.Queue`（例如 maxsize 8–16），主 worker 回覆後只 `put_nowait`，滿了丟棄並記錄 `shadow_skipped`；影子 worker 執行前檢查主佇列是否為空；兩者以一把 GPU 鎖序列化並讓主工作優先（兩執行緒同時跑 CUDA 會互相拖慢）。影子結果缺漏須在比較分析中報告（被丟棄者多為尖峰時段照片，可能造成選擇偏差）。NOW 低流量下現況可接受，可列為 FUTURE 改善項。
- 本報告推論（reply→push 成本控制）：(1) 佇列滿已用 reply 回「忙碌」（免費）；(2) 預估等待 >45 秒時，可先以 reply 回「已收到，完成後通知」，結果再 push（每張 1 則）；或不 push，請使用者稍後點 rich menu「查詢結果」以新的 reply token 取得（**免費但多一步**）——在輕用量方案下較能避開 200 則上限，建議作為 FUTURE 備案；(3) 本月 push 計數達額度 80% 時停止 push、改為「查詢結果」模式。
- 本報告推論（佇列技術選擇）：
  - NOW/FUTURE：維持「SQLite jobs 表（持久狀態、去重）＋ asyncio.Queue（記憶體排程）＋單一 GPU worker」。單機單 GPU 單程序下最簡單，且狀態已持久化。
  - FastAPI BackgroundTasks：可行但無界、無優先權、難以限流；官方也指出重型計算可考慮其他工具 → 不如現有有界佇列。
  - Celery/RQ＋Redis、arq（需 Redis）、Huey：多程序、多機時才有價值；Windows 上 Redis 與 Celery 的官方支援狀況本輪未查證。對本專案屬過度設計，並增加一個需維護的服務。
  - 批次化：低流量下等待湊批只會增加延遲 → 不建議；FUTURE 若量測顯示尖峰明顯，可評估「最多等 50 ms、最多 4 張」的微批次。
- 本報告推論（暖機、健康檢查、降級）：
  - 暖機：啟動時對每個模型跑一次假影像推論，避免第一位使用者承擔初始化延遲；若用 TensorRT／ORT-TRT，engine 須在上線前建置並快取（官方指出首次建置可達數分鐘）。
  - 健康檢查：`/health` 可加入 `torch.cuda.is_available()`、上次成功推論時間、本月 push 計數；`/health` 若經 tunnel 對外公開，應考慮只回 ready/not-ready，詳細資訊改只在 localhost 管理介面顯示。
  - GPU 不可用（驅動錯誤、`OperationLock` 被訓練占用等）：選項 A——CPU 後備（官方 CPU ONNX YOLO 39–90 ms 量級顯示可行，但分類器＋DINOv2 在 CPU 會再增加時間，且須驗證 CPU 與 GPU 輸出一致）；選項 B——以 reply 回「服務暫停，請稍後再傳」並停止接單（drain 已具備）。**NOW 建議選項 B**（簡單、不引入未驗證的第二條推論路徑）；FUTURE 若需高可用再評估 A，且 CPU 路徑輸出須標示並納入驗證。
  - 逾時：保留「逾時後仍等 GPU 執行緒結束才釋放槽位」的設計，避免 GPU 上堆積殭屍推論；逾時分支 `continue` 不再送第二則結果，符合預期。
- 本報告推論（VRAM 與多模型）：主模型＋影子模型＋分類器＋DINOv2 權重合計僅數百 MB 以內（見問題四），主要風險是**訓練作業與服務同時占用 GPU**——`OperationLock` 已處理；應把「服務運行中不得訓練」列為操作規範（亦符合「不自動訓練」原則）。

### Gaps
- Celery 在 Windows 的官方支援、Redis 是否有官方原生 Windows 版：未查證 → 未找到可靠證據（不作陳述）。
- Huey、arq 官方文件：未查證。
- 尖峰（例如同時 10 張）下的實際排隊時間與 push 比例：需以工作台 LINE 模擬器（不發真實訊息）壓力測試。
- `Conversation.handle()` 同意閘門與下載順序：需以測試確認。

### 參考文獻完整資訊（存取日期 2026-10-30／31）
1. [A] LY Corporation / LINE Developers. Receive messages (webhook). https://developers.line.biz/en/docs/messaging-api/receiving-messages/ （無更新日期）
2. [A] LINE Developers. Messaging API reference（Markdown 版）. https://developers.line.biz/en/reference/messaging-api/index.html.md （無更新日期）
3. [A] LINE Developers. Retry failed API requests. https://developers.line.biz/en/docs/messaging-api/retrying-api-request/
4. [A] LINE Developers. Messaging API pricing. https://developers.line.biz/en/docs/messaging-api/pricing/
5. [A] LINE Developers. Messaging API overview. https://developers.line.biz/en/docs/messaging-api/overview/
6. [A] LINE Biz 台灣. LINE 官方帳號. https://tw.linebiz.com/service/account-solutions/line-official-account/
7. [A] LINE Biz 台灣. LINE 官方帳號 2026 價格方案調整公告（2026/09/01 發布，2026/11/1 生效）. https://tw.linebiz.com/column/LINEOA-2026-Price-Plan/
8. [A] Pillow (PIL Fork) 13.0.0 documentation, Image module. https://pillow.readthedocs.io/en/stable/reference/Image.html ；原始碼 https://raw.githubusercontent.com/python-pillow/Pillow/main/src/PIL/Image.py
9. [A] OWASP Cheat Sheet Series. File Upload Cheat Sheet. https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html
10. [A] OWASP. API Security Top 10 2023 — API4:2023 Unrestricted Resource Consumption. https://api-security.owasp.org/editions/2023/en/0xa4-unrestricted-resource-consumption
11. [D；ICLR 2014] Szegedy C, Zaremba W, Sutskever I, Bruna J, Erhan D, Goodfellow I, Fergus R. Intriguing properties of neural networks. arXiv:1312.6199. https://arxiv.org/abs/1312.6199
12. [D；ICLR 2015] Goodfellow IJ, Shlens J, Szegedy C. Explaining and Harnessing Adversarial Examples. arXiv:1412.6572. https://arxiv.org/abs/1412.6572
13. [B] Finlayson SG, Bowers JD, Ito J, Zittrain JL, Beam AL, Kohane IS. Adversarial attacks on medical machine learning. Science. 2019;363(6433):1287-1289. doi:10.1126/science.aaw4399. https://pubmed.ncbi.nlm.nih.gov/30898923/
14. [C/B] Ma X, Niu Y, Gu L, Wang Y, Zhao Y, Bailey J, Lu F. Understanding adversarial attacks on deep learning based medical image analysis systems. Pattern Recognition. 2021;110:107332. doi:10.1016/j.patcog.2020.107332. 預印本 https://arxiv.org/abs/1907.10456
15. [A] Ultralytics. YOLO26. https://docs.ultralytics.com/models/yolo26/
16. [A] Ultralytics. YOLO11. https://docs.ultralytics.com/models/yolo11/
17. [A] Ultralytics. Export mode. https://docs.ultralytics.com/modes/export/
18. [A] Ultralytics. TensorRT integration. https://docs.ultralytics.com/integrations/tensorrt/
19. [C/B] Ozdemir OB, Li R. Bridging the Reliability Gap: INT8 Quantization Effects on Discrimination and Calibration in Medical Imaging. Proceedings of the 7th Conference on Health, Inference, and Learning, PMLR 333:952-965, 2026. https://proceedings.mlr.press/v333/ozdemir26a.html
20. [D] Qu C, Zhao R, Yu Y, Liu B, Yao T, Zhu J, Landman BA, Tang Y, Huo Y. Post-Training Quantization for 3D Medical Image Segmentation: A Practical Study on Real Inference Engines. arXiv:2501.17343, 2025. https://arxiv.org/abs/2501.17343
21. [A] PyTorch / torchvision. efficientnet_b0. https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.efficientnet_b0.html
22. [A/E] Meta AI Research. DINOv2（GitHub README）. https://github.com/facebookresearch/dinov2
23. [A] NVIDIA. TensorRT Installation Guide（TensorRT 11.4.1；last updated 2026-10-28）. https://docs.nvidia.com/deeplearning/tensorrt/latest/installing-tensorrt/installing.html
24. [A] ONNX Runtime. TensorRT Execution Provider. https://onnxruntime.ai/docs/execution-providers/TensorRT-ExecutionProvider.html
25. [A] PyTorch Tutorials. How to use torch.compile on Windows CPU/XPU. https://docs.pytorch.org/tutorials/prototype/inductor_windows.html
26. [E] PyTorch Forums. Windows support timeline for torch.compile. https://discuss.pytorch.org/t/windows-support-timeline-for-torch-compile/182268 ；AOTInductor on Windows. https://discuss.pytorch.org/t/aotinductor-on-windows/224382
27. [A] FastAPI. Background Tasks. https://fastapi.tiangolo.com/tutorial/background-tasks/
28. [E] Buchner J. imagehash（GitHub，BSD-2-Clause）. https://github.com/JohannesBuchner/imagehash
29. [A] Cloudflare. Cloudflare Tunnel（last updated 2026-08-04）. https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/
30. [A] Cloudflare. SSL/TLS encryption modes（last updated 2026-04-16）. https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/
