"""Workbench database upgrades, applied in order when a database is opened (storage.db).

Each module upgrades `PRAGMA user_version` by one step and does nothing when the database
is already at or past its version.  Before changing anything it copies the whole database
(common.database_backup: 04_備份/修改前副本/資料庫/ for the real database).  To add an
upgrade, write vN_<name>.py with `migrate(con, home)` and append it to STEPS.
"""

from __future__ import annotations

from importlib import import_module

STEPS = ('v1_trash', 'v2_queries', 'v3_reports', 'v4_intake', 'v5_area_index', 'v6_no_audit', 'v7_single_area')


LATEST = len(STEPS)


def apply(con, home) -> None:
    for name in STEPS:
        import_module(f'{__name__}.{name}').migrate(con, home)
