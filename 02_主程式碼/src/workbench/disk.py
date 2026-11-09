"""Disk usage by area and the cleanable old work outputs (D5).

Walking 3+ GB of files takes seconds, so the scan runs in a background thread and the
endpoint returns the last result with its time.  Cleaning is never done here: the page
sends the chosen items to the trash, which applies every protection rule.
"""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path

CACHE_SECONDS = 600
_state: dict = {}
_lock = threading.Lock()


def size_of(path: Path) -> tuple[int, int]:
    """Logical bytes and file count; links are not followed."""
    total = count = 0
    stack = [path]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    try:
                        if entry.is_symlink():
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            stack.append(entry.path)
                        elif entry.is_file(follow_symlinks=False):
                            total += entry.stat(follow_symlinks=False).st_size
                            count += 1
                    except OSError:
                        continue
        except (FileNotFoundError, NotADirectoryError, PermissionError):
            continue
    return total, count


def _areas(root: Path, backup_dir: Path) -> list[dict]:
    data = root / 'data'
    from src.common import snapshot_folders

    snapshots = snapshot_folders(root)
    photos = sum(size_of(p)[0] for p in data.iterdir() if p.is_dir() and p not in snapshots) if data.is_dir() else 0
    photo_files = sum(p.stat().st_size for p in data.iterdir() if p.is_file()) if data.is_dir() else 0
    runtime = root / 'runtime'
    db_bytes = (
        sum(p.stat().st_size for p in (runtime / 'workbench').glob('*.sqlite3*') if p.is_file())
        if (runtime / 'workbench').is_dir()
        else 0
    )
    # Daily zips (04_備份/工作台紀錄 or the configured folder) and the copies taken before changes
    # (04_備份/修改前副本).  Older installations kept them under runtime/; those are counted too.
    from src.common import backup_root, inbox_root

    backup_parts = {backup_dir, backup_root(root) / '修改前副本', runtime / 'backups', runtime / 'workbench/backups'}
    backups = sum(size_of(p)[0] for p in backup_parts)
    runtime_total = size_of(runtime)[0]
    inside_runtime_backups = sum(size_of(p)[0] for p in backup_parts if p.resolve().is_relative_to(runtime.resolve()))
    rows = [
        ('photos', '照片與標註', photos + photo_files, 'data（不含資料快照）'),
        ('snapshots', '資料快照', sum(size_of(p)[0] for p in snapshots), 'data/snapshots'),
        ('runs', '訓練與評估輸出', size_of(root / 'runs')[0], 'runs'),
        ('models', '模型', size_of(root / 'models')[0], 'models（版本與預訓練權重）'),
        ('backups', '備份', backups, '04_備份（不含外接硬碟）'),
        ('database', '資料庫', db_bytes, 'runtime/workbench/*.sqlite3'),
        (
            'other',
            '暫存與其他',
            max(0, runtime_total - db_bytes - inside_runtime_backups) + size_of(inbox_root(root))[0],
            'runtime 暫存、05_匯入區',
        ),
        ('archive', '原始資料封存', size_of(root / 'archive')[0], 'archive（只讀封存，不提供清理）'),
    ]
    return [{'key': k, 'name': n, 'bytes': b, 'note': note} for k, n, b, note in rows]


def _cleanable(root: Path) -> list[dict]:
    from src.workbench import jobs, registry, resources
    from src.common import read_json

    refs = set()
    for target in ('local', 'line'):
        path = registry.REFS / (target + '.json')
        node = read_json(path) if path.exists() else None
        while node:
            refs.add(node.get('artifact'))
            node = node.get('previous')
    protected_jobs = set()
    for meta in registry.metadata_listing(include_trashed=True):
        if meta['id'] in refs:
            protected_jobs.add(meta.get('experiment'))
    now = time.time()
    items = []
    for job in jobs.listing(limit=None):
        if job['state'] not in jobs.TERMINAL or job['id'] in protected_jobs:
            continue
        age = now - (job['updated'] or job['created'] or now)
        if job['state'] != 'succeeded':
            reason = {'failed': '失敗的工作', 'cancelled': '已取消的工作', 'interrupted': '中斷的工作'}[job['state']]
        elif job['kind'] in ('predict', 'regression'):
            reason = '模擬預測或回歸測試的暫存輸出'
        elif age > 30 * 86400:
            reason = '完成超過 30 天的工作'
        else:
            continue
        size, files = size_of(jobs.folder(job['id']))
        evaluation = root / 'runs/workbench/evaluations' / job['id']
        if evaluation.is_dir():
            size += size_of(evaluation)[0]
        cfg = job['config']
        items.append(
            {
                'type': 'job',
                'id': job['id'],
                'name': cfg.get('name') or cfg.get('model') or cfg.get('artifact') or job['kind'],
                'kind': job['kind'],
                'state': job['state'],
                'updated': job['updated'],
                'bytes': size,
                'files': files,
                'reason': reason,
            }
        )
    from src.workbench.trash import LEGACY_RUN

    states = resources.states('legacy_run')
    runs = root / 'runs'
    for path in sorted(runs.iterdir()) if runs.is_dir() else []:
        if path.is_dir() and LEGACY_RUN.match(path.name) and states.get(path.name, 'active') == 'active':
            size, files = size_of(path)
            items.append(
                {
                    'type': 'legacy_run',
                    'id': path.name,
                    'name': path.name,
                    'kind': 'legacy',
                    'state': 'succeeded',
                    'updated': path.stat().st_mtime,
                    'bytes': size,
                    'files': files,
                    'reason': '舊版工作台產生的歷史輸出',
                }
            )
    items.sort(key=lambda x: x['bytes'], reverse=True)
    return items[:100]


def _scan(root: Path, backup_dir: Path, key: str) -> None:
    try:
        started = time.time()
        free = None
        try:
            import shutil

            usage = shutil.disk_usage(root)
            free = {'total': usage.total, 'free': usage.free}
        except OSError:
            pass
        result = {
            'state': 'ready',
            'areas': _areas(root, backup_dir),
            'cleanable': _cleanable(root),
            'disk': free,
            'calculated_at': time.time(),
            'elapsed': round(time.time() - started, 2),
        }
    except Exception as exc:
        result = {'state': 'failed', 'error': str(exc), 'calculated_at': time.time()}
    with _lock:
        _state[key] = result


def usage(root: Path, refresh: bool = False) -> dict:
    from src.workbench import backup

    backup_dir = backup.directory(root)
    key = str(Path(root).resolve())
    with _lock:
        current = _state.get(key)
        running = current and current.get('state') == 'calculating'
        stale = (
            not current
            or current.get('state') == 'failed'
            or time.time() - current.get('calculated_at', 0) > CACHE_SECONDS
        )
        if (refresh or stale) and not running:
            _state[key] = {**(current or {}), 'state': 'calculating', 'previous_state': (current or {}).get('state')}
            threading.Thread(target=_scan, args=(Path(root), backup_dir, key), daemon=True, name='disk-usage').start()
        result = dict(_state[key])
    return result


def trash_release(root: Path | None = None) -> int:
    """Estimated bytes that permanently deleting the trash would release (D2 reminder)."""
    import json
    from src.workbench import jobs

    with jobs.db() as con:
        rows = con.execute("SELECT capacity FROM resource_lifecycle WHERE state='trashed'").fetchall()
    total = 0
    for row in rows:
        try:
            total += int((json.loads(row[0]) if row[0] else {}).get('estimated_release_bytes') or 0)
        except (ValueError, TypeError):
            continue
    return total
