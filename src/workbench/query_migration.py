"""Additive read-model/import schema. Does not alter research files."""
from src.workbench.storage import file_lock
import sqlite3

def migrate(con,home):
    if con.execute('PRAGMA user_version').fetchone()[0]>=2:return
    with file_lock(home/'schema.lock'):
        if con.execute('PRAGMA user_version').fetchone()[0]>=2:return
        backup=home/'backups/before-query-v2.sqlite3';backup.parent.mkdir(parents=True,exist_ok=True)
        if not backup.exists():
            with sqlite3.connect(backup) as target:con.backup(target)
        statements=[
            'CREATE TABLE query_meta(name TEXT PRIMARY KEY,value TEXT NOT NULL)',
            'CREATE TABLE data_index(id TEXT PRIMARY KEY,status TEXT,eligible INTEGER,reviewed INTEGER,reviewer TEXT,decision TEXT,review_at REAL,payload TEXT NOT NULL)',
            'CREATE INDEX data_classification ON data_index(status,eligible,id)',
            'CREATE INDEX data_review_filter ON data_index(reviewed,reviewer,decision,review_at,id)',
            'CREATE TABLE file_projection(path TEXT PRIMARY KEY,signature TEXT NOT NULL,payload TEXT NOT NULL)',
            'CREATE TABLE imports(id TEXT PRIMARY KEY,kind TEXT NOT NULL,batch TEXT NOT NULL,state TEXT NOT NULL,created REAL NOT NULL,updated REAL NOT NULL,session TEXT NOT NULL,idem TEXT UNIQUE,payload TEXT NOT NULL)',
            'CREATE INDEX jobs_state_created ON jobs(state,created,id)',
            'CREATE INDEX audit_at_id ON audit(at DESC,id DESC)',
            'CREATE TABLE scheduler_reconciled(id TEXT PRIMARY KEY,updated REAL NOT NULL)',
        ]
        con.execute('BEGIN IMMEDIATE')
        try:
            for sql in statements:con.execute(sql)
            con.execute('PRAGMA user_version=2');con.commit()
        except BaseException:con.rollback();raise
