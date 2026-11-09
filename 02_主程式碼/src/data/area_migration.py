"""One-time, repeatable migration from two review areas to one (2026-11).

The lesion detection area was removed.  A photo's state now comes only from its classification
review, so photos confirmed only in the detection area become excluded (those were duplicate
copies whose other copy stays in classification).  The detection columns leave the manifest.
Box files stay next to their photos, unused.  The manifest is backed up first.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from src.common import ROOT, pre_change_dir, read_manifest, record_path, stamp, write_json, write_manifest
from src.data import tasks


def migrate_single_area(root: Path = ROOT) -> dict:
    from src.workbench.storage import dataset_lock
    from src.data.dataset import move_with_annotations, recover_reviews

    with dataset_lock(root):
        recover_reviews(root)
        rows = read_manifest(root)
        retired = [c for c in tasks.RETIRED_COLUMNS if rows and c in rows[0]]
        moving = []
        for row in rows:
            state = tasks.area_state(row, 'cls')
            status = tasks.storage_status(state)
            if status != row['status']:
                moving.append({'image_id': row['image_id'], 'from': row['status'], 'to': status})
        if not retired and not moving:
            return {'changed': 0, 'note': '已是單一工作區，無需遷移'}
        backup = pre_change_dir('manifest', root) / f'manifest-before-single-area-{stamp()}.csv'
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / 'data/manifest.csv', backup)
        moved = {m['image_id']: m['to'] for m in moving}
        for row in rows:
            row['cls_review'] = tasks.area_state(row, 'cls')
            if row['image_id'] in moved:
                status = moved[row['image_id']]
                base = (
                    'approved'
                    if status == 'approved'
                    else f"{status}/" + ('other' if status == 'excluded' else 'annotation')
                )
                row.update(move_with_annotations(row, base, root), status=status)
            for column in tasks.RETIRED_COLUMNS:
                row.pop(column, None)
        write_manifest(rows, root)
        record = root / 'data/migrations' / f'single-area-{stamp()}.json'
        write_json(
            record,
            {
                'schema_version': 1,
                'migration': 'single_review_area',
                'backup': record_path(backup, root),
                'removed_columns': retired,
                'moved': moving,
            },
        )
    from src.workbench.queries import data_index

    data_index.invalidate(root)
    return {
        'changed': len(rows),
        'moved': len(moving),
        'backup': record_path(backup, root),
        'record': record.relative_to(root).as_posix(),
    }
