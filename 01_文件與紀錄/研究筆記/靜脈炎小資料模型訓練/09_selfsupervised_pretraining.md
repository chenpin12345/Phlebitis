# Self-supervised / domain-adaptive continued pretraining on small unlabeled in-domain image sets (phlebitis IV-site photos)

Scope: whether in-domain SSL (DINO/DINOv2-style continued pretraining, MAE, SimCLR, MoCo v2/v3, BYOL, MICLe, DIET-CP, ExPLoRA) beats a strong generic frozen backbone (DINOv2/DINOv3, SigLIP) + logistic regression when only ~10^2–10^3 unlabeled in-domain photos exist; thresholds; consumer-GPU cost; failure modes; consent/revocation and leakage implications; NOW (~120 labeled photos / 14 patients) vs FUTURE (~1,000 labeled + a few thousand unlabeled).

Access date for every source below: 2026-10-30 (fetched/read that day) unless noted. Source grades: [A] official docs/standards, [B] systematic review or top-venue peer-reviewed, [C] other peer-reviewed, [D] preprint, [E] blog/forum/example code. Claim labels: **research evidence** / **industry practice** / **inference**.

Bibliography (only sources actually opened in this session):
- [B] Azizi S, Mustafa B, Ryan F, Beaver Z, Freyberg J, Deaton J, Loh A, Karthikesalingam A, Kornblith S, Chen T, Natarajan V, Norouzi M. 2021. "Big Self-Supervised Models Advance Medical Image Classification." ICCV 2021 (the opened arXiv page lists no venue; ICCV attribution taken from the task brief, not re-verified). https://arxiv.org/abs/2101.05224 (full PDF v2 read).
- [B] Azizi S, et al. 2023. "Robust and data-efficient generalization of self-supervised machine learning for diagnostic imaging" (REMEDIS). Nature Biomedical Engineering 7:756–779. doi:10.1038/s41551-023-01049-7 (Nature page redirected to login; full text read from preprint arXiv:2205.09723v2 https://arxiv.org/abs/2205.09723v2). Full author list not verified.
- [D] El-Nouby A, Izacard G, Touvron H, Laptev I, Jégou H, Grave E. 2021. "Are Large-scale Datasets Necessary for Self-Supervised Pre-training?" arXiv:2112.10740. https://arxiv.org/abs/2112.10740 (full PDF read).
- [B] Huang S-C, Pareek A, Jensen M, Lungren MP, Yeung S, Chaudhari AS. 2023. "Self-supervised learning for medical image classification: a systematic review and implementation guidelines." npj Digital Medicine 6:74. doi:10.1038/s41746-023-00811-0. https://pmc.ncbi.nlm.nih.gov/articles/PMC10131505/
- [C] Zhou L, Liu H, Bae J, He J, Samaras D, Prasanna P. 2023. "Self Pre-training with Masked Autoencoders for Medical Image Classification and Segmentation." IEEE ISBI 2023 (arXiv v2 = camera-ready). https://arxiv.org/abs/2203.05573 (full PDF read).
- [D] Rodas B, Montesino N, Ambsdorf J, Klindt D, Balestriero R. 2025. "DIET-CP: Lightweight and Data Efficient Self Supervised Continued Pretraining." arXiv:2509.06990. https://arxiv.org/html/2509.06990v1
- [D] Ilse M, Sharma H, Schwaighofer A, Bond-Taylor S, Pérez-García F, et al. 2025. "Data Scaling Laws for Radiology Foundation Models." arXiv:2509.12818. https://arxiv.org/html/2509.12818v1
- [B] Khanna S, Irgau M, Lobell DB, Ermon S. 2025. "ExPLoRA: Parameter-Efficient Extended Pre-Training to Adapt Vision Transformers under Domain Shifts." ICML 2025. https://arxiv.org/html/2406.10973v5
- [C] Gröger F, Gottfrois P, Amruthalingam L, Gonzalez-Jimenez A, Lionetti S, Soenksen-Martinez LR, Navarini AA, Pouly M. 2024. "Towards Scalable Foundation Models for Digital Dermatology." ML4H 2024 Findings. https://arxiv.org/abs/2411.05514 (abstract only).
- [C] Chaves L, Bissoto A, Valle E, Avila S. 2022. "An Evaluation of Self-Supervised Pre-Training for Skin-Lesion Analysis." ISIC Workshop @ ECCV 2022. https://arxiv.org/abs/2106.09229v3 (abstract only).
- [B] Chen T, Kornblith S, Norouzi M, Hinton G. 2020. "A Simple Framework for Contrastive Learning of Visual Representations" (SimCLR). ICML 2020. https://arxiv.org/abs/2002.05709 (full PDF read).
- [B] Chen X, Xie S, He K. 2021. "An Empirical Study of Training Self-Supervised Vision Transformers" (MoCo v3). ICCV 2021. https://arxiv.org/abs/2104.02057 (abstract only).
- [B] Caron M, et al. 2021. "Emerging Properties in Self-Supervised Vision Transformers" (DINO). ICCV 2021. https://ar5iv.labs.arxiv.org/html/2104.14294
- [B] Bourtoule L, Chandrasekaran V, Choquette-Choo CA, Jia H, Travers A, Zhang B, Lie D, Papernot N. 2021. "Machine Unlearning." IEEE S&P 2021. https://ar5iv.labs.arxiv.org/html/1912.03817
- [D] Li Y, Wang N, Shi J, Liu J, Hou X. 2016. "Revisiting Batch Normalization For Practical Domain Adaptation" (AdaBN). arXiv:1603.04779. https://arxiv.org/abs/1603.04779 (abstract only).
- [B] Phuntsho K, Abdullah, Lee K, Lee I, Ahn E. 2026. "Toward Clinically Ready Foundation Models in Medical Image Analysis: Adaptation Mechanisms and Deployment Trade-offs." Artificial Intelligence Review (per arXiv comment). https://arxiv.org/abs/2603.14271 (abstract only).
- [A] facebookresearch/dinov2 README. https://github.com/facebookresearch/dinov2
- [A] LightlyTrain docs, distillation / DINOv2 pretraining. https://docs.lightly.ai/train/stable/methods/distillation.html
- [A] Hugging Face Transformers docs, ViTMAE (v5.22.1). https://huggingface.co/docs/transformers/model_doc/vit_mae
- [E] solo-learn GitHub README. https://github.com/vturrisi/solo-learn
- Project code (read locally 2026-10-30): `02_主程式碼/src/workbench/adapters.py`, `02_主程式碼/src/workbench/external_models.py`, `02_主程式碼/src/data/revocations.py`, `02_主程式碼/requirements.txt`.

---

## Q1. Research evidence: how small can the unlabeled in-domain set be, how big are the gains, and were splits patient-level?

### Takeaway
The flagship medical SSL papers that show clear gains (Azizi 2021, REMEDIS 2023) used **~200k–450k unlabeled dermatology photos** and datacenter TPUs; their in-domain-SSL increment over ImageNet-SSL alone was ~+1–2 % top-1 (derm), and REMEDIS' derm in-distribution gain over a strong supervised baseline was small (top-3 0.923→0.926). The only evidence at the **~1,000-image** scale comes from (a) denoising/masked-image pretraining on target data under full fine-tuning (El-Nouby 2021; Zhou 2023) and (b) the 2025 preprint DIET-CP, which reports sizeable frozen-feature (kNN/linear-probe) gains for DINOv2/DINOv3 on low-resolution MedMNIST with N≈1,000 unlabeled images, but also clear regressions on some datasets. No study found was on IV-site / phlebitis photos.

### Cited Findings
**Azizi et al. 2021 (SimCLR + MICLe; ResNet-50/152)** — research evidence
- Derm SSL set: training-set images "and additional unlabeled images from the same source leading to a total of **454,295 images**" (D_UnlabeledDerm). MICLe used only the 15,340 labeled training cases (1–6 images per case). — [Azizi 2021](https://arxiv.org/abs/2101.05224)
- Derm labeled data: 12,306 patients; 15,340 train / 1,190 val / 4,146 test cases; dev/test split "ensuring no patient overlap"; 27 classes (26 conditions + Other). → patient-level test split **yes** for derm. — [Azizi 2021](https://arxiv.org/abs/2101.05224)
- CheXpert: 224,316 radiographs from 65,240 patients; the authors "randomly re-split the training set into 67,429 training images, 22,240 validation images, and 33,745 test images" → patient-level split **not stated** for CXR (image-level re-split). — [Azizi 2021](https://arxiv.org/abs/2101.05224)
- Gains: ImageNet→Derm SSL vs ImageNet-only SSL **+1.92 ± 0.16 %** top-1; MICLe over SimCLR **+1.18 ± 0.09 %**; best MICLe ResNet-152(2×) 70.02 ± 0.22 % vs supervised ImageNet 63.36 % (the "+6.7 %" headline) and vs BiT-M (ImageNet-21k) 68.45 %; CXR mean AUC 0.7729 vs 0.7625 supervised ImageNet vs 0.7720 BiT. — [Azizi 2021](https://arxiv.org/abs/2101.05224)
- Derm-only SSL (no ImageNet init) was *worse* than ImageNet→Derm (e.g., ResNet-50 4×: 66.93 vs 67.63; with MICLe 67.55 vs 68.81) → "pretraining on ImageNet is likely complementary". — [Azizi 2021](https://arxiv.org/abs/2101.05224)
- External / distribution-shift evaluation: zero-shot on D_ExternalDerm (biopsy-labelled skin cancers, different source) and NIH CXR (112,120 images, 30,805 patients); SSL models generalised better. — [Azizi 2021](https://arxiv.org/abs/2101.05224)
- Compute: derm SimCLR batch 512, LR 0.3, up to 150k steps; CXR best batch 1024, LR 0.5, 100k steps; MICLe batch 128, LR 0.1, 100k steps; 16–64 Cloud TPU cores; "~12 hours to pretrain a ResNet-50 (1×) with batch size 512 and for 100 epochs" on 64 TPU cores. — [Azizi 2021](https://arxiv.org/abs/2101.05224)

**REMEDIS, Azizi et al. 2023** — research evidence
- Derm: "Self-supervised pretraining leveraged a total of **207,032 unlabeled images**"; in-distribution 20,676 cases; OOD set 28,300 cases from Australian skin-cancer clinics (biopsy labels). Fundus unlabeled set 2,287,716 images from 308,507 patients. — [REMEDIS preprint](https://arxiv.org/abs/2205.09723v2)
- Derm in-distribution top-3 accuracy "improved modestly": standard supervised 0.900, strong supervised 0.923, REMEDIS 0.926. Mammography 0.869→0.870 (not significant). Larger gains elsewhere (CXR AUC 0.816→0.833; pathology metastases 0.916→0.954). Headline: up to 11.5 % in-distribution improvement; 1–33 % of OOD labeled data needed to match supervised baselines retrained on all data. — [REMEDIS preprint](https://arxiv.org/abs/2205.09723v2); [Nature BME DOI](https://doi.org/10.1038/s41551-023-01049-7)
- Compute: "using 64 TPU cores, ≈24 hours was needed to pretrain a ResNet-50 (1×) with batch size 1024 for 1000 epochs in a dataset with 200K examples"; up to ~150 h on 256 TPU cores for million-scale sets. — [REMEDIS preprint](https://arxiv.org/abs/2205.09723v2)
- Patient-level splitting of in-distribution sets: not verified in the portions read (paper mentions forming positive pairs "based on patient meta-data" for pathology/mammography/CXR). OOD evaluation is on separate institutions/sources (external validation: yes).

**El-Nouby et al. 2021 (target-only BEiT / SplitMask, ViT)** — research evidence (preprint)
- Smallest target dataset: **Stanford Cars, 8,144 train images**. ViT-S, target-only SplitMask 92.8 % vs supervised ImageNet (DeiT) 92.2 % vs BEiT-ImageNet 92.4 % vs random init 35.3 % (after full fine-tuning, 300 epochs, batch 1024). — [El-Nouby 2021](https://arxiv.org/abs/2112.10740)
- Using 1,000 ImageNet images (1/class) for pretraining gave "+4 points over training from scratch"; peak performance already with ~5 % of ImageNet at fixed number of updates. — [El-Nouby 2021](https://arxiv.org/abs/2112.10740)
- Joint-embedding DINO degrades as pretraining data shrinks (iNat-19 transfer: 78.4 full ImageNet → 73.1 at 10 % → 70.1 at 1 %), while BEiT (75.2/74.5/74.1) and SplitMask (75.4/75.4/74.8) are nearly flat. — [El-Nouby 2021](https://arxiv.org/abs/2112.10740)
- Small sets need very long schedules (10 % ImageNet: ~3k epochs; 1 %: 30k epochs) but overfit: on Stanford Cars "pre-training longer than 5k epochs leads to a severe drop". Compute used: 16 GPUs, batch 2048. — [El-Nouby 2021](https://arxiv.org/abs/2112.10740)
- Caveat: Clipart/Painting/Sketch (34k–52k images) — supervised ImageNet pretraining remained best. — [El-Nouby 2021](https://arxiv.org/abs/2112.10740)

**Zhou et al. 2023 (MAE self pre-training, medical)** — research evidence
- ChestX-ray14 (112,120 CXRs, 32,717 patients, official ~80/20 split): ViT-B/16 MAE self-pretrained 81.5 % mAUC vs supervised ImageNet-1K 80.7 % vs no pretraining 74.4 %. — [Zhou 2023](https://arxiv.org/abs/2203.05573)
- BTCV CT (30 subjects; 18 train / 12 val by subject): MAE self pre-training raised UNETR DSC 78.8 → 83.5 % vs ImageNet-supervised 79.67 % — the "small-scale dataset (N=30)" claim (but 3-D volumes yield many sub-volumes). MAE: LR 1.5e-4, wd 0.05, mask 75 %, 800 epochs (CXR14), 10,000 epochs (BTCV). — [Zhou 2023](https://arxiv.org/abs/2203.05573)
- Patient-level: BTCV split by subject (yes); CXR14 "official split" — whether patient-wise is not stated in the text read; BraTS "randomly split" scans.

**DIET-CP (Rodas et al. 2025)** — research evidence (preprint), closest to our regime
- Continued pretraining with N = 1,000 random unlabeled images (BreastMNIST N = 546); ViT-B DINOv2, DINOv3, MAE; frozen evaluation by kNN and linear probe. — [DIET-CP](https://arxiv.org/html/2509.06990v1)
- Medical average F1 (MedMNIST subsets incl. DermaMNIST, 3 runs): DINOv2 kNN 53.06 → 70.82, linear probe 71.52 → 76.33; DINOv3 LP 74.77 → 79.20; MAE LP 60.60 → 68.98. — [DIET-CP](https://arxiv.org/html/2509.06990v1)
- Ablation on DINOv2 ViT-S: 1,000 samples sufficient; more did not help in their setup; ViT-S LP 63.98 → 66.62 (+2.64). — [DIET-CP](https://arxiv.org/html/2509.06990v1)
- Recipe: single GPU, ViT-B "under 10 minutes on an H100", AdamW LR 1e-4, wd 0.05, 150 epochs, batch 32, first 5 % epochs head-only then last two blocks unfrozen, label smoothing ~0.3, 224 px. — [DIET-CP](https://arxiv.org/html/2509.06990v1)
- Evaluation: MedMNIST standard splits; patient-level not stated; no external validation; MedMNIST images are low-resolution (inference: much easier domain gap than real photos).

**Large-scale continued DINOv2 (RAD-DINO) — scaling evidence**
- Continual pretraining of RAD-DINO / MedImageInsight on nested subsets 30k, 50k, 100k, 1M, 3.5M CXRs (single institution): MI2 beats its open-weights model at ~30k samples (findings), **RAD-DINO needs ~100k**; patient-level 80/10/10 split; external holdouts VinDr-CXR (~9k) and RANZCR-CLiP (~17k). Compute: 32 H100, batch 1280; 0.33 h (30k) to 40.8 h (3.5M). — [Ilse 2025](https://arxiv.org/html/2509.12818v1)

**ExPLoRA (LoRA continued DINOv2 pretraining)**
- Unfreeze last block + LoRA (rank 32–64) elsewhere, continue the original DINOv2 objective; linear-probe gains vs frozen DINOv2: fMoW-RGB 67.60 → 76.86, Camelyon17 (pathology) 93.27 → 94.41, RESISC-45 +1.0, SpaceNet +0.1; but **iWildCam 66.04 → 62.95 (regression)**. Unlabeled sets were ~5k (SpaceNet) to ~400k–800k (fMoW); GPU cost 30–320 GPU-hours (GPU type not given). — [ExPLoRA](https://arxiv.org/html/2406.10973v5)

**Systematic review**
- 79 studies (2012–2021/22): most SSL-pretrained models beat the same architecture without SSL (relative AUROC +0.216–32.6 %); 5 studies reported decreases (0.98–4.51 %); contrastive studies averaged +6.35 %; end-to-end fine-tuning beat frozen-feature classifiers in 8/11 studies; only 18/79 initialised from natural-image weights; cited work: cutting pretraining images 250k → 50k typically cost >10 % downstream accuracy. Guidelines: use public natural-image pretrained weights, then continue SSL in-domain; compare several SSL methods. The review does not analyse patient-level splitting/leakage. — [Huang 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10131505/)

**Dermatology-specific**
- Gröger 2024: SSL on >240,000 dermatology images, 12 downstream tasks; small models "approach the performance of models 50 times larger". — [Gröger 2024](https://arxiv.org/abs/2411.05514)
- Chaves 2022: self-supervision "particularly useful for low training data scenarios (<1,500 and <150 samples)" — these thresholds refer to **labeled training-set size**, not unlabeled pretraining size; abstract does not say whether SSL weights were in-domain. — [Chaves 2022](https://arxiv.org/abs/2106.09229v3)

### Inferences
- (inference) Every medical paper showing robust in-domain SSL gains had ≥~10^5 unlabeled images; at ≤5k images the only positive evidence is preprint-level (DIET-CP, ExPLoRA SpaceNet ~5k with ~0 gain) or natural-image (El-Nouby, ≥8k) — i.e., **weak evidence** for our regime.
- (inference) The in-domain SSL *increment* over a good generic init was ~1–2 points in derm even at 200k–450k images; expect smaller or zero at ~10^3 images, and with only 14 patients the CV noise (one patient ≈ 7 % of patients) will swamp a 1–2-point effect.
- (inference) DIET-CP's large kNN gains partly reflect that frozen DINOv2 kNN on 28×28-upsampled MedMNIST is poor; for full-resolution phone photos of skin (closer to natural images) the domain gap — and thus the gain — is likely smaller (consistent with DIET-CP's own finding of no gain/regression on natural-image fine-grained sets).

### Gaps
- No study found on IV-site/phlebitis photos, nor any SSL study on wound/skin photos at ≤5k unlabeled images with patient-level CV — **no reliable evidence found**.
- MAE (He et al. 2022, CVPR), DINOv2 (Oquab et al. 2023), BYOL (Grill et al. 2020), MoCo v2 primary papers were not opened in this session; their numbers are not cited here.
- REMEDIS full author list and in-distribution patient-level split details not verified (Nature page behind redirect).
- No paper found that compares in-domain continued SSL against frozen SigLIP on small medical photo sets.

---

## Q2. Counter-evidence and failure cases (forgetting, collapse, small batches)

### Takeaway
Continued SSL on small sets can and does hurt: documented regressions for strong DINO backbones (DIET-CP on fine-grained natural sets and RetinaMNIST; ExPLoRA on iWildCam; RAD-DINO "catastrophic forgetting" on an external CXR set), overfitting with long schedules on ~8k images, and degradation of joint-embedding methods (DINO) as data shrinks. Contrastive methods lose accuracy with small batches unless trained longer.

### Cited Findings
- DIET-CP regressions: FGVC-Aircraft DINOv2 LP 43.47 → 38.47, DINOv3 LP 61.00 → 48.56; Food-101 DINOv2 LP 73.54 → 65.29; RetinaMNIST LP −3.99 (DINOv2) / −4.27 (DINOv3); authors: DIET-CP "does not improve fine-grained in-domain tasks" for strong DINO models; training-loss decrease does not reliably track downstream gain. — [DIET-CP](https://arxiv.org/html/2509.06990v1) (research evidence, preprint)
- ExPLoRA iWildCam LP 66.04 → 62.95; authors attribute it to a small domain gap (ImageNet already contains animals) → overfitting. LoRA on all matrices or MLP-only hurt. — [ExPLoRA](https://arxiv.org/html/2406.10973v5)
- RAD-DINO continued on up to 3.5M in-house CXRs scored below the open-weights model on external VinDr (57.7 vs 60.2 average accuracy); authors report "signs of catastrophic forgetting"/distribution mismatch. — [Ilse 2025](https://arxiv.org/html/2509.12818v1)
- DINO degrades with less pretraining data (iNat-19 78.4 → 70.1 from 100 % → 1 % ImageNet); Stanford-Cars SplitMask pretraining >5k epochs → "severe drop"; BEiT diverged (numerical instability) on clipart/sketch with long schedules. — [El-Nouby 2021](https://arxiv.org/abs/2112.10740)
- Derm-only SSL from the medical set without ImageNet init underperformed ImageNet→Derm (Table 2). — [Azizi 2021](https://arxiv.org/abs/2101.05224)
- Review: 5 of 79 studies reported decreases of 0.98–4.51 % with SSL. — [Huang 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10131505/)
- Batch size (SimCLR): "when the number of training epochs is small (e.g. 100 epochs), larger batch sizes have a significant advantage"; "with more training steps/epochs, the gaps … decrease or disappear"; square-root LR scaling helps small batches. — [SimCLR](https://arxiv.org/abs/2002.05709)
- Batch size (DINO, ViT-S, 100 ep, kNN): bs 128 → 57.9, 256 → 59.1, 512 → 59.6, 1024 → 59.9; bs 128 ran on one GPU; bs 8 reached 35.2 % after 50 epochs. Collapse avoided by centering + sharpening with momentum teacher (centering alone → uniform collapse). — [DINO](https://ar5iv.labs.arxiv.org/html/2104.14294)
- MoCo v3: for self-supervised ViTs "instability is a major issue that degrades accuracy" and can be hidden by apparently good results. — [MoCo v3](https://arxiv.org/abs/2104.02057)

### Inferences
- (inference) On an 8–24 GB consumer GPU, DINO-style batch 32–128 is workable (DINO lost only ~2 kNN points at bs 128 on ImageNet); SimCLR at bs ≤128 is the most batch-sensitive choice — prefer non-contrastive (DINO/BYOL-style), MoCo (queue) or MAE/DIET when batch is small.
- (inference) Main practical failure mode for us is **silent forgetting**: the adapted backbone may look better on in-distribution folds but lose generic robustness (lighting, phone models, skin tones). Always keep the generic frozen backbone as a comparator and test on held-out patients/sources.
- (inference) With ~120 images, collapse/overfit of any full-backbone SSL is likely; partial unfreezing (last 1–2 blocks or LoRA) is the only defensible setting.

### Gaps
- No quantitative study found of collapse frequency for DINO/BYOL at ≤1k images.
- BYOL small-batch behaviour not verified from the primary paper in this session.

---

## Q3. Practical thresholds — "below N unlabeled images, don't bother"?

### Takeaway
No guideline or regulator gives a minimum unlabeled-set size. Empirical anchors: in-domain gains reported at ~454k / ~207k (derm, full SSL), 30k–100k (continued DINOv2 / CLIP-style on CXR before beating open weights), ~8k (target-only MIM with full fine-tuning on natural images), ~1k (DIET-CP, preprint, MedMNIST, frozen eval, with regressions). Any threshold for phlebitis photos is inference.

### Cited Findings
- RAD-DINO continued pretraining needed ~100k CXRs to beat the off-the-shelf RAD-DINO on findings; MI2 ~30k. — [Ilse 2025](https://arxiv.org/html/2509.12818v1)
- DIET-CP: 1,000 images sufficient for gains in their ablation; more did not help. — [DIET-CP](https://arxiv.org/html/2509.06990v1)
- El-Nouby: 1,000 images give +4 points over scratch (but scratch is a weak baseline); ~8k-image target-only MIM ≈ ImageNet pretraining. — [El-Nouby 2021](https://arxiv.org/abs/2112.10740)
- Review cites 250k → 50k pretraining images costing >10 % accuracy. — [Huang 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10131505/)
- LightlyTrain docs suggest up to 10,000 epochs for datasets under 100k images and batch 128–2,048 (vendor guidance, not evidence). — [LightlyTrain docs](https://docs.lightly.ai/train/stable/methods/distillation.html) (industry practice)

### Inferences (all labelled inference — no source gives these numbers)
- **< ~500 unlabeled images (our NOW):** do not run backbone SSL; expected benefit ≈ 0 and indistinguishable from noise with 14 patients; risk of overfitting and leakage dominates.
- **~1k–5k images, many patients (FUTURE):** only lightweight continued pretraining (DIET-CP-style, ExPLoRA-style LoRA/last-block, or short DINO continuation of DINOv2-S) is worth a *pre-registered experiment*, and only if the frozen baseline shows a clear failure pattern (e.g., poor kNN neighbour purity, sensitivity to lighting/skin tone). Treat as exploratory.
- **≳ 10k–30k images from ≳ several hundred patients:** full continued DINOv2 pretraining becomes plausible by analogy with Ilse 2025 (30k–100k) — but the analogy (CXR, ViT-B, 32 H100) is weak.
- The more relevant unit is probably **number of distinct patients/sites/devices**, not photo count (inference): 3,000 photos from 30 patients carry little new variation.

### Gaps
- No evidence-based threshold for skin/IV-site photographs — **no reliable evidence found**.

---

## Q4. Cheaper alternatives to full in-domain SSL

### Takeaway
For our pipeline (frozen DINOv2-S + logistic regression), the cheap options with the best evidence/cost ratio are: keep the frozen backbone and improve the head/features (multi-layer or patch-token pooling, kNN), try other frozen generic backbones (DINOv3, SigLIP) under the same patient-level CV, and — only later — parameter-efficient continued SSL (last block/LoRA). Normalisation-statistics adaptation (AdaBN) applies to BN networks (EfficientNet-B0), not to DINOv2's LayerNorm ViT.

### Cited Findings
- DIET-CP shows the **frozen DINOv3 linear probe is already the strongest starting point** (medical avg F1 74.77 vs DINOv2 71.52 before adaptation). — [DIET-CP](https://arxiv.org/html/2509.06990v1)
- ExPLoRA: unfreeze 1 block + LoRA, <10 % of parameters, continuing DINOv2 loss; unfreezing an extra block without LoRA gave only small gains. — [ExPLoRA](https://arxiv.org/html/2406.10973v5)
- AdaBN: parameter-free adaptation by modulating BN statistics across the network. — [AdaBN](https://arxiv.org/abs/1603.04779)
- DINOv2 registers variants perform similarly to non-register versions (ViT-L/14 kNN 83.8 vs 83.5). — [DINOv2 README](https://github.com/facebookresearch/dinov2)
- Review: earlier-layer features can help for some tasks; combining representations improved performance. — [Huang 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10131505/)

### Inferences
- (inference) Registers are an architecture choice of the released checkpoint, not an adaptation method — swapping to a "-reg" DINOv2 is just another frozen backbone to test.
- (inference) Unlabeled photos can be used *without training the backbone*: (a) active-learning selection — embed the unlabeled pool with the frozen backbone, pick diverse/uncertain photos (k-center / cluster coverage) for nurse labelling; (b) near-duplicate and quality screening; (c) kNN label suggestions shown to a human (must never auto-write labels — project rule).
- (inference) AdaBN on EfficientNet-B0: recompute BN running stats on in-domain photos (no gradient). Cheap (<1 min), but with ~120 images it may destabilise stats; test under CV only.

### Gaps
- No small-medical-photo evidence comparing SigLIP vs DINOv2 vs DINOv3 frozen features was collected here (other notes may cover it).

---

## Q5. Data governance: consent/revocation, unlearning, and patient-level leakage in SSL

### Takeaway
A backbone continued-pretrained on a photo is a derivative of that photo; the only *exact* way to remove a revoked photo's influence is to retrain without it (Bourtoule 2021 definition). Because small-scale continued pretraining is cheap (minutes–hours), "retrain from the generic checkpoint excluding revoked images" is practical and preferable to approximate unlearning. Including test-fold patients' unlabeled images in SSL is transductive use of test data: it must be either excluded per fold or explicitly reported as transductive.

### Cited Findings
- Exact unlearning definition: training then unlearning must give the same distribution of models as never training on the point; baseline = retrain from scratch without the point. SISA (shards + slices) speeds unlearning (Purchase 4.63×, SVHN 2.45×, ImageNet 1.36×) at an accuracy cost that grows with number of shards, and constituent models become weak when data per shard are small. — [Bourtoule 2021](https://ar5iv.labs.arxiv.org/html/1912.03817)
- Azizi's MICLe builds positive pairs from multiple images of the same patient case — relevant both to leakage (same-patient images) and to our multiple-photos-per-patient data. — [Azizi 2021](https://arxiv.org/abs/2101.05224)
- Review notes some studies form positive pairs from the same patient/CT series but does not analyse leakage. — [Huang 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10131505/)
- Only 173/705 (24.5 %) medical foundation-model adaptation studies had confirmed independent external validation. — [Phuntsho 2026](https://arxiv.org/abs/2603.14271)
- Project code already has a revocation table (`src/data/revocations.py`: `revoke`, `revoked`, `is_revoked`) and the DINOv2 adapter records `backbone_hash` = sha256 of `model.safetensors`. — local code read 2026-10-30.

### Inferences
- (inference) SISA is unnecessary here: with ≤5k images, a full continued-pretraining rerun costs ~0.5–3 GPU-h (see Q6), so exact retraining is affordable; sharding would only weaken an already data-starved model.
- (inference) Policy proposal (for human approval, not auto-applied): every adapted backbone gets a manifest (image IDs/SHA-256 of all SSL images, consent status snapshot, generic parent checkpoint hash, config, seed). On any revocation hitting a manifest, the backbone and every classifier built on it are marked "contains revoked data — do not use", and a rebuild excluding revoked images is *proposed* to the operator (consistent with "no auto-training"). Keep the generic frozen backbone as the always-available fallback (it never contains project photos).
- (inference) Memorisation risk: MAE-type reconstruction models can partially reconstruct training images; do not export or share adapted backbones outside the project, and treat them as containing personal data.
- (inference) Leakage: SSL on unlabeled images of test patients does not leak labels, but it adapts the representation to exactly those patients' skin, lighting and device — an optimistic bias of unknown size (transductive). Correct protocol: inside StratifiedGroupKFold, run SSL only on images of training-fold patients (+ unlabeled photos of patients who never appear in any test fold). With 3 folds that means 3 SSL runs; affordable at this scale. Report any transductive variant separately.
- (inference) Unlabeled LINE photos must pass the same consent and revocation filter as labeled ones *at SSL time*; unlabeled pools are often forgotten in revocation sweeps.

### Gaps
- A primary study quantifying the optimistic bias from transductive SSL on test-patient images in medical imaging was not found (Kamnitsas et al., arXiv:2107.08964, on transductive segmentation appeared only as a search snippet and was not opened) — **no reliable evidence found**.
- Taiwan PDPA / IRB rules on derived models from revoked data were not researched here.

---

## Q6. Implementation: tools, hyperparameters, GPU cost, export into the existing frozen-feature + LR pipeline

### Takeaway
Simplest local route that plugs straight into the current code: continue-train the **same HF `Dinov2Model` (dinov2-small, hidden 384)** in plain PyTorch (DIET-CP-style or DINO-loss with last 1–2 blocks / LoRA), merge any LoRA, then `save_pretrained(..., safe_serialization=True)` → `config.json` + `model.safetensors`, which the existing adapter loads. Expected cost at 1k–5k images: well under a few GPU-hours. All of this runs offline; no cloud needed.

### Cited Findings
- Existing pipeline: `adapters.py` loads `Dinov2Model.from_pretrained(base, local_files_only=True, use_safetensors=True)`, extracts features, fits `sklearn LogisticRegression`; external import (`external_models.py`) accepts only `.safetensors/.json/.npz`, expects `{'config.json','model.safetensors','classifier.npz'}` for `dinov2_small`, and `DINO_HIDDEN = 384`. requirements: `transformers>=4.46,<5`, `safetensors>=0.4,<1`. — local code read 2026-10-30.
- DINOv2 official training: code and weights Apache-2.0; reference training ViT-L/16 on ImageNet-1k = 4 A100-80GB nodes (32 GPUs) ~1 day; tested on Linux only; custom data requires editing dataset classes. — [DINOv2 README](https://github.com/facebookresearch/dinov2) (→ unsuitable for single Windows GPU; inference)
- LightlyTrain: supports DINOv2 pretraining on own data and distillation; recommends 100–3,000 epochs, batch 128–2,048; exports `.pt` (needs conversion to safetensors). — [LightlyTrain docs](https://docs.lightly.ai/train/stable/methods/distillation.html)
- solo-learn: MIT licence; SimCLR, MoCo v2+/v3, BYOL, DINO, MAE, VICReg, Barlow Twins, etc.; ResNet/ViT/Swin/ConvNeXt backbones; PyTorch Lightning (mixed precision, grad accumulation); last news Jan 2024; model-zoo checkpoints "no longer available as of 2026" (maintenance risk). — [solo-learn](https://github.com/vturrisi/solo-learn)
- HF `ViTMAEForPreTraining`: default `mask_ratio=0.75`, `norm_pix_loss` (normalized pixels "improved representation quality"); decoder discarded after pretraining; checkpoints `facebook/vit-mae-base` (ViT-B/16, hidden 768). — [HF ViTMAE docs](https://huggingface.co/docs/transformers/model_doc/vit_mae)
- DIET-CP recipe (single GPU): AdamW 1e-4, wd 0.05, 150 epochs, batch 32, 10 % warm-up + cosine, head-only first 5 % then last 2 blocks, label smoothing ~0.3, aug = RandomResizedCrop/flip/color-jitter/grayscale/blur; ViT-B <10 min on H100 for ~1k images. — [DIET-CP](https://arxiv.org/html/2509.06990v1)
- DINO compute anchor: ViT-S/16, ImageNet (~1.28M images), 100 epochs, 2×224² + 10×96² multi-crop, two 8-GPU servers: 24.2 h (74.6 % linear); without multi-crop 15.3 h. — [DINO](https://ar5iv.labs.arxiv.org/html/2104.14294)
- MAE self-pretraining recipe: LR 1.5e-4, wd 0.05, cosine + warm-up, mask 75 %. — [Zhou 2023](https://arxiv.org/abs/2203.05573)

### Inferences — GPU time estimates (basis shown; all inference)
- DINO-style continuation of ViT-S: DINO used 24.2 h × 16 GPUs ≈ 387 GPU-h for 1.28M × 100 = 128M image-epochs → ≈ 3×10⁻⁶ GPU-h per image-epoch (datacenter GPU of 2021). 5,000 images × 100 epochs = 0.5M image-epochs ≈ **1.5 GPU-h**; 1,000 × 300 = 0.3M ≈ **~1 GPU-h**. On a consumer RTX-class GPU with AMP assume 1–3× that, plus Windows dataloader overhead → budget **1–5 h**. Partial unfreezing reduces backward cost further.
- DIET-CP on DINOv2-S, 1k–5k images, 150 epochs: H100 ViT-B <10 min for 1k; ViT-S is ~4× fewer FLOPs than ViT-B; consumer GPU several × slower than H100 → **~10–60 min**.
- MAE ViT-B from `facebook/vit-mae-base`, 5k images × 800–1,600 epochs (small-data MIM needs long schedules per El-Nouby/Zhou): 4–8M image-epochs → order **5–15 h**; overfitting beyond ~5k epochs on small sets.
- SimCLR/MoCo/BYOL ResNet-50 via solo-learn: ~1–4 h for 5k × 200 epochs (inference by analogy); SimCLR at batch ≤128 is the weakest choice (Q2).
- Memory (inference, must be measured with `torch.cuda.max_memory_allocated`): ViT-S/14 at 224 px with AMP, 2 global + 6 local crops, batch 32–64 should fit 8 GB if only last 2 blocks train; full fine-tuning batch 64 likely needs ~12–16 GB or gradient checkpointing; ViT-B MAE batch 64 with 75 % masking fits ~12 GB (encoder sees 25 % of tokens). Use gradient accumulation to reach effective 128–256.

### Per-method summary (for decision; "evidence" = strength for ≤5k-image skin photos)

| Method | Evidence for our regime | Min data (inference) | Expected benefit | Main risks | Tooling |
|---|---|---|---|---|---|
| Frozen DINOv2-S/B, DINOv3, SigLIP + LR/kNN (baseline) | Moderate (DIET-CP baselines; industry practice) | 0 unlabeled | Reference | Domain gap | existing `adapters.py` |
| DIET-CP-style continued pretraining (last 2 blocks) | Weak (one preprint, MedMNIST, regressions on some sets) | ~500–1,000 imgs, many patients | 0 to + several LP points; may hurt | regression on fine-grained tasks; loss≠downstream | plain PyTorch + HF Dinov2Model |
| ExPLoRA-style DINO loss + LoRA/last block | Weak–moderate (ICML 2025; ≥5k imgs; one regression) | ~5k+ | +0–9 LP points in non-medical shift; +1.1 pathology | forgetting; tuning | custom code (+ `peft`) |
| Full DINO/DINOv2 continued pretraining | Strong only at ≥30k–100k (CXR) | ≥30k (inference) | +1–2 pts at 10⁵ scale | forgetting (RAD-DINO), compute | LightlyTrain / official repo (Linux) |
| MAE (target-only or continued) | Moderate for ≥8k with **full fine-tuning**; weak for frozen features (MAE frozen features weak per DIET-CP LP 60.6) | ≥5k–10k | Helps fine-tuning, not LR-on-frozen | long schedules, overfit, new adapter needed (ViT-B) | HF ViTMAE |
| SimCLR / MoCo v2/v3 / BYOL / MICLe | Strong at 2×10⁵+ (Azizi); none at ≤5k | ≥10⁴ (inference) | +1–2 pts at scale | small-batch penalty, instability | solo-learn / lightly |

### Pseudo-code (DIET-CP-style on HF DINOv2-small; for a *proposed* experiment — not to be auto-run)
```python
# inputs: ssl_images = consented, non-revoked photos of TRAINING-FOLD patients only (per CV fold)
model = Dinov2Model.from_pretrained(GENERIC_DIR, local_files_only=True, use_safetensors=True)  # dinov2-small, 384-d
for p in model.parameters(): p.requires_grad = False
head = nn.Linear(384, len(ssl_images))          # DIET: target = datum index (no labels)
# epochs 0..7 (5%): train head only; then unfreeze model.encoder.layer[-2:] (+ final layernorm)
opt = AdamW(params, lr=1e-4, weight_decay=0.05); sched = cosine(warmup=10%)   # ranges: lr 5e-5–2e-4
loss = CrossEntropy(label_smoothing=0.3)                                        # 0.2–0.4
epochs = 150 (100–300); batch = 32 (16–64); AMP fp16/bf16; img 224 (Dinov2 accepts 224, patch 14)
aug = RandomResizedCrop(224, scale=(0.4,1)), HFlip, mild ColorJitter, (avoid strong hue shifts: redness is the signal)
for x, idx in loader: loss(head(model(x).pooler_output), idx).backward(); ...
model.save_pretrained(OUT_DIR, safe_serialization=True)  # -> config.json + model.safetensors (drop the DIET head)
# write manifest.json: image sha256 list, consent snapshot, parent hash, seed, config
# then: existing adapter fits LogisticRegression on frozen features of OUT_DIR, same StratifiedGroupKFold
```
- (inference) Colour-jitter caution: phlebitis grading depends on erythema; strong hue/saturation jitter or grayscale (used in generic SSL recipes) may teach invariance to the very cue that matters — keep jitter mild and test with/without.
- (inference) For LoRA: merge (`merge_and_unload`) before `save_pretrained` so key names match plain `Dinov2Model`; verify `load_state_dict(strict=True)` and hidden size 384 (required by `external_models.py`). LightlyTrain/official-repo checkpoints are `.pt`/timm-style keys → need a key-mapping conversion to HF names and safetensors before import (the project's importer rejects `.pt`).

### Validation on the platform (inference / protocol)
- Same patient-level StratifiedGroupKFold (3-fold), SSL nested inside each fold; compare against frozen generic backbone with identical LR head, seeds and folds; report per-fold metrics and patient-level bootstrap CIs; also kNN neighbour-purity and a lighting/device subgroup check; any gain smaller than fold-to-fold spread = "no demonstrated benefit". Human review before any adapted backbone is registered (project rule).

### Gaps
- Exact current location of HF `run_mae.py` example script not verified (GitHub path returned 404).
- No measured memory/time on the user's actual GPU — must be benchmarked locally.
- GPU type for DINO's 24.2 h figure not confirmed in the text read.

---

## Q7. NOW vs FUTURE recommendation

### Takeaway
**NOW (~120 labeled photos, 14 patients, small unknown unlabeled pool): do not do in-domain SSL.** Use frozen generic backbones (DINOv2-S/B, DINOv3, SigLIP) + logistic regression/kNN under patient-level CV; use any unlabeled photos only for embedding-based active-learning selection and QC. **FUTURE (~1,000 labeled + a few thousand unlabeled, more patients):** a single, pre-registered, low-cost experiment with DIET-CP- or ExPLoRA-style partial continued pretraining of DINOv2-S is reasonable; full SSL (DINO/MAE/SimCLR from scratch or full-backbone) is not justified until ~10⁴–10⁵ images from many patients.

### Cited Findings
- Gains at scale are modest (+1.92 % ImageNet→Derm, 454k images; derm top-3 0.923→0.926 with 207k images). — [Azizi 2021](https://arxiv.org/abs/2101.05224); [REMEDIS](https://arxiv.org/abs/2205.09723v2)
- ~1k-image continued pretraining can help frozen features but also regress. — [DIET-CP](https://arxiv.org/html/2509.06990v1)
- Continued DINOv2 needs ~100k CXRs to beat open weights. — [Ilse 2025](https://arxiv.org/html/2509.12818v1)
- SSL is most useful with few *labels* (<1,500 / <150) — supporting the use of strong pretrained (SSL) backbones rather than in-domain SSL itself. — [Chaves 2022](https://arxiv.org/abs/2106.09229v3)

### Inferences
- NOW (inference): with 14 patients and 9 normals, the CV standard error dwarfs any plausible SSL effect; spending effort on more patients, balanced normals and label quality has higher expected value than SSL. Any SSL result would be unpublishable as evidence of benefit.
- FUTURE (inference): pre-conditions before running SSL — ≥ ~1,000 consented unlabeled photos from ≥ ~100 distinct patients (not in test folds), revocation manifest in place, frozen-baseline CV established. Compare (a) frozen DINOv2-S, (b) frozen DINOv3/SigLIP, (c) DIET-CP-adapted DINOv2-S, (d) ExPLoRA-style; adopt (c)/(d) only if improvement exceeds fold spread on patient-level CV *and* holds on a later-collected or LINE-vs-hospital source split.
- Cloud: none of the recommended methods require cloud; Azizi/REMEDIS used Google Cloud TPUs — local alternatives are the single-GPU recipes above. Do not use hosted training services (e.g., any cloud LightlyTrain/managed notebooks) with research photos.

### Gaps
- No direct evidence for this task/domain; all NOW/FUTURE thresholds are inference and should be revisited when the project has its own frozen-baseline learning curves.
