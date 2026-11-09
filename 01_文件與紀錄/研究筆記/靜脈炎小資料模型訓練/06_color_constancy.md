# Color constancy / color correction for clinical smartphone photos of IV sites (phlebitis research prototype)

Scope: gray-world, Shades of Gray (SoG), max-RGB/white patch, gray-edge, learned WB (FFCC, Afifi & Brown), WB augmentation, color-chart calibration; for EfficientNet-B0 / DINOv2-small+LR classification and YOLO11/26 detection, on hospital + LINE smartphone photos of arm/hand-dorsum IV sites (erythema is a key sign).

Access date for every URL below: 2026-10-30 or 2026-10-31 (session spanned midnight). Grades: [A] standards/regulators; [B] systematic review / meta-analysis / top venue (CVPR/ICCV, JAMA-family); [C] other peer-reviewed; [D] preprint; [E] blog / official code / forum (supporting only).
Conclusion labels: **research evidence** / **industry practice** / **inference**.
Verification caveat: several PDFs (Barata 2015 JBHI, Gessert 2019, ICC White Paper 46) were served as binary and could not be text-extracted in this session; for those only abstract/landing-page level facts are reported and marked "not verified in full text". Items taken from search-result summaries rather than an opened page are marked "(search summary)".

---

## Q1. Dermatology evidence for color constancy (dermoscopy vs clinical/smartphone), magnitude of gains, counter-evidence

### Takeaway
Color constancy (CC) as preprocessing has peer-reviewed support in **dermoscopy** (Barata 2015: large gains for a hand-crafted color-histogram classifier on multi-source images) and is widespread **industry/challenge practice** (SoG, p=6), but there is **no reliable controlled evidence for macroscopic smartphone photos of skin**, and the evidence that exists for deep CNNs is mixed (lesion-dependent segmentation gains; small, sometimes negative effects on in-distribution test sets). For a task whose label depends on redness, CC is plausible but must be tested by ablation, not assumed.

### Cited Findings
- **[C] Barata C, Celebi ME, Marques JS (2015).** "Improving Dermoscopy Image Classification Using Color Constancy." *IEEE J Biomed Health Inform* 19(3):1146–1152. DOI 10.1109/JBHI.2014.2336473 (online July 2014). Compared Gray World, max-RGB, Shades of Gray, General Gray World; classifier = bag-of-features using **1-D RGB color histograms only**; on **multi-source** images CC raised sensitivity **71.0% → 79.7%** and specificity **55.2% → 76%** (abstract figures). — [dblp record](https://dblp.org/rec/journals/titb/BarataCM15); [ISR Lisboa page](https://welcome.isr.tecnico.ulisboa.pt/?p=21369). *Not verified in full text: chosen p, lesion-vs-patient split, external validation.* **research evidence** (dermoscopy, hand-crafted features; gain magnitude is unlikely to transfer to CNNs whose features are not pure color histograms — **inference**).
- **[C] Ng JH, Goyal M, Hewitt B, Yap MH (2019).** "The effect of color constancy algorithms on semantic segmentation of skin lesions." *Proc. SPIE 10953, Medical Imaging 2019*, 109530R. DOI 10.1117/12.2512702. ISIC 2017 segmentation with FCNs; CC preprocessing **improved Naevi and Seborrhoeic Keratosis but not Melanoma** → benefit is class-dependent (counter-evidence to "always helps"). — [SPIE](https://biomedicaloptics.spiedigitallibrary.org/conference-proceedings-of-spie/10953/109530R/The-effect-of-color-constancy-algorithms-on-semantic-segmentation-of/10.1117/12.2512702.full) (abstract level). **research evidence**.
- **[D] Galdran A, Alvarez-Gila A, Meyer MI, López Saratxaga C, Araújo T, Garrote E, Aresta G, Costa P, Mendonça AM, Campilho A (2017).** "Data-Driven Color Augmentation Techniques for Deep Skin Image Analysis." arXiv:1703.03702 (ISIC 2017). Normalizes the training set with **SoG while keeping each image's estimated illuminant**, then at training time re-applies illuminants **sampled from the training-set illuminant distribution** = "color-constancy augmentation". Abstract reports only "promising" validation results, no numbers; p not stated on abstract page. — [arXiv](https://arxiv.org/abs/1703.03702). **research evidence (weak, preprint)**.
- **[D] statement** that SoG is "one of the most popular preprocessing techniques" in ISIC 2018 lesion segmentation and "works best with p=6" (secondary citation, not an ablation). — [arXiv 2306.14255](https://arxiv.org/pdf/2306.14255) (search summary). **industry practice**.
- **[C/B] Finlayson GD, Trezzi E (2004).** "Shades of Gray and Colour Constancy." *Proc. 12th Color Imaging Conference (IS&T/SID)*, pp. 37–41. Gray-World (p=1) and max-RGB (p=∞) are special cases of a Minkowski-norm estimator; **L6 norm performed best overall** on a large calibrated (natural-scene, not skin) dataset, comparable to more elaborate algorithms. — [UEA ePrints](https://ueaeprints.uea.ac.uk/23682); [IS&T library](https://library.imaging.org/cic/articles/12/1/art00008) (search summary of abstract). Note: p=6 was optimized on **natural scenes**, not skin close-ups — **inference**.
- **[E] Kaggle SIIM-ISIC 2020 silver-medal write-up**: CC preprocessing "significantly improved validation scores" (no controlled numbers, lesion-level). — [blog](https://amaarora.github.io/posts/2020-08-23-siimisic.html). **industry practice**, supporting only.
- **[D] Gessert N et al. (2019)** "Skin Lesion Classification Using Ensembles of Multi-Resolution EfficientNets with Meta Data." arXiv:1910.03910 (ISIC 2019 1st place). Abstract does not mention CC; full text could not be extracted, so the commonly repeated claim that this winner used SoG is **not verified here**. — [arXiv](https://arxiv.org/abs/1910.03910).
- **Smartphone/clinical photos:** a thesis-level work (humentech.utm.my) used SoG before MobileNet-v2 on smartphone clinical images (87.9% multi-class accuracy from images alone), **no ablation without CC** reported in the snippet (search summary, not opened) — no reliable controlled evidence. A 2023 DermoCC-GAN study (Politecnico di Torino, iris.polito.it) reports learned CC on dermoscopy improved classification (max accuracy 74.67%) (search summary, not opened).
- **Counter-evidence mechanism (gray-world on dominant-color scenes):** gray-world "will have very poor performance in scenes with a dominant color, or large colored surfaces, such as a close-up of a human face", and the estimate is pulled toward the skin tone so skin appears overly neutral; edge-based variants (gray-edge) only partly fix it. — van de Weijer group paper hosted at [lear.inrialpes.fr](https://lear.inrialpes.fr/people/vandeweijer/papers/cr2542.pdf) (search summary; PDF not opened, so exact title/venue not verified — the canonical gray-edge reference is van de Weijer, Gevers & Gijsenij, "Edge-Based Color Constancy", IEEE TIP 2007, cited from background knowledge, verify before formal use). **research evidence (general vision)**; applied to erythema: a frame filled with red-tinged skin is read as a reddish illuminant and part of the redness is removed — **inference** (no dermatology study found that measured this directly).
- **Patient-level splits / external validation:** none of the dermatology CC studies above (as far as abstracts show) report patient-grouped splits or external validation; ISIC datasets are lesion-level. — **no reliable evidence found** on patient-level CC effects.

### Inferences
- Gains in Barata 2015 come from a system that only sees color histograms; a CNN fine-tuned on RGB can partially learn illumination invariance, so expected gains are smaller (Afifi & Brown 2019 in Q4 show CC preprocessing gives +0.014 to +0.028 on WB-shifted test sets and −0.011 to +0.002 on clean tests for CNNs).
- Phlebitis photos differ from dermoscopy: no built-in illuminant, mixed backgrounds (sheets, tape, dressings, gloves — often near-white), and the lesion (redness) is a large fraction of the frame in stage 2. The near-white dressing/tape is actually helpful for white-patch-type estimates (**inference**).
- Because labels depend on redness, any global CC can shift class-relevant signal; the risk is highest for gray-world (p=1) on close-ups, lower for SoG p≈6 and max-RGB-like estimates that weight bright (often white tape/dressing) pixels (**inference**).

### Gaps
- No controlled study of CC on **macroscopic smartphone skin/wound photos** with a patient-grouped split was found.
- Barata 2015 full text (p choice, split protocol) not verified.
- No study found on CC effect on **erythema-graded classification** (e.g., phlebitis, cellulitis, wound redness) specifically.

---

## Q2. Color charts / reference cards; clinical photography standards

### Takeaway
A color reference card in frame is the only approach with **measured colorimetric accuracy** for wound/skin photos (ΔE roughly halves to thirds vs uncalibrated), and ISIC consensus lists color calibration among technique standards; but it needs a chart in every image, uniform lighting and unsaturated patches, which is realistic for hospital photography and **not realistic for anonymous LINE submissions** without distributing cards. No ISO/DICOM standard mandates a specific skin-photo color workflow; DICOM only provides containers (ICC profile module).

### Cited Findings
- **[C] Van Poucke S et al. (2010)** (full author list not verified this session). "Automatic colorimetric calibration of human wounds." *BMC Medical Imaging* 10:7. DOI 10.1186/1471-2342-10-7. Macbeth ColorChecker Mini in frame, single RGB→sRGB transform. vs spectrophotometer: **median ΔE_ab 6.40 calibrated vs 17.75 uncalibrated**; reproducibility median 3.43 vs 23.26 (all images), 2.83 vs 14.25 (normal settings); deliberately wrong WB and over/under-exposure tolerated; calibration rejected if ≥~6 of 24 patches saturated (white, deep red, yellow, orange most affected); **largest errors in red/orange/yellow patches**; requires chart in every image and uniform illumination; 39 Nikon D200 + 15 Canon images, 40 wound images for detection repeatability; no clinical outcome data. — [PMC2850874](https://pmc.ncbi.nlm.nih.gov/articles/PMC2850874). **research evidence**. Note authors list per standard citation; verify on publisher page before formal citation.
- **[C] Cugmas B, Štruc E (2020).** "Accuracy of an Affordable Smartphone-Based Teledermoscopy System for Color Measurements in Canine Skin." *Sensors* (MDPI) 2020. ColorChecker-based smartphone→CIELAB calibration: **ΔE 1.8–6.6 (CIE76), 1.1–4.5 (CIE94)**; erythema-index estimation errors **0.5–3%**; required **fixed manual WB and fixed exposure** and white-patch normalization; canine skin, dermoscope attachment (controlled lighting). — [PMC7662536](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7662536/) (search summary of the article; not fully opened). **research evidence (veterinary, controlled)**.
- **[C] Colorimetric calibration of wound photography with off-the-shelf devices**, Proc. SPIE 10136, 1013617 (2017), DOI 10.1117/12.2254721 (Deserno group): compared gamma correction, white balancing, background unification and **24-patch card + least-squares affine RGB transform** for chronic-wound follow-up. — [SPIE](https://www.spiedigitallibrary.org/conference-proceedings-of-spie/10136/1013617/Colorimetric-calibration-of-wound-photography-with-off-the-shelf-devices/10.1117/12.2254721.full) (abstract level, search summary).
- **[C] Nixon M et al. (2020)** "Accurate device-independent colorimetric measurements using smartphones." *PLOS ONE* (PMC7098568): cameras do not compensate ambient light automatically; a reference card corrects inter-device variation. — [PMC7098568](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7098568/) (search summary).
- **Wounds review** (HMP Global "importance of accurate color in wound photography"): calibration = placing a small target with known values next to the wound; found **no objective, measurable assessment of image accuracy in contemporary wound photography**. — [HMP](https://www.hmpgloballearningnetwork.com/site/wounds/literature-review/importance-accurate-color-wound-photography-and-data) (search summary). **industry practice gap**.
- **[B] Katragadda C et al. (2017).** "Technique Standards for Skin Lesion Imaging: A Delphi Consensus Statement." *JAMA Dermatol* 153(2):207–213. DOI 10.1001/jamadermatol.2016.3949. ISIC members, hybrid Delphi (5 rounds + 2 validation rounds); recommendation categories include lighting, background color, field of view, scale and **color calibration (2 items)**; authors state real-world feasibility/validity testing is still needed. Companion: "Proposed Technical Guidelines for the Acquisition of Clinical Images of Skin-Related Conditions" (JAMA Dermatol 2017). — [PubMed 27892996](https://pubmed.ncbi.nlm.nih.gov/27892996/). Exact wording of the color items not retrieved. **industry practice / expert consensus**.
- **[A] DICOM Supplement 221 (Dermoscopy)**, WG-19, final text Nov/Dec 2020: new dermoscopic image IOD that **includes an ICC Profile Module**; WG-19 now covers dermoscopy, total-body photography (Supplement 250, 2D TBP) and RCM. No dermatology *clinical-photo* color-calibration mandate found. — [DICOM Sup 221 PDF](https://www.dicomstandard.org/News/current/docs/sups/sup221.pdf), [WG-19 page](https://www.dicomstandard.org/activity/wgs/wg-19) (search summary). **[A]**, containers only.
- **[A/E] ICC White Paper 46 "Medical Photography Guidelines"** (International Color Consortium) recommends ICC-based color management in medical photography — [ICC](https://archive.color.org/files/whitepapers/ICC_White_Paper46-Medical_Photography_Guidelines.pdf); PDF opened but text not extractable; content **not verified**.
- **ISO 17321** (camera colour characterization): not opened in this session — **no verified content**; do not cite specifics.

### Inferences
- Hospital arm (controlled): a printed ColorChecker-type card (or even a neutral gray/white card) next to the IV site is practical and would allow true colorimetric correction and a* measurement; this is the strongest evidence-backed option (**inference from Van Poucke 2010, Cugmas 2020**).
- LINE public arm: requiring a card is impractical (users lack cards; printed cards via home printers are not colorimetric; LINE recompression and smartphone "beautify"/HDR tone mapping are non-linear, and a linear 3×3 fit assumes a roughly linear pipeline). Opportunistic references (white medical tape, white gauze, transparent dressing over skin) can serve as a white patch when present (**inference**).
- Red/orange patches have the largest calibration errors in Van Poucke 2010, i.e., the colors most relevant to erythema are the least accurately corrected (**research evidence**, relevance to erythema = **inference**).

### Gaps
- No study found that evaluated reference-card use **by lay public** in teledermatology apps (compliance, error rates).
- ISO 17321 and ICC WP46 contents not verified.
- No Taiwanese guidance (TFDA / Taiwan Dermatological Association) on clinical photo color found (not searched in depth — gap).

---

## Q3. Erythema quantification from RGB (a*, erythema index), effect of WB, skin tone

### Takeaway
CIELAB a* and RGB-derived erythema indices (EI) are the standard photo-based redness proxies, but cross-device agreement even **after** good linear calibration is only moderate for EI (ICC 0.65 in a Korean Fitzpatrick III–IV dataset), and uncalibrated smartphone color errors (ΔE00 ≈ 7–8) are far above perceptual thresholds. Therefore a* from uncalibrated LINE photos is a **relative, within-image** signal (lesion vs adjacent normal skin), not an absolute measurement.

### Cited Findings
- **[D] Kang S (2025/2026).** "The Color-Clinical Decoupling: Why Perceptual Calibration Fails Clinical Biomarkers in Smartphone Dermatology." arXiv:2512.21988v2 (v1 26 Dec 2025, v2 6 Jan 2026). AI Hub Korean Skin Condition Measurement dataset: **965 Korean subjects, Fitzpatrick III–IV, 43,424 images**; DSLR (reference) vs tablet vs smartphone. Raw ΔE00 vs DSLR **8.26 (tablet), 6.99 (smartphone)**; **0% of raw images ΔE<2**. Linear CCM (3×3 + offset, 5-fold CV) → **1.88 / 2.29 (−77% / −67%)**. Inter-device ICC(3,1) after calibration: **Melanin Index 0.767, Erythema Index 0.652 (moderate), ITA 0.455 (poor; b* ICC 0.425), L* 0.774**. Variance of ΔE: facial region η²=0.252 vs device η²=0.070 (region ≈3.6× device) → argues single-patch calibration is inadequate. Limits: healthy skin only, controlled lighting, Korean only. — [arXiv HTML](https://arxiv.org/html/2512.21988v2). **research evidence (preprint)**; highly relevant to Taiwanese skin types (East Asian, Fitzpatrick III–IV) — relevance is **inference**.
- **[C] Cugmas & Štruc 2020**: with ColorChecker calibration and fixed WB/exposure, EI estimation error 0.5–3%; a* is among common erythema indices compared against visual erythema scores (related Cugmas study). — [PMC7662536](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7662536/) (search summary). Implies EI is reliable **only under locked WB/exposure + chart** (**inference**).
- **Afifi & Brown 2019 (ICCV)**: simple diagonal (gray-world-type) correction applied to already-rendered sRGB images performs poorly compared with methods that model the camera's non-linear rendering (paper Fig. 6). — [ar5iv HTML](https://ar5iv.labs.arxiv.org/html/1912.06960). Relevance: LINE JPEGs are rendered sRGB, so any von-Kries/diagonal CC (gray-world, SoG, max-RGB) is an approximation (**inference**).
- Mechanism (gray-world on skin-dominant frames pulls estimate toward skin color) — see Q1 van de Weijer citation.

### Inferences
- **a* is shifted by WB along with everything else**: a reddish (tungsten) cast increases a* of all pixels; per-image CC removes some of this but can also remove true erythema when redness dominates. A **within-image contrast** — Δa* = median a*(lesion ROI) − median a*(reference normal skin ROI on the same arm) — is much less sensitive to global WB than absolute a* because a global diagonal cast shifts both ROIs similarly (approximately; not exact in CIELAB) (**inference**).
- For Fitzpatrick III–IV skin (most Taiwanese patients), higher melanin lowers visible redness contrast; EI agreement already only moderate in Kang 2025 for Korean skin. Do not use ITA-based skin-tone stratification from uncalibrated photos (ICC 0.455 even after calibration) (**inference from research evidence**).
- Using a* as a **verification tool** (does CC preserve class separation?) is appropriate; using it as a **ground-truth label** is not.

### Gaps
- No study of a*/EI for **phlebitis** or IV-site redness found.
- No human-skin study found comparing smartphone a* vs Mexameter/spectrophotometer under uncontrolled lighting.
- No evidence on how LINE recompression specifically affects a* (chroma subsampling 4:2:0 halves chroma resolution — general JPEG fact, not verified for LINE in this session).

---

## Q4. Learned white balance (FFCC, Afifi & Brown) and WB augmentation: evidence, availability, license, cost

### Takeaway
The strongest top-venue evidence (Afifi & Brown, ICCV 2019) says that for CNNs, **realistic WB augmentation beats both HSV/RGB jitter and WB-correction preprocessing** on WB-shifted test sets, while preprocessing gives smaller, inconsistent gains (and small losses on clean tests). The WB augmenter is MIT-licensed, offline, numpy-only — usable now. Deep WB (CVPR 2020) is research-only/non-commercial; FFCC is Apache-2.0 MATLAB, archived, needs linear raw data with ground-truth illuminants → **not worth it** for this project.

### Cited Findings
- **[B] Afifi M, Brown MS (2019).** "What Else Can Fool Deep Learning? Addressing Color Constancy Errors on Deep Neural Network Performance." *ICCV 2019*, pp. 243–252. arXiv:1912.06960. — [CVF page](https://openaccess.thecvf.com/content_ICCV_2019/html/Afifi_What_Else_Can_Fool_Deep_Learning_Addressing_Color_Constancy_Errors_ICCV_2019_paper.html); numbers from [ar5iv full text](https://ar5iv.labs.arxiv.org/html/1912.06960):
  - WB errors at test time: SmallNet CIFAR-10 top-1 **0.799 → 0.655**; AlexNet CIFAR-10 **0.933 → 0.797**; AlexNet CIFAR-100 **0.768 → 0.526**.
  - On WB-error test sets, training augmentation: HSV jitter / RGB jitter / **WB-aug**: SmallNet C10 0.747 / 0.765 / **0.786**; AlexNet C10 0.864 / 0.872 / **0.889**; AlexNet C100 0.613 / 0.645 / **0.670**.
  - WB-aug on **original** test sets: +0.010, **−0.007, −0.033** (can cost in-distribution accuracy).
  - WB **preprocessing** (WB-sRGB correction, train+test): WB-error tests +0.028 / +0.014 / +0.017; original tests +0.002 / −0.001 / **−0.011**.
  - ADE20K SegNet IoU on WB-error images 0.180 → 0.197 (WB-corrected training) / 0.199 (WB-aug).
  - Experiments are natural images at low resolution, **no medical data, no grouped splits**. **research evidence** for generic CNNs.
- **[E] WB_color_augmenter repo** (official): **MIT license**; Python (NumPy + Pillow) CLI and `WBEmulator` module; PyTorch on-the-fly demo with `aug_prob`; up to 10 WB variants per image (default), built from Rendered WB dataset Set 1; no runtime figures given; Colab example claims +3% on CIFAR-10. — [GitHub](https://github.com/mahmoudnafifi/WB_color_augmenter). Fully local/offline (**inference** from code description: numpy model file, no network calls described).
- **[B] Afifi M, Brown MS (2020).** "Deep White-Balance Editing." *CVPR 2020*. DOI 10.1109/CVPR42600.2020.00147. Official code has PyTorch (tested with PyTorch 1.2/1.5, Python 3.6); README: "provided for research purposes only and CAN NOT be used for commercial purposes"; LICENSE.md terms not read; runtime/model size not stated in README. — [GitHub](https://github.com/mahmoudnafifi/deep_white_balance). Local/offline usable for research (**inference**), old dependency versions.
- **[B] Barron JT, Tsai Y-T (2017).** "Fast Fourier Color Constancy." *CVPR 2017* (arXiv:1611.07596). Official code: **Apache-2.0, MATLAB**, **archived Nov 5 2022**; no pretrained models; training requires **linear thumbnails with black level removed + per-image ground-truth illuminant**; Google patent US10949958B2 exists. Community Python port (shuwei666/ffcc-python, Apache-2.0) not evaluated. — [GitHub google/ffcc](https://github.com/google/ffcc). LINE JPEGs are not linear raw → FFCC does not fit (**inference**).
- **[D] Galdran 2017** (Q1): SoG-normalize + resample training-set illuminants = a cheap, dependency-free version of WB augmentation tailored to the dataset's own illuminant distribution. — [arXiv](https://arxiv.org/abs/1703.03702).
- **Cloud dependency:** none of the above methods requires cloud; all can run locally. No method in this note needs third-party upload.

### Inferences
- Compute: SoG/gray-world are O(N pixels) numpy ops, ~milliseconds per 1–4 MP image on CPU (**inference** from algorithmic cost; not benchmarked). WB_color_augmenter: KNN over a small feature set + color mapping; CPU-feasible offline precompute of 10 variants × 120 photos is trivial (**inference**; not benchmarked). Deep WB: a small U-Net-style model on GPU; feasible on consumer GPU but adds dependency/maintenance (**inference**).
- For 120 photos, learned WB *correction* models trained on natural scenes are untested on skin close-ups and could hallucinate corrections that remove redness; not worth the risk/complexity NOW (**inference**).

### Gaps
- No runtime benchmarks found for WB_color_augmenter or Deep WB on consumer GPUs.
- No study of WB augmentation on medical skin images with patient-level evaluation.

---

## Q5. Recommended pipeline NOW vs FUTURE; ablation design; implementation

### Takeaway
**NOW (14 patients, ~120 photos):** do **not** adopt any color correction as a fixed preprocessing step by default. Keep raw sRGB as the baseline; add **mild, illuminant-realistic color augmentation** (SoG-illuminant resampling à la Galdran, or WB_color_augmenter, MIT) to classifier training; run a small, pre-registered ablation (raw / SoG-p6 preprocessing / WB-aug) with patient-grouped CV, reported per source, and treat any difference as exploratory (n=14 patients cannot resolve small effects). Add a **color-cast flag** to the quality check rather than silently correcting. **FUTURE (~1,000 photos):** re-run the same ablation with enough power; decide preprocessing vs augmentation per model from data; introduce a reference card in the hospital arm to obtain calibrated subsets for verification.

### Cited Findings (basis for the recommendation)
- Augmentation > preprocessing for CNN robustness to WB shifts; preprocessing gains small and can be negative on clean tests — Afifi & Brown ICCV 2019 [ar5iv](https://ar5iv.labs.arxiv.org/html/1912.06960). **research evidence (natural images)**.
- CC benefit is class-dependent (not for melanoma) — Ng et al. SPIE 2019 [SPIE](https://biomedicaloptics.spiedigitallibrary.org/conference-proceedings-of-spie/10953/109530R/The-effect-of-color-constancy-algorithms-on-semantic-segmentation-of/10.1117/12.2512702.full). **research evidence**.
- SoG p=6 is the popular dermoscopy default — [arXiv 2306.14255](https://arxiv.org/pdf/2306.14255); L6 best on natural scenes — [Finlayson & Trezzi 2004](https://ueaeprints.uea.ac.uk/23682). **industry practice**.
- Large multi-source gains with a color-histogram classifier — Barata 2015 [dblp](https://dblp.org/rec/journals/titb/BarataCM15). **research evidence (dermoscopy)**.
- Reference card gives measurable accuracy but needs chart in every frame — Van Poucke 2010 [PMC2850874](https://pmc.ncbi.nlm.nih.gov/articles/PMC2850874). **research evidence**.

### Per-method summary (evidence strength / benefit / minimum data / cost / risk)

| Method | Evidence strength (this use case) | Expected benefit; when not worth it | Min data | Compute (basis) | Main risks | Role recommended |
|---|---|---|---|---|---|---|
| Gray-world (SoG p=1) | Weak: dermoscopy only; known failure on dominant-color close-ups | Low; **not worth it** when skin/redness fills frame | none (unsupervised) | ms/image CPU (inference) | Removes erythema; over-neutralizes skin | Do not use as preprocessing; at most as one arm of ablation |
| Shades of Gray p=6 | Moderate for dermoscopy (Barata 2015, challenge practice); none for smartphone clinical | Possible gain on hospital vs LINE domain gap; unknown on redness | none | ms/image CPU (inference) | Partial redness removal; estimate driven by bright tape/dressing (helpful) or specular glare (harmful) | **Ablation arm NOW**; preprocessing only if FUTURE ablation supports it |
| max-RGB / white-patch | Weak; fails with clipped highlights (LINE/phone HDR) | Useful only if a known white object (tape/gauze/card) exists | none | ms/image | Saturated pixels → wrong estimate; use 99th percentile not max | Use as **ROI-based white patch** when tape/card is annotated (FUTURE) |
| Gray-edge (1st order, p=6, σ=2) | Weak; better than gray-world in theory on dominant-color scenes (van de Weijer 2007) | Unknown; edges are dominated by catheter/tape | none | ~tens of ms (Gaussian derivatives) | JPEG block edges in LINE photos bias estimate (inference) | Optional ablation arm FUTURE only |
| SoG-illuminant resampling augmentation (Galdran 2017) | Weak–moderate (preprint) + supported by ICCV 2019 logic | Robustness to source/lighting shift without destroying training signal | ≥ few dozen images to estimate illuminant distribution (inference) | negligible | Too-wide sampling creates unrealistic colors; may cost clean-set accuracy (ICCV: −0.007 to −0.033) | **Recommended NOW** for EfficientNet; FUTURE keep |
| WB_color_augmenter (Afifi & Brown 2019, MIT) | Moderate (ICCV, natural images) | Same as above, more realistic camera-rendered casts | none (pretrained on Rendered WB set) | CPU, offline precompute (inference) | Same as above | Alternative to SoG resampling; pick one, not both, NOW |
| Deep WB (CVPR 2020) | Moderate for natural images; none for skin | Not worth it NOW | none (pretrained) | GPU U-Net (inference) | Research-only license; may "correct" redness; old deps | Do not use NOW; maybe FUTURE as ablation |
| FFCC | Strong in CC benchmarks; needs linear raw + GT illuminants | **Not applicable** (sRGB JPEG from LINE) | hundreds of raw images with GT | MATLAB | Archived repo | Do not use |
| Color chart / reference card | Strongest colorimetric evidence (ΔE 17.75→6.40) | High for hospital arm measurement; impractical for LINE public | 1 chart per photo | ms (linear fit) | Saturated red/orange patches; non-uniform light; workflow burden | FUTURE hospital-arm protocol; also gold-standard check of CC methods |

### Recommended pipeline — NOW (14 patients, ~120 photos)
1. **Baseline stays raw sRGB** (after EXIF transpose) for all three model families. Rationale: n=14 patients; any preprocessing that changes redness can create or remove label signal; effect sizes in literature (+0.01–0.03 for CNNs) are smaller than fold-to-fold noise expected with 14 patients (**inference**).
2. **Classifier augmentation (EfficientNet-B0):** add one illuminant-realistic color augmentation, applied with probability 0.5 on train only: (a) SoG-illuminant resampling — estimate per-image SoG (p=6) illuminant on the **training fold only**, store the set, at training time divide by own illuminant and multiply by a randomly drawn training illuminant, optionally interpolated (α∈[0,1]) toward the original to limit strength; or (b) WB_color_augmenter (MIT, offline). Keep current flip/rotation. Do **not** add hue jitter (hue shifts move red toward orange/pink and directly corrupt the erythema cue — **inference**); if using brightness/contrast, keep ±10–15%.
3. **DINOv2-small + logistic regression (frozen):** augmentation is irrelevant unless features are computed for augmented copies; NOW compare only raw vs SoG-p6-preprocessed features (two runs). Feature caching in `dino_features()` must key on the preprocessing setting (base_hash) to avoid stale cache (**inference** from code structure).
4. **YOLO11n detection:** Ultralytics hsv_h/hsv_s/hsv_v are already applied as random augmentation; the project already has a `no_color` switch (sets hsv_* to 0) in `02_主程式碼/src/training/runner.py` (line ~63). Recommendation NOW: keep `hsv_h` small (≤0.005; the Ultralytics default hsv_h=0.015 — from Ultralytics docs, not re-verified this session; check the project's config — shifts hue by up to ±0.015 of the hue circle ≈ ±5°, which for erythema is non-trivial — **inference**), keep hsv_s/hsv_v moderate; do not add CC preprocessing for YOLO (localization of the IV site does not depend on precise color — **inference**). Ablation: `no_color` vs default vs hsv_h=0.005.
5. **Quality check (warn, never auto-correct silently):** extend `02_主程式碼/src/workbench/flags.py::measure()` with a **color-cast metric**: SoG(p=6) illuminant estimate normalized to unit-sum chromaticity; flag when max channel ratio (e.g., R/G or B/G of the estimate) departs from neutral beyond a threshold set from the hospital-photo distribution (e.g., outside its 2.5–97.5 percentile). Report as a warning like other reasons; human decides. Also flag **clipped-highlight fraction per channel** (R>250) because red clipping destroys erythema gradation.
6. **Inference consistency:** whatever preprocessing a model was trained with must be recorded in the experiment record (experiment.json) and applied identically in `ModelPredictor.predict` (`adapters.py` ~line 712) — CC must run **before** `tensor_image()` padding (which pads with RGB (124,116,104)); padding before CC would bias the estimate toward that gray (**inference** from code).
7. **No auto-adoption:** results of the ablation are reported to the human; switching default preprocessing requires confirmation (project principle).

### Recommended pipeline — FUTURE (~1,000 photos, 3 balanced classes)
1. Re-run the full ablation (below) with 5-fold patient-grouped CV (or repeated 3-fold) and per-source reporting; adopt SoG preprocessing **only** if it improves the LINE-source macro-F1/AUC without degrading hospital-source performance and passes the a* preservation check.
2. Hospital arm: add a small reference card (ColorChecker-type or at minimum a neutral gray + white patch) in frame for a **calibration subset** (e.g., ≥100 photos). Use it to (a) compute card-based ground-truth illuminant, (b) measure angular error of SoG/gray-world/gray-edge/max-RGB on *your* photos (choose p empirically, e.g., p∈{1,2,4,6,8,∞}), (c) measure lesion a* in calibrated colorimetric space. This turns CC choice into a measured decision (**inference**, method from Van Poucke 2010 / Cugmas 2020).
3. LINE arm: instruct users (optional) to include a white object (tissue/paper) near the site; annotate a "white reference" box in a subset to allow ROI white-patch correction and to validate global CC (**inference**; no evidence on lay compliance — gap).
4. Consider training-time **domain mixing** (WB-aug strength tuned on hospital→LINE transfer) and report **leave-source-out** evaluation (train hospital → test LINE and vice versa) as a stress test.
5. Deep WB / learned methods: only as an extra ablation arm, research-use license respected, offline.

### Ablation design (patient-grouped, per-source)
- **Splits:** StratifiedGroupKFold (group = patient), 3 folds NOW (as in project), 5 folds FUTURE; same fold assignment for all arms (paired comparison). Seeds: ≥3 repeats with different fold shuffles NOW because of 14 patients.
- **Arms (classification):** A0 raw; A1 SoG p=6 preprocessing (train+inference); A2 raw + SoG-illuminant-resampling aug; A3 raw + WB_color_augmenter; (FUTURE) A4 gray-world p=1; A5 gray-edge; A6 card-calibrated subset.
- **Arms (YOLO):** default hsv; `no_color`; hsv_h=0.005; (optional) SoG preprocessing.
- **Metrics:** binary — AUROC, sensitivity/specificity at a fixed threshold, balanced accuracy; staging — macro-F1, per-class recall, quadratic-weighted kappa; YOLO — mAP50, mAP50-95. Report **per source (hospital vs LINE)** and per fold; patient-level aggregation (mean of per-photo probabilities per patient-visit) as a secondary analysis.
- **Statistics:** paired per-patient differences; bootstrap over patients for CIs. NOW: with 9 normal photos (from few patients) differences are **exploratory only**; state that explicitly; no claims of improvement unless CI excludes 0 (**inference**).
- **Robustness test (NOW, cheap):** evaluate each trained A0–A3 model on the held-out fold with **synthetic casts** (WB_color_augmenter variants or SoG-illuminant swaps) — reproduces the ICCV 2019 protocol on your data; measures sensitivity to lighting rather than claiming clinical accuracy.
- **Redness-preservation check (required for any preprocessing arm):** see code below.

### Implementation (numpy/OpenCV; code locations in this repo)
Suggested new module: `02_主程式碼/src/workbench/color.py` (pure functions, unit-tested); called from `flags.py::measure()` (quality metric), the EfficientNet dataset `__getitem__` in `adapters.py::efficient_train` (~line 246–260, before `tensor_image`), `dino_features()` (~line 400), and `ModelPredictor.predict()` (~line 712). Record `color_preprocess` and `color_aug` in the experiment config (`contracts.py` Experiment) so inference reproduces training.

```python
import numpy as np, cv2

def _lin(srgb):  # optional: approximate linearization of sRGB (0..1)
    return np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)

def _delin(lin):
    return np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(lin, 1 / 2.4) - 0.055)

def estimate_illuminant(rgb_u8, p=6, mask=None, clip_hi=250, clip_lo=5):
    """Minkowski-norm (Shades of Gray) illuminant estimate.
    p=1 -> gray-world; p=6 -> SoG (Finlayson & Trezzi 2004); p=np.inf -> max-RGB.
    mask: optional bool HxW to restrict pixels (e.g., exclude lesion ROI, or use only a white-tape ROI)."""
    x = rgb_u8.astype(np.float64)
    valid = np.all((x < clip_hi) & (x > clip_lo), axis=2)       # drop clipped/dark pixels
    if mask is not None:
        valid &= mask
    px = _lin(x[valid] / 255.0)                                   # N x 3, linear-ish
    if px.shape[0] < 500:
        return None                                               # too few pixels -> do not correct
    if np.isinf(p):
        e = np.percentile(px, 99, axis=0)                         # robust max-RGB (white patch)
    else:
        e = np.power(np.mean(np.power(px, p), axis=0), 1.0 / p)
    return e / (np.linalg.norm(e) + 1e-12)                        # unit-norm illuminant

def apply_von_kries(rgb_u8, e, target=None, strength=1.0):
    """Diagonal correction: map illuminant e to target (default neutral). strength in [0,1] blends."""
    target = np.ones(3) / np.sqrt(3) if target is None else target
    gain = target / np.maximum(e, 1e-6)
    gain = gain / gain[1]                                         # keep green fixed -> preserve luminance roughly
    gain = 1.0 + strength * (gain - 1.0)
    lin = _lin(rgb_u8.astype(np.float64) / 255.0) * gain
    return (np.clip(_delin(np.clip(lin, 0, 1)), 0, 1) * 255 + 0.5).astype(np.uint8)

def shades_of_gray(rgb_u8, p=6, mask=None):
    e = estimate_illuminant(rgb_u8, p=p, mask=mask)
    return rgb_u8 if e is None else apply_von_kries(rgb_u8, e)

def gray_edge(rgb_u8, p=6, sigma=2.0):
    """1st-order gray-edge (van de Weijer et al. 2007)."""
    x = _lin(rgb_u8.astype(np.float64) / 255.0)
    x = cv2.GaussianBlur(x, (0, 0), sigma)
    gx = cv2.Sobel(x, cv2.CV_64F, 1, 0); gy = cv2.Sobel(x, cv2.CV_64F, 0, 1)
    mag = np.sqrt(gx ** 2 + gy ** 2).reshape(-1, 3)
    e = np.power(np.mean(np.power(mag, p), axis=0), 1.0 / p)
    e = e / (np.linalg.norm(e) + 1e-12)
    return apply_von_kries(rgb_u8, e)

# --- Training-time "color constancy augmentation" (Galdran et al. 2017 idea) ---
class IlluminantAug:
    def __init__(self, train_images_u8, p=6, prob=0.5, max_strength=1.0, rng=None):
        ills = [estimate_illuminant(im, p=p) for im in train_images_u8]   # TRAIN FOLD ONLY
        self.ills = np.array([e for e in ills if e is not None]); self.p = p
        self.prob = prob; self.max_strength = max_strength
        self.rng = rng or np.random.default_rng()
    def __call__(self, rgb_u8):
        if self.rng.random() > self.prob or len(self.ills) == 0:
            return rgb_u8
        e_own = estimate_illuminant(rgb_u8, p=self.p)
        if e_own is None:
            return rgb_u8
        e_new = self.ills[self.rng.integers(len(self.ills))]
        s = self.rng.uniform(0, self.max_strength)
        # remove own illuminant, add a sampled one: gain = e_new / e_own
        return apply_von_kries(rgb_u8, e_own, target=e_new, strength=s)

# --- Quality-check color-cast metric (warn only) ---
def color_cast(rgb_u8, p=6):
    e = estimate_illuminant(rgb_u8, p=p)
    if e is None:
        return {'cast_rg': None, 'cast_bg': None}
    return {'cast_rg': float(e[0] / e[1]), 'cast_bg': float(e[2] / e[1]),
            'red_clip_frac': float((rgb_u8[..., 0] >= 250).mean())}
```

Parameters: p=6 (default; tune p∈{1,2,4,6,8,∞} FUTURE using card subset); clip_hi=250 / clip_lo=5; gray-edge σ=2; augmentation prob 0.5, strength U(0,1). Order in pipeline: load → EXIF transpose → (optional CC) → resize/pad (`tensor_image`) → model-specific aug → normalize. For YOLO, CC preprocessing (if adopted) must be applied to saved training images **and** at inference; Ultralytics hsv aug then operates on the corrected images (it compounds — reduce hsv_h when CC is on).

**Redness-preservation verification (run before adopting any preprocessing):**
```python
def lab_a(rgb_u8):  # OpenCV 8-bit Lab: a in [0,255], 128 = neutral
    lab = cv2.cvtColor(rgb_u8, cv2.COLOR_RGB2LAB).astype(np.float32)
    return lab[..., 1] - 128.0

# For each photo with a lesion ROI (YOLO box or hand ROI) and a reference normal-skin ROI on the same arm:
#   a_les = median(lab_a(img)[lesion]); a_ref = median(lab_a(img)[ref]); d_a = a_les - a_ref
# Compute for raw and for each CC variant. Report per class (normal / stage1 / stage2) and per source:
#   - distribution of a_les and d_a (median, IQR)
#   - separability: AUROC of d_a for phlebitis vs normal; Spearman rho of d_a vs stage; Cliff's delta between stages
# Acceptance rule (inference): CC must not reduce AUROC/rho of d_a by more than its bootstrap-over-patients CI,
# and should reduce the hospital-vs-LINE gap in a_ref (normal skin) — that is the intended effect.
```
Note: OpenCV's 8-bit Lab assumes sRGB/D65; values are approximate CIELAB, adequate for relative before/after comparison, not for absolute colorimetry (**inference**).

### Inferences
- The source/domain gap (hospital vs LINE) is likely driven by illumination, camera rendering, and LINE recompression together; CC addresses only the global-illuminant part. Leave-source-out evaluation is the honest way to measure the gap (**inference**).
- WB augmentation is the lower-risk choice NOW because it never changes inference-time inputs and cannot erase redness in test images; its main risk (slight in-distribution accuracy loss) is measurable in the ablation (**inference** from ICCV 2019 numbers).
- If SoG preprocessing is ever adopted, computing the illuminant on a mask that **excludes the lesion ROI** (or uses only near-white pixels like tape/gauze) reduces erythema removal; this requires the YOLO box at inference (two-stage pipeline) (**inference**).

### Gaps
- No empirical data on this project's photos yet (illuminant distribution per source, a* separability) — must be measured by the ablation above.
- No literature found on phlebitis/IV-site photo color normalization; all recommendations are transferred from dermoscopy, wound imaging, and generic CNN robustness work.
- Runtime of WB_color_augmenter / Deep WB on the user's GPU not benchmarked.
- LINE image recompression parameters (quality, chroma subsampling, max resolution) not verified from an official LINE source in this session.
