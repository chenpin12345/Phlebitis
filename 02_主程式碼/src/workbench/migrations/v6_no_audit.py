"""Schema v6: the operation-audit feature is retired (project owner decision, 2026-10-16).

Trash actions are traced by trash_operations (管理操作紀錄); data reviews by data/reviews/*.json;
jobs by the jobs table. Existing audit rows, their trash lifecycle rows, operations that only
touched audit rows, and every cached preview are removed. A full backup is taken first."""

import sqlite3
from src.workbench.storage import file_lock
from src.common import database_backup


def migrate(con, home):
    if con.execute('PRAGMA user_version').fetchone()[0] >= 6:
        return
    with file_lock(home / 'schema.lock'):
        if con.execute('PRAGMA user_version').fetchone()[0] >= 6:
            return
        backup = database_backup(home, 'before-no-audit-v6.sqlite3')
        backup.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            with sqlite3.connect(backup) as target:
                con.backup(target)
        con.execute('BEGIN IMMEDIATE')
        try:
            con.execute('DELETE FROM audit')
            con.execute("DELETE FROM resource_lifecycle WHERE type='audit'")
            audit_only = [
                r[0]
                for r in con.execute(
                    "SELECT id FROM trash_operations o WHERE NOT EXISTS (SELECT 1 FROM json_each(o.plan,'$.targets') t "
                    "WHERE json_extract(t.value,'$.type')!='audit')"
                )
            ]
            for ident in audit_only:
                con.execute('DELETE FROM trash_steps WHERE operation=?', (ident,))
                con.execute('DELETE FROM trash_operations WHERE id=?', (ident,))
            con.execute('DELETE FROM trash_previews')  # previews are short-lived caches (5 minutes)
            con.execute('PRAGMA user_version=6')
            con.commit()
        except BaseException:
            con.rollback()
            raise
