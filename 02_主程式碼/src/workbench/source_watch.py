"""Detect new photos in the authorized external folder (岡山高醫) without importing them (A4).

Read-only: the folder is walked and files are hashed; nothing is copied, moved or
renamed.  A file is new when its content hash is neither in the manifest nor recorded as
a source alias.  Unchanged files (same size and mtime) reuse their cached hash, so a
check after the first one only stats the folder.  Importing stays the normal external
import (scan, confirm), started from the 「岡山高醫新照片」 button.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from pathlib import Path

from src.common import read_json, read_manifest, write_json
from src.data import filename_rules

CACHE = 'runtime/imports/source_watch.json'
SUFFIXES = ('.jpg', '.jpeg', '.png', '.webp')
_lock = threading.Lock()


def _source(root: Path):
    from src.imports import external

    for key, config in external.sources(root).items():
        if config.get('auto_apply'):
            return key, config
    return None, None


def _known(root: Path) -> set[str]:
    known = {r['sha256'] for r in read_manifest(root)}
    from src.data import photo_trash, sources

    known |= photo_trash.tombstones(root) | photo_trash.in_trash_hashes(root)

    for entry in sources.load(root)['images'].values():
        for alias in entry.get('aliases', []):
            if alias.get('source_sha256'):
                known.add(alias['source_sha256'])
    return known


def check(root: Path) -> dict:
    """Walk the folder (read-only) and count photos that are not in the project yet."""
    import os
    from src.imports import external

    with _lock:
        path = root / CACHE
        cache = read_json(path) if path.exists() else {}
        try:
            key, config = _source(root)
            if not key:
                state = {
                    'available': False,
                    'reason': '沒有設定自動分類的外部來源',
                    'count': 0,
                    'checked_at': time.time(),
                }
                write_json(path, {**cache, 'state': state})
                return state
            base, config = external.source_base(root, key)
        except (OSError, ValueError, KeyError) as exc:
            state = {
                'available': False,
                'reason': str(exc).replace(str(root), '專案'),
                'count': 0,
                'checked_at': time.time(),
            }
            write_json(path, {**cache, 'state': state})
            return state
        hashes = cache.get('hashes', {}) if cache.get('source') == key else {}
        seen, new = {}, []
        known = _known(root)
        for directory, dirs, names in os.walk(base, followlinks=False):
            dirs[:] = [d for d in dirs if not (Path(directory) / d).is_symlink()]
            for name in names:
                file = Path(directory) / name
                if file.suffix.lower() not in SUFFIXES or file.is_symlink():
                    continue
                rel = file.relative_to(base).as_posix()
                if not filename_rules.is_standard(rel):
                    continue  # the import refuses these names, so they are not new photos
                try:
                    stat = file.stat()
                except OSError:
                    continue
                stamp = [stat.st_size, stat.st_mtime_ns]
                cached = hashes.get(rel)
                if cached and cached['stat'] == stamp:
                    digest = cached['sha256']
                else:
                    h = hashlib.sha256()
                    try:
                        with file.open('rb') as stream:
                            for block in iter(lambda: stream.read(1024 * 1024), b''):
                                h.update(block)
                    except OSError:
                        continue
                    digest = h.hexdigest()
                seen[rel] = {'stat': stamp, 'sha256': digest}
                if digest not in known:
                    new.append(rel)
                if len(seen) > 5000:
                    break
        new.sort()
        signature = hashlib.sha256(json.dumps(new, ensure_ascii=False).encode()).hexdigest()[:16]
        state = {
            'available': True,
            'source': key,
            'source_name': config.get('name', key),
            'count': len(new),
            'files': new[:20],
            'total_files': len(seen),
            'checked_at': time.time(),
            'signature': signature,
        }
        write_json(path, {'source': key, 'hashes': seen, 'state': state})
        return state


def cached(root: Path) -> dict:
    path = root / CACHE
    if path.exists():
        try:
            return read_json(path).get('state') or {'count': 0}
        except (OSError, ValueError):
            pass
    return {'count': 0, 'available': None}


class Watcher:
    """Re-check every few minutes while the workbench is open; notify once per new set."""

    def __init__(self, root: Path, interval: int = 300):
        self.root, self.interval = Path(root), interval
        self.stop = threading.Event()
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self.run, daemon=True, name='source-watch')
        self.thread.start()

    def close(self):
        self.stop.set()
        if self.thread:
            self.thread.join(5)

    def run(self):
        self.stop.wait(30)
        while not self.stop.is_set():
            self.tick()
            self.stop.wait(self.interval)

    def tick(self):
        try:
            state = check(self.root)
        except Exception:
            return
        if state.get('count'):
            from src.workbench.notifications import add

            add(
                'new_photos',
                f"岡山高醫資料夾有 {state['count']} 張新照片",
                '到資料審查按「岡山高醫新照片」比對並匯入。',
                '#data?area=cls&source_new=1',
                'info',
                key='source-watch:' + state['signature'],
            )
