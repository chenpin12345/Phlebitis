"""Schema v7: the lesion detection area was removed, so its query columns go.
The projection is rebuilt from the manifest."""

import sqlite3

from src.common import database_backup
from src.workbench.storage import file_lock


def migrate(con, home):
    if con.execute('PRAGMA user_version').fetchone()[0] >= 7:
        return
    with file_lock(home / 'schema.lock'):
        if con.execute('PRAGMA user_version').fetchone()[0] >= 7:
            return
        backup = database_backup(home, 'before-single-area-v7.sqlite3')
        backup.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            with sqlite3.connect(backup) as target:
                con.backup(target)
        columns = {r[1] for r in con.execute('PRAGMA table_info(data_index)')}
        statements = ['DROP INDEX IF EXISTS data_task_detection', 'DROP INDEX IF EXISTS data_area_det']
        statements += [
            f'ALTER TABLE data_index DROP COLUMN {name}'
            for name in ('eligible_detection', 'det_state')
            if name in columns
        ]
        con.execute('BEGIN IMMEDIATE')
        try:
            for sql in statements:
                con.execute(sql)
            con.execute("UPDATE query_meta SET value=json_set(value,'$.state','stale') WHERE name='data'")
            con.execute('PRAGMA user_version=7')
            con.commit()
        except BaseException:
            con.rollback()
            raise
