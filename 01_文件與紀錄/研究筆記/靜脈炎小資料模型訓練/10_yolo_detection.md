# YOLO11 / YOLO26 (Ultralytics 8.4) detection training and evaluation for small, subtle skin lesions with tiny data

**Scope and access.** This covers phlebitis IV-site photos: a single class ("lesion"), with diffuse redness or swelling. NOW = about 24 boxed images from 14 patients, plus 9 normal photos. FUTURE = about 1,000 photos. Every source was accessed on 2026-10-30.

**Installed version.** The project venv was checked locally: `02_主程式碼/.venv/Lib/site-packages/ultralytics/__init__.py` reports `__version__ = "8.4.161"`. Code-level claims below were checked against this installed copy where stated.

**Source grades.**
- [A] = official docs or official code
- [B] = systematic review or top-venue paper
- [C] = other peer-reviewed work
- [D] = preprint
- [E] = blog, forum or search snippet

**Conclusion labels.** Each conclusion carries one of: (research evidence), (industry practice), or (inference).

**Local hardware.** `01_文件與紀錄/驗證報告/environment.json` records an "NVIDIA GeForce RTX 5050 Laptop GPU" with `vram_bytes: 8546484224`, about 8 GB (local file).

---

## Q1. Ultralytics official training settings (defaults, freeze, patience, imgsz, rect, optimizer auto, warmup, nbs)

### Takeaway
Ultralytics defaults are built for COCO-scale data: epochs=100, patience=100, imgsz=640, batch=16, optimizer=auto, mosaic=1.0, close_mosaic=10, nbs=64.

The official YOLO26 Training Recipe gives one small-data row, for datasets under 1,000 images: AdamW with lr0=0.001, about 50 epochs, patience=20, mosaic=0.5, mixup=0, copy_paste=0, and "consider freeze=10". This is the only official anchor, and 24 images is about 40 times smaller than that range.

In the installed 8.4.161, `optimizer=auto` resolves to **AdamW with lr = 0.002/(…) → 0.002 for nc=1**. It switches to MuSGD only above 10,000 iterations, and it never selects SGD in 8.4. In the NOW regime, auto always means AdamW. (Basis: official code [A].)

### Cited Findings
- **default.yaml (GitHub `main`; the file has no version header) [A]:**
  - Schedule and batching: `epochs: 100`, `patience: 100` ("early stop after N epochs without val improvement"), `batch: 16` (-1 = AutoBatch, float = GPU-memory fraction), `imgsz: 640`, `rect: False`, `cos_lr: False`, `close_mosaic: 10`.
  - Optimizer: `optimizer: auto` (SGD, MuSGD, Adam, Adamax, AdamW, NAdam, RAdam, RMSProp, auto), `lr0: 0.01`, `lrf: 0.01`, `momentum: 0.937`, `weight_decay: 0.0005`.
  - Warmup: `warmup_epochs: 3.0`, `warmup_momentum: 0.8`, `warmup_bias_lr: 0.1`.
  - Loss gains: `box: 7.5`, `cls: 0.5`, `dfl: 1.5` ("DFL when reg_max > 1, L1 on DFL-free YOLO26").
  - Freezing and classes: `freeze:` (None; int = first N layers; list = indices or module names like "23.cv2"), `single_cls: False`.
  - Augmentation: `multi_scale: 0.0` (now a float fraction of imgsz), `mosaic: 1.0`, `mixup: 0.0`, `cutmix: 0.0`, `copy_paste: 0.0`, `fliplr: 0.5`, `degrees: 0.0`, `scale: 0.5`, `translate: 0.1`.
  - Runtime: `amp: True`, `cache: False`, `pretrained: True`, `nbs: 64` ("gradients accumulate over round(nbs / batch) batches per optimizer step"), `time:` (max hours).
  - Inference thresholds: `conf:` (predict 0.25, val 0.001), `iou: 0.7`, `max_det: 300`.
  - Source: [default.yaml](https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/cfg/default.yaml)
- **Configuration docs [A]:**
  - `optimizer=auto` will "pick AdamW or MuSGD from the number of training iterations", and auto ignores `lr0`.
  - `freeze` "Freezes the first N layers of the model, or specific layers by index or module name".
  - `rect` "Enables minimum padding strategy" and "may affect accuracy".
  - `batch=-1` means "auto mode for 60% of available GPU memory".
  - Val defaults are `conf` 0.001 and `iou` 0.7.
  - Val/predict `nms` defaults to None. None or True uses NMS. False means "use the NMS-free one-to-one head when available".
  - The page has no `end2end` argument for val or predict.
  - Source: [Ultralytics Configuration](https://docs.ultralytics.com/usage/cfg/)
- **Auto optimizer (installed 8.4.161, `engine/trainer.py` lines 1152-1153) [A, code, checked locally]:** `lr_fit = round(0.002 * 5 / (4 + nc), 6)`, then `("MuSGD", 0.01, 0.9) if iterations > 10000 else ("AdamW", lr_fit, 0.9)`. GitHub `main` has the same logic. Under MuSGD, only 2D/4D weights use Muon, and the cls heads `cv3` and `one2one_cv3` get 3x the LR — [trainer.py main](https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/engine/trainer.py)
  - (inference) For nc=1, lr_fit = 0.002.
  - (inference) Ultralytics 8.0-8.3 picked SGD above 10k iterations. That is from memory and not re-verified, so treat "SGD under auto" as superseded in 8.4.
- **Gradient accumulation and weight decay (installed trainer.py lines 312-313) [A, code]:** `self.accumulate = max(round(self.args.nbs / self.batch_size), 1)`, and `weight_decay = self.args.weight_decay * self.batch_size * self.accumulate / self.args.nbs`.
- **Warmup (installed trainer.py lines 268-271, 509-526) [A, code]:** warmup iterations are `round(warmup_epochs * num_batches)`, capped so at least the final epoch is not warmup. This version has no 100-iteration minimum. During warmup:
  - `accumulate` ramps from 1 to nbs/batch.
  - The bias LR falls from 0.1, and the other LRs rise from 0 to lr0.
  - Momentum ramps from 0.8 to the configured momentum.
- **Early stopping (installed `utils/torch_utils.py` line 1122) [A, code]:** `self.patience = patience or float("inf")`. So **`patience=0` disables early stopping**.
- **Freeze (installed trainer.py lines 378-379; also `main`) [A, code]:**
  - An int N becomes `range(N)`, which maps to name prefixes `model.{x}.`.
  - `.dfl` is always frozen.
  - BatchNorm layers in frozen modules are kept in eval mode, and the run raises an error if nothing remains trainable — [trainer.py main](https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/engine/trainer.py)
- **Layer indices [A, config]:** the YOLO11 backbone is layers 0-10: 0 Conv P1/2, 1 Conv P2/4, 2 C3k2, 3 Conv P3/8, 4 C3k2, 5 Conv P4/16, 6 C3k2, 7 Conv P5/32, 8 C3k2, 9 SPPF, 10 C2PSA. The neck/head is 11-22, and Detect is 23 (taking 16, 19, 22 = P3/P4/P5) — [yolo11.yaml](https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/cfg/models/11/yolo11.yaml). YOLO26 uses the same index layout (backbone 0-10, head 11-22, Detect 23), plus `end2end: True` and `reg_max: 1` — [yolo26.yaml](https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/cfg/models/26/yolo26.yaml)
- **YOLO26 Training Recipe guide [A]:**
  - On fine-tuning: "Fine-tuning with defaults is a strong baseline."
  - **Under 1,000 images:** `mosaic=0.5, mixup=0.0, copy_paste=0.0`, `optimizer=AdamW, lr0=0.001`, about 50 epochs, `patience=20`, "consider `freeze=10`".
  - **Over 50k images:** follow the pretraining recipe and use MuSGD.
  - The COCO checkpoints were trained at 640, batch 128, with MuSGD. The S-X COCO fine-tune stage used lr0=0.00038.
  - The released checkpoints come from an internal branch, so results on `main` "will not be bit-identical".
  - Medical imaging is named as a domain, but the guide gives no medical-specific advice.
  - Source: [YOLO26 Training Recipe](https://docs.ultralytics.com/guides/yolo26-training-recipe)
- **Model Training Tips guide [A]:**
  - "A good starting point is 300 epochs" (generic advice).
  - `batch=-1` targets about 60% of memory.
  - Pretrained weights come from `model=yolo26n.pt`, and "`pretrained=True` on a `*.yaml` model does not fetch weights on its own".
  - The guide suggests comparing `optimizer=auto` against MuSGD.
  - `multi_scale=0.25` at 640 samples sizes from 480 to 800.
  - It does not cover freezing, background images, or minimum dataset size.
  - Source: [Model Training Tips](https://docs.ultralytics.com/guides/model-training-tips/)
- **Project config (local) `02_主程式碼/configs/train.json`:** `epochs 120, imgsz 640, batch 4, patience 25, optimizer auto, amp false, deterministic true, mosaic 0, mixup 0, degrees 10, translate 0.05, scale 0.05, hsv_h 0.01, hsv_s 0.2, hsv_v 0.15, fliplr 0.5, conf 0.001, iou 0.7, workers 0`. No `freeze`, `nbs` or `lr0` is set.

### Inferences
- (inference, from code) **Hidden issue in the current config.** batch=4 with the default nbs=64 gives accumulate=16 after warmup. A NOW fold has about 16-22 training images including backgrounds, which is only 4-6 batches per epoch. So **the optimizer steps only about once every 3-4 epochs**, roughly 30-45 steps in 120 epochs.
  - Fix: set `nbs` equal to `batch` (for example batch=8, nbs=8) so every batch is an optimizer step. Weight decay stays at 0.0005, because 8·1/8 = 1.
  - This interaction is not documented for small data. Treat it as an ablation, not an established fact about accuracy.
- (inference, from code) `optimizer: auto` in train.json silently ignores any lr0 and uses AdamW at lr 0.002 (nc=1). To follow the official small-data recipe (AdamW, lr0=0.001), set `optimizer='AdamW', lr0=0.001` explicitly. The platform already writes `effective.json` with the optimizer class and per-group LRs (`adapters.py` lines 558-568), which can confirm what actually ran.
- (inference) With patience=100 and epochs=100 (Ultralytics default), early stopping never fires. In the project (patience=25, val fold of about 8 boxed images), early stopping and `best.pt` selection key on a very noisy val mAP. That makes the best epoch an optimistic pick on the same fold used for reporting.
  - NOW: use a **fixed epoch count chosen in advance** (`patience=0`, and report `last.pt`), or pick epochs by an inner split.
- (inference) `freeze=10` (the official suggestion) freezes backbone layers 0-9 and leaves layer 10 (C2PSA) trainable. `freeze=11` freezes the full backbone, and `freeze=23` trains only Detect. In TFA terms (Q3), freezing more is the few-shot-consistent choice. Ablate {0, 10, 11} under patient-grouped CV.
- (industry practice) `rect=True` reduces padding but turns off shuffle-style mosaic batching assumptions, and the docs warn it "may affect accuracy". It is not recommended for training here. For val it is a compute optimization only.

### Gaps
- I found no official Ultralytics statement on the minimum number of images or instances for fine-tuning. The older "Tips for Best Training Results" figures (≥1,500 images, ≥10,000 instances per class, 0-10% backgrounds) were **not re-opened in this session**, so treat them as unverified recollection.
- There is no official guidance on `nbs` for tiny datasets.

---

## Q2. YOLO11 vs YOLO26 — verified differences, numbers, export, small objects, known 8.4 issues

### Takeaway
YOLO26 shipped in Ultralytics **v8.4.0 on 14 Jan 2026** [A]. Its main changes:
- It removes DFL (`reg_max=1`).
- It adds a one-to-one NMS-free head alongside the one-to-many head, and both are trained.
- It adds ProgLoss and STAL ("Small-Target-Aware Label Assignment").
- It adds the MuSGD optimizer.

At equal size on COCO-640, YOLO26 beats YOLO11 by 1.4-1.6 mAP50-95 points with similar params and FLOPs. The NMS-free head costs 0.6-0.8 mAP. The "43% faster CPU" claim holds for **n** (56.1 → 38.9 ms) but **not for s** (90.0 → 87.2 ms, about 3%). On T4 GPU, YOLO26n is slightly slower than YOLO11n.

No official AP_small numbers exist, so the claim that YOLO26 is better for small objects rests on design intent (STAL), not measured evidence.

### Cited Findings
- **Release dates.**
  - YOLO11: "released on September 27, 2024" [A] — [YOLO11 docs](https://docs.ultralytics.com/models/yolo11/).
  - YOLO26: "released January 2026" [A] — [YOLO26 docs](https://docs.ultralytics.com/models/yolo26/). GitHub release v8.4.0 is dated 14 Jan (2026) and says it introduces YOLO26 with "native end-to-end NMS-free architecture", DFL "fully removed", MuSGD "inspired by Kimi K2", and "43% faster CPU inference" [A] — [v8.4.0 release](https://github.com/ultralytics/ultralytics/releases/tag/v8.4.0).
  - Conflict: the Sapkota et al. preprint (v5, 16 Mar 2026) says YOLO26 was "released in September 2025" [D] — [arXiv 2509.25164v5](https://arxiv.org/html/2509.25164v5). (inference) This probably refers to the pre-release announcement. Use 14 Jan 2026 (v8.4.0) as the software release date.
- **COCO val, 640 px, detection (YOLO26 docs page, last-updated stamp Aug 21, 2026) [A]:**

| Model | mAP50-95 | mAP50-95 e2e | CPU ONNX ms | T4 TRT10 ms | Params M | FLOPs B |
|---|---|---|---|---|---|---|
| YOLO26n | 40.9 | 40.1 | 38.9±0.7 | 1.7 | 2.4 | 5.5 |
| YOLO26s | 48.6 | 47.8 | 87.2±0.9 | 2.5 | 9.5 | 20.9 |
| YOLO26m | 53.1 | 52.5 | 220.0±1.4 | 4.7 | 20.4 | 68.4 |

  - Speeds are measured with `nms=False`. Params and FLOPs are for the fused model — [YOLO26 docs](https://docs.ultralytics.com/models/yolo26/)

- **YOLO11 (same conditions) [A]:**

| Model | mAP50-95 | CPU ONNX ms | T4 TRT10 ms | Params M | FLOPs B |
|---|---|---|---|---|---|
| YOLO11n | 39.5 | 56.1±0.8 | 1.5 | 2.6 | 6.5 |
| YOLO11s | 47.0 | 90.0±1.2 | 2.5 | 9.4 | 21.6 |
| YOLO11m | 51.5 | 183.2±2.0 | 4.7 | 20.1 | 68.1 |

  - Source: [YOLO11 docs](https://docs.ultralytics.com/models/yolo11/). The YOLO11 page says nothing about small objects.
- **YOLO26 features (docs) [A]:**
  - The optional one-to-one head gives NMS-free predictions. **"Prediction and validation default to the one-to-many head for accuracy"** (NMS applied). Pass `nms=False` to use the one-to-one head in `predict`, `val` and `export`.
  - Both heads are trained regardless of which one you use.
  - STAL "improves positive label coverage for small objects".
  - ProgLoss shifts emphasis toward the inference head.
  - MuSGD is a SGD+Muon hybrid.
  - `yolo26-p2.yaml` (P2 small-object head) ships as an architecture only, with **no released weights**.
  - Export: `model.export(format="onnx", nms=False)` for NMS-free export, or `nms=True` to embed NMS. DFL removal simplifies export.
  - Source: [YOLO26 docs](https://docs.ultralytics.com/models/yolo26/)
- **Preprint analyses.**
  - Sapkota, Cheppally, Sharda, Karkee (Cornell / Kansas State), "YOLO26: Key Architectural Enhancements and Performance Benchmarking for Real-Time Object Detection", arXiv:2509.25164v5, 2026 [D]. STAL is described only qualitatively ("explicitly prioritizes label assignments for small objects"). It reports **no AP_small numbers and no YOLO11 head-to-head**, and its benchmark tables appear to reuse Ultralytics-reported figures — [arXiv](https://arxiv.org/html/2509.25164v5)
  - Chakrabarty (KIIT), "YOLO26: An Analysis of NMS-Free End to End Framework…", arXiv:2601.12882v2, 18 Mar 2026 [D]. It is explicitly secondary, relying only on public Ultralytics material. It reports no STAL, ProgLoss or MuSGD ablations, and its STAL, ProgLoss and MuSGD figures are "conceptual". It discusses the "Export Gap", attributed to DFL softmax being hard to quantize on NPUs — [arXiv](https://arxiv.org/html/2601.12882v2)
  - A search snippet claimed a STAL ablation (AP_S 29.0 → 29.6). **It could not be found in the paper I opened, so it is unverified and should not be used.**
  - A search snippet for a YOLO26 vs YOLOv8 VisDrone paper (arXiv 2605.24831) said both models "struggl[e] significantly with dense small targets" [E/snippet only; paper not opened].
- **Training loss config [A]:** `dfl` gain becomes an L1 box-distance gain on DFL-free YOLO26 — [default.yaml](https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/cfg/default.yaml)
- **Known 8.4 behaviour change (local code, project fix commit d481560) [A-equivalent, local]:** the comment at `02_主程式碼/src/workbench/adapters.py` line 539 reads "Ultralytics 8.4 keeps tloss as {name: value}; older releases used a tensor ordered by loss_names". Lines 540-546 handle both forms.
  - The GitHub release notes I opened (v8.4.0 and v8.4.184-193) **do not document** this change. Ultralytics' releases page has 53 pages, and I did not scan every 8.4.x release for it.
- **Other 8.4 config changes seen [A]:**
  - `multi_scale` is now a float range (default 0.0), not a bool. (inference) Old configs passing `multi_scale=True` may be coerced to 1.0, a very large ±100% range. Verify before use.
  - `optimizer` lists MuSGD.
  - `cls_remap: True` remaps pretrained class-head rows by class-name match when fine-tuning across datasets.
  - Source: [default.yaml](https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/cfg/default.yaml)
- **Privacy-relevant settings [A]:**
  - `sync: True` by default, meaning "Send anonymized analytics and crash reports to Ultralytics". Disable it with `from ultralytics import settings; settings.update({"sync": False})`.
  - Logger integrations `clearml`, `comet`, `dvc`, `mlflow` and `raytune` default to True. `tensorboard` and `wandb` default to False.
  - `api_key` (Ultralytics Platform) is empty by default.
  - Source: [Ultralytics Settings](https://docs.ultralytics.com/usage/settings/)

### Inferences
- (inference) For this project, **YOLO26s vs YOLO11s** is about +1.6 COCO mAP at equal params and FLOPs. With 24 images, that gap is far below fold-to-fold noise (Q5), so the choice cannot be decided on NOW data. On the local GPU, the CPU-speed advantage does not matter.
- (inference) The **NMS vs end2end** option the project exposes (`contracts.py` line 44, `adapters.py` lines 744 and 902, `assist.py` line 63, all passing `nms=False` for end2end) matches the docs. Use the default one-to-many + NMS path for evaluation, since it is about 0.8 COCO mAP better.
  - For single-class, few-lesion photos, NMS cost is negligible.
  - End2end matters mainly for export or edge deployment, which is not a project goal.
- (inference) YOLO11 also has no reliable small-object advantage. "Better for small objects" should not drive the model choice here, because phlebitis lesions are mostly not COCO-small (Q4).
- **(privacy, industry practice) Never use Ultralytics HUB or Platform, or cloud training.**
  - Keep `api_key` empty.
  - Set `sync=False`.
  - Disable `clearml`, `comet`, `dvc`, `mlflow` and `raytune` in settings so no logger can ship metrics or images if those packages happen to be installed.
  - Keep pretrained `.pt` files local, as the project already does under `models/pretrained/`.
  - The local alternative is plain `model.train()` on the local GPU with TensorBoard off, or a local file-based logger.

### Gaps
- Official AP_small / AP_medium for YOLO26 vs YOLO11: **no reliable evidence found**.
- I did not confirm from release notes which exact 8.4.x patch introduced the dict `tloss`.
- I did not verify whether early 8.4.x patches defaulted val/predict to the end2end head. The docs (Aug 2026) say one-to-many is the default. Check the installed 8.4.161 behaviour with `model.val(...)` both ways.

---

## Q3. Evidence on fine-tuning detectors with tens of images; medical small-data YOLO; leakage counter-evidence

### Takeaway
The few-shot detection literature says fine-tuning only the last layers of a pretrained detector is a strong baseline. It also says **results with few samples vary so much that single-split numbers are unreliable** (research evidence).

Medical YOLO studies with small data mostly:
- split by image or by source, not by patient;
- report no external validation;
- use well-defined targets.

Leakage evidence shows that splitting non-independent images (same subject) can inflate accuracy by about 30-55 points on small datasets (research evidence, from a classification setting). For 24 boxed images from 14 patients there is **no published evidence** that a YOLO detector gives reliable lesion boxes. Treat it as an annotation assistant only.

### Cited Findings
- **Wang X, Huang TE, Darrell T, Gonzalez JE, Yu F. "Frustratingly Simple Few-Shot Object Detection." arXiv:2003.06957, 2020** [D on the page opened; widely reported as ICML 2020, but the venue was not confirmed on the opened page].
  - Fine-tuning only the last layer of an existing detector on rare classes "is crucial". It beats meta-learning by about 2-20 points.
  - "High variance across the few training samples" makes benchmarks unreliable. The authors revised the protocol to sample **multiple groups of training examples**.
  - Source: [arXiv](https://arxiv.org/abs/2003.06957)
- **Silva R, Hayat K, Riggs CM, Doube M. "How many radiographs are needed to re-train a deep learning system for object detection?" arXiv:2210.08734, 2022** [D].
  - YOLOv5s transfer learning on 396 equine carpal radiographs. With ≥96 training radiographs, precision, recall and mAP all exceeded 0.95. The authors conclude about 100 radiographs suffice.
  - Leave-one-out CV was used. Patient-level splitting and external validation were not stated.
  - Source: [arXiv](https://arxiv.org/abs/2210.08734)
  - (inference) These are rigid, high-contrast, fixed-position bones in a standardized projection, the opposite of diffuse erythema in uncontrolled smartphone photos. Use this as an optimistic upper bound, not a transferable estimate.
- **Lau CH, Yu KH-O, Yip TF, et al. "An artificial intelligence-enabled smartphone app for real-time pressure injury assessment." Front. Med. Technol. 2022;4:905074. doi:10.3389/fmedt.2022.905074** [C].
  - YOLOv4 trained on about 190 public pressure-injury images (stage counts sum to 191, which is internally inconsistent), augmented to 1,278 train and 144 val images. Split by **image source**, and patient count not reported.
  - Val accuracy 63.2% (per-stage sensitivity 37-76.7%).
  - The "independent test" was 10 local photos (80%), and real-world tests used **printed images on a forearm**. No external validation.
  - Source: [PMC9541137](https://pmc.ncbi.nlm.nih.gov/articles/PMC9541137/)
- **Other small-data wound and pressure-ulcer YOLO studies (search snippets only; not opened, unverified details) [E]:**
  - An Applied Sciences 2024 YOLOv8 pressure-ulcer app with 2,800 images, reporting mAP50 90.8%.
  - An MHSRS military wound abstract using a patient-level split (101 / 21 patients) plus an external military set (27 patients), YOLOv8n as the detector feeding SAM2.1, with patient-level bootstrap CIs. It is cited here only as an example of the design pattern.
  - Snippet hits for ulcer/forensic YOLO studies used **random image-level splits** (90/10, 70/20/10).
  - Source: [search results; e.g., MHSRS abstract](https://mhsrs.health.mil/MHSRS/download/downloadabstractfile/5614)
- **Leakage: Yagis E, et al. "Effect of data leakage in brain MRI classification using 2D convolutional neural networks." Sci Rep 2021;11:22544. doi:10.1038/s41598-021-01681-w** [C; abstract read via DOAJ record in search results, full text not opened].
  - A slice-level (not subject-level) split inflated accuracy by 30% (OASIS), 29% (ADNI), 48% (PPMI) and 55% (local PD).
  - With **random labels**, the slice-level split still gave about 96% accuracy, against 50% for the subject-level split.
  - The effect is "severe, especially for small datasets".
  - Source: [DOAJ record](https://doaj.org/article/ba8c3daef34b44d98cdadf6e89dba3e3)
- **Ultralytics K-Fold guide [A].** The code uses sklearn `KFold(shuffle=True, random_state=20)` at the **image level**, but the FAQ says related images (same patient, sequence, camera or site) should stay in one fold — [K-Fold guide](https://docs.ultralytics.com/guides/kfold-cross-validation/)

### Inferences
- (inference) Multiple photos per patient (about 120 photos from 14 patients) are the same structure as "slices per subject". Random photo-level splits would leak lesion appearance, skin tone, arm and background. **Patient-grouped folds are mandatory**, and the official K-Fold example must be modified.
- (inference) With about 8 boxed test images per fold, a TFA-style protocol is needed:
  - repeat patient-grouped CV over several seeds (for example 5 seeds × 3 folds);
  - report the spread (mean, SD, min-max), not one number.
- (inference) NOW detection outputs should be framed as **annotation-assistant proposals that a human confirms**, consistent with the platform rule that boxes are written only after confirmation. No performance claims beyond "exploratory, n=14 patients" are defensible.

### Gaps
- Peer-reviewed YOLO studies on **phlebitis or IV-site** detection: none found in this search (other researchers may cover this).
- A quantitative learning curve for YOLO on diffuse skin lesions at 20-1,000 images: **no reliable evidence found**.

---

## Q4. Small-object settings (imgsz, P2, SAHI) — and are phlebitis lesions "small objects"?

### Takeaway
SAHI slicing gives large AP gains on truly tiny objects in aerial imagery (research evidence). YOLO26 offers a P2 head with no pretrained weights (official). A raised imgsz costs about (imgsz/640)² in compute.

Phlebitis redness that covers "a few %" of the photo is **medium or large by COCO size conventions** at imgsz 640. So the bottleneck is low contrast and boundary ambiguity, not object size (inference). SAHI and P2 are not worth doing NOW. imgsz 960/1024 is a reasonable FUTURE ablation only.

### Cited Findings
- **Akyon FC, Altinuc SO, Temizel A. "Slicing Aided Hyper Inference and Fine-tuning for Small Object Detection." ICIP 2022; arXiv:2202.06934 (v5, Oct 2022)** [C].
  - Slicing at inference raised AP on VisDrone/xView by 6.8% (FCOS), 5.1% (VFNet) and 5.3% (TOOD).
  - With slicing-aided fine-tuning the cumulative gains were 12.7%, 13.4% and 14.5%.
  - The abstract page does not quantify the compute cost.
  - Source: [arXiv](https://arxiv.org/abs/2202.06934)
- **YOLO26 P2** `yolo26-p2.yaml` is "architecture only", with no released weights [A] — [YOLO26 docs](https://docs.ultralytics.com/models/yolo26/)
- **Metrics Reloaded** recommends a **lower localization threshold for small structures and for high size variability** (FP3.1 and FP3.2) [B] — [arXiv 2206.01653](https://arxiv.org/html/2206.01653)
- **FLOPs at 640:** YOLO11n 6.5 B, YOLO11s 21.6 B, YOLO26s 20.9 B [A] — [YOLO11 docs](https://docs.ultralytics.com/models/yolo11/), [YOLO26 docs](https://docs.ultralytics.com/models/yolo26/)

### Inferences
- (inference, arithmetic) A 4:3 photo letterboxed to 640 is 640×480 = 307,200 px.
  - A lesion covering 3% of the image is about 9,200 px², roughly a 96×96 box. That is at the COCO medium/large boundary (COCO small < 32² = 1,024 px², large > 96²; COCO definitions from memory, page not opened).
  - Only lesions under about 0.33% of the frame are COCO-small at 640.
  - So most phlebitis redness is **not a small object**. Needle puncture points or early, faint redness in whole-arm shots may be.
- (inference) imgsz 1024 multiplies FLOPs and activation memory by about 2.56, and 1280 by about 4.
  - Possible benefit: finer colour and texture gradients at the boundary.
  - Risk: with 24 images, the larger input mainly adds variance.
  - NOW: keep 640. FUTURE: ablate 640 vs 960/1024 under patient-grouped CV, and keep the larger size only if per-patient sensitivity at a fixed FP/image improves beyond the seed-to-seed SD.
- (inference) SAHI and P2 head: not recommended. Lesions are not tiny, P2 has no pretrained weights (training from scratch with tiny data), and SAHI tiling splits diffuse lesions across tiles and complicates box merging.

### Gaps
- An actual distribution of box area / image area in the project's 24 boxed images was not measured here. **Compute it from the YOLO label files** (mean w·h in normalized units) before deciding on imgsz.

---

## Q5. Detection evaluation under small data

### Takeaway
With about 8 boxed test images per fold, mAP50-95 is dominated by IoU at 0.75-0.95. For diffuse erythema that measures the annotator's boundary convention rather than detection (inference, supported by IoU-perception and erythema inter-rater evidence).

Report instead:
- lesion-level sensitivity at a lenient localization criterion (IoU ≥ 0.3, or a center-hit criterion);
- false positives per image, **separately on normal images**;
- an FROC curve or FROC score;
- per-patient cluster-bootstrap CIs.

Choose the operating threshold on training folds only. Metrics Reloaded endorses F-beta plus FROC or AP and CIs for small test sets (research evidence / standard).

### Cited Findings
- **Maier-Hein L, Reinke A, et al. "Metrics Reloaded: recommendations for image analysis validation." Nature Methods 2024;21:195-212. doi:10.1038/s41592-023-02151-z** [B]. Preprint version: [arXiv 2206.01653](https://arxiv.org/html/2206.01653), which is what I opened; the nature.com page redirected to login.
  - For object detection, the localization criterion should depend on the reference granularity (Box IoU, Mask IoU, center point, point-inside-box).
  - The assignment strategy can be "based on IoU > 0.5" when no scores or overlaps exist.
  - Use F-beta as the per-class counting metric, complemented by **FROC ("easier interpretation") or AP ("standardized")** when scores exist.
  - Use lower thresholds for small or size-variable structures.
  - Give confidence intervals when the test set is small.
  - Bibliographic details confirmed via [Warwick WRAP](https://wrap.warwick.ac.uk/183654).
- **Strafforello O, Rajasekart V, Kayhan OS, Inel O, van Gemert J. "Humans disagree with the IoU for measuring object detector localization error." ICIP 2022; arXiv:2207.14221** [C]. More than 70 participants judged errors with equal IoU as unequal, so "IoU scores alone… might not be sufficient" — [arXiv](https://arxiv.org/abs/2207.14221)
- **Erythema boundary variability.** Liu et al. 2021, Clinical Hematology International (cutaneous chronic GVHD photos) [C; **search snippet only**, DOAJ returned 403].
  - Inter-rater ICC rose from 0.19 to 0.51 when baseline photos were added.
  - A "Do Not Miss / Do Not Include" confidence-tiered marking gave more consistent results (median Dice 0.94-0.96 vs 0.73-0.81 for traditional marking).
  - Source: [DOAJ](https://doaj.org/article/7fef6828160d4c5b80da2ff5c6f95cb9). Use cautiously.
- **FROC convention (LUNA16).**
  - The score is the average sensitivity at 1/8, 1/4, 1/2, 1, 2, 4 and 8 FPs per scan [C/D; search snippet from arXiv 1706.04303, paper not opened] — [arXiv](https://arxiv.org/pdf/1706.04303)
  - (inference) For 2D photos, use FPs per image, and a smaller range such as 0.125-2 FP/image.
- **Ultralytics val** uses `conf=0.001` by default, so mAP integrates over essentially all detections. The predict default is 0.25 [A] — [cfg docs](https://docs.ultralytics.com/usage/cfg/). (inference) Neither value is a clinically chosen operating point.
- **Leakage and inflation for non-independent samples** — Yagis 2021, above [C].

### Inferences
- (inference, arithmetic) With 10 lesions in a test fold, 8/10 sensitivity has a 95% Wilson CI of about 0.49-0.94. Each missed box moves sensitivity by 10 points. Fold-level mAP50-95 differences of ±0.1 between YOLO11s and YOLO26s are uninterpretable.
- (inference, arithmetic) 0 FP on all 9 normal images gives a 95% upper bound of about 3/9 ≈ 33% of normal images with ≥1 FP (rule of three). Nine normals cannot show a low false-alarm rate.
- (inference) **Recommended metric set** (custom post-processing, not Ultralytics `val` alone):
  1. Lesion-level sensitivity at IoU ≥ 0.3, plus a secondary center-hit or IoMin ≥ 0.5 criterion. Also report mAP50 for comparability. Report mAP50-95 only as a secondary figure, with a caveat.
  2. FP per image, split into lesion images and normal images.
  3. An FROC curve and FROC score (mean sensitivity at 0.125, 0.25, 0.5, 1, 2 FP/image).
  4. Image-level "any lesion detected" sensitivity and specificity, which ties into the "needs human review" routing.
  5. CIs by **patient-cluster bootstrap**: resample patients, recompute pooled metrics, 2,000 replicates. With 14 patients, percentile intervals are themselves unstable, so report them together with fold and seed spread.
- (inference) **Threshold selection.** Choose `conf` inside training folds only. Pick it to hit a target sensitivity (for example ≥0.9 lesion-level) or a maximum FP/image on train-fold out-of-fold predictions, then freeze it for the test fold.
  - The "needs human review" band (low-confidence interval) should be set the same way.
  - Never tune on the pooled test predictions.
- (inference) **Formulation.** For diffuse redness without a crisp edge, boxes give inconsistent references, and IoU-based metrics then penalize boundary convention. Alternatives:
  - (a) Keep detection, but evaluate with lenient or center criteria and use it to **crop or localize** for the image-level stage classifier and for human review.
  - (b) Coarse polygon or mask segmentation (YOLO-seg) with confidence-tiered annotation ("definitely red" core vs "uncertain" rim, following the Liu 2021 idea). Evaluate with tolerant boundary metrics.
  - (c) Image-level classification plus CAM for visualization only. No reliable evidence was found here that CAM localization is accurate enough for erythema, so it should not be presented as localization.
  - Given the stage is assigned at image level and boxes carry no stage, (a) is the lowest-cost NOW option.
- (inference) **Inter-annotator check.** Before trusting any IoU number, have 2 annotators box the same 24 images and compute their mutual IoU. Model-vs-human IoU above the human-vs-human IoU is not meaningful.

### Gaps
- Published inter-annotator **box** IoU for phlebitis or erythema: **no reliable evidence found**.
- I did not open the full Metrics Reloaded text for its handling of empty-reference images (Suppl. Note 2.4).

---

## Q6. GPU memory and time (YOLO11n/s, YOLO26s; imgsz 640/1024; 8-24 GB)

### Takeaway
I found no reliable published VRAM or epoch-time benchmarks for these models at these sizes. Estimates here rest on official FLOPs and AutoBatch behaviour (inference).

The local GPU is an RTX 5050 Laptop with 8 GB. AutoBatch (`batch=-1`) targets 60% of VRAM, about 4.8 GB. NOW (about 24-33 images) is dominated by per-epoch overhead and validation, and compute is not a constraint. For FUTURE, measure with the project's built-in `vram_bytes` logging.

### Cited Findings
- **AutoBatch [A].** `batch=-1` targets about 60% of GPU memory, a float sets the fraction, and on CPU it falls back to batch=16 — [cfg docs](https://docs.ultralytics.com/usage/cfg/), [Training Tips](https://docs.ultralytics.com/guides/model-training-tips/)
- **FLOPs at 640 [A]:** YOLO11n 6.5 B, YOLO11s 21.6 B, YOLO26s 20.9 B (params 2.6 / 9.4 / 9.5 M) — [YOLO11 docs](https://docs.ultralytics.com/models/yolo11/), [YOLO26 docs](https://docs.ultralytics.com/models/yolo26/)
- **Forum guidance [E]** suggests `batch=0.9`-style fractions to let AutoBatch size the batch. No hard numbers — [Ultralytics community](https://community.ultralytics.com/t/optimize-gpu-utilization-while-training/768)
- **Local measurement hook.** `adapters.py` line 555 logs `torch.cuda.max_memory_allocated()` per epoch, and the project config sets `amp: false` (FP32) (local).

### Inferences
- (inference) Compute per image is about FLOPs × (imgsz/640)². YOLO11s or YOLO26s at 1024 is about 53-55 GFLOPs forward, about 2.5 times YOLO11s at 640. Activation memory scales similarly with batch × imgsz².
- (inference) With FP32 (`amp: false`), activation memory is about twice AMP. At imgsz 1024 on 8 GB, expect batch to fall to low single digits for the s models. **Do not trust this estimate. Run `batch=-1` once per (model, imgsz) and record the chosen batch and `vram_bytes`.**
- (inference) If AMP is re-enabled for speed, check that the AMP capability check passes on the RTX 50-series. The project likely disabled AMP for determinism or compatibility; I did not check the reason.
- (inference) Epoch time:
  - NOW, about 6 batches of 4: seconds per epoch. Total runtime is dominated by validation and plotting.
  - FUTURE, about 670 train images: tens of batches per epoch at 640. Measure it, and do not quote a number without a run.
  - For 8 GB, n or s at 640 is the practical default. 1024 is for an ablation only.

### Gaps
- Published VRAM or time tables for YOLO11/YOLO26 training on consumer GPUs: **no reliable evidence found**.

---

## Q7. Recommendations — NOW vs FUTURE, with implementation

### Takeaway
**NOW** (24 boxed images, 14 patients, 9 normals): detection performance cannot be estimated reliably. Use the detector only as an **annotation assistant whose boxes a human confirms**. That needs a pretrained s model, a frozen backbone, AdamW lr0=1e-3, a fixed epoch count, weak geometric augmentation, near-zero hue jitter, single_cls, normals as background images, and patient-grouped 3-fold CV repeated over seeds.

**FUTURE** (about 1,000 photos): run proper patient-grouped 5-fold CV plus a held-out site-split test (hospital vs LINE). Ablate imgsz, freeze, YOLO11s vs YOLO26s and background ratio, and evaluate with FROC, FP/image on normals and patient-bootstrap CIs. (Evidence strength: official docs for the settings, few-shot and leakage literature for the protocol, inference for the specifics.)

### Cited Findings
- Official small-data row: AdamW lr0=0.001, about 50 epochs, patience=20, mosaic=0.5, mixup=0, copy_paste=0, freeze=10 [A] — [YOLO26 Training Recipe](https://docs.ultralytics.com/guides/yolo26-training-recipe)
- Few-shot evidence favours fine-tuning only the last layers, evaluated over multiple sampled training sets [D] — [Wang et al. 2020](https://arxiv.org/abs/2003.06957)
- Group-aware folds are needed [A FAQ] — [K-Fold guide](https://docs.ultralytics.com/guides/kfold-cross-validation/). Small-data leakage is severe [C] — [Yagis 2021](https://doaj.org/article/ba8c3daef34b44d98cdadf6e89dba3e3)
- Metric choice and CIs [B] — [Metrics Reloaded](https://arxiv.org/html/2206.01653)
- Installed-code facts: auto → AdamW below 10k iterations; nbs accumulation; `patience=0` → no early stop; freeze mapping [A, local 8.4.161].

### Inferences

**NOW — recommendation table (all inference unless noted)**

| Setting | Value / range | Evidence | Benefit / when not worth it |
|---|---|---|---|
| Model | `yolo11s.pt` or `yolo26s.pt` (COCO-pretrained); keep n as a speed baseline | [A] tables | The s-vs-26s difference is below noise at n=24; do not over-interpret |
| imgsz | 640 (no rect for training) | [A] default; Q4 inference | 1024 not worth it until the lesion-size distribution shows <0.5% area |
| freeze | 10 (official) or 11 (full backbone); ablate {0, 10, 11} | [A] recipe; [D] TFA | Reduces overfitting; freeze=0 is only worth testing at FUTURE scale |
| optimizer / lr0 | `optimizer='AdamW', lr0=0.001` explicit (auto would use 0.002 and ignore lr0) | [A] recipe + code | — |
| batch / nbs | batch 8, **nbs 8** (or batch 4, nbs 4) | [A] code; inference | Restores one optimizer step per batch (default nbs=64 gives about 1 step per 3-4 epochs) |
| epochs / patience | Fixed 50-100 chosen in advance, `patience=0`; report last.pt; or early stop only via an inner split | [A] recipe (about 50) + code | Avoids optimistic best.pt picked on the test fold |
| warmup / cos_lr | warmup_epochs 3 (= about 12-18 iterations); cos_lr True or False (minor) | [A] code | Negligible effect expected |
| Augmentation | mosaic 0-0.5, mixup 0, copy_paste 0, fliplr 0.5, degrees ≤10, scale 0.1-0.3, translate 0.05-0.1, **hsv_h ≤0.005**, hsv_s/v ≤0.2 | [A] recipe; inference | Hue jitter can turn redness into normal skin tone (label noise); details in the augmentation note |
| single_cls | True (nc=1) | — | Stage belongs to the classifier |
| Background images | Include the 9 normal photos (image with no or empty label file) in **training folds only for patients in that fold** | Industry practice (Ultralytics treats unlabeled images as background; not re-verified in this session) | Lowers FP on normal skin; can lower recall if overweighted |
| multi_scale | 0 | [A] default | Not worth it at n=24 |
| Validation | `conf=0.001, iou=0.7` for mAP; the operating conf comes from train-fold OOF | [A] cfg | — |
| Repeats | 3 patient-grouped folds × 5 seeds | [D] TFA protocol | Shows variance; about 15 runs, each minutes long |

**Minimum data (inference):**
- Any reported detection metric needs ≥3 patients with lesions per test fold.
- An "assistant only" deployment needs nothing more than human confirmation.
- A performance claim needs FUTURE-scale data plus an external (site or LINE) test.

**Risks:**
- Overfitting to patient, arm or background.
- Lucky folds.
- Hue augmentation destroying the signal.
- Box-convention noise.
- Normal images from the same patients leaking across folds if the split is not grouped on all images.

**FUTURE (~1,000 photos: about 667 lesion images with boxes plus about 333 normals):**
- Model: YOLO11s vs YOLO26s (and n), pretrained. Freeze ablation {0, 10}.
- Optimizer:
  - auto → AdamW, since about 670/16 × 100 ≈ 4,200 iterations is below 10,000.
  - Or explicit AdamW with lr0 1e-3.
  - MuSGD only when iterations exceed 10k, and only as an ablation.
- Schedule: epochs 100-150, patience 30-50 (val folds are now larger), batch from AutoBatch (`-1`), nbs default.
- Augmentation: mosaic 0.5-1.0 with close_mosaic 10; imgsz 640 vs 960/1024 ablation.
- Backgrounds: about 33% background images is more than typical practice. Ablate 10% / 33% and report FP/image on normals vs sensitivity.
- Protocol: 5-fold StratifiedGroupKFold (group = patient, stratify on stage/normal), plus a **held-out external split** (train hospital → test LINE, and the reverse) to measure domain shift.
- GPU: s at 640 should fit 8 GB at moderate batch (verify). For 1024, use AutoBatch plus AMP if it is stable.

**Pseudo-code (per-fold yaml with patient grouping; local only)**

```python
# Code location: new helper next to 02_主程式碼/src/workbench/adapters.py::yolo_train (data prep),
# training call stays in adapters.py line ~607 (model.train(**params)), params merged from configs/train.json.
from sklearn.model_selection import StratifiedGroupKFold
from ultralytics import YOLO, settings
settings.update({"sync": False, "clearml": False, "comet": False, "dvc": False,
                 "mlflow": False, "raytune": False})        # no outbound analytics/loggers; never use HUB/Platform

df = load_index()   # one row per photo: path, patient_id, has_box (bool), stage_or_normal
for seed in [0, 1, 2, 3, 4]:
    sgkf = StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=seed)
    for k, (tr, te) in enumerate(sgkf.split(df, y=df.stage_or_normal, groups=df.patient_id)):
        assert set(df.patient_id[tr]).isdisjoint(df.patient_id[te])
        write_list(f"fold{seed}_{k}_train.txt", df.path[tr])      # includes normal photos as backgrounds
        write_list(f"fold{seed}_{k}_val.txt",   df.path[te])      # (empty/no .txt label = background)
        write_yaml(f"fold{seed}_{k}.yaml", dict(path=ROOT, train=..., val=..., names={0: "lesion"}))

        model = YOLO("models/pretrained/yolo26s.pt")              # local weights
        model.train(data=f"fold{seed}_{k}.yaml", imgsz=640, epochs=60, patience=0,
                    batch=8, nbs=8, optimizer="AdamW", lr0=1e-3, cos_lr=False, warmup_epochs=3,
                    freeze=10, single_cls=True, mosaic=0.0, mixup=0.0, copy_paste=0.0,
                    fliplr=0.5, degrees=10, translate=0.05, scale=0.2, hsv_h=0.005, hsv_s=0.2, hsv_v=0.15,
                    seed=seed, deterministic=True, workers=0, amp=False, plots=True)
        preds = model.predict(test_paths, conf=0.001, iou=0.7, nms=None)   # nms=False -> YOLO26 one-to-one head
        save_oof(preds, fold=(seed, k))

# Custom evaluation (new module, e.g. src/workbench/detection_metrics.py):
# match(pred, gt, crit="iou>=0.3" | "center_in_box"), greedy by score, one-to-one
# froc = [sens_at_fppi(t) for t in (0.125,0.25,0.5,1,2)], fppi split normal vs lesion images
# conf_op = choose_on_train_oof(target_sens=0.9)  -> apply to test fold; "needs human review" band likewise
# CI = patient_cluster_bootstrap(oof, B=2000)
```

**Platform validation (inference):**
- After each run, read `effective.json` (optimizer class, LRs, trainable parameter count, end2end flag) and `checkpoint_selection.json` (`adapters.py` lines 557-583). Confirm that AdamW at 0.001 ran, that trainable parameters dropped with freeze, and that the epoch was fixed.
- Keep the human-confirmation step in `assist.py` (line 63 calls predict with the NMS/end2end switch) as the only path by which a box is written.

### Gaps
- None of the parameter ranges have been validated on phlebitis photos. They are starting points and must be justified by the patient-grouped CV results.
- Background images: the installed 8.4.161 `ultralytics/data/dataset.py` line 186 reports `f"{nf} images, {nm + ne} backgrounds, {nc} corrupt"`. So **missing (nm) and empty (ne) label files both count as backgrounds** [A, local code]. A missing or empty label file is therefore a valid way to add the 9 normal photos. Confirm the "backgrounds" count in the scan log on the first run.
- The official docs page on recommended background-image proportion was not re-opened in this session.
