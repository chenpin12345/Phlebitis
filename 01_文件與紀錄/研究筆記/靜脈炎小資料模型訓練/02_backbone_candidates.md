# Backbone candidates for a small, local, offline phlebitis skin-photo classifier

Scope: verified facts (existence, size, data, license, hosting, offline/safetensors usability, VRAM) for candidate pretrained backbones; evidence on dermatology benchmarks; license conflicts; NOW (≈120 photos / 14 patients) vs FUTURE (≈1,000 balanced) recommendations.
All sources accessed 2026-10-30. Source grades: [A] official docs / model cards / license files; [B] top-venue peer-reviewed; [C] other peer-reviewed; [D] preprint; [E] blog/forum/example code. Full bibliographic register at the end of Q4. Conclusion labels: (research evidence) / (industry practice) / (inference).

---

## Q1. Per-model facts: existence, params, resolution, patch, embedding, pretraining data, license, hosting, gating, offline use, safetensors

### Takeaway
All requested models exist except that "SkinGPT" is an MLLM chat system, not a classification backbone. Every candidate can run fully offline on local weights once downloaded. The real blockers are file format and licence terms. Derm Foundation ships only as TF-Keras, so it cannot meet the project's "safetensors only" import rule. PanDerm ships as `.pth` under CC-BY-NC-ND. BiomedCLIP ships as `.bin`. DINOv3, MedSigLIP and Derm Foundation need a gated Hugging Face agreement before the one-time download.

### Verified comparison table (all values from sources cited in the Cited Findings list; "n/s" = not stated in the source I opened)

| Model | Exists? | Params (vision) | Input / patch | Emb. dim | Pretraining data | License (doc date) | Hosting / gated | Weights format | Offline on Windows/PyTorch |
|---|---|---|---|---|---|---|---|---|---|
| DINOv2 ViT-S/14, B/14, L/14, g/14 (± registers) | Yes | 21M / 86M / 300M / 1.1B | patch 14 | n/s on pages opened (384/768/1024/1536 per benchmark paper for B and g) | 142M curated images (LVD-142M) | Apache-2.0 (code + weights) | HF `facebook/dinov2-*`, ungated | safetensors | Yes (transformers, torch.hub) |
| DINOv3 ViT-S/16, S+/16, B/16, L/16, H+/16, 7B/16 | Yes (arXiv 2508.10104, 13 Aug 2025) | 21M / 29M / 86M / 300M / 840M / 6,716M | patch 16; 4 register tokens; any size that is a multiple of 16 | 384 / 384 / 768 / 1024 / 1280 / 4096 | LVD-1689M (≈1.689B images curated from ≈17B public Instagram images); SAT-493M satellite variants also exist | DINOv3 License (custom, not Apache; "Last Updated: August 19, 2025") | HF `facebook/dinov3-*`, **gated** (share HF info + accept). The timm mirrors also carry dinov3-license | safetensors (F32) | Yes, after the gated download (transformers AutoModel; timm mirrors exist) |
| DINOv3 ConvNeXt T/S/B/L (distilled from ViT-7B) | **Yes** | 29M / 50M / 89M / 198M | CNN | n/s | LVD-1689M | DINOv3 License | same, gated | safetensors | Yes |
| SigLIP 2 (So400m/14-384 card checked) | Yes (arXiv 2502.14786) | ≈1B total (vision+text) for So400m | 384 / patch 14 | n/s | WebLI | Apache-2.0 | HF `google/siglip2-*`, ungated | safetensors | Yes (transformers; also in open_clip) |
| SigLIP (v1) | Yes; open_clip lists ViT-SO400M-14-SigLIP | not verified this session | – | – | WebLI | not verified this session | HF/open_clip | – | Yes |
| CLIP (OpenAI) / OpenCLIP | Yes | not verified this session (open_clip's model_profile.csv not opened) | 224 typical | – | WIT (OpenAI); LAION-2B, DataComp-1B, DFN-2B (OpenCLIP) | open_clip code license not read; per-weight licences on each HF card | HF/open_clip; `pretrained=` accepts a local path | .bin common; safetensors not mentioned | Yes |
| ConvNeXt V1 (torchvision) | Yes | T 28.6M / S 50.2M / B 88.6M / L 197.8M | 224 | – | ImageNet-1K weights | torchvision: weights "may have their own licenses…"; user must check | torchvision | .pth (convertible) | Yes |
| ConvNeXt V2 (timm, FCMAE) | Yes | atto 3.7 / femto 5.2 / pico 9.1 / nano 15.6 / tiny 28.6 / base 88.7 / large 198.0 / huge 660.3 M | 224 train / 288 test (tiny) | – | FCMAE self-sup + IN-1k / IN-22k fine-tune | **CC-BY-NC-4.0** (timm card) | HF `timm/convnextv2_*`, ungated | safetensors | Yes |
| EfficientNetV2 (torchvision) | Yes | S 21.5M / M 54.1M / L 118.5M (B0 = 5.3M for reference) | – | – | ImageNet-1K | same torchvision caveat | torchvision | .pth | Yes |
| BiomedCLIP (Microsoft) | Yes | n/s (ViT-B/16 + PubMedBERT) | 224 / patch 16 (from name) | 512 (per benchmark paper) | PMC-15M: ≈15M figure–caption pairs from PubMed Central | MIT. Card: "Any deployed use case … is currently out of scope" | HF, ungated | `open_clip_pytorch_model.bin` (no safetensors noted) | Yes (open_clip) |
| Derm Foundation (Google HAI-DEF) | Yes (created 2023-12-19, v1.0.0) | n/s (BiT-M ResNet101x3) | **448×448 PNG** | **6144** | Stage 1: web image–text pairs (size n/s). Stage 2: tele-derm (US, Colombia), Australian skin-cancer set, other public images; smartphone + dermatoscope | HAI-DEF Terms of Use ("Last modified: November 15, 2024") | HF `google/derm-foundation`, **gated** (accept terms; approved immediately) | **TF-Keras SavedModel** (`from_pretrained_keras`); **no safetensors** | Runs locally per card; cloud optional. Needs a TensorFlow environment, not PyTorch |
| MedSigLIP-448 (Google HAI-DEF) | Yes (created 2025-07-09, v1.0.0) | ≈400M vision + ≈400M text (0.9B total) | **448×448**; patch n/s on card | 1152 (per benchmark paper) | Medical image–text pairs (CXR, derm, ophtho, histopath, CT/MRI) + natural pairs. Derm sources: SCIN, PAD-UFES-20, Colombian tele-derm, Australian skin cancer, non-diseased skin | HAI-DEF Terms of Use | HF `google/medsiglip-448`, **gated** | safetensors | Yes (transformers AutoModel) |
| PanDerm (Nature Medicine 2025) | **Yes** | n/s (ViT-L/16; Base = ViT-B/16, released 04/2025) | pretrain 224 / patch 16 | 1024 (L) / 768 (B) per benchmark paper | ≈2.15M images: TBP tiles 757,890; dermatopathology 537,047; clinical 460,328; dermoscopy 384,441 | **CC-BY-NC-ND 4.0** (non-commercial academic research) | Google Drive (.pth); DermLIP_PanDerm on HF | **.pth** (conversion needed) | Yes (PyTorch 2.4.1 code) |
| MONET (Nature Medicine 2024) | **Yes** | 0.4B total (CLIP ViT-L/14) | ViT-L/14; resolution n/s | 1024 (per benchmark paper) | 105,550 dermatology image–text pairs from the medical literature | **not stated on HF card** | HF `suinleelab/monet` | safetensors | Yes (transformers zero-shot pipeline) |
| DermLIP / Derm1M (ICCV 2025) | **Yes** | n/s. Variants: ViT-B/16 + GPT77 text; PanDerm-B + PubMedBERT-256 text | n/s | – | Derm1M: 1,029,761 image–text pairs, 403,563 unique images, 390 conditions (YouTube, PubMed, forums, public datasets, slides) | Dataset CC BY-NC 4.0; **weights licence not stated** | HF `redlessone/DermLIP_*` (gating not mentioned) | n/s (open_clip-style hf-hub loading is inferred) | Likely yes (inference) |
| RAD-DINO (Microsoft) | Yes | 86.6M (ViT-B/14, from DINOv2-base) | shorter side 518 | 768 | 882,775 chest X-rays (MIMIC-CXR, CheXpert, NIH, PadChest, BRAX) | MIT; "not meant to be used for clinical practice" | HF, ungated | safetensors | Yes. **Wrong domain (chest X-ray)** |
| SkinGPT-4 | Exists (Nature Communications, Jul 2024; arXiv 2304.10691) | MLLM (fine-tuned MiniGPT-4) | – | – | 52,929 public + proprietary skin images | not verified | – | – | Not a classification backbone |
| DermINO | Exists as a preprint (arXiv 2508.12190, v2 25 Sep 2025) | n/s | – | – | 432,776 images | weights availability and licence not found | – | – | Unknown |

### Cited Findings
- DINOv2 sizes: ViT-S/14 21M, B/14 86M, L/14 300M, g/14 1,100M, each with and without registers. ImageNet linear accuracy, e.g. S 81.1% and S+reg 80.9%. Pretraining on "142 M images". "DINOv2 code and model weights are released under the Apache License 2.0". XRay-DINO and Cell-DINO weights are FAIR Noncommercial instead [A] — [facebookresearch/dinov2 README](https://github.com/facebookresearch/dinov2)
- `facebook/dinov2-small`: Apache-2.0, ungated, 22.1M params, safetensors, transformers AutoModel [A] — [HF dinov2-small](https://huggingface.co/facebook/dinov2-small)
- DINOv3 variant table, LVD-1689M (≈17B Instagram pool), SAT-493M, 4 registers, patch 16, gated access, safetensors F32, ConvNeXt T/S/B/L distilled variants (29/50/89/198M) [A] — [HF dinov3-vitb16-pretrain-lvd1689m](https://huggingface.co/facebook/dinov3-vitb16-pretrain-lvd1689m)
- DINOv3 License, "Last Updated: August 19, 2025": a limited, royalty-free licence to use, modify and redistribute. Commercial use is not explicitly barred. ITAR/trade-control, military, nuclear, espionage and weapons uses are prohibited. Redistribution must include the agreement. Published research must acknowledge use. Meta may modify the terms, and continued use counts as acceptance. On termination you must delete the materials. Medical use is not mentioned [A] — [DINOv3 LICENSE.md](https://github.com/facebookresearch/dinov3/blob/main/LICENSE.md)
- timm mirrors of DINOv3 (e.g. `timm/vit_small_patch16_dinov3.lvd1689m`) carry the dinov3-license tag and a LICENSE.md. I saw only search snippets [E] — [timm dinov3 repo listing](https://huggingface.co/timm/vit_small_patch16_dinov3.lvd1689m/tree/main)
- SigLIP 2 So400m/14-384: Apache-2.0, ungated, ≈1B params (F32 safetensors), WebLI, transformers support. Tschannen et al. 2025, arXiv 2502.14786 [A] — [HF siglip2-so400m-patch14-384](https://huggingface.co/google/siglip2-so400m-patch14-384)
- open_clip lists SigLIP / SigLIP2 models. `pretrained` accepts local paths and Hub checkpoints can be downloaded manually. Safetensors is not mentioned on the README [A] — [mlfoundations/open_clip](https://github.com/mlfoundations/open_clip)
- torchvision parameter counts: EfficientNet-B0 5.3M (77.7% IN-1k), V2-S 21.5M (84.2%), V2-M 54.1M, V2-L 118.5M; ConvNeXt T 28.6M, S 50.2M, B 88.6M, L 197.8M; ViT-B/16 86.6M. Weights "may have their own licenses or terms and conditions derived from the dataset used for training" [A] — [torchvision models](https://docs.pytorch.org/vision/stable/models.html)
- ConvNeXt V2 timm weights are licensed **cc-by-nc-4.0**. Tiny is 28.6M params and 4.5 GMACs, with the variant parameter list as in the table [A] — [HF timm/convnextv2_tiny.fcmae_ft_in22k_in1k](https://huggingface.co/timm/convnextv2_tiny.fcmae_ft_in22k_in1k)
- BiomedCLIP card facts:
  - MIT licence, PMC-15M, open_clip 2.23.0, `.bin` weights.
  - The card says "Any deployed use case of the model --- commercial or otherwise --- is currently out of scope."
  - Citation: Zhang S. et al., NEJM AI 2(1), doi:10.1056/AIoa2400640.

  [A] — [HF BiomedCLIP](https://huggingface.co/microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224)
- Derm Foundation card facts:
  - Architecture: BiT-M ResNet101x3. Input: 448×448 PNG. Output: 6144-d embedding.
  - Framework: TF-Keras with a `serving_default` signature; trained in JAX.
  - Training data: two stages, including tele-dermatology data (US, Colombia) captured by smartphones and dermatoscopes.
  - Access: gated under HAI-DEF terms.
  - Runs locally; Google Cloud Model Garden is only suggested for scale.
  - Performance claim: a linear classifier on its embeddings is "≈10–15%" more accurate than standard BiT-M. No tables are given.

  [A] — [HF google/derm-foundation](https://huggingface.co/google/derm-foundation)
- MedSigLIP-448 card facts: ≈400M + 400M params, 448 px input, 64-token text, training data list including SCIN and PAD-UFES-20, gated HAI-DEF access, safetensors, transformers support, created 2025-07-09 [A] — [HF google/medsiglip-448](https://huggingface.co/google/medsiglip-448)
- PanDerm repository facts:
  - Paper: Nature Medicine 2025 (article s41591-025-03747-y); preprint arXiv 2410.15038.
  - Licence: CC-BY-NC-ND 4.0, non-commercial academic research.
  - Weights: on Google Drive as `.pth`; PanDerm is ViT-L/16 and PanDerm_Base is ViT-B/16 (04/2025).
  - Software: PyTorch 2.4.1.

  [A] — [GitHub SiyuanYan1/PanDerm](https://github.com/SiyuanYan1/PanDerm)
- PanDerm pretraining modality counts (≈2.15M images): TBP 35.3%, dermatopathology 25.4%, clinical 21.4%, dermoscopy 17.9% [D] — [arXiv 2410.15038v3](https://arxiv.org/html/2410.15038)
- MONET: CLIP ViT-L/14, 0.4B params, 105,550 pairs, safetensors, transformers. Kim C. et al., Nature Medicine 2024, doi:10.1038/s41591-024-02887-x. The card does not state a licence [A] — [HF suinleelab/monet](https://huggingface.co/suinleelab/monet)
- Derm1M / DermLIP: 1,029,761 pairs and 403,563 unique images. The dataset is "non-commercial research purposes under the CC BY-NC-4.0 license". HF repos are `redlessone/DermLIP_ViT-B-16` and `redlessone/DermLIP_PanDerm-base-w-PubMed-256`. The weights licence is not separately stated [A/B] — [GitHub SiyuanYan1/Derm1M](https://github.com/SiyuanYan1/Derm1M); [ICCV 2025 paper page](https://openaccess.thecvf.com/content/ICCV2025/html/Yan_Derm1M_A_Million-scale_Vision-Language_Dataset_Aligned_with_Clinical_Ontology_Knowledge_ICCV_2025_paper.html)
- RAD-DINO: MIT, 86.6M params, 518 px, 882,775 chest X-rays, "not meant to be used for clinical practice". Pérez-García F. et al., Nature Machine Intelligence 2025, doi:10.1038/s42256-024-00965-w [A] — [HF microsoft/rad-dino](https://huggingface.co/microsoft/rad-dino)
- SkinGPT-4: a fine-tuned MiniGPT-4 MLLM trained on 52,929 skin images, published in Nature Communications in July 2024. I verified only the DOAJ listing and the arXiv mirror [C/D] — [DOAJ record](https://doaj.org/article/4cc0771c7c504516849eb9d83dc15cf9); [arXiv 2304.10691](https://arxiv.org/abs/2304.10691v2)
- DermINO: a 432,776-image hybrid-pretrained derm model. I found no numeric comparison or weights licence on the abstract page [D] — [arXiv 2508.12190](https://arxiv.org/abs/2508.12190)

### VRAM estimates (inference, not measured; basis stated)
Basis:
- Weights in fp16 take params × 2 bytes.
- Full fine-tuning with AMP + AdamW keeps ≈16 bytes/param of persistent state: fp32 weights 4 + grads 4 + Adam moments 8.
- Activations at batch 16, 224 px, AMP are roughly 1–2 GB for ViT-S/ConvNeXt-T-class models, 3–5 GB for ViT-B-class, and 8–12 GB for ViT-L-class.
- Add ≈0.5–1 GB for the CUDA context.

Uncertainty is roughly ±50%. **Measure on the target GPU with `torch.cuda.max_memory_allocated()` before relying on these figures.** These are (inference) and not from any source.

| Backbone | Frozen-feature inference (fp16, batch 16) | Full fine-tune (AMP, AdamW, batch 16, 224) | Fits 8 GB consumer GPU? |
|---|---|---|---|
| DINOv2/v3 ViT-S, EfficientNetV2-S, ConvNeXt(V2)-T, EffNet-B0 | < 1.5 GB | ≈ 2–4 GB | Yes |
| DINOv2/v3 ViT-B, ConvNeXt-B, BiomedCLIP-B, PanDerm-B, SigLIP2-B | ≈ 1–2 GB | ≈ 5–8 GB | Inference yes; fine-tuning borderline. Use grad checkpointing or LoRA |
| DINOv2/v3 ViT-L, MONET (L/14), PanDerm-L | ≈ 2–3 GB | ≈ 12–18 GB | Inference yes; full fine-tuning no (needs 16–24 GB or LoRA) |
| MedSigLIP vision (≈400M) at its native 448 px (4× the tokens of 224) | ≈ 2–4 GB | > 20 GB (full fine-tune not advisable) | Inference yes |
| Derm Foundation (BiT-R101x3, 448 px, TF) | Param count not verified. Likely 2–4 GB | not applicable (embedding API) | Inference probably yes |

### Inferences
- (inference) Only DINOv2, SigLIP 2, MONET, MedSigLIP, DINOv3 and RAD-DINO already ship safetensors that load directly in transformers. Converting PanDerm `.pth`, BiomedCLIP `.bin` or torchvision `.pth` to safetensors is mechanically easy: load once with `torch.load(..., weights_only=True)`, then `safetensors.torch.save_file`. This requires unpickling the original file once, so do it only from the official source.
- (inference) Derm Foundation is not convertible to PyTorch safetensors in a practical way, because it is a TF SavedModel with a different architecture runtime. Using it would violate the project's "safetensors only" external-model rule unless the rule is relaxed for a separate, offline TF embedding step. Recent TensorFlow versions do not support native-Windows GPU (WSL2 required). This is industry knowledge I did not re-verify this session; see Gaps.
- (inference) Gated models (DINOv3, MedSigLIP, Derm Foundation) need a one-time online download through an HF account. After that, `HF_HUB_OFFLINE=1` or a local path gives fully offline use. No photo leaves the machine.
- (inference) DINOv3 ViT-S/16 uses 16-px patches, so a 224 input gives 196 tokens. That is cheaper than DINOv2-S/14 at 224, which gives 256 tokens.

### Gaps
- Parameter counts were not stated on the pages opened for BiomedCLIP, PanDerm, DermLIP, Derm Foundation (BiT-R101x3) and OpenAI CLIP / OpenCLIP. I have **no reliable evidence** for these numbers this session.
- Embedding dims for DINOv2-S/L and MedSigLIP patch size were not on the opened cards. The dims in the table come only from the 2601.12382 benchmark.
- Not opened this session, so unverified:
  - MONET's licence; the HF card is silent and the GitHub LICENSE was not opened.
  - The DermLIP weights licence.
  - The open_clip code licence.
  - The OpenAI CLIP licence.
  - The SigLIP v1 card.
  - SigLIP 2 B/16 sizes.
- I did not open the TensorFlow installation docs, so the native-Windows GPU limitation is unverified this session.

---

## Q2. Benchmark evidence: do domain-specific (derm) models beat general models (DINOv2/v3, SigLIP) on clinical, non-dermoscopic photos in few-shot / linear-probe settings?

### Takeaway
Developer-run studies (PanDerm, Derm1M, Google's model cards) report that derm-specific or medical models beat DINOv2 and BiomedCLIP by a few points. The one independent benchmark found (2026, dermoscopy only, patient-level split) shows that general-medical MedSigLIP and MedImageInsights are best. In that benchmark Derm Foundation and MONET are within ≈0.5 point, DINOv2-giant is ≈1.8 points behind on 40-class, and PanDerm is *worse* than DINOv2 (research evidence). There is **no reliable evidence** on clinical smartphone photos of erythema or swelling such as phlebitis. Expected gains from domain models are small, uncertain, and must be tested on project data.

### Cited Findings
- **PanDerm (developer-run; Nature Medicine 2025 [B], arXiv v3 [D]).**
  - Extended Data Table 8, clinical-photo datasets (W_F1 / AUROC / BACC):

    | Dataset | SL-ImageNet ViT-L | DINOv2 ViT-L | SwAVDerm | PanDerm |
    |---|---|---|---|---|
    | DDI | .773 / .743 / .655 | .756 / .749 / .612 | .730 / .747 / .571 | .790 / .843 / .722 |
    | DermC | .756 / .797 / .700 | .763 / .796 / .717 | – | .788 / .876 / .740 |

    General DINOv2 ≈ supervised ImageNet on clinical photos. PanDerm gains ≈+0.1 AUROC on DDI.
  - Label efficiency on PAD (W_F1): PanDerm .607 at 5% of labels vs DINOv2 .560; .758 vs .695 at 100%.
  - Linear probing (sklearn logistic regression) ≈ full fine-tuning for PanDerm (PAD 94.50 vs 93.59).
  - Splits for the clinical datasets are **not described as patient-level** in the visible text; HAM10000 used the "clean" no-patient-crossing version, and TBP was patient-level.
  - External melanoma validation came from 7 centres (+2.1 to +4.0% AUROC).

  — [arXiv 2410.15038v3](https://arxiv.org/html/2410.15038); [Nature Medicine article page](https://www.nature.com/articles/s41591-025-03747-y) (paywall redirect; content read via arXiv)
- PanDerm supplementary text (search snippet only) reports that a CLIP teacher pretrained on the natural domain outperformed BiomedCLIP and MONET as teachers. This is a pretraining-teacher ablation, not a downstream linear probe, so it is weak counter-evidence that small medical CLIPs lag web-scale CLIP [B, snippet only] — [PanDerm supplementary PDF (institutional mirror)](https://cris.unibo.it/retrieve/handle/11585/1037927/a6367364-c674-4397-806e-2f7e058acf95/41591_2025_3747_MOESM1_ESM.pdf)
- **Independent benchmark (Yuceyalcin, Yilmaz, Temelkuran; arXiv 2601.12382v1, 18 Jan 2026) [D].**
  - Setup: DERM12345, 12,345 **dermoscopic** images from Türkiye, patient-level split (9,860 / 2,485), no external validation. Frozen features with the best of 6 adapters (MLP usually best).
  - Weighted F1 (binary malignancy / 40-class):
    - MedSigLIP 96.43 / 69.79
    - Derm Foundation 96.04 / 69.50
    - MONET 96.02 / 69.31
    - DINOv2-giant 95.61 / 68.00
    - CLIP-L 95.80 / 67.81
    - DINOv3 (384-d, i.e. ViT-S) 95.60 / 66.78
    - DINOv2-B 95.99 / 65.95
    - MedImageInsights 97.52 / 65.50
    - CLIP-B 95.29 / 64.64
    - PanDerm-B 95.59 / 64.12
    - ResNet-50 94.51 / 58.82
    - BiomedCLIP 94.99 / 58.78
    - PanDerm-L 91.79 / 36.65 (authors suspect a defective public checkpoint)
  - The authors conclude that general medical models at scale can match or exceed specialised ones, and that clinical photos remain unverified.

  — [arXiv 2601.12382v1](https://arxiv.org/html/2601.12382v1)
- **MedSigLIP card (Google-run).** On "Skin Conditions" (1,612 images, 79 classes), MedSigLIP linear-probe AUC is 0.881 vs Derm Foundation 0.843; MedSigLIP zero-shot AUC is 0.851. The split method is not stated on the card [A] — [HF medsiglip-448](https://huggingface.co/google/medsiglip-448)
- **Derm Foundation card (Google-run).** Its embeddings beat standard BiT-M by "about 10–15%" accuracy across training-data fractions. No tables are given and the comparison is only against an ImageNet-era CNN [A] — [HF derm-foundation](https://huggingface.co/google/derm-foundation)
- **Derm1M / DermLIP (developer-run, ICCV 2025) [B].**
  - Zero-shot average over PAD, HAM10000, Fitzpatrick17k and Daffodil: DermLIP-PanDerm 58.8% vs BiomedCLIP 44.1%.
  - 10%-label linear probe: 69.6% vs MONET 66.9%.
  - No DINOv2 or SigLIP baseline appears on the repository page.

  — [GitHub Derm1M](https://github.com/SiyuanYan1/Derm1M)
- The HAI-DEF technical report (Kiraly et al., arXiv 2411.15128, v2 26 Nov 2024) exists, but its abstract page gives no derm data-efficiency numbers. I did not read the full text [D] — [arXiv 2411.15128](https://arxiv.org/abs/2411.15128)

### Inferences
- (research evidence, weak) On clinical photos (DDI, DermC), DINOv2-L was no better than supervised ImageNet ViT-L in PanDerm's own tables. Self-supervised general features are therefore not automatically superior on clinical skin photos.
- (research evidence) In the only independent comparison, which used dermoscopy, the spread between the best general-vision model (DINOv2-g) and the best derm/medical model (MedSigLIP) was ≈1.8 W-F1 points on the 40-class task and <1 point on binary. Those gaps are far smaller than the sampling noise expected with 14 patients.
- (inference) Transfer to phlebitis:
  - Phlebitis is diffuse erythema, swelling and cords along a vein on arm or hand photos, with no lesion morphology.
  - Most domain models are *not* dermoscopy-only:
    - PanDerm has 21% clinical images and 35% TBP.
    - Derm Foundation includes smartphone tele-dermatology.
    - MedSigLIP includes SCIN (crowd-sourced smartphone photos) and PAD-UFES-20 (smartphone clinical photos).
  - Derm Foundation and MedSigLIP are therefore the closest in acquisition domain (smartphone, uncontrolled lighting). DermLIP/Derm1M is closest in breadth of conditions.
  - None was trained on IV-site or phlebitis images, so any benefit must be shown empirically.
- (inference) With binary normal = 9 photos (from an even smaller number of patients), a 3-fold patient-level CV cannot resolve backbone differences of 1–5 points. Backbone comparisons NOW are exploratory. Report them with CIs and do not use them for selection claims.

### Gaps
- **No reliable evidence found** of any backbone evaluated on phlebitis, IV-site, or erythema/inflammation-severity photos.
- I found no independent (non-developer) benchmark on clinical non-dermoscopic photos that compares DINOv2/v3 and SigLIP 2 with Derm Foundation, MedSigLIP, PanDerm and MONET under a patient-level split. The CVPRW 2026 "Exploiting Unpaired Dermatology" supplement appeared in search results but was not opened.
- The PanDerm per-model linear-probe numbers vs MONET and BiomedCLIP on clinical datasets were not visible in the portions read. The Fitzpatrick17k and SD-128 numbers for DINOv2 were not found.
- DINOv3 and SigLIP 2 have no dermatology clinical-photo results in any source read, apart from DINOv3 (ViT-S) in the dermoscopy benchmark.

---

## Q3. License / data-use terms that may conflict with a research-only, local-only, no-cloud project

### Takeaway
No candidate requires a cloud API at inference, and all can run offline after download (research evidence from the cards). The main issues fall into four groups:
- **Gated agreements:** DINOv3, MedSigLIP and Derm Foundation.
- **HAI-DEF obligations:** "Clinical Use" explicitly includes research studies that diagnose or treat patients, and regulatory and pass-through obligations apply.
- **Non-commercial / no-derivatives terms:** PanDerm is CC-BY-NC-ND, ConvNeXt V2 timm weights are CC-BY-NC, and DermLIP data is CC-BY-NC.
- **Format:** Derm Foundation offers no safetensors.

### Cited Findings
- HAI-DEF Terms ("Last modified: November 15, 2024") [A] — [HAI-DEF Terms of Use](https://developers.google.com/health-ai-developer-foundations/terms):
  - Clinical Use is defined as "any use in diagnosis or treatment of patients (including as part of a research study)".
  - Users must seek Health Regulatory Authorization "when applicable".
  - Use that could make Google a medical-device "manufacturer" is prohibited, and the Prohibited Use Policy is incorporated.
  - On distribution, which includes hosted APIs, the use restrictions must pass downstream, the agreement must be included, and a Notice file is required.
  - Google may terminate, after which you must delete all copies.
  - The terms contain no Google Cloud or telemetry requirement.
- DINOv3 License (Aug 19, 2025): gated acceptance; no medical-use prohibition; must acknowledge DINOv3 in published research; Meta may change the terms unilaterally [A] — [DINOv3 LICENSE.md](https://github.com/facebookresearch/dinov3/blob/main/LICENSE.md)
- PanDerm: CC-BY-NC-ND 4.0, non-commercial academic research only [A] — [GitHub PanDerm](https://github.com/SiyuanYan1/PanDerm)
- BiomedCLIP: MIT, but "Any deployed use case … is currently out of scope" [A] — [HF BiomedCLIP](https://huggingface.co/microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224)
- ConvNeXt V2 (timm FCMAE weights): cc-by-nc-4.0 [A] — [HF timm convnextv2](https://huggingface.co/timm/convnextv2_tiny.fcmae_ft_in22k_in1k)
- Derm1M dataset: CC BY-NC 4.0, commercial use needs separate permission [A] — [GitHub Derm1M](https://github.com/SiyuanYan1/Derm1M)
- RAD-DINO: MIT, "not meant to be used for clinical practice" [A] — [HF rad-dino](https://huggingface.co/microsoft/rad-dino)
- Derm Foundation: runs locally; Model Garden (cloud) is only suggested for production scale [A] — [HF derm-foundation](https://huggingface.co/google/derm-foundation)

### Inferences
- (inference) None of these terms forbids a research-only, non-diagnostic prototype that runs locally. The project must still observe the following:
  1. **HAI-DEF (MedSigLIP, Derm Foundation):**
     - Keep the system explicitly non-clinical; do not use outputs to diagnose or treat study patients.
     - Keep a copy of the terms with any shared fine-tuned heads or embeddings.
     - Record acceptance of the terms in the project log.
     - If the study is ever framed as a clinical study, regulatory review becomes "applicable".
  2. **PanDerm (CC-BY-NC-ND):**
     - Fine-tuned PanDerm weights should not be redistributed. The "ND" term restricts sharing adapted material; this is my reading of the CC licence, whose legal code I did not open.
     - Keep them internal, and never use them commercially.
  3. **DINOv3:**
     - Cite the paper in any publication.
     - Save the licence version date next to the weights, since Meta may change the terms.
  4. **ConvNeXt V2 timm / DermLIP:** non-commercial only. That is fine for this project but blocks future productisation.
- (inference) The "photos never go to cloud" principle conflicts with none of the candidates. Avoid only the optional Google Cloud Model Garden route and any hosted inference API. Local alternative: download the weights once, then run with `HF_HUB_OFFLINE=1`.
- (inference) The project's "safetensors only" import rule excludes Derm Foundation as-is. Possible local alternatives:
  - Use MedSigLIP (same HAI-DEF family, includes derm data, safetensors, PyTorch).
  - Or extract Derm Foundation embeddings once in an isolated offline TF environment and import only the embeddings (.npy), not the model. That needs an explicit rule exception.

### Gaps
- I did not open the Google Prohibited Use Policy incorporated by HAI-DEF, so its exact text was not verified.
- I did not open the CC BY-NC-ND 4.0 legal code, so the ND interpretation for model weights is my inference.
- The MONET and DermLIP weights licences were not found.

---

## Q4. Which candidates to run NOW (14 patients, ≈120 photos) vs FUTURE (≈1,000 balanced), and which are not worth it

### Takeaway
NOW: run only frozen-feature linear probes (logistic regression, strong L2, class weights) under patient-level CV. Use a handful of small or medium safetensors backbones: DINOv2-S/B (current baseline), DINOv3-S/B, SigLIP 2-B, and MedSigLIP-448 as the derm-aware candidate. Optionally add PanDerm-B (after local `.pth`→safetensors conversion) or MONET. FUTURE: add partial fine-tuning or LoRA of the 1–2 best backbones and an EfficientNetV2-S / ConvNeXt-T full fine-tune. Not worth it: ViT-L/g/7B full fine-tuning, RAD-DINO, SkinGPT-4, PanDerm-L, BiomedCLIP. All of this is (inference) based on the evidence above plus industry practice.

### Cited Findings
- For PanDerm, linear probing ≈ full fine-tuning (PAD 94.50 vs 93.59 accuracy); the probe was sklearn logistic regression [D] — [arXiv 2410.15038v3](https://arxiv.org/html/2410.15038)
- In a frozen-feature benchmark, the MLP adapter was usually best, and the choice of adapter changed results a lot (MedSigLIP MLP 69.8% vs SVM 46.9%) [D] — [arXiv 2601.12382v1](https://arxiv.org/html/2601.12382v1)
- The public PanDerm-L checkpoint performed far below PanDerm-B (40-class W-F1 36.65 vs 64.12; suspected defective checkpoint) [D] — [arXiv 2601.12382v1](https://arxiv.org/html/2601.12382v1)
- BiomedCLIP ranked near the bottom on dermoscopy (40-class W-F1 58.78, below ResNet-50 at 58.82) [D] — [arXiv 2601.12382v1](https://arxiv.org/html/2601.12382v1)
- RAD-DINO was trained only on chest X-rays [A] — [HF rad-dino](https://huggingface.co/microsoft/rad-dino)

### Recommendation table (inference unless marked)

| Candidate | NOW (≈120 imgs / 14 pts) | FUTURE (≈1,000 balanced) | Notes |
|---|---|---|---|
| DINOv2-S/14 (+reg) | **Run** (existing baseline; frozen + LR) | Linear probe baseline; partial unfreeze of the last 2–4 blocks | Apache-2.0, safetensors, <4 GB fine-tune |
| DINOv2-B/14 (+reg) | **Run** (frozen + LR) | Last-blocks fine-tune or LoRA | 86M |
| DINOv3 ViT-S/16, B/16 | **Run** (frozen + LR) | Last-blocks / LoRA | Gated DINOv3 License; cite; record licence date |
| DINOv3 ConvNeXt-T/S | Optional | **Run**: full fine-tune is feasible on 8 GB | Gives a CNN with DINOv3 features for Grad-CAM |
| SigLIP 2 B/16 (or So400m vision tower) | **Run** (frozen + LR) | Last-blocks / LoRA | Apache-2.0 |
| MedSigLIP-448 (vision tower only) | **Run** (frozen + LR; native 448 px) | Frozen + LR/MLP; LoRA only if VRAM allows | HAI-DEF gated; non-clinical use; derm + smartphone data in pretraining |
| PanDerm-B | Optional (frozen + LR after local safetensors conversion) | Frozen / partial | CC-BY-NC-ND; do not redistribute fine-tuned weights. Avoid PanDerm-L |
| MONET (ViT-L/14) | Optional (frozen + LR) | Frozen | Licence unverified; check before use |
| DermLIP-ViT-B/16 | Optional | Frozen | Weights licence unverified |
| Derm Foundation | Not now (TF-only, conflicts with safetensors rule) | Only with an approved offline-TF embedding exception | 448 px, 6144-d |
| EfficientNet-B0 (current), EfficientNetV2-S, ConvNeXt(V1)-T | Keep B0 frozen as the existing baseline | **Run**: full or partial fine-tune with augmentation | torchvision; check weights licence caveat |
| ConvNeXt V2-T/N | Optional | Run if non-commercial is acceptable | cc-by-nc-4.0 |
| BiomedCLIP | Not worth it | Not worth it | Weak derm results; `.bin` only |
| RAD-DINO | Not worth it | Not worth it | Chest X-ray domain |
| ViT-L/g/H+/7B full fine-tune | Not worth it | Not worth it on consumer GPU (frozen features from ViT-L at most) | VRAM; overfitting |
| SkinGPT-4 / MLLMs | Not worth it | Not worth it | Not a classifier backbone |

### Inferences
- (industry practice) For ≈120 images from 14 patients, frozen embeddings + regularised logistic regression is the standard low-variance choice, and fine-tuning beyond a classification head mainly overfits patient identity. Bounding-box crops (≈24 images) can be used as an additional frozen-feature input, with whole-image vs lesion-crop compared at patient level.
- (inference) Pick the backbone only by patient-level CV with CIs. Pre-register a short list of ≤5 backbones before running, so the CV is not overfitted by selection across many backbones and adapters. Report every run, including losers.
- (inference) For ≈1,000 balanced photos, keep the linear probe as the reference. Add (a) last-block unfreezing or LoRA (rank 8–16) on ViT-S/B and (b) a full fine-tune of a ≤30M CNN (EfficientNetV2-S, ConvNeXt-T, DINOv3-ConvNeXt-T), all within an 8 GB budget at batch 16 with AMP. Gains will be limited by the *number of patients*, not photos.
- (inference) Whatever is chosen, pseudo-labels or suggestions from any of these models still need human confirmation before being written to labels, per the project principles. None of the licences changes this.

### Gaps
- No measured VRAM figures came from primary sources. All VRAM numbers are inference and must be measured locally.
- I found no evidence on LoRA vs linear probe for ≤200-image clinical-photo datasets in dermatology.

### Source register (author/org, year, title, venue, URL/DOI, grade; all accessed 2026-10-30)
1. Meta AI / facebookresearch. DINOv2 GitHub README (code & weights Apache-2.0). https://github.com/facebookresearch/dinov2 [A]. Paper: Oquab M. et al. 2023, "DINOv2: Learning Robust Visual Features without Supervision", arXiv:2304.07193 (cited via the HF card; paper not opened) [D].
2. Hugging Face model card facebook/dinov2-small. https://huggingface.co/facebook/dinov2-small [A]
3. Hugging Face model card facebook/dinov3-vitb16-pretrain-lvd1689m. https://huggingface.co/facebook/dinov3-vitb16-pretrain-lvd1689m [A]. Paper: Siméoni O. et al. 2025, "DINOv3", arXiv:2508.10104 (date 13 Aug 2025 per card; paper not opened) [D].
4. Meta. DINOv3 License, last updated 19 Aug 2025. https://github.com/facebookresearch/dinov3/blob/main/LICENSE.md [A]
5. timm DINOv3 mirror listing. https://huggingface.co/timm/vit_small_patch16_dinov3.lvd1689m/tree/main [E, snippet]
6. Google. HF model card google/siglip2-so400m-patch14-384. https://huggingface.co/google/siglip2-so400m-patch14-384 [A]. Tschannen M. et al. 2025, "SigLIP 2: Multilingual Vision-Language Encoders…", arXiv:2502.14786 [D, not opened].
7. mlfoundations. open_clip README. https://github.com/mlfoundations/open_clip [A]
8. PyTorch. torchvision "Models and pre-trained weights". https://docs.pytorch.org/vision/stable/models.html [A]
9. timm. HF card timm/convnextv2_tiny.fcmae_ft_in22k_in1k. https://huggingface.co/timm/convnextv2_tiny.fcmae_ft_in22k_in1k [A]
10. Microsoft. HF card BiomedCLIP-PubMedBERT_256-vit_base_patch16_224. https://huggingface.co/microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224 [A]. Zhang S. et al., "A Multimodal Biomedical Foundation Model Trained from Fifteen Million Image–Text Pairs", NEJM AI 2(1), doi:10.1056/AIoa2400640 [B, not opened].
11. Google Health AI. HF card google/derm-foundation (v1.0.0, created 2023-12-19). https://huggingface.co/google/derm-foundation [A]
12. Google Health AI. HF card google/medsiglip-448 (v1.0.0, created 2025-07-09). https://huggingface.co/google/medsiglip-448 [A]
13. Google. Health AI Developer Foundations Terms of Use, last modified 15 Nov 2024. https://developers.google.com/health-ai-developer-foundations/terms [A]
14. Kiraly A.P. et al. 2024, "Health AI Developer Foundations", arXiv:2411.15128v2 (26 Nov 2024). https://arxiv.org/abs/2411.15128 [D]
15. Yan S., Yu Z., Primiero C., Vico-Alonso C., Wang Z., … Ge Z. 2025, "A multimodal vision foundation model for clinical dermatology", Nature Medicine. https://www.nature.com/articles/s41591-025-03747-y (paywall; read via arXiv:2410.15038v3, 13 Apr 2025, https://arxiv.org/html/2410.15038) [B/D]
16. SiyuanYan1/PanDerm GitHub (licence CC-BY-NC-ND 4.0). https://github.com/SiyuanYan1/PanDerm [A]
17. PanDerm Supplementary Information (institutional mirror). https://cris.unibo.it/retrieve/handle/11585/1037927/a6367364-c674-4397-806e-2f7e058acf95/41591_2025_3747_MOESM1_ESM.pdf [B, search snippet only]
18. Kim C., Gadgil S.U., DeGrave A.J., Omiye J.A., Cai Z.R., Daneshjou R., Lee S.-I. 2024, "Transparent medical image AI via an image–text foundation model grounded in medical literature", Nature Medicine, doi:10.1038/s41591-024-02887-x. Card: https://huggingface.co/suinleelab/monet [A card; B paper not opened]
19. Yan S. et al. 2025, "Derm1M: A Million-scale Vision-Language Dataset Aligned with Clinical Ontology Knowledge for Dermatology", ICCV 2025, pp. 12681–12690. https://openaccess.thecvf.com/content/ICCV2025/html/Yan_Derm1M_A_Million-scale_Vision-Language_Dataset_Aligned_with_Clinical_Ontology_Knowledge_ICCV_2025_paper.html [B]; GitHub https://github.com/SiyuanYan1/Derm1M [A]
20. Yuceyalcin F., Yilmaz A., Temelkuran B. 2026, "A Hierarchical Benchmark of Foundation Models for Dermatology", arXiv:2601.12382v1 (18 Jan 2026). https://arxiv.org/html/2601.12382v1 [D]
21. Microsoft. HF card microsoft/rad-dino. https://huggingface.co/microsoft/rad-dino [A]. Pérez-García F. et al. 2025, "Exploring scalable medical image encoders beyond text supervision", Nature Machine Intelligence, doi:10.1038/s42256-024-00965-w [B, not opened].
22. SkinGPT-4 (authors not verified this session), Nature Communications, Jul 2024 (DOAJ record https://doaj.org/article/4cc0771c7c504516849eb9d83dc15cf9 [C]); arXiv:2304.10691 https://arxiv.org/abs/2304.10691v2 [D]. Search snippets only.
23. Xu J., Cheng D., Zhao X. et al. 2025, "DermINO: Hybrid Pretraining for a Versatile Dermatology Foundation Model", arXiv:2508.12190v2. https://arxiv.org/abs/2508.12190 [D]
