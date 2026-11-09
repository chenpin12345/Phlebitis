"""Full backup to an external folder: incremental copies, old versions, 30-day retention,
verification, restore into a new folder and reminders.  Everything runs in temporary folders."""

import json
import subprocess
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src import common, paths
from src.workbench import backup, full_backup, settings
from workbench_fixture import configure

DAY = 86400
T0 = time.mktime((2026, 9, 1, 10, 0, 0, 0, 0, -1))


@pytest.fixture
def env(tmp_path, tmp_path_factory, monkeypatch):
    app, _ = configure(tmp_path, monkeypatch)
    external = tmp_path_factory.mktemp('external_drive')
    with TestClient(app) as client:
        client.headers.update({'X-CSRF-Token': client.get('/api/v1/session').json()['csrf'], 'X-Operator': 'test'})
        current = client.get('/api/v1/settings/workbench').json()
        r = client.put(
            '/api/v1/settings/workbench',
            json={**current, 'full_backup': {**current['full_backup'], 'directory': str(external)}},
        )
        assert r.status_code == 200, r.text
        yield client, tmp_path, external / full_backup.BASE_NAME


def name_of(t):
    return time.strftime('%Y%m%d-%H%M%S', time.localtime(t))


def test_incremental_run_keeps_old_versions_and_restores_any_run(env, tmp_path_factory):
    _, root, base = env
    annotation = root / 'data/approved/annotations/a_landscape.txt'
    annotation.parent.mkdir(parents=True, exist_ok=True)
    annotation.write_text('0 0.5 0.5 0.4 0.6\n')
    original_annotation = annotation.read_bytes()
    photo = next((root / 'data/approved/images').glob('*.jpg'))
    original_photo = photo.read_bytes()

    first = full_backup.run(root, now=T0)
    assert first['copied'] == first['total_files'] > 10
    current = base / full_backup.CURRENT
    assert (current / 'data/manifest.csv').is_file() and (current / 'database/workbench.sqlite3').is_file()
    assert (base / full_backup.LISTS / (first['run'] + '.json')).is_file()

    second = full_backup.run(root, now=T0 + 60)
    assert second['copied'] <= 1, 'unchanged photos and records are not copied again'

    annotation.write_text('0 0.4 0.4 0.2 0.2\n')
    photo.unlink()
    third = full_backup.run(root, now=T0 + 120)
    old = base / full_backup.OLD / third['run']
    rel_annotation = 'data/' + annotation.relative_to(root / 'data').as_posix()
    rel_photo = 'data/' + photo.relative_to(root / 'data').as_posix()
    assert (old / rel_annotation).read_bytes() == original_annotation
    assert (old / rel_photo).read_bytes() == original_photo
    assert not (current / rel_photo).exists(), '目前檔案 mirrors the latest state'
    assert (current / rel_annotation).read_text() == '0 0.4 0.4 0.2 0.2\n'

    out = tmp_path_factory.mktemp('restore') / 'first'
    result = full_backup.restore_to(first['run'], out)
    assert result['missing_count'] == 0 and result['restored'] == first['total_files']
    assert (out / rel_annotation).read_bytes() == original_annotation
    assert (out / rel_photo).read_bytes() == original_photo


def test_verify_reports_damaged_and_missing_files(env):
    _, root, base = env
    full_backup.run(root, now=T0)
    assert full_backup.verify()['ok']
    current = base / full_backup.CURRENT
    (current / 'data/manifest.csv').write_text('damaged')
    next((current / 'data/approved/images').glob('*.jpg')).unlink()
    result = full_backup.verify()
    assert not result['ok'] and result['damaged'] == ['data/manifest.csv'] and result['missing_count'] == 1


def test_interrupted_run_is_resumed_under_the_same_name(env):
    _, root, base = env
    full_backup.run(root, now=T0)
    base.joinpath(full_backup.RUNNING).write_text(json.dumps({'run': name_of(T0 + 30)}), encoding='utf-8')
    resumed = full_backup.run(root, now=T0 + 90)
    assert resumed['run'] == name_of(T0 + 30) and resumed['resumed']
    assert not (base / full_backup.RUNNING).exists()


def make_run(base, t, extra_old=True):
    name = name_of(t)
    (base / full_backup.LISTS).mkdir(parents=True, exist_ok=True)
    (base / full_backup.LISTS / (name + '.json')).write_text(json.dumps({'run': name, 'finished': t, 'files': {}}))
    if extra_old:
        folder = base / full_backup.OLD / name / 'data'
        folder.mkdir(parents=True)
        (folder / 'old.txt').write_text('old version')
    return name


def test_retention_removes_only_old_versions_older_than_the_limit(tmp_path):
    base = tmp_path / full_backup.BASE_NAME
    now = T0 + 60 * DAY
    old1 = make_run(base, now - 40 * DAY)
    old2 = make_run(base, now - 31 * DAY)
    kept = make_run(base, now - 29 * DAY)
    future = make_run(base, now + 2 * DAY)
    newest = make_run(base, now, extra_old=False)
    (base / full_backup.OLD / '自己建立的資料夾').mkdir()
    (base / full_backup.CURRENT).mkdir()
    (base / full_backup.CURRENT / 'keep.txt').write_text('latest')
    result = full_backup.prune(base, 30, now=now)
    assert {r['folder'] for r in result['removed']} == {old1, old2}
    assert set(result['removed_lists']) == {old1, old2}
    assert (base / full_backup.OLD / kept).is_dir() and (base / full_backup.OLD / future).is_dir()
    assert (base / full_backup.OLD / '自己建立的資料夾').is_dir()
    assert (base / full_backup.LISTS / (newest + '.json')).is_file()
    assert (base / full_backup.CURRENT / 'keep.txt').read_text() == 'latest'
    reasons = {s['folder']: s['reason'] for s in result['skipped']}
    assert '未來' in reasons[future] and '格式' in reasons['自己建立的資料夾']
    log = json.loads((base / full_backup.PRUNE_LOG).read_text(encoding='utf-8'))
    assert log['entries'][-1]['freed_bytes'] == 2 * len('old version')


def test_retention_never_removes_the_newest_list(tmp_path):
    base = tmp_path / full_backup.BASE_NAME
    only = make_run(base, T0)
    result = full_backup.prune(base, 30, now=T0 + 90 * DAY)
    assert result['removed_lists'] == [] and (base / full_backup.LISTS / (only + '.json')).is_file()


def test_retention_skips_folders_containing_junctions(tmp_path):
    base = tmp_path / full_backup.BASE_NAME
    name = make_run(base, T0)
    make_run(base, T0 + 60 * DAY, extra_old=False)
    elsewhere = tmp_path / 'elsewhere'
    elsewhere.mkdir()
    (elsewhere / 'precious.txt').write_text('not part of the backup')
    link = base / full_backup.OLD / name / 'link'
    made = subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(elsewhere)], capture_output=True)
    if made.returncode != 0:
        pytest.skip('junctions are not available here')
    result = full_backup.prune(base, 30, now=T0 + 60 * DAY)
    assert result['removed'] == [] and 'junction' in result['skipped'][0]['reason']
    assert (elsewhere / 'precious.txt').read_text() == 'not part of the backup'


def test_failed_run_does_not_prune(env, monkeypatch):
    _, root, base = env
    full_backup.run(root, now=T0)
    stale = base / full_backup.OLD / name_of(T0 - 90 * DAY)
    stale.mkdir(parents=True)
    make_run(base, T0 - 90 * DAY, extra_old=False)

    def broken(source, target):
        raise OSError('外接硬碟已移除')

    monkeypatch.setattr(full_backup, '_copy', broken)
    (root / 'data/manifest.csv').write_text((root / 'data/manifest.csv').read_text(encoding='utf-8-sig') + '\n')
    with pytest.raises(OSError):
        full_backup.run(root, now=T0 + 60)
    assert stale.is_dir(), 'nothing is removed when the backup did not finish'


def test_target_inside_the_data_area_is_refused(env):
    client, root, _ = env
    current = client.get('/api/v1/settings/workbench').json()
    inside_real = str(common._STORE / 'data/backup')
    r = client.put(
        '/api/v1/settings/workbench',
        json={**current, 'full_backup': {**current['full_backup'], 'directory': inside_real}},
    )
    assert r.status_code == 400
    s = settings.load()
    (root / 'data/sub').mkdir()
    settings.save(
        {**s.model_dump(), 'full_backup': {**s.full_backup.model_dump(), 'directory': str(root / 'data/sub')}}
    )
    with pytest.raises(ValueError, match='不能放在'):
        full_backup.run(root, now=T0)


def test_restore_refuses_non_empty_or_project_folders(env, tmp_path_factory):
    client, root, _ = env
    first = full_backup.run(root, now=T0)
    busy = tmp_path_factory.mktemp('busy')
    (busy / 'x.txt').write_text('x')
    r = client.post(f"/api/v1/full-backups/{first['run']}/restore-to", json={'output': str(busy)})
    assert r.status_code == 400 and '空資料夾' in r.json()['detail']
    r = client.post(f"/api/v1/full-backups/{first['run']}/restore-to", json={'output': str(common._STORE / 'restore')})
    assert r.status_code == 400
    r = client.post('/api/v1/full-backups/..%5Cevil/restore-to', json={'output': str(busy / 'new')})
    assert r.status_code in (400, 404)


def test_api_runs_in_background_and_reports_progress(env):
    client, root, base = env
    assert client.get('/api/v1/full-backups').json()['due'] is True
    started = client.post('/api/v1/full-backups')
    assert started.status_code == 200 and started.json()['state'] == 'running'
    finished = full_backup.wait()
    assert finished['state'] == 'done', finished
    view = client.get('/api/v1/full-backups').json()
    assert view['available'] and len(view['runs']) == 1 and view['due'] is False
    assert view['status']['last_success'] and view['runs'][0]['total_files'] > 10
    client.post('/api/v1/full-backups/verify')
    assert full_backup.wait()['result']['ok']


def test_reminders_after_seven_days_and_after_new_imports(env):
    _, root, _ = env
    now = time.time()
    assert any(k.startswith('full-backup-due:') for k in full_backup.remind(root, now=now))
    full_backup.run(root, now=now)
    assert full_backup.remind(root, now=now + DAY) == []
    assert any(k.startswith('full-backup-due:') for k in full_backup.remind(root, now=now + 8 * DAY))
    from src.imports import service

    with service.store(root) as con:
        con.execute(
            'INSERT INTO imports(id,kind,batch,state,created,updated,session,idem,payload) VALUES(?,?,?,?,?,?,?,?,?)',
            ('a' * 32, 'photos', 'b', 'completed', now + 10, now + 10, 's', None, '{}'),
        )
    assert any(k.startswith('full-backup-after-import:') for k in full_backup.remind(root, now=now + DAY))


def test_isolated_roots_never_write_into_the_real_backup_folder(env):
    _, root, _ = env
    real = paths.BACKUP_ROOT
    before = sorted(p.as_posix() for p in real.rglob('*')) if real.exists() else []
    backup.create('manual', root)
    full_backup.run(root, now=T0)
    assert backup.directory(root) == root / 'backups/工作台紀錄'
    after = sorted(p.as_posix() for p in real.rglob('*')) if real.exists() else []
    assert before == after


def test_deep_folders_beyond_windows_path_limit_are_backed_up(env, tmp_path_factory):
    """The Hugging Face cache under models/pretrained is deep; backup paths pass 260 characters."""
    _, root, base = env
    deep = (
        full_backup._long(root / 'models/pretrained')
        / ('very-long-folder-name-' * 4)
        / ('another-long-folder-' * 4)
        / ('x' * 60)
    )
    deep.mkdir(parents=True)
    (deep / 'model.safetensors').write_bytes(b'weights')
    assert len(str(deep / 'model.safetensors')) - 4 > 260 or len(str(base)) + 200 > 260
    result = full_backup.run(root, now=T0)
    assert result['total_files'] > 10
    assert full_backup.verify()['ok']
    out = tmp_path_factory.mktemp('restore_deep') / 'r'
    restored = full_backup.restore_to(result['run'], out)
    assert restored['missing_count'] == 0 and not restored['output'].startswith(r'\\?')
