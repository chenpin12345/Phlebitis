"""Task-specific labels, eligibility, snapshots and filename rules."""

import json
import zlib
import pytest
from PIL import Image
from src.common import sha256, write_manifest, read_manifest
from src.data import tasks, filename_rules, evidence, revocations
from src.data.dataset import audit, build, validate_split, review


def make_row(root, ident, label, stage='', boxes=None, status='approved', group='g0'):
    im = root / f"data/{status}/images/{ident}.jpg"
    im.parent.mkdir(parents=True, exist_ok=True)
    c = zlib.crc32(ident.encode())
    Image.new("RGB", (120, 90), (c % 256, (c >> 8) % 256, (c >> 16) % 256)).save(im)
    return dict(
        image_id=ident,
        sha256=sha256(im),
        image_path=im.relative_to(root).as_posix(),
        annotation_path='',
        status=status,
        label_state=label,
        candidate_group=group,
        subject_id=group,
        group_verified='true',
        reviewer='t',
        reason='fixture',
        updated_at='test',
        original_paths='[]',
        stage_label=stage,
    )


@pytest.fixture
def staged(tmp_path):
    rows = []
    for g in range(3):
        rows.append(make_row(tmp_path, f"n{g}", 'negative', 'normal', boxes='', group=f"p{g}"))
        rows.append(make_row(tmp_path, f"a{g}", 'positive', 'stage1', group=f"p{g}"))
        rows.append(make_row(tmp_path, f"b{g}", 'positive', 'stage2', boxes='0 0.5 0.5 0.2 0.2', group=f"p{g}"))
    write_manifest(rows, tmp_path)
    return tmp_path


@pytest.mark.parametrize(
    'name,stage,side',
    [
        ('01/20260429_ZZ0601_LH_2_3.jpg', 'stage2', 'LH'),
        ('01/20260429_ZZ0601_RH_2_3.jpg', 'stage2', 'RH'),
        ('08/20260519 ZZ0801_RH_1_4.jpg', 'stage1', 'RH'),
        ('01(正常)/20260429_ZZ0601_LH_0_1.jpg', 'normal', 'LH'),
        ('10/20260524_ZZ10-01_LH_2_1.jpg', 'stage2', 'LH'),
    ],
)
def test_filename_rule_uses_stage_after_side_not_sequence(name, stage, side):
    result = filename_rules.parse('gangshan_filename_v1', name)
    assert result['value'] == stage and result['side'] == side


@pytest.mark.parametrize(
    'name',
    [
        '03/20260428_ZZ1401_LL_2_1.jpg',
        '01(正常)/20260429_ZZ0601_LH_1_1.jpg',
        'x/random.jpg',
        'x/20260429_ZZ0601_LH_3_1.jpg',
        'x/a.csv',
    ],
)
def test_unknown_or_conflicting_names_are_never_normal(name):
    assert filename_rules.parse('gangshan_filename_v1', name)['value'] == 'unknown'


def test_eligibility_is_per_task_with_reasons(staged):
    report = audit(staged)
    assert not report['errors']
    rows = {r['image_id']: r for r in read_manifest(staged)}
    stage1 = tasks.eligibility(rows['a0'])
    assert stage1['binary_classification']['eligible'] and stage1['stage_classification']['eligible']
    unstaged = dict(rows['a0'], stage_label='')
    e = tasks.eligibility(unstaged)
    assert e['binary_classification']['eligible'] and not e['stage_classification']['eligible']
    unknown = dict(rows['a0'], status='pending_review', label_state='unknown', stage_label='')
    assert tasks.effective(unknown)['stage'] == 'unknown'
    assert not any(v['eligible'] for v in tasks.eligibility(unknown).values())


def test_stage_snapshot_and_legacy_meaning(staged):
    info = build(root=staged, task='stage_classification')
    assert info['task'] == 'stage_classification' and info['class_mapping'] == {'normal': 0, 'stage1': 1, 'stage2': 2}
    images = list((staged / 'data/snapshots' / info['version'] / 'images').iterdir())
    assert len(images) == 9, 'one normalized copy per image, not per fold'
    split = validate_split(staged / info['folds'][0]['dataset'], staged)
    from src.workbench.adapters import check_split_task, truth_of

    check_split_task(split, 'stage_classification')
    with pytest.raises(ValueError):
        check_split_task(split, 'binary_classification')
    assert {truth_of(m, split, 'stage_classification') for f in ('train', 'val') for m in split['members'][f]} <= {
        0,
        1,
        2,
    }
    # Legacy schema-2 members stay binary: positive=1 is never read as stage1.
    legacy = {'schema_version': 2, 'members': {'train': [{'label_state': 'positive'}], 'val': []}}
    assert truth_of(legacy['members']['train'][0], legacy, 'binary_classification') == 1
    with pytest.raises(ValueError, match='舊版快照'):
        check_split_task({**legacy, 'members': {'train': [], 'val': []}}, 'binary_classification')


def test_withdrawal_blocks_immediately(staged):
    info = build(root=staged, task='binary_classification')
    revocations.revoke('image', 'a0', 'consent withdrawn', 'test', staged)
    from src.workbench.views import data_rows

    row = next(r for r in data_rows(staged) if r['image_id'] == 'a0')
    assert not any(v['eligible'] for v in row['tasks'].values())
    member_fold = next(
        f for f in info['folds'] if any(m['image_id'] == 'a0' for ms in f['members'].values() for m in ms)
    )
    with pytest.raises(ValueError, match='withdrawn'):
        validate_split(staged / member_fold['dataset'], staged)


def test_rule_evidence_is_suggestion_only(staged):
    rows = {r['image_id']: r for r in read_manifest(staged)}
    evidence.append(
        'a0',
        {
            'task': 'stage_classification',
            'value': 'stage2',
            'method': 'rule_prefill',
            'rule_version': 'gangshan_filename_v1',
        },
        staged,
        dedupe_key='k',
    )
    evidence.append(
        'a0',
        {
            'task': 'stage_classification',
            'value': 'stage2',
            'method': 'rule_prefill',
            'rule_version': 'gangshan_filename_v1',
        },
        staged,
        dedupe_key='k',
    )
    assert len(evidence.read('a0', staged)['entries']) == 1
    hint = evidence.suggestion('a0', rows['a0'], staged)
    assert hint['value'] == 'stage2' and hint['conflict'], 'confirmed stage1 is not silently overwritten'
    assert read_manifest(staged)[1]['stage_label'] == 'stage1'


def test_row_revision_ignores_unset_optional_columns():
    row = {'image_id': 'x', 'status': 'approved'}
    assert tasks.row_revision(row) == tasks.row_revision({**row, 'stage_label': '', 'detection_state': ''})
    assert tasks.row_revision(row) != tasks.row_revision({**row, 'stage_label': 'stage1'})


def test_multiclass_metrics():
    from src.workbench.metrics import multiclass_metrics

    samples = [
        {'image_id': str(i), 'truth': t, 'prediction': p}
        for i, (t, p) in enumerate([(0, 0), (0, 1), (1, 1), (2, 2), (2, 1)])
    ]
    samples.append({'image_id': 'x', 'truth': 1, 'prediction': None, 'error': 'boom'})
    m = multiclass_metrics(samples, ['normal', 'stage1', 'stage2'])
    assert m['confusion_matrix'] == [[1, 1, 0], [0, 1, 0], [0, 1, 1]]
    assert m['per_class']['stage1']['precision'] == pytest.approx(1 / 3) and m['per_class']['stage1']['recall'] == 1
    assert m['failed'] == 1 and not m['complete'] and m['macro_f1'] == pytest.approx((2 / 3 + 0.5 + 2 / 3) / 3)


def test_contracts_keep_legacy_dumps_and_scheme():
    from src.workbench.contracts import InferenceConfig, Experiment

    assert 'label_scheme' not in InferenceConfig().model_dump()
    e = Experiment(model='efficientnet_b0', dataset='x', task='stage_classification')
    assert (
        e.inference.label_mapping == {'normal': 0, 'stage1': 1, 'stage2': 2}
        and e.model_dump()['task'] == 'stage_classification'
    )
    assert 'task' not in Experiment(model='efficientnet_b0', dataset='x').model_dump()
    with pytest.raises(ValueError):
        Experiment(model='dinov2_small', dataset='x', task='stage_classification', parameters={'solver': 'liblinear'})


def test_stage_snapshot_excludes_unstaged_positives(staged):
    rows = list(read_manifest(staged))
    for g in range(3):
        rows.append(make_row(staged, f"u{g}", 'positive', 'positive_unstaged', group=f"p{g}"))
    write_manifest(rows, staged)
    stage = build(root=staged, task='stage_classification')
    members = {m['image_id'] for f in stage['folds'] for ms in f['members'].values() for m in ms}
    assert not any(i.startswith('u') for i in members), 'positives without a stage never enter staging snapshots'
    binary = build(root=staged, task='binary_classification')
    members = {m['image_id'] for f in binary['folds'] for ms in f['members'].values() for m in ms}
    assert {'u0', 'u1', 'u2'} <= members, 'they still count as positive for the binary task'
