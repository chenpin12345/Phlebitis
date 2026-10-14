"""Task-specific labels and training eligibility.

This module is the single rule source for every API, page and snapshot builder.

Two independent work areas share one image catalogue:
  * the YOLO area (lesion detection): boxes / confirmed no-lesion / not annotated,
    reviewed through ``det_review``;
  * the classification area (other models): binary and stage labels, reviewed
    through ``cls_review``.
Neither area reads the other's labels or review state.  ``status`` only records
where the file is stored and is derived from the two area states.

Binary labels keep the legacy ``label_state`` meaning (positive/negative/unknown).
Stage labels use the user-provided rule (normal / stage1 / stage2); it is not
claimed to be any published clinical grading standard.
"""
from __future__ import annotations

from src.workbench.storage import digest

# Manifest columns added after schema 2. Empty or missing values mean "not yet set";
# they are excluded from the row revision so pre-existing review history still matches.
OPTIONAL_COLUMNS = ('stage_label', 'detection_state', 'label_scheme', 'quality_state', 'usage_state', 'cls_review', 'det_review')

STAGES = ('normal', 'stage1', 'stage2', 'positive_unstaged', 'unknown')
DETECTION_STATES = ('boxes', 'no_target', 'not_annotated')
QUALITY = ('', 'acceptable', 'limited', 'unusable')
USAGE = ('', 'active', 'test_only', 'withdrawn')
AREAS = ('cls', 'det')
AREA_STATES = ('pending', 'confirmed', 'excluded')
AREA_COLUMN = {'cls': 'cls_review', 'det': 'det_review'}
DECISION_STATE = {'approve': 'confirmed', 'exclude': 'excluded', 'needs_changes': 'pending', 'reopen': 'pending'}
STATE_DECISION = {'confirmed': 'approve', 'excluded': 'exclude', 'pending': 'needs_changes'}

TASKS = ('binary_classification', 'stage_classification', 'detection')
TASK_AREA = {'binary_classification': 'cls', 'stage_classification': 'cls', 'detection': 'det'}
TASK_NAMES = {'binary_classification': '二分類（正常／陽性）', 'stage_classification': '分期分類（正常／第一期／第二期）', 'detection': '病灶偵測'}
SCHEMES = {
    'binary_v1': {'task': 'binary_classification', 'classes': ['negative', 'positive'], 'version': 1,
                  'description': '二分類：negative=0（正常），positive=1（陽性）。舊模型與舊快照固定使用此方案。'},
    'stage_v1': {'task': 'stage_classification', 'classes': ['normal', 'stage1', 'stage2'], 'version': 1,
                 'description': '使用者提供之分期規則：normal=0、stage1=1（第一期）、stage2=2（第二期）。非已驗證的臨床分級標準。'},
    'detection_v1': {'task': 'detection', 'classes': ['phlebitis'], 'version': 1,
                     'description': '單類別病灶框；確認無病灶的照片使用空標註。框不帶分期。'},
}
TASK_SCHEME = {'binary_classification': 'binary_v1', 'stage_classification': 'stage_v1', 'detection': 'detection_v1'}
STAGE_TO_BINARY = {'normal': 'negative', 'stage1': 'positive', 'stage2': 'positive', 'positive_unstaged': 'positive'}

REASONS = {
    'cls_pending': '尚未在其他模型分類區完成確認',
    'cls_excluded': '已在其他模型分類區排除',
    'det_pending': '尚未在 YOLO 框選區完成確認',
    'det_excluded': '已在 YOLO 框選區排除',
    'integrity': '完整性檢查失敗',
    'withdrawn': '研究授權已撤回或停止使用',
    'test_only': '測試素材，不納入正式訓練',
    'quality': '影像品質判定不可用',
    'binary_unknown': '二分類標籤未確認',
    'stage_unconfirmed': '分期尚未確認',
    'stage_unknown_positive': '陽性但分期未知（可用於二分類，不可用於分期）',
    'stage_conflict': '分期與二分類標籤矛盾',
    'not_annotated': '尚未完成病灶框選（不等於確認無病灶）',
}


def mapping(scheme: str) -> dict[str, int]:
    return {name: i for i, name in enumerate(SCHEMES[scheme]['classes'])}


def row_revision(row: dict) -> str:
    """Revision of a manifest row; unset optional columns do not change it."""
    return digest({k: v for k, v in row.items() if not (k in OPTIONAL_COLUMNS and not v) and k not in ('revision',)})


def area_state(row: dict, area: str) -> str:
    """Review state of one work area. Rows written before the split inherit it from status."""
    value = row.get(AREA_COLUMN[area]) or ''
    if value:
        return value
    return {'approved': 'confirmed', 'excluded': 'excluded'}.get(row.get('status'), 'pending')


def storage_status(cls: str, det: str) -> str:
    """Where the file lives: any confirmed area keeps it in approved storage."""
    if 'confirmed' in (cls, det):
        return 'approved'
    if cls == det == 'excluded':
        return 'excluded'
    return 'pending_review'


def effective(row: dict) -> dict:
    """Effective labels per area. Explicit columns win; legacy rows keep their old meaning."""
    cls, det = area_state(row, 'cls'), area_state(row, 'det')
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
    detection = row.get('detection_state') or ''
    detection_source = 'confirmed' if detection else 'legacy'
    if not detection:
        # Legacy only (before migrate-tasks wrote explicit states): the old single form
        # stored boxes for positives and empty labels for negatives.
        if det == 'confirmed' and row.get('yolo_path'):
            detection = 'boxes' if binary == 'positive' else 'no_target'
        else:
            detection = 'not_annotated'
    return {'binary': binary, 'stage': stage, 'stage_source': stage_source, 'detection': detection,
            'detection_source': detection_source, 'quality': row.get('quality_state') or '',
            'usage': row.get('usage_state') or 'active', 'label_scheme': row.get('label_scheme') or '',
            'cls_state': cls, 'det_state': det}


def consistency_errors(row: dict) -> list[str]:
    """Only checks inside one area; the two areas never constrain each other."""
    e = effective(row)
    if e['stage'] in STAGE_TO_BINARY and e['binary'] in ('positive', 'negative') and STAGE_TO_BINARY[e['stage']] != e['binary']:
        return [REASONS['stage_conflict']]
    return []


def eligibility(row: dict, *, audit_error: str | None = None, review: dict | None = None, revoked: bool = False) -> dict:
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
    detection = list(common)
    if e['det_state'] != 'confirmed':
        detection.append(REASONS['det_excluded' if e['det_state'] == 'excluded' else 'det_pending'])
    if e['detection'] == 'not_annotated':
        detection.append(REASONS['not_annotated'])
    result = {'binary_classification': binary, 'stage_classification': stage, 'detection': detection}
    return {task: {'eligible': not reasons, 'reasons': reasons} for task, reasons in result.items()}


def target(row: dict, task: str) -> str:
    """Class name for a training row; callers must have checked eligibility."""
    e = effective(row)
    if task == 'binary_classification':
        return e['binary']
    if task == 'stage_classification':
        return e['stage']
    if task == 'detection':
        return 'phlebitis' if e['detection'] == 'boxes' else 'background'
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
