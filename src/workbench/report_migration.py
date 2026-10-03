"""Normalized report summary/sample projection; source reports remain unchanged."""
from src.workbench.storage import file_lock
import sqlite3

def migrate(con,home):
    if con.execute('PRAGMA user_version').fetchone()[0]>=3:return
    with file_lock(home/'schema.lock'):
        if con.execute('PRAGMA user_version').fetchone()[0]>=3:return
        backup=home/'backups/before-report-v3.sqlite3';backup.parent.mkdir(parents=True,exist_ok=True)
        if not backup.exists():
            with sqlite3.connect(backup) as target:con.backup(target)
        con.execute('BEGIN IMMEDIATE')
        try:
            con.execute('CREATE TABLE report_index(id TEXT PRIMARY KEY,path TEXT UNIQUE,signature TEXT,model TEXT,artifact TEXT,evaluated TEXT,payload TEXT)')
            con.execute('CREATE INDEX report_model_time ON report_index(model,evaluated DESC,id DESC)')
            con.execute('CREATE TABLE report_samples(report TEXT,position INTEGER,image TEXT,payload TEXT,PRIMARY KEY(report,position))')
            con.execute('CREATE INDEX report_sample_image ON report_samples(report,image)')
            con.execute('PRAGMA user_version=3');con.commit()
        except BaseException:con.rollback();raise
