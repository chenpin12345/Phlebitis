"""M2.5: source check, photo removal, patients, leakage guards."""

import io
import json
import random

import numpy as np
import pytest
from PIL import Image

from src.common import read_manifest, sha256, write_manifest
from src.data import dataset, evidence, filename_rules, remove_source, source_rules, sources, tasks
from src.workbench import source_audit

OLD = remove_source.OLD_FOLDER
COLUMNS = (
    'image_id sha256 image_path annotation_path status label_state candidate_group subject_id group_verified '
    'reviewer reason updated_at original_paths stage_label label_scheme quality_state cls_review'
).split()


def picture(path, seed, size=(96, 96), colour=None, fmt='JPEG'):
    rng = np.random.default_rng(seed)
    pixels = rng.integers(0, 255, (size[1], size[0], 3), dtype=np.uint8)
    if colour is not None:
        pixels = (pixels * 0.1 + np.array(colour) * 0.9).astype(np.uint8)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(pixels).save(path, format=fmt)


def row(root, ident, *, status='approved', label='positive', stage='stage1', original='', subject='', **image):
    path = root / f'data/{status if status != "pending_review" else "pending_review/annotation"}'
    path = path / 'images' / f'{ident}.jpg'
    picture(path, abs(hash(ident)) % 2**31, **image)
    return {
        **dict.fromkeys(COLUMNS, ''),
        'image_id': ident,
        'sha256': sha256(path),
        'image_path': path.relative_to(root).as_posix(),
        'status': status,
        'label_state': label,
        'stage_label': stage if status == 'approved' else '',
        'label_scheme': 'stage_v1' if status == 'approved' else '',
        'subject_id': subject,
        'group_verified': 'true' if subject else 'false',
        'original_paths': json.dumps([original] if original else []),
        'cls_review': {'approved': 'confirmed', 'excluded': 'excluded'}.get(status, 'pending'),
    }


def gangshan(code, side='LH', stage=1, n=1):
    return f'岡山高醫/2026010112_{code}_{side}_{stage}_{n}.jpg'


def test_source_check_catches_a_planted_shortcut(tmp_path):
    rows = []
    for i in range(12):  # Normal photos all from another camera, with another size and colour.
        rows.append(
            row(
                tmp_path,
                f'o{i}',
                label='negative',
                stage='normal',
                original=f'x/IMG_{i}.jpg',
                size=(160, 120),
                colour=(40, 90, 200),
            )
        )
    for i in range(12):
        rows.append(row(tmp_path, f'g{i}', original=gangshan(f'ZZ{i}'), colour=(200, 90, 40)))
    write_manifest(rows, tmp_path)
    result = source_audit.check(tmp_path)
    assert result['level'] == 'high'
    assert result['label_from_metadata']['balanced_accuracy'] > 0.9
    assert result['source_from_colour']['balanced_accuracy'] > 0.9
    assert abs(result['label_from_metadata']['shuffled_labels'] - 0.5) < 0.2
    assert {r['source']: r['normal'] for r in result['crosstab']} == {'gangshan': 0, 'other': 12}
    assert result['findings']


def test_source_check_says_when_there_is_only_one_source(tmp_path):
    rows = [row(tmp_path, f'g{i}', original=gangshan(f'ZZ{i}')) for i in range(6)]
    write_manifest(rows, tmp_path)
    result = source_audit.check(tmp_path)
    assert result['level'] == 'single_source'
    assert '一個來源' in result['findings'][0]


def test_source_check_notices_a_size_only_one_class_has(tmp_path):
    rows = [row(tmp_path, f'n{i}', label='negative', stage='normal', original=gangshan(f'ZZ{i}')) for i in range(6)]
    rows += [row(tmp_path, f'p{i}', original=gangshan(f'ZZ{i + 9}'), size=(80, 120)) for i in range(6)]
    rows += [row(tmp_path, f'q{i}', original=gangshan(f'ZZ{i + 19}'), size=(120, 80)) for i in range(2)]
    write_manifest(rows, tmp_path)
    result = source_audit.check(tmp_path)
    assert {'size': '120×80', 'normal': 0, 'positive': 8} in result['sizes'], 'turned photos count together'
    assert result['level'] in ('watch', 'high')
    assert any('120×80 的 8 張全是陽性' in text for text in result['findings'])


def test_results_never_hold_codes_or_filenames(tmp_path):
    rows = [
        row(tmp_path, f'g{i}', subject=f'ZZ{i % 2}', original=gangshan(f'ZZ{i % 2}'), label=label, stage=stage)
        for i, (label, stage) in enumerate([('negative', 'normal')] * 4 + [('positive', 'stage1')] * 4)
    ]
    write_manifest(rows, tmp_path)
    text = json.dumps(source_audit.run(tmp_path), ensure_ascii=False)
    assert 'ZZ0' not in text and 'ZZ1' not in text and '.jpg' not in text


def removal_set(root):
    rows = [
        row(root, 'img0', label='negative', stage='normal', original=f'archive/legacy/{OLD}/images/train/IMG_0001.jpg'),
        row(
            root,
            'img1',
            status='pending_review',
            label='unknown',
            original=f'archive/legacy/{OLD}/images/val/IMG_0002.jpg',
        ),
        # This hospital's photo in the old folder, without an import alias: it stays.
        row(
            root,
            'keep0',
            status='excluded',
            label='unknown',
            original=f'archive/legacy/{OLD}/images/train/{gangshan("ZZ1").split("/")[1]}',
        ),
        row(root, 'keep1', original=gangshan('ZZ2')),
    ]
    write_manifest(rows, root)
    (root / f'archive/legacy/{OLD}/labels').mkdir(parents=True)
    (root / f'archive/legacy/{OLD}/labels/a.txt').write_text('x', encoding='utf-8')
    for ident in ('img0', 'keep1'):
        evidence.append(ident, {'task': 'classification', 'source': 'human_review', 'method': 'review'}, root)
        (root / 'data/reviews').mkdir(exist_ok=True)
        (root / f'data/reviews/20260101T000000000000Z_{ident}.json').write_text('{}', encoding='utf-8')
    (root / 'data/spot_checks.json').write_text(
        json.dumps(
            {
                'schema_version': 1,
                'samples': [{'image_id': 'img0', 'state': 'correct'}],
                'considered': ['img0', 'keep1'],
            }
        ),
        encoding='utf-8',
    )
    (root / 'data/duplicate_decisions.json').write_text(
        json.dumps(
            {
                'schema_version': 1,
                'pairs': {'img0|keep1': {'decision': 'different'}, 'keep0|keep1': {'decision': 'different'}},
            }
        ),
        encoding='utf-8',
    )
    return rows


def test_removal_preview_changes_nothing(tmp_path):
    removal_set(tmp_path)
    before = (tmp_path / 'data/manifest.csv').read_bytes()
    plan = remove_source.preview(tmp_path)
    assert plan['photos'] == 2 and plan['kept'] == 2 and plan['archive_files'] == 1
    assert (tmp_path / 'data/manifest.csv').read_bytes() == before
    assert not (tmp_path / remove_source.DESTINATION).exists()


def test_removal_moves_only_the_selected_photos_and_can_rerun(tmp_path):
    rows = removal_set(tmp_path)
    kept = {r['image_id']: r for r in rows if r['image_id'].startswith('keep')}
    result = remove_source.apply(tmp_path, expect=2)
    assert result['changed'] == 2 and result['archive_moved']
    assert (tmp_path / result['backup']).is_file()
    after = {r['image_id']: r for r in read_manifest(tmp_path)}
    assert after == kept, 'other photos keep every field'
    base = tmp_path / remove_source.DESTINATION
    assert (base / 'images/img0.jpg').is_file() and (base / 'images/img1.jpg').is_file()
    assert (base / OLD / 'labels/a.txt').is_file() and not (tmp_path / remove_source.ARCHIVE).exists()
    assert (base / 'records/data/reviews/20260101T000000000000Z_img0.json').is_file()
    assert (tmp_path / 'data/reviews/20260101T000000000000Z_keep1.json').is_file()
    assert not evidence.path('img0', tmp_path).exists() and evidence.path('keep1', tmp_path).exists()
    spot = json.loads((tmp_path / 'data/spot_checks.json').read_text(encoding='utf-8'))
    assert spot['samples'] == [] and spot['considered'] == ['keep1']
    decided = json.loads((tmp_path / 'data/duplicate_decisions.json').read_text(encoding='utf-8'))
    assert list(decided['pairs']) == ['keep0|keep1']
    assert 'photos' in json.loads((base / '清單.json').read_text(encoding='utf-8'))
    assert remove_source.apply(tmp_path, expect=2)['changed'] == 0, 'repeatable'


def test_removal_stops_when_the_count_is_not_the_expected_one(tmp_path):
    removal_set(tmp_path)
    with pytest.raises(ValueError, match='預期 37'):
        remove_source.apply(tmp_path, expect=37)
    assert len(read_manifest(tmp_path)) == 4
    assert (tmp_path / remove_source.ARCHIVE).exists()


def test_interrupted_removal_can_finish(tmp_path, monkeypatch):
    removal_set(tmp_path)
    real = remove_source._forget_in_decisions

    def crash(root, ids):
        raise OSError('power cut')

    monkeypatch.setattr(remove_source, '_forget_in_decisions', crash)
    with pytest.raises(OSError):
        remove_source.apply(tmp_path, expect=2)
    monkeypatch.setattr(remove_source, '_forget_in_decisions', real)
    (tmp_path / remove_source.DESTINATION / 'records').mkdir(exist_ok=True)
    assert remove_source.apply(tmp_path, expect=2)['changed'] == 2
    assert {r['image_id'] for r in read_manifest(tmp_path)} == {'keep0', 'keep1'}


def test_hyphenated_codes_are_one_patient(tmp_path):
    assert filename_rules.record_code(gangshan('ZZ12-01')) == filename_rules.record_code(gangshan('ZZ1201'))
    rows = [row(tmp_path, 'a', original=gangshan('ZZ12-01')), row(tmp_path, 'b', original=gangshan('zz1201'))]
    write_manifest(rows, tmp_path)
    assert source_rules.assign_subjects(tmp_path)['changed'] == 2
    after = read_manifest(tmp_path)
    assert {r['subject_id'] for r in after} == {'ZZ1201'} and {r['group_verified'] for r in after} == {'true'}
    assert source_rules.assign_subjects(tmp_path)['changed'] == 0, 'repeatable'


def test_assignment_keeps_a_patient_set_by_a_person_and_skips_other_photos(tmp_path):
    rows = [
        row(tmp_path, 'a', original=gangshan('ZZ1'), subject='ZZ9'),
        row(tmp_path, 'b', status='excluded', label='unknown', original=gangshan('ZZ2')),
        row(tmp_path, 'c', original='x/IMG_1.jpg'),
    ]
    write_manifest(rows, tmp_path)
    assert source_rules.assign_subjects(tmp_path)['changed'] == 0
    assert [r['subject_id'] for r in read_manifest(tmp_path)] == ['ZZ9', '', '']


def test_filling_patients_keeps_reviews_attached():
    before = {
        'image_id': 'a',
        'status': 'approved',
        'cls_review': 'confirmed',
        'subject_id': '',
        'group_verified': 'false',
    }
    after = {**before, 'subject_id': 'ZZ1', 'group_verified': 'true'}
    assert tasks.row_revision(before) == tasks.row_revision(after)


def cohort(root, patients=6, *, normal=3):
    rows = []
    for p in range(patients):
        label, stage = ('negative', 'normal') if p < normal else ('positive', 'stage1')
        for n in range(3):
            rows.append(
                row(root, f'p{p}n{n}', label=label, stage=stage, subject=f'ZZ{p}', original=gangshan(f'ZZ{p}', n=n))
            )
    write_manifest(rows, root)
    return rows


def test_unassigned_photos_block_every_snapshot(tmp_path):
    rows = cohort(tmp_path)
    rows[0].update(subject_id='', group_verified='false')
    write_manifest(rows, tmp_path)
    for demo in (True, False):
        with pytest.raises(ValueError, match='病人分組'):
            dataset.build(root=tmp_path, demo=demo)


def test_snapshot_groups_do_not_carry_the_record_number(tmp_path):
    cohort(tmp_path)
    info = dataset.build(root=tmp_path, demo=True)
    text = (tmp_path / f"data/snapshots/{info['version']}/fold0/split.json").read_text(encoding='utf-8')
    assert 'patient_' in text and '"ZZ0"' not in text and 'ZZ1' not in text


def test_each_fold_needs_a_normal_patient(tmp_path):
    cohort(tmp_path, normal=2)
    with pytest.raises(ValueError, match='只來自 2 位病人'):
        dataset.build(root=tmp_path, demo=True, folds=3)


def test_near_duplicates_of_two_patients_across_folds_are_refused(tmp_path):
    rows = cohort(tmp_path)
    copy = tmp_path / rows[-1]['image_path']
    Image.open(tmp_path / rows[0]['image_path']).save(copy, format='JPEG', quality=70)  # same picture, other patient
    rows[-1]['sha256'] = sha256(copy)
    groups = [tasks.group_key(r) for r in rows]
    train = [i for i in range(len(rows)) if i != len(rows) - 1]
    problems = dataset.leakage(rows, groups, [(train, [len(rows) - 1])], tmp_path)
    assert any('近似' in p for p in problems)


def test_same_patient_on_both_sides_is_refused(tmp_path):
    rows = cohort(tmp_path)
    groups = [tasks.group_key(r) for r in rows]
    problems = dataset.leakage(rows, groups, [([0], [1])], tmp_path)
    assert any('同一位病人' in p for p in problems)


def test_shuffled_labels_keep_validation_and_class_counts():
    members = [
        {'image_id': str(i), 'label_state': 'positive' if i % 3 else 'negative', 'stage_label': '', 'target': 'x'}
        for i in range(30)
    ]
    split = {'members': {'train': members, 'val': [dict(members[0])]}}
    mixed = tasks.shuffled_labels(split, 1)
    assert mixed['members']['val'] == split['members']['val']
    assert [m['image_id'] for m in mixed['members']['train']] == [m['image_id'] for m in members]
    assert sorted(m['label_state'] for m in mixed['members']['train']) == sorted(m['label_state'] for m in members)
    assert [m['label_state'] for m in mixed['members']['train']] != [m['label_state'] for m in members]
    assert split['members']['train'] == members, 'the snapshot itself is not touched'


def test_shuffled_labels_score_about_chance():
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import balanced_accuracy_score

    rng = np.random.default_rng(0)
    labels = ['negative', 'positive'] * 100
    x = np.array([[1.5 * (v == 'positive')] for v in labels]) + rng.normal(size=(200, 1))
    train = [{'label_state': v, 'stage_label': '', 'target': v} for v in labels[:140]]
    honest, control = [], []
    for seed in range(20):
        mixed = tasks.shuffled_labels({'members': {'train': train, 'val': []}}, seed)['members']['train']
        for out, source in ((honest, train), (control, mixed)):
            model = LogisticRegression().fit(x[:140], [m['label_state'] for m in source])
            out.append(balanced_accuracy_score(labels[140:], model.predict(x[140:])))
    assert np.mean(honest) > 0.7
    assert abs(np.mean(control) - 0.5) < 0.1


def test_control_model_cannot_be_activated(monkeypatch, tmp_path):
    from src.workbench import registry

    monkeypatch.setattr(registry, 'ROOT', tmp_path)
    monkeypatch.setattr(registry, 'get', lambda ident: {'extra': {'control': 'shuffled_labels'}})
    monkeypatch.setattr(registry, 'guarded', lambda f: f, raising=False)
    with pytest.raises(ValueError, match='不能啟用'):
        registry.activate.__wrapped__('x') if hasattr(registry.activate, '__wrapped__') else registry.activate('x')


def test_formal_snapshot_needs_no_approval_step(tmp_path):
    cohort(tmp_path)
    info = dataset.build(root=tmp_path)
    assert 'demo' not in info['version'] and 'approval' not in info


def test_inventory_numbers_patients_and_warns_about_few_normal_patients(tmp_path):
    rows = cohort(tmp_path)
    rows.append(row(tmp_path, 'loose', original='x/IMG_1.jpg'))
    write_manifest(rows, tmp_path)
    data = source_audit.inventory(tmp_path)
    assert (
        data['patients'] == 6
        and data['normal_patients'] == 3
        and data['normal_photos'] == 9
        and data['unassigned'] == 1
    )
    assert data['rows'][0]['label'] == '病人 01'
    assert 'ZZ' not in json.dumps(data, ensure_ascii=False)
    assert any('流程驗證' in w for w in data['warnings']) and any('沒有病人分組' in w for w in data['warnings'])


def test_origin_counts_hospital_filenames_without_an_alias():
    photo = {'image_id': 'a', 'original_paths': json.dumps([f'{OLD}/{gangshan("ZZ1").split("/")[1]}'])}
    assert sources.origin(photo, None) == 'gangshan'
    assert sources.origin({'image_id': 'b', 'original_paths': '["x/IMG_1.jpg"]'}, None) == 'other'
    assert sources.origin({'image_id': 'line_1', 'original_paths': '[]'}, None) == 'line'
    assert sources.origin({'image_id': 'c', 'original_paths': '[]'}, {'display_name': 'x.jpg'}) == 'gangshan'


def test_photos_without_an_import_record_still_show_their_filename(tmp_path):
    photo = {'image_id': 'a', 'original_paths': json.dumps([f'{OLD}/images/train/20260101_ZZ1_LH_1_1.jpg'])}
    data = {'images': {}}
    assert sources.lookup('a', data, row=photo)['display_name'] == '20260101_ZZ1_LH_1_1.jpg'
    assert sources.lookup('a', data)['display_name'] is None
    tag = {'image_id': 'b', 'original_paths': '["research_asset:1"]'}
    assert sources.lookup('b', data, row=tag)['display_name'] is None, 'provenance tags are not filenames'


def test_only_the_confirmed_name_format_is_standard():
    assert filename_rules.is_standard('x/20260101_ZZ1-2_LH_1_1.jpg')
    for name in ('20260101 ZZ1_LH_1_1.jpg', '2026010112_ZZ1_LH_1_1.jpg', '20260101_ZZ1_LH_1.jpg', 'IMG_0001.jpg'):
        assert not filename_rules.is_standard(name), name


def test_removing_nonstandard_names_keeps_the_rest_and_forgets_the_alias(tmp_path):
    bad = row(tmp_path, 'bad', original='岡山高醫/20260101 ZZ1_LH_1_1.jpg')
    long = row(tmp_path, 'long', original='岡山高醫/2026010112_ZZ2_LH_1_1.jpg')
    good = row(tmp_path, 'good', original='岡山高醫/20260101_ZZ3_LH_1_1.jpg')
    write_manifest([bad, long, good], tmp_path)
    (tmp_path / remove_source.ARCHIVE).mkdir(parents=True)
    (tmp_path / 'data/image_sources.json').write_text(
        json.dumps({'schema_version': 1, 'images': {'bad': {'aliases': []}, 'good': {'aliases': []}}}), encoding='utf-8'
    )
    kwargs = {'choose': remove_source.nonstandard, 'destination': remove_source.NONSTANDARD_DESTINATION}
    assert remove_source.preview(tmp_path, remove_source.nonstandard)['photos'] == 2
    assert remove_source.apply(tmp_path, expect=2, **kwargs)['changed'] == 2
    assert [r['image_id'] for r in read_manifest(tmp_path)] == ['good']
    assert (tmp_path / remove_source.NONSTANDARD_DESTINATION / 'images/bad.jpg').is_file()
    assert (tmp_path / remove_source.ARCHIVE).exists(), 'the old folder is not part of this removal'
    assert list(sources.load(tmp_path)['images']) == ['good']
    assert remove_source.apply(tmp_path, expect=2, **kwargs)['changed'] == 0, 'repeatable'


def test_old_index_rows_are_rebuilt_after_an_upgrade(tmp_path, monkeypatch):
    from src.workbench.queries import data_index

    asked = []
    monkeypatch.setattr(data_index, 'request_rebuild', asked.append)
    monkeypatch.setattr(data_index, 'signature', lambda root, full=False: 's')
    now = __import__('time').time()
    fresh = {'state': 'ready', 'signature': 's', 'checked_at': now, 'projection': data_index.PROJECTION}
    for value, expected in (
        (fresh, 0),
        ({**fresh, 'projection': None}, 1),
        ({**fresh, 'state': 'stale'}, 1),
    ):
        asked.clear()
        monkeypatch.setattr(data_index, 'state', lambda root, v=value: v)
        data_index.freshness(tmp_path)
        assert len(asked) == expected


def test_sealed_test_patients_stay_out_of_training_and_unlock_once(tmp_path):
    from src.data import prospective
    from src.workbench import ledger

    (tmp_path / 'runtime').mkdir()
    cohort(tmp_path, patients=8)
    seen = prospective.register('新病人', ['zz-7', ' ZZ7 ', ''], 'test', 'tester', tmp_path)
    assert seen['count'] == 1 and seen['role_name'] == '測試'
    assert 'ZZ7' not in (tmp_path / 'data/prospective/list-0001.json').read_text(encoding='utf-8')
    info = dataset.build(root=tmp_path, demo=True)
    groups = {m['group'] for m in info['folds'][0]['members']['train'] + info['folds'][0]['members']['val']}
    assert tasks.group_key({'subject_id': 'ZZ7'}) not in groups and len(groups) == 7
    assert prospective.unlock('list-0001', 'tester', tmp_path)['unlocked_at']
    with pytest.raises(ValueError, match='已解鎖過'):
        prospective.unlock('list-0001', 'tester', tmp_path)
    assert tasks.group_key({'subject_id': 'ZZ7'}) in prospective.reserved(tmp_path), 'still never trained on'
    assert [r['event'] for r in ledger.read(tmp_path)] == ['prospective_sealed', 'prospective_unlocked']


def test_development_patients_may_be_trained_on_and_one_patient_has_one_role(tmp_path):
    from src.data import prospective

    (tmp_path / 'runtime').mkdir()
    cohort(tmp_path)
    prospective.register('開發', ['ZZ1'], 'development', 'tester', tmp_path)
    assert prospective.reserved(tmp_path) == set()
    with pytest.raises(ValueError, match='只能有一個角色'):
        prospective.register('測試', ['ZZ1'], 'test', 'tester', tmp_path)
    with pytest.raises(ValueError, match='角色'):
        prospective.register('x', ['ZZ2'], 'other', 'tester', tmp_path)


def test_a_changed_list_cannot_be_unlocked(tmp_path):
    from src.data import prospective

    (tmp_path / 'runtime').mkdir()
    write_manifest([row(tmp_path, 'a', subject='ZZ1')], tmp_path)
    prospective.register('n', ['ZZ1'], 'test', 'tester', tmp_path)
    path = tmp_path / 'data/prospective/list-0001.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    data['patients'] = ['other']
    path.write_text(json.dumps(data), encoding='utf-8')
    with pytest.raises(ValueError, match='封存雜湊不符'):
        prospective.unlock('list-0001', 'tester', tmp_path)


def test_data_card_has_no_filenames_or_codes(tmp_path):
    from src.workbench import cards

    cohort(tmp_path)
    source_audit.run(tmp_path)
    text = cards.data_markdown(tmp_path)
    assert '兩位醫師核准' in text and '病人 01' in text and 'ZZ' not in text and '.jpg' not in text


@pytest.mark.parametrize('text', ['20260101_ZZ1_LH_1_1.jpg', '20260101 ZZ1_RH_2', 'x_LL_2_1', 'candidate:ZZ1'])
def test_exports_with_a_filename_shape_are_refused(text):
    from src.workbench import cards

    with pytest.raises(ValueError, match='檔名樣式'):
        cards._safe('報告 ' + text)
