from __future__ import annotations

import csv
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from src.telemetry import timed

ROOT = Path(__file__).resolve().parents[1]


def inside(path: str | Path, root: Path = ROOT) -> Path:
    root = root.resolve()
    p = Path(path)
    p = (root / p).resolve() if not p.is_absolute() else p.resolve()
    if not p.is_relative_to(root):
        raise ValueError(f"Path must stay inside project: {p}")
    return p


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


@timed('hash')
def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


@timed('file_read')
def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def read_manifest(root: Path = ROOT) -> list[dict]:
    with (root / "data/manifest.csv").open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_manifest(rows: list[dict], root: Path = ROOT) -> None:
    path = root / "data/manifest.csv"
    if not rows:
        with path.open(encoding='utf-8-sig',newline='') as existing:
            fields=next(csv.reader(existing))
    else:fields=list(rows[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def rows_digest(rows: list[dict]) -> str:
    return hashlib.sha256(json.dumps(rows, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
