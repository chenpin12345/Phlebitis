"""Batch 1 (2026-10-17): overview counts, next steps, notifications, global search,
disk usage, settings and the daily backup with restore."""

import json
import time
import zipfile
from src.common import read_manifest, write_json
from src.workbench import jobs, resources
from test_trash import app, wait, do, terminal_job  # noqa: F401
from test_trash_one_step import one_step


def test_overview_content_counts_only_finished_photos(app):
    c, root, _ = app
    data = c.get('/api/v1/overview').json()
    a = data['areas']['cls']
    assert sum(a['confirmed_labels'].values()) == a['progress']['confirmed']
    assert list(data['areas']) == ['cls']


def test_next_steps_lists_pending_work_with_links(app):
    c, root, _ = app
    items = c.get('/api/v1/next-steps').json()['items']
    keys = {i['key']: i for i in items}
    assert 'cls_pending' in keys and keys['cls_pending']['href'].startswith('#data?area=cls')
    assert all(i['text'] and i['action'] and i['href'].startswith('#') for i in items)


def test_job_completion_and_trash_create_notifications(app):
    c, root, _ = app
    ident = terminal_job()
    with jobs.db() as con:
        con.execute("UPDATE jobs SET state='running' WHERE id=?", (ident,))
    jobs.update(ident, 'failed', 'CUDA out of memory')
    jobs.update(ident, 'failed', 'CUDA out of memory')  # repeated update records one notice
    listing = c.get('/api/v1/notifications').json()
    job = [n for n in listing['items'] if n['kind'] == 'job']
    assert len(job) == 1 and job[0]['level'] == 'error' and 'CUDA' in job[0]['body'] and job[0]['href'].endswith(ident)
    do(c, 'move', 'job', terminal_job())
    listing = c.get('/api/v1/notifications').json()
    assert any(n['kind'] == 'trash' and '移至垃圾桶完成' in n['title'] for n in listing['items'])
    assert listing['unread'] >= 2
    after = c.post('/api/v1/notifications/read', json={}).json()
    assert after['unread'] == 0


def test_global_search_groups_and_marks_trash(app):
    c, root, artifact = app
    photos = c.get('/api/v1/search', params={'q': 'p_mismatch'}).json()
    assert photos['groups'][0]['key'] == 'photos' and photos['groups'][0]['items'][0]['id'] == 'p_mismatch'
    model = c.get('/api/v1/search', params={'q': artifact['id']}).json()
    hit = next(g for g in model['groups'] if g['key'] == 'models')['items'][0]
    assert hit['href'].startswith('#models?') and not hit['trash']
    moved = terminal_job()
    do(c, 'move', 'job', moved)
    found = c.get('/api/v1/search', params={'q': moved[:12]}).json()
    job = next(g for g in found['groups'] if g['key'] == 'jobs')['items'][0]
    assert job['trash'] == '在垃圾桶' and job['href'].startswith('#trash?')
    assert c.get('/api/v1/search', params={'q': ''}).json()['total'] == 0


def test_disk_usage_lists_cleanable_outputs_and_cleaning_goes_to_trash(app):
    c, root, _ = app
    c.get('/api/v1/disk-usage?refresh=true')
    usage = wait(c, '/api/v1/disk-usage', finished=lambda d: d['state'] in ('ready', 'failed'))
    assert usage['state'] == 'ready'
    assert {a['key'] for a in usage['areas']} >= {'photos', 'runs', 'models', 'backups', 'database'}
    failed = next(i for i in usage['cleanable'] if i['type'] == 'job' and i['state'] == 'failed')
    assert failed['reason'] == '失敗的工作'
    done = one_step(c, 'move', [{'type': 'job', 'id': failed['id']}])
    assert done['state'] == 'consumed' and resources.record('job', failed['id'])['state'] == 'trashed'


def test_settings_validation(app):
    c, root, _ = app
    current = c.get('/api/v1/settings/workbench').json()
    assert current['spot_check']['ratio'] == 0.05 and 'release' not in current
    bad = c.put('/api/v1/settings/workbench', json={**current, 'spot_check': {'ratio': 2}})
    assert bad.status_code in (400, 422)
    relative = c.put(
        '/api/v1/settings/workbench', json={**current, 'backup': {**current['backup'], 'directory': 'relative/dir'}}
    )
    assert relative.status_code == 400
    ok = c.put('/api/v1/settings/workbench', json={**current, 'notifications': {'system': True}}).json()
    assert ok['notifications']['system'] is True


def test_backup_restore_round_trip(app):
    c, root, _ = app
    first = c.post('/api/v1/backups').json()
    assert first['file_count'] >= 3 and first['database']
    with zipfile.ZipFile(root / 'backups/工作台紀錄' / first['name']) as archive:
        names = set(archive.namelist())
    assert 'data/manifest.csv' in names and 'runtime/workbench/workbench.sqlite3' in names and 'backup.json' in names
    assert not any(n.endswith('.jpg') for n in names), 'photos are not copied'
    # A review made after the backup is removed by the restore; the manifest returns to its state.
    before = (root / 'data/manifest.csv').read_bytes()
    row = next(r for r in read_manifest(root) if r['image_id'] == 'p_000')
    from src.data.tasks import row_revision

    r = c.put(
        '/api/v1/data/p_000/classification',
        json={
            'decision': 'approve',
            'revision': row_revision(row),
            'label': 'negative',
            'stage': 'normal',
            'reviewer': '測試',
            'reason': '備份還原測試',
        },
    )
    assert r.status_code == 200, r.text
    assert (root / 'data/manifest.csv').read_bytes() != before
    newer = list((root / 'data/reviews').glob('*_p_000.json'))
    assert newer
    result = c.post(f"/api/v1/backups/{first['name']}/restore", json={}).json()
    assert result['removed_newer_records'] >= 1 and not result['database']
    assert (root / 'data/manifest.csv').read_bytes() == before
    assert not any(p.exists() for p in newer)
    listing = c.get('/api/v1/backups').json()
    assert any(i['kind'] == 'before-restore' and i['name'] == result['safety_backup'] for i in listing['items'])


def test_backup_restore_refused_while_a_job_runs_and_names_are_checked(app):
    c, root, _ = app
    first = c.post('/api/v1/backups').json()
    ident = terminal_job()
    with jobs.db() as con:
        con.execute("UPDATE jobs SET state='running' WHERE id=?", (ident,))
    r = c.post(f"/api/v1/backups/{first['name']}/restore", json={})
    assert r.status_code == 400 and '正在執行' in r.json()['detail']
    assert c.post('/api/v1/backups/..%5Cevil.zip/restore', json={}).status_code in (400, 404)


def test_backup_rotation_keeps_the_configured_count(app):
    c, root, _ = app
    current = c.get('/api/v1/settings/workbench').json()
    c.put('/api/v1/settings/workbench', json={**current, 'backup': {**current['backup'], 'keep': 2}})
    for _ in range(4):
        c.post('/api/v1/backups')
    manual = [i for i in c.get('/api/v1/backups').json()['items'] if i['kind'] == 'manual']
    assert len(manual) == 2
