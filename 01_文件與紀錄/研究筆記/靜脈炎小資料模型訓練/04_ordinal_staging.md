# Ordinal classification for phlebitis staging (normal < stage 1 < stage 2) with very small image datasets: methods and metrics

Scope: 3-class ordered staging of IV-site photos (research prototype, not a diagnostic tool). NOW = 9 normal / 23 stage 1 / 24 stage 2 photos from 14 patients. FUTURE = about 1,000 balanced photos, with the patient count growing slowly.
Source grades: [A] official docs, standards and reporting guidelines; [B] top-venue peer-reviewed papers or systematic reviews; [C] other peer-reviewed papers; [D] preprints; [E] blogs, example code and forums.
Every source was accessed on 2026-10-30. The simulation was run locally on 2026-10-31. Full bibliographic details are in the "Source register" at the end of Q6.
Evidence labels: **[research evidence]** = stated in a source I opened; **[industry practice]** = library defaults and documented usage; **[inference]** = my own reasoning or my own simulation. The simulation is not a published result.

---

## Q1. What do benchmarks and medical-imaging studies show about ordinal methods vs softmax cross-entropy? (gain sizes, data sizes, counter-evidence)

### Takeaway
Every comparison I could verify used thousands to hundreds of thousands of images and 4 to 33 classes. In that setting, ordinal heads and losses beat plain softmax cross-entropy (CE) by modest margins. The gain is large when there are many classes (age estimation: MAE −0.1 to −0.7 years) and small when there are 4 or 5 classes (MAE −0.006 to −0.03; QWK +0.007 to +0.03 for CORN or CDW-CE vs CE on a 4-class endoscopy dataset). Several studies show no gain or a reversal. I found **no reliable evidence for a dataset of about 100 images or for a 3-class problem**.

### Cited Findings
**Benchmarks from the method papers (non-medical, large n)**
- **CORAL** (ResNet-34, 3 seeds, random 80/20 splits; mean test MAE in years, CE / OR-CNN / CORAL): MORPH-2 (55,608 images) 3.34±0.07 / 2.83±0.03 / 2.64±0.02; AFAD (165,501) 3.60±0.02 / 3.51±0.04 / 3.47±0.05; CACD (159,449) 5.65±0.11 / 5.38±0.02 / 5.25±0.01. Labels are ages, so there are dozens of classes. **[research evidence]** — [Cao, Mirjalili & Raschka 2020, PRL, arXiv v7 PDF](https://arxiv.org/abs/1901.07884) [C]
- **CORN** (ResNet-34, 5 seeds; test MAE, CE / OR-NN / CORAL / CORN): balanced MORPH-2 (20,625 images, 33 classes) 3.73±0.12 / 3.13±0.09 / 2.99±0.04 / 2.98±0.02; balanced AFAD (13 classes) 3.28±0.04 / 2.85±0.03 / 2.99±0.03 / 2.81±0.02; Fireman tabular data (16 classes, 40,688 rows) 0.80 / 0.76 / 0.82 / 0.76. On Fireman the authors write that performance is "relatively close" and the task is easy "regardless of the loss function". On Fireman, **CORAL was worse than CE** (0.82 vs 0.80). **[research evidence]** — [Shi, Cao & Raschka 2023, Pattern Anal Applic, arXiv v5 PDF](https://arxiv.org/abs/2111.08851) [C]
- In the CORN supplement (5-class image aesthetics, VGG16 pretrained, about 13.9k images), all methods (CE, OR-NN, CORAL, CORN, CNNPOR, SORD) fall within a test MAE of about 0.25–0.33. The text-extracted table is garbled column-wise, so I cite only the range. On the text datasets (LSTM), CE-RNN reached MAE 1.10±0.09 vs OR-RNN 1.11±0.07 on TripAdvisor, so there was no ordinal gain. **[research evidence]** — [Shi et al. 2023](https://arxiv.org/abs/2111.08851) [C]
- **SORD** soft ordinal labels (VGG-16): on 5-class image aesthetics (about 14.8k images), about +2% accuracy and about −0.02 MAE vs prior baselines. On Adience (26k images, 8 age groups, subject-exclusive folds), accuracy 59.6±3.6% vs 57.4±5.8% (CNN-POR) and 56.7±6.0% (Niu et al.); MAE 0.49±0.05 vs 0.54–0.61. The fold-to-fold SD (±3.6–6.0 accuracy points) is larger than the gain. **[research evidence]** — [Díaz & Marathe, CVPR 2019](https://openaccess.thecvf.com/content_CVPR_2019/papers/Diaz_Soft_Labels_for_Ordinal_Regression_CVPR_2019_paper.pdf) [B]

**Medical grading studies**
- **CLM layer (proportional-odds or cumulative-link output) plus QWK loss**, from Vargas et al.: on Kaggle diabetic retinopathy (5 grades; 17,563 training image pairs, 10% of patients held out for validation, official test set of 26,788 pairs), test QWK 0.582±0.016 vs 0.498±0.013 for a nominal softmax-CE network. On Adience, QWK 0.881±0.005 vs 0.787±0.004. Caveats: a small CNN trained from scratch; the CLM was combined with a continuous QWK loss and tuned learning rate and batch size; the authors note that some nominal configurations "stagnated". The ordinal benefit therefore mixes in optimisation effects. Splits were patient-aware (validation held out by patient, official test set). There was no external testing. **[research evidence]** — [Vargas, Gutiérrez & Hervás-Martínez 2020, Neurocomputing, arXiv PDF](https://arxiv.org/abs/1905.13392) [C]
- The same paper reports de la Torre et al.'s QWK-loss result on DR as QWK 0.537 (validation only, 128×128 images). I did not open the de la Torre paper itself. **[research evidence, secondary]** — [Vargas et al. 2020](https://arxiv.org/abs/1905.13392) [C]
- **Ulcerative colitis endoscopy (LIMUC, 11,276 images, 564 patients, 4 Mayo grades with 6,105 / 3,052 / 1,254 / 865 images)**, mean±SD QWK:

  | Backbone | CE | CORN | MSE | CDW-CE |
  |---|---|---|---|---|
  | ResNet18 | 0.8296 | 0.8366 | 0.8540 | 0.8568 |
  | Inception-v3 | 0.8360 | 0.8431 | — | 0.8678 |
  | MobileNet-v3-L | 0.8302 | 0.8412 | — | 0.8588 |

  With ResNet18, MAE was 0.2581 (CE), 0.2517 (CORN), 0.2346 (plain MSE regression) and 0.2300 (CDW-CE). CORN beat CE by less than 1 SD on most metrics. A simple MSE regression on the class index beat CORN. On the binary remission task, CE scored better than CORN and CO2. The page I read does not state a patient-level split, and no external test set is reported. **[research evidence]** — [Polat, Çağlar & Temizel, ESWA 2025, arXiv 2412.01246v3](https://arxiv.org/html/2412.01246v3) [C]; version read: [D]
- **Knee OA, KL grading**: a 2025 conference paper tested 20 configurations (2 losses × 2 output layers × 5 soft-label schemes). The best was categorical CE + CLM output + beta-distribution soft labels. The abstract page gives no numbers, dataset size or split. **[research evidence, weak]** — [Bérchez-Moreno et al., IWANN 2025](https://dguijo.github.io/publication/berchez-2025-knee) [C]; only the abstract page was opened.
- The **dlordinal** library (PyTorch) collects CLM layers, soft labels (beta, binomial, Poisson, triangular), weighted-kappa loss and ordinal metrics. The arXiv abstract reports no benchmark numbers. **[industry practice]** — [Bérchez-Moreno et al. 2024, arXiv 2407.17163](https://arxiv.org/abs/2407.17163) [D]
- **Unimodal Poisson/binomial outputs** (Beckham & Pal, ICML 2017) and **squared EMD loss** (Hou, Yu & Samaras 2016): I opened only the abstracts. Both claim gains over CE on ordinal image datasets but give no numbers on the abstract pages. **[research evidence, unverified magnitude]** — [Beckham & Pal 2017](https://arxiv.org/abs/1705.05278) [B as ICML; read as D]; [Hou et al. 2016](https://arxiv.org/abs/1611.05916) [D]

**Leakage and external-validation check of the medical studies cited**

| Study | Images / patients | Patient-level split? | External test? |
|---|---|---|---|
| Vargas 2020 (DR) | about 35k pairs train / about 27k test | Yes (validation by patient; official test split) | No |
| Polat 2025 (LIMUC) | 11,276 / 564 | Not stated on the page read | No |
| An 2021 (glaucoma, see Q2) | 954 eyes | Not stated ("eyes", 80/20 stratified ×3) | No |
| Bérchez 2025 (knee) | not stated | Not stated | Unknown |

### Inferences
- **[inference]** The size of the published gains shrinks as the number of classes falls. With 3 classes, "distance" information is minimal: the only ordinal distinction is that a normal↔stage 2 error is worse than an adjacent error. The plausible benefit is mostly fewer off-by-two errors and less fragile training, not higher accuracy.
- **[inference]** The largest "ordinal vs nominal" gaps (Vargas, +0.084 QWK) came from from-scratch CNNs with weak nominal baselines. Gaps against well-tuned pretrained CE baselines were ≤0.03 QWK (Polat). These are a better guide for an ImageNet-pretrained EfficientNet-B0.
- **[inference]** In Polat, plain MSE regression on the class index beat CORN. That supports trying the "single scalar + thresholds" family as a baseline, alongside CORAL and CORN.
- **[inference]** At NOW sample sizes, a true improvement of +0.01–0.03 QWK is far below the sampling noise. My simulation in Q3 gives a 95% range of about ±0.19 QWK for n=56 images, even before accounting for patient clustering. **No method comparison done NOW can show that ordinal beats CE.**

### Gaps
- No reliable evidence found for ordinal vs softmax with ~100 images, with 3 classes, or on phlebitis, pressure-ulcer or wound photos.
- I could not open full text for: the acne severity paper (Wu et al., ICCV 2019, ACNE04; search result only), Nirthika et al. 2020 (DR/prostate QWK loss vs CE; search snippet only), Chen et al. knee OA ordinal loss, the Herlev cervical cytology ordinal losses (Albuquerque et al., PeerJ CS 2021; the 403 error blocked it), and Gleason or pressure-ulcer ordinal studies. Their numbers are **not** used here.
- No calibration comparisons (ECE, Brier) of ordinal heads vs CE were found in the sources I opened. Polat does not report calibration.
- I did not open a systematic review of deep ordinal classification. dlordinal is a software paper, not a review.

---

## Q2. With only 3 classes, is ordinal modelling worth it? Hierarchical decomposition (normal vs phlebitis, then stage 1 vs stage 2)

### Takeaway
With 3 classes, CORN is mathematically the hierarchical decomposition: one task for normal vs phlebitis, and one for stage 2 vs stage 1 among phlebitis cases. It shares the backbone and keeps the outputs consistent, so the "ordinal vs hierarchical" choice mostly collapses to "one shared model vs two separate models". The only verified small-data hierarchical evidence is from one group, on 954 OCT eyes, without patient-level split detail or external testing. For NOW, the decision should be based on the ability to reuse the existing binary task and on interpretability, not on expected accuracy gains.

### Cited Findings
- CORN computes the rank probabilities as a chain of conditionals: task k is trained only on the subset with y > k−1, so P(y>k) = Π P(y>j | y>j−1). It is rank-consistent by construction. The ablation shows that the conditional subsets improve MAE on 3 of 4 datasets vs training all tasks on the full batch (AFAD 2.81 vs 3.06; AES 0.43 vs 0.68; Fireman 0.76 vs 0.81; MORPH-2 2.98 vs 2.93 was the exception). **[research evidence]** — [Shi et al. 2023](https://arxiv.org/abs/2111.08851) [C]
- CORAL uses K−1 binary tasks P(y>k) that share one weight vector and differ only in bias. This guarantees ordered probabilities. The authors attribute CORAL's weaker performance vs OR-NN on balanced MORPH-2 and AFAD to this weight-sharing constraint, which may limit expressiveness. **[research evidence]** — [Cao et al. 2020](https://arxiv.org/abs/1901.07884); [Shi et al. 2023](https://arxiv.org/abs/2111.08851) [C]
- **Hierarchical vs flat on a small medical dataset**: the study used glaucoma OCT with 156 normal eyes and 798 glaucoma eyes across 4 subtypes (954 eyes, single hospital). Pairs of eyes with discordant labels from two specialists were excluded, and the split was 80/20 stratified ×3. The stacked ensemble reached Cohen's κ 0.809 (hierarchical + transfer) vs 0.727 (flat). With 25% of training data (185 images), hierarchical reached κ 0.642 vs 0.546 for flat. The authors note that for single models at small training sizes the hierarchical advantage was not significant. The abstract's "9.7%" is the *smallest* relative gap. Units are "eyes", the paper does not say whether eyes from the same patient were kept in one split, and there is no external test. **[research evidence]** — [An et al. 2021, Sci Rep 11:4250](https://pmc.ncbi.nlm.nih.gov/articles/PMC7921640) [C]
- A celiac-severity hierarchical model (HMIC, same research group) was seen only in search snippets and was not opened. **[gap]**

### Inferences
- **[inference] For K=3, CORN equals a shared-backbone hierarchy.** Task 1 is P(phlebitis) = P(y≥1), trained on all images. Task 2 is P(stage 2 | phlebitis), trained only on the stage 1 and stage 2 images (47 NOW). The class probabilities are P(normal) = 1−p1, P(stage 1) = p1(1−p2) and P(stage 2) = p1·p2. Task 1's output is directly comparable to the existing binary model, so the platform can show a single model's "binary view" and "stage view" without contradictions.
- **[inference] Option H (two separate models)** = the existing binary model plus a new stage 1 vs stage 2 model trained on 47 phlebitis photos.
  - Pros: reuses the validated binary pipeline unchanged; each model can have its own threshold; errors are easy to attribute; the stage model's data (23 vs 24) is balanced.
  - Cons: no shared features; two calibrations; and a "normal" image that reaches the stage model still gets a stage. Gate it: only show a stage when the binary decision is positive.
- **[inference] Option CORN (one model, shared backbone)** gives the same decomposition in one network and needs no new data plumbing. Its task 2 sees only 47 images NOW, the same as Option H.
- **[inference] CORAL with K=3** is a proportional-odds (logit cumulative-link) model: one score with two thresholds. It assumes that one image score moves normal→1 and 1→2 equally. That is plausible if "stage" is a severity continuum (redness, swelling extent). It is less plausible if the normal↔stage 1 boundary depends on different visual cues (subtle erythema) than the 1↔2 boundary (induration, cord or streak). In the second case CORN, Option H or softmax are safer.
- **[inference] Is it worth it NOW?** The cost is small (Q4: one head swap or one extra sklearn model), but no accuracy benefit will be detectable. The legitimate reasons to adopt it NOW are: (a) consistency with the binary task; (b) structurally excluding non-monotone probability profiles; (c) reporting ordinal metrics. Softmax CE stays as the baseline that every ordinal variant must be compared against.

### Gaps
- No study compares hierarchical vs ordinal vs flat on 3 ordered classes with fewer than 100 images.
- No independent replication of the hierarchical-advantage claim was found. The evidence comes from one group (Yokota/Kowsari affiliations in search results).

---

## Q3. Metrics: definitions, pitfalls with 3 classes and tiny test sets, recommended reporting, patient-grouped bootstrap CIs, reporting guidance

### Takeaway
With 3 classes, every ordinal metric comes from three numbers: exact hits, adjacent (off-by-one) errors and normal↔stage 2 (off-by-two) errors. Report them as a confusion matrix with raw counts, plus MAE, off-by-two count, per-class recall and QWK/LWK, each with patient-cluster bootstrap CIs and the number of patients per class. On n≈56 images (14 patients), QWK has a 95% sampling range of roughly 0.41–0.79 even under independence. QWK also changes with class prevalence and can look "substantial" for a model that never predicts stage 1.

### Cited Findings
**Definitions (K=3, classes 0/1/2)**
- QWK = 1 − Σ w_ij·O_ij / Σ w_ij·E_ij, where O is the observed confusion matrix, E is the outer product of the marginals divided by n, and w_ij = (i−j)²/(K−1)². With K=3 the weights are 0 / 0.25 / 1. Linear weights (LWK) are |i−j|/(K−1) = 0 / 0.5 / 1. Vargas et al. use QWK, MAE and 1-off accuracy as the ordinal metrics. **[research evidence]** — [Vargas et al. 2020](https://arxiv.org/abs/1905.13392) [C]
- MAE on the class index = mean |y − ŷ| (the metric used in CORAL, CORN and SORD). **[research evidence]** — [Cao et al. 2020](https://arxiv.org/abs/1901.07884); [Shi et al. 2023](https://arxiv.org/abs/2111.08851)
- **Pitfalls of QWK.** The QWK literature lists sensitivity to the rating scale, the "kappa paradox" (low κ despite high raw agreement), prevalence effects, and dependence on where the agreements sit on the diagonal. It concludes that QWK alone "may not be sufficient". **[research evidence]** — [Doewes, Kurdhi & Saxena 2023, ERIC ED630859](https://files.eric.ed.gov/fulltext/ED630859.pdf) [C]; only the abstract was readable.
- **Reporting guidance.** CLAIM 2024 says to partition data "disjoint at the patient level or higher" (Item 20) and to report the number and qualifications of annotators (Item 16), inter- and intra-rater variability (Item 18), and the uncertainty of performance metrics as SD and/or CIs (Item 29), using bootstrap when CIs cannot be calculated directly (Item 38). It also asks for a description of external testing data, or a justification when there is none (Item 33). CLAIM does not mention ordinal outcomes. **[research evidence / standard]** — [Tejani et al. 2024, Radiol Artif Intell 6(4):e240300](https://pmc.ncbi.nlm.nih.gov/articles/PMC11304031) [A]
- TRIPOD+AI (BMJ 2024) replaces TRIPOD 2015 and refers clustered-data studies to TRIPOD-Cluster. In the parts I could read, I found no item text on ordinal or multicategory outcomes or on multiple observations per participant. **[research evidence / standard]** — [Collins et al. 2024, BMJ 385:e078378](https://www.bmj.com/content/385/bmj-2023-078378) [A]

**Own simulation (local Python, 2026-10-31). Not published evidence.** I assumed a moderate model whose row-conditional confusion (true → predicted) is [[.70,.25,.05],[.15,.65,.20],[.05,.25,.70]] and drew 3,000 i.i.d. test sets with the given class counts (mean, 2.5–97.5 percentiles). **[inference]**

| Test set | QWK | LWK | MAE | Off-by-two rate | Accuracy |
|---|---|---|---|---|---|
| NOW pooled, 9/23/24 (n=56) | 0.62 (0.41–0.79) | 0.55 (0.37–0.72) | 0.35 (0.21–0.50) | 0.03 (0–0.09) | 0.68 (0.55–0.80) |
| One CV fold, about 3/8/8 (n=19) | 0.61 (0.26–0.89) | 0.54 (0.22–0.85) | 0.35 (0.11–0.58) | 0.03 (0–0.11) | 0.68 (0.47–0.90) |
| Balanced, 19/19/18 (n=56) | 0.67 (0.49–0.82) | 0.60 (0.42–0.76) | 0.35 (0.21–0.50) | 0.03 (0–0.09) | 0.68 (0.55–0.80) |
| FUTURE test, 67/67/66 (n=200) | 0.68 (0.58–0.76) | 0.60 (0.51–0.69) | 0.35 (0.28–0.43) | 0.03 (0.01–0.06) | 0.68 (0.62–0.75) |

- **Prevalence dependence (same model, population values) [inference]:** QWK 0.618 at NOW prevalence (16/41/43%), 0.675 when balanced, and 0.588 at 60/30/10%. Accuracy stays about 0.68 in all three. So QWK computed NOW and QWK computed on the FUTURE balanced set **are not comparable**, even for an identical model.
- **Middle-class blind spot [inference]:** on the NOW labels, a model that *never predicts stage 1* (sends every stage 1 to stage 2, with the extremes correct) gets QWK 0.665, accuracy 0.59, MAE 0.41 and zero off-by-two errors. A QWK of 0.67 would conventionally read as "substantial" while one class is never output. This is why per-class recall and the confusion matrix are mandatory.

### Inferences
- **[inference] Identities for K=3:** MAE = (n_off1 + 2·n_off2)/n; adjacent (1-off) accuracy = 1 − n_off2/n. MAE and adjacent accuracy carry no information beyond the confusion matrix. Report the matrix with counts and treat the scalars as summaries.
- **[inference] Recommended reporting per run.** Report:
  - the 3×3 confusion matrix (counts) and the number of patients contributing to each true class;
  - per-class recall (sensitivity for each stage) and balanced accuracy;
  - MAE;
  - the off-by-two count with an exact (Clopper-Pearson) or Wilson interval;
  - QWK and LWK as secondary measures, with a note that they are prevalence-dependent;
  - for the binary view (normal vs any phlebitis, i.e. task 1), the existing metrics (normal false-positive rate, etc.).

  The headline should be MAE plus the matrix, not QWK.
- **[inference] Off-by-two count with zero events:** with 0 errors in n i.i.d. images, the 95% upper bound is about 3/n (rule of three): 5.4% for n=56 and 1.5% for n=200. Clustering by patient widens this. Only 9 NOW images are normal, so normal → stage 2 errors can be estimated from only 9 images.
- **[inference] Patient-grouped (cluster) bootstrap.** Pseudo-code for `src/eval`, or wherever the existing Wilson/bootstrap CIs are computed:
  ```python
  # y, yhat: arrays per image; pid: patient id per image (pooled out-of-fold predictions)
  pids = np.unique(pid); B = 2000; rng = np.random.default_rng(seed)
  stats = []
  for b in range(B):
      draw = rng.choice(pids, size=len(pids), replace=True)            # resample PATIENTS
      idx = np.concatenate([np.where(pid == p)[0] for p in draw])      # keep all photos of each drawn patient
      if len(np.unique(y[idx])) < 3: continue                           # QWK undefined/unstable; count & report skips
      stats.append(metric(y[idx], yhat[idx]))                           # MAE, QWK, off2 count, per-class recall
  ci = np.percentile(stats, [2.5, 97.5]); report n_skipped
  ```
  Caveats [inference]: (1) With only 14 clusters, percentile bootstrap CIs are themselves unreliable and probably too narrow. Label them "approximate" and also report the per-fold spread and/or leave-one-patient-out results. (2) Use pooled out-of-fold predictions from patient-level StratifiedGroupKFold. Never bootstrap images from one patient into both train and test. (3) Report how many bootstrap replicates lacked a class.
- **[inference] Comparing two methods:** use a *paired* patient bootstrap of the difference (same resampled patients for both models) and report the CI of ΔMAE and Δoff-by-two. Given the table above, differences smaller than about 0.15 MAE are not resolvable NOW.

### Gaps
- I found no published guideline (TRIPOD+AI or CLAIM) with specific advice on ordinal outcomes or on QWK vs MAE.
- The Applied Soft Computing 2023 study on weighted kappa for ordinal classifier evaluation (S1568494623000388) returned 403 and was not read. Its recommendation of quadratic-weighted AC2 is from a search snippet only and is not used.
- No published small-sample (n<100) coverage study of cluster-bootstrap CIs for QWK was found.

---

## Q4. Implementation: coral-pytorch, CORN, swapping heads on EfficientNet-B0 and DINOv2+sklearn, costs, class weights

### Takeaway
All candidate heads change only the last layer (1,280→2 or 3 outputs) or the loss and target encoding. The backbone dominates GPU memory and time, so cost is unchanged from the current softmax runs. On DINOv2 features, `mord.LogisticAT` (sklearn API, L2 penalty, `sample_weight`) is the practical ordinal logistic model. `statsmodels.OrderedModel` is unpenalised and needs strong dimensionality reduction at n=56. In coral-pytorch, CORAL accepts per-*task* importance weights. CORN's loss has no weight argument, so imbalance must be handled by sampling or a custom weighted loss.

### Cited Findings
- coral-pytorch API:
  - `coral_loss(logits, levels, importance_weights=None, reduction='mean')`, where logits and levels are shaped (n, K−1) and `importance_weights` is shaped (K−1,), i.e. per binary task, not per class.
  - `corn_loss(logits, y_train, num_classes)`, where logits are (n, K−1) and labels are integers. There is no weighting argument.
  - Class wrappers `CoralLoss` and `CornLoss`.
  - Dataset helpers `levels_from_labelbatch(labels, num_classes)` → (n, K−1), `proba_to_label(probas)` and `corn_label_from_logits(logits)` → (n,). The docstring says logits are (n, n_classes), which is inconsistent with the (n, K−1) shape used by `corn_loss`; check against the source.
  - The package has a `CoralLayer` (layers subpackage; signature not opened).

  **[industry practice]** — [coral-pytorch docs: losses](https://raschka-research-group.github.io/coral-pytorch/api_subpackages/coral_pytorch.losses/), [dataset](https://raschka-research-group.github.io/coral-pytorch/api_subpackages/coral_pytorch.dataset/), [home](https://raschka-research-group.github.io/coral-pytorch/) [A]
- CORN paper hyperparameters (ResNet-34): Adam, 200 epochs, LR 5e-4, batch 256 (CORN: batch 16), best epoch chosen on validation MAE. The supplement for VGG16 on AES used CORN LR 5e-5 with batch 32–64. **[research evidence]** — [Shi et al. 2023](https://arxiv.org/abs/2111.08851) [C]
- SORD: soft target y_i = exp(−φ(r_t, r_i)) / Σ_k exp(−φ(r_t, r_k)), with φ = |r_t − r_i|. It trains with a KL/CE loss on an unchanged softmax head and decodes with argmax or the expected value Σ r_k·p_k. The paper used SGD with momentum 0.9, LR 1e-4 to 1e-3, batch 32 and ≤50 epochs. **[research evidence]** — [Díaz & Marathe 2019](https://openaccess.thecvf.com/content_CVPR_2019/papers/Diaz_Soft_Labels_for_Ordinal_Regression_CVPR_2019_paper.pdf) [B]
- CLM output layer: one projection plus ordered thresholds with a logit, probit or complementary log-log link. The code is the ayrna `deep-ordinal-clm` repository and the dlordinal library. **[research evidence]** — [Vargas et al. 2020](https://arxiv.org/abs/1905.13392) [C]; [dlordinal](https://arxiv.org/abs/2407.17163) [D]
- CDW-CE: a distance-weighted CE with a power α (best 5–7) and a margin m (0.0025–0.05), tuned per backbone. **[research evidence]** — [Polat et al. 2025](https://arxiv.org/html/2412.01246v3) [C/D]. I did not transcribe the exact equation; verify it against the paper before implementing.
- mord source code:
  - `LogisticAT`, `LogisticIT` (`alpha=1.0, verbose=0, max_iter=1000`) and `LogisticSE`.
  - `fit(X, y, sample_weight=None)`. Labels must be consecutive integers; gaps raise an error.
  - L2 penalty `alpha·0.5·‖w‖²` on the weights only, not the thresholds. Thresholds are constrained to stay ordered. Optimiser: L-BFGS-B.
  - `predict_proba` returns (n, K). `score` returns −MAE for AT and accuracy for IT.
  - Docs version 0.3 (©2015). The repository shows 92 commits and no releases listed.

  **[industry practice]** — [mord threshold_based.py](https://raw.githubusercontent.com/fabianp/mord/master/mord/threshold_based.py) [A, source]; [mord docs](https://pythonhosted.org/mord/); [GitHub](https://github.com/fabianp/mord)
- `statsmodels` `OrderedModel(endog, exog, offset=None, distr='probit'|'logit')`:
  - exog must have no constant; a constant raises a ValueError.
  - `predict` returns per-category probabilities.
  - The documentation calls the model "experimental" and does not mention regularisation.

  **[industry practice]** — [statsmodels OrderedModel](https://www.statsmodels.org/stable/generated/statsmodels.miscmodels.ordinal_model.OrderedModel.html) [A]
- In the project code, the EfficientNet head is built in `02_主程式碼/src/workbench/adapters.py` (around line 162, `efficientnet_b0(weights=None)`), the loss in the same file (around line 267, `torch.nn.CrossEntropyLoss(weight=weights)`), and the DINOv2 classifier in the same file (around line 461, `LogisticRegression(`). Patient-level folds are in `src/data/dataset.py` (around line 411) and `src/data/holdout.py` (around line 138). These locations come from a grep of the repository on 2026-10-30.

### Inferences
**Method cards.** Evidence strength refers to the 3-class small-data setting. All cards are **[inference]** unless they cite a source.

**A. Softmax CE (baseline, keep it)**
- Evidence: the strong default. It was competitive in the CORN text and tabular tasks and in Polat's binary task.
- Benefit: reference point. Always run it.
- Minimum data: none beyond the current setup.
- Code: current.
- Cost: current.
- Risk: off-by-two errors are not penalised more than adjacent ones.

**B. CORN (preferred ordinal head; equals the shared-backbone hierarchy at K=3)**
- Evidence: moderate in general (large benchmarks), weak for K=3 and small n.
- Expected benefit NOW: consistency with the binary task. No measurable accuracy gain expected.
- Code, in `adapters.py`:
  ```python
  # head: replace model.classifier[1] = nn.Linear(1280, 3) with
  model.classifier[1] = nn.Linear(1280, K-1)                          # K=3 -> 2 logits
  # loss (train loop, replacing CrossEntropyLoss):
  loss = corn_loss(logits, y, num_classes=K)                           # from coral_pytorch.losses
  # imbalance: corn_loss has no weight arg -> use WeightedRandomSampler, or custom:
  #   task0 = BCEWithLogits(logits[:,0], (y>0).float(), pos_weight=n_normal/n_phleb-ish)
  #   m = y>0; task1 = BCEWithLogits(logits[m,1], (y[m]>1).float())
  # inference decoding:
  p = torch.sigmoid(logits).cumprod(dim=1)                             # [P(y>0), P(y>1)]
  probs = torch.stack([1-p[:,0], p[:,0]-p[:,1], p[:,1]], 1)            # class probabilities
  yhat = (p > 0.5).sum(1)                                              # == corn_label_from_logits
  binary_score = p[:,0]                                                # phlebitis-vs-normal view
  ```
- Hyperparameters: keep the current fine-tuning LR. The paper used 5e-4 with Adam from scratch-trained heads and 5e-5 for pretrained VGG, so a sweep of 1e-5 to 5e-4 is reasonable. Use batch 16–32 and early stopping on validation MAE within the training folds.
- Decoding thresholds: 0.5 by default. Moving the task 0 threshold is how the normal false-positive rate is tuned, so it must be chosen inside the CV folds, never on test.

**C. CORAL / CLM-logit (proportional odds; "single scalar + 2 thresholds")**
- Evidence: moderate in general. CORAL was worse than CE on Fireman and worse than OR-NN on balanced data.
- Use it only if a severity-continuum assumption is believed.
- Code: `nn.Linear(1280, 1, bias=False)` plus 2 biases (`CoralLayer`). Loss: `coral_loss(logits, levels_from_labelbatch(y, K), importance_weights=w)`. Decode with `(sigmoid(logits) > 0.5).sum(1)`.
- `importance_weights` re-weights the two cumulative tasks (e.g. up-weight the y>0 task), not individual classes. For per-class imbalance use a sampler.
- **Single scalar + thresholds (regression variant):** a 1-output head trained with MSE on y ∈ {0,1,2}. Decode by rounding, or with 2 cut-points tuned on validation folds. This was competitive in Polat (MSE beat CORN).

**D. SORD / unimodal soft labels**
- Evidence: moderate in general (CVPR); gains about 2 accuracy points on 5–8 classes. Nothing for K=3.
- Code: no head change. Replace the one-hot targets in the CE loss with soft targets computed from distances to the true class:
  ```python
  T = torch.tensor([[0.,1,2],[1,0,1],[2,1,0]])
  soft = torch.softmax(-alpha*T[y], dim=1)
  loss = -(soft * log_softmax(logits)).sum(1).mean()
  ```
- With alpha=1, the soft target for a stage 2 image is [0.090, 0.245, 0.665], and for stage 1 it is [0.212, 0.576, 0.212]. That is heavy smoothing for 3 classes. Sweep alpha over {1, 2, 3, 5}; at alpha=2 the stage 2 target becomes [0.016, 0.117, 0.867]. Class weights can multiply the per-sample loss as before.
- Risk: the equal-spacing assumption between normal→1 and 1→2. This can be relaxed with an asymmetric distance matrix, but that adds a hyperparameter you cannot tune at n=56.

**E. Squared EMD / CDF loss**
- Evidence: weak, since only the abstract was read.
- My own definition (not transcribed from Hou et al.): `loss = ((cumsum(softmax(logits))[:, :K-1] - cumsum(onehot(y))[:, :K-1])**2).sum(1).mean()`.
- With K=3, this penalises an off-by-two error 4× an adjacent error in squared-CDF terms (an adjacent error moves one CDF entry, an off-by-two moves both).
- Usually combined with CE (e.g. CE + λ·EMD², λ ∈ [0.1, 1]) for stable early training. This is my inference, not verified.

**F. CDW-CE**
- Evidence: one medical study (4 classes, 11k images), where it was the best in its own paper.
- It has 2 extra hyperparameters (α, margin) that cannot be tuned reliably NOW.
- Status: FUTURE only.

**G. DINOv2-small frozen features (384-d CLS) + ordinal linear model**
```python
from sklearn.pipeline import make_pipeline; from sklearn.preprocessing import StandardScaler
import mord
clf = make_pipeline(StandardScaler(), mord.LogisticAT(alpha=a))                  # y in {0,1,2}
# alpha sweep: logspace(-2, 3); choose by inner StratifiedGroupKFold on MAE
clf.fit(X_tr, y_tr, logisticat__sample_weight=w_tr)                              # class weights via sample_weight
P = clf.predict_proba(X_te)   # (n,3)
```
- Hierarchical alternative: two `sklearn LogisticRegression` models (all images: y>0; phlebitis-only: y==2).
- statsmodels `OrderedModel(distr='logit')` is only usable after PCA to about 3–10 components. With 384 unpenalised features and 56 samples, the MLE is non-identifiable or perfectly separated. Use it for inference-style summaries, not prediction.
- Cost: well under a second per fit on CPU at n≈120 × 384, versus the feature extraction that the platform already caches.

**GPU memory and time**
- An EfficientNet-B0 classifier has about 5.3M parameters. The head swap changes the final Linear from 1280×3 + 3 = 3,843 to 1280×2 + 2 = 2,562 (CORN) or 1,280 + 2 (CORAL) parameters, under 0.1% of the model.
- The losses are O(n·K) elementwise operations on batch-size×≤3 tensors. Activation memory and FLOPs are set by the backbone at 224², so **VRAM and epoch time are the same as the current softmax runs to within measurement noise**. This is my reasoning, not a benchmark.
- On the DINOv2 path, mord adds about 0 GPU cost.

**Class weights and imbalance**
- CE: `weight=` per class (current).
- SORD/EMD: multiply the per-sample loss by w[y].
- CORAL: per-task `importance_weights` plus a sampler.
- CORN: a sampler or the custom weighted BCE above.
- mord: `sample_weight`.
- Always compute weights inside each training fold.

**How to validate on the platform (all variants)**
- Same patient-level StratifiedGroupKFold folds and seeds as the CE baseline.
- Pooled out-of-fold predictions; the Q3 metric set; paired patient bootstrap of differences.
- Report negative and null results. A human reviews the results before any model is registered (no auto-deploy).
- Add a unit test that the CORN/CORAL decoded probabilities are monotone, sum to 1, and that `yhat ∈ {0,1,2}`.

### Gaps
- I did not open the `CoralLayer` signature page or the coral-pytorch changelog or version. Check `pip show coral-pytorch` locally before pinning a version.
- I did not verify whether statsmodels `OrderedModel.fit` supports weights or penalties beyond what its class page shows.
- No measured GPU benchmarks for these heads were found. The cost statement is reasoning only.

---

## Q5. Label noise at stage boundaries (single annotator; filename-rule-derived hospital labels): do ordinal or soft labels help?

### Takeaway
There is a plausible rationale and some indirect evidence that distribution-type soft labels degrade less than CORAL under synthetic adjacent-biased noise. I found no clean evidence that soft or ordinal labels beat plain CE under realistic, systematic noise such as filename rules, and none at small n. The bigger lever NOW is auditing the labels: a second rater on a sample, and a check of the filename rules against the images.

### Cited Findings
- ORDAC (preprint) used Adience (about 26k images, 8 classes) and DR (over 88k images, 5 grades), with synthetic asymmetric noise whose flip probability decays with rank distance (τ = 0.2, 0.4) and a clean test set. Macro-MAE:
  - Adience: CORAL 0.8349 → 1.0427 vs DLDL-v2 (label-distribution soft targets) 0.7618 → 0.8649, at τ = 0.2 → 0.4.
  - DR: CORAL 0.8403 / 0.8595 vs DLDL-v2 0.8025 / 0.8488.
  - Their correction method reached 0.6463 / 0.7192 on Adience.

  There is no plain-CE or SORD baseline in the main table, so the paper does not isolate soft labels vs CE. **[research evidence]** — [Sedighi Moghaddam & Mohammadi 2025, arXiv 2509.02351v2](https://arxiv.org/html/2509.02351v2) [D]
- CLAIM 2024 asks for the number and qualifications of annotators and the methods used to measure inter- and intra-rater variability (Items 16 and 18). **[standard]** — [Tejani et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11304031) [A]
- An et al. excluded images where two specialists disagreed. That is a label-quality step a single-annotator dataset cannot reproduce. **[research evidence]** — [An et al. 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC7921640) [C]

### Inferences
- **[inference]** Filename-rule labels give *systematic* noise (e.g. a whole hospital folder labelled stage 2, or a date-based rule), not the random adjacent flips that soft-label papers simulate. Soft labels cannot fix systematic bias. They only reduce over-confidence near boundaries.
- **[inference]** Where noise is truly adjacent (normal↔1, 1↔2 judgement calls), SORD with moderate alpha (2–3) and CORN/CORAL are reasonable and cheap hedges. Do not claim robustness without a test. The minimum test: re-label a random 20–30% sample blind (second rater, or the same rater ≥2 weeks later), report weighted κ between the labels, and report model performance against both label sets.
- **[inference]** Hospital (filename-labelled) and LINE (manually reviewed) photos differ in both label process and image domain. Report metrics stratified by source, so that label noise and domain shift are not mixed together.
- **[inference]** The model must not be used to "correct" labels automatically. Any model-suggested relabel goes through human confirmation, in line with the project principle of no fabricated labels.

### Gaps
- No study of ordinal or soft labels vs CE under realistic annotator noise with fewer than 1,000 images was found.
- Garg & Manwani (ACML 2020, noise-robust ordinal losses) and the lung-nodule URL paper were seen only in search snippets and were not opened or used.

---

## Q6. NOW (normal 9 / stage 1 23 / stage 2 24; 14 patients) vs FUTURE (about 1,000 balanced) recommendations

### Takeaway
**NOW:** keep softmax CE (class-weighted) as the reference. Add CORN as an effectively free head swap, or keep the two-model hierarchy (existing binary model plus a stage 1 vs 2 model on 47 images) on DINOv2+LR. Add `mord.LogisticAT` as the ordinal linear baseline. The main value NOW is better *reporting* (confusion matrix, MAE, off-by-two count, patient bootstrap) and label auditing; no method can be shown to be better. **FUTURE:** run a pre-registered comparison of CE vs CORN vs SORD (vs CDW-CE) across 5 seeds × patient-grouped CV. Expect differences of at most a few hundredths of QWK, and judge them on patient-level paired CIs.

### Cited Findings
- The verified gains of ordinal over CE in medical grading with 4–5 classes and ≥11k images are QWK +0.007 to +0.011 for CORN and +0.027 to +0.032 for CDW-CE (LIMUC), and +0.084 for CLM+QWK loss against a weak from-scratch CE (DR). **[research evidence]** — [Polat et al. 2025](https://arxiv.org/html/2412.01246v3); [Vargas et al. 2020](https://arxiv.org/abs/1905.13392)
- Hierarchical classification beat flat with 185 to 739 training images (κ 0.642 vs 0.546 at 25%; 0.809 vs 0.727 at 100%) in one single-centre OCT study without patient-split detail or external testing. Single-model gains were not significant at small sizes. **[research evidence]** — [An et al. 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC7921640)
- My own simulation (Q3): at n=56 the 95% range of MAE is about 0.21–0.50; at n=200 it is about 0.28–0.43, before patient clustering. **[inference]**

### Inferences
**NOW (research prototype; 14 patients)**

| Method | Evidence strength (K=3, small n) | Expected benefit NOW | Worth doing NOW? | Min. data (inference) | Cost |
|---|---|---|---|---|---|
| Softmax CE + class weights | baseline | — | Yes (reference) | current | current |
| CORN head (= shared hierarchy) | weak | Consistent binary and stage views; no detectable accuracy gain | Yes, as an ablation | current | same as CE |
| Two-model hierarchy (binary + stage 1 vs 2) | weak (one study) | Reuses validated binary model; stage model balanced 23/24 | Yes, on DINOv2+LR (cheapest) | current | trivial |
| CORAL / proportional odds / mord LogisticAT | weak | One severity score; monotone | Yes, on DINOv2 (mord) only | current | trivial |
| SORD soft labels | weak | Possible calibration and boundary smoothing | Optional (alpha=2–3, fixed a priori, not tuned) | current | same as CE |
| EMD², CDW-CE | very weak / one study | Hyperparameters cannot be tuned | **No** (defer) | about several hundred per class, a guess | same as CE |
| statsmodels OrderedModel on 384-d | n/a | Non-identifiable at n=56 | **No** (only after PCA ≤10) | — | trivial |

- Fix alpha, thresholds and epochs *a priori*, or tune them only in inner folds. With 14 patients, any hyperparameter search over ordinal variants risks overfitting to the CV folds. **[inference]**
- Any claim must be worded as "no detectable difference at n=56 images / 14 patients", not as "ordinal is better". **[inference]**

**FUTURE (about 1,000 balanced images; patients grow slowly)**
- Effective sample size is set by *patients*, not photos. Keep patient-level StratifiedGroupKFold, and use a held-out patient group of at least about 20% of patients. Ideally add an external test from a different site or source (CLAIM Item 33). **[standard + inference]**
- Planned comparison: CE vs CORN vs SORD (alpha ∈ {1,2,3}) vs CDW-CE (α ∈ {3,5,7}, margin ∈ {0, 0.025, 0.05}), plus the hierarchy. Use 5 seeds per fold. Primary endpoint: MAE plus off-by-two count. Secondary: QWK/LWK, per-class recall, normal false-positive rate. Run a paired patient bootstrap on the differences. **[inference]**
- Balanced FUTURE data raises QWK mechanically relative to NOW, about +0.05 in my simulation for the same model. Never present that rise as model improvement. **[inference]**
- If a second rater exists by then, report rater–rater weighted κ next to model–rater κ. A model "beating" the inter-rater κ is a red flag for label leakage (e.g. filename cues), not a success. **[inference]**
- GPU: identical to current EfficientNet-B0 fine-tuning. The head and loss changes are negligible (Q4). Five seeds × 3 folds × 4 losses = 60 runs, at the per-run time of the existing CE job. **[inference]**

### Gaps
- There is no empirical basis for a "minimum dataset size" at which ordinal heads start to help. Values in the table are guesses and are labelled as such.
- No phlebitis-specific ordinal grading literature was found in this research round.

### Source register (all questions; access date 2026-10-30 unless noted)
1. Cao W, Mirjalili V, Raschka S. Rank consistent ordinal regression for neural networks with application to age estimation. *Pattern Recognition Letters* 140:325–331, 2020. doi:10.1016/j.patrec.2020.11.008. arXiv:1901.07884v7 (full PDF read). https://arxiv.org/abs/1901.07884 — [C]
2. Shi X, Cao W, Raschka S. Deep neural networks for rank-consistent ordinal regression based on conditional probabilities. *Pattern Analysis and Applications*, 2023. doi:10.1007/s10044-023-01181-9. arXiv:2111.08851v5 (full PDF read). https://arxiv.org/abs/2111.08851 — [C]
3. Díaz R, Marathe A. Soft Labels for Ordinal Regression. *CVPR* 2019, pp. 4738–4747. doi:10.1109/CVPR.2019.00487. https://openaccess.thecvf.com/content_CVPR_2019/papers/Diaz_Soft_Labels_for_Ordinal_Regression_CVPR_2019_paper.pdf (full PDF read) — [B]
4. Vargas VM, Gutiérrez PA, Hervás-Martínez C. Cumulative link models for deep ordinal classification. *Neurocomputing* 401:48–58, 2020. doi:10.1016/j.neucom.2020.03.034. arXiv:1905.13392 (full PDF read). https://arxiv.org/abs/1905.13392 — [C]
5. Polat G, Çağlar ÜM, Temizel A. Class Distance Weighted Cross Entropy Loss for Classification of Disease Severity. *Expert Systems with Applications*, 2025 (journal DOI not shown on the page read). arXiv:2412.01246v3. https://arxiv.org/html/2412.01246v3 — [C] journal / [D] version read
6. Bérchez-Moreno F, Vargas VM, Gómez-Orellana AM, Guijo-Rubio D, Romeo L, Conti E, Gutiérrez PA, Hervás-Martínez C. Knee Osteoarthritis Severity Grading Using Soft Labelling and Ordinal Classification. *IWANN* 2025. doi:10.1007/978-3-032-02725-2_41. https://dguijo.github.io/publication/berchez-2025-knee (abstract page only) — [C]
7. Bérchez-Moreno F, Vargas VM, Ayllón-Gavilán R, Guijo-Rubio D, Hervás-Martínez C, Fernández JC, Gutiérrez PA. dlordinal: a Python package for deep ordinal classification. arXiv:2407.17163, 2024 (v3 2025). doi:10.48550/arXiv.2407.17163. https://arxiv.org/abs/2407.17163 — [D]
8. Beckham C, Pal C. Unimodal probability distributions for deep ordinal classification. *ICML* 2017. arXiv:1705.05278. https://arxiv.org/abs/1705.05278 (abstract only) — [B]
9. Hou L, Yu C-P, Samaras D. Squared Earth Mover's Distance-based Loss for Training Deep Neural Networks. arXiv:1611.05916, 2016. https://arxiv.org/abs/1611.05916 (abstract only) — [D]
10. An G, Akiba M, Omodaka K, Nakazawa T, Yokota H. Hierarchical deep learning models using transfer learning for disease detection and classification based on small number of medical images. *Scientific Reports* 11:4250, 2021. doi:10.1038/s41598-021-83503-7. https://pmc.ncbi.nlm.nih.gov/articles/PMC7921640 — [C]
11. Sedighi Moghaddam A, Mohammadi MR. Ordinal Adaptive Correction: A Data-Centric Approach to Ordinal Image Classification with Noisy Labels. arXiv:2509.02351v2, 2025. https://arxiv.org/html/2509.02351v2 — [D]
12. Doewes A, Kurdhi NA, Saxena A. Evaluating Quadratic Weighted Kappa as the Standard Performance Metric for Automated Essay Scoring. 2023 (EDM proceedings per metadata; ERIC ED630859). https://files.eric.ed.gov/fulltext/ED630859.pdf (abstract readable only) — [C]
13. Tejani AS, Klontzas ME, Gatti AA, Mongan JT, Moy L, Park SH, Kahn CE Jr; CLAIM 2024 Update Panel. Checklist for Artificial Intelligence in Medical Imaging (CLAIM): 2024 Update. *Radiology: Artificial Intelligence* 6(4):e240300, 2024. doi:10.1148/ryai.240300. https://pmc.ncbi.nlm.nih.gov/articles/PMC11304031 — [A]
14. Collins GS, Moons KGM, Dhiman P, Riley RD, Beam AL, Van Calster B, et al. TRIPOD+AI statement. *BMJ* 385:e078378, 2024. doi:10.1136/bmj-2023-078378. https://www.bmj.com/content/385/bmj-2023-078378 — [A]
15. coral-pytorch documentation (Raschka Research Group): https://raschka-research-group.github.io/coral-pytorch/ ; losses API https://raschka-research-group.github.io/coral-pytorch/api_subpackages/coral_pytorch.losses/ ; dataset API https://raschka-research-group.github.io/coral-pytorch/api_subpackages/coral_pytorch.dataset/ — [A] (official docs)
16. mord (Pedregosa F.): docs v0.3 https://pythonhosted.org/mord/ ; repository https://github.com/fabianp/mord ; source https://raw.githubusercontent.com/fabianp/mord/master/mord/threshold_based.py — [A] (official source/docs)
17. statsmodels `OrderedModel` documentation: https://www.statsmodels.org/stable/generated/statsmodels.miscmodels.ordinal_model.OrderedModel.html — [A]
18. Own simulation script (not a source of evidence; reproducible): `C:/Users/user/AppData/Local/Temp/claude/C--Users-user-Desktop-Phlebitis/6930897b-588f-4662-b316-ec59998130bd/scratchpad/qwk_sim.py`, run 2026-10-31 with the project venv Python, seed 0.

Seen only in search results and **not opened, so not used as evidence**: Wu et al., ICCV 2019 acne LDL (ACNE04); Albuquerque, Cruz & Cardoso, PeerJ CS 2021 (Herlev; 403); Nirthika et al., ICIIS 2020; Chen et al. knee OA ordinal loss; Garg & Manwani, ACML 2020; TRIPOD-Cluster (BMJ 2023); the Applied Soft Computing 2023 weighted-kappa study (403).
