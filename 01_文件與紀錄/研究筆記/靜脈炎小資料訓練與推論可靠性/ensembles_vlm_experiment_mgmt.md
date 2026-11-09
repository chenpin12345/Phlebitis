# Ensembling / TTA / distillation, local vision-language models, and hyperparameter search, tracking and reproducibility for a tiny phlebitis-photo research platform

Scope note for the report writer: access date for every web source below is 2026-10-30/31 unless stated. Source grades: [A] official docs / regulators / reporting guidelines / official model cards; [B] top peer-reviewed venue or systematic review; [C] other peer-reviewed; [D] preprint (arXiv/medRxiv); [E] blogs, forums, third-party guides, vendor registry pages (supporting only). Evidence labels: "Research evidence shows" = cited finding; "Industry practice" = docs/vendor practice; "This report's inference" = written in the Inferences subsections only.

Project constants used in inferences: ~120 photos, 14 patients, binary positive 47 / normal 9, stage normal 9 / stage1 23 / stage2 24, ~24 boxed photos, single annotator, patient-level StratifiedGroupKFold 3-fold, optional held-out ~20% patients (~14-18 photos, i.e. only ~3 patients).

Cross-cutting evidence gap: a search for photo-based phlebitis / IV-site AI found no published peer-reviewed classifier with reported performance — 未找到可靠證據. The closest items are trial registrations without results: ClinicalTrials.gov NCT07889895 (AI prediction of PIVC-related phlebitis from mobile-phone photos graded with the Visual Infusion Phlebitis scale; planned metrics include sensitivity, specificity, F1 and calibration) — [Source](https://clinicaltrials.gov/study/NCT07889895) [A, registry]; and a DeepCath registry entry (deep learning on catheter exit-site photographs, enrolling) — [Source](https://ctv.veeva.com/study/identifying-local-signs-at-the-catheter-insertion-site-with-artificial-intelligence) [E]. Related imaging work is ultrasound-based, not photos. So every applicability statement for phlebitis below is extrapolated from dermatology / general medical imaging.

---

## A1. Using the 3 CV fold models as an ensemble at inference (and evaluating it without leakage)

### Takeaway
Research evidence shows that deep ensembles reliably improve calibration and robustness, and that roughly 5 members is enough. Gains are smaller and noisier on small, patient-clustered data. Averaging the 3 fold models is cheap and reasonable, but its performance can only be reported on patients that none of the 3 models saw (a held-out test set or nested CV). The out-of-fold CV score describes single fold models, not the ensemble.

### Cited Findings
- Research evidence shows: Lakshminarayanan, Pritzel & Blundell (DeepMind), "Simple and Scalable Predictive Uncertainty Estimation using Deep Ensembles", arXiv:1612.01474 (v3 2017-11-04; published at NIPS 2017, a venue the search did not independently confirm). Ensembles trained with proper scoring rules give calibrated uncertainty "as good or better than approximate Bayesian NNs" and higher uncertainty on OOD examples — [Source](https://arxiv.org/abs/1612.01474) [B]
- Research evidence shows: Ovadia et al., "Can You Trust Your Model's Uncertainty? Evaluating Predictive Uncertainty Under Dataset Shift", NeurIPS 2019 (arXiv:1906.02530). Deep ensembles were the most robust method under dataset shift, and "a relatively small ensemble size (e.g., 5) is sufficient". Under shift, models become "confidently wrong". Temperature scaling improved in-distribution calibration but often made calibration worse under shift — [Source, Google Research blog 2020-01-15 summarising the paper](https://research.google/blog/can-you-trust-your-models-uncertainty/) [E summary of a B paper; exact figures not re-checked in the paper]
- Research evidence shows (medical): Mehrtash A, Wells WM, Tempany CM, Abolmaesumi P, Kapur T. "Confidence Calibration and Predictive Uncertainty Estimation for Deep Medical Image Segmentation." IEEE Trans Med Imaging 2020;39(12):3868-3878. doi:10.1109/TMI.2020.3006437. FCNs are poorly calibrated and overconfident, and ensembling consistently improved confidence calibration across brain, heart and prostate segmentation — [Source](https://pmc.ncbi.nlm.nih.gov/articles/PMC7704933) [B]. Leakage/external-validation note: this is segmentation on public MRI datasets, not small-data classification. Whether its splits were patient-level and whether it tested on an external site was not verified in this session.
- Research evidence / industry practice (dermatology): Ha Q, Liu B, Liu F. "Identifying Melanoma Images using EfficientNet Ensemble: Winning Solution to the SIIM-ISIC Melanoma Classification Challenge." arXiv:2010.05351 (2020). The ensemble combined EfficientNet B3-B7, SE-ResNeXt-101 and ResNeSt-101 at several input sizes, with 5-fold CV on 2018-2020 ISIC data. It reached CV AUC 0.9600 and private leaderboard AUC 0.9490. The authors credit "a stable validation scheme", the prediction target, a tuned pipeline, and ensembling "very diverse models" — [Source](https://arxiv.org/abs/2010.05351) [D]. Note: this is a dermoscopy dataset of tens of thousands of images, three orders of magnitude larger than this project. The private leaderboard is an external test of sorts, but drawn from the same challenge distribution.
- Research evidence shows (selection/variance): Bouthillier et al. "Accounting for Variance in Machine Learning Benchmarks", MLSys 2021 (arXiv:2103.03098). Variance from data sampling, initialization and hyperparameter choice "impact markedly" benchmark outcomes — [Source](https://proceedings.mlsys.org/paper_files/paper/2021/hash/0184b0cd3cfb185989f858a1d9f5c1eb-Abstract.html) [B]
- Research evidence shows (why the leakage caveat matters): Varma & Simon (2006) show that error estimates are biased when any selection or training step happens outside the evaluation loop. Nested CV is nearly unbiased (details in C1) — [Source](https://pmc.ncbi.nlm.nih.gov/articles/PMC1397873) [B]

### Inferences
This report's inference:
- **Leakage-free evaluation of a fold ensemble.** Each of the 3 fold models was trained on about 2/3 of the patients, so every CV image was in the training set of 2 of the 3 models. Scoring the averaged ensemble on CV images therefore leaks. Valid options:
  - (a) Freeze the patients in a held-out set before any CV, train the 3 fold models on the rest, and score the ensemble once on the held-out patients.
  - (b) Nested CV. An outer patient-level split leaves patients out; inside each outer training set, run 3-fold CV and average the 3 inner models; score that ensemble on the outer test patients. With 14 patients, the outer loop could be leave-2-patients-out (7 outer folds), stratified as well as possible by stage.
  - (c) Report the out-of-fold (OOF) CV metric as "single-model performance". Label any ensemble number as "ensemble, evaluated on held-out patients only".
  - Never tune the ensemble's weights or decision threshold on the same OOF predictions and then report them as final.
- **NOW (120 photos / 14 patients).**
  - Expected benefit: modest. Probably slightly better calibration and lower variance from individual folds, with no reliable accuracy gain. With 3 members, ensemble variance reduction is limited (Ovadia suggests ~5).
  - The held-out set of ~3 patients is too small to show any difference between single model and ensemble. Example from this report's Wilson calculation: 0 false alarms out of 9 normal photos gives a 95% CI of 0-30%. The 9 normal photos also come from very few patients, so the effective n is smaller still.
  - Use the ensemble mainly to produce a disagreement/uncertainty signal (variance across folds) shown to the human reviewer, not as a performance claim.
- **FUTURE (~1,000 photos, 3 classes balanced).** A 5-member ensemble (5 folds, or 5 seeds on full training data) becomes worthwhile for calibration and stability. Nested CV or a properly sized patient-level test set (dozens of patients) can show the benefit. Number of patients, not photos, determines evidential value.
- **Minimum data.** No source gives a minimum. Practically, at least enough held-out patients per class that Wilson CIs on balanced accuracy are narrower than the expected gain (inference).
- **Wiring into the stack.** Store the 3 fold checkpoints with a shared `ensemble_id` in SQLite. At inference, load the members in FastAPI, average softmax probabilities (EfficientNet-B0) or logistic-regression probabilities (DINOv2), and return the mean plus the per-member spread. For YOLO, Ultralytics detection ensembling needs box fusion such as WBF/NMS across models. That is extra engineering; keep detection single-model for now. The snapshot diff should record "ensemble vs. best single fold" on held-out patients only.
- **GPU estimate.** Inference-only cost scales linearly with the number of members. EfficientNet-B0 / DINOv2-small forward passes are small, so 3-5 members fit easily in 8 GB VRAM. Training cost equals the CV you already run, so there is no extra training for a fold ensemble. These are inferences; no benchmark was measured.
- **Risks.**
  - The ensemble can be presented as "more accurate" without valid evidence.
  - Fold models trained on very different patient subsets may disagree wildly, which is informative but needs a UI explanation.
  - Calibration gains measured in-distribution may not hold for LINE-uploaded photos (Ovadia: shift makes models confidently wrong).

### Gaps
- No study found on fold-model ensembles specifically for very small (<20 patient) medical photo datasets — 未找到可靠證據.
- ISIC-challenge ensemble benefits on small subsets were not quantified in sources found.
- Exact ensemble-size curves from Ovadia 2019 were not re-verified in the paper itself.

---

## A2. Test-time augmentation (TTA): benefit, harm, calibration

### Takeaway
TTA is not a free gain. Research evidence shows that it can raise average accuracy while flipping many correct predictions to wrong ones. A 2026 preprint reports large accuracy drops in medical image classification with standard geometric TTA. TTA does help uncertainty estimation in segmentation and post-hoc calibration in skin-cancer classification. For this project, TTA belongs only as a pre-registered, evaluated option (mild flips or intensity changes), and is best used as an uncertainty signal rather than for accuracy.

### Cited Findings
- Research evidence shows: Shanmugam D, Blalock D, Balakrishnan G, Guttag J. "Better Aggregation in Test-Time Augmentation." ICCV 2021, pp. 1214-1223 (arXiv:2011.11156). TTA can raise net accuracy while changing many correct predictions to incorrect. Simple averaging is suboptimal, and the paper proposes learned aggregation — [Source](https://openaccess.thecvf.com/content/ICCV2021/html/Shanmugam_Better_Aggregation_in_Test-Time_Augmentation_ICCV_2021_paper.html) [B]
- Research evidence shows (harm in medical classification, preprint): "I Can't Believe TTA Is Not Better: When Test-Time Augmentation Hurts Medical Image Classification", arXiv:2604.09697 (April 2026, single author; peer review not confirmed). On 3 MedMNIST v2 benchmarks, standard-pipeline TTA "consistently degrades accuracy" relative to single-pass inference, by up to 31.6 percentage points for ResNet-18 on pathology. The author attributes this to distribution shift between augmented inputs and the training distribution. Intensity-only augmentations were less harmful than geometric ones — [Source](https://arxiv.org/abs/2604.09697) [D]. Leakage note: MedMNIST official splits; patient-level separation was not verified. No external validation.
- Research evidence shows (uncertainty, segmentation): Wang G, Li W, Aertsen M, Deprest J, Ourselin S, Vercauteren T. "Aleatoric uncertainty estimation with test-time augmentation for medical image segmentation with convolutional neural networks." Neurocomputing 2019;338:34-45 (MEDLINE lists vol 335). doi:10.1016/j.neucom.2019.01.103. TTA-based uncertainty beat test-time dropout alone and reduced overconfident incorrect predictions (fetal brain and brain tumour MRI) — [Source](https://arxiv.org/abs/1807.07356) [B/C]. Leakage/external-validation details not verified.
- Research evidence shows (calibration, skin): Hekler A, Brinker TJ, Buettner F. "Test Time Augmentation Meets Post-hoc Calibration: Uncertainty Quantification under Real-World Conditions." AAAI 2023;37(12). doi:10.1609/aaai.v37i12.26735. A TTA extension of post-hoc calibration gave "substantially better calibration" across architectures, with a skin-cancer application — [Source](https://ojs.aaai.org/index.php/AAAI/article/view/26735) [B]. Dataset size and patient-level split were not verified.
- Research evidence (theory): Kimura M. "Understanding Test-Time Augmentation." ICONIP 2021 (1):558-569 (arXiv:2402.06892). A theoretical treatment noting that TTA's empirical success lacks theoretical grounding — [Source](https://arxiv.org/abs/2402.06892) [C]

### Inferences
This report's inference:
- **Applies when** the TTA transforms are ones the model saw in training: horizontal flip is plausible for arm photos, along with small rotations, since the classifier already offers a rotation aug option, and small brightness changes.
- **Does not apply** to transforms that change clinically meaningful colour (redness is a key phlebitis sign) or that crop out the lesion. Colour jitter at test time could directly alter the decision signal.
- **NOW.** Do not adopt TTA for accuracy. If tried at all, pre-register one small set (identity + h-flip + ±10° rotation, mean of probabilities) and compare it to single-pass inference on the same OOF predictions, reported with CIs. Expect no detectable difference with 14 patients. Use the TTA spread (variance across augmentations) as an extra "uncertain, needs human review" flag, which matches the human-confirmation principle.
- **FUTURE.** Evaluate TTA together with calibration metrics (ECE/Brier) per class on held-out patients. Consider learned aggregation (Shanmugam) only if a separate calibration split exists, otherwise it is another tuned component that leaks.
- **Minimum data.** Not established by any source (未找到可靠證據).
- **Wiring.** In the FastAPI inference service, add a `tta_policy` field (stored with each prediction in SQLite) and log both single-pass and TTA outputs so snapshot diff can compare them. Ultralytics detection supports `augment=True` at predict time. Whether this helps on YOLO11/26 for this data is unknown, and it is an inference that it should be evaluated before use.
- **GPU.** Cost is K times the number of forward passes (K≈3-8). This is negligible for B0 / DINOv2-small on any 8 GB card. Combined with a 3-model ensemble that is 9-24 passes per photo, still interactive (inference).
- **Risks.** Silent accuracy loss (MedMNIST preprint). Overconfidence is not fixed by TTA under shift. Calibration may change, so recalibrate and re-report after enabling it.

### Gaps
- No TTA study on clinical (non-dermoscopic) skin photos or IV sites — 未找到可靠證據.
- Effect of TTA on calibration in small classification datasets with patient clustering was not found.

---

## A3. Knowledge distillation (KD) to small models — worth it when inference already runs on a GPU?

### Takeaway
KD (Hinton et al. 2015) usually improves student accuracy, but Stanton et al. (NeurIPS 2021) show that students often fail to match the teacher (low fidelity). Distilling DINOv2 into a small CNN has been reported in medical benchmarks, with inconsistent results across tasks. With ~120 photos and GPU inference already available, KD has little to offer now. It mainly matters for future on-device or CPU deployment, and it adds a model whose behaviour must be re-evaluated in full.

### Cited Findings
- Research evidence shows: Stanton S, Izmailov P, Kirichenko P, Alemi AA, Wilson AG. "Does Knowledge Distillation Really Work?" NeurIPS 2021 (arXiv:2106.05945). KD can improve student generalization but "often fails" to transfer the teacher's predictive distribution. Fidelity is hard to achieve even with interventions, and the best fidelity reached only about 85% top-1 agreement in their augmentation study. Enlarging the distillation set makes optimization harder — [Source](https://arxiv.org/abs/2106.05945) [B] (details from abstract/poster-level summaries)
- Hinton, Vinyals & Dean, "Distilling the Knowledge in a Neural Network" (arXiv:1503.02531, 2015): the original soft-target KD formulation. Not re-fetched in this session; cite as the canonical reference [D].
- Research evidence (medical, foundation-model teacher): "MedAlmighty: enhancing disease diagnosis with large vision model distillation", Frontiers in Artificial Intelligence 2025. doi:10.3389/frai.2025.1527980. A frozen DINOv2 teacher guides a lightweight CNN student with combined cross-entropy and KL loss, aimed at scarce medical data. The authors note "inconsistent performance across different medical tasks", attributed to a domain gap — [Source](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2025.1527980/full) [C]. Leakage note: MedMNIST-style benchmarks with predefined splits; no external validation reported in the sources found.
- Supporting: DINO-MX (arXiv:2511.01610) reports that smaller students (including dinov2-small) benefit from distilling a pathology foundation model on PathMNIST — [Source](https://arxiv.org/pdf/2511.01610) [D]. Lightly's docs show DINOv2 ViT-B/14 → ResNet-18 feature-matching (MSE) distillation as tooling — [Source](https://docs.lightly.ai/train/0.12.4/methods/distillation.html) [E].
- Licensing: the HAI-DEF terms define Model Derivatives to include models trained by transferring patterns "through distillation or synthetic data". A student distilled from MedGemma therefore inherits the HAI-DEF use restrictions — [Source](https://developers.google.com/health-ai-developer-foundations/terms) [A]

### Inferences
This report's inference:
- **NOW.** Not worth it. The DINOv2-small + logistic-regression pipeline already runs on the GPU, and the "teacher" (DINOv2 + LR trained on 14 patients) is itself unvalidated. A student would copy its errors with imperfect fidelity. KD also adds hyperparameters (temperature, α), each a new selection risk (C1). One case where it could help: unlabeled photos (e.g., new LINE uploads, if consented) as distillation inputs. That is close to pseudo-labelling, so teacher outputs must not become labels without human confirmation.
- **FUTURE.** Consider KD only if there is a concrete deployment need: CPU-only server, mobile/edge, or latency. The student must then be evaluated exactly like a new model (patient-level CV + held-out). Report teacher-student agreement (fidelity) as well as accuracy.
- **GPU.** Distillation training of a B0 student from cached DINOv2 features is light (fits 8 GB). Teacher features can be precomputed once (inference).
- **Risks.** Hidden degradation on minority classes (normal = 9 photos). License inheritance if the teacher is a HAI-DEF model. Over-interpreting "student matches teacher" as validity.

### Gaps
- No KD study on clinical skin photos with <200 images found — 未找到可靠證據.
- Hinton 2015 was not re-fetched (canonical, but not re-verified here).

---

## B1. Which open multimodal models run locally on a consumer GPU (8-16 GB), with licences, as of 2026

### Takeaway
Several open VLMs run locally on Windows through Hugging Face transformers or Ollama/llama.cpp:
- MedGemma 1.5 4B: HAI-DEF terms, with explicit clinical-use restrictions.
- Qwen3-VL 2B/4B/8B: Apache-2.0.
- Gemma 3 4B+ (Gemma Terms) and Gemma 4 (reported Apache-2.0).
- Llama 3.2 Vision 11B: Llama Community Licence; the EU restriction is not relevant to Taiwan.
- LLaVA-Med and BiomedCLIP: research-only, deployment out of scope.

vLLM is officially Linux-first. Avoid any "-cloud" model variants, because research photos must stay local.

### Cited Findings
- **MedGemma 1.5 4B-it** (official model card) [A]: [Source](https://huggingface.co/google/medgemma-1.5-4b-it)
  - Version 1.5.0, created 2026-01-13; on 2026-01-23 the generation config was changed to greedy decoding by default. Available "only" as a 4B multimodal instruction-tuned variant. BF16 weights; requires transformers ≥4.50.0 (Gemma 3 support).
  - Images are normalized to 896×896 and encoded to 256 tokens. Context ≥128K tokens.
  - Licence: "health-ai-developer-foundations" (HAI-DEF terms; acceptance required on HF).
  - Limitations: outputs "not meant to directly inform clinical diagnosis, patient management, or treatment". Evaluated mainly on single-image tasks; not evaluated for multi-turn use; "may be more sensitive to the specific prompt than Gemma 3". Validation data should be representative and non-public to reduce contamination.
- **HAI-DEF Terms of Use** (last modified 2024-11-15) [A]: [Source](https://developers.google.com/health-ai-developer-foundations/terms)
  - "Clinical Use" means "any use in diagnosis or treatment of patients (including as part of a research study)".
  - Users must seek Health Regulatory Authorization when applicable. Any use "that could cause a Health Regulatory Authority to deem Google to be a 'manufacturer' of a medical device" is prohibited.
  - Outputs are provided "AS IS"; the user is "solely responsible" and must indemnify Google. Derivatives include distilled models.
- **Qwen3-VL-8B-Instruct** (model card) [A]: Apache-2.0, BF16, family in dense and MoE variants; needs recent transformers (install from source was advised). The card has no medical disclaimer — [Source](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct)
- **Ollama qwen3-vl library** [E/vendor registry]: [Source](https://ollama.com/library/qwen3-vl)
  - Tags and download sizes: 2b 1.9 GB, 4b 3.3 GB, 8b 6.2 GB (latest), 30b 20 GB, 32b 21 GB, 235b 143 GB; 256K context.
  - "Qwen3-VL models require Ollama 0.12.7".
  - A `qwen3-vl:235b-cloud` variant exists. It is a cloud-run model and must not be used for research photos.
- **Third-party VRAM guidance** [E, low reliability]: the vision encoder adds roughly 1-3 GB over the text model. Llama 3.2 Vision 11B is ~7.8 GB to download (12-16 GB cards suggested); gemma3:4b is 3.3 GB; qwen2.5vl comes in 3B-72B (3.2-49 GB). WSL2 GPU passthrough competes with native Windows Ollama for VRAM — [Source](https://dasroot.net/posts/2026/01/running-vision-models-vram-requirements/); [Source](https://www.promptquorum.com/prompt-bites/which-ollama-models-support-vision). Sources conflict (e.g., a "~6 GB" figure for Gemma 3 4B vision vs the 3.3 GB download), so treat these as rough.
- **Gemma Terms of Use** (last modified 2026-04-01) [A]: Google claims no rights in outputs, and the user is solely responsible. The Prohibited Use Policy is incorporated by reference (its medical clauses were not read). The page states that Gemma 4 is governed by a separate Gemma 4 licence — [Source](https://ai.google.dev/gemma/terms)
- **Gemma 4** [E, secondary only]: reported Apache 2.0 licence. Sizes E2B, E4B, 26B MoE (A4B) and 31B dense, plus a later 12B. All are multimodal, with a configurable image token budget (70-1,120 tokens) — [Source](https://en.wikipedia.org/wiki/Gemma_(language_model)). Verify on the official model card before citing.
- **LLaVA-Med v1.5 (Mistral-7B)** model card [A]: "intended to be used solely for (I) future research on visual-language processing"; "not intended to be used in clinical care or for any clinical decision making purposes"; "Any deployed use case of the model --- commercial or otherwise --- is out of scope"; English-only. The base model carries the Mistral-7B-Instruct-v0.2 licence (Apache-2.0 tag) — [Source](https://huggingface.co/microsoft/llava-med-v1.5-mistral-7b). The paper is Li et al., NeurIPS 2023 (Datasets & Benchmarks), not re-fetched.
- **BiomedCLIP** (PubMedBERT_256-vit_base_patch16_224) model card [A]: MIT licence, but research-only, and "Any deployed use case of the model" is out of scope. Pretrained on PMC-15M (15M figure-caption pairs from PubMed Central). English-only — [Source](https://huggingface.co/microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224)
- **PanDerm** [B]: Yan S et al., "A multimodal vision foundation model for clinical dermatology", Nature Medicine 2025 (published 2025-06-06). Self-supervised on >2 million images from 11 institutions across 4 modalities. The GitHub repo provides PanDerm_Large_LP / PanDerm_Base_LP checkpoints that need fine-tuning or linear probing. The weights licence was not confirmed; the companion Derm1M dataset is CC BY-NC 4.0 — [Source](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12353815/); [Source](https://github.com/SiyuanYan1/PanDerm). PanDerm is a vision encoder, not a chat VLM, so it is a candidate frozen backbone like DINOv2.
- **SkinGPT-4** [B]: Zhou J et al., Nat Commun 2024;15:5649 (2024-07-05), PMID 38969632. A ViT aligned with Llama-2-13b-chat, trained on 52,929 skin-disease images and evaluated on 150 real-life cases with board-certified dermatologists. The preprint describes it as fine-tuned MiniGPT-4 — [Source](https://pubmed.ncbi.nlm.nih.gov/38969632/). Leakage/external validation: the 150 real-life cases are a separate evaluation, but patient-level details were not verified.
- **Llama 3.2 Vision** [E/vendor blog]: EU-domiciled individuals and companies are not granted rights to the multimodal Llama 3.2 models; the text-only 1B/3B models are unaffected — [Source](https://huggingface.co/blog/llama32). Taiwan is not affected, but the Llama Community Licence and Acceptable Use Policy still apply. The current licence text was not re-read.
- **vLLM on Windows** [E]: only community statements were found. vLLM "officially supports Linux only", with WSL or Docker as the usual Windows route. An unofficial Windows build exists (single-GPU, no NCCL, no FlashInfer/FA3) — [Source](https://dev.to/aivrar/running-vllm-natively-on-windows-4ahm); [Source](https://github.com/aivrar/vllm-windows-build/wiki)

### Inferences
This report's inference:
- **VRAM by arithmetic**, not measured: weights ≈ parameters × bytes per parameter, plus vision encoder, activations and KV cache.
  - MedGemma 4B: bf16 ≈ 8 GB weights → ~10 GB at runtime; 8-bit ≈ 4-5 GB; 4-bit ≈ 3 GB. A 12-16 GB card runs bf16; an 8 GB card should use 4/8-bit (bitsandbytes or GGUF).
  - Qwen3-VL-8B (~9B): bf16 ≈ 18 GB (too big for 16 GB); 4-bit ≈ 6 GB (fits 8-12 GB).
  - Qwen3-VL-4B / 2B fit any 8 GB card. Llama 3.2 11B at 4-bit fits 12-16 GB.
  - Quantization can change medical answers, so any quantized model must be evaluated as its own model.
- **Windows path.** (1) Hugging Face transformers + accelerate in the existing Python venv (most controllable, deterministic greedy decoding, no extra server). (2) Ollama native Windows, exposed only on localhost. Disable or avoid any cloud-model features and "-cloud" tags; whether Ollama can globally disable cloud models was not verified. Avoid vLLM on Windows.
- **Licence ranking for this project** (research, Taiwan, no commercial deployment):
  - Qwen3-VL (Apache-2.0) is the least restrictive, and Gemma 4 (reportedly Apache-2.0) similarly, pending verification.
  - Gemma 3 Terms are moderate.
  - MedGemma (HAI-DEF) is the most restrictive. Its "Clinical Use" definition explicitly includes research studies that diagnose or treat patients. Showing MedGemma output to LINE users or clinicians as a judgement about their IV site would likely count as Clinical Use and could trigger the regulatory-authorization clause.
  - LLaVA-Med and BiomedCLIP forbid any deployed use. They are acceptable only as offline research baselines.
- **Conflict flag (inviolable principles).** All cloud VLM APIs (GPT-4V/4o, Gemini) are excluded for research photos. The published evidence on them can be cited, but no project photo may be sent. Local alternatives: MedGemma 1.5 4B, Qwen3-VL 4B/8B, Gemma 3/4.
- **Import rule.** The platform accepts external models only as safetensors with full evaluation. MedGemma, Qwen3-VL and Gemma ship safetensors on HF, while Ollama uses GGUF, a different format. Choosing Ollama means amending the import rule or keeping VLMs outside the safetensors pipeline (flag).

### Gaps
- InternVL (sizes, licence, Windows) was not verified in this session — 未找到可靠證據 (not searched to completion).
- Official per-precision VRAM numbers for MedGemma / Qwen3-VL were not published on the cards fetched; the figures above are arithmetic estimates.
- Gemma 4 licence and sizes come only from secondary sources.
- The PanDerm weights licence was not found.
- Gemma Prohibited Use Policy medical clauses were not read.
- Taiwan TFDA medical-device software rules for a LINE-facing AI judgement were not researched (out of scope; flag for legal/IRB).

---

## B2. Performance evidence of VLMs on dermatology / clinical photo classification (zero/few-shot); any phlebitis evidence?

### Takeaway
Research evidence shows that general VLMs are weak at fine-grained dermatology diagnosis:
- GPT-4V scored 6.2% top-1 on dermatology cases and performed worse on darker skin.
- Frontier models scored worse than random on adversarial medical probing; LLaVA-Med dropped by up to 57%.
- Medical-tuned open models do better on curated multiple-choice tasks (MedGemma 1.5 4B: 73.5% on an internal 4-way dermatology MCQ).

There is no evidence on phlebitis or IV-site photos (未找到可靠證據). Any zero-shot VLM result on this project's data would be uninterpretable without the same patient-level evaluation.

### Cited Findings
- Research evidence (preprint): Jiang, Omiye, Daneshjou et al., "Evaluating General Vision-Language Models for Clinical Medicine", medRxiv 2024. doi:10.1101/2024.04.12.24305744. In dermatology GPT-4V had top-1 accuracy 6.2% and top-3 21%, with significantly worse accuracy on darker skin tones (p<0.001). On the DDI dataset it over-predicted malignancy and was less likely to name rare conditions — [Source](https://medrxiv.org/content/10.1101/2024.04.12.24305744v2.full) [D]. Evaluation only (no training), so there is no train/test leakage, but pretraining contamination cannot be excluded.
- Research evidence (preprint): medRxiv 2024.01.24.24301743, GPT-4V on 9 common dermatology conditions. For malignancy prediction, dermatologists reached ~68% accuracy vs GPT-4V ~40%; GPT-4V had higher sensitivity (0.86 vs 0.71) — [Source](https://www.medrxiv.org/content/10.1101/2024.01.24.24301743.full.pdf) [D]. This pattern of high sensitivity with low accuracy implies many false alarms, which is directly relevant to the "normal false-alarm rate" metric.
- Research evidence shows: Yan Q, He X, Yue X, Wang XE. "Worse than Random? An Embarrassingly Simple Probing Evaluation of Large Multimodal Models in Medical VQA." NeurIPS 2024 (arXiv:2405.20421). GPT-4o, GPT-4V and Gemini Pro did worse than random on specialized diagnostic probing questions. Adding negated hallucinated-attribute questions dropped LLaVA-Med by up to 57% and Gemini Pro by 25%. Poor visual understanding was a main bottleneck — [Source](https://arxiv.org/abs/2405.20421) [B]
- Official model card: MedGemma 1.5 4B on US-DermMCQA (internal, 4-way multiple-choice skin condition classification, accuracy): Gemma 3 4B 52.5, MedGemma 1 4B 71.8, MedGemma 1.5 4B 73.5, MedGemma 1 27B 71.7. No other dermatology classification benchmark is reported. The card warns about prompt sensitivity — [Source](https://huggingface.co/google/medgemma-1.5-4b-it) [A, vendor self-report; internal dataset, not externally reproducible]
- Research evidence (preprint, CLIP-style): DermLIP / Derm1M (arXiv:2503.14911) reports 58.8% average zero-shot accuracy across 4 dermatology datasets (PanDerm-based variant) vs 44.1% for BiomedCLIP — [Source](https://arxiv.org/abs/2503.14911) [D, self-reported]. The MAKE checkpoint card reports PAD-UFES-20 accuracy 0.6675 (6 classes) and Fitzpatrick17k top-1 0.3716 (113 classes). Its authors state that fine-grained accuracy is "well below clinical reliability" — [Source](https://huggingface.co/Xieji-Li/MAGEN-O-MAKE) [E]
- SkinGPT-4 (Nat Commun 2024) was evaluated on 150 real-life cases with dermatologists. Detailed accuracy figures were not retrieved — [Source](https://pubmed.ncbi.nlm.nih.gov/38969632/) [B]
- Phlebitis / IV-site: no published VLM or CNN evaluation found; only unreported trial registrations — [Source](https://clinicaltrials.gov/study/NCT07889895) → 未找到可靠證據.

### Inferences
This report's inference:
- **Phlebitis staging is harder for VLMs than these benchmarks.** It hinges on subtle erythema, swelling and cord-like veins around a cannula, across varied Taiwanese skin tones and phone lighting. The darker-skin degradation (Jiang et al.) and the high-sensitivity/low-accuracy pattern predict a high false-alarm rate on the 9 normal photos. Treat any zero-shot VLM result as a weak baseline expected near chance for stage 1 vs stage 2.
- **NOW.** At most an offline baseline: run each candidate VLM once, with a frozen prompt template, greedy decoding and a closed answer set (e.g., "normal / stage 1 / stage 2 / cannot judge"). Score it with the same patient-level metrics and CIs. Expect results indistinguishable from chance given n. Never iterate prompts on the evaluation photos; prompt tuning is hyperparameter tuning (C1). Few-shot exemplars must come from training-fold patients only.
- **FUTURE.** With ~1,000 balanced photos, parameter-efficient fine-tuning of a 2-4B VLM (e.g., LoRA on Qwen3-VL-4B or MedGemma 4B in 4-bit) is technically feasible on 12-16 GB. A frozen vision encoder (DINOv2, PanDerm) + linear head is still the more defensible comparator, because it is cheaper, deterministic and easier to validate.

### Gaps
- No open-VLM (Qwen-VL, InternVL, Gemma) zero-shot numbers on Fitzpatrick17k / DDI / PAD-UFES were found in this session.
- No position-bias study specific to dermatology VLMs was found.
- The LLaVA-Med paper's own dermatology numbers were not retrieved.
- The MedGemma technical report beyond the model card was not fetched.

---

## B3. Should a local VLM be a baseline or an assistant (retake advice, "is this an arm?" OOD filter)? Risks

### Takeaway
Use a local VLM as (1) an offline research baseline and possibly (2) a constrained image-quality / OOD gate whose outputs are mapped to fixed, pre-written messages. Never use it as a free-text generator of diagnostic statements to LINE users. Licence terms (HAI-DEF, LLaVA-Med, BiomedCLIP) and the evidence of hallucination support this restriction.

### Cited Findings
- Hallucination / negation failures in medical VQA, including LLaVA-Med dropping up to 57% — [Source](https://arxiv.org/abs/2405.20421) [B]
- MedGemma card: outputs are not to directly inform diagnosis; not evaluated for multi-turn use; prompt-sensitive — [Source](https://huggingface.co/google/medgemma-1.5-4b-it) [A]
- HAI-DEF: Clinical Use includes use in diagnosis "including as part of a research study". Regulatory authorization is required when applicable. Uses that make Google a device "manufacturer" are prohibited — [Source](https://developers.google.com/health-ai-developer-foundations/terms) [A]
- LLaVA-Med and BiomedCLIP: any deployed use is out of scope — [Source](https://huggingface.co/microsoft/llava-med-v1.5-mistral-7b); [Source](https://huggingface.co/microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224) [A]
- GPT-4V performed worse on darker skin and over-predicted malignancy, which bears on the fairness of user-facing messages — [Source](https://medrxiv.org/content/10.1101/2024.04.12.24305744v2.full) [D]

### Inferences
This report's inference:
- **Retake advice.** A safer design is a classifier-style quality check (blur, too dark, IV site not visible, not an arm/hand) whose label selects a pre-written Traditional Chinese template, e.g. "請在光線充足處重拍，讓注射部位置中". The VLM never writes the user-facing text. This removes hallucinated diagnostic claims and keeps the message reviewable.
- **OOD filter.** A cheaper, deterministic alternative is DINOv2-small embedding distance to the training set, or a small logistic "arm/hand vs other" head. These are easy to evaluate with labelled negatives. A VLM "is this an arm?" prompt can serve as a second opinion, but needs its own evaluation set, including non-arm photos and arms without IV sites.
- **Conflicts to flag.**
  - (i) Any VLM text reaching LINE users that mentions phlebitis or a stage risks a clinical-claim violation and, for MedGemma, potentially "Clinical Use" under HAI-DEF.
  - (ii) VLM labels or pseudo-labels may only be suggestions that a human confirms.
  - (iii) Ollama "-cloud" model tags would send photos off-machine and are prohibited.
- **GPU.** A 4B VLM at 4-bit (~3-5 GB) can share a 12-16 GB GPU with the classifiers. On 8 GB, avoid running it at the same time as YOLO training (inference).
- **NOW vs FUTURE.**
  - NOW: offline baseline only, plus possibly a quality gate prototype evaluated on a small labelled set.
  - FUTURE: if a quality gate proves accurate on held-out photos, consider exposing template messages only, after ethics/legal review.

### Gaps
- No study on VLM-based photo-quality or retake guidance for wound/IV-site photos — 未找到可靠證據.
- Taiwan regulatory position on AI-generated health messages via LINE was not researched.

---

## C1. Overfitting the validation set through hyperparameter / model selection on small data: evidence and practical rules

### Takeaway
Research evidence shows that selecting hyperparameters on the same CV estimate you report causes optimistic bias. Varma & Simon found ~8-12 percentage points on null data, and Cawley & Talbot found the effect can be "surprisingly large". CV error bars at n≈100 are about ±10% (Varoquaux), and here the effective n is 14 patients, so error bars are wider still. Practical rules for this project:
- tiny pre-registered search spaces
- nested CV for any selection
- repeated patient-level CV over seeds, with spread reported
- one-shot use of the held-out patients

### Cited Findings
- Research evidence shows: Cawley GC, Talbot NLC. "On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation." JMLR 2010;11:2079-2107. The variance of the model-selection criterion causes over-fitting in model selection; the resulting performance loss "can be surprisingly large"; and common evaluation practices are susceptible to selection bias — [Source](https://www.jmlr.org/papers/v11/cawley10a.html) [B]
- Research evidence shows: Varma S, Simon R. "Bias in error estimation when using cross-validation for model selection." BMC Bioinformatics 2006;7:91. doi:10.1186/1471-2105-7-91. The CV error of the tuned classifier is "a substantially biased estimate" of true error, while nested CV gives an estimate very close to the independent test error. On null data, mean bias was -12.2% (shrunken centroids) and -8.3% (SVM) — [Source](https://pmc.ncbi.nlm.nih.gov/articles/PMC1397873) [B]
- Research evidence shows: Varoquaux G. "Cross-validation failure: Small sample sizes lead to large error bars." NeuroImage 2018;180(Pt A):68-77. doi:10.1016/j.neuroimage.2017.06.061. Error bars are about ±10% for 100 samples, and the standard error across folds strongly underestimates them — [Source](https://arxiv.org/abs/1706.07581) [B]
- Research evidence shows: Bouthillier et al., MLSys 2021. Data sampling, initialization and hyperparameter choice markedly affect benchmarks. Randomizing more sources of variation approximates the ideal estimator at 51× lower compute — [Source](https://arxiv.org/abs/2103.03098) [B]
- Research evidence shows (test-set reuse): Recht B, Roelofs R, Schmidt L, Shankar V. "Do ImageNet Classifiers Generalize to ImageNet?" ICML 2019, PMLR 97:5389-5400. New test sets gave accuracy drops of 3-15% (CIFAR-10) and 11-14% (ImageNet). These were attributed not to adaptive overfitting from test reuse but to distribution differences; model rankings were preserved — [Source](https://proceedings.mlr.press/v97/recht19a) [B]. Contrast: on huge test sets adaptive overfitting was small, but with a ~14-18-photo held-out set every reuse is far more consequential (inference).

### Inferences
This report's inference, with practical rules:
1. **Pre-register** in a YAML/JSON config committed to git before running: the candidate configs (e.g., EfficientNet-B0 frozen vs. last-block unfrozen; class weights on/off; lr ∈ {1e-3, 3e-4}), the primary metric (balanced accuracy), secondary metrics (normal false-alarm rate, macro F1), and the decision rule. Keep the space ≤ ~4-8 configs NOW.
2. **Nested CV** for any selection. Outer patient-level folds evaluate; inner folds select. With 14 patients, outer leave-2-patients-out × inner 3-fold is feasible computationally, but each inner training set has only ~8 patients. Prefer fixed defaults over search NOW.
3. **Repeated CV.** Repeat the patient-level StratifiedGroupKFold with ≥5-10 different split seeds and several training seeds. Report mean, SD and min-max across repeats, alongside Wilson/bootstrap CIs. Bootstrap at the patient level (cluster bootstrap), not the photo level.
4. **One-shot held-out.** Use the held-out patients once, for the final pre-registered config, and log the access in the snapshot DB. After any look, that set becomes "used". This is consistent with the CLAIM 2024 term "internal testing dataset".
5. **Treat every adjustable choice as a hyperparameter** — VLM prompts, TTA policy, thresholds, ensemble weights — and count it in the search budget.
6. **NOW vs FUTURE.**
   - NOW: avoid automated HP search entirely; at most a 4-config comparison under nested CV, reported as exploratory.
   - FUTURE (~1,000 photos, ideally ≫14 patients): a small Optuna search (≤30-50 trials) inside the inner loop becomes defensible. Still report outer-loop and seed variance.
- **Principle check.** HP search must be launched manually by a researcher and must never auto-promote or auto-deploy the best trial. This is consistent with the "no automatic training / deployment" rule if a "search job" is treated as an explicit human-started action (flag for the platform owner).

### Gaps
- No quantitative study of selection bias specifically for grouped (patient-clustered) CV with <20 groups — 未找到可靠證據.
- Bouthillier's specific seed-vs-split recommendations were not retrieved beyond the abstract.

---

## C2. Optuna, MLflow and alternatives: a minimal local setup consistent with SQLite + FastAPI

### Takeaway
Industry practice and the official docs support an all-local setup:
- Optuna with `storage="sqlite:///…"` (resumable).
- Optionally MLflow, whose current docs default to a SQLite backend (`sqlite:///mlflow.db`) served on 127.0.0.1:5000. Remote access requires `--host 0.0.0.0` plus `--allowed-hosts`. The file store is in maintenance (KTLO) mode.

Weights & Biases is cloud-hosted by default and should be excluded. For a tiny project, extending the app's own SQLite with a runs/manifest table may be enough.

### Cited Findings
- Optuna official tutorial: `storage_name = f"sqlite:///{study_name}.db"`; `create_study(..., storage=storage_name, load_if_exists=True)` resumes. "The storage doesn't store the state of the instance of samplers and pruners"; to keep a seeded sampler's state, pickle `study.sampler`. Other RDBs (PostgreSQL/MySQL) are possible — [Source](https://optuna.readthedocs.io/en/stable/tutorial/20_recipes/001_rdb.html) [A]. The Optuna version is not shown on the page.
- MLflow (latest docs): the tracking server uses a SQLite database (`sqlite:///mlflow.db`) for run metadata and serves the UI/REST at http://127.0.0.1:5000. Remote connections need `--host 0.0.0.0`, and with that you should set `--allowed-hosts` — [Source](https://www.mlflow.org/docs/latest/self-hosting/architecture/tracking-server/) [A]
  - The 3.5.1 docs state the server listens on localhost:5000 by default, accepts only local connections, and that the file backend is in Keep-the-Light-On mode — [Source](https://mlflow.org/docs/3.5.1/self-hosting/architecture/tracking-server) [A]
  - Older 3.0.0rc1 docs described the default as the `./mlruns` file store — [Source](https://mlflow.org/docs/3.0.0rc1/tracking/server) [A]. These docs contradict each other on the default backend because the default changed within MLflow 3.x; the exact release of the switch was not pinned down.

### Inferences
This report's inference (tooling not individually verified this session is marked "not verified"):
- **Minimal recommended setup NOW.** No new server. Add tables to the existing SQLite DB:
  - `experiment_run`: run_id, git commit, config JSON, dataset manifest hash, split seed, train seed, library versions, GPU/driver, start/end, metrics JSON, artifact paths.
  - `heldout_access_log`.

  FastAPI already provides the UI hooks and the snapshot diff can read these rows. This avoids a second web service and port.
- **Optuna (optional, FUTURE).** Use a separate `optuna.db` file to avoid lock contention with the app DB. Run single-process, since SQLite concurrency is limited (inference; not discussed on the page). Seed the sampler (e.g., TPESampler(seed=…)) and pickle it for resumption, per the docs.
- **MLflow (optional).** If richer comparison UI is wanted: `mlflow server --backend-store-uri sqlite:///mlflow.db` on the default 127.0.0.1, with a local artifact directory. Never bind 0.0.0.0. Do not use model-registry aliases to trigger deployment, to keep "no automatic deployment".
- **Not verified this session.** MLflow Windows support; DVC (data versioning via content hashes, local remote possible); Aim (local); TensorBoard (local; Ultralytics logs to it). Weights & Biases defaults to a cloud service, so flag and exclude it for research photos and metadata unless self-hosted. W&B self-hosting was not checked.
- **DVC vs manifest.** For ~120-1,000 photos, a JSON/CSV dataset manifest (file path, SHA-256, patient pseudo-ID, label, label version, annotator, box presence) stored in git plus in SQLite gives most of DVC's value with no new tool.

### Gaps
- The exact MLflow 3.x release that switched the default backend to SQLite was not identified.
- Optuna's SQLite concurrency guidance (JournalStorage) was not retrieved.
- DVC, Aim, TensorBoard and W&B docs were not fetched (time budget).

---

## C3. Reproducibility (PyTorch, Ultralytics), data versioning, model cards/datasheets, reporting guidelines (TRIPOD+AI, CLAIM 2024)

### Takeaway
The PyTorch docs prescribe seeding all RNGs, `torch.use_deterministic_algorithms(True, warn_only=False)`, `cudnn.benchmark=False` / `cudnn.deterministic=True` and seeded DataLoader workers, and state that bitwise reproducibility is not guaranteed across releases, platforms or CPU vs GPU. Ultralytics defaults to `seed=0`, `deterministic=True`. Therefore report variance across seeds rather than claim exact reproducibility. Report with TRIPOD+AI (27 items) and CLAIM 2024, and document the models and data with model cards and datasheets.

### Cited Findings
- PyTorch Reproducibility note (stable docs, last updated 2026-05-14; internal links point to docs/2.15) [A]: [Source](https://docs.pytorch.org/docs/stable/notes/randomness.html)
  - `torch.manual_seed()` seeds "all devices (both CPU and CUDA)". Also seed Python `random` and NumPy.
  - Use `torch.use_deterministic_algorithms(True, warn_only=False)`, since with warn_only=True fused SDPA backends only warn.
  - `cudnn.benchmark=False` makes cuDNN choose its algorithm deterministically; `cudnn.deterministic=True`.
  - DataLoader: `worker_init_fn` that seeds NumPy/random from `torch.initial_seed() % 2**32`, plus a seeded `torch.Generator`.
  - "Completely reproducible results are not guaranteed across PyTorch releases, individual commits, or different platforms"; results "may not be reproducible between CPU and GPU executions, even when using identical seeds"; deterministic ops "are often slower".
  - `CUBLAS_WORKSPACE_CONFIG` did not appear in the excerpt read. Its required values (commonly `:4096:8` or `:16:8`) were not re-verified this session.
- Ultralytics train settings (official docs; page shows YOLO26 and "YOLO27 (Coming Soon)", no library version) [A]: `seed` default 0 ("ensuring reproducibility of results across runs with the same configurations"), `deterministic` default True ("Forces deterministic algorithm use, ensuring reproducibility but may affect performance and speed"), `workers` 8, `amp` True (FP16; "bf16" on supported CUDA) — [Source](https://docs.ultralytics.com/usage/cfg/). The older YOLOv5 code calls `torch.use_deterministic_algorithms(True)` and sets `CUBLAS_WORKSPACE_CONFIG` when deterministic is on — [Source, mirror, E](https://huggingface.co/spaces/xiang-wuu/yolov5/commit/27d831b6e4ae4b0286ba0159f5c8542e052cd3c9). Not confirmed for Ultralytics 8.4.
- MedGemma generation config changed to greedy decoding by default on 2026-01-23. VLM outputs can therefore change with a config revision, so pin the model revision hash — [Source](https://huggingface.co/google/medgemma-1.5-4b-it) [A]
- Mitchell M, Wu S, Zaldivar A, Barnes P, Vasserman L, Hutchinson B, Spitzer E, Raji ID, Gebru T. "Model Cards for Model Reporting." FAT* '19 (Atlanta, 29-31 Jan 2019). doi:10.1145/3287560.3287596; arXiv:1810.03993. Model cards provide "benchmarked evaluation in a variety of conditions" — [Source](https://arxiv.org/abs/1810.03993) [B]
- Gebru T et al. "Datasheets for Datasets." arXiv:1803.09010; CACM 2021 publication confirmed only by a secondary source in this session — [Source](https://arxiv.org/abs/1803.09010) [D; CACM venue unverified here]
- TRIPOD+AI: Collins GS, Moons KGM, et al. "TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine learning methods." BMJ 2024;385:e078378 (published 2024-04-16; erratum BMJ 2024;385:q902). A 27-item checklist, an expanded checklist, and a 13-item TRIPOD+AI for Abstracts. It supersedes TRIPOD 2015 — [Source](https://www.bmj.com/content/385/bmj-2023-078378) [A]
- CLAIM 2024 Update: Tejani AS, Klontzas ME, Gatti AA, Mongan JT, Moy L, Park SH, Kahn CE Jr; CLAIM 2024 Update Panel. Radiol Artif Intell 2024;6(4):e240300. doi:10.1148/ryai.240300. Items are answered Yes/No/NA. It recommends "external testing" over "external validation", "internal testing dataset" for the held-out subset, and "reference standard". The Delphi panel had 73 volunteers, 72 of whom completed both rounds. It is not extended to radiomics — [Source](https://pmc.ncbi.nlm.nih.gov/articles/PMC11304031) [A]

### Inferences
This report's inference:
- **Reproducibility recipe** (one helper called at job start, logged to the run row):
  - set `PYTHONHASHSEED` and `random`/`numpy`/`torch` seeds
  - `torch.use_deterministic_algorithms(True, warn_only=False)`
  - `cudnn.benchmark=False`, `cudnn.deterministic=True`
  - set `CUBLAS_WORKSPACE_CONFIG` (value to confirm in the PyTorch / CUDA docs)
  - seeded DataLoader generator + `worker_init_fn`
  - Ultralytics `seed=<logged>`, `deterministic=True`
  - consider `workers=0` on Windows if worker seeding is problematic (inference)
  - log torch/CUDA/cuDNN/driver/ultralytics/transformers versions and the GPU name

  Expect run-to-run metric jitter even then (AMP, atomic ops, driver differences). On 14 patients, report results as distributions across ≥5 training seeds.
- **Data versioning.** A SHA-256 per photo plus a manifest hash per dataset snapshot. Store the label-version and annotator fields (single annotator, which is a known limitation to report under TRIPOD+AI / CLAIM). Record which photos have boxes. Record the patient pseudo-ID used for grouping, and verify that no patient appears in both train and test, with an automated assert.
- **Model card per exported model.** Intended use ("research prototype, not diagnosis"), training manifest hash, CV/held-out metrics with CIs and seed spread, subgroup notes (E-Da vs LINE source; skin tone if recorded), known failure cases, licence of base weights (e.g., HAI-DEF inheritance). A datasheet covers the photo collection: consent, sources, LINE upload conditions, de-identification.
- **Reporting.** TRIPOD+AI applies because this is a prediction model. CLAIM 2024 is radiology-focused but its imaging items (data partitions, reference standard, internal/external testing terminology) transfer well. State clearly that there is no external testing and that the evaluation is patient-level internal CV with an internal testing dataset.
- **NOW vs FUTURE.** The same recipe applies to both. FUTURE adds a second annotator / inter-rater agreement, and ideally an external testing set from another site or period.

### Gaps
- `CUBLAS_WORKSPACE_CONFIG` values and cuBLAS determinism requirements were not re-verified.
- Whether Ultralytics 8.4 calls `torch.use_deterministic_algorithms` internally was not confirmed from current source.
- The Datasheets CACM 2021 DOI was not verified in this session.
- The TRIPOD+AI item list was not retrieved item by item.
