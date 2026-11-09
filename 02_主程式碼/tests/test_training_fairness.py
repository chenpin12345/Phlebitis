"""M3: fixed epochs, baselines, training-fold thresholds, DINOv2 variants, hierarchical stages."""

import json

import numpy as np
import pytest
from PIL import Image

from src.common import write_manifest
from src.data import threshold
from src.data.dataset import build, validate_split
from src.workbench import adapters, baselines, registry
from src.workbench.contracts import BASELINES, Experiment
from test_multiclass import stage_snapshot  # noqa: F401
from test_tasks import make_row


def test_threshold_is_the_highest_that_keeps_the_target_sensitivity():
    scores = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.05, 0.6, 0.2]
    truths = [1] * 10 + [0, 0]
    choice = threshold.choose(scores, truths)
    assert choice['threshold'] == 0.1, '9 of 10 positives need the ninth highest score'
    assert choice['inner_sensitivity'] == 0.9 and choice['inner_false_positive_rate'] == 1


def test_threshold_stays_inside_the_allowed_range():
    assert 0 < threshold.choose([0.0, 0.0], [1, 1])['threshold'] < 1
    assert 0 < threshold.choose([1.0, 1.0], [1, 1])['threshold'] < 1


def rows_for(groups):
    return [{'image_id': f'{g}{i}', 'group': g, 'truth': t} for g, t in groups for i in range(2)]


def test_inner_predictions_see_only_the_training_members_and_never_split_a_patient():
    train = rows_for([('a', 0), ('b', 0), ('c', 1), ('d', 1), ('e', 1), ('f', 1)])
    validation = rows_for([('leak', 1)])
    seen = []

    def scorer(fit, held):
        assert not {r['group'] for r in fit} & {r['group'] for r in held}, 'a patient is on both sides'
        seen.extend(r['image_id'] for r in fit + held)
        return [0.9 if r['truth'] else 0.1 for r in held]

    choice = threshold.from_training(train, lambda r: r['truth'], scorer, 1)
    assert choice['threshold'] == 0.9 and choice['inner_folds'] == 2
    assert not set(seen) & {r['image_id'] for r in validation}


def test_too_few_patients_keep_the_configured_threshold():
    rows = rows_for([('a', 0), ('c', 1), ('d', 1)])
    assert threshold.from_training(rows, lambda r: r['truth'], lambda *a: [], 1) is None


def binary_snapshot(root):
    rows = []
    for g in range(6):
        label, stage = ('negative', 'normal') if g < 3 else ('positive', 'stage1')
        rows += [make_row(root, f'p{g}n{i}', label, stage, group=f'p{g}') for i in range(2)]
    write_manifest(rows, root)
    return build(root=root)


@pytest.fixture
def binary(tmp_path, monkeypatch):
    import src.common as common

    info = binary_snapshot(tmp_path)
    monkeypatch.setattr(adapters, 'inside', lambda value, root=None: common.inside(value, root or tmp_path))
    monkeypatch.setattr(baselines, 'inside', lambda value, root=None: common.inside(value, root or tmp_path))
    monkeypatch.setattr(registry, 'VERSIONS', tmp_path / 'models/versions')
    monkeypatch.setattr(registry, 'ROOT', tmp_path)
    monkeypatch.setattr(registry, 'audit', lambda *a, **k: None)
    monkeypatch.setattr(adapters, 'validate_split', lambda dataset: validate_split(dataset, tmp_path))
    split = validate_split(tmp_path / info['folds'][0]['dataset'], tmp_path)
    return tmp_path, info, split


def small_efficient(root, name, split, **extra):
    import torch

    torch.manual_seed(0)
    np.random.seed(0)
    import random

    random.seed(0)
    folder = root / name
    folder.mkdir()
    cfg = Experiment(model='efficientnet_b0', dataset='x', device='cpu', demo=True, epochs=2, batch=4, **extra)
    output, effective = adapters.efficient_train(cfg, split, folder, None)
    return folder, output, effective


def test_validation_photos_do_not_change_the_trained_model(binary):
    import torch

    root, _, split = binary
    _, first, _ = small_efficient(root, 'a', split)
    wrong = {
        **split,
        'members': {
            **split['members'],
            'val': [{**m, 'target': 'negative', 'label_state': 'negative'} for m in split['members']['val']],
        },
    }
    for row in wrong['members']['val']:  # also different pictures
        Image.new('RGB', (64, 64), 'white').save(root / row['image_path'])
    folder, second, effective = small_efficient(root, 'b', wrong)
    a, b = (torch.load(p / 'model.pt', weights_only=True) for p in (first, second))
    assert all(torch.equal(a[k], b[k]) for k in a if 'num_batches' not in k)
    assert effective['checkpoint_metric'] == 'final_epoch'
    assert (
        'validation is not used'
        in json.loads((folder / 'checkpoint_selection.json').read_text(encoding='utf-8'))['rule']
    )


def test_training_runs_every_epoch_even_with_patience(binary):
    root, _, split = binary
    folder, _, _ = small_efficient(root, 'a', split, patience=1)
    assert json.loads((folder / 'checkpoint_selection.json').read_text(encoding='utf-8'))['epoch'] == 2
    state = __import__('torch').load(folder / 'last.pt', weights_only=True)
    assert state['epoch'] == 2


def test_efficientnet_saves_the_threshold_it_chose_from_the_training_fold(binary, monkeypatch):
    root, _, split = binary
    seen = []
    real = threshold.from_training

    def spy(rows, truth, scorer, seed, target=threshold.TARGET):
        seen.extend(r['image_id'] for r in rows)
        return real(rows, truth, scorer, seed, target)

    monkeypatch.setattr(threshold, 'from_training', spy)
    _, output, effective = small_efficient(root, 'a', split, threshold_policy='sensitivity_090')
    assert set(seen) == {m['image_id'] for m in split['members']['train']}
    saved = json.loads((output / 'threshold.json').read_text(encoding='utf-8'))
    assert saved['threshold'] == effective['threshold'] and 0 < saved['threshold'] < 1


@pytest.mark.parametrize('model', ['baseline_majority', 'baseline_colour'])
def test_baselines_train_predict_and_cannot_be_activated(binary, monkeypatch, model):
    root, info, split = binary
    (root / 'configs').mkdir(exist_ok=True)
    import shutil

    shutil.copy2(
        __import__('src.paths', fromlist=['CODE_ROOT']).CODE_ROOT / 'configs/service.json',
        root / 'configs/service.json',
    )
    folder = root / 'job'
    folder.mkdir()
    cfg = Experiment(
        model=model, dataset=info['folds'][0]['dataset'], device='cpu', demo=True, threshold_policy='sensitivity_090'
    )
    monkeypatch.setattr(adapters, 'ROOT', root)
    output, effective = adapters.train(cfg, folder)
    assert effective['baseline'] and effective['output_classes'] == 2
    artifact = registry.register(
        output,
        cfg.model,
        cfg.inference.model_dump(),
        'job',
        True,
        {'dataset': cfg.dataset, 'task': 'binary_classification'},
    )
    predictor = adapters.ModelPredictor(artifact['id'], 'cpu')
    record, _ = predictor.predict((root / split['members']['val'][0]['image_path']).read_bytes())
    assert sum(record['class_scores'].values()) == pytest.approx(1, abs=1e-4)
    assert record['predicted_class'] in ('negative', 'positive')
    monkeypatch.setattr(registry, 'get', lambda ident: artifact)
    with pytest.raises(ValueError, match='不能啟用'):
        registry.activate.__wrapped__(artifact['id'])


def test_dino_knn_baseline_end_to_end_with_a_tiny_backbone(binary, monkeypatch):
    from transformers import Dinov2Config, Dinov2Model

    root, info, split = binary
    import shutil

    (root / 'configs').mkdir(exist_ok=True)
    shutil.copy2(
        __import__('src.paths', fromlist=['CODE_ROOT']).CODE_ROOT / 'configs/service.json',
        root / 'configs/service.json',
    )
    base = root / 'pretrained/dinov2_small'
    Dinov2Model(
        Dinov2Config(hidden_size=32, num_hidden_layers=1, num_attention_heads=2, image_size=28, patch_size=14)
    ).save_pretrained(base, safe_serialization=True)
    monkeypatch.setattr(adapters, 'ROOT', root)
    monkeypatch.setattr(adapters, 'PRETRAINED', root / 'pretrained')
    monkeypatch.setattr(adapters, 'prepare', lambda model, folder: base)
    folder = root / 'job'
    folder.mkdir()
    cfg = Experiment(
        model='baseline_dino_knn',
        dataset=info['folds'][0]['dataset'],
        device='cpu',
        demo=True,
        threshold_policy='sensitivity_090',
    )
    output, effective = adapters.train(cfg, folder)
    assert 0 < effective['threshold'] <= 1
    artifact = registry.register(
        output,
        cfg.model,
        cfg.inference.model_dump(),
        'job',
        True,
        {'dataset': cfg.dataset, 'task': 'binary_classification'},
    )
    predictor = adapters.ModelPredictor(artifact['id'], 'cpu')
    record, _ = predictor.predict((root / split['members']['val'][0]['image_path']).read_bytes())
    assert sum(record['class_scores'].values()) == pytest.approx(1)


def test_every_baseline_is_refused_by_the_model_list():
    assert BASELINES == {'baseline_majority', 'baseline_colour', 'baseline_dino_knn'}


def test_knn_scores_share_of_the_nearest_rows():
    reference = np.array([[1.0, 0], [0.9, 0.1], [0, 1.0], [0.1, 0.9]])
    labels = np.array([0, 0, 1, 1])
    scores = baselines.knn_scores(reference, labels, np.array([[1.0, 0.0]]), 2, k=3)
    assert scores[0].tolist() == pytest.approx([2 / 3, 1 / 3])


def test_feature_cache_keeps_variants_apart(tmp_path, monkeypatch):
    import torch

    class Output:
        def __init__(self, x):
            self.last_hidden_state = torch.ones(1, 5, 4) * float(x.shape[-1])

    calls = []

    def model(pixel_values):
        calls.append(pixel_values.shape[-1])
        return Output(pixel_values)

    picture = tmp_path / 'a.jpg'
    Image.new('RGB', (64, 64), 'red').save(picture)
    monkeypatch.setattr(adapters, 'ROOT', tmp_path)
    monkeypatch.setattr(adapters, 'inside', lambda value: picture)
    monkeypatch.setattr(adapters, 'check_cancel', lambda folder: None)
    monkeypatch.setattr(adapters, 'progress', lambda *a, **k: None)
    row = [{'image_id': 'a', 'dataset_sha256': 'h', 'image_path': 'a.jpg'}]
    plain = adapters.dino_features(model, row, 'cpu', tmp_path, 'w')
    both = adapters.dino_features(model, row, 'cpu', tmp_path, 'w', 'cls_mean')
    large = adapters.dino_features(model, row, 'cpu', tmp_path, 'w', 'cls', 518)
    other = adapters.dino_features(model, row, 'cpu', tmp_path, 'other-weights')
    again = adapters.dino_features(model, row, 'cpu', tmp_path, 'w')
    assert plain.shape[1] == 4 and both.shape[1] == 8 and large[0, 0] == 518 and plain[0, 0] == 224
    assert len(calls) == 4 and other.shape == plain.shape and again.tolist() == plain.tolist()


def test_hierarchical_stage_scores_add_up_and_stay_marked_descriptive(stage_snapshot, monkeypatch):  # noqa: F811
    import torch
    import transformers

    root, info = stage_snapshot

    class Backbone:
        def to(self, *a):
            return self

        def eval(self):
            return self

        def parameters(self):
            return [torch.nn.Parameter(torch.zeros(1))]

    monkeypatch.setattr(transformers.Dinov2Model, 'from_pretrained', lambda *a, **k: Backbone())
    split = validate_split(root / info['folds'][0]['dataset'], root)

    def features(model, rows, *args):
        return np.array([[float(adapters.truth_of(r, split, 'stage_classification')), 1.0] for r in rows])

    monkeypatch.setattr(adapters, 'dino_features', features)
    base = root / 'base'
    base.mkdir()
    (base / 'model.safetensors').write_bytes(b'fixture')
    job = root / 'job'
    job.mkdir()
    cfg = Experiment(
        model='dinov2_small',
        dataset='x',
        device='cpu',
        task='stage_classification',
        parameters={'strategy': 'hierarchical'},
    )
    output, effective = adapters.dino_train(cfg, split, job, base)
    assert effective['strategy'] == 'hierarchical' and effective['descriptive_only']
    saved = np.load(output / 'classifier.npz', allow_pickle=False)
    predictor = adapters.ModelPredictor.__new__(adapters.ModelPredictor)
    predictor.kind, predictor.classifier, predictor.pooling = 'dinov2_small', saved, 'cls'

    class Hidden:
        last_hidden_state = torch.tensor([[[2.0, 1.0]]])

    predictor.model = lambda pixel_values: Hidden
    scores = predictor.class_scores(None)
    assert scores.sum() == pytest.approx(1) and int(scores.argmax()) == 2


def test_flat_stage_model_is_kept_as_the_default():
    assert Experiment(model='dinov2_small', dataset='x').parameters == {}
    assert Experiment(model='dinov2_small', dataset='x').threshold_policy == 'fixed'


def test_a_saved_old_config_still_loads():
    old = {'model': 'efficientnet_b0', 'dataset': 'x', 'patience': 5, 'epochs': 120}
    assert Experiment(**old).patience == 5


def test_folds_share_one_backbone_and_a_changed_file_is_refused(tmp_path, monkeypatch):
    import torch
    import transformers

    class Backbone:
        def to(self, *a):
            return self

        def eval(self):
            return self

        def parameters(self):
            return [torch.nn.Parameter(torch.zeros(1))]

    pretrained = tmp_path / 'pretrained'
    base = pretrained / 'dinov2_small'
    base.mkdir(parents=True)
    (base / 'model.safetensors').write_bytes(b'weights')
    (base / 'config.json').write_text('{}', encoding='utf-8')
    monkeypatch.setattr(adapters, 'PRETRAINED', pretrained)
    monkeypatch.setattr(transformers.Dinov2Model, 'from_pretrained', lambda *a, **k: Backbone())
    split = {
        'label_scheme': 'binary_v1',
        'members': {
            'train': [
                {
                    'image_id': f'{i}',
                    'group': f'g{i}',
                    'label_state': 'positive' if i % 2 else 'negative',
                    'target': 'x',
                }
                for i in range(6)
            ]
        },
    }
    monkeypatch.setattr(adapters, 'truth_of', lambda r, s, t: int(r['label_state'] == 'positive'))
    monkeypatch.setattr(adapters, 'split_scheme', lambda s: 'binary_v1')
    monkeypatch.setattr(
        adapters,
        'dino_features',
        lambda model, rows, *a: np.array([[float(r['label_state'] == 'positive'), 1.0] for r in rows]),
    )
    job = tmp_path / 'job'
    job.mkdir()
    cfg = Experiment(model='dinov2_small', dataset='x', device='cpu')
    output, _ = adapters.dino_train(cfg, split, job, base)
    assert not (output / 'model.safetensors').exists(), 'no copy per fold'
    assert adapters.dino_weights(output) == base
    (base / 'model.safetensors').write_bytes(b'other')
    with pytest.raises(ValueError, match='主幹權重'):
        adapters.dino_weights(output)


def test_older_artifacts_keep_loading_their_own_copy(tmp_path):
    (tmp_path / 'model.safetensors').write_bytes(b'weights')
    assert adapters.dino_weights(tmp_path) == tmp_path


def test_clearing_a_reference_frees_the_model(tmp_path, monkeypatch):
    import src.workbench.resources as resources
    from src.common import write_json

    monkeypatch.setattr(registry, 'REFS', tmp_path)
    monkeypatch.setattr(registry, 'audit', lambda *a, **k: None)
    write_json(tmp_path / 'local.json', {'artifact': 'm1', 'previous': None})
    with pytest.raises(ValueError, match='解除'):
        registry.rollback.__wrapped__('local')
    assert registry.clear_reference.__wrapped__('local')['artifact'] == 'm1'
    assert not (tmp_path / 'local.json').exists()
    with pytest.raises(ValueError, match='沒有使用中'):
        registry.clear_reference.__wrapped__('local')
    with pytest.raises(ValueError, match='沒有使用中'):
        registry.rollback.__wrapped__('local')
    with pytest.raises(ValueError):
        registry.clear_reference.__wrapped__('other')


@pytest.mark.parametrize(
    'name', ['artifact/threshold.json', 'artifact/baseline.json', 'artifact/knn.npz', 'artifact/backbone.json']
)
def test_files_of_new_runs_belong_to_their_job(name):
    from src.workbench import trash

    assert trash.known_job_file(name, {'kind': 'train', 'id': 'x'}, {})
