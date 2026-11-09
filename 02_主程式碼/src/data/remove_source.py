"""One-time removal of photos that do not belong in the project.

The workbench's trash never takes dataset photos, so this tool does it: preview first, back up,
then MOVE everything to `待你刪除/非岡山照片/`.  Nothing is deleted here; the project owner
deletes that folder after checking it.  Re-running continues an interrupted run and changes
nothing after a finished one.

    python -m src.data.remove_source                      # preview: not from 岡山高醫 (#61)
    python -m src.data.remove_source --apply --expect 37
    python -m src.data.remove_source --nonstandard        # preview: name not in the hospital's format
    python -m src.data.remove_source --nonstandard --apply --expect 24
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from src.common import (
    ROOT,
    inside,
    pre_change_dir,
    read_json,
    read_manifest,
    record_path,
    stamp,
    write_json,
    write_manifest,
)
from src.data import evidence, filename_rules

OLD_FOLDER = 'YOLODataset'
ARCHIVE = f'archive/legacy/{OLD_FOLDER}'
DESTINATION = '待你刪除/非岡山照片'
NONSTANDARD_DESTINATION = '待你刪除/不符檔名格式'
README = """# 移出專案的照片

這裡是 M2.5 移出專案的照片與紀錄，系統已不再使用。

- `images/`：移除的照片
- `{folder}/`：舊來源資料夾（如果有）
- `records/`：這些照片的審查與標籤來源紀錄
- `清單.json`：每張照片的代號與雜湊

確認沒問題後，直接刪除整個資料夾即可。
"""


def _paths(row: dict) -> list[str]:
    return [str(p).replace('\\', '/') for p in json.loads(row.get('original_paths') or '[]')]


def selected(rows: list[dict]) -> list[dict]:
    """Photos from the old folder whose every name lacks the hospital's filename format.
    Not the 「其他」 tab: photos of this hospital without an import alias are listed there too."""
    return [
        r
        for r in rows
        if any(OLD_FOLDER in p for p in _paths(r)) and not any(filename_rules.record_code(p) for p in _paths(r))
    ]


def nonstandard(rows: list[dict]) -> list[dict]:
    """Photos with no name in the format the hospital confirmed."""
    return [r for r in rows if not any(filename_rules.is_standard(p) for p in _paths(r))]


def _records(root: Path, ids: set[str]) -> list[Path]:
    """Files that exist only because of these photos."""
    found = [p for p in (root / 'data/reviews').glob('*.json') if p.stem.split('_', 1)[-1] in ids]
    found += [evidence.path(i, root) for i in sorted(ids) if evidence.path(i, root).exists()]
    return found


def preview(root: Path = ROOT, choose=selected) -> dict:
    rows = read_manifest(root)
    chosen = choose(rows)
    ids = {r['image_id'] for r in chosen}
    archive = root / ARCHIVE
    return {
        'photos': len(chosen),
        'statuses': {s: sum(1 for r in chosen if r['status'] == s) for s in sorted({r['status'] for r in chosen})},
        'kept': len(rows) - len(chosen),
        'kept_statuses': {
            s: sum(1 for r in rows if r['image_id'] not in ids and r['status'] == s)
            for s in sorted({r['status'] for r in rows if r['image_id'] not in ids})
        },
        'records': len(_records(root, ids)),
        'archive_files': sum(1 for p in archive.rglob('*') if p.is_file()) if archive.exists() else 0,
    }


def _move(source: Path, target: Path) -> None:
    if target.exists():
        raise ValueError(f'目的地已有同名檔案，沒有繼續：{target.name}')
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(target))


def _forget_in_decisions(root: Path, ids: set[str]) -> None:
    path = root / 'data/image_sources.json'
    if path.exists():
        data = read_json(path)
        kept = {k: v for k, v in data.get('images', {}).items() if k not in ids}
        if len(kept) != len(data.get('images', {})):
            write_json(path, {**data, 'images': kept})
    path = root / 'data/duplicate_decisions.json'
    if path.exists():
        data = read_json(path)
        kept = {k: v for k, v in data.get('pairs', {}).items() if not set(k.split('|')) & ids}
        if len(kept) != len(data.get('pairs', {})):
            write_json(path, {**data, 'pairs': kept})
    path = root / 'data/spot_checks.json'
    if path.exists():
        data = read_json(path)
        samples = [s for s in data.get('samples', []) if s['image_id'] not in ids]
        considered = [i for i in data.get('considered', []) if i not in ids]
        if len(samples) != len(data.get('samples', [])) or len(considered) != len(data.get('considered', [])):
            write_json(path, {**data, 'samples': samples, 'considered': considered})


def apply(root: Path = ROOT, *, expect: int, choose=selected, destination: str = DESTINATION) -> dict:
    from src.data.dataset import recover_reviews
    from src.workbench.queries import data_index
    from src.workbench.storage import dataset_lock

    with dataset_lock(root):
        recover_reviews(root)
        rows = read_manifest(root)
        chosen = choose(rows)
        archive = root / ARCHIVE
        if not chosen and (choose is not selected or not archive.exists()):
            return {'changed': 0, 'note': '已移除，無需處理'}
        if chosen and len(chosen) != expect:
            raise ValueError(f'選到 {len(chosen)} 張，預期 {expect} 張，沒有變更任何檔案')
        ids = {r['image_id'] for r in chosen}
        base = root / destination
        listing = base / '清單.json'
        backup = None
        if chosen:
            backup = pre_change_dir('manifest', root) / f'manifest-before-source-removal-{stamp()}.csv'
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(root / 'data/manifest.csv', backup)
            base.mkdir(parents=True, exist_ok=True)
            write_json(
                listing,
                {
                    'schema_version': 1,
                    'removed_at': stamp(),
                    'photos': [
                        {k: r[k] for k in ('image_id', 'sha256', 'status', 'label_state', 'image_path')} for r in chosen
                    ],
                },
            )
            (base / 'README.md').write_text(README.format(folder=OLD_FOLDER), encoding='utf-8')
        # Files first, manifest last: a crash leaves a run that can simply be repeated.
        for r in chosen:
            image = inside(r['image_path'], root)
            if image.exists():
                _move(image, base / 'images' / image.name)
            if r.get('annotation_path') and inside(r['annotation_path'], root).exists():
                note = inside(r['annotation_path'], root)
                _move(note, base / 'images' / note.name)
        records = _records(root, ids)
        for path in records:
            _move(path, base / 'records' / path.relative_to(root))
        _forget_in_decisions(root, ids)
        moved_archive = choose is selected and archive.exists()
        if moved_archive:
            _move(archive, base / OLD_FOLDER)
        write_manifest([r for r in rows if r['image_id'] not in ids], root)
        entry = {
            'schema_version': 1,
            'migration': 'remove_non_gangshan_photos' if choose is selected else 'remove_nonstandard_names',
            'backup': record_path(backup, root) if backup else None,
            'removed': sorted(ids),
            'moved_to': destination,
            'records': len(records),
            'archive_moved': moved_archive,
        }
        write_json(root / 'data/migrations' / f'source-removal-{stamp()}.json', entry)
    data_index.invalidate(root)
    return {'changed': len(ids), **{k: entry[k] for k in ('backup', 'moved_to', 'records', 'archive_moved')}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--expect', type=int)
    parser.add_argument('--nonstandard', action='store_true')
    args = parser.parse_args()
    choose = nonstandard if args.nonstandard else selected
    print(preview(choose=choose))
    if args.apply:
        if args.expect is None:
            parser.error('--apply 需要 --expect，先看預覽的張數')
        destination = NONSTANDARD_DESTINATION if args.nonstandard else DESTINATION
        print(apply(expect=args.expect, choose=choose, destination=destination))


if __name__ == '__main__':
    main()
