"""Externally trained models: only plain tensors are accepted; the workbench rebuilds them,
registers an unevaluated version and refuses to activate it before a project evaluation."""

import json
import shutil
import sys
from pathlib import Path

import pytest
import torch
from fastapi.testclient import TestClient
from safetensors.torch import save_file

from src.common import code_path, read_json, write_json
from src.imports import service
from src.workbench import registry
from workbench_fixture import configure

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import model_package  # noqa: E402


@pytest.fixture
def environment(tmp_path, monkeypatch):
    app, artifact = configure(tmp_path, monkeypatch)
    with TestClient(app):
        yield tmp_path


def package(folder, model, config=None, training='外部電腦訓練，岡山高醫 2026-09 照片'):
    return model_package.write_package(
        folder,
        {
            'schema_version': 1,
            'purpose': 'inference',
            'model': model,
            'source': {'type': 'external', 'training_data': training},
            'config': config or {},
        },
    )


def efficient_tensors(classes=2):
    from src.workbench.adapters import load_efficient

    return model_package._plain(load_efficient(classes=classes).state_dict())


def test_external_model_is_rebuilt_registered_and_cannot_be_activated(environment):
    root = environment
    folder = root / 'inbox/models/external_eff2'
    folder.mkdir(parents=True)
    save_file(efficient_tensors(), str(folder / 'model.safetensors'))
    package(folder, 'efficientnet_b0')
    item = service.preview(root, 'models', 'external_eff2')
    assert item['state'] == 'ready', item.get('error')
    assert '評估前不能啟用' in item['items'][0]['reason']
    result = service.commit(root, item['id'], 'external-eff2')
    assert result['state'] == 'completed', result.get('error')
    ident = result['items'][0]['artifact']
    meta = read_json(root / 'models/versions' / ident / 'artifact.json')
    assert meta['extra']['source'] == 'external' and meta['extra']['task'] == 'binary_classification'
    assert set(meta['files']) == {'model.pt'}, 'stored in the same format as the workbench training output'
    assert not (root / 'runtime/imports/staging' / (item['id'] + '-converted')).exists()
    with pytest.raises(ValueError, match='外部訓練的模型必須先'):
        registry.activate(ident, 'local', allow_unevaluated=True)
    with pytest.raises(ValueError):
        registry.activate(ident, 'line')


def test_external_efficientnet_stage_model_round_trip(environment, tmp_path_factory):
    from src.workbench.adapters import load_efficient

    root = environment
    trained = tmp_path_factory.mktemp('trainer') / 'model_state.pt'
    torch.save(load_efficient(classes=3).state_dict(), trained)
    out = root / 'inbox/models/external_eff'
    model_package.main(
        [
            'export',
            '--model',
            'efficientnet_b0',
            '--weights',
            str(trained),
            '--out',
            str(out),
            '--training-data',
            '外部 EfficientNet',
            '--label-scheme',
            'stage_v1',
        ]
    )
    item = service.preview(root, 'models', 'external_eff')
    assert item['state'] == 'ready', item.get('error')
    result = service.commit(root, item['id'], 'external-eff')
    assert result['state'] == 'completed', result.get('error')
    meta = read_json(root / 'models/versions' / result['items'][0]['artifact'] / 'artifact.json')
    assert meta['extra']['task'] == 'stage_classification' and set(meta['files']) == {'model.pt'}


def test_pickled_weights_are_refused_even_when_listed(environment):
    root = environment
    folder = root / 'inbox/models/with_pt'
    folder.mkdir(parents=True)
    save_file(efficient_tensors(), str(folder / 'model.safetensors'))
    (folder / 'extra.pt').write_bytes(b'pickled code')
    pkg = package(folder, 'efficientnet_b0')
    pkg['files']['extra.pt'] = model_package.sha256(folder / 'extra.pt')
    write_json(folder / 'package.json', pkg)
    item = service.preview(root, 'models', 'with_pt')
    assert item['state'] == 'failed' and '.pt' in item['error']


def test_training_data_description_is_required(environment):
    root = environment
    folder = root / 'inbox/models/no_training'
    folder.mkdir(parents=True)
    save_file(efficient_tensors(), str(folder / 'model.safetensors'))
    package(folder, 'efficientnet_b0', training='')
    item = service.preview(root, 'models', 'no_training')
    assert item['state'] == 'failed' and 'training_data' in item['error']


def test_wrong_architecture_fails_at_commit_without_registering(environment):
    root = environment
    folder = root / 'inbox/models/wrong'
    folder.mkdir(parents=True)
    save_file(efficient_tensors(classes=3), str(folder / 'model.safetensors'))
    package(folder, 'efficientnet_b0')  # declared binary, tensors have three classes
    item = service.preview(root, 'models', 'wrong')
    assert item['state'] == 'ready'
    before = set((root / 'models/versions').iterdir())
    result = service.commit(root, item['id'], 'wrong')
    assert result['state'] != 'completed' and '架構不符' in (result.get('error') or '')
    assert set((root / 'models/versions').iterdir()) == before


def test_manifest_command_updates_hashes(tmp_path):
    folder = tmp_path / 'pkg'
    folder.mkdir()
    (folder / 'notes.json').write_text('{}')
    write_json(folder / 'package.json', {'schema_version': 1, 'model': 'efficientnet_b0', 'files': {}})
    model_package.main(['manifest', str(folder)])
    files = json.loads((folder / 'package.json').read_text(encoding='utf-8'))['files']
    assert files == {'notes.json': model_package.sha256(folder / 'notes.json')}


def test_external_dino_classifier_is_checked_and_registered(environment, tmp_path_factory):
    import numpy as np
    from transformers import Dinov2Config, Dinov2Model

    root = environment
    trained = tmp_path_factory.mktemp('dino')
    config = Dinov2Config(
        hidden_size=384, num_hidden_layers=12, num_attention_heads=6, intermediate_size=1536, patch_size=14
    )
    Dinov2Model(config).save_pretrained(trained, safe_serialization=True)
    np.savez(
        trained / 'classifier.npz',
        coef=np.zeros((1, 384)),
        intercept=np.zeros(1),
        classes=np.array([0, 1]),
        mean=np.zeros(384),
        scale=np.ones(384),
    )
    out = root / 'inbox/models/external_dino'
    model_package.main(
        [
            'export',
            '--model',
            'dinov2_small',
            '--weights',
            str(trained),
            '--out',
            str(out),
            '--training-data',
            '外部 DINO',
        ]
    )
    item = service.preview(root, 'models', 'external_dino')
    assert item['state'] == 'ready', item.get('error')
    result = service.commit(root, item['id'], 'external-dino')
    assert result['state'] == 'completed', result.get('error')
    meta = read_json(root / 'models/versions' / result['items'][0]['artifact'] / 'artifact.json')
    assert set(meta['files']) == {'config.json', 'model.safetensors', 'classifier.npz'}

    bad = root / 'inbox/models/bad_dino'
    shutil.copytree(out, bad)
    np.savez(
        bad / 'classifier.npz',
        coef=np.zeros((3, 384)),
        intercept=np.zeros(3),
        classes=np.array([0, 1, 2]),
        mean=np.zeros(384),
        scale=np.ones(384),
    )
    model_package.main(['manifest', str(bad)])
    item = service.preview(root, 'models', 'bad_dino')
    result = service.commit(root, item['id'], 'bad-dino')
    assert result['state'] != 'completed' and '形狀' in (result.get('error') or '')


def test_model_card_states_external_training(environment):
    root = environment
    folder = root / 'inbox/models/card_model'
    folder.mkdir(parents=True)
    save_file(efficient_tensors(), str(folder / 'model.safetensors'))
    package(folder, 'efficientnet_b0', training='外院 50 張')
    item = service.preview(root, 'models', 'card_model')
    ident = service.commit(root, item['id'], 'card')['items'][0]['artifact']
    from src.workbench.evaluation_views import model_card

    limits = model_card(root, ident)['limitations']
    assert any('外院 50 張' in x for x in limits) and any('評估分數可能偏高' in x for x in limits)
    assert not any(x.startswith('只在本專案的照片上訓練') for x in limits)


def test_corrupt_photo_is_rejected_without_failing_the_batch(environment):
    from PIL import Image

    root = environment
    folder = root / 'inbox/photos/broken'
    folder.mkdir(parents=True)
    (folder / 'bad.jpg').write_bytes(b'not an image')
    Image.new('RGB', (100, 80), 'purple').save(folder / 'good.jpg')
    item = service.preview(root, 'photos', 'broken')
    assert item['state'] == 'ready', item.get('error')
    actions = {x['name']: x['action'] for x in item['items']}
    assert actions == {'bad.jpg': 'reject', 'good.jpg': 'add'}
    from src.inference.engine import InvalidImage, decode_image

    with pytest.raises(InvalidImage):
        decode_image(b'not an image', read_json(code_path('configs/service.json')))
