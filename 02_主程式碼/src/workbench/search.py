"""Global search for the page header (D4): photos, jobs, model versions and snapshots.

Items in the trash are included and marked, so a moved item can still be found.
Read-only; every result is a link to the page that owns the item.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.common import snapshot_versions

LIMIT = 8
TRASH_STATES = {
    'trashed': '在垃圾桶',
    'purging': '永久刪除中',
    'partial_failed': '在垃圾桶（刪除部分失敗）',
    'needs_check': '在垃圾桶（待檢查）',
}


def _hit(text, q):
    return q in str(text or '').lower()


def search(root: Path, q: str) -> dict:
    q = ' '.join((q or '').split()).lower()
    if not q:
        return {'query': '', 'groups': [], 'total': 0}
    if len(q) > 100:
        raise ValueError('搜尋文字過長')
    from src.workbench import jobs, registry, resources
    from src.workbench.queries import data_index

    groups = []

    photos = []
    with data_index.connection(root) as con:
        rows = con.execute(
            """SELECT id,display_name,cls_state FROM data_index
            WHERE instr(lower(id),?)>0 OR instr(lower(COALESCE(display_name,'')),?)>0 OR instr(lower(COALESCE(json_extract(payload,'$.original_paths'),'')),?)>0
            ORDER BY display_name IS NULL,COALESCE(display_name,id) LIMIT ?""",
            (q, q, q, LIMIT + 1),
        ).fetchall()
    names = {'pending': '待處理', 'confirmed': '已完成', 'excluded': '排除'}
    for r in rows[:LIMIT]:
        photos.append(
            {
                'id': r['id'],
                'title': r['display_name'] or r['id'],
                'detail': names.get(r['cls_state'], r['cls_state']),
                'href': '#data?'
                + _query(
                    {
                        'area': 'cls',
                        'view': 'all',
                        'image': r['id'],
                    }
                ),
            }
        )
    with jobs.db() as con:
        intake_rows = (
            con.execute(
                "SELECT i.id,i.received_at,i.state,i.simulated FROM research_intake i WHERE instr(lower(i.id),?)>0 OR instr(lower(COALESCE(i.promoted_image_id,'')),?)>0 ORDER BY i.received_at DESC LIMIT ?",
                (q, q, LIMIT),
            ).fetchall()
            if _table(con, 'research_intake')
            else []
        )
    research_states = resources.states('research_photo')
    for r in intake_rows:
        state = research_states.get(r['id'], 'active')
        if state == 'purged':
            continue
        photos.append(
            {
                'id': r['id'],
                'title': ('模擬收件 ' if r['simulated'] else 'LINE 收件 ') + r['id'][:12],
                'detail': 'LINE 研究收件',
                'href': (
                    '#trash?' + _query({'type': 'research_photo', 'search': r['id']})
                    if state != 'active'
                    else '#intake'
                ),
                'trash': TRASH_STATES.get(state),
            }
        )
    if photos:
        groups.append({'key': 'photos', 'name': '照片', 'items': photos[:LIMIT], 'more': len(rows) > LIMIT})

    job_states = resources.states('job')
    found = []
    with jobs.db() as con:
        for r in con.execute('SELECT id,kind,state,config,created FROM jobs ORDER BY created DESC').fetchall():
            cfg = json.loads(r['config'] or '{}')
            if not (
                r['id'].startswith(q)
                or _hit(cfg.get('name'), q)
                or _hit(cfg.get('model'), q)
                or _hit(cfg.get('artifact'), q)
            ):
                continue
            state = job_states.get(r['id'], 'active')
            if state == 'purged':
                continue
            label = {
                'train': '訓練',
                'evaluate': '評估',
                'predict': '預測',
                'regression': '回歸測試',
                'prepare': '權重準備',
            }.get(r['kind'], r['kind'])
            found.append(
                {
                    'id': r['id'],
                    'title': (cfg.get('name') + ' · ' if cfg.get('name') else '')
                    + (cfg.get('model') or cfg.get('artifact') or label),
                    'detail': f"{label}・{r['id'][:8]}",
                    'trash': TRASH_STATES.get(state),
                    'href': (
                        '#trash?' + _query({'type': 'job', 'search': r['id']})
                        if state != 'active'
                        else '#models?' + _query({'tab': 'jobs', 'job': r['id']})
                    ),
                }
            )
            if len(found) > LIMIT:
                break
    if found:
        groups.append({'key': 'jobs', 'name': '工作', 'items': found[:LIMIT], 'more': len(found) > LIMIT})

    model_states = resources.states('model')
    models = []
    for meta in registry.metadata_listing(include_trashed=True):
        if not (_hit(meta['id'], q) or _hit(meta.get('model'), q) or _hit(meta.get('experiment'), q)):
            continue
        state = model_states.get(meta['id'], 'active')
        if state == 'purged':
            continue
        models.append(
            {
                'id': meta['id'],
                'title': meta['id'],
                'detail': meta.get('model', ''),
                'trash': TRASH_STATES.get(state),
                'href': (
                    '#trash?' + _query({'type': 'model', 'search': meta['id']})
                    if state != 'active'
                    else '#models?' + _query({'tab': 'registry', 'artifact': meta['id']})
                ),
            }
        )
    if models:
        groups.append({'key': 'models', 'name': '模型版本', 'items': models[:LIMIT], 'more': len(models) > LIMIT})

    snapshot_states = resources.states('snapshot')
    snapshots = []
    for path in reversed(snapshot_versions(root)):
        try:
            info = json.loads(path.read_text(encoding='utf-8-sig'))
        except (OSError, ValueError):
            continue
        version = info.get('version') or path.parent.name
        if not (_hit(version, q) or _hit(info.get('name'), q)):
            continue
        state = snapshot_states.get(version, 'active')
        if state == 'purged':
            continue
        snapshots.append(
            {
                'id': version,
                'title': info.get('name') or version,
                'detail': version if info.get('name') else (info.get('task') or ''),
                'trash': TRASH_STATES.get(state),
                'href': (
                    '#trash?' + _query({'type': 'snapshot', 'search': version})
                    if state != 'active'
                    else '#models?' + _query({'tab': 'snapshots'})
                ),
            }
        )
    if snapshots:
        groups.append(
            {'key': 'snapshots', 'name': '資料快照', 'items': snapshots[:LIMIT], 'more': len(snapshots) > LIMIT}
        )
    return {'query': q, 'groups': groups, 'total': sum(len(g['items']) for g in groups)}


def _table(con, name):
    return bool(con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone())


def _query(values: dict) -> str:
    from urllib.parse import urlencode

    return urlencode(values)
