"""Prospective patient lists (#21, #22): decide what a new patient is for before seeing results.

A list is sealed with a hash when it is registered.  `development` patients may be trained on;
`test` and `calibration` patients never enter a training snapshot.  A list can be unlocked once,
and that is written to the experiment ledger.  Only hashed patient keys are stored.
"""

from __future__ import annotations

from pathlib import Path

from src.common import ROOT, read_json, stamp, write_json
from src.data import tasks

FOLDER = 'data/prospective'
ROLES = {'development': '開發', 'test': '測試', 'calibration': '校準'}


def _digest(role: str, patients: list[str]) -> str:
    from src.workbench.storage import digest

    return digest({'role': role, 'patients': sorted(patients)})


def _normalize(code: str) -> str:
    return code.strip().replace('-', '').upper()


def _files(root: Path) -> list[Path]:
    folder = root / FOLDER
    return sorted(folder.glob('*.json')) if folder.exists() else []


def listing(root: Path = ROOT) -> list[dict]:
    return [
        {
            **{k: v for k, v in read_json(p).items() if k != 'patients'},
            'count': len(read_json(p)['patients']),
            'role_name': ROLES[read_json(p)['role']],
        }
        for p in _files(root)
    ]


def reserved(root: Path = ROOT) -> set[str]:
    """Patient keys that training snapshots must leave out, unlocked or not."""
    return {key for p in _files(root) for key in read_json(p)['patients'] if read_json(p)['role'] != 'development'}


def register(name: str, codes: list[str], role: str, by: str, root: Path = ROOT) -> dict:
    from src.workbench import ledger
    from src.workbench.storage import dataset_lock

    if role not in ROLES:
        raise ValueError('角色必須是開發、測試或校準')
    if not name.strip() or not by.strip():
        raise ValueError('請填名單名稱，並先設定操作者名稱')
    normal = sorted({_normalize(c) for c in codes if c.strip()})
    if not normal:
        raise ValueError('名單沒有病人')
    keys = [tasks.group_key({'subject_id': code}) for code in normal]
    with dataset_lock(root):
        taken = {key for p in _files(root) for key in read_json(p)['patients']}
        if set(keys) & taken:
            raise ValueError(f'{len(set(keys) & taken)} 位病人已在其他名單，一位病人只能有一個角色')
        ident = f'list-{len(_files(root)) + 1:04d}'
        entry = {
            'schema_version': 1,
            'id': ident,
            'name': ' '.join(name.split())[:60],
            'role': role,
            'patients': sorted(keys),
            'sealed': _digest(role, keys),
            'registered_by': by.strip(),
            'registered_at': stamp(),
            'unlocked_at': None,
            'unlocked_by': None,
        }
        write_json(root / FOLDER / f'{ident}.json', entry)
    ledger.append(root, {'event': 'prospective_sealed', 'list': ident, 'role': role, 'sealed': entry['sealed']})
    return next(x for x in listing(root) if x['id'] == ident)


def unlock(ident: str, by: str, root: Path = ROOT) -> dict:
    from src.workbench import ledger
    from src.workbench.storage import dataset_lock

    if not by.strip():
        raise ValueError('請先設定操作者名稱')
    path = root / FOLDER / f'{ident}.json'
    if not path.resolve().is_relative_to((root / FOLDER).resolve()) or not path.exists():
        raise FileNotFoundError(ident)
    with dataset_lock(root):
        entry = read_json(path)
        if entry['unlocked_at']:
            raise ValueError('這份名單已解鎖過，不能再解鎖')
        if _digest(entry['role'], entry['patients']) != entry['sealed']:
            raise ValueError('名單內容和封存雜湊不符，已停止解鎖')
        entry.update(unlocked_at=stamp(), unlocked_by=by.strip())
        write_json(path, entry)
    ledger.append(root, {'event': 'prospective_unlocked', 'list': ident, 'sealed': entry['sealed'], 'by': by.strip()})
    return next(x for x in listing(root) if x['id'] == ident)
