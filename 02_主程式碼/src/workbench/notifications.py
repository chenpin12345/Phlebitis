"""Completion notices shown under the bell in the page header (D3).

Producers: finished training/evaluation/weight jobs, trash operations, new photos in the
岡山高醫 folder and automatic backups.  A notice is only a pointer; it never changes data.
`key` makes a producer idempotent (the same event is recorded once).
"""

from __future__ import annotations

import time

KEEP = 500


def _db(home=None):
    """Notices live next to the jobs table, so tests that isolate jobs.db isolate notices too."""
    from src.workbench import jobs, storage

    return storage.db(home) if home else jobs.db()


LEVELS = ('info', 'success', 'error')


def _ensure(con):
    con.execute(
        'CREATE TABLE IF NOT EXISTS notifications(id INTEGER PRIMARY KEY, at REAL, kind TEXT, level TEXT, title TEXT, body TEXT, href TEXT, key TEXT UNIQUE, read INTEGER NOT NULL DEFAULT 0)'
    )


def add(
    kind: str, title: str, body: str = '', href: str = '', level: str = 'info', key: str | None = None, home=None
) -> None:
    """Never raises: a failed notice must not fail the work it reports."""
    try:
        with _db(home) as con:
            _ensure(con)
            con.execute(
                'INSERT OR IGNORE INTO notifications(at,kind,level,title,body,href,key) VALUES(?,?,?,?,?,?,?)',
                (time.time(), kind, level if level in LEVELS else 'info', title[:200], body[:1000], href[:300], key),
            )
            con.execute(
                'DELETE FROM notifications WHERE id NOT IN (SELECT id FROM notifications ORDER BY id DESC LIMIT ?)',
                (KEEP,),
            )
    except Exception:
        pass


def listing(limit: int = 30) -> dict:
    if not 1 <= limit <= 100:
        raise ValueError('無效的筆數')
    with _db() as con:
        _ensure(con)
        items = [
            dict(r)
            for r in con.execute(
                'SELECT id,at,kind,level,title,body,href,read FROM notifications ORDER BY id DESC LIMIT ?', (limit,)
            )
        ]
        unread = con.execute('SELECT COUNT(*) FROM notifications WHERE read=0').fetchone()[0]
        latest = con.execute('SELECT MAX(id) FROM notifications').fetchone()[0] or 0
    for item in items:
        item['read'] = bool(item['read'])
    return {'items': items, 'unread': unread, 'latest': latest}


def mark_read(ids: list[int] | None = None) -> dict:
    with _db() as con:
        _ensure(con)
        if ids is None:
            con.execute('UPDATE notifications SET read=1 WHERE read=0')
        else:
            con.execute(
                'UPDATE notifications SET read=1 WHERE id IN (SELECT value FROM json_each(?))',
                (__import__('json').dumps([int(i) for i in ids]),),
            )
    return listing()


JOB_NAMES = {'train': '訓練', 'evaluate': '評估', 'prepare': '權重準備'}


def job_finished(ident: str, kind: str, state: str, config: dict, error: str | None) -> None:
    """Called from jobs.update when a job reaches a terminal state."""
    if kind not in JOB_NAMES or state not in ('succeeded', 'failed', 'interrupted'):
        return
    label = config.get('name') or config.get('model') or config.get('artifact') or ident[:8]
    ok = state == 'succeeded'
    title = f"{JOB_NAMES[kind]}{'完成' if ok else '失敗' if state == 'failed' else '中斷'}：{label}"
    body = '' if ok else (error or '')[:300]
    add('job', title, body, '#models?tab=jobs&job=' + ident, 'success' if ok else 'error', key=f'job:{ident}:{state}')


TRASH_NAMES = {'move': '移至垃圾桶', 'restore': '還原', 'purge': '永久刪除'}


def trash_finished(ident: str, action: str, results: list[dict]) -> None:
    ok = sum(r.get('state') == 'succeeded' for r in results)
    bad = sum(r.get('state') == 'failed' for r in results)
    title = f"{TRASH_NAMES.get(action, '垃圾桶操作')}{'完成' if not bad else '未全部完成'}：{ok} 項" + (
        f'，{bad} 項失敗' if bad else ''
    )
    add('trash', title, '', '#trash', 'success' if not bad else 'error', key=f'trash:{ident}')
