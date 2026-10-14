"""One-time, repeatable migration to explicit per-area review states.

Rows written before the two-area split derive both area states from ``status``.
This writes those states explicitly (cls_review / det_review) and records each
legacy approved row's localisation state from its YOLO file content, so the YOLO
area never again depends on the binary label.  Images, boxes and snapshots are
not modified.  The manifest is backed up first; already-explicit values are kept.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from src.common import ROOT, inside, read_manifest, stamp, write_json, write_manifest
from src.data import tasks


def migrate_areas(root: Path = ROOT) -> dict:
    from src.workbench.storage import dataset_lock
    from src.data.dataset import recover_reviews, _yolo_boxes
    with dataset_lock(root):
        recover_reviews(root)
        rows = read_manifest(root)
        changed = []
        for row in rows:
            before = {k: row.get(k, '') for k in ('cls_review', 'det_review', 'detection_state')}
            for area in tasks.AREAS:
                column = tasks.AREA_COLUMN[area]
                if not row.get(column):
                    row[column] = tasks.area_state(row, area)
            if not row.get('detection_state') and row['det_review'] == 'confirmed' and row.get('yolo_path'):
                label = inside(row['yolo_path'], root)
                if label.is_file():
                    row['detection_state'] = 'boxes' if _yolo_boxes(label) else 'no_target'
            after = {k: row.get(k, '') for k in before}
            if after != before:
                changed.append({'image_id': row['image_id'], 'before': before, 'after': after})
        if not changed:
            return {'changed': 0, 'note': '已是明確的兩區狀態，無需遷移'}
        backup = root / 'runtime/backups' / f'manifest-before-areas-{stamp()}.csv'
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / 'data/manifest.csv', backup)
        write_manifest(rows, root)
        record = root / 'data/migrations' / f'areas-{stamp()}.json'
        write_json(record, {'schema_version': 1, 'migration': 'two_area_review_states', 'backup': backup.relative_to(root).as_posix(), 'changed': changed})
    from src.workbench.queries import data_index
    data_index.invalidate(root)
    return {'changed': len(changed), 'backup': backup.relative_to(root).as_posix(), 'record': record.relative_to(root).as_posix()}
