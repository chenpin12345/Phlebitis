"""Batch 5 (2026-10-17): LINE activation (the C1 checklist was removed the same day), shadow mode that never replies
(C2) and LINE usage statistics (C3).  No real LINE message is sent: the client is fake."""

import time
from fastapi.testclient import TestClient
from src.common import write_json, read_json, sha256
from src.workbench import registry, shadow, intake
from src.workbench.contracts import InferenceConfig
from src.workbench.metrics import binary_metrics
from test_trash import app  # noqa: F401
from test_line import FakePredictor, FakeLine, settings, post, event, until


def passing_report(root, artifact, *, demo=False, fpr_errors=0, n=40):
    samples = [{'image_id': f'r{i}', 'truth': i % 2, 'prediction': i % 2, 'status': 'ok'} for i in range(n)]
    for i in range(fpr_errors):
        samples[2 * i]['prediction'] = 1  # normal photos judged positive
    report = {
        'artifact': artifact['id'],
        'artifact_hash': artifact['artifact_hash'],
        'config': artifact['config'],
        'model': artifact['model'],
        'metrics': binary_metrics(samples),
        'samples': samples,
        'snapshot': 'fixture',
        'fold': 0,
        'demo_only': demo,
        'evaluated_at': '2026-10-17T00:00:00Z',
        'report_id': 'd' * 32,
    }
    write_json(root / 'runs/workbench/evaluations' / ('d' * 32) / 'report.json', report)


def test_line_activation_needs_only_a_complete_evaluation(app):
    """C1 (release checklist) was removed on 2026-10-17: LINE needs a matching complete evaluation, nothing more."""
    c, root, artifact = app
    assert c.get(f"/api/v1/artifacts/{artifact['id']}/release-check").status_code in (404, 405)
    r = c.post('/api/v1/artifacts/activate', json={'artifact': artifact['id'], 'target': 'line'})
    assert r.status_code == 400 and 'evaluation' in r.json()['detail']
    passing_report(root, artifact, fpr_errors=6)  # weak and a research-demo model: no thresholds any more
    r = c.post('/api/v1/artifacts/activate', json={'artifact': artifact['id'], 'target': 'line'})
    assert r.status_code == 200, r.text
    assert read_json(registry.REFS / 'line.json')['artifact'] == artifact['id']
    card = c.get(f"/api/v1/artifacts/{artifact['id']}/card").json()
    assert 'release' not in card


def test_old_release_settings_are_ignored(app):
    from src.workbench import jobs, settings as prefs
    import json

    with jobs.db() as con:
        con.execute(
            'INSERT OR REPLACE INTO flags(id,data) VALUES(?,?)',
            (prefs.KEY, json.dumps({'spot_check': {'ratio': 0.1}, 'release': {'min_samples': 5}})),
        )
    assert prefs.load().spot_check.ratio == 0.1
    assert 'release' not in app[0].get('/api/v1/settings/workbench').json()


def test_shadow_reference_rules(app):
    c, root, artifact = app
    r = c.post('/api/v1/shadow', json={'artifact': artifact['id']})
    assert r.status_code == 200 and shadow.current()['artifact'] == artifact['id']
    assert c.get('/api/v1/shadow').json()['shadow']['artifact'] == artifact['id']
    c.post('/api/v1/shadow', json={'artifact': None})
    assert shadow.current() is None
    write_json(registry.REFS / 'line.json', {'artifact': artifact['id'], 'previous': None})
    assert c.post('/api/v1/shadow', json={'artifact': artifact['id']}).status_code == 400
    assert c.post('/api/v1/shadow', json={'artifact': 'missing'}).status_code in (400, 404, 409)


class ShadowPredictor(FakePredictor):
    metadata = {'id': 'shadow_model', 'demo_only': True}

    def predict(self, raw):
        self.calls += 1
        return {
            'status': 'not_detected',
            'boxes': [],
            'model_version': 'shadow_model',
            'elapsed_ms': 1,
            'demo_only': True,
            'prediction_score': 0.2,
        }, b''


def test_line_shadow_never_replies_and_records_a_comparison(tmp_path):
    line, main, extra = FakeLine(), FakePredictor(), ShadowPredictor()
    from src.line_bot.service import create_app

    app = create_app(settings(tmp_path), predictor=main, client=line, shadow=extra)
    with TestClient(app) as c:
        post(c, [event()])
        until(lambda: bool(line.sent))
        until(lambda: extra.calls == 1)
        time.sleep(0.1)
    assert len(line.sent) == 1, 'only the main model replies'
    text = str(line.sent[0])
    assert 'not_detected' not in text and '未達' not in text
    from src.workbench import storage

    with storage.db(tmp_path / 'workbench') as con:
        rows = [dict(r) for r in con.execute('SELECT * FROM shadow_predictions')]
    assert (
        len(rows) == 1
        and rows[0]['main_status'] == 'suspected'
        and rows[0]['shadow_status'] == 'not_detected'
        and rows[0]['agree'] == 0
    )
    with storage.db(tmp_path / 'workbench') as con:
        usage = [dict(r) for r in con.execute('SELECT * FROM line_usage')]
    assert len(usage) == 1 and usage[0]['source'] == 'line' and usage[0]['status'] == 'suspected'


def test_shadow_failure_is_recorded_and_harmless(app):
    c, root, artifact = app
    write_json(registry.REFS / 'shadow.json', {'artifact': artifact['id'], 'since': 'now'})

    class Broken:
        metadata = {'id': artifact['id']}

        def predict(self, raw):
            raise RuntimeError('CUDA out of memory')

    shadow.run(Broken(), b'raw', {'status': 'suspected', 'model_version': 'main'}, 'simulator')
    shadow.run(ShadowPredictor(), b'raw', {'status': 'not_detected', 'model_version': 'main'}, 'simulator')
    shadow.run(ShadowPredictor(), b'raw', {'status': 'suspected', 'model_version': 'main'}, 'simulator')
    s = c.get('/api/v1/shadow?period=7').json()
    # Only rows of the current shadow model are counted: the failed run; the two fakes are 'shadow_model'.
    assert s['total'] == 1 and s['failed'] == 1 and s['agreement'] is None
    c.post('/api/v1/shadow', json={'artifact': None})
    s = c.get('/api/v1/shadow?period=all').json()
    assert s['total'] == 3 and s['failed'] == 1 and s['compared'] == 2 and s['agreed'] == 1 and s['agreement'] == 0.5
    assert any('CUDA' in (r['shadow_error'] or '') for r in s['disagreements'])


def test_usage_statistics(app):
    c, root, _ = app
    now = time.time()
    for days, status, offered in [
        (1, 'suspected', True),
        (2, 'not_detected', True),
        (3, 'quality_rejected', False),
        (40, 'suspected', True),
    ]:
        intake.record_usage(
            source='line',
            record={'status': status, 'model_version': 'm'},
            consent_offered=offered,
            clock=lambda d=days: now - d * 86400,
        )
    intake.record_usage(source='simulator', record={'status': 'suspected', 'model_version': 'm'}, consent_offered=True)
    s = c.get('/api/v1/intake/stats?period=30&source=line').json()
    assert (
        s['analyses'] == 3
        and s['quality_rejected'] == 1
        and abs(s['quality_rejected_rate'] - 1 / 3) < 1e-9
        and s['consent_offered'] == 2
    )
    assert s['status'] == {'suspected': 1, 'not_detected': 1, 'quality_rejected': 1} and len(s['series']) == 30
    assert c.get('/api/v1/intake/stats?period=all&source=line').json()['analyses'] == 4
    assert c.get('/api/v1/intake/stats?period=7&source=simulator').json()['analyses'] == 1
    assert c.get('/api/v1/intake/stats?period=5').status_code == 400
