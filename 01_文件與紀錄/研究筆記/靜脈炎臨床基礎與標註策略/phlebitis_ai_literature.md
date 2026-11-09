# AI / 機器學習 / 電腦視覺判讀靜脈炎、輸液滲漏/外滲及其他 PIVC 置入部位併發症：文獻表與證據成熟度

> 檢索/存取日期：2026-10-30 至 2026-10-31（以下 "存取 2026-10-30" 簡記為 "acc. 10-30"）。
> 來源分級：[A] 官方/標準/報告指引；[B] 系統性回顧/統合分析/頂級期刊；[C] 一般同儕審查（含 IEEE EMBC 等審查制會議論文）；[D] 預印本；[E] 部落格/論壇/程式碼/新聞稿/廠商資料（僅輔助）。
> 結論標記：**研究證據顯示** / **業界慣例** / **本報告推論**。
> 狀態：本檔在兩次 rate-limit 中斷後寫成；已完成兩輪檢索（廣泛探索 + 逐篇開啟主要文獻）。標註「數字來自搜尋摘要」者為未能開啟原文/摘要頁，僅由搜尋引擎摘要得知，需再核對。

## Q1. 目前究竟有哪些「以照片（或影片/熱影像/其他影像）判讀 PIVC 部位併發症」的 AI 研究？（文獻表）

### Takeaway
**研究證據顯示**：以「一般可見光照片 + 深度學習」判讀 PIVC 併發症、且已發表結果者，本輪檢索只找到**一條研究線**——泰國 Thammasat 大學 TUXAT（外滲/滲漏嚴重度，非靜脈炎）：EMBC 2022、EMBC 2024、Sci Rep 2026。**以照片判讀「靜脈炎」(VIP/INS) 的已發表 AI 模型研究：未找到可靠證據**；唯一直接相關的是土耳其一項已登錄、狀態為 completed 但尚無結果的試驗（NCT07889895）。其餘為非照片模態（超音波影片 AI、熱影像閾值法、光學/生物阻抗/壓力感測器 + ML）。

### 文獻表 A：照片（可見光）+ AI —— 核心可比研究

| # | 研究 | 國家 | 影像數 | 病人數 | 類別定義/量表 | 模型/方法 | 驗證方式（分割層級/CV/洩漏風險） | 外部驗證 | 主要結果（精確數字） | 限制 | 偏誤風險評論（PROBAST+AI / CLAIM / TRIPOD+AI 概念） |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A1 | Munthuli A, et al. "Extravasation Screening and Severity Prediction from Skin Lesion Image using Deep Neural Networks." IEEE EMBC 2022, pp.1827–1833. DOI 10.1109/EMBC48229.2022.9871115；PMID 36086628 [C] | 泰國 | 1,084（依 2026 Sci Rep 對本版的描述） | 未在可取得內容中找到 | 4 級：Asymptomatic / Mild / Moderate / Severe（自訂嚴重度，非 INS infiltration scale；**無法取得全文**，標註者與準則未確認） | U-Net ×2（皮膚、病灶分割）+ DenseNet-121（嚴重度分類）+ 規則式 multi-class 修正 | **未找到**分割層級描述（**無法取得全文**）。若 ~8 張/人且隨機影像分割 → 高洩漏風險 | 未見 | 二元（無症狀 vs 異常）Sens 77.78%、Spec 90.24%；異常內 F1：Mild 0.8049、Severe 0.6429、Moderate 0.6250；整體 F1 78.83%（後者引自 2026 Sci Rep） | 智慧型手機照片未標準化；中間等級（Moderate）最差 | Participants/predictors 領域：便利樣本、單國；Analysis 領域：分割層級不明、無校準、無 CI → **高/不明偏誤風險**。數字來自摘要 + 二手引述 |
| A2 | Munthuli A, et al. "Redefining the classification of extravasation severity using CLIP linear probe with few-shot instances." IEEE EMBC 2024, pp.1–7. DOI 10.1109/EMBC53108.2024.10782522 [C] | 泰國 | 訓練：每類 64 張平衡子集（few-shot）；測試子集 102 張（27/40/24/11） | 未在可取得內容中找到 | 同 4 級；ground truth 由皮膚科醫師判定（依 2026 Sci Rep 描述） | 凍結 CLIP ViT-L/14@336 特徵 + logistic regression，多分類器投票集成 | 未說明是否 patient-level（**本輪未能直接開啟此篇，資訊來自 2026 Sci Rep 引述**） | 未見 | 最高 macro F1 **81.34%**；誤分 6/27、6/40、4/24、2/11（共 18/102，推算 accuracy ≈82%） | 測試集小（Severe 僅 11 張）；「最高」值可能為多組設定中擇優 | **與本專案最可比**（凍結基礎模型 + 線性分類器 ≈ 本專案 DINOv2-small + LR）。擇優報告（"maximum"）→ 樂觀偏誤；無 CI；分割層級不明 → 高/不明偏誤風險 |
| A3 | Munthuli A, Liao P, Pongcharoen P, … Tantibundhit C. "Intravenous extravasation report generation using deep learning, generative artificial intelligence, and visual question answering techniques." *Sci Rep* 2026;16:21542. DOI 10.1038/s41598-026-51901-4；PMC13350960 [C]（[PMC 全文, acc. 10-30](https://pmc.ncbi.nlm.nih.gov/articles/PMC13350960/)） | 泰國（19 家醫院：9 衛生部、6 曼谷、4 大學醫院） | **1,085**（TUXAT app 智慧型手機拍攝，未標準化；手、臂、腿、足） | **135**（≈8 張/人） | 4 級嚴重度；人工評分另用 1–5 Likert（Discoloration / Integrity / Edema） | GroundingDINO（Swin-T）分割 + 凍結 CLIP ViT-L/14 + LR 集成分類 + VQA（Qwen2-VL-72B AWQ、Ovis1.6-Gemma2-9B、MiniCPM-V-2.6，共識規則）生成報告 | **Patient-level split：未說明**；CV：未說明；增強：未說明；類別不平衡：訓練用 64/類平衡子集，測試集不平衡未處理 | **否**（作者列為未來工作："external validation using independent datasets"） | 嚴重度分類沿用 2024：macro F1 81.34%。報告品質（3 位皮膚科醫師、204 份報告）：模型主效應 Wilks Λ=0.999, F=0.19, p=0.904（不顯著）；嚴重度 p=0.013；評分者 p<0.001。評分者間一致性：Discoloration 最佳（例 Moderate 組 Krippendorff α=0.576、ICC(2,k)=0.652），Integrity 最差（Severe 組為負值） | 只有照片（無溫度、發燒、肢體活動資訊）；評分者主觀性大；Severe 僅 11 張；單一國家；VQA 漏看細微發紅/輕度水腫、偶有幻覺 | 參考標準本身信度低（Integrity/Edema 一致性差）→ 標籤雜訊；多張/人且未說明分組 → **資料洩漏風險不明**；無外部驗證 → PROBAST+AI 整體「高偏誤風險」；CLAIM 中資料分割、ground truth 細節不足 |

### 文獻表 B：照片 + AI —— 已登錄但尚無結果

| # | 研究 | 國家 | 規模 | 類別/量表 | 方法計畫 | 驗證計畫 | 狀態 | 評論 |
|---|---|---|---|---|---|---|---|---|
| B1 | NCT07889895 "Predicting Peripheral Intravenous Catheter-Related Phlebitis With AI-Based Models"（Kutahya Health Sciences University）[登錄紀錄，非結果；[CT.gov API, acc. 10-30](https://clinicaltrials.gov/api/v2/studies/NCT07889895)] | 土耳其 | 實際收案 461 人 | VIPS 0–5；**靜脈炎定義 VIPS ≥2**；由專家護理師與一位醫師分級 | 手機照片 + 深度學習；摘要提到多模態（人口學、臨床、導管資料）；架構未說明 | train/val/test；**比例與是否 patient-level 未說明**；結果指標含 sens/spec/acc/precision/recall/F1/**calibration** | Completed（start 2025-07-15；primary completion 2026-02-15；completion 2026-09-13；first posted 2026-10-22，晚於完成日 = 回溯登錄） | 唯一找到「照片 + VIP 靜脈炎 + AI」的直接研究；內文對影像來源描述不一致（排程評估時拍 vs 已診斷靜脈炎者拍）→ 可能為病例對照式取樣（spectrum bias）。**尚無可引用的成效數字** |

### 文獻表 C：非照片模態（標記為 non-photo modality）

| # | 研究 | 模態 | 國家 | 樣本 | 標籤/參考標準 | 方法 | 驗證 | 外部驗證 | 結果（精確數字） | 偏誤風險評論 |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 | Bahl A, Johnson S, Mielke N, Blaivas M, Blaivas L. *J Vasc Access* 2025;26(6):1923–1930. DOI 10.1177/11297298241307055；PMID 39831402 [C]（[PubMed, acc. 10-30](https://pubmed.ncbi.nlm.nih.gov/39831402/)） | **超音波影片**（non-photo） | 美國（作者機構） | 開發集 2,133 段影片（361 failure / 1,772 non-failure）；病人數未說明 | PIVC failure（次日失效；定義細節摘要不足） | 專有 ML 演算法，架構未公開 | 另一批「unseen」真實世界影片；**是否 patient-level 未說明** | 未明確 | Acc 0.93、Sens 0.77、Spec 0.98、PPV 0.91、NPV 0.93、AUC 0.87（摘要稱 "best achieved results"） | 擇優報告、模型不透明、作者持有專利（A Little Cold Gel, LLC）→ 高偏誤風險；且為 "failure" 綜合結局，非靜脈炎/滲漏個別類別。**無法取得全文，數字來自摘要** |
| C2 | Doesburg F, Smit JM, Paans W, Onrust M, Nijsten MW, Dieperink W. *PLoS ONE* 2019;14(3):e0213754. DOI 10.1371/journal.pone.0213754 [C]（[PMC, acc. 10-30](https://pmc.ncbi.nlm.nih.gov/articles/PMC6415825/)） | **紅外線熱影像**（non-photo；無 ML） | 荷蘭（UMCG ICU） | 128 人（pilot 57 / validation 71）；229 支 PVC；691 次量測 | VIP ≥1 定義為靜脈炎（34%，78 支） | ΔT（置入點 − 近端 10 cm 參考點）+ 多變量 logistic | pilot / validation 兩階段（時間序列分開） | 否（單中心） | 中位 ΔT VIP0 vs ≥1：pilot −0.90 vs 0.6 °C（p=0.002）；validation −0.45 vs 0.45 °C（p<0.001）；ΔT OR 1.494（95% CI 1.202–1.855）；多變量模型 AUC 0.76；未報告 sens/spec/cutoff | 未盲、無 VIP 評分者一致性、未校正輸液溫度；VIP ≥1 門檻低。對本專案的啟示：熱影像可作為可見光照片的補充模態 |
| C3 | Matsui Y, Murayama R, Tanabe H, … Sanada H. *J Infus Nurs* 2017;40(6):367–374. DOI 10.1097/NAN.0000000000000250；PMID 29112585；PMC5680995 [C]（[PMC, acc. 10-30](https://pmc.ncbi.nlm.nih.gov/articles/PMC5680995)） | **熱影像**（化療外滲；人工閾值，非 ML） | 日本（金澤醫科大學） | 257 人（26 例外滲）；402 次化療；823 張熱影像（平均 3.2 張/次） | 輸注中腫脹或次診時皮下出血/紅斑/色素沉著/硬結/水泡/表皮脫落（護理師肉眼 + 研究者次診檢查；**無客觀金標準**） | 低溫區由邊緣至中心溫度下降 <0.7 °C/cm 為陽性；cutoff 由 ROC（AUC 0.94）選取 | 同一資料集導出與評估 cutoff（無獨立測試）→ 樂觀偏誤 | 否 | Sens 84.6%、Spec 94.8%、PPV 64.7%、NPV 98.2%；護理師漏檢 14/26（54%）vs 熱影像 4/26（15%），p=0.008 | 文中人數敘述不一致（104 同意 / 80 分析 / 257 分析）；排除靜脈炎；有 Terumo 員工共同作者 |
| C4 | Oya M, Murayama R, Oe M, … Sanada H. *Eur J Oncol Nurs* 2017;28:56–61. DOI 10.1016/j.ejon.2017.02.009；PMID 28478856 [C]（[PubMed, acc. 10-30](https://pubmed.ncbi.nlm.nih.gov/28478856/)） | 熱影像影片 + 超音波（非 ML） | 日本 | 62 人、74 次觀察、8 例硬結 | 次一化療日硬結/壞死 | 6 種熱影像型態分類 + 多變量 logistic | — | 否 | 「穿刺點扇形低溫」型態與硬結顯著相關；摘要未給 OR/sens/spec | 事件數僅 8 → 極高過擬合風險。**數字來自摘要** |
| C5 | Lee H-C, Lin J-S. "An Open-Source Wearable Sensor System for Detecting Extravasation of Intravenous Infusion." *IEEE Trans Instrum Meas* 2021;70 [C]（**臺灣 國立清華大學**） | **穿戴式感測**（壓力 + 體溫 + 光學；non-photo）+ 深度學習 | 臺灣 | 依搜尋摘要：含「在人工皮膚上產生外渗」的模擬平台；人體樣本數**未能確認** | 外渗 vs 正常 | CNN + LSTM（Light-ConvLSTM） | 未能確認 | 未能確認 | 偵測率 83.7%、誤報率 6.2% | **本輪嘗試開啟 NTHU PDF 失敗；數字來自搜尋摘要**（另見 Hirata 2023 ACS Sensors 回顧同樣引用）。若資料主要來自人工皮膚/假體，臨床外推性低 |
| C6 | ivWatch（近紅外光學感測，FDA 510(k) K162478）[A：官方監管文件，但資料為廠商提供]；JAVA 2019（Cincinnati Children's）[C] | 光學感測（non-photo，非影像） | 美國 | 510(k) 兒科：2 週–17 歲、3.3–196.7 kg；JAVA：alarm 關閉 156 人 / 開啟 57 人 | 臨床判定滲漏 | 專有訊號演算法 | — | — | 510(k)：Sens 80.0%（95% CI 51.9–95.7%），盲化非警示組 78.3%（56.5–92.5%）；約每 10 天 1 次假陽性（排除疼痛沖洗/裝置問題）。JAVA：「possible」通知平均早 32.3 h、「probable」早 29.8 h | ECRI 評為單一小型診斷世代研究、高偏誤風險，510(k) 中另六項研究無資料。**數字來自搜尋摘要（fda.innolitics、hpnonline、ECRI 頁），本輪未逐頁開啟** |
| C7 | D'Andrea V, et al. *J Vasc Access* 2024. DOI 10.1177/11297298231177723 [C]；van Rens R, et al. 2025 回溯世代（PMC12228456；PMID 40617616）[C] | 新生兒光學感測（ivWatch） | 義大利；荷蘭（Wilhelmina Children's） | van Rens：32,713 次成功新生兒 PIVC 置入（單中心） | Millam score / IEGS | 光學裝置 vs 常規 | — | — | D'Andrea：滲漏發生率 80%，多數 Millam <2；van Rens：與較早偵測 PIVIE 及較低 IEGS 嚴重度相關 | 非影像 AI；**數字來自搜尋摘要**。新生兒/小兒「照片 AI」研究：**未找到可靠證據** |
| C8 | Jambulingam JA, McCrory R, West L, Inan OT. IEEE EMBC 2016:4755–4758. DOI 10.1109/EMBC.2016.7591790 [C]；ATTENTIV 生物阻抗導管（SVM 偵測導管脫位）[C/E] | 皮膚拉伸 + 生物阻抗（non-photo） | 美國 | 未核實 | 滲漏/導管脫位 | 多模態感測；ATTENTIV 用 SVM | 未核實 | — | 未核實 | 僅由 Sci Rep 2026 參考文獻與 ResearchGate 標題得知，**未開啟原文** |
| C9 | Takahashi T, Nakagami G, Murayama R, Abe M, Matsumoto M, Sanada H. "Automated Ultrasonographic Detection of Thrombus and Subcutaneous Edema due to Peripheral Intravenous Catheter." *JAVA* 2025;30(2):27–32. DOI 10.2309/JAVA-D-24-00023 [C]（[Fujita Pure 摘要頁, acc. 10-31](https://pure.fujita-hu.ac.jp/en/publications/automated-ultrasonographic-detection-of-thrombus-and-subcutaneous-2/)） | **超音波靜態影像**（non-photo）；深度學習 | 日本（東大/藤田） | 訓練 263 張、評估 452 張（共 715）；**病人數未報告** | 人工標註血栓、皮下水腫（測試集人工：99 血栓、359 水腫） | 全卷積網路（FCN，架構未命名） | 固定 train/test 分割；**是否依病人分組未說明** | 未見 | 血栓：Acc 0.723、Sens 0.383、Spec 0.818；水腫：Acc 0.881、Sens 0.928、Spec 0.697；未報 AUC | 這是「影像 AI 判讀 PIVC 併發症（血栓/水腫=滲漏前兆）」最接近的同儕審查研究，但模態為超音波。病人數與分組不明 → 洩漏風險不明；**數字來自摘要** |
| C10 | Nexus Medical LLC 專利 US11400212B2 "Clinical assessment of an intravenous catheter site"（發明人 W. Cary Dikeman；申請 2019-07-19；核准 2022-08-02）[E：專利]（[Google Patents, acc. 10-31](https://patents.google.com/patent/US11400212B2/en)） | 手機**校準照片**（以導管 hub 為尺寸/色彩校準物）與基線照片比較 | 美國 | 無 | 色差、紅線（streaking）、腫脹、硬度 | 「可用」統計、神經網路、ML（未描述具體模型） | 無 | 無 | **無任何效能數據或臨床研究** | 僅為概念/權利範圍；不可當成證據。但「以 hub 做色彩/尺寸校準」與「同一病人基線比較」對本專案拍攝規範有參考價值 |

### 文獻表 D：相鄰研究（非併發症判讀，但常被誤認）

| 研究 | 內容 | 為何不算 |
|---|---|---|
| Takahashi T, Murayama R, et al. BMJ Open 2022（PMC9174762）[C]（[PMC, acc. 10-30](https://pmc.ncbi.nlm.nih.gov/articles/PMC9174762/)，搜尋摘要） | 超音波自動量測靜脈，998 張（訓練 739 / 測試 259） | 目的為「預防」PIVC failure（選血管），非判讀併發症 |
| Abe-Doi M, et al. J Vasc Access 2024 [C] | AI 血管偵測輔助初學護理師選穿刺點 | 同上 |
| KAKEN 19K21424 [E/計畫] | 日本 AI 超音波血管徑/深度辨識，259 張，目標預防點滴漏れ | 計畫資料，非併發症判讀 |
| Seoul EHR 深度學習預測靜脈炎（Stud Health Technol Inform 2024；PMID 39049337；DOI 10.3233/SHTI240231）[C] | 27,532 次住院、70,293 次 PIVC；Acc 0.93、AUC 0.89 | **非影像**（結構化 EHR）；數字來自搜尋摘要 |
| Bahl 2021 PLoS ONE（DOI 10.1371/journal.pone.0253243）[C] | 62 支導管超音波：皮下水腫 35 例（臨床檢查僅 6 例），預測過早失效 | 非 ML；是 C1 的前導 |
| 2010 韓國《임상간호연구》16(1) 靜脈炎量表信度研究（koreascience JAKO201008156726677）[C] | 用 20 張靜脈炎照片做 test-retest 評估者信度 | 非 AI，但顯示「照片評 VIP」的人類信度問題（標籤雜訊來源） |
| Matsui Y, Murayama R, et al. 日本看護科学/JNSE 1(1)（J-STAGE）[C] | 健康成人 6 名之點滴外漏模型熱影像，針尖周圍出現低溫區 | 模擬模型、非 ML |
| PPML：Predicting peripheral venous catheter related phlebitis using machine learning（BMC Med Inform Decis Mak 2025；DOI 10.1186/s12911-025-03158-6）[C]（搜尋摘要） | 心臟科住院病人，隨機森林，前瞻驗證；中文報導稱測試 AUC 0.89 | **非影像**（臨床資料）；數字來自搜尋摘要/[E] 新聞（生物通） |
| "Development of a Machine Learning-Based Model for Predicting the Incidence of PIVC-Associated Phlebitis"（PMC11295139；PMID 39108413）[C]（搜尋摘要） | ICU 約 2,400 支導管，random survival forest vs Cox | **非影像**；國家與精確數字未核實 |
| Asman A, et al. iJOE 2024;20(08)（[頁面, acc. 10-31](https://online-journals.org/index.php/i-joe/article/view/48345)）[C] | 印尼「智慧型手機 Early Warning System 顯示」，16 人，靜脈炎發生率組間差異 p=0.001 | **未使用照片/電腦視覺**；樣本極小 |
| Roboflow Universe「Peripheral intravenous access」資料集 [E] | 公開影像資料集 | 本輪開啟 403，**內容/類別未能確認**，不可假設含靜脈炎標籤 |

### Cited Findings（重點出處）
- TUXAT 資料 1,085 張/135 人/19 家醫院、未說明 patient-level 分割、無外部驗證、macro F1 81.34% — [Sci Rep 2026, PMC13350960](https://pmc.ncbi.nlm.nih.gov/articles/PMC13350960/)（acc. 10-30）
- TUXAT 2022 Sens 77.78% / Spec 90.24%、F1 Mild 0.8049 / Severe 0.6429 / Moderate 0.6250 — 來自 EMBC 2022 摘要（經搜尋摘要；DOI 10.1109/EMBC48229.2022.9871115，PMID 36086628；**無法取得全文**）
- 土耳其 VIP 照片 AI 試驗 461 人、VIPS ≥2、分割層級未說明、無結果 — [ClinicalTrials.gov API NCT07889895](https://clinicaltrials.gov/api/v2/studies/NCT07889895)（acc. 10-30）
- 超音波影片 AI 預測 PIVC failure：2,133 影片、AUC 0.87、COI — [PubMed 39831402](https://pubmed.ncbi.nlm.nih.gov/39831402/)（acc. 10-30）
- 熱影像靜脈炎（非 ML）AUC 0.76 — [PMC6415825](https://pmc.ncbi.nlm.nih.gov/articles/PMC6415825/)（acc. 10-30）
- 熱影像化療外滲 Sens 84.6% / Spec 94.8% — [PMC5680995](https://pmc.ncbi.nlm.nih.gov/articles/PMC5680995)（acc. 10-30）
- 熱影像型態與硬結（62 人/74 觀察/8 事件）— [PubMed 28478856](https://pubmed.ncbi.nlm.nih.gov/28478856/)（acc. 10-30）

### Inferences
- **本報告推論**：截至 2026-10-31，「照片判讀靜脈炎」的已發表 AI 研究在可檢索英文文獻中仍為空白；本專案若完成並公開，可能屬於最早一批（但需注意土耳其 NCT07889895 結果可能很快發表）。
- **本報告推論**：TUXAT 是唯一「照片 + 嚴重度分級 + 多中心」的實證，但臨床實體是外滲/滲漏而非靜脈炎；其中「Asymptomatic vs Mild」最易混淆，與本專案 normal vs stage 1 的難點相同。

### Gaps
- 中國 CNKI/萬方、臺灣 Airiti/NDLTD、韓國 KCI/RISS、日本 CiNii/医中誌：本工具無法直接查詢這些資料庫（需登入/非公開搜尋介面），只能透過一般網路搜尋間接檢索；**本報告不能宣稱這些資料庫中「不存在」相關研究**，只能說「經一般網路搜尋未找到」。
- 中文搜尋「静脉炎 深度学习 图像」「输液外渗 人工智能」只得到超音波靜脈偵測碩士論文、壓力性損傷 YOLO 研究等相鄰結果；未找到靜脈炎照片 AI 論文。
- 日文「静脈炎 画像 深層学習」「点滴漏れ 検出 画像 機械学習」：只找到熱影像（非 ML）與超音波血管 AI；未找到照片 AI。
- 韓文「정맥염 딥러닝」「정맥주사 침윤 인공지능」：未找到照片 AI；只找到量表信度研究與護理指引（建議拍照記錄滲漏進展）。
- TUXAT 2022/2024 EMBC 全文、Lee & Lin 2021 全文未能開啟（IEEE 付費 / PDF 抓取失敗）。

## Q2. 逐篇方法學檢核：patient-level split？外部驗證？樣本量？類別不平衡？增強影像是否跨分割洩漏？

### Takeaway
**研究證據顯示**：所有找到的影像 AI 研究（A1–A3、C1、C9），**沒有一篇在可取得的文本中明確說明 patient-level 分割**，也**沒有一篇做外部驗證**，沒有一篇報告校準或信賴區間。類別不平衡只有 TUXAT 2024/2026 處理過（訓練時用每類 64 張的平衡子集）。增強影像是否跨分割洩漏：全部「未說明」。

### Cited Findings
| 研究 | 病人數 | 影像數 | 張/人 | Patient-level split | CV | 外部驗證 | 不平衡處理 | 增強洩漏 | 校準/CI |
|---|---|---|---|---|---|---|---|---|---|
| A1 TUXAT 2022 (EMBC) | 未知 | 1,084 | 未知 | 未說明（無全文） | 未知 | 否 | 未知 | 未知 | 未見 |
| A2 TUXAT 2024 (EMBC) | 未知 | 訓練 64 張/類；測試 102 張 | 未知 | 未說明 | 未知 | 否 | 平衡子集 | 未知 | 未見 |
| A3 TUXAT 2026 (Sci Rep) | 135 | 1,085 | ≈8.0 | **未說明** | 未說明 | **否**（列為未來工作） | 訓練用平衡子集；測試集不平衡 | 未說明 | 無 |
| B1 NCT07889895 | 461 | 未知 | 未知 | 未說明 | 未知 | 未知 | 未知 | 未知 | 計畫報告 calibration |
| C1 Bahl 2025（超音波影片） | 未說明 | 2,133 段影片 | 未知 | 未說明 | 未說明 | 「unseen」集，性質不明 | 未說明 | 未說明 | 未見 |
| C9 Takahashi 2025（超音波） | 未報告 | 715 | 未知 | 未說明 | 否（固定分割） | 未見 | 未說明 | 未說明 | 未見 |
| C3 Matsui 2017（熱影像閾值） | 257 | 823 | 3.2/次治療 | 不適用（cutoff 在同一資料集上選定並評估） | 否 | 否 | — | — | 無 |

- 出處：[Sci Rep 2026 PMC13350960](https://pmc.ncbi.nlm.nih.gov/articles/PMC13350960/)（存取 10-30）；[NCT07889895 API](https://clinicaltrials.gov/api/v2/studies/NCT07889895)（存取 10-30）；[PubMed 39831402](https://pubmed.ncbi.nlm.nih.gov/39831402/)（存取 10-30）；[Fujita Pure](https://pure.fujita-hu.ac.jp/en/publications/automated-ultrasonographic-detection-of-thrombus-and-subcutaneous-2/)（存取 10-31）；[PMC5680995](https://pmc.ncbi.nlm.nih.gov/articles/PMC5680995)（存取 10-30）。
- TUXAT 2026 自述的限制：嚴重組只有 11 張；單一國家資料；照片無法提供溫度/發燒資訊；嚴重組的評分者間 Integrity 一致性為負值。— [PMC13350960](https://pmc.ncbi.nlm.nih.gov/articles/PMC13350960/)
- Bahl 2025 作者是持有該 AI 專利之公司的成員（利益衝突），且摘要報告的是「best achieved results」。— [PubMed 39831402](https://pubmed.ncbi.nlm.nih.gov/39831402/)

### Inferences
- **本報告推論**：TUXAT 平均每人約 8 張。若做的是影像層級隨機分割，同一病人的近重複照片（同一病灶、不同角度或時間）很可能同時落在訓練集與測試集，macro F1 81% 可能被高估。依 PROBAST+AI 的 Analysis 領域，「未說明是否避免同一受試者跨集」應判為 high/unclear。
- **本報告推論**：TUXAT 2024 的「maximum macro F1」是多組設定中的最佳值。測試集只有 102 張、Severe 只有 11 張，以二項比例粗估，單一類別 F1 的 95% CI 寬度可能超過 ±0.15，數字精度有限。

### Gaps
- 無法確認 TUXAT 2022/2024 原文是否描述 patient-wise split（IEEE 全文未能取得）。
- 無法確認 Bahl 2025、Takahashi 2025 的病人數與分組方式（只有摘要）。

## Q3. 綜合：這個領域的證據成熟度如何？典型樣本量多大？最常見的缺陷是什麼？

### Takeaway
**研究證據顯示**：以照片判讀 PIVC 併發症的 AI 仍處於**早期開發（development-only）階段**。全球可核實的只有一條研究線（TUXAT，外滲/滲漏，135 人/1,085 張）。靜脈炎照片 AI 的已發表研究為零，只有一項土耳其試驗剛完成、尚無結果。目前沒有外部驗證，沒有前瞻性臨床影響研究，也沒有獲得監管核准的照片 AI 產品。非照片模態中，光學感測（ivWatch）有 FDA 510(k) 與兒科/新生兒臨床資料，但它不是影像 AI；熱影像研究用的都是人工閾值或統計方法，不是 ML。

### Cited Findings
- 各模態的證據位置：
  - 照片 + DL：EMBC 會議論文 2 篇 + Sci Rep 1 篇（同一團隊）。— [PMC13350960 參考文獻](https://pmc.ncbi.nlm.nih.gov/articles/PMC13350960/)
  - 照片 + DL 判讀靜脈炎：只有試驗登錄。— [NCT07889895](https://clinicaltrials.gov/api/v2/studies/NCT07889895)
  - 超音波 + AI：Bahl 2025（2,133 段影片，AUC 0.87）；Takahashi 2025（715 張；血栓 Sens 0.383、水腫 Sens 0.928）。— [PubMed 39831402](https://pubmed.ncbi.nlm.nih.gov/39831402/)；[Fujita Pure](https://pure.fujita-hu.ac.jp/en/publications/automated-ultrasonographic-detection-of-thrombus-and-subcutaneous-2/)
  - 熱影像（非 ML）：Doesburg 2019 AUC 0.76（128 人）；Matsui 2017 Sens 84.6%/Spec 94.8%（257 人）。— [PMC6415825](https://pmc.ncbi.nlm.nih.gov/articles/PMC6415825/)；[PMC5680995](https://pmc.ncbi.nlm.nih.gov/articles/PMC5680995)
  - 光學感測：ivWatch 510(k) 兒科 Sens 80.0%（95% CI 51.9–95.7%）；ECRI 評其主要研究為高偏誤風險。— 數字來自搜尋摘要（fda.innolitics K162478、ECRI 產品簡報），**未逐頁開啟**
- 典型樣本量（照片/影像 AI）：病人約 100–500 人，影像約 700–2,100 張；嚴重類別的測試影像常少於 15 張（TUXAT Severe 為 11 張）。出處同上。
- Doesburg 2019 討論中將熱影像「結合機器學習」列為未來研究方向，也就是尚未做過。— [PMC6415825](https://pmc.ncbi.nlm.nih.gov/articles/PMC6415825/)（引文經搜尋摘要轉述）
- 參考標準本身不穩定：VIP 未在鎮靜病人中驗證，深膚色病人評分困難（Doesburg 2019）；TUXAT 中皮膚科醫師間的 Integrity 一致性在嚴重組為負值。— [PMC6415825](https://pmc.ncbi.nlm.nih.gov/articles/PMC6415825/)；[PMC13350960](https://pmc.ncbi.nlm.nih.gov/articles/PMC13350960/)

### 最常見的缺陷（本報告依 PROBAST+AI 四個領域歸納）
1. **Participants/data**：便利樣本，單一國家或單中心；病例對照式取樣，只拍已診斷者（如 NCT07889895 內文的描述），會造成 spectrum bias。
2. **Predictors（影像本身）**：拍攝未標準化（光線、距離、角度、敷料遮蔽）。這雖然貼近真實情境，但研究沒有報告影像品質的分布。
3. **Outcome（標籤）**：自訂嚴重度、評分者人數少、未報告評分者間一致性（或一致性差）；未說明標註者是否對臨床資訊盲化；照片無法呈現疼痛、溫熱、硬結等 VIP 必要條件。
4. **Analysis**：未說明 patient-level 分割、沒有 CV 或只有單一分割、擇優報告、沒有 CI、沒有校準、沒有外部驗證、少數類別樣本極少。
- **業界慣例**：皮膚影像 AI 領域普遍把 patient/lesion-level 分割當作基本要求，並以外部測試集（不同機構、不同膚色）作為發表門檻。CLAIM 2024 與 TRIPOD+AI 都要求報告這些項目（見 Q5）。

### Inferences
- **本報告推論**：本領域的證據成熟度可評為「概念驗證/早期開發」，大約相當於 TRL 3–4，或 DECIDE-AI/IDEAL 框架中的開發前期。目前沒有任何研究達到外部驗證層級，更沒有臨床影響研究。
- **本報告推論**：參考標準（肉眼 VIP/嚴重度）本身一致性不高，因此任何照片模型的表現上限都受標註者一致性限制。沒有報告 inter-rater κ 的研究，其準確率無法解讀。

### Gaps
- 未取得 ECRI 與 FDA 510(k) 原文頁做逐字確認；ivWatch 的數字只作為非影像對照。
- 尚無任何已發表的系統性回顧專門彙整「PIVC 併發症影像 AI」。Hirata 等人 2023 年的 ACS Sensors 回顧（DOI 10.1021/acssensors.2c02602）聚焦感測技術，本輪未開啟全文。

## Q4. 與本專案（臺灣研究原型，約 120 張/14 人）的可比性，以及可信的下一個研究應具備什麼？

### Takeaway
**本報告推論**：已發表研究中最可比的方法是 **TUXAT 2024/2026 的「凍結 CLIP ViT-L/14 + logistic regression」**，與本專案的「DINOv2-small 凍結 + LR」做法相近。其 macro F1 81.34%（4 類、測試 102 張、分割層級不明）是目前唯一可引用的照片嚴重度基準，但不能直接拿來和本專案 patient-level 3-fold CV 的結果比較。本專案使用 StratifiedGroupKFold（patient-level），在「分割」這一面向的嚴謹度上，**已優於所有已發表研究所報告的程度**。不過本專案樣本量（14 人）遠小於 TUXAT（135 人），且類別嚴重不平衡（positive 47 vs normal 9）。

### Cited Findings
- TUXAT 2026：1,085 張/135 人、19 家醫院、智慧型手機未標準化照片、4 級、凍結 CLIP + LR、訓練用每類 64 張的平衡子集。— [PMC13350960](https://pmc.ncbi.nlm.nih.gov/articles/PMC13350960/)
- TUXAT 2022：U-Net + DenseNet-121（對應本專案的 EfficientNet-B0 整圖分類 + 可選的分割/偵測）；Moderate 類 F1 最低，為 0.6250。— EMBC 2022 摘要（DOI 10.1109/EMBC48229.2022.9871115，無法取得全文）
- 以 YOLO 系列偵測靜脈炎/滲漏照片：**未找到任何已發表研究**。中文只找到 YOLOv8 用於壓力性損傷分期的相鄰領域研究。— [中國全科醫學 DOI 10.12114/j.issn.1007-9572.2024.0168](https://www.chinagp.net/CN/10.12114/j.issn.1007-9572.2024.0168)（搜尋摘要）
- 土耳其 NCT07889895 以 VIPS ≥2 為靜脈炎門檻，並預計報告 calibration。— [NCT07889895](https://clinicaltrials.gov/api/v2/studies/NCT07889895)。本專案的 binary（positive vs normal）與 staging（normal/stage1/stage2）門檻需要明確對應到 VIP 或 INS 等級，否則無法與該研究比較。
- 專利 US11400212B2 提出以導管 hub 作為尺寸/色彩校準物，並與同一病人的基線照片比較。— [Google Patents](https://patents.google.com/patent/US11400212B2/en)（存取 10-31，[E]，無效能數據）

### 可比性對照
| 本專案元素 | 已發表研究中最接近的對應 | 可比程度 |
|---|---|---|
| DINOv2-small 凍結 + LR | TUXAT 2024/2026 凍結 CLIP + LR | 高（同為 foundation-model linear probe），但類別定義不同（外滲 vs 靜脈炎） |
| EfficientNet-B0 凍結整圖分類 | TUXAT 2022 DenseNet-121 | 中 |
| YOLO11n/s、YOLO26s 病灶偵測（約 24 張有框） | 無 | 無已發表對照 |
| normal / stage1 / stage2 | TUXAT Asymptomatic/Mild/Moderate/Severe；NCT07889895 VIPS 0–5 | 低至中（需要對應表） |
| StratifiedGroupKFold patient-level 3-fold | 無任何已發表研究明確報告 | 本專案較嚴謹 |
| 14 人 / 約 120 張 | TUXAT 135 人 / 1,085 張 | 本專案小一個數量級 |

### 可信的下一個研究（本報告推論；依 TRIPOD+AI / CLAIM 2024 / PROBAST+AI 的要素）
1. **樣本與取樣**：連續收案，不要只拍已診斷者；事先寫好樣本量計算；以「病人數」而非照片數作為主要單位。約 1,000 張平衡照片時，至少需要 100–200 位以上病人，並記錄每人張數的分布，避免少數病人貢獻大量照片。
2. **參考標準**：事先指定 VIP（或 INS phlebitis scale），並在床邊評估，包含觸痛、溫熱、硬結等照片看不到的要素。至少 2 位獨立評分者加 1 位裁決者，報告 weighted κ。照片判讀者與床邊判讀者分開，這樣也能估計「照片可判讀的上限」。
3. **影像擷取**：訂定標準化協定（距離、角度、光源、色卡/尺寸參照物、是否移除敷料），並保留一部分未標準化照片來測試穩健性。
4. **分割與驗證**：以 patient-level（甚至 site/episode-level）分組；增強只在訓練折內進行；近重複照片要去重；用巢狀 CV 調參；保留至少 20% 病人作為 held-out test；做**時間外驗證（temporal）並至少加一家外院的外部驗證**。
5. **分析**：報告 sens/spec/PPV/NPV 及其 95% CI（以病人層級 bootstrap 估計）、AUROC、校準（calibration slope/intercept 或可靠度圖）、混淆矩陣，以及各膚色、部位、光線子群的表現。事先指定主要指標與操作點（篩檢情境應偏重 sensitivity）。
6. **比較基準**：與護理師肉眼 VIP 判讀做比較（reader study），不要只報告模型準確率。
7. **報告**：附上 CLAIM 2024 與 TRIPOD+AI 的完整 checklist，並以 PROBAST+AI 自評。

### Inferences
- **本報告推論**：以 14 人、normal 只有 9 張來說，任何 binary 指標的 CI 都會非常寬。例如 specificity 只用 9 張估計，錯一張就差約 11 個百分點。因此結果只能定位為 feasibility，不應宣稱準確率，這也與本專案「研究原型、非診斷」的定位一致。
- **本報告推論**：本專案若在報告中寫清楚 patient-level 分組、增強只在折內、近重複照片的處理方式與標註者一致性，即使樣本小，方法學透明度也會高於目前已發表的照片 AI 文獻。

### Gaps
- 未找到臺灣（Airiti/NDLTD）任何靜脈炎照片 AI 研究或學位論文。但 **Airiti 與 NDLTD 無法用本工具直接檢索**，不能宣稱不存在。
- 臺灣唯一找到的相關研究是清華大學 Lee & Lin 2021（穿戴式感測 + ConvLSTM，非照片），全文未能開啟。

## Q5. 用於評估的報告/偏誤框架（[A]）

### Takeaway
**研究證據顯示（指引層級）**：PROBAST+AI（BMJ 2025）、TRIPOD+AI（BMJ 2024）與 CLAIM 2024 Update（Radiology: AI）是評估與撰寫這類研究的現行標準，三者都要求報告資料分割單位、參考標準、外部驗證與校準。

### Cited Findings
- PROBAST+AI：Moons KGM 等，BMJ 2025;388:e082505（DOI 10.1136/bmj-2024-082505；2025-03-24 發表），取代 PROBAST 2019。分為 development 與 evaluation 兩部分，各含 participants/data sources、predictors、outcome、analysis 四個領域；development 有 16 個、evaluation 有 18 個 signalling questions；applicability 只評前三個領域。— [ORA Oxford 紀錄](https://ora.ox.ac.uk/objects/uuid:8b15c087-459b-43fa-ad03-1f66ed6ba370)、[NDORMS](https://www.ndorms.ox.ac.uk/publication/2100914)（經搜尋摘要；存取 10-31）[A]
- TRIPOD+AI：Collins GS、Moons KGM 等，BMJ 2024;385:e078378（2024-04-16），含 27 項 checklist 與摘要 checklist，取代 TRIPOD 2015。— 搜尋摘要（[BMJ 節點](https://www.bmj.com/node/1095803)，未逐頁開啟）[A]
- CLAIM 2024 Update：Tejani AS、Klontzas ME、Gatti AA 等，Radiology: Artificial Intelligence；由 72 位專家組成的小組制定；原 2020 版以 STARD 為模板。— [RSNA CLAIM 頁](https://pubs.rsna.org/page/ai/claim)（搜尋摘要）[A]
- 一篇編輯評論指出，宣稱遵循 CLAIM 的論文中，近 60% 沒有附上完整 checklist。— [Diagn Interv Radiol 2024](https://www.dirjournal.org/articles/doi/dir.2024.242849)（搜尋摘要）[C]

### Inferences
- **本報告推論**：照片類的非放射影像研究仍在 CLAIM 的適用範圍內（其範圍是醫學影像 AI）；而模型本身屬於診斷/預測模型，所以同時適用 TRIPOD+AI 與 PROBAST+AI。

### Gaps
- 本輪未逐頁開啟 BMJ 與 RSNA 原文。DOI 與卷期是依搜尋摘要與機構典藏紀錄整理，撰寫正式報告前建議再開原文核對。

---
### 檢索紀錄（供重現）
- 英文：phlebitis deep learning image classification；PIVC infiltration machine learning images；phlebitis photographs CNN；"Visual Infusion Phlebitis" AI；infrared thermography infiltration；extravasation deep learning camera；Munthuli EMBC 2022；Bahl ultrasound AI；ultrasound DL subcutaneous edema Takahashi；ivWatch pediatric；neonatal infiltration camera；IV infiltration thermal DL；phlebitis AI 2025；CLIP linear probe extravasation；phlebitis YOLO smartphone；IV cannula site CV dataset；arXiv/medRxiv phlebitis infiltration；thermal imaging phlebitis ML。
- 簡體中文：静脉炎 深度学习 图像 识别；输液外渗 人工智能 图像；输液性静脉炎 智能识别 卷积神经网络。
- 繁體中文：靜脈炎 人工智慧 影像 辨識 護理。
- 日文：静脈炎 画像 深層学習 点滴 AI；点滴漏れ 検出 画像 機械学習 血管外漏出。
- 韓文：정맥염 딥러닝 이미지 분류；정맥주사 침윤 정맥염 인공지능 사진。
- **未能直接檢索**（需登入或無公開 API）：CNKI、萬方、Airiti、NDLTD、KCI、RISS、KoreaMed、CiNii、医中誌、IEEE Xplore 全文、Scopus。這些只透過一般網路搜尋間接覆蓋，因此「未找到」不等於「不存在」。
- 本輪開啟失敗：NTHU Lee & Lin PDF（抓取失敗）、ScienceDirect Oya 2017（403）、Roboflow（403）、ClinicalTrials.gov 網頁版（改用 API 後成功）。
