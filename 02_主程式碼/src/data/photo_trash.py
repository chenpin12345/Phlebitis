"""Deleting a photo from the system, with everything that exists because of it.

Two steps.  `move` takes the photo out of use and keeps it restorable under data/photo_trash/.
`purge`, which only the project owner starts from the trash page, then removes the photo, its
records and every copy: snapshot images, report images and heat maps, feature and pixel caches,
finished review journals, and its filename in other records.

What is kept on purpose: the source file in 05_匯入區 (a hash in data/deleted_photos.json stops it
being offered again), report numbers, models (they are marked for re-evaluation; what a model
learned cannot be deleted) and backups (replaced when they expire).
"""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path, PurePosixPath

from src.common import ROOT, inside, read_json, read_manifest, snapshot_versions, stamp, write_json, write_manifest
from src.data import evidence, remove_source, revocations

FOLDER = 'data/photo_trash'
TOMBSTONES = 'data/deleted_photos.json'
SOURCE = 'photo_trash'
RENAMED = '（已刪除照片）'


def _busy(root: Path) -> bool:
    from src.workbench import jobs

    with jobs.db() as con:
        return bool(
            con.execute(
                "SELECT 1 FROM jobs WHERE state NOT IN ('succeeded','failed','cancelled','interrupted') LIMIT 1"
            ).fetchone()
        )


def _refuse_while_busy(root: Path) -> None:
    if _busy(root):
        raise ValueError('有工作正在執行，請等工作結束後再刪除照片')


def _folder(root: Path, ident: str) -> Path:
    path = (root / FOLDER / ident).resolve()
    if not path.is_relative_to((root / FOLDER).resolve()) or path == (root / FOLDER).resolve():
        raise ValueError('無效的照片代號')
    return path


def _snapshots_with(root: Path, ids: set[str]) -> dict[str, set[str]]:
    found = {}
    for meta in snapshot_versions(root):
        folder = meta.parent / 'images'
        hits = {i for i in ids if (folder / f'{i}.jpg').exists()}
        if hits:
            found[meta.parent.name] = hits
    return found


def _reports_with(root: Path, ids: set[str]) -> list[tuple[Path, set[str]]]:
    found = []
    for path in (root / 'runs/workbench/evaluations').glob('*/report.json'):
        samples = {s.get('image_id') for s in read_json(path).get('samples', [])}
        if samples & ids:
            found.append((path.parent, samples & ids))
    return found


def _models_with(root: Path, ids: set[str]) -> list[str]:
    """Models whose training fold held these photos, by the fold they name."""
    from src.workbench import registry

    names = []
    for meta in registry.metadata_listing():
        dataset = (meta.get('extra') or {}).get('dataset')
        split = inside(dataset, root).parent / 'split.json' if dataset else None
        if split and split.exists():
            train = {m['image_id'] for m in read_json(split)['members']['train']}
            if train & ids:
                names.append(meta['id'])
    return names


def _size(paths) -> int:
    return sum(p.stat().st_size for p in paths if p.is_file())


def _copies(root: Path, ids: set[str]) -> list[Path]:
    paths = []
    for version, hits in _snapshots_with(root, ids).items():
        base = next(m.parent for m in snapshot_versions(root) if m.parent.name == version)
        paths += [base / 'images' / f'{i}.jpg' for i in hits]
    for folder, hits in _reports_with(root, ids):
        for ident in hits:
            paths += [folder / f'{ident}.jpg', folder / 'heatmaps' / f'{ident}.png']
    return paths


def preview(ids: list[str], root: Path = ROOT) -> dict:
    wanted = set(ids)
    rows = [r for r in read_manifest(root) if r['image_id'] in wanted]
    if len(rows) != len(wanted):
        raise ValueError('有照片不在系統內')
    all_rows = read_manifest(root)
    left = [r for r in all_rows if r['image_id'] not in wanted and r['status'] == 'approved']
    before = {r['subject_id'] for r in all_rows if r['status'] == 'approved' and r['subject_id']}
    after = {r['subject_id'] for r in left if r['subject_id']}
    photo_bytes = _size(inside(r['image_path'], root) for r in rows)
    copies = _copies(root, wanted)
    return {
        'photos': len(rows),
        'approved': sum(r['status'] == 'approved' for r in rows),
        'patients_lost': len(before - after),
        'snapshots': len(_snapshots_with(root, wanted)),
        'reports': len(_reports_with(root, wanted)),
        'models': len(_models_with(root, wanted)),
        'bytes': photo_bytes + _size(copies),
        'busy': _busy(root),
    }


def move(ids: list[str], by: str, root: Path = ROOT) -> dict:
    from src.data.dataset import recover_reviews
    from src.workbench.queries import data_index
    from src.workbench.storage import dataset_lock

    if not by.strip():
        raise ValueError('請先設定操作者名稱')
    _refuse_while_busy(root)
    wanted = set(ids)
    with dataset_lock(root):
        recover_reviews(root)
        rows = read_manifest(root)
        chosen = [r for r in rows if r['image_id'] in wanted]
        if len(chosen) != len(wanted):
            raise ValueError('有照片不在系統內')
        names = (
            read_json(root / 'data/image_sources.json')
            if (root / 'data/image_sources.json').exists()
            else {'images': {}}
        )
        for row in chosen:
            ident = row['image_id']
            revocations.revoke('image', ident, '移到垃圾桶', SOURCE, root)  # effective at once, snapshots included
            folder = _folder(root, ident)
            image = inside(row['image_path'], root)
            files = [image, *sorted((image.parent.parent / 'annotations').glob(ident + '*'))]
            if row.get('annotation_path') and inside(row['annotation_path'], root) not in files:
                files.append(inside(row['annotation_path'], root))
            files += remove_source._records(root, {ident})
            moved = []
            for n, path in enumerate(f for f in files if f.exists()):
                target = folder / 'files' / f'{n}_{path.name}'
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(path), str(target))
                moved.append({'stored': target.name, 'path': path.relative_to(root).as_posix()})
            write_json(
                folder / 'record.json',
                {
                    'schema_version': 1,
                    'row': row,
                    'source': names.get('images', {}).get(ident),
                    'files': moved,
                    'moved_at': time.time(),
                    'moved_by': by.strip(),
                },
            )
        if any(r['image_id'] in names.get('images', {}) for r in chosen):
            write_json(
                root / 'data/image_sources.json',
                {**names, 'images': {k: v for k, v in names['images'].items() if k not in wanted}},
            )
        write_manifest([r for r in rows if r['image_id'] not in wanted], root)
    data_index.invalidate(root)
    return {'moved': len(chosen)}


def listing(root: Path = ROOT) -> dict:
    items = []
    base = root / FOLDER
    for path in sorted(base.glob('*/record.json')) if base.exists() else []:
        record = read_json(path)
        row = record['row']
        name = PurePosixPath(
            str((json.loads(row.get('original_paths') or '[]') or [row['image_path']])[0]).replace('\\', '/')
        ).name
        items.append(
            {
                'image_id': row['image_id'],
                'name': name,
                'status': row['status'],
                'stage': row.get('stage_label') or '',
                'moved_at': record['moved_at'],
                'moved_by': record['moved_by'],
            }
        )
    return {'items': items, 'busy': _busy(root)}


def restore(ids: list[str], by: str, root: Path = ROOT) -> dict:
    from src.workbench.queries import data_index
    from src.workbench.storage import dataset_lock

    _refuse_while_busy(root)
    with dataset_lock(root):
        rows = read_manifest(root)
        names = (
            read_json(root / 'data/image_sources.json')
            if (root / 'data/image_sources.json').exists()
            else {'images': {}}
        )
        for ident in ids:
            folder = _folder(root, ident)
            record = read_json(folder / 'record.json')
            if record['row']['sha256'] in {r['sha256'] for r in rows}:
                raise ValueError('這張照片已重新匯入，不能再還原；可以直接永久刪除垃圾桶裡的紀錄')
            for item in record['files']:
                target = root / item['path']
                if target.exists():
                    raise ValueError('原位置已有同名檔案，沒有還原')
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(folder / 'files' / item['stored']), str(target))
            rows.append(record['row'])
            if record.get('source'):
                names.setdefault('images', {})[ident] = record['source']
            revocations.clear('image', ident, SOURCE, root)
            shutil.rmtree(folder)
        write_json(root / 'data/image_sources.json', names)
        write_manifest(rows, root)
    data_index.invalidate(root)
    return {'restored': len(ids)}


def _names_of(row: dict, source: dict | None) -> set[str]:
    names = {PurePosixPath(str(p).replace('\\', '/')).name for p in json.loads(row.get('original_paths') or '[]')}
    return names | {a['filename'] for a in (source or {}).get('aliases', [])}


def _names_still_used(root: Path, leaving: set[str]) -> set[str]:
    """Two different photos can share a filename; the one that stays keeps it."""
    path = root / 'data/image_sources.json'
    sources = read_json(path)['images'] if path.exists() else {}
    used = set()
    for row in read_manifest(root):
        used |= _names_of(row, sources.get(row['image_id']))
    base = root / FOLDER
    for record_path in base.glob('*/record.json') if base.exists() else []:
        record = read_json(record_path)
        if record['row']['image_id'] not in leaving:
            used |= _names_of(record['row'], record.get('source'))
    return used


def _rewrite_names(root: Path, names: set[str]) -> int:
    """Filenames of deleted photos also sit in other photos' records.  Reviews and the manifest
    change together, so a review still matches its row."""
    changed = 0
    paths = [root / 'data/manifest.csv']
    for folder in ('data/reviews', 'data/label_evidence', 'data/migrations', 'data/imports', 'runtime/imports'):
        paths += [p for p in (root / folder).rglob('*.json')] if (root / folder).exists() else []
    from src.imports import service as imports

    with imports.store(root) as con:
        for ident, payload in con.execute('SELECT id,payload FROM imports').fetchall():
            fresh = payload
            for name in names:
                fresh = fresh.replace(json.dumps(name, ensure_ascii=False)[1:-1], RENAMED)
            if fresh != payload:
                con.execute('UPDATE imports SET payload=? WHERE id=?', (fresh, ident))
                changed += 1
    for path in paths:
        if not path.exists():
            continue
        text = path.read_text(encoding='utf-8-sig' if path.suffix == '.csv' else 'utf-8')
        fresh = text
        for name in names:
            fresh = fresh.replace(name, RENAMED)
        if fresh != text:
            path.write_text(fresh, encoding='utf-8-sig' if path.suffix == '.csv' else 'utf-8')
            changed += 1
    return changed


def _drop_caches(root: Path, ids: set[str], hashes: set[str]) -> None:
    features = root / 'runtime/workbench/features'
    for sidecar in features.glob('*.json') if features.exists() else []:
        if read_json(sidecar).get('image_id') in ids:
            sidecar.with_suffix('.npy').unlink(missing_ok=True)
            sidecar.unlink()
    (root / 'data/audit_report.json').unlink(missing_ok=True)  # a saved check result; rebuilt on the next audit
    from src.workbench.queries import images

    images.clear(root)  # thumbnails are named by a hash of their source, so all of them go; rebuilt on view
    staged = root / 'runtime/imports/external'
    for copy in staged.rglob('*') if staged.exists() else []:
        if copy.is_file() and not copy.is_symlink():
            from src.common import sha256

            if sha256(copy) in hashes:
                copy.unlink()
    for name in ('runtime/imports/pixel_cache.json', 'runtime/workbench/quality_cache.json'):
        path = root / name
        if path.exists():
            cache = read_json(path)
            kept = {k: v for k, v in cache.items() if k not in hashes}
            if len(kept) != len(cache):
                write_json(path, kept)
    for journal in (root / 'runtime/review_transactions').glob('*/journal.json'):
        tx = read_json(journal)
        text = ''.join(p.read_text(encoding='utf-8', errors='ignore') for p in journal.parent.iterdir() if p.is_file())
        if tx.get('state') != 'pending' and any(i in text for i in ids):
            shutil.rmtree(journal.parent)


def _forget_decisions(root: Path, ids: set[str]) -> None:
    remove_source._forget_in_decisions(root, ids)
    path = root / 'data/quality_reviews.json'
    if path.exists():
        data = read_json(path)
        kept = {k: v for k, v in data.get('images', {}).items() if k not in ids}
        if len(kept) != len(data.get('images', {})):
            write_json(path, {**data, 'images': kept})


def _mark_models(root: Path, names: list[str]) -> None:
    from src.workbench import jobs

    with jobs.db() as con:
        for name in names:
            con.execute(
                'INSERT OR REPLACE INTO flags(id,data) VALUES(?,?)',
                (
                    'model_attention:' + name,
                    json.dumps({'reason': '訓練用的照片已被刪除，需重新評估', 'at': stamp()}, ensure_ascii=False),
                ),
            )


def purge(ids: list[str], by: str, root: Path = ROOT) -> dict:
    """Permanent.  Only the project owner starts this, from the trash page."""
    from src.workbench import ledger
    from src.workbench.queries import data_index
    from src.workbench.storage import dataset_lock

    if not by.strip():
        raise ValueError('請先設定操作者名稱')
    _refuse_while_busy(root)
    wanted = set(ids)
    freed = 0
    with dataset_lock(root):
        records = {i: read_json(_folder(root, i) / 'record.json') for i in ids}
        current = read_manifest(root)
        back_ids, back_hashes = {r['image_id'] for r in current}, {r['sha256'] for r in current}
        returned = {i for i, r in records.items() if i in back_ids or r['row']['sha256'] in back_hashes}
        trash_only = list(ids)
        wanted = wanted - returned
        hashes = {r['row']['sha256'] for i, r in records.items() if i not in returned}
        kept_out = {r['row']['sha256'] for i, r in records.items() if i not in returned and not r.get('may_return')}
        names = set()
        for ident, record in records.items():
            if ident not in returned:
                names |= _names_of(record['row'], record.get('source'))
        names -= _names_still_used(root, wanted)
        models = _models_with(root, wanted)
        snapshots = _snapshots_with(root, wanted)
        copies = _copies(root, wanted)
        for path in copies:
            if path.is_file():
                freed += path.stat().st_size
                path.unlink()
        reports = len(_reports_with(root, wanted))
        state_path = root / 'data/snapshot_states.json'
        states = read_json(state_path) if state_path.exists() else {}
        for version in snapshots:
            states[version] = {'status': 'contains_deleted', 'reason': '含已刪除的照片，不能再訓練', 'at': stamp()}
        if snapshots:
            write_json(state_path, states)
        for ident in trash_only:
            folder = _folder(root, ident)
            freed += sum(p.stat().st_size for p in folder.rglob('*') if p.is_file())
            shutil.rmtree(folder)
        if kept_out:
            tomb_path = root / TOMBSTONES
            tombs = read_json(tomb_path) if tomb_path.exists() else {'schema_version': 1, 'sha256': {}}
            tombs['sha256'].update({h: stamp() for h in kept_out})
            write_json(tomb_path, tombs)
        _forget_decisions(root, wanted)
        _drop_caches(root, wanted, hashes)
        rewritten = _rewrite_names(root, names)
    _mark_models(root, models)
    from src.workbench.queries.data_index import connection

    with connection(root) as con:  # the index is rebuilt later; these rows must not wait for that
        con.executemany('DELETE FROM data_index WHERE id=?', [(i,) for i in trash_only])
    for ident in trash_only:
        revocations.clear('image', ident, SOURCE, root)  # nothing left to stop; the hash stops a re-import
    ledger.append(root, {'event': 'photos_deleted', 'count': len(ids), 'snapshots': len(snapshots), 'by': by.strip()})
    data_index.invalidate(root)
    return {
        'deleted': len(ids),
        'bytes': freed,
        'snapshots': len(snapshots),
        'reports': reports,
        'models': len(models),
        'records_rewritten': rewritten,
    }


def in_trash_hashes(root: Path = ROOT) -> set[str]:
    base = root / FOLDER
    records = [read_json(p) for p in base.glob('*/record.json')] if base.exists() else []
    return {r['row']['sha256'] for r in records if not r.get('may_return')}


def allow_return(ids: list[str], root: Path = ROOT) -> dict:
    """One-time exception for photos the project owner will import again (2026-11-07): they
    leave no hash behind.  Every other deletion does."""
    for ident in ids:
        path = _folder(root, ident) / 'record.json'
        write_json(path, {**read_json(path), 'may_return': True})
        revocations.clear('image', ident, SOURCE, root)
    return {'marked': len(ids)}


def tombstones(root: Path = ROOT) -> set[str]:
    path = root / TOMBSTONES
    return set(read_json(path)['sha256']) if path.exists() else set()


def clean_leftover_copies(root: Path = ROOT) -> dict:
    """Report images of photos that already left the project.  Numbers stay in the reports."""
    current = {r['image_id'] for r in read_manifest(root)}
    in_trash = {p.name for p in (root / FOLDER).iterdir()} if (root / FOLDER).exists() else set()
    files = freed = 0
    for path in (root / 'runs/workbench/evaluations').rglob('*'):
        if path.is_file() and path.suffix.lower() in ('.jpg', '.png') and path.stem not in current | in_trash:
            freed += path.stat().st_size
            files += 1
            path.unlink()
    return {'files': files, 'bytes': freed}
