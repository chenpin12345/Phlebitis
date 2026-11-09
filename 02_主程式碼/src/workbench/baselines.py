"""Baselines every real model has to beat (#8).  They go through the same training job,
evaluation and reports as a model, but can never be activated (registry.activate).

  baseline_majority    always the class frequencies of the training fold
  baseline_colour      logistic regression on a colour histogram
  baseline_dino_knn    nearest neighbours on DINOv2 features (no training of any kind)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from src.common import inside, read_json, write_json

KNN = 5


def logit_scores(classifier, features) -> np.ndarray:
    """Class scores of one feature row from a saved linear classifier."""
    z = ((features - classifier['mean']) / classifier['scale']) @ classifier['coef'].T + classifier['intercept']
    if z.shape[1] == 1:
        p = float((1 / (1 + np.exp(-np.clip(z, -700, 700))))[0, 0])
        return np.array([1 - p, p])
    z = z[0] - z[0].max()
    e = np.exp(z)
    return e / e.sum()


def knn_scores(reference, labels, query, classes: int, k: int = KNN) -> np.ndarray:
    """Share of each class among the k most similar reference rows (cosine)."""
    a = reference / np.maximum(np.linalg.norm(reference, axis=1, keepdims=True), 1e-12)
    b = query / np.maximum(np.linalg.norm(query, axis=1, keepdims=True), 1e-12)
    near = np.argsort(-(b @ a.T), axis=1, kind='stable')[:, : min(k, len(a))]
    return np.stack([np.bincount(labels[row], minlength=classes) / near.shape[1] for row in near])


def _colour(row) -> np.ndarray:
    from src.workbench.source_audit import colour_features

    with Image.open(inside(row['image_path'])) as im:
        return np.array(colour_features(im))


def _dino(folder, device):
    from transformers import Dinov2Model
    from src.workbench import adapters

    base = adapters.prepare('dinov2_small', folder)
    model = Dinov2Model.from_pretrained(base, local_files_only=True, use_safetensors=True).to(device).eval()
    return model, sha256_of(base)


def sha256_of(base: Path) -> str:
    from src.common import sha256

    return sha256(base / 'model.safetensors')


def train(cfg, split, folder):
    from src.data.tasks import SCHEMES
    from src.workbench import adapters
    from src.workbench.contracts import experiment_task

    task = experiment_task(cfg.model, cfg.task)
    scheme = adapters.split_scheme(split)
    classes = len(SCHEMES[scheme]['classes'])
    rows = split['members']['train']
    y = np.array([adapters.truth_of(r, split, task) for r in rows])
    output = folder / 'artifact'
    output.mkdir(exist_ok=True)
    by_row = None
    fit = None
    if cfg.model == 'baseline_majority':
        priors = (np.bincount(y, minlength=classes) / len(y)).tolist()
        write_json(output / 'baseline.json', {'kind': cfg.model, 'priors': priors})
    elif cfg.model == 'baseline_colour':
        adapters.progress(folder, 'extracting_features', total=len(rows))
        x = np.stack([_colour(r) for r in rows])
        scaler, classifier = adapters.fit_linear(x, y, cfg.parameters, cfg.seed)
        adapters.save_linear(output / 'classifier.npz', scaler, classifier, x.shape[1])
        write_json(output / 'baseline.json', {'kind': cfg.model})
        by_row = dict(zip((r['image_id'] for r in rows), x))

        def fit(train_x, train_y, held_x):
            s, c = adapters.fit_linear(train_x, train_y, cfg.parameters, cfg.seed)
            return c.predict_proba(s.transform(held_x) if s is not None else held_x)[:, 1]

    else:
        device = adapters.device_name(cfg.device)
        model, base_hash = _dino(folder, device)
        x = adapters.dino_features(model, rows, device, folder, base_hash)
        np.savez(output / 'knn.npz', x=x, y=y)
        write_json(output / 'baseline.json', {'kind': cfg.model, 'k': KNN, 'backbone_hash': base_hash})
        by_row = dict(zip((r['image_id'] for r in rows), x))

        def fit(train_x, train_y, held_x):
            return knn_scores(train_x, train_y, held_x, classes)[:, 1]

    effective = {
        'parameters': {'baseline': cfg.model},
        'total_parameters': 0,
        'trainable_parameters': 0,
        'task': task,
        'label_scheme': scheme,
        'output_classes': classes,
        'baseline': True,
    }
    if fit is not None:

        def scorer(train_rows, held_rows):
            train_x = np.stack([by_row[r['image_id']] for r in train_rows])
            train_y = np.array([adapters.truth_of(r, split, task) for r in train_rows])
            return fit(train_x, train_y, np.stack([by_row[r['image_id']] for r in held_rows]))

        effective.update(adapters.choose_threshold(cfg, split, task, output, scorer))
    write_json(folder / 'effective.json', effective)
    return output, effective


class Baseline:
    """Scores for one photo; same class order as the model's label scheme."""

    def __init__(self, kind: str, path: Path, classes: int, device: str):
        self.kind, self.classes, self.device = kind, classes, device
        if kind == 'baseline_majority':
            self.priors = np.array(read_json(path / 'baseline.json')['priors'])
        elif kind == 'baseline_colour':
            self.classifier = np.load(path / 'classifier.npz', allow_pickle=False)
        else:
            from transformers import Dinov2Model
            from src.workbench import adapters

            data = np.load(path / 'knn.npz', allow_pickle=False)
            self.x, self.y = data['x'], data['y']
            base = adapters.PRETRAINED / 'dinov2_small'
            self.model = (
                Dinov2Model.from_pretrained(base, local_files_only=True, use_safetensors=True).to(device).eval()
            )

    def scores(self, image) -> np.ndarray:
        if self.kind == 'baseline_majority':
            return self.priors
        if self.kind == 'baseline_colour':
            from src.workbench.source_audit import colour_features

            return logit_scores(self.classifier, np.array(colour_features(image))[None])
        import torch
        from src.workbench import adapters

        x = adapters.tensor_image(image).unsqueeze(0).to(self.device)
        with torch.inference_mode():
            features = self.model(pixel_values=x).last_hidden_state[:, 0].cpu().numpy()
        return knn_scores(self.x, self.y, features, self.classes)[0]
