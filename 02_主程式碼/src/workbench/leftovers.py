"""What is left behind after something was deleted, and removing it.

`audit` only reads; `sweep` removes.  Both cover the same categories, so a sweep can always be
checked with an audit afterwards.  `after_purge` is called by the trash right after a permanent
deletion, so new deletions leave nothing behind in the first place.

Kept on purpose (named in the deletion report, never swept):
  * resource_lifecycle rows marked 'purged' and deleted_job_keys: they stop a deleted id or
    request key from being reused silently;
  * trash operation history, the audit log and the experiment ledger: records of what was done,
    which the project owner can clear in the trash page;
  * consent and withdrawal records of LINE research photos (legal record);
  * data/migrations: history of one-off data changes (ids only).
"""

from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path

from src.common import ROOT, read_json, read_manifest, stamp, write_json

RETIRED = (
    'runtime/ultralytics',
    'runtime/experiments.log',
    'runtime/workbench/staging',
    'runtime/performance-baseline-pytest.xml',
    'runtime/performance-current-pytest.xml',
    'runtime/performance-final-pytest.xml',
    'data/yolo',
)


def _db():
    from src.workbench import jobs

    return jobs.db()


def _has(con, table: str) -> bool:
    return bool(con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone())


def _purged(kind: str) -> set[str]:
    with _db() as con:
        return {r[0] for r in con.execute("SELECT id FROM resource_lifecycle WHERE type=? AND state='purged'", (kind,))}


def _is_link(path: Path) -> bool:
    return path.is_symlink() or bool(getattr(path, 'is_junction', lambda: False)())


def _size(path: Path) -> int:
    if not path.exists() or _is_link(path):
        return 0
    if path.is_file():
        return path.stat().st_size
    return sum(p.stat().st_size for p in path.rglob('*') if p.is_file() and not _is_link(p))


def _remove(path: Path, inside: Path) -> int:
    """Remove a file or a folder tree that sits inside `inside`; links are never followed."""
    path = Path(path)
    if not path.exists() and not _is_link(path):
        return 0
    if not Path(os.path.abspath(path)).is_relative_to(Path(os.path.abspath(inside))):
        raise ValueError('不在允許的範圍內：' + str(path))
    if _is_link(path):
        raise ValueError('不會刪除連結：' + path.name)
    size = _size(path)
    if path.is_dir():
        for child in path.rglob('*'):
            if _is_link(child):
                raise ValueError('資料夾內有連結，沒有刪除：' + child.name)
        shutil.rmtree(path)
    else:
        path.unlink()
    return size


def _empty_dirs(base: Path) -> None:
    if not base.is_dir() or _is_link(base):
        return
    for folder in sorted(
        (p for p in base.rglob('*') if p.is_dir() and not _is_link(p)), key=lambda p: len(p.parts), reverse=True
    ):
        try:
            folder.rmdir()
        except OSError:
            pass


# --------------------------------------------------------------------------------- per deletion
def after_purge(kind: str, ident: str, root: Path = ROOT) -> None:
    """Everything a permanently deleted resource leaves outside its own folder."""
    if kind == 'job':
        from src.workbench import jobs

        _remove(root / 'runs/workbench/evaluations' / ident, root / 'runs/workbench/evaluations')
        with _db() as con:
            con.execute('DELETE FROM report_samples WHERE report=?', (ident,))
            con.execute('DELETE FROM report_index WHERE id=?', (ident,))
            if _has(con, 'notifications'):  # made on first use
                con.execute(
                    'DELETE FROM notifications WHERE key LIKE ? OR href LIKE ?', (f'job:{ident}:%', f'%job={ident}%')
                )
        folder = jobs.folder(ident)
        _empty_dirs(folder)
        try:
            folder.rmdir()
        except OSError:
            pass
    elif kind == 'model':
        from src.workbench import registry

        folder = registry.artifact_path(ident)
        _empty_dirs(folder)
        try:
            folder.rmdir()
        except OSError:
            pass
        with _db() as con:
            con.execute('DELETE FROM flags WHERE id=?', ('model_attention:' + ident,))
    elif kind == 'snapshot':
        _forget_snapshot(root, ident)
    elif kind == 'research_photo':
        from src.workbench import intake

        folder = intake.HOME / 'research_intake' / ident
        _empty_dirs(folder)
        try:
            folder.rmdir()
        except OSError:
            pass


def _forget_snapshot(root: Path, version: str) -> None:
    state_path = root / 'data/snapshot_states.json'
    if state_path.exists():
        states = read_json(state_path)
        if version in states:
            states.pop(version)
            write_json(state_path, states)
    for pointer in (root / 'data/snapshots').glob('latest_*.json'):
        if read_json(pointer).get('version') == version:
            pointer.unlink()
    with _db() as con:
        con.execute("DELETE FROM file_projection WHERE path LIKE ?", (f'%/{version}/%',))


# --------------------------------------------------------------------------------- whole project
def _categories(root: Path) -> dict[str, list]:
    """name -> list of ('path', Path, bytes) or ('sql', statement, params, count)."""
    from src.imports import service as imports
    from src.workbench import jobs

    found: dict[str, list] = {}
    jobs_root = root / 'runs/workbench/jobs'
    purged_jobs = _purged('job')
    found['刪除工作留下的資料夾'] = [
        ('path', jobs_root / i, _size(jobs_root / i)) for i in sorted(purged_jobs) if (jobs_root / i).exists()
    ]
    reports = root / 'runs/workbench/evaluations'
    found['刪除工作留下的評估報告'] = [
        ('path', reports / i, _size(reports / i)) for i in sorted(purged_jobs) if (reports / i).exists()
    ]
    versions = root / 'models/versions'
    purged_models = _purged('model')
    stale = time.time() - 3600
    found['刪除模型留下的資料夾'] = (
        [
            ('path', p, _size(p))
            for p in sorted(versions.iterdir())
            if versions.exists()
            if p.is_dir() and (p.name in purged_models or (p.name.startswith('.') and p.stat().st_mtime < stale))
        ]
        if versions.exists()
        else []
    )
    with _db() as con:
        rows = con.execute('SELECT id,path FROM report_index').fetchall()
        gone = [r[0] for r in rows if not (root / r[1]).exists() and not Path(r[1]).exists()]
        orphan_samples = con.execute(
            'SELECT COUNT(*) FROM report_samples WHERE report NOT IN (SELECT id FROM report_index)'
        ).fetchone()[0]
        notes = con.execute('SELECT id,key,href FROM notifications').fetchall() if _has(con, 'notifications') else []
        projections = con.execute('SELECT path FROM file_projection').fetchall()
        expired = con.execute('SELECT COUNT(*) FROM trash_previews WHERE expires<?', (time.time(),)).fetchone()[0]
        known_jobs = {r[0] for r in con.execute('SELECT id FROM jobs')}
        assets = {r[0] for r in con.execute('SELECT path FROM assets')}
        synthetic = [
            r[0]
            for r in con.execute('SELECT id,data FROM cases')
            if 'Synthetic' in (r[1] or '') or 'synthetic_fixture' in (r[1] or '')
        ]
    found['已不存在的報告索引'] = [('sql', 'DELETE FROM report_index WHERE id=?', (i,), 1) for i in gone]
    if orphan_samples:
        found['已不存在的報告索引'].append(
            ('sql', 'DELETE FROM report_samples WHERE report NOT IN (SELECT id FROM report_index)', (), orphan_samples)
        )
    dead_notes = []
    for nid, key, href in notes:
        job = None
        if key and key.startswith('job:'):
            job = key.split(':')[1]
        elif href and 'job=' in href:
            job = href.split('job=')[1].split('&')[0]
        if job and job not in known_jobs:
            dead_notes.append(('sql', 'DELETE FROM notifications WHERE id=?', (nid,), 1))
    found['指向已刪除工作的通知'] = dead_notes
    found['已不存在檔案的索引'] = [
        ('sql', 'DELETE FROM file_projection WHERE path=?', (p,), 1)
        for (p,) in projections
        if not (root / p).exists() and not Path(p).exists()
    ]
    found['過期的刪除預覽'] = (
        [('sql', 'DELETE FROM trash_previews WHERE expires<?', (time.time(),), expired)] if expired else []
    )
    found['測試用的合成案例'] = [('sql', 'DELETE FROM cases WHERE id=?', (i,), 1) for i in synthetic]

    # Photo copies outside the project's own photo folders.
    staged = root / imports.EXTERNAL_STAGING
    busy = False
    with imports.store(root) as con:
        busy = bool(con.execute("SELECT 1 FROM imports WHERE state IN ('queued','running') LIMIT 1").fetchone())
    found['匯入暫存的照片副本'] = (
        [] if busy else [('path', p, _size(p)) for p in sorted(staged.iterdir())] if staged.exists() else []
    )
    locks = [p for p in (root / 'runtime/imports').glob('*.lock')] if (root / 'runtime/imports').exists() else []
    found['匯入留下的鎖定檔'] = [] if busy else [('path', p, _size(p)) for p in locks]
    cache = root / 'runtime/cache/images'
    current = read_manifest(root) if (root / 'data/manifest.csv').exists() else []
    found['縮圖快取'] = [('path', p, _size(p)) for p in cache.glob('*.jpg')] if cache.exists() and not current else []
    sims = root / 'runtime/workbench/assets/simulation'
    found['沒有紀錄的模擬照片'] = (
        [
            ('path', p, _size(p))
            for p in sorted(sims.glob('*'))
            if p.is_file() and not any(Path(a).name == p.name for a in assets)
        ]
        if sims.exists()
        else []
    )
    from src.data import photo_trash

    alive = (
        {r['image_id'] for r in current} | {p.name for p in (root / photo_trash.FOLDER).iterdir()}
        if (root / photo_trash.FOLDER).exists()
        else {r['image_id'] for r in current}
    )
    hashes = (
        {r['sha256'] for r in current}
        | photo_trash.in_trash_hashes(root)
        | {read_json(p)['row']['sha256'] for p in (root / photo_trash.FOLDER).glob('*/record.json')}
    )
    features = root / 'runtime/workbench/features'
    orphan_features = []
    for sidecar in sorted(features.glob('*.json')) if features.exists() else []:
        try:
            owner = read_json(sidecar).get('image_id')
        except (OSError, ValueError):
            owner = None
        if owner not in alive:
            orphan_features += [
                ('path', sidecar, _size(sidecar)),
                ('path', sidecar.with_suffix('.npy'), _size(sidecar.with_suffix('.npy'))),
            ]
    found['已刪除照片的特徵快取'] = orphan_features
    cached = []
    for name in ('runtime/imports/pixel_cache.json', 'runtime/workbench/quality_cache.json'):
        path = root / name
        if path.exists():
            extra = [k for k in read_json(path) if k not in hashes]
            if extra:
                cached.append(('json', path, extra, len(extra)))
    found['已刪除照片的像素與品質快取'] = cached
    journals = root / 'runtime/review_transactions'
    finished = []
    for journal in sorted(journals.glob('*/journal.json')) if journals.exists() else []:
        try:
            pending = read_json(journal).get('state') == 'pending'
        except (OSError, ValueError):
            pending = False
        if not pending:
            finished.append(('path', journal.parent, _size(journal.parent)))
    found['已完成的審查交易紀錄'] = finished
    found['已移除功能留下的檔案'] = [('path', root / p, _size(root / p)) for p in RETIRED if (root / p).exists()]
    hf = root / 'models/pretrained/hf-cache'
    complete = all((root / 'models/pretrained' / m / 'model.safetensors').exists() for m in ('dinov2_small',))
    found['已複製完成的下載快取'] = [('path', hf, _size(hf))] if hf.exists() and complete else []
    states = root / 'data/snapshot_states.json'
    if states.exists():
        from src.common import snapshot_versions

        existing = {p.parent.name for p in snapshot_versions(root)}
        stale_states = [v for v in read_json(states) if v not in existing]
        found['已刪除快照的狀態紀錄'] = [('json', states, stale_states, len(stale_states))] if stale_states else []
    return found


def audit(root: Path = ROOT) -> dict:
    out = {}
    for name, items in _categories(root).items():
        if items:
            out[name] = {
                'count': sum(i[3] if i[0] in ('sql', 'json') else 1 for i in items),
                'bytes': sum(i[2] for i in items if i[0] == 'path'),
            }
    return out


def sweep(root: Path = ROOT) -> dict:
    """Remove every leftover category.  Run with the workbench idle; it never touches live data."""
    from src.common import database_backup
    from src.workbench.storage import dataset_lock

    home = root / 'runtime/workbench'
    if (home / 'workbench.sqlite3').exists():
        backup = database_backup(home, f'before-sweep-{stamp()}.sqlite3')
        backup.parent.mkdir(parents=True, exist_ok=True)
        with _db() as con:
            con.execute('VACUUM INTO ?', (str(backup),))
    result = {}
    with dataset_lock(root):
        # Removing one kind can expose another (rows of a report whose index row just went), so
        # repeat until a pass finds nothing.
        for _ in range(5):
            if not _sweep_once(root, result):
                break
        _empty_dirs(root / 'models/versions')
        for base in ('runs/workbench/jobs', 'runs/workbench/evaluations'):
            for folder in (root / base).iterdir() if (root / base).exists() else []:
                if folder.is_dir() and not _is_link(folder) and not any(folder.iterdir()):
                    folder.rmdir()
    return result


def _sweep_once(root: Path, result: dict) -> bool:
    changed = False
    if True:
        for name, items in _categories(root).items():
            done = freed = 0
            for item in items:
                if item[0] == 'path':
                    freed += _remove(item[1], root)
                    done += 1
                elif item[0] == 'sql':
                    with _db() as con:
                        con.execute(item[1], item[2])
                    done += item[3]
                else:
                    data = read_json(item[1])
                    for key in item[2]:
                        data.pop(key, None)
                    write_json(item[1], data)
                    done += item[3]
            if done:
                old = result.get(name, {'count': 0, 'bytes': 0})
                result[name] = {'count': old['count'] + done, 'bytes': old['bytes'] + freed}
                changed = True
    return changed
