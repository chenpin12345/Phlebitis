"""Label evidence history, stored next to the manifest without changing row revisions.

Evidence records where a label came from (human review, a versioned filename rule,
legacy migration, LINE research intake).  Rule evidence is a suggestion only: it never
becomes a confirmed label until a reviewer confirms it through ``dataset.review``.
"""
from __future__ import annotations

import re
from pathlib import Path

from src.common import ROOT, read_json, stamp, write_json

SCHEMA = 1


def path(image_id: str, root: Path = ROOT) -> Path:
    if not re.fullmatch(r'[A-Za-z0-9_\-]{1,80}', image_id):
        raise ValueError('Invalid image id')
    return root / 'data/label_evidence' / f'{image_id}.json'


def read(image_id: str, root: Path = ROOT) -> dict:
    p = path(image_id, root)
    return read_json(p) if p.exists() else {'schema_version': SCHEMA, 'image_id': image_id, 'entries': []}


def append(image_id: str, entry: dict, root: Path = ROOT, *, dedupe_key: str | None = None) -> dict:
    """Append one entry. ``dedupe_key`` makes repeated imports idempotent."""
    data = read(image_id, root)
    if dedupe_key and any(e.get('dedupe_key') == dedupe_key for e in data['entries']):
        return data
    item = {'at': stamp(), **entry}
    if dedupe_key:
        item['dedupe_key'] = dedupe_key
    data['entries'].append(item)
    write_json(path(image_id, root), data)
    return data


def suggestion(image_id: str, row: dict, root: Path = ROOT) -> dict | None:
    """Latest unconfirmed rule suggestion for the stage task, with conflict status."""
    data = read(image_id, root)
    rules = [e for e in data['entries'] if e.get('method') == 'rule_prefill' and e.get('task') == 'stage_classification' and e.get('value') in ('normal', 'stage1', 'stage2')]
    if not rules:
        return None
    values = sorted({e['value'] for e in rules})
    latest = rules[-1]
    from src.data.tasks import STAGE_TO_BINARY, effective
    current = effective(row)
    conflict = len(values) > 1
    reasons = []
    if conflict:
        reasons.append('多個來源檔名推得不同分期：' + '、'.join(values))
    binary = STAGE_TO_BINARY.get(latest['value'])
    if binary and current['binary'] in ('positive', 'negative') and binary != current['binary']:
        conflict = True
        reasons.append('規則分期與既有二分類標籤矛盾')
    if row.get('stage_label') and row['stage_label'] != latest['value']:
        conflict = True
        reasons.append('規則分期與已確認分期不同（已確認標籤不會被覆蓋）')
    confirmed = bool(row.get('stage_label')) and row['stage_label'] == latest['value'] and not conflict
    return {'value': latest['value'], 'values': values, 'rule': latest.get('rule_version'), 'source': latest.get('source'),
            'conflict': conflict, 'conflict_reasons': reasons, 'confirmed': confirmed}
