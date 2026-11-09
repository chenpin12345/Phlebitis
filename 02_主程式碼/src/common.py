from __future__ import annotations

import csv
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from src.telemetry import timed
from src.paths import BACKUP_ROOT, CODE_ROOT, DOCS_ROOT, INBOX_ROOT, STORE_ROOT

# Data root: data/, models/, runs/, runtime/, archive/. Stored relative paths
# ('data/...', 'runs/...') are relative to this folder.
ROOT = STORE_ROOT
_STORE = STORE_ROOT  # unpatched copy; tests replace ROOT with temporary folders


def _is_real(root: Path | None) -> tuple[Path, bool]:
    root = ROOT if root is None else Path(root)
    return root, root.resolve() == _STORE.resolve()


def code_path(relative: str, root: Path | None = None) -> Path:
    """Code-side files (configs/, web/dist). The real data root maps to the code folder;
    any other root (isolated tests) keeps its own copy under root/."""
    root, real = _is_real(root)
    return (CODE_ROOT if real else root) / relative


SNAPSHOT_DIR = 'data/snapshots'
# Snapshots built before 2026-11 stay in place: job and report records point at these paths.
OLD_SNAPSHOT_DIR = 'data/yolo'


def snapshot_folders(root: Path | None = None) -> list[Path]:
    root = ROOT if root is None else Path(root)
    return [root / SNAPSHOT_DIR, root / OLD_SNAPSHOT_DIR]


def snapshot_versions(root: Path | None = None) -> list[Path]:
    """Every snapshot's dataset_version.json, new and old location."""
    return sorted(p for base in snapshot_folders(root) for p in base.glob('*/dataset_version.json'))


def snapshot_folder(version: str, root: Path | None = None) -> Path:
    """Folder of one snapshot: where it already is, otherwise the location for new ones."""
    folders = snapshot_folders(root)
    return next((base / version for base in folders if (base / version).is_dir()), folders[0] / version)


def config_path(name: str, root: Path | None = None) -> Path:
    return code_path('configs/' + name, root)


def backup_root(root: Path | None = None) -> Path:
    """04_備份 for the real data root; an isolated root (tests) keeps root/backups."""
    root, real = _is_real(root)
    return BACKUP_ROOT if real else root / 'backups'


def inbox_root(root: Path | None = None) -> Path:
    """05_匯入區 for the real data root; an isolated root (tests) keeps root/inbox."""
    root, real = _is_real(root)
    return INBOX_ROOT if real else root / 'inbox'


def pre_change_dir(kind: str, root: Path | None = None) -> Path:
    """Where copies taken just before a data change are kept: kind is 'manifest' or '資料庫'."""
    return backup_root(root) / '修改前副本' / kind


def record_path(path: Path, root: Path | None = None) -> str:
    """A path for JSON records: relative to the data root when inside it, otherwise relative to
    the workspace (04_備份/..., 05_匯入區/...), otherwise absolute."""
    from src.paths import WORKSPACE_ROOT

    root, _ = _is_real(root)
    path = Path(path).resolve()
    for base in (root.resolve(), WORKSPACE_ROOT):
        if path.is_relative_to(base):
            return path.relative_to(base).as_posix()
    return str(path)


def database_backup(home: Path, name: str) -> Path:
    """Pre-migration copy of a workbench database in `home` (runtime/workbench).
    The real database keeps its copies in 04_備份; an isolated home keeps them next to itself."""
    real = Path(home).resolve() == (_STORE / 'runtime/workbench').resolve()
    return (pre_change_dir('資料庫', _STORE) if real else Path(home) / 'backups') / name


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


def replace_path(source, target) -> None:
    """os.replace; on Windows it fails briefly while another thread still has the target open."""
    import time

    for attempt in range(6):
        try:
            os.replace(source, target)
            return
        except PermissionError:
            if attempt == 5:
                raise
            time.sleep(0.05 * (attempt + 1))


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)
        replace_path(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def read_manifest(root: Path = ROOT) -> list[dict]:
    with (root / "data/manifest.csv").open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_manifest(rows: list[dict], root: Path = ROOT) -> None:
    path = root / "data/manifest.csv"
    if not rows:
        with path.open(encoding='utf-8-sig', newline='') as existing:
            fields = next(csv.reader(existing))
    else:
        # Ordered union: rows gaining newer optional columns never break older rows.
        fields = list(rows[0])
        for row in rows[1:]:
            fields += [k for k in row if k not in fields]
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        replace_path(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def rows_digest(rows: list[dict]) -> str:
    return hashlib.sha256(json.dumps(rows, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
