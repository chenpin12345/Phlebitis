from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from src.common import ROOT, write_json

HOME = ROOT / 'runtime/workbench'
operator = ContextVar('workbench_operator', default=None)

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()).hexdigest()

@contextmanager
def file_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as f:
        f.seek(0, 2)
        if f.tell() == 0:
            f.write(b'0'); f.flush()
        f.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise RuntimeError('資源正在使用，請稍後重試。') from exc
        try: yield
        finally:
            f.seek(0)
            if os.name == 'nt': msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else: fcntl.flock(f.fileno(), fcntl.LOCK_UN)

@contextmanager
def dataset_lock(root=ROOT):
    """Serialize reads and writes of manifest/annotations with a bounded wait."""
    deadline=time.monotonic()+5
    while True:
        lock=file_lock(root/'runtime/data.lock')
        try:
            lock.__enter__()
            break
        except RuntimeError:
            if time.monotonic()>=deadline: raise
            time.sleep(.02)
    try: yield
    finally: lock.__exit__(None,None,None)

@contextmanager
def db(home=HOME):
    home.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(home / 'workbench.sqlite3', timeout=15)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA journal_mode=WAL')
    con.executescript('''
    CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, idem TEXT UNIQUE, kind TEXT, state TEXT, config TEXT, created REAL, updated REAL, pid INTEGER, born REAL, error TEXT);
    CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, at REAL, actor TEXT, action TEXT, detail TEXT);
    CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY, session TEXT, message TEXT, status TEXT, payload TEXT, updated REAL);
    CREATE TABLE IF NOT EXISTS tombstones(session TEXT, message TEXT, expires REAL, PRIMARY KEY(session,message));
    CREATE TABLE IF NOT EXISTS assets(id TEXT PRIMARY KEY, category TEXT, path TEXT, created REAL, expires REAL, metadata TEXT);
    CREATE TABLE IF NOT EXISTS cases(id TEXT PRIMARY KEY, revision INTEGER, data TEXT);
    CREATE TABLE IF NOT EXISTS flags(id TEXT PRIMARY KEY, data TEXT);
    ''')
    from src.workbench.migrations import migrate
    migrate(con, home)
    try:
        yield con
        con.commit()
    except BaseException:
        con.rollback(); raise
    finally: con.close()

def audit(action, detail, home=HOME, *, actor=None, outcome=None):
    detail = dict(detail)
    detail['_audit'] = {'schema_version':2, 'outcome':outcome or ('submitted' if action=='enqueue' else 'succeeded'), 'identity':'self_declared' if actor or operator.get() else 'unrecorded'}
    from src.workbench.views import redact
    with db(home) as con:
        con.execute('INSERT INTO audit(at,actor,action,detail) VALUES(?,?,?,?)', (time.time(), actor or operator.get() or 'local_operator', action, json.dumps(redact(detail), ensure_ascii=False)))

def flag(key, value=None):
    with db() as con:
        if value is not None:
            con.execute('INSERT OR REPLACE INTO flags VALUES(?,?)', (key, json.dumps(value, ensure_ascii=False)))
        row = con.execute('SELECT data FROM flags WHERE id=?', (key,)).fetchone()
        return json.loads(row[0]) if row else None
