# 可解釋性方法與捷徑學習（shortcut learning）偵測／緩解：應用於小型靜脈炎照片研究平台

> 用途：供報告撰寫者改寫為繁體中文章節。存取日期：除另註外，所有來源於 2026-10-30／2026-10-31 存取（以「存取 2026-10-31」簡記）。
> 來源分級：[A] 官方文件／監管機構／國際標準與報告指引；[B] 系統性回顧、統合分析、頂刊／頂會同儕審查；[C] 其他同儕審查（含 workshop）；[D] 預印本；[E] 部落格、官方範例程式、論壇。
> 標註語：「研究證據顯示」＝有引用的同儕審查結果；「業界作法」＝函式庫／工具文件所描述的慣例；「本報告推論」＝根據證據所做的推論，非文獻結論。
> 專案背景提醒：資料約 120 張照片、14 位病人；任務敘述中「positive 47、normal 9」與「stage normal 9、s1 23、s2 24」合計 56 張，與「約 120 張」不一致——可能其餘照片未標註或為未審 LINE 照片，撰寫報告前需向資料負責人確認，**不得**自行補數字。有病灶框者約 24 張。
> 驗證方式：Nature 系列與 RSNA 網站拒絕自動抓取（303 重導／403），故改以 Europe PMC REST API、Semantic Scholar API、arXiv API 讀取書目與摘要（round 2 回到原始紀錄）。**未讀全文**的論文，其內文細節（表格數字）一律不列為已驗證。作者名單只列 API 回傳的部分作者，其餘以 et al. 表示。

---

## Q1. 顯著圖（saliency）方法的可靠性爭議：哪些方法通過 sanity check？

### Takeaway
研究證據一致顯示：顯著圖在醫學影像上的定位能力明顯差於人類與專用定位網路，且部分方法對模型權重幾乎不敏感；常見方法中 Grad-CAM 與 vanilla gradient 通過 Adebayo 的參數隨機化檢查，Guided Backprop／Guided Grad-CAM 不通過，但「通過 sanity check」只是必要條件，不保證可信。對本平台：熱圖只能當「研究者除錯工具」，不能當「模型看對病灶」的證據，更不應給 LINE 民眾看。

### Cited Findings

**A. 方法原始文獻（支持證據）**
- Grad-CAM：以流入最後卷積層的梯度產生粗略定位圖，無需改架構或重訓；人類研究宣稱可幫助未受訓使用者分辨較強與較弱模型。[B] Selvaraju RR, Cogswell M, Das A, et al. "Grad-CAM: Visual Explanations from Deep Networks via Gradient-based Localization." ICCV 2017；IJCV 2019, DOI 10.1007/s11263-019-01228-7。— [arXiv 1610.02391](https://arxiv.org/abs/1610.02391)（存取 2026-10-31）
- Grad-CAM++：以正向偏導數加權特徵圖，宣稱定位更好、能處理同圖多個物件。[C] Chattopadhay A, Sarkar A, Howlader P, et al. WACV 2018, DOI 10.1109/WACV.2018.00097。— [arXiv 1710.11063](https://arxiv.org/abs/1710.11063)（存取 2026-10-31）
- Score-CAM：免梯度，以每張 activation map 遮罩後的前向分數為權重；作者宣稱「通過 sanity check」。[C] Wang H, Wang Z, Du M, et al. CVPR 2020 Workshop on Fair, Data Efficient and Trusted CV。— [arXiv 1910.01279](https://arxiv.org/abs/1910.01279)（存取 2026-10-31）
- Integrated Gradients：提出 Sensitivity 與 Implementation Invariance 兩公理，IG 同時滿足、不需改網路、只需數次梯度呼叫。[B] Sundararajan M, Taly A, Yan Q. ICML 2017（venue 依通行引用，arXiv feed 未列）。— [arXiv 1703.01365](https://arxiv.org/abs/1703.01365)（存取 2026-10-31）
- Attention rollout / attention flow：原始注意力權重因跨層資訊混合而不可靠；rollout／flow 與 ablation 及輸入梯度重要性的相關性高於 raw attention。[B] Abnar S, Zuidema W. "Quantifying Attention Flow in Transformers." ACL 2020（venue 依通行引用）。— [arXiv 2005.00928](https://arxiv.org/abs/2005.00928)（存取 2026-10-31）
- Chefer 等：以 Deep Taylor Decomposition 在 Transformer 中傳遞 relevance（含注意力層與 skip connection），宣稱優於既有方法。[B] Chefer H, Gur S, Wolf L. "Transformer Interpretability Beyond Attention Visualization." CVPR 2021（venue 依通行引用）。— [arXiv 2012.09838](https://arxiv.org/abs/2012.09838)（存取 2026-10-31）
- HiResCAM：Grad-CAM 的梯度平均可能標出模型「沒有使用」的區域；HiResCAM（activation 與 gradient 逐元素相乘）在特定架構下保證只標出實際使用的位置；PASCAL VOC 2012 上 Grad-CAM 產生比模型實際關注更大、更平滑的圖。[D] Draelos RL, Carin L. — [arXiv 2011.08891](https://arxiv.org/abs/2011.08891)（存取 2026-10-31）

**B. 反證與失敗案例**
- Sanity check：「在我們測試的方法中，Gradients 與 GradCAM 通過，Guided BackProp 與 Guided GradCAM 失敗」；最像邊緣偵測器的方法（Guided Backprop 及其變體）對隨機化測試最不敏感；作者承認此檢查是「必要而非充分」條件。摘要另指出部分方法「與模型及資料生成過程皆無關」。[B] Adebayo J, Gilmer J, Muelly M, Goodfellow I, Hardt M, Kim B. "Sanity Checks for Saliency Maps." NeurIPS 2018。— [arXiv 1810.03292](https://arxiv.org/abs/1810.03292)；通過／失敗清單之原文句經搜尋引擎摘自 [arXiv PDF](https://arxiv.org/pdf/1810.03292)（PDF 過大無法直接讀取，存取 2026-10-31）
- 輸入不變性：對輸入加一個不改變模型的常數平移，即可讓許多顯著圖方法錯誤歸因；提出 input invariance 作為可靠性要求。[D]（另有書章版本，本輪未驗證書目）Kindermans P-J, Hooker S, Adebayo J, et al. "The (Un)reliability of saliency methods." — [arXiv 1711.00867](https://arxiv.org/abs/1711.00867)（存取 2026-10-31）
- 醫學影像基準：7 種方法（含 Grad-CAM、Grad-CAM++、IG），多種架構、兩種指標；**Grad-CAM 整體最佳，但全部顯著差於人類基準**；差距在**較小、形狀較複雜**的病灶最大；模型信心與 Grad-CAM 定位表現正相關。[B] Saporta A, Gui X, Agrawal A, Pareek A, Truong S, Nguyen CDT, Ngo V, Seekins J, Blankenberg F, Ng A, Lungren MP, Rajpurkar P. "Benchmarking saliency methods for chest X-ray interpretation." Nature Machine Intelligence 2022, DOI 10.1038/s42256-022-00536-x。— [Semantic Scholar 紀錄](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1038/s42256-022-00536-x)；預印本 [medRxiv 10.1101/2021.02.28.21252634](https://doi.org/10.1101/2021.02.28.21252634)（存取 2026-10-31）。小樣本／洩漏備註：大型胸片資料，非小樣本；病人層級切分與外部驗證細節本輪未讀全文，未驗證。
- 醫學影像可信度：SIIM-ACR 氣胸與 RSNA 肺炎資料集，8 種顯著圖方法，以定位效用、權重隨機化敏感度、重複性、再現性評估；**8 種全部至少未過一項準則**，且都差於定位網路：氣胸 AUPRC 0.024–0.224 vs U-Net 0.404；肺炎 AUPRC 0.160–0.519 vs RetinaNet 0.596（P<.005）；分割任務 5 種、偵測任務 2 種未過權重隨機化測試；作者建議「若目標是定位，請用偵測或分割模型」。[B] Arun N, Gaw N, Singh P, Chang K, Aggarwal M, et al. "Assessing the Trustworthiness of Saliency Maps for Localizing Abnormalities in Medical Imaging." Radiology: Artificial Intelligence 2021;3(6):e200267, DOI 10.1148/ryai.2021200267。— [Europe PMC API](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%2210.1148/ryai.2021200267%22&resultType=core)（存取 2026-10-31）。備註：公開挑戰賽資料、非小樣本；病人切分未於摘要說明；無外部驗證敘述。
- 被忽略的可信度（MICCAI 2022 → Radiology: AI 延伸版）：定義「相關性（預測改變時顯著圖應改變）」與「抵抗性（預測不變時顯著圖不應被輕易操弄）」。延伸版測 7 種方法（vanilla backprop、backprop×image、GradCAM、guided GradCAM、IG、SmoothGrad、XRAI）：敏感度實驗中模型 AUC 由 0.88 降到 0.01，顯著圖卻幾乎不變（mean SSIM ≥0.76），prediction-saliency correlation（PSC）最高僅 0.25（95% CI 0.12–0.38）；穩健性實驗中 AUC 維持 0.88，但顯著圖可被推向目標圖案（與原圖 SSIM ≤0.51），PSC 最高 0.12（95% CI 0.0–0.25）；商用原型 AUC 下降 8.6%（P<.01）而顯著圖相似度 >0.88；放射師僅辨識出 23.3%（2 年資歷）與 44.8%（15 年資歷）的被改影像。作者**未**排序方法，結論為七種在敏感度與穩健性上皆弱。[B] Zhang J, Chao H, Dasegowda G, Wang G, Kalra MK, Yan P. "Overlooked Trustworthiness of Saliency Maps." MICCAI 2022, LNCS 13433:451–461, DOI 10.1007/978-3-031-16437-8_43（書目來自 [researchr](https://researchr.org/publication/ZhangCDWKY22/bibtex)）；延伸版 "Revisiting the Trustworthiness of Saliency Methods in Radiology AI." Radiology: AI 2024;6(1):e220221, DOI 10.1148/ryai.220221。— [PMC10831523](https://pmc.ncbi.nlm.nih.gov/articles/PMC10831523)（存取 2026-10-31）。洩漏備註：CheXpert 隨機 6:1 切分，**未描述病人層級切分**；無外部資料集驗證。
- 評估指標本身也不穩：文獻中 saliency fidelity 指標計算方式不一致且會顯著改變結果；心理計量信度測試顯示指標可能統計上不可靠，方法排名因此可能不可信。[B] Tomsett R, Harborne D, Chakraborty S, et al. "Sanity Checks for Saliency Metrics." AAAI-20。— [arXiv 1912.01451](https://arxiv.org/abs/1912.01451)（存取 2026-10-31）
- ROAR：在多個大型影像資料集上，許多常用歸因方法**不優於隨機指派重要性**；只有 VarGrad 與 SmoothGrad-Squared 優於隨機。[B] Hooker S, Erhan D, Kindermans P-J, et al. "A Benchmark for Interpretability Methods in Deep Neural Networks." NeurIPS 2019。— [arXiv 1806.10758](https://arxiv.org/abs/1806.10758)（存取 2026-10-31）
- 事後解釋偵測「未知」捷徑的能力很差：feature attribution、concept activation、training-point ranking 三類方法在使用者事先不知道捷徑時大多失效（背景模糊等隱藏偽影最嚴重）；feature attribution 甚至會在模型沒有依賴捷徑時誤示依賴；盲測使用者研究支持此結論；**若使用者已知要找哪個捷徑，解釋才有用**。[B] Adebayo J, Muelly M, Abelson H, Kim B. "Post hoc Explanations may be Ineffective for Detecting Unknown Spurious Correlation." ICLR 2022。— [arXiv 2212.04629](https://arxiv.org/abs/2212.04629)；[MLAnthology](https://mlanthology.org/iclr/2022/adebayo2022iclr-post)（存取 2026-10-31）
- 注意力不是解釋：NLP 任務中學到的注意力常與梯度重要性不相關，且很不同的注意力分布可得相同預測。[B] Jain S, Wallace BC. "Attention is not Explanation." NAACL 2019。— [arXiv 1902.10186](https://arxiv.org/abs/1902.10186)；反駁：是否算解釋取決於定義，並提出四種檢驗（均勻權重基準、跨種子變異校準、凍結預訓練權重診斷、對抗注意力訓練）。[B] Wiegreffe S, Pinter Y. "Attention is not not Explanation." EMNLP 2019。— [arXiv 1908.04626](https://arxiv.org/abs/1908.04626)（存取 2026-10-31）。（此爭議原在 NLP；延伸到 ViT 屬本報告推論。）
- ViT／DINOv2 注意力圖偽影：監督式與自監督 ViT 的特徵圖會在**低資訊的背景區域**出現高範數 token，被網路挪作內部運算；加入額外 register token 可消除並得到更平滑的特徵與注意力圖。[D]（通行引用為 ICLR 2024，本輪未驗證）Darcet T, Oquab M, Mairal J, Bojanowski P. "Vision Transformers Need Registers." — [arXiv 2309.16588](https://arxiv.org/abs/2309.16588)（存取 2026-10-31）。官方 DINOv2 repo 提供 register 版本：ViT-S/14 distilled 21M 參數，無 register linear 81.1%、有 register（`dinov2_vits14_reg`）80.9%；程式與權重 Apache-2.0。[A] — [facebookresearch/dinov2 README](https://github.com/facebookresearch/dinov2)（存取 2026-10-31）
- 立場文章：XAI 不太可能為「個別病人決策」帶來它被期待的信任、透明與偏誤緩解；作者主張以嚴謹內外部驗證取代，並警告不要把可解釋性當作臨床部署的必要條件。[B] Ghassemi M, Oakden-Rayner L, Beam AL. "The false hope of current approaches to explainable artificial intelligence in health care." Lancet Digital Health 2021;3(11):e745–e750, DOI 10.1016/S2589-7500(21)00208-9。— [Europe PMC（PMID 34711379）](https://europepmc.org/article/MED/34711379)（存取 2026-10-31）。**對立觀點**：DeGrave 等認為外部測試不能保證模型依賴醫學相關病理，主張 XAI 應為臨床部署前提。[B] DeGrave AJ, Janizek JD, Lee S-I. "AI for radiographic COVID-19 detection selects shortcuts over signal." Nature Machine Intelligence 2021, DOI 10.1038/s42256-021-00338-7。— [Semantic Scholar 紀錄](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1038/s42256-021-00338-7)（存取 2026-10-31）。兩者不完全矛盾（本報告推論）：Ghassemi 反對把熱圖當**個案層級**信任依據；DeGrave 把 XAI 當**模型層級稽核**工具。

**C. 函式庫（業界作法）**
- pytorch-grad-cam（`pip install grad-cam`，MIT）支援 GradCAM、HiResCAM、GradCAMElementWise、GradCAM++、XGradCAM、AblationCAM、ScoreCAM、EigenCAM、EigenGradCAM、LayerCAM、FullGrad 等；ViT 以 `reshape_transform`（去除 class token 並還原空間）支援，範例 target layer `model.blocks[-1].norm1`；有 Faster-RCNN 與 **YOLOv5 EigenCAM** 教學；內建 ROAD、CamMultImageConfidenceChange 等評估；文件提醒 ScoreCAM 與 AblationCAM 需大量前向傳遞（有批次實作）、`aug_smooth=True` 約增加 6 倍時間；HiResCAM「在某些模型上有可證明的忠實性」。[A]（官方 repo 文件）— [jacobgil/pytorch-grad-cam](https://github.com/jacobgil/pytorch-grad-cam)（存取 2026-10-31；README 未標版本號）
- Captum：Integrated Gradients（Riemann 或 Gauss-Legendre 積分）、Occlusion（「在影像這類鄰近像素高度相關的情況最有用」）、Feature Ablation（可分組遮罩影像區段）、Shapley Value Sampling（完整列舉計算量極大，故抽樣）、GradCAM（限與輸入空間對齊的卷積層、需上採樣）、NoiseTunnel（SmoothGrad／SmoothGrad²／VarGrad）。[A] — [Captum Attribution Algorithms](https://captum.ai/docs/attribution_algorithms)（存取 2026-10-31）
- Ultralytics YOLO：**未找到可靠證據**顯示 Ultralytics 官方內建 Grad-CAM／saliency；本輪只找到 pytorch-grad-cam 的 YOLOv5 EigenCAM 教學（見上）。

### Inferences

**I-1. 方法「是否通過 sanity check」排序（本報告推論，整合上列證據）**

| 等級 | 方法 | 依據 | 備註 |
|---|---|---|---|
| 相對可信（通過參數隨機化，但定位仍差於人類） | Grad-CAM、vanilla gradient | Adebayo 2018 通過；Saporta 2022 為最佳；但 Arun 2021、Zhang 2022/2024 顯示仍有失敗 | Grad-CAM 解析度粗（EfficientNet-B0 在 224 輸入時最後特徵圖為 7×7，依架構推算）；**小病灶**（早期靜脈炎紅斑）正是 Saporta 指出差距最大的情境 |
| 作者自稱通過、獨立驗證有限 | Score-CAM、HiResCAM | Score-CAM 自稱通過（workshop）；HiResCAM 有理論保證（預印本） | 醫學影像的獨立 sanity check：未找到可靠證據 |
| 理論性質好、實證混合 | Integrated Gradients | 滿足公理；但 Saporta 中不如 Grad-CAM、Zhang 2024 PSC 低、Kindermans 指出參考點問題 | 對 baseline（黑圖／模糊圖）選擇敏感 |
| 未通過 | Guided Backprop、Guided Grad-CAM | Adebayo 2018 明確失敗（類邊緣偵測器） | 平台中不應使用 |
| 不應單獨當解釋 | Raw attention、DINOv2 CLS attention | Jain & Wallace；Abnar & Zuidema；Darcet（背景高範數 token） | 若要看 DINOv2，改用 `dinov2_vits14_reg` + rollout 或 Chefer 法，僅作質性參考 |
| 未直接測 | Grad-CAM++、attention rollout、Chefer relevance | Saporta 含 Grad-CAM++ 但次於 Grad-CAM；其餘在醫學影像的 Adebayo 式檢查未找到可靠證據 | — |

**I-2. 逐方法規格（本報告推論；數據來源見上）**

| 方法 | 適用 | 不適用 | 預期效益 | 最少資料 | 串接 | 計算成本 | 風險 |
|---|---|---|---|---|---|---|---|
| Grad-CAM / HiResCAM（EfficientNet-B0） | 研究者除錯、檢查是否落在膠帶／床單 | 小病灶精確定位；給民眾看 | 快速發現明顯捷徑（Winkler 2019 亦用熱圖連結藍色標記與偽陽性） | 任意；但量化需 ≥24 張有框圖 | pytorch-grad-cam：`GradCAM(model=m, target_layers=[m.features[-1]])`（torchvision EfficientNet）；HiResCAM 同介面 | 每張 1 次前向 + 1 次反向；消費級 GPU 上極快 | 粗解析度；「看起來合理」造成確認偏誤；Zhang 2024 顯示可被操弄 |
| Score-CAM / AblationCAM | 想避開梯度飽和 | 線上即時推論 | 圖較乾淨（作者宣稱） | 同上 | pytorch-grad-cam `ScoreCAM`（可設 batch_size） | 約等於最後層通道數次前向（EfficientNet-B0 為 1,280 通道，依架構推算）；120 張可離線跑完 | 獨立驗證少 |
| Integrated Gradients | 要像素級、有公理保證 | baseline 定義不清時 | 精細邊界 | 同上 | Captum `IntegratedGradients(model).attribute(x, baselines=b, target=t)`；可包 `NoiseTunnel` | n_steps 次前向+反向（Captum 預設步數本輪未驗證） | baseline 選擇影響結果；圖雜訊大 |
| Occlusion（Captum 或自製框遮罩） | 檢驗「遮住某區域後預測變多少」——最貼近捷徑測試 | — | 介入式（對該模型而言）證據 | 同上 | Captum `Occlusion` 或以 SQLite 中的框座標遮罩 | 依視窗數，數百次前向；離線可接受 | 遮罩造成分布外影像（ROAD 論文指出遮罩形狀會洩漏資訊） |
| DINOv2 attention / rollout | 質性觀察凍結特徵的關注處 | 解釋「LR 分類器」的決策（注意力與 LR 權重無直接關係） | 低 | — | transformers `output_attentions=True`；建議換 `dinov2_vits14_reg` | 低 | 背景高範數 token（Darcet）被誤讀成「模型看背景」 |
| YOLO EigenCAM | 看偵測骨幹激活 | 類別特定解釋（EigenCAM 取激活第一主成分，與類別無關——依方法原理推論） | 低；YOLO 本身輸出的框就是最直接的定位解釋（呼應 Arun 2021 建議定位用偵測模型） | — | pytorch-grad-cam YOLOv5 教學；與 Ultralytics 8.x 相容性需自測 | 低 | 版本相容性；誤當作類別證據 |

**I-3. NOW vs FUTURE**
- NOW（~120 張、14 病人）：只保留 Grad-CAM（或 HiResCAM）+ Occlusion 作研究者端除錯；每次產生熱圖時同時產生 Adebayo 式「權重隨機化」對照（同圖、隨機初始化模型的熱圖），若兩者 SSIM 很高即標示「此熱圖不可解讀」。不做方法間排名——24 張框圖不足以穩定排序，且指標本身信度有疑（Tomsett 2020）。
- FUTURE（~1,000 張、三類平衡）：可加 Score-CAM、IG 與 Quantus 的 MPRT 系列做系統化比較；有更多框時報告方法間差異的信賴區間。
- 與原則的衝突：無直接衝突；但若把熱圖放到 LINE 回覆，民眾會理解為「AI 看到發炎在這裡」，接近臨床診斷宣稱（見 Q4）。

### Gaps
- 未找到在「皮膚／傷口臨床照片（非皮膚鏡、非放射影像）」上做 Adebayo 式 sanity check 的同儕審查研究——未找到可靠證據。
- 未讀到 Saporta 2022 全文表格（各方法 mIoU／hit rate、與人類差距百分比）；撰寫時不可引用具體百分比。
- DeGrave 2021 內外部 AUC 數字未驗證（medRxiv 403、Nature 重導）。
- Grad-CAM++、attention rollout、Chefer relevance 在醫學影像的獨立 sanity check：未找到可靠證據。
- Captum IG 預設 `n_steps`、Ultralytics 是否內建可解釋性：本輪未驗證。

---

## Q2. 如何量化「模型是否看病灶」：指標、門檻與 24 張框圖的限制

### Takeaway
可用指標有 pointing game（hit rate）、energy-based pointing game／熱圖能量落在框內比例、閾值化熱圖與框的 IoU/Dice、AUPRC、deletion/insertion、ROAR/ROAD；Quantus 已實作多數。**文獻沒有公認的「可接受門檻」**——Saporta 以人類標註者為參照、Arun 以專用定位網路為參照、CheXlocalize 以驗證集調閾值。對只有 ~24 張框圖的本專案，應報告「相對隨機基準與權重隨機化對照的提升」並附病人層級信賴區間，而非絕對門檻。

### Cited Findings
- Pointing game 源自 Excitation Backprop 論文（顯著圖最大值點是否落在標註物件內），用於 MS COCO、PASCAL VOC07、ImageNet 的弱監督定位。[B] Zhang J, Lin Z, Brandt J, et al. "Top-down Neural Attention by Excitation Backprop." ECCV 2016（期刊延伸版書目本輪未驗證）。— [arXiv 1608.00507](https://arxiv.org/abs/1608.00507)（存取 2026-10-31）
- CheXlocalize（Saporta 團隊官方程式）：熱圖轉分割預設用 **Otsu 自動全域閾值**；可選「在驗證集上使 mIoU 最大」的各病灶閾值；可選在預測機率低於門檻時輸出全零遮罩（門檻亦以驗證集 mIoU 調）；指標為 **mIoU（嚴格）** 與 **hit rate（pointing game，寬鬆）**；有計算「相對人類基準下降百分比」的腳本。[A]（官方程式庫文件）— [rajpurkarlab/cheXlocalize](https://github.com/rajpurkarlab/cheXlocalize)（存取 2026-10-31）
- Arun 2021 以像素層級 AUPRC 與 SSIM（重複性／再現性）評估，並以 U-Net／RetinaNet 為參照上限（數字見 Q1）。[B] — [Europe PMC API](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%2210.1148/ryai.2021200267%22&resultType=core)（存取 2026-10-31）
- RISE 以隨機遮罩探測黑箱模型，並用 **deletion／insertion** 指標與以人類標註區段計算的 pointing 指標評估。[D]（通行引用 BMVC 2018，本輪未驗證）Petsiuk V, Das A, Saenko K. — [arXiv 1806.07421](https://arxiv.org/abs/1806.07421)（存取 2026-10-31）
- ROAR（移除重要像素後**重訓**看準確率下降）顯示多數方法不優於隨機。[B] Hooker et al. NeurIPS 2019 — [arXiv 1806.10758](https://arxiv.org/abs/1806.10758)
- ROAD：像素擾動評估會透過「被移除像素的形狀」洩漏資訊；ROAD（Remove and Debias）提升一致性、無需重訓、計算量比既有方法最多降低 99%。[B] Rong Y, Leemann T, Borisov V, et al. ICML 2022。— [arXiv 2202.00449](https://arxiv.org/abs/2202.00449)（存取 2026-10-31）。pytorch-grad-cam 已內建 ROAD（MoRF／LeRF／組合）。[A] — [pytorch-grad-cam](https://github.com/jacobgil/pytorch-grad-cam)
- Score-CAM 論文的 energy-based pointing game：**本輪只驗證 Score-CAM 摘要，未讀到該指標原文定義**；Quantus 中概念相近的實作為 "Attribution Localisation"／"Relevance Mass Accuracy"（概念對應為本報告推論）。
- Quantus 指標分類：Faithfulness（Faithfulness Correlation、Pixel Flipping、Infidelity、ROAD、Sufficiency）、Robustness（Local Lipschitz、Max/Avg-Sensitivity、Relative Input Stability）、**Localisation（Pointing Game、Attribution Localisation、Top-K Intersection、Relevance Rank Accuracy、Relevance Mass Accuracy、AUC、Focus）**、Complexity、**Randomisation（MPRT、Smooth MPRT、Efficient MPRT、Random Logit）**、Axiomatic；支援 PyTorch／TensorFlow，內建 Captum、tf-explain、Zennit；**README 明示「實作未經原作者驗證」，並要求記錄 Quantus 版本以利重現**。[B] Hedström A, et al. "Quantus: An Explainable AI Toolkit for Responsible Evaluation of Neural Network Explanations and Beyond." JMLR 2023;24(34):1–11。— [Quantus GitHub](https://github.com/understandable-machine-intelligence-lab/Quantus)（存取 2026-10-31）
- 指標本身的信度問題：Tomsett 2020（見 Q1）。[B] — [arXiv 1912.01451](https://arxiv.org/abs/1912.01451)
- Saporta：模型信心與 Grad-CAM 定位表現正相關——只評估高信心正確樣本會高估定位能力（後半句為本報告推論）。[B] — [Semantic Scholar](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1038/s42256-022-00536-x)

### Inferences
- **門檻設定方式（本報告推論）**：文獻未提供可移植到靜脈炎照片的絕對門檻。建議三層參照：
  1. **隨機基準**：pointing game 的隨機命中率 = 框面積／影像面積；能量比例的隨機期望值也等於框面積比例。報告「lift = 實測值／框面積比例」。
  2. **權重隨機化對照**（Adebayo；Quantus MPRT）：同一指標在隨機權重模型上的值；訓練後模型須明顯高於它，否則熱圖不可解讀。
  3. **人類基準**（FUTURE）：請第二位標註者獨立畫框，兩人框的 IoU 作為上限（Saporta 作法）。
- **建議的內部暫定門檻（本報告推論，非文獻值，報告中須標示為內部約定）**：
  - Pointing game：hit rate 的 95% CI 下界 > 平均框面積比例（隨機命中率）。
  - 熱圖能量落在框內比例：中位 lift ≥ 2。
  - IoU：以 Otsu 閾值（沿用 CheXlocalize 預設）計算並描述性報告；**不以 IoU≥0.5（物件偵測慣例）作為顯著圖合格線**，因 Saporta／Arun 均顯示顯著圖遠不及專用定位，用 0.5 幾乎必然全數失敗而失去鑑別力。
  - Deletion：刪除熱圖前 10% 像素後的預測機率下降，應大於刪除隨機 10% 像素（配對比較，Wilcoxon）。
- **24 張框圖的統計限制（本報告計算）**：若 24 張中 18 張命中（75%），Wilson 95% CI 約 55%–88%；任何單一數字都帶 ±15–20 個百分點的不確定性。14 位病人、同病人多張 → 必須以**病人為單位**做 cluster bootstrap，否則 CI 過窄。
- **NOW**：只算 pointing game + 能量比例 lift + 權重隨機化對照，配 cluster bootstrap CI；同時報告「預測錯誤」樣本（避免 Saporta 指出的信心偏差）。ROAR 需重訓，NOW 不做；ROAD 可做但結論只供參考。計算成本：120 張 Grad-CAM 在單張消費級 GPU 上分鐘級可完成（本報告推論）。
- **FUTURE（~1,000 張）**：若框圖增至約 150–200 張（本報告建議目標，非文獻值），可加 IoU/Dice、AUPRC、Quantus Localisation 全套與 MPRT，並做方法間比較；ROAR 可在離線、**人工啟動並記錄**的條件下做一次（不違反「不自動訓練」原則）。
- **串接**：pytorch-grad-cam 產生 numpy 熱圖 → 用 SQLite 已存的框座標計算指標 → 寫回 SQLite 評估表 → React 顯示；Quantus 可直接接 Captum 歸因。必須記錄 grad-cam、Captum、Quantus 版本號。

### Gaps
- 未找到針對「臨床照片中發炎病灶」設定顯著圖定位門檻的文獻——未找到可靠證據。
- Score-CAM energy-based pointing game 原文定義、Saporta 的 hit rate／mIoU 實際數值：本輪未讀全文。
- CAM／Grad-CAM 原論文熱圖轉框所用的最大值百分比閾值：本輪未驗證，勿引用。

---

## Q3. 捷徑學習：證據、偵測、緩解與檢核清單

### Takeaway
研究證據顯示醫學影像模型會利用醫院來源、掃描機型、皮膚標記、色卡貼片、背景皮膚質地與色彩平衡等非病理特徵，且內部測試看不出來（Zech、Badgeley、Winkler、Nauta、DeGrave）。本專案「E-Da 醫院 vs LINE 民眾」若與標籤相關，即為 Zech 型來源混淆；膠帶、敷料、針頭、筆跡、尺、手圈對應 Winkler／Nauta 型人工物捷徑。在 14 位病人規模下，最可行的是「分層成效 + 遮罩反事實測試 + 從特徵／metadata 預測混淆因子」，而非 group DRO 等需較多資料的方法。

### Cited Findings

**A. 概念與醫學案例**
- 捷徑定義：在標準基準上表現好、在更嚴苛（真實世界）條件下失敗的決策規則；作者提出模型解讀與基準設計建議。[B] Geirhos R, Jacobsen J-H, Michaelis C, Zemel R, Brendel W, Bethge M, Wichmann FA. "Shortcut learning in deep neural networks." Nature Machine Intelligence 2020, DOI 10.1038/s42256-020-00257-z。— [arXiv 2004.07780](https://arxiv.org/abs/2004.07780)（存取 2026-10-31）
- 醫院混淆：158,323 張胸片（NIH 112,120 張／30,805 人；Mount Sinai 42,396／12,904；Indiana 3,807／3,683）；肺炎盛行率 Mount Sinai 34.2%、NIH 1.2%、Indiana 1.0%；**只用「哪家醫院」排序即得 AUC 0.861（95% CI 0.855–0.866）**；合併訓練模型內部 AUC 0.931 → 外部 Indiana 0.815（P=0.001）；**CNN 辨識醫院系統準確率 99.95%（NIH，22,050/22,062）與 99.98%（Mount Sinai，8,386/8,388）**；5 個自然比較中 3 個外部表現較差；訓練站點盛行率相同時外部表現一致（P=0.88）。[B] Zech JR, Badgeley MA, Liu M, Costa AB, Titano JJ, et al. "Variable generalization performance of a deep learning model to detect pneumonia in chest radiographs: A cross-sectional study." PLOS Medicine 2018;15(11):e1002683, DOI 10.1371/journal.pmed.1002683。— [PLOS](https://journals.plos.org/plosmedicine/article?id=10.1371/journal.pmed.1002683)；摘要經 [Europe PMC API](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%2210.1371/journal.pmed.1002683%22&resultType=core) 驗證（存取 2026-10-31）。備註：有外部驗證（Indiana）。
- 髖部骨折混淆：17,587 張 X 光；影像可預測全部 20 個病人／流程變項，最佳為掃描機型 AUC 1.00、廠牌 0.98、急件狀態 0.79；骨折僅影像 AUC 0.78，加病人資料 0.86、再加流程資料 0.91；在病人變項平衡的測試集降到 0.67；**在病人與流程變項皆平衡的測試集降到 0.52（95% CI 0.46–0.58，等同機率）**。[B] Badgeley MA, Zech JR, Oakden-Rayner L, Glicksberg BS, Liu M, et al. npj Digital Medicine 2019;2:31, DOI 10.1038/s41746-019-0105-1。— [Europe PMC（PMID 31304378）](https://europepmc.org/article/MED/31304378)（存取 2026-10-31）。備註：病人層級切分本輪未驗證；「平衡測試集」本身就是偵測方法。
- 皮膚標記：歐盟核准為醫療器材的 CNN（訓練 >120,000 張皮膚鏡影像），130 個黑色素細胞病灶（107 良性痣、23 黑色素瘤），同一病灶分別拍無標記、有龍膽紫標記、裁切去標記三組；**無標記 sens 95.7%、spec 84.1%、AUC 0.969；有標記 sens 100%、spec 45.8%（P<.001）、AUC 0.922；裁切後 sens 100%、spec 97.2%、AUC 0.993**；熱圖顯示藍色標記與偽陽性相關；作者建議供 CNN 分析的影像應避免皮膚標記。[B] Winkler JK, Fink C, Toberer F, Enk A, Deinlein T, et al. JAMA Dermatology 2019;155(10):1135–1141, DOI 10.1001/jamadermatol.2019.1735。— [Europe PMC API](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%2210.1001/jamadermatol.2019.1735%22&resultType=core)（存取 2026-10-31）。備註：同病灶配對設計（模型為外部訓練，無訓練／測試洩漏問題）；僅 23 例黑色素瘤、CI 寬；**是本專案「筆跡／皮膚標記」與「裁切至病灶」兩項的最直接類比證據**。
- 色卡貼片：ISIC 中彩色校正貼片只出現在良性影像；VGG16 分類器部分依賴貼片判良性；在惡性影像插入貼片顯著增加誤判；以良性皮膚組織 **inpainting** 移除貼片並重訓可去偏。[C] Nauta M, Walsh R, Dubowski A, Seifert C. Diagnostics 2021;12(1):40, DOI 10.3390/diagnostics12010040。— [Europe PMC（PMID 35054207）](https://europepmc.org/article/MED/35054207)（存取 2026-10-31）。備註：病人層級切分與外部驗證本輪未驗證。
- 去除病灶仍可分類：模型在**沒有臨床上有意義的病灶資訊**時仍能分類皮膚病灶，甚至超過以皮膚科醫師為基準的 AI 表現，顯示虛假相關；加入臨床資訊幾乎無改善。[C] Bissoto A, Fornaciali M, Valle E, Avila S. "(De)Constructing Bias on Skin Lesion Datasets." ISIC Workshop @ CVPR 2019。— [arXiv 1904.08818](https://arxiv.org/abs/1904.08818)（存取 2026-10-31；摘要無數字）
- 分析七種可作為捷徑的視覺人工物（具體清單本輪未讀全文），套用 SOTA 去偏方法並提出偵測偏誤的測試集；結論是**現有去偏方法尚不足以解決皮膚病灶模型的偏誤**。[C] Bissoto A, Valle E, Avila S. "Debiasing Skin Lesion Datasets and Models? Not So Fast." ISIC Workshop @ CVPR 2020。— [arXiv 2004.11457](https://arxiv.org/abs/2004.11457)（存取 2026-10-31）
- 尺：Narla 等 2018 評論確為 J Invest Dermatol 138(10):2108–2110（DOI 10.1016/j.jid.2018.06.175）[C]，但**本輪取得的摘要未提及尺**；「Esteva 分類器較傾向把有尺的影像判為惡性」之說未經本輪核實原文，撰寫時須標示為「常被引用、本報告未核實」。— [Europe PMC API](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%2210.1016/j.jid.2018.06.175%22&resultType=core)（存取 2026-10-31）
- 隱藏分層：模型在訓練／測試未識別的重要子群表現差；出現在低盛行、低標籤品質、細微特徵或有虛假相關的子群；臨床重要子群相對表現差異超過 20%。[C] Oakden-Rayner L, Dunnmon J, Carneiro G, Ré C. ACM CHIL 2020:151–159, DOI 10.1145/3368555.3384468。— [Europe PMC（PMID 33196064）](https://europepmc.org/article/MED/33196064)（存取 2026-10-31）
- COVID 胸片：模型依賴混淆因子而非病理，看似準確但換醫院即失效；外部測試不保證模型依賴醫學相關特徵。[B] DeGrave et al. NMI 2021 — [Semantic Scholar](https://api.semanticscholar.org/graph/v1/paper/DOI:10.1038/s42256-021-00338-7)（具體數字未驗證）
- 生成式 AI 稽核：結合皮膚科醫師與生成反事實影像，稽核 5 個區分黑色素瘤與相似病灶的分類器（皮膚鏡與臨床照片）；分類器依賴臨床有意義特徵（病灶色素型態），也依賴**背景皮膚質地與色彩平衡**等不良特徵。[B] DeGrave AJ, Cai ZR, Janizek JD, Daneshjou R, Lee S-I. "Auditing the inference processes of medical-image classifiers by leveraging generative AI and the expertise of physicians." Nature Biomedical Engineering（線上 2023；卷期 2025;9(3):294–306），DOI 10.1038/s41551-023-01160-9。— [Europe PMC（PMID 38155295）](https://europepmc.org/article/MED/38155295)（存取 2026-10-31）。與本專案直接相關（推論）：背景皮膚與色彩平衡在 E-Da 與 LINE 手機照片間幾乎必然不同。

**B. 偵測方法證據**
- 從影像預測混淆因子：模型可從醫學影像預測自我報告種族（外部驗證 X 光 AUC 0.91–0.99、胸部 CT 0.87–0.96、乳房攝影 0.81），而 BMI（0.55）、疾病分布（0.61）、乳房密度（0.61）等可能中介變項預測力差；影像裁切或損壞後仍可偵測。[B] Gichoya JW, Banerjee I, Bhimireddy AR, Burns JL, Celi LA, et al. Lancet Digital Health 2022;4(6):e406–e414, DOI 10.1016/S2589-7500(22)00063-2。— [Europe PMC API](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=TITLE:%22AI%20recognition%20of%20patient%20race%20in%20medical%20imaging%22&resultType=core)（存取 2026-10-31）。Zech（醫院 99.95%／99.98%）、Badgeley（掃描機型 AUC 1.00）屬同類證據。
- 測試集重抽樣 + 模型檢視：結合 test-set resampling、遷移學習、多任務學習與模型檢視研究受保護特徵的編碼；修正族群與盛行率偏移後部分子群差異消失；**單靠遷移學習無法判斷模型是否使用病人資訊**（即「可預測 ≠ 被使用」）。[C] Glocker B, Jones C, Bernhardt M, Winzeck S. eBioMedicine 2023;89:104467, DOI 10.1016/j.ebiom.2023.104467。— [Europe PMC API](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=TITLE:%22Algorithmic%20encoding%20of%20protected%20characteristics%20in%20chest%20X-ray%22&resultType=core)（存取 2026-10-31）
- 背景依賴：模型僅用背景即有「非平凡」準確率；前景分類正確但背景被對抗挑選時誤判最高 87.5%；較準確的模型較少依賴背景。[D]（通行引用 ICLR 2021，未驗證）Xiao K, Engstrom L, Ilyas A, et al. "Noise or Signal: The Role of Image Backgrounds in Object Recognition." — [arXiv 2006.09994](https://arxiv.org/abs/2006.09994)（存取 2026-10-31）
- Slice discovery：Domino 以跨模態嵌入發現系統性錯誤；在 1,235 個設定（自然、醫學、時間序列）中找出 36% 的 slice，比先前方法高 12 個百分點，並在 35% 設定中以自然語言精確描述 slice。[B] Eyuboglu S, Varma M, Saab K, et al. ICLR 2022（Oral）。— [arXiv 2203.14960](https://arxiv.org/abs/2203.14960)（存取 2026-10-31）
- 事後解釋偵測未知捷徑效果差（Adebayo 2022，見 Q1）→ 偵測應以「已知候選混淆因子清單 + 介入式測試」為主（後半句為本報告推論）。[B] — [arXiv 2212.04629](https://arxiv.org/abs/2212.04629)

**C. 緩解方法證據**
- Group DRO：在過參數化網路上單純 group DRO 會失敗（可完美擬合訓練資料）；**需較強正則化（較大 L2 或 early stopping）**，最差群組準確率提升 10–40 個百分點，平均準確率維持。[B]（通行引用 ICLR 2020，arXiv feed 未列 venue）Sagawa S, Koh PW, Hashimoto TB, et al. — [arXiv 1911.08731](https://arxiv.org/abs/1911.08731)（存取 2026-10-31）。需要群組標籤。
- JTT：先 ERM 訓練數 epoch，再上調誤分類樣本權重；四個任務平均縮小 ERM 與 group DRO 之間 75% 的最差群組差距；只需小型驗證集上的群組標籤供調參。[B] Liu EZ, Haghgoo B, Chen AS, et al. ICML 2021。— [arXiv 2107.09044](https://arxiv.org/abs/2107.09044)（存取 2026-10-31）
- 解釋懲罰（CDEP）：以正則化懲罰模型對已知錯誤特徵的解釋，在玩具與真實資料提升準確率（具體資料集與數字本輪未驗證）；ICML 版附勘誤更正 Table 1 數字但趨勢不變。[B] Rieger L, Singh C, Murdoch WJ, et al. ICML 2020。— [arXiv 1909.13584](https://arxiv.org/abs/1909.13584)（存取 2026-10-31）
- Inpainting 移除人工物並重訓（Nauta 2021）；裁切去除標記使 spec 由 45.8% 回到 97.2%（Winkler 2019）（見上）。
- 反證：Bissoto 2020 指出現有去偏方法「尚未準備好」。[C] — [arXiv 2004.11457](https://arxiv.org/abs/2004.11457)

### Inferences

**I-1. 本專案捷徑學習檢核清單（混淆因子｜如何檢查｜可接受門檻）**
所有門檻為**本報告提出的內部研究約定**，非文獻標準；文獻只提供「方法」與「失敗量級」。所有檢查一律用**病人分組交叉驗證（GroupKFold by patient）**並以 cluster bootstrap 報告 CI。

| # | 混淆因子 | 文獻類比 | 如何檢查 | 可接受門檻（內部約定） | NOW 可行？ |
|---|---|---|---|---|---|
| 1 | 資料來源（E-Da vs LINE） | Zech 2018；Badgeley 2019 | (a) 來源 × 標籤 × 分期列聯表；(b) DINOv2 嵌入 + LR 預測來源；(c) 各來源分開報告成效 | (a) 若某標籤幾乎只來自單一來源 → 判定「病變與來源無法區分」，只能報告來源內結果；(b) 來源可預測本身不算失敗（Zech 中 >99.9%），但必須搭配 (c)；(c) 任一來源內 AUC 的 CI 包含 0.5 → 不得宣稱跨來源有效 | 是（LINE 數量少時 (c) 只能描述） |
| 2 | 膠帶／透明敷料 | Nauta 2021（貼片）；Winkler 2019 | 人工標註有／無；分層成效；遮罩膠帶後 Δp | 記錄兩層陽性率差；遮罩後預測翻轉率 ≤10%、中位 \|Δp\| ≤0.1 | 是（需人工標註） |
| 3 | IV 針頭／導管 | 同上；「有導管＝住院中＝較可能發炎」為合理混淆路徑（推論） | 同上；Grad-CAM 能量落在導管框的比例 | 導管框內能量 lift <2 | 是 |
| 4 | 床單／背景／拍攝環境 | Xiao 2020；DeGrave 2023 | **背景-only 模型**：病灶與手臂區塗灰，只用背景訓練／評估 | 背景-only AUC 的 95% CI 包含 0.5，或點估計 ≤0.6 | 部分（需手臂粗遮罩） |
| 5 | 筆跡／皮膚標記（圈出紅腫範圍的筆線） | Winkler 2019（spec 84.1%→45.8%） | 人工標註；有筆跡 vs 無筆跡的偽陽性率；inpaint 筆跡後重測 | 有筆跡組偽陽性率不顯著高於無筆跡組；inpaint 後翻轉率 ≤10% | 是（**高優先**：臨床常以筆圈出紅腫範圍，與陽性高度相關——推論） |
| 6 | 尺／量尺 | Narla 2018（未核實） | 同 #5 | 同 #5 | 是 |
| 7 | 醫院手圈 | Zech 型（指示住院／來源） | 遮罩手圈後 Δp；分層 | 翻轉率 ≤10% | 是 |
| 8 | 光線、白平衡、手機型號、解析度、JPEG 壓縮（LINE 會重新壓縮——推論） | DeGrave 2023（色彩平衡）；Badgeley（機型 AUC 1.00） | 只用 metadata（解析度、檔案大小、EXIF 機型、平均色彩）預測標籤 | metadata-only AUC 的 CI 包含 0.5 | 是（便宜，**應最先做**） |
| 9 | 病人身分（同病人多張） | 一般資料洩漏原則（推論） | 所有切分以病人分組；比較隨機切分 vs 病人切分差距 | 只接受病人分組結果；差距大時列為洩漏證據 | 是（**必做**） |
| 10 | 時間／病程（同病人先後照片分期不同） | Oakden-Rayner 2020 | 依拍攝時間分層；檢查是否學到「同一手臂外觀」 | 須在病人分組下評估 | 是 |
| 11 | 標籤生成方式（E-Da 檔名規則 vs LINE 人工審閱） | Oakden-Rayner 2020（低標籤品質子群） | 抽樣由第二位審閱者複核，算一致性 | 報告不一致率；**不得**以模型預測回填標籤 | 是（小規模抽樣） |
| 12 | 構圖：病灶大小、拍攝距離、手臂部位 | Saporta（小病灶定位差） | 依框面積分層 | 描述性報告 | 部分 |
| 13 | 膚色 | DeGrave 2023（背景皮膚） | 描述分布；FUTURE 分層 | NOW 只描述；FUTURE 子群 CI 重疊 | 僅描述 |

**I-2. 偵測方法逐項規格（本報告推論）**

| 方法 | 支持證據 | 反證／失敗 | 適用 | 不適用 | 預期效益 | 最少資料 | 串接 | 成本 | 風險 |
|---|---|---|---|---|---|---|---|---|---|
| metadata 分層成效 | Zech、Badgeley、Oakden-Rayner | 子群太小 → CI 無意義 | 已知候選因子 | 未知因子 | 高 | 每層至少數名病人；NOW 多數只能描述 | scikit-learn + SQLite metadata 欄位 | 極低 | 多重比較；小樣本假陰性 |
| 遮罩／反事實（遮病灶、遮人工物、inpainting） | Winkler（裁切）、Nauta（插入／inpaint 貼片）、DeGrave 2023 | 遮罩造成分布外（ROAD 論文） | 已知人工物位置 | 人工物與病灶重疊 | 高；介入式證據 | 1 張即可做；24 張框立即可用 | OpenCV `cv2.inpaint` 或灰塊，本地執行 | 低 | 灰塊本身成新捷徑；生成式 inpainting 須本地模型（不可上雲端） |
| 背景-only／去病灶模型 | Bissoto 2019；Xiao 2020 | 需重訓 | 有手臂／病灶遮罩 | 遮罩品質差 | 高 | NOW 可做但 CI 寬 | 同訓練流程、換輸入 | 中 | 屬「訓練」，須人工觸發與記錄 |
| 從嵌入預測混淆因子 | Zech、Badgeley、Gichoya | Glocker：可預測 ≠ 被使用 | DINOv2 凍結特徵現成 | — | 中；風險提示 | NOW 可做 | DINOv2 嵌入 + `LogisticRegression` + `GroupKFold` | 極低 | 被誤讀為「模型一定用了」 |
| Domino／slice discovery | Domino（36%、+12pp） | 設計於大資料；Adebayo 2022 | FUTURE | NOW（120 張難成穩定 slice） | 中 | 推論：數百張以上 | 需本地跨模態（CLIP 類）模型；**不可呼叫雲端 API** | 中 | 誤導性 slice 描述 |
| 錯誤畫廊聚類（專案已有 gallery） | 業界作法 | 主觀 | NOW | — | 中；產生假設 | 任意 | gallery 加 metadata 篩選與 DINOv2 嵌入 k-means | 低 | 確認偏誤 |
| Grad-CAM 落在人工物 | Winkler 以熱圖連結標記 | Adebayo 2022；Zhang 2024 | 已知人工物框 | 未知捷徑 | 低–中 | 需人工物框 | pytorch-grad-cam + 框 | 低 | 熱圖本身不可靠（Q1） |

**I-3. 緩解方法逐項規格（本報告推論）**

| 方法 | 證據 | 反證 | NOW | FUTURE | 成本 | 原則衝突／風險 |
|---|---|---|---|---|---|---|
| 病灶裁切／ROI 輸入 | Winkler 裁切後 spec 97.2%、AUC 0.993 | 裁切丟失周邊脈絡（靜脈走向、紅腫延伸範圍）——推論；推論時也需框 | 作為**對照組**：全圖 vs 裁切成效差 | 主要候選管線：YOLO 框（人工確認）→ 分類 | 低 | YOLO 框須人工確認才當輸入（符合原則） |
| 標準化拍照流程（不畫筆跡、移除尺／手圈、固定背景與光源） | Winkler 作者建議避免標記 | Nauta：**色卡本身曾成為捷徑**——若加色卡，各類別必須一致出現 | 立即可推行（LINE 投稿說明、病房 SOP） | 同 | 極低 | 無 |
| 人工物標註（每張勾選膠帶／針頭／筆跡／尺／手圈／背景類型） | 所有分層與群組方法的前提 | 人力成本 | **最高優先** | 持續 | 人力 | 無 |
| 來源平衡抽樣 | Zech（盛行率相同時外部一致，P=0.88） | 小資料下平衡＝丟資料 | 有限 | 是 | 低 | 無 |
| 背景隨機化／人工物 inpainting 增強 | Nauta；Xiao | Bissoto 2020 | 可小規模試 | 是 | 中 | 生成模型須本地；增強影像**不得**混入真實資料統計或當作新標註 |
| Group DRO | Sagawa：worst-group +10–40pp（需強正則化） | 需群組標籤；過參數化下單純版會失敗 | **不建議**（14 病人，群組極小） | 可考慮（群組＝來源×人工物） | 中 | 訓練須人工觸發 |
| JTT | Liu 2021：縮小 75% 差距 | 小資料上調權重易放大標籤雜訊（推論） | 不建議 | 可考慮 | 中（訓兩次） | 同上；**不得自動化成持續重訓** |
| CDEP 解釋懲罰 | Rieger 2020 | 需已知錯誤特徵遮罩 | 不建議 | 可試 | 中 | 同上 |

**I-4. NOW vs FUTURE 總結（本報告推論）**
- NOW：(1) 人工物與來源標註；(2) 病人分組切分；(3) metadata-only 與 embedding→來源／標籤 檢查；(4) 24 張框圖做遮病灶／遮人工物反事實測試；(5) 全圖 vs 裁切對照。不做 group DRO、JTT、Domino。所有結果只能寫「在本資料中觀察到／未觀察到 X」，**不能寫「模型沒有捷徑」**（Adebayo 2022；Geirhos 2020）。
- FUTURE：加子群 CI、本地 Domino、背景-only 模型、人工觸發的 group DRO／JTT 實驗；盡可能取得第二家醫院或時間外的測試集做外部驗證（Zech、DeGrave 2021 顯示內部驗證不足）。
- 原則衝突提醒：(a) 自動以錯誤樣本重訓（如自動化 JTT）違反「不自動訓練」；(b) 以雲端生成服務做反事實（DeGrave 2023 類作法）違反「不上傳研究照片」；(c) 以模型預測回填標籤違反「不偽造標籤」；(d) 在研究成果中宣稱「已排除捷徑」屬誇大成效。

### Gaps
- 靜脈炎或 IV 部位照片的捷徑學習研究：未找到可靠證據。
- Bissoto 2019/2020 具體數字與七種人工物清單：本輪只讀摘要。
- Narla 2018 關於尺的說法：未核實原文。
- DeGrave 2021 具體 AUC 下降：未驗證。
- 各檢查的可接受門檻在文獻中無標準：未找到可靠證據；表中門檻皆為內部約定。

---

## Q4. 如何向使用者呈現解釋：是否該給 LINE 民眾看熱圖？自動化偏誤證據

### Takeaway
研究證據顯示解釋會提高人對 AI 建議的接受度，**不論 AI 是否正確**（Bansal CHI 2021）；局部（框／特徵型）解釋提升「快速順從」型信任且與 AI 對錯無關，影響有時發生在醫師未察覺時（Prinster Radiology 2024）；非專家從「正確」解釋性建議中獲益最多（Gaube 2023）。加上 Q1 的熱圖不可靠證據，本報告建議：**不對 LINE 民眾顯示熱圖或機率**，熱圖只在研究者介面、獨立判讀之後顯示，並附「研究用、非診斷」警語。

### Cited Findings
- 解釋增加接受度而非互補效能：三個資料集的使用者研究中，AI 協助帶來團隊增益，但**解釋沒有增加增益**，而是讓人更可能接受 AI 建議，**不論建議是否正確**。[B] Bansal G, Wu T, Zhou J, et al. "Does the Whole Exceed its Parts? The Effect of AI Explanations on Complementary Team Performance." CHI 2021。— [arXiv 2006.14779](https://arxiv.org/abs/2006.14779)（存取 2026-10-31；非醫療任務、摘要無數字）
- 解釋類型影響醫師：多中心前瞻隨機研究（2022 年 4–9 月），220 位醫師（放射科為任務專家；內科與急診為非專家）；AI 正確時，局部（特徵型、框）解釋比全域（原型）解釋準確率較高（β=0.86，adjusted P<.001）；局部解釋減少考慮 AI 建議的時間（β=−0.19，P=.01）；**局部解釋使醫師更快與 AI 一致（simple trust）且與 AI 是否正確無關（β=1.32，P=.048）**；解釋類型與 AI 信心對主觀信心與感知有用性無顯著影響；作者結論：影響有時發生在醫師未察覺時。[B] Prinster D, Mahmood A, Saria S, Jeudy J, Lin CT, et al. "Care to Explain? AI Explanation Types Differentially Impact Chest Radiograph Diagnostic Performance and Physician Trust in AI." Radiology 2024;313(2):e233261, DOI 10.1148/radiol.233261。— [Europe PMC API](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=AUTH:%22Prinster%20D%22&resultType=core)（存取 2026-10-31）。備註：使用模擬 AI 工具（ChestAId），非真實模型。
- 非專家受益於正確的解釋性 AI：醫師閱讀胸片時收到**正確**建議，操弄是否附視覺標註、以及標示來源為 AI 或放射師；附標註的 AI 建議得到最高診斷準確率；醫師評 AI 建議品質高於人類建議；兩項操弄對信心影響不大；**非任務專家受益明顯，任務專家效果較小**。[C] Gaube S, Suresh H, Raue M, Lermer E, Koch TK, et al. Scientific Reports 2023;13:1383, DOI 10.1038/s41598-023-28633-w。— [Europe PMC（PMID 36697450）](https://europepmc.org/article/MED/36697450)（存取 2026-10-31）。備註：只給正確建議，無法直接評估錯誤建議下的順從。
- 領域化解釋提升信任：與皮膚科醫師推理一致的 XAI 比傳統 AI 顯著提升皮膚科醫師的診斷信心與信任。[B] Chanda T, Hauser K, Hobelsberger S, Bucher TC, Garcia CN, et al. Nature Communications 2024;15:524, DOI 10.1038/s41467-023-43095-4。— [Europe PMC（PMID 38225244）](https://europepmc.org/article/MED/38225244)（存取 2026-10-31）。在本專案脈絡，「信任提升」在模型未驗證時反而是風險（本報告推論）。
- 顯著圖可被操弄而預測不變，放射師僅辨識出 23.3%／44.8% 被改影像（Zhang 2024，見 Q1）。[B] — [PMC10831523](https://pmc.ncbi.nlm.nih.gov/articles/PMC10831523)
- 不應以解釋作為個別病人決策的信任依據（Ghassemi 2021，見 Q1）。[B] — [Europe PMC](https://europepmc.org/article/MED/34711379)

### Inferences
- **LINE 民眾端（本報告推論）**：不顯示熱圖、機率或分期；回覆以「已收到、研究團隊將人工審閱、如有紅腫熱痛請洽醫護人員」類非診斷文字為主。理由：(1) 民眾是非專家，屬 Bansal／Gaube 中最易受解釋影響的族群；(2) 熱圖本身不可靠（Q1）；(3) 熱圖等同「AI 指出發炎位置」，與「不做臨床診斷宣稱」原則**衝突**；(4) 本專案無外部驗證、無已驗證成效。
- **研究者／醫護審閱端**：可顯示熱圖，但 (a) 預設摺疊；(b) 並列權重隨機化對照或 sanity 指標，避免單看一張圖；(c) **先讓審閱者獨立判讀，再顯示模型建議與熱圖**以降低錨定（推論；本領域直接證據未找到）；(d) 每張熱圖標示「研究用、定位能力未驗證」；(e) 審閱者的確認／否決寫入 SQLite，作為「人工確認」稽核軌跡（符合原則）。
- **呈現格式**：要給醫護看定位時，以 YOLO 框（經人工確認）優先於顯著圖（Arun 2021 建議定位用偵測模型）；但 Prinster 2024 顯示框式局部解釋也會提高不論對錯的順從，所以框同樣要在獨立判讀之後才顯示。
- NOW 與 FUTURE 在此問題上答案相同：即使資料增加，在沒有外部驗證與相關法規審查前，民眾端都不應顯示。

### Gaps
- 一般民眾（病人）觀看醫療 AI 熱圖對自我照護決策的影響：未找到可靠證據（Bansal 受試者為群眾但非醫療任務）。
- 傷口／靜脈炎照片上「先獨立判讀再顯示 AI」的效果：未找到可靠證據。
- 本輪未查監管文件（如 FDA／TFDA 對臨床決策支援解釋的指引）；若報告需要須另行查證。

### 參考文獻總表（全部問題共用；作者、年份、標題、出處、DOI/URL、分級；存取 2026-10-30／31）
1. [B] Adebayo J, Gilmer J, Muelly M, Goodfellow I, Hardt M, Kim B. 2018. Sanity Checks for Saliency Maps. NeurIPS 2018. https://arxiv.org/abs/1810.03292
2. [B] Adebayo J, Muelly M, Abelson H, Kim B. 2022. Post hoc Explanations may be Ineffective for Detecting Unknown Spurious Correlation. ICLR 2022. https://arxiv.org/abs/2212.04629
3. [D] Kindermans P-J, Hooker S, Adebayo J, et al. 2017. The (Un)reliability of saliency methods. https://arxiv.org/abs/1711.00867
4. [B] Saporta A, Gui X, Agrawal A, et al. 2022. Benchmarking saliency methods for chest X-ray interpretation. Nat Mach Intell. DOI 10.1038/s42256-022-00536-x
5. [B] Arun N, Gaw N, Singh P, et al. 2021. Assessing the Trustworthiness of Saliency Maps for Localizing Abnormalities in Medical Imaging. Radiol Artif Intell 3(6):e200267. DOI 10.1148/ryai.2021200267
6. [B] Zhang J, Chao H, Dasegowda G, Wang G, Kalra MK, Yan P. 2022. Overlooked Trustworthiness of Saliency Maps. MICCAI 2022, LNCS 13433:451–461. DOI 10.1007/978-3-031-16437-8_43
7. [B] Zhang J, Chao H, Dasegowda G, Wang G, Kalra MK, Yan P. 2024. Revisiting the Trustworthiness of Saliency Methods in Radiology AI. Radiol Artif Intell 6(1):e220221. DOI 10.1148/ryai.220221
8. [B] Ghassemi M, Oakden-Rayner L, Beam AL. 2021. The false hope of current approaches to explainable artificial intelligence in health care. Lancet Digit Health 3(11):e745–e750. DOI 10.1016/S2589-7500(21)00208-9
9. [B] Jain S, Wallace BC. 2019. Attention is not Explanation. NAACL 2019. https://arxiv.org/abs/1902.10186
10. [B] Wiegreffe S, Pinter Y. 2019. Attention is not not Explanation. EMNLP 2019. https://arxiv.org/abs/1908.04626
11. [B] Selvaraju RR, Cogswell M, Das A, et al. 2017/2019. Grad-CAM. ICCV 2017; IJCV, DOI 10.1007/s11263-019-01228-7. https://arxiv.org/abs/1610.02391
12. [C] Chattopadhay A, Sarkar A, Howlader P, et al. 2018. Grad-CAM++. WACV 2018. DOI 10.1109/WACV.2018.00097
13. [C] Wang H, Wang Z, Du M, et al. 2020. Score-CAM. CVPR Workshops 2020. https://arxiv.org/abs/1910.01279
14. [B] Sundararajan M, Taly A, Yan Q. 2017. Axiomatic Attribution for Deep Networks. ICML 2017. https://arxiv.org/abs/1703.01365
15. [B] Abnar S, Zuidema W. 2020. Quantifying Attention Flow in Transformers. ACL 2020. https://arxiv.org/abs/2005.00928
16. [B] Chefer H, Gur S, Wolf L. 2021. Transformer Interpretability Beyond Attention Visualization. CVPR 2021. https://arxiv.org/abs/2012.09838
17. [D] Draelos RL, Carin L. 2020. Use HiResCAM instead of Grad-CAM for faithful explanations of convolutional neural networks. https://arxiv.org/abs/2011.08891
18. [D] Darcet T, Oquab M, Mairal J, Bojanowski P. 2023. Vision Transformers Need Registers. https://arxiv.org/abs/2309.16588
19. [D] Oquab M, Darcet T, Moutakanni T, et al. 2023. DINOv2: Learning Robust Visual Features without Supervision. https://arxiv.org/abs/2304.07193 ；[A] https://github.com/facebookresearch/dinov2
20. [B] Zhang J, Lin Z, Brandt J, et al. 2016. Top-down Neural Attention by Excitation Backprop. ECCV 2016. https://arxiv.org/abs/1608.00507
21. [D] Petsiuk V, Das A, Saenko K. 2018. RISE: Randomized Input Sampling for Explanation of Black-box Models. https://arxiv.org/abs/1806.07421
22. [B] Hooker S, Erhan D, Kindermans P-J, et al. 2019. A Benchmark for Interpretability Methods in Deep Neural Networks. NeurIPS 2019. https://arxiv.org/abs/1806.10758
23. [B] Rong Y, Leemann T, Borisov V, et al. 2022. A Consistent and Efficient Evaluation Strategy for Attribution Methods. ICML 2022. https://arxiv.org/abs/2202.00449
24. [B] Tomsett R, Harborne D, Chakraborty S, et al. 2020. Sanity Checks for Saliency Metrics. AAAI-20. https://arxiv.org/abs/1912.01451
25. [B] Hedström A, et al. 2023. Quantus. JMLR 24(34):1–11. https://github.com/understandable-machine-intelligence-lab/Quantus
26. [A] jacobgil. pytorch-grad-cam (MIT). https://github.com/jacobgil/pytorch-grad-cam
27. [A] Captum. Attribution algorithms. https://captum.ai/docs/attribution_algorithms
28. [A] rajpurkarlab. CheXlocalize. https://github.com/rajpurkarlab/cheXlocalize
29. [B] Geirhos R, Jacobsen J-H, Michaelis C, et al. 2020. Shortcut learning in deep neural networks. Nat Mach Intell. DOI 10.1038/s42256-020-00257-z
30. [B] DeGrave AJ, Janizek JD, Lee S-I. 2021. AI for radiographic COVID-19 detection selects shortcuts over signal. Nat Mach Intell. DOI 10.1038/s42256-021-00338-7
31. [B] Zech JR, Badgeley MA, Liu M, Costa AB, Titano JJ, et al. 2018. Variable generalization performance of a deep learning model to detect pneumonia in chest radiographs. PLOS Med 15(11):e1002683. DOI 10.1371/journal.pmed.1002683
32. [B] Winkler JK, Fink C, Toberer F, Enk A, Deinlein T, et al. 2019. Association Between Surgical Skin Markings in Dermoscopic Images and Diagnostic Performance of a Deep Learning Convolutional Neural Network for Melanoma Recognition. JAMA Dermatol 155(10):1135–1141. DOI 10.1001/jamadermatol.2019.1735
33. [C] Bissoto A, Fornaciali M, Valle E, Avila S. 2019. (De)Constructing Bias on Skin Lesion Datasets. CVPR Workshops (ISIC). https://arxiv.org/abs/1904.08818
34. [C] Bissoto A, Valle E, Avila S. 2020. Debiasing Skin Lesion Datasets and Models? Not So Fast. CVPR Workshops (ISIC). https://arxiv.org/abs/2004.11457
35. [C] Narla A, Kuprel B, Sarin K, Novoa R, Ko J. 2018. Automated Classification of Skin Lesions: From Pixels to Practice. J Invest Dermatol 138(10):2108–2110. DOI 10.1016/j.jid.2018.06.175
36. [C] Oakden-Rayner L, Dunnmon J, Carneiro G, Ré C. 2020. Hidden Stratification Causes Clinically Meaningful Failures in Machine Learning for Medical Imaging. ACM CHIL 2020:151–159. DOI 10.1145/3368555.3384468
37. [B] Badgeley MA, Zech JR, Oakden-Rayner L, Glicksberg BS, Liu M, et al. 2019. Deep learning predicts hip fracture using confounding patient and healthcare variables. npj Digit Med 2:31. DOI 10.1038/s41746-019-0105-1
38. [B] DeGrave AJ, Cai ZR, Janizek JD, Daneshjou R, Lee S-I. 2023 online / 2025 issue. Auditing the inference processes of medical-image classifiers by leveraging generative AI and the expertise of physicians. Nat Biomed Eng 9(3):294–306. DOI 10.1038/s41551-023-01160-9
39. [C] Nauta M, Walsh R, Dubowski A, Seifert C. 2021. Uncovering and Correcting Shortcut Learning in Machine Learning Models for Skin Cancer Diagnosis. Diagnostics 12(1):40. DOI 10.3390/diagnostics12010040
40. [B] Gichoya JW, Banerjee I, Bhimireddy AR, et al. 2022. AI recognition of patient race in medical imaging: a modelling study. Lancet Digit Health 4(6):e406–e414. DOI 10.1016/S2589-7500(22)00063-2
41. [C] Glocker B, Jones C, Bernhardt M, Winzeck S. 2023. Algorithmic encoding of protected characteristics in chest X-ray disease detection models. eBioMedicine 89:104467. DOI 10.1016/j.ebiom.2023.104467
42. [D] Xiao K, Engstrom L, Ilyas A, et al. 2020. Noise or Signal: The Role of Image Backgrounds in Object Recognition. https://arxiv.org/abs/2006.09994
43. [B] Eyuboglu S, Varma M, Saab K, et al. 2022. Domino: Discovering Systematic Errors with Cross-Modal Embeddings. ICLR 2022. https://arxiv.org/abs/2203.14960
44. [B] Sagawa S, Koh PW, Hashimoto TB, et al. 2020. Distributionally Robust Neural Networks for Group Shifts. ICLR 2020. https://arxiv.org/abs/1911.08731
45. [B] Liu EZ, Haghgoo B, Chen AS, et al. 2021. Just Train Twice. ICML 2021. https://arxiv.org/abs/2107.09044
46. [B] Rieger L, Singh C, Murdoch WJ, et al. 2020. Interpretations are useful: penalizing explanations to align neural networks with prior knowledge. ICML 2020. https://arxiv.org/abs/1909.13584
47. [B] Bansal G, Wu T, Zhou J, et al. 2021. Does the Whole Exceed its Parts? CHI 2021. https://arxiv.org/abs/2006.14779
48. [B] Prinster D, Mahmood A, Saria S, Jeudy J, Lin CT, et al. 2024. Care to Explain? Radiology 313(2):e233261. DOI 10.1148/radiol.233261
49. [C] Gaube S, Suresh H, Raue M, Lermer E, Koch TK, et al. 2023. Non-task expert physicians benefit from correct explainable AI advice when reviewing X-rays. Sci Rep 13:1383. DOI 10.1038/s41598-023-28633-w
50. [B] Chanda T, Hauser K, Hobelsberger S, et al. 2024. Dermatologist-like explainable AI enhances trust and confidence in diagnosing melanoma. Nat Commun 15:524. DOI 10.1038/s41467-023-43095-4
