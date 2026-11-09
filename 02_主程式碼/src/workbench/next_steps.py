"""The overview's to-do list (D2): only things that need a person, each with one link.

Every check is independent and fails quietly (a broken check hides its row, never the list).
"""

from __future__ import annotations

from src.common import snapshot_versions

import json
import time
from pathlib import Path


def _size(n: int) -> str:
    for unit, scale in (('GB', 1024**3), ('MB', 1024**2)):
        if n >= scale:
            return f'{n / scale:.1f} {unit}'
    return f'{n / 1024:.0f} KB'


def collect(root: Path) -> list[dict]:
    items: list[dict] = []
    for check in (
        _source_new,
        _area_pending,
        _duplicates,
        _spot_check,
        _quality,
        _patients,
        _snapshots,
        _intake,
        _failed_jobs,
        _backup,
        _trash,
    ):
        try:
            items.extend(check(root))
        except Exception:
            continue
    return items


def _source_new(root):
    from src.workbench import source_watch

    state = source_watch.cached(root)
    n = state.get('count') or 0
    if n:
        return [
            {
                'key': 'source_new',
                'text': f'岡山高醫資料夾有 {n} 張新照片',
                'action': '匯入',
                'href': '#data?area=cls&source_new=1',
                'level': 'info',
            }
        ]
    return []


def _area_pending(root):
    from src.workbench.queries import data_index

    out = []
    cls = data_index.area_query(root, 'cls', 'pending', size=1)['total']
    if cls:
        out.append(
            {
                'key': 'cls_pending',
                'text': f'{cls} 張照片待分類',
                'action': '開始分類',
                'href': '#data?area=cls&view=pending',
            }
        )
    return out


def _duplicates(root):
    from src.workbench import flags

    n = flags.summary(root).get('duplicate_pending', 0)
    return (
        [
            {
                'key': 'duplicates',
                'text': f'{n} 張疑似重複待確認',
                'action': '查看',
                'href': '#data?area=cls&view=all&flag=duplicate',
            }
        ]
        if n
        else []
    )


def _quality(root):
    from src.workbench import flags

    n = flags.summary(root).get('quality_pending', 0)
    return (
        [
            {
                'key': 'quality',
                'text': f'{n} 張照片品質待確認',
                'action': '查看',
                'href': '#data?area=cls&view=all&flag=quality',
            }
        ]
        if n
        else []
    )


def _patients(root):
    from src.workbench import source_audit

    unassigned = source_audit.inventory(root)['unassigned']
    if not unassigned:
        return []
    return [
        {
            'key': 'patients',
            'text': f'{unassigned} 張已核准照片還沒有病人分組',
            'action': '查看',
            'href': '#trust?tab=inventory',
        }
    ]


def _spot_check(root):
    from src.workbench import settings, spot_check

    if not settings.load().spot_check.enabled:
        return []
    state = spot_check.status(root)
    if state['pending']:
        return [
            {
                'key': 'spot_check',
                'text': f"抽查：本批 {state['pending']} 張待確認",
                'action': '開始抽查',
                'href': '#data?area=cls&spot=1',
            }
        ]
    if state['unsampled']:
        return [
            {
                'key': 'spot_check_new',
                'text': f"{state['unsampled']} 張自動分類照片尚未抽查",
                'action': '開始抽查',
                'href': '#data?area=cls&spot=1',
            }
        ]
    return []


def _snapshots(root):
    from src.common import read_json
    from src.workbench import resources

    path = root / 'data/snapshot_states.json'
    states = read_json(path) if path.exists() else {}
    removed = {k for k, v in resources.states('snapshot').items() if v != 'active'}
    latest = {}
    for p in snapshot_versions(root):
        try:
            info = json.loads(p.read_text(encoding='utf-8-sig'))
        except (OSError, ValueError):
            continue
        version = info.get('version') or p.parent.name
        if version in removed or info.get('purpose'):  # independent test sets and their derived training folds
            continue
        task = info.get('task')
        if task:
            latest[task] = (info.get('created_at') or version, version)
    names = {'binary_classification': '二分類', 'stage_classification': '分期'}
    out = []
    for task, (_, version) in sorted(latest.items()):
        status = (states.get(version) or {}).get('status')
        if status:
            out.append(
                {
                    'key': 'snapshot_' + task,
                    'text': f'{names.get(task, task)}快照已過期（資料已變更）',
                    'action': '重建',
                    'href': '#models?tab=snapshots&task=' + task,
                }
            )
    return out


def _intake(root):
    from src.workbench import jobs

    with jobs.db() as con:
        if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='research_intake'").fetchone():
            return []
        n = con.execute(
            "SELECT COUNT(*) FROM research_intake WHERE state='received' AND usage_state!='withdrawn'"
        ).fetchone()[0]
    return (
        [{'key': 'intake', 'text': f'LINE 研究收件 {n} 張待審查', 'action': '審查', 'href': '#intake?state=received'}]
        if n
        else []
    )


def _failed_jobs(root):
    from src.workbench import jobs

    since = time.time() - 3 * 86400
    with jobs.db() as con:
        n = con.execute(
            """SELECT COUNT(*) FROM jobs WHERE state IN ('failed','interrupted') AND kind IN ('train','evaluate','prepare') AND updated>=?
            AND NOT EXISTS (SELECT 1 FROM resource_lifecycle r WHERE r.type='job' AND r.id=jobs.id AND r.state!='active')""",
            (since,),
        ).fetchone()[0]
    return (
        [
            {
                'key': 'failed_jobs',
                'text': f'近 3 天有 {n} 個工作失敗或中斷',
                'action': '查看',
                'href': '#models?tab=jobs',
                'level': 'error',
            }
        ]
        if n
        else []
    )


def _backup(root):
    from src.workbench import backup

    state = backup.listing(root)
    if state['enabled'] and (state['last_auto'] is None or time.time() - state['last_auto'] > 36 * 3600):
        return [
            {
                'key': 'backup',
                'text': '超過一天沒有自動備份',
                'action': '立即備份',
                'href': '#settings?section=backup',
                'level': 'error',
            }
        ]
    return []


def _trash(root):
    from src.workbench import disk

    n = disk.trash_release(root)
    if n >= 50 * 1024**2:
        return [{'key': 'trash', 'text': f'垃圾桶有約 {_size(n)} 可釋放', 'action': '前往垃圾桶', 'href': '#trash'}]
    return []
