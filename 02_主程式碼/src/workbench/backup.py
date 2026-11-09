"""Daily automatic backup of the workbench's small, irreplaceable records (D1).

A backup is one zip holding the photo manifest, every annotation file the manifest
references, review records, label evidence, source names, the workbench database
(copied with SQLite's online backup API, so it is consistent while in use), the
configs and the model references.  Photos and weights are not copied: they are large
and are not rewritten by the workbench; full_backup.py copies them to an external drive.
Zips are kept in 04_備份/工作台紀錄 unless the settings page names another folder.

Restore puts the dataset records back exactly as they were (reviews and evidence made
after the backup are removed; a safety backup of the current state is taken first).
The database is restored only when explicitly requested.  Model references and configs
are never restored automatically: that would switch models without an explicit choice.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import sqlite3
import tempfile
import threading
import time
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath

from src.common import ROOT, backup_root, config_path, read_manifest, write_json

SCHEMA = 1
KINDS = {'auto': '每日自動', 'manual': '手動', 'before-restore': '還原前', 'before-import': '匯入前'}
DATA_JSON = (
    'snapshot_states.json',
    'image_sources.json',
    'duplicate_decisions.json',
    'spot_checks.json',
    'experiment_ledger.jsonl',
)
RESTORABLE_DIRS = ('data/reviews/', 'data/label_evidence/', 'data/prospective/')
_mutex = threading.Lock()


def _root(root):
    from src import common

    return Path(root) if root else common.ROOT


def directory(root=None) -> Path:
    from src.workbench import settings

    configured = settings.load().backup.directory
    return Path(configured) if configured else backup_root(_root(root)) / '工作台紀錄'


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _collect(root: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    data = root / 'data'
    if (data / 'manifest.csv').is_file():
        files['data/manifest.csv'] = data / 'manifest.csv'
        for row in read_manifest(root):
            for key in ('annotation_path',):
                value = (row.get(key) or '').replace('\\', '/')
                if value and not value.startswith('/') and '..' not in PurePosixPath(value).parts:
                    path = root / value
                    if path.is_file():
                        files[value] = path
    for name in DATA_JSON:
        if (data / name).is_file():
            files['data/' + name] = data / name
    for folder in ('reviews', 'label_evidence', 'prospective'):
        for path in sorted((data / folder).rglob('*.json')) if (data / folder).is_dir() else []:
            files[path.relative_to(root).as_posix()] = path
    for path in sorted((root / 'models/references').glob('*.json')) if (root / 'models/references').is_dir() else []:
        files[path.relative_to(root).as_posix()] = path
    for name in ('import_sources.json', 'research_consent.json', 'service.json'):
        path = config_path(name, root)
        if path.is_file():
            files['configs/' + name] = path
    return files


def _database(root: Path) -> Path:
    from src.workbench import storage

    home = Path(storage.HOME) if _root(None).resolve() == root.resolve() else root / 'runtime/workbench'
    return home / 'workbench.sqlite3'


def create(kind: str = 'manual', root=None) -> dict:
    if kind not in KINDS:
        raise ValueError('無效的備份種類')
    root = _root(root)
    target_dir = directory(root)
    target_dir.mkdir(parents=True, exist_ok=True)
    with _mutex:
        created = datetime.now().strftime('%Y%m%dT%H%M%S%f')
        name = f'workbench-{created}-{kind}.zip'
        files = _collect(root)
        manifest = {'schema_version': SCHEMA, 'kind': kind, 'created': time.time(), 'files': {}, 'database': None}
        partial = target_dir / (name + '.partial')
        try:
            with zipfile.ZipFile(partial, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
                for rel, path in sorted(files.items()):
                    content = path.read_bytes()
                    manifest['files'][rel] = _sha(content)
                    archive.writestr(rel, content)
                db_path = _database(root)
                if db_path.is_file():
                    with tempfile.TemporaryDirectory() as tmp:
                        copy = Path(tmp) / 'workbench.sqlite3'
                        source = sqlite3.connect(db_path, timeout=15)
                        try:
                            target = sqlite3.connect(copy)
                            try:
                                source.backup(target)
                            finally:
                                target.close()
                        finally:
                            source.close()
                        content = copy.read_bytes()
                    manifest['database'] = _sha(content)
                    archive.writestr('runtime/workbench/workbench.sqlite3', content)
                archive.writestr('backup.json', json.dumps(manifest, ensure_ascii=False, indent=1))
            os.replace(partial, target_dir / name)
        finally:
            partial.unlink(missing_ok=True)
        _rotate(target_dir, kind)
    return describe(target_dir / name)


def _rotate(target_dir: Path, kind: str) -> None:
    from src.workbench import settings

    keep = settings.load().backup.keep
    same = sorted(target_dir.glob(f'workbench-*-{kind}.zip'), reverse=True)
    for old in same[keep:]:
        old.unlink(missing_ok=True)  # retention of our own backup copies, not user data


def describe(path: Path) -> dict:
    with zipfile.ZipFile(path) as archive:
        manifest = json.loads(archive.read('backup.json'))
    files = manifest['files']
    return {
        'name': path.name,
        'kind': manifest['kind'],
        'kind_name': KINDS.get(manifest['kind'], manifest['kind']),
        'created': manifest['created'],
        'bytes': path.stat().st_size,
        'file_count': len(files),
        'database': bool(manifest.get('database')),
        'reviews': sum(f.startswith('data/reviews/') for f in files),
        'annotations': sum('/annotations/' in f for f in files),
    }


def listing(root=None) -> dict:
    target_dir = directory(root)
    items = []
    for path in sorted(target_dir.glob('workbench-*.zip'), reverse=True) if target_dir.is_dir() else []:
        try:
            items.append(describe(path))
        except (OSError, KeyError, ValueError, zipfile.BadZipFile):
            items.append(
                {
                    'name': path.name,
                    'kind': 'unknown',
                    'kind_name': '無法讀取',
                    'created': path.stat().st_mtime,
                    'bytes': path.stat().st_size,
                    'damaged': True,
                }
            )
    items.sort(key=lambda x: x['created'], reverse=True)
    last_auto = next((i['created'] for i in items if i['kind'] == 'auto'), None)
    from src.workbench import settings

    s = settings.load().backup
    return {
        'items': items,
        'directory': str(target_dir),
        'enabled': s.enabled,
        'keep': s.keep,
        'last_auto': last_auto,
        'due': s.enabled and (last_auto is None or time.time() - last_auto > 86400),
    }


def _resolve(name: str, root=None) -> Path:
    if '/' in name or '\\' in name or not name.startswith('workbench-') or not name.endswith('.zip'):
        raise ValueError('無效的備份名稱')
    path = directory(root) / name
    if not path.is_file():
        raise FileNotFoundError(name)
    return path


def restore(name: str, *, include_database: bool = False, root=None) -> dict:
    """Put the dataset records back to the backup.  Refused while jobs or deletions run."""
    root = _root(root)
    path = _resolve(name, root)
    from src.workbench import jobs, resources
    from src.workbench.storage import dataset_lock

    with jobs.db() as con:
        active = con.execute("SELECT COUNT(*) FROM jobs WHERE state IN ('queued','running','cancelling')").fetchone()[0]
        busy = con.execute("SELECT COUNT(*) FROM trash_operations WHERE state IN ('preparing','running')").fetchone()[0]
    if active or busy:
        raise ValueError('有工作或垃圾桶操作正在執行，請完成或停止後再還原')
    with zipfile.ZipFile(path) as archive:
        manifest = json.loads(archive.read('backup.json'))
        contents = {}
        for rel, expected in manifest['files'].items():
            parts = PurePosixPath(rel).parts
            if rel.startswith('/') or '..' in parts or not parts:
                raise ValueError('備份內容路徑不安全：' + rel)
            data = archive.read(rel)
            if _sha(data) != expected:
                raise ValueError('備份檔案內容與紀錄不符，已停止還原：' + rel)
            contents[rel] = data
        database = (
            archive.read('runtime/workbench/workbench.sqlite3')
            if include_database and manifest.get('database')
            else None
        )
        if database is not None and _sha(database) != manifest['database']:
            raise ValueError('備份資料庫與紀錄不符，已停止還原')
    if include_database and database is None:
        raise ValueError('此備份沒有資料庫')
    safety = create('before-restore', root)
    restored = removed = 0
    with resources.resource_lock(), dataset_lock(root):
        for folder in RESTORABLE_DIRS:
            base = root / folder
            keep = {rel for rel in contents if rel.startswith(folder)}
            for current in sorted(base.rglob('*.json')) if base.is_dir() else []:
                if current.relative_to(root).as_posix() not in keep:
                    current.unlink()  # newer than the backup; kept in the safety backup above
                    removed += 1
        for rel, data in contents.items():
            if rel.startswith(('configs/', 'models/references/')):
                continue
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=target.parent, suffix='.restore')
            with os.fdopen(fd, 'wb') as stream:
                stream.write(data)
            os.replace(tmp, target)
            restored += 1
        if database is not None:
            with tempfile.TemporaryDirectory() as tmp:
                copy = Path(tmp) / 'restore.sqlite3'
                copy.write_bytes(database)
                source = sqlite3.connect(copy)
                try:
                    live = sqlite3.connect(_database(root), timeout=15)
                    try:
                        source.backup(live)
                    finally:
                        live.close()
                finally:
                    source.close()
    from src.workbench.queries import data_index

    data_index.invalidate(root)
    data_index.request_rebuild(root)
    try:
        from src.workbench.queries.images import clear

        clear(root)
    except Exception:
        pass
    return {
        'restored': restored,
        'removed_newer_records': removed,
        'database': database is not None,
        'safety_backup': safety['name'],
    }


class Scheduler:
    """While the workbench runs, take one automatic backup a day."""

    def __init__(self, root=None, interval=600):
        self.root, self.interval = root, interval
        self.stop = threading.Event()
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self.run, daemon=True, name='workbench-backup')
        self.thread.start()

    def close(self):
        self.stop.set()
        if self.thread:
            self.thread.join(5)

    def run(self):
        self.stop.wait(60)  # let the server finish starting first
        while not self.stop.is_set():
            self.tick()
            self.stop.wait(self.interval)

    def tick(self):
        self.daily()
        self.full_backup_reminder()

    def full_backup_reminder(self):
        """Remind about the full backup (photos and models) kept on an external drive."""
        try:
            from src.workbench import full_backup

            full_backup.remind(_root(self.root))
        except Exception:
            pass  # a reminder must never stop the daily backup

    def daily(self):
        from src.workbench.notifications import add

        try:
            if not listing(self.root)['due']:
                return
            item = create('auto', self.root)
            add(
                'backup',
                '已完成每日自動備份',
                f"{item['file_count']} 個檔案",
                '#settings',
                'success',
                key='backup:' + item['name'],
            )
        except Exception as exc:
            add(
                'backup',
                '每日自動備份失敗',
                str(exc)[:300],
                '#settings',
                'error',
                key='backup-failed:' + time.strftime('%Y%m%d'),
            )
