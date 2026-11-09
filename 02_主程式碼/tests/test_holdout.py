"""B5 (2026-10-17): fixed independent test set, ticked per experiment in 建立實驗."""

import pytest
from fastapi.testclient import TestClient
from src.common import read_json, sha256, write_manifest
from src.data import holdout
from src.data.dataset import build, validate_split
from test_tasks import make_row
from workbench_fixture import configure


@pytest.fixture
def larger(tmp_path):
    rows = []
    for g in range(10):
        rows.append(make_row(tmp_path, f"n{g}", 'negative', 'normal', boxes='', group=f"p{g}"))
        rows.append(make_row(tmp_path, f"a{g}", 'positive', 'stage1', group=f"q{g}"))
        rows.append(make_row(tmp_path, f"b{g}", 'positive', 'stage2', boxes='0 0.5 0.5 0.2 0.2', group=f"r{g}"))
    write_manifest(rows, tmp_path)
    return tmp_path


def members(root, dataset):
    split = validate_split(root / dataset, root)
    return split['members']['train'] + split['members']['val']


@pytest.mark.parametrize('task', ['binary_classification', 'stage_classification'])
def test_test_set_is_held_out_of_every_fold(larger, task):
    info = build(root=larger, task=task)
    source = larger / 'data/snapshots' / info['version'] / 'dataset_version.json'
    before = sha256(source)
    pair = holdout.derive(info['folds'][0]['dataset'], larger)
    assert sha256(source) == before, 'the chosen snapshot is never modified'
    test = members(larger, pair['test_dataset'])
    assert validate_split(larger / pair['test_dataset'], larger)['purpose'] == 'independent_test'
    every = {m['image_id'] for m in members(larger, info['folds'][0]['dataset'])}
    test_ids, test_groups = {m['image_id'] for m in test}, {m['group'] for m in test}
    assert {m['target'] for m in test} == {
        m['target'] for f in info['folds'] for ms in f['members'].values() for m in ms
    }
    assert 0.1 <= len(test_ids) / len(every) <= 0.34
    assert len(pair['folds']) == len(info['folds'])
    for dataset in pair['folds']:
        fold = members(larger, dataset)
        assert {m['image_id'] for m in fold} == every - test_ids
        assert not {m['group'] for m in fold} & test_groups, 'whole case groups stay on one side'
    assert holdout.derive(info['folds'][1]['dataset'], larger) == pair, 'the same pair is reused'


def test_test_set_is_fixed_across_snapshots(larger):
    a = build(root=larger, task='binary_classification', seed=1)
    b = build(root=larger, task='binary_classification', seed=7)
    ta = {m['image_id'] for m in members(larger, holdout.derive(a['folds'][0]['dataset'], larger)['test_dataset'])}
    tb = {m['image_id'] for m in members(larger, holdout.derive(b['folds'][0]['dataset'], larger)['test_dataset'])}
    assert ta == tb


def test_too_little_data_is_refused_clearly(tmp_path):
    rows = []
    for g in range(3):
        rows.append(make_row(tmp_path, f"n{g}", 'negative', 'normal', boxes='', group=f"p{g}"))
        rows.append(make_row(tmp_path, f"a{g}", 'positive', 'stage1', group=f"p{g}"))
    write_manifest(rows, tmp_path)
    info = build(root=tmp_path, task='binary_classification')
    with pytest.raises(ValueError, match='資料不足以保留獨立測試集'):
        holdout.derive(info['folds'][0]['dataset'], tmp_path)
    assert not list((tmp_path / 'data/snapshots').glob('*holdout*')) and not list(
        (tmp_path / 'data/snapshots').glob('*testset*')
    )


def test_derived_snapshot_cannot_be_derived_again(larger):
    info = build(root=larger, task='binary_classification')
    pair = holdout.derive(info['folds'][0]['dataset'], larger)
    with pytest.raises(ValueError, match='衍生快照'):
        holdout.derive(pair['folds'][0], larger)


@pytest.fixture
def app(tmp_path, monkeypatch):
    application, artifact = configure(tmp_path, monkeypatch)
    from src.data import dataset

    original = dataset.validate_split
    monkeypatch.setattr(dataset, 'validate_split', lambda path, root_=None: original(path, root=root_ or tmp_path))
    with TestClient(application) as c:
        c.headers.update({'X-CSRF-Token': c.get('/api/v1/session').json()['csrf'], 'X-Operator': 'test-operator'})
        yield c, tmp_path, artifact


def experiment(dataset, **extra):
    return {'model': 'efficientnet_b0', 'dataset': dataset, 'device': 'cpu', 'demo': True, 'epochs': 1, **extra}


def test_checkbox_controls_the_test_set(app):
    c, root, _ = app
    r = c.post(
        '/api/v1/snapshots', json={'folds': 2, 'seed': 42, 'demo': True, 'task': 'binary_classification'}
    )  # fixture: 6 photos
    assert r.status_code == 200, r.text
    snap = r.json()
    plain = c.post('/api/v1/experiments', json=experiment(snap['folds'][1]['dataset']))
    assert plain.status_code == 200, plain.text
    assert (
        plain.json()['config']['dataset'] == snap['folds'][1]['dataset']
        and 'independent_test' not in plain.json()['config']
    )
    held = c.post('/api/v1/experiments', json=experiment(snap['folds'][1]['dataset'], holdout=True))
    assert held.status_code == 200, held.text
    config = held.json()['config']
    assert (
        config['holdout'] is True
        and '_holdout_' in config['dataset']
        and config['dataset'].endswith('fold1/dataset.yaml')
    )
    assert config['independent_test'].endswith('fold0/dataset.yaml') and '_testset_' in config['independent_test']
    # Only the server chooses the test set.
    forged = c.post(
        '/api/v1/experiments', json=experiment(snap['folds'][0]['dataset'], independent_test=config['independent_test'])
    )
    assert forged.status_code == 400
    cv = c.post(
        '/api/v1/experiments/cross-validation',
        json={'snapshot': snap['version'], 'configs': [experiment('placeholder', holdout=True, name='保留測試')]},
    )
    assert cv.status_code == 200, cv.text
    assert len({j['config']['independent_test'] for j in cv.json()}) == 1 and all(
        '_holdout_' in j['config']['dataset'] for j in cv.json()
    )
    options = c.get('/api/v1/snapshot-options').json()
    purposes = {o['version']: o.get('purpose') for o in options}
    assert purposes[snap['version']] is None and set(purposes.values()) >= {'holdout_training', 'independent_test'}


def test_card_and_three_fold_view_keep_test_results_apart(app):
    c, root, artifact = app
    from test_batch4_evaluation import write_report

    samples = [{'image_id': f'v{i}', 'truth': i % 2, 'prediction': i % 2, 'status': 'ok'} for i in range(10)]
    write_report(
        root,
        'a' * 32,
        samples,
        artifact=artifact['id'],
        extra={
            'artifact_hash': artifact['artifact_hash'],
            'config': artifact['config'],
            'training_protocol': {'cv_group': '1' * 16},
        },
    )
    wrong = [{**s, 'prediction': 1 - s['truth']} for s in samples]
    write_report(
        root,
        'b' * 32,
        wrong,
        artifact=artifact['id'],
        extra={
            'artifact_hash': artifact['artifact_hash'],
            'config': artifact['config'],
            'purpose': 'independent_test',
            'evaluated_at': '2026-10-09T10:00:00Z',
            'training_protocol': {'cv_group': '1' * 16},
        },
    )
    card = c.get(f"/api/v1/artifacts/{artifact['id']}/card").json()
    assert card['evaluation']['report_id'] == 'a' * 32
    assert card['independent_test']['report_id'] == 'b' * 32
    group = next(g for g in c.get('/api/v1/report-groups').json()['items'] if g['cv_group'] == '1' * 16)
    assert [f['report_id'] for f in group['folds']] == ['a' * 32]
