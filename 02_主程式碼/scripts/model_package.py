"""Prepare a model package for 05_匯入區/models/<名稱>/.

export    On the computer where the model was trained, turn YOUR OWN weights into plain tensors
          (model.safetensors) and write package.json.  Run it with this project's code:

            .venv\\Scripts\\python.exe scripts\\model_package.py export --model efficientnet_b0 ^
                --weights D:\\訓練\\model.pt --out D:\\匯出\\efficientnet_外部A ^
                --training-data "岡山高醫 2026-09 照片 80 張，依個案分組，未含本專案驗證集"

          Then copy the --out folder into 05_匯入區\\models\\ and import it from the workbench.
manifest  Recompute the SHA-256 list in an existing package folder after its files changed.

Opening a .pt file runs code stored inside it, so only export weights you trained yourself.
The workbench itself never opens a .pt from outside; it rebuilds the model from the tensors.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ALLOWED = ('.safetensors', '.json', '.npz')
MODELS = ('efficientnet_b0', 'dinov2_small')


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def files_of(folder: Path) -> dict[str, str]:
    return {
        p.relative_to(folder).as_posix(): sha256(p)
        for p in sorted(folder.rglob('*'))
        if p.is_file() and p.name != 'package.json' and p.suffix.lower() in ALLOWED
    }


def write_package(folder: Path, package: dict) -> dict:
    package['files'] = files_of(folder)
    (folder / 'package.json').write_text(json.dumps(package, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return package


def _plain(state: dict) -> dict:
    """Independent float32 tensors (safetensors refuses shared storage)."""
    import torch

    tensors = {}
    for key, value in state.items():
        if not isinstance(value, torch.Tensor):
            raise SystemExit(f'權重中有非張量內容：{key}')
        tensors[key] = value.detach().clone().float().contiguous() if value.is_floating_point() else value.clone()
    return tensors


def export(args) -> dict:
    from safetensors.torch import save_file
    from src.workbench.contracts import InferenceConfig

    out = Path(args.out)
    if out.exists() and any(out.iterdir()):
        raise SystemExit('--out 必須是空資料夾或尚不存在的資料夾')
    out.mkdir(parents=True, exist_ok=True)
    config = {'threshold': args.threshold, 'imgsz': args.imgsz}
    if args.label_scheme:
        config['label_scheme'] = args.label_scheme
    config = InferenceConfig(**config).model_dump()
    weights = Path(args.weights)
    if args.model == 'efficientnet_b0':
        import torch

        state = torch.load(weights, map_location='cpu', weights_only=True)
        if isinstance(state, dict) and 'state_dict' in state:
            state = state['state_dict']
        save_file(_plain(state), str(out / 'model.safetensors'))
    else:
        if not weights.is_dir():
            raise SystemExit('DINOv2 請以 --weights 指定含 config.json、model.safetensors、classifier.npz 的資料夾')
        for name in ('config.json', 'model.safetensors', 'classifier.npz'):
            shutil.copy2(weights / name, out / name)
    package = {
        'schema_version': 1,
        'purpose': 'inference',
        'model': args.model,
        'source': {'type': 'external', 'training_data': args.training_data},
        'config': config,
    }
    return write_package(out, package)


def manifest(args) -> dict:
    folder = Path(args.folder)
    path = folder / 'package.json'
    if not path.is_file():
        raise SystemExit('資料夾內沒有 package.json；請先從 05_匯入區/範本/package.json 複製一份')
    return write_package(folder, json.loads(path.read_text(encoding='utf-8-sig')))


def main(argv=None):
    parser = argparse.ArgumentParser(description='準備 05_匯入區/models 的模型包')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('export', help='把自己訓練的權重轉成可安全匯入的模型包')
    p.add_argument('--model', required=True, choices=MODELS)
    p.add_argument('--weights', required=True, help='EfficientNet：state_dict .pt；DINOv2：資料夾')
    p.add_argument('--out', required=True, help='輸出資料夾（空資料夾或尚不存在）')
    p.add_argument('--training-data', required=True, help='訓練資料來源說明，例如「岡山高醫 2026-09 照片 80 張」')
    p.add_argument('--threshold', type=float, default=0.5)
    p.add_argument('--imgsz', type=int, default=224)
    p.add_argument('--label-scheme', choices=('binary_v1', 'stage_v1'), help='分類模型：二分類或分期')
    p = sub.add_parser('manifest', help='重新計算模型包的 SHA-256 清單')
    p.add_argument('folder')
    args = parser.parse_args(argv)
    package = export(args) if args.command == 'export' else manifest(args)
    print(json.dumps({'model': package['model'], 'files': package['files']}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
