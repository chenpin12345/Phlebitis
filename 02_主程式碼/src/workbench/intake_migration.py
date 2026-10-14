"""Schema v4: task eligibility projection, stop-use records, research consent and
LINE research intake, offline simulator transcript and retryable cleanup tasks.
Additive only; existing tables and rows are not rewritten."""
from src.workbench.storage import file_lock
import sqlite3

def migrate(con,home):
    if con.execute('PRAGMA user_version').fetchone()[0]>=4:return
    with file_lock(home/'schema.lock'):
        if con.execute('PRAGMA user_version').fetchone()[0]>=4:return
        backup=home/'backups/before-intake-v4.sqlite3';backup.parent.mkdir(parents=True,exist_ok=True)
        if not backup.exists():
            with sqlite3.connect(backup) as target:con.backup(target)
        statements=[
            'ALTER TABLE data_index ADD COLUMN eligible_binary INTEGER NOT NULL DEFAULT 0',
            'ALTER TABLE data_index ADD COLUMN eligible_stage INTEGER NOT NULL DEFAULT 0',
            'ALTER TABLE data_index ADD COLUMN eligible_detection INTEGER NOT NULL DEFAULT 0',
            'ALTER TABLE data_index ADD COLUMN display_name TEXT',
            'CREATE INDEX data_task_binary ON data_index(eligible_binary,id)',
            'CREATE INDEX data_task_stage ON data_index(eligible_stage,id)',
            'CREATE INDEX data_task_detection ON data_index(eligible_detection,id)',
            'CREATE TABLE usage_revocations(kind TEXT NOT NULL,ident TEXT NOT NULL,at REAL NOT NULL,reason TEXT NOT NULL,source TEXT NOT NULL,PRIMARY KEY(kind,ident))',
            'CREATE TABLE research_consents(id TEXT PRIMARY KEY,source TEXT NOT NULL,simulated INTEGER NOT NULL,user_key TEXT NOT NULL,session TEXT,event_id TEXT NOT NULL UNIQUE,message_id TEXT NOT NULL,result_token TEXT,version TEXT NOT NULL,scope TEXT NOT NULL,decision TEXT NOT NULL,decided_at REAL NOT NULL,withdrawn_at REAL,withdraw_event TEXT,detail TEXT NOT NULL)',
            'CREATE INDEX consent_message ON research_consents(source,message_id)',
            'CREATE TABLE research_intake(id TEXT PRIMARY KEY,consent_id TEXT NOT NULL UNIQUE,asset_path TEXT,image_sha256 TEXT,source TEXT NOT NULL,simulated INTEGER NOT NULL,received_at REAL NOT NULL,state TEXT NOT NULL,quality TEXT NOT NULL DEFAULT \'\',binary_label TEXT NOT NULL DEFAULT \'unknown\',stage_label TEXT NOT NULL DEFAULT \'unknown\',subject_alias TEXT NOT NULL DEFAULT \'\',prediction TEXT,reviewer TEXT,note TEXT,promoted_image_id TEXT,usage_state TEXT NOT NULL,cleanup_state TEXT NOT NULL DEFAULT \'none\',revision INTEGER NOT NULL DEFAULT 1,updated REAL NOT NULL)',
            'CREATE INDEX intake_filter ON research_intake(state,usage_state,source,received_at DESC)',
            'CREATE TABLE sim_messages(id INTEGER PRIMARY KEY AUTOINCREMENT,session TEXT NOT NULL,direction TEXT NOT NULL,event_id TEXT,kind TEXT NOT NULL,payload TEXT NOT NULL,status TEXT NOT NULL,created REAL NOT NULL,updated REAL NOT NULL)',
            'CREATE INDEX sim_messages_session ON sim_messages(session,id)',
            'CREATE TABLE cleanup_tasks(id TEXT PRIMARY KEY,kind TEXT NOT NULL,target TEXT NOT NULL,state TEXT NOT NULL,attempts INTEGER NOT NULL DEFAULT 0,error TEXT,created REAL NOT NULL,updated REAL NOT NULL,detail TEXT NOT NULL)',
            'CREATE INDEX cleanup_state ON cleanup_tasks(state,updated)',
        ]
        con.execute('BEGIN IMMEDIATE')
        try:
            for sql in statements:con.execute(sql)
            con.execute('PRAGMA user_version=4');con.commit()
        except BaseException:con.rollback();raise
