"""One-off: replace the old source name in stored records (see 來源名稱統一企劃).

Default is a preview that changes nothing.  --apply packs a copy of everything it will touch,
checks every new file (reverses to the same bytes, same JSON structure apart from the name),
and only then replaces the files.  Rerunning after an interruption finishes the rest.
Run with the workbench closed.  The old name is written in pieces so that a search of the
project stays clean.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import src  # noqa: E402,F401
from src.common import OLD_SNAPSHOT_DIR, ROOT, SNAPSHOT_DIR, backup_root, stamp, write_json  # noqa: E402
from src.workbench.storage import dataset_lock  # noqa: E402

OLD_ID, NEW_ID = 'yi' + 'da', 'gangshan'
OLD_NAME, NEW_NAME = '義' + '大', '岡山高醫'
PAIRS = ((OLD_ID.encode(), NEW_ID.encode()), (OLD_NAME.encode(), NEW_NAME.encode()))
AREAS = ('data', 'runtime/imports')
SKIPPED = (OLD_SNAPSHOT_DIR, SNAPSHOT_DIR, 'runtime/imports/external', 'runtime/imports/staging')
SUFFIXES = {'.json', '.jsonl', '.csv', '.txt', '.md'}
PROGRESS = 'data/migrations/source-name-unify.progress.json'
DATABASE = 'runtime/workbench/workbench.sqlite3'
SNAPSHOT_FOLDER = '來源名稱統一前'


def renamed(data: bytes) -> bytes:
    for old, new in PAIRS:
        data = data.replace(old, new)
    return data


def restored(data: bytes) -> bytes:
    for old, new in PAIRS:
        data = data.replace(new, old)
    return data


def has_old(data: bytes) -> bool:
    return any(old in data for old, _ in PAIRS)


def has_new(data: bytes) -> bool:
    return any(new in data for _, new in PAIRS)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def text_files(root: Path) -> list[Path]:
    found = []
    for area in AREAS:
        base = root / area
        if not base.is_dir():
            continue
        for folder, names, files in os.walk(base):
            relative = Path(folder).relative_to(root).as_posix()
            names[:] = [n for n in names if f'{relative}/{n}' not in SKIPPED]
            found += [Path(folder) / f for f in files if Path(f).suffix.lower() in SUFFIXES]
    return sorted(p for p in found if p != root / PROGRESS)


def targets(root: Path) -> list[Path]:
    return [p for p in text_files(root) if has_old(p.read_bytes())]


def batch_folders(root: Path) -> list[Path]:
    base = root / 'runtime/imports/external'
    return sorted(base.glob(OLD_ID + '-*')) if base.is_dir() else []


def database_counts(root: Path) -> dict:
    path = root / DATABASE
    if not path.is_file():
        return {}
    con = sqlite3.connect(f'file:{path.as_posix()}?mode=ro', uri=True)
    try:
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        counts = {}
        for table, columns in (('imports', ('batch', 'payload')), ('data_index', ('payload',))):
            if table not in tables:
                continue
            where = ' OR '.join(f'{c} LIKE ? OR {c} LIKE ?' for c in columns)
            values = [f'%{OLD_ID}%', f'%{OLD_NAME}%'] * len(columns)
            counts[table] = con.execute(f'SELECT COUNT(*) FROM {table} WHERE {where}', values).fetchone()[0]
        return counts
    finally:
        con.close()


def preview(root: Path) -> dict:
    found = targets(root)
    return {
        'files': len(found),
        'folders': len(batch_folders(root)),
        'database': database_counts(root),
        'mixed_old_and_new': sum(has_new(p.read_bytes()) for p in found),
    }


def same_structure(old, new) -> bool:
    """Equal JSON apart from the name, including object keys."""

    def convert(value):
        if isinstance(value, str):
            return renamed(value.encode()).decode()
        if isinstance(value, list):
            return [convert(v) for v in value]
        if isinstance(value, dict):
            return {convert(k): convert(v) for k, v in value.items()}
        return value

    return convert(old) == new


def check(path: Path, before: bytes, after: bytes) -> None:
    if restored(after) != before:
        raise RuntimeError(f'無法反向還原：{path.name}')
    if has_old(after):
        raise RuntimeError(f'替換後仍有舊名：{path.name}')
    if path.suffix.lower() == '.json' and not same_structure(json.loads(before), json.loads(after)):
        raise RuntimeError(f'JSON 結構改變：{path.name}')


def snapshot(root: Path, files: list[Path]) -> Path:
    folder = backup_root(root) / '修改前副本' / SNAPSHOT_FOLDER
    folder.mkdir(parents=True, exist_ok=True)
    name = stamp()
    with zipfile.ZipFile(folder / f'records-{name}.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(root).as_posix())
    database = root / DATABASE
    if database.is_file():
        source = sqlite3.connect(database)
        target = sqlite3.connect(folder / f'workbench-{name}.sqlite3')
        try:
            source.backup(target)
        finally:
            target.close()
            source.close()
    return folder


def update_database(root: Path) -> None:
    path = root / DATABASE
    if not path.is_file():
        return

    def both(column):
        return f"replace(replace({column},'{OLD_ID}','{NEW_ID}'),'{OLD_NAME}','{NEW_NAME}')"

    con = sqlite3.connect(path)
    try:
        with con:
            tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if 'imports' in tables:
                con.execute(f"UPDATE imports SET batch={both('batch')}, payload={both('payload')}")
            if 'data_index' in tables:
                con.execute(f"UPDATE data_index SET payload={both('payload')}")
    finally:
        con.close()


def apply(root: Path, fail_after: int | None = None) -> dict:
    progress = root / PROGRESS
    with dataset_lock(root):
        resuming = progress.exists()
        files = targets(root)
        if not resuming:
            mixed = preview(root)['mixed_old_and_new']
            if mixed:
                raise RuntimeError(f'{mixed} 個紀錄同時含新舊名稱，替換後無法反向還原，請先檢查')
            snapshot(root, files)
        changes = []
        for path in files:
            before = path.read_bytes()
            after = renamed(before)
            check(path, before, after)
            changes.append((path, before, after))
        progress.parent.mkdir(parents=True, exist_ok=True)
        write_json(progress, {'started': True})
        for count, (path, _, after) in enumerate(changes):
            if fail_after is not None and count == fail_after:
                raise RuntimeError('測試用中斷')
            temporary = path.with_name(path.name + '.renaming')
            temporary.write_bytes(after)
            os.replace(temporary, path)
        folders = batch_folders(root)
        for folder in folders:
            folder.rename(folder.with_name(NEW_ID + folder.name[len(OLD_ID) :]))
        update_database(root)
        record = {
            'schema_version': 1,
            'operation': 'source_name_unify',
            'at': stamp(),
            'resumed': resuming,
            'files': [
                {'path': p.relative_to(root).as_posix(), 'before': digest(b), 'after': digest(a)} for p, b, a in changes
            ],
            'folders': len(folders),
        }
        write_json(root / f"data/migrations/source-name-unify-{record['at']}.json", record)
        progress.unlink()
    return {'files': len(changes), 'folders': len(folders)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    if not args.apply:
        print(json.dumps(preview(root), ensure_ascii=False))
        return 0
    print(json.dumps(apply(root), ensure_ascii=False))
    from src.workbench.queries import data_index

    data_index.rebuild(root)
    print(json.dumps(preview(root), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
