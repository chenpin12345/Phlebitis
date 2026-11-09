"""Batch 2 (2026-10-17): 岡山高醫 new-photo detection (A4), duplicate check (A3),
quality flags (A6) and spot checks of rule-classified photos (A5).
Every suggestion needs a person's click before anything is written."""

import io
import time
from PIL import Image
from src.common import read_manifest, write_json, sha256
from src.data import tasks
from src.workbench import flags, spot_check, source_watch
from test_trash import app  # noqa: F401


def jpeg(color, size=(160, 120)):
    buffer = io.BytesIO()
    Image.new('RGB', size, color).save(buffer, 'JPEG', quality=92)
    return buffer.getvalue()


def ready_flags(root):
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        value = flags.current(root, wait=5)
        if value['state'] == 'ready':
            return value
    raise AssertionError('flags not computed')


def test_source_watch_counts_only_new_content_and_never_writes_to_the_source(app, tmp_path):
    c, root, _ = app
    source = tmp_path / '岡山高醫'
    known = root / read_manifest(root)[0]['image_path']
    (source / '01').mkdir(parents=True)
    (source / '01/already.jpg').write_bytes(known.read_bytes())
    (source / '02').mkdir()
    (source / '02/20261017_ZZ0601_LH_1_1.jpg').write_bytes(jpeg((200, 30, 30)))
    (source / '02/notes.csv').write_text('1,2')
    write_json(
        root / 'configs/import_sources.json',
        {
            'schema_version': 1,
            'sources': {
                'gangshan': {
                    'name': '岡山高醫',
                    'path': str(source),
                    'label_rule': 'gangshan_filename_v3',
                    'alias_source': 'gangshan',
                    'auto_apply': True,
                }
            },
        },
    )
    before = {p: (p.stat().st_mtime_ns, p.read_bytes()) for p in source.rglob('*') if p.is_file()}
    state = c.get('/api/v1/source-watch/new?refresh=true').json()
    assert state['available'] and state['count'] == 1 and state['files'] == ['02/20261017_ZZ0601_LH_1_1.jpg']
    assert {p: (p.stat().st_mtime_ns, p.read_bytes()) for p in source.rglob('*') if p.is_file()} == before
    assert c.get('/api/v1/source-watch/new').json()['count'] == 1  # cached answer for the button
    steps = {i['key']: i for i in c.get('/api/v1/next-steps').json()['items']}
    assert steps['source_new']['text'] == '岡山高醫資料夾有 1 張新照片'
    watcher = source_watch.Watcher(root)
    watcher.tick()
    watcher.tick()
    notes = [n for n in c.get('/api/v1/notifications').json()['items'] if n['kind'] == 'new_photos']
    assert len(notes) == 1 and '1 張新照片' in notes[0]['title']


def test_source_watch_without_a_source_is_quiet(app):
    c, root, _ = app
    state = c.get('/api/v1/source-watch/new?refresh=true').json()
    assert state['count'] == 0 and state['available'] is False


def test_quality_flags_and_acknowledgement(app):
    c, root, _ = app
    value = ready_flags(root)
    assert value['quality_ids'], 'flat synthetic photos are flagged as possibly blurred'
    ident = value['quality_ids'][0]
    detail = c.get(f'/api/v1/data/{ident}/flags').json()
    assert detail['quality']['pending'] and any('可能失焦' in r for r in detail['quality']['reasons'])
    page = c.get('/api/v1/data-area', params={'area': 'cls', 'view': 'all', 'flag': 'quality', 'size': 100}).json()
    assert page['total'] == len(value['quality_ids']) and all('quality' in i['flags'] for i in page['items'])
    assert c.post(f'/api/v1/data/{ident}/quality-ack', json={'reviewer': '品管'}).status_code == 200
    assert ident not in ready_flags(root)['quality_ids']
    assert c.get('/api/v1/data-area', params={'area': 'cls', 'flag': 'bogus'}).status_code == 400


def test_duplicate_pairs_need_a_person_and_duplicate_excludes_one_copy(app):
    c, root, _ = app
    value = ready_flags(root)
    pending = [p for p in value['pairs'] if not p['decision']]
    assert pending, 'the synthetic photos share one layout and are near duplicates'
    first, second = pending[0], pending[1]
    r = c.post(
        '/api/v1/duplicates/decision',
        json={'a': first['a'], 'b': first['b'], 'decision': 'not_duplicate', 'reviewer': '品管'},
    )
    assert r.status_code == 200, r.text
    after = ready_flags(root)
    assert next(p for p in after['pairs'] if p['key'] == first['key'])['decision'] == 'not_duplicate'
    rows = {r['image_id']: r for r in read_manifest(root)}
    before_status = rows[second['b']]['status']
    r = c.post(
        '/api/v1/duplicates/decision',
        json={'a': second['a'], 'b': second['b'], 'decision': 'duplicate', 'keep': second['a'], 'reviewer': '品管'},
    )
    assert r.status_code == 200, r.text
    assert r.json()['excluded'] == second['b']
    row = next(r for r in read_manifest(root) if r['image_id'] == second['b'])
    assert tasks.area_state(row, 'cls') == 'excluded' and before_status != 'excluded'
    assert any(
        '重複照片' in (rv.get('after') or {}).get('reason', '')
        for rv in c.get(f"/api/v1/data/{second['b']}/annotation").json()['history']
    )
    bad = c.post(
        '/api/v1/duplicates/decision',
        json={'a': second['a'], 'b': second['a'], 'decision': 'duplicate', 'keep': second['a'], 'reviewer': '品管'},
    )
    assert bad.status_code == 400


def rule_classify(root, ident, stage='normal'):
    from src.data.dataset import review
    from src.data.tasks import row_revision, STAGE_TO_BINARY

    row = next(r for r in read_manifest(root) if r['image_id'] == ident)
    review(
        ident,
        revision=row_revision(row),
        root=root,
        decision='approve',
        label=STAGE_TO_BINARY[stage],
        stage=stage,
        reviewer='依檔名規則（專案負責人授權）',
        reason='規則',
        source='authorized_filename_rule',
    )


def test_spot_check_samples_rule_classified_photos_and_wrong_reopens(app):
    c, root, _ = app
    for ident in ('p_000', 'p_001', 'p_002'):
        rule_classify(root, ident)
    status = spot_check.status(root)
    assert status['auto_total'] == 3 and status['unsampled'] == 3 and status['pending'] == 0
    steps = {i['key'] for i in c.get('/api/v1/next-steps').json()['items']}
    assert 'spot_check_new' not in steps, 'off by default'
    assert c.get('/api/v1/spot-check').json()['enabled'] is False
    prefs = c.get('/api/v1/settings/workbench').json()
    prefs['spot_check']['enabled'] = True
    assert c.put('/api/v1/settings/workbench', json=prefs).status_code == 200
    steps = {i['key'] for i in c.get('/api/v1/next-steps').json()['items']}
    assert 'spot_check_new' in steps
    started = c.post('/api/v1/spot-check/start').json()
    assert len(started['items']) == 1 and started['unsampled'] == 0  # 5 % of 3, at least one
    again = c.post('/api/v1/spot-check/start').json()
    assert [i['image_id'] for i in again['items']] == [
        i['image_id'] for i in started['items']
    ], 'a pending batch is not redrawn'
    item = started['items'][0]
    done = c.post(
        '/api/v1/spot-check/' + item['image_id'],
        json={'correct': False, 'reviewer': '品管', 'revision': item['revision']},
    ).json()
    assert done['pending'] == 0 and done['checked'] == 1 and done['wrong'] == 1
    row = next(r for r in read_manifest(root) if r['image_id'] == item['image_id'])
    assert tasks.area_state(row, 'cls') == 'pending'
    assert (
        c.post('/api/v1/spot-check/' + item['image_id'], json={'correct': True, 'reviewer': '品管'}).status_code == 400
    )


def test_spot_check_correct_keeps_the_classification(app):
    c, root, _ = app
    rule_classify(root, 'p_010', 'normal')
    item = c.post('/api/v1/spot-check/start').json()['items'][0]
    c.post('/api/v1/spot-check/' + item['image_id'], json={'correct': True, 'reviewer': '品管'})
    row = next(r for r in read_manifest(root) if r['image_id'] == item['image_id'])
    assert tasks.area_state(row, 'cls') == 'confirmed' and spot_check.status(root)['checked'] == 1
