"""Batch 4 (2026-10-17): three-fold runs (B1), report summary with intervals (B2), error
gallery (B3), Grad-CAM heat maps (B4), snapshot differences (B7) and model cards (B8)."""

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from src.common import write_json, read_json
from src.workbench import evaluation_views, registry, jobs
from src.workbench.contracts import InferenceConfig
from src.workbench.metrics import binary_metrics, multiclass_metrics
from workbench_fixture import configure


@pytest.fixture
def app(tmp_path, monkeypatch):
    application, artifact = configure(tmp_path, monkeypatch, include_reports=True)
    with TestClient(application) as c:
        c.headers.update({'X-CSRF-Token': c.get('/api/v1/session').json()['csrf'], 'X-Operator': 'test-operator'})
        yield c, tmp_path, artifact


def write_report(
    root, rid, samples, *, artifact='historical', model='efficientnet_b0', fold=0, extra=None, multiclass=None
):
    directory = root / 'runs/workbench/evaluations' / rid
    metrics = multiclass_metrics(samples, multiclass) if multiclass else binary_metrics(samples)
    report = {
        'artifact': artifact,
        'artifact_hash': 'synthetic',
        'model': model,
        'snapshot': 'fixture',
        'fold': fold,
        'evaluated_at': f'2026-10-0{fold + 1}T10:00:00Z',
        'config': InferenceConfig().model_dump(),
        'metrics': metrics,
        'samples': samples,
        'demo_only': True,
        'expected_folds': 3,
        **(extra or {}),
    }
    if multiclass:
        report.update(classes=multiclass, label_scheme='stage_v1', task='stage_classification')
    write_json(directory / 'report.json', report)
    for s in samples:
        Image.new('RGB', (120, 90), 'teal').save(directory / (s['image_id'] + '.jpg'))
    return report


def test_wilson_and_bootstrap_are_correct_and_reproducible():
    lo, hi = evaluation_views.wilson(9, 10)
    assert lo == pytest.approx(0.596, abs=0.002) and hi == pytest.approx(0.982, abs=0.002)
    assert evaluation_views.wilson(0, 0) is None
    samples = [{'truth': i % 2, 'prediction': (i % 2) if i % 5 else 1 - (i % 2)} for i in range(40)]
    a = evaluation_views.bootstrap(samples, evaluation_views._binary_ba)
    assert a == evaluation_views.bootstrap(samples, evaluation_views._binary_ba) and a[0] < 0.8 < a[1]


def test_report_summary_plain_language_and_errors(app):
    c, root, _ = app
    samples = [
        {'image_id': f'p_{n:03}', 'group': f'g{n // 2}', 'truth': n % 2, 'prediction': n % 2, 'status': 'ok'}
        for n in range(20)
    ]
    samples[1]['prediction'] = 0  # a missed positive
    samples[2]['prediction'] = 1  # a false alarm
    samples[3]['image_id'] = 'gone_from_manifest'
    samples[3]['prediction'] = 0
    write_report(root, 'a' * 32, samples)
    s = c.get('/api/v1/reports/' + 'a' * 32 + '/summary').json()
    keys = {m['key']: m for m in s['metrics']}
    assert keys['sensitivity']['count'] == '8/10' and keys['false_positive_rate']['count'] == '1/10'
    lo, hi = keys['sensitivity']['ci']
    assert lo < 0.8 < hi
    assert any('在 10 張陽性照片中找出 8 張' in l for l in s['lines'])
    assert any('只有 20 張驗證照片' in x for x in s['cautions']) and any('流程展示' in x for x in s['cautions'])
    assert s['matrix'] == {'kind': 'binary', 'tp': 8, 'fn': 2, 'fp': 1, 'tn': 9}
    e = c.get('/api/v1/reports/' + 'a' * 32 + '/errors').json()
    groups = {g['key']: g for g in e['groups']}
    assert e['total'] == 3 and len(groups['missed']['items']) == 2 and len(groups['false_alarm']['items']) == 1
    missed = {i['image_id']: i for i in groups['missed']['items']}
    assert (
        missed['p_001']['review_href'] == '#data?area=cls&view=all&image=p_001'
        and missed['gone_from_manifest']['review_href'] is None
    )


def test_multiclass_summary(app):
    c, root, _ = app
    classes = ['normal', 'stage1', 'stage2']
    samples = [
        {'image_id': f'm{n}', 'truth': n % 3, 'prediction': n % 3 if n % 4 else (n + 1) % 3, 'status': 'ok'}
        for n in range(30)
    ]
    write_report(root, 'b' * 32, samples, model='efficientnet_b0', multiclass=classes)
    s = c.get('/api/v1/reports/' + 'b' * 32 + '/summary').json()
    assert (
        s['metrics'][0]['key'] == 'macro_f1'
        and s['matrix']['kind'] == 'multiclass'
        and len(s['matrix']['confusion_matrix']) == 3
    )
    assert any(l.startswith('正常 10 張中判對') for l in s['lines'])


def test_three_fold_groups_pool_folds(app):
    c, root, _ = app
    for fold in range(3):
        samples = [
            {
                'image_id': f'f{fold}_{n}',
                'group': f'g{fold}{n}',
                'truth': n % 2,
                'prediction': n % 2 if n != fold else 1 - n % 2,
                'status': 'ok',
            }
            for n in range(10)
        ]
        write_report(
            root,
            str(fold + 3) * 32,
            samples,
            fold=fold,
            extra={'training_protocol': {'cv_group': '0123456789abcdef', 'name': '三折 · fold %d' % fold}},
        )
    items = c.get('/api/v1/report-groups').json()['items']
    g = next(i for i in items if i['cv_group'] == '0123456789abcdef')
    assert g['complete'] and g['fold_count'] == 3 and g['pooled']['n'] == 30 and g['name'] == '三折'
    assert g['mean'] == pytest.approx(0.9, abs=0.05) and g['sd'] is not None
    assert c.get('/api/v1/report-groups/0123456789abcdef/errors').json()['total'] == 3


def test_cross_validation_queues_one_job_per_fold(app, monkeypatch):
    c, root, _ = app
    from src.data import dataset

    original = dataset.validate_split
    monkeypatch.setattr(dataset, 'validate_split', lambda path, root_=None: original(path, root=root))
    snapshot = c.post('/api/v1/snapshots', json={'folds': 3, 'seed': 42, 'demo': True, 'task': 'binary_classification'})
    assert snapshot.status_code == 200, snapshot.text
    version = snapshot.json()['version']
    r = c.post(
        '/api/v1/experiments/cross-validation',
        json={
            'snapshot': version,
            'configs': [
                {
                    'model': 'efficientnet_b0',
                    'dataset': 'placeholder',
                    'device': 'cpu',
                    'demo': True,
                    'epochs': 1,
                    'name': '三折測試',
                }
            ],
        },
    )
    assert r.status_code == 200, r.text
    created = r.json()
    groups = {j['config']['cv_group'] for j in created}
    assert len(created) == 3 and len(groups) == 1
    assert sorted(j['config']['dataset'].split('/')[-2] for j in created) == ['fold0', 'fold1', 'fold2']
    assert [j['config']['name'] for j in created] == ['三折測試 · fold 0', '三折測試 · fold 1', '三折測試 · fold 2']
    listing = c.get('/api/v1/jobs-query').json()['items']
    assert sum(j['config'].get('cv_group') in groups for j in listing) == 3
    bad = c.post(
        '/api/v1/experiments/cross-validation', json={'snapshot': '../evil', 'configs': [{'model': 'efficientnet_b0'}]}
    )
    assert bad.status_code == 400


def test_snapshot_diff(app):
    c, root, _ = app

    def snapshot(version, members):
        write_json(
            root / 'data/snapshots' / version / 'dataset_version.json',
            {
                'version': version,
                'task': 'binary_classification',
                'name': version[-4:],
                'folds': [
                    {
                        'fold': 0,
                        'members': {
                            'train': [{'image_id': k, 'target': v} for k, v in members.items()][:-1],
                            'val': [{'image_id': k, 'target': v} for k, v in members.items()][-1:],
                        },
                    }
                ],
            },
        )

    snapshot('demo_binary_20261001T000000Z', {'a': 'positive', 'b': 'negative', 'c': 'positive'})
    snapshot('demo_binary_20261002T000000Z', {'a': 'positive', 'b': 'positive', 'd': 'negative'})
    d = c.get('/api/v1/snapshots/demo_binary_20261001T000000Z/diff/demo_binary_20261002T000000Z').json()
    assert [i['image_id'] for i in d['added']] == ['d'] and [i['image_id'] for i in d['removed']] == ['c']
    assert (
        d['changed'] == [{'image_id': 'b', 'display_name': None, 'before': 'negative', 'after': 'positive'}]
        and d['unchanged'] == 1
    )
    assert c.get('/api/v1/snapshots/demo_binary_20261001T000000Z/diff/demo_binary_20261001T000000Z').status_code == 400


def test_heatmap_for_efficientnet_only(app, tmp_path):
    c, root, _ = app
    import torch
    from src.workbench.adapters import load_efficient

    source = tmp_path / 'effnet'
    source.mkdir()
    torch.manual_seed(0)
    torch.save(load_efficient(classes=2).state_dict(), source / 'model.pt')
    config = InferenceConfig(imgsz=224, preprocess='rgb-letterbox224-imagenet-v1').model_dump()
    meta = registry.register(
        source,
        'efficientnet_b0',
        config,
        '1' * 32,
        True,
        {'task': 'binary_classification', 'label_scheme': 'binary_v1'},
    )
    samples = [{'image_id': 'p_000', 'truth': 1, 'prediction': 0, 'status': 'ok'}]
    write_report(root, 'c' * 32, samples, artifact=meta['id'], model='efficientnet_b0')
    r = c.get('/api/v1/reports/' + 'c' * 32 + '/heatmaps/p_000')
    assert r.status_code == 200, r.text
    assert r.headers['content-type'] == 'image/png'
    with Image.open(root / 'runs/workbench/evaluations' / ('c' * 32) / 'heatmaps/p_000.png') as im:
        assert im.size == (120, 90)
    assert c.get('/api/v1/reports/' + 'c' * 32 + '/heatmaps/p_000').status_code == 200  # cached
    assert c.get('/api/v1/reports/' + '8' * 32 + '/heatmaps/history_00').status_code == 400  # DINOv2 report
    assert c.get('/api/v1/reports/' + 'c' * 32 + '/heatmaps/not_in_report').status_code == 400


def test_model_card(app):
    c, root, artifact = app
    card = c.get(f"/api/v1/artifacts/{artifact['id']}/card").json()
    assert card['task'] == 'binary_classification' and card['intended_use'].startswith('判斷整張照片')
    assert card['in_use'] == {'local': False, 'line': False, 'shadow': False}
    assert any('研究原型' in l for l in card['limitations']) and 'release' not in card
    assert c.get('/api/v1/artifacts/not_a_model/card').status_code in (400, 404)
