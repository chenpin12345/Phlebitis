# LINE 介面元件與拍照引導設計（研究原型：民眾上傳手臂/手部 IV 部位照片，靜脈炎照片分類，僅研究用途、非臨床診斷）

> 存取日：2026-10-30（LINE 文件第一輪；因速率限制中斷）與 2026-10-31（續查、驗證）。
> 文件日期說明：LINE Developers 文件頁（含 `index.html.md` 原始 Markdown 版）**均未顯示「最後更新日」**；以下凡標「頁面未標更新日」即此意。數字一律取自原文，已於 2026-10-31 用 curl 下載官方 Markdown 原文 grep 驗證。
> 來源分級：[A] 官方文件/法規/標準；[B] 系統性回顧/頂級期刊；[C] 同儕審查；[D] 預印本；[E] 部落格/範例/論壇（僅輔助）。
> 語氣標示：**研究證據顯示** / **業界慣例** / **本報告推論**。

---

## Q1. Rich menu（圖文選單）：限制、分眾、alias 切換、優先序、速率限制

### Takeaway
官方限制為：每個 LINE 官方帳號（以 API）最多 1000 個 rich menu、1000 個 alias；每個 rich menu 最多 20 個點擊區；圖片 JPEG/PNG、寬 800–2500 px、高 ≥250 px、寬高比 ≥1.45、≤1 MB；批次綁定一次最多 500 個 user ID。顯示優先序為「per-user（API）> default（API）> default（OA Manager）」；per-user 立即生效，API default 需使用者重開聊天室且「可能最多一分鐘」。rich menu 在 LINE for PC 不顯示。對本研究，「同意前 / 同意後」兩套選單用 per-user link（或 alias 切換）實作可行且即時。

### Cited Findings
- 圖片規格（Upload rich menu image 節）：Image format JPEG 或 PNG；width 800–2500 px；height ≥250 px；aspect ratio (w/h) ≥1.45；Max file size 1 MB；且「已設定的圖片不能替換」，要更新圖須建新 rich menu 物件。[A] — [Messaging API reference – Upload rich menu image](https://developers.line.biz/en/reference/messaging-api/#upload-rich-menu-image)（頁面未標更新日；存取 2026-10-31）
- 每帳號以 Messaging API 最多建立 1000 個 rich menu；超過回 400。[A] — [Messaging API reference – Create rich menu](https://developers.line.biz/en/reference/messaging-api/#create-rich-menu)（存取 2026-10-31）
- Rich menu object：`areas` Max 20 個 area objects；`chatBarText` 最多 14 字元；`name` 最多 300 字元（不顯示給使用者）；`selected: true` 表示預設展開。[A] — [Messaging API reference – Rich menu object](https://developers.line.biz/en/reference/messaging-api/#rich-menu-object)（存取 2026-10-31）
- Rich menu alias：每個官方帳號以 API 最多 1000 個 alias，滿額須先刪除；alias 只能指向同 channel 建立的 rich menu；alias 指向的 rich menu 必須已上傳圖片。[A] — [Messaging API reference – Create rich menu alias](https://developers.line.biz/en/reference/messaging-api/#create-rich-menu-alias)（存取 2026-10-31）
- `richmenuswitch` action：**只能用在 rich menu**，不能用於 Flex Message 或 quick reply；點擊後切換 rich menu，並以 webhook 回傳含 alias ID 的 postback event（`postback.params.newRichMenuAliasId`；切換失敗時不含此欄）；必要欄位 `richMenuAliasId`、`data`；`label` 選填、最多 20 字元，在裝置無障礙功能開啟時會被朗讀。[A] — [Messaging API reference – Rich menu switch action](https://developers.line.biz/en/reference/messaging-api/#richmenu-switch-action)（存取 2026-10-31）
- 批次綁定/解除：Link rich menu to multiple users 與 Unlink rich menus from multiple users 的 `userIds` 皆 Max 500 user IDs，回 202。[A] — [Messaging API reference – Link rich menu to multiple users](https://developers.line.biz/en/reference/messaging-api/#link-rich-menu-to-users)（存取 2026-10-31）
- 速率限制（per channel，token bucket 演算法；超過回 429）：Create rich menu / Delete rich menu / Delete rich menu alias / Get the status of rich menu batch control = **100 requests/hour**（以 OA Manager 建立/刪除不受此限）；Replace or unlink the linked rich menus in batches = **3 requests/hour**；Get rich menu list = 10 requests/second；其他端點（含 link/unlink per-user）= 2,000 requests/second。[A] — [Messaging API reference – Rate limits](https://developers.line.biz/en/reference/messaging-api/#rate-limits)（存取 2026-10-31）
- 顯示優先序（高→低）：1) 以 Messaging API 設定的 per-user rich menu；2) 以 Messaging API 設定的 default rich menu；3) 以 LINE Official Account Manager 設定的 default rich menu。非好友只會看到 default，且無法被綁定 per-user rich menu。[A] — [Rich menus overview](https://developers.line.biz/en/docs/messaging-api/rich-menus-overview/)（頁面未標更新日；存取 2026-10-31）
- 生效時間：per-user 立即生效（使用者不需重進聊天室）；但若直接刪除未解綁的 per-user menu，要到使用者重開聊天室才消失；API default 於使用者重開聊天室時生效，「It may take up to a minute」；OA Manager default 亦於重開聊天室時生效。[A] — [Rich menus overview](https://developers.line.biz/en/docs/messaging-api/rich-menus-overview/)；[Use per-user rich menus](https://developers.line.biz/en/docs/messaging-api/use-per-user-rich-menus/)（存取 2026-10-31）
- 「Rich menus aren't displayed on LINE for PC (macOS, Windows).」[A] — [Rich menus overview](https://developers.line.biz/en/docs/messaging-api/rich-menus-overview/)（存取 2026-10-31）
- 以 OA Manager 建立的 rich menu 只能在該工具中取得/編輯/看統計（工具間不互通）。[A] — [Rich menus overview](https://developers.line.biz/en/docs/messaging-api/rich-menus-overview/)
- 透過 alias 切換時，使用者看到的是優先序最高的 per-user menu；所以清除 default 對已切換過的使用者無效（官方疑難排解說明）。[A] — [Switch between tabs on rich menus](https://developers.line.biz/en/docs/messaging-api/switch-rich-menus/)（存取 2026-10-31）
- 變更時間軸：本輪未在官方 release notes / news 找到 2024–2026 年 rich menu 規格（尺寸、上限）變更公告。（見 Gaps）

### Inferences
- **本報告推論**：同意流程建議「default rich menu = 同意前選單（說明研究、開始同意、隱私權說明、聯絡窗口；**不放上傳照片按鈕**）」；使用者完成同意（後端記錄 consent 版本與時間）後，伺服器呼叫 Link rich menu to user，換成「同意後選單」（上傳照片、拍照說明、我的上傳紀錄、撤回同意）。per-user 立即生效，比改 default（需重開聊天室、最多約 1 分鐘）可靠。撤回同意時 unlink → 退回 default（同意前）。
- **本報告推論**：alias + `richmenuswitch` 適合「同一階段內的分頁」（如「上傳 / 說明」兩分頁），但切換由使用者端點擊觸發、不經伺服器同意檢查，**不應用作同意門檻**；同意前後的切換應由伺服器以 per-user link 控制，伺服器也必須在收到圖片時再檢查 consent（rich menu 只是 UI，不是存取控制）。
- **本報告推論**：14 位病人規模下，100 req/hour 建立限制與 3 req/hour 批次限制不構成問題；只需在部署時一次建立 2–4 個 rich menu。
- **本報告推論**：因 PC 版不顯示 rich menu，說明文字中應指引「請用手機 LINE 操作」。

### Gaps
- Rich menu 文件頁未提供「最後更新日」，無法給出文件版本日期；未找到 2024–2026 rich menu 規格變更紀錄（未找到可靠證據）。
- richmenuswitch 的實際切換延遲（毫秒級或秒級）官方未給數字（未找到可靠證據）。
- Rich menu 支援的最低 LINE app 版本本輪未查到。

---

## Q2. Flex Message：大小限制、altText、無障礙、跨裝置差異（用於同意摘要卡、結果卡）

### Takeaway
單一 bubble JSON 上限 30 KB、carousel 上限 50 KB 且最多 12 個 bubble；`altText` 必填、最多 1500 字元。官方明說相同 Flex Message 在不同 OS、LINE 版本、解析度、語言、字型下呈現可能不同，並提供 `scaling` 屬性讓字級隨 LINE 字體設定縮放（LINE iOS/Android 13.6.0+）。

### Cited Findings
- Flex Message `altText` 必填，Max 1500 字元。[A] — [Messaging API reference – Flex Message](https://developers.line.biz/en/reference/messaging-api/#flex-message)（存取 2026-10-31）
- 「The maximum size of JSON data that defines a bubble is 30 KB.」；「…a carousel is 50 KB.」；carousel 內 bubbles Max 12。[A] — [Messaging API reference – Bubble / Carousel](https://developers.line.biz/en/reference/messaging-api/#bubble)（存取 2026-10-31）
- 「The same Flex Message may be rendered differently depending on the environment of the recipient device… device OS, LINE version, device resolution, language settings, and font.」[A] — [Send Flex Messages](https://developers.line.biz/en/docs/messaging-api/using-flex-messages/)（頁面未標更新日；存取 2026-10-31）
- 版本支援：Flex Message 支援所有 LINE 版本，但 box `maxWidth`/`maxHeight`、text `lineSpacing`、video 需 iOS/Android 11.22.0+（PC 7.7.0+）；bubble size `deca`/`hecto` 與 button/text/icon 的 `scaling` 需 iOS/Android 13.6.0+（PC 7.17.0+）；舊版不支援 deca/hecto 時以 `kilo` 顯示。[A] — [Send Flex Messages – Operating environment](https://developers.line.biz/en/docs/messaging-api/using-flex-messages/)
- 無障礙：`scaling: true` 可依 LINE app 字體大小設定自動縮放字級與 icon，「send messages with accessibility in mind」；`adjustMode: shrink-to-fit` 為 best-effort、某些平台可能無效；bubble 寬度依螢幕而定，建議用 `flex` 而非 px 寬度；未指定 offset 時元件位置可能因裝置而異。[A] — [Flex Message layout](https://developers.line.biz/en/docs/messaging-api/flex-message-layout/)（存取 2026-10-31）
- 動作 `label` 會在裝置開啟無障礙功能時被朗讀（richmenuswitch label 說明）。[A] — [Messaging API reference – Rich menu switch action](https://developers.line.biz/en/reference/messaging-api/#richmenu-switch-action)
- 官方提供 Flex Message Simulator 可先預覽版面。[A] — [Send Flex Messages](https://developers.line.biz/en/docs/messaging-api/using-flex-messages/)
- 變更時間軸：`filler` 元件在 reference 中標示為 deprecated。[A] — [Messaging API reference – Flex Message](https://developers.line.biz/en/reference/messaging-api/#flex-message)（棄用日期本輪未查）

### Inferences
- **本報告推論**：同意摘要卡用單一 `mega`/`giga` bubble，內容只放「研究目的、只用於研究不提供診斷、照片存放於研究團隊自有電腦、可隨時撤回」4–5 行重點 + 「閱讀完整說明」(uri) + 「我同意」(postback) 按鈕；完整同意書放自有 HTTPS 網頁或 LIFF。`altText` 應寫成可獨立理解的句子（例：「研究同意說明：請在手機上開啟查看並點選『我同意』」），因為通知列/舊版/無障礙朗讀只看得到 altText。
- **本報告推論**：結果卡必須以非診斷語句呈現（例：「研究模型分類結果（非醫療診斷）」），並附「若紅、腫、熱、痛或有疑慮請聯絡醫療人員」固定文字；開啟 `scaling: true` 照顧長者大字體。所有 text 加 `wrap: true`，避免固定 px 寬度。
- **本報告推論**：30 KB 對文字卡綽綽有餘；不要把照片縮圖以 data URI 塞入（Flex image 需 HTTPS URL），若要顯示照片縮圖，URL 會指向自有伺服器，LINE 用戶端會向該伺服器取圖——需評估是否等同將研究照片 URL 暴露於 LINE 平台（建議結果卡不放照片）。

### Gaps
- 官方未提供 Flex Message 對螢幕報讀器（VoiceOver/TalkBack）逐元件朗讀行為的完整規格（未找到可靠證據）。
- altText 1500 字元是否在所有通知位置完整顯示，官方未說明。

---

## Q3. Quick reply：數量、動作類型、行為、平台支援（拍照 / 從相簿選）

### Takeaway
每則訊息最多 13 個 quick reply 按鈕；camera、cameraRoll、location 三種動作**只能用在 quick reply**；按鈕在點擊後消失，但 camera / cameraRoll / datetimepicker / location 會保留到使用者真的送出資料為止；quick reply 只支援 LINE for iOS / Android（PC 不支援）。這是「拍照」「從相簿選」最省工的入口。

### Cited Findings
- 「You can set up to 13 quick reply buttons to a message of any type.」；reference：`items` Max 13 objects；若一次回多則訊息，只顯示最後一則的 quickReply。[A] — [Use quick replies](https://developers.line.biz/en/docs/messaging-api/using-quick-reply/)；[Messaging API reference – Quick reply](https://developers.line.biz/en/reference/messaging-api/#quick-reply)（頁面未標更新日；存取 2026-10-30/31）
- 可用動作：postback、message、uri、datetimepicker、camera、cameraRoll、location、clipboard；**richmenuswitch 不可用**。camera/cameraRoll/location 只能用於 quick reply。[A] — [Use quick replies](https://developers.line.biz/en/docs/messaging-api/using-quick-reply/)；[Camera action](https://developers.line.biz/en/reference/messaging-api/#camera-action)
- Camera action：「This action can be configured only with quick reply buttons… the camera screen in LINE is opened.」label 最多 20 字元。Camera roll action 同樣只能 quick reply，開啟 LINE 內相簿畫面。[A] — [Messaging API reference – Camera action / Camera roll action](https://developers.line.biz/en/reference/messaging-api/#camera-action)（存取 2026-10-31）
- 行為：一般按鈕點擊後消失；camera、camera roll、datetime picker、location 按鈕會保留直到使用者送出預期資料；聊天室有新訊息送出時按鈕消失，該訊息被刪除則重新出現。[A] — [Use quick replies](https://developers.line.biz/en/docs/messaging-api/using-quick-reply/)（存取 2026-10-30）
- 平台：支援 LINE for iOS 與 LINE for Android（1 對 1、群組、多人聊天）；文件未列 PC。未設 icon 時 camera/cameraRoll/location 顯示預設 icon。[A] — [Use quick replies](https://developers.line.biz/en/docs/messaging-api/using-quick-reply/)
- 使用者傳來的圖片：webhook image message 的 `contentProvider.type = line` 時，以 message ID 呼叫 Get content（`api-data.line.me`）取得二進位；「Content is automatically deleted after a certain period from when the message was sent. There is no guarantee for how long content is stored.」[A] — [Messaging API reference – Get content](https://developers.line.biz/en/reference/messaging-api/#get-content)（存取 2026-10-31）

### Inferences
- **本報告推論（關鍵取捨）**：quick reply camera/cameraRoll 路線中，照片是**以 LINE 聊天訊息傳送、先存於 LY Corporation（LINE）平台**，研究端再以 Get content 下載。若研究計畫/IRB 的「照片不得進入第三方雲端」解讀為「不得經任何第三方伺服器」，此路線**本質上不符**；若解讀為「研究端不主動上傳至第三方雲端儲存/AI 服務」，則需在同意書揭露「照片會經 LINE 傳輸並暫存於 LINE 伺服器」。此點應交由 IRB 決定，並與 05_consent / 06_security 筆記對齊。
- **本報告推論**：webhook 收到 image 事件後應**立即**下載（因官方不保證保留期限），存自有 SQLite/檔案系統，並回覆一則含 quick reply（再拍一張 / 完成）與拍攝重點提示的訊息。
- **本報告推論**：上傳流程範例——rich menu「上傳照片」(postback) → bot 回覆「拍照前三個重點」文字或小 Flex + quick reply [📷 拍照][🖼 從相簿選][❓拍照範例]；收到照片後回覆「已收到第 N 張」+ quick reply [再拍一張][完成]。13 個上限遠高於需求，建議 ≤4 個，以利長者閱讀。

### Gaps
- LINE 傳送圖片時是否壓縮（LINE app 有「照片畫質：標準/高」設定）以及 Get content 取得的是否為原檔解析度，官方 Messaging API 文件未說明（未找到可靠證據）；這會影響分類模型輸入品質，建議實測。
- Get content 實際保留天數官方明言「不保證」，無數字。
- quick reply 支援的最低 LINE 版本未查到。

---

## Q4. LIFF：版本、尺寸、相機/相簿存取、限制、外部瀏覽器、權限、ID token、異動時間軸

### Takeaway
目前最新 LIFF SDK 為 **v2.31.2（2026-10-07）**；**v2.20.0–v2.31.0 因安全問題已 deprecated，官方預定約 2026-11-24 起限制使用**，新開發務必用 ≥v2.31.1。LIFF app 只能加到 LINE Login channel（Messaging API channel 自 2020-02-05 起不能新增），每 channel 最多 30 個；尺寸 Compact/Tall/Full；Endpoint 必須 https。官方自 2025-02-12 起建議「新 LIFF app 以 LINE MINI App 建立」，並表示 LIFF 將整合進 LINE MINI App 品牌，但截至查證日未見完成日期。LIFF browser = iOS WKWebView / Android WebView，官方未特別列出 `<input type=file>` 或 getUserMedia 限制，實務行為需實機測試。

### Cited Findings
- 版本：最新 v2.31.2（2026/10/07，改變 LIFF browser 中 URL query 值內 `?` 的處理）；v2.31.1（2026/09/30，安全修正）；v2.31.0（2026/08/31）；v2.30.0（2026/08/17）；v2.28.0（2026/03/24，新增 `liff.requestFriendship()`）；v2.27.0（2025/06/25，新增 `liff.permission.getGrantedAll()`）；v2.24.0（2024/07/23，新增 `liff.getAppLanguage()`、`liff.getLanguage()` deprecated）。[A] — [LIFF release notes](https://developers.line.biz/en/docs/liff/release-notes/)（存取 2026-10-30/31）
- 安全棄用：「LIFF v2.20.0 - v2.31.0 have been deprecated because an issue with potential security implications was identified… update to LIFF v2.31.1 or later immediately.」並「plan to restrict the use of older versions of the LIFF SDK (v2.20.0 through v2.31.0) around November 24, 2026」。[A] — [LIFF release notes](https://developers.line.biz/en/docs/liff/release-notes/)；相關 news：[2026-09-30 LIFF v2.31.1 released](https://developers.line.biz/en/news/2026/09/30/release-liff-2-31-1/)、[2026-10-20 Overview of the LIFF SDK vulnerability…](https://developers.line.biz/en/news/2026/10/20/liff-sdk-issue/)（news 頁為 JS 渲染，本輪只能從 release notes 交叉引用確認標題與日期）
- LIFF v1 end-of-life：2021-10-01。[A] — [LIFF release notes](https://developers.line.biz/en/docs/liff/release-notes/)
- Messaging API channel：2019-11-11 公告、**2020-02-05 生效**「不能再把 LIFF app 加到 Messaging API channel」，既有者可續用；LINE Login channel 不受影響。[A] — [LIFF release notes](https://developers.line.biz/en/docs/liff/release-notes/)
- 新增 LIFF：加到 LINE Login channel；每 channel 最多 30 個 LIFF app；Size 選 Compact / Tall / Full；「The URL scheme must be **https**. URL fragments can't be specified.」；Scopes：`openid`（getIDToken）、`email`、`profile`、`chat_message.write`（sendMessages）；Add friend option（LINE Login channel 才有）；Scan QR（`liff.scanCodeV2()` 需開啟）；Module mode 僅 Full 可選。LIFF URL 格式 `https://liff.line.me/{liffId}`，使用者經 LY Corporation 的 LIFF server 轉址到開發者 endpoint。[A] — [Adding a LIFF app to your channel](https://developers.line.biz/en/docs/liff/registering-liff-apps/)（頁面未標更新日；存取 2026-10-31）
- 整合宣告：「In the future, LIFF and the LINE MINI App will be integrated into a single brand… LIFF will be integrated into the LINE MINI App… we recommend that you create a new LIFF app as a LINE MINI App.」引用 news 2025-02-12。[A] — [Adding a LIFF app to your channel](https://developers.line.biz/en/docs/liff/registering-liff-apps/)；[News 2025-02-12](https://developers.line.biz/en/news/2025/02/12/line-mini-app/)（news 本文為 JS 渲染未能讀取全文）
- 整合時程：一篇日文技術文章稱至 2026 年 9 月仍無整合時程續報，且官方 FAQ 指 LINE Login channel 建立的 LIFF 不能事後遷移為 MINI App。[E] — [Classmethod: LIFF / LINE Login / MINI App differences](https://dev.classmethod.jp/articles/liff-line-login-mini-app-differences/)（僅輔助，未於官方 FAQ 原文驗證）
- LIFF browser：iOS 用 WKWebView、Android 用 Android WebView，行為依此；建議最新 iOS/Android/LINE；外部瀏覽器建議最新 Edge/Chrome/Firefox/Safari；LIFF browser 快取無法明確刪除，以 Cache-Control 控制；`liff.sendMessages()` 在從「最近使用的服務」重新載入後會失敗；LIFF 不支援 OpenChat。[A] — [LIFF overview](https://developers.line.biz/en/docs/liff/overview/)（存取 2026-10-30/31）
- LIFF browser 不支援的 web 技術（官方列舉）：theme-color meta、download 屬性、Add to home screen、Service Workers；其他技術是否支援「in accordance with the specifications of WKWebView and Android WebView」。**官方未將 `<input type="file">`、`capture`、getUserMedia 列為不支援。**[A] — [Differences between the LIFF browser and external browser](https://developers.line.biz/en/docs/liff/differences-between-liff-browser-and-external-browser/)（存取 2026-10-31）
- 實務回報：Android 14 上 `accept="image/*"` 僅開相簿選擇器；`accept="image/*;capture=camera"` 可恢復相機/檔案選項；獨立 `capture` 屬性則直接開相機；且在 LINE in-app browser 中出現的選擇器與 Chrome 不同。[E] — [zenn.dev 文章](https://zenn.dev/bltsdc/articles/52fd898281d48c)；iOS 17 上 `capture` 未開相機的未解問答 [E] — [Stack Overflow mirror](https://backiee.wasmer.app/http_Stackoverflow_com/questions/79630177/ios-17-camera-capture-not-working-in-next-js-with-input-type-file-capture)（均僅輔助）
- `liff.scanCodeV2()`：iOS 14.3+、Android 全版本的 LIFF browser 可用；外部瀏覽器需支援 WebRTC；PC 的 LIFF browser 不可用；內部使用 jsQR。[A] — [LIFF API reference – liff.scanCodeV2()](https://developers.line.biz/en/reference/liff/#scan-code-v2)（存取 2026-10-31）——**本報告推論**：此表顯示 LIFF browser 在 iOS 14.3+ 可取得相機串流（WebRTC/getUserMedia 類能力），但官方未直接保證一般網頁 getUserMedia 可用。
- `liff.isInClient()` 判斷是否在 LIFF browser；外部瀏覽器中 `liff.getLineVersion()` 回傳 null；在外部瀏覽器或 LINE in-app browser 開 LIFF 時須用 `liff.login()` 登入，而非自行發 LINE Login authorization request。[A] — [LIFF API reference](https://developers.line.biz/en/reference/liff/#is-in-client)
- `liff.sendMessages()` 條件：在 1 對 1/群組/多人聊天開啟的 LIFF browser、啟用 `chat_message.write`、非從最近使用服務重新載入；否則 403；一次最多 5 則訊息。[A] — [LIFF API reference – liff.sendMessages()](https://developers.line.biz/en/reference/liff/#send-messages)
- ID token：`liff.getIDToken()` 需 `openid` scope，JWT 有效 1 小時；LIFF browser 中於 `liff.init()` 取得，外部瀏覽器需 `liff.login()` 後取得。[A] — [LIFF API reference – liff.getIDToken()](https://developers.line.biz/en/reference/liff/#get-id-token)
- 伺服器端：「Don't send the details of the user profile obtained with liff.getDecodedIDToken() and liff.getProfile() to the server」；應傳 ID token 到伺服器，由伺服器呼叫 `POST /oauth2/v2.1/verify` 驗證後取得使用者資料；或傳 access token 以 `GET /oauth2/v2.1/verify` + `GET /v2/profile`；使用者關閉 LIFF 時 access token 會被撤銷。[A] — [Using user data in LIFF apps and servers](https://developers.line.biz/en/docs/liff/using-user-profile/)（存取 2026-10-31）
- `liff.permission.query()` / `liff.permission.requestAll()`（已全部同意時呼叫 requestAll 會 reject，應先 query）；`liff.permanentLink.createUrlBy()` 為建議做法，`createUrl()` 未來大版可能棄用；Permanent link 分享在目前 URL 不以 Endpoint URL 開頭時失敗。[A] — [LIFF API reference](https://developers.line.biz/en/reference/liff/#permission-query)；[LIFF release notes](https://developers.line.biz/en/docs/liff/release-notes/)
- `liff.openWindow({ url, external: true })` 可在外部瀏覽器開啟；LINE 14.20.0 以後對 Universal Links/App Links 的行為不再因 OS 而異。[A] — [LIFF API reference – liff.openWindow()](https://developers.line.biz/en/reference/liff/#open-window)

### Inferences
- **本報告推論**：LIFF 上傳頁的照片 POST 目標是我方 endpoint 網域（瀏覽器直接上傳），**照片本身不經 LINE 訊息平台**；但 LIFF URL 開啟時會經 LY 的 LIFF server 轉址、SDK 會與 LINE 平台交換 token（只含身分，不含照片）。這是符合「照片不進第三方雲端」最直接的設計。
- **本報告推論（hosting）**：LIFF endpoint 與 Messaging API webhook 都必須是公開可達的 HTTPS。若用 Cloudflare Tunnel / ngrok 等反向代理，TLS 通常在代理商端終止，照片明文會經過該第三方——可能違反「不經第三方雲端」；替代方案為：自有網域 + 路由器 port-forward + Let's Encrypt 憑證直接終止於本機（FastAPI/反向代理 Caddy 或 nginx），或使用在本機終止 TLS 的通道方案（需逐一查證其 TLS 終止位置）。此節需與 06_security 筆記交叉確認。
- **本報告推論**：LIFF 實作採 `<input type="file" accept="image/*">`（讓使用者選拍照或相簿），另提供「直接拍照」按鈕用 `capture="environment"`；必須在 iOS（多版本）與 Android（多廠牌）LINE 內實機測試。getUserMedia 自製取景框（overlay）在 iOS WKWebView 可行性需測試，不宜作為唯一路徑。
- **本報告推論**：身分綁定一律用 ID token → 伺服器 `/oauth2/v2.1/verify`，不信任前端傳來的 userId；LIFF SDK 版本鎖定 ≥2.31.1（建議 2.31.2）。
- **本報告推論**：因官方建議新 LIFF 改以 LINE MINI App 建立，但台灣 MINI App 認證需「certified provider」（見 Q5），研究原型可先在 LINE Login channel 建 LIFF（仍官方支援），或建「未認證 MINI App」；兩者都會被未來整合影響，需在計畫書標註風險。

### Gaps
- 2025-02-12 news 全文與 LIFF→MINI App 整合的實際完成日期：未能讀取（JS 渲染），截至 2026-10-31 未找到官方公告整合已完成（未找到可靠證據）。
- 2026-10-20 LIFF SDK 漏洞的技術細節未讀到全文。
- LIFF browser 中 `<input capture>` 與 getUserMedia 的官方支援聲明：未找到可靠證據（僅 [E] 實務回報）。
- LIFF browser 的 Full/Tall/Compact 在各裝置的實際高度比例，官方以圖示呈現、無數字。

---

## Q5. LINE MINI App：台灣可用性、審查、認證/未認證、是否適合研究原型、與 LIFF 差異、近期政策

### Takeaway
任何人都可建立「未認證 MINI App」（功能受限，header 顯示 endpoint 網域）；要成為認證 MINI App 須送審，而**服務地區為台灣或泰國時，只有隸屬「certified provider」的 MINI App channel 才能申請審查**（台灣透過 LINE Biz-Solutions 申請成為 certified provider）。MINI Apps 分頁僅日本可用。自 2025-10-01 起 MINI App 可在網頁瀏覽器使用。對 14 人研究原型，未認證 MINI App 或 LINE Login channel 的 LIFF 都可行；認證 MINI App 門檻與流程對研究原型不划算。

### Cited Findings
- 「Anyone can create an unverified MINI App, but… some features are restricted.」建立 MINI App channel 後即為未認證，直到通過審查；未認證 header 顯示標題與 endpoint 網域名稱；認證後顯示認證徽章與 MINI App 名稱，並可用「加到主畫面捷徑」「Custom Path」「Channel consent simplification」。[A] — [Introducing LINE MINI App](https://developers.line.biz/en/docs/line-mini-app/discover/introduction/)（頁面未標更新日；存取 2026-10-31）
- 能開發者：「Anyone who is a permitted customer in the LINE MINI App Policy can develop LINE MINI Apps.」[A] — [Introducing LINE MINI App](https://developers.line.biz/en/docs/line-mini-app/discover/introduction/)；[LINE MINI App Policy](https://terms2.line.me/LINE_MINI_App?lang=en)
- 台灣審查：「If the country or region to provide the service is Taiwan or Thailand, only LINE MINI App channels under a certified provider can apply for the verification review.」台灣申請管道：LINE Biz-Solutions。[A] — [Submitting LINE MINI App](https://developers.line.biz/en/docs/line-mini-app/submit/submission-guide/)（存取 2026-10-31）；[LINE Biz-Solutions 台灣 MINI App](https://tw.linebiz.com/service/other-solutions/line-mini-app/)
- 審查前須符合：icon 規範、橫向 safe area、loading icon、custom action button、效能指南、MINI App Policy；provider 名稱須等於服務提供者；隱私權政策中取得資料的公司須與 provider 名稱相同。[A] — [Submitting LINE MINI App](https://developers.line.biz/en/docs/line-mini-app/submit/submission-guide/)
- 入口：OA 的 rich menu / rich message 可連結 MINI App；「The MINI Apps tab is only available to users in Japan.」；Home tab「最近使用」與 LINE 搜尋只限認證 MINI App。[A] — [Introducing LINE MINI App](https://developers.line.biz/en/docs/line-mini-app/discover/introduction/)
- 與 LIFF 差異：MINI App 不能隱藏 action button（無 Module mode）；同一 channel 不能加多個 web app；畫面尺寸只能 Full。[A] — [Introducing LINE MINI App](https://developers.line.biz/en/docs/line-mini-app/discover/introduction/)
- MINI App 以 LIFF 開發，支援 OS/LINE 版本依 LIFF 建議環境；最低 LIFF SDK v2.1；HTML5 大多可用（例 Geolocation API）。[A] — [LINE MINI App specifications](https://developers.line.biz/en/docs/line-mini-app/discover/specifications/)（存取 2026-10-31）
- 時間軸：
  - 2023-12-13：MINI App 的 LIFF URL 改為 `miniapp.line.me/{liffId}`，舊 `liff.line.me` 連結仍可開啟。[A]（經搜尋摘要轉述，出自官方 console guide）— [LINE Developers Console Guide for LINE MINI App](https://developers.line.biz/en/docs/line-mini-app/discover/console-guide/)
  - 2025-02-12：官方宣布 LIFF 與 MINI App 將整合為單一品牌，建議新 LIFF 以 MINI App 建立。[A] — [News 2025-02-12](https://developers.line.biz/en/news/2025/02/12/line-mini-app/)
  - 2025-10-01：「all LINE MINI App users will be able to use the service in a web browser」（2025-09-26 公告）；外部瀏覽器開啟時先顯示引導頁，可點「Open in web browser」。[A] — [LINE MINI App specifications](https://developers.line.biz/en/docs/line-mini-app/discover/specifications/)；[News 2025-09-26](https://developers.line.biz/en/news/2025/09/26/mini-app-browser/)
  - 2026-08-17：LIFF v2.30.0 為 MINI App 的多帳號加好友選項新增參數（該設定預定 2026 年 9 月於日本提供）。[A] — [LIFF release notes](https://developers.line.biz/en/docs/liff/release-notes/)
  - 2026-09-30 / 2026-10-20：LIFF/LINE MINI App 共用的 LIFF SDK 漏洞與舊版限制（約 2026-11-24）。[A] — [LIFF release notes](https://developers.line.biz/en/docs/liff/release-notes/)

### Inferences
- **本報告推論**：研究原型（14 位病人）**不需要**認證 MINI App——認證的好處（主畫面捷徑、搜尋曝光、簡化同意）對受邀受試者無意義，而台灣審查需先成為 certified provider，屬商業合作流程。
- **本報告推論**：若要「順應官方方向」可建立未認證 MINI App（channel 類型 LINE MINI App），代價是只能 Full 尺寸、header 顯示網域；若要保留 Tall/Compact 半版頁面（例：同意摘要彈出半屏）則用 LINE Login channel 的 LIFF。兩者後端程式碼（LIFF SDK + 自有 HTTPS endpoint）幾乎相同。
- **本報告推論**：未認證 MINI App 的 header 會顯示 endpoint 網域，若網域是動態 DNS 或隧道服務網域，可能降低受試者信任；建議使用研究單位可辨識的網域。

### Gaps
- MINI App Policy 中「permitted customer」在台灣對學術/研究單位或個人開發者是否適用：未讀取 Policy 全文（未找到可靠證據）。
- 台灣 certified provider 的申請條件與費用：未查證（LINE Biz-Solutions 頁面未讀取全文）。
- 未認證 MINI App 在台灣對一般使用者是否有使用人數或其他限制：未找到可靠證據。

---

## Q6. 拍照引導設計模式：病人自拍照片品質證據、指引、即時回饋、長者、反證

### Takeaway
**研究證據顯示**：病人/家屬自拍照片多數「足以做臨床判斷」（約 80–91% 足夠），但簡單書面指示的效果**不一致**——有 RCT 顯示可略升影像品質但不改善診斷一致性；較大型的研究顯示訓練後一致性小幅上升（79%→84%）。**即時品質回饋**（AI 或色卡/清晰度偵測）在單臂與小型隨機可行性研究中顯著減少不良影像。拍照步驟是最大的可用性障礙，長者、肥胖、部位難拍者最困難。所有研究樣本小或為單臂設計，證據等級中低；**未找到**針對 IV 部位/靜脈炎自拍照片品質的研究。

### Cited Findings
**指引類（[A] 專業學會/標準）**
- ISIC Delphi 共識（JAMA Dermatol 2017;153(2):207–213；DOI 10.1001/jamadermatol.2016.3949）：5 輪 Delphi，最後 33 項建議，涵蓋照明、背景顏色、視野、方向、對焦、解析度、比例尺、色彩校正、儲存；作者指出仍需真實臨床可行性與效度驗證。[A/C 共識聲明] — [PubMed 27892996](https://pubmed.ncbi.nlm.nih.gov/27892996/)（摘要層級，未讀 33 項全文）
- 英國皮膚科醫學會（BAD）病人衛教單「Teledermatology」（2025-04 製作，下次審閱 2028-04）：用素色背景（空白牆或布）；均勻光線、避免陰影；先拍一張顯示部位位置的全景，再 1–2 張近拍；手機保持適中距離，太近會模糊，可點螢幕手動對焦；皮膚病灶可在旁放尺顯示大小；難拍部位請信任的人代拍；「Don't add any filters or edits」。頁面未提及閃光燈。[A] — [BAD Patient Information Hub: Teledermatology](https://www.skinhealthinfo.org.uk/condition/teledermatology)（存取 2026-10-31）
- 傷口攝影院內指引（僅輔助）：同一相機/解析度/光源/角度與距離、放置量尺與 ID、白色背景、避免藍綠背景、均勻室光時關閉閃光燈。[E] — [Southern Health (Canada) Wound Photography](https://staffnet.southernhealth.ca/wp-content/uploads/Wound-Photography.pdf)；[VUMC Wound Photography Guidelines](https://www.vumc.org/pip/sites/vumc.org.pip/files/Wound%20Photography%20Guidelines.docx)
- 燒燙傷單位稽核：僅 36% 照片光線理想，只有 1 張照片含比例尺（臨床人員拍攝，非病人）。[C，會議摘要] — [J Burn Care Res 摘要 757, PMC11023133](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11023133/)

**病人自拍品質與指示效果（[C]）**
- O'Connor et al., JAMA Dermatol 2017;153(12):1243–1248（DOI 10.1001/jamadermatol.2017.4280；NCT03246945）：40 對親子，內嵌 1:1 RCT（20 vs 20）給「3 步驟拍照指示單」；整體照片 vs 面診一致性 83%（κ=0.81）；**指示對一致性無顯著效果（85% vs 80%，P=.68）**；最佳單張影像品質分數略高（PQRS 9.5 vs 8.9，P=.04）。限制：樣本小、單一判讀者、模擬情境、診間光線。[C，小型 RCT] — [PubMed 29141082](https://pubmed.ncbi.nlm.nih.gov/29141082/)；[PMC5817452](https://pmc.ncbi.nlm.nih.gov/articles/PMC5817452/)
- Liu et al., Dermatol Online J 2024;30(3)（DOI 10.5070/D330363877）「Patient photographs taken without instructions are of sufficient quality for clinical decision-making in teledermatology」：113 組 e-visit 照片中 103 組（91.2%）足夠；僅 1.9% 因影像不足轉面診；作者提到樣本小、都會區、族群組成限制，並認為長者可能需要客製化工具。[C，回溯性，**反證：無指示也多數足夠**] — [PubMed 39090050](https://pubmed.ncbi.nlm.nih.gov/39090050/)；數字取自 [UCLA Health 摘要頁](https://connect.uclahealth.org/dom/2024/08/02/patient-photographs-taken-without-instructions-are-of-sufficient-quality-for-clinical-decision-making-in-teledermatology/)（PubMed 無摘要，未讀全文）
- 同一文引用的對照：另一研究中皮膚科醫師在無臨床脈絡下評 1200 張病人照片，只有 62.2% 足夠、55.1% 有用。[C，經二手引用] — [Quality and Perceived Usefulness of Patient-Submitted Store-and-Forward Teledermatology Images（ResearchGate）](https://www.researchgate.net/publication/362298942_Quality_and_Perceived_Usefulness_of_Patient-Submitted_Store-and-Forward_Teledermatology_Images)（未讀全文，期刊資訊未驗證）
- Saade et al., Int J Telemed Appl 2025:5789165（DOI 10.1155/ijta/5789165）：360 位成人，每人三組照片（病人自拍未協助 / 簡短標準化訓練後自拍 / 住院醫師拍），隨機抽一組給遠距判讀；診斷一致性 79% / 84% / 87%；治療一致性 38% / 44% / 45%；需追問病史比例 64%→47%。[C，中型隨機世代研究；期刊影響力一般] — [PubMed 41041428](https://pubmed.ncbi.nlm.nih.gov/41041428/)
- Macefield et al., J Tissue Viability 2023;32(1):94–101（DOI 10.1016/j.jtv.2023.01.001）：由 11 份文件歸納 21 個傷口攝影要素，其中 16 個納入病人指示；16 位病人認知訪談預測試後修正；89 位出院病人世代：52/89（58.4%）拍了照片，46/52（88.5%）成功傳送；未拍原因主要是健康問題（7）或沒時間/參與度低（4），技術/能力問題僅 2；影像經至少兩位獨立審閱者評為高品質、足以遠端評估 SSI。[C，世代研究，無對照組] — [PubMed 36681617](https://pubmed.ncbi.nlm.nih.gov/36681617/)
- Gunter et al., JMIR mHealth uHealth 2016;4(3):e113（DOI 10.2196/mhealth.6023）：9 位血管/一般外科住院病人可用性測試（ISO 9241-11）；只有 5/9（55.5%）能獨立完成 app，**最困難的是拍傷口照片**；**年紀較大、肥胖、鼠蹊部傷口的新手最困難**；81.8% 影像足以診斷；SUS 83.3/100；訓練約 4.7 分鐘。[C，極小樣本] — [PubMed 27683059](https://pubmed.ncbi.nlm.nih.gov/27683059/)

**即時品質回饋（[C]）**
- Vodrahalli et al., JAMA Dermatol 2023;159(5):496–503（DOI 10.1001/jamadermatol.2023.0091），TrueImage 2.0：回溯 357 張影像，辨識不良品質 ROC-AUC 0.78（模糊 0.84、光線 0.70）；98 位成人單臂臨床先導，病人拍照時即時回饋原因並可重拍，「reduction in the number of patients with a poor-quality image by 68.0%」。[C，品質改善研究、單臂無同期對照] — [PubMed 36920380](https://pubmed.ncbi.nlm.nih.gov/36920380/)
- Zhang et al., JMIR mHealth uHealth 2021;9(7):e26149（DOI 10.2196/26149）：系統性硬化症指端潰瘍居家自拍，app + 自製色卡貼紙 + 手機支架；隨機分「基本版 vs 即時品質回饋版」（清晰度 + 色卡偵測）；21 人收案、15 人納入分析；色卡偵測率 0.96（191/199）vs 0.86（158/183），回饋組清晰度顯著較高（P<.001）；每次評估中位數 <50 秒。作者有專利申請利益衝突。[C，小型隨機可行性研究] — [PubMed 34328440](https://pubmed.ncbi.nlm.nih.gov/34328440/)

**與靜脈炎直接相關**
- 未找到評估「病人或護理人員以手機拍攝 PIVC 部位照片、判讀靜脈炎一致性」的已發表研究；僅有一項登錄試驗（NCT07889895）以手機即時拍攝靜脈炎部位、由專家以 VIP scale（0–5）分級並測試深度學習模型（無結果）。[A 登錄資料] — [ClinicalTrials.gov NCT07889895](https://clinicaltrials.gov/study/NCT07889895)；靜脈炎評估量表尚缺一致共識（西班牙 Delphi：專家偏好 Maddox scale）。[C] — [PMC10855708](https://pmc.ncbi.nlm.nih.gov/articles/PMC10855708/)

### Inferences
- **研究證據顯示**：(1) 不給指示時多數照片仍「足夠」，但仍有約 10–20% 不足；(2) 純書面指示對最終判讀的增益小且不穩定；(3) 主動、即時的品質檢查與重拍機制效果較明確；(4) 拍照動作本身是流程中最大障礙，長者與部位難拍者最吃力。
- **業界慣例**（BAD、傷口攝影院內指引、ISIC 共識）：素色背景、均勻自然光、避免陰影與濾鏡、全景 + 近拍、適中距離並對焦、必要時放比例尺/色卡、同一距離角度重複拍攝、請他人代拍。
- **本報告推論（本研究適用的引導設計）**：
  1. 拍照前只給 3–4 條、配圖的要點（一張「好例子」示意圖 + 一張「壞例子」），而非長文；以 Flex bubble 或 LIFF 頁面呈現，字級 `scaling: true`。
  2. 要求「一張可看出手臂/手部位置的全景 + 一張 IV 部位近拍（約一個手掌寬距離）」；建議請家人代拍（單手拍自己另一隻手臂困難——由 Gunter 2016 的難拍部位結果推論）。
  3. 「關閉美顏/濾鏡」「不要用閃光燈、在白天靠窗或明亮室內」「手臂放在素色毛巾/床單上」。
  4. 收到照片後由伺服器做**輕量自動品質檢查**（模糊度 Laplacian variance、過暗/過曝、解析度），不合格立即回覆具體原因 + quick reply [重拍]——這是證據最一致的改善手段（Vodrahalli 2023、Zhang 2021）。
  5. 比例尺/色卡：對分類研究有價值（顏色校正、大小），但會增加受試者負擔；14 人階段可由研究人員在收案時提供小色卡/紙尺，並在研究設計中作為可選項比較——ISIC 共識列入但真實可行性尚待驗證。
  6. 因 IV 部位為**分類研究**而非臨床判讀，品質標準應與標註者（護理師）評分一致性連動：預先定義「可標註 / 不可標註」準則並統計不可標註比例，作為後續改版依據。

### Gaps
- 針對 IV 部位/靜脈炎自拍照片品質或照片判讀一致性的研究：**未找到可靠證據**。
- 長者自拍影像品質的年齡分層資料：僅 Gunter 2016（n=9）質性觀察；**未找到可靠證據**的量化研究。
- 「in-app 取景框 overlay」單獨效果的對照研究：未找到可靠證據（TrueImage 與 Zhang 都是品質回饋，不是 overlay）。
- 閃光燈對皮膚/傷口照片的影響：BAD 衛教未提及；僅院內指引 [E] 建議均勻室光時關閉，無研究證據。
- 系統性回顧：本輪未找到專門針對「病人自拍醫療照片品質」的系統性回顧（一篇二手引用稱皮膚癌 app 系統性回顧中近 20% 病人照片不可判讀，但未取得原文：[PMC9907654](https://pmc.ncbi.nlm.nih.gov/articles/PMC9907654/)）。
- Broman et al. 2018（JAMA Surg 模擬研究：加入傷口照片使特異度上升但敏感度/準確度下降、外科醫師較易低估分流）僅見搜尋摘要，未驗證原文，故不列為已引用發現。

---

## Q7. 建議介面組合：現在（~14 位病人）vs 未來（~1,000 張照片）

### Takeaway
**本報告推論**：關鍵分歧在「照片是否允許經 LINE 平台傳輸」。若 IRB/計畫允許（並在同意書揭露），現階段以「rich menu（per-user 分同意前/後）+ quick reply camera/cameraRoll + 伺服器自動品質檢查回覆」最快上線；若「照片不得經任何第三方」，則上傳必須走 LIFF（或未認證 MINI App）頁面直傳自有 HTTPS 伺服器，LINE 只負責入口、通知與身分（ID token）。未來 1,000 張規模建議統一走 LIFF 上傳頁，以取得引導 overlay、metadata、版本化同意與一致品質檢查。

### Cited Findings
- Quick reply camera/cameraRoll 只能在 quick reply、只支援 iOS/Android；照片成為 LINE 訊息，研究端用 Get content 下載，內容保留期間不保證。[A] — [Use quick replies](https://developers.line.biz/en/docs/messaging-api/using-quick-reply/)；[Get content](https://developers.line.biz/en/reference/messaging-api/#get-content)
- LIFF 需 LINE Login channel（或 MINI App channel）、endpoint 必須 https；LIFF URL 會先經 LY 的 LIFF server 轉址到開發者 endpoint。[A] — [Adding a LIFF app to your channel](https://developers.line.biz/en/docs/liff/registering-liff-apps/)
- 伺服器端身分應以 ID token + `/oauth2/v2.1/verify` 驗證，不可信任前端傳來的 profile。[A] — [Using user data in LIFF apps and servers](https://developers.line.biz/en/docs/liff/using-user-profile/)
- 官方建議新 LIFF 以 MINI App 建立；台灣 MINI App 認證需 certified provider。[A] — [Introducing LINE MINI App](https://developers.line.biz/en/docs/line-mini-app/discover/introduction/)；[Submitting LINE MINI App](https://developers.line.biz/en/docs/line-mini-app/submit/submission-guide/)
- LIFF SDK v2.20.0–v2.31.0 預定約 2026-11-24 被限制，須用 ≥v2.31.1。[A] — [LIFF release notes](https://developers.line.biz/en/docs/liff/release-notes/)
- 即時品質回饋可明顯減少不良影像（68% 減少；色卡偵測 0.96 vs 0.86）。[C] — [PubMed 36920380](https://pubmed.ncbi.nlm.nih.gov/36920380/)；[PubMed 34328440](https://pubmed.ncbi.nlm.nih.gov/34328440/)

### Inferences
- **本報告推論——比較表**

| 面向 | A. Rich menu + quick reply（camera/cameraRoll） | B. Rich menu + LIFF 上傳頁（自有 HTTPS） |
|---|---|---|
| 照片路徑 | 經 LINE 訊息平台暫存，再由 Get content 下載 | 瀏覽器直傳我方伺服器，不經 LINE 訊息 |
| 符合「不進第三方雲端」 | 視 IRB 解讀；需揭露；嚴格解讀下不符 | 較符合（但 HTTPS 通道/代理需自控 TLS） |
| 開發量 | 低（webhook + 下載 + 回覆） | 中（LIFF 前端、ID token 驗證、上傳 API、HTTPS 公開） |
| 拍照引導 | 只能在拍照前/後以文字、Flex 說明；事後品質回饋 + 重拍 | 可加範例圖、步驟頁、（實測可行時）取景 overlay、上傳前預覽與即時品質檢查 |
| Metadata（部位、左右手、留置天數、症狀問卷） | 需多輪對話 / postback 收集，易斷 | 同一表單一次收集，與照片綁定 |
| 同意書 | Flex 摘要 + 外部網頁 | LIFF 內完整同意頁 + 版本記錄 |
| 長者友善 | 操作最熟悉（同一般傳照片） | 多一層網頁，需測試字級與按鈕大小 |
| 相機相容性風險 | 低（LINE 原生相機/相簿） | 中（WKWebView/WebView 的 file input / getUserMedia 差異，需實機測） |
| 影像畫質 | LINE 可能壓縮（未證實，需實測） | 可取得原始檔（瀏覽器可能重新編碼 HEIC→JPEG，需測） |

- **本報告推論——現在（~14 位病人）**：
  - 若 IRB 允許 A：default rich menu（同意前）→ Flex 同意摘要 + 外部同意頁（自有伺服器）→ 同意後 per-user rich menu → 「上傳照片」→ 3 點拍照提示 + quick reply [拍照][相簿][範例] → webhook 立即 Get content 存本機 → 自動品質檢查 → 回覆「已收到/請重拍（原因）」+ 結果卡（非診斷字樣）。
  - 若 IRB 不允許照片經 LINE：直接採 B，但流程簡化——rich menu「上傳照片」(uri 開 LIFF，Tall 或 Full) → LIFF 頁：一張範例圖 + `<input type=file accept="image/*">` + 2–3 個必填欄位 → POST 至 FastAPI（附 ID token）→ 伺服器驗 token、存檔、品質檢查 → 頁面即時顯示結果並可重拍；回到聊天室時 bot 以 push/reply 送結果卡（push 會計入訊息額度，見 02_taiwan_pricing_quotas）。
  - 兩者皆應：rich menu 同意閘道由伺服器控管；收到照片時再次檢查 consent；PC 版提示改用手機。
- **本報告推論——未來（~1,000 張）**：統一走 B（LIFF 或未認證 MINI App），加入：分步驟引導頁、上傳前客戶端品質檢查（模糊/亮度）、metadata 表單、同意版本化、上傳失敗重試；quick reply 只保留作為「開啟上傳頁」與「重拍提醒」的快捷鍵。HTTPS 需以自有網域、TLS 終止於本機的方式公開，並做好 Windows 主機的可用性（UPS、自動重啟）與備份（見 06_security）。
- **本報告推論**：無論 A 或 B，都應在研究前以 3–5 位長者做可用性前測（仿 Macefield 2023 的認知訪談與 Gunter 2016 的 ISO 9241-11 觀察），以「可標註照片比例」與「獨立完成率」為指標。

### Gaps
- LINE 傳圖壓縮程度與 LIFF 中 file input 回傳的原始解析度、HEIC 處理：需實機測試，無官方資料（未找到可靠證據）。
- 台灣 IRB 對「經 LINE 傳輸研究照片」的實際審查立場：本輪未搜尋（屬 05/06 筆記範圍）。
- 自控 TLS 的公開通道方案（各隧道服務 TLS 終止位置）未在本輪逐一查證。
