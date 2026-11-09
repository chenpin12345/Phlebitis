"""After a permanent deletion nothing that names the deleted thing is left, except the records
kept on purpose (src/workbench/leftovers.py): lifecycle and request keys, trash history, the
audit log and the experiment ledger."""

import json
import sqlite3
import time
import uuid

import pytest
from PIL import Image

from src.common import read_manifest, sha256, write_json, write_manifest
from src.workbench import jobs, leftovers, registry, resources
from test_trash import app, commit, do, preview, terminal_job, wait  # noqa: F401

KEPT_TABLES = {'resource_lifecycle', 'deleted_job_keys', 'trash_operations', 'trash_steps', 'trash_previews', 'audit'}
KEPT_FILES = {'experiment_ledger.jsonl'}


def mentions(root, text):
    """Every file name, text file and database row in the project that contains `text`."""
    found = []
    for path in root.rglob('*'):
        if not path.is_file():
            continue
        if text in path.as_posix():
            found.append(path.relative_to(root).as_posix())
            continue
        if path.name in KEPT_FILES:
            continue
        if path.suffix in ('.sqlite3',):
            con = sqlite3.connect(f'file:{path}?mode=ro', uri=True)
            for (table,) in con.execute("SELECT name FROM sqlite_master WHERE type='table'"):
                if table in KEPT_TABLES:
                    continue
                cols = [c[1] for c in con.execute(f'PRAGMA table_info({table})')]
                for col in cols:
                    if con.execute(
                        f'SELECT COUNT(*) FROM {table} WHERE instr(CAST({col} AS TEXT),?)>0', (text,)
                    ).fetchone()[0]:
                        found.append(f'{path.name}:{table}.{col}')
            con.close()
        elif path.suffix in ('.json', '.jsonl', '.csv', '.txt', '.log', '.yaml'):
            if text in path.read_text(encoding='utf-8', errors='ignore'):
                found.append(path.relative_to(root).as_posix())
    return found


def evaluated_job(root, artifact):
    """An evaluate job with its report, report index rows and a finished notification."""
    ident = terminal_job('evaluate', {'artifact': artifact['id'], 'dataset': 'fixture'})
    report = root / 'runs/workbench/evaluations' / ident
    (report / 'heatmaps').mkdir(parents=True)
    write_json(
        report / 'report.json',
        {'artifact': artifact['id'], 'model': 'efficientnet_b0', 'metrics': {}, 'samples': [{'image_id': 'x'}]},
    )
    write_json(report / 'progress.json', {'stage': 'done'})
    Image.new('RGB', (8, 8)).save(report / 'heatmaps/x.png')
    with jobs.db() as con:
        con.execute(
            'INSERT INTO report_index(id,path,signature,model,artifact,evaluated,payload) VALUES(?,?,?,?,?,?,?)',
            (
                ident,
                f'runs/workbench/evaluations/{ident}/report.json',
                's',
                'efficientnet_b0',
                artifact['id'],
                'now',
                '{}',
            ),
        )
        con.execute('INSERT INTO report_samples(report,position,image,payload) VALUES(?,?,?,?)', (ident, 0, 'x', '{}'))
    from src.workbench import notifications

    notifications.job_finished(ident, 'evaluate', 'succeeded', {'artifact': artifact['id']}, None)
    return ident


def test_a_purged_job_leaves_nothing(app):
    c, root, artifact = app
    ident = evaluated_job(root, artifact)
    folder = jobs.folder(ident)
    write_json(folder / 'experiment.json', {'requested': {}})
    write_json(folder / 'effective.json', {})
    (folder / 'artifact').mkdir()
    write_json(folder / 'artifact/threshold.json', {'threshold': 0.5})
    (folder / 'official_verification').mkdir()
    (folder / 'official_verification/model.safetensors').write_bytes(b'w' * 64)
    do(c, 'move', 'job', ident)
    op = do(c, 'purge', 'job', ident)
    assert op['state'] == 'completed', op
    assert mentions(root, ident) == []
    assert resources.record('job', ident)['state'] == 'purged'


def test_a_purged_model_leaves_nothing(app):
    c, root, artifact = app
    ident = artifact['id']
    (registry.artifact_path(ident) / 'extra_unlisted.json').write_text('{}', encoding='utf-8')
    with jobs.db() as con:
        con.execute('INSERT OR REPLACE INTO flags(id,data) VALUES(?,?)', ('model_attention:' + ident, '{}'))
    do(c, 'move', 'model', ident)
    op = do(c, 'purge', 'model', ident)
    assert op['state'] == 'completed', op
    left = [
        m
        for m in mentions(root, ident)
        if 'evaluations' not in m and 'report_' not in m and 'jobs/' not in m and not m.startswith('inbox/')
    ]
    assert left == [], left  # reports and jobs belong to their own evaluate jobs; inbox/ is the source package
    assert not registry.artifact_path(ident).exists()


def test_a_purged_snapshot_leaves_nothing(app):
    c, root, _ = app
    from src.data.dataset import build

    info = build(root=root, demo=True)
    version = info['version']
    write_json(root / 'data/snapshot_states.json', {version: {'status': 'superseded'}})
    do(c, 'move', 'snapshot', version)
    op = do(c, 'purge', 'snapshot', version)
    assert op['state'] == 'completed', op
    left = [m for m in mentions(root, version)]
    assert left == [], left


def test_a_purged_photo_leaves_nothing_but_its_hash(app, monkeypatch):
    c, root, _ = app
    from src.data import photo_trash
    from src.workbench.queries import images

    monkeypatch.setattr(photo_trash, '_busy', lambda root: False)
    row = next(r for r in read_manifest(root) if r['status'] == 'approved')
    ident = row['image_id']
    images.render(root, row, True) if hasattr(images, 'render') else None
    staged = root / 'runtime/imports/external/gangshan-x'
    staged.mkdir(parents=True)
    (staged / 'copy.jpg').write_bytes((root / row['image_path']).read_bytes())
    photo_trash.move([ident], 'tester', root)
    photo_trash.purge([ident], 'tester', root)
    left = [
        m
        for m in mentions(root, ident)
        if not m.startswith('runs/') and 'report_samples' not in m and 'deleted_photos' not in m
    ]
    assert left == [], left
    assert not staged.joinpath('copy.jpg').exists()
    assert not list((root / 'runtime/cache/images').glob('*.jpg')) if (root / 'runtime/cache/images').exists() else True


def test_the_sweep_removes_what_older_deletions_left(app):
    c, root, artifact = app
    ident = evaluated_job(root, artifact)
    do(c, 'move', 'job', ident)
    do(c, 'purge', 'job', ident)
    # What a deletion made before 2026-11 left behind.
    old = jobs.folder(ident)
    old.mkdir(parents=True)
    write_json(old / 'request.json', {'id': ident})
    report = root / 'runs/workbench/evaluations' / ident
    report.mkdir(parents=True)
    write_json(report / 'report.json', {})
    from src.workbench import notifications

    notifications.job_finished(ident, 'evaluate', 'succeeded', {'artifact': artifact['id']}, None)
    with jobs.db() as con:
        con.execute(
            'INSERT INTO trash_previews(id,session,created,expires,state,plan) VALUES(?,?,?,?,?,?)',
            ('p', 's', 0, 1, 'ready', '{}'),
        )
    retired = root / leftovers.RETIRED[0]  # a folder of the removed detection model
    retired.mkdir(parents=True)
    (retired / 'settings.json').write_text('{}', encoding='utf-8')
    assert leftovers.audit(root)
    leftovers.sweep(root)
    leftovers.sweep(root)
    left = [m for m in mentions(root, ident) if not m.startswith('before-sweep-')]
    assert left == [], left  # the database copy taken just before the sweep keeps the old rows on purpose
    assert not retired.exists()
    remaining = {k: v for k, v in leftovers.audit(root).items() if k != '縮圖快取'}
    assert remaining == {}, remaining


def test_the_sweep_never_touches_live_things(app):
    c, root, artifact = app
    before_manifest = (root / 'data/manifest.csv').read_bytes()
    live = terminal_job('train')
    leftovers.sweep(root)
    assert (root / 'data/manifest.csv').read_bytes() == before_manifest
    assert jobs.folder(live).exists() and registry.artifact_path(artifact['id']).exists()


def test_clearing_a_simulator_session_removes_its_photo_and_records(app):
    import io

    c, root, _ = app
    from src.workbench import lifecycle, simulation
    from src.workbench.storage import db

    data = io.BytesIO()
    Image.new('RGB', (96, 96), 'red').save(data, format='JPEG')
    asset = lifecycle.upload(data.getvalue())
    simulation.add_message(
        'demo-clear', 'in', 'image', {'image': {'asset': asset['id']}}, 'done', event_id='event-clear'
    )
    store = simulation.store()
    store.db.execute(
        "INSERT INTO jobs(event_id,message_id,status,token,expires,updated) VALUES(?,?,?,?,?,?)",
        ('event-clear', 'message-clear', 'done', 'token-clear', time.time() + 60, time.time()),
    )
    store.db.execute('INSERT INTO results(token,record,expires) VALUES(?,?,?)', ('token-clear', '{}', time.time() + 60))
    store.db.commit()
    store.close()
    simulation.clear_session('demo-clear')
    assert mentions(root, asset['id']) == []
    assert mentions(root, 'event-clear') == [] and mentions(root, 'token-clear') == []


def test_a_purged_research_photo_leaves_no_empty_folder(app):
    from src.workbench import intake

    folder = intake.HOME / 'research_intake' / ('a' * 32)
    folder.mkdir(parents=True)
    leftovers.after_purge('research_photo', 'a' * 32)
    assert not folder.exists()
