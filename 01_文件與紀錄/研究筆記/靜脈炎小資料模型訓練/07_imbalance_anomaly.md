# Class imbalance and anomaly-detection framing for tiny phlebitis photo datasets (07)

Scope: binary (phlebitis 47 vs normal 9) and 3-class staging (normal 9 / stage1 23 / stage2 24) on ~120 photos from 14 patients NOW; ~1,000 balanced photos FUTURE. Access date for all web sources: 2026-10-30 unless noted. Source grades: [A] official docs/standards, [B] systematic review / top-venue peer-reviewed, [C] other peer-reviewed, [D] preprint, [E] blog/example code/forum. Conclusion labels: (research evidence) / (industry practice) / (inference).

Platform facts used below (read from local code 2026-10-30, not web sources):
- EfficientNet loss: `02_主程式碼/src/workbench/adapters.py` ~L261-267 builds `CrossEntropyLoss(weight=counts.sum()/(classes*counts))` when `class_weight=='balanced'` (inverse frequency, same formula as sklearn 'balanced'). Train DataLoader uses `shuffle=True`, no sampler (~L259). Dataset class `Images` ~L245-257.
- DINOv2 + LR: `adapters.py` `dino_train` ~L434-500: frozen CLS features (`dino_features` ~L400) -> StandardScaler (train only) -> `LogisticRegression(C, solver, max_iter, class_weight)`. `workbench/contracts.py` ~L196-200, L283 restricts `class_weight` to None/'balanced'.
- Decision rule: `adapters.py` ~L773-776 binary `prediction = int(score >= cfg.threshold)`; staging decides by `argmax` (~L779-785) and the binary view is `1 - normal score`. `class_scores` (~L695) docstring: "Uncalibrated per-class model scores ... never a disease probability."
- Splits: `src/data/dataset.py` ~L379-411 and `src/data/holdout.py` ~L108-138 use `StratifiedGroupKFold(shuffle=True, random_state=seed)`. Evaluation guard against train/val subject overlap: `adapters.py` `evaluate` ~L819-836.
- Metrics/CI: `src/workbench/evaluation_views.py` `wilson()` L24, balanced accuracy L127, FPR with Wilson CI L150-154; `src/training/runner.py` L210 `normal_image_false_positive_rate`.

---

## Q1. Research evidence for each imbalance method in small, imbalanced (medical) image classification, with counter-evidence

### Takeaway
No method has strong evidence at n_minority=9 from a handful of patients; the large-sample evidence (Buda 2018, Cui 2019, Menon 2021) comes from CIFAR/ImageNet-scale benchmarks with hundreds to thousands of minority images, and the best calibration-focused evidence (van den Goorbergh 2022) says resampling/weighting do not improve discrimination and distort probabilities, while threshold moving achieves the same sensitivity/specificity trade-off without distortion. NOW, the defensible package is: keep or drop `class_weight='balanced'` (cheap, low-risk, little expected effect), prefer threshold moving / post-hoc logit adjustment chosen on patient-grouped out-of-fold scores, and avoid SMOTE and focal loss.

### Cited Findings

**Buda, Maki, Mazurowski — systematic CNN imbalance study [B]**
- Bibliographic: Buda M, Maki A, Mazurowski MA. "A systematic study of the class imbalance problem in convolutional neural networks." Neural Networks 106 (2018) 249-259 (journal volume/pages from training knowledge; the arXiv page lists DOI 10.1016/j.neunet.2018.07.011). arXiv:1710.05381. — [arXiv](https://arxiv.org/abs/1710.05381)
- Conclusions (abstract, verified): imbalance is detrimental to CNN performance; oversampling was the dominant remedy "in almost all analyzed scenarios" and should be applied to the level that fully eliminates imbalance; optimal undersampling ratio depends on imbalance extent; oversampling did not cause CNN overfitting; thresholding to compensate for prior class probabilities is recommended when overall number of correctly classified cases is of interest. — [arXiv 1710.05381](https://arxiv.org/abs/1710.05381)
- Caveat (inference): experiments were on MNIST, CIFAR-10 and ImageNet subsets with artificially induced imbalance, i.e., the minority class still had many distinct images; "oversampling does not overfit" cannot be transferred to 9 images from ~2-4 patients, where oversampling only repeats the same few images (and their patient-specific skin/lighting) more often per epoch.

**van den Goorbergh et al. 2022 — harm of imbalance corrections for risk models [B]**
- Bibliographic: van den Goorbergh R, van Smeden M, Timmerman D, Van Calster B. "The harm of class imbalance corrections for risk prediction models: illustration and simulation using logistic regression." JAMIA 2022;29(9):1525-1534. doi:10.1093/jamia/ocac093. — [JAMIA](https://academic.oup.com/jamia/article/29/9/1525/6605096)
- Studied random undersampling (RUS), random oversampling (ROS), SMOTE vs no correction, with standard and ridge logistic regression; also recalibration and threshold shifting. — [JAMIA](https://academic.oup.com/jamia/article/29/9/1525/6605096)
- All corrections overestimated risk: case-study calibration intercept ~0.06 uncorrected vs -1.32 to -1.50 corrected; RUS gave worst calibration slope (0.85 SLR, 0.93 ridge). — [JAMIA](https://academic.oup.com/jamia/article/29/9/1525/6605096)
- Discrimination not improved: AUROC 0.79-0.80 across methods; in simulations RUS often lowered AUROC, especially with lower event fraction, smaller training sets, more predictors. — [JAMIA](https://academic.oup.com/jamia/article/29/9/1525/6605096)
- At threshold 0.5 uncorrected sensitivity ~29-31%, specificity 96%; corrections moved to sensitivity 69-75%, specificity 74-78%; shifting the threshold gave similar results without distorting probabilities. Corrected models had reduced net benefit in decision curves. — [JAMIA](https://academic.oup.com/jamia/article/29/9/1525/6605096)
- Recommendation: outcome imbalance is not a problem in itself; adjust the threshold instead; if correcting, recalibrate. — [JAMIA](https://academic.oup.com/jamia/article/29/9/1525/6605096)
- Applicability (inference): directly relevant to the DINOv2-embedding + logistic regression pipeline (which *is* a logistic regression on 384-d features, many more predictors than events -> exactly the "small n, many predictors" regime where RUS hurt most). Study is tabular clinical data, not images.

**Cui et al. 2019 — class-balanced loss by effective number of samples [B]**
- Bibliographic: Cui Y, Jia M, Lin T-Y, Song Y, Belongie S. "Class-Balanced Loss Based on Effective Number of Samples." CVPR 2019 (venue from training knowledge; CVF PDF returned HTTP 403 when fetched). arXiv:1901.05555. — [arXiv](https://arxiv.org/abs/1901.05555)
- Effective number E_n = (1 - beta^n)/(1 - beta), beta in [0,1); class weight proportional to 1/E_n; evaluated on artificially long-tailed CIFAR, ImageNet, iNaturalist. — [arXiv](https://arxiv.org/abs/1901.05555)
- Inference (math, verifiable): beta=0 gives E_n=1 (no reweighting); beta->1 gives E_n->n (inverse frequency). With n in {9,23,24} and typical beta in {0.9,0.99,0.999}: beta=0.9 gives E = 6.1, 9.1, 9.2 (almost uniform weights); beta=0.99 gives E = 8.6, 20.6, 21.4 (close to inverse frequency); beta=0.999 is essentially inverse frequency. So at this dataset size the effective-number scheme collapses to either "no weighting" or "inverse frequency" and adds one more hyperparameter to tune on 9 normals — little to gain over sklearn/PyTorch 'balanced'.
- Gap: recommended beta values and imbalance factors tested could not be verified from the primary PDF (403).

**Lin et al. 2017 — focal loss [B]; Mukhoti et al. 2020 — focal loss and calibration [B]**
- Focal loss FL(p_t) = -alpha_t (1 - p_t)^gamma log(p_t) was introduced for dense one-stage object detection (RetinaNet, ICCV 2017, arXiv:1708.02002) where the imbalance is ~1:1000 easy background anchors (from training knowledge; primary source not re-opened in this session — treat details as unverified).
- Mukhoti J, Kulharia V, Sanyal A, Golodetz S, Torr PHS, Dokania PK. "Calibrating Deep Neural Networks using Focal Loss." NeurIPS 2020. arXiv:2002.09437. Abstract: focal loss, as opposed to standard cross-entropy, yields models that are already well calibrated, and combined with temperature scaling gives SOTA calibration while preserving accuracy. — [arXiv](https://arxiv.org/abs/2002.09437)
- Note on requested counter-evidence: the expected claim "focal loss harms calibration" is **contradicted** by Mukhoti 2020 for balanced classification (focal loss reduces over-confidence). However, focal loss with an alpha class-weight term combines reweighting with confidence shrinkage; no reliable evidence found in this session for focal loss improving balanced accuracy over weighted CE in small medical image classification.
- Inference: with a frozen backbone and a linear head trained on ~45 images per fold, almost every training example becomes "easy" quickly; focal loss then down-weights nearly everything and mainly acts like a learning-rate/regularisation change. Not worth a new hyperparameter (gamma) NOW.

**Menon et al. 2021 — logit adjustment [B]**
- Bibliographic: Menon AK, Jayasumana S, Rawat AS, Jain H, Veit A, Kumar S. "Long-tail learning via logit adjustment." ICLR 2021 (arXiv comment: "Published as a conference paper in ICLR 2021"). arXiv:2007.07314. — [arXiv](https://arxiv.org/abs/2007.07314v2)
- Post-hoc rule (Eq. 9): predict argmax_y f_y(x) - tau * log(pi_y), pi_y = training class prior; logit-adjusted loss (Eq. 10): l(y,f(x)) = log[1 + sum_{y'!=y} (pi_{y'}/pi_y)^tau * exp(f_{y'}(x) - f_y(x))]. — [arXiv HTML](https://arxiv.org/html/2007.07314v2)
- Both are Fisher-consistent for the balanced error; applying post-hoc adjustment on top of the adjusted loss is "statistically incoherent"; tau=1 used for the loss; post-hoc tau may be tuned on holdout. — [arXiv HTML](https://arxiv.org/html/2007.07314v2)
- Inverse-prior weighting is also consistent but "has minimal effect in separable settings" and does not enforce a margin. — [arXiv HTML](https://arxiv.org/html/2007.07314v2)
- CIFAR-10-LT balanced error (ResNet-32): ERM 27.16; post-hoc LA tau=1 22.60; post-hoc tau* 19.08; LA loss 22.33. CIFAR-100-LT: ERM 61.64; LA loss 56.11. — [arXiv HTML](https://arxiv.org/html/2007.07314v2)
- Relevance (inference): "minimal effect in separable settings" is exactly the frozen-feature small-n regime (384-d DINOv2 / 1280-d EfficientNet features with ~45 training images are almost surely linearly separable), so class weighting is expected to do little; post-hoc logit adjustment = moving the decision threshold on the logit scale for binary, and is the principled multi-class generalisation of threshold moving for the 3-class argmax rule.

**Oversampling / WeightedRandomSampler / undersampling**
- Buda 2018 (above) supports oversampling for CNNs at benchmark scale [B]; van den Goorbergh 2022 shows ROS/RUS/SMOTE distort calibration without AUROC gain for logistic regression [B].
- Inference: in PyTorch, `WeightedRandomSampler` with replacement and inverse-frequency weights is, in expectation, equivalent to inverse-frequency loss weighting but with higher gradient variance; with 9 normal photos each epoch would repeat each normal ~5x. Undersampling to 9:9 discards 38 of 47 positives (~80% of data) — not justifiable NOW.

**SMOTE in embedding space**
- Blagus R, Lusa L. "SMOTE for high-dimensional class-imbalanced data." BMC Bioinformatics 2013;14:106 (22 Mar 2013). doi:10.1186/1471-2105-14-106; PMC3648438 [C]. Findings: in high-dimensional data SMOTE hardly reduces most classifiers' bias toward the majority class, and random undersampling generally did better; SMOTE helps kNN only after variable selection, otherwise biases kNN toward the minority; DQDA gets worse (biased class variance); SVM and CART little effect; SMOTE preserves class means but shrinks variance and makes test samples closer to synthetic than real minority samples; it introduces positive correlation between synthetic and source samples. — [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC3648438/)
- van den Goorbergh 2022: SMOTE gave calibration slopes < 1 and no AUROC gain [B]. — [JAMIA](https://academic.oup.com/jamia/article/29/9/1525/6605096)
- imbalanced-learn docs (v0.14.2, "Common pitfalls") [A]: resampling the whole dataset before splitting leaks information and balances the test set artificially; the fix is an imblearn `Pipeline` cross-validated as a whole. Example (adult census, balanced accuracy): no resampling CV 0.609 / held-out 0.628; leaky resampling CV 0.724 vs held-out 0.698 (optimistic); resampling inside Pipeline CV 0.732 vs held-out 0.727. — [imbalanced-learn](https://imbalanced-learn.org/stable/common_pitfalls.html)
- Inference: Blagus & Lusa's "SMOTE makes test points look closer to synthetic minority points" is directly relevant to kNN/Mahalanobis anomaly scores — never SMOTE before fitting a distance-based score.
- Inference: SMOTE with k_neighbors=5 needs >= 6 minority points per training fold; with 9 normals in 3-fold group CV a training fold may hold only ~6 normals from 2-3 patients, so synthetic points are interpolations between photos of the *same* patient's arm — they add no new patient variability and may create embedding points that correspond to no real photo. Synthetic points must never be reported as real labelled data (project principle).

**Johnson & Khoshgoftaar 2019 survey [B/C]**
- Johnson JM, Khoshgoftaar TM. "Survey on deep learning with class imbalance." Journal of Big Data 2019;6:27. doi:10.1186/s40537-019-0192-5 — Springer fetch redirected to login; content NOT verified this session. — [DOI](https://doi.org/10.1186/s40537-019-0192-5)

**Balanced-accuracy-aware model selection**
- Inference/industry practice: selecting hyperparameters by balanced accuracy (already implemented, `evaluation_views.py` L127) is appropriate, but with 9 normals each misclassified normal changes specificity by 11 percentage points and balanced accuracy by ~5.6 points; comparing configurations on such a metric is mostly noise (see Q2 CIs). Prefer threshold-free ranking metrics (AUROC on OOF scores, log-loss) for model selection and leave the operating point to a separate threshold step.

### Inferences
- NOW ranking by expected value / risk: (1) threshold moving or post-hoc logit adjustment on OOF scores; (2) `class_weight='balanced'` (essentially free, consistent, little effect when separable; leave as an option, report both); (3) WeightedRandomSampler (equivalent in expectation, more variance — skip); (4) focal loss, effective-number weights (extra hyperparameter, no data to tune — skip); (5) SMOTE, undersampling (skip).
- Any of these only changes the operating point; none adds information about normal-arm appearance. The binding constraint is patients with normal photos, not the loss.

### Gaps
- No reliable evidence found for any imbalance method evaluated on a dataset with <20 minority images from <5 patients with patient-level splits.
- Primary text of Cui 2019 (CVF 403) and Johnson & Khoshgoftaar 2019 (Springer login redirect) could not be opened this session; their numbers are not cited.
- Leakage/external validation of cited studies: Buda 2018 and Menon 2021 use standard benchmark splits (no patient structure); van den Goorbergh 2022 is a simulation plus one clinical case study with data split by study design (details not extracted); BMAD uses curated public datasets (patient-level split status not extracted). None is externally validated on skin photographs.
- Lin 2017 focal loss primary source not re-opened this session.

---

## Q2. What can realistically be learned from 9 normal photos from few patients? Effective sample size and CI width

### Takeaway
With 9 normal photos clustered in a few patients, the effective sample size for the normal false-positive rate is closer to the number of normal patients than to 9; even a perfect 0/9 FPR has a Wilson 95% upper bound of ~30%, so the platform cannot currently distinguish a model with 5% FPR from one with 30% FPR. Collecting more normal photos from more patients (contralateral arm, pre-insertion and post-removal photos) is the dominant fix.

### Cited Findings
- Wilson 95% CI (computed locally with the standard Wilson formula, z=1.96; same method as `evaluation_views.py` L24): 0/9 -> 0.000-0.299; 1/9 -> 0.020-0.435; 2/9 -> 0.063-0.547; 0/3 (if only 3 normal patients counted as units) -> 0.000-0.561; 0/30 -> 0-0.114; 3/30 -> 0.035-0.256; 0/100 -> 0-0.037; 5/100 -> 0.022-0.112; 0/333 -> 0-0.011; 17/333 -> 0.032-0.080. (inference/computation; no web source needed)
- van den Goorbergh 2022 found harm of RUS was worse with smaller training sets and more predictors (simulation) — supports not discarding data. — [JAMIA](https://academic.oup.com/jamia/article/29/9/1525/6605096)
- Fernando et al. survey identifies data scarcity in medicine as a major cause of poor generalisation and notes patient-specific factors create variability among normal samples. — [ar5iv 2012.02364](https://ar5iv.labs.arxiv.org/html/2012.02364)

### Inferences
- Effective sample size: for clustered data, n_eff = n / (1 + (m - 1) * ICC), m = photos per patient. With m~3 and a plausible high ICC for "same arm, same skin, same phone" (e.g., 0.5-0.9; no measured value), n_eff for 9 normal photos is ~4.5-5.6 down toward the number of normal patients. (inference; ICC values are illustrative, not measured)
- In 3-fold StratifiedGroupKFold, each validation fold holds ~3 normal photos (likely 1 patient); per-fold FPR is 0/3, 1/3, 2/3 or 3/3 — fold-level metrics are not interpretable; only pooled OOF metrics are.
- An optional held-out ~20% of patients (~14-18 photos) may contain 0-2 normal photos -> held-out normal FPR is uninformative; report it as "n too small" rather than a number.
- Dominant fix (inference, consistent with the project's no-fabrication principle): photograph the contralateral (non-cannulated) arm/hand dorsum of each enrolled patient at each visit, pre-insertion site photos, and post-removal healed-site photos, with the same phone/lighting protocol. This multiplies normal patients (every positive patient also contributes a normal arm) and decorrelates "normal" from "specific patient", which matters because with 14 patients a model can learn patient identity cues. Caveats: contralateral arm is not the same anatomical site and lacks a cannula/dressing — the model could learn "dressing present = phlebitis". Mitigation: include pre-insertion photos with tape/dressing context, post-removal photos, and normal cannulated sites (VIP score 0) as the true normal class; label "contralateral" as a separate source tag so it can be excluded in a sensitivity analysis.
- Targets (inference from Wilson math): to bound normal FPR upper CI at ~11% you need ~30 normal photos with 0 errors; for ~4% about 100; realistically aim for >=30 normal *patients*, not photos.

### Gaps
- No published ICC for repeated photos of the same patient's skin found; n_eff values above are illustrative.
- No reliable evidence found on contralateral-arm photos as negative controls for phlebitis image models specifically.

---

## Q3. Threshold moving: nested selection, target normal FPR, instability with tiny folds

### Takeaway
Threshold moving is the best-supported, calibration-preserving way to trade sensitivity for specificity (research evidence: van den Goorbergh 2022; Buda 2018; Menon 2021 post-hoc logit adjustment), but the threshold must be chosen on out-of-fold scores that were not used to evaluate the same threshold; with 9 normals, a threshold set for "target normal FPR <= 10%" is determined by the single highest-scoring normal photo and is essentially unstable.

### Cited Findings
- Threshold shifting achieved the same sensitivity/specificity balance as resampling without distorting probabilities. — [JAMIA 2022](https://academic.oup.com/jamia/article/29/9/1525/6605096)
- Buda 2018 recommends thresholding to compensate for prior class probabilities. — [arXiv](https://arxiv.org/abs/1710.05381)
- Post-hoc logit adjustment (subtract tau*log pi_y) is Fisher-consistent for balanced error; tau tunable on holdout. — [arXiv HTML](https://arxiv.org/html/2007.07314v2)
- scikit-learn `TunedThresholdClassifierCV` [A]: tunes the decision threshold post-training using internal CV to maximise a metric; default scoring is balanced accuracy; default cv is 5-fold stratified; `cv="prefit"` tunes on the data passed to fit; the docs warn never to use the same data to train the classifier and tune the threshold; `predict_proba` is unchanged (ROC/PR identical), only labels change; `FixedThresholdClassifier` sets a manual threshold. The page does not mention group-aware CV. — [scikit-learn docs](https://scikit-learn.org/stable/modules/classification_threshold.html) (version introduced not stated on page; 1.5 per training knowledge, unverified)
- Inference: because the docs do not mention groups and default cv is plain stratified, passing `cv=` an explicit iterable of patient-grouped splits (from `StratifiedGroupKFold(...).split(X, y, groups)`) is required to avoid patient leakage inside threshold tuning.

### Inferences
- Nested protocol (pseudo-code):
  ```
  outer = StratifiedGroupKFold(3, groups=patient)   # existing splitter, dataset.py L411
  for train_o, test_o in outer:
      inner = StratifiedGroupKFold(min(3, n_normal_patients_in_train_o), groups=patient)
      oof = cross_val_predict(model, X[train_o], y[train_o], groups=..., cv=inner, method='predict_proba')
      t = choose_threshold(oof, y[train_o], rule)   # e.g. max balanced acc, or FPR target
      fit model on train_o; score test_o; apply t -> record metrics
  report pooled outer metrics; final deployable threshold = choose_threshold on full OOF
  ```
  With 14 patients and maybe 2-4 normal patients, the inner loop will often have only 1-2 normal patients per inner fold -> the inner OOF normal scores come from 1-2 people. (inference)
- Threshold rules (inference): (a) Youden / max balanced accuracy on OOF; (b) target FPR: t = quantile_{1-target}(normal OOF scores) — with 9 normals, the 90th percentile equals the 1st/2nd highest normal score, so one photo sets the threshold; (c) logit-prior shift t = sigmoid(log(pi_pos/pi_neg)) on uncalibrated LR output (no tuning, = post-hoc logit adjustment with tau=1, i.e., moves 0.5 to ~0.84 for 47:9 priors — compute: pi_pos=47/56=0.839). Option (c) has zero tuned parameters and is the most stable NOW.
- Instability check: bootstrap OOF predictions by patient (resample patients with replacement, 1,000-2,000 reps, seconds on CPU) and report the distribution of the chosen threshold and the resulting FPR; if the threshold's 95% interval spans most of [0,1], report "threshold not identifiable at current n".
- Report the threshold as a research-tool setting with human confirmation (project principle), never auto-applied.

### Gaps
- No reliable evidence found quantifying optimism of non-nested threshold selection at n<60 in image classification.

---

## Q4. Anomaly-detection framing: one-class from normals, or from positives only

### Takeaway
Research evidence (BMAD 2024; Fernando 2021 survey) shows one-class/unsupervised medical anomaly detection is trained on thousands of normal images and still varies from AUROC ~62% (liver CT) to ~98.6% (OCT), and supervised methods generally outperform unsupervised ones when labelled anomalies exist. With 9 normal photos from few patients, a normal-only model would mostly learn those patients' skin tone, lighting and background; NOW it is not sensible as the main model. A kNN/Mahalanobis distance-to-normal score on DINOv2 embeddings is cheap and useful only as an *auxiliary* out-of-distribution / quality signal. "Learning only positives" is not meaningful for discriminating normal vs phlebitis.

### Cited Findings
- BMAD: Bao J, Sun H, Deng H, He Y, Zhang Z, Li X. "BMAD: Benchmarks for Medical Anomaly Detection." CVPR Workshops (VAND) 2024, pp. 4042-4053; arXiv:2306.11876 (v3, 28 Apr 2024). — [CVF](https://openaccess.thecvf.com/content/CVPR2024W/VAND/html/Bao_BMAD_Benchmarks_for_Medical_Anomaly_Detection_CVPRW_2024_paper.html), [arXiv](https://arxiv.org/abs/2306.11876v3) [B/C — workshop]
- BMAD training set sizes (normal training images): BraTS2021 7,500; BTCV+LiTS 1,542; RESC 4,297; OCT2017 26,315; RSNA 8,000; Camelyon16 5,088. — [arXiv HTML](https://arxiv.org/html/2306.11876v3)
- Best image-level AUROC: BraTS PatchCore 91.65; liver CFA 62.00; RESC PatchCore 91.55; OCT2017 PatchCore 98.57; RSNA chest X-ray CS-Flow 83.20; Camelyon16 MKD 77.54. No single algorithm consistently wins; feature-based methods generally beat reconstruction-based; PatchCore, RD4AD, CS-Flow top three overall. — [arXiv HTML](https://arxiv.org/html/2306.11876v3)
- BMAD limitations: data almost all from advanced countries; hyperparameters not tuned per dataset; no few-shot results reported. — [arXiv HTML](https://arxiv.org/html/2306.11876v3)
- Fernando T, Gammulle H, Denman S, Sridharan S, Fookes C. "Deep Learning for Medical Anomaly Detection - A Survey." ACM Computing Surveys 54(7), 2021/2022, article 141. doi:10.1145/3464423; arXiv:2012.02364. Statements: medical AD is often posed as supervised; supervised methods have "demonstrated superior performance to unsupervised methods"; models must represent "the diverse nature of the normal data distribution"; changing capture conditions make normals look abnormal, "yielding higher false positive rates"; data scarcity is a major cause of poor generalisation; mentions a VAE framework for skin-image anomalies. — [ar5iv](https://ar5iv.labs.arxiv.org/html/2012.02364), [search listing](https://arxiv.org/abs/2012.02364v2) [B]
- PatchCore: Roth K, Pemula L, Zepeda J, Schölkopf B, Brox T, Gehler P. "Towards Total Recall in Industrial Anomaly Detection." CVPR 2022; arXiv:2106.08265 [B]. Abstract: image-level AUROC "up to 99.6%" on MVTec AD and "competitive results in the few samples regime" (industrial, controlled capture; few-shot table numbers not verified). — [arXiv](https://arxiv.org/abs/2106.08265)
- Counter-evidence contrast (inference): PatchCore reaches ~99.6% on controlled industrial objects but only 62-92% AUROC on most BMAD medical sets with thousands of normals — medical normal variability is the hard part, which IV-site photos from phones/LINE amplify.

### Inferences
- When one-class from normals is sensible (inference): normals are plentiful and homogeneous (standardised capture), abnormals are rare/heterogeneous/unlabelled, and the goal is "flag anything unusual for human review". Here the opposite holds NOW: positives (47) outnumber normals (9), normals are heterogeneous (skin tone, hair, lighting, LINE-submitted phone photos, dressings), and phlebitis signs (erythema, swelling, streak) are subtle colour/texture shifts that also arise from lighting — the failure mode Fernando et al. describe (higher FPR from capture variation).
- How many normals (inference): BMAD datasets use 1,542-26,315 normal training images; no reliable evidence found on medical one-class performance with <=10 normals. Industrial few-shot AD (MVTec) is not transferable: MVTec objects are pose/lighting-controlled.
- "Learn only positives": a one-class model of phlebitis would score normal arms by distance to phlebitis photos; because both share the same arm/background context, distance is dominated by nuisance factors; this answers "is this like our phlebitis photos" not "is this phlebitis vs normal". Not meaningful as a classifier; possibly useful as an out-of-domain detector ("is this an arm/IV-site photo at all") — inference.
- Cheap auxiliary design (inference): kNN distance (k=1-3, cosine) or Ledoit-Wolf-shrunk Mahalanobis distance on L2-normalised DINOv2 CLS embeddings, fitted on *all* training photos of the target domain (both classes) to flag out-of-distribution submissions (non-arm photos, extreme lighting) — this uses 56+ images, not 9. A normal-only Mahalanobis needs covariance in 384-d from 9 points: rank <= 8, so shrinkage is mandatory and the score degenerates to a scaled Euclidean distance to the normal mean.

### Gaps
- No reliable evidence found for one-class/unsupervised anomaly detection on skin-surface photographs of IV sites or phlebitis.
- PatchCore/PaDiM/Deep SVDD few-shot numbers not verified this session.

---

## Q5. Implementation on the current stack (code, parameters, compute)

### Takeaway
All candidate treatments are a few lines in existing functions and cost seconds to minutes on a consumer GPU; the work is in evaluation (nested OOF, patient bootstrap), not training.

### Cited Findings
- Logit-adjusted loss and post-hoc formulas — [Menon 2021](https://arxiv.org/html/2007.07314v2)
- Effective-number formula — [Cui 2019](https://arxiv.org/abs/1901.05555)

### Inferences (pseudo-code, parameter ranges, locations)
- **Inverse-frequency CE (exists)**: `adapters.py` ~L261-267. Keep; range {None, 'balanced'}.
- **Effective-number weights** (optional, low priority): `w_c = (1-beta)/(1-beta**n_c); w = w * C / w.sum()`; beta in {0.9, 0.99, 0.999}. Replace `weights` at ~L262. Contract change needed in `contracts.py` L283.
- **Focal loss** (not recommended NOW):
  ```python
  def focal(logits, y, gamma=2.0, alpha=None):
      logp = logits.log_softmax(1); ce = F.nll_loss(logp, y, weight=alpha, reduction='none')
      pt = logp.gather(1, y[:,None]).exp().squeeze(1)
      return ((1-pt)**gamma * ce).mean()
  ```
  gamma in {1, 2, 3}; location: replace `loss_fn` at ~L267.
- **WeightedRandomSampler** (not recommended NOW): `w_i = 1/counts[y_i]; DataLoader(..., sampler=WeightedRandomSampler(w, num_samples=len(w), replacement=True))` replacing `shuffle=True` at ~L259. Do not combine with class weights (double correction).
- **Logit-adjusted loss** (FUTURE option if any imbalance remains): `loss = CE(logits + tau*log(prior), y)`, tau=1, prior from train-fold counts; predict with plain argmax. Do not also post-hoc adjust.
- **Post-hoc logit adjustment / threshold** (recommended NOW): binary: `t = sigmoid(tau*log(pi_pos/pi_neg))` applied to positive score (default tau=1 -> 0.84 for 47:9), or tuned via nested OOF; 3-class: `argmax(log s_c - tau*log pi_c)`. Location: decision code ~L773-785 (binary uses `cfg.threshold`; stage path would need a prior vector in the decision rule record).
- **sklearn LR**: `LogisticRegression(class_weight='balanced', C in {0.01, 0.1, 1})` exists at ~L461. Stronger L2 (smaller C) matters more than weighting at n~45 in 384-d.
- **SMOTE inside fold** (not recommended; if ever tested for an ablation): `imblearn.pipeline.Pipeline([('scale', StandardScaler()), ('smote', SMOTE(k_neighbors=min(5, n_min_train-1))), ('lr', LogisticRegression())])` passed to the CV loop so SMOTE sees only train-fold rows. Requires adding imbalanced-learn dependency.
- **OOF thresholding grouped by patient**: `cross_val_predict(pipe, X, y, groups=g, cv=StratifiedGroupKFold(3, shuffle=True, random_state=seed), method='predict_proba')` on cached DINOv2 features (`dino_features` caches by backbone hash ~L400). For EfficientNet, reuse fold models' val predictions already written by `evaluate` (~L819+ records `score`, `class_scores`, `group`).
- **kNN / Mahalanobis OOD score**: `Z = normalize(features); d_knn = 1 - max cos(Z_test, Z_train)`; `LedoitWolf().fit(Z_train)`; `d_m = mahalanobis`. Location: new helper beside `dino_features`; show as a "photo unlike training data" flag, not a disease score.
- **Compute** (inference with basis): DINOv2-small forward on ~120 images at 224 px is a few seconds on a consumer GPU (~22M params); LR fit, OOF CV, 2,000 patient bootstraps on a 120x384 matrix are CPU seconds. EfficientNet-B0 (~5M params) frozen-backbone training for 3 folds x ~30 epochs x ~40 images is minutes. No method above changes order of magnitude; GPU cost is not a deciding factor.

### Gaps
- imbalanced-learn is not currently a project dependency (not checked against requirements file in this note); adding it only for a SMOTE ablation is not justified NOW.

---

## Q6. Interaction with ordinal staging (CORAL/CORN) and with the "scores are not probabilities" UI note

### Takeaway
Class weighting and resampling shift the score scale (research evidence for logistic regression: calibration intercept from ~0.06 to about -1.3 to -1.5), which reinforces the existing UI wording that scores are not probabilities; for ordinal models, imbalance treatment should act on the cumulative-threshold tasks (normal vs >=stage1 is the 9-vs-47 task), and post-hoc threshold adjustment per ordinal cut point is the analogue of logit adjustment.

### Cited Findings
- Imbalance corrections produce overestimated, miscalibrated probabilities; recalibration largely fixes the intercept. — [JAMIA 2022](https://academic.oup.com/jamia/article/29/9/1525/6605096)
- Focal loss tends to reduce over-confidence relative to CE (balanced settings). — [arXiv 2002.09437](https://arxiv.org/abs/2002.09437)
- Post-hoc logit adjustment tau may be tuned with calibration measures (ECE or proper scoring rule). — [arXiv HTML](https://arxiv.org/html/2007.07314v2)

### Inferences
- CORAL/CORN (covered in other notes) decompose 3 classes into binary tasks P(y>normal) and P(y>stage1 | ...). The first task has the 9:47 imbalance; the second is 23:24 (balanced). So per-task weighting (only on task 1) or per-cut-point threshold adjustment is appropriate; uniform class weights over the 3 classes would also distort the balanced task-2 boundary. (inference; CORAL/CORN primary sources not opened in this note.)
- UI: keep "not a disease probability" text; additionally record in `decision_rule` whether class weighting/oversampling/logit adjustment was used, because the same score number means different things across these settings. Any future calibration (temperature/Platt) must be fitted on patient-grouped OOF scores and cannot be trusted with 9 normals.

### Gaps
- No reliable evidence found on class weighting inside CORAL/CORN for small medical datasets.

---

## Q7. NOW vs FUTURE recommendations; which treatments to remove after balancing, and how to verify

### Takeaway
NOW: invest in collecting normal photos from more patients; use at most `class_weight='balanced'` plus a transparent post-hoc threshold/prior shift chosen on patient-grouped OOF scores; report normal FPR with Wilson CI and say it is not estimable. FUTURE (~1,000 photos, balanced 3 classes): remove class weights, samplers, focal loss and prior shifts (with balanced priors log pi_c is constant, so logit adjustment and inverse-frequency weights become no-ops by construction), keep threshold selection only if the deployment prevalence or a target FPR differs from 1:1:1.

### Cited Findings
- Imbalance is "not a problem in itself"; threshold adjustment is the simpler option. — [JAMIA 2022](https://academic.oup.com/jamia/article/29/9/1525/6605096)
- Logit adjustment uses log class priors pi_y; equal priors give identical adjustment for all classes. — [arXiv HTML](https://arxiv.org/html/2007.07314v2)
- Effective-number weights depend only on n_c; equal n_c gives equal weights. — [arXiv](https://arxiv.org/abs/1901.05555)

### NOW (research prototype, ~120 photos / 14 patients)
| Method | Evidence strength | Expected benefit NOW | Minimum data (inference) | Risk | Recommendation |
|---|---|---|---|---|---|
| Collect more normals (contralateral, pre-insertion, healed) | inference (+ Fernando survey on data scarcity) | Largest; only way to narrow FPR CI | >=30 normal patients | site/dressing shortcut | Do first |
| Threshold / post-hoc prior shift on OOF | research evidence (JAMIA 2022, Menon 2021, Buda 2018) | Moderate; sets operating point honestly | any; stable only with >=30 normals | unstable, optimistic if not nested | Do, nested, human-confirmed |
| class_weight='balanced' (CE / LR) | research evidence (consistent; minimal in separable) | Small | any | calibration shift | Optional; report with/without |
| Effective-number weights | research evidence at large scale only | ~none (collapses to above) | hundreds per class | extra hyperparameter | Skip |
| Focal loss | research evidence for detection; calibration evidence mixed | ~none for frozen linear head | — | extra hyperparameter | Skip |
| WeightedRandomSampler | research evidence (Buda) at benchmark scale | ~ same as weighting, more variance | — | overfit to 9 images | Skip |
| SMOTE (embeddings) | counter-evidence (JAMIA 2022; Blagus & Lusa 2013) | none expected | — | synthetic-as-real risk, leakage | Skip |
| Undersampling | counter-evidence (JAMIA 2022 RUS worst) | negative | — | discards 80% of data | Skip |
| One-class from normals | counter-evidence (BMAD scale; Fernando) | negative as classifier | thousands of normals | learns patient/lighting | Skip as classifier; kNN OOD flag optional |

### FUTURE (~1,000 photos, balanced 3 classes, slowly growing patients)
- Remove: class weights, WeightedRandomSampler, focal-loss alpha, logit adjustment priors (no-ops under equal priors — inference from formulas). Keep: patient-grouped CV, balanced accuracy + macro-F1 + normal FPR with CIs, threshold selection only when the intended use specifies a target normal FPR or a prevalence different from training.
- Balanced *photo* counts can still hide patient imbalance (e.g., many normal photos from few patients). Check per-class patient counts; if normals come from far fewer patients, the effective imbalance persists (inference).
- One-class / anomaly detection could be revisited as an auxiliary OOD flag once there are hundreds of normal photos from >=50-100 patients (inference; BMAD-scale datasets use >=1,500 normals).
- Calibration (temperature scaling on OOF) becomes feasible with >=100 normals; then the UI could show calibrated scores only after documented validation — still not a clinical probability claim.

### How to verify removal is safe (inference, platform procedure)
1. Same patient-grouped folds and seed (`dataset.py` L411), run A = current treatment, B = treatment removed.
2. Compare pooled OOF balanced accuracy, normal FPR, macro-F1 with patient-level bootstrap CIs of the paired difference (B - A); accept removal if the 95% CI of the difference includes 0 and the lower bound is above a pre-declared margin (e.g., -3 points balanced accuracy).
3. Check calibration-in-the-large on OOF (mean score vs observed rate per class) — removing weights under balance should not shift it.
4. Record both runs in the registry; the change requires human confirmation (no auto-deploy).

### Gaps
- No reliable evidence found on non-inferiority margins for removing imbalance treatment in medical image classifiers; margin above is a suggestion.
