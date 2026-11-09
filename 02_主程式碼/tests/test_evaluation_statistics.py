"""M3.5: repeated group CV, patient-level intervals, metrics, ledger, explanation maps."""

import numpy as np
import pytest
from PIL import Image

from src.common import write_manifest
from src.data.dataset import _partitions, build, validate_split
from src.workbench import evaluation_views as ev
from src.workbench import ledger
from test_tasks import make_row


def cohort(root, normal=3, positive=5):
    rows = []
    for g in range(normal + positive):
        label, stage = ('negative', 'normal') if g < normal else ('positive', 'stage1')
        rows += [make_row(root, f'p{g}n{i}', label, stage, group=f'p{g}') for i in range(2)]
    write_manifest(rows, root)
    return rows


def test_repeated_snapshot_keeps_every_repeat_a_full_partition(tmp_path):
    cohort(tmp_path)
    info = build(root=tmp_path, repeats=3, seed=1)
    assert info['repeats'] == 3 and info['folds_per_repeat'] == 3 and len(info['folds']) == 9
    photos = 16
    for repeat in range(3):
        folds = [f for f in info['folds'] if f['repeat'] == repeat]
        validation = [m['image_id'] for f in folds for m in f['members']['val']]
        assert len(validation) == len(set(validation)) == photos, 'each photo validated once per repeat'
        for f in folds:
            train, val = ({m['group'] for m in f['members'][k]} for k in ('train', 'val'))
            assert not train & val, 'a patient is never on both sides'
            assert any(m['label_state'] == 'negative' for m in f['members']['val'])
    assert validate_split(tmp_path / info['folds'][8]['dataset'], tmp_path)['repeat'] == 2
    keys = {
        frozenset(frozenset(m['group'] for m in f['members']['val']) for f in info['folds'] if f['repeat'] == r)
        for r in range(3)
    }
    assert len(keys) == 3, 'repeats are different partitions'


def test_a_split_without_a_normal_patient_in_a_fold_is_thrown_away():
    labels = [0, 0, 0, 1, 1, 1, 1, 1, 1]
    groups = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']
    found, seeds = _partitions(labels, groups, 3, 4, 0, 2)
    assert found and len(seeds) == len(found)
    for parts in found:
        assert all(any(labels[i] == 0 for i in val) for _, val in parts)


def test_impossible_splits_return_nothing_instead_of_a_bad_one():
    assert _partitions([0, 0, 1, 1], ['a', 'a', 'b', 'c'], 2, 2, 0, 2)[0] == []


def test_fewer_different_partitions_than_requested_are_reported(tmp_path):
    cohort(tmp_path, normal=2, positive=2)
    info = build(root=tmp_path, folds=2, repeats=5)
    assert info['repeats_requested'] == 5 and info['repeats'] < 5 and len(info['folds']) == 2 * info['repeats']


def test_bootstrap_draws_whole_patients():
    samples = [{'group': g, 'truth': 1, 'prediction': 1} for g, n in (('a', 1), ('b', 2), ('c', 3)) for _ in range(n)]
    seen = []

    def spy(rows):
        counts = {}
        for row in rows:
            counts[row['group']] = counts.get(row['group'], 0) + 1
        seen.append(counts)
        return 1.0

    ev.bootstrap(samples, spy)
    size = {'a': 1, 'b': 2, 'c': 3}
    assert all(count % size[g] == 0 for counts in seen for g, count in counts.items())


def test_patient_interval_is_wider_than_treating_photos_as_independent():
    samples = []
    for g in range(6):  # three patients always right, three always wrong, ten photos each
        samples += [{'group': f'p{g}', 'truth': 1, 'prediction': int(g < 3)} for _ in range(10)]
    photos = [{k: v for k, v in s.items() if k != 'group'} for s in samples]

    def hit(s):
        return s['prediction'] == 1

    patient = ev._rate(samples, hit, lambda s: True, 30, 60)
    image = ev._rate(photos, hit, lambda s: True, 30, 60)
    assert patient[1] == 'patient_bootstrap' and image[1] == 'wilson'
    assert patient[0][1] - patient[0][0] > (image[0][1] - image[0][0]) * 1.5


def test_pooled_folds_match_a_hand_count():
    samples = [
        {'image_id': 'a', 'group': 'p1', 'truth': 1, 'prediction': 1, 'score': 0.9},
        {'image_id': 'b', 'group': 'p1', 'truth': 1, 'prediction': 0, 'score': 0.4},
        {'image_id': 'c', 'group': 'p2', 'truth': 0, 'prediction': 1, 'score': 0.6},
        {'image_id': 'd', 'group': 'p3', 'truth': 0, 'prediction': 0, 'score': 0.1},
        # The same photos in a second repeat.
        {'image_id': 'a', 'group': 'p1', 'truth': 1, 'prediction': 1, 'score': 0.8},
        {'image_id': 'b', 'group': 'p1', 'truth': 1, 'prediction': 1, 'score': 0.7},
        {'image_id': 'c', 'group': 'p2', 'truth': 0, 'prediction': 0, 'score': 0.2},
        {'image_id': 'd', 'group': 'p3', 'truth': 0, 'prediction': 0, 'score': 0.3},
    ]
    s = ev.summarize(samples, classes=None, multiclass=False, demo_only=False, subjects=3)
    keys = {m['key']: m for m in s['metrics']}
    assert s['n'] == 8 and s['photos'] == 4 and s['patients'] == 3
    assert keys['sensitivity']['value'] == 0.75 and keys['sensitivity']['count'] == '3/4'
    assert keys['false_positive_rate']['value'] == 0.25
    assert keys['balanced_accuracy']['value'] == 0.75
    brier = (0.1**2 + 0.6**2 + 0.6**2 + 0.1**2 + 0.2**2 + 0.3**2 + 0.2**2 + 0.3**2) / 8
    assert s['calibration']['brier'] == pytest.approx(brier)
    assert sum(b['n'] for b in s['calibration']['bins']) == 8


def test_macro_mae_by_hand():
    samples = [
        {'truth': 0, 'prediction': 2},
        {'truth': 0, 'prediction': 0},
        {'truth': 1, 'prediction': 1},
        {'truth': 2, 'prediction': 1},
    ]
    assert ev._macro_mae(samples, 3) == pytest.approx((1 + 0 + 1) / 3)


def test_calibration_needs_scores():
    assert ev.calibration([{'truth': 1, 'prediction': 1}]) is None


def test_ledger_only_grows_and_notices_a_changed_line(tmp_path):
    (tmp_path / 'runtime').mkdir()
    cfg = {'model': 'efficientnet_b0', 'dataset': 'data/snapshots/v1/fold0/dataset.yaml', 'epochs': 30}
    ledger.record_run(tmp_path, 'job1', cfg)
    ledger.record_run(tmp_path, 'job2', {**cfg, 'dataset': 'data/snapshots/v1/fold1/dataset.yaml'})
    ledger.record_run(tmp_path, 'job3', {**cfg, 'epochs': 60})
    first = (tmp_path / ledger.PATH).read_text(encoding='utf-8')
    ledger.record_result(tmp_path, {'report_id': 'r', 'snapshot': 'v1', 'metrics': {'sensitivity': 0.9, 'samples': []}})
    assert (tmp_path / ledger.PATH).read_text(encoding='utf-8').startswith(first), 'old lines never change'
    state = ledger.summary(tmp_path, 'v1')
    assert state == {'settings': 2, 'runs': 3, 'results': 1, 'intact': True}, 'other folds are the same setting'
    (tmp_path / ledger.PATH).write_text(first.replace('job1', 'jobX'), encoding='utf-8')
    assert not ledger.intact(tmp_path)


def test_ledger_holds_no_photos_or_names(tmp_path):
    (tmp_path / 'runtime').mkdir()
    ledger.record_result(tmp_path, {'report_id': 'r', 'metrics': {'accuracy': 1}, 'samples': [{'image_id': 'secret'}]})
    assert 'secret' not in (tmp_path / ledger.PATH).read_text(encoding='utf-8')


def test_attention_map_marks_up_the_photo(tmp_path, monkeypatch):
    from transformers import Dinov2Config, Dinov2Model
    from src.workbench import registry

    folder = tmp_path / 'model'
    Dinov2Model(
        Dinov2Config(hidden_size=32, num_hidden_layers=1, num_attention_heads=2, image_size=28, patch_size=14)
    ).save_pretrained(folder, safe_serialization=True)
    monkeypatch.setattr(registry, 'artifact_path', lambda ident: folder)
    picture = tmp_path / 'a.png'
    Image.fromarray(np.random.default_rng(0).integers(0, 255, (120, 200, 3), dtype=np.uint8)).save(picture)
    overlay = ev._attention('x', picture)
    assert overlay.size == (200, 120) and overlay.mode == 'RGB'
    assert np.abs(np.asarray(overlay, dtype=int) - np.asarray(Image.open(picture), dtype=int)).sum() > 0


def test_baselines_have_no_heat_map(tmp_path, monkeypatch):
    from src.workbench import report_views

    monkeypatch.setattr(report_views, 'get', lambda ident: {'model': 'baseline_colour'})
    with pytest.raises(ValueError, match='基線'):
        ev.heatmap(tmp_path, 'r', 'i')


def test_repeated_group_reports_one_value_per_repeat(tmp_path, monkeypatch):
    from src.workbench import report_views

    def report(fold, repeat, right):
        samples = [
            {
                'image_id': f'{fold}{i}',
                'group': f'g{fold}{i}',
                'truth': i % 2,
                'prediction': i % 2 if right else 1 - i % 2,
                'status': 'ok',
            }
            for i in range(4)
        ]
        return {
            'report_id': f'r{fold}',
            'fold': fold,
            'repeat': repeat,
            'model': 'baseline_colour',
            'task': 'binary_classification',
            'snapshot': 's',
            'expected_folds': 4,
            'evaluated_at': str(fold),
            'training_protocol': {'cv_group': 'a' * 16},
            'metrics': {'kind': 'binary', 'balanced_accuracy': None, 'complete': True},
            'samples': samples,
        }

    reports = [report(0, 0, True), report(1, 0, True), report(2, 1, False), report(3, 1, True)]
    monkeypatch.setattr(report_views, 'listing', lambda: reports)
    (tmp_path / 'runtime').mkdir()
    group = ev.groups(tmp_path)[0]
    assert group['repeats'] == 2 and group['baseline'] and group['complete']
    assert group['mean'] == pytest.approx((1.0 + 0.5) / 2)
    assert group['ledger']['settings'] == 0


def test_reports_with_removed_photos_are_marked_as_unverified(tmp_path):
    cohort(tmp_path, normal=1, positive=1)
    samples = [
        {'image_id': 'p0n0', 'truth': 0, 'prediction': 0, 'status': 'ok'},
        {'image_id': 'gone', 'truth': 1, 'prediction': 1, 'status': 'ok'},
    ]
    assert ev.removed_photos(samples, tmp_path) == 1
    report = {'samples': samples, 'metrics': {'kind': 'binary'}}
    assert any('待驗證' in c for c in ev.report_summary(report, tmp_path)['cautions'])
    assert not any('待驗證' in c for c in ev.report_summary({**report, 'samples': samples[:1]}, tmp_path)['cautions'])
