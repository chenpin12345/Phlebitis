# Semi-supervised learning, active learning and human-in-the-loop design for a small phlebitis photo dataset

Scope: a research prototype (not clinical diagnosis) that classifies photos of IV insertion sites (binary phlebitis/normal, and staging normal/stage 1/stage 2), with YOLO box detection.
Data NOW: about 120 photos from 14 patients, binary 47 positive vs 9 normal, about 24 photos with boxes, one annotator. FUTURE: about 1,000 photos, three balanced classes.
Inviolable rules: no auto-training or auto-deploy; model suggestions must be human-confirmed before they are written; no fabricated labels or performance numbers; all compute stays local.
All sources were accessed on 2026-10-30 unless stated otherwise.

Source grades: [A] official docs, regulators or standards; [B] systematic reviews, meta-analyses or top-venue peer-reviewed papers; [C] other peer-reviewed work; [D] preprints; [E] blogs, example code or forums (supporting only).
Conclusion labels: **(research evidence)**, **(industry practice)**, **(inference)**.
"Opened" means I fetched the page itself. "Search-only" means I saw only search-result summaries, so the claim needs re-checking against the primary paper before anyone relies on it.

---

## Q1. Does SSL help medical imaging at tiny labeled sizes, and when does it hurt?

### Takeaway
The evidence that SSL works comes from settings with hundreds to thousands of labeled images and tens of thousands to hundreds of thousands of in-distribution unlabeled images.
I found no reliable evidence that SSL helps at 14 patients and about 120 labels. The canonical realistic-evaluation paper shows three things:
- out-of-class unlabeled data can make SSL worse than using no unlabeled data;
- transfer learning can beat SSL;
- validation sets of about 100 examples cannot tell methods apart.

All three conditions hold here (LINE photos of mixed content, a strong DINOv2 transfer baseline, a tiny patient-grouped test set). **SSL is not worth doing NOW.** In the FUTURE it is a guarded, manually launched experiment at most.

### Cited Findings

**Method papers and headline numbers (benchmarks, not medical)**
- **Pseudo-Label (Lee 2013).** Trains on labeled and unlabeled data together, using the class with the highest predicted probability as a "true" label for unlabeled inputs. ICML 2013 Workshop on Challenges in Representation Learning. — Search-only, [C/workshop]: [search summary of Lee 2013 PDF](https://storage.googleapis.com/kaggle-forum-message-attachments/8924/pseudo_label_final.pdf). **(research evidence, weak)**
- **Mean Teacher (Tarvainen & Valpola, NIPS 2017).** Averages model weights rather than label predictions.
  - SVHN: 4.35% error with 250 labels.
  - CIFAR-10 with 4,000 labels: 10.55% → 6.28% error with ResNets.
  - ImageNet with 10% labels: 35.24% → 9.11% error, as stated in the abstract (I believe this is top-5 error; check the paper).
  - [B] [arXiv:1703.01780](https://arxiv.org/abs/1703.01780). **(research evidence)**
- **FixMatch (Sohn et al., NeurIPS 2020).** CIFAR-10: 94.93% accuracy with 250 labels and 88.61% with 40 labels (4 per class). — [B] [arXiv:2001.07685](https://arxiv.org/abs/2001.07685). **(research evidence)**
- **FixMatch official code** (google-research/fixmatch). An example run folder name shows threshold 0.95, batch 64, lr 0.03, wd 0.0005, wu (λ_u) 1.0, uratio (μ) 7. The README does not call these the defaults. — [E] [github.com/google-research/fixmatch](https://github.com/google-research/fixmatch). **(industry practice)**
- **FlexMatch (Zhang et al., NeurIPS 2021).** Curriculum Pseudo Labeling uses per-class, per-step thresholds with no extra parameters or compute.
  - With 4 labels per class, it cuts error relative to FixMatch by about 13.96% on CIFAR-100 and 18.96% on STL-10.
  - It matches or beats FixMatch with about 1/5 of the training time.
  - [B] [arXiv:2110.08263](https://arxiv.org/abs/2110.08263). **(research evidence)**

**Realistic-evaluation caveats**
- **Oliver et al. (NeurIPS 2018)** — [B] [arXiv:1804.09170](https://arxiv.org/abs/1804.09170) and [full text, ar5iv](https://ar5iv.labs.arxiv.org/html/1804.09170). **(research evidence)**
  - *Transfer beats SSL.* An ImageNet-pretrained WRN-28-2 fine-tuned on 4,000 CIFAR-10 labels reached 12.09% error (12.91% with overlapping ImageNet classes removed). The best SSL method on the same network (VAT + EntMin) reached 13.13%; fully supervised reached 20.26%.
  - *Class mismatch hurts.* With 6 CIFAR-10 animal classes (400 labels each) and unlabeled data from 4 classes with varying overlap, out-of-class unlabeled data can "hurt performance compared to not using any unlabeled data at all".
  - *Small validation sets.* By Hoeffding's inequality, being 95% confident that a validation estimate is within 1% needs "nearly 20,000 validation examples". On SVHN with a validation set of 100, "differentiating between the performance of the models is not feasible".
  - *Recommendations.* Report tuned supervised and transfer baselines. Vary class mismatch and the amounts of labeled and unlabeled data. Do not tune on unrealistically large validation sets. SSL is most appropriate when no similar-domain labeled data exists, when labeled and unlabeled data share a distribution, and when the labeled set is large enough for reliable validation.
- **USB benchmark (Wang et al., NeurIPS 2022 Datasets & Benchmarks).** 15 tasks across CV, NLP and audio, with pretrained backbones to cut cost. Evaluating FixMatch on all 15 tasks takes 39 GPU-days on one V100, vs 335 GPU-days for TorchSSL on 5 CV tasks. — [B] [arXiv:2208.07204](https://arxiv.org/abs/2208.07204). **(research evidence)**

**Medical-imaging SSL at small labeled sizes**
- **Huang, Jiang, Aeron & Hughes (CVPR 2024)** — [B] [arXiv:2307.08919](https://arxiv.org/abs/2307.08919) and [full text, ar5iv](https://ar5iv.labs.arxiv.org/html/2307.08919). **(research evidence)**
  - *Design.* 13 semi- and self-supervised methods vs labeled-only baselines on 4 medical datasets, more than 20,000 GPU-hours. Hyperparameters were tuned on realistic validation sets, never larger than the training set.
  - *Labeled and unlabeled sizes:*

    | Dataset | Labeled train | Labeled val | Unlabeled |
    |---|---|---|---|
    | TissueMNIST | 400 | 400 | ~165k |
    | PathMNIST | 450 | 450 | ~89.5k |
    | TMED-2 | 1,660 | 235 | 353.5k |
    | AIROGS (60 positives) | 600 | 600 | ~94k |

  - *Gains.* MixMatch was the most reliable: balanced accuracy +12.4 (PathMNIST), +3.7 (TissueMNIST), −0.2 (TMED-2), +5.7 (AIROGS); median +4.7.
  - *Failures.* PseudoLabel had a median of −2.3. Mean Teacher was below baseline on 3 of 4 datasets. MoCo scored −18.8 and SimSiam −11.6 on TMED-2. Hyperparameters transferred from another dataset can diverge (MixMatch on AIROGS).
  - *ImageNet pretraining* gave only 0.5–3 points (about 5 for FixMatch on PathMNIST). It mainly sped convergence and reduced variance.
  - *Compute.* Performance saturated after about 25 GPU-hours per 80,000 unlabeled examples.
  - *Leakage and external validation.* I did not verify patient-level splitting in these datasets, and there is no external validation in the sense of a new site. The paper is a benchmark, not a clinical study.
- **Medical SSL surveys.** I did not open the Jiao et al. survey or the Chen et al. 2022 MedIA survey. **No verified numbers from them are used here.**

**Semi-supervised object detection (SSOD)**
- **Unbiased Teacher (Liu et al., ICLR 2021).** Identifies pseudo-labeling bias in SSOD; uses a gradually progressing teacher plus a class-balance loss that down-weights overconfident pseudo-labels.
  - On MS-COCO: +6.8 mAP over the prior state of the art at 1% labels, and about +10 mAP over the supervised baseline at 0.5/1/2% labels.
  - 1% of COCO is still about 1,200 labeled images (inference from COCO train2017 ≈ 118k images).
  - [B] [arXiv:2102.09480](https://arxiv.org/abs/2102.09480). **(research evidence)**
- **Efficient Teacher (Xu et al., 2023).** SSOD for YOLOv5, built from a Dense Detector, a Pseudo Label Assigner and an Epoch Adaptor. Claims state-of-the-art on VOC, COCO-standard and COCO-additional with fewer FLOPs. Code is at AlibabaResearch/efficientteacher. — [D] [arXiv:2302.07577](https://arxiv.org/abs/2302.07577). **(research evidence, preprint)**

### Inferences
- **(inference)** Every positive SSL result above uses at least about 400 labeled images (often thousands) and at least about 89k unlabeled images, all from the same distribution. The project has about 120 labeled photos from 14 patients and an unknown, heterogeneous LINE pool. That is outside the regime where gains were shown.
- **(inference)** The current DINOv2-small + logistic regression model is a strong transfer baseline. Oliver et al. and Huang et al. both show that well-tuned transfer or supervised baselines erase much of the reported SSL gain. Any SSL claim on this platform has to beat the tuned DINOv2+LR and EfficientNet-B0 baselines on the same patient-grouped folds.
- **(inference) Validation resolution is too coarse.** With 3 patient-grouped folds and 14 patients, each test fold holds about 4–5 patients and about 40 photos. By the same Hoeffding bound Oliver et al. use:
  - per fold (n ≈ 40): ε = sqrt(ln(2/0.05)/(2n)) ≈ 0.21;
  - all ~120 out-of-fold predictions pooled: ε ≈ 0.12.

  Photos are clustered within patients, so the effective n is closer to 14. An SSL gain of a few points (the typical size in Huang et al.) cannot be detected NOW, and SSL hyperparameters (τ, λ_u, μ) cannot be tuned meaningfully.
- **(inference) Imbalance makes it worse.** The binary task (47 vs 9) is highly imbalanced. A fixed-threshold FixMatch will mostly produce majority-class pseudo-labels. This motivates class-adaptive thresholds (the FlexMatch idea) and class-balance terms (Unbiased Teacher), but neither was validated at n = 9 minority examples.
- **(inference) LINE photos are out-of-distribution risk.** LINE submissions may include non-IV-site content, different lighting, and different skin tones and devices. That matches the class-mismatch failure Oliver et al. describe. An OOD filter (for example, DINOv2 distance to labeled IV-site photos) plus human screening would be needed before any photo enters an unlabeled pool.
- **(inference) SSOD for YOLO:** with about 24 boxed photos, SSOD is far below the 0.5–10% COCO regimes studied (≥ ~600 labeled images). Efficient Teacher is YOLOv5-specific; porting it to Ultralytics 8.4 YOLO11/YOLO26 would be a substantial engineering project. In the Ultralytics docs I reviewed, I found no built-in Ultralytics SSOD mode (not exhaustively verified). **Not worth doing NOW or at FUTURE scale unless boxed images reach many hundreds.**

### Gaps
- No reliable evidence found on SSL for photos of skin, wounds or IV sites at tens to hundreds of labels.
- I did not open the Jiao et al. or Chen et al. 2022 medical SSL surveys, so no numbers from them are included.
- I did not verify FixMatch's paper-level defaults (B = 64, K = 2^20 iterations, SGD with Nesterov, cosine schedule) from the paper text; the ar5iv conversion failed. Only the official repo's example run folder was seen.
- No primary source gives a minimum labeled/unlabeled count at which SSL becomes worthwhile. Oliver et al. state only qualitative conditions.

---

## Q2. Active learning: cold start, typicality vs uncertainty, and AL vs random

### Takeaway
Evidence conflicts:
- Hacohen et al. (ICML 2022) and Chen et al. (MIDL 2023) show uncertainty-based AL is at or below random at low budgets, while typicality/diversity selection (TypiClust, HaCon) beats random.
- Munjal et al. (CVPR 2022) and Lüth et al. (NeurIPS 2023) show that with proper regularization and tuning, AL gains over random are often marginal and inconsistent. Lüth et al. found cold-start failures mostly absent except for Entropy/BALD, and BADGE the most robust.

For this platform:
- **NOW:** use typicality/diversity selection (DINOv2 + k-means/TypiClust, with a one-photo-per-patient constraint) to decide *which photos to box or review first*. Do not expect measurable label savings.
- **FUTURE:** a BADGE- or margin-based loop is reasonable, but only after a simulated-AL check on the platform's own patient-grouped data shows it beats random.

### Cited Findings
- **Hacohen, Dekel & Weinshall (ICML 2022)** — [B] [arXiv:2202.02794](https://arxiv.org/abs/2202.02794); method details from [ar5iv full text](https://ar5iv.labs.arxiv.org/html/2202.02794). **(research evidence)**
  - Typical examples are best at low budgets and unrepresentative examples at high budgets (a "phase transition").
  - TypiClust: typicality = inverse mean Euclidean distance to the K = 20 nearest neighbours in a self-supervised embedding (SimCLR; DINO for ImageNet). Cluster into |L| + B clusters with k-means, then pick the most typical example from each of the B largest uncovered clusters.
  - In the supervised low-budget setting, "all other baseline AL methods perform on par with random selection or worse", with budgets of B = M or 5M (M = number of classes).
  - With semi-supervised training, 10 TypiClust-chosen CIFAR-10 labels gave 93.2% with FlexMatch, reported as +39.4% over random selection.
- **Chen, Bai, Huang, Lu, Wen, Yuille & Zhou.** "Making Your First Choice: To Address Cold Start Problem in Medical Active Learning." MIDL 2023, PMLR 227:496–525 (2024). — [C] [PMLR](https://proceedings.mlr.press/v227/chen24a.html); code at [github.com/cliangyu/CSVAL](https://github.com/cliangyu/CSVAL) (search-only). **(research evidence)**
  - AL is less efficient than random at the first few choices, which the authors attribute to biased and outlier initial queries.
  - HaCon uses contrastive features to find typical data and pseudo-labels (cluster labels) for label diversity. It needs no annotations and beats random "by a large margin" on 3 public medical datasets.
  - Exact numbers and dataset names were not on the page I opened.
- **Lüth, Bungert, Klein & Jaeger (NeurIPS 2023)** — [B] [arXiv:2301.10625](https://arxiv.org/abs/2301.10625) and [ar5iv full text](https://ar5iv.labs.arxiv.org/html/2301.10625). **(research evidence)**
  - Five pitfalls: P1 data distribution (balanced benchmarks), P2 starting budget, P3 query size, P4 untuned classifier configuration, P5 not comparing with or combining Self-SL/Semi-SL.
  - AL turned out more robust to small starting budgets than previously reported; cold-start failures were "largely absent". Exceptions: BALD/Entropy with Self-SL on CIFAR-100, and BALD/Core-Set/Entropy with Self-SL on MIO-TCD.
  - BADGE was the most robust, with no sub-random failures. Entropy was the only method with cold-start problems in the main experiments.
  - AL gains were larger on class-imbalanced data (ISIC-2019, MIO-TCD).
  - Tuning hyperparameters on a validation set made a *random* baseline beat originally reported AL results on CIFAR-10/100.
  - Semi-SL (FixMatch) generalized poorly beyond CIFAR and cost about 80× (up to about 400× per the limitations section) the training time of standard training.
  - Recommendations: default to BADGE; tune on a validation split; Self-SL pretraining helps; Semi-SL + AL is usually not worth the cost; use smaller query sizes with BALD.
- **Munjal, Hayat, Hayat, Sourati & Khan (CVPR 2022).** Under identical settings, uncertainty-, diversity- and committee-based AL gave inconsistent gains over random. With strong regularization they showed "marginal or no advantage over the random sampling baseline". Uncontrolled stochasticity can reverse published conclusions. — [B] [arXiv:2002.09564](https://arxiv.org/abs/2002.09564). **(research evidence)**
- **Sener & Savarese (ICLR 2018), Core-set.** Many AL heuristics are not effective for CNNs in batch settings. AL is framed as core-set selection (cover the data geometry) and substantially outperformed the methods of the time. — [B] [arXiv:1708.00489](https://arxiv.org/abs/1708.00489). **(research evidence)**
- **Ash et al. (ICLR 2020), BADGE.** Samples "disparate and high-magnitude" points in a hallucinated gradient space, trading off uncertainty and diversity without hand-tuned hyperparameters; "consistently performs as well or better" across batch sizes and architectures. The abstract page I opened does not mention k-means++ seeding; that detail comes from my prior knowledge of the paper and is unverified here. — [B] [arXiv:1906.03671](https://arxiv.org/abs/1906.03671). **(research evidence)**
- **Budd, Robinson & Kainz (2021).** "A survey on active learning and human-in-the-loop deep learning for medical image analysis." *Medical Image Analysis* 71:102062, doi:10.1016/j.media.2021.102062. An opinion-led review covering AL, interaction with model outputs, practical deployment, and open questions, with a segmentation focus. — [B] search-only: [ar5iv listing](https://ar5iv.arxiv.org/html/1910.02923), [Imperial repository](https://spiral.imperial.ac.uk/entities/publication/405db4f2-8511-4c2e-b5c8-c5f3bae176d7). **(research evidence; contents not verified in full)**

### Inferences
- **(inference) The evidence is narrower than "AL saves X% of labels".** Benchmarks run with pools of tens of thousands; this project's NOW pool is about 120 labeled photos plus an unknown unlabeled LINE count.
  - Hospital class labels come almost free from filename rules, so AL for class labels saves little.
  - The expensive human steps are **lesion boxes** (only about 24 of about 120 photos have them) and **manual LINE review**. That is where prioritization pays off.
- **(inference) Multiple photos per patient break the i.i.d. assumption.** A TypiClust-style selector should add a group constraint: at most one or two photos per patient (or per LINE user) per batch. Otherwise the most "typical" cluster centres may all come from one patient.
- **(inference)** Uncertainty sampling from 3 fold models trained on 14 patients will be poorly calibrated. Hacohen et al.'s low-budget argument and Lüth et al.'s Entropy cold-start failures both argue against entropy as the first query rule NOW.
- **(inference)** Lüth et al. found larger gains under class imbalance. The current binary data is imbalanced (47:9), but the FUTURE data is planned to be balanced, which lowers AL's expected benefit then.
- **(inference) Label savings cannot be quantified for this domain.** No primary source opened gives a transferable percentage. **No reliable evidence found** for a number that would apply here.

### Gaps
- Exact HaCon numbers (datasets, AUC gains over random) were not on the PMLR abstract page; the PDF was not opened.
- Budd et al. (2021) was search-only, so I extracted no quantitative claims from it.
- I found no study of AL with a patient-grouped constraint at 10–20 patients.

---

## Q3. Complying with "model suggestions must be human-confirmed before being written"

### Takeaway
Classic FixMatch, Mean Teacher, Pseudo-Label, Unbiased Teacher and Efficient Teacher all train on **unconfirmed** model outputs at training time.
- They never *write* a label, so a literal reading of the rule may allow them.
- But the resulting weights *are* shaped by unconfirmed labels, which conflicts with the rule's intent.

Recommended policy:
1. **Default (compliant):** "confirmed pseudo-labels only". The model proposes, a human accepts, edits or rejects, and only the human-confirmed record is written, with full provenance.
2. **Optional, and only if the project owner explicitly approves it in writing:** an "experimental consistency-regularization" track. Pseudo-targets stay in GPU memory only; nothing is persisted. Each run is manually launched; the output is quarantined as experimental and not eligible for promotion or shadow-to-primary use without a separate human decision.

### Cited Findings
- FixMatch's pseudo-labels are produced on the fly from weakly augmented views, filtered by a confidence threshold (official example run: 0.95), and used as targets for strongly augmented views. Nothing is stored. — [B] [arXiv:2001.07685](https://arxiv.org/abs/2001.07685); [E] [official repo](https://github.com/google-research/fixmatch). **(research evidence)**
- Pseudo-label bias is a known failure mode: Unbiased Teacher was designed around overconfident, class-biased pseudo-labels in detection. — [B] [arXiv:2102.09480](https://arxiv.org/abs/2102.09480). **(research evidence)**
- Confirmation-bias risk: PseudoLabel had a negative median gain (−2.3) across 4 medical datasets. — [B] [Huang et al. 2024](https://ar5iv.labs.arxiv.org/html/2307.08919). **(research evidence)**
- Ultralytics predict outputs map directly to a suggestion record: `boxes.xyxy`/`boxes.xywhn`, `boxes.conf`, `boxes.cls`. Defaults are `conf=0.25` and `iou=0.7`; `save_txt` writes `[class x y w h conf]`. — [A] [Ultralytics predict docs](https://docs.ultralytics.com/modes/predict/). **(industry practice)**

### Inferences (design proposal)
- **(inference) Conflict analysis.**
  - *Letter of the rule:* "written" means persisted to the label store or DB. On-the-fly FixMatch writes nothing, so it does not breach the letter.
  - *Spirit of the rule:* the rule exists so that no unverified model output silently becomes ground truth. A model trained with unconfirmed pseudo-targets embeds them in its weights. If that model is later used to make *suggestions*, the unconfirmed signal propagates indirectly.
  - *Training launches:* the "no auto-training" rule also forbids any background or scheduled SSL. Every SSL run must be a manual launch.
  - *Conclusion:* treat on-the-fly SSL as **not permitted by default**. Allow it only as Tier B below, after an explicit owner decision recorded in the project's decision log.
- **(inference) Tier A — confirmed pseudo-labels only (fully compliant; recommended).**
  1. A human manually launches a suggestion job: predict over an unlabeled batch with model version X.
  2. The job writes rows to `model_suggestions` only. They are never visible to the training loader.
  3. The review UI lets the human accept, edit or reject. An accept or edit creates a normal `annotations` row with `source='assisted_accepted'` or `'assisted_edited'` and `suggestion_id`.
  4. Training reads only `annotations` (human-created or human-confirmed). Rejected and pending suggestions are never trainable.
  5. Training manifests record how many training labels came from assisted review, so assisted vs fully manual labels can be ablated.
- **(inference) Tier B — experimental in-memory consistency regularization (optional; needs owner approval).**
  - The unlabeled pool is a frozen manifest of photo IDs. It is consent-checked at launch and re-checked at every epoch: revoked photos are removed immediately, matching the "revocation takes effect immediately" rule.
  - Pseudo-targets live only in GPU/CPU memory during the run. No pseudo-label is ever logged per image; at most, aggregate counts such as mask rate per class are logged.
  - The output checkpoint is tagged `experimental_ssl=true`. It cannot be selected as a primary or shadow model, or used to generate suggestions, without a separate human sign-off.
  - Every comparison is reported against the same-fold supervised baseline.
- **(inference) Revocation.** When consent is revoked, pending suggestions on that photo are set to `void`, the photo leaves every AL/SSL pool, and any confirmed label leaves training sets per the existing platform policy. How to handle models already trained on revoked photos is outside this note's scope; follow the platform's existing revocation rules.

### Gaps
- No published guidance found on regulating "on-the-fly pseudo-labels" under a human-confirmation rule. The analysis above is entirely inference.

---

## Q4. Do model suggestions bias annotators (automation bias, anchoring), and how to mitigate?

### Takeaway
Yes, consistently.
- Annotators anchor on pre-annotations in NLP labeling (EMNLP 2016).
- Radiologists of every experience level followed incorrect AI BI-RADS suggestions in a Radiology 2023 study (search-only).

For a single annotator, the main mitigations:
- a blind first pass on a random audit subset;
- hiding scores by default;
- requiring an explicit action to accept;
- tracking accept, edit and reject rates per model version.

### Cited Findings
- **Berzak, Huang, Barbu, Korhonen & Katz (EMNLP 2016), "Anchoring and Agreement in Syntactic Annotations".** "A clear anchoring effect" when annotators edit tagger/parser output, leading to overestimated parser performance and lower annotation quality than human-only annotation. — [B] [arXiv:1605.04481](https://arxiv.org/abs/1605.04481). **(research evidence)**
- **Dratsch et al. (Radiology 2023), "Automation Bias in Mammography: The Impact of Artificial Intelligence BI-RADS Suggestions on Reader Performance".** Search-only — the primary article was not opened; verify before citing.
  - 27 radiologists read 50 mammograms with purported AI suggestions.
  - Inexperienced readers: 79.7% correct when the AI was correct vs 19.8% when it was incorrect. Very experienced readers: 82.3% vs 45.5%.
  - Proposed safeguards include showing AI confidence, explaining the system's reasoning, and keeping readers accountable.
  - [B] [RSNA news](https://www.rsna.org/news/2023/may/ai-bias-may-impair-accuracy); [Univ. Lübeck record](https://research.uni-luebeck.de/en/publications/automation-bias-in-mammography-the-impact-of-artificial-intellige/). **(research evidence; secondary access)**
- **Label suggestions in German Covid-19 opinion mining** (arXiv 2105.12980). Suggestion acceptance rates stayed stable at about 68–73%, and annotators rarely accepted model errors. — [D] search-only: [arXiv:2105.12980](https://arxiv.org/pdf/2105.12980). **(research evidence, weak)**
- **LLM suggestions for crowdworkers** (arXiv 2507.15821). Suggestions did not speed workers up but raised their confidence and significantly shifted the label distribution. — [D] search-only: [arXiv:2507.15821](https://web3.arxiv.org/pdf/2507.15821). **(research evidence, weak)**

### Inferences
- **(inference)** With one annotator and no second reader, anchoring cannot be detected by inter-rater disagreement. It has to be measured inside the workflow.
- **(inference) Mitigations, in order of priority:**
  1. **Blind audit subset.** For example, 10–20% of each suggestion batch, chosen at random, is labeled with no suggestion shown. Compare the blind labels with what the model would have suggested, to estimate the anchoring rate.
  2. **Hide the score and class colour by default.** Show the box outline only; the score is available on demand. This reverses the Dratsch "show confidence" suggestion. The trade-off is unresolved: no reliable evidence found for which option is better in single-annotator image labeling.
  3. **Opt-in acceptance.** No "accept all"; each suggestion needs an explicit action, and each box needs a per-box confirm.
  4. **Store `display_mode`.** Record whether a suggestion was shown, plus time-to-decision.
  5. **Monitor the acceptance rate per model version.** A near-100% acceptance rate is a red flag, not a success.
  6. **Keep staging labels suggestion-free.** For staging, the ordinal and clinically ambiguous task, do not show model stage suggestions at all NOW. Use model assistance only for box localization.
- **(inference)** Because anchoring inflates apparent agreement between model and labels (Berzak et al.), evaluation metrics must be computed only on labels created without suggestions (the blind subset, or labels made before suggestions existed). Otherwise reported performance will be inflated.

### Gaps
- No reliable evidence found specifically on anchoring in bounding-box annotation of skin or wound photos.
- The Dratsch numbers were seen only through secondary pages; the primary DOI was not opened.

---

## Q5. Patient-level leakage in SSL and AL

### Takeaway
SSL and AL add new leakage paths beyond the labeled split:
- unlabeled photos from test-fold patients used in SSL training (transductive leakage);
- clustering or typicality computed over the full pool including test patients;
- LINE photos from the same person under different submissions.

Every unlabeled photo needs a group ID: hospital patient ID or LINE user ID, merged with near-duplicate clusters. The unlabeled pool for fold k must exclude every group in fold k's test set.

### Cited Findings
- Oliver et al. recommend realistic splits and warn against tuning on unrealistically large or unrealistic validation data. — [B] [ar5iv:1804.09170](https://ar5iv.labs.arxiv.org/html/1804.09170). **(research evidence)**
- Lüth et al. P4/P5: AL must be evaluated with tuned classifiers and with proper validation drawn from the starting budget. — [B] [ar5iv:2301.10625](https://ar5iv.labs.arxiv.org/html/2301.10625). **(research evidence)**
- No primary source opened specifically quantifies patient-level leakage through the SSL unlabeled pool. **No reliable evidence found** for a magnitude.

### Inferences
- **(inference) Rules for the platform:**
  1. **Group IDs.** Every photo, labeled or not, carries `group_id`: the hospital patient ID, or a pseudonymous LINE user ID. Photos with an unknown owner get a singleton group, merged with any near-duplicate cluster.
  2. **Near-duplicate merging.** Compute DINOv2-small CLS embeddings and merge photos with cosine similarity above a threshold (for example 0.9; tune by human inspection of the pairs) into the same group. This guards against one person submitting the same arm through different channels.
  3. **Per-fold unlabeled pools.** For SSL fold k: `U_k = U − {photos whose group ∈ test_groups_k}`. Never use test-fold photos as unlabeled data, even unlabeled.
  4. **Fit selection models on the training fold only.** For AL simulation and for k-means/typicality, fit on that fold's pool, not on all photos. Frozen DINOv2 weights are fine because they were pretrained externally.
  5. **Group-aware queries.** An AL query batch should spread across groups (at most one photo per group per batch).
  6. **Consent filter at every pool build.** A revoked photo drops out of U_k and the AL pool immediately.
- **(inference)** Reported AL/SSL results should note that only 14 patients exist, so per-fold estimates carry the wide uncertainty computed in Q1.

### Gaps
- No public study found that measures SSL leakage via unlabeled test-patient images in dermatology or wound photography.

---

## Q6. Implementation in the stack (SQLite, DINOv2, Ultralytics, PyTorch)

### Takeaway
Build in this order:
1. A `model_suggestions` table plus a review UI (Tier A), so model-assisted box suggestions from Ultralytics `predict` become human-confirmed labels with provenance.
2. An offline active-learning selector (DINOv2-small embeddings, group-constrained k-means/TypiClust, with optional CV-ensemble uncertainty in FUTURE).
3. A simulated-AL benchmark on the existing labeled data.

FixMatch code is given below for completeness. It should exist only as a manually launched experimental script (Tier B), and is not recommended NOW.

### Cited Findings
- Ultralytics predict: `conf` default 0.25, `iou` 0.7, `max_det` 300; `save_txt`/`save_conf` file format; Results attributes `boxes.xyxy`, `boxes.xywhn`, `boxes.conf`, `boxes.cls`. — [A] [docs.ultralytics.com/modes/predict](https://docs.ultralytics.com/modes/predict/). **(industry practice)**
- TypiClust: K = 20 neighbours for typicality, |L| + B k-means clusters, most typical point from each of the B largest uncovered clusters. — [B] [ar5iv:2202.02794](https://ar5iv.labs.arxiv.org/html/2202.02794). **(research evidence)**
- FixMatch example settings: τ = 0.95, λ_u (wu) = 1, μ (uratio) = 7, batch 64, lr 0.03, wd 5e-4. — [E] [official repo](https://github.com/google-research/fixmatch). FlexMatch per-class thresholds — [B] [arXiv:2110.08263](https://arxiv.org/abs/2110.08263). **(industry practice / research evidence)**
- DINOv2 is a self-supervised ViT family distilled from a 1B-parameter model (Oquab et al.; arXiv 2304.07193, v2 2024). The abstract page does not state the ViT-S/14 parameter count. — [B/D] [arXiv:2304.07193](https://arxiv.org/abs/2304.07193). **(research evidence)**
- Compute basis: SSL saturated at about 25 GPU-hours per 80k unlabeled examples (Huang et al. 2024). — [B] [ar5iv:2307.08919](https://ar5iv.labs.arxiv.org/html/2307.08919). Semi-SL cost about 80× standard training (Lüth et al. 2023). — [B] [ar5iv:2301.10625](https://ar5iv.labs.arxiv.org/html/2301.10625). FixMatch across 15 USB tasks: 39 V100 GPU-days. — [B] [arXiv:2208.07204](https://arxiv.org/abs/2208.07204). **(research evidence)**

### Inferences (concrete design)

#### 6.1 SQLite schema (inference)
```sql
CREATE TABLE model_suggestions (
  id               INTEGER PRIMARY KEY,
  photo_id         INTEGER NOT NULL REFERENCES photos(id),
  group_id         TEXT NOT NULL,              -- patient / LINE user / dup-cluster
  task             TEXT NOT NULL CHECK (task IN ('box','binary','stage')),
  payload_json     TEXT NOT NULL,              -- {"cls":0,"xywhn":[...]} or {"label":"stage1"}
  score            REAL,                       -- conf / prob; hidden in UI by default
  model_name       TEXT NOT NULL,              -- e.g. 'yolo11s'
  model_version    TEXT NOT NULL,              -- training run id
  weights_sha256   TEXT NOT NULL,
  job_id           TEXT NOT NULL,              -- manual suggestion-job launch id
  query_strategy   TEXT,                       -- 'random','typiclust','margin','badge'
  query_rank       INTEGER,
  display_mode     TEXT NOT NULL CHECK (display_mode IN ('shown','blind_audit')),
  status           TEXT NOT NULL DEFAULT 'pending'
                   CHECK (status IN ('pending','accepted','edited','rejected','void')),
  reviewer         TEXT,
  reviewed_at      TEXT,
  decision_ms      INTEGER,
  annotation_id    INTEGER REFERENCES annotations(id),  -- set only on accept/edit
  created_at       TEXT NOT NULL DEFAULT (datetime('now'))
);
-- annotations gains: source TEXT CHECK (source IN ('manual','filename_rule','assisted_accepted','assisted_edited')),
--                    suggestion_id INTEGER NULL REFERENCES model_suggestions(id)
-- Training loaders read ONLY annotations; a DB view `trainable_annotations` joins consent='active'.
-- Consent revocation trigger: UPDATE model_suggestions SET status='void' WHERE photo_id=? AND status='pending'.
```

#### 6.2 Box-suggestion workflow with Ultralytics (inference; API per [A] docs)
```python
# backend/app/ml/suggest_boxes.py (proposed location). Run ONLY from a manual "Create suggestion job" button.
from ultralytics import YOLO
model = YOLO(weights_path)               # record sha256(weights) before use
for batch in chunks(photo_paths, 16):
    results = model.predict(batch, conf=0.10, iou=0.5, max_det=5, verbose=False)
    for r, pid in zip(results, batch_ids):
        for xywhn, conf, cls in zip(r.boxes.xywhn.tolist(), r.boxes.conf.tolist(), r.boxes.cls.tolist()):
            insert_suggestion(pid, task="box", payload={"cls": int(cls), "xywhn": xywhn},
                              score=conf, display_mode=pick_blind_or_shown(pid))  # ~15% blind_audit
# Nothing is written to labels/*.txt. YOLO label files are exported only from confirmed annotations.
```
- Use a low `conf` (0.05–0.15) for recall during human review: a human removing a box is cheaper than missing a lesion. The parameter range is inference.
- The React review UI shows the outline only. The keyboard flow is Accept / Adjust / Reject / No-lesion. The score is hidden unless toggled.

#### 6.3 Active-learning selector (inference)
```python
# backend/app/ml/al_select.py (proposed). Offline, manual, returns a ranked list. Never labels anything.
emb = dinov2_small_cls(pool_imgs)                       # frozen, L2-normalised, cached by photo sha256
def typicality(X, k=20):                                 # Hacohen et al. K=20
    d = knn_dist(X, k)                                   # sklearn NearestNeighbors
    return 1.0 / d.mean(1)
def typiclust_grouped(emb_pool, emb_labeled, groups, B, used_groups):
    km = KMeans(n_clusters=len(emb_labeled) + B, n_init=10).fit(np.vstack([emb_labeled, emb_pool]))
    uncovered = [c for c in largest_clusters(km) if not covers_labeled(c)]
    picks = []
    for c in uncovered:
        cand = [i for i in members(c) if groups[i] not in used_groups]  # <=1 photo per patient/LINE user
        if cand:
            i = max(cand, key=lambda j: typicality_in_cluster(j, c))
            picks.append(i); used_groups.add(groups[i])
        if len(picks) == B: break
    return picks
# FUTURE uncertainty: p = mean over 3 CV fold models (DINOv2+LR, or EffNet-B0);
#   margin = p_top1 - p_top2 ; entropy = -sum p log p ; disagreement = var over folds
#   hybrid: take the 3*B highest-margin-uncertain, then k-means++ into B for diversity (BADGE-like, cheap)
# MC dropout (EfficientNet-B0 classifier dropout): T=10-20 stochastic passes, model.train() on dropout only.
```
Parameter ranges (inference):
- B = 5–20 photos per query (Lüth et al.: small query sizes help BALD);
- k-NN K = 10–20, reduced when the pool is small;
- cap the cluster count at the pool size.

#### 6.4 Simulated AL on existing labels — the platform's validation protocol (inference)
1. For each of the 3 StratifiedGroupKFold folds, use the training patients as the "pool" and keep the test patients fixed.
2. Seed with S = 6–10 photos chosen by each strategy (random, TypiClust-grouped, k-means centroid, and later margin and BADGE). Reveal the labels of queried photos from the existing ground truth.
3. Query B = 5 photos per round until the pool is exhausted. At each step, refit DINOv2+LR (cheap) and record balanced accuracy, AUROC and macro-F1 on the test patients.
4. Repeat over at least 10 random seeds. Report the mean learning curve with 95% CI and the area under the learning curve per strategy.
5. Declare AL "worth it" only if its curve sits above random's with non-overlapping CIs at the budgets that matter.

#### 6.5 FixMatch pseudo-code (Tier B only; manual launch; in-memory pseudo-targets; inference)
```python
# experiments/ssl/fixmatch_effnet.py (proposed; outside the app's training queue)
tau, lam_u, mu = 0.95, 1.0, 2          # paper/official repo: tau 0.95, lam_u 1, mu 7; mu 2-3 here for VRAM
B = 16                                  # labeled batch; unlabeled batch = mu*B
weak   = T.Compose([T.RandomResizedCrop(224, scale=(0.8,1)), T.RandomHorizontalFlip()])
strong = T.Compose([weak, T.RandAugment(num_ops=2, magnitude=10), T.RandomErasing()])   # cutout-like
ema = torch.optim.swa_utils.AveragedModel(model, multi_avg_fn=get_ema_multi_avg_fn(0.999))
for step in range(max_steps):
    xl, yl = next(lab_iter)                       # confirmed labels only
    xu = next(unl_iter)                           # consent re-checked at each epoch; fold-excluded groups
    logits_l = model(weak(xl))
    with torch.no_grad():
        p = model(weak(xu)).softmax(1)
        conf, yhat = p.max(1)
        mask = (conf >= tau_per_class(yhat)).float()   # FlexMatch-style class-adaptive option
    logits_u = model(strong(xu))
    loss = F.cross_entropy(logits_l, yl, weight=class_w) + \
           lam_u * (F.cross_entropy(logits_u, yhat, reduction='none') * mask).mean()
    opt.zero_grad(); scaler.scale(loss).backward(); scaler.step(opt); scaler.update(); ema.update_parameters(model)
    log_aggregate(mask_rate_per_class(mask, yhat))     # NEVER log per-image pseudo-labels
save(ema, tags={"experimental_ssl": True, "unlabeled_manifest_sha": ..., "fold": k})
```
Parameter ranges (inference, starting from the cited defaults):
- τ 0.90–0.97 (FlexMatch-style per-class thresholds for the imbalanced binary task);
- λ_u 0.5–1;
- μ 2–7, limited by VRAM;
- lr 0.003–0.03 SGD for fine-tuning a pretrained EfficientNet-B0. The paper's 0.03 was for training WRN from scratch; lower is typical for fine-tuning (inference).

#### 6.6 GPU memory and time estimates (all inference; basis stated; measure before trusting)
- **DINOv2-small embedding** of 1,000 photos at 224 px, inference only. DINOv2 ViT-S/14 has about 21M parameters (from prior knowledge; the abstract page did not state it). Memory under about 2 GB; time on the order of a minute on a consumer GPU. AL selection (k-means on 1,000 × 384) takes seconds on CPU.
- **Simulated AL with DINOv2+LR:** features are cached, so each refit is a scikit-learn LR on at most 120 (NOW) or 1,000 (FUTURE) rows. A full 3-fold × 10-seed × ~20-round run takes minutes on CPU.
- **YOLO suggestion job** (predict over about 1,000 images, YOLO11s): batch inference, minutes, under 4 GB VRAM. Basis: nano and small models, inference only.
- **FixMatch with EfficientNet-B0 at 224 px, B = 16, μ = 2:**
  - about 16 + 32 × 2 views = 80 images per step plus backward;
  - with AMP, probably about 6–10 GB VRAM. Unverified estimate; lower μ or resolution if OOM.
  - Time basis: Huang et al.'s saturation at about 25 GPU-hours per 80k unlabeled images, scaled linearly, suggests about 0.3 GPU-hours per 1k unlabeled images. That figure was for 28–384 px images on their hardware, so treat it as an order of magnitude only.
  - The run must repeat for 3 folds × several hyperparameter settings. Lüth et al. report Semi-SL at about 80× standard training cost.

### Gaps
- I did not verify FixMatch's full paper hyperparameter table (2^20 iterations, Nesterov, cosine decay) from primary text.
- No measured VRAM or time numbers exist for this hardware. All estimates above are inference and must be benchmarked on the platform's GPU.
- I found no official Ultralytics semi-supervised training mode in the docs reviewed (only the predict page was opened).

---

## Q7. NOW (14 patients, ~120 labeled) vs FUTURE (~1,000): when are SSL and AL worth it?

### Takeaway
- **NOW:**
  - **SSL: not worth it.** Below every studied regime; no possible validation resolution; out-of-distribution LINE risk; principle conflict.
  - **AL as "label savings": not measurable.**
  - **Do:** Tier A model-assisted box suggestions with a blind audit, typicality/diversity ordering of which unboxed or LINE photos to review first, and the simulated-AL benchmark as groundwork.
- **FUTURE:**
  - **AL** (BADGE/margin + diversity, group-constrained) is worth a simulated test once a large unlabeled, consented pool exists and labeling is the bottleneck.
  - **SSL** only as a Tier B experiment. Preconditions: at least several hundred labeled photos from many patients; a much larger in-distribution unlabeled pool, OOD-filtered (evidence regime: tens of thousands); an owner decision; and a gain over the tuned DINOv2+LR baseline on patient-grouped folds.

### Cited Findings
- Demonstrated medical SSL gains used 400–1,660 labeled and about 89k–353k unlabeled images, with median MixMatch +4.7 balanced accuracy and some methods negative. — [B] [Huang et al. 2024](https://ar5iv.labs.arxiv.org/html/2307.08919).
- SSL is most appropriate when the labeled set is large enough for reliable validation and the data are in-distribution; transfer can beat SSL. — [B] [Oliver et al. 2018](https://ar5iv.labs.arxiv.org/html/1804.09170).
- At low budgets, uncertainty-based AL is at or below random and typicality wins. — [B] [Hacohen et al. 2022](https://ar5iv.labs.arxiv.org/html/2202.02794); medical cold start: [C] [Chen et al. MIDL 2023](https://proceedings.mlr.press/v227/chen24a.html).
- Under tuned baselines, AL advantages are often marginal; BADGE is the most robust; gains are larger with class imbalance; Semi-SL + AL is rarely worth its cost. — [B] [Lüth et al. 2023](https://ar5iv.labs.arxiv.org/html/2301.10625); [B] [Munjal et al. 2022](https://arxiv.org/abs/2002.09564).

### Inferences

| Item | NOW | FUTURE (~1,000 labeled, balanced) |
|---|---|---|
| Pseudo-Label / FixMatch / FlexMatch / Mean Teacher | **Do not do.** Evidence strength for this regime: none. | Optional Tier B experiment if the in-distribution unlabeled pool reaches at least several thousand (evidence regime ≥ ~90k; below that is unknown). Expected benefit: small, possibly negative vs the DINOv2+LR transfer baseline. |
| SSOD (Unbiased / Efficient Teacher) | **Do not do** (24 boxes). | Only if boxed photos reach many hundreds **and** an Ultralytics-compatible implementation exists; otherwise skip. Efficient Teacher is YOLOv5-specific [D]. |
| Model-assisted box suggestions (Tier A) | **Do.** Main practical win: about 96 unboxed photos, plus a blind audit to measure anchoring. | Do; track acceptance and edit rates per model version. |
| AL query: typicality/diversity (TypiClust, k-means) | **Do, as review ordering.** Low cost; group constraint. Benefit unquantifiable at this size. | Use for each new unlabeled batch's first round (cold start). |
| AL query: uncertainty (entropy / margin / least-confidence / MC dropout) | **Do not rely on it.** Poorly calibrated with 14 patients; Entropy shows cold-start failures [B]. | Margin or a BADGE-like hybrid after the simulated-AL benchmark shows a gain over random. |
| Core-set | Not needed (pool too small). | Alternative to BADGE; one sub-random case reported with Self-SL [B]. |
| BADGE | Overkill NOW. | Recommended default per Lüth et al. [B]; needs last-layer gradient embeddings from EfficientNet-B0 or LR. |
| Simulated AL benchmark | **Do now** as tooling; results will have wide CIs. | Re-run to decide whether AL beats random. |

- **(inference) Minimum data thresholds.** No reliable evidence found for hard thresholds. Working heuristic, not an evidence-based number:
  - consider SSL only when (a) the out-of-fold test set is big enough to resolve about 3–5 point differences, which needs hundreds of patient-grouped test photos by the Hoeffding argument in Q1, and (b) the in-distribution unlabeled pool is at least 10× the labeled set.
  - AL becomes worth a real loop only when the unlabeled, consented pool is much larger than the labeling capacity per review session (for example ≥ 5–10× a session's capacity), and labels are costly (manual LINE staging, boxes) rather than filename-derived.
- **(inference) Label noise.** Because hospital stages come from filename rules, label noise rather than label quantity may be the binding constraint. A human re-review queue prioritized by fold-model disagreement (a Tier A suggestion of type `stage`, blind-first) may yield more than SSL or AL.

### Gaps
- No primary evidence found on SSL or AL for IV-site or phlebitis photos, or for any task at 14 patients.
- The size of the unlabeled pool is unknown, which blocks a concrete FUTURE SSL go/no-go.

### Bibliography (all sources accessed 2026-10-30)
1. Lee, D.-H. (2013). Pseudo-Label: The Simple and Efficient Semi-Supervised Learning Method for Deep Neural Networks. ICML 2013 Workshop on Challenges in Representation Learning. Search-only: https://storage.googleapis.com/kaggle-forum-message-attachments/8924/pseudo_label_final.pdf [C]
2. Tarvainen, A., Valpola, H. (2017). Mean teachers are better role models: Weight-averaged consistency targets improve semi-supervised deep learning results. NIPS 2017. https://arxiv.org/abs/1703.01780, doi:10.48550/arXiv.1703.01780 [B]
3. Sohn, K., Berthelot, D., Li, C.-L., Zhang, Z., Carlini, N., Cubuk, E. D., Kurakin, A., Zhang, H., Raffel, C. (2020). FixMatch: Simplifying Semi-Supervised Learning with Consistency and Confidence. NeurIPS 2020. https://arxiv.org/abs/2001.07685 [B]; code https://github.com/google-research/fixmatch [E]
4. Zhang, B., Wang, Y., Hou, W., Wu, H., Wang, J., Okumura, M., Shinozaki, T. (2021). FlexMatch: Boosting Semi-Supervised Learning with Curriculum Pseudo Labeling. NeurIPS 2021. https://arxiv.org/abs/2110.08263 [B]
5. Oliver, A., Odena, A., Raffel, C., Cubuk, E. D., Goodfellow, I. J. (2018). Realistic Evaluation of Deep Semi-Supervised Learning Algorithms. NeurIPS 2018. https://arxiv.org/abs/1804.09170 [B]
6. Wang, Y., Chen, H., Fan, Y., et al. (2022). USB: A Unified Semi-supervised Learning Benchmark for Classification. NeurIPS 2022 Datasets & Benchmarks. https://arxiv.org/abs/2208.07204 [B]
7. Huang, Z., Jiang, R., Aeron, S., Hughes, M. C. (2024). Systematic comparison of semi-supervised and self-supervised learning for medical image classification. CVPR 2024. https://arxiv.org/abs/2307.08919 [B]
8. Liu, Y.-C., Ma, C.-Y., He, Z., Kuo, C.-W., Chen, K., Zhang, P., Wu, B., Kira, Z., Vajda, P. (2021). Unbiased Teacher for Semi-Supervised Object Detection. ICLR 2021. https://arxiv.org/abs/2102.09480 [B]
9. Xu, B., Chen, M., Guan, W., Hu, L. (2023). Efficient Teacher: Semi-Supervised Object Detection for YOLOv5. arXiv:2302.07577. https://arxiv.org/abs/2302.07577 [D]
10. Sener, O., Savarese, S. (2018). Active Learning for Convolutional Neural Networks: A Core-Set Approach. ICLR 2018. https://arxiv.org/abs/1708.00489 [B]
11. Ash, J. T., Zhang, C., Krishnamurthy, A., Langford, J., Agarwal, A. (2020). Deep Batch Active Learning by Diverse, Uncertain Gradient Lower Bounds (BADGE). ICLR 2020. https://arxiv.org/abs/1906.03671 [B]
12. Hacohen, G., Dekel, A., Weinshall, D. (2022). Active Learning on a Budget: Opposite Strategies Suit High and Low Budgets. ICML 2022, PMLR 162. https://arxiv.org/abs/2202.02794 [B]
13. Chen, L., Bai, Y., Huang, S., Lu, Y., Wen, B., Yuille, A., Zhou, Z. (2024). Making Your First Choice: To Address Cold Start Problem in Medical Active Learning. MIDL 2023, PMLR 227:496–525. https://proceedings.mlr.press/v227/chen24a.html [C]
14. Munjal, P., Hayat, N., Hayat, M., Sourati, J., Khan, S. (2022). Towards Robust and Reproducible Active Learning Using Neural Networks. CVPR 2022. https://arxiv.org/abs/2002.09564 [B]
15. Lüth, C. T., Bungert, T. J., Klein, L., Jaeger, P. F. (2023). Navigating the Pitfalls of Active Learning Evaluation: A Systematic Framework for Meaningful Performance Assessment. NeurIPS 2023. https://arxiv.org/abs/2301.10625 [B]
16. Budd, S., Robinson, E. C., Kainz, B. (2021). A survey on active learning and human-in-the-loop deep learning for medical image analysis. Medical Image Analysis 71:102062. doi:10.1016/j.media.2021.102062. Search-only: https://ar5iv.arxiv.org/html/1910.02923 [B]
17. Berzak, Y., Huang, Y., Barbu, A., Korhonen, A., Katz, B. (2016). Anchoring and Agreement in Syntactic Annotations. EMNLP 2016. https://arxiv.org/abs/1605.04481 [B]
18. Dratsch, T., et al. (2023). Automation Bias in Mammography: The Impact of Artificial Intelligence BI-RADS Suggestions on Reader Performance. Radiology. Secondary only: https://www.rsna.org/news/2023/may/ai-bias-may-impair-accuracy ; https://research.uni-luebeck.de/en/publications/automation-bias-in-mammography-the-impact-of-artificial-intellige/ [B, primary not opened]
19. Oquab, M., Darcet, T., Moutakanni, T., et al. (2023/2024). DINOv2: Learning Robust Visual Features without Supervision. arXiv:2304.07193. https://arxiv.org/abs/2304.07193 [B/D]
20. Ultralytics. Predict mode documentation. https://docs.ultralytics.com/modes/predict/ [A]
21. Label-suggestion anchoring preprints (search-only): arXiv:2105.12980 https://arxiv.org/pdf/2105.12980 ; arXiv:2507.15821 https://web3.arxiv.org/pdf/2507.15821 [D]
