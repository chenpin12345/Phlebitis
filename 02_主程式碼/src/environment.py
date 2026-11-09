"""Versions and GPU state reported by `python -m src doctor`."""

from __future__ import annotations

import importlib.metadata
import sys


def environment() -> dict:
    import torch

    info = {
        "python": sys.version,
        "torch": torch.__version__,
        "cuda_runtime": torch.version.cuda,
        "cuda_available": torch.cuda.is_available(),
    }
    if info["cuda_available"]:
        info.update(gpu=torch.cuda.get_device_name(0), vram_bytes=torch.cuda.get_device_properties(0).total_memory)
        x = torch.ones((128, 128), device="cuda")
        info["gpu_compute_ok"] = bool((x @ x).mean().item() == 128)
        del x
    for name in ["torchvision", "fastapi", "httpx", "Pillow", "numpy"]:
        try:
            info[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            info[name] = None
    return info
