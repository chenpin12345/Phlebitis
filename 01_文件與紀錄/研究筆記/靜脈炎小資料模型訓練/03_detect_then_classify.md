# Detect-then-classify (lesion / insertion-site crop) vs whole-image classification for small medical / skin photo datasets

Scope: IV-insertion-site phlebitis photos (arm / hand dorsum), binary (phlebitis vs normal) and staging (normal / stage 1 / stage 2). Research prototype, not clinical diagnosis.
All sources accessed 2026-10-30. Grades: [A] official docs/registries/standards, [B] systematic review or top-venue peer-reviewed, [C] other peer-reviewed, [D] preprint, [E] blog/vendor docs/forum/teaching material (supporting only).
Each conclusion is labelled **research evidence**, **industry practice**, or **inference**.
Search coverage: about 30 search and fetch calls in at least two rounds per question: an overview search first, then the primary text (PMC full text, arXiv/ar5iv full text, or the PDF itself). Where I could only see an abstract or search snippet, the note says so.

## Q1. What does research show about lesion cropping vs full image (dermatology, wounds / pressure injury, DFU, other medical imaging)?

### Takeaway
No study I found ran a clean, patient-level, head-to-head comparison of "detector/manual crop → classifier" against "whole photo → classifier" on clinical skin or wound photos. Published two-stage systems (face skin cancer, pressure injury, DFU) work, but none of them isolates how much the crop itself contributes. The quantified gains for "local + global" come from large datasets (ChestX-ray14, 112k images) or from abstract-level claims. In the one ablation I could verify, the crop alone was worse than the whole image, and only the fusion of the two helped.

### Cited Findings
- **Face skin cancer, two-stage (R-CNN blob detector → CNN on crops)**, Han SS, Moon IJ et al., JAMA Dermatol 2020;156(1):29-37, doi:10.1001/jamadermatol.2019.3807 [B]. Training used 182,348 clinical photos, from which the detector produced 924,538 candidate lesions; the classifier was trained on 1,106,886 crops. Validation: 2,844 images from 673 patients at 3 hospitals; AUC 0.910 overall (dermatology set 0.896, plastic surgery set 0.954). At the T90 threshold, sensitivity 89.2% / specificity 77.9%. Crop margin and size are not reported. Validation images were taken after 2018 to avoid overlap, but patient-level separation is not stated explicitly, and Asan Medical Center supplied both training and validation data, so the validation is only partly external. The authors did not test an end-to-end whole-image model and list the multistage design as a limitation. Patient score = maximum malignancy output across a mean of 4.2 photos per patient. Handling of zero detections is not described. — [PMC6902187](https://pmc.ncbi.nlm.nih.gov/articles/PMC6902187) (**research evidence**)
- **Pressure injury, two-stage (YOLOv9 → DenseNet161 on crops)**, Lai T-Y, Chou Y-J, Liu C-Y, et al., "Novel two-stage deep learning framework for automated pressure injury classification", BMJ Health Care Inform 2026;33(1):e101636, doi:10.1136/bmjhci-2025-101636 [C]. Data: 1,807 images from 232 patients, single centre (China Medical University Hospital, Taiwan, 2020-2024). Split: random 80/20, with patient-level separation **not stated** (leakage possible). Detector mAP@0.5 = 0.796. Internal test (n=365): accuracy 0.775, F1 0.775. In a prospective pilot (190 patients), accuracy was 0.887 but F1 only 0.574. 13 of the 190 cases had incorrect lesion localisation, and when lesion colour resembled the surrounding skin the boxes were partial and the crops were misclassified. No crop margin is reported, there is no fallback for detector failure, and the authors state there was **no single-stage baseline**, so the gain from the two-stage design is untested. The paper does not describe its independent CMUH set as multi-site external validation. — [PMC13034204](https://pmc.ncbi.nlm.nih.gov/articles/PMC13034204/) (**research evidence**)
- **Pressure ulcer, "semi-two-stream" (original image + cropped wound area)**, Zalluhoğlu C, Akdogan D, Karakaya D, Güzel MS, Ulgu MM, Ardali K, et al., "Region-Based Semi-Two-Stream Convolutional Neural Networks for Pressure Ulcer Recognition", J Imaging Inform Med 2024;(2):801-813, doi:10.1007/s10278-023-00960-4 [C]. The abstract reports 93% accuracy, 93% precision, 92% recall and 93% F1, and says the method beat the base CNNs. I could only reach the abstract (Springer redirected to a login), so the dataset size, the crop method, the patient split and the single-stream baseline numbers are **not verified**. — [Ankara Univ. AVESIS record](https://avesis.ankara.edu.tr/yayin/2eaac59a-6e10-4372-82b1-e318b0a20a45/region-based-semi-two-stream-convolutional-neural-networks-for-pressure-ulcer-recognition) (**research evidence, abstract-level only**)
- **DFU (DFUC2021)**, Yap MH et al., "Analysis Towards Classification of Infection and Ischaemia of Diabetic Foot Ulcers", IEEE BHI 2021, arXiv:2104.03068 [D/C]. Ulcer regions were cropped from expert bounding boxes (averaged across annotators) to make patches: 15,683 patches in total (5,955 train, 5,734 test, 3,994 unlabelled). EfficientNet-B0 was the best backbone, with four-class macro-F1 ≈ 0.55. So crop-based classification of infection / ischaemia was still hard even with about 6k labelled patches, and the paper has no whole-image comparison. — [arXiv 2104.03068](https://arxiv.org/abs/2104.03068) (**research evidence**)
- **Pressure-injury segmentation and staging in one pass (Mask R-CNN)**, Swerdlow et al., Comput Math Methods Med 2023, doi:10.1155/2023/3858997 [C]. The search snippet reports 92.6% detection accuracy and 93.0% segmentation accuracy. Full text not opened. — [PMC9911250](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9911250/) (**research evidence, snippet-level**)
- **Dermoscopy "cropping vs resizing"**, Mahbod A et al., CMPB 2020, doi:10.1016/j.cmpb.2020.105475 [C], with the earlier conference version arXiv:2006.14715 [D]. Cropping beat resizing at all six scales (224-450 px), and the multi-scale, multi-network ensemble (MSM-CNN) reached 86.2% balanced accuracy on ISIC 2018. **Caveat:** here "cropping" means cropping the (already lesion-centred) dermoscopic image to keep native resolution, not a crop around a detector box. The supported point is "keep lesion pixels at higher resolution"; it does not show that a lesion box beats the whole image. Inputs of 64×64 degraded performance, while 128 px and above performed well. — [arXiv 2006.14715](https://arxiv.org/pdf/2006.14715) (**research evidence**)
- **Chest X-ray global + local (AG-CNN)**, Guan Q, Huang Y, Zhong Z, Zheng Z, Zheng L, Yang Y, "Diagnose like a Radiologist: Attention Guided CNN for Thorax Disease Classification", arXiv:1801.09927 (2018) [D]; journal version Pattern Recognit Lett 2020;131:38-45 [C]. Mean AUC with ResNet-50: global 0.841, **local crop only 0.817**, fusion 0.868. With DenseNet-121: 0.840 / 0.810 / 0.871. The crop comes from the heat-map mask (τ=0.7) → largest connected region → bounding box. The data were ChestX-ray14 (112,120 images, 30,805 patients), **randomly shuffled 70/10/20 without a stated patient-level split**, so patient leakage is possible. — [ar5iv 1801.09927](https://ar5iv.labs.arxiv.org/html/1801.09927) (**research evidence**, large data)
- **Generic detection: context padding around the box helps**, Girshick R et al., "Rich feature hierarchies…" (R-CNN), CVPR 2014, arXiv:1311.2524 [B]. Text verified from the PDF: the box is dilated so that p=16 px of context surround it at the 227 px warped size (about 7% per side, ≈1.16× box), and "warping with context padding (p = 16 pixels) outperformed the alternatives by a large margin (3-5 mAP points)". — [arXiv 1311.2524](https://arxiv.org/abs/1311.2524) (**research evidence**, natural images)
- **Object-centric cropping in few-shot classification**, Abdali A, Boguslawski B, Drumetz L, Gripon V, arXiv:2508.00218 (2025) [D]. Adding the object's location "markedly enhances classification across established benchmarks", and much of the gain survives with SAM boxes from a single click. I verified only the abstract. A search snippet says that a fixed 60 px context worked best with ground-truth boxes, while "multiple" context modes worked slightly better with imperfect SAM boxes; that detail is **unverified**. — [arXiv 2508.00218](https://arxiv.org/abs/2508.00218) (**research evidence, natural images, preprint**)

### Inferences
- (**inference**) In this project, `tensor_image()` letterboxes the *whole* photo to 224×224 (`src/workbench/adapters.py` L142). A 4032×3024 phone photo is shrunk about 18× on its long side, so a 300 px erythema patch becomes about 17 px. The Mahbod 64-px result suggests that lesion detail at roughly that scale is degraded. This is the strongest mechanistic reason to expect a benefit from cropping here. It argues for **higher effective resolution on the insertion site**, which can also be had from a larger whole-image input (e.g. 448-518 px), not only from a crop.
- (**inference**) The published two-stage systems needed hundreds to thousands of boxed images, and even then their detectors mislocalised (Lai: 13/190). None of them shows that cropping beats the whole image on the same patients.

### Gaps
- No reliable evidence found for a patient-level, same-data head-to-head of crop vs whole image on **clinical skin / wound photographs**, and none with external validation.
- No reliable evidence found on burn-depth or cellulitis/erythema photo studies comparing crop vs whole image. The searches found only erythema-migrans and general skin-disease classifiers ([PMC9060152](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9060152/)), none relevant to the crop question.
- The semi-two-stream paper's baseline numbers could not be verified (paywall).

## Q2. Counter-evidence: when cropping loses context, detector errors propagate, and small-data failures

### Takeaway
There are three kinds of counter-evidence. (1) In the only ablation I could verify, the local crop alone was *worse* than the whole image (AG-CNN). (2) Detector mislocalisation, especially partial boxes on low-contrast lesions, propagated into misclassification in a real two-stage wound system. (3) Context carries real signal and also spurious signal. For phlebitis staging the context is clinically necessary: the higher INS grades are defined by streak formation and palpable cord length along the vein, which can extend beyond a tight lesion box.

### Cited Findings
- Local-only branch lower than global: ResNet-50 0.817 vs 0.841, DenseNet-121 0.810 vs 0.840 mean AUC. — [Guan et al., ar5iv 1801.09927](https://ar5iv.labs.arxiv.org/html/1801.09927) [D] (**research evidence**)
- Error propagation: 13/190 prospective cases had wrong lesion localisation. Lesions coloured like the surrounding skin got partial boxes, which led to misclassification, and intra-lesion heterogeneity led to under-staging. Prospective F1 was 0.574. — [Lai et al. 2026, PMC13034204](https://pmc.ncbi.nlm.nih.gov/articles/PMC13034204/) [C] (**research evidence**)
- Two-stage face system: skin markings were mistaken for lesions, small periocular lesions were missed, and non-uniform backgrounds affected results. — [Han et al. 2020, PMC6902187](https://pmc.ncbi.nlm.nih.gov/articles/PMC6902187) [B] (**research evidence**)
- R-CNN error analysis: most top false positives were poor localisation (IoU 0.1-0.5) rather than background confusion, and bounding-box regression fixed many of them. — [Girshick et al. 2014, arXiv 1311.2524](https://arxiv.org/abs/1311.2524) [B] (**research evidence**, natural images)
- Context also carries spurious signal: models trained on ISIC images with the lesion fully occluded still scored above a dermatologist-curated benchmark, and adding clinically meaningful information did not help. — Bissoto A, Fornaciali M, Valle E, Avila S, "(De)Constructing Bias on Skin Lesion Datasets", CVPR Workshops (ISIC) 2019, [arXiv 1904.08818](https://arxiv.org/abs/1904.08818v1) [C/D]; follow-up "Debiasing Skin Lesion Datasets and Models? Not So Fast" [arXiv 2004.11457](https://ar5iv.arxiv.org/html/2004.11457) [D] (**research evidence**). This cuts both ways: a whole image can learn shortcuts (dressing type, background, hospital vs LINE source), and a crop removes some of them.
- Phlebitis grading needs extent. In INS-based scales, grade 1 is erythema at the access site, with or without pain. Grade 2 is pain with erythema and/or oedema. Grade 3 adds streak formation or a palpable venous cord. Grade 4 adds a cord longer than 1 inch and/or purulent drainage. One Indonesian text places the ≈1 inch cord at grade 3, which conflicts with the INS wording. Pain and palpable cord cannot be seen in a photo. — [MGH PCS IV module 9 (teaching material citing INS)](https://www.mghpcs.org/EED/CL/Assets/documents/CL_Module9.pdf) [E]; the INS Standards themselves were not opened. (**industry practice**)

### Inferences
- (**inference**) A tight lesion box (1.0-1.2×) will often cut off a streak running proximally along the vein, along with the oedema margin. For stage 2 (or INS grade 3+), the classifier then loses the very feature that defines the stage. Use context ratios of 1.5-2.5×, multi-scale crops, or crop + whole-image fusion, not tight crops. Elongated streaks also argue for padding along the box's long axis or using a square crop around an enlarged box.
- (**inference**) With ~24 boxed photos from ≤14 patients, any YOLO detector will have high localisation variance. A crop pipeline then multiplies two error sources, and the photo-level effect cannot be separated from patient identity.
- (**inference, important for this dataset**) **Shortcut risk:** if only positive photos have lesion boxes, any "crop when a box exists, whole image otherwise" rule makes the input type itself predictive of the label. The crop ROI must therefore be defined so that it exists for **every** photo, normals included: an **insertion-site / dressing ROI**, not a "lesion" ROI. Either annotate it on normals too, or generate it by the same detector for every image.

### Gaps
- No reliable evidence found that quantifies how much accuracy is lost when a crop cuts away surrounding erythema or streaks, for phlebitis or for cellulitis.
- No phlebitis-specific study of what image area graders actually use (no reader eye-tracking or ROI study found).

## Q3. Ground-truth boxes for training vs detector boxes at test time (train/test mismatch)

### Takeaway
I found no medical study that measured this mismatch directly. Evidence from general vision (R-CNN's IoU-band training, few-shot detection, and object-centric cropping) and established detection practice support training the classifier on **jittered boxes**, and on **out-of-fold detector boxes**, rather than on clean manual boxes only.

### Cited Findings
- R-CNN trains its CNN on every proposal with IoU ≥ 0.5 to ground truth as a positive, i.e. it deliberately trains on imperfect boxes. For the SVM, the negative threshold IoU < 0.3 was chosen by grid search over {0, 0.1, … 0.5}; using 0.5 cost 5 mAP and using 0 cost 4 mAP ("selecting this threshold carefully is important"). — [Girshick et al. 2014, arXiv 1311.2524](https://arxiv.org/abs/1311.2524) [B] (**research evidence**)
- A CVPR 2023 few-shot detection paper reports, per a search snippet, that classification accuracy drops by about 5% as the box IoU with ground truth falls from 1.0 to 0.5. — Xu et al., "Generating Features with Increased Crop-related Diversity for Few-Shot Object Detection", CVPR 2023, [CVF open access PDF](https://openaccess.thecvf.com/content/CVPR2023/papers/Xu_Generating_Features_With_Increased_Crop-Related_Diversity_for_Few-Shot_Object_Detection_CVPR_2023_paper.pdf) [B]. **Number not verified in the full text.** (**research evidence, unverified number**)
- A fine-grained classification paper shifts and rescales boxes during classifier training so that it is robust to detector offsets ("Region based Ensemble Learning Network for Fine-grained Classification", [arXiv 1902.03377](https://arxiv.org/pdf/1902.03377)) [D]. Snippet-level only. (**research evidence, snippet-level**)
- DFUC2021 averaged boxes from several annotators before cropping, which reduces single-annotator box noise. — [Yap et al., arXiv 2104.03068](https://arxiv.org/abs/2104.03068) [D] (**research evidence**)

### Inferences
- (**inference / industry practice**) Recommended training recipe:
  (a) **Jitter manual boxes** on the fly: centre shift ±10-15% of box w/h, scale (context ratio) uniform in [1.2, 2.0] (try [1.3, 2.5] for staging), aspect ratio ±10%, and reject jitters whose IoU with the original box is below 0.5. This mirrors R-CNN's ≥0.5 positive band.
  (b) **Cross-fitted detector boxes:** inside each StratifiedGroupKFold training fold, train the detector on k-1 sub-folds and predict boxes on the held-out sub-fold, so every training photo gets a box from a detector that never saw it. Then mix about 50% jittered manual crops with 50% out-of-fold detector crops. A detector predicting on its own training images gives near-perfect boxes and hides the test-time error.
  (c) At test time use a **fixed context ratio** (e.g. 1.5×), optionally averaged over {1.2, 1.5, 2.0} as test-time augmentation.
- (**inference**) Report results separately for (i) manual boxes at test time (upper bound, "oracle ROI") and (ii) detector boxes at test time (the realistic pipeline). The gap between them is the mismatch cost.

### Gaps
- No reliable evidence found on clinical skin, wound or phlebitis photos for the size of the GT-box-train / detector-box-test gap, or for the best jitter ranges. The ranges above are inference.

## Q4. Global + local dual-branch / two-stream / zoom-in / MIL in small data: help or overfit?

### Takeaway
Fusion beat either branch alone in AG-CNN, but on about 78k training images. The pressure-ulcer semi-two-stream paper claims a gain with unverified data size. Attention MIL beat instance-level pooling on very small histology sets (58 and 100 images), though with whole-slide-style tiling, not phone photos. I found no small clinical-photo study with a proper overfitting ablation. For 14 patients, a *trainable* second branch is very likely to overfit. The low-risk version is **frozen-feature fusion**: concatenate DINOv2/EfficientNet embeddings of the whole image and of the crops, then fit a regularised logistic regression.

### Cited Findings
- AG-CNN fusion: 0.868 vs global 0.841 (ResNet-50), trained on ChestX-ray14 (random 70/10/20 split of 112,120 images, patient split not stated). — [ar5iv 1801.09927](https://ar5iv.labs.arxiv.org/html/1801.09927) [D] (**research evidence**, large data)
- Semi-two-stream pressure ulcer model: 93% accuracy, claimed better than base CNNs (abstract only). — [Zalluhoğlu et al. 2024, doi:10.1007/s10278-023-00960-4](https://avesis.ankara.edu.tr/yayin/2eaac59a-6e10-4372-82b1-e318b0a20a45/region-based-semi-two-stream-convolutional-neural-networks-for-pressure-ulcer-recognition) [C] (**research evidence, abstract-level**)
- Attention-based deep MIL: Ilse M, Tomczak JM, Welling M, ICML 2018, [arXiv 1802.04712](https://arxiv.org/abs/1802.04712) [B]. Breast cancer: 58 H&E images (896×768, 32×32 patches, 672 per bag). Colon cancer: 100 images (27×27 patches). Evaluated with 10-fold CV × 5 repeats. AUC: breast 0.775 (attention) / 0.799 (gated) vs 0.612 (instance+max) / 0.719 (instance+mean); colon 0.968 vs 0.914 / 0.866. Patient-level splitting is not discussed, and there is no external validation. — [ar5iv 1802.04712](https://ar5iv.labs.arxiv.org/html/1802.04712) (**research evidence**)
- Dual-branch clinical skin lesion networks exist, e.g. CR-Conformer (Med Biol Eng Comput 2024, doi:10.1007/s11517-023-02904-0), with a +1.08% accuracy claim on a private 10-class clinical set; and a Double-Branch Network on about 3,361 clinical images (Front Med 2023, doi:10.3389/fmed.2023.1114362). Both were seen at snippet level only, and **no overfitting ablation was found in either.** — [search result listing (unpaywall / Frontiers PDF)](https://www.frontiersin.org/journals/medicine/articles/10.3389/fmed.2023.1114362/pdf) [C] (**research evidence, snippet-level**)

### Inferences
- (**inference**) NOW: a trainable dual-branch EfficientNet doubles the trainable head and compute, and with 9 normal photos (likely from very few patients) it will memorise patients. The frozen-feature version adds only logistic-regression weights (e.g. 384-dim DINOv2-S CLS × 3 views = 1,152 features → 1 or 3 outputs). It is the only variant worth testing now.
- (**inference**) FUTURE (~1,000 photos): a two-view EfficientNet-B0 with shared weights and late fusion (shared backbone, concatenated pooled features, dropout 0.3-0.5) becomes testable. Weight sharing keeps parameters at about 5.3M, as in a single network. Use AG-CNN-style attention crops only if no boxes exist; Grad-CAM-derived crops on small data are noisy.
- (**inference**) MIL over patches (tiling the whole photo into e.g. 224 px tiles at native resolution, plus attention pooling) is an alternative that needs **no boxes at all** and keeps resolution. Phone photos have far fewer informative tiles than histology, though, and there is no evidence for it on skin photos. It is a FUTURE option, not NOW.

### Gaps
- No reliable evidence found of a global+local model trained on fewer than ~500 clinical photos with patient-level CV.
- Zoom-in-Net (Wang et al., MICCAI 2017, diabetic retinopathy) was not opened in this round, so no numbers are cited.

## Q5. Existing phlebitis / infusion-site / PIVC image-AI studies

### Takeaway
I found **no peer-reviewed study** that detects or classifies phlebitis from photos of the insertion site, in English or Chinese searches. The only direct lead is a registered prospective trial (NCT07889895) using mobile-phone photos graded on the VIP scale, with no results posted. Other "phlebitis AI" work uses EHR data, and other PIVC imaging AI targets ultrasound or NIR vein finding, not phlebitis.

### Cited Findings
- **NCT07889895 "AI Prediction of PIVC-Related Phlebitis"** [A-registry]. Per the search snippets: prospective collection of demographic, clinical, catheter and catheter-site image data; real-time mobile-phone photos graded by expert nurses and a physician on the VIP scale (0-5), with phlebitis defined as VIP ≥ 2; a train/validation/test split; planned metrics include sensitivity, specificity, accuracy, precision, recall, F1 and calibration; 461 enrolled participants. **The record page did not render through the fetch tool, so the sponsor, country, dates and whether cropping is used could not be verified. No results are posted.** — [clinicaltrials.gov NCT07889895](https://clinicaltrials.gov/study/NCT07889895) (**research evidence: registration only**)
- EHR-based (non-image) phlebitis prediction, Seoul: Lee, Cho, Kim, "Deep Learning for Predicting Phlebitis in Patients with Intravenous Catheters", Stud Health Technol Inform 2024, doi:10.3233/SHTI240231. Per the snippet: 27,532 admissions and 70,293 PIVC events, accuracy 0.93, AUC 0.89. — [IOS Press](https://ebooks.iospress.nl/doi/10.3233/SHTI240231) [C] (**research evidence**, not image-based)
- An ML model for PIVC-associated phlebitis incidence from clinical variables (not images). — [PMC11295139](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11295139/) [C] (snippet-level)
- PIVC-adjacent imaging AI that is not phlebitis: ultrasound vein measurement on 998 images ([PMC9174762](https://pmc.ncbi.nlm.nih.gov/articles/PMC9174762/)) [C]; NIR venipuncture robot (VeniBot, [arXiv 2105.12951](https://arxiv.org/pdf/2105.12951)) [D]; YOLO detection of infusion containers and drip levels ([PMC9954958](https://pmc.ncbi.nlm.nih.gov/articles/PMC9954958/), [PubMed 34198397](https://pubmed.ncbi.nlm.nih.gov/34198397)) [C].
- A smartphone early-warning *display* for phlebitis prevention reported lower incidence (P = 0.001), but it does no image classification. — [i-JOE 48345](https://online-journals.org/index.php/i-joe/article/view/48345) [C] (snippet-level)
- VIP inter-observer reliability in one study: ICC = 0.906 (Portuguese version, Research Square preprint). — [researchsquare rs-882728](https://www.researchsquare.com/article/rs-882728/latest.pdf) [D] (snippet-level)

### Inferences
- (**inference**) There is no published benchmark, crop convention, or data-size reference for phlebitis photos. Any crop-vs-whole result from this project would be new and must be reported with patient counts and CIs, without performance claims beyond the folds.
- (**inference**) Because the reference standard (VIP / INS) includes pain and a palpable cord, which a photo cannot show, image-only staging has a ceiling set by the label definition, whatever the input framing.

### Gaps
- No reliable evidence found of phlebitis image studies from Taiwan, Korea, Japan or China. Chinese-language searching (静脉炎 图像 深度学习) returned only grading guides and vein-biometrics papers. CNKI, Wanfang and J-STAGE could not be searched directly with these tools.
- The NCT07889895 sponsor, country and timeline are unverified.

## Q6. NOW (14 patients, ~120 photos, ~24 boxed) vs FUTURE (~1,000 balanced photos): is crop-based classification viable, and how much boxed data does a detector need?

### Takeaway
**NOW:** a *detector-driven* crop pipeline is not viable as a primary method. 24 boxes from ≤14 patients cannot give a reliable detector, and the 9 normal photos make any difference unmeasurable: the 95% Wilson upper bound on normal FPR with 0/9 errors is about 30%. A **manual / human-confirmed insertion-site ROI for all ~120 photos, plus frozen-feature fusion (whole + 1.5× + 2.5× crop)**, is a reasonable *exploratory* paired comparison. It costs little compute, but it needs about 100 extra human box confirmations. **FUTURE (~1,000):** a detect-then-classify or two-view model becomes testable, provided boxes exist for every photo including normals, the classifier is trained on jittered and out-of-fold detector boxes, and the whole image is always kept as a branch or fallback. Patient count, not photo count, will remain the limiting factor.

### Cited Findings
- Ultralytics' training-tips guide gives **no minimum dataset size**. It suggests 300 epochs as a starting point, fewer epochs for smaller datasets to avoid overfitting, `fraction=` subset runs, and `batch=-1` auto-sizing to about 60% of GPU memory. — [docs.ultralytics.com/guides/model-training-tips](https://docs.ultralytics.com/guides/model-training-tips/) [E] (**industry practice**)
- YOLO11n: 2.6M params, 6.5 GFLOPs, 1.5 ms on T4 TensorRT at 640. YOLO11s: 9.4M params, 21.6 GFLOPs, 2.5 ms. — [docs.ultralytics.com/models/yolo11](https://docs.ultralytics.com/models/yolo11/) [A/E vendor docs]
- EfficientNet-B0 (torchvision IMAGENET1K_V1): 5,288,548 params, 0.39 GFLOPS, 20.5 MB, ImageNet top-1 77.692%. — [torchvision docs](https://docs.pytorch.org/vision/main/models/generated/torchvision.models.efficientnet_b0.html) [A/E vendor docs]
- Reference points for detector data size in two-stage wound and skin systems: 1,807 images / 232 patients → mAP50 0.796 with 13/190 prospective mislocalisations ([Lai 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13034204/)); 182k photos for the face detector ([Han 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC6902187)). (**research evidence**)

### Inferences

**Minimum boxed data (inference; no reliable evidence for a threshold).** I found no source that states a minimum number of boxes for a "reliable" medical lesion detector. As operating guidance, not evidence: treat the detector as a *box suggester* that a human confirms until it achieves, under patient-level CV, recall ≥ 0.9 at IoU ≥ 0.3-0.5 on the insertion-site ROI, with the CI reported. This probably needs a few hundred boxed photos from ≥ 50-100 patients. An insertion-site / dressing ROI (a large, consistent object) should be easier to learn than a lesion box. These numbers are inference.

**NOW (14 patients): recommended plan, all inference.**
1. Define the ROI as **"IV insertion site + surrounding skin"**, annotated on *every* photo including normals. YOLO proposes boxes and a human confirms each one (consistent with the no-auto-write rule). Store it as a separate label type so the existing lesion boxes are untouched.
2. Primary experiment: DINOv2-small frozen features → logistic regression, comparing (A) whole letterbox-224 (current), (B) crop at 1.5×, (C) crop at 2.5×, (D) concat[A, B, C], and (E) whole image at a higher input size (e.g. 448/518) as the "resolution-only" control. Same StratifiedGroupKFold folds and seeds, with patients as groups.
3. Do not train a detector-driven classifier now. At most, run YOLO crops at test time for a qualitative check.
4. Expect wide CIs. Report per-patient results and the paired difference with a patient-cluster bootstrap. With 14 patients, a "no significant difference" result is the expected outcome and is not evidence of equivalence.

**FUTURE (~1,000 balanced photos): inference.** Train YOLO11n/s or YOLO26s on the ROI with patient-level folds. Get cross-fitted (out-of-fold) detector boxes for the classifier training set. EfficientNet-B0 is then fine-tuned on mixed crops (jittered manual + OOF detector), optionally as a shared-weight two-view model (whole + crop). Keep the whole-image model as a parallel baseline and fallback. Validate on a held-out patient group and, if possible, on the LINE vs hospital sources separately (source shift).

**Method cards (all estimates are inference unless a source is cited).**

| Method | Evidence strength | Expected benefit / when not worth it | Min data (inference) | GPU memory / time (basis) | Main risks |
|---|---|---|---|---|---|
| Manual-ROI crop, frozen DINOv2 + LR, multi-ratio concat | Low (indirect: Mahbod resolution; AG-CNN fusion; R-CNN context) | Could recover detail lost by an ~18× downsample. Not worth it if the higher-resolution whole-image control (E) matches it. | All photos ROI-boxed (~120 now) | ViT-S/14 forward at 224, batch 1-16: well under 2 GB; ~120 photos × 3 views ≈ 360 forwards, i.e. seconds to about a minute on a consumer GPU; LR fit < 1 s. Basis: model size class; not measured here. | Shortcut if ROI only on positives; annotator ROI bias (single annotator) |
| EfficientNet-B0 trained on jittered crops (frozen or last stage) | Low-moderate (R-CNN IoU-band training; general practice) | Robustness to box error. Not worth it NOW (too few patients for fine-tuning to beat frozen features). | ≥ several hundred photos / ≥ 50 patients | Same FLOPs as current (0.39 GFLOPs per 224 input, torchvision); batch 32 with last stage unfrozen likely < 3 GB; ~1k photos × 30 epochs: minutes. | Overfit to patients; crop-scale leakage |
| YOLO detect → crop → classifier (full pipeline) | Moderate that it works at scale (Han 2020; Lai 2026); no evidence that it beats whole image | Useful for uncontrolled LINE framing (small site in a big photo). Not worth it if photos are already tightly framed. | Detector: few hundred boxed photos (inference) | YOLO11n at 640 trains on 24-1,000 images in minutes to about an hour on a consumer GPU (6.5 GFLOPs per image, Ultralytics); inference about 2.6M + 5.3M params, tens of ms per photo | Error propagation (Lai: 13/190); train/test box mismatch |
| Two-view shared-weight fusion (whole + crop) | Moderate on large data (AG-CNN); abstract-level for wounds | Keeps streak / oedema context and lesion detail. Not worth it NOW (trainable fusion head overfits). | ~1,000 photos | 2× forward per sample (≈0.78 GFLOPs); memory about 2× activations | Overfitting; more hyperparameters |
| MIL over native-resolution tiles | Moderate for histology (Ilse 2018, 58-100 images); none for skin photos | No boxes needed. Not worth it NOW. | ~1,000 photos | Tiles × forwards per photo (e.g. 20-50 tiles → 20-50× compute); use frozen features | Weak signal per tile; background tiles dominate |
| Fallback: whole image + "needs human review" when no ROI | Industry practice; consistent with the engine's existing "no box is not certainty of absence" | Always needed | n/a | n/a | Silent negatives if "no box" is mapped to normal |
| Fallback: centre crop / skin-colour crop | No reliable evidence found | Unreliable for LINE photos (arbitrary framing; lighting-sensitive skin segmentation) | n/a | Negligible | Systematic misses |

**Hyperparameter ranges (inference / industry practice).**
- Context ratio r (crop side = r × max(box w, h), square, clamped to the image and reflect- or mean-padded as in R-CNN): train jitter U[1.2, 2.0] (binary), U[1.3, 2.5] (staging); test fixed 1.5, with TTA {1.2, 1.5, 2.0}.
- Centre jitter ±0.10-0.15 × box size; aspect ±10%; keep jitter IoU ≥ 0.5 vs source box.
- Minimum crop side ≥ 224 px of native pixels (avoid upsampling tiny crops); if the box is < 5% of the image short side, use r ≥ 2.0.
- Detector for crop generation: conf 0.05-0.25 (lower than the display threshold), keep the top-1 box. If there are several boxes, classify each and take the max severity (analogous to Han's max-over-photos rule). imgsz 640-1024 for phone photos.
- Mix ratio of manual-jittered to OOF detector crops: 0.5 / 0.5 (FUTURE).
- LR on frozen features: C in {0.01, 0.1, 1}, class_weight='balanced', standardise features; tune C only inside the training folds.

**Pseudo-code: where the change lives (inference; not implemented).**

```python
# NEW helper (e.g. src/data/crops.py) — pure geometry, no labels written
def yolo_to_xyxy(line, W, H):            # YOLO label: "cls cx cy w h" normalised; read via _yolo_boxes() src/data/dataset.py L15
    _, cx, cy, w, h = line
    return (cx-w/2)*W, (cy-h/2)*H, (cx+w/2)*W, (cy+h/2)*H

def context_crop(im, box, ratio=1.5, jitter=None, rng=None):
    x0,y0,x1,y1 = box; cx,cy = (x0+x1)/2,(y0+y1)/2; s = max(x1-x0, y1-y0)
    if jitter:                             # training only
        ratio = rng.uniform(*jitter['ratio'])          # e.g. (1.2, 2.0)
        cx += rng.uniform(-.15,.15)*s; cy += rng.uniform(-.15,.15)*s
    side = max(ratio*s, 224)               # never upsample tiny crops
    return ImageOps.pad(im.crop((cx-side/2, cy-side/2, cx+side/2, cy+side/2)), ...)  # out-of-image -> pad colour (124,116,104) as tensor_image

# TRAINING — src/workbench/adapters.py efficient_train().Images.__getitem__ (L253)
with Image.open(inside(row['image_path'])) as im:
    roi = row.get('roi_xyxy')                 # human-confirmed ROI for EVERY photo incl. normals
    if params.get('input') == 'crop' and roi:
        if self.augment and row.get('oof_det_xyxy') and random.random() < params.get('det_mix', 0.5):
            roi = row['oof_det_xyxy']         # cross-fitted detector box (FUTURE)
        im = context_crop(im, roi, params.get('ratio', 1.5), params.get('jitter') if self.augment else None, random)
    elif params.get('input') == 'crop':
        raise ValueError('ROI missing: refuse rather than silently mixing whole/crop inputs')  # avoids label-correlated input type
    x = tensor_image(im, params if self.augment else None)

# FROZEN FEATURES — adapters.py dino_features() (L400-L432)
# cache key MUST include crop spec, else cached whole-image features are reused:
key = digest({..., 'preprocess': f'rgb-roi{roi_sha}-r{ratio}-letterbox224-imagenet-v1'})
# multi-view: feats = np.concatenate([f_whole, f_r15, f_r25], axis=1) -> StandardScaler -> LogisticRegression

# INFERENCE — adapters.py ModelPredictor.predict() (L712); classifier currently uses whole image at L769
roi, roi_conf = None, 0.0
if self.policy.crop_mode != 'off':           # new InferenceConfig fields (src/workbench/contracts.py L37):
    r = self.detector.predict(im, imgsz=cfg.imgsz, conf=cfg.roi_conf_min, verbose=False)[0]   # crop_mode, crop_ratio, roi_conf_min, roi_detector_id
    if len(r.boxes): b = r.boxes[int(r.boxes.conf.argmax())]; roi, roi_conf = b.xyxy[0].tolist(), float(b.conf)
if roi is not None:
    x = tensor_image(context_crop(im, roi, cfg.crop_ratio)).unsqueeze(0)
    input_used = 'roi_crop'
else:
    x = tensor_image(im).unsqueeze(0); input_used = 'whole_image_fallback'
    status_override = 'needs_review'        # never map "no ROI" to normal
values = self.class_scores(x.to(self.device))
record['input_used'] = input_used; record['roi'] = roi; record['roi_confidence'] = roi_conf
# also: if roi_conf < cfg.threshold -> status 'needs_review' (mirrors existing L787 rule)
```

**Validation on the platform (inference).**
- Paired design: the same `StratifiedGroupKFold` folds (src/data/dataset.py L411), the same seed, and the same patients in each fold for every arm (whole-224, whole-448/518, crop-1.5, crop-2.5, concat). Report balanced accuracy, macro-F1 and normal FPR per arm, plus **paired differences** with a patient-cluster bootstrap (resample patients, ≥2,000 reps) and Wilson CIs per arm.
- For a photo-level paired test, McNemar is optional, but it ignores within-patient correlation, so report it only alongside the cluster bootstrap.
- Two crop conditions: an oracle ROI (manual) and a pipeline ROI (detector). Report the fallback rate (photos with no ROI) per class. A class-dependent fallback rate is a red flag for shortcut learning.
- Grad-CAM on the whole-image model should check whether attention already falls on the insertion site. If it lands on dressings or background, that supports the crop arm (and the Bissoto-style shortcut concern).
- With 9 normal photos, normal FPR is barely estimable: 0/9 gives a 95% Wilson CI of 0-29.9% (computed: z²/(n+z²) = 3.84/12.84). Report "underpowered" rather than a winner.
- Nothing auto-trains or auto-deploys. ROI suggestions from YOLO are written only after human confirmation.

### Gaps
- No reliable evidence found for a minimum number of boxes for a reliable medical-photo detector. The thresholds above are inference.
- GPU time and memory figures are estimates from model FLOPs and parameter counts (torchvision, Ultralytics), not measured on the user's GPU. Run a timed one-fold pilot to confirm.
- No source verifies the best context ratio for skin photos. The 1.16× R-CNN figure is for natural images, and the 60 px few-shot figure is an unverified snippet.

### Source register (full bibliographic details; all accessed 2026-10-30)
1. Han SS, Moon IJ, Lim W, Suh IS, Lee SY, Na JI, Kim SH, Chang SE. Keratinocytic Skin Cancer Detection on the Face Using Region-Based Convolutional Neural Network. JAMA Dermatol. 2020;156(1):29-37. doi:10.1001/jamadermatol.2019.3807. https://pmc.ncbi.nlm.nih.gov/articles/PMC6902187 [B]
2. Lai T-Y, Chou Y-J, Liu C-Y, Chen C-W, Lin C-T, Wang W-C, Hsu Y, Hsieh M-L, Chang S-S. Novel two-stage deep learning framework for automated pressure injury classification. BMJ Health Care Inform. 2026;33(1):e101636. doi:10.1136/bmjhci-2025-101636. https://pmc.ncbi.nlm.nih.gov/articles/PMC13034204/ [C]
3. Zalluhoğlu C, Akdogan D, Karakaya D, Güzel MS, Ulgu MM, Ardali K, et al. Region-Based Semi-Two-Stream Convolutional Neural Networks for Pressure Ulcer Recognition. J Imaging Inform Med. 2024;(2):801-813. doi:10.1007/s10278-023-00960-4. Abstract via https://avesis.ankara.edu.tr/yayin/2eaac59a-6e10-4372-82b1-e318b0a20a45/region-based-semi-two-stream-convolutional-neural-networks-for-pressure-ulcer-recognition [C, abstract only]
4. Yap MH, et al. Analysis Towards Classification of Infection and Ischaemia of Diabetic Foot Ulcers. IEEE BHI 2021. arXiv:2104.03068. https://arxiv.org/abs/2104.03068 [D/C] (only first author confirmed)
5. Mahbod A, Schaefer G, Wang C, Dorffner G, Ecker R, Ellinger I. Transfer learning using a multi-scale and multi-network ensemble for skin lesion classification. Comput Methods Programs Biomed. 2020;193:105475. doi:10.1016/j.cmpb.2020.105475; and "Investigating and Exploiting Image Resolution for Transfer Learning-based Skin Lesion Classification", ICPR 2020, arXiv:2006.14715. https://arxiv.org/pdf/2006.14715 [C/D] (journal author list and volume not re-verified in this session)
6. Guan Q, Huang Y, Zhong Z, Zheng Z, Zheng L, Yang Y. Diagnose like a Radiologist: Attention Guided Convolutional Neural Network for Thorax Disease Classification. arXiv:1801.09927 (2018); Pattern Recognit Lett. 2020;131:38-45. https://ar5iv.labs.arxiv.org/html/1801.09927 [D/C]
7. Girshick R, Donahue J, Darrell T, Malik J. Rich feature hierarchies for accurate object detection and semantic segmentation. CVPR 2014. arXiv:1311.2524. https://arxiv.org/abs/1311.2524 [B]
8. Bissoto A, Fornaciali M, Valle E, Avila S. (De)Constructing Bias on Skin Lesion Datasets. CVPR Workshops (ISIC) 2019. arXiv:1904.08818. https://arxiv.org/abs/1904.08818v1 [C/D]; follow-up: Bissoto A, Valle E, Avila S. Debiasing Skin Lesion Datasets and Models? Not So Fast. arXiv:2004.11457. https://ar5iv.arxiv.org/html/2004.11457 [D]
9. Ilse M, Tomczak JM, Welling M. Attention-based Deep Multiple Instance Learning. ICML 2018. arXiv:1802.04712. https://ar5iv.labs.arxiv.org/html/1802.04712 [B]
10. Abdali A, Boguslawski B, Drumetz L, Gripon V. Object-Centric Cropping for Visual Few-Shot Classification. arXiv:2508.00218 (2025). https://arxiv.org/abs/2508.00218 [D]
11. Xu et al. Generating Features with Increased Crop-related Diversity for Few-Shot Object Detection. CVPR 2023. https://openaccess.thecvf.com/content/CVPR2023/papers/Xu_Generating_Features_With_Increased_Crop-Related_Diversity_for_Few-Shot_Object_Detection_CVPR_2023_paper.pdf [B] (number cited from a snippet only; full author list not verified)
12. ClinicalTrials.gov NCT07889895. AI Prediction of PIVC-Related Phlebitis. https://clinicaltrials.gov/study/NCT07889895 [A-registry] (record body not rendered by the fetch tool; details from search snippets)
13. Lee, Cho, Kim. Deep Learning for Predicting Phlebitis in Patients with Intravenous Catheters. Stud Health Technol Inform. 2024. doi:10.3233/SHTI240231. https://ebooks.iospress.nl/doi/10.3233/SHTI240231 [C] (snippet-level)
14. Swerdlow et al. Simultaneous Segmentation and Classification of Pressure Injury Image Data Using Mask-R-CNN. Comput Math Methods Med. 2023. doi:10.1155/2023/3858997. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9911250/ [C] (snippet-level)
15. MGH Patient Care Services. IV/CL Module 9: Nursing management of VAD complications (INS phlebitis scale table). https://www.mghpcs.org/EED/CL/Assets/documents/CL_Module9.pdf [E]
16. Ultralytics. Model training tips guide. https://docs.ultralytics.com/guides/model-training-tips/ ; YOLO11 model page. https://docs.ultralytics.com/models/yolo11/ [E vendor docs]
17. PyTorch torchvision. efficientnet_b0 model docs. https://docs.pytorch.org/vision/main/models/generated/torchvision.models.efficientnet_b0.html [E vendor docs]
18. Supporting only (snippet-level, not relied upon): CR-Conformer, Med Biol Eng Comput 2024, doi:10.1007/s11517-023-02904-0; Double-branch network (CSLI), Front Med 2023, doi:10.3389/fmed.2023.1114362; i-JOE smartphone EWS https://online-journals.org/index.php/i-joe/article/view/48345 ; ultrasound vein AI https://pmc.ncbi.nlm.nih.gov/articles/PMC9174762/ ; PIVC phlebitis ML https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11295139/ ; VIP reliability https://www.researchsquare.com/article/rs-882728/latest.pdf ; VeniBot https://arxiv.org/pdf/2105.12951 ; region-ensemble fine-grained https://arxiv.org/pdf/1902.03377 ; skin disease + patient info https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9060152/
