# 06 資安設計：單機 Windows PC 上的 LINE Messaging API Bot 後端

> 範圍：研究原型（非臨床診斷）、台灣；FastAPI + React 管理介面 + SQLite，一台 Windows PC（消費級 NVIDIA GPU）。管理介面只綁 127.0.0.1，公開 webhook 服務與它分開。會收到手臂、手背的 IV 留置部位照片；研究照片不得上傳到第三方雲端儲存。webhook 簽章驗證已實作。
>
> 來源分級：[A] 官方文件或標準（LINE、OWASP、NIST、廠商官方文件）；[E] 部落格、論壇、範例程式碼（只作輔助）。
> 存取日：所有來源都在 **2026-10-31** 存取。原訂 2026-10-30，因工具流量限制延後一天。「文件日期」欄寫「頁面未標示」時，表示頁面上找不到發布或更新日期。
> 用語：**研究證據顯示**＝來源明文寫的；**業界慣例**＝常見做法，但本輪沒有一手文件佐證；**本報告推論**＝作者自己的推理。
> ⚠ 標記：與「研究照片不上第三方雲端」原則衝突，或可能衝突。

---

## Q1. Channel 憑證：channel secret、各類 channel access token、Windows 上的儲存與輪替

### Takeaway
LINE 目前有四種 channel access token：v2.1（JWT，最長 30 天、上限 30 個）、stateless（15 分鐘、不限數量、無法撤銷）、short-lived（30 天、上限 30 個，超過時最舊的失效）、long-lived（無期限、上限 1 個）。官方文件建議用「使用者自訂效期」的 token（v2.1）取代 long-lived，但本輪沒找到任何已公告的 long-lived 或 short-lived 棄用計畫。本專案建議：用 v2.1 或 stateless 搭配 assertion signing key（RSA 私鑰），私鑰與 channel secret 放在 Windows Credential Manager（DPAPI）或 ACL 鎖住的檔案，不放 repo。

### Cited Findings

**Channel secret**
- 研究證據顯示：webhook 簽章用 channel secret 當 HMAC-SHA256 的金鑰。channel secret 在 Console 的 Basic settings 分頁，每個 channel 不同，要有 Admin 權限才能查看或重發。官方原文表示「重發後舊 secret 失效」— [A] LINE Developers, "Verify webhook signature", https://developers.line.biz/en/docs/messaging-api/verify-webhook-signature/ （文件日期：頁面未標示；存取 2026-10-31）
- 研究證據顯示：stateless token 的發行端點接受 `client_id` + `client_secret` 這種變體，所以 channel secret 除了驗簽之外，也能用來換 token。洩漏的影響因此不只是「偽造 webhook」— [A] LINE 官方 OpenAPI 規格 `line/line-openapi` channel-access-token.yml, https://raw.githubusercontent.com/line/line-openapi/main/channel-access-token.yml （文件日期：未標示，main 分支；存取 2026-10-31）
- 同一份規格中，`POST /oauth2/v2.1/revoke` 與 `POST /v2/oauth/accessToken`（發 short-lived）都需要 `client_secret` — 同上 [A]

**Token 種類、效期與上限**（官方表格整理）

| 類型 | 效期 | 每 channel 上限 | 超過上限時 | 能否撤銷 |
|---|---|---|---|---|
| v2.1（使用者自訂效期，JWT） | 最長 30 天 | 30 | API 回錯誤，無法再發 | 可（`POST https://api.line.me/oauth2/v2.1/revoke`） |
| Stateless | 15 分鐘 | 不限 | — | **不可** |
| Short-lived | 30 天 | 30 | 依發行順序讓最舊的失效 | 可（`POST https://api.line.me/v2/oauth/revoke`） |
| Long-lived | 無期限 | 1 | 舊的失效 | 可，隨時（同上） |

- 上表的效期、上限與撤銷性，以及以下事項，來自 [A] LINE Developers, "Channel access token", https://developers.line.biz/en/docs/basics/channel-access-token/ （文件日期：頁面未標示；存取 2026-10-31）：
  - long-lived 只適用於 Messaging API channel，在 Console 的 Messaging API 分頁發行。
  - 重發 long-lived 會讓現有 token 失效，但重發時可以讓舊 token 最多延長 24 小時。
  - 上限按類型分開計算，過期的 token 不計入。
- 「超過上限時」那一欄來自 [A] LINE Developers Tips, "Points to check when using the Messaging API from multiple tools with a single LINE Official Account", https://developers.line.biz/en/tips/2026/07/23/using-multiple-api-tools/ （文件日期 2026-07-23；存取 2026-10-31）
- 端點（server 都是 `https://api.line.me`），出自 [A] line-openapi channel-access-token.yml（URL 同上）：

| 用途 | 方法與路徑 | 參數 |
|---|---|---|
| 發 stateless | `POST /oauth2/v3/token` | `grant_type=client_credentials`，加上 `client_assertion_type=urn:ietf:params:oauth:client-assertion-type:jwt-bearer` + `client_assertion`（JWT），或 `client_id` + `client_secret` 二選一 |
| 發 v2.1 | `POST /oauth2/v2.1/token` | 回應含 `access_token`、`expires_in`、`key_id` |
| 驗證 v2.1 | `GET /oauth2/v2.1/verify?access_token=…` | |
| 列出有效 v2.1 key ID | `GET /oauth2/v2.1/tokens/kid` | 需 JWT assertion |
| 撤銷 v2.1 | `POST /oauth2/v2.1/revoke` | `client_id`、`client_secret`、`access_token` |
| 發 short-lived | `POST /v2/oauth/accessToken` | |
| 驗證 short-lived 或 long-lived | `POST /v2/oauth/verify` | |
| 撤銷 short-lived 或 long-lived | `POST /v2/oauth/revoke` | `access_token` |

- v2.1 的 JWT 規格，出自 [A] LINE Developers, "Issue channel access token v2.1", https://developers.line.biz/en/docs/messaging-api/generate-json-web-token/ （文件日期：頁面未標示；存取 2026-10-31）：
  - assertion signing key 是 RSA 2048、`alg: RS256`。註冊的公鑰不能帶 `kid`；在 Console 的 Basic settings 註冊後才拿到 `kid`。
  - JWT header 為 `alg=RS256`、`typ=JWT`、`kid`。payload 為 `iss=sub=channel ID`、`aud=https://api.line.me/`、`exp`（JWT assertion 本身最長 30 分鐘）、`token_exp`（token 最長 30 天）。
  - 官方建議「安全地保存 token 與 key ID 的配對」。私鑰的保存方式，頁面沒有規定。
- 官方使用建議，出自 [A] "Channel access token"（URL 同上）：
  - v2.1 與 short-lived 要在效期內重複使用，不要每次呼叫都重發。
  - 應在到期前自動重發。
  - stateless 的設計就是每次使用都重新發行。
  - 疑似外洩的 token 應立即撤銷。
  - 一般每個開發團隊發行 token，每組最多 2 個，以便不中斷地輪替。
- 研究證據顯示：官方「Building a bot」頁提到，若使用 long-lived token，可以在 Security 分頁用 IP 或 CIDR 限制「哪些伺服器能呼叫 LINE API」。同頁建議改用「使用者自訂效期」的 token — [A] LINE Developers, "Build a bot", https://developers.line.biz/en/docs/messaging-api/building-bot/ （文件日期：頁面未標示；存取 2026-10-31）
- 研究證據顯示：本輪所讀的 channel access token 頁面**沒有任何棄用公告** — [A] "Channel access token"（URL 同上）

**Windows 上的儲存與輪替**
- 研究證據顯示：OWASP Logging Cheat Sheet 把 access token、加密金鑰與其他 primary secret 列為不得直接寫入 log 的資料 — [A] OWASP, Logging Cheat Sheet, https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html （文件日期：頁面未標示；存取 2026-10-31）

### Inferences
- 本報告推論，token 選型：本專案是單機、單一後端，建議按以下優先順序選擇。
  1. **v2.1**：產生 RSA 金鑰對，公鑰註冊到 Console，私鑰留在本機。啟動時用 JWT 換一個例如 7 天效期的 token，到期前自動重發，並把舊的撤銷。
  2. **stateless**：每 15 分鐘用 JWT 換一次即可。不必管理 token 狀態，外洩後最多 15 分鐘就失效；代價是無法撤銷，而且每次換 token 都依賴 api.line.me 可連線。
  - **不建議 long-lived**：無期限，而且外洩後必須手動到 Console 重發。
  - **不建議 stateless 的 `client_id + client_secret` 變體**：等於把 channel secret 變成「可換 token 的密碼」，channel secret 的價值因此提高。改用 JWT 變體，能讓 channel secret 只負責驗簽。
- 本報告推論，channel secret 洩漏的影響：攻擊者可以偽造 webhook（注入假照片或假事件），並且（透過 stateless 端點）換到 token，冒用 bot 推播。輪替步驟：
  1. 在 Console 重發 channel secret。官方文件表示舊 secret 失效，但是否立即失效、有無寬限期，本輪沒有找到文字。
  2. 更新本機儲存。
  3. 重啟 webhook 服務。
  4. 用 Console 的「Verify」與 `POST https://api.line.me/v2/bot/channel/webhook/test` 確認（端點出自 Messaging API reference 的 Markdown 版，https://developers.line.biz/en/reference/messaging-api/index.html.md，[A]，存取 2026-10-31）。
  5. 撤銷所有現存 token，並重發新 token。
- 業界慣例（本輪沒有抓取一手文件驗證），Windows 上的秘密儲存：
  - (a) Python `keyring` 套件在 Windows 預設使用 Windows Credential Manager。它以使用者帳號的 DPAPI 保護，只有同一使用者能解密。
  - (b) `.env` 檔適合開發階段，但必須列入 `.gitignore`，並用 `icacls` 移除 `Users` 與 `Everyone` 的讀取權，只留服務帳號與 Administrators。
  - (c) 環境變數會被同使用者的其他行程、crash dump 與診斷工具讀到，不適合長期保存高價值秘密。
  - 建議做法：RSA 私鑰與 channel secret 存進 Credential Manager（keyring），或存成 DPAPI 加密檔。服務啟動時讀入記憶體，不寫回 log 或 DB。
- 業界慣例（NIST SP 800-57 對 cryptoperiod 的一般原則；本輪未抓取原文）：定期輪替，並在疑似外洩時立即輪替。具體建議如下。
  - assertion signing key：每 6–12 個月輪替一次，這是本報告推論的值。LINE 允許同一 channel 註冊多把公鑰，因此可以「先加新 key、切換、再刪舊 key」。是否允許多把公鑰，本輪未驗證。
  - token：用 v2.1 的短效期（≤30 天）自動輪替。
  - 建議另寫一頁「憑證外洩 runbook」，列出：撤銷 token → 重發 secret → 輪替 RSA key → 檢查 log 有無異常推播 → 通報 IRB／計畫主持人。

### Gaps
- channel secret 重發後，舊值是否**立即**失效、有無寬限期：本輪只找到「舊 secret 失效」的文字，沒有時序描述 → 未找到可靠證據。
- stateless channel access token 的**推出日期**，以及完整的 token 變更時間線（LINE News 或 changelog 條目）：搜尋沒有找到 → 未找到可靠證據。建議撰寫者直接查 https://developers.line.biz/en/news/ 。
- LINE 官方對「應該用哪一種 token」沒有明確排名，只有「建議用使用者自訂效期 token」這句（出自 Build a bot 頁）。
- long-lived 或 short-lived 的棄用公告：本輪沒有找到 → 未找到可靠證據（不代表不存在）。
- keyring、DPAPI、NIST SP 800-57 與 OWASP Secrets Management Cheat Sheet 的原文：本輪因工具配額沒有抓取，上述相關內容都標為「業界慣例」。

---

## Q2. 從本機 PC 對外暴露 webhook：五種方案比較

### Takeaway
LINE 要求 webhook URL 是 HTTPS，憑證須由公開 CA 簽發（Let's Encrypt 可以，self-signed 不行），支援 TLS 1.2／1.3、不支援 1.1 以下。LINE **不公開** webhook 來源 IP，所以無法用 IP 白名單保護 webhook，只能靠簽章驗證。webhook 本體只有 JSON（訊息 ID、userId、replyToken），照片要由後端**主動**連到 `api-data.line.me` 下載，所以照片位元組不會經過 tunnel 業者。但如果之後做 LIFF 或網頁上傳頁，照片就會經過 tunnel；Cloudflare 會在 edge 解密，這與「不上第三方雲端」原則衝突 ⚠。

### Cited Findings
- 研究證據顯示，LINE 的 TLS 規格，出自 [A] LINE Developers, "SSL/TLS specification of the webhook source", https://developers.line.biz/en/docs/messaging-api/ssl-tls-spec-of-the-webhook-source/ （文件日期：頁面未標示；存取 2026-10-31）：
  - bot 伺服器必須使用 HTTPS。
  - 支援 TLS 1.3 與 TLS 1.2，**不支援 TLS 1.1 以下**。
  - 憑證須「由公開 CA 簽發」，購買的或 Let's Encrypt 等免費憑證都可以。
  - 目前的 cipher suite：TLS 1.3 的 AES-GCM 與 CHACHA20；TLS 1.2 的 ECDHE-(ECDSA|RSA)-AES-GCM 與 CHACHA20-POLY1305。
  - 已棄用的 suite（例如 AES128-SHA、ECDHE-RSA-AES128-SHA）「可能在近期無預警停用」。
- 研究證據顯示，以下出自 [A] "Build a bot"（URL 同 Q1）：
  - 憑證須由「一般瀏覽器廣泛信任的 CA」簽發，「不允許 self-signed 憑證」。
  - 憑證鏈要完整，中繼憑證要正確安裝。
  - 一個 channel 只能設一個 webhook URL。
- 研究證據顯示：LINE 企業開發指引要求 bot 伺服器支援 TLS 1.2 以上 — [A] LINE Developers, "Development guidelines for corporate customers", https://developers.line.biz/en/docs/partner-docs/development-guidelines/ （只取自搜尋摘要，全文本輪未抓取；文件日期：未確認；存取 2026-10-31）
- 研究證據顯示：LINE 官方原文表示 LINE Platform 的 IP 位址**不公開**，所以 IP 存取控制不能取代簽章驗證，官方建議以簽章驗證為主 — [A] "Verify webhook signature"（URL 同 Q1）
- 研究證據顯示，照片取得方式，出自 [A] LINE Developers, "Receive messages (webhook)", https://developers.line.biz/en/docs/messaging-api/receiving-messages/ （文件日期：頁面未標示；存取 2026-10-31）：
  - 使用者傳來的圖片、影片、音訊、檔案，要用 `GET https://api-data.line.me/v2/bot/message/{messageId}/content` 取得，並帶 `Authorization: Bearer {channel access token}`。
  - 縮圖可用 `/content/preview` 取得。
  - 使用者傳送的內容會在一段時間後由 LINE 自動刪除，期間未載明。
- 研究證據顯示：Cloudflare Tunnel 由本機 `cloudflared` 建立**只出不進**的連線，連到 Cloudflare 網路。因此防火牆可以封鎖所有入站流量 — [A] Cloudflare Docs, "Connect networks", https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/ （文件日期 2026-08-04；存取 2026-10-31）
- 業界共識（多為 [E] 來源）：Cloudflare 對代理的公開 hostname（包括走 Tunnel 的）**在 edge 終止 TLS、能看到明文 HTTP**，再另開一段連線到 origin。Cloudflare 不支援不終止 TLS 的 passthrough；origin 憑證只保護 edge 到 origin 那一段 — [E] Nextcloud 論壇 "Is Cloudflare Tunnel safe (privacy focused)?", https://help.nextcloud.com/t/is-cloudflare-tunnel-safe-privacy-focused/150268 ；[E] Pangolin, "Peer-to-Peer Alternative to Cloudflare Tunnels with Edge TLS Termination", https://pangolin.net/news/building-a-peer-to-edge-peer-reverse-proxy （兩者文件日期：未確認；存取 2026-10-31）
  - 注意：本輪沒有抓到 Cloudflare 官方明文描述「edge 解密」的頁面。不過這是 CDN 或反向代理提供 WAF 與快取功能的必要條件。
- 研究證據顯示：ngrok 雲端 Traffic Inspector 可記錄 HTTP 請求，並提供「full capture mode and replay」，也記錄 TCP 連線與 TLS 握手資訊。保存期限為 Free 24 小時、Hobbyist 與 Pay-as-you-go 72 小時，加購最長 90 天，之後清除。standalone agent 另有本機介面 `http://localhost:4040` — [A] ngrok Docs, "Traffic Inspection", https://ngrok.com/docs/obs/traffic-inspection/ （文件日期：頁面未標示；存取 2026-10-31）
  - full capture（是否存 body）是否預設開啟、如何關閉，該頁沒有寫明。
- 研究證據顯示，Tailscale Funnel，出自 [A] Tailscale Docs, "Tailscale Funnel", https://tailscale.com/kb/1223/funnel （last validated 2026-01-20；存取 2026-10-31）：
  - 狀態為 beta，「available for all plans」。
  - **TLS 在你自己的裝置上終止**，原文寫 relay「無法解密」經過的資料。
  - 只能用 443、8443、10000 埠；網域固定為 `*.ts.net`；頻寬有「不可調整」的上限，未給數字。
  - 需要 Tailscale v1.38.3 以上、MagicDNS、HTTPS 憑證，以及 policy 裡的 `funnel` attribute。
  - 頻繁申請憑證可能撞上 Let's Encrypt 速率限制。

### Inferences
- 本報告推論，比較表：

| 方案 | TLS 終止點 | 誰能看到明文 webhook JSON | 入站埠 | IP 白名單 | DDoS | 費用 | 與「不上雲」原則 |
|---|---|---|---|---|---|---|---|
| (a) 固定 IP + Caddy/nginx + Let's Encrypt + 路由器轉埠 | 本機 | 只有本機 | 要開 443（以及 ACME 用的 80，或改用 DNS-01） | 無法做（LINE 不公開 IP） | 自己承受，家用網路易被打掛 | 固定 IP 月租（依 ISP） | 最符合 |
| (b) Cloudflare Tunnel | **Cloudflare edge** | Cloudflare | 無 | 可在 Cloudflare 上設 WAF 或路徑規則 | 強 | 免費方案可用（本輪未抓到官方價目） | webhook JSON 可接受；**上傳頁 ⚠** |
| (c) ngrok | ngrok edge | ngrok，Inspector 可能保存 | 無 | 付費功能（未驗證） | 中 | Free 有限制，付費才有固定網域（本輪未驗證） | Inspector 保存請求 ⚠ |
| (d) Tailscale Funnel | **本機** | 只有本機，relay 只轉 TCP | 無 | 無 | 有限，頻寬有上限 | 各方案皆可（beta） | 符合 |
| (e) 小型 VPS relay | 看設計：VPS 若終止 TLS，VPS 就看得到明文；若做 TCP passthrough 加 WireGuard 回本機，則在本機終止 | 看設計 | 本機不需開埠 | 可在 VPS 做 | 依 VPS 業者 | VPS 月租 | passthrough 設計符合；VPS 若落地或快取資料 ⚠ |

- 本報告推論，關鍵論點：
  - 一般流程下，webhook 只帶 JSON；照片由後端**出站**到 `api-data.line.me` 取得，這條連線直接從 PC 出去，不經過 tunnel。因此在 (b)、(c) 方案下，tunnel 業者看得到的是：
    - userId
    - 訊息 ID
    - replyToken
    - 使用者打的文字
    - 時間戳記

    這些仍屬個人資料（userId 是穩定識別碼；文字可能含症狀描述），應寫進 IRB 或知情同意的資料流說明。
  - ⚠ 如果使用 LIFF、網頁上傳頁或管理介面對外，照片位元組就會經過 tunnel。若用 Cloudflare 或 ngrok，業者會在 edge 解密，違反「不上第三方雲端」原則。替代做法：上傳頁一律走 (d) Tailscale Funnel（本機終止 TLS），或走 (a) 自架反代；不然就只透過 LINE 聊天傳照片，不做上傳頁。
  - ⚠ 照片本身一定會先存在 LINE Platform（第三方）。這是使用 LINE 的必然結果，不是 tunnel 造成的。應在研究計畫中載明，並在下載後盡快處理。LINE 會自動刪除，但期限未公告。
  - **ngrok Inspector**：若使用 ngrok，必須確認 full capture 已關閉，或改用不保存 body 的設定。本機 4040 介面只綁 localhost，但也會顯示 body。
  - **建議排序**（研究原型、單機、重視隱私）：
    1. 首選 (d) Tailscale Funnel。TLS 在本機終止、不開入站埠、免費。風險是 beta 狀態、頻寬上限，以及網域固定為 ts.net。
    2. 次選 (a)，前提是能取得固定 IP，並願意承擔家用網路的 DDoS 風險。
    3. 若只走聊天、不做上傳頁，(b) 可以接受。它的 DDoS 防護最好，但要接受 Cloudflare 看得到 webhook JSON。
  - 無論哪一種，都要做到：
    - 只轉送 `POST /webhook`（或隨機化路徑，例如 `/webhook/<隨機字串>`，作為額外的低成本屏障；**不能取代**簽章驗證）。
    - 憑證由公開 CA 簽發。
    - 只開 TLS 1.2／1.3，以及 LINE 列為 current 的 cipher suite。

### Gaps
- LINE webhook 的逾時秒數、重送次數與間隔：官方明文「不公開，可能變更」（出自 "Receive messages" 頁）。
- Cloudflare 官方「edge 終止 TLS」的一手文字，以及 Cloudflare Tunnel 免費方案條款：本輪沒有抓到一手頁面 → 以 [E] 輔助。
- ngrok 目前的 Free 方案限制（隨機網域、頻寬、每月請求數）與 full capture 預設值：未找到可靠證據。
- Tailscale Funnel 的具體頻寬數字：官方未公開。
- 台灣家用 ISP 固定 IP 的價格：本輪沒有研究。

---

## Q3. 隔離架構

### Takeaway
把系統拆成三個行程：只接 webhook 的公開服務、只綁 127.0.0.1 的管理 API，以及推論 worker。三者以非管理員帳號執行，用 Windows 防火牆限制入站；SQLite 與照片目錄以 NTFS ACL 限縮，整機啟用 BitLocker。這幾項主要對應 OWASP API Security Top 10 2023 的 API2、API4、API8、API9。

### Cited Findings
- 研究證據顯示：LINE 要求簽章驗證使用**原始 body**，「代理或負載平衡器不得修改 header 或 body」，並以 UTF-8 處理 — [A] "Verify webhook signature"（URL 同 Q1）
- 研究證據顯示：webhook 應回 200；官方建議**非同步處理**事件，讓後續請求不必等待。若長時間收不到 webhook，平台可能暫停對你的 webhook 傳送 — [A] "Receive messages"（URL 同 Q2）；[A] Messaging API reference（Markdown 版，URL 同 Q1）
- 研究證據顯示：Cloudflare Tunnel 只建立出站連線，因此防火牆可以封鎖所有入站流量 — [A] Cloudflare "Connect networks"（URL 同 Q2）
- 研究證據顯示：OWASP 建議限制並定期審查 log 讀取權限，log 盡早移到唯讀媒體，並監控對 log 的存取 — [A] OWASP Logging Cheat Sheet（URL 同 Q1）

### Inferences
- 本報告推論，建議架構：
  ```
  Internet → (Funnel / Caddy / cloudflared) → 127.0.0.1:8001  webhook-svc
                       ├─ 只允許 POST /webhook
                       ├─ body 上限 ~1 MB
                       ├─ 先驗 HMAC，再 enqueue
                       └─ 回 200
  127.0.0.1:8000  admin-api + React（不經任何 tunnel；防火牆封鎖入站）
  worker 行程：從 queue（SQLite 表）取事件 → 出站下載 api-data.line.me → Pillow 驗證 → 推論（GPU）→ reply/push
  ```
- 本報告推論，各項原則：
  - webhook-svc 不掛載 admin router，也不用同一個 FastAPI app。這樣就算 tunnel 設定錯誤，也不會把管理介面暴露出去。
  - 反代或 tunnel 端只轉送 `/webhook`，其餘路徑回 404。webhook-svc 本身也只註冊這一條路由，做成雙層 allowlist。
  - FastAPI 要關閉 `/docs`、`/redoc`、`/openapi.json`（`docs_url=None` 等）。
- 業界慣例（未抓一手文件），Windows 設定：
  - 建一個標準使用者（非 Administrators）作服務帳號，用 NSSM、WinSW 或工作排程器以該帳號執行。
  - 用 `New-NetFirewallRule` 封鎖 8000、8001 的入站流量（只用本機時，綁 127.0.0.1 即足夠）。
  - 若採方案 (a)，只開放 443 入站給反代的執行檔。
  - SQLite DB、照片目錄與秘密檔用 `icacls` 移除繼承，只授權給服務帳號與 Administrators。
  - 啟用 BitLocker 加密整碟，並保護外接備份碟（BitLocker To Go）。
  - 注意：Windows 11 Home 沒有完整的 BitLocker 管理介面，只有「裝置加密」，需確認硬體支援。這是本報告推論，本輪未驗證。
- 本報告推論，對應 OWASP API Security Top 10 2023（類別名稱依既有知識，本輪未抓取 https://owasp.org/API-Security/editions/2023/en/0x11-t10/ 驗證）：
  - **API2 Broken Authentication**：webhook 只靠 HMAC。admin 介面雖然只綁本機，仍應設登入，因為 PC 可能有多位使用者。
  - **API4 Unrestricted Resource Consumption**：body 上限、每位使用者的照片數上限、佇列長度上限（見 Q4）。
  - **API8 Security Misconfiguration**：關閉 docs 端點、關閉 debug、TLS 設定。
  - **API9 Improper Inventory Management**：明確列出哪些路由對外。
  - **API10 Unsafe Consumption of APIs**：把 LINE 回傳的內容視為不可信，因此要驗證圖片（見 Q6）。
  - **API1 BOLA**：管理介面依 userId 或 photoId 查資料時要檢查授權。

### Gaps
- Windows 服務帳號、防火牆、NTFS ACL、BitLocker（Home 版）的一手 Microsoft 文件：本輪因配額沒有抓取 → 標為業界慣例，撰寫者引用前應補查。
- OWASP API Security Top 10 2023 原文：本輪未抓取。

---

## Q4. 速率限制與濫用防護

### Takeaway
順序很重要：先檢查 body 大小，再驗 HMAC 簽章，**通過後**才做任何解析、DB 寫入或下載。驗證通過後依 `webhookEventId` 去重、按 userId 做 token bucket，並設每日照片上限。同一個 channel 的所有工具共用 LINE API 的 rate limit，下載與回覆也需要節流。

### Cited Findings
- 研究證據顯示：缺少簽章 header 或簽章不符時，不應處理事件，應以錯誤結束 — [A] "Verify webhook signature"（URL 同 Q1）
- 研究證據顯示：LINE 的 rate limit 按 channel 與 API 功能計算，同一個 channel 的多個工具合計不得超過 — [A] LINE Tips 2026-07-23（URL 同 Q1）
- 研究證據顯示：同一事件可能送達不只一次，應以 `webhookEventId` 去重。啟用 redelivery 時，重送事件與原事件除了 `deliveryContext.isRedelivery` 之外完全相同，replyToken 也相同。重送可能不照順序到達，應以 `timestamp` 判斷前後文 — [A] "Receive messages"（URL 同 Q2）

### Inferences
- 本報告推論，處理順序：
  1. 反代或 ASGI 層限制 body 大小（webhook JSON 通常很小；可設 1 MB 上限，超過回 413）。
  2. 讀取原始 bytes。
  3. 用 `hmac.compare_digest` 做 HMAC-SHA256 常數時間比對（LINE 沒有規定比對方式，這是本報告建議）。不符就回 401 或 400，不寫 DB、不記 body。
  4. 解析 JSON。
  5. 每個事件以 `webhookEventId` 插入 SQLite（UNIQUE 約束），重複的就略過。
  6. 寫入佇列後立即回 200。
- 本報告推論，限流：
  - **per-IP 限流對 webhook 意義有限**：來源都是 LINE，而且 LINE 不公開 IP。偽造請求在 HMAC 這一關就會被擋下，成本很低。per-IP 限流比較適合防止未驗簽前的洪水攻擊，可以在 tunnel 或反代層做（Cloudflare WAF rate limiting、Caddy rate-limit 外掛，或 slowapi 以 IP 為 key）。
  - **per-userId**：在 worker 端用 SQLite 記錄。例如每位使用者每分鐘最多 N 則訊息、每日最多 M 張照片（研究流程每天只需 1–3 張，上限可設 10）。超過的部分只回一則說明，不下載、不推論。
  - 「無驗證的 slowapi 限流」只能保護 CPU，無法辨識濫用者，所以 userId 限流要放在驗簽之後。
- 本報告推論，照片洪水攻擊：
  - 佇列設長度上限，以及每位使用者的未處理件數上限。
  - 下載限制並行數（例如 2），並遵守 LINE rate limit。
  - GPU 推論採單一 worker 序列處理。
  - 下載前可先檢查 `contentProvider.type`（`line` 或 `external`）。若為 external，代表會連到外部 URL，屬於 SSRF 相關風險（見 Q6），建議直接拒絕。
- 本報告推論：reply token 有使用期限，而佇列可能延遲處理，所以佇列較長時改用 push message 回覆。注意 push 會計入訊息額度。

### Gaps
- LINE 各 API（get content、reply、push、token 發行）的 rate limit 具體數字：本輪抓到的 reference 片段沒有包含 → 未找到可靠證據，撰寫者應查 Messaging API reference 的「Rate limits」節。
- reply token 的有效時間：本輪沒有找到一手文字 → 未找到可靠證據。
- slowapi 文件：本輪未抓取。

---

## Q5. Log 遮罩

### Takeaway
依 OWASP，以下內容不得直接寫入 log：access token、秘密、金鑰、連線字串、敏感個資。對本專案而言就是：

- channel access token
- channel secret 與 RSA 私鑰
- Authorization header
- `x-line-signature`
- replyToken
- 完整 userId（改為 keyed hash）
- 照片 bytes
- webhook 原始 body

做法是在 Python logging 掛 Filter，關閉或精簡 uvicorn access log，並避免例外 traceback 把 request body 帶進 log。

### Cited Findings
- 研究證據顯示，OWASP 列出應移除、遮罩、雜湊或加密、不得直接記錄的資料，出自 [A] OWASP Logging Cheat Sheet（URL 同 Q1）：
  - session 識別值（需要追蹤時可改記雜湊值）
  - access tokens
  - 密碼
  - 加密金鑰與其他 primary secrets
  - DB 連線字串
  - 敏感個資與部分 PII
  - 比 log 系統等級更高的資料

  同一份文件的其他建議：
  - 不需要身分時，以假名化或去識別化處理。
  - 使用結構化格式（JSON）防止 CR/LF log injection，並限制寫入 log 的使用者輸入長度。
  - 依法定或契約期限保存，不得提前刪除，也不得超期保存。
- 研究證據顯示：redelivery 的事件與原事件除了 `isRedelivery` 外完全相同，**replyToken 也相同**。因此 log 裡的 replyToken 在有效期內可被重用 — [A] "Receive messages"（URL 同 Q2）
- 研究證據顯示：ngrok 雲端 Traffic Inspector 會保存流量事件 24 小時到 90 天（依方案），本機 4040 介面也可以檢視請求 — [A] ngrok "Traffic Inspection"（URL 同 Q2）

### Inferences
- 本報告推論，實作重點：
  - 自訂 `logging.Filter`，掛在 root logger 與 uvicorn 的 logger 上。它對 `record.msg` 與 `record.args` 做正規表示式遮罩，涵蓋：
    - `Bearer\s+\S+`
    - `"replyToken"\s*:\s*"[^"]+"`
    - `x-line-signature`
    - `U[0-9a-f]{32}`（LINE userId 的格式；依既有知識，本輪未驗證）
    - JWT 的三段 base64url 格式
  - userId 以 `HMAC-SHA256(server_pepper, userId)` 取前 16 hex，作為 log 與分析用的假名；pepper 和其他秘密存放在同一處。
  - uvicorn 用 `--no-access-log`（或 `access_log=False`），改由自己的 middleware 記錄。只記：方法、路徑、狀態碼、耗時、body 長度、驗簽結果、事件數、雜湊後的 userId。**不記** query string、header、body。
  - 例外處理：全域 exception handler 只記錄例外類型與 traceback，`logger.exception` 不附 request 物件。FastAPI 的 `RequestValidationError` 預設會回傳輸入值，webhook 端應改寫成簡短錯誤。
  - httpx 或 requests 的 debug log 會印出 Authorization header，正式環境把它們的 logger 等級設為 WARNING。
  - 照片絕不寫入 log 或錯誤追蹤服務（例如 Sentry 這類雲端 APM）。⚠ 第三方雲端 APM 或錯誤追蹤服務若接收 request body 或附件，就違反原則；替代做法是只寫本機 log 檔。
  - log 檔放在 ACL 限縮的目錄；用 `RotatingFileHandler` 或 `TimedRotatingFileHandler`；依研究計畫訂出保存期限。
  - ⚠ 若使用 ngrok：Inspector 會在雲端保存請求，包含 webhook JSON 與 replyToken。應關閉 full capture、改用不保存內容的方案，或改用 Funnel 或自架反代。
- 業界慣例：replyToken 有效期短，但仍應遮罩，因為 log 可能在有效期內被讀到，而且重送事件會帶相同 token。

### Gaps
- uvicorn 官方 logging 設定文件、Python `logging.Filter` 文件：本輪未抓取（屬一般知識）。
- ngrok full capture 的預設值與關閉方法：未找到可靠證據。

---

## Q6. 其他：圖片驗證、SSRF、相依套件、重放防護

### Takeaway
HMAC 簽章不含時間戳記，本身無法防重放。應以 `webhookEventId` 唯一鍵去重，搭配「事件 timestamp 過舊就只記不處理」的策略；時間窗要放寬，以容納 redelivery 延遲。下載的圖片要用 Pillow 的 `formats=` 限制格式並保留 decompression bomb 防護（不可設 `MAX_IMAGE_PIXELS=None`），也要限制下載大小。

### Cited Findings
- 研究證據顯示：LINE 簽章頁沒有提到時間戳記、nonce 或重放防護 — [A] "Verify webhook signature"（URL 同 Q1）
- 研究證據顯示：事件可能重複送達，應以 `webhookEventId` 去重；重送事件可能延遲並且亂序；重送次數與間隔不公開，平台可能強制關閉重送 — [A] "Receive messages"（URL 同 Q2）
- 研究證據顯示，Pillow 13.0.0 文件，出自 [A] Pillow Docs, `PIL.Image.open`, https://pillow.readthedocs.io/en/stable/reference/Image.html （Pillow 13.0.0；存取 2026-10-31）：
  - 像素數超過 `MAX_IMAGE_PIXELS` 會發出 `DecompressionBombWarning`；超過兩倍時改為拋出 `DecompressionBombError`。
  - 設為 `None` 會停用這項檢查。
  - 可用 `warnings.simplefilter` 把警告升級為錯誤。
  - `Image.open(fp, formats=[...])` 可以限制嘗試解析的格式。
- 研究證據顯示：LINE 會在一段時間後自動刪除使用者傳送的內容 — [A] "Receive messages"（URL 同 Q2）

### Inferences
- 本報告推論，重放防護：
  - 威脅模型：攻擊者若取得一份合法的 webhook body 和簽章（例如從 tunnel 業者的 log、ngrok Inspector 或誤記的 log），可以原封不動重送。
  - 防護做法：
    1. `webhookEventId` 存 SQLite UNIQUE，保留至少 7–30 天。
    2. 事件 `timestamp` 與現在相差超過例如 1 小時：若 `isRedelivery=false`，記為可疑並不處理；若為 redelivery，可放寬到例如 24 小時。這是本報告的建議值，LINE 沒有公告重送時間窗。
  - 也因此，前述的「不在任何地方保存原始 body 加簽章」，本身就是重放防護的一環。
- 本報告推論，圖片驗證流程：
  1. 下載時用串流讀取，並設上限，例如 20 MB；LINE 圖片大小上限本輪未查證。
  2. 用 magic bytes 確認是 JPEG 或PNG（必要時含 HEIC）。
  3. 呼叫 `Image.open(buf, formats=["JPEG","PNG"])`，接著 `img.verify()`，再重新開檔後 `load()`。
  4. 把 `DecompressionBombWarning` 設為 error。`MAX_IMAGE_PIXELS` 依研究需求下修（例如 50 MP）。
  5. 重新編碼存檔並去除 EXIF（含 GPS），檔名用隨機 UUID，不使用原始名稱。
- 本報告推論，SSRF：
  - 後端只連固定網域（`api.line.me`、`api-data.line.me`），一般沒有 SSRF 風險。
  - 若事件的 `contentProvider.type == "external"`（帶外部 URL），**不要**去抓那個 URL。這個欄位的語意依既有知識，本輪未抓取 reference 驗證。
  - httpx 用 `follow_redirects=False`，並設 allowlist。
- 業界慣例，相依套件：
  - 固定版本（`requirements.txt` 加 hash，或 `uv.lock`）。
  - 定期執行 `pip-audit`。
  - 追蹤 `line-bot-sdk`、Pillow、FastAPI、uvicorn、cloudflared、tailscale、Caddy 的安全公告；Pillow 歷來有影像解析相關的 CVE。
  - 本輪沒有抓取 line-bot-sdk-python 的 release notes。
- 本報告推論，⚠ 雲端衝突總表：
  - Cloudflare 或 ngrok 若轉送上傳頁流量 → 改用 Funnel 或自架反代。
  - ngrok Inspector 保存請求 → 關閉或不使用 ngrok。
  - 雲端錯誤追蹤或 APM 收到 body → 只用本機 log。
  - 雲端備份（OneDrive 自動同步桌面資料夾！）可能把照片目錄同步上去 → 照片與 DB 放在不受 OneDrive 同步的路徑，例如 `C:\PhlebitisData\`，備份到 BitLocker 加密的外接碟。
    - 這點與本專案特別相關：專案位於 `C:\Users\user\Desktop\...`。若使用者開啟 OneDrive「桌面備份」，桌面會被同步。是否已開啟，本報告推論者無法確認，應實際檢查。

### Gaps
- LINE 圖片訊息的大小上限、`contentProvider` 欄位的確切定義：本輪沒有抓到 reference 的相關段落 → 未找到可靠證據。
- Pillow `MAX_IMAGE_PIXELS` 的預設值：抓取內容在該段落之前就被截斷了。依既有知識約為 89,478,485，但本輪未驗證，引用前應確認。
- line-bot-sdk-python 最新版本與安全公告：本輪未查。
