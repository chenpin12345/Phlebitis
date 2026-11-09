# Data augmentation for small skin-photo classification and YOLO small-lesion detection (phlebitis prototype)

Access date for every source below: 2026-10-30. Source grades: [A] official docs / source code, [B] top-venue peer-reviewed or systematic review, [C] other peer-reviewed, [D] preprint, [E] blog / forum / tutorial. Each conclusion is tagged **(research evidence)**, **(industry practice)** or **(inference)**.

Scope note: the project is a research prototype, with no clinical claims. Every recommendation is a *candidate setting to ablate on the existing patient-level StratifiedGroupKFold (3-fold) splits*. None of it should be switched on automatically, and each needs human confirmation (project principle).

Project state observed in the local code (read-only check, 2026-10-30) [A, local source]:
- Ultralytics installed: `ultralytics.__version__ = "8.4.161"`. torch 2.13.0+cu130, torchvision 0.28.0+cu130 (`02_主程式碼/.venv/Lib/site-packages`).
- YOLO config `02_主程式碼/configs/train.json` is already conservative: `mosaic 0, mixup 0, hsv_h 0.01, hsv_s 0.2, hsv_v 0.15, degrees 10, translate 0.05, scale 0.05, fliplr 0.5, flipud 0, workers 0, batch 4, epochs 120, patience 25, amp false, deterministic true`. `src/training/runner.py:64` has a `--no_color` switch that sets `hsv_h/s/v = 0`. That switch is the natural colour-ablation arm.
- Classifier augmentation lives in `src/workbench/adapters.py::tensor_image()` (around lines 142-157): pad to 224 + horizontal flip p=0.5 + uniform rotation ±`rotation`, with rotation ≤45° enforced in `contracts.py:257`. There is no colour or crop augmentation. The DINOv2 path (`dino_features()` around line 400, `dino_train()` around line 434) extracts frozen features once, without augmentation, and then fits sklearn `LogisticRegression`.

---

## Q1. Dermatology augmentation evidence, and colour augmentation vs the erythema (redness) signal

### Takeaway
The best-known dermatology study (Perez et al. 2018, ISIC 2017 dermoscopy, 2,000 training images, melanoma) found that geometric transforms (crop, affine, flip) helped consistently. Colour transforms were mixed. Training-time augmentation alone did *not* help below about 500 training images; it helped mainly when combined with test-time augmentation.

I found **no reliable evidence** that directly measures how hue or saturation jitter affects erythema, redness, phlebitis, wound or burn colour classification. A reasoned inference therefore drives the recommendation: hue jitter at zero or very small values, low saturation jitter, and moderate brightness/contrast jitter, which simulates the real LINE-smartphone lighting variation.

### Cited Findings
- **Perez F, Vasconcelos C, Avila S, Valle E. "Data Augmentation for Skin Lesion Analysis." ISIC Skin Image Analysis Workshop / OR 2.0, LNCS 2018.** DOI 10.1007/978-3-030-01201-4_33 (published version, not opened). arXiv:1809.01442 (DOI 10.48550/arXiv.1809.01442) [C]. [arXiv abstract](https://arxiv.org/abs/1809.01442); [ar5iv full text](https://ar5iv.labs.arxiv.org/html/1809.01442).
  - Data and models: ISIC 2017 data with 2,000 train / 150 val / 600 test images. Inception-v4, ResNet-152 and DenseNet-161 (ImageNet-pretrained, fine-tuned), 6 runs each. (research evidence)
  - 13 scenarios with these magnitudes. B colour: saturation, contrast and brightness factors in [0.7, 1.3]. C: B plus hue shift in [-0.1, 0.1]. D affine: rotation ≤90°, shear ≤20°, scale [0.8, 1.2]. E: flips. F random crop: 40-100% of area, aspect 3/4-4/3. G random erasing: ≤30% of the image, p=0.5. H elastic (TPS). I lesion-mix. J = F→D→E→C. K = J+G. L = J+H. M = I+J. (research evidence)
  - Best scenario J: test AUC 0.854 (Inception-v4), 0.882 (ResNet) and 0.879 (DenseNet), without external data. The top ISIC 2017 entries scored 0.874, 0.870 and 0.868, but used 3,444 to about 9,600 training images. (research evidence)
  - What helped and what hurt:
    - Geometric transforms gave the most consistent gains.
    - "both color transforms performed worse than scenario A (no augmentation) with 144 crops on ResNet". Hue (C) beat colour-without-hue (B).
    - Random erasing gave little gain, or was worse on ResNet. Adding it to J (scenario K) lowered AUC.
    - Elastic plus the others (L) was worse than J.
    - Lesion-mix (I, M) was worst. (research evidence)
  - TTA: averaging 64 augmented copies, or 144 crops, beat the single original image across scenarios. 16 copies were used on validation. (research evidence)
  - Dataset size experiment (subsets of 1,500, 1,000, 500, 250 and 125): train plus test augmentation helped noticeably at ≥500 images. *Training-only augmentation hurt below 500 images*. With augmentation, 500 to 1,000 images beat 1,500 to 2,000 images without it. (research evidence; as summarised from the ar5iv text, and the per-scenario figure values were not readable)
  - Leakage and external validation caveat: ISIC 2017 uses the challenge's fixed splits. The paper text I read did not discuss patient-level grouping, and multiple images of the same lesion or patient could not be ruled out. There was no external validation beyond the challenge test set. The task is melanoma under a dermoscope (controlled lighting), not erythema in smartphone photos.
- **Galdran A, et al. "Data-Driven Color Augmentation Techniques for Deep Skin Image Analysis." arXiv:1703.03702 (2017), DOI 10.48550/arXiv.1703.03702** [D]. [arXiv](https://arxiv.org/abs/1703.03702).
  - The authors use shades-of-gray colour constancy to estimate each image's illuminant. They then augment by re-applying illuminants sampled from the training distribution, instead of random colour jitter. They stress that colour is a core cue for skin lesions.
  - The abstract reports no quantitative comparison with plain colour jitter. (research evidence, weak)
- **Saha A, et al. "Leveraging Adaptive Color Augmentation in CNNs for Deep Skin Lesion Segmentation." ISBI 2020, arXiv:2011.00148** [C]. Seen only as a search-result snippet, [arXiv PDF](https://arxiv.org/pdf/2011.00148); not fully opened. The snippet says they bound colour difference and saturation because extreme augmentation creates unnatural hues that hurt learning. Treat it as a pointer only.
- **Yuan H, ..., Burlina P. "EdgeMixup: Improving Fairness for Skin Disease Classification and Segmentation." arXiv:2202.13883 (2022)** [D]. [arXiv](https://arxiv.org/abs/2202.13883). A later MICCAI 2023 version exists per the [MICCAI 2023 paper page](https://conferences.miccai.org/2023/papers/234-Paper1416.html), which I did not open in depth.
  - Task: erythema migrans (Lyme) and skin-tone bias. The method converts to HSV, applies a red mask, runs Canny on the V channel, and blends the edge map with the image (weight 0.3) to suppress skin-tone cues.
  - Reported result: a 10.99% reduction in the light-vs-dark accuracy gap and +8.4% on an under-represented subgroup. (research evidence, preprint; numbers from the search summary of the abstract)
  - This is the closest "redness lesion plus skin tone" augmentation paper I found. It does *not* test hue jitter.
- Pressure-ulcer literature (Wounds UK, 141 patients) uses the mean and SD of hue, saturation and intensity as features that *discriminate* normal skin from grade 2a/2b ulcers. It also notes that darker skin makes stage I detection harder. Source: [Wounds UK article](https://wounds-uk.com/journal-articles/using-hue-saturation-and-intensity-compared-with-three-other-pressure-ulcer-grading-systems-1/) [C]; search-result summary only, not fully opened. This supports the premise that hue and saturation carry the diagnostic signal in redness-type lesions. It is not an augmentation study.
- I found no study that ablates hue or saturation jitter for erythema index, phlebitis, burns, wounds or pressure ulcers in deep learning. Two searches returned none: "color augmentation hue jitter erythema skin redness deep learning" and "wound pressure ulcer image classification color augmentation hue saturation". **No reliable evidence found.**

### Inferences
- **How large the colour jitter actually is (inference, from library math):**
  - Ultralytics `RandomHSV` in the installed 8.4.161 code does three things. It shifts hue by `r_h*180` OpenCV units (full circle = 180), with `r_h ~ U(-hsv_h, hsv_h)`. It multiplies saturation by `1 + U(-hsv_s, hsv_s)`. It multiplies value by `1 + U(-hsv_v, hsv_v)`. Source: `.venv/Lib/site-packages/ultralytics/data/augment.py`, class `RandomHSV` [A].
  - So the *default* `hsv_h=0.015` is about ±2.7 OpenCV units (about ±5.4° of hue). The *default* `hsv_s=0.7` multiplies saturation by **0.3-1.7**, and `hsv_v=0.4` multiplies brightness by 0.6-1.4.
  - A ×0.3 saturation factor can turn a clearly erythematous patch into near-skin-tone. A ×1.7 factor can make mildly pink normal skin look inflamed. That is label-changing noise for a redness-staged task. The project's current `hsv_s=0.2` (×0.8-1.2) is far milder and consistent with this reasoning.
  - torchvision `ColorJitter(hue=h)` samples a hue shift in [-h, h] as a fraction of the full hue circle, with h ≤ 0.5. Perez's hue of 0.1 is therefore about ±36°, which is large for a red-vs-skin distinction. This is my reading of the torchvision `adjust_hue` semantics; I did not open the ColorJitter page in this session.
- Brightness and contrast jitter is better justified than hue or saturation jitter. LINE photos have uncontrolled lighting and exposure, and brightness changes alter saturation less than direct saturation scaling does. (inference)
- A more physically plausible alternative is illuminant or white-balance augmentation (the Galdran approach), or grey-world normalisation at *both* train and test time. Either one simulates camera and lighting variation without arbitrarily rotating the redness hue. (inference; supported weakly by [Galdran 2017](https://arxiv.org/abs/1703.03702))
- Fitzpatrick and skin-tone robustness: Taiwanese patients are mostly Fitzpatrick III-IV (assumption, not verified). Hue jitter does not simulate skin-tone variation realistically, because melanin changes the brightness and saturation of the whole skin field rather than shifting hue. If skin-tone robustness matters, collect diverse data and evaluate per subgroup instead of using jitter. (inference)
- Perez's result that training-only augmentation hurt below 500 images transfers to the NOW regime (about 120 photos from 14 patients) only as a warning. It is a different modality, task and model regime. (inference)

### Gaps
- No direct evidence on hue or saturation augmentation vs erythema, phlebitis, burn, wound or pressure-ulcer colour signals.
- I could not read the per-scenario AUC values of Perez et al. (they are in a figure). The Saha 2020 and Wounds UK HSI papers were seen only as snippets.
- Garcea et al. 2023 (review of data augmentation in medical imaging) was not located or opened in this session.

---

## Q2. RandAugment / TrivialAugment / AutoAugment / MixUp / CutMix on small medical data

### Takeaway
RandAugment's own paper shows that the **optimal magnitude increases with dataset size and model size**. Tiny datasets therefore want *weaker* RandAugment, if any. TrivialAugment is tuning-free but samples from a fixed operation set that includes strong colour operations.

Medical evidence for MixUp and CutMix comes from preprints and is dataset-dependent (positive on MRI and fundus with thousands of images). Ordinal grading has explicit counter-arguments, since standard mixup is "ill-suited" for it. For NOW (14 patients, 9 normal photos) none of these is worth running, except perhaps as a later ablation.

### Cited Findings
- **Cubuk ED, Zoph B, Shlens J, Le QV. "RandAugment: Practical automated data augmentation with a reduced search space." arXiv:1909.13719 (2019), DOI 10.48550/arXiv.1909.13719** [D]; also published at CVPR Workshops 2020, which I did not confirm from the pages I opened. [arXiv](https://arxiv.org/abs/1909.13719); [ar5iv](https://ar5iv.labs.arxiv.org/html/1909.13719).
  - N is the number of operations applied sequentially, and M is one global magnitude on a 0-10 integer scale (0-30 in one preliminary experiment). (research evidence)
  - "larger networks demand larger data distortions for regularization". The optimal magnitude "increases monotonically with training set size" (Wide-ResNet-28-10 trained on CIFAR-10 subsets of 1K, 4K, 10K and others). The appendix gives an optimal M of 4 (WRN-28-2) and 5 (WRN-28-10) on CIFAR-10. (research evidence; natural images, not medical)
- **Müller SG, Hutter F. "TrivialAugment: Tuning-free Yet State-of-the-Art Data Augmentation." ICCV 2021 (oral). arXiv:2103.10158, DOI 10.48550/arXiv.2103.10158** [B]. [arXiv](https://arxiv.org/abs/2103.10158). It applies a single augmentation per image and needs no tuning. The authors report that it beats previous auto-augmentation methods on natural-image benchmarks. The abstract has no medical or small-data evidence. (research evidence)
- **Qi X, Zhang Z, et al. "MediAug: Exploring Visual Augmentation in Medical Imaging." arXiv:2504.18983 (2025)** [D]. [arXiv](https://arxiv.org/abs/2504.18983v1); [code](https://github.com/aigeeksgroup/MediAug).
  - The study benchmarks MixUp, YOCO, CropMix, CutMix, AugMix and SnapMix with ResNet-50 and ViT-B on brain-tumour MRI and fundus eye-disease images.
  - Best methods differ by dataset and backbone. For brain tumour, MixUp was best with ResNet-50 (79.19%) and SnapMix with ViT-B (99.44%). For fundus, YOCO was best with ResNet-50 (91.60%) and CutMix with ViT-B (97.94%). The repository reports CutMix α=1.0 as best in its sweep.
  - So the effect is dataset-dependent. No patient-level grouping or external validation is described in what I read. (research evidence, preprint, search-summary level)
- Ordinal grading:
  - DisMix (arXiv:2608.04652, 2026) [D] states "Image mixup is ... ill-suited for ordinal classification tasks such as medical disease grading". It proposes order-aware mixing. [arXiv PDF](https://arxiv.org/pdf/2608.04652) (search snippet only).
  - The DFPG ordinal-regression preprint [D] proposes Adjacent-Category Mixup, which mixes only neighbouring grades. It gives a small gain over plain MixUp on Adience: MAE 0.4427 vs 0.4442. [arXiv PDF](https://arxiv.org/pdf/2505.05834) (search snippet only).
  - (research evidence, weak)
- Fine-grained, non-medical: the OpenMixup benchmark lists MixUp and CutMix slightly *below* the vanilla baseline for ResNet-18 in a fine-grained transfer table, for example CutMix 51.24 vs vanilla 51.79. Source: [OpenMixup docs](https://openmixup.readthedocs.io/en/latest/mixup_benchmarks/Mixup_downstream.html) [E] (search snippet only). This is counter-evidence for fine-grained signals.
- Ultralytics classify defaults are `auto_augment: randaugment` and `erasing: 0.4`, but they only apply to Ultralytics *classify* training. Source: [default.yaml on GitHub main](https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/cfg/default.yaml) and the installed 8.4.161 copy [A]. The project's EfficientNet-B0 uses its own torchvision/PIL pipeline, so these defaults do not affect it.
- I did not open the original MixUp (Zhang et al., ICLR 2018) or CutMix (Yun et al., ICCV 2019) papers in this session, so I cite neither by URL or DOI. Their mechanisms are standard knowledge: MixUp blends images and labels convexly, and CutMix pastes a box with an area-proportional label.

### Inferences
- **CutMix can cut out the lesion (inference).** Phlebitis signs (erythema around the IV site, a streak, a cord) occupy a small part of a whole-arm photo. A random CutMix box can delete the lesion or paste it into a normal image, while the label is mixed by *area*, not by lesion presence. That is label noise.
- **MixUp vs staging (inference).** MixUp on {normal, stage 1, stage 2} produces "30% stage 2 + 70% normal" soft labels. That is incompatible with a staging rule based on redness *extent*. A blended image's redness is a pixel average, not a stage-1 lesion.
  - If tried at all, use it on the binary task only, with a small α (about 0.2), or use adjacent-class-only mixing.
- **RandAugment / TrivialAugmentWide colour operations (inference).** torchvision's operation pools include Color (saturation), Contrast, Brightness, Sharpness, Posterize, Solarize, Equalize and AutoContrast. Solarize, Posterize and Equalize change the red/skin colour balance strongly. TrivialAugmentWide samples magnitude uniformly up to the maximum, so 1 in about 14 samples is a strong colour operation.
  - For a redness task, prefer a custom RandAugment-like pool restricted to geometric operations plus brightness and contrast, at low magnitude (M ≈ 3-5 on the 0-10 scale, N = 1-2). This follows from Cubuk's "smaller data needs smaller magnitude" result plus the colour argument.
- **AutoAugment (inference).** Its policies were learned on ImageNet, CIFAR and SVHN. No evidence was found that they transfer to small medical colour-signal tasks. Not recommended now.
- **Frozen backbone (inference).** With the EfficientNet backbone frozen, augmentation only regularises the linear head. The expected gain from strong policies is small, and the risk of colour-label noise remains.

### Gaps
- No study found of RandAugment, TrivialAugment, MixUp or CutMix on skin photos with fewer than 200 images, or on patient-grouped skin datasets.
- Garcea et al. 2023 and Chlap et al. 2021 were not read in full. Chlap 2021 is a systematic review covering CT and MRI only: *J Med Imaging Radiat Oncol* 65(5):545-563, DOI 10.1111/1754-9485.13261; bibliographic data from a [BVS record](https://pesquisa.bvsalud.org/sms/resource/pt/mdl-34145766), full text paywalled. It does not cover RGB skin photos.

---

## Q3. Augmentation with frozen DINOv2 features + logistic regression, and test-time augmentation (TTA)

### Takeaway
The official DINOv2 evaluation code keeps **logistic regression without augmentation** separate from **linear classification with data augmentation**. Augmentation is therefore optional for the frozen-feature + LR pipeline, and the no-augmentation LR is the standard baseline.

TTA evidence conflicts:
- Perez 2018 found TTA (64 copies) helped on ISIC.
- A 2026 preprint on MedMNIST found standard-pipeline TTA *usually hurts*, by up to 31.6 points on pathology. Dermatology was the exception (+1.6% for ResNet-18). Intensity-only TTA was safer than geometric TTA.

So TTA has to be ablated per model, never assumed.

### Cited Findings
- The DINOv2 README lists two separate commands: "Logistic regression classification on ImageNet-1k" (`log_regression.py`) and "Linear classification with data augmentation on ImageNet-1k" (`linear.py`). Source: [DINOv2 README mirror](https://huggingface.co/spaces/InstantX/InstantID/raw/main/torchhub/facebookresearch_dinov2_main/README.md) [E, mirror of official repo; search-snippet level]. Paper: Oquab et al., arXiv:2304.07193 (not opened). (industry practice)
- **Medeiros DN. "I Can't Believe TTA Is Not Better: When Test-Time Augmentation Hurts Medical Image Classification." arXiv:2604.09697 (Apr 2026)** [D]. [arXiv](https://arxiv.org/abs/2604.09697).
  - Three MedMNIST v2 datasets (including dermatology and pathology) and four architectures (21K-11M parameters).
  - Standard-pipeline TTA generally reduced accuracy vs single pass. The worst case was -31.6 pp (ResNet-18, pathology), and the harm grew with more views. The exception was ResNet-18 on dermatology (+1.6%).
  - Intensity-only TTA preserved more accuracy than geometric TTA. Including the original image reduced but did not remove the harm.
  - Proposed mechanism: distribution shift amplified by batch-norm statistics mismatch.
  - Recommendation: validate TTA per model-dataset pair. (research evidence, preprint, single author)
- Perez 2018: averaging 64 augmented copies or 144 crops beat single-image inference, and test-time augmentation was what made training augmentation pay off below 500 images. Source: [ar5iv](https://ar5iv.labs.arxiv.org/html/1809.01442) [C]. (research evidence)
- Ultralytics detection TTA (`augment=True` at predict) uses three passes: scales [1, 0.83, 0.67] with flips [none, left-right, none]. It **reverts to single-scale with a warning if the model is `end2end`** or the head is not `Detect`. Source: installed 8.4.161 `ultralytics/nn/tasks.py`, `_predict_augment`; `augment: False` is the default in default.yaml [A].
  - Inference: YOLO26 is marketed as NMS-free end-to-end, so `augment=True` probably has no effect for YOLO26s. Check the warning in the logs.

### Inferences
- **Feature-level augmentation for DINOv2 + LR (inference; no reliable small-medical evidence found).**
  1. For each training-fold image, extract features from K augmented views (K = 4-10: flip, rotation ±15°, RandomResizedCrop scale 0.8-1.0, brightness/contrast ±0.1-0.15, no hue).
  2. Fit LR on all views with `sample_weight = 1/K` (or class weight × 1/K). This keeps the effective sample size and the meaning of the C regularisation unchanged.
  3. Evaluate on the un-augmented validation image, optionally also with a flip-TTA averaged *feature* or *probability*.
  - Expected gain: small. DINOv2 features are already fairly invariant to flips and crops. Run it only as an ablation.
- Cost of feature augmentation (inference): DINOv2-small (ViT-S/14, about 22M parameters) forward passes at 224 px for 120 × 10 views = 1,200 images. That is seconds to about a minute on a consumer GPU (estimate, not measured), and much less than one fine-tuning epoch. Cache features keyed by (image hash, augmentation seed, model hash). The existing `dino_features()` already caches by `base_hash`.
- **TTA (inference).**
  - With frozen EfficientNet in `eval()` mode, BN statistics are frozen, so the BN-mismatch mechanism is weaker. But the head was trained on flip/rotation views, so flip-TTA (2 views) is the safest candidate.
  - Avoid colour TTA for a redness task.
  - Report single-pass and TTA results side by side on the same folds. Choose decision thresholds on non-TTA *or* TTA validation scores consistently, never mixed.

### Gaps
- No study found of augmented-view feature banks for frozen foundation-model features with fewer than 200 medical images.
- DINOv2's own `linear.py` augmentation recipe was not opened.

---

## Q4. Ultralytics YOLO 8.4 defaults, mosaic for small lesions and tiny data, recommended values

### Takeaway
I verified the defaults in two places: the installed **Ultralytics 8.4.161** `default.yaml` and the GitHub `main` default.yaml (both read 2026-10-30). They are:

`hsv_h 0.015, hsv_s 0.7, hsv_v 0.4, degrees 0.0, translate 0.1, scale 0.5, shear 0.0, perspective 0.0, flipud 0.0, fliplr 0.5, bgr 0.0, mosaic 1.0, mixup 0.0, cutmix 0.0, copy_paste 0.0 (segment/obb only), copy_paste_mode flip, auto_augment randaugment (classify), erasing 0.4 (classify), close_mosaic 10, multi_scale 0.0, imgsz 640, batch 16, workers 8, cache False, epochs 100, patience 100, amp True, augment False`.

The default `hsv_s=0.7` (saturation ×0.3-1.7) and `scale=0.5` (objects resized ×0.5-1.5) are both aggressive for a small, redness-defined lesion. Mosaic further shrinks objects.

### Cited Findings
- Defaults are quoted verbatim from [Ultralytics default.yaml, GitHub main](https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/cfg/default.yaml) [A]. They are identical in the installed `02_主程式碼/.venv/Lib/site-packages/ultralytics/cfg/default.yaml`, `__version__ = "8.4.161"` [A]. (The installed copy says "segment/obb" for copy_paste. GitHub main says "segment/semantic/obb".)
- [Ultralytics "YOLO Data Augmentation" guide](https://docs.ultralytics.com/guides/yolo-data-augmentation/) [A]:
  - Ranges: hsv_* 0-1, degrees 0-180, perspective 0-0.001, and `scale` as a float (1-scale to 1+scale) or a (min, max) tuple.
  - Mosaic "Combines four training images into one" and is described as "Highly effective for improving small object detection and context understanding". The guide also cautions that mosaic "can also make the training process more challenging".
  - `close_mosaic` disables mosaic for the final N epochs (example: epochs=200 with close_mosaic=20 stops it after epoch 180). "Closing the mosaic also disables `copy_paste`, `mixup`, and `cutmix`".
  - General advice: "Start with a small set of augmentations and gradually add more as needed". Augmentations should "reflect the same data distribution your model will encounter in production". Use mosaic only where partial occlusion or multiple objects are acceptable.
  - `copy_paste` "requires polygon labels (segment and OBB tasks)". The guide gives **no guidance for colour-dependent or medical tasks**. (industry practice)
- HSV math (installed `augment.py` `RandomHSV`) [A]: hue LUT `(x + r0*180) % 180`, saturation `x*(1+r1)`, value `x*(1+r2)`, with `r ~ U(-1,1)*[hsv_h, hsv_s, hsv_v]`. Since 8.3.79, `lut_sat[0]=0` keeps pure white from changing colour.
- Ultralytics `classify_augmentations()` in the installed code has its own defaults (`hsv_s=0.4`, `erasing=0.0` in the function signature) that the train config overrides. Relevant only if Ultralytics classify models are used. [A]
- Mosaic for small defects: a YOLOv5 issue thread raises mosaic's effect on small defects as a concern, which maintainers acknowledged ([ultralytics/yolov5#13027](https://www.Github.com/ultralytics/yolov5/issues/13027)) [E, search snippet only]. A tutorial suggests `mosaic=0.0` for tiny datasets and quotes "~100+ images per class" ([theneuralbase](https://theneuralbase.com/yolo/learn/intermediate/mosaic-augmentation/)) [E, low reliability; not a basis for decisions].
- I found no peer-reviewed study of mosaic on fewer than 50 training images or on small skin lesions. **No reliable evidence found.**

### Inferences
- **Mosaic geometry (inference).** With imgsz 640, a mosaic tile places four images on a 1280×1280 canvas, then random-affine crops back to 640. Each source image ends up at about half its linear size before the `scale` jitter. A lesion box spanning 40 px at 640 can drop to about 20 px (and to about 10 px with scale ×0.5), near the stride-8 P3 limit.
  - With 24 boxed images, mosaic mostly recombines the same 24 lesions. It adds context diversity but also tiny-object difficulty.
  - The project's current `mosaic: 0` is a defensible baseline. Mosaic=1.0 with close_mosaic is an ablation arm, not a default.
- `copy_paste` has **no effect** with box-only labels (detect task), so leave it at 0. (inference from the docs statement)
- `erasing` and `auto_augment` affect classify only, so they are irrelevant to the detector. (from docs)
- `mixup` and `cutmix` for detection blend or paste whole images with boxes. For redness, MixUp alpha-blending halves the erythema contrast while the box keeps a "positive" label. Keep both at 0 now. (inference)
- `flipud`: smartphone photos of the hand dorsum or forearm come in arbitrary orientations. If the photo set already shows rotated or upside-down arms, flipud 0.5 and degrees 15-30 are realistic. If photos are mostly upright, keep flipud 0. Check this by eye on the 120 photos. (inference)

### Recommended YOLO values (candidates to ablate; not auto-applied)

| arg | Ultralytics 8.4.161 default | NOW (~24 boxed images, 14 patients) | FUTURE (~1,000 images) | basis |
|---|---|---|---|---|
| hsv_h | 0.015 (±5.4°) | **0.0-0.01** (current 0.01) | 0.0-0.01 | inference (redness hue = signal) |
| hsv_s | 0.7 (×0.3-1.7) | **0.0-0.2** (current 0.2) | 0.1-0.3 | inference + HSV math [A] |
| hsv_v | 0.4 (×0.6-1.4) | 0.15-0.3 (current 0.15) | 0.2-0.4 | inference (lighting variation is real) |
| degrees | 0.0 | 10-15 (current 10) | 10-30 if orientation varies | inference |
| translate | 0.1 | 0.05-0.1 | 0.1 | default / industry practice |
| scale | 0.5 (×0.5-1.5) | **0.1-0.3**, or tuple (0.8, 1.2) | 0.3-0.5 | inference (small lesions) |
| shear / perspective | 0 / 0 | 0 / 0 | 0-2 / 0-0.0005 | default |
| fliplr | 0.5 | 0.5 | 0.5 | default |
| flipud | 0.0 | 0 (0.5 only if photo orientation is arbitrary) | same rule | inference |
| bgr | 0.0 | **0 (never: swaps red/blue)** | 0 | inference |
| mosaic | 1.0 | **0** baseline; ablation arm 1.0 + close_mosaic 10 | 1.0 (or 0.5) with close_mosaic 10-15 | docs [A] + inference |
| close_mosaic | 10 | n/a if mosaic=0 | 10-15 | docs [A] |
| mixup | 0.0 | 0 | 0-0.1 (ablate) | inference |
| cutmix | 0.0 | 0 | 0 (ablate ≤0.1 only if positive) | inference |
| copy_paste | 0.0 | 0 (no effect without polygons) | 0 unless segmentation masks exist | docs [A] |
| multi_scale | 0.0 | 0 | 0-0.25 | default |
| augment (TTA, predict) | False | False; ablate True on YOLO11 only (end2end YOLO26 falls back) | same | source code [A] |
| workers | 8 | 0 (current; deterministic, Windows-safe) | 2-4 if CPU-bound (verify determinism) | PyTorch Windows notes [A] |
| cache | False | 'ram' is cheap at this size | 'ram' or 'disk' | docs [A] |

Example call (code location: `02_主程式碼/src/training/runner.py` merges `configs/train.json` into `model.train(**cfg)`; `src/workbench/adapters.py::yolo_train` for the workbench path):
```python
model.train(data=..., epochs=120, imgsz=640, batch=4, workers=0, seed=42, deterministic=True,
            hsv_h=0.0, hsv_s=0.2, hsv_v=0.2, degrees=10, translate=0.05, scale=0.2,
            fliplr=0.5, flipud=0.0, mosaic=0.0, mixup=0.0, cutmix=0.0, copy_paste=0.0, bgr=0.0)
# Ablation arm B: mosaic=1.0, close_mosaic=10 (all else equal); arm C: hsv_s=0, hsv_h=0 (= existing --no_color)
```

### Gaps
- No peer-reviewed evidence found on mosaic, scale or hsv settings for fewer than 50-image medical detection datasets, or for erythema-type targets.
- I did not verify YOLO26's `end2end` attribute in the installed weights. Check for the warning "Model does not support 'augment=True'".

---

## Q5. Augmentation and patient-grouped CV, implementation, GPU/time cost, NOW vs FUTURE

### Takeaway
Augment **after** the patient-level split, and **only** inside the training fold, on the fly. Never write augmented copies to disk before splitting. If offline copies or cached augmented features exist, each must carry the source patient ID and be filtered by fold.

Leakage through augmented copies, or through same-patient images, inflates accuracy. This is documented in OCT studies and in reporting standards.

### Cited Findings
- OCT deep-learning study (arXiv:2202.12267) [C/D]: augmented versions of the same image landing in both train and test reproduce a per-image split. Per-image splits in OCT studies reported accuracies above 95%, which the authors link to leakage. [arXiv PDF](https://arxiv.org/pdf/2202.12267) (search snippet only). (research evidence)
- REFORMS reporting standards (arXiv:2308.07832) [D]: splitting after preprocessing or oversampling causes leakage. They cite 21 pre-term-birth papers with over-optimistic results from oversampling before partitioning. [arXiv PDF](https://arxiv.org/pdf/2308.07832) (search snippet only). (research evidence)
- Longitudinal brain MRI (arXiv:2309.00350) [D]: recommends subject-wise splits for repeated scans of the same subject. [arXiv PDF](https://arxiv.org/pdf/2309.00350) (search snippet only).
- torchvision v2 `CutMix` / `MixUp` [A] ([official example](https://docs.pytorch.org/vision/stable/auto_examples/transforms/plot_cutmix_mixup.html)):
  - They operate on **batches**: "expect batches of samples as input, not individual images".
  - "neither CutMix nor MixUp are part of this pre-processing pipeline". Apply them after the DataLoader in the training loop, or in `collate_fn`.
  - Labels change from shape (batch,) to (batch, num_classes) and can be passed straight to `F.cross_entropy`.
- PyTorch Windows notes [A] ([docs 2.15](https://docs.pytorch.org/docs/2.15/notes/windows.html)):
  - Windows "uses spawn instead of fork". DataLoader code must sit under `if __name__ == '__main__':`.
  - CUDA IPC is unsupported. Workarounds are `num_workers=0` or returning CPU tensors from the Dataset.
  - No performance figures are given.

### Inferences (implementation, cost, validation)
- **Leakage rules for this platform (inference):**
  1. Split by patient first (existing StratifiedGroupKFold), then augment on the fly in training only.
  2. Validation and test use deterministic preprocessing (pad 224, no augmentation, or the declared TTA).
  3. DINOv2 augmented-view features are generated only for training-fold members, or cached for all images but *selected* by fold membership.
  4. Threshold and calibration selection must use the un-augmented validation fold.
  5. LINE submissions of the same arm on different days must share one patient ID.
  6. Repeat each ablation over several seeds, because 3 folds with only 9 normal photos give very high variance.
- **Ablation protocol (inference):**
  - Same folds, same seeds (e.g., 3 seeds × 3 folds). Arms: no-augmentation / current (flip+rot) / +mild colour / +crop / +RandAug-lite. YOLO arms: mosaic on/off and colour on/off.
  - Metrics: patient-level balanced accuracy, macro-F1 and AUROC with fold-level spread (binary); per-stage recall and adjacent-stage confusion (staging); mAP50 and recall at the low-FP operating point (YOLO).
  - Treat a difference smaller than the fold SD as no difference. With 14 patients, expect wide confidence intervals and do not claim gains from a single run.
- **Code location (inference from repository read):**
  - Per-sample transforms go in `adapters.py::tensor_image()`. Replace the PIL ops with a `torchvision.transforms.v2.Compose`, applied only when `self.augment`.
  - MixUp/CutMix go in `efficient_train()`'s batch loop, or in a DataLoader `collate_fn`.
  - TTA goes in the predictor `class_scores()/predict()` (around lines 695-712) and in `evaluate()`. The existing comment "Evaluate training fit without augmentation" at around line 915 should stay as is.
  - YOLO settings go in `configs/train.json`.
- **GPU memory and time (inference; no benchmark measured):**
  - torchvision v2 and Ultralytics augmentations run on CPU in the dataloader and add no GPU memory. MixUp/CutMix on GPU tensors are negligible.
  - With `workers=0` on Windows, augmentation is serial. At 120 images × 224 px this is milliseconds per image. At 1,000 images × 640 px with mosaic it can make YOLO training CPU-bound. Try `cache='ram'` first, then `workers=2-4` (check that `deterministic=True` reproducibility still holds).
  - Feature augmentation for DINOv2 costs K× the extraction time (seconds to minutes). TTA costs k× inference.

### Recommended classification values (EfficientNet-B0 frozen / last-stage-unfrozen; DINOv2 + LR)

| method | evidence strength | NOW (14 pts, ~120 photos) | FUTURE (~1,000, balanced) | min data (inference) | risk |
|---|---|---|---|---|---|
| Horizontal flip p=0.5 | industry practice; Perez flips helped [C] | yes (already) | yes | any | negligible (arms are left/right symmetric) |
| Rotation | Perez affine helped [C] | ±10-20° (≤45 allowed) | ±15-30° | any | padding corners; fill colour constant |
| RandomResizedCrop | Perez crops helped (40-100% area) [C] | scale (0.75, 1.0), ratio (3/4, 4/3) | (0.5, 1.0) if lesion is central, else (0.65, 1.0) | any | cropping the lesion out leaves a positive label on a lesion-free image |
| Brightness / contrast jitter | Perez mixed [C]; inference | 0.1-0.15 each | 0.15-0.25 | any | low |
| Saturation jitter | no direct evidence; inference | 0-0.05 | ≤0.1, ablate | — | changes redness = label |
| Hue jitter | no direct evidence; inference | **0** | 0-0.01 (≈±3.6°), ablate | — | rotates erythema hue |
| RandAugment | Cubuk [D]: small data → smaller M | no (or N=1, M≤3, geometric + brightness/contrast pool only) | N=1-2, M=3-5, colour ops removed | ~500+ (Perez threshold, analogy) | Solarize/Posterize/Color ops |
| TrivialAugmentWide | Müller & Hutter [B], natural images | no | ablate only with a custom op pool | ~1,000 | fixed op pool includes strong colour ops |
| AutoAugment | no medical evidence found | no | no | — | ImageNet policy |
| Random erasing | Perez: little gain or worse [C] | no | ≤0.1 ablate | — | erases lesion |
| MixUp | MediAug mixed [D]; ordinal counter-argument [D] | no | binary only, α≈0.2, ablate | ~1,000 | soft labels contradict staging |
| CutMix | MediAug mixed [D]; lesion-removal inference | no | no (or lesion-aware variant) | — | cuts out lesion |
| DINOv2 feature-bank augmentation | no direct evidence | optional ablation K=4-8, sample_weight=1/K | ablation | any | small gain; cache bookkeeping |
| TTA | Perez +[C] vs Medeiros − [D] | flip-only (2 views), ablate | flip + mild rotation, ablate | any | can hurt; report both |

torchvision v2 pseudo-code (torchvision 0.28 installed; insert in `tensor_image` / Dataset `__getitem__`, training fold only):
```python
from torchvision.transforms import v2
import torch
train_tf = v2.Compose([
    v2.ToImage(),
    v2.RandomResizedCrop(224, scale=(0.75, 1.0), ratio=(3/4, 4/3), antialias=True),  # NOW
    v2.RandomHorizontalFlip(p=0.5),
    v2.RandomRotation(degrees=15, fill=(124, 116, 104)),
    v2.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.0, hue=0.0),          # no hue/sat NOW
    # FUTURE ablation: v2.RandAugment(num_ops=1, magnitude=3) only after removing colour ops (custom subclass)
    v2.ToDtype(torch.float32, scale=True),
    v2.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])
eval_tf = v2.Compose([v2.ToImage(), v2.Resize(...)/pad-to-224, v2.ToDtype(torch.float32, scale=True), v2.Normalize(...)])

# FUTURE, binary task only (efficient_train batch loop):
mix = v2.RandomChoice([v2.MixUp(num_classes=2, alpha=0.2)])     # CutMix deliberately omitted
for x, y in loader:
    if use_mix: x, y = mix(x, y)                                  # y -> (B, 2) soft labels
    loss = torch.nn.functional.cross_entropy(model(x), y, weight=class_w)

# TTA (predict/evaluate): p = 0.5*(softmax(model(x)) + softmax(model(x.flip(-1))))

# DINOv2 feature bank (dino_train), training-fold members only:
#   feats = [dino(train_tf(img)) for img in train for _ in range(K)]; LogisticRegression(...).fit(X, y, sample_weight=1/K * class_w[y])
```
Note: the `v2.MixUp(alpha=...)` argument is standard in torchvision, but the example page I opened shows only `num_classes`. Confirm the signature locally with `help(v2.MixUp)`.

### Gaps
- No measured GPU-time or memory numbers for this hardware. These need a timing run on the platform.
- No primary evidence found on augmentation × grouped CV in dermatology specifically. The leakage sources above are from OCT, MRI and general ML, and were read at snippet level.
- Garcea et al. 2023 review, Zhang et al. 2018 (MixUp) and Yun et al. 2019 (CutMix) were not opened in this session, so their claims are not cited here.
