"""Photo flags for data review: suspected duplicates (A3) and image quality (A6).

Both are suggestions only.  A duplicate pair stays "待確認" until a person decides
「不是重複」 or 「是重複」 (then the chosen copy is excluded through a normal review).
A quality flag stays until a person sets the photo's quality or marks it acceptable.

Pixel fingerprints reuse the import cache (runtime/imports/pixel_cache.json); quality
metrics use the same measurements and default thresholds as model inference.  Everything
is cached by content hash and computed in a background thread, so list pages never wait.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

from src.common import read_json, read_manifest, write_json

NEAR = 4  # dHash bits; same rule as the external import's near-duplicate candidates
DECISIONS = 'data/duplicate_decisions.json'
QUALITY_ACK = 'data/quality_reviews.json'
QUALITY_CACHE = 'runtime/workbench/quality_cache.json'
_state: dict = {}
_lock = threading.Lock()


def pair_key(a: str, b: str) -> str:
    return '|'.join(sorted((a, b)))


def measure(path: Path) -> dict:
    """Blur / dark / bright measurements identical to ModelPredictor.predict."""
    import cv2
    import numpy as np
    from PIL import Image, ImageOps
    from src.workbench.contracts import InferenceConfig

    cfg = InferenceConfig()
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im).convert('RGB')
        gray = np.asarray(ImageOps.grayscale(ImageOps.contain(im, (512, 512))))
    blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    dark = float((gray < 15).mean())
    bright = float((gray > 240).mean())
    reasons = []
    if blur < cfg.blur_threshold:
        reasons.append(f'可能失焦（清晰度 {blur:.1f}，低於 {cfg.blur_threshold:g}）')
    if dark > cfg.dark_fraction:
        reasons.append(f'大部分畫面過暗（{dark * 100:.0f}% 像素過暗）')
    if bright > cfg.bright_fraction:
        reasons.append(f'大部分畫面過亮（{bright * 100:.0f}% 像素過亮）')
    return {
        'blur_variance': round(blur, 2),
        'dark_fraction': round(dark, 4),
        'bright_fraction': round(bright, 4),
        'reasons': reasons,
    }


def _signature(root: Path, rows: list[dict]) -> str:
    from src.workbench.storage import digest
    from src.workbench.queries.data_index import stat_key

    return digest(
        [
            [
                r['image_id'],
                r['sha256'],
                r.get('status'),
                r.get('cls_review'),
                r.get('quality_state'),
            ]
            for r in rows
        ]
        + [stat_key(root / DECISIONS), stat_key(root / QUALITY_ACK)]
    )


def _compute(root: Path, key: str, signature: str) -> None:
    try:
        from src.common import inside
        from src.data.tasks import area_state
        from src.imports.external import project_fingerprints, _distance

        rows = read_manifest(root)
        prints = project_fingerprints(root, rows)
        cache_path = root / QUALITY_CACHE
        cache = read_json(cache_path) if cache_path.exists() else {}
        changed = False
        for row in rows:
            if row['sha256'] not in cache:
                try:
                    cache[row['sha256']] = measure(inside(row['image_path'], root))
                except Exception as exc:
                    cache[row['sha256']] = {'error': str(exc)[:200], 'reasons': []}
                changed = True
        if changed:
            write_json(cache_path, cache)
        decisions = read_json(root / DECISIONS).get('pairs', {}) if (root / DECISIONS).exists() else {}
        acks = read_json(root / QUALITY_ACK).get('images', {}) if (root / QUALITY_ACK).exists() else {}
        active = [r for r in rows if r.get('status') != 'excluded']
        pairs = []
        for i, a in enumerate(active):
            pa = prints.get(a['sha256']) or {}
            if not pa.get('dhash'):
                continue
            for b in active[i + 1 :]:
                pb = prints.get(b['sha256']) or {}
                if not pb.get('dhash'):
                    continue
                same = a['sha256'] == b['sha256'] or pa.get('pixel_sha256') == pb.get('pixel_sha256')
                distance = 0 if same else _distance(pa['dhash'], pb['dhash'])
                if same or distance <= NEAR:
                    k = pair_key(a['image_id'], b['image_id'])
                    pairs.append(
                        {
                            'key': k,
                            'a': min(a['image_id'], b['image_id']),
                            'b': max(a['image_id'], b['image_id']),
                            'kind': 'pixel' if same else 'near',
                            'distance': distance,
                            'decision': (decisions.get(k) or {}).get('decision'),
                        }
                    )
        # Doctors already approved these photos: no reminder unless one side is still open.
        status = {r['image_id']: r.get('status') for r in rows}
        open_pairs = [
            p for p in pairs if not p['decision'] and not (status.get(p['a']) == status.get(p['b']) == 'approved')
        ]
        duplicate_ids = sorted({x for p in open_pairs for x in (p['a'], p['b'])})
        quality = {}
        for r in rows:
            q = cache.get(r['sha256']) or {}
            if not q.get('reasons'):
                continue
            ack = acks.get(r['image_id'])
            settled = bool((r.get('quality_state') or '').strip()) or (ack and ack.get('sha256') == r['sha256'])
            quality[r['image_id']] = {**q, 'pending': not settled and area_state(r, 'cls') == 'pending'}
        result = {
            'state': 'ready',
            'signature': signature,
            'computed_at': time.time(),
            'pairs': pairs,
            'duplicate_ids': duplicate_ids,
            'quality': quality,
            'quality_ids': sorted(k for k, v in quality.items() if v['pending']),
        }
    except Exception as exc:
        result = {
            'state': 'failed',
            'error': str(exc),
            'signature': signature,
            'computed_at': time.time(),
            'pairs': [],
            'duplicate_ids': [],
            'quality': {},
            'quality_ids': [],
        }
    with _lock:
        _state[key] = result


def current(root: Path, wait: float = 0) -> dict:
    """Latest computed flags; starts a background refresh when the data changed."""
    root = Path(root)
    key = str(root.resolve())
    rows = read_manifest(root)
    signature = _signature(root, rows)
    thread = None
    with _lock:
        value = _state.get(key)
        if not value or (value.get('signature') != signature and value.get('state') != 'computing'):
            _state[key] = {
                **(value or {'pairs': [], 'duplicate_ids': [], 'quality': {}, 'quality_ids': []}),
                'state': 'computing',
                'signature': signature,
            }
            thread = threading.Thread(target=_compute, args=(root, key, signature), daemon=True, name='photo-flags')
            thread.start()
        value = _state[key]
    if wait and value.get('state') == 'computing':
        deadline = time.monotonic() + wait
        while time.monotonic() < deadline:
            time.sleep(0.05)
            with _lock:
                value = _state[key]
            if value.get('state') != 'computing':
                break
    return dict(value)


def summary(root: Path) -> dict:
    value = current(root)
    return {
        'state': value.get('state'),
        'duplicate_pending': len(value.get('duplicate_ids', [])),
        'quality_pending': len(value.get('quality_ids', [])),
        'duplicate_pairs': sum(1 for p in value.get('pairs', []) if not p['decision']),
    }


def ids(root: Path, flag: str) -> list[str]:
    value = current(root)
    return value.get('duplicate_ids' if flag == 'duplicate' else 'quality_ids', [])


def for_image(root: Path, image_id: str) -> dict:
    value = current(root, wait=10)
    pairs = [p for p in value.get('pairs', []) if image_id in (p['a'], p['b'])]
    return {
        'state': value.get('state'),
        'quality': value.get('quality', {}).get(image_id),
        'duplicates': [{**p, 'other': p['b'] if p['a'] == image_id else p['a']} for p in pairs],
    }


def decide_pair(root: Path, a: str, b: str, decision: str, *, keep: str | None, reviewer: str) -> dict:
    """Record a person's decision on a suspected duplicate pair.  「是重複」 excludes the
    copy that is not kept, in both work areas, through the normal review path."""
    from src.workbench.storage import dataset_lock, file_lock

    if decision not in ('not_duplicate', 'duplicate') or a == b:
        raise ValueError('無效的重複判定')
    if not reviewer.strip():
        raise ValueError('請先填寫操作者名稱')
    key = pair_key(a, b)
    known = {p['key'] for p in current(root, wait=10).get('pairs', [])}
    if key not in known:
        raise ValueError('這兩張照片目前不是疑似重複配對，請重新整理')
    rows = {r['image_id']: r for r in read_manifest(root)}
    if a not in rows or b not in rows:
        raise ValueError('照片不存在')
    excluded = None
    if decision == 'duplicate':
        if keep not in (a, b):
            raise ValueError('請選擇要保留的照片')
        excluded = b if keep == a else a
        from src.data.dataset import review
        from src.data.tasks import row_revision

        reason = f'重複照片：與 {keep} 為同一張，保留 {keep}'
        row = rows[excluded]
        review(
            excluded,
            revision=row_revision(row),
            root=root,
            decision='exclude',
            label=row.get('label_state') or 'unknown',
            stage=row.get('stage_label') or 'unknown',
            reviewer=reviewer,
            reason=reason,
        )
    with file_lock(root / 'runtime/duplicate-decisions.lock'):
        path = root / DECISIONS
        data = read_json(path) if path.exists() else {'schema_version': 1, 'pairs': {}}
        data['pairs'][key] = {
            'decision': decision,
            'keep': keep,
            'excluded': excluded,
            'by': reviewer,
            'at': time.time(),
        }
        write_json(path, data)
    _after_change(root)
    return {'key': key, 'decision': decision, 'excluded': excluded}


def acknowledge_quality(root: Path, image_id: str, reviewer: str) -> dict:
    from src.workbench.storage import file_lock

    if not reviewer.strip():
        raise ValueError('請先填寫操作者名稱')
    row = next((r for r in read_manifest(root) if r['image_id'] == image_id), None)
    if row is None:
        raise ValueError('照片不存在')
    with file_lock(root / 'runtime/quality-reviews.lock'):
        path = root / QUALITY_ACK
        data = read_json(path) if path.exists() else {'schema_version': 1, 'images': {}}
        data['images'][image_id] = {
            'decision': 'acceptable',
            'sha256': row['sha256'],
            'by': reviewer,
            'at': time.time(),
        }
        write_json(path, data)
    _after_change(root)
    return {'image_id': image_id, 'acknowledged': True}


def _after_change(root: Path) -> None:
    from src.workbench.queries import data_index

    data_index.rebuild(root)
    try:
        from src.workbench.queries.images import clear

        clear(root)
    except Exception:
        pass
