"""Workbench preferences kept in the flags table (one JSON document, validated on write).

Each section belongs to one feature: notifications (D3), automatic backup (D1), the full
backup to an external drive (full_backup.py) and spot checks of rule-classified photos (A5).  The LINE release checklist (C1) was
removed on 2026-10-17; a stored 'release' section from that time is ignored.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

KEY = 'workbench_settings'


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


class Notifications(Strict):
    system: bool = False  # Windows system notifications through the browser Notification API


class Backup(Strict):
    enabled: bool = True
    directory: str = Field('', max_length=400)  # empty = 04_備份/工作台紀錄
    keep: int = Field(14, ge=1, le=90)


class FullBackup(Strict):
    directory: str = Field('', max_length=400)  # folder on an external drive; empty = not set up yet
    keep_days: int = Field(30, ge=7, le=365)  # 舊版本 older than this are removed after a successful run
    remind_days: int = Field(7, ge=1, le=90)
    include_runs: bool = False  # runs/ holds re-creatable training outputs (several GB)


class SpotCheck(Strict):
    enabled: bool = False  # doctors approved the labels; a second check is opt-in
    ratio: float = Field(0.05, gt=0, le=1)


class WorkbenchSettings(Strict):
    notifications: Notifications = Notifications()
    backup: Backup = Backup()
    full_backup: FullBackup = FullBackup()
    spot_check: SpotCheck = SpotCheck()


def load() -> WorkbenchSettings:
    from src.workbench import jobs

    with jobs.db() as con:
        row = con.execute('SELECT data FROM flags WHERE id=?', (KEY,)).fetchone()
    if not row:
        return WorkbenchSettings()
    import json

    try:
        data = json.loads(row[0])
        data.pop('release', None)  # retired C1 thresholds
        return WorkbenchSettings(**data)
    except (ValueError, TypeError):
        return WorkbenchSettings()  # an unreadable document never blocks the workbench


def save(value: dict) -> WorkbenchSettings:
    import json
    from src.workbench import jobs

    checked = WorkbenchSettings(**value)
    from pathlib import Path

    if checked.backup.directory and not Path(checked.backup.directory).is_absolute():
        raise ValueError('備份位置必須是完整路徑，例如 E:\\靜脈炎備份')
    if checked.full_backup.directory:
        if not Path(checked.full_backup.directory).is_absolute():
            raise ValueError('完整備份位置必須是完整路徑，例如 E:\\靜脈炎完整備份')
        from src import common

        if Path(checked.full_backup.directory).resolve().is_relative_to(common.ROOT.resolve()):
            raise ValueError('完整備份位置不能放在資料區裡面，請選擇外接硬碟上的資料夾')
    with jobs.db() as con:
        con.execute(
            'INSERT OR REPLACE INTO flags(id,data) VALUES(?,?)',
            (KEY, json.dumps(checked.model_dump(), ensure_ascii=False)),
        )
    return checked
