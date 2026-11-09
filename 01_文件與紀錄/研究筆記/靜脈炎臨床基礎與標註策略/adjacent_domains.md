# 鄰近領域影像 AI 對靜脈炎照片分級專案的借鏡（紅斑量化、蜂窩性組織炎、壓傷分級、SSI 遠端照片、傷口分割、小資料教訓）

> 存取日期：所有連結皆於 2026-10-30 存取／搜尋。
> 來源分級：[A] 官方/標準；[B] 系統性回顧/統合分析/頂級期刊；[C] 一般同儕審查；[D] 預印本/學位論文；[E] 部落格/程式碼/新聞稿（僅作輔助）。
> 結論標記：**研究證據顯示** / **業界慣例** / **本報告推論**。
> 方法：第一輪概覽搜尋，第二輪回到原始論文（PMC 全文、期刊頁、模型卡、GitHub）核對樣本數、切分、外部驗證與數值。凡只看到摘要或搜尋摘要片段者，皆明確註明「僅摘要」或「僅搜尋片段」。每個 AI 研究都標註「病人層級切分？／外部驗證？」。
> 專案背景：台灣研究原型（非診斷），醫院與民眾以 LINE 傳照片；14 位病人約 120 張、3 類分級；未來約 1,000 張；僅限本機運算（單張消費級 NVIDIA GPU）；只允許匯入 safetensors 權重並在本機重新完整評估；不自動訓練/部署。

---

## Q1. 從 RGB 照片量化紅斑（erythema index、CIELAB a*、比色法）與深度學習的比較；和臨床人員的可靠度

### Takeaway
CIELAB a* 這類比色指標**觀察者之間重現性高**，但**和臨床評分的相關性偏弱**（rosacea 研究 Rs=0.37）。而且只有在拍攝條件標準化時才有意義。目前沒有找到「a* 對上深度學習、以臨床醫師為參考標準」的正面比較研究。紅斑本身就是臨床人員在照片上**最不一致**的特徵之一（見 Q4 的 Wiseman 研究）。

### Cited Findings
- [C] Logger et al. 2020（Skin Res Technol 26:804–812，DOI 10.1111/srt.12878）：21 位 rosacea 病人接受 ivermectin 治療 16 週，以 ImageJ 在照片上量 CIELAB a*。觀察者間相關 R²=0.82；病灶 a* 和臨床評分只有弱相關（Rs=0.37）；病灶 a* 在第 16、28 週顯著下降（P<.05）。red/green ratio 則沒有顯著變化。作者建議用病灶 a* 追蹤紅斑。（僅摘要與搜尋片段，未開全文）— [Zendy 書目頁](https://zendy.io/title/10.1111/srt.12878)；[PMC7754330 PDF 鏡像](https://rcastoragev2.blob.core.windows.net/3fcd45ea8630a379079beead5d132e7c/PMC7754330.pdf)
- [C] 同組全文指出：RGB 反映外觀但沒有校正亮度，CIELAB 的優點是能校正亮度變異（僅搜尋片段）— [PMC7754330 PDF 鏡像](https://rcastoragev2.blob.core.windows.net/3fcd45ea8630a379079beead5d132e7c/PMC7754330.pdf)
- [C] Dall'Oglio et al.（Skin Res Technol）：8 位皮膚科醫師評 100 張 rosacea 影像。標準照片對紅斑/微血管擴張的一致性只有 poor–fair；改用「erythema-directed digital photography」後提升到 moderate–good（僅搜尋片段）— [irosacea 轉載 PubMed RSS](https://irosacea.org/forums/topic/14609-pubmed-rss-feed-inter-observer-evaluation-of-erythema-directed-photography-for-the-assessment-of-erythema-and-telangiectasias-in-rosacea/)；[Wiley 摘要（代理連結）](https://onlinelibrary-wiley-com-443.webvpn.zafu.edu.cn/doi/abs/10.1111/srt.12979)
- [C] Frew et al. 2021：醫師對紅斑的目視分級在不同膚色間不可靠，評分者間信度只有 moderate；電腦輔助的 EQscore 和臨床評分一致，且信度較高（僅搜尋片段，未核對數值）— [Peeref](https://peeref.com/works/20746780)
- 研究證據顯示：比色指標的重現性高於人眼，但「和臨床判斷一致」的證據弱。標準化攝影（固定光源、偏振、色卡）是提升一致性的前提。

### Inferences
- 本報告推論：LINE 會重新壓縮 JPEG，民眾的手機還會自動白平衡/HDR/美顏，畫面裡也沒有色卡。在這種條件下，a* 的絕對值不可比；就算要用，也只適合同一張照片內的**相對值**（病灶區 a* 減去同臂遠端正常皮膚 a*，即 Δa*）。這和 Logger 的「lesional vs non-lesional」設計一致。
- 本報告推論：在 14 位病人的資料上，Δa* 可以當作**可解釋的基線特徵**，或附加在 DINOv2/EfficientNet embedding 後面送進 logistic regression。它也能做「標註一致性 sanity check」：如果標成第 2 級的照片 Δa* 反而比第 0 級低，就提示標註或拍攝有問題。不建議把 a* 單獨當分級器。
- 本報告推論：未來收約 1,000 張時，醫院端照片建議放一張色卡/灰卡（可以和比例尺貼紙合一）。這樣才能做色彩校正，讓 a* 可比；但要注意 Q6 的「標記物捷徑」風險。

### Gaps
- 未找到可靠證據：以 RGB 手機照片比較「a*/erythema index」和「深度學習」對發炎分級、並以臨床醫師為參考標準的正面對決研究。
- 未找到可靠證據：在 LINE 等通訊軟體重壓縮後 a* 的誤差量化。
- Frew 2021 EQscore 的具體 ICC 數值未核對。

---

## Q2. 蜂窩性組織炎 vs 偽蜂窩性組織炎：照片 AI 與熱影像

### Takeaway
這個領域**實證最紮實的是熱影像，而不是 RGB 深度學習**。Ko 2018（JID，不是 JAMA Derm）先建立模型；Pulia 2024（JAMA Derm）做前瞻驗證，204 人、FLIR ONE Pro、最高溫 ≥31.2°C，敏感度 93.5%，但特異度只有 38.4%。我**沒有找到**以 RGB 臨床照片做 cellulitis vs pseudocellulitis 深度學習的可靠同儕審查研究；任務指示提到的「Cho et al.」與「Stanford pseudocellulitis AI」也都**未找到可靠證據**。

### Cited Findings
- 更正：Ko et al. 2018 的熱影像研究刊在 **J Invest Dermatol 2018;138(3):520–526（DOI 10.1016/j.jid.2017.09.022）**，題名 "Skin Surface Temperatures Measured by Thermal Imaging Aid in the Diagnosis of Cellulitis"。同年的 JAMA Dermatol 2018;154(5):529–536 是另一篇 RCT，主題是「皮膚科會診對疑似 cellulitis 的影響」，與熱影像無關 — [Duke Scholars 書目](https://scholars.duke.edu/publication/1590510)；[Harvard DASH](https://dash.harvard.edu/entities/publication/73120379-4adf-6bd4-e053-0100007fdf3b)
- [C] Ko 2018 JID：病人隨機分到皮膚科會診組（n=40）或標準照護組（n=32）；以會診組建立預測模型，再在另一組驗證；會診組有 28% 被改診斷為 pseudocellulitis（僅搜尋片段）— [Duke Scholars](https://scholars.duke.edu/publication/1590510)
- 數值衝突：搜尋摘要寫 Ko 2018 患側/健側溫差在 cellulitis 為 3.7°C、pseudocellulitis 為 0.2°C（p=0.002）；Pulia 2024 引述 Ko 時寫的是「最高溫平均差 2.6 (2.7)°C」，並說明 Ko 用的是溫度梯度而非最高溫當切點。兩者可能是不同指標，未開 Ko 全文無法裁定 — [JAMA Derm Pulia 2024](https://jamanetwork.com/journals/jamadermatology/fullarticle/2816455)
- [B] Pulia et al., JAMA Dermatol 2024;160(5):511–517（已開全文頁）：
  - 前瞻診斷驗證，依 STARD 報告；單一急診（美國中西部四級醫院），2018/10–2020/03；便利取樣。
  - n=204：cellulitis 92（45.1%）、pseudocellulitis 112。熱影像用 FLIR ONE Pro（手機外接）在約 30 cm 拍攝。
  - 患肢最高溫 ≥31.2°C：Se 93.5%、Sp 38.4%、PPV 55.5%、NPV 87.8%、C-index 0.72。ALT-70（n=175）：Se 98.8%、Sp 22.0%、C-index 0.65。兩者都陽性才算陽性：Se 91.7%、Sp 53.9%。
  - 參考標準：沒有切片/培養金標準，由 6 位醫師（急診/感染/皮膚各 2）多數決；首輪共識 187/204（91.7%），17 例沒有共識，其中 3 例以主治急診醫師診斷當 tie-breaker，未報告 kappa。
  - 限制：單中心、88.2% 白人、切點只做內部交叉驗證、**無外部驗證**。
  - 病人層級切分：每人一筆，不涉及多張照片洩漏；外部驗證：無。
  - — [JAMA Dermatology 全文頁](https://jamanetwork.com/journals/jamadermatology/fullarticle/2816455)
- [D] 與 RGB 照片最接近的是 erythema migrans 深度學習研究，鑑別診斷含 cellulitis、tinea、zoster；臨床影像敏感度 88.55%（僅搜尋片段，arXiv，未核對切分）— [arXiv 2402.15566](https://www.arxiv.org/pdf/2402.15566)
- [C] 非照片：point-of-care 超音波深度學習分類正常/cellulitis/膿瘍的先導研究（僅搜尋片段）— [Frontiers in Medicine 2023](https://www.frontiersin.org/journals/medicine/articles/10.3389/fmed.2023.1162124/epub)
- 研究證據顯示：「發紅+腫」這類外觀線索本身不足以區分感染性和非感染性發炎，所以熱影像研究要靠溫度差，臨床上也需要多位專家共識當參考標準；即使如此，首輪仍有約 8% 案例沒有共識。

### Inferences
- 本報告推論：靜脈炎同樣以紅、腫、熱、痛分級，而 RGB 照片只捕捉得到「紅」和部分「腫」，熱與痛都看不到。所以照片模型的上限受到「照片可見資訊」限制。研究原型應明說：模型預測的是「照片上可見的分級特徵」，不是完整的臨床分級。
- 本報告推論：Pulia 的參考標準做法（多專科小組多數決、記錄無共識案例、tie-breaker 規則）可以直接移植到 120 張照片的標註流程，例如 2–3 位護理師/醫師獨立標註、記錄一致率、無共識案例另外處理。
- 本報告推論：手機外接熱像儀（如 FLIR ONE Pro）在醫院端可列為未來研究選項。它能在本機擷取，不需要雲端；但民眾端 LINE 照片拿不到熱影像。

### Gaps
- 未找到可靠證據：RGB 臨床照片做 cellulitis vs pseudocellulitis 深度學習的同儕審查論文；「Cho et al.」和「Stanford pseudocellulitis AI」都無法確認存在。
- Ko 2018 的敏感度/特異度數值未取得全文核對。

---

## Q3. 壓傷（pressure injury）分級 AI；臨床人員看照片 vs 床邊的一致性

### Takeaway
壓傷分級 CNN 的內部準確率約 0.79–0.93，但**外部測試會下降**（Kim 2023：0.793 → 0.717）。臨床人員看照片 vs 床邊分級的一致性只有 fair–moderate（κ≈0.39–0.58），**第 1 期（只有紅斑、皮膚完整）最差**。這和靜脈炎低分級「只有紅」的情境高度類比。

### Cited Findings
- [C] Kim J, Lee C, Choi S, et al. "Augmented decision-making in wound care…" Int J Med Inform 2023;180:105266（DOI 10.1016/j.ijmedinf.2023.105266）：
  - 3,098 張臨床影像（內部 2,614、外部 484），分類壓傷與相關皮膚病。
  - top-1 accuracy 內部 0.793（95% CI 0.778–0.808）、外部 0.717（0.676–0.758）。
  - 24 位讀者（皮膚科住院醫師、病房護理師、醫學生）在 CNN 輔助下準確率從 0.501 提升到 0.672，Fleiss κ 從 0.414 提升到 0.641。
  - 病人層級切分：摘要未說明（未開全文）；外部驗證：有（獨立外部資料集）。
  - — [Yonsei 典藏](https://ir.ymlib.yonsei.ac.kr/handle/22282913/196758)；[PubMed 37866277](https://pubmed.ncbi.nlm.nih.gov/37866277)
- [C] Lei et al., JMIR Med Inform 2025（e62774）：821 張、6 類（含 unstageable、suspected DTI），比較 AlexNet/VGG16/GoogLeNet/ResNet18，ResNet18 accuracy 0.9333。同組另有 7,677 張「增強後」資料集的版本，DenseNet121 為 93.71%。病人層級切分與外部驗證都未確認（僅搜尋片段）；資料是在增強後才切分還是切分後才增強，無法確認。— [JMIR Med Inform](https://medinform.jmir.org/2025/1/e62774)
- [C] Mask R-CNN 壓傷分期與組織分割研究（PubMed 38683775）：100 張測試集，stage recognition AP 0.603，作者稱優於包含造口治療師在內的醫護人員。PubMed 頁面因 cookie 限制無法開啟，數值僅來自搜尋片段；切分與外部驗證都未確認。— [PubMed 38683775](https://www.pubmed.gov/38683775/)
- [C] 床邊 vs 照片：多中心 100 個壓瘡，認證傷口護理師在床邊評，三人專家小組看數位照片評；分期一致性 κ=0.39–0.58。DTI 與 unstageable 一致性最高，**stage 1 最低**（JWOCN 2013;40(2):150–156，DOI 10.1097/WON.0b013e31828093a4；僅會議講義與搜尋片段）— [NDNQI 會議講義 PDF](https://ana.confex.com/ana/ndnqi12/webprogram/Handout/Paper7154/Wound_Photography_Study.pdf)；[會議摘要頁](https://ana.confex.com/ana/ndnqi12/webprogram/Paper7154.html)
- [D] UNLV 學位論文：床邊護理師和傷口專家（照片＋病史）分期 κ=0.460，54% 不一致 — [UNLV Digital Scholarship](https://digitalscholarship.unlv.edu/thesesdissertations/2928)
- [C] 土耳其研究：694 張照片，只比較照片評分者之間（不同能力層級），κ≈0.84–0.94。這是 photo-vs-photo，不能和 bedside-vs-photo 直接比較（僅搜尋片段）— [Koç University 典藏](https://research.hub.ku.edu.tr/entities/publication/246d8618-e5e5-45d8-b0dc-fc60f30c90f6/full)
- 研究證據顯示：同一批照片讓不同評分者看，一致性可以很高；但「照片 vs 床邊」只有中等。照片遺失的資訊（觸診、溫度、按壓變白）是主因，而且以紅斑為主的低分期最受影響。

### Inferences
- 本報告推論：靜脈炎 3 類中，「0 級 vs 1 級」的邊界類似壓傷 stage 1：主要靠紅斑，還可能涉及觸診與疼痛。可以預期這是**標註雜訊最大、模型也最難分**的邊界。建議在標註表中記錄「此判斷是否依賴床邊資訊（痛、硬、熱、條索）」，並另外計算「僅看照片」標註和「床邊臨床分級」的一致性。
- 本報告推論：Kim 2023 用約 3,000 張影像，外部測試約下降 8 個百分點。專案在 1,000 張時也應預期跨來源（醫院 vs LINE 民眾）會明顯掉分，所以要依來源分層報告。
- 本報告推論：Lei 2025 那類「增強後 7,677 張、準確率 93%」的結果要特別小心：如果增強在切分前完成，同一張原圖的變體會同時出現在訓練與測試集，等同洩漏。專案的增強必須在病人層級切分**之後**、只套用在訓練折上。

### Gaps
- 任務指示提到的台灣/日本壓傷分級 AI 研究，本次沒有找到可核對的原始論文（有一筆 NTHU 會議論文連結，未開啟）。
- Kim 2023 是否為病人層級切分、外部資料來源，未取得全文。
- 未找到 NPIAP 2016 分期定義下照片 vs 床邊一致性的新研究（2013 研究使用 NPUAP 分期）。

---

## Q4. 病人自拍手機照片偵測手術部位感染（SSI）：臨床人員遠端判讀一致性與 AI 結果

### Takeaway
**研究證據顯示**：(1) 臨床人員看照片判斷「發紅」的一致性很差（Gwet's AC 0.27–0.34），判斷裂開、壞死則很好（0.85–0.93）；(2) 遠端照片流程（TWIST RCT）能讓 SSI 較早在 7 天內被診斷，但主要結局（診斷時間）沒有顯著差異；(3) 目前最大的 AI 研究（Mayo，約 20,000 張、6,000+ 位病人）用兩階段管線（先找切口、再判感染），感染 AUC 約 0.81–0.83，需要非常大的資料量才達到中等表現。

### Cited Findings
- [C] Wiseman JT, Fernandes-Taylor S, et al. J Vasc Surg Venous Lymphat Disord 2016;4(3):320–8（PMID 27318052；**已開 PMC 全文**）：
  - 80 個血管外科術後傷口；180 筆床邊評估、720 筆照片評估（9 位評分者 × 80 張）；照片分 34 張品質差、46 張品質佳。
  - 評分者間 Gwet's AC（床邊 / 照片品質差 / 照片品質佳）：
    - **發紅**：0.44 / 0.27 / 0.34
    - 瘀斑：0.56 / 0.52 / 0.49
    - cellulitis：0.68 / 0.83 / 0.67
    - 滲液：0.76 / 0.58 / 0.41
    - 裂開：0.86 / 0.90 / 0.88
    - 壞死：0.93 / 0.88 / 0.85
  - 照片 vs 床邊：發紅 Se 61%、Sp 75–81%，跨模式 AC 0.27；cellulitis Se 50–63%、Sp 63–83%，跨模式 AC 0.32。
  - 照片品質好壞對一致性影響不大。作者把照片判讀敏感度低歸因於「單張照片」的限制。
  - — [PMC4913032](https://pmc.ncbi.nlm.nih.gov/articles/PMC4913032)
- [B] McLean KA, et al.（TWIST Collaborators）"Remote diagnosis of surgical-site infection using a mobile digital intervention: a randomised controlled trial in emergency surgery patients", npj Digit Med 2021;4 (DOI 10.1038/s41746-021-00526-0)：
  - 492 位急診腹部手術病人（智慧型手機組 223、常規組 269），術後第 3、7、15 天上傳傷口照片並回答症狀問卷，由外科團隊人工判讀。
  - 主要結局（SSI 診斷時間）無顯著差異；7 天內被診斷的勝算 OR 3.7（95% CI 1.02–13.51，p=0.043）；30 天 SSI 率 9.4% vs 7.4%（無差異）；社區就醫次數減少。
  - 不是 AI 研究，是人工遠端判讀（僅摘要）。
  - — [Univ. of Edinburgh Research Explorer](https://www.research.ed.ac.uk/en/publications/remote-diagnosis-of-surgical-site-infection-using-a-mobile-digita/)；[DOAJ](https://doaj.org/article/ac3ff51ec06c40639ad19df305de1632)
- [B] Muaddi H, et al. "Imaging Based Surgical Site Infection Detection Using Artificial Intelligence", Ann Surg 2025（DOI 10.1097/sla.0000000000006826）：
  - 9 家 Mayo 醫院，>20,000 張病人經入口網站上傳的照片、>6,000 位病人。
  - 兩階段：判斷「是否為切口」，再判斷「是否感染」；比較 ViT、ResNet50、MobileNetV4、U-Net，ViT 最佳。
  - 切口辨識 accuracy 94%；感染 AUC 0.81（新聞稿）／端到端 AUC 0.83（ASA 年會摘要）；感染偵測 accuracy 0.78±0.01、recall 0.60±0.03、F1 0.73±0.03。
  - 作者稱跨族群表現一致，但沒有獨立驗證；前瞻研究進行中。
  - **未開全文**，數值來自新聞稿與會議摘要，兩者 AUC 不一致。病人層級切分：未確認；外部驗證：未確認（多院資料，是否做 hospital-held-out 未知）。
  - — [Mayo Clinic 專業人員新聞](https://www.mayoclinic.org/medical-professionals/surgery/news/ai-powered-imaging-tool-enhances-detection-of-surgical-site-infections/mac-20587160) [E]；[ASA 2025 會議摘要](https://meeting.americansurgical.org/program/2025/12.cgi) [D]；[Hospimedica](https://www.hospimedica.com/surgical-techniques/articles/294805977/ai-tool-detects-surgical-site-infections-from-patient-submitted-photos.html) [E]
- [D] MIT 學位論文（盧安達鄉村剖腹產/手術傷口）：手機 RGB 照片 CNN 的 AUC 約 0.64–0.86；熱影像 transfer-learning CNN 的中位 AUC 約 0.90。後續論文做了離線 Android app，含自動裁切、影像品質即時回饋、色彩校正、裝置端推論（僅搜尋片段）— [MIT DSpace 1721.1/139063](https://dspace.mit.edu/handle/1721.1/139063?show=full)；[MIT DSpace 1721.1/147526](https://dspace.mit.edu/handle/1721.1/147526)
- [C] JMIR 2024 範圍回顧：以 ML 從影像辨識手術傷口感染「仍屬新興研究」，納入研究多數偏誤風險不明（全文頁擷取失敗，僅搜尋片段）— [JMIR 2024 e52880 PDF](https://jmir.org/2024/1/e52880/PDF)
- [C] Surgical Infections 2019 "A Roadmap for Automatic SSI Detection and Evaluation Using User-Generated Incision Images"：整理居家自拍切口照的影像品質與分析挑戰，提及 mPOWEr 等病人端 app（僅摘要）— [PubMed 31424335](https://pubmed.ncbi.nlm.nih.gov/31424335/)
- [C] 照片判讀 SSI 的一致性差異很大：
  - Palmgren 2019 皮膚移植術後 8 張照片、國際皮膚科醫師問卷，κ=0.19（slight）— [Region H 典藏](https://research.regionh.dk/en/publications/variability-in-the-diagnosis-of-surgical-site-infections-after-fu/)
  - Bruce 2021 下肢創傷（WOLLF），照片評分者 κ=0.63，且**只看照片會高估深部 SSI**— [Warwick WRAP](https://wrap.warwick.ac.uk/id/eprint/156809)
  - 剖腹產研究：CDC 標準為 moderate、ASEPSIS 為 very good — [Frontiers in Surgery 2023](https://www.frontiersin.org/journals/surgery/articles/10.3389/fsurg.2023.1123193/text)
  - （以上均僅摘要/片段）
- 未找到可靠證據：任務指示提到的「McLean 2023 SSI AI」、「Hsu et al. 台灣 SSI AI」、「Fernandes-Taylor AI 模型」，本次都沒有找到可核對的原始論文。Fernandes-Taylor 參與的是上面 Wiseman 2016 的人工判讀一致性研究。

### Inferences
- 本報告推論（高度可移植）：Wiseman 的數據直接說明「發紅」是照片上最不可靠的特徵，連床邊也只有 0.44。靜脈炎分級以發紅為核心，所以專案的**標註天花板可能很低**。在 14 位病人的資料上，模型與標註者的一致性如果達到標註者彼此之間的水準（例如 κ 約 0.3–0.5），就已經是合理結果；不應期待 90% 以上的準確率。應先量測標註者間一致性，再用它當模型表現的上限參考。
- 本報告推論：Mayo 的兩階段架構（先偵測切口/判斷影像可用，再分類）對應到專案現有的 YOLO 偵測（找 IV 部位）→ 裁切 → 分類器。MIT app 的「影像品質回饋、自動裁切、色彩校正」對應到 LINE 照片的前處理需求。這是 SSI 領域的**業界慣例**。
- 本報告推論：Mayo 用 >20,000 張達到 AUC 約 0.81；就算 1,000 張靜脈炎照片的任務比 SSI 單純（固定部位），也只宜期待中等表現。照片 AI 應定位為「優先順序/提醒」，不是診斷，這和 TWIST 的結論一致：遠端照片的價值在「較早被看到」。

### Gaps
- Mayo 2025 全文的切分方式（病人層級？醫院層級留出？）、影像品質排除比例，未核對。
- JMIR 2024 範圍回顧納入研究的逐篇數據未取得。

---

## Q5. 手機傷口分割與測量（FUSeg、DFU 挑戰、Swift、imitoMeasure）：準確度與失敗模式

### Takeaway
在**標準化的臨床拍攝**（固定距離、單一部位、像素級標註）下，傷口分割 Dice 約 0.89；測量 app 對**模型傷口**的 ICC 約 0.97–1.00。但這些結果多來自小樣本、單中心或廠商相關研究，主要失敗模式是比例尺/角度、小傷口、矩形大傷口、光線。

### Cited Findings
- [B/D] FUSeg 2021（MICCAI 挑戰；論文刊於 Information 2024;15(3):140）：1,210 張像素級標註足部潰瘍影像，來自 889 位病人、收集 2 年；以平均 Dice 排名，結果於 2021-08-16 公布 — [MDPI Information](https://www.mdpi.com/2078-2489/15/3/140)；[Zenodo 挑戰說明](https://zenodo.org/records/4575314/files/FootUlcerSegmentationChallenge2021_02-11-2021_09-02-06.pdf)
- [D] 名次聲稱有衝突：x-FUSegNet 自稱 Dice 89.23%、排行榜第一；另一篇 ensemble CNN 也自稱第一。應以官方排行榜（fusc.grand-challenge.org，未開啟）為準 — [arXiv 2305.02961](https://arxiv.org/abs/2305.02961v2)；[arXiv 2109.01408](https://arxiv.org/pdf/2109.01408)
- [C] Swift Wound app（PLoS ONE 2017，PMC5560698）：15 張**塑膠模型傷口**照片和數位面積儀比較，app 評分者間 ICC 0.97–1.00；尺量法 ICC 0.92–0.97（僅搜尋片段）— [PMC5560698](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5560698/)
- [C] imitoMeasure（Egyptian J Hosp Med 2022）：下肢慢性傷口和手動 planimetry 比較，r=0.998、ICC 0.999；小樣本、單中心 — [EKB 期刊頁](https://journals.ekb.eg/article_270504.html)
- [C] 其他 app：Tissue Analytics 研究中，尺量法面積比 app 大約 30%，傷口越小差異越大；WoundDesk 相對數位 planimetry 高估 13%，且大型矩形傷口準確度下降（僅搜尋片段）— [Telemedicine journal (jtelemed.ru)](https://jtelemed.ru/en/article/reliability-and-accuracy-wound-surface-measurement-using-mobile-technology)；[HMP Wounds](https://www.hmpgloballearningnetwork.com/site/wounds/rapid-communication/prospective-trial-interrater-and-intrarater-reliability-wound)
- [B] Anisuzzaman et al. "Image-Based AI in Wound Assessment: A Systematic Review", Adv Wound Care 2022;11(12):687–709（DOI 10.1089/wound.2021.0091）：從 >250 篇篩出 115 篇，涵蓋分割（測量）與分類（診斷）；具體限制陳述未取得全文（僅摘要）— [PubMed 34544270](https://www.pubmed.gov/34544270/)；[arXiv 2009.07141](https://arxiv.org/abs/2009.07141)
- [C] Derm Foundation 模型卡也承認：在很亮或很暗的照片上品質會下降 — [HF google/derm-foundation](https://huggingface.co/google/derm-foundation/blob/main/README.md?code=true)

### Inferences
- 本報告推論：傷口面積測量依賴清楚的邊界和比例尺。靜脈炎的紅斑邊界模糊、漸層，而且 LINE 照片沒有比例尺，所以「像素級分割＋面積」**不適合當 120 張階段的目標**；用 bounding box（YOLO）定位、再做影像層級分級，比較符合資料量。
- 本報告推論：如果未來要量紅斑範圍（例如靜脈炎量表的紅斑公分數），醫院端需要固定拍攝流程（距離、角度、比例尺/色卡貼紙）。這屬於資料蒐集設計，不是模型問題。
- 本報告推論：FUSeg 的資料規模（約 1,200 張、889 位病人、每人約 1.4 張）和專案未來的 1,000 張相近，但病人數多很多。專案應優先增加**病人數**，而不是每人的張數。

### Gaps
- 未找到 Swift Skin and Wound（現行產品）的獨立多中心驗證。
- 未找到可靠證據：手機分割模型在 JPEG 重壓縮/通訊軟體傳輸後的表現衰退。
- FUSeg 官方排行榜 Dice 數值未直接核對。

---

## Q6. 小資料教訓：遷移學習、皮膚科基礎模型、少樣本、捷徑學習、資料集偏移、病人層級洩漏

### Takeaway
**研究證據顯示**：(1) 畫面中的人工標記會讓 CNN 學到捷徑（Winkler 2019：手術墨水標記讓特異度從 84.1% 掉到 45.8%）；(2) 換到不同族群/資料集時，AUC 可以下降 29–40%（DDI）；(3) 同一病人/病灶的影像跨訓練與測試集會虛增表現。皮膚科基礎模型（PanDerm、Derm Foundation）宣稱更省標註，但**授權與權重格式都不符合專案「只匯入 safetensors」的規則**。

### Cited Findings
- **捷徑學習（標記物）**
  - [B] Winkler JK, Haenssle HA, et al. JAMA Dermatol 2019;155(10):1135–1141（DOI 10.1001/jamadermatol.2019.1735）：
    - 130 個黑色素細胞病灶（107 個良性痣、23 個黑色素瘤），比較有/無龍膽紫手術標記。
    - 無標記：Se 95.7%、Sp 84.1%；有標記：Sp 降到 45.8%（標記提高了黑色素瘤機率分數，讓良性痣變成偽陽性）。
    - 把標記裁掉後恢復到 Se 100%、Sp 97.2%、AUC 0.993。
    - 作者推測訓練資料中帶標記的黑色素瘤比例偏高，讓網路把標記和惡性聯想在一起；這是商用 CNN 的測試研究，非自訓練。
    - — [PMC6694463](https://pmc.ncbi.nlm.nih.gov/articles/PMC6694463)；[PubMed 31411641](https://pubmed.ncbi.nlm.nih.gov/31411641/)
- **資料集偏移**
  - [B] Daneshjou R, et al. "Disparities in dermatology AI performance on a diverse, curated clinical image set", Sci Adv 2022;8(32)（DOI 10.1126/sciadv.abq6147）：
    - DDI 共 656 張、病理證實。3 個在原資料集表現良好的模型，換到 DDI 後 ROC-AUC 下降 29–40%（預印本數字）。
    - 深膚色與罕見疾病是主因；皮膚科醫師（常是標註者）在這些影像上也表現較差。
    - 用 DDI 微調可以縮小 FST I–II 和 V–VI 的差距。
    - — [PMC9374341](https://pmc.ncbi.nlm.nih.gov/articles/PMC9374341)；[arXiv 2111.08006](https://arxiv.org/abs/2111.08006v1)
- **病人/病灶層級洩漏**
  - [D] arXiv 2401.14497（DermaMNIST/Fitzpatrick17k 品質稽核）：
    - DermaMNIST 的同一病灶影像出現在多個 train/val/test 切分中，作者釋出修正版 DermaMNIST-C。
    - 文中轉引 Oner 等人：一篇 Nature Medicine 病理 DL 論文以 slide 而非病人切分，被視為洩漏。
    - 轉引 Bussola 等人：同一受試者的 patch 同時出現在訓練與驗證集時，表現明顯虛增。
    - （轉引部分未開原文）
    - — [arXiv 2401.14497](https://arxiv.org/html/2401.14497v2)
  - [D] 2026 預印本指出 ISIC 2019 有大量跨切分的重複/近重複影像（僅搜尋片段）— [arXiv 2608.07574](https://arxiv.org/pdf/2608.07574)
  - 業界慣例：新近研究以 patient ID（沒有則用 lesion ID）分組切分，同一組不跨 train/test（僅搜尋片段）— [arXiv 2608.07574](https://arxiv.org/pdf/2608.07574)；[DermoGPT arXiv 2601.01868](https://arxiv.org/pdf/2601.01868)
- **皮膚科基礎模型**
  - [B] PanDerm（Yan S, …, Ge Z. Nature Medicine 2025;31(8):2691–2702，DOI 10.1038/s41591-025-03747-y）：
    - 以自監督方式在 11 個機構、4 種影像模態、>200 萬張皮膚影像上預訓練。
    - 在 28 個基準任務上達到 SOTA，常常只用 10% 標註資料就超越既有模型。
    - 讀者研究：協助非皮膚科人員在 128 種疾病的鑑別診斷上提升 16.5%。
    - — [Monash Research](https://research.monash.edu/en/publications/a-multimodal-vision-foundation-model-for-clinical-dermatology/)；[MedUni Wien 新聞](https://www.meduniwien.ac.at/web/en/ueber-uns/news/2025/news-in-june-2025/new-ai-system-for-analysing-skin-diseases-tested/) [E]
  - [E] PanDerm GitHub（已開）：
    - 授權 **CC-BY-NC-ND 4.0**（非商業、禁止改作）。
    - 權重是 PyTorch **.pth**，PanDerm（ViT-L/16）與 PanDerm_Base（ViT-B/16）放在 **Google Drive**；DermLIP_PanDerm 在 HF。
    - 需要 linear probing 或微調才能用（`linear_eval.py` 有 `percent_data` 參數）。
    - 後繼模型 DermFM-Zero（PanDerm-2）於 2026-02-13 釋出，頁面未載明授權。
    - — [GitHub SiyuanYan1/PanDerm](https://github.com/SiyuanYan1/PanDerm)
  - [D] PanDerm 補充資料（僅搜尋片段）：5% 資料設定下，DINOv2 weighted F1 0.803，ImageNet 監督式 0.792；未確認是 linear probe 還是微調 — [Nat Med 補充資料 PDF（UNIBO 典藏）](https://cris.unibo.it/retrieve/handle/11585/1037927/a6367364-c674-4397-806e-2f7e058acf95/41591_2025_3747_MOESM1_ESM.pdf)
  - [A/E] Google Derm Foundation 模型卡（已開）：
    - BiT-M ResNet101x3，輸入 448×448，輸出 6,144 維 embedding。
    - 微調資料含美國/哥倫比亞遠距皮膚科、澳洲皮膚癌資料，包含智慧型手機與病人自拍影像。
    - 以 TF-Keras（`from_pretrained_keras`）載入，**非 PyTorch／未標示 safetensors**；HF 需登入同意 Health AI Developer Foundations 使用條款（license: other）。
    - 宣稱 linear classifier 比標準 BiT-M 準確約 10–15%。
    - 也提供 Vertex AI 雲端服務端點。
    - — [HF google/derm-foundation README](https://huggingface.co/google/derm-foundation/blob/main/README.md?code=true)；[HAI-DEF 使用條款](https://developers.google.cn/health-ai-developer-foundations/terms)；[Serving API（雲端）](https://developers.google.com/health-ai-developer-foundations/derm-foundation/serving-api)
- **少樣本**
  - [D] Woerner & Baumgartner 2024（arXiv 2408.08058，MICCAI 2024 workshop oral）：在 19 個醫學影像資料集上比較 16 個預訓練模型。訓練集極小時 BiomedCLIP 平均最佳；樣本稍多時 LAION-2B CLIP 較好；**每類超過約 5 張時，微調 ImageNet ResNet-18 表現相近**。頁面未提 DINOv2，也未說明是否含皮膚科資料 — [arXiv 2408.08058](https://arxiv.org/abs/2408.08058v1)
  - [D] 皮膚病灶自監督研究：自監督預訓練的 linear probe 優於 ImageNet 監督式，且和監督式微調相當（ResNet-50，非 DINOv2；僅搜尋片段）— [arXiv 2401.00692](https://arxiv.org/pdf/2401.00692)
- **報告規範**
  - [A] TRIPOD+AI（Collins GS, et al. BMJ 2024;385:e078378，DOI 10.1136/bmj-2023-078378）：27 項清單＋13 項摘要清單，取代 TRIPOD 2015，適用迴歸與 ML — [Birmingham 典藏](https://research.birmingham.ac.uk/en/publications/tripodai-statement-updated-guidance-for-reporting-clinical-predic/)；[EQUATOR](https://www.equator-network.org/?p=11341)
  - [A] CLAIM 2024 Update（Tejani, Klontzas, Gatti, et al. Radiol Artif Intell 2024;6(4):e240300）：72 人 Delphi 共識；每項改為 Yes/No/NA；建議用「reference standard」和「external testing」（取代 external validation）；不是評分工具 — [PMC11304031](https://pmc.ncbi.nlm.nih.gov/articles/PMC11304031)；[RSNA CLAIM 頁](https://pubs.rsna.org/page/ai/claim)

### Inferences
- 本報告推論（授權/格式）：
  - **PanDerm**：.pth（pickle，有任意程式碼執行風險）放在 Google Drive，授權 CC-BY-NC-ND。依專案「只允許 safetensors」規則**不能直接匯入**。如果人工確認要評估，應由人在隔離環境把權重轉成 safetensors，記錄雜湊後再在本機完整重評；還要確認 NC-ND 對「研究原型」是否允許（ND 可能限制散布微調後的權重）。
  - **Derm Foundation**：TF-Keras 格式，不在專案 PyTorch/safetensors 管線內；雲端 Vertex 服務違反「不上傳照片」，必須排除。本機 TF 推論在技術上可行，但仍不符合 safetensors 規則。
  - **本機替代**：繼續用 DINOv2-small（Meta 在 HF 發布；safetensors 可用性與 Apache-2.0 授權本次未開頁核對，需人工確認）＋ logistic regression 當主要基線；EfficientNet-B0（torchvision）凍結骨幹當對照。BiomedCLIP（open_clip 格式）可列為「待人工確認授權/格式」的候選，本次未核對。
- 本報告推論（捷徑）：靜脈炎照片中常見的 IV 敷料、透明膜、膠帶、留置針、手寫日期、皮膚筆畫的紅斑邊界，**最可能是捷徑**。例如重度靜脈炎時針已拔除、敷料不同，或護理師在嚴重案例畫邊界。這與 Winkler 的機制同構。建議：
  - (a) 標註時記錄「是否有敷料/針/筆跡/比例尺」；
  - (b) 用 Grad-CAM 或遮蔽測試檢查模型注意力；
  - (c) 做「遮掉敷料區」的對照評估；
  - (d) 比較醫院來源 vs LINE 民眾來源的分級分布，避免「來源 = 分級」的捷徑（例如民眾多傳嚴重案例）。
- 本報告推論（洩漏）：14 位病人、約 120 張 ≈ 每人 8–9 張，同一人多張高度相似。**影像層級隨機切分必然虛增**，必須用 leave-one-patient-out 或 GroupKFold(groups=patient_id)；資料增強只放在訓練折；超參數選擇也要做巢狀的病人層級切分。報告時寫明 CLAIM 的「reference standard」，並清楚標示「無 external testing」。
- 本報告推論（小資料策略）：依 Woerner & Baumgartner，在每類僅數張到數十張時，凍結 embedding＋線性分類器通常比微調穩定。專案現在的 DINOv2-small 凍結＋LR、EfficientNet-B0 凍結骨幹，正是證據支持的方向。到了約 1,000 張、且病人數足夠時，才考慮部分解凍微調，並保留病人層級外部測試集（例如另一家醫院或另一段時間）。
- 本報告推論（偏移）：DDI 顯示換族群後 AUC 下降 29–40%，標註者在困難影像上也較差。台灣病人以 Fitzpatrick III–IV 為主，歐美皮膚科預訓練模型可能存在膚色偏移；LINE 壓縮與室內燈光是另一種偏移。

### Gaps
- 未找到可靠證據：DINOv2 對 ImageNet 監督式模型、在 <20 張/類的皮膚**照片**任務上做 linear probe 的配對比較（PanDerm 補充資料數字僅搜尋片段）。
- 未核對：MONET（皮膚科概念模型）、Narla 等人捷徑學習文獻；任務指示所列項目本次未開原文。
- 未找到量化「皮膚科 AI 修正病人層級洩漏後掉多少分」的同儕審查研究。
- DermFM-Zero 授權、DINOv2/BiomedCLIP 的 safetensors 可用性與授權，未開頁核對。

---

## Q7. 哪些教訓可移植到靜脈炎照片（全臂照、小病灶、畫面有 IV 敷料、LINE 壓縮 JPEG），哪些不能

### Takeaway
**最可移植**的是流程與評估面：病人層級切分、偵測後裁切的兩階段管線、標記物捷徑的檢查、先量標註者一致性當天花板、依來源分層與外部測試、CLAIM/TRIPOD+AI 報告。**較不可移植**的是表現數字：大多來自標準化臨床拍攝或數千到數萬張資料，以及需要特殊硬體的方法（熱影像、皮膚鏡、偏振攝影）。

### Cited Findings
- 兩階段（先定位/判斷影像可用，再分類）是 SSI 自拍照 AI 的做法 — [Mayo Clinic 新聞](https://www.mayoclinic.org/medical-professionals/surgery/news/ai-powered-imaging-tool-enhances-detection-of-surgical-site-infections/mac-20587160) [E]；[MIT DSpace 147526](https://dspace.mit.edu/handle/1721.1/147526) [D]
- 照片上「發紅」的評分者一致性很差（AC 0.27–0.34），照片 vs 床邊 AC 0.27 — [PMC4913032](https://pmc.ncbi.nlm.nih.gov/articles/PMC4913032) [C]
- 以紅斑為主的壓傷 stage 1，照片 vs 床邊一致性最低 — [NDNQI 講義](https://ana.confex.com/ana/ndnqi12/webprogram/Handout/Paper7154/Wound_Photography_Study.pdf) [C]
- 標記物捷徑：特異度 84.1% → 45.8%，裁掉後恢復 — [PMC6694463](https://pmc.ncbi.nlm.nih.gov/articles/PMC6694463) [B]
- 外部測試會掉分：壓傷 0.793 → 0.717 — [PubMed 37866277](https://pubmed.ncbi.nlm.nih.gov/37866277) [C]；DDI AUC 下降 29–40% — [PMC9374341](https://pmc.ncbi.nlm.nih.gov/articles/PMC9374341) [B]
- CIELAB a* 觀察者間重現性高，但和臨床評分弱相關 — [Zendy srt.12878](https://zendy.io/title/10.1111/srt.12878) [C]
- 熱影像對 cellulitis 敏感度高、特異度低，需要外接硬體 — [JAMA Derm 2024](https://jamanetwork.com/journals/jamadermatology/fullarticle/2816455) [B]

### Inferences
**可移植（本報告推論，依優先順序）**
1. **病人層級切分是硬性要求**：用 GroupKFold/LOPO，並報告每位病人的結果分布。這是業界慣例，也有研究證據（洩漏虛增）。
2. **先量標註一致性**：2–3 位標註者獨立標註 120 張，計算 κ/Gwet's AC。Wiseman 的發紅 AC 約 0.3–0.4 可以當預期參考；模型應和「標註者間一致性」比較，而不是和 100% 比較。
3. **偵測 → 裁切 → 分類**：全臂照片中病灶很小，直接全圖分類會被背景、敷料、衣物主導。YOLO 先框出 IV 部位/紅斑區，再把裁切圖送進 DINOv2/EfficientNet，和 Mayo、MIT 的做法一致。
4. **捷徑檢查**：敷料、針、膠帶、筆跡、比例尺、背景（病床 vs 居家）、拍攝裝置/來源都可能是捷徑。記錄 metadata、做遮蔽消融與 saliency 檢查。
5. **Δa* 當可解釋輔助特徵**：同一張照片內病灶 vs 鄰近正常皮膚的差，可以抵消部分 LINE 白平衡/壓縮影響。只當輔助特徵與標註 sanity check，不單獨當分級器。
6. **依來源分層與外部測試**：醫院 vs LINE 民眾、不同醫院、不同時間各自報告；依 CLAIM 2024 用「external testing」一詞，並依 TRIPOD+AI 報告。
7. **影像品質閘門**：模糊、過曝/過暗、病灶不在畫面內的照片先篩除或標記，不要硬分級。Derm Foundation 模型卡也承認極亮/極暗會劣化。

**不能直接移植或需打折（本報告推論）**
- 皮膚鏡/黑色素瘤的表現數字（AUC>0.9）：影像標準化程度、病灶對比都和全臂照片不同。
- 傷口分割/面積測量（Dice 0.89、ICC 0.97+）：來自邊界清楚的潰瘍與模型傷口；靜脈炎紅斑邊界漸層、LINE 照片無比例尺。
- 熱影像：民眾 LINE 照片拿不到；只適合列為醫院端未來研究。
- Mayo 的 AUC 約 0.81：建立在 >20,000 張、>6,000 位病人上，不能外推到 1,000 張。
- 雲端基礎模型（Derm Foundation Vertex 服務）：違反不上傳照片原則，排除。PanDerm/Derm Foundation 的本機權重也因格式（.pth/TF）與授權（NC-ND/HAI-DEF）不符合現行規則，需人工審查。

**對兩個資料規模的具體預期（本報告推論）**
- **14 位病人／約 120 張**：只適合「可行性與失敗模式探索」。主要產出應是：標註者一致性、LOPO 下凍結 embedding＋LR 的混淆矩陣（附信賴區間）、捷徑/品質檢查結果。不宜宣稱準確率。
- **約 1,000 張**：應優先提高病人數，例如 ≥100 位，而不是每人很多張；同時保留至少一個「另一院或另一時期」的外部測試集。可以比較凍結 vs 部分微調，但不自動訓練/部署，模型選擇由人確認。

### Gaps
- 未找到可靠證據：直接以照片 AI 做靜脈炎（PIVC phlebitis）分級的鄰近領域外部驗證研究（靜脈炎本身的文獻由其他研究者負責）。
- 未找到可靠證據：通訊軟體（LINE/WhatsApp）傳輸壓縮對皮膚照片 AI 表現的量化影響。
