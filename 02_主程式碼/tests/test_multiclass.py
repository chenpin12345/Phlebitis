"""Three-class stage models: training output size, inference schema, evaluation mapping (CPU only)."""
import numpy as np
import pytest
from src.common import write_manifest
from src.data.dataset import build, validate_split
from test_tasks import make_row


@pytest.fixture
def stage_snapshot(tmp_path, monkeypatch):
    rows = []
    for g in range(3):
        rows.append(make_row(tmp_path, f"n{g}", 'negative', 'normal', group=f"p{g}"))
        rows.append(make_row(tmp_path, f"a{g}", 'positive', 'stage1', group=f"p{g}"))
        rows.append(make_row(tmp_path, f"b{g}", 'positive', 'stage2', group=f"p{g}"))
    write_manifest(rows, tmp_path)
    info = build(root=tmp_path, task='stage_classification')
    import shutil
    (tmp_path / 'configs').mkdir(exist_ok=True)
    shutil.copy2(__import__('src.paths', fromlist=['CODE_ROOT']).CODE_ROOT / 'configs/service.json', tmp_path / 'configs/service.json')
    from src.workbench import adapters, registry
    import src.common as common
    monkeypatch.setattr(adapters, 'inside', lambda value, root=None: common.inside(value, root or tmp_path))
    monkeypatch.setattr(registry, 'VERSIONS', tmp_path / 'models/versions')
    monkeypatch.setattr(registry, 'ROOT', tmp_path)
    monkeypatch.setattr(adapters, 'validate_split', lambda dataset: validate_split(dataset, tmp_path))
    return tmp_path, info


def test_efficientnet_three_class_end_to_end(stage_snapshot, monkeypatch):
    import torch
    from src.workbench import adapters, registry
    from src.workbench.contracts import Experiment
    root, info = stage_snapshot
    torch.manual_seed(0)
    dataset = info['folds'][0]['dataset']
    cfg = Experiment(model='efficientnet_b0', dataset=dataset, device='cpu', demo=True, epochs=1, batch=4, task='stage_classification')
    split = validate_split(root / dataset, root)
    job = root / 'job'; job.mkdir()
    output, effective = adapters.efficient_train(cfg, split, job, None)
    assert effective['output_classes'] == 3 and effective['label_scheme'] == 'stage_v1'
    state = torch.load(output / 'model.pt', weights_only=True)
    assert state['classifier.1.weight'].shape[0] == 3
    monkeypatch.setattr(registry, 'audit', lambda *a, **k: None)
    artifact = registry.register(output, cfg.model, cfg.inference.model_dump(), 'job', True, {'dataset': dataset, 'task': 'stage_classification', 'label_scheme': 'stage_v1'})
    predictor = adapters.ModelPredictor(artifact['id'], 'cpu')
    record, _ = predictor.predict((root / split['members']['val'][0]['image_path']).read_bytes())
    assert record['predicted_class'] in ('normal', 'stage1', 'stage2') and record['label_scheme'] == 'stage_v1'
    assert sum(record['class_scores'].values()) == pytest.approx(1, abs=1e-4)
    assert record['binary_prediction'] == int(record['predicted_class'] != 'normal')
    from src.line_bot.messages import results
    patient = results({**record, 'model_version': 'x'}, '/i', patient_view=True)
    flat = str(patient)
    assert 'stage1' not in flat and 'stage2' not in flat, 'patients never see stage output'
    folder = root / 'evaluation'; folder.mkdir()
    monkeypatch.setattr(adapters, 'ROOT', root)
    report = adapters.evaluate(artifact['id'], dataset, 'cpu', folder)
    assert report['task'] == 'stage_classification' and report['metrics']['kind'] == 'multiclass'
    assert len(report['metrics']['confusion_matrix']) == 3 and report['classes'] == ['normal', 'stage1', 'stage2']
    assert report['metrics']['complete']


def test_dino_multinomial_scores(stage_snapshot, monkeypatch):
    import torch, transformers
    from src.workbench import adapters
    from src.workbench.contracts import Experiment
    root, info = stage_snapshot
    class Backbone:
        def to(self, *a): return self
        def eval(self): return self
        def parameters(self): return [torch.nn.Parameter(torch.zeros(1))]
    monkeypatch.setattr(transformers.Dinov2Model, 'from_pretrained', lambda *a, **k: Backbone())
    split = validate_split(root / info['folds'][0]['dataset'], root)
    from src.workbench.adapters import truth_of
    def features(model, rows, *args):
        return np.array([[float(truth_of(r, split, 'stage_classification')), 1.0] for r in rows])
    monkeypatch.setattr(adapters, 'dino_features', features)
    base = root / 'base'; base.mkdir(); (base / 'model.safetensors').write_bytes(b'fixture')
    job = root / 'job'; job.mkdir()
    cfg = Experiment(model='dinov2_small', dataset='x', device='cpu', task='stage_classification')
    artifact, effective = adapters.dino_train(cfg, split, job, base)
    saved = np.load(artifact / 'classifier.npz', allow_pickle=False)
    assert saved['classes'].tolist() == [0, 1, 2] and saved['coef'].shape[0] == 3
    assert effective['score_function'].startswith('softmax')
    with pytest.raises(ValueError):
        adapters.dino_train(Experiment.model_construct(**{**cfg.__dict__, 'parameters': {'solver': 'liblinear'}}), split, root / 'job', base)
