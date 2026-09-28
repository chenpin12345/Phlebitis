# LINE 官方帳號展示設定

## 已有功能

手機傳照片 → 簽章驗證 → 背景排隊 → 本地 YOLO11n 分析 → 結果卡片與框選圖。支援拍照說明、結果說明、專題介紹及四格圖文選單。第一版只支援一對一聊天。

缺少真實 LINE 帳號金鑰與公開 HTTPS 網址時，程式仍可做完整本地模擬測試，但無法宣稱已完成手機端實際串接。

## 帳號準備

1. 建立或使用自己的 LINE 官方帳號，在管理後台啟用 Messaging API。
2. 在 LINE Developers 取得 Channel secret 與 Channel access token。
3. 複製 .env.example 為 .env，在本機編輯實際值。不要貼到公開訊息或提交 Git。
4. 確認 models/selected/best.pt 與 metadata.json 已由 select 指令產生。
5. 目前模型屬展示模型，請在 .env 設定 DEMO_MODEL_ALLOWED=true；這不會把模型變成正式驗證模型。
6. 用你選用的 HTTPS 通道服務將公開網址轉送到 http://127.0.0.1:8000，並填入 PUBLIC_BASE_URL。
7. 執行 .venv\Scripts\python.exe -m src serve。
8. 在 LINE 後台設定 Webhook URL 為 PUBLIC_BASE_URL 加 /webhook，啟用 webhook，按 Verify。
9. 關閉會與機器人重複回覆的自動回應，加入官方帳號為好友並實際傳送測試照片。

例如已自行安裝 ngrok，可於另一個終端機執行 ngrok http 8000；或使用 Cloudflare Tunnel。服務網域變更時，PUBLIC_BASE_URL 與 LINE webhook URL 必須一起更新。通道帳號及可用網域由使用者管理，程式不會自動公開電腦。

## 圖文選單

    .\.venv\Scripts\python.exe -m src menu

素材輸出在 docs/line_menu，包含 rich-menu.png 與 rich-menu.json，這個指令不寫入 LINE。

確認帳號設定與圖稿後，若要設定為官方帳號的預設選單：

    .\.venv\Scripts\python.exe -m src menu --publish

此指令會建立新選單並設成預設，不刪除帳號既有選單。也可在 LINE Official Account Manager 手動上傳圖片，將四區設為傳送「開始分析」「拍照說明」「結果說明」「專題介紹」。

桌面版 LINE 可輸入相同文字，無需圖文選單。

## 行為及限制

- 訊息簽章由 Channel secret 驗證；相同事件編號於紀錄保留期間不重複分析。
- 單一使用者同時只處理一張；佇列預設最多等待四個任務。
- 顯示最多 60 秒的分析動畫；動畫不是後台處理期限。
- 在回覆權杖有效期間回覆；等待較久的任務以 push 傳回，需注意帳號額度及傳送資格。
- 圖片上限 10 MB、2,500 萬像素，支援 JPEG／PNG／WEBP。
- 模糊照片可能仍能解碼，系統不保證自動辨識所有影像品質問題；使用者應遵循拍照指引。
- 推論超過 120 秒會通知逾時。GPU 背景執行緒無法安全強制終止，會等該工作離開後再處理下一張，避免重疊使用 GPU。
- 服務重新啟動時，未完成任務標為 interrupted；原圖不落地，所以無法自行恢復，使用者需要重新傳圖。
- 無法解碼、超大圖片、佇列滿載或模型失敗都有文字提示。
- 框選圖供 LINE 透過 HTTPS 讀取，以不可猜測網址暫存一小時後失效；取消傳送事件會刪除本機對應結果。
- SQLite 只留任務識別與雜湊使用者識別等運作資訊；已結束任務保留 24 小時後清理。
- 原圖不永久保存、不自動加入訓練集。本機刪除不能刪除 LINE 平台或使用者聊天中的副本。

## 真實帳號驗收

依序確認：Verify 成功、文字選單回覆、正常傳圖、損壞圖片提示、連續傳圖排隊、框選圖片可顯示、服務關閉後不再聲稱在線。確認 push 額度及網域更新程序。

本地測試完全使用模擬 LINE；手機端驗收完成前，交接紀錄必須標示「待帳號與 HTTPS 設定」。


## 圖片輸出與官方規格

框選圖會另行縮放為最長邊 1600 像素以下、900 KB 以下的 JPEG，原圖不改寫。這張圖同時用作完整圖及預覽圖；JSON 框座標對應 source_size，圖片尺寸另記於 annotated_size。LINE 預覽圖限制為 1 MB，因此不能直接把手機原尺寸 JPEG 當預覽圖。

- [LINE 圖片訊息規格](https://developers.line.biz/en/reference/messaging-api/nojs/#image-message)
- [LINE webhook、重送及取消傳送說明](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)

結果回覆遇到網路不確定狀態時不自動重送，以避免重複通知；任務記錄 delivery_unconfirmed，已產生的圖片仍按原本時限保留。

取消傳送的訊息識別另保留 24 小時，避免 LINE 事件順序不同時，已取消的照片又被重送事件重新分析。
