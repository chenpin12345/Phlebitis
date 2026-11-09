# Fine-tuning strategies for very small medical / skin-photo classification datasets (phlebitis project)

Status: COMPLETE (2026-10-31). All web sources accessed 2026-10-30. Grades: [A] official docs/registries/standards; [B] systematic review or top-venue peer-reviewed (ICLR/ECCV/ACL/NeurIPS, Nature-family, NeuroImage); [C] other peer-reviewed (MIDL, MICCAI workshops); [D] preprint; [E] blog/example code/forum. Every conclusion is tagged **(research evidence)**, **(industry practice)** or **(inference)**.

Local facts observed on 2026-10-30 in the project venv (`02_主程式碼/.venv`), relevant to every recommendation below:
- GPU = NVIDIA GeForce RTX 5050 Laptop GPU, ~8.0 GB VRAM (`torch.cuda.get_device_properties`). torch 2.13.0+cu130, torchvision 0.28.0, transformers 4.57.6, scikit-learn 1.9.1, ultralytics 8.4.161. **peft and timm are NOT installed** (LoRA/PEFT needs a local `pip install peft`. That is a package download only, and no photos leave the machine).
- Current code (`02_主程式碼/src/workbench/adapters.py`): `efficient_train()` (l.217) freezes the backbone and optionally unfreezes `model.features[-1]` (l.239–242), uses class weights, AdamW/SGD and `CosineAnnealingLR`. `dino_features()`/`dino_train()` (l.400–465) use **CLS token only** (`last_hidden_state[:, 0]`) + sklearn `LogisticRegression(C=params.get('C',1), class_weight=...)`. Patient-grouped CV is in `src/data/dataset.py` l.379–411 and `src/data/holdout.py` l.108–138 (`StratifiedGroupKFold`).
- Installed transformers 4.57.6 `modeling_dinov2.py`: attention projections are named `query`, `key`, `value` (l.201–203), output `dense` (l.245), MLP `fc1`/`fc2` (l.336–341). `Dinov2ForImageClassification` head = `nn.Linear(hidden_size*2, num_labels)` on `torch.cat([cls_token, patch_tokens.mean(dim=1)])` (l.562–591). Upstream transformers `main` has renamed these to `q_proj/k_proj/v_proj/o_proj` ([GitHub main source](https://raw.githubusercontent.com/huggingface/transformers/main/src/transformers/models/dinov2/modeling_dinov2.py)), so LoRA `target_modules` **must be checked against the installed version** (print `named_modules()`).

---

## Q1. What does research evidence show about linear probe vs PEFT vs full fine-tuning in low-data regimes, and at what sample sizes does the ranking change?

### Takeaway
No study covers this project's exact setting (≈120 smartphone skin photos from 14 patients). The nearest studies point one way. Below roughly 5–20 images per class, a linear probe on frozen features from a strong pretrained backbone is the most reliable choice. A fully fine-tuned small CNN (ResNet-18) only catches up to within about 0.5 AUROC from around 10–30 images per class. PEFT beats full fine-tuning on dermatology only in data-scaling studies that still use hundreds to thousands of images (HAM10000 at ≤50% of 7,511 images for ViT-B). So the ranking changes somewhere between tens and hundreds of images per class, and the exact point depends on the dataset.

### Cited Findings
- **Kumar A, Raghunathan A, Jones R, Ma T, Liang P. "Fine-Tuning can Distort Pretrained Features and Underperform Out-of-Distribution." ICLR 2022 (oral). arXiv:2202.10054. [B]**
  - Across 10 distribution-shift datasets, full FT gave about +2% ID accuracy but about −7% OOD accuracy versus linear probing (LP).
  - LP-FT (first train the head by LP, then fine-tune everything from that head) beat FT by about +1% ID and +10% OOD. FT is worse OOD "when the pretrained features are good and the distribution shift is large". Mechanism: when the head starts random or fixed, the lower layers get distorted while the head is still being learned.
  - Averages over all datasets: ID FT 85.1 / LP 82.9 / LP-FT 85.7; OOD FT 59.3 / LP 66.2 / LP-FT 68.9.
  - Examples: CIFAR-10→STL OOD FT 82.4 / LP 85.1 / LP-FT 90.7; ImageNet→ImageNet-A FT 27.8 / LP 45.7 / LP-FT 49.1.
  - Recipe: LP = L2-regularised logistic regression on frozen penultimate features, with an L2 sweep chosen on ID validation. FT = cosine schedule, batch 64, sweep of 6 LRs, early stopping, 3 seeds. On ImageNet each LP-FT stage used half the FT epochs.
  - Limits: no low-data experiments of its own (training sets were ~20K to >1M). It cites Kornblith et al. 2019, where LP beat FT with very few examples and FT won once there were more than ~30 examples per class (cited second-hand; Kornblith not opened). LP-FT trailed FT ID on FMoW (51.8 vs 56.5), where the features are weak.
  - (research evidence) — [arXiv abs](https://arxiv.org/abs/2202.10054); [ar5iv full text](https://ar5iv.labs.arxiv.org/html/2202.10054)
- **Woerner S, Baumgartner CF. "Navigating Data Scarcity using Foundation Models: A Benchmark of Few-Shot and Zero-Shot Learning Approaches in Medical Imaging." MICCAI 2024 workshop (MedAGI, oral); arXiv:2408.08058. [C/D]**
  - Setup: 16 foundation models × 19 MedIMeta datasets, including 3 skin datasets (`derm`, `skinl_derm`, `skinl_photo`; the last is clinical skin photos). n = 1, 2, 3, 5, 7, 10, 15, 20, 25, 30 shots per class; 100 random task instances per dataset.
  - Methods: linear probe for the foundation models. Full FT only for ResNet-18/50, because FT of large models is "computationally prohibitive for the majority of practitioners".
  - HP search: Adam was best; LR 1e-5 to 0.1; 5–200 steps. LR 1e-4 with ≥120 steps was near-optimal. A zero-initialised head was as good or better.
  - Harmonic-mean AUROC, CLIP-ViT-H LP vs fine-tuned ResNet-18: n=5 75.6 vs 73.9; n=10 79.1 vs 78.6; n=20 82.5 vs 82.4; n=25 83.8 vs 83.3; n=30 84.6 vs 84.1. BiomedCLIP was best at the smallest n; fine-tuned ResNet-18 beat BiomedCLIP from n≥20.
  - DINOv2-g/14 LP: 64.7 (n=1) and 84.0 (n=30), slightly behind CLIP-ViT-H and BiomedCLIP.
  - Fine-tuned ResNet-18 beat fine-tuned ResNet-50. No SDs are reported, and results varied widely across datasets.
  - (research evidence) — [arXiv HTML](https://arxiv.org/html/2408.08058)
- **Dutt R, Ericsson L, Sanchez P, Tsaftaris SA, Hospedales T. "Parameter-Efficient Fine-Tuning for Medical Image Analysis: The Missed Opportunity." MIDL 2024, PMLR 250. arXiv:2305.08252v4. [C]**
  - Setup: 17 PEFT methods, >700 experiments. Datasets: BreastUS (584 images), HAM10000 (7,511), Fitzpatrick17k (5,809), SMDG (9,852), RSNA Pneumonia (20,412).
  - Average F1 by backbone:

    | Backbone | Full FT | Linear probe | Best PEFT |
    |---|---|---|---|
    | ViT-B (in21k) | 0.84 | 0.74 | LoRA 0.88 |
    | ViT-L | 0.83 | 0.77 | LoRA 0.86 |
    | ViT-H | 0.77 | — | LoRA 0.83 |
    | ResNet50 | 0.77 | 0.72 | SSF 0.85 (~60K params, 0.25%) |

  - The headline "up to 22%" gain is BreastUS: SSF 0.94 vs FT 0.72.
  - HAM10000 data scaling (100% down to 1% = 75 images; 3 seeds):
    - ViT-B: FT is best at 100%. Below about 50%, PEFT beats FT (LoRA by up to +6%).
    - ViT-L: LoRA beats FT from 80% downward. BitFit wins only below 20%.
    - Per-size numbers are only in a figure.
  - HP: AdamW, batch 512, LR tuned per method with Optuna. PEFT preferred an LR about 10× higher than full FT. Epochs and LoRA rank are not stated.
  - Patient- or lesion-level splitting is not described. HAM10000 contains several images per lesion, so leakage risk is not addressed.
  - (research evidence) — [arXiv v4 HTML](https://arxiv.org/html/2305.08252v4); [PMLR](https://proceedings.mlr.press/v250/dutt24a.html)
- **Baharoon M, Qureshi W, Ouyang J, Xu Y, Aljouie A, Peng W. "Towards General Purpose Vision Foundation Models for Medical Image Analysis: An Experimental Study of DINOv2 on Radiology Benchmarks." arXiv:2312.02366v4 (Sep 2024). [D]**
  - Radiology, not skin. Compared kNN, LP, few-shot, PEFT (LoRA, BitFit) and end-to-end FT.
  - Few-shot (linear head on frozen features, 1–16 patients per class; results only in a figure): no clear ranking at 1–4 per class; DINOv2 leads from 8 per class.
  - HP: LoRA r=48, α=16, dropout 0.1, LoRA LR 2e-4, head LR 5e-3. FT backbone LR searched over 5e-4 to 1e-7 (larger models preferred lower LR); batch 32 for ViTs; 10–20 epochs. LP LR grid 1e-1 to 1e-5. GPU: RTX A6000.
  - Splits were made by "systematic sampling"; patient-level grouping is not stated.
  - (research evidence) — [arXiv v4 HTML](https://arxiv.org/html/2312.02366v4)
- **Oquab M, Darcet T, Moutakanni T, et al. "DINOv2: Learning Robust Visual Features without Supervision." arXiv:2304.07193. [D; journal venue not confirmed on the page opened]**
  - ImageNet-1k linear-probe top-1 with frozen features: ViT-S/14 81.1, ViT-B/14 84.5, ViT-L/14 86.3, ViT-g/14 86.5. kNN: 79.0 / 82.1 / 83.5 / 83.5.
  - Full FT adds only about +2 points (ViT-g 86.5→88.5 at 224 px; 86.7→88.9 at 448 px), and the authors call fine-tuning optional.
  - Training ends with a short phase at 518×518. Code and weights are Apache-2.0; ViT-g has ~1.1B params.
  - (research evidence, natural images) — [ar5iv](https://ar5iv.labs.arxiv.org/html/2304.07193)
- **Model cards and docs:**
  - `facebook/dinov2-small` HF model card [A]: Apache-2.0, 22.1M params (F32), safetensors available; "One typically places a linear layer on top of the [CLS] token". — [HF](https://huggingface.co/facebook/dinov2-small)
  - HF DINOv2 docs [A]: patch size 14; default config hidden 768, 12 layers, mlp_ratio 4 (= base); the processor yields 224×224 by default (`[1, 1+256, 768]` for base). — [HF docs](https://huggingface.co/docs/transformers/model_doc/dinov2)
- **Yan S, Yu Z, Primiero C, ..., Kittler H, Soyer HP, Ge Z. PanDerm, "A Multimodal Vision Foundation Model for Clinical Dermatology." arXiv:2410.15038v3 (Apr 2025). [D; Nature Medicine 2025 per the supplementary-file name "41591_2025_3747", not verified on a journal page]**
  - ViT-L, 224 px. The paper states that linear probing performs comparably to full FT overall (Ext. Data Table 37, not in the HTML). Most classification tasks were evaluated by LP only.
  - Matched or beat other models using 5–30% of labels. PAD-UFES-20 (smartphone clinical photos) was +9.0% over the next-best model.
  - HAM10000/BCN20000 used "clean" patient-level splits. External validation on images from 7 centres for melanoma.
  - FT recipe: CE, LR 5e-4, 50 epochs, 10 warm-up.
  - Weight license is not stated in the paper (check the repo before any use).
  - (research evidence) — [arXiv v3 HTML](https://arxiv.org/html/2410.15038v3)
- **Kim HE, Cosa-Linan A, Santhanam N, Jannesari M, Maros ME, Ganslandt T. "Transfer learning for medical image classification: a literature review." BMC Med Imaging 22:69 (2022). DOI 10.1186/s12880-022-00793-7. [B]**
  - 121 eligible studies (PubMed + WoS up to 31 Dec 2020).
  - Approaches used: feature extractor n=38, fine-tuning from scratch (all layers) n=27, hybrid feature extractor + SVM/RF n=7, partial fine-tuning n=3. 46 studies compared approaches, with no consensus winner.
  - The authors' Fig. 6 analysis found fine-tuning all layers did not improve performance.
  - Recommendation: start with a deep CNN as a feature extractor, then unfreeze conv layers top-down with a low LR, and update all layers only if the features do not fit.
  - Limits: ImageNet CNNs only; no ViTs; EfficientNet not discussed.
  - (research evidence, review) — [PMC9007400](https://pmc.ncbi.nlm.nih.gov/articles/PMC9007400/)
- **Jia M, Tang L, Chen B-C, Cardie C, Belongie S, Hariharan B, Lim S-N. "Visual Prompt Tuning." ECCV 2022. arXiv:2203.12119. [B]**
  - VTAB-1k (1,000 training images per task, 800/200 train/val): VPT-deep beat full FT on 20 of 24 tasks, with <1% trainable params. FGVC average: FT 88.54, VPT-deep 89.11, VPT-shallow 84.62.
  - Across 10–80% of FGVC data VPT-deep consistently beat FT. Linear probe and Adapter reverse ranking when more data is available.
  - (research evidence) — [ar5iv](https://ar5iv.labs.arxiv.org/html/2203.12119)

### Inferences
- **Sample-size thresholds.** Synthesising Woerner 2024, Kumar 2022 (citing Kornblith) and Dutt 2024 (inference):
  - Below ~10–20 labelled images per class, frozen features + linear probe should be the default.
  - Around 20–30 per class, a fine-tuned small CNN reaches parity with linear probes, but rarely clearly beats them.
  - In the hundreds to thousands, PEFT ≥ full FT for ViTs until roughly half of a ~7.5K-image dermatology set (~3.7K images). Full FT tends to win only above that.
- **This project NOW.** Normal has only 9 photos from even fewer patients (patient count for normal not given), so it sits deep in the "linear probe" regime (inference).
- **This project FUTURE.** At ~333 per class from few patients, the regime is "LP-FT / PEFT plausibly helps; must be shown on paired folds" (inference).
- **Feature pooling.** Concatenating CLS + mean patch tokens (as the HF head does) is a zero-cost change worth testing against the current CLS-only features. No direct evidence was found for this exact task (inference).

### Gaps
- No study of phlebitis or IV-site photo classification was found. ClinicalTrials.gov NCT07889895 registers a protocol (mobile-phone photos of catheter sites, VIP score ≥2 = phlebitis, deep-learning model) with no results. — [A] [NCT07889895](https://clinicaltrials.gov/study/NCT07889895)
- No primary study compares LP vs LoRA vs FT on <150 clinical skin photos with patient-grouped CV. The per-shot numbers for `skinl_photo` in Woerner 2024 were not extracted (only harmonic means).
- Dutt 2024 per-size numbers exist only in a figure. Its epochs and LoRA rank are not reported.

---

## Q2. Counter-evidence: where PEFT/LoRA or fine-tuning hurt or did not beat linear probing; variance across seeds/folds; leakage in cited studies

### Takeaway
There are several documented cases where fine-tuning or PEFT does not beat a linear probe:
- DINOv2 ViT-L end-to-end FT scored below its linear probe on two chest X-ray benchmarks.
- BitFit tied the linear probe on CheXpert.
- AdaptFormer fell below the linear probe on ViT-L in the MIDL PEFT benchmark.
- VPT lost badly to full FT on MAE/MoCo self-supervised backbones.
- FT loses OOD robustness compared with LP under distribution shift.

Variance is large at n≈100: CV error bars are about ±10%, and fold standard errors underestimate them. Lesion/patient leakage and near-duplicates are documented in the dermatology benchmarks the PEFT papers use, and the PEFT benchmarks themselves do not report patient-level splitting.

### Cited Findings
- **Baharoon et al. 2024 (DINOv2 on radiology).** ViT-L/14 end-to-end FT < LP: NIH 0.717 vs 0.763; CheXpert 0.786 vs 0.821. For ViT-g the reverse held: FT 0.769 vs 0.759 and 0.848 vs 0.818. BitFit 0.817 vs LP 0.818 on CheXpert. LoRA (0.823) and BitFit stayed below full FT for ViT-g. (research evidence) [D] — [arXiv](https://arxiv.org/html/2312.02366v4)
- **Dutt et al. 2024.** AdaptFormer < LP on ViT-L (0.76 vs 0.77). LoRA was the worst method for text-to-image (FID 410 vs full FT 77). Linear probe was the weakest method on ResNet50. Data-scaling results are averaged over only 3 seeds. (research evidence) [C] — [arXiv](https://arxiv.org/html/2305.08252v4)
- **Jia et al. 2022 (VPT).**
  - With self-supervised backbones VPT-deep underperformed full FT: MAE VTAB-Natural 36.02 vs 59.29; MoCo v3 lower on average.
  - Memory (ViT-B/16, Table 12): VPT-deep with p=200 used 25.8 GB peak training memory vs 11.7 GB for full FT. Inference latency was 140.8 vs 69.7 ms/img. So PEFT is not automatically cheaper.
  - (research evidence) [B] — [ar5iv](https://ar5iv.labs.arxiv.org/html/2203.12119)
- **Kumar et al. 2022.** FT ~7% worse OOD than LP on average. On FMoW (weak features) LP-FT trailed FT ID (51.8 vs 56.5), so LP-FT is not universally best. (research evidence) [B] — [ar5iv](https://ar5iv.labs.arxiv.org/html/2202.10054)
- **Howard & Ruder 2018 (ULMFiT ablation).** Discriminative LR made AG worse when combined with gradual unfreezing: error 6.04 vs 5.81. (research evidence, NLP) [B] — [ar5iv](https://ar5iv.labs.arxiv.org/html/1801.06146)
- **Varoquaux G. "Cross-validation failure: Small sample sizes lead to large error bars." arXiv:1706.07581 (2017), published in NeuroImage 180:68–77 (2018).** The journal details come from the search-result listing; only the arXiv page was opened.
  - "eg ±10% for 100 samples".
  - The standard error across CV folds "strongly underestimates" the true error bars.
  - Large variance plus publication filtering can inflate reported accuracies.
  - (research evidence) [B] — [arXiv abs](https://arxiv.org/abs/1706.07581)
- **Bouthillier X, Delaunay P, Bronzi M, ..., Varoquaux G, Vincent P. "Accounting for Variance in Machine Learning Benchmarks." arXiv:2103.03098 (MLSys 2021 submission). [D]** Variance from data sampling, weight initialisation and hyperparameter choice "impact markedly the results". Randomising more sources of variation brings the estimator closer to the ideal one, with a reported 51× compute reduction. (research evidence) — [arXiv abs](https://arxiv.org/abs/2103.03098)
- **Leakage in dermatology benchmarks used by these papers:**
  - Abhishek K, Jain A, Hamarneh G. "Investigating the Quality of DermaMNIST and Fitzpatrick17k Dermatological Image Datasets." Scientific Data 12:196 (2025); arXiv:2401.14497. Documents duplicates, train–test leakage, mislabels and no well-defined test partition in DermaMNIST/HAM10000 and Fitzpatrick17k, and quantifies the effect on benchmarks. Per the search snippet, images of the same lesion appear across splits and a corrected DermaMNIST-C is released; these details were not verified in the abstract. [B] — [arXiv abs](https://arxiv.org/abs/2401.14497)
  - RECOD Titans at ISIC 2017: many near-duplicates within and between ISIC sources distorted internal validation AUCs; they kept near-duplicates in the same split. [D] — [arXiv 1703.04819](https://arxiv.org/pdf/1703.04819) (search snippet only)
  - **Implication:** Dutt 2024 uses HAM10000 and Fitzpatrick17k without a stated lesion-level split, so its low-data PEFT gains could be inflated (inference). PanDerm explicitly used clean patient-level splits and external validation [D/B]. Woerner 2024 and Baharoon 2024 do not state patient-level grouping.
- **Leakage and validation summary for cited small-sample medical studies:**

  | Study | Patient-level split | External validation |
  |---|---|---|
  | Dutt 2024 | not stated | none |
  | Woerner 2024 | not stated (MedIMeta tasks) | none |
  | Baharoon 2024 | not stated | none |
  | PanDerm | yes for HAM10000/BCN20000 | yes (7 centres) |
  | Kim 2022 review | not assessed | n/a |

### Inferences
- **NOW (14 patients).**
  - Any fine-tuning gain smaller than ~10 percentage points of balanced accuracy is not distinguishable from noise (Varoquaux magnitude; Wilson calculations in Q5).
  - Seed and fold variance of a fine-tuned network will likely exceed that of a convex logistic-regression probe. LR on fixed features is deterministic given the split, while the FT result also depends on seed (inference).
  - This alone makes FT/LoRA "not worth it" now unless a gain is very large and consistent across every repeated split (inference).
- **Photo dependence.** Multiple photos per patient (dates, left/right arm) are the same leakage mechanism documented for HAM10000. The project's existing `StratifiedGroupKFold` by patient is the correct guard. Model selection (C, epochs, LR) must also stay inside the training patients (nested or inner grouped split) (inference).

### Gaps
- No reliable evidence found on seed-to-seed SD of LoRA vs LP specifically for <150-image skin datasets.
- The exact leaked-lesion counts in DermaMNIST were not extracted (abstract only).

---

## Q3. Gradual unfreezing (ULMFiT-style) and discriminative learning rates: evidence in vision/medical imaging and typical LR ratios

### Takeaway
The primary evidence comes from NLP. ULMFiT uses an empirical rule of dividing the LR by 2.6 per layer going down, with one layer unfrozen per epoch. Vision and medical evidence is indirect:
- The Kim 2022 review recommends top-down incremental unfreezing at a low LR, as advice rather than a measured comparison.
- Surgical fine-tuning (ICLR 2023) shows that tuning only some layers can match or beat full FT, with the best layers depending on the type of shift.
- The PEFT and DINOv2 papers effectively use a head LR ≥10× the backbone LR.

No controlled study of gradual unfreezing on small skin-photo data was found.

### Cited Findings
- **Howard J, Ruder S. "Universal Language Model Fine-tuning for Text Classification." ACL 2018 (P18-1031), arXiv:1801.06146. [B]**
  - Discriminative FT: first choose the last-layer LR ηᴸ by tuning only the last layer, then use η^{l−1} = η^l / 2.6 for lower layers. The rule was chosen empirically.
  - Gradual unfreezing: unfreeze the last layer and train 1 epoch, then unfreeze the next lower layer, repeating until all layers train to convergence.
  - Slanted-triangular LR (STLR): cut_frac 0.1, ratio 32, η_max 0.01.
  - Classifier ablation, validation error %:

    | Setting | IMDb | TREC-6 | AG |
    |---|---|---|---|
    | Full FT | 6.87 | 6.86 | 5.81 |
    | Full + discr | 5.57 | 6.21 | 5.62 |
    | Last layer only | 6.49 | 16.09 | 8.38 |
    | Freez (gradual unfreezing) | 6.37 | 6.86 | 5.81 |
    | Freez + discr | 5.39 | 5.86 | 6.04 |
    | Freez + discr + stlr | 5.00 | 5.69 | 5.38 |

  - With 100 labelled examples, supervised ULMFiT matched from-scratch training on ~10× (IMDb) or ~20× (AG) more data.
  - (research evidence, NLP/LSTM only) — [ar5iv](https://ar5iv.labs.arxiv.org/html/1801.06146); [arXiv abs](https://arxiv.org/abs/1801.06146)
- **Lee Y, Chen AS, Tajwar F, Kumar A, Yao H, Liang P, Finn C. "Surgical Fine-Tuning Improves Adaptation to Distribution Shifts." ICLR 2023, arXiv:2210.11466. [B]** Tuning a subset of layers matches or beats full FT. For image corruptions (input-level shift), tuning only the first few layers works best. Validated on 7 tasks covering 3 shift types. (research evidence) — [arXiv abs](https://arxiv.org/abs/2210.11466)
- **Kim et al. 2022 review [B].** Recommends incremental top-down unfreezing with a low LR after the feature-extractor stage. The review's evidence is mixed: e.g., Singh et al. found tuning the last FC layers > fine-tuning all layers, while Yu et al. found full retraining of DenseNet201 best. — [PMC9007400](https://pmc.ncbi.nlm.nih.gov/articles/PMC9007400/)
- **Head vs backbone LR ratios used in medical FM studies.**
  - Baharoon 2024: head LR taken from LP (grid up to 1e-1), backbone ≤5e-4; LoRA 2e-4 vs head 5e-3, i.e. a 25× ratio. [D] — [arXiv](https://arxiv.org/html/2312.02366v4)
  - Dutt 2024: PEFT preferred ~10× higher LR than full FT. [C] — [arXiv](https://arxiv.org/html/2305.08252v4)
  - (research evidence for the values used; not ablated)

### Inferences
- **EfficientNet-B0 group structure.** torchvision `model.features` is an `nn.Sequential` (verified in the installed `efficientnet.py` l.313). By the torchvision architecture it has 9 children: stem, 7 MBConv stages, and the final 1×1 conv. Verify with `len(model.features)` (inference).
- **Suggested LR scheme (inference):**
  - Head LR h.
  - `features[8]` and `features[7]` at h/10.
  - Each earlier group divided by 2.6 (ULMFiT ratio), or simply frozen.
- **DINOv2 groups.** Use transformer blocks `encoder.layer[i]` with layer-wise decay (e.g. 0.65–0.85 per block, a common BEiT-style practice; no primary source opened in this session). Since DINOv2 is 12 layers for S/B, 2.6× per block would freeze the bottom layers effectively (2.6^11 ≈ 3.7e4) (inference).
- **NOW.** Gradual unfreezing adds several extra hyperparameters (epochs per stage, number of stages, ratio). On ~80 training images per fold these cannot be tuned without overfitting the validation folds. "Not worth doing" now (inference).
- **FUTURE.** With ~1,000 images, a 2-stage version is a reasonable experiment and equals LP-FT plus a partial unfreeze: (1) LP / head only; (2) unfreeze the last 1–2 stages or blocks with a 10× lower LR (inference).

### Gaps
- No reliable evidence found of a controlled gradual-unfreezing vs single-stage FT comparison on medical or skin images. The 2.6 ratio has never been validated for CNN/ViT vision as far as found.

---

## Q4. Practical recommended configs for EfficientNet-B0 and DINOv2-small/base: NOW (14 patients, ~120 photos, normal 9) vs FUTURE (~1,000 balanced)

### Takeaway
**NOW:**
- Primary: DINOv2 frozen features + L2 logistic regression. Try CLS vs CLS+mean-patch, ViT-S vs ViT-B, and 224 vs 448/518 px.
- Comparator: EfficientNet-B0 frozen backbone + linear head.
- Do not do: full FT, LoRA, VPT, adapters or gradual unfreezing. Normal = 9 photos makes every comparison statistically uninformative.

**FUTURE (~1,000 balanced):**
- Add LP-FT for EfficientNet-B0 (unfreeze last 1–2 stages with a 10× lower LR).
- Add LoRA (r 4–16) or BitFit on DINOv2-S/B.
- Keep the linear probe as the baseline that every method must beat on identical patient-grouped folds.

### Cited Findings
- Parameter and size facts:
  - EfficientNet-B0 torchvision `IMAGENET1K_V1`: 5,288,548 params; 0.39 GFLOPs; 77.692 ImageNet acc@1; 20.5 MB; eval transform resize 256 bicubic → centre-crop 224, ImageNet mean/std. [A] — [torchvision docs](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.efficientnet_b0.html)
  - DINOv2-small: 22.1M params, Apache-2.0, safetensors. [A] — [HF card](https://huggingface.co/facebook/dinov2-small)
- HF PEFT LoRA image-classification guide (ViT-B/16 in21k, Food-101). [A/E] (industry practice) — [HF PEFT docs](https://huggingface.co/docs/peft/main/en/task_guides/lora_based_methods)
  - `LoraConfig(r=16, lora_alpha=16, target_modules=["query","value"], lora_dropout=0.1, bias="none", modules_to_save=["classifier"])` → 667,493 / 86.5M trainable (0.77%).
  - Example run: LR 5e-3, batch 128 × grad-accum 4, fp16, 5 epochs, `load_best_model_at_end=True`.
  - The docs note that "With LoRA-like methods, you can afford to use a higher batch size and learning rate".
  - Variant trainable counts on the same model: LoHa 1.26M; LoKr 116K; AdaLoRA 520K (AdaLoRA needs `update_and_allocate()` every step).
- LR ranges and recipes reported in studies:

  | Setting | Values | Source |
  |---|---|---|
  | Few-shot LP | Adam, LR ~1e-4, ≥120 steps, zero-init head | [Woerner 2024](https://arxiv.org/html/2408.08058) |
  | LoRA on DINOv2 | r=48, α=16, LR 2e-4, head LR 5e-3 | [Baharoon 2024](https://arxiv.org/html/2312.02366v4) |
  | Full FT backbone | ≤5e-4 down to 1e-7, lower for bigger models | [Baharoon 2024](https://arxiv.org/html/2312.02366v4) |
  | PanDerm FT | LR 5e-4, 50 epochs, 10 warm-up | [PanDerm](https://arxiv.org/html/2410.15038v3) |
  | VPT | SGD with base LR grid scaled by batch/256; WD {0.01, 1e-3, 1e-4, 0}; cosine with 10 warm-up epochs; 100 epochs for ViT-B; prompt length {1…200} | [VPT](https://ar5iv.labs.arxiv.org/html/2203.12119) |
  | LP-FT | head initialised from the LP solution, then FT with a sweep of 6 LRs, early stopping, 3 seeds | [Kumar 2022](https://ar5iv.labs.arxiv.org/html/2202.10054) |

### Inferences

**Per-method decision table.** Evidence strength: H = several B-grade sources; M = one B-grade source, or C/D sources that agree; L = indirect or NLP-only.

| Method | Evidence strength | NOW (14 pts / 120 photos / normal 9) | FUTURE (~1,000 balanced) | Minimum data before trying (inference) | Main risks |
|---|---|---|---|---|---|
| Linear probe on frozen features (sklearn LR) | H for few-shot (Woerner, Kumar, DINOv2, PanDerm) | **DO: primary.** Tune C by inner grouped CV only | **DO: baseline** that everything must beat | any | weak features for this domain; threshold instability with 9 normals |
| Frozen backbone + small head (torch, 1-layer or MLP) | M | DO (EfficientNet-B0 comparator); an MLP head adds nothing over LR at this n | DO | any; MLP head only >~30/class | head overfits; BN stats if not kept in eval |
| LP-FT (Kumar) | M (B-grade, not medical/small) | not worth it (no power to detect) | **DO (first FT method to try)** | ~>30 images/class AND >~20 patients/class (inference from Kornblith-via-Kumar, Woerner) | feature distortion if LR too high; seed variance |
| Partial unfreeze last stage/block (= current EfficientNet option) | M (Kim review; surgical FT) | keep as an option, but report as exploratory | DO, combined with LP-FT | as LP-FT | same |
| Gradual unfreezing + discriminative LR | L (NLP) | NOT worth it | optional, only as a 2-stage version | ≥ several hundred | too many HPs to tune on small validation sets |
| LoRA (peft) on DINOv2 | M (Dutt; Baharoon mixed) | NOT worth it | **DO (one config, r 4–16)** | hundreds of images (Dutt crossover in the thousands for full-vs-PEFT; vs LP untested at <100) | target_modules names; still needs activation memory; seed variance |
| BitFit / bias / LayerNorm tuning | M (Dutt: wins only at <20% data; Baharoon: = LP) | not worth it | cheap alternative to LoRA | hundreds | small gains, may equal LP |
| Adapters (AdaptFormer etc.) | M with negative cases (AdaptFormer < LP on ViT-L) | NO | low priority | hundreds+ | can underperform LP |
| VPT / prompt tuning | M (VTAB-1k wins on supervised backbones; fails on MAE/MoCo) | NO | low priority; DINOv2 is self-supervised, where VPT underperformed (inference by analogy) | ~1,000 | memory 2× at long prompts; no confirmed built-in peft support for ViT image classification (not verified) |
| Full fine-tuning | M (B-grade: worse OOD; FT ViT-L < LP on CXR) | NO | only EfficientNet-B0 full FT as an ablation | thousands (Dutt crossover ≈3.7K for ViT-B) | overfitting, OOD loss (smartphone/LINE photos = shift) |

**NOW: concrete config (inference, anchored to the cited ranges):**
- Data:
  - Keep the patient-grouped 3-fold split (`StratifiedGroupKFold`). Repeat it with ≥10 different split seeds, since 3 folds × 14 patients gives very few distinct partitions.
  - Normal photos are few, so check each fold has ≥1 normal *patient* in the test set. Otherwise that fold's normal-FPR is undefined.
- DINOv2 linear probe:
  - Cache features once per backbone and resolution, excluding augmentation.
  - `LogisticRegression(penalty="l2", C ∈ logspace(-3, 2, 11), class_weight="balanced", solver="lbfgs", max_iter=5000)`, with features standardised.
  - Choose C by inner grouped CV over training patients (or fix C=1 a priori to avoid selection noise).
  - Compare CLS vs `concat(CLS, mean(patch))` (matches the HF head; 2×384 dims for S), and ViT-S vs ViT-B.
  - 518 px is the DINOv2 final pretraining resolution (DINOv2 paper). It may help small-lesion visibility; test it, but count it as one more comparison.
- EfficientNet-B0 frozen + linear head:
  - AdamW, LR 1e-3–3e-3 for the head, WD 1e-4–1e-2, batch 8–16, 30–60 epochs, cosine schedule.
  - No early stopping on the test fold. Early-stop only on an inner validation patient split, or fix the epoch count a priori.
  - Keep BN in eval mode. Augmentation: rotation, flips, mild colour jitter for LINE lighting.
- Seeds: ≥5 training seeds per split for torch heads. LR is deterministic per split.
- Do not use TTA or thresholds tuned on test folds.

**FUTURE (~1,000 balanced, ~333/class): concrete config (inference):**
- LP baseline as above (C grid unchanged).
- EfficientNet-B0 LP-FT:
  - Stage 1: head-only, 20–30 epochs at LR 1e-3.
  - Stage 2: unfreeze `features[6:]` (or all) at backbone LR 1e-4–3e-4 and head LR 1e-3, WD 1e-2 (AdamW), 15–30 epochs, cosine with 1–2 warm-up epochs, batch 32.
  - Early stopping on a grouped inner validation split, patience 5–8 epochs, monitoring balanced accuracy.
- DINOv2-S/B LoRA:
  - Settings: r ∈ {4, 8, 16}, α = r…2r, dropout 0.1, targets `["query","value"]` on transformers 4.57.6.
  - LR 1e-4–5e-4 for LoRA, head LR 1e-3–5e-3, WD 0.01–0.05, 10–30 epochs, batch 16–32 at 224 px (smaller at 518), AMP bf16/fp16.
  - Alternative: BitFit (biases only) at LR 1e-3.
- Seeds: 3–5 per split × repeated grouped 5-fold.

**Pseudo-code: where each change goes (inference; target files are the existing modules):**

```python
# ---------- data loading (src/data/dataset.py, workbench/adapters.py::tensor_image) ----------
splitter = StratifiedGroupKFold(n_splits=3 if NOW else 5, shuffle=True, random_state=split_seed)
for split_seed in range(10):               # repeated grouped CV; SAME splits reused by every method
    for tr_idx, te_idx in splitter.split(X, y, groups=patient_id):
        inner = StratifiedGroupKFold(3, shuffle=True, random_state=split_seed).split(
                    X[tr_idx], y[tr_idx], groups=patient_id[tr_idx])   # model selection only on train patients
train_tf = T.Compose([T.RandomResizedCrop(224, scale=(0.7, 1)), T.RandomRotation(20),
                      T.RandomHorizontalFlip(), T.ColorJitter(0.2, 0.2, 0.1), T.ToTensor(), T.Normalize(MEAN, STD)])
eval_tf  = T.Compose([T.Resize(256, interpolation=BICUBIC), T.CenterCrop(224), T.ToTensor(), T.Normalize(MEAN, STD)])

# ---------- (1) Linear probe on cached DINOv2 features (adapters.py::dino_features/dino_train) ----------
with torch.no_grad():
    h = dino(pixel_values=x).last_hidden_state            # [B, 1+N, D]
    feat = torch.cat([h[:, 0], h[:, 1:].mean(1)], dim=1)  # NEW option: CLS + mean-patch (HF head layout)
clf = make_pipeline(StandardScaler(), LogisticRegression(C=C, class_weight="balanced", max_iter=5000))

# ---------- (2) Frozen EfficientNet-B0 + head (adapters.py::efficient_train) ----------
m = efficientnet_b0(weights=None); m.load_state_dict(local_weights)       # local file, no cloud
for p in m.parameters(): p.requires_grad = False
m.classifier[1] = nn.Linear(1280, n_classes)                              # trainable head
m.eval(); m.classifier.train()                                            # keep BN running stats frozen

# ---------- (3) LP-FT + discriminative LR (training loop, stage 2) ----------
m.classifier[1].load_state_dict(head_from_stage1)                         # LP-FT: init head from LP solution
for p in m.features[6:].parameters(): p.requires_grad = True
groups = [{"params": m.classifier.parameters(), "lr": head_lr},
          {"params": m.features[7:].parameters(), "lr": head_lr / 10},
          {"params": m.features[6].parameters(),  "lr": head_lr / 10 / 2.6}]   # ULMFiT ratio, optional
opt = torch.optim.AdamW(groups, weight_decay=1e-2)
# gradual unfreezing (optional, FUTURE only): at epoch e, set requires_grad=True for one more lower group

# ---------- (4) LoRA / BitFit on DINOv2 (needs `pip install peft`, local) ----------
model = Dinov2ForImageClassification.from_pretrained(local_dir, num_labels=3)  # head = Linear(2*D, 3)
print([n for n, _ in model.named_modules() if n.endswith(("query", "value", "q_proj", "v_proj"))])  # check names
cfg = LoraConfig(r=8, lora_alpha=16, lora_dropout=0.1, bias="none",
                 target_modules=["query", "value"],          # transformers 4.57.6; ["q_proj","v_proj"] on newer
                 modules_to_save=["classifier"])
model = get_peft_model(model, cfg); model.print_trainable_parameters()
opt = torch.optim.AdamW([{"params": [p for n, p in model.named_parameters() if "lora_" in n], "lr": 3e-4},
                         {"params": [p for n, p in model.named_parameters() if "classifier" in n], "lr": 3e-3}],
                        weight_decay=0.05)
# BitFit alternative: freeze all; set requires_grad=True for params whose name endswith(".bias") + classifier

# ---------- loss (same for all) ----------
loss = F.cross_entropy(logits, y, weight=class_weights_from_train_fold, label_smoothing=0.0 to 0.1)

# ---------- training-loop guards ----------
scaler/autocast(bf16 or fp16); grad clip 1.0; early stop on INNER val balanced-acc (patience 5-8)
log: split_seed, fold, train_seed, method, per-image prob -> for paired comparison (Q5)

# ---------- inference ----------
model.eval(); probs = softmax(model(eval_tf(img)))          # LoRA: optionally model.merge_and_unload()
save adapters/heads as safetensors; predictions remain suggestions requiring human confirmation
```

**Not worth doing NOW (inference):** full FT of DINOv2; LoRA/adapters/VPT; gradual unfreezing; big MLP heads; HP search beyond a small C grid; 518 px for EfficientNet (it was trained at 224).

### Gaps
- No reliable evidence found for optimal LoRA rank on <1,000 skin photos. The rank values above come from the HF example (16) and Baharoon (48), not small-skin data.
- VPT support in the HF `peft` library for ViT image classification was not verified in this session.
- Layer-wise LR decay values for DINOv2 (0.65–0.85) come from common practice. No primary source was opened.

---

## Q5. How to evaluate whether fine-tuning beats linear probing on such small data, and the minimum data for differences to be detectable

### Takeaway
Compare methods paired: identical patient-grouped splits, repeated across many split seeds, with patient-level aggregation and a patient-level bootstrap. With 14 patients and 9 normal photos, only very large and very consistent differences are detectable. A per-patient sign test needs ≥6 of 6, ≥8 of 9, or ≥12 of 14 non-tied patients favouring one method to reach p<0.05. At ~1,000 images, per-image paired tests could detect ~3–5 pp differences, but only if photos were independent. Clustering by patient raises the requirement substantially.

### Cited Findings
- CV error bars are ~±10% at n=100, and fold-SE underestimates them. (research evidence) [B] — [Varoquaux arXiv](https://arxiv.org/abs/1706.07581)
- Data sampling, initialisation and HP choice all markedly change benchmark outcomes. Randomising more sources of variance improves the estimate of the expected difference. (research evidence) [D] — [Bouthillier 2021](https://arxiv.org/abs/2103.03098)
- Kumar 2022 used 3 seeds per configuration. Dutt 2024 used 3 seeds. Woerner 2024 used 100 random task instances per dataset. (research evidence) — [Kumar](https://ar5iv.labs.arxiv.org/html/2202.10054); [Dutt](https://arxiv.org/html/2305.08252v4); [Woerner](https://arxiv.org/html/2408.08058)

### Inferences
- **Protocol (inference):**
  1. Fix R ≥ 10 repetitions of patient-grouped K-fold (K=3 NOW, K=5 FUTURE). The same split indices are used for all methods.
  2. Run each method with S seeds (S=5 NOW for torch methods, 3 FUTURE).
  3. Save out-of-fold probabilities per image.
  4. Aggregate to patient level (mean probability per patient-visit or per patient).
  5. Compute the paired difference Δ = metric(FT) − metric(LP) per repetition, reporting the distribution (median, 2.5–97.5 percentiles) and P(Δ>0).
  6. Run a patient-cluster bootstrap: resample patients with replacement (≥2,000 resamples) and recompute Δ, giving a CI for Δ.
  7. Declare "FT better" only if the CI lower bound > 0 *and* normal-FPR is not worse.
- **Corrected tests.** Do not use a naive t-test over folds; folds overlap, which is the same underestimation Varoquaux describes. Use the bootstrap or a corrected resampled t-test (inference; no primary source for the correction opened).
- **Wilson 95% CIs** (computed locally, binomial Wilson formula) show the resolution available:

  | Result | 95% CI |
  |---|---|
  | normal specificity 9/9 | 0.70–1.00 |
  | 8/9 | 0.57–0.98 |
  | 7/9 | 0.45–0.94 |
  | 40/47 positives | 0.72–0.93 |
  | 300/333 (FUTURE per class) | 0.86–0.93 |
  | 320/333 | 0.93–0.98 |

  So NOW, one normal photo changes normal-FPR by 11 pp, and CIs span ~30 pp (inference).
- **Exact two-sided sign test over patients where the methods differ** (computed locally). Number of patients needed in one direction for p<0.05:

  | Non-tied patients m | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 |
  |---|---|---|---|---|---|---|---|---|---|
  | Needed in one direction | 6 | 7 | 8 | 8 | 9 | 10 | 10 | 11 | 12 |

  With 14 patients, FT must be better for essentially all patients where the methods disagree (inference).
- **McNemar paired-proportion sample size** (α=0.05 two-sided, power 0.8; standard Connor-type formula, computed locally; assumes independent images):

  | Discordant rate p_d | Difference d | Paired images needed |
  |---|---|---|
  | 0.10 | 3 pp | ≈870 |
  | 0.10 | 5 pp | ≈312 |
  | 0.06 | 3 pp | ≈521 |
  | 0.15 | 5 pp | ≈469 |
  | 0.20 | 10 pp | ≈155 |

  Photos cluster within patients, so multiply by the design effect 1 + (m − 1)·ICC, where m = photos per patient. With m=8 and ICC=0.3, the requirement roughly triples. In the FUTURE scenario, the binding constraint is therefore the **number of patients**, not photos (inference).
- **Minimum detectable (inference):**
  - NOW: only differences of ≳15–20 pp balanced accuracy that hold on nearly every patient could be claimed.
  - FUTURE with ~1,000 photos: ~5 pp differences are detectable only with on the order of ≥100 patients. If patient counts stay low, report the estimate and its CI and do not declare a winner.
- **Reporting.** State that results are internal CV on a single annotator's labels with no external validation. No clinical performance claims (project principle).

### Gaps
- No primary source opened for the corrected resampled t-test (Nadeau & Bengio) or for the McNemar sample-size formula. Both are standard statistics, but treat them as inference here.
- ICC of predictions within patient is unknown for this data. Estimate it from the out-of-fold predictions once available.

---

## Q6. VRAM and time estimates on a single consumer NVIDIA GPU (8–24 GB) for each strategy, ViT-S/B/L and EfficientNet-B0 at 224/518 px

### Takeaway
Published anchors are sparse:
- VPT (ECCV 2022, Table 12) reports ViT-B/16 full FT at 11.7 GB peak training memory (batch size not captured in the extracted text), VPT-deep (p=200) at 25.8 GB, and inference at 0.87 GB.
- Everything else below is parameter and activation arithmetic, explicitly labelled as inference. It should be confirmed with `torch.cuda.max_memory_allocated()` on the project's 8 GB RTX 5050 Laptop GPU.

Key point: LoRA/BitFit save optimizer and gradient memory but **not activation memory**, which dominates at 518 px.

### Cited Findings
- ViT-B/16 (224) training peak memory: full FT 11.7 GB; VPT-deep p=1 10.3 GB; p=200 25.8 GB. Inference peak: full FT 0.87 GB; VPT p=200 1.85 GB. Latency 69.7 vs 140.8 ms/img. [B] — [VPT ar5iv](https://ar5iv.labs.arxiv.org/html/2203.12119)
- Parameter counts:
  - EfficientNet-B0: 5.29M — [torchvision](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.efficientnet_b0.html)
  - DINOv2-S: 22.1M — [HF](https://huggingface.co/facebook/dinov2-small)
  - ViT-B/16 (google in21k): 86.5M — [HF PEFT guide](https://huggingface.co/docs/peft/main/en/task_guides/lora_based_methods)
  - DINOv2-g: ~1.1B — [DINOv2](https://ar5iv.labs.arxiv.org/html/2304.07193)
  - DINOv2 base config: hidden 768, 12 layers, patch 14 — [HF docs](https://huggingface.co/docs/transformers/model_doc/dinov2)
- Baharoon 2024 ran DINOv2 FT/LoRA on RTX A6000 (48 GB class) with batch 32 for ViTs. [D] — [arXiv](https://arxiv.org/html/2312.02366v4)
- Local GPU: RTX 5050 Laptop, ~8.0 GB (observed 2026-10-30).

### Inferences
- **Token counts.** Patch 14 at 224 px → 16×16 = 256 + 1 CLS = 257 tokens. At 518 px → 37×37 = 1,369 + 1 = 1,370 tokens (5.3× more). Activation memory scales roughly linearly with tokens when SDPA/flash attention avoids storing the N×N attention map (default `attn_implementation="sdpa"`); quadratic otherwise (inference).
- **Static memory for training.** With AdamW and fp32 master weights: weights 4 B + grads 4 B + Adam states 8 B = 16 B per *trainable* parameter, plus 4 B (or 2 B in half precision) per frozen parameter (inference):

  | Model (params) | Full FT static | LoRA/BitFit/LP static |
  |---|---|---|
  | EfficientNet-B0 (5.3M) | ≈0.09 GB | ≈0.02 GB |
  | ViT-S (22M) | ≈0.35 GB | ≈0.09 GB |
  | ViT-B (~86M; 12·768² × 12 ≈ 85M from config) | ≈1.4 GB | ≈0.35 GB (0.17 GB fp16) |
  | ViT-L (~300M; 12·1024² × 24 ≈ 302M) | ≈4.8 GB | ≈1.2 GB |

- **Activations per training image.** Mixed precision with SDPA, rough rule ≈ 34 bytes × tokens × hidden × layers, a standard transformer estimate (no primary source opened; inference):

  | Model | 224 px | 518 px |
  |---|---|---|
  | ViT-S | ≈40 MB | ≈0.21 GB |
  | ViT-B | ≈80 MB | ≈0.43 GB |
  | ViT-L | ≈0.21 GB | ≈1.1 GB |

  The same applies to LoRA, because gradients must flow back through all frozen layers above the lowest adapted layer. BitFit behaves the same way.
- **Feasibility on 8 GB (inference; CUDA context + allocator overhead ~0.5–1 GB):**

  | Strategy | ViT-S 224 | ViT-S 518 | ViT-B 224 | ViT-B 518 | ViT-L 224 | ViT-L 518 | EffNet-B0 224 |
  |---|---|---|---|---|---|---|---|
  | LP (cached features, forward only, batch 1–16) | ✓ <1 GB | ✓ ~1 GB | ✓ ~1 GB | ✓ ~1–2 GB | ✓ ~2 GB | ✓ ~2–4 GB (batch ≤4) | ✓ |
  | Frozen backbone + head trained online (no_grad backbone) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ small batch | ✓ |
  | LoRA/BitFit, batch 16, AMP | ✓ ~1.5 GB | ✓ ~4 GB | ✓ ~2 GB | ✗ at batch 16 (~7 GB+); ✓ batch 4 + grad-accum or grad checkpointing | ✓ ~5 GB | ✗ (needs 24 GB or batch 1–2 + checkpointing) | n/a |
  | Full FT, batch 16, AMP | ✓ ~1.5 GB | ✓ ~4 GB | ✓ ~3 GB (VPT table: 11.7 GB at their unspecified batch) | ✗ on 8 GB; borderline on 12–16 GB | ✗ on 8 GB; ✓ 16–24 GB | ✗ (24 GB + checkpointing) | ✓ (EfficientNet activations for batch 32 at 224 are expected to fit; no published number found) |

- **Time (inference; assumes training throughput of a few hundred img/s for EfficientNet-B0/ViT-S at 224 and tens of img/s for ViT-B at 518 on a laptop RTX 5050; MEASURE first):**
  - NOW: each fold trains on ~80 images, so one epoch takes seconds and is dominated by JPEG decode and augmentation. Example for EfficientNet-B0 head training: 10 split seeds × 3 folds × 5 seeds × 50 epochs × 80 images ≈ 0.6 M image-passes, about 0.5–1 h. Feature caching for LP takes about 1 minute per backbone and resolution; the LR fits take seconds.
  - FUTURE: ~800 training images per fold. LP-FT EfficientNet-B0: 5 folds × 3 seeds × 10 repeats × 50 epochs × 800 ≈ 6 M image-passes, several hours to an overnight run. DINOv2-B LoRA at 518 px would be ~5× slower than at 224, so restrict 518 px to the single best configuration.
- **Operational advice (inference):**
  - Use bf16/fp16 autocast, `attn_implementation="sdpa"`, gradient checkpointing (`model.gradient_checkpointing_enable()`) for ViT-B/L, and grad-accumulation for an effective batch of 16–32.
  - Log `torch.cuda.max_memory_allocated()` and seconds/epoch into each experiment record so these estimates are replaced by measurements.
  - All training runs locally. No method above requires cloud services.

### Gaps
- No published per-image activation memory for EfficientNet-B0 or DINOv2 at 518 px on consumer GPUs was found. The VPT 11.7 GB anchor lacks the batch size in the extracted text.
- No published training-throughput numbers for an RTX 5050 Laptop GPU were found. Measure locally.

### Source register (full bibliographic details; all accessed 2026-10-30)
1. Kumar A, Raghunathan A, Jones R, Ma T, Liang P. Fine-Tuning can Distort Pretrained Features and Underperform Out-of-Distribution. ICLR 2022. arXiv:2202.10054. https://arxiv.org/abs/2202.10054 [B]
2. Dutt R, Ericsson L, Sanchez P, Tsaftaris SA, Hospedales T. Parameter-Efficient Fine-Tuning for Medical Image Analysis: The Missed Opportunity. MIDL 2024, PMLR 250. arXiv:2305.08252v4. https://proceedings.mlr.press/v250/dutt24a.html ; https://arxiv.org/html/2305.08252v4 [C]
3. Woerner S, Baumgartner CF. Navigating Data Scarcity using Foundation Models: A Benchmark of Few-Shot and Zero-Shot Learning Approaches in Medical Imaging. MICCAI 2024 MedAGI workshop. arXiv:2408.08058. https://arxiv.org/html/2408.08058 [C/D]
4. Baharoon M, Qureshi W, Ouyang J, Xu Y, Aljouie A, Peng W. Towards General Purpose Vision Foundation Models for Medical Image Analysis: An Experimental Study of DINOv2 on Radiology Benchmarks. arXiv:2312.02366v4, 2024. https://arxiv.org/html/2312.02366v4 [D]
5. Oquab M, Darcet T, Moutakanni T, et al. DINOv2: Learning Robust Visual Features without Supervision. arXiv:2304.07193 (2023). https://ar5iv.labs.arxiv.org/html/2304.07193 [D; venue not confirmed]
6. Yan S, Yu Z, Primiero C, et al., Ge Z. A Multimodal Vision Foundation Model for Clinical Dermatology (PanDerm). arXiv:2410.15038v3 (2025). https://arxiv.org/html/2410.15038v3 [D; Nature Medicine 2025 indicated but not verified]
7. Kim HE, Cosa-Linan A, Santhanam N, Jannesari M, Maros ME, Ganslandt T. Transfer learning for medical image classification: a literature review. BMC Medical Imaging 2022;22:69. DOI 10.1186/s12880-022-00793-7. https://pmc.ncbi.nlm.nih.gov/articles/PMC9007400/ [B]
8. Howard J, Ruder S. Universal Language Model Fine-tuning for Text Classification. ACL 2018 (P18-1031). arXiv:1801.06146. https://ar5iv.labs.arxiv.org/html/1801.06146 [B]
9. Lee Y, Chen AS, Tajwar F, Kumar A, Yao H, Liang P, Finn C. Surgical Fine-Tuning Improves Adaptation to Distribution Shifts. ICLR 2023. arXiv:2210.11466. https://arxiv.org/abs/2210.11466 [B]
10. Jia M, Tang L, Chen B-C, Cardie C, Belongie S, Hariharan B, Lim S-N. Visual Prompt Tuning. ECCV 2022. arXiv:2203.12119. https://ar5iv.labs.arxiv.org/html/2203.12119 [B]
11. Varoquaux G. Cross-validation failure: Small sample sizes lead to large error bars. arXiv:1706.07581 (2017); NeuroImage 2018;180:68–77 (journal details from search listing). https://arxiv.org/abs/1706.07581 [B]
12. Bouthillier X, Delaunay P, Bronzi M, et al., Varoquaux G, Vincent P. Accounting for Variance in Machine Learning Benchmarks. arXiv:2103.03098 (2021). https://arxiv.org/abs/2103.03098 [D]
13. Abhishek K, Jain A, Hamarneh G. Investigating the Quality of DermaMNIST and Fitzpatrick17k Dermatological Image Datasets. Scientific Data 2025;12(1):196. arXiv:2401.14497. https://arxiv.org/abs/2401.14497 [B]
14. RECOD Titans at ISIC Challenge 2017. arXiv:1703.04819. https://arxiv.org/pdf/1703.04819 [D] (search snippet only)
15. Hugging Face PEFT docs, "LoRA methods" task guide. https://huggingface.co/docs/peft/main/en/task_guides/lora_based_methods [A/E]
16. Hugging Face Transformers docs, DINOv2 model page (v5.22.1 docs). https://huggingface.co/docs/transformers/model_doc/dinov2 [A]; transformers main-branch source modeling_dinov2.py https://raw.githubusercontent.com/huggingface/transformers/main/src/transformers/models/dinov2/modeling_dinov2.py [A/E]
17. facebook/dinov2-small model card. https://huggingface.co/facebook/dinov2-small [A]
18. PyTorch torchvision docs, efficientnet_b0. https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.efficientnet_b0.html [A]
19. ClinicalTrials.gov NCT07889895, "AI Prediction of PIVC-Related Phlebitis". https://clinicaltrials.gov/study/NCT07889895 [A]
