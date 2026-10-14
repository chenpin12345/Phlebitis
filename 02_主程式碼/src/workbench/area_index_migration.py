"""Schema v5: per-area review state columns on the query projection (YOLO / classification).
Additive only; the projection is rebuilt from the manifest."""
from src.workbench.storage import file_lock
import sqlite3

def migrate(con,home):
    if con.execute('PRAGMA user_version').fetchone()[0]>=5:return
    with file_lock(home/'schema.lock'):
        if con.execute('PRAGMA user_version').fetchone()[0]>=5:return
        backup=home/'backups/before-areas-v5.sqlite3';backup.parent.mkdir(parents=True,exist_ok=True)
        if not backup.exists():
            with sqlite3.connect(backup) as target:con.backup(target)
        statements=[
            "ALTER TABLE data_index ADD COLUMN cls_state TEXT NOT NULL DEFAULT 'pending'",
            "ALTER TABLE data_index ADD COLUMN det_state TEXT NOT NULL DEFAULT 'pending'",
            'CREATE INDEX data_area_cls ON data_index(cls_state,id)',
            'CREATE INDEX data_area_det ON data_index(det_state,id)',
        ]
        con.execute('BEGIN IMMEDIATE')
        try:
            for sql in statements:con.execute(sql)
            # Existing projection rows lack area states; force a rebuild.
            con.execute("UPDATE query_meta SET value=json_set(value,'$.state','stale') WHERE name='data'")
            con.execute('PRAGMA user_version=5');con.commit()
        except BaseException:con.rollback();raise
