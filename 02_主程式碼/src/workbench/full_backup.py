"""Full backup of photos, models and records to a folder of the user's choice (external drive).

The daily backup (backup.py) keeps only the small records.  This module copies everything
that cannot be rebuilt: photos and annotations (data/), model weights (models/), the original
source copies (archive/), the import area (05_匯入區, including the 岡山高醫 originals), the
workbench database, configs and the daily record zips.  runs/ is optional.

Layout inside the chosen folder:

    靜脈炎完整備份/目前檔案/<area>/...        the latest copy of every file
    靜脈炎完整備份/舊版本/<run>/<area>/...    files that run replaced or that were deleted
    靜脈炎完整備份/清單/<run>.json            every file of that run with size and SHA-256
    靜脈炎完整備份/清理紀錄.json              what retention removed and when

Each run copies only new or changed files.  Before a file in 目前檔案 is replaced or removed,
the old copy is moved to 舊版本/<run>, so any run within the retention period can be restored.
A run counts only once its 清單 file is written; an interrupted run is resumed by the next one
under the same run name.

Retention (default 30 days) runs only after a successful run: 舊版本/<run> folders and 清單
files whose recorded finish time is older than the limit are removed, after checking that the
folder has the system's name format, has a 清單, lies inside 舊版本, contains no links or
junctions and is not dated in the future.  目前檔案 is never touched by retention.  Restoring a
run needs only the 舊版本 folders of later runs, so every run inside the limit stays complete.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sqlite3
import tempfile
import threading
import time
from pathlib import Path

from src.common import STORE_ROOT, backup_root, code_path, inbox_root, read_json, write_json

BASE_NAME = '靜脈炎完整備份'
CURRENT, OLD, LISTS = '目前檔案', '舊版本', '清單'
PRUNE_LOG = '清理紀錄.json'
RUNNING = '執行中.json'
RUN_NAME = re.compile(r'^\d{8}-\d{6}$')
STATUS_KEY = 'full_backup_status'
SCHEMA = 1
SKIP_SUFFIXES = ('.lock', '.partial', '.tmp', '.restore')
SKIP_NAMES = {'Thumbs.db', 'desktop.ini', '__pycache__'}
# Copies of the 岡山高醫 photos made while importing them; the originals are backed up from 05.
SKIP_RUNTIME_IMPORTS = {'staging', 'external', 'cache'}

_thread: threading.Thread | None = None
_progress: dict = {'state': 'idle'}
_mutex = threading.Lock()


# ---------------------------------------------------------------- settings and status


def _settings():
    from src.workbench import settings

    return settings.load().full_backup


def load_status() -> dict:
    from src.workbench import jobs

    with jobs.db() as con:
        row = con.execute('SELECT data FROM flags WHERE id=?', (STATUS_KEY,)).fetchone()
    try:
        return json.loads(row[0]) if row else {}
    except ValueError:
        return {}


def _save_status(**changes) -> dict:
    from src.workbench import jobs

    status = {**load_status(), **changes}
    with jobs.db() as con:
        con.execute(
            'INSERT OR REPLACE INTO flags(id,data) VALUES(?,?)', (STATUS_KEY, json.dumps(status, ensure_ascii=False))
        )
    return status


def base_folder(directory: str | Path) -> Path:
    return Path(directory) / BASE_NAME


def same_drive(directory: str | Path, root: Path) -> bool:
    return Path(directory).resolve().drive.lower() == Path(root).resolve().drive.lower()


# ---------------------------------------------------------------- what is backed up


def sources(root: Path, include_runs: bool) -> list[tuple[str, Path, set[str]]]:
    """(area name inside the backup, source folder, skipped child folder names)."""
    from src.workbench import backup

    items = [
        ('data', root / 'data', set()),
        ('models', root / 'models', set()),
        ('archive', root / 'archive', set()),
        ('configs', code_path('configs', root), set()),
        ('匯入區', inbox_root(root), set()),
        ('工作台紀錄', backup.directory(root), set()),
        ('runtime/imports', root / 'runtime/imports', SKIP_RUNTIME_IMPORTS),
    ]
    if include_runs:
        items.append(('runs', root / 'runs', set()))
    return items


def _is_link(path: Path) -> bool:
    return path.is_symlink() or bool(getattr(path, 'is_junction', lambda: False)())


def _long(path: Path) -> Path:
    """Windows extended-length form of an absolute path.  The Hugging Face cache under
    models/pretrained is deep; below a backup folder it easily passes the 260-character limit."""
    if os.name != 'nt':
        return Path(path)
    text = str(Path(path).resolve())
    if text.startswith('\\\\?\\'):
        return Path(text)
    if text.startswith('\\\\'):  # network share \\server\share
        return Path('\\\\?\\UNC\\' + text[2:])
    return Path('\\\\?\\' + text)


def _walk(area: str, folder: Path, skipped: set[str]):
    if not folder.is_dir() or _is_link(folder):
        return
    folder = _long(folder)
    for directory, dirs, files in os.walk(folder, followlinks=False):
        here = Path(directory)
        keep = []
        for name in dirs:
            if name in SKIP_NAMES or _is_link(here / name):
                continue
            if here == folder and name in skipped:
                continue
            keep.append(name)
        dirs[:] = keep
        for name in files:
            if name in SKIP_NAMES or name.endswith(SKIP_SUFFIXES):
                continue
            path = here / name
            if _is_link(path):
                continue
            yield area + '/' + path.relative_to(folder).as_posix(), path


def _check_target(base: Path, root: Path, include_runs: bool) -> None:
    resolved = base.resolve()
    for _, folder, _ in sources(root, include_runs):
        if folder.exists() and resolved.is_relative_to(folder.resolve()):
            raise ValueError('完整備份位置不能放在要備份的資料夾裡面，請選擇外接硬碟或其他資料夾')
    if resolved.is_relative_to(Path(root).resolve()):
        raise ValueError('完整備份位置不能放在資料區裡面，請選擇外接硬碟或其他資料夾')


# ---------------------------------------------------------------- file helpers


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def _copy(source: Path, target: Path) -> str:
    """Copy through a .partial file; the copy on disk is read back and must match."""
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + '.partial')
    h = hashlib.sha256()
    try:
        with source.open('rb') as src, partial.open('wb') as dst:
            for block in iter(lambda: src.read(1024 * 1024), b''):
                h.update(block)
                dst.write(block)
        digest = h.hexdigest()
        if sha256_file(partial) != digest:
            raise OSError('寫入備份後讀回的內容不符：' + target.name)
        stat = source.stat()
        os.utime(partial, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        os.replace(partial, target)
        return digest
    finally:
        partial.unlink(missing_ok=True)


def _move_to_old(base: Path, run: str, rel: str) -> None:
    current = base / CURRENT / rel
    if not current.exists():
        return
    old = base / OLD / run / rel
    old.parent.mkdir(parents=True, exist_ok=True)
    if old.exists():  # resumed run: the version from before this run is already kept
        current.unlink()
        return
    os.replace(current, old)


def _manifests(base: Path) -> dict[str, dict]:
    result = {}
    folder = base / LISTS
    for path in sorted(folder.glob('*.json')) if folder.is_dir() else []:
        if RUN_NAME.match(path.stem):
            try:
                result[path.stem] = read_json(path)
            except (OSError, ValueError):
                continue
    return result


def _snapshot_database(root: Path, folder: Path) -> Path | None:
    from src.workbench import backup

    db_path = backup._database(root)
    if not db_path.is_file():
        return None
    copy = folder / 'workbench.sqlite3'
    source = sqlite3.connect(db_path, timeout=15)
    try:
        target = sqlite3.connect(copy)
        try:
            source.backup(target)
        finally:
            target.close()
    finally:
        source.close()
    return copy


# ---------------------------------------------------------------- one backup run


def run(root: Path | None = None, *, now: float | None = None, progress: dict | None = None) -> dict:
    """Run one full backup into the configured folder and apply retention afterwards."""
    from src import common
    from src.workbench.storage import file_lock

    root = Path(root) if root else common.ROOT
    cfg = _settings()
    if not cfg.directory:
        raise ValueError('尚未設定完整備份位置；請在設定頁填入外接硬碟上的資料夾')
    target_dir = Path(cfg.directory)
    if not target_dir.is_dir():
        raise FileNotFoundError('找不到完整備份位置，請確認外接硬碟已接上：' + str(target_dir))
    base = base_folder(target_dir)
    _check_target(base, root, cfg.include_runs)
    base = _long(base)
    progress = progress if progress is not None else {}
    base.mkdir(exist_ok=True)
    with file_lock(base / '.lock'):
        marker = base / RUNNING
        resumed = marker.is_file()
        run_name = read_json(marker)['run'] if resumed else time.strftime('%Y%m%d-%H%M%S', time.localtime(now))
        if not RUN_NAME.match(run_name):
            raise ValueError('執行中標記內容無效：' + str(marker))
        if not resumed and (base / LISTS / (run_name + '.json')).exists():
            raise ValueError('上一次完整備份剛完成，請稍候一秒再試')
        write_json(marker, {'run': run_name, 'started': time.time()})
        manifests = _manifests(base)
        previous = manifests[max(manifests)]['files'] if manifests else {}
        files: dict[str, list] = {}
        copied = moved = 0
        copied_bytes = 0
        progress.update(phase='整理檔案清單', files_done=0, files_total=0)
        with tempfile.TemporaryDirectory() as tmp:
            entries = [
                (rel, path)
                for area, folder, skipped in sources(root, cfg.include_runs)
                for rel, path in _walk(area, folder, skipped)
            ]
            database = _snapshot_database(root, Path(tmp))
            if database:
                entries.append(('database/workbench.sqlite3', database))
            progress.update(phase='複製新增與變更的檔案', files_total=len(entries))
            for rel, path in entries:
                try:
                    stat = path.stat()
                except FileNotFoundError:
                    continue  # removed while the backup was running; the next run records it
                current = base / CURRENT / rel
                known = previous.get(rel)
                if known and known[0] == stat.st_size and known[1] == stat.st_mtime_ns and current.is_file():
                    if current.stat().st_size == stat.st_size:
                        files[rel] = known
                        progress['files_done'] = progress.get('files_done', 0) + 1
                        continue
                digest = sha256_file(path)
                if current.is_file():
                    same = (
                        known[2] == digest
                        if known and current.stat().st_size == known[0]
                        else sha256_file(current) == digest
                    )
                    if same:
                        files[rel] = [stat.st_size, stat.st_mtime_ns, digest]
                        progress['files_done'] = progress.get('files_done', 0) + 1
                        continue
                    _move_to_old(base, run_name, rel)
                    moved += 1
                digest = _copy(path, current)
                files[rel] = [stat.st_size, stat.st_mtime_ns, digest]
                copied += 1
                copied_bytes += stat.st_size
                progress['files_done'] = progress.get('files_done', 0) + 1
        progress.update(phase='保存已刪除檔案的舊版本')
        for rel in sorted(set(previous) - set(files)):
            if (base / CURRENT / rel).exists():
                _move_to_old(base, run_name, rel)
                moved += 1
        finished = time.time() if now is None else now
        manifest = {
            'schema_version': SCHEMA,
            'run': run_name,
            'finished': finished,
            'resumed': resumed,
            'include_runs': cfg.include_runs,
            'copied': copied,
            'copied_bytes': copied_bytes,
            'moved_to_old': moved,
            'total_files': len(files),
            'total_bytes': sum(v[0] for v in files.values()),
            'files': files,
        }
        write_json(base / LISTS / (run_name + '.json'), manifest)
        marker.unlink(missing_ok=True)
        progress.update(phase='清理超過保留天數的舊版本')
        pruned = prune(base, cfg.keep_days, now=finished)
    summary = {k: v for k, v in manifest.items() if k != 'files'}
    summary['pruned'] = pruned
    _save_status(
        last_success=finished, last_run=run_name, last_summary=summary, last_error=None, directory=str(target_dir)
    )
    return summary


# ---------------------------------------------------------------- retention


def _has_links(folder: Path) -> bool:
    for directory, dirs, files in os.walk(folder, followlinks=False):
        here = Path(directory)
        if any(_is_link(here / name) for name in dirs + files):
            return True
    return False


def prune(base: Path, keep_days: int, *, now: float | None = None) -> dict:
    """Remove 舊版本/<run> and 清單/<run>.json older than keep_days.  Called after a successful run."""
    now = time.time() if now is None else now
    cutoff = now - keep_days * 86400
    manifests = _manifests(base)
    newest = max(manifests) if manifests else None
    old_root = (base / OLD).resolve()
    removed, skipped, freed = [], [], 0
    for folder in sorted((base / OLD).iterdir()) if (base / OLD).is_dir() else []:
        name = folder.name
        manifest = manifests.get(name)
        if not RUN_NAME.match(name) or manifest is None:
            skipped.append({'folder': name, 'reason': '名稱格式不符或沒有對應清單'})
            continue
        if _is_link(folder) or not folder.resolve().is_relative_to(old_root):
            skipped.append({'folder': name, 'reason': '連結或位置不在舊版本內'})
            continue
        finished = manifest.get('finished', now)
        if finished > now:
            skipped.append({'folder': name, 'reason': '時間在未來（電腦時鐘可能有誤）'})
            continue
        if finished >= cutoff:
            continue
        if _has_links(folder):
            skipped.append({'folder': name, 'reason': '資料夾內含連結或 junction'})
            continue
        size = sum(p.stat().st_size for p in folder.rglob('*') if p.is_file())
        shutil.rmtree(folder)
        freed += size
        removed.append({'folder': name, 'finished': finished, 'bytes': size})
    removed_lists = []
    for name, manifest in manifests.items():
        finished = manifest.get('finished', now)
        if name == newest or finished > now or finished >= cutoff:
            continue
        (base / LISTS / (name + '.json')).unlink(missing_ok=True)
        removed_lists.append(name)
    result = {
        'at': now,
        'keep_days': keep_days,
        'removed': removed,
        'removed_lists': removed_lists,
        'skipped': skipped,
        'freed_bytes': freed,
    }
    if removed or removed_lists or skipped:
        log = base / PRUNE_LOG
        history = read_json(log) if log.is_file() else {'entries': []}
        history['entries'] = (history.get('entries', []) + [result])[-500:]
        write_json(log, history)
    return result


# ---------------------------------------------------------------- verify and restore


def verify(directory: str | Path | None = None, progress: dict | None = None) -> dict:
    """Check every file of the newest run in 目前檔案 against its SHA-256."""
    base = _long(base_folder(directory or _settings().directory))
    manifests = _manifests(base)
    if not manifests:
        raise FileNotFoundError('這個位置還沒有完整備份')
    run_name = max(manifests)
    files = manifests[run_name]['files']
    progress = progress if progress is not None else {}
    progress.update(phase='核對檔案', files_total=len(files), files_done=0)
    missing, damaged = [], []
    for rel, (size, _, digest) in files.items():
        path = base / CURRENT / rel
        if not path.is_file():
            missing.append(rel)
        elif path.stat().st_size != size or sha256_file(path) != digest:
            damaged.append(rel)
        progress['files_done'] += 1
    result = {
        'run': run_name,
        'checked': len(files),
        'missing': missing[:200],
        'damaged': damaged[:200],
        'missing_count': len(missing),
        'damaged_count': len(damaged),
        'ok': not missing and not damaged,
        'at': time.time(),
    }
    _save_status(last_verify=result)
    return result


def check_restore(run_name: str, output: str | Path, directory: str | Path | None = None) -> tuple[Path, dict, Path]:
    if not RUN_NAME.match(run_name or ''):
        raise ValueError('無效的備份時間')
    directory = directory or _settings().directory
    if not directory:
        raise ValueError('尚未設定完整備份位置')
    base = base_folder(directory)
    manifests = _manifests(base)
    if run_name not in manifests:
        raise FileNotFoundError('找不到這次備份的清單；可能已超過保留天數')
    output = Path(output)
    if not output.is_absolute():
        raise ValueError('還原位置必須是完整路徑')
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError('還原位置必須是空資料夾或尚不存在的資料夾')
    from src import common

    for protected in (base, STORE_ROOT, common.ROOT):
        if output.resolve().is_relative_to(Path(protected).resolve()):
            raise ValueError('不能還原到備份資料夾或正式資料區裡；請選擇另一個空資料夾，核對後再手動替換')
    return base, manifests, output


def restore_to(
    run_name: str, output: str | Path, directory: str | Path | None = None, progress: dict | None = None
) -> dict:
    """Rebuild the state of one run into an empty folder.  Live project data is never overwritten."""
    base, manifests, shown = check_restore(run_name, output, directory)
    base, output = _long(base), _long(shown)
    later = sorted(name for name in manifests if name > run_name)
    files = manifests[run_name]['files']
    progress = progress if progress is not None else {}
    progress.update(phase='還原檔案', files_total=len(files), files_done=0)
    missing = []
    for rel, (size, mtime_ns, digest) in files.items():
        candidates = [base / OLD / name / rel for name in later] + [base / CURRENT / rel]
        found = next(
            (c for c in candidates if c.is_file() and c.stat().st_size == size and sha256_file(c) == digest), None
        )
        if found is None:
            missing.append(rel)
        else:
            target = output / rel
            if _copy(found, target) != digest:
                raise OSError('還原後內容不符：' + rel)
            os.utime(target, ns=(mtime_ns, mtime_ns))
        progress['files_done'] += 1
    return {
        'run': run_name,
        'output': str(shown),
        'restored': len(files) - len(missing),
        'missing': missing[:200],
        'missing_count': len(missing),
    }


# ---------------------------------------------------------------- background work and overview


def start(action: str, root: Path | None = None, **kwargs) -> dict:
    """Start backup / verify / restore in a background thread; one at a time."""
    global _thread
    from src.workbench.notifications import add

    if action not in ('backup', 'verify', 'restore'):
        raise ValueError('無效的完整備份操作')
    if action == 'restore':
        check_restore(kwargs.get('run', ''), kwargs.get('output', ''))  # refuse at once, not in the background
    elif not _settings().directory:
        raise ValueError('尚未設定完整備份位置；請先在下方填入外接硬碟上的資料夾並儲存')
    with _mutex:
        if _thread and _thread.is_alive():
            raise ValueError('完整備份工作正在執行，請等它完成')
        progress = {'state': 'running', 'action': action, 'started': time.time(), 'phase': '準備中'}
        _progress.clear()
        _progress.update(progress)

        def work():
            try:
                if action == 'backup':
                    result = run(root, progress=_progress)
                    note = f"新增或更新 {result['copied']} 個檔案，共 {result['total_files']} 個"
                    pruned = result['pruned']
                    add(
                        'backup',
                        '已完成完整備份',
                        note,
                        '#settings?section=full-backup',
                        'success',
                        key='full-backup:' + result['run'],
                    )
                    if pruned['removed'] or pruned['removed_lists']:
                        add(
                            'backup',
                            f"已清除 {len(pruned['removed'])} 個超過 {pruned['keep_days']} 天的舊版本（{pruned['freed_bytes'] / 1024 ** 2:.1f} MB）",
                            '',
                            '#settings?section=full-backup',
                            'info',
                            key='full-backup-prune:' + result['run'],
                        )
                elif action == 'verify':
                    result = verify(progress=_progress)
                    add(
                        'backup',
                        '完整備份核對完成' if result['ok'] else '完整備份核對發現問題',
                        f"核對 {result['checked']} 個檔案；缺少 {result['missing_count']}、內容不符 {result['damaged_count']}",
                        '#settings?section=full-backup',
                        'success' if result['ok'] else 'error',
                    )
                else:
                    result = restore_to(kwargs['run'], kwargs['output'], progress=_progress)
                    add(
                        'backup',
                        '完整備份已還原到指定資料夾',
                        f"{result['restored']} 個檔案 → {result['output']}",
                        '#settings?section=full-backup',
                        'success' if not result['missing_count'] else 'error',
                    )
                _progress.update(state='done', result=result, finished=time.time())
            except Exception as exc:  # reported to the page and as a notice; nothing is retried silently
                message = str(exc)[:500]
                _progress.update(state='failed', error=message, finished=time.time())
                if action == 'backup':
                    _save_status(last_error={'at': time.time(), 'message': message})
                add(
                    'backup',
                    '完整備份失敗' if action == 'backup' else '完整備份操作失敗',
                    message,
                    '#settings?section=full-backup',
                    'error',
                )

        _thread = threading.Thread(target=work, daemon=True, name='full-backup-' + action)
        _thread.start()
    return dict(_progress)


def wait(timeout: float = 60) -> dict:
    """Tests and scripts: wait for the running background operation."""
    thread = _thread
    if thread:
        thread.join(timeout)
    return dict(_progress)


def overview(root: Path | None = None) -> dict:
    from src import common

    root = Path(root) if root else common.ROOT
    cfg = _settings()
    status = load_status()
    runs, available, reason = [], False, ''
    if cfg.directory:
        base = base_folder(cfg.directory)
        if Path(cfg.directory).is_dir():
            available = True
            for name, manifest in sorted(_manifests(base).items(), reverse=True):
                runs.append(
                    {
                        k: manifest.get(k)
                        for k in (
                            'run',
                            'finished',
                            'copied',
                            'copied_bytes',
                            'moved_to_old',
                            'total_files',
                            'total_bytes',
                            'resumed',
                        )
                    }
                )
        else:
            reason = '找不到備份位置（外接硬碟可能未接上）'
    last = status.get('last_success')
    return {
        'settings': cfg.model_dump(),
        'available': available,
        'reason': reason,
        'same_drive': bool(cfg.directory) and same_drive(cfg.directory, root),
        'runs': runs,
        'status': status,
        'progress': dict(_progress),
        'due': last is None or time.time() - last > cfg.remind_days * 86400,
        'last_import': last_import(root),
    }


# ---------------------------------------------------------------- reminders


def last_import(root: Path) -> float | None:
    from src.imports import service

    try:
        with service.store(root) as con:
            row = con.execute(
                "SELECT MAX(updated) FROM imports WHERE kind IN ('photos','external_photos') AND state='completed'"
            ).fetchone()
    except sqlite3.Error:
        return None
    return row[0] if row and row[0] else None


def remind(root: Path, now: float | None = None) -> list[str]:
    """Called by the daily-backup scheduler.  Returns the notice keys it tried to add."""
    from src.workbench.notifications import add

    now = time.time() if now is None else now
    cfg = _settings()
    last = load_status().get('last_success')
    keys = []
    if last is None or now - last > cfg.remind_days * 86400:
        key = 'full-backup-due:' + time.strftime('%Y%m%d', time.localtime(now))
        body = '從未做過完整備份' if last is None else f'上次完整備份已超過 {cfg.remind_days} 天'
        add(
            'backup',
            '請做一次完整備份（照片與模型）',
            body + '；請接上外接硬碟後到設定頁按「立即完整備份」。',
            '#settings?section=full-backup',
            'info',
            key=key,
        )
        keys.append(key)
    imported = last_import(root)
    if imported and (last is None or imported > last):
        key = f'full-backup-after-import:{int(imported)}'
        add(
            'backup',
            '有新匯入的照片尚未完整備份',
            '請接上外接硬碟後到設定頁按「立即完整備份」。',
            '#settings?section=full-backup',
            'info',
            key=key,
        )
        keys.append(key)
    return keys
