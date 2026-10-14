"""Shared LINE conversation rules, research consent, intake, withdrawal and the offline simulator."""
import json
from urllib.parse import parse_qs
import pytest
from fastapi.testclient import TestClient
from src.common import write_json, read_manifest, write_manifest
from src.workbench import intake
from src.workbench.storage import db
from src.line_bot.service import create_app, Settings
from test_line import FakePredictor, FakeLine, post, event, until


@pytest.fixture
def research(tmp_path, monkeypatch):
    root = tmp_path / 'project'
    home = root / 'runtime/workbench'
    write_json(root / 'configs/research_consent.json', {'schema_version': 1, 'line_enabled': True, 'simulator_enabled': True, 'current_version': 'v1',
                                                        'versions': {'v1': {'approved': True, 'title': 'T', 'scope': 's', 'text': '同意說明', 'retention': '至撤回'}}})
    write_manifest([dict(image_id='seed', sha256='0' * 64, image_path='data/pending_review/annotation/images/seed.jpg', annotation_path='', yolo_path='', status='pending_review',
                         label_state='unknown', candidate_group='', subject_id='', group_verified='false', reviewer='', reason='', updated_at='', original_paths='[]')], root)
    monkeypatch.setattr(intake, 'ROOT', root)
    monkeypatch.setattr(intake, 'HOME', home)
    monkeypatch.setattr(intake, '_refresh_index', lambda: None)
    return root, home


def line_app(tmp_path, home, predictor=None, line=None):
    s = Settings('test-secret', 'fake-token', 'https://demo.example', tmp_path / 'unused', runtime=tmp_path / 'line-runtime', research_home=home)
    return create_app(s, predictor=predictor or FakePredictor(), client=line or FakeLine())


def postback(eid, data, user='U-test'):
    return {'type': 'postback', 'webhookEventId': eid, 'replyToken': 'r', 'source': {'type': 'user', 'userId': user}, 'postback': {'data': data}}


def text(eid, value, user='U-test'):
    return {'type': 'message', 'webhookEventId': eid, 'replyToken': 'r', 'source': {'type': 'user', 'userId': user}, 'message': {'type': 'text', 'id': eid, 'text': value}}


def consent_data(sent, decision):
    quick = sent[-1]['quickReply']['items']
    return next(i['action']['data'] for i in quick if i['action']['type'] == 'postback' and parse_qs(i['action']['data'])['decision'][0] == decision)


def intake_rows(home):
    with db(home) as con:
        return [dict(r) for r in con.execute('SELECT * FROM research_intake')]


def test_consent_is_separate_and_prediction_is_not_a_label(tmp_path, research):
    root, home = research
    line = FakeLine()
    with TestClient(line_app(tmp_path, home, line=line)) as c:
        post(c, [event()]); until(lambda: bool(line.sent))
        messages = line.sent[0]
        assert [m['type'] for m in messages] == ['flex', 'image', 'text', 'text'], 'result then a separate consent question'
        data = consent_data(messages, 'accept')
        post(c, [postback('p1', data)]); until(lambda: len(line.sent) == 2)
        assert '已記錄您的研究使用同意' in line.sent[1][0]['text']
        post(c, [postback('p1', data)])  # LINE redelivery of the same event
        post(c, [postback('p2', data)])  # a second tap on the same photo
        until(lambda: len(line.sent) == 3)
        assert '不會重複建立' in line.sent[2][0]['text']
        rows = intake_rows(home)
        assert len(rows) == 1 and rows[0]['binary_label'] == 'unknown' and rows[0]['stage_label'] == 'unknown'
        assert json.loads(rows[0]['prediction'])['status'] == 'suspected' and rows[0]['usage_state'] == 'active'
        # Withdrawal by text command stops use immediately.
        post(c, [text('t1', '撤回研究同意')]); until(lambda: len(line.sent) == 4)
        assert '已撤回 1 張' in line.sent[3][0]['text']
    row = intake_rows(home)[0]
    assert row['usage_state'] == 'withdrawn'
    from src.data import revocations
    assert row['image_sha256'] in revocations.revoked(root)['sha256']


def test_decline_other_user_and_expired_photo(tmp_path, research):
    root, home = research
    line = FakeLine()
    with TestClient(line_app(tmp_path, home, line=line)) as c:
        post(c, [event()]); until(lambda: bool(line.sent))
        accept, decline = consent_data(line.sent[0], 'accept'), consent_data(line.sent[0], 'decline')
        post(c, [postback('x1', accept, user='U-other')]); until(lambda: len(line.sent) == 2)
        assert '只能由傳送照片' in line.sent[1][0]['text']
        post(c, [postback('x2', decline)]); until(lambda: len(line.sent) == 3)
        assert '不同意' in line.sent[2][0]['text'] and not intake_rows(home)
        post(c, [{'type': 'unsend', 'unsend': {'messageId': '123'}}])
        post(c, [postback('x3', accept)]); until(lambda: len(line.sent) == 4)
        assert '已過期' in line.sent[3][0]['text'] and not intake_rows(home)


def test_consent_not_offered_when_disabled(tmp_path, research):
    root, home = research
    cfg = json.loads((root / 'configs/research_consent.json').read_text(encoding='utf-8'))
    cfg['versions']['v1']['approved'] = False
    write_json(root / 'configs/research_consent.json', cfg)
    line = FakeLine()
    with TestClient(line_app(tmp_path, home, line=line)) as c:
        post(c, [event()]); until(lambda: bool(line.sent))
        assert len(line.sent[0]) == 3, 'unapproved consent text is never shown to real LINE users'
        assert not any((tmp_path / 'line-runtime/line_pending').glob('*.jpg')), 'no clean original kept without a consent question'


def accepted_intake(home, simulated=True):
    import uuid
    from PIL import Image
    pending = home / 'p.jpg'; pending.parent.mkdir(parents=True, exist_ok=True)
    Image.new('RGB', (120, 90), (200, 40, 40)).save(pending)
    result = intake.decide(source='simulator' if simulated else 'line', simulated=simulated, user_key='u', session='s', event_id=uuid.uuid4().hex, message_id=uuid.uuid4().hex,
                           result_token='t', version='v1', decision='accept', pending=pending, prediction={'status': 'suspected'})
    return result['intake']


def test_review_promote_and_test_material_excluded(research):
    root, home = research
    ident = accepted_intake(home)
    with pytest.raises(ValueError, match='人工確認'):
        intake.promote(ident, revision=1, actor='研究員')
    row = intake.review(ident, revision=1, state='reviewed', binary_label='positive', stage_label='stage2', quality='acceptable', subject_alias='case01', subject_confirmed=True, note='', actor='研究員')
    result = intake.promote(ident, revision=row['revision'], actor='研究員')
    manifest = {r['image_id']: r for r in read_manifest(root)}
    new = manifest[result['image_id']]
    assert new['status'] == 'pending_review' and new['stage_label'] == 'stage2' and new['usage_state'] == 'test_only'
    from src.data.tasks import eligibility
    approved = dict(new, status='approved')
    assert all('測試素材' in ' '.join(v['reasons']) for v in eligibility(approved).values()), 'simulated material never enters formal training'
    assert intake.promote(ident, revision=row['revision'] + 1, actor='研究員')['status'] == 'already_promoted'


def test_withdrawal_effective_while_compute_and_dataset_locks_busy(research):
    root, home = research
    from src.lock import OperationLock
    from src.workbench.storage import file_lock
    from src.data import revocations
    ident = accepted_intake(home, simulated=False)
    row = intake.review(ident, revision=1, state='reviewed', binary_label='negative', stage_label='normal', quality='acceptable', subject_alias='', subject_confirmed=False, note='', actor='r')
    promoted = intake.promote(ident, revision=row['revision'], actor='r')['image_id']
    with OperationLock(), file_lock(root / 'runtime/data.lock'):
        intake.withdraw_intake(ident, reason='participant request', actor='r')
        table = revocations.revoked(root)
        assert promoted in table['image']
        result = intake.run_cleanup()
        assert result[0]['state'] == 'retry' and '忙碌' in result[0]['error']
    done = intake.run_cleanup()
    assert done[0]['state'] == 'done'
    assert promoted not in {r['image_id'] for r in read_manifest(root)}
    assert not (home / 'research_intake' / ident / 'original.jpg').exists()
    with pytest.raises(ValueError):
        intake.image_path(ident)


def test_simulator_image_result_consent_and_stage_privacy(tmp_path, monkeypatch):
    """Image -> (worker) result + consent question -> postback accept -> simulated intake (test material)."""
    import io
    from PIL import Image
    from workbench_fixture import configure
    from src.workbench import simulation, adapters, jobs
    app, artifact = configure(tmp_path, monkeypatch)

    class FakePredictor:
        metadata = {'extra': {'dataset': 'fixture'}}
        def __init__(self, *a, **k): pass
        def predict(self, raw):
            buffer = io.BytesIO(); Image.new('RGB', (80, 80)).save(buffer, 'JPEG')
            return {'status': 'suspected', 'task_type': 'classification', 'task': 'stage_classification', 'label_scheme': 'stage_v1', 'predicted_class': 'stage2',
                    'class_scores': {'normal': .1, 'stage1': .2, 'stage2': .7}, 'prediction_score': .9, 'binary_prediction': 1, 'model_version': 'm', 'elapsed_ms': 1, 'demo_only': True}, buffer.getvalue()
    monkeypatch.setattr(adapters, 'ModelPredictor', FakePredictor)
    with TestClient(app) as c:
        h = {'x-csrf-token': c.get('/api/v1/session').json()['csrf']}
        buffer = io.BytesIO(); Image.new('RGB', (120, 90), (200, 50, 50)).save(buffer, 'JPEG')
        asset = c.post('/api/v1/assets', content=buffer.getvalue(), headers=h).json()['id']
        sent = c.post('/api/v1/simulation/events', json={'session': 'and', 'type': 'image', 'asset': asset, 'artifact': artifact['id'], 'device': 'cpu', 'development': True, 'event_id': 'img-1', 'message_id': 'mid-1'}, headers=h).json()
        assert sent['status'] == 'queued'
        job = jobs.get(sent['job'])
        folder = jobs.folder(job['id']); folder.mkdir(parents=True, exist_ok=True)
        simulation.process(job['config'], folder)  # what the worker process runs
        bot = [m for m in c.get('/api/v1/simulation/and/messages').json()['items'] if m['direction'] == 'bot']
        assert [m['kind'] for m in bot] == ['flex', 'image', 'text', 'text']
        assert 'stage2' not in json.dumps(bot[0]['payload']) and '疑似陽性' in json.dumps(bot[0]['payload'], ensure_ascii=False), 'patients see only the binary view'
        data = next(i['action']['data'] for i in bot[-1]['payload']['quickReply']['items'] if i['action']['type'] == 'postback' and 'accept' in i['action']['data'])
        accepted = c.post('/api/v1/simulation/events', json={'session': 'and', 'type': 'postback', 'data': data, 'display': '同意研究使用'}, headers=h).json()
        assert '已記錄您的研究使用同意' in accepted['messages'][0]['text']
        items = c.get('/api/v1/intake').json()['items']
        assert len(items) == 1 and items[0]['simulated'] and items[0]['usage_state'] == 'test_only'
        assert items[0]['binary_label'] == 'unknown' and items[0]['prediction']['predicted_class'] == 'stage2', 'prediction stored as reference only'
        other = c.post('/api/v1/simulation/events', json={'session': 'someone-else', 'type': 'postback', 'data': data}, headers=h).json()
        assert '只能由傳送照片' in other['messages'][0]['text']


def test_simulator_uses_shared_rules_without_network(tmp_path, monkeypatch):
    import httpx
    from workbench_fixture import configure
    from src.workbench import simulation
    def forbidden(*args, **kwargs):
        raise AssertionError('offline simulator must not contact LINE')
    from src.line_bot import service
    monkeypatch.setattr(httpx.HTTPTransport, 'handle_request', forbidden)
    monkeypatch.setattr(httpx.AsyncHTTPTransport, 'handle_async_request', forbidden)
    monkeypatch.setattr(service.LineClient, '__init__', forbidden)
    app, artifact = configure(tmp_path, monkeypatch)
    with TestClient(app) as c:
        token = c.get('/api/v1/session').json()['csrf']
        h = {'x-csrf-token': token}
        first = c.post('/api/v1/simulation/events', json={'session': 'ios', 'type': 'text', 'text': '拍照說明', 'event_id': 'e-1', 'message_id': 'm-1'}, headers=h).json()
        assert first['status'] == 'accepted' and first['delivery'] == 'delivered_simulated'
        again = c.post('/api/v1/simulation/events', json={'session': 'ios', 'type': 'text', 'text': '拍照說明', 'event_id': 'e-1', 'message_id': 'm-1'}, headers=h).json()
        assert again['status'] == 'duplicate' and again['retry'], 'retry of the same event is deduplicated'
        messages = c.get('/api/v1/simulation/ios/messages').json()
        assert [m['direction'] for m in messages['items']] == ['user', 'bot']
        assert messages['items'][1]['payload']['quickReply']['items'][0]['action']['type'] == 'message'
        menu = c.get('/api/v1/simulation/rich-menu').json()
        assert len(menu['areas']) == 4 and menu['menu']['size'] == {'width': 2500, 'height': 1686}
        withdraw = c.post('/api/v1/simulation/events', json={'session': 'ios', 'type': 'text', 'text': '撤回研究同意'}, headers=h).json()
        assert '目前沒有生效中的研究使用同意' in withdraw['messages'][0]['text']
        assert c.delete('/api/v1/simulation/ios', headers=h).status_code == 200
        assert c.get('/api/v1/simulation/ios/messages').json()['items'] == []
