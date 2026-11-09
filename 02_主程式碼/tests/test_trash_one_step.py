"""One-step trash actions (2026-10-17): move without a preview dialog, protected items reported
with reasons, purge confirmed by one dialog without typing, undo via one-step restore."""

import json
import time
import uuid
from src.common import write_json
from src.workbench import jobs, registry, resources
from test_trash import app, wait, preview, commit, do, terminal_job  # noqa: F401


def one_step(c, action, targets):
    r = c.post('/api/v1/trash/previews', json={'action': action, 'targets': targets, 'auto_commit': True})
    assert r.status_code == 200, r.text
    return wait(
        c,
        '/api/v1/trash/previews/' + r.json()['id'],
        finished=lambda d: d['state'] not in ('calculating', 'ready') or d.get('blocked'),
    )


def test_one_step_move_and_undo(app):
    c, root, _ = app
    ids = [terminal_job() for _ in range(3)]
    done = one_step(c, 'move', [{'type': 'job', 'id': i} for i in ids])
    assert done['state'] == 'consumed' and done['operation']
    op = wait(c, '/api/v1/trash/operations/' + done['operation'])
    assert op['state'] == 'completed' and all(resources.record('job', i)['state'] == 'trashed' for i in ids)
    undo = one_step(c, 'restore', [{'type': 'job', 'id': i} for i in ids])
    assert undo['state'] == 'consumed' and all(resources.record('job', i)['state'] == 'active' for i in ids)


def test_protected_items_block_with_reasons_and_nothing_is_written(app):
    c, root, artifact = app
    # The model LINE uses is protected; a running job is protected too.
    write_json(registry.REFS / 'line.json', {'artifact': artifact['id'], 'previous': None})
    running = terminal_job()
    with jobs.db() as con:
        con.execute("UPDATE jobs SET state='running' WHERE id=?", (running,))
    free = terminal_job()
    targets = [{'type': 'model', 'id': artifact['id']}, {'type': 'job', 'id': running}, {'type': 'job', 'id': free}]
    result = one_step(c, 'move', targets)
    assert result['state'] == 'ready' and result['blocked'] and not result.get('operation')
    reasons = {i['id']: ' '.join(i['blockers']) for i in result['items'] if i['blockers']}
    assert running in reasons and '工作尚未終止' in reasons[running]
    assert artifact['id'] in reasons and 'LINE正在使用此模型' in reasons[artifact['id']]
    assert all(
        resources.record(t['type'], t['id'])['state'] == 'active' for t in targets
    ), 'a blocked batch writes nothing'
    # "Move the rest" is a new one-step request for the unprotected items only.
    rest = one_step(c, 'move', [{'type': 'job', 'id': free}])
    assert rest['state'] == 'consumed' and resources.record('job', free)['state'] == 'trashed'


def test_one_step_purge_runs_after_confirmation_dialog(app):
    c, root, _ = app
    ident = terminal_job()
    do(c, 'move', 'job', ident)
    done = one_step(c, 'purge', [{'type': 'job', 'id': ident}])
    assert done['state'] == 'consumed'
    op = wait(
        c,
        '/api/v1/trash/operations/' + done['operation'],
        finished=lambda d: d['state'] not in ('preparing', 'running'),
    )
    assert op['state'] == 'completed' and resources.record('job', ident)['state'] == 'purged'


def test_auto_commit_is_idempotent_per_preview(app):
    c, root, _ = app
    ident = terminal_job()
    done = one_step(c, 'move', [{'type': 'job', 'id': ident}])
    with jobs.db() as con:
        ops = con.execute("SELECT COUNT(*) FROM trash_operations WHERE idem=?", ('auto:' + done['id'],)).fetchone()[0]
    assert ops == 1


def test_operation_records_delete_without_typing(app):
    c, root, _ = app
    moved = do(c, 'move', 'job', terminal_job())
    check = c.post('/api/v1/trash/operation-history/delete', json={'ids': [moved['id']]}).json()
    assert check['state'] == 'preview' and check['deletable'] == 1 and 'confirmation' not in check
    done = c.post('/api/v1/trash/operation-history/delete', json={'ids': [moved['id']], 'execute': True}).json()
    assert done['deleted'] == 1
