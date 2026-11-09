"""Models trained outside this workbench: checked and rebuilt from plain tensors, never unpickled.

A model trained elsewhere (another computer, Colab) arrives as a package in
05_匯入區/models/<名稱>/ whose package.json says "source": {"type": "external"}.  Only
.safetensors, .json and .npz files are accepted.  A .pt/.pth file is a Python pickle and can run
arbitrary code when it is opened, so the workbench never opens one it did not write itself;
scripts/model_package.py converts a trainer's own weights on the trainer's computer.

On import the workbench rebuilds the model from the official architecture shipped with the
installed libraries, loads the tensors with strict=True and writes the artifact in the same
format as its own training output.  The version is registered as unevaluated, marked
extra.source = "external", and registry.activate refuses it until it has a complete evaluation
on this project's data (the development-only shortcut does not apply).  An external model may
have been trained on photos that are also in this project's evaluation set, so its scores can
look better than they are; the evaluation pages say so.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from src.common import read_json

ALLOWED_SUFFIXES = ('.safetensors', '.json', '.npz')
REQUIRED = {
    'efficientnet_b0': {'model.safetensors'},
    'dinov2_small': {'config.json', 'model.safetensors', 'classifier.npz'},
}
DINO_HIDDEN = 384  # facebook/dinov2-small
NOTE = '外部訓練的模型可能看過本專案的評估照片，評估分數可能偏高；啟用前請確認訓練資料來源。'


def is_external(metadata: dict) -> bool:
    return (metadata.get('extra') or {}).get('source') == 'external'


def check(package: dict, files: dict) -> dict:
    """Validate the declaration of an external package (file contents are only hashed here)."""
    from src.data.tasks import SCHEMES
    from src.workbench.contracts import MODELS, InferenceConfig

    if package.get('purpose') != 'inference':
        raise ValueError('外部模型只能以推論用途（inference）匯入')
    model = package.get('model')
    if model not in REQUIRED:
        raise ValueError('不支援的模型種類：' + str(model))
    bad = sorted(name for name in files if Path(name).suffix.lower() not in ALLOWED_SUFFIXES)
    if bad:
        raise ValueError('外部模型只接受 .safetensors、.json、.npz；不接受：' + '、'.join(bad))
    missing = sorted(REQUIRED[model] - set(files))
    if missing:
        raise ValueError('外部模型包缺少檔案：' + '、'.join(missing))
    training = package.get('source', {}).get('training_data')
    if not isinstance(training, str) or not training.strip() or len(training) > 2000:
        raise ValueError('外部模型必須在 source.training_data 說明訓練資料來源（2000 字以內）')
    config = InferenceConfig(**package.get('config', {}))
    task = SCHEMES[config.scheme]['task']
    return {'type': 'external', 'task': task, 'config': config.model_dump(), 'training_data': training.strip()}


def _tensors(path: Path) -> dict:
    from safetensors.torch import load_file

    return load_file(str(path))


def convert(model: str, stage: Path, out: Path, config: dict) -> None:
    """Rebuild the model from `stage` (verified package files) into an artifact folder `out`."""
    out.mkdir(parents=True)
    if model == 'efficientnet_b0':
        _efficientnet(stage, out, config)
    else:
        _dino(stage, out, config)


def _classes(config: dict) -> int:
    from src.data.tasks import SCHEMES
    from src.workbench.contracts import InferenceConfig

    return len(SCHEMES[InferenceConfig(**config).scheme]['classes'])


def _efficientnet(stage: Path, out: Path, config: dict) -> None:
    import torch
    from src.workbench.adapters import load_efficient

    classes = _classes(config)
    net = load_efficient(classes=classes)
    try:
        net.load_state_dict(_tensors(stage / 'model.safetensors'), strict=True)
    except RuntimeError as exc:
        raise ValueError(f'權重與 EfficientNet-B0（{classes} 類）架構不符：{str(exc)[:300]}') from exc
    torch.save(net.state_dict(), out / 'model.pt')
    check = load_efficient(classes=classes)
    check.load_state_dict(torch.load(out / 'model.pt', map_location='cpu', weights_only=True))


def _dino(stage: Path, out: Path, config: dict) -> None:
    import numpy as np
    from transformers import Dinov2Model

    settings = read_json(stage / 'config.json')
    expected = {'model_type': 'dinov2', 'hidden_size': DINO_HIDDEN, 'num_hidden_layers': 12, 'patch_size': 14}
    if any(settings.get(k) != v for k, v in expected.items()):
        raise ValueError('config.json 必須是 DINOv2 ViT-S/14（model_type=dinov2、hidden_size=384、12 層、patch 14）')
    if settings.get('auto_map'):
        raise ValueError('config.json 不能指定自訂程式碼（auto_map）')
    for name in ('config.json', 'model.safetensors', 'classifier.npz'):
        shutil.copy2(stage / name, out / name)
    _, info = Dinov2Model.from_pretrained(out, local_files_only=True, use_safetensors=True, output_loading_info=True)
    if any(info.get(k) for k in ('missing_keys', 'unexpected_keys', 'mismatched_keys')):
        raise ValueError('DINOv2 權重與架構不符')
    classes = _classes(config)
    rows = 1 if classes == 2 else classes
    with np.load(out / 'classifier.npz', allow_pickle=False) as c:
        if set(c.files) != {'coef', 'intercept', 'classes', 'mean', 'scale'}:
            raise ValueError('classifier.npz 必須只有 coef、intercept、classes、mean、scale')
        if (
            c['classes'].tolist() != list(range(classes))
            or c['coef'].shape != (rows, DINO_HIDDEN)
            or c['intercept'].shape != (rows,)
            or c['mean'].shape != (DINO_HIDDEN,)
            or c['scale'].shape != (DINO_HIDDEN,)
        ):
            raise ValueError(f'classifier.npz 的形狀與 {classes} 類標籤方案不符')
