"""Immediate stop-use records (research consent withdrawal and similar).

Written in a short SQLite transaction that never waits for the GPU lock, the dataset
lock or file cleanup, so a withdrawal is effective even while those are busy.
Eligibility, snapshot building, split validation and training preflight all consult it.
"""
from __future__ import annotations

import time
from pathlib import Path

from src.common import ROOT


def _db(root: Path):
    from src.workbench.storage import db
    return db(Path(root) / 'runtime/workbench')


def revoke(kind: str, ident: str, reason: str, source: str, root: Path = ROOT) -> None:
    if kind not in ('image', 'sha256', 'intake', 'consent'):
        raise ValueError('Invalid revocation kind')
    with _db(root) as con:
        con.execute('INSERT OR IGNORE INTO usage_revocations(kind,ident,at,reason,source) VALUES(?,?,?,?,?)', (kind, ident, time.time(), reason, source))


def revoked(root: Path = ROOT) -> dict[str, set[str]]:
    try:
        with _db(root) as con:
            rows = con.execute('SELECT kind,ident FROM usage_revocations').fetchall()
    except Exception as exc:  # A missing table must never silently allow withdrawn data.
        raise RuntimeError('無法讀取停止使用紀錄，為安全起見暫停建立資料：' + str(exc)) from exc
    result: dict[str, set[str]] = {'image': set(), 'sha256': set(), 'intake': set(), 'consent': set()}
    for kind, ident in rows:
        result.setdefault(kind, set()).add(ident)
    return result


def is_revoked(row: dict, table: dict[str, set[str]]) -> bool:
    return row.get('image_id') in table['image'] or row.get('sha256') in table['sha256']
