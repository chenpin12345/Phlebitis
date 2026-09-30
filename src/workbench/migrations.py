"""Versioned, idempotent workbench migrations. No data is discarded."""
import sqlite3
from src.workbench.storage import file_lock


def migrate(con, home):
    if con.execute('PRAGMA user_version').fetchone()[0] >= 1:
        return
    with file_lock(home / 'schema.lock'):
        if con.execute('PRAGMA user_version').fetchone()[0] >= 1:
            return
        backup = home / 'backups' / 'before-trash-v1.sqlite3'
        backup.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            with sqlite3.connect(backup) as target:
                con.backup(target)
        con.execute('BEGIN IMMEDIATE')
        try:
            sql = con.execute("SELECT sql FROM sqlite_master WHERE name='audit'").fetchone()[0]
            if 'AUTOINCREMENT' not in sql.upper():
                con.execute('ALTER TABLE audit RENAME TO audit_before_v1')
                con.execute('CREATE TABLE audit(id INTEGER PRIMARY KEY AUTOINCREMENT, at REAL, actor TEXT, action TEXT, detail TEXT)')
                con.execute('INSERT INTO audit(id,at,actor,action,detail) SELECT id,at,actor,action,detail FROM audit_before_v1')
                con.execute('DROP TABLE audit_before_v1')
            statements = [
                '''CREATE TABLE resource_lifecycle(type TEXT, id TEXT, state TEXT NOT NULL,
                    revision INTEGER NOT NULL, moved REAL, actor TEXT, summary TEXT NOT NULL,
                    capacity TEXT, operation TEXT, PRIMARY KEY(type,id))''',
                '''CREATE TABLE trash_previews(id TEXT PRIMARY KEY, session TEXT NOT NULL,
                    created REAL NOT NULL, expires REAL NOT NULL, state TEXT NOT NULL, plan TEXT NOT NULL)''',
                '''CREATE TABLE trash_operations(id TEXT PRIMARY KEY, idem TEXT UNIQUE NOT NULL,
                    fingerprint TEXT NOT NULL, action TEXT NOT NULL, state TEXT NOT NULL,
                    created REAL NOT NULL, updated REAL NOT NULL, actor TEXT, plan TEXT NOT NULL,
                    result TEXT NOT NULL)''',
                '''CREATE TABLE trash_steps(operation TEXT, type TEXT, resource TEXT, path TEXT,
                    state TEXT NOT NULL, identity TEXT, bytes INTEGER, error TEXT,
                    PRIMARY KEY(operation,type,resource,path))''',
                '''CREATE TABLE deleted_job_keys(idem TEXT PRIMARY KEY, id TEXT NOT NULL,
                    kind TEXT NOT NULL, fingerprint TEXT NOT NULL)''',
                'CREATE INDEX lifecycle_state ON resource_lifecycle(state,moved,type,id)',
            ]
            for statement in statements:
                con.execute(statement)
            con.execute('PRAGMA user_version=1')
            con.commit()
        except BaseException:
            con.rollback()
            raise
