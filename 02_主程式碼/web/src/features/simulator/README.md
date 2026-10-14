# LINE 模擬器（iOS／Android 樣式）

- `Simulator.tsx`：工程設定（手機外）、對話狀態、送出與重試。平台樣式只是 CSS 類別（`.line-phone.ios`／`.android`），切換不清空對話、不重送、不重新推論。
- `LineMessage.tsx`：依 `src/line_bot/messages.py` 實際產生的結構渲染：文字＋quickReply、圖片、Flex（bubble／box／text 的 layout、spacing、weight、size、color、wrap）。其他類型會明示「不支援」。
- 圖文選單由 `GET /api/v1/simulation/rich-menu` 提供（與 `src/line_bot/menu.py` 發布的 payload 相同），依 bounds 比例渲染點擊區。
- 後端：`src/workbench/simulation.py` 以 `src/line_bot/conversation.py`（與正式 webhook 共用的事件規則）處理事件，並以本機模擬 transport 記錄訊息（`sim_messages`），不使用 token、secret 或外部 API。

## 參考與限制（2026-10-13）

依據 LINE Developers Messaging API 文件（訊息類型、quick reply、postback action、rich menu 2500×1686 與區域定義）及 Flex Message 元件規格。

- 沒有取得逐版本的官方客戶端畫面，因此**不宣稱逐像素一致**。
- 色彩、圓角與字型集中在 `style.css` 的 `.line-phone` CSS 變數中，可調整。
- 「已送出（模擬）」只代表本機 transport 已記錄，不是 LINE 的送達或已讀回執。
