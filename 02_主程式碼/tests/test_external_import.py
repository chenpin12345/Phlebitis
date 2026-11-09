"""Read-only external source import (岡山高醫-style folders) with display names and rule evidence."""

import io
import json
import pytest
from PIL import Image
from src.common import sha256, write_manifest, read_manifest, write_json
from src.data import sources, evidence, tasks
from src.imports import external, service


def jpeg(color, size=(160, 120)):
    buffer = io.BytesIO()
    Image.new('RGB', size, color).save(buffer, 'JPEG', quality=92)
    return buffer.getvalue()


@pytest.fixture
def env(tmp_path):
    root = tmp_path / 'project'
    source = tmp_path / '岡山高醫 來源'
    existing = jpeg((10, 200, 30))
    im = root / 'data/approved/images/legacy_a.jpg'
    im.parent.mkdir(parents=True)
    im.write_bytes(existing)
    lab = root / 'data/approved/annotations/legacy_a.txt'
    lab.parent.mkdir(parents=True)
    lab.write_text('')
    write_manifest(
        [
            dict(
                image_id='legacy_a',
                sha256=sha256(im),
                image_path='data/approved/images/legacy_a.jpg',
                annotation_path='',
                status='approved',
                label_state='negative',
                candidate_group='',
                subject_id='',
                group_verified='false',
                reviewer='m',
                reason='r',
                updated_at='t',
                original_paths=json.dumps(['圖片/一般/20260429_ZZ0601_LH_0_1.jpg']),
            )
        ],
        root,
    )
    files = {
        '01(正常)/20260429_ZZ0601_LH_0_1.jpg': existing,
        '08/20260519_ZZ0801_RH_1_1.jpg': jpeg((200, 30, 30)),
        '08/20260519_ZZ0801_RH_1_2.jpg': jpeg((200, 30, 30)),  # same bytes as _1_1
        '09/20260510_ZZ0101_LL_2_1.jpg': jpeg((30, 30, 200)),
        '13/很長的中文檔名（測試）__多個底線__20260507_ZZ11-01_RH_2_3.jpg': jpeg((90, 90, 20)),
        '13/20260507_ZZ11-01_RH_2_3.jpg': jpeg((20, 90, 90)),
        '13/thermal.csv': b'1,2,3\n',
        '13/broken.jpg': b'not an image',
    }
    for name, data in files.items():
        p = source / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    write_json(
        root / 'configs/import_sources.json',
        {
            'schema_version': 1,
            'sources': {
                'gangshan': {
                    'name': '岡山高醫',
                    'path': str(source),
                    'label_rule': 'gangshan_filename_v1',
                    'alias_source': 'gangshan',
                }
            },
        },
    )
    (root / 'inbox/photos').mkdir(parents=True)
    return root, source, {k: v for k, v in files.items()}


def by_name(item):
    return {e['name']: e for e in item['items']}


def test_scan_is_read_only_and_categorizes(env):
    root, source, files = env
    before = {p: p.stat().st_mtime_ns for p in source.rglob('*') if p.is_file()}
    item = external.scan(root, 'gangshan')
    assert item['state'] == 'ready', item.get('error')
    e = by_name(item)
    assert (
        e['01(正常)/20260429_ZZ0601_LH_0_1.jpg']['category'] == 'existing'
        and e['01(正常)/20260429_ZZ0601_LH_0_1.jpg']['action'] == 'alias'
    )
    assert e['08/20260519_ZZ0801_RH_1_1.jpg']['action'] == 'add'
    assert e['08/20260519_ZZ0801_RH_1_2.jpg']['category'] == 'duplicate_in_source'
    assert e['13/thermal.csv']['action'] == 'reject' and '熱像' in e['13/thermal.csv']['reason']
    assert e['13/broken.jpg']['category'] == 'corrupt'
    wrong = e['13/很長的中文檔名（測試）__多個底線__20260507_ZZ11-01_RH_2_3.jpg']
    assert wrong['category'] == 'bad_name' and wrong['action'] == 'reject'
    assert e['09/20260510_ZZ0101_LL_2_1.jpg']['label']['value'] == 'unknown'
    assert e['13/20260507_ZZ11-01_RH_2_3.jpg']['label']['value'] == 'stage2'
    assert str(source) not in json.dumps(
        service.public(item), ensure_ascii=False
    ), 'full computer paths are not exposed'
    assert before == {p: p.stat().st_mtime_ns for p in source.rglob('*') if p.is_file()}


def test_commit_imports_missing_and_names_existing(env):
    root, source, files = env
    old_revision = tasks.row_revision(read_manifest(root)[0])
    item = external.scan(root, 'gangshan')
    done = external.commit(root, item['id'], 'external:' + item['id'])  # the CLI default key
    assert done['state'] == 'completed', done.get('error')
    rows = read_manifest(root)
    assert len(rows) == 1 + 3, 'three distinct new contents; duplicate in source imported once'
    assert (
        tasks.row_revision(next(r for r in rows if r['image_id'] == 'legacy_a')) == old_revision
    ), 'pure display-name update never changes the row'
    names = sources.load(root)['images']
    assert names['legacy_a']['display_name'] == '20260429_ZZ0601_LH_0_1.jpg'
    dup = by_name(done)['08/20260519_ZZ0801_RH_1_1.jpg']['image_id']
    assert by_name(done)['08/20260519_ZZ0801_RH_1_2.jpg']['image_id'] == dup
    assert (
        names[dup]['conflict'] and names[dup]['display_name'] == '20260519_ZZ0801_RH_1_1.jpg'
    ), 'deterministic choice, aliases kept'
    new_row = next(r for r in rows if r['image_id'] == dup)
    assert (
        new_row['status'] == 'pending_review' and new_row['label_state'] == 'unknown'
    ), 'filename stage is evidence, not a label'
    assert evidence.suggestion(dup, new_row, root)['value'] == 'stage1'
    # Re-running is idempotent: nothing is imported twice.
    again = external.commit(root, external.scan(root, 'gangshan')['id'], 'k2')
    assert again['state'] == 'completed' and len(read_manifest(root)) == 4
    assert len(evidence.read(dup, root)['entries']) == 2, 'one entry per source alias, deduplicated across runs'
    assert all(p.exists() for p in source.rglob('*.jpg'))


def test_interrupted_commit_retry_does_not_duplicate(env, monkeypatch):
    root, source, files = env
    item = external.scan(root, 'gangshan')
    original = sources.save
    calls = {'n': 0}

    def flaky(data, root_):
        calls['n'] += 1
        if calls['n'] == 1:
            raise OSError('injected failure')
        return original(data, root_)

    monkeypatch.setattr(sources, 'save', flaky)
    failed = external.commit(root, item['id'], 'k')
    assert failed['state'] == 'failed'
    retried = external.commit(root, item['id'], 'k', retry=True)
    assert retried['state'] == 'completed', retried.get('error')
    assert len(read_manifest(root)) == 4


def test_same_name_different_content_variants_are_flagged_not_merged():
    rows = [
        {
            'image_id': 'aaaa',
            'image_path': 'data/approved/images/20260424_ZZ0701_RH_2_1_b547a27cc811f866.jpg',
            'original_paths': '["YOLODataset/images/train/20260424_ZZ0701_RH_2_1.jpg"]',
        },
        {
            'image_id': 'bbbb',
            'image_path': 'data/pending_review/annotation/images/20260424_ZZ0701_RH_2_1_3a7c22eac0405d85.jpg',
            'original_paths': '[]',
        },
        {
            'image_id': 'cccc',
            'image_path': 'data/pending_review/unknown_source/images/import_x.jpg',
            'original_paths': '["research_asset:zz"]',
        },
    ]
    found = sources.variants(rows, {'images': {}})
    assert found['aaaa'] == ['bbbb'] and found['bbbb'] == ['aaaa'] and found['cccc'] == []


def test_unlisted_external_source_is_refused(env):
    root, _, _ = env
    with pytest.raises(ValueError, match='未設定'):
        external.source_base(root, 'other')
    result = external.scan(root, 'other')
    assert result['state'] == 'failed' and '未設定' in result['error']


def test_external_copies_are_staged_outside_the_import_area(env):
    root, source, files = env
    item = external.scan(root, 'gangshan')
    done = external.commit(root, item['id'], 'external:' + item['id'])
    assert done['state'] == 'completed', done.get('error')
    staged = root / service.EXTERNAL_STAGING / done['inbox_batch']
    assert not staged.exists(), 'the staged copies go once the photos are in data/'
    added = [e for e in done['items'] if e['action'] == 'add']
    assert added and all(
        (root / r['image_path']).is_file() for r in read_manifest(root) if r['sha256'] in {e['sha256'] for e in added}
    )
    assert not list((root / 'runtime/imports').glob('*.lock')), 'one-off lock files go too'
    assert not any((root / 'inbox/photos').iterdir()), 'the import area holds only what people put there'
    assert service.batches(root, 'photos')['items'] == []


def test_relative_source_path_is_resolved_from_the_workspace(env, monkeypatch):
    root, source, files = env
    from src import paths

    monkeypatch.setattr(paths, 'WORKSPACE_ROOT', source.parent)
    config = json.loads((root / 'configs/import_sources.json').read_text(encoding='utf-8'))
    config['sources']['gangshan']['path'] = source.name
    write_json(root / 'configs/import_sources.json', config)
    base, _ = external.source_base(root, 'gangshan')
    assert base == source.resolve()
    assert external.scan(root, 'gangshan')['state'] == 'ready'


def test_recorded_inbox_paths_resolve_to_the_import_area(tmp_path):
    root = tmp_path / 'project'
    photo = root / 'inbox/photos/b1/x.jpg'
    photo.parent.mkdir(parents=True)
    photo.write_bytes(jpeg((1, 2, 3)))
    assert service.recorded_path(root, photo) == 'inbox/photos/b1/x.jpg'
    assert service.source_path(root, 'inbox/photos/b1/x.jpg') == root / 'inbox/photos/b1/x.jpg'
    staged = root / service.EXTERNAL_STAGING / 'gangshan-1/y.jpg'
    assert service.recorded_path(root, staged) == 'runtime/imports/external/gangshan-1/y.jpg'
    assert service.source_path(root, 'runtime/imports/external/gangshan-1/y.jpg') == staged


def test_import_area_that_is_a_junction_is_refused(tmp_path):
    import subprocess

    root = tmp_path / 'project'
    root.mkdir()
    elsewhere = tmp_path / 'elsewhere'
    (elsewhere / 'photos/b1').mkdir(parents=True)
    made = subprocess.run(['cmd', '/c', 'mklink', '/J', str(root / 'inbox'), str(elsewhere)], capture_output=True)
    if made.returncode != 0:
        pytest.skip('junctions are not available here')
    with pytest.raises(ValueError, match='junction'):
        service.batch_path(root, 'photos', 'b1')
