# LINE 使用者傳送影像的處理方式及其對靜脈炎照片分類模型的影響

> 查證日期：2026-10-30 至 2026-10-31（研究中途因工具額度中斷，隔日續查）。來源分級：[A] 官方文件／主管機關／標準；[B] 系統性回顧、統合分析、頂級會議；[C] 同儕審查論文；[D] 預印本；[E] 部落格、範例程式、論壇（只能佐證，不能單獨作為依據）。
> 用語：**研究證據顯示**＝有文獻支持；**業界慣例**＝常見做法、證據有限；**本報告推論**＝本報告的推理，需要實測。
> 所有 developers.line.biz 頁面都沒有標示「最後更新日期」，因此文件日期一律記為「頁面未標示，查證日 2026-10-30／31」。

## Q1. Messaging API「Get content」：保存期限、檔案大小、速率限制、preview／transcoding、contentProvider、imageSet

### Takeaway
官方只說使用者傳送的內容會「在一段時間後自動刪除」，沒有公布天數，也不保證保存多久。官方也明確寫出使用者內容「可能在內部被轉換，例如縮小（shrinking）」，所以 Bot 下載到的檔案不保證是手機上的原檔。收到 webhook 就應立即下載並自行保存。

### Cited Findings
- [A] Get content 端點 `GET https://api-data.line.me/v2/bot/message/{messageId}/content`。原文："Content is automatically deleted after a certain period from when the message was sent." 官方沒有給天數，也不保證保存期間。— [Messaging API reference（index.html.md，Get content 段）](https://developers.line.biz/en/reference/messaging-api/index.html.md)（頁面未標示日期；查證 2026-10-31）
- [A] 同一段原文："Content sent by users may be transformed internally, such as shrinking." 這是 LINE 官方承認 Bot 取得的內容可能被縮小或轉換。— [同上](https://developers.line.biz/en/reference/messaging-api/index.html.md)
- [A] 二進位資料仍在準備中時，Get content 回傳 `202`，此時拿不到資料。內容不存在回 `404 Not Found`；使用者收回（unsend）訊息時回 `410 Gone`（"The content is gone"）。— [同上](https://developers.line.biz/en/reference/messaging-api/index.html.md)
- [A] Preview 端點 `GET .../content/preview`：「preview image is image data converted to a smaller data size than the original content」。預覽圖同樣「在一段時間後自動刪除」。對非影像／影片訊息會回 `400`（"The content can not be previewed"）。— [同上](https://developers.line.biz/en/reference/messaging-api/index.html.md)；[Receiving messages 文件](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)（說預覽圖可當縮圖使用）
- [A] Transcoding 端點 `GET .../content/transcoding` 只適用於影片與音訊，狀態值有 `processing`、`succeeded`、`failed`。對影像訊息 ID 呼叫會回 `400`。— [同上](https://developers.line.biz/en/reference/messaging-api/index.html.md)
- [A] Receiving messages 文件原文："Content that users send is automatically deleted after a certain period of time."（同樣沒有天數）。— [Receiving messages](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)
- [A] 影像訊息 webhook 的 `contentProvider.type` 有兩種值。`line` 表示「The image was sent by a LINE user」，二進位要用 Get content 取得。`external` 時，影像 URL 放在 `contentProvider.originalContentUrl`，`previewImageUrl` 也只在 external 時提供，伺服器「isn't provided by LY Corporation」。— [Messaging API reference（Message event／Image）](https://developers.line.biz/en/reference/messaging-api/index.html.md)
- [A] `imageSet` 只在一次同時傳送多張影像時出現。`imageSet.id` 是影像組 ID；`imageSet.index` 從 1 起算；`imageSet.total` 是總張數。原文："The webhooks are delivered in an undefined order, not in the order of the values in imageSet.index." — [同上](https://developers.line.biz/en/reference/messaging-api/index.html.md)
- [A] 速率限制是「per API function (endpoint) on a per-channel basis」。速率表沒有 Get content 的專屬列，兜底的「Other API endpoints」列是 2,000 requests/second。把 2,000 rps 套用到 Get content 是依表格推得，官方沒有直接寫。— [同上（Rate limits 段）](https://developers.line.biz/en/reference/messaging-api/index.html.md)
- [A] 部分端點的網域已從 api.line.me 改為 api-data.line.me（2019-11-08 公告，2020-04-30 前需要更新）。— [LINE Developers News（Messaging API tag）](https://developers.line.biz/en/news/tags/messaging-api)
- 最大檔案大小：Messaging API reference 的 Get content、preview、transcoding 段都**沒有寫大小上限**（未找到可靠證據）。間接資料：LINE 說明中心說相簿原始畫質照片上限是 20 MB、1 億像素，但那是「相簿」功能，不是聊天傳送，也不是 Bot API。— [LINE Help（相簿）](https://help.line.me/line/smartphone/sp?contentId=20000248&lang=en)（[A]，頁面未標示日期，內容來自搜尋摘要）

### Inferences
- 本報告推論：保存天數未公開，而且使用者可以收回訊息（410），所以後端應在收到 webhook 後立即呼叫 Get content，把 bytes 寫進本地儲存。重試只用來處理 202 或暫時性錯誤，不能依賴「之後再抓」。
- 本報告推論：一次傳多張時要用 `imageSet.id + index` 重組；webhook 到達順序不保證，不能用到達順序判斷「第幾張」。
- 本報告推論：分析只用 Get content 的完整檔。preview 官方明說是較小的版本，不應拿來推論。
- 本報告推論：OA 的 webhook 處理正常情況下都是 `line` 類型；遇到 `external` 要另外處理（下載第三方 URL），研究原型可以直接拒收並提示使用者重傳。

### Gaps
- 內容保存的確切天數：官方未公開，未找到可靠證據。坊間傳聞的天數都沒有官方出處，因此不列。
- Get content 的專屬速率上限與單檔大小上限：官方未寫，未找到可靠證據。
- 官方說的 "shrinking" 在什麼條件下發生（尺寸門檻、是否只對「一般畫質」送出的照片）：未找到可靠證據，需要實測。

## Q2. LINE 會不會壓縮或縮小使用者傳的照片？標準／高畫質／原始畫質，以及 OA 收到哪個版本

### Takeaway
會。LINE App 預設以「標準畫質」傳送，長邊約縮到 1,478 px 左右。手動選「高畫質」約 2,365 px；單次勾選「原始畫質（ORIGINAL）」可以保留原始解像度，但檔案大小仍可能變小。OA 收到哪個版本，官方只說「可能被縮小」。實測數字都是 [E] 等級，而且全部是 iPhone，需要在本專案自行用 Bot 實測。

### Cited Findings
- [A] LINE 官方說明中心提到設定路徑「Settings > Photos & videos > Sent photo quality」，可以更改傳送照片畫質。— [LINE Help: I can't send/receive/open photos/videos…](https://help.line.me/line/smartphone/sp?contentId=20000236&lang=en)（頁面未標示日期；搜尋摘要）
- [A] 相簿的原始畫質上傳只限 LYP Premium（日本）／LINE Premium（台灣、泰國）會員。只有未編輯過的照片能以原始畫質上傳，限制為 20 MB、1 億像素。— [LINE Help: Creating/editing albums](https://help.line.me/line/smartphone/sp?contentId=20000248&lang=en)（搜尋摘要；這是相簿，不是聊天）
- [E] 實測一，iPhone XS MAX，原圖 3024×4032、2.54 MB：
  - 標準：1108×1478、283 KB
  - 高畫質：1774×2364、744 KB
  - ORIGINAL：3024×4032、1.9 MB

  — [app-liv.jp](https://app-liv.jp/articles/121899)（最後更新 2025-11-06；查證 2026-10-31）
- [E] 實測二，iPhone 11 Pro Max，原圖 3.7 MB、3024×4032：
  - 高畫質：1.5 MB、1774×2365
  - 標準：604 KB、1109×1479
  - 「原始」選項：10 MB 的圖仍降為 5.3 MB；6–7 MB 的圖則無損送出
  - Android 12（AQUOS sense6）收下來約 349 KB，未給像素
  - 測試版本：iOS LINE 15.2.0、Android LINE 15.1.4
  - PC 版超過 20 MB 即使設為原圖也只會以縮圖送出

  — [appllio.com](https://appllio.com/line-send-original-size-photos)（文章日期 2025-03-02）
- 交叉比對：兩篇獨立 [E] 實測的標準畫質長邊（1478 對 1479）與高畫質長邊（2364 對 2365）幾乎一致，可信度相對較高，但兩篇都只測 iPhone。
- [E] 台灣媒體：手機版預設是「標準畫質」，可以在「照片・影片 › 照片的傳送畫質」改成「高畫質」；電腦版在「設定 › 聊天 › 照片解析度」選「原圖」。— [瘋先生 mrmad（2019-12-28）](https://mrmad.com.tw/line-delivers-high-quality-photos)；也可以在選照片的畫面點「原始畫質」單次送原圖，有文章說是 LINE 9.12.0 之後的功能（搜尋摘要，未逐篇開啟）— [kikinote](https://kikinote.net/161617)、[sogi](https://www.sogi.com.tw/articles/line/6260302)
- [A] OA 端：官方原文 "Content sent by users may be transformed internally, such as shrinking."。沒有說明 Bot 收到的是傳送端選的版本，還是另一次轉檔。— [Messaging API reference](https://developers.line.biz/en/reference/messaging-api/index.html.md)
- [E] 舊版非官方 Perl SDK 的文件說 content 方法取得「original file which was sent by user」。這是舊版、非官方說法，不能作為現行依據。— [LINE-Bot-API 0.03（metacpan）](https://web.hz.metacpan.org/pod/release/YAPPO/LINE-Bot-API-0.03/lib/LINE/Bot/API.pm)

### Inferences
- 本報告推論：一般使用者多半不改預設，所以 OA 收到的照片很可能大多是標準畫質（約 1108×1478 或更小）的重新編碼 JPEG。醫院相機原檔常見 12 MP 以上，兩者在解析度與壓縮程度上有系統性差異（domain shift）。
- 本報告推論：app-liv 實測中，ORIGINAL 的解析度不變但檔案從 2.54 MB 降到 1.9 MB，可能是重新編碼、移除中繼資料，或 HEIC 與 JPEG 換算造成。文章沒說明，無法判定。
- 本報告推論：EfficientNet-B0（常用輸入 224 px）與 DINOv2-small（常用 224 px）最後都會把影像縮到很小，所以「解析度從 4032 降到 1478」對整張圖分類的直接影響可能有限。YOLO 偵測小病灶、以及 Laplacian 模糊分數則會明顯受影響：Laplacian variance 依解析度與 JPEG 平滑而變，同一個門檻不能同時套用在醫院原檔與 LINE 檔上。

### Gaps
- Android 各品牌在標準、高畫質、原始畫質的像素與 JPEG quality 實測：只找到一筆 Android 檔案大小，未找到可靠的像素數據。
- LINE 標準與高畫質使用的 JPEG quality 值（QF）：未找到可靠證據。可以用 JPEG 量化表反推，例如 ImageMagick `identify -verbose` 的 Quality 估計，屬於自行實測。
- Bot 透過 Get content 收到的像素，是否等於傳送端選的畫質：未找到任何公開實測，必須自行測。

## Q3. LINE 內建相機與相簿傳送的差異（壓縮、濾鏡與美顏、HEIC 轉 JPEG）

### Takeaway
沒有找到可靠來源說明 LINE 聊天室內建相機拍照時，是否預設套用美肌、濾鏡，或用不同的壓縮方式。HEIC 的公開資料也只涉及「以檔案方式傳送時原樣傳出」。這一題基本上未找到可靠證據，需要自行實測。

### Cited Findings
- 聊天室內建相機的美顏或濾鏡預設：搜尋只找到 LINE「視訊通話」的美肌、濾鏡功能，不是聊天室相機。— [appllio（視訊通話）](https://appllio.com/line-video-calls-perfect-guide)（[E]）；舊報導談的是另一款獨立 App「LINE Camera」的美顏功能（2013），與聊天室相機無關 — [SoraNews24 2013-12-18](https://soranews24.com/2013/12/18/our-reporter-makes-himself-too-sexy-for-his-face-with-line-cameras-beauty-function/)（[E]）。**未找到可靠證據。**
- [E] 用 LINE「檔案」功能附加 .heic 檔時會原樣傳出、不轉檔；建議先轉成 JPG 或改以一般照片方式傳送。— [fileconv.pages.dev](https://fileconv.pages.dev/en/blog/heic-share-tips)（第三方工具網站，單一來源）
- [E] iPhone 可在「設定 › 相機 › 格式 › 最相容」改為拍 JPG。— [瘋先生 mrmad](https://mrmad.com.tw/?p=49322)
- [A] LINE 官方說明：只有未編輯的照片能以原始畫質上傳到相簿；編輯過的照片無法用原始畫質。— [LINE Help（相簿）](https://help.line.me/line/smartphone/sp?contentId=20000248&lang=en)

### Inferences
- 本報告推論：以「照片」方式（不是「檔案」）送出時，iOS 的 HEIC 很可能由 LINE App 轉成 JPEG，因為標準與高畫質實測的輸出都是重新縮放過的影像。但沒有直接證據，Bot 端應以 magic bytes 判斷格式，不要只看副檔名。
- 本報告推論：如果使用者在 LINE 傳送前的編輯畫面套用濾鏡或亮度調整，會改變紅斑的顏色。發給受試者的拍照指引應明確寫「不要套用濾鏡或編輯」。
- 本報告推論：如果用「檔案」方式傳送，Bot 會收到 file 類型的訊息（webhook 有 file message 類型），bytes 可能比較接近原檔。這點本輪沒有逐字查證 reference，需要確認後才寫進流程。

### Gaps
- 聊天室相機的預設影像處理（美肌、自動濾鏡、銳化）：未找到可靠證據。
- 用照片方式送 HEIC 時是否轉 JPEG、色彩描述檔（Display P3 → sRGB）是否轉換：未找到可靠證據。這一項對紅斑色彩很重要，建議實測。

## Q4. EXIF（GPS、時間、機型、方向）是否被移除？方向如何處理？隱私影響

### Takeaway
沒有 LINE 官方聲明。中文、日文 [E] 文章彼此說法不一，有的說 LINE 會刪位置資訊，有的沒有依據。也沒有任何公開實測針對 Messaging API 收到的檔案檢查 EXIF。設計上必須假設「可能保留，也可能移除」，Bot 端要自行檢查並主動清除 GPS。

### Cited Findings
- [E] 一篇台灣文章說 LINE 上傳照片時「不會帶太多照片資訊」，沒有原始拍攝日期和地點。另一篇說不必擔心 LINE、Messenger、iMessage 洩漏 EXIF 定位，但沒有說明依據。兩者都不是官方說法。— 搜尋摘要來源：[koc.com.tw](https://koc.com.tw/archives/408817)、[applealmond](https://applealmond.com/posts/127361)（兩者 [E]，未逐篇開啟）
- [E] dime.jp 說用 LINE 在聊天室傳照片時，LINE 會刪除位置資訊。這指的是 App 對 App，不能直接推到 Messaging API。— [dime.jp](https://dime.jp/genre/1974458/)（搜尋摘要）
- [E] 提醒：即使刪除位置資訊，EXIF 內的縮圖仍可能殘留修改前的影像。— [livedoor news](https://news.livedoor.com/article/detail/9171934/)（舊文，搜尋摘要）
- 方向（Orientation tag 與實際旋轉像素）：**未找到可靠證據**。
- 官方聲明：在 help.line.me 與 developers.line.biz 都**未找到**說明 EXIF 處理方式的頁面。

### Inferences
- 本報告推論：標準與高畫質會重新縮放、重新編碼，常見實作在重編碼時會丟掉 EXIF，並把方向「烙進」像素。但 ORIGINAL 選項可能保留 EXIF，包括 GPS。兩條路徑的行為可能不同。
- 本報告推論：隱私方面，研究原型應在存檔流程中做兩件事：(a) 保留原始 bytes 的雜湊（作為稽核證據）；(b) 另存一份移除 GPS 的工作副本，只記錄必要欄位（拍攝時間、機型、Orientation、寬高）。原始 bytes 若可能含 GPS，應依 IRB 或資料管理計畫加密，並限制存取。
- 本報告推論：讀圖時一律先做 `ImageOps.exif_transpose`（Pillow），並記錄是否有套用旋轉。否則同一張照片在醫院資料與 LINE 資料中，方向可能不一致；YOLO 的框座標也會錯位。

### Gaps
- 標準、高畫質、ORIGINAL × iOS／Android 下，Bot 收到的檔案是否保留 GPS、DateTimeOriginal、Make／Model、Orientation：沒有任何公開實測。建議用含 GPS 的測試照（在無病人的環境下拍）實測矩陣。

## Q5. 對模型表現的影響：JPEG 壓縮、縮小、色偏與白平衡、手機相機差異（含反證）

### Takeaway
研究證據顯示：一般 CNN 對中等程度的 JPEG 壓縮相對穩健，但對模糊與雜訊敏感；白平衡造成的色偏會明顯降低 DNN 表現；皮膚科模型在旋轉、亮度、對比這類簡單變換下，有 6.5–22% 的病灶預測會翻轉；同一次就診補拍的照片，預測也不穩定。沒有找到專門研究「LINE／WhatsApp 傳送後的臨床照片」對 AI 影響的同儕審查論文，也沒有找到以照片分類靜脈炎的已發表模型（只有臨床試驗登錄）。

### Cited Findings
- [C] Young et al., npj Digital Medicine 2021;4:10, DOI 10.1038/s41746-020-00380-6：
  - 模型：SE-ResNet-50 ensemble。
  - 測試資料：7 組，其中 5 組刻意來自與訓練資料不同的情境（外部驗證）。
  - 變換：旋轉、亮度、對比、水平翻轉。結果翻轉的病灶比例為 6.5–22%；VAMC-T 為 16/101（15.8%）。
  - 同一次就診從不同角度、倍率補拍的照片：24/79（30%）預測不一致。
  - Test-time augmentation 沒有改善 AUROC。
  - 沒有測 JPEG 或模糊，也沒有測不同手機。文中未說明是否以病人為單位切分。

  — [PMC7820258](https://pmc.ncbi.nlm.nih.gov/articles/PMC7820258/)
- [C／會議] Dodge & Karam, QoMEX 2016（arXiv:1604.04004）：4 個影像分類 DNN 在模糊、雜訊、對比、JPEG、JPEG2000 下的表現。對模糊與雜訊特別敏感，對一般品質範圍的 JPEG 與對比變化相對穩健。這是 ImageNet 自然影像，不是醫學影像。— [arXiv 1604.04004](https://arxiv.org/abs/1604.04004)
- [B／頂會] Afifi & Brown, ICCV 2019（arXiv:1912.06960）：相機白平衡（computational color constancy）錯誤造成的整體色偏會降低分類與分割 DNN 的表現；一般的 color augmentation 無法模擬這種誤差。作者提出 WB emulation 增強，以及 WB 校正前處理，在 CIFAR-10/100、ADE20K 有改善。程式碼公開在 WB_color_augmenter。— [CVF Open Access](https://openaccess.thecvf.com/content_ICCV_2019/html/Afifi_What_Else_Can_Fool_Deep_Learning_Addressing_Color_Constancy_Errors_ICCV_2019_paper.html)
- [C] 反證與範圍：數位病理研究指出，以未壓縮高品質影像訓練的 CNN，在壓縮比 24:1 以內仍穩健；用低品質影像訓練，能改善相同壓縮程度下的表現。— [PMC7113072](https://pmc.ncbi.nlm.nih.gov/articles/PMC7113072/)。另有 SPIE JMI 2019 研究 JPEG 2000 壓縮對 CNN 的影響 — [DOI 10.1117/1.JMI.6.2.027501](https://www.spiedigitallibrary.org/journals/Journal-of-Medical-Imaging/volume-6/issue-02/027501/Impact-of-JPEG-2000-compression-on-deep-convolutional-neural-networks/10.1117/1.JMI.6.2.027501.full)（只看了搜尋摘要）。
- [C／workshop] 反方向證據：MICCAI 2022 workshop 研究發現，訓練與推論時特定的 JPEG 品質因子組合會對病理分類產生不利影響。— [TUM portal](https://portal.fis.tum.de/en/publications/deep-learning-on-lossily-compressed-pathology-images-adverse-effe/)（搜尋摘要）
- [C] 皮膚影像壓縮：一篇 2024 IEEE 會議論文以 Five Modulus Method（不是 JPEG）壓縮 HAM10000 皮膚鏡影像，原圖與壓縮圖的準確度差異很小。— [Amrita 出版頁](https://www.amrita.edu/publication/classification-of-skin-lesions-using-five-modulus-method-for-image-compression/)（搜尋摘要；壓縮法不同，外推有限）
- [C] 遠距皮膚科中，病人自拍照片的品質：
  - Duke 調查（JAMA Dermatology 2022）：皮膚科醫師認為病人照片「有助決策」的比例是 55.1%，「品質足夠」是 62.2%；文中引述既往研究，品質不良率約 10–40%。
  - 另一項 e-visit 研究：91.2% 的照片品質足夠；照片不佳的主因是失焦或模糊（不佳照片中有 60%，合格照片中只有 7.8%）。

  — 搜尋摘要來源：[aminer 條目](https://aminer.org/pub/62ff697890e50fcafd3c3afd/quality-and-perceived-usefulness-of-patient-submitted-store-and-forward-teledermatology-images)、[eScholarship PDF](https://escholarship.org/content/qt1vs9c5n5/qt1vs9c5n5.pdf)、[JMIR Dermatology 2022 e37517](https://derma.jmir.org/2022/3/e37517/)（未逐篇開全文，數字以摘要為準）
- [C] 奧地利前瞻研究（263 名病人）：手機拍攝照片的品質與診斷正確性顯著相關。— [FH OÖ](https://pure.fh-ooe.at/en/publications/a-prospective-study-of-mobile-phones-for-dermatology-in-a-clinica/)（搜尋摘要）
- [D] 皮膚鏡影像訓練的模型直接測手機照片（PAD-UFES-20）時準確度大幅下降，作者歸因於成像設備、族群與拍攝流程等 domain shift；用在地資料微調能改善。— [arXiv 2606.03214](https://arxiv.org/pdf/2606.03214)、[arXiv 2602.19857](https://arxiv.org/html/2602.19857v1)、[DermAI arXiv 2511.10367](https://arxiv.org/pdf/2511.10367)（預印本，只看了搜尋摘要）
- [D] 一篇痤瘡 AI 預印本引述：iOS 與 Android 的色彩呈現流程不同，皮膚科醫師之間的判讀一致性也隨之不同；作者主張外部驗證應依裝置分層。— [arXiv 2607.26461](https://arxiv.org/pdf/2607.26461)（預印本，二手引述）
- WhatsApp／通訊軟體傳送後的臨床影像診斷品質：只找到南非 WhatsApp 皮膚科使用研究，以及「2018 年回顧只找到 3 篇」的說法；**沒有找到直接量化壓縮對 AI 影響的研究**。— [JMIR mHealth 2021;9(7):e26149](https://mhealth.jmir.org/2021/7/e26149)（搜尋摘要）
- 靜脈炎照片 AI：只找到一項臨床試驗登錄，用手機即時拍攝、以 VIP score ≥2 定義靜脈炎、訓練深度學習模型，尚無結果。— [ClinicalTrials.gov NCT07889895](https://clinicaltrials.gov/study/NCT07889895)（[A] 登錄資料，不是結果）。其他已發表的相關研究用的是超音波或臨床變項，不是照片 — [PMC11295139](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11295139/)
- 資料洩漏與切分：Young 2021 文中未說明是否以病人為單位切分。其他預印本只看了摘要，無法確認。

### Inferences
- 本報告推論：本專案的風險排序大致如下：
  1. 色偏與白平衡（紅斑判讀的核心特徵；有 ICCV 證據，而且 iOS 與 Android 色彩流程不同）
  2. 模糊（文獻一致顯示敏感；遠距皮膚科最常見的不良原因）
  3. 解析度下降（主要影響 YOLO 小目標與 Laplacian 門檻）
  4. JPEG 量化（在 224 px 分類器上，影響可能最小）
- 本報告推論：現有資料約 120 張、14 名病人。即使以病人為單位切分，每個 fold 的病人數也很少；「依來源（醫院或 LINE）分層」的評估幾乎沒有統計檢定力，任何來源間差異都可能是病人差異或期別分布差異造成，混雜無法排除。目前只適合做描述性比較，以及「同一張照片 → 模擬 LINE 壓縮 → 看預測是否翻轉」的穩健性壓力測試（仿 Young 2021），不適合下「LINE 照片表現較差」的結論。
- 本報告推論：未來約 1,000 張、類別平衡時，可以做：
  - 依來源與裝置（iOS 或 Android）分層的 AUROC 與 calibration，附信賴區間；
  - leave-source-out 驗證；
  - 前提是病人層級切分，且同一病人不同時間點的照片必須在同一側，避免洩漏。

### Gaps
- 直接研究「LINE 或 WhatsApp 傳送 → 皮膚或傷口 AI 表現」的同儕審查論文：未找到可靠證據。
- 以 JPEG QF 系統性測試皮膚臨床照片（非皮膚鏡）分類器的研究：未找到可靠證據（只有病理、自然影像，以及非 JPEG 壓縮的研究）。
- 紅斑或靜脈炎分期對色彩誤差的敏感度：未找到可靠證據。

## Q6. 建議：保存原始 bytes 與雜湊、記錄來源、依來源評估、模擬 LINE 壓縮做增強、色卡與拍照指引

### Takeaway
業界慣例與官方 API 特性都支持「收到就存、原樣存、記錄 metadata」。用模擬 LINE 壓縮做訓練增強屬於本報告推論，有間接證據支持（低品質訓練有助同品質推論；WB 增強有效），但沒有本領域的直接證據。色卡校正在傷口攝影已有技術層面的證據（色差降低），但沒有找到證明它能提升紅斑分級正確性的臨床試驗。

### Cited Findings
- [A] 內容會自動刪除、使用者可以收回（410）、可能被縮小，因此後端必須立即保存。— [Messaging API reference](https://developers.line.biz/en/reference/messaging-api/index.html.md)
- [C] 用低品質（壓縮）影像訓練，可以提升相同壓縮程度下的表現。— [PMC7113072](https://pmc.ncbi.nlm.nih.gov/articles/PMC7113072/)；但也有特定 QF 組合造成不利影響的反例 — [TUM portal](https://portal.fis.tum.de/en/publications/deep-learning-on-lossily-compressed-pathology-images-adverse-effe/)
- [B] WB emulation 增強，以及 WB 前處理，可以降低色偏造成的性能損失（自然影像）。— [Afifi & Brown ICCV 2019](https://openaccess.thecvf.com/content_ICCV_2019/html/Afifi_What_Else_Can_Fool_Deep_Learning_Addressing_Color_Constancy_Errors_ICCV_2019_paper.html)
- [C] 傷口攝影色卡校正：
  - SPIE 2015（Deserno 團隊）用 24 色塊參考卡，以 35 個角點做幾何校正，並做非線性 RGB 色彩校正。
  - SPIE 2017 測試 gamma、白平衡、卡片色彩校正，比較校正前後色塊數值的變異。
  - 2014 年鈣化防禦症（calciphylaxis）研究用卡片做尺度正規化，並做 affine 色彩轉換。

  — [SPIE 2015 DOI 10.1117/12.2081809](https://photonicsforenergy.spiedigitallibrary.org/conference-proceedings-of-spie/9414/94143J/Human-wound-photogrammetry-with-low-cost-hardware-based-on-automatic/10.1117/12.2081809.full)、[SPIE 2017 DOI 10.1117/12.2254721](https://www.spiedigitallibrary.org/conference-proceedings-of-spie/10136/1013617/Colorimetric-calibration-of-wound-photography-with-off-the-shelf-devices/10.1117/12.2254721.full)、[TUM portal](https://portal.fis.tum.de/en/publications/towards-quantitative-assessment-of-calciphylaxis/)（搜尋摘要）
- [E／利益衝突] 2026-05 的 WCCC Tools Work Group 回顧〈The importance of accurate color in wound photography and data〉，新聞稿來自販售校正卡的廠商 TRUE-See；全文未取得。— [HMP Global](https://www.hmpgloballearningnetwork.com/site/wounds/literature-review/importance-accurate-color-wound-photography-and-data)
- [C] 拍照回饋機制可以提升居家傷口 App 的照片品質；失焦是遠距皮膚科最常見的不良原因。— [PMC9223770](https://pmc.ncbi.nlm.nih.gov/articles/PMC9223770)、[eScholarship](https://escholarship.org/content/qt1vs9c5n5/qt1vs9c5n5.pdf)（搜尋摘要）

### Inferences
本節內容都是本報告推論，第 7 點另有說明。

1. **存檔（業界慣例＋官方 API 特性）**：收到 webhook 後立刻呼叫 Get content，把 bytes 原樣寫檔，不要先用 PIL 重存。同時記錄以下欄位：
   - 雜湊：SHA-256。
   - 訊息與來源識別：`messageId`、`imageSet.id/index/total`、`contentProvider.type`、webhook timestamp、user ID（雜湊化）。
   - 檔案特性：magic bytes 判定的格式、寬高、檔案大小、JPEG 量化表估計的 QF、EXIF 是否存在、Orientation 值、是否含 GPS（布林值，不存座標）。
   - 來源標記：`source_channel`（hospital_camera／line_oa／line_file）。
2. **工作副本**：另存一份 exif_transpose 後、移除 GPS 的工作影像，模型只讀工作副本。
3. **依來源評估**：每次評估都另外輸出依 `source_channel` 分層的指標。小資料階段（約 120 張、14 人）只做描述與壓力測試；約 1,000 張時才做分層 AUROC、CI 與 leave-source-out。
4. **LINE 退化增強**：先用 Bot 實測 iOS、Android × 標準、高畫質、原始的實際像素與 QF，再把醫院原檔「縮到長邊約 1478 或約 2365 px，並以實測 QF 重新編碼」，作為訓練增強與測試時的壓力測試。數字以本專案實測為準；[E] 的 1108×1478 和 1774×2364 只作為初始值。
5. **品質檢查門檻分來源**：Laplacian variance 先 resize 到固定長邊再計算，避免 LINE 標準畫質（約 1478 px）與醫院原檔（約 4032 px）分數不可比。
6. **色彩**：
   - 訓練時加 WB emulation 增強（Afifi 的 WB_color_augmenter，或簡單的色溫與 tint 抖動）；
   - 拍照指引寫明自然光或白光、不用閃光燈、不用濾鏡、不編輯、對焦後再拍；
   - 未來若要以顏色量化紅斑，可以考慮在畫面中放小型灰卡或色卡，並在推論前做卡片色彩校正。小資料階段建議先只做 WB 增強，不依賴色卡，因為受試者依從性與卡片偵測失敗會增加新的雜訊源。
7. **拍照引導文字**（業界慣例＋遠距皮膚科證據）：建議使用者在選照片時勾選「原始畫質」。但是否確實影響 Bot 收到的檔案，必須先實測。若 Bot 收到的仍是縮圖，就不要增加使用者負擔。

### Gaps
- 色卡是否能提升紅斑或靜脈炎分級的一致性或 AI 正確率：未找到可靠證據（只有色差技術指標與廠商宣稱）。
- 「模擬 LINE 壓縮增強」能否改善 LINE 來源照片的表現：未找到本領域直接證據，屬於推論，需要以未來約 1,000 張資料驗證。
