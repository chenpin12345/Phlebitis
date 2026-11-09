"""Spot checks of photos classified automatically from 岡山高醫 filenames (A5).

Each time new rule-classified photos appear, a share of them (設定與維護 → 抽查比例,
default 5 %, at least one) is drawn at random and shown one by one.  「正確」 records the
check; 「有誤」 records it and moves the photo's classification back to 待處理 through a
normal review, so a person re-classifies it.  Nothing is changed without that click.
"""

from __future__ import annotations

import json
import math
import random
import time
from pathlib import Path

from src.common import read_json, read_manifest, write_json

PATH = 'data/spot_checks.json'
RULE_SOURCE = 'authorized_filename_rule'


def _load(root: Path) -> dict:
    path = root / PATH
    return read_json(path) if path.exists() else {'schema_version': 1, 'samples': [], 'considered': []}


def auto_classified(root: Path) -> dict[str, dict]:
    """Photos whose current classification came from the authorized filename rule."""
    from src.data.tasks import area_state

    latest: dict[str, dict] = {}
    for path in sorted((root / 'data/reviews').glob('*.json')):
        try:
            record = json.loads(path.read_text(encoding='utf-8-sig'))
        except (OSError, ValueError):
            continue
        if record.get('area') != 'cls' and record.get('task') not in ('classification',):
            continue
        ident = (record.get('after') or {}).get('image_id') or path.stem.split('_', 1)[-1]
        latest[ident] = record
    rows = {r['image_id']: r for r in read_manifest(root)}
    return {
        ident: rows[ident]
        for ident, record in latest.items()
        if record.get('source') == RULE_SOURCE and ident in rows and area_state(rows[ident], 'cls') == 'confirmed'
    }


def status(root: Path) -> dict:
    data = _load(root)
    auto = auto_classified(root)
    pending = [s for s in data['samples'] if s['state'] == 'pending' and s['image_id'] in auto]
    considered = set(data['considered'])
    checked = [s for s in data['samples'] if s['state'] in ('correct', 'wrong')]
    return {
        'pending': len(pending),
        'unsampled': len([i for i in auto if i not in considered]),
        'auto_total': len(auto),
        'checked': len(checked),
        'wrong': sum(s['state'] == 'wrong' for s in checked),
    }


def view(root: Path) -> dict:
    data = _load(root)
    auto = auto_classified(root)
    from src.data import sources

    names = sources.load(root)['images']
    items = []
    for s in data['samples']:
        if s['state'] != 'pending' or s['image_id'] not in auto:
            continue
        row = auto[s['image_id']]
        from src.data.tasks import row_revision

        alias = next(iter((names.get(s['image_id']) or {}).get('aliases', [])), None)
        items.append(
            {
                'image_id': s['image_id'],
                'batch': s['batch'],
                'stage': row.get('stage_label') or 'unknown',
                'label': row.get('label_state'),
                'display_name': alias['filename'] if alias else None,
                'revision': row_revision(row),
            }
        )
    history = sorted(
        (s for s in data['samples'] if s['state'] != 'pending'), key=lambda s: s.get('at') or 0, reverse=True
    )[:20]
    return {**status(root), 'items': items, 'history': history}


def start(root: Path, ratio: float) -> dict:
    from src.workbench.storage import file_lock

    with file_lock(root / 'runtime/spot-checks.lock'):
        data = _load(root)
        auto = auto_classified(root)
        if any(s['state'] == 'pending' and s['image_id'] in auto for s in data['samples']):
            return view(root)
        considered = set(data['considered'])
        new = sorted(i for i in auto if i not in considered)
        if not new:
            return view(root)
        k = min(len(new), max(1, math.ceil(len(new) * ratio)))
        batch = time.strftime('%Y%m%dT%H%M%S')
        chosen = random.Random(batch + ''.join(new)).sample(new, k)
        data['considered'] = sorted(considered | set(new))
        data['samples'] += [
            {
                'image_id': i,
                'batch': batch,
                'state': 'pending',
                'created': time.time(),
                'batch_size': len(new),
                'stage': auto[i].get('stage_label'),
            }
            for i in chosen
        ]
        write_json(root / PATH, data)
    return view(root)


def answer(root: Path, image_id: str, *, correct: bool, reviewer: str, revision: str | None = None) -> dict:
    from src.workbench.storage import file_lock

    if not reviewer.strip():
        raise ValueError('請先填寫操作者名稱')
    with file_lock(root / 'runtime/spot-checks.lock'):
        data = _load(root)
        sample = next((s for s in data['samples'] if s['image_id'] == image_id and s['state'] == 'pending'), None)
        if not sample:
            raise ValueError('這張照片不在待抽查清單中')
        auto = auto_classified(root)
        if image_id not in auto:
            sample.update(state='superseded', at=time.time(), note='抽查前已被人工修改')
            write_json(root / PATH, data)
            raise ValueError('這張照片的分類已被人工修改，已從抽查清單移除')
        row = auto[image_id]
        if not correct:
            from src.data.dataset import review
            from src.data.tasks import row_revision

            review(
                image_id,
                revision=revision or row_revision(row),
                root=root,
                decision='needs_changes',
                label=row.get('label_state') or 'unknown',
                stage=row.get('stage_label') or 'unknown',
                reviewer=reviewer,
                reason='抽查：依檔名自動分類有誤，退回待處理重新分類',
            )
        sample.update(state='correct' if correct else 'wrong', by=reviewer, at=time.time())
        write_json(root / PATH, data)
    if not correct:
        from src.workbench.queries import data_index

        data_index.rebuild(root)
        try:
            from src.workbench.queries.images import clear

            clear(root)
        except Exception:
            pass
    return view(root)
