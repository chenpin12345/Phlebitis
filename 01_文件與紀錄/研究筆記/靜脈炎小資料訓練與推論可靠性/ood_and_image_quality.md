# OOD 偵測／拒答 與 學習式影像品質評估＋重拍引導 — 應用於小型靜脈炎照片研究平台

Notes for the report writer. All sources accessed 2026-10-30/31 (written as 2026-10-31). Source grades: [A] official docs / standards / reporting guidelines; [B] systematic reviews, top journals/conferences; [C] other peer-reviewed; [D] preprints (arXiv); [E] blogs, forums, repos, example code (supporting only).
Evidence labels: **[研究證據]** = research evidence shows; **[業界做法]** = industry practice; **[本報告推論]** = this report's inference (no direct source).
Search rounds: round 1 = overview web searches; round 2 = original full text (arXiv HTML/PDF, PMC, eScholarship), official repos, plus DOI content-negotiation (doi.org) and the arXiv API to confirm titles. Every DOI in References resolved on 2026-10-31 to the stated title.

Project context used to judge applicability: research prototype, not diagnosis; 14 patients / ~120 photos (positive 47, normal 9; stage normal 9 / s1 23 / s2 24); public LINE uploads (non-arm images, memes, screenshots, documents, faces, blur, extreme lighting); Windows + one consumer NVIDIA GPU; all compute local; models = YOLO11/26, EfficientNet-B0, DINOv2-small frozen + logistic regression; current quality gate = Laplacian variance + dark/bright pixel ratios.

**Correction for the writer:** "Failure detection in medical image classification: a reality check and benchmarking testbed" (TMLR 2022) is by **Bernhardt, De Sousa Ribeiro & Glocker**, not Bungert. Bungert co-authored two related papers: "Understanding Silent Failures in Medical Image Classification" (arXiv 2307.14729) and "A Call to Reflect on Evaluation Practices for Failure Detection in Image Classification" (Jaeger, Lüth, Klein, Bungert; arXiv 2211.15259).

---

## A1. Which post-hoc and training-based OOD methods work, and how strong is the evidence? (MSP, ODIN, Energy, Mahalanobis, kNN, ViM, ReAct, OE, OpenOOD, CLIP/MCM, DINOv2 features)

### Takeaway
No OOD score wins across benchmarks (OpenOOD v1.5). Every method does much better on far-OOD (textures, unrelated scenes, which here means memes, screenshots and documents) than on near-OOD (semantically close classes, which here means legs, other skin conditions and hands with no IV). For a frozen DINOv2 + logistic-regression stack, the best-supported cheap option is **kNN distance on L2-normalised frozen features**: it assumes no distribution and needs no retraining. MSP or energy from the classifier can serve as a second signal. Mahalanobis is unreliable with tiny, non-Gaussian data.

### Cited Findings
- **[研究證據] MSP baseline.** Hendrycks & Gimpel, "A Baseline for Detecting Misclassified and Out-of-Distribution Examples in Neural Networks", ICLR 2017 [B]. Uses the maximum softmax probability as the score. — [arXiv 1610.02136](https://arxiv.org/abs/1610.02136) (title verified via arXiv API 2026-10-31)
- **[研究證據] OpenOOD v1.5** (Zhang, Yang et al., arXiv 2306.09301 [D]; OpenOOD v1 = NeurIPS 2022 Datasets & Benchmarks [B]).
  - ImageNet-1K, ResNet-50, AUROC near-OOD / far-OOD: MSP 76.02/85.23; ODIN 74.75/89.47; Energy (EBO) 75.89/89.47; Mahalanobis (MDS) 55.44/74.25; ReAct 77.38/93.67; ViM 72.08/92.68; KNN 71.10/90.18; ASH 78.17/95.74.
  - CIFAR-10, ResNet-18: MSP 88.03/90.73; EBO 87.58/91.21; MDS 84.20/89.72; ViM 88.68/93.48; KNN 90.64/92.96; Outlier Exposure 94.82/96.00.
  - The authors write that "there is no single method that consistently outperforms others across benchmarks." Near-OOD AUROC is consistently lower than far-OOD AUROC.
  - Post-hoc methods win at large scale. Training methods, including OE, help on small datasets. OE helps near-OOD mainly when its outlier set resembles the test OOD.
  - Adding covariate-shifted ID samples drops near-OOD AUROC by more than 10%, so full-spectrum detection is unsolved.
  - ImageNet near-OOD sets: SSB-hard and NINCO. Far-OOD sets: iNaturalist, Textures and OpenImage-O.
  — [arXiv html v5](https://arxiv.org/html/2306.09301v5)
- **[研究證據] ODIN.** Liang, Li & Srikant, "Enhancing The Reliability of Out-of-distribution Image Detection in Neural Networks", ICLR 2018 [B]. Uses temperature scaling plus input perturbation. In OpenOOD v1.5 ODIN scores *below* MSP on near-OOD: ImageNet 74.75 vs 76.02, CIFAR-10 82.87 vs 88.03. — [arXiv 1706.02690](https://arxiv.org/abs/1706.02690); numbers from [OpenOOD v1.5](https://arxiv.org/html/2306.09301v5)
- **[研究證據] Energy score.** Liu, Wang, Owens & Li, "Energy-based Out-of-distribution Detection", NeurIPS 2020 [B]. On a CIFAR-10 WideResNet, the energy score cut average FPR95 by 18.03% compared with softmax confidence. It is post-hoc and needs no retraining. — [NeurIPS 2020 poster](https://neurips.cc/virtual/2020/poster/17313); [arXiv 2010.03759](https://arxiv.org/abs/2010.03759)
- **[研究證據] Mahalanobis.** Lee, Lee, Lee & Shin, "A Simple Unified Framework for Detecting Out-of-Distribution Samples and Adversarial Attacks", NeurIPS 2018 [B]. — [arXiv 1807.03888](https://arxiv.org/abs/1807.03888)
  - Counter-evidence: OpenOOD v1.5 near-OOD AUROC on ImageNet is only 55.44, close to chance [D].
  - In Roy et al.'s dermatology near-OOD task, Mahalanobis scored 68.1, below MSP at 72.1 [B] ([ar5iv 2104.03829](https://ar5iv.labs.arxiv.org/html/2104.03829)).
  - A medical OOD survey says Mahalanobis "performs pretty well in contextual shift detection but poorly in semantic shift detection" [D] ([arXiv 2404.18279](https://arxiv.org/abs/2404.18279)).
  - Woodland et al. (medical segmentation) found kNN "drastically improved scalability and performance" over Mahalanobis on bottleneck features, and that the Gaussian assumption may not hold [D] ([arXiv 2408.02761](https://arxiv.org/abs/2408.02761)).
- **[研究證據] Deep kNN.** Sun, Ming, Zhu & Li, "Out-of-Distribution Detection with Deep Nearest Neighbors", ICML 2022 [B]. It is non-parametric with no distributional assumption. On ImageNet-1k it cut FPR@TPR95 by 24.77% compared with SSD+ using the same model. — [arXiv 2204.06507](https://arxiv.org/abs/2204.06507). The k values and normalisation details are in the full paper and code; they were not re-extracted this session (gap).
- **[研究證據] ViM.** Wang, Li, Feng & Zhang, "ViM: Out-Of-Distribution with Virtual-logit Matching", CVPR 2022 [B]. Combines the feature residual off the principal subspace with the logits. — [arXiv 2203.10807](https://arxiv.org/abs/2203.10807). In OpenOOD v1.5 it is strong on far-OOD (ImageNet 92.68) but weaker on near-OOD (72.08). It needs a principal subspace estimated from many ID features, which is poorly conditioned with ~120 images (本報告推論).
- **[研究證據] ReAct.** Sun, Guo & Li, "ReAct: Out-of-distribution Detection With Rectified Activations", NeurIPS 2021 [B]. Clips penultimate-layer activations. — [arXiv 2111.12797](https://arxiv.org/abs/2111.12797). OpenOOD ImageNet: 77.38/93.67.
- **[研究證據] Outlier Exposure.** Hendrycks, Mazeika & Dietterich, "Deep Anomaly Detection with Outlier Exposure", ICLR 2019 [B]. — [arXiv 1812.04606](https://arxiv.org/abs/1812.04606); [ICLR 2019 poster](https://iclr.cc/virtual/2019/poster/772)
  - FPR95 for WRN-40-2, from the aggregator hyper.ai and NOT re-verified in the paper's tables: CIFAR-10 MSP 34.94 → OE 9.50; CIFAR-100 62.66 → 38.50.
  - OpenOOD v1.5 confirms OE gives the best CIFAR-10 near-OOD AUROC (94.82). It was not run on ImageNet-1K because no suitable outlier data existed.
- **[研究證據] Zero-shot CLIP OOD (MCM).** Ming, Cai, Gu, Sun, Li & Li, "Delving into Out-of-Distribution Detection with Vision-Language Representations", NeurIPS 2022 [B]. Maximum Concept Matching uses text embeddings of the ID class names as prototypes and needs no training. On a hard task with semantically similar classes it beat a pure-vision baseline by 13.1% AUROC, and it works well with few samples per class. Code: github.com/deeplearning-wisc/MCM. — [NeurIPS proceedings](https://papers.nips.cc/paper_files/paper/2022/hash/e43a33994a28f746dcfd53eb51ed3c2d-Abstract-Conference.html)
- **[研究證據] DINOv2 frozen features + kNN.** Zhao, Liu, Wen, Tan & Qi, "Equipping Vision Foundation Model with Mixture of Experts for OOD Detection", arXiv 2510.10584 [D]. A CVF ICCV 2025 supplemental exists, so it is likely ICCV 2025 [B], but this is not fully confirmed. — [arXiv html](https://arxiv.org/html/2510.10584); [CVF supplemental](https://openaccess.thecvf.com/content/ICCV2025/supplemental/Zhao_Equipping_Vision_Foundation_ICCV_2025_supplemental.pdf)
  - Setup: frozen DINOv2, ImageNet-1K as ID, results averaged over iNaturalist/Places/SUN/Textures (mostly far-OOD).
  - FPR95 / AUROC: MSP 40.85/89.41; Energy 51.96/86.82; **KNN 29.27/92.67**, the best post-hoc method.
  - Naive fine-tuning reached 28.34/92.18 and was worse on 3 of the 4 OOD sets.
  - On a fine-grained OpenImage subset, DINOv2+KNN reached FPR95 17.23, vs 29.87 for the CLIP-based LSN.
  - The paper's tables are internally inconsistent (Table 1 vs Table 7).
- **[研究證據] Counter-evidence for DINOv2 on near-OOD.** The Fi-ImageNet-1k benchmark (arXiv 2609.01027 [D], 2026) reports that frozen DINOv2-g/14 with a linear probe reaches a best near-OOD AUROC of about 77.5 (GEN). That is below supervised IN-21k ViTs (~80-81). This comes from search snippets only and has not been independently replicated. — [arXiv 2609.01027](https://arxiv.org/pdf/2609.01027)
- **[研究證據] DINOv2 itself.** Oquab et al., "DINOv2: Learning Robust Visual Features without Supervision" [D]. — [arXiv 2304.07193](https://arxiv.org/abs/2304.07193)
- **[研究證據] Survey.** Yang, Zhou, Li & Liu, "Generalized Out-of-Distribution Detection: A Survey". — [arXiv 2110.11334](https://arxiv.org/abs/2110.11334)

### Inferences
- [本報告推論] What this means for the platform:
  - LINE memes, screenshots, documents, food and scenery are far-OOD. kNN or energy on DINOv2 should work well here (ImageNet-scale far-OOD AUROC is about 90 or higher).
  - Legs, feet, neck, other rashes, bruises, tattoos and hands with no IV are near-OOD. Expect AUROC around 55-80 or worse, and do not promise to detect them.
- [本報告推論] Method fit for each existing model:
  - **DINOv2-small + LR:** kNN is the natural fit: the cosine distance to the k-th nearest ID training embedding, with k=1-5 at NOW sizes. The LR's MSP or energy on its logits adds a second signal. Mahalanobis and ViM need a covariance or principal subspace from ~120 vectors in 384-D, which is singular or ill-conditioned. They would only work with heavy shrinkage (e.g., Ledoit-Wolf), so they are not recommended NOW.
  - **EfficientNet-B0:** MSP, energy and ReAct drop in post-hoc on the logits or penultimate features. Skip ODIN: it needs an extra backward pass for input perturbation and showed no near-OOD gain in OpenOOD.
  - **YOLO detector:** no IV-site or arm box above confidence τ is itself a strong domain signal. No published evidence was found for this exact use (本報告推論).
  - **OE:** needs retraining with an outlier set. It matches the gatekeeper idea in A3. Any such training run must be started by a human, because the principles forbid automatic training.
- [本報告推論] NOW vs FUTURE:
  - **NOW** (120 photos, 14 patients): the ID bank is all ID training embeddings, so the kNN score is fully defined. Any learned OOD head will tend to overfit. Rely on far-OOD capability and send everything ambiguous to "needs human review".
  - **FUTURE** (~1,000 photos, balanced 3 classes): the kNN bank is denser, which resolves near-OOD better. Shrinkage-Mahalanobis and ViM become estimable. OE or gatekeeper training with collected negatives becomes realistic.
- [本報告推論] GPU and latency (expectations, not measurements):
  - A DINOv2 ViT-S/14 forward pass at 224×224 on a consumer NVIDIA GPU should take a few milliseconds per image.
  - kNN over ≤10^4 384-D vectors is sub-millisecond on CPU (brute-force numpy/sklearn or FAISS-CPU).
  - Energy and MSP cost nothing extra; they come from the logits.
  - The writer should recommend a local benchmark: time 100 images with `torch.cuda.synchronize`.

### Gaps
- The exact k and normalisation details from Sun et al. ICML 2022 were not re-extracted.
- No benchmark was found of DINOv2-small (ViT-S/14), or of any OOD method, on **medical smartphone photos of limbs** → 未找到可靠證據.
- Zero-shot OOD evidence for SigLIP was not searched.
- The OE FPR95 numbers come from an aggregator and were not checked against the paper's tables.

---

## A2. Medical and dermatology OOD evidence and failure cases (near-OOD vs far-OOD, small data)

### Takeaway
In medical imaging, sophisticated OOD and confidence scores often fail to beat plain MSP, and success on CIFAR-style benchmarks does not carry over. Dermatology near-OOD (unseen skin conditions) reaches only ~72-83 AUROC even with 14k cases and specialised training. A 14-patient phlebitis platform therefore cannot claim to detect near-OOD inputs. What it can realistically do is screen out far-OOD junk and route everything else to humans.

### Cited Findings
- **[研究證據] Bernhardt M, De Sousa Ribeiro F, Glocker B.** "Failure Detection in Medical Image Classification: A Reality Check and Benchmarking Testbed." TMLR 2022 (accepted 2022-09-26) [B]. They tested 9 confidence scores on 6 medical datasets, multiclass and binary. None of the advanced methods consistently beat the softmax baseline. Better OOD reliability or better calibration did not necessarily mean better failure detection for in-domain inputs. Code: github.com/melanibe/failure_detection_benchmark. — [arXiv 2205.14094](https://arxiv.org/abs/2205.14094); [Imperial repository](https://spiral.imperial.ac.uk/entities/publication/4f4648cb-b7de-43ff-934a-0ec6884f1a7e)
- **[研究證據] Berger C, Paschali M, Glocker B, Kamnitsas K.** "Confidence-based Out-of-Distribution Detection: A Comparative Study and Analysis." UNSURE workshop @ MICCAI 2021 (best paper per the repo), arXiv 2107.02568 [C]. They compared MCP, deep ensembles, ODIN, Mahalanobis, center loss and MC dropout on CIFAR-10 vs SVHN, then on CheXpert chest X-rays. High performance on the vision benchmark "does not directly translate" to the medical task. Code: github.com/christophbrgr/ood_detection_framework. — [arXiv 2107.02568](https://arxiv.org/abs/2107.02568)
- **[研究證據] Roy AG et al. (Google Health).** "Does your dermatology classifier know what it doesn't know? Detecting the long-tail of unseen conditions." Medical Image Analysis 2022;75:102274, DOI 10.1016/j.media.2021.102274 [B]. — [ar5iv 2104.03829](https://ar5iv.labs.arxiv.org/html/2104.03829)
  - Data: 14,427 cases from 17 sites (California, Hawaii), up to 6 images per case.
  - Classes: 26 inlier conditions (≥100 cases each) and 199 outlier conditions, split 68 train / 66 val / 65 test. The test set has 1,192 inlier and 937 outlier cases.
  - OOD AUROC (BiT-L): MSP 72.1; Mahalanobis 68.1; OE+MSP 72.9; reject bucket 75.6; hierarchical outlier detection (HOD, λ=0.1) 79.4; 5-model diverse ensemble 83.0.
  - The authors call this near-OOD ("subtle semantic differences") and harder than dataset-level shift.
  - Splits are by condition class. The retrieved text reports no external validation on a different population.
- **[研究證據] Combalia M, Codella N, Rotemberg V, … Halpern A, Malvehy J.** "Validation of artificial intelligence prediction models for skin cancer diagnosis using dermoscopy images: the 2019 International Skin Imaging Collaboration Grand Challenge." Lancet Digit Health 2022;4(5):e330-e339, DOI 10.1016/S2589-7500(22)00021-8 [B]. ISIC 2019 training had 25,331 images in 8 categories. The test set added an outlier ("none of the others") class that was absent from training. Specific sensitivity numbers for the unknown class were not retrieved. — [UB repository PDF](https://diposit.ub.edu/dspace/bitstream/2445/201464/1/Validation%20of%20artificial%20intelligence%20prediction%20models%20for%20skin_TheLancet.pdf); [ISIC 2019 page](https://challenge.isic-archive.com/landing/2019/)
- **[研究證據] Unsupervised dermoscopic OOD** (arXiv 2111.04807 [D]). AUROC was 0.694 / 0.642 with 6 ID lesion classes and 2 held-out OOD classes, showing that held-out skin-lesion classes are hard. — [ar5iv 2111.04807](https://ar5iv.labs.arxiv.org/html/2111.04807)
- **[研究證據] Medical OOD survey** (arXiv 2404.18279 [D]). Mahalanobis is good at contextual/covariate shift and poor at semantic shift. — [arXiv 2404.18279](https://arxiv.org/abs/2404.18279)
- **[研究證據] OpenOOD v1.5.** Covariate-shifted ID inputs (same class, different capture conditions) drop near-OOD AUROC by more than 10%. This matters here because real IV-site photos from LINE under odd lighting are covariate-shifted ID, and OOD scores may wrongly reject them. — [arXiv html v5](https://arxiv.org/html/2306.09301v5)

### Inferences
- [本報告推論] Leakage and validation in the cited medical studies:
  - Bernhardt and Berger use public benchmark datasets such as CheXpert. Whether patients were split cleanly depends on each dataset's protocol, which the retrieved text does not state.
  - Roy et al. split OOD by condition, not by patient. The retrieved text does not address patient leakage of inlier cases between train and test.
  - None report external validation of the OOD detector at a separate hospital.
  - Treat all their AUROCs as optimistic upper bounds for this project.
- [本報告推論] Failure modes specific to this platform:
  1. True IV-site photos under covariate shift get flagged OOD, producing a false "cannot judge". Examples: dark-skinned arms, yellow indoor light, tape or dressing occlusion, ICU lighting.
  2. Near-OOD inputs get accepted as ID and receive a confident but meaningless phlebitis stage. Examples: a bruise from venipuncture, contact dermatitis from tape, cellulitis, a leg IV site.
  3. The normal class has only 9 photos, so a normal-looking arm from a public user may sit far from the ID bank and be wrongly rejected.
  - Decision rule: near-OOD or borderline → "needs human review", never an automatic "result".
- [本報告推論] NOW vs FUTURE:
  - **NOW:** claim only far-OOD screening, and document near-OOD as an explicit limitation.
  - **FUTURE:** with ~1,000 photos and a curated near-OOD test set (legs, bruises, dermatitis, other wounds), near-OOD AUROC can at least be *measured*. Roy et al. suggest specialised training (reject bucket or HOD) adds about 3-7 AUROC points, but it needs labelled outlier classes.

### Gaps
- MOOD challenge results were not researched (time budget); the writer should not cite numbers for it.
- No phlebitis- or IV-site-specific OOD study was found → 未找到可靠證據.
- No study of OOD in public messaging-app (LINE/WhatsApp) medical photo intake was found → 未找到可靠證據.

---

## A3. Dedicated "gatekeeper" classifier vs local zero-shot CLIP/SigLIP; screenshot heuristics; face detection for privacy

### Takeaway
A two-layer gate can run on one consumer GPU without any cloud call:
1. Local zero-shot CLIP/SigLIP prompts plus DINOv2 kNN distance answer "is this a photo of forearm or back-of-hand skin?"
2. Cheap heuristics catch screenshots and documents, and a local face detector protects privacy.

A supervised gatekeeper trained on ID photos vs collected negatives (outlier exposure in spirit) has stronger support from the OE evidence. However, it needs negatives that resemble real near-OOD and a human-triggered training run, so it is a FUTURE item.

### Cited Findings
- **[研究證據] OE principle.** Training with auxiliary outliers is supported; OpenOOD shows it helps near-OOD mainly when the outliers resemble the test OOD. — [arXiv 1812.04606](https://arxiv.org/abs/1812.04606); [OpenOOD v1.5](https://arxiv.org/html/2306.09301v5)
- **[研究證據] MCM / CLIP zero-shot OOD** needs no training and is strong with few samples per class. — [NeurIPS 2022](https://papers.nips.cc/paper_files/paper/2022/hash/e43a33994a28f746dcfd53eb51ed3c2d-Abstract-Conference.html)
- **[研究證據] DINOv2 vs CLIP.** On a fine-grained OOD subset, frozen DINOv2+kNN beat the CLIP-based LSN (FPR95 17.23 vs 29.87) [D]. — [arXiv 2510.10584](https://arxiv.org/html/2510.10584)
- **[研究證據] Roy et al.** A coarse inlier-vs-outlier head trained jointly with outlier classes beat MSP: 72.1 → 75.6 (reject bucket) → 79.4 (HOD) AUROC. This is direct dermatology support for a learned rejection head when labelled outliers exist. — [ar5iv 2104.03829](https://ar5iv.labs.arxiv.org/html/2104.03829)
- **[研究證據] ImageQX** had explicit "no skin" and "healthy skin" classes alongside "lesion" and "poor quality", a dermatology precedent for combining the domain gate and the quality gate. Its "no skin" F1 was only 0.74, which the authors attribute to very few no-skin training images. — [PMC10468541](https://pmc.ncbi.nlm.nih.gov/articles/PMC10468541)
- **[業界做法/資料集] HaGRID** (ai-forever/hukenovs). Usable as "hand but not IV site" negatives. — [GitHub hagrid](https://github.com/hukenovs/hagrid); [HF dataset card](https://huggingface.co/datasets/abhishek/hagrid)
  - v1: 554,800 FullHD images, 18 gestures plus no_gesture. Licence is a variant of CC BY-SA 4.0; see the repo's licence file.
  - HaGRIDv2: 1,086,158 images, 33 classes, CC BY 4.0 per the arXiv metadata.
  - The images contain people's faces.
- **[業界做法] Local face detector YuNet** (libfacedetection / OpenCV `FaceDetectorYN`) [E]. — [libfacedetection GitHub](https://github.com/ShiqiYu/libfacedetection); [HF forum](https://discuss.huggingface.co/t/best-free-production-grade-model-for-simple-face-detection-yes-no-confidence-in-a-python-microservice/180012); [OpenCV forum (Windows acceleration)](https://forum.opencv.org/t/unable-to-get-hardware-acceleration-for-yunet-on-windows-in-python-opencv/18551)
  - README benchmark on an Intel i7-7820X: ~13.09 ms single-thread at 320×240 (about 76 FPS), ~50 ms at 640×480.
  - The ONNX model is ~230 KB.
  - An MIT licence is claimed only in a forum post; verify the OpenCV Zoo LICENSE.
  - OpenCV DNN does not support the newest YuNet's dynamic input shape, so use the fixed-shape `face_detection_yunet_2023mar.onnx`.

### Inferences
- [本報告推論] Recommended gate pipeline. Wire it into FastAPI before any classifier; everything runs locally.
  1. **File/format gate.** Decode with Pillow. Reject non-images, animated GIF/WebP and tiny images (e.g., short side < 480 px) → "please retake".
  2. **Screenshot/document heuristics.** No published validation was found, so treat these as weak signals: combine them and never hard-reject on one alone.
     - (a) Exact phone-screen aspect ratios, with pixel-perfect flat regions or a status-bar band at the top.
     - (b) A high share of perfectly uniform colour pixels and long straight horizontal or vertical edges (UI).
     - (c) Text density from local OCR (PaddleOCR or Tesseract, both local): many text boxes suggest a document or screenshot.
     - (d) No EXIF camera make/model. CAVEAT: it was NOT verified whether LINE strips or keeps EXIF when forwarding images. If LINE re-encodes and strips EXIF, which is plausible, (d) is useless for LINE uploads.
  3. **Face gate (privacy).** Run YuNet on CPU (~10-50 ms). If it detects a face above the confidence threshold, do not store the original in the research set. Store a blurred copy, or ask the user to re-shoot only the arm, and reply "please retake" with privacy wording. This supports the no-identity-leakage principle without any cloud call.
  4. **Domain gate (zero-shot).** Run CLIP/SigLIP locally via Hugging Face transformers: download the weights once, then set `HF_HUB_OFFLINE=1`.
     - ID prompts, e.g. "a close-up photo of a forearm with an intravenous catheter", "a photo of the back of a hand with an IV cannula", "a photo of human skin on an arm".
     - Negative prompts, e.g. "a screenshot of a phone app", "a document", "a meme", "a photo of a face", "a photo of food", "a photo of a leg", "a photo of a cat".
     - Score with an MCM-style softmax over the ID prompts plus the margin against the best negative.
     - Run both the CLIP domain margin and the DINOv2 kNN distance, and require both to pass before the "result" pathway.
  5. **Domain gate (learned, FUTURE).** Logistic regression on frozen DINOv2 features. This is essentially OE on a linear head and trains in seconds on CPU.
     - Positives: all ID photos, from the hospital and from accepted LINE uploads.
     - Negatives: HaGRID hand crops (faces cropped out), public leg/foot/other-skin images, screenshots and documents generated locally, and rejected LINE uploads after human labelling.
     - Use patient-grouped CV.
- [本報告推論] NOW vs FUTURE:
  - **NOW:** zero-shot CLIP, DINOv2 kNN, heuristics and the face gate; no learned gatekeeper. There are too few ID images, and with 14 patients from one hospital the gate may learn "hospital background" as the ID cue and reject every LINE photo of a real IV site.
  - **FUTURE:** a learned gatekeeper once at least a few hundred negatives exist, plus ID photos from both sources.
- [本報告推論] Latency (design target, must be measured locally):
  - CLIP ViT-B/32 or SigLIP-base image encoding: a few ms to ~20 ms per image on a consumer GPU.
  - YuNet and OCR on CPU: tens to a few hundred ms. OCR is the slowest step, so run it only when the cheaper heuristics are ambiguous.
  - Total gate under ~0.5 s per photo is a reasonable target.
- [本報告推論] Conflicts with the inviolable principles:
  - Cloud VLM APIs for "is this an arm?" (e.g., hosted GPT/Gemini vision) would send research photos to third parties → CONFLICT. Use local CLIP/SigLIP instead.
  - Training the gatekeeper, or adding rejected uploads as negatives, must be human-triggered and human-labelled. No automatic retraining loops from production logs.
  - HaGRID contains faces and is CC BY-SA. Keep it out of the research photo store, document the licence, and crop or discard faces.
  - Downloading model weights from Hugging Face is an outbound download, not an upload of photos, so it does not conflict. Pin versions and verify licences: CLIP ships an OpenAI licence file; the SigLIP model card states Apache-2.0, which was not verified this session.

### Gaps
- No peer-reviewed evaluation was found of screenshot/document heuristics (EXIF absence, UI edges, OCR text density) for medical intake → 未找到可靠證據.
- How the LINE Messaging API handles EXIF and recompression was not verified.
- The 11k Hands dataset licence was not verified; the search returned nothing.
- SigLIP's licence and zero-shot OOD performance were not verified this session.

---

## A4. Setting and validating OOD/abstention thresholds; how many samples; production monitoring

### Takeaway
Set the OOD threshold on patient-grouped in-distribution validation scores so it keeps a target TPR, for example accepting 95% of genuine IV-site photos. Then report FPR@95TPR and AUROC on a curated local OOD test set, split into far-OOD and near-OOD. With 120 ID photos from 14 patients the threshold itself is statistically shaky: about ±4 percentage points on TPR, more given patient clustering. So run the gate in shadow or "warn" mode with human review before it is allowed to reject anything.

### Cited Findings
- **[研究證據] Metric conventions.** FPR at 95% TPR (FPR95) and AUROC are the standard OOD metrics in Energy (NeurIPS 2020), Deep kNN (ICML 2022) and OpenOOD. — [arXiv 2010.03759](https://arxiv.org/abs/2010.03759); [arXiv 2204.06507](https://arxiv.org/abs/2204.06507); [OpenOOD v1.5](https://arxiv.org/html/2306.09301v5)
- **[研究證據] Evaluation-practice critique.** Jaeger, Lüth, Klein & Bungert, "A Call to Reflect on Evaluation Practices for Failure Detection in Image Classification" (arXiv 2211.15259; ICLR 2023 per later versions, not verified). Argues OOD detection and misclassification detection should be evaluated together as holistic failure detection. — [search result listing](https://arxiv.deeppaper.ai/papers/2211.15259v2)
- **[研究證據] Bernhardt et al.** Better OOD separation does not imply better failure detection for in-domain errors, so threshold the classifier's confidence separately from the OOD gate. — [arXiv 2205.14094](https://arxiv.org/abs/2205.14094)
- **[研究證據] TrueImage.** The authors recommend tuning operating thresholds per dermatologist or practice and per disease category, with adjustable settings. This is a precedent for thresholds owned by humans. — [arXiv 2010.02086](https://arxiv.org/abs/2010.02086)

### Inferences
- [本報告推論] Procedure (NOW and FUTURE):
  1. Compute OOD scores for ID validation images with **patient-grouped** cross-validation (GroupKFold by patient). The kNN bank must exclude the held-out patient's own images. Otherwise near-duplicate photos of the same arm give near-zero distance, which is leakage and produces an over-tight threshold.
  2. Set τ to the 5th percentile of ID scores, which keeps ~95% TPR. Record τ, the date, the data version and the human who approved it (principle: humans confirm).
  3. Curate a local OOD test set that is never uploaded anywhere. Report AUROC and FPR@95TPR separately for each part:
     - far-OOD: screenshots, documents, memes, food, pets, scenery, faces;
     - near-OOD: legs/feet, neck, other wounds, bruises, dermatitis, hands with no IV, IV sites fully covered by dressing.
  4. Map a two-threshold design to the reply types:
     - score ≥ τ_high → continue to the quality gate and classifier;
     - τ_low ≤ score < τ_high → "needs human review";
     - score < τ_low → "cannot judge", with polite wording;
     - classifier MSP below its own threshold → "needs human review".
- [本報告推論] Sample-size arithmetic (binomial, ignoring clustering):
  - The SE of a 95% TPR estimate is √(0.95·0.05/n). For n=120 that is ±2.0% SE (95% CI about ±3.9 pp); for n=1,000 it is ±0.7% SE (±1.4 pp).
  - For FPR on m OOD images with zero false accepts, the "rule of three" gives a 95% upper bound of about 3/m: m=60 → ≤5%; m=300 → ≤1%.
  - Estimating an FPR near 5% within ±2 pp needs m≈460.
  - With 14 patients, the effective sample size for TPR is closer to the number of patients than the number of photos, so NOW thresholds are provisional.
- [本報告推論] Suggested OOD test-set sizes:
  - **NOW:** at least 100 far-OOD and 60 near-OOD images, enough only for rule-of-three-level claims.
  - **FUTURE:** at least 300 far-OOD and 300 near-OOD images, sampled from real LINE rejects that were consented and human-reviewed.
- [本報告推論] Production monitoring (shadow mode):
  - Log per upload: timestamp, source (hospital or LINE), OOD scores (kNN, CLIP margin), quality scores, the decision that *would* have been made, and the final human decision.
  - Store the scores in SQLite. Do not keep images from non-consenting users beyond the retention policy.
  - Review weekly: rejection rate by source, drift in the kNN distance distribution (e.g., median and 95th percentile), and the share of human overrides.
  - Any threshold change is a human decision with a changelog entry; no auto-recalibration.

### Gaps
- No medical-domain study was found that specifies the minimum number of OOD samples needed to validate an intake gate → 未找到可靠證據. The numbers above are statistical arithmetic only.
- Conformal and selective-prediction approaches to threshold guarantees were not researched.

---

## B1. Classical and deep no-reference IQA (BRISQUE, NIQE, PIQE, NIMA, HyperIQA, MUSIQ, CLIP-IQA, MANIQA, TOPIQ, Q-Align, LIQE) and the pyiqa library: do they predict "diagnosability"?

### Takeaway
Generic NR-IQA models are trained on natural-image aesthetic or distortion MOS. No direct evidence shows they predict whether a clinical skin photo is usable for diagnosis. The only medical comparison found shows BRISQUE and NIQE uncorrelated, or correlated in the wrong direction, with expert scores. Dermatology groups (Stanford TrueImage, ImageQX) built task-specific supervised quality models instead. pyiqa is convenient and runs locally, but its current licence is PolyForm Noncommercial: fine for an academic prototype, a flag for any future commercial use.

### Cited Findings
- **[研究證據] BRISQUE.** Mittal A, Moorthy AK, Bovik AC. "No-Reference Image Quality Assessment in the Spatial Domain." IEEE Trans Image Process 2012;21(12):4695-4708. DOI 10.1109/TIP.2012.2214050 [B]. (DOI resolved 2026-10-31.)
- **[研究證據] NIQE.** Mittal A, Soundararajan R, Bovik AC. "Making a 'Completely Blind' Image Quality Analyzer." IEEE Signal Process Lett 2013;20(3):209-212. DOI 10.1109/LSP.2012.2227726 [B].
- **[研究證據] NIMA.** Talebi H, Milanfar P. "NIMA: Neural Image Assessment." IEEE Trans Image Process 2018;27(8):3998-4011. DOI 10.1109/TIP.2018.2831899 [B]; [arXiv 1709.05424](https://arxiv.org/abs/1709.05424).
- **[研究證據] MUSIQ.** Ke et al., "MUSIQ: Multi-scale Image Quality Transformer", ICCV 2021 [B]. — [arXiv 2108.05997](https://arxiv.org/abs/2108.05997)
- **[研究證據] CLIP-IQA.** Wang J, Chan KCK, Loy CC. "Exploring CLIP for Assessing the Look and Feel of Images." AAAI 2023 [B]. Uses antonym prompt pairs ("Good photo"/"Bad photo") because a single prompt correlates poorly with human ratings; needs no task-specific training. — [AAAI OJS](https://ojs.aaai.org/index.php/AAAI/article/view/25353/25125); [arXiv 2207.12396](https://arxiv.org/abs/2207.12396)
- **[研究證據] Q-Align.** Wu et al., "Q-Align: Teaching LMMs for Visual Scoring via Discrete Text-Defined Levels" (ICML 2024 per the authors; not re-verified). An LMM-based scorer with billions of parameters. — [arXiv 2312.17090](https://arxiv.org/abs/2312.17090)
- **[業界做法/E] pyiqa (IQA-PyTorch, chaofengc).** Current README, read 2026-10-31. — [GitHub chaofengc/IQA-PyTorch](https://github.com/chaofengc/IQA-PyTorch); [PyPI 0.1.1](https://pypi.org/project/pyiqa/0.1.1/)
  - **Licence:** "PolyForm Noncommercial License 1.0.0", plus the NTU S-Lab License for applicable components and a LICENSE-OpenAI-CLIP file. The GitHub sidebar shows "MIT license", which conflicts; check the LICENSE files. The older PyPI 0.1.1 README said CC BY-NC-SA 4.0.
  - **Install:** `pip install pyiqa`.
  - **NR metrics listed:** BRISQUE, NIQE, NRQM, MUSIQ, TOPIQ (topiq_nr), NIMA, DBCNN, PI, HyperIQA, CNNIQA, MetaIQA, WaDIQaM-NR, QualiCLIP, FGResQ, and Q-ReAlign (Qwen-VL-based). PIQE, CLIP-IQA, MANIQA and LIQE were not confirmed on the README page read this session; some may exist in code, so verify with `pyiqa.list_models()`.
  - **Weights:** hosted on Hugging Face (IQA-PyTorch-Weights) and cached in `~/.cache/torch/hub/pyiqa/`. Some weights were retrained by the project rather than by the original authors.
  - No Windows-specific notes.
- **[研究證據] Counter-evidence (medical, not skin).** Tian X, Anantrasirichai N, Nicholson L, Achim A. Biol Imaging 2024;4:e15, DOI 10.1017/S2633903X24000163 [C]. Against 10 experts' MOS, NIQE had SROCC 0.6346 in the wrong direction and BRISQUE 0.032. The authors note that metrics designed for natural images may not suit medical imaging. This is retinal OCT/confocal, not skin photos, so the evidence is indirect. — [PMC11704141](https://pmc.ncbi.nlm.nih.gov/articles/PMC11704141/)
- **[研究證據] TrueImage background.** The authors note IQA methods have "generally been studied for use on natural images". They chose interpretable hand-crafted features restricted to the skin and lesion regions because "the background can be blurry" without harming usability. This is a key reason global NR-IQA scores mislead. — [arXiv 2010.02086](https://arxiv.org/abs/2010.02086)
- **[研究證據] ImageQX** did not benchmark against BRISQUE or NIQE either; it cites deep IQA only in related work. — [PMC10468541](https://pmc.ncbi.nlm.nih.gov/articles/PMC10468541)

### Inferences
- [本報告推論] No direct study was found correlating BRISQUE, NIQE, MUSIQ or CLIP-IQA with the diagnostic usability of clinical skin or limb photos → 未找到可靠證據 either way. Still, every dermatology quality system found (TrueImage, ImageQX) chose task-specific labels, which is practice-level evidence that generic scores are not enough.
- [本報告推論] Failure risks specific to IV-site photos:
  - Global sharpness scores reward a sharp background (bed sheets, text on tape) even when the cannula site is blurred.
  - Aesthetic models (NIMA/MUSIQ, trained on AVA/KonIQ) penalise clinical close-ups.
  - Whole-image exposure misses glare on the exact site.
  - Brightness heuristics depend on skin tone; TrueImage notes most of its images were of lighter skin.
- [本報告推論] Practical use: compute 1-2 generic scores (e.g., BRISQUE on CPU, MUSIQ or TOPIQ-NR on GPU) on the YOLO-detected IV-site crop, and use them only as *features* or logged diagnostics, never as the sole retake trigger.
- [本報告推論] Latency (not measured; benchmark locally):
  - BRISQUE and NIQE run on CPU at roughly tens of ms per 512-px image.
  - MUSIQ, TOPIQ and CLIP-IQA are CNN/ViT scale, roughly tens of ms on a consumer GPU.
  - Q-Align and Q-ReAlign are LMM scale: several GB of VRAM and hundreds of ms to seconds per image. That is overkill and would compete for VRAM with YOLO and DINOv2 on one GPU.
- [本報告推論] Licence and principle check: pyiqa's PolyForm Noncommercial licence is compatible with a non-commercial research prototype but must be recorded. First use downloads weights from Hugging Face, so pre-download them and run offline. No photos leave the machine, so there is no cloud conflict.

### Gaps
- Whether PIQE, MANIQA, LIQE and HyperIQA are available in current pyiqa, and under what licence, was not individually confirmed.
- No dermatology or wound study comparing generic NR-IQA with clinician usability ratings was found → 未找到可靠證據.
- Google's dermatology image-quality work and smartphone wound-photo quality studies were not reached this session.

---

## B2. Training a small task-specific quality model (human quality labels, DINOv2 + LR, sample size, active labelling, inter-rater agreement)

### Takeaway
Two dermatology precedents show that task-specific quality models work moderately well:
- TrueImage v1: 362 images, hand-crafted features + logistic regression; rejects 50% of poor images while keeping 80% of good ones.
- ImageQX: 36,509 images, CNN; macro F1 0.73, close to the inter-rater 0.77.

The quality labels themselves are noisy. Dermatologists agree well on blur (pairwise F1 0.83) but poorly on framing (0.24) and resolution (0.32). A phlebitis quality model should therefore start with a few well-defined labels and measure rater agreement first.

### Cited Findings
- **[研究證據] TrueImage v1.** Vodrahalli K, Daneshjou R, Novoa RA, Chiou A, Ko JM, Zou J. "TrueImage: A Machine Learning Algorithm to Improve the Quality of Telehealth Photos." Pacific Symposium on Biocomputing 2021;26:220-231 [C]. Full text verified from the arXiv PDF. — [arXiv 2010.02086](https://arxiv.org/abs/2010.02086)
  - **Features:** per-patch blur frequency features (100 patches); under/over-exposure and colour quartiles for lighting; skin/lesion pixel ratio in the centre crop for zoom/crop. The skin model is a GMM trained on ~50,000 skin pixels from 14,701 face images.
  - **Classifiers:** 4 logistic regressions (good/poor, blurry, lighting, zoom/crop).
  - **Data:** 362 images: Web 55, Web-augmented 179 (synthetic Gaussian blur or random corner crop), Stanford clinic 99, self-taken poor lighting 29. Labels: 146 good, 90 blurry, 41 poor lighting, 88 zoom/crop.
  - **Split:** random at image level (not patient-grouped). Augmentation was applied after the split, and a dermatologist screened the synthetic test images for realism.
  - **Results:** reject 50% of poor images while keeping 80% of good ones, or reject 10% of poor while keeping >95% of good. Blur was detected well; lighting and crop only moderately.
  - **Runtime:** ~1 s per photo, single-threaded on a laptop CPU.
  - **Limitations:** mostly lighter skin tones; no external validation.
- **[研究證據] TrueImage 2.0.** Vodrahalli K, Ko J, Chiou AS, Novoa R, Abid A, Phung M, Yekrang K, Petrone P, Zou J, Daneshjou R. "Development and Clinical Evaluation of an AI Support Tool for Improving Telemedicine Photo Quality." arXiv 2209.09105 (2022) [D; journal version not confirmed]. Trained on 1,700 clinician-annotated telemedicine images. Retrospective test on 357 images: ROC-AUC 0.78 for poor quality, 0.84 for blurry, 0.70 for lighting. Performance is reported as consistent across age, gender and skin tone. — [arXiv 2209.09105](https://arxiv.org/abs/2209.09105)
- **[研究證據] ImageQX.** Jalaboi R, Winther O, Galimzianova A. "Explainable Image Quality Assessments in Teledermatological Photography." Telemed J E Health 2023;29(9):1342-1348, DOI 10.1089/tmj.2022.0405 [C]. — [PMC10468541](https://pmc.ncbi.nlm.nih.gov/articles/PMC10468541)
  - **Data:** 36,509 smartphone photos (Imagine app, 2017-2019), 26,635 train / 9,874 test. Up to 12 board-certified dermatologists labelled each image; the reference is a plurality vote.
  - **Labels:** classes lesion / no skin / healthy skin / poor quality (~20% poor). Explanations: bad framing, bad light, blurry, low resolution, too far away; an explanation counts as positive if at least one rater cited it.
  - **Inter-rater pairwise F1** (no kappa reported): poor quality 0.67±0.07; mean 0.77±0.07. Explanations: framing 0.24, light 0.65, blurry 0.83, resolution 0.32, distance 0.51. The Discussion quotes 0.62 for poor-quality agreement, an internal inconsistency.
  - **Model:** macro F1 0.73±0.01 (specificity 0.90, sensitivity 0.73). Explanation F1: framing 0.37, light 0.61, blurry 0.70, resolution 0.52, distance 0.42. Mean explanation sensitivity was only 0.39.
  - **Limitations:** Grad-CAM sometimes focused on the background. The split is by image and patient separation is not stated, so there is leakage risk. No external validation. Model size 15 MB.
- **[研究證據] UCSF E-Visit study.** Blurriness was present in 60% of inadequate photos vs 7.8% of adequate ones (P<0.001), so blur is the dominant actionable failure. — [eScholarship](https://escholarship.org/uc/item/1vs9c5n5)

### Inferences
- [本報告推論] Proposed phlebitis quality labels: multi-label, per photo, by 2 raters.
  - Primary target: `usable_for_staging` (yes/no).
  - Reasons: `blurry`, `too_dark`, `overexposed_or_glare`, `site_not_visible / not_centered`, `too_far`, `too_close/cropped`, `occluded_by_tape_or_dressing`, `wrong_body_part`, `face_or_identifying_content`, `screenshot_or_non_photo`.
  - ImageQX predicts low agreement on framing, distance and resolution, so define them operationally. For example, "too far" = the IV-site region covers < 10% of the image; "cropped" = the site touches the image border. Give raters a reference card with example photos.
- [本報告推論] Measure agreement before training. Use Cohen's κ (2 raters) or Krippendorff's α per label on at least 50-100 photos. Drop or merge labels with κ < 0.4, a common rule-of-thumb cut-off for "moderate" agreement (not sourced here).
- [本報告推論] Model design:
  - Inputs: the frozen DINOv2-small CLS embedding (and/or mean-pooled patch embedding) of the YOLO IV-site crop and of the whole image, concatenated with the existing fixed-formula features (Laplacian variance on the crop, dark/bright ratios) as interpretable inputs.
  - One L2-regularised logistic regression per label, mirroring TrueImage's 4-LR design but with learned features.
  - Training takes seconds on CPU. Inference adds ~0 ms, because the classifier and OOD gate already compute the DINOv2 pass.
- [本報告推論] Sample size:
  - TrueImage reached usable blur and quality detection with 362 images (with synthetic augmentation), and v2 used 1,700. ImageQX used ~27k.
  - Rule of thumb for LR on frozen features: at least 30-50 positive examples per reason label for a stable estimate.
  - **NOW** (~120 photos, mostly good hospital photos): too few natural poor-quality examples. The only option is **synthetic degradations** as in TrueImage (Gaussian/motion blur, gamma darkening, over-exposure, random crops, simulated tape occlusion). These risk teaching the model the synthetic artefact, so evaluate only on real poor photos.
  - **FUTURE** (~1,000 photos plus real LINE uploads): enough real negatives for blur, dark and too-far; occlusion and wrong-body-part will still be sparse.
- [本報告推論] Active labelling. Send these uploads to human labelling first:
  - (a) the fixed formula and the learned gate disagree;
  - (b) the LR probability is in [0.3, 0.7];
  - (c) the OOD score is near τ.
  - Labels are written only after a human confirms them (principle).
- [本報告推論] Patient-level leakage: multiple photos of the same arm on the same day are near-duplicates. Quality-model CV must use GroupKFold by patient (hospital) or by hashed LINE user ID (public), unlike TrueImage and ImageQX, which split by image.

### Gaps
- No phlebitis, IV-site or wound-photo quality dataset or label scheme was found → 未找到可靠證據.
- No published learning curve (performance vs number of labelled quality images) for frozen foundation-model features was found → 未找到可靠證據.

---

## B3. Retake feedback: does actionable feedback improve photo quality? Guidelines and Traditional-Chinese LINE reply templates

### Takeaway
Evidence that automated, actionable feedback improves photo quality comes mainly from one prospective pilot: TrueImage 2.0 reported 68% fewer patients with a poor-quality image (n=98, preprint). The counter-evidence comes from UCSF and CHOP teledermatology: photos taken without any instructions were adequate 91-92.5% of the time, and instructions did not improve diagnostic concordance. Retake prompts should therefore be few and specific (blur first), and should fire only for clearly unusable photos so users are not annoyed.

### Cited Findings
- **[研究證據] TrueImage 2.0 prospective pilot.** With 98 patients, real-time feedback reduced the number of patients with a poor-quality image by 68.0% [D, preprint]. The abstract gives no pilot design details such as controls or randomisation. — [arXiv 2209.09105](https://arxiv.org/abs/2209.09105)
- **[研究證據] TrueImage v1.** Example feedback was "turn on camera flash" for dim lighting, with finer messages ("too dark" vs "too bright") planned. In a survey of 37 dermatologists, 78.4% reported that about 1 in 5 photos per visit was poor quality. — [arXiv 2010.02086](https://arxiv.org/abs/2010.02086)
- **[研究證據] Counter-evidence.** Liu JY, Lohman ME, Klufas D, Fassett M, Amerson E, Twigg A, Leslie K, Khodosh R. "Patient photographs taken without instructions are of sufficient quality for clinical decision making in teledermatology." Dermatol Online J 2024;30(3):17, DOI 10.5070/D330363877 [C, research letter]. — [eScholarship](https://escholarship.org/uc/item/1vs9c5n5)
  - Setting: UCSF, 113 E-Visits (Jun 2020-Apr 2021), no photo instructions.
  - Results: 91.2% of photos adequate (103/113); a clinical decision was made in 95.4% of cases; only 1.9% needed an in-person visit because of inadequate photos. Older age was associated with a lower quality score.
  - Cited CHOP pediatric study (40 visits): 7.5% inadequate, 89% concordance, and photography instructions did NOT improve concordance.
  - Cited Duke study: of 1,200 patient images rated without context, only 62.2% were of sufficient quality and 55.1% were useful.
  - Limitations: a single rater scored quality; patients were mostly White, privately insured and urban; the sample is small.
- **[A/B 標準] ISIC / JAMA Dermatology standards.**
  - Katragadda C, Finnane A, Soyer HP, Marghoob AA, Halpern A, Malvehy J, Kittler H, Hofmann-Wellenhof R, Da Silva D, Abraham I, Curiel-Lewandrowski C. "Technique Standards for Skin Lesion Imaging: A Delphi Consensus Statement." JAMA Dermatol 2017;153(2):207-213, DOI 10.1001/jamadermatol.2016.3949. 33 recommendations covering lighting, background colour, field of view, orientation, focus/depth of field, resolution, scale, colour calibration and storage; a recommendation was retained if its mean and median ratings were both ≥4. — [PubMed 27892996](https://pubmed.ncbi.nlm.nih.gov/27892996/)
  - Finnane A, Curiel-Lewandrowski C, Wimberley G, Caffery L, Katragadda C, Halpern A, Marghoob AA, Malvehy J, Kittler H, Hofmann-Wellenhof R, Abraham I, Soyer HP. "Proposed Technical Guidelines for the Acquisition of Clinical Images of Skin-Related Conditions." JAMA Dermatol 2017;153(5):453-457, DOI 10.1001/jamadermatol.2016.6214. Translates the ISIC Standards for Dermatological Imaging into clinical use; 2 clinical photographers checked feasibility. — [Arizona repository](https://repository.arizona.edu/handle/10150/624154)
- **[A/B 準則] ATA-affiliated guideline.** Camaj Deda L, Goldberg RH, Jamerson TA, Lee I, Tejasvi T. "Dermoscopy practice guidelines for use in telemedicine." npj Digit Med 2022;5:55, DOI 10.1038/s41746-022-00587-9. Reviewed by American Telemedicine Association teledermatology experts; it mainly covers dermoscopy and clinician capture. — [PMC9046409](https://pmc.ncbi.nlm.nih.gov/articles/PMC9046409)
  - Centre the lesion and hold the camera perpendicular to the skin.
  - "All edges of the lesion shall be visualized."
  - For rashes, the close-up should show roughly 25:75 normal to affected skin.
  - Regional images should include anatomic landmarks.
  - The scale must not obscure the lesion.
  - Keep orientation consistent across follow-ups.
- **[E] Patient-facing telederm photo guides** (NHS and consultant guides, ATA-adapted handouts). — [Consultant Connect guide PDF](https://www.consultantconnect.org.uk/wp-content/uploads/2021/07/Taking_the_best_photos_for_Telederm_Guide.05.pdf); [NHS Western Isles Good Photography Guide](https://www.benbecula.wihb.scot.nhs.uk/wp-content/uploads/2024/12/The-Good-Photography-Guide.pdf)
  - Tap the screen on the lesion to focus.
  - If too close, step back slightly and zoom (close-ups blur).
  - Minimise window backlight.
  - Take one close-up, one standard and one zoomed-out image.

### Inferences
- [本報告推論] A note on flash: TrueImage suggests "turn on flash" for dim light, but flash causes specular glare on moist or taped skin, and the project brief asks for "避免閃光". Recommend "move to a bright place or turn on the room light, avoid flash glare", and test both locally.
- [本報告推論] LINE reply templates (Traditional Chinese, research-prototype tone, no diagnosis). Send one message with at most 1-2 specific fixes, chosen by detected reason in this priority order: wrong subject > face/privacy > blur > too dark > overexposed/glare > too far > occluded > cropped.
  - 共同開頭（請重拍）：「謝謝您上傳照片。這張照片目前不容易判讀，想麻煩您再拍一張：」
  - 模糊：「請把手機拿穩、離手臂約 15–20 公分，先點一下螢幕上打針的位置讓它對焦，再按快門。」
  - 太暗：「請到明亮的地方（例如開燈的室內或靠近窗邊但不要背光），避免使用閃光燈。」
  - 過亮／反光：「畫面有反光或太亮，請稍微換個角度，避免燈光或陽光直接照在皮膚上，也不要開閃光燈。」
  - 太遠：「請靠近一點，讓打針（留置針）的位置佔畫面大約一半。」
  - 太近／被切到：「請稍微往後一點，讓打針位置和周圍約一個手掌寬的皮膚都完整入鏡。」
  - 被膠布／敷料遮住：「打針的位置被膠布或紗布遮住了。請不要自行撕開敷料；若醫護人員方便協助，再拍一張能看到周圍皮膚的照片。」（Safety: never tell the public to remove a dressing or catheter.）
  - 非手臂／非照片（cannot judge）：「這張圖片看起來不是手臂或手背打針部位的照片（例如截圖、文件或其他物品），本研究系統無法判讀。如需上傳，請拍攝手臂或手背打針的位置。」
  - 拍到臉：「為保護您的隱私，請只拍手臂或手背，不要拍到臉或其他可辨識身分的資訊。這張照片不會被納入研究資料。」（Use only if the retention policy really discards the photo; check that the wording matches the implementation.）
  - 需人工審閱：「已收到照片，系統需要研究人員進一步確認，確認後會再回覆您。」
  - 結果（research reference only）：「以下為研究用系統的初步參考結果，並非醫療診斷。若有紅、腫、熱、痛或其他不適，請立即告知醫護人員或就醫。」
  - Footer for all messages: 「本服務為研究用途，不提供醫療診斷。」
- [本報告推論] Principle conflict to flag: auto-sending a "result" reply to public LINE users before a human confirms it could count as releasing a model suggestion without human confirmation, and could read as a diagnostic claim. Safer NOW: only "please retake", "cannot judge" and "needs human review" are automatic; "result" is sent only after a researcher confirms. LINE uploads of IV sites from outside the hospital also mean real patients, so the escalation text ("請告知醫護人員") is required.

### Gaps
- No randomised trial of automated photo-retake feedback was found → 未找到可靠證據. The TrueImage 2.0 pilot design is not confirmed.
- The full ATA "Practice Guidelines for Teledermatology" text was not retrieved (only the table of contents was visible), so do not quote it.
- No study of retake-feedback wording in Chinese or via messaging apps was found → 未找到可靠證據.

---

## B4. Validating a learned quality gate against the fixed-formula gate; rejection-rate monitoring; NOW vs FUTURE

### Takeaway
Compare any learned quality gate head-to-head with the current Laplacian/dark-bright formula on three things:
1. downstream phlebitis and stage accuracy on the accepted photos;
2. agreement with human "usable/unusable" labels;
3. the rejection rate it imposes on genuine users.

Use patient-grouped splits and run in shadow mode first. TrueImage shows the operating point is a policy trade-off: reject 10% of poor photos while keeping >95% of good ones, or reject 50% while keeping 80%.

### Cited Findings
- **[研究證據] Operating-point trade-off.** TrueImage could reject 50% of poor photos while keeping 80% of good ones, or reject 10% of poor while keeping >95% of good. The authors say thresholds should be set per clinician or practice and per disease category. — [arXiv 2010.02086](https://arxiv.org/abs/2010.02086)
- **[研究證據] Expert-level ceiling.** ImageQX reached macro F1 0.73 vs inter-rater 0.77, so a model cannot be validated beyond rater agreement; report both. — [PMC10468541](https://pmc.ncbi.nlm.nih.gov/articles/PMC10468541)
- **[研究證據] Base rates differ by setting.** Inadequate patient-submitted photos were 8.8% at UCSF (no instructions), while at Duke 37.8% were insufficient when rated without context. The expected rejection rate depends heavily on population and context. — [eScholarship](https://escholarship.org/uc/item/1vs9c5n5)
- **[研究證據] Failure detection is not the same as OOD detection.** Following Bernhardt et al., judge confidence-based rejection by its effect on the downstream classifier's errors (risk-coverage), not only by OOD AUROC. — [arXiv 2205.14094](https://arxiv.org/abs/2205.14094)

### Inferences
- [本報告推論] Validation protocol:
  1. **Labelled set:** every photo gets a human `usable_for_staging` label plus reasons (B2). Double-label at least 30% of photos to compute κ.
  2. **Gates to compare:** G0 = no gate; G1 = current fixed formula (warn/reject thresholds); G2 = learned DINOv2+LR quality model; G3 = G1 OR G2.
  3. **Metrics for each gate:**
     - sensitivity and specificity against the human usable label;
     - rejection rate on genuinely usable photos;
     - **downstream** phlebitis yes/no and stage accuracy (balanced accuracy, macro-F1) on accepted photos vs coverage (risk-coverage curve).
     - Use GroupKFold by patient throughout, and bootstrap by patient for CIs.
  4. **Decision rule:** call G2 better only if it improves downstream accuracy at equal or lower false rejection of usable photos, with a patient-bootstrap CI that excludes zero. NOW this will almost certainly be inconclusive (14 patients), so report it as exploratory.
  5. **Shadow mode in production:** run G1 (active, warn-only) and G2 (logged only) side by side. Review disagreements weekly with a human, and switch to "reject" only after human sign-off.
- [本報告推論] Monitoring:
  - Track rejection rate by source (hospital vs LINE), by reason and by week.
  - Track the retake success rate (share of users whose next upload passes), time-to-usable-photo and the human override rate.
  - Alert a human (no automatic action) if the rejection rate of hospital photos exceeds e.g. 10% (hospital photos should mostly pass), or if the LINE rejection rate changes by more than 2× week-on-week.
- [本報告推論] NOW vs FUTURE:
  - **NOW** (~120 photos, 14 patients):
    - Keep the fixed formula as the active gate in **warn-only** mode.
    - Compute it on the YOLO IV-site crop instead of the whole image, to reduce background effects.
    - Add the DINOv2 kNN + CLIP domain gate.
    - Start human quality labelling and measure κ.
    - Use synthetic degradations only for development tests, not for claims.
  - **FUTURE** (~1,000 balanced photos plus real LINE rejects):
    - Train G2 (one LR per reason) in a human-triggered run and compare it with G1 as above.
    - Consider moving to "reject" only for the clearest reasons (severe blur, non-photo).
- [本報告推論] Compute budget summary (consumer NVIDIA GPU, to be measured):
  - YOLO detection + DINOv2-small + LR heads + CLIP/SigLIP-base + kNN should total well under 100 ms of GPU time per photo.
  - YuNet and the fixed formula on CPU: tens of ms.
  - OCR, run only when needed: hundreds of ms.
  - Avoid LMM-based IQA (Q-Align class) on the same GPU.

### Gaps
- No published head-to-head comparison of fixed-formula vs learned quality gates on downstream medical classifier accuracy was found → 未找到可靠證據.
- No evidence was found on acceptable user-facing rejection rates for public health photo services → 未找到可靠證據.

---

## References (full; access date 2026-10-31)
1. Hendrycks D, Gimpel K. A Baseline for Detecting Misclassified and Out-of-Distribution Examples in Neural Networks. ICLR 2017. arXiv:1610.02136. https://arxiv.org/abs/1610.02136 [B]
2. Liang S, Li Y, Srikant R. Enhancing The Reliability of Out-of-distribution Image Detection in Neural Networks (ODIN). ICLR 2018. arXiv:1706.02690. https://arxiv.org/abs/1706.02690 [B]
3. Lee K, Lee K, Lee H, Shin J. A Simple Unified Framework for Detecting Out-of-Distribution Samples and Adversarial Attacks. NeurIPS 2018. arXiv:1807.03888. https://arxiv.org/abs/1807.03888 [B]
4. Hendrycks D, Mazeika M, Dietterich T. Deep Anomaly Detection with Outlier Exposure. ICLR 2019. arXiv:1812.04606. https://arxiv.org/abs/1812.04606 [B]
5. Liu W, Wang X, Owens J, Li Y. Energy-based Out-of-distribution Detection. NeurIPS 2020. arXiv:2010.03759. https://neurips.cc/virtual/2020/poster/17313 [B]
6. Sun Y, Guo C, Li Y. ReAct: Out-of-distribution Detection With Rectified Activations. NeurIPS 2021. arXiv:2111.12797. https://arxiv.org/abs/2111.12797 [B]
7. Sun Y, Ming Y, Zhu X, Li Y. Out-of-Distribution Detection with Deep Nearest Neighbors. ICML 2022. arXiv:2204.06507. https://arxiv.org/abs/2204.06507 [B]
8. Wang H, Li Z, Feng L, Zhang W. ViM: Out-Of-Distribution with Virtual-logit Matching. CVPR 2022. arXiv:2203.10807. https://arxiv.org/abs/2203.10807 [B] (title verified via arXiv API; author list not re-checked)
9. Ming Y, Cai Z, Gu J, Sun Y, Li W, Li Y. Delving into Out-of-Distribution Detection with Vision-Language Representations. NeurIPS 2022. https://papers.nips.cc/paper_files/paper/2022/hash/e43a33994a28f746dcfd53eb51ed3c2d-Abstract-Conference.html [B]
10. Zhang J, Yang J, et al. OpenOOD v1.5: Enhanced Benchmark for Out-of-Distribution Detection. arXiv:2306.09301. https://arxiv.org/html/2306.09301v5 [D] (OpenOOD v1: Yang J et al., NeurIPS 2022 Datasets & Benchmarks [B])
11. Yang J, Zhou K, Li Y, Liu Z. Generalized Out-of-Distribution Detection: A Survey. arXiv:2110.11334. https://arxiv.org/abs/2110.11334 [B/D]
12. Oquab M, et al. DINOv2: Learning Robust Visual Features without Supervision. arXiv:2304.07193. https://arxiv.org/abs/2304.07193 [D]
13. Zhao S, Liu J, Wen X, Tan H, Qi X. Equipping Vision Foundation Model with Mixture of Experts for Out-of-Distribution Detection. arXiv:2510.10584 (ICCV 2025 supplemental on CVF). https://arxiv.org/html/2510.10584 [D/B]
14. Fi-ImageNet-1k: An OOD Benchmark From the Inside of the ImageNet-1k Validation Set. arXiv:2609.01027 (2026). https://arxiv.org/pdf/2609.01027 [D] (authors not recorded)
15. Bernhardt M, De Sousa Ribeiro F, Glocker B. Failure Detection in Medical Image Classification: A Reality Check and Benchmarking Testbed. TMLR 2022. arXiv:2205.14094. https://arxiv.org/abs/2205.14094 [B]
16. Berger C, Paschali M, Glocker B, Kamnitsas K. Confidence-based Out-of-Distribution Detection: A Comparative Study and Analysis. UNSURE @ MICCAI 2021. arXiv:2107.02568. https://arxiv.org/abs/2107.02568 [C]
17. Guha Roy A, Ren J, Azizi S, Loh A, Natarajan V, Mustafa B, Pawlowski N, Freyberg J, Liu Y, Beaver Z, Vo N, Bui P, Winter S, MacWilliams P, Corrado GS, Telang U, Liu Y, Cemgil T, Karthikesalingam A, et al. Does your dermatology classifier know what it doesn't know? Detecting the long-tail of unseen conditions. Med Image Anal 2022;75:102274. doi:10.1016/j.media.2021.102274 [B]
18. Combalia M, Codella N, Rotemberg V, Carrera C, Dusza S, Gutman D, Helba B, Kittler H, Kurtansky NR, Liopyris K, Marchetti MA, Podlipnik S, Puig S, Rinner C, Tschandl P, Weber J, Halpern A, Malvehy J. Validation of artificial intelligence prediction models for skin cancer diagnosis using dermoscopy images: the 2019 ISIC Grand Challenge. Lancet Digit Health 2022;4(5):e330-e339. doi:10.1016/S2589-7500(22)00021-8 [B]
19. Unsupervised Approaches for Out-Of-Distribution Dermoscopic Lesion Detection. arXiv:2111.04807. https://ar5iv.labs.arxiv.org/html/2111.04807 [D]
20. Woodland M, et al. Dimensionality Reduction and Nearest Neighbors for Improving Out-of-Distribution Detection in Medical Image Segmentation. arXiv:2408.02761. https://arxiv.org/abs/2408.02761 [D]
21. Out-of-distribution Detection in Medical Image Analysis: A survey. arXiv:2404.18279. https://arxiv.org/abs/2404.18279 [D]
22. Mittal A, Moorthy AK, Bovik AC. No-Reference Image Quality Assessment in the Spatial Domain (BRISQUE). IEEE TIP 2012;21(12):4695-4708. doi:10.1109/TIP.2012.2214050 [B]
23. Mittal A, Soundararajan R, Bovik AC. Making a "Completely Blind" Image Quality Analyzer (NIQE). IEEE SPL 2013;20(3):209-212. doi:10.1109/LSP.2012.2227726 [B]
24. Talebi H, Milanfar P. NIMA: Neural Image Assessment. IEEE TIP 2018;27(8):3998-4011. doi:10.1109/TIP.2018.2831899 [B]
25. Ke J, Wang Q, Wang Y, Milanfar P, Yang F. MUSIQ: Multi-scale Image Quality Transformer. ICCV 2021. arXiv:2108.05997. https://arxiv.org/abs/2108.05997 [B]
26. Wang J, Chan KCK, Loy CC. Exploring CLIP for Assessing the Look and Feel of Images. AAAI 2023. https://ojs.aaai.org/index.php/AAAI/article/view/25353/25125 [B]
27. Wu H, et al. Q-Align: Teaching LMMs for Visual Scoring via Discrete Text-Defined Levels. arXiv:2312.17090. https://arxiv.org/abs/2312.17090 [D/B]
28. Chen C, et al. IQA-PyTorch (pyiqa). GitHub https://github.com/chaofengc/IQA-PyTorch ; PyPI https://pypi.org/project/pyiqa/ [E]
29. Tian X, Anantrasirichai N, Nicholson L, Achim A. The quest for early detection of retinal disease: 3D CycleGAN-based translation of OCT into confocal microscopy. Biol Imaging 2024;4:e15. doi:10.1017/S2633903X24000163 [C]
30. Vodrahalli K, Daneshjou R, Novoa RA, Chiou A, Ko JM, Zou J. TrueImage: A Machine Learning Algorithm to Improve the Quality of Telehealth Photos. Pac Symp Biocomput 2021;26:220-231. arXiv:2010.02086. https://arxiv.org/abs/2010.02086 [C]
31. Vodrahalli K, Ko J, Chiou AS, Novoa R, Abid A, Phung M, Yekrang K, Petrone P, Zou J, Daneshjou R. Development and Clinical Evaluation of an AI Support Tool for Improving Telemedicine Photo Quality. arXiv:2209.09105 (2022). https://arxiv.org/abs/2209.09105 [D]
32. Jalaboi R, Winther O, Galimzianova A. Explainable Image Quality Assessments in Teledermatological Photography. Telemed J E Health 2023;29(9):1342-1348. doi:10.1089/tmj.2022.0405. https://pmc.ncbi.nlm.nih.gov/articles/PMC10468541 [C]
33. Liu JY, Lohman ME, Klufas D, Fassett M, Amerson E, Twigg A, Leslie K, Khodosh R. Patient photographs taken without instructions are of sufficient quality for clinical decision making in teledermatology. Dermatol Online J 2024;30(3):17. doi:10.5070/D330363877. https://escholarship.org/uc/item/1vs9c5n5 [C]
34. Katragadda C, Finnane A, Soyer HP, Marghoob AA, Halpern A, Malvehy J, Kittler H, Hofmann-Wellenhof R, Da Silva D, Abraham I, Curiel-Lewandrowski C. Technique Standards for Skin Lesion Imaging: A Delphi Consensus Statement. JAMA Dermatol 2017;153(2):207-213. doi:10.1001/jamadermatol.2016.3949 [B]
35. Finnane A, Curiel-Lewandrowski C, Wimberley G, Caffery L, Katragadda C, Halpern A, Marghoob AA, Malvehy J, Kittler H, Hofmann-Wellenhof R, Abraham I, Soyer HP. Proposed Technical Guidelines for the Acquisition of Clinical Images of Skin-Related Conditions. JAMA Dermatol 2017;153(5):453-457. doi:10.1001/jamadermatol.2016.6214 [B]
36. Camaj Deda L, Goldberg RH, Jamerson TA, Lee I, Tejasvi T. Dermoscopy practice guidelines for use in telemedicine. npj Digit Med 2022;5:55. doi:10.1038/s41746-022-00587-9. https://pmc.ncbi.nlm.nih.gov/articles/PMC9046409 [B]
37. HaGRID – HAnd Gesture Recognition Image Dataset. https://github.com/hukenovs/hagrid ; arXiv:2206.08219 [D/E]
38. ShiqiYu/libfacedetection (YuNet). https://github.com/ShiqiYu/libfacedetection [E]
39. Jaeger PF, Lüth CT, Klein L, Bungert TJ. A Call to Reflect on Evaluation Practices for Failure Detection in Image Classification. arXiv:2211.15259 [D]
40. Bungert TJ, et al. Understanding Silent Failures in Medical Image Classification. arXiv:2307.14729 [D] (existence seen in search results only; content not reviewed)
