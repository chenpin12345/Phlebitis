"""Task-specific labels and training eligibility.

This module is the single rule source for every API, page and snapshot builder.

Photos are reviewed in one work area: whole-photo classification (binary and stage labels),
reviewed through ``cls_review``.  ``status`` only records where the file is stored and is
derived from that review state.

Binary labels keep the legacy ``label_state`` meaning (positive/negative/unknown).
Stage labels use the user-provided rule (normal / stage1 / stage2); it is not
claimed to be any published clinical grading standard.
"""

from __future__ import annotations

import hashlib
import random

from src.workbench.storage import digest

# Manifest columns added after schema 2. Empty or missing values mean "not yet set";
# they are excluded from the row revision so pre-existing review history still matches.
OPTIONAL_COLUMNS = (
    'stage_label',
    'label_scheme',
    'quality_state',
    'usage_state',
    'cls_review',
)
# Removed in 2026-11 together with lesion detection. Older review records still carry them, so
# they stay out of the row revision or those records would stop matching the current rows.
RETIRED_COLUMNS = ('yolo_path', 'det_review', 'detection_state')
# Who a photo belongs to is not part of its label review: filling these must not detach reviews.
GROUP_COLUMNS = ('subject_id', 'group_verified')

STAGES = ('normal', 'stage1', 'stage2', 'positive_unstaged', 'unknown')
QUALITY = ('', 'acceptable', 'limited', 'unusable')
USAGE = ('', 'active', 'test_only', 'withdrawn')
AREAS = ('cls',)
AREA_STATES = ('pending', 'confirmed', 'excluded')
AREA_COLUMN = {'cls': 'cls_review'}
DECISION_STATE = {'approve': 'confirmed', 'exclude': 'excluded', 'needs_changes': 'pending', 'reopen': 'pending'}
STATE_DECISION = {'confirmed': 'approve', 'excluded': 'exclude', 'pending': 'needs_changes'}

TASKS = ('binary_classification', 'stage_classification')
TASK_AREA = {'binary_classification': 'cls', 'stage_classification': 'cls'}
TASK_NAMES = {
    'binary_classification': '二分類（正常／陽性）',
    'stage_classification': '分期分類（正常／第一期／第二期）',
}
SCHEMES = {
    'binary_v1': {
        'task': 'binary_classification',
        'classes': ['negative', 'positive'],
        'version': 1,
        'description': '二分類：negative=0（正常），positive=1（陽性）。舊模型與舊快照固定使用此方案。',
    },
    'stage_v1': {
        'task': 'stage_classification',
        'classes': ['normal', 'stage1', 'stage2'],
        'version': 1,
        'description': '使用者提供之分期規則：normal=0、stage1=1（第一期）、stage2=2（第二期）。非已驗證的臨床分級標準。',
    },
}
TASK_SCHEME = {'binary_classification': 'binary_v1', 'stage_classification': 'stage_v1'}
STAGE_TO_BINARY = {'normal': 'negative', 'stage1': 'positive', 'stage2': 'positive', 'positive_unstaged': 'positive'}

REASONS = {
    'cls_pending': '尚未完成分類確認',
    'cls_excluded': '已排除',
    'integrity': '完整性檢查失敗',
    'withdrawn': '研究授權已撤回或停止使用',
    'test_only': '測試素材，不納入正式訓練',
    'quality': '影像品質判定不可用',
    'binary_unknown': '二分類標籤未確認',
    'stage_unconfirmed': '分期尚未確認',
    'stage_unknown_positive': '陽性但分期未知（可用於二分類，不可用於分期）',
    'stage_conflict': '分期與二分類標籤矛盾',
}


def mapping(scheme: str) -> dict[str, int]:
    return {name: i for i, name in enumerate(SCHEMES[scheme]['classes'])}


def row_revision(row: dict) -> str:
    """Revision of a manifest row; unset optional columns do not change it."""
    skipped = ('revision', *RETIRED_COLUMNS, *GROUP_COLUMNS)
    return digest({k: v for k, v in row.items() if not (k in OPTIONAL_COLUMNS and not v) and k not in skipped})


def shuffled_labels(split: dict, seed: int) -> dict:
    """Control run (#4): training labels are permuted, validation keeps the truth.  A pipeline
    without leakage scores about chance on such a run."""
    train = split['members']['train']
    order = random.Random(seed).sample(range(len(train)), len(train))
    fields = ('label_state', 'stage_label', 'target')
    shuffled = [{**m, **{k: train[n][k] for k in fields}} for m, n in zip(train, order)]
    return {**split, 'members': {**split['members'], 'train': shuffled}}


def group_key(row: dict) -> str:
    """Patient key for snapshots and everything derived from them: the 病歷號 stays in the manifest."""
    return 'patient_' + hashlib.sha256(row['subject_id'].encode('utf-8')).hexdigest()[:16]


def area_state(row: dict, area: str) -> str:
    """Review state. Rows written before explicit states inherit it from status."""
    value = row.get(AREA_COLUMN[area]) or ''
    if value:
        return value
    return {'approved': 'confirmed', 'excluded': 'excluded'}.get(row.get('status'), 'pending')


def storage_status(cls: str) -> str:
    """Where the file lives, derived from its review state."""
    return {'confirmed': 'approved', 'excluded': 'excluded'}.get(cls, 'pending_review')


def effective(row: dict) -> dict:
    """Effective labels. Explicit columns win; legacy rows keep their old meaning."""
    cls = area_state(row, 'cls')
    binary = row.get('label_state') or 'unknown'
    stage = row.get('stage_label') or ''
    stage_source = 'confirmed' if stage else 'none'
    if not stage:
        if cls == 'confirmed' and binary == 'negative':
            stage, stage_source = 'normal', 'legacy_binary'
        elif binary == 'positive':
            stage, stage_source = 'positive_unstaged', 'legacy_binary'
        else:
            stage = 'unknown'
    return {
        'binary': binary,
        'stage': stage,
        'stage_source': stage_source,
        'quality': row.get('quality_state') or '',
        'usage': row.get('usage_state') or 'active',
        'label_scheme': row.get('label_scheme') or '',
        'cls_state': cls,
    }


def consistency_errors(row: dict) -> list[str]:
    """Binary and stage labels must agree."""
    e = effective(row)
    if (
        e['stage'] in STAGE_TO_BINARY
        and e['binary'] in ('positive', 'negative')
        and STAGE_TO_BINARY[e['stage']] != e['binary']
    ):
        return [REASONS['stage_conflict']]
    return []


def eligibility(
    row: dict, *, audit_error: str | None = None, review: dict | None = None, revoked: bool = False
) -> dict:
    """Per-task eligibility with explicit reasons; never a single boolean."""
    e = effective(row)
    common = []
    if audit_error:
        common.append(REASONS['integrity'] + '：' + audit_error)
    if revoked or e['usage'] == 'withdrawn':
        common.append(REASONS['withdrawn'])
    if e['usage'] == 'test_only':
        common.append(REASONS['test_only'])
    if e['quality'] == 'unusable':
        common.append(REASONS['quality'])
    cls = list(common)
    if e['cls_state'] != 'confirmed':
        cls.append(REASONS['cls_excluded' if e['cls_state'] == 'excluded' else 'cls_pending'])
    cls += consistency_errors(row)
    binary = list(cls)
    if e['binary'] not in ('positive', 'negative'):
        binary.append(REASONS['binary_unknown'])
    stage = list(cls)
    if e['stage'] == 'positive_unstaged':
        stage.append(REASONS['stage_unknown_positive'])
    elif e['stage'] not in ('normal', 'stage1', 'stage2'):
        stage.append(REASONS['stage_unconfirmed'])
    result = {'binary_classification': binary, 'stage_classification': stage}
    return {task: {'eligible': not reasons, 'reasons': reasons} for task, reasons in result.items()}


def target(row: dict, task: str) -> str:
    """Class name for a training row; callers must have checked eligibility."""
    e = effective(row)
    if task == 'binary_classification':
        return e['binary']
    if task == 'stage_classification':
        return e['stage']
    raise ValueError('Unknown task')


def member_scheme(split: dict) -> str:
    """Label scheme of a snapshot fold. Schema-2 (legacy) snapshots are binary_v1, always."""
    return split.get('label_scheme') or 'binary_v1'


def member_class(member: dict, scheme: str) -> int:
    """Class index of a snapshot member under the snapshot's own scheme."""
    if scheme == 'binary_v1' and 'target' not in member:
        if member.get('label_state') not in ('positive', 'negative'):
            raise ValueError('Legacy member has unknown binary label')
        return int(member['label_state'] == 'positive')
    names = mapping(scheme)
    if member.get('target') not in names:
        raise ValueError('Snapshot member label is outside its label scheme')
    return names[member['target']]
