"""Deleting a photo removes everything that exists because of it, and only that."""

import json

import pytest
from PIL import Image

from src.common import read_json, read_manifest, sha256, write_json, write_manifest
from src.data import dataset, evidence, photo_trash, revocations, tasks
from src.workbench import source_watch
from test_tasks import make_row

NAME = '20260101_ZZ1_LH_1_1.jpg'


@pytest.fixture
def project(tmp_path, monkeypatch):
    from src.workbench import registry

    monkeypatch.setattr(photo_trash, '_busy', lambda root: False)
    monkeypatch.setattr(photo_trash, '_mark_models', lambda root, names: None)
    monkeypatch.setattr(registry, 'metadata_listing', lambda: [])
    monkeypatch.setattr('src.workbench.ledger.append', lambda root, entry: None)
    rows = []
    for g in range(6):
        label, stage = ('negative', 'normal') if g < 3 else ('positive', 'stage1')
        rows += [make_row(tmp_path, f'p{g}n{i}', label, stage, group=f'p{g}') for i in range(2)]
    target = rows[6]
    target['original_paths'] = json.dumps([f'岡山高醫/{NAME}'])
    note = tmp_path / 'data/approved/annotations/p3n0.txt'
    note.parent.mkdir(parents=True, exist_ok=True)
    note.write_text('x', encoding='utf-8')
    target['annotation_path'] = note.relative_to(tmp_path).as_posix()
    (note.parent / 'p3n0_unlisted.txt').write_text('y', encoding='utf-8')  # a box file the manifest never named
    other = rows[7]
    other['reason'] = f'與「{NAME}」為同一拍攝'
    write_manifest(rows, tmp_path)
    write_json(
        tmp_path / 'data/reviews/20260101T000000000000Z_p3n1.json',
        {'after': other, 'task': 'classification', 'area': 'cls'},
    )
    write_json(tmp_path / 'data/reviews/20260101T000000000000Z_p3n0.json', {'after': target})
    evidence.append('p3n0', {'task': 'classification', 'source': 'human_review', 'method': 'review'}, tmp_path)
    write_json(
        tmp_path / 'data/image_sources.json',
        {
            'schema_version': 1,
            'images': {
                'p3n0': {
                    'aliases': [{'filename': NAME, 'source': 'gangshan', 'relative_path': NAME}],
                    'display_name': NAME,
                }
            },
        },
    )
    write_json(tmp_path / 'data/quality_reviews.json', {'images': {'p3n0': {}, 'p3n1': {}}})
    write_json(tmp_path / 'data/duplicate_decisions.json', {'pairs': {'p3n0|p3n1': {}, 'p0n0|p0n1': {}}})
    info = dataset.build(root=tmp_path, demo=True)
    report = tmp_path / 'runs/workbench/evaluations/r1'
    (report / 'heatmaps').mkdir(parents=True)
    Image.new('RGB', (64, 64)).save(report / 'p3n0.jpg')
    Image.new('RGB', (64, 64)).save(report / 'heatmaps/p3n0.png')
    Image.new('RGB', (64, 64)).save(report / 'p0n0.jpg')
    write_json(
        report / 'report.json', {'samples': [{'image_id': 'p3n0'}, {'image_id': 'p0n0'}], 'metrics': {'accuracy': 0.5}}
    )
    features = tmp_path / 'runtime/workbench/features'
    features.mkdir(parents=True)
    (features / 'k.npy').write_bytes(b'x')
    write_json(features / 'k.json', {'image_id': 'p3n0'})
    write_json(tmp_path / 'runtime/imports/pixel_cache.json', {target['sha256']: {}, rows[0]['sha256']: {}})
    journal = tmp_path / 'runtime/review_transactions/t1'
    write_json(journal / 'journal.json', {'state': 'committed', 'files': [], 'note': 'p3n0'})
    return tmp_path, info, target, other


def tree(root):
    return {
        p.relative_to(root).as_posix(): sha256(p)
        for p in (root / 'data').rglob('*')
        if p.is_file() and 'snapshots' not in p.parts
    }


def test_preview_changes_nothing_and_counts_the_copies(project):
    root, _, target, _ = project
    before = tree(root)
    plan = photo_trash.preview(['p3n0'], root)
    assert plan['photos'] == 1 and plan['approved'] == 1 and plan['snapshots'] == 1 and plan['reports'] == 1
    assert plan['patients_lost'] == 0 and plan['bytes'] > (root / target['image_path']).stat().st_size
    assert tree(root) == before


def test_move_stops_use_at_once_and_restore_brings_back_every_file(project):
    root, info, target, _ = project
    before = tree(root)
    assert photo_trash.move(['p3n0'], 'tester', root) == {'moved': 1}
    assert 'p3n0' not in {r['image_id'] for r in read_manifest(root)}
    assert not (root / target['image_path']).exists()
    assert not (root / 'data/reviews/20260101T000000000000Z_p3n0.json').exists()
    with pytest.raises(ValueError, match='withdrawn'):
        dataset.validate_split(root / info['folds'][0]['dataset'], root)
    assert photo_trash.listing(root)['items'][0]['name'] == NAME
    photo_trash.restore(['p3n0'], 'tester', root)
    after = tree(root)
    assert {k: v for k, v in after.items() if k != 'data/manifest.csv' and 'image_sources' not in k} == {
        k: v for k, v in before.items() if k != 'data/manifest.csv' and 'image_sources' not in k
    }
    assert 'p3n0' in {r['image_id'] for r in read_manifest(root)}
    assert 'p3n0' in read_json(root / 'data/image_sources.json')['images']
    assert not revocations.is_revoked({'image_id': 'p3n0', 'sha256': ''}, revocations.revoked(root))
    assert not (root / photo_trash.FOLDER / 'p3n0').exists()


def test_purge_leaves_nothing_behind_except_numbers_and_a_hash(project):
    root, info, target, other = project
    photo_trash.move(['p3n0'], 'tester', root)
    result = photo_trash.purge(['p3n0'], 'tester', root)
    assert result['deleted'] == 1 and result['snapshots'] == 1 and result['bytes'] > 0
    leftovers = [p for p in root.rglob('*') if 'p3n0' in p.name]
    assert not leftovers, leftovers
    assert (root / 'runs/workbench/evaluations/r1/p0n0.jpg').exists(), 'other photos keep theirs'
    assert read_json(root / 'runs/workbench/evaluations/r1/report.json')['metrics'] == {'accuracy': 0.5}
    assert not (root / 'runtime/workbench/features/k.npy').exists()
    assert list(read_json(root / 'runtime/imports/pixel_cache.json')) != [target['sha256']]
    assert target['sha256'] not in read_json(root / 'runtime/imports/pixel_cache.json')
    assert not (root / 'runtime/review_transactions/t1').exists()
    assert list(read_json(root / 'data/duplicate_decisions.json')['pairs']) == ['p0n0|p0n1']
    assert list(read_json(root / 'data/quality_reviews.json')['images']) == ['p3n1']
    assert target['sha256'] in photo_trash.tombstones(root)
    state = read_json(root / 'data/snapshot_states.json')[info['version']]
    assert state['status'] == 'contains_deleted'


def test_the_filename_leaves_other_records_and_their_reviews_still_match(project):
    root, _, _, other = project
    photo_trash.move(['p3n0'], 'tester', root)
    photo_trash.purge(['p3n0'], 'tester', root)
    row = next(r for r in read_manifest(root) if r['image_id'] == 'p3n1')
    assert NAME not in row['reason'] and photo_trash.RENAMED in row['reason']
    after = read_json(root / 'data/reviews/20260101T000000000000Z_p3n1.json')['after']
    assert tasks.row_revision(after) == tasks.row_revision(row)
    for path in (root / 'data').rglob('*.json'):
        if 'snapshots' not in path.parts:
            assert NAME not in path.read_text(encoding='utf-8'), path


def test_a_purged_photo_is_not_offered_again(project):
    root, _, target, _ = project
    photo_trash.move(['p3n0'], 'tester', root)
    assert target['sha256'] in source_watch._known(root), 'also while it is in the trash'
    photo_trash.purge(['p3n0'], 'tester', root)
    assert target['sha256'] in source_watch._known(root)


def test_nothing_moves_while_a_job_is_running(project, monkeypatch):
    root, *_ = project
    monkeypatch.setattr(photo_trash, '_busy', lambda root: True)
    before = tree(root)
    for action in (photo_trash.move, photo_trash.restore, photo_trash.purge):
        with pytest.raises(ValueError, match='工作正在執行'):
            action(['p3n0'], 'tester', root)
    assert tree(root) == before


def test_unknown_photos_and_paths_are_refused(project):
    root, *_ = project
    with pytest.raises(ValueError, match='不在系統內'):
        photo_trash.move(['nope'], 'tester', root)
    with pytest.raises(ValueError, match='無效'):
        photo_trash.purge(['../manifest'], 'tester', root)
    with pytest.raises(ValueError, match='操作者'):
        photo_trash.move(['p3n0'], ' ', root)


def test_leftover_cleaning_keeps_current_and_trashed_photos(project):
    root, *_ = project
    report = root / 'runs/workbench/evaluations/r1'
    Image.new('RGB', (64, 64)).save(report / 'gone.jpg')
    Image.new('RGB', (64, 64)).save(report / 'heatmaps/gone.png')
    photo_trash.move(['p3n0'], 'tester', root)
    assert photo_trash.clean_leftover_copies(root)['files'] == 2
    assert (report / 'p0n0.jpg').exists() and (report / 'p3n0.jpg').exists()


def test_report_images_come_from_the_snapshot_then_the_project(project, monkeypatch):
    from src.workbench import registry, report_views

    root, info, target, _ = project
    monkeypatch.setattr(registry, 'ROOT', root)
    report = {
        'snapshot': info['version'],
        'samples': [{'image_id': 'p3n0'}, {'image_id': 'p0n1'}, {'image_id': 'gone'}],
    }
    monkeypatch.setattr(report_views, 'get', lambda ident: report)
    (root / 'runs/workbench/evaluations/r2').mkdir(parents=True)
    assert report_views.image_path('r2', 'p3n0').parent.name == 'images', 'the picture that was evaluated'
    report['snapshot'] = None
    assert report_views.image_path('r2', 'p0n1').name == 'p0n1.jpg'
    with pytest.raises(FileNotFoundError, match='已從系統刪除'):
        report_views.image_path('r2', 'gone')


def twins(root):
    rows = read_manifest(root)
    next(r for r in rows if r['image_id'] == 'p4n0')['original_paths'] = json.dumps([f'岡山高醫/{NAME}'])
    write_manifest(rows, root)


def test_a_photo_sharing_the_filename_keeps_its_name(project):
    root, *_ = project
    twins(root)
    photo_trash.move(['p3n0'], 'tester', root)
    assert photo_trash.purge(['p3n0'], 'tester', root)['deleted'] == 1
    after = {r['image_id']: r for r in read_manifest(root)}
    assert NAME in after['p4n0']['original_paths'], 'the other photo is not touched'
    assert NAME in after['p3n1']['reason'], 'the name still belongs to a photo in the project'


def test_a_twin_still_in_the_trash_keeps_the_name(project):
    root, *_ = project
    twins(root)
    photo_trash.move(['p3n0', 'p4n0'], 'tester', root)
    photo_trash.purge(['p3n0'], 'tester', root)
    assert NAME in {i['name'] for i in photo_trash.listing(root)['items']}
    photo_trash.restore(['p4n0'], 'tester', root)
    assert NAME in next(r for r in read_manifest(root) if r['image_id'] == 'p4n0')['original_paths']


def test_purging_both_twins_removes_the_name(project):
    root, *_ = project
    twins(root)
    photo_trash.move(['p3n0', 'p4n0'], 'tester', root)
    photo_trash.purge(['p3n0', 'p4n0'], 'tester', root)
    assert NAME not in (root / 'data/manifest.csv').read_text(encoding='utf-8-sig')


def test_the_one_time_exception_leaves_no_trace_but_later_deletions_do(project):
    root, _, target, other = project
    photo_trash.move(['p3n0', 'p3n1'], 'tester', root)
    assert target['sha256'] in source_watch._known(root)
    assert photo_trash.allow_return(['p3n0'], root) == {'marked': 1}
    assert target['sha256'] not in source_watch._known(root), 'offered again while in the trash'
    assert other['sha256'] in source_watch._known(root), 'the other photo was not exempted'
    assert not revocations.is_revoked({'image_id': 'p3n0', 'sha256': ''}, revocations.revoked(root))
    photo_trash.purge(['p3n0', 'p3n1'], 'tester', root)
    assert target['sha256'] not in photo_trash.tombstones(root)
    assert other['sha256'] in photo_trash.tombstones(root)


def test_a_new_deletion_never_inherits_the_exception(project):
    root, _, target, _ = project
    photo_trash.move(['p3n0'], 'tester', root)
    photo_trash.allow_return(['p3n0'], root)
    photo_trash.restore(['p3n0'], 'tester', root)
    photo_trash.move(['p3n0'], 'tester', root)
    assert target['sha256'] in photo_trash.in_trash_hashes(root)
    photo_trash.purge(['p3n0'], 'tester', root)
    assert target['sha256'] in photo_trash.tombstones(root)


def test_purging_the_old_record_keeps_a_photo_that_was_imported_again(project):
    root, info, target, _ = project
    photo_trash.move(['p3n0'], 'tester', root)
    photo_trash.allow_return(['p3n0'], root)
    stored = root / photo_trash.FOLDER / 'p3n0/files'
    picture = next(p for p in stored.iterdir() if p.suffix == '.jpg')
    back = root / 'data/approved/images/import_again.jpg'
    back.write_bytes(picture.read_bytes())
    rows = read_manifest(root)
    write_manifest(
        rows + [{**target, 'image_id': 'import_again', 'image_path': back.relative_to(root).as_posix()}], root
    )
    with pytest.raises(ValueError, match='已重新匯入'):
        photo_trash.restore(['p3n0'], 'tester', root)
    photo_trash.purge(['p3n0'], 'tester', root)
    assert back.exists() and 'import_again' in {r['image_id'] for r in read_manifest(root)}
    assert NAME in (root / 'data/manifest.csv').read_text(encoding='utf-8-sig'), 'its filename stays'
    assert not (root / photo_trash.FOLDER / 'p3n0').exists()
    assert target['sha256'] not in photo_trash.tombstones(root)
