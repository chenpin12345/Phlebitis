from __future__ import annotations

import io
import json
import math
import os
import random
import shutil
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps
from src.common import ROOT, inside, read_json, write_json, sha256, stamp
from src.common import config_path
from src.paths import CODE_ROOT
from src.data.dataset import validate_split
from src.data.tasks import shuffled_labels
from src.inference.engine import decode_image, encode_result
from src.workbench.baselines import logit_scores
from src.workbench.contracts import BASELINES, MODELS, Experiment, InferenceConfig, experiment_task
from src.workbench.storage import digest

PRETRAINED = ROOT / 'models/pretrained'


class Cancelled(Exception):
    pass


def check_cancel(folder):
    if (folder / 'cancel').exists():
        raise Cancelled('使用者停止工作')


def progress(folder, stage, **values):
    write_json(folder / 'progress.json', {'stage': stage, 'at': time.time(), **values})
    with (folder / 'progress.jsonl').open('a', encoding='utf-8') as f:
        f.write(json.dumps({'stage': stage, 'at': time.time(), **values}, ensure_ascii=False, allow_nan=False) + '\n')


def prepare(model, folder):
    PRETRAINED.mkdir(parents=True, exist_ok=True)
    progress(folder, 'preparing_weights', model=model)
    if model.startswith('dinov2'):
        dest = PRETRAINED / model
        freshly_downloaded = not (dest / 'model.safetensors').exists()
        if not (dest / 'model.safetensors').exists():
            from huggingface_hub import snapshot_download, HfApi

            revision = HfApi().model_info(MODELS[model]['source']).sha
            source = snapshot_download(
                MODELS[model]['source'],
                revision=revision,
                allow_patterns=['config.json', 'model.safetensors'],
                cache_dir=str(PRETRAINED / 'hf-cache'),
            )
            shutil.copytree(source, dest, dirs_exist_ok=True)
            write_json(dest / 'source.json', {'source': MODELS[model]['source'], 'revision': revision})
            shutil.rmtree(PRETRAINED / 'hf-cache', ignore_errors=True)  # a second full copy otherwise
        files = {
            p.name: sha256(p)
            for p in dest.iterdir()
            if p.suffix in ('.safetensors', '.json') and p.name != 'provenance.json'
        }
        write_json(dest / 'provenance.json', {'files': files, 'source': MODELS[model]['source']})
        if freshly_downloaded:
            write_json(
                ROOT / 'runtime/imports/trusted-official' / (model + '.json'),
                {
                    'source': MODELS[model]['source'],
                    'files': {
                        p.name: sha256(p) for p in dest.iterdir() if p.name in ('config.json', 'model.safetensors')
                    },
                    'revision': revision,
                },
            )
        return dest
    dest = PRETRAINED / (model + '.pth')
    freshly_downloaded = not dest.exists()
    if not dest.exists():
        temporary = dest.with_suffix('.download')

        def report(block, size, total):
            check_cancel(folder)
            if block % 128 == 0:
                progress(
                    folder, 'downloading', bytes=min(block * size, total) if total > 0 else block * size, total=total
                )

        import requests

        for attempt in range(5):
            try:
                offset = temporary.stat().st_size if temporary.exists() else 0
                with requests.get(
                    MODELS[model]['source'],
                    headers={'Range': f'bytes={offset}-'} if offset else {},
                    stream=True,
                    timeout=(20, 40),
                ) as response:
                    response.raise_for_status()
                    append = offset > 0 and response.status_code == 206
                    if not append:
                        offset = 0
                    total = int(response.headers.get('content-length', 0)) + offset
                    with temporary.open('ab' if append else 'wb') as output:
                        done = offset
                        for chunk in response.iter_content(256 * 1024):
                            check_cancel(folder)
                            output.write(chunk)
                            done += len(chunk)
                            progress(folder, 'downloading', bytes=done, total=total, attempt=attempt + 1)
                    if total and done != total:
                        raise OSError('Download incomplete')
                break
            except Cancelled:
                raise
            except Exception:
                if attempt == 4:
                    raise
                progress(folder, 'retrying_download', attempt=attempt + 2)
        temporary.replace(dest)
    write_json(
        dest.with_suffix('.source.json'),
        {'source': MODELS[model]['source'], 'sha256': sha256(dest), 'prepared': stamp()},
    )
    if freshly_downloaded:
        write_json(
            ROOT / 'runtime/imports/trusted-official' / (model + '.json'),
            {'source': MODELS[model]['source'], 'files': {dest.name: sha256(dest)}, 'prepared': stamp()},
        )
    return dest


def device_name(value):
    import torch

    if value != 'cpu' and not torch.cuda.is_available():
        raise ValueError('CUDA 不可用，請明確選擇 CPU。')
    return 'cpu' if value == 'cpu' else 'cuda:0'


def tensor_image(image, augment=None, size=224):
    import torch

    image = ImageOps.pad(
        image.convert('RGB'), (size, size), method=Image.Resampling.BICUBIC, color=(124, 116, 104), centering=(0.5, 0.5)
    )
    if augment:
        if augment.get('flip', True) and random.random() < 0.5:
            image = ImageOps.mirror(image)
        rotation = float(augment.get('rotation', 0))
        if rotation:
            image = image.rotate(
                random.uniform(-rotation, rotation), resample=Image.Resampling.BILINEAR, fillcolor=(124, 116, 104)
            )
    x = torch.from_numpy(np.asarray(image).copy()).permute(2, 0, 1).float() / 255
    return (x - torch.tensor([0.485, 0.456, 0.406])[:, None, None]) / torch.tensor([0.229, 0.224, 0.225])[:, None, None]


def load_efficient(path=None, classes=2):
    import torch
    from torchvision.models import efficientnet_b0

    model = efficientnet_b0(weights=None)
    if path:
        model.load_state_dict(torch.load(path, map_location='cpu', weights_only=True))
    model.classifier[1] = torch.nn.Linear(model.classifier[1].in_features, classes)
    return model


def split_scheme(split):
    from src.data.tasks import member_scheme

    return member_scheme(split)


def check_split_task(split, task):
    """A snapshot serves exactly one task."""
    from src.data.dataset import snapshot_task
    from src.data.tasks import SCHEMES, TASK_NAMES

    snapshot = snapshot_task(split)
    if snapshot is None:
        raise ValueError('舊版快照不能再使用；請建立新的資料快照。')
    if snapshot != task:
        raise ValueError(f'快照任務為「{TASK_NAMES[snapshot]}」，與實驗任務「{TASK_NAMES[task]}」不同。')
    classes = SCHEMES[split['label_scheme']]['classes']
    for subset in ('train', 'val'):
        if {r['target'] for r in split['members'][subset]} != set(classes):
            raise ValueError('訓練與驗證折均須包含此任務的全部類別：' + '、'.join(classes))


def truth_of(member, split, task):
    """Ground-truth class index of a snapshot member under the snapshot's own scheme."""
    from src.data.tasks import member_class

    return member_class(member, split_scheme(split))


def efficient_training_mode(model, strategy='backbone'):
    model.train()
    model.features.eval()
    if strategy == 'last_stage':
        model.features[-1].train()


def efficient_model(cfg, base, classes, scheme):
    import torch
    from src.workbench.registry import get, artifact_path

    params = cfg.parameters
    model = load_efficient(base, classes)
    if cfg.initial_artifact:
        prior = get(cfg.initial_artifact)
        if prior['model'] != cfg.model:
            raise ValueError('Initial artifact recipe mismatch')
        if InferenceConfig(**prior['config']).scheme != scheme:
            raise ValueError('初始模型的標籤方案與快照不同，不能直接微調')
        model.load_state_dict(
            torch.load(artifact_path(cfg.initial_artifact) / 'model.pt', map_location='cpu', weights_only=True)
        )
    for p in model.features.parameters():
        p.requires_grad = False
    if params.get('freeze', 'backbone') == 'last_stage':
        for p in model.features[-1].parameters():
            p.requires_grad = True
    return model


def efficient_loader(rows, split, task, params, batch, augment=False):
    from torch.utils.data import Dataset, DataLoader

    class Images(Dataset):
        def __len__(self):
            return len(rows)

        def __getitem__(self, i):
            row = rows[i]
            with Image.open(inside(row['image_path'])) as im:
                x = tensor_image(im, params if augment else None)
            return x, truth_of(row, split, task)

    return DataLoader(Images(), batch_size=batch, shuffle=augment, num_workers=0)


def efficient_loss(params, rows, split, task, classes, device):
    import torch

    counts = np.bincount([truth_of(x, split, task) for x in rows], minlength=classes)
    weights = (
        torch.tensor(counts.sum() / (classes * np.maximum(counts, 1)), dtype=torch.float32, device=device)
        if params.get('class_weight') == 'balanced'
        else None
    )
    return torch.nn.CrossEntropyLoss(weight=weights)


def efficient_optimizer(model, params):
    import torch

    optimizer_cls = torch.optim.AdamW if params.get('optimizer', 'AdamW') == 'AdamW' else torch.optim.SGD
    return optimizer_cls(
        [p for p in model.parameters() if p.requires_grad],
        lr=params.get('learning_rate', 0.001),
        weight_decay=params.get('weight_decay', 0.0001),
    )


def efficient_inner_scores(cfg, split, task, base, classes, scheme, device, folder, fit_rows, held_rows):
    """Positive-class scores for held_rows from a model trained only on fit_rows."""
    import torch

    params = cfg.parameters
    model = efficient_model(cfg, base, classes, scheme).to(device)
    loader = efficient_loader(fit_rows, split, task, params, cfg.batch, True)
    loss_fn = efficient_loss(params, fit_rows, split, task, classes, device)
    optimizer = efficient_optimizer(model, params)
    for _ in range(cfg.epochs):
        check_cancel(folder)
        efficient_training_mode(model, params.get('freeze', 'backbone'))
        for x, y in loader:
            optimizer.zero_grad()
            loss_fn(model(x.to(device)), y.to(device)).backward()
            optimizer.step()
    model.eval()
    values = []
    with torch.inference_mode():
        for x, _ in efficient_loader(held_rows, split, task, params, cfg.batch):
            values += model(x.to(device)).softmax(1)[:, 1].cpu().tolist()
    return values


def choose_threshold(cfg, split, task, output, scorer) -> dict:
    """Pick the decision threshold from the training members only and save it with the model."""
    from src.data import threshold

    if cfg.threshold_policy != 'sensitivity_090' or task != 'binary_classification':
        return {}
    rows = split['members']['train']
    choice = threshold.from_training(rows, lambda r: truth_of(r, split, task), scorer, cfg.seed)
    if choice is None:
        write_json(
            output / 'threshold.json', {'rule': 'too few patients for inner predictions; configured threshold kept'}
        )
        return {'threshold_rule': 'fallback'}
    write_json(output / 'threshold.json', choice)
    return {'threshold': choice['threshold'], 'threshold_rule': choice['rule'], 'threshold_selection': choice}


def efficient_train(cfg, split, folder, base):
    import torch
    from src.data.tasks import SCHEMES

    params = cfg.parameters
    device = device_name(cfg.device)
    task = experiment_task(cfg.model, cfg.task)
    scheme = split_scheme(split)
    classes = len(SCHEMES[scheme]['classes'])
    model = efficient_model(cfg, base, classes, scheme).to(device)

    train = efficient_loader(split['members']['train'], split, task, params, cfg.batch, True)
    val = efficient_loader(split['members']['val'], split, task, params, cfg.batch)
    loss_fn = efficient_loss(params, split['members']['train'], split, task, classes, device)
    optimizer = efficient_optimizer(model, params)
    scheduler = (
        torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, cfg.epochs)
        if params.get('scheduler', 'none') == 'cosine'
        else None
    )
    start = 0
    if cfg.resume_job:
        checkpoint = torch.load(resume_folder(cfg) / 'last.pt', map_location=device, weights_only=True)
        model.load_state_dict(checkpoint['model'])
        optimizer.load_state_dict(checkpoint['optimizer'])
        if scheduler and checkpoint.get('scheduler'):
            scheduler.load_state_dict(checkpoint['scheduler'])
        start = checkpoint['epoch']
        if start >= cfg.epochs:
            raise ValueError('Checkpoint already completed requested epochs')
    actual = {
        'freeze': params.get('freeze', 'backbone'),
        'scheduler': params.get('scheduler', 'none'),
        'class_weight': params.get('class_weight'),
        'flip': bool(params) and params.get('flip', True),
        'rotation': params.get('rotation', 0),
        'optimizer': type(optimizer).__name__,
        'learning_rate': optimizer.param_groups[0]['lr'],
        'weight_decay': optimizer.param_groups[0]['weight_decay'],
        'epochs': cfg.epochs,
        'batch': cfg.batch,
        'imgsz': 224,
        'device': cfg.device,
        'seed': cfg.seed,
    }
    effective = {
        'parameters': actual,
        'total_parameters': sum(p.numel() for p in model.parameters()),
        'trainable_parameters': sum(p.numel() for p in model.parameters() if p.requires_grad),
        'checkpoint_metric': 'final_epoch',
        'preprocess': cfg.inference.preprocess,
        'task': task,
        'label_scheme': scheme,
        'output_classes': classes,
    }
    write_json(folder / 'effective.json', effective)
    output = folder / 'artifact'
    output.mkdir(exist_ok=True)
    for epoch in range(start, cfg.epochs):
        check_cancel(folder)
        efficient_training_mode(model, params.get('freeze', 'backbone'))
        loss_sum = 0
        seen = 0
        for x, y in train:
            check_cancel(folder)
            x = x.to(device)
            y = y.to(device)
            optimizer.zero_grad()
            loss = loss_fn(model(x), y)
            loss.backward()
            optimizer.step()
            loss_sum += loss.item() * len(y)
            seen += len(y)
        model.eval()
        val_loss = 0
        correct = 0
        total = 0
        with torch.inference_mode():
            for x, y in val:
                x = x.to(device)
                y = y.to(device)
                logits = model(x)
                val_loss += loss_fn(logits, y).item() * len(y)
                correct += (logits.argmax(1) == y).sum().item()
                total += len(y)
        value = val_loss / total  # recorded for the curve only; it never picks a model (#7)
        if scheduler:
            scheduler.step()
        checkpoint = {
            'epoch': epoch + 1,
            'model': model.state_dict(),
            'optimizer': optimizer.state_dict(),
            'scheduler': scheduler.state_dict() if scheduler else None,
        }
        torch.save(checkpoint, folder / 'last.tmp')
        os.replace(folder / 'last.tmp', folder / 'last.pt')
        progress(
            folder,
            'training',
            epoch=epoch + 1,
            epochs=cfg.epochs,
            train_loss=loss_sum / seen,
            val_loss=value,
            val_accuracy=correct / total,
            vram_bytes=torch.cuda.max_memory_allocated() if device != 'cpu' else None,
        )
    torch.save(model.cpu().state_dict(), output / 'model.pt')
    write_json(
        folder / 'checkpoint_selection.json',
        {'epoch': cfg.epochs, 'rule': 'fixed number of epochs; validation is not used', 'artifact': 'model.pt'},
    )
    effective.update(
        choose_threshold(
            cfg,
            split,
            task,
            output,
            lambda fit_rows, held_rows: efficient_inner_scores(
                cfg, split, task, base, classes, scheme, device, folder, fit_rows, held_rows
            ),
        )
    )
    write_json(folder / 'effective.json', effective)
    return output, effective


def dino_weights(path):
    """Folder with the frozen backbone of a DINOv2 artifact.  Older artifacts hold their own copy;
    newer ones name the shared file in models/pretrained, checked by hash."""
    if (path / 'model.safetensors').exists():
        return path
    if not (path / 'backbone.json').exists():
        raise ValueError('這個模型沒有 DINOv2 主幹權重')
    reference = read_json(path / 'backbone.json')
    base = PRETRAINED / reference['model']
    if not (base / 'model.safetensors').exists() or sha256(base / 'model.safetensors') != reference['sha256']:
        raise ValueError('找不到訓練時使用的 DINOv2 主幹權重，或內容已不同')
    return base


def dino_pool(hidden, pooling='cls'):
    import torch

    if pooling == 'cls_mean':
        return torch.cat([hidden[:, 0], hidden[:, 1:].mean(1)], 1)
    return hidden[:, 0]


def fit_linear(x, y, params, seed):
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression

    scaler = StandardScaler().fit(x) if params.get('standardize', True) else None
    classifier = LogisticRegression(
        C=params.get('C', 1),
        solver=params.get('solver', 'lbfgs'),
        max_iter=params.get('max_iter', 200),
        class_weight=params.get('class_weight'),
        random_state=seed,
    )
    classifier.fit(scaler.transform(x) if scaler is not None else x, y)
    return scaler, classifier


def save_linear(path, scaler, classifier, width, **extra):
    np.savez(
        path,
        coef=classifier.coef_,
        intercept=classifier.intercept_,
        classes=classifier.classes_,
        mean=scaler.mean_ if scaler is not None else np.zeros(width),
        scale=scaler.scale_ if scaler is not None else np.ones(width),
        **extra,
    )


def dino_features(model, members, device, folder, base_hash, pooling='cls', size=224):
    import torch

    cache = ROOT / 'runtime/workbench/features'
    cache.mkdir(parents=True, exist_ok=True)
    values = []
    for i, row in enumerate(members):
        check_cancel(folder)
        key = digest(
            {
                'input': row['dataset_sha256'],
                'weights': base_hash,
                'preprocess': f'rgb-letterbox{size}-imagenet-v1',
                'pooling': 'CLS' if pooling == 'cls' else 'CLS+mean',
            }
        )
        path = cache / (key + '.npy')
        if path.exists():
            features = np.load(path, allow_pickle=False)
        else:
            with Image.open(inside(row['image_path'])) as im:
                x = tensor_image(im, size=size).unsqueeze(0).to(device)
            with torch.inference_mode():
                features = dino_pool(model(pixel_values=x).last_hidden_state, pooling).cpu().numpy()[0]
            np.save(path, features, allow_pickle=False)
        write_json(
            cache / (key + '.json'),
            {'image_id': row['image_id'], 'input_hash': row['dataset_sha256'], 'weights_hash': base_hash},
        )
        values.append(features)
        progress(folder, 'extracting_features', completed=i + 1, total=len(members))
    return np.stack(values)


def dino_train(cfg, split, folder, base):
    from transformers import Dinov2Model

    device = device_name(cfg.device)
    model = Dinov2Model.from_pretrained(base, local_files_only=True, use_safetensors=True).to(device).eval()
    for p in model.parameters():
        p.requires_grad = False
    from src.data.tasks import SCHEMES

    task = experiment_task(cfg.model, cfg.task)
    scheme = split_scheme(split)
    classes = len(SCHEMES[scheme]['classes'])
    rows = split['members']['train']
    params = cfg.parameters
    pooling = params.get('pooling', 'cls')
    size = params.get('resolution', 224)
    if pooling not in ('cls', 'cls_mean') or size not in (224, 518):
        raise ValueError('DINOv2 只支援 cls／cls_mean 與 224／518 解析度')
    strategy = params.get('strategy', 'flat')
    if strategy == 'hierarchical' and classes != 3:
        raise ValueError('階層式分期只用於分期任務')
    base_hash = sha256(base / 'model.safetensors')
    x = dino_features(model, rows, device, folder, base_hash, pooling, size)
    y = np.array([truth_of(r, split, task) for r in rows])
    if sorted(set(y.tolist())) != list(range(classes)):
        raise ValueError('訓練資料必須包含標籤方案的全部類別')
    if classes > 2 and params.get('solver', 'lbfgs') != 'lbfgs':
        raise ValueError('多類別只支援 lbfgs')
    check_cancel(folder)
    progress(folder, 'fitting_classifier', samples=len(y), features=x.shape[1])
    output = folder / 'artifact'
    output.mkdir(exist_ok=True)
    if Path(base).resolve().parent == PRETRAINED.resolve():
        # Every fold uses the same frozen backbone: keep one file, not one per fold.
        write_json(output / 'backbone.json', {'model': Path(base).name, 'sha256': base_hash})
    else:
        for name in ('config.json', 'model.safetensors', 'source.json'):
            if (base / name).exists():
                shutil.copy2(base / name, output / name)
    if strategy == 'hierarchical':
        # Step 1 normal or positive, step 2 which stage among the positives only.
        scaler, classifier = fit_linear(x, (y > 0).astype(int), params, cfg.seed)
        scaled = scaler.transform(x) if scaler is not None else x
        from sklearn.linear_model import LogisticRegression

        second = LogisticRegression(
            C=params.get('C', 1),
            max_iter=params.get('max_iter', 200),
            class_weight=params.get('class_weight'),
            random_state=cfg.seed,
        ).fit(scaled[y > 0], (y[y > 0] == 2).astype(int))
        np.savez(
            output / 'classifier.npz',
            coef=classifier.coef_,
            intercept=classifier.intercept_,
            classes=np.arange(classes),
            mean=scaler.mean_ if scaler is not None else np.zeros(x.shape[1]),
            scale=scaler.scale_ if scaler is not None else np.ones(x.shape[1]),
            coef2=second.coef_,
            intercept2=second.intercept_,
        )
    else:
        scaler, classifier = fit_linear(x, y, params, cfg.seed)
        save_linear(output / 'classifier.npz', scaler, classifier, x.shape[1])
    effective = {
        'pooling': 'CLS' if pooling == 'cls' else 'CLS+mean',
        'resolution': size,
        'strategy': strategy,
        'parameters': classifier.get_params(),
        'total_parameters': sum(p.numel() for p in model.parameters()),
        'trainable_parameters': int(classifier.coef_.size + classifier.intercept_.size),
        'iterations': classifier.n_iter_.tolist(),
        'train_only_scaler': True,
        'feature_count': int(x.shape[1]),
        'backbone_hash': base_hash,
        'task': task,
        'label_scheme': scheme,
        'output_classes': classes,
        'score_function': (
            'sigmoid of the single positive-class logit' if classes == 2 else 'softmax over multinomial logits'
        ),
    }
    if strategy == 'hierarchical':
        effective['score_function'] = 'positive score, then stage score among positives'
        effective['descriptive_only'] = True
    by_row = dict(zip((r['image_id'] for r in rows), x))

    def scorer(fit_rows, held_rows):
        fit_x = np.stack([by_row[r['image_id']] for r in fit_rows])
        fit_y = np.array([truth_of(r, split, task) for r in fit_rows])
        s, c = fit_linear(fit_x, fit_y, params, cfg.seed)
        held = np.stack([by_row[r['image_id']] for r in held_rows])
        return c.predict_proba(s.transform(held) if s is not None else held)[:, 1]

    effective.update(choose_threshold(cfg, split, task, output, scorer))
    write_json(output / 'pipeline.json', effective)
    write_json(folder / 'effective.json', effective)
    return output, effective


def train(cfg: Experiment, folder):
    import torch

    device_name(cfg.device)
    random.seed(cfg.seed)
    np.random.seed(cfg.seed)
    torch.manual_seed(cfg.seed)
    torch.set_num_threads(4)
    split = validate_split(inside(cfg.dataset))
    if split.get('purpose') == 'independent_test':
        raise ValueError('Reserved independent test snapshots cannot be used for model selection/training')
    if split['demo_only'] and not cfg.demo:
        raise ValueError('這是流程展示快照，必須明確勾選研究展示模式。')
    check_split_task(split, experiment_task(cfg.model, cfg.task))
    original = split
    if cfg.control == 'shuffled_labels':
        split = shuffled_labels(split, cfg.seed)
    if cfg.model in BASELINES:
        from src.workbench import baselines

        write_json(folder / 'experiment.json', {'requested': cfg.model_dump(), 'split': original, 'source': ''})
        return baselines.train(cfg, split, folder)
    base = prepare(cfg.model, folder) if not cfg.base_import else imported_base(cfg)
    write_json(
        folder / 'experiment.json',
        {
            'requested': cfg.model_dump(),
            'split': original,
            'source': MODELS[cfg.model]['source'],
            'prepared_hash': sha256(base) if base.is_file() else sha256(base / 'model.safetensors'),
        },
    )
    fn = efficient_train if cfg.model == 'efficientnet_b0' else dino_train
    return fn(cfg, split, folder, base)


class ModelPredictor:
    def __init__(self, ident, device='cpu'):
        import torch
        from src.workbench.registry import get, artifact_path

        self.metadata = get(ident)
        if self.metadata.get('extra', {}).get('purpose') == 'checkpoint':
            raise ValueError('Checkpoint 不是推論模型')
        self.path = artifact_path(ident)
        self.device = device_name(device)
        self.raw_device = device
        from src.data.tasks import SCHEMES

        self.config = read_json(config_path('service.json', ROOT))
        self.policy = InferenceConfig(**self.metadata['config'])
        self.kind = self.metadata['model']
        if self.kind not in MODELS:
            raise ValueError('這個模型種類已移除，不能再執行')
        self.task = MODELS[self.kind]['task']
        # Artifacts without an explicit task/scheme are legacy binary models and keep that meaning.
        self.training_task = experiment_task(self.kind, self.metadata.get('extra', {}).get('task'))
        self.scheme = self.policy.scheme
        self.classes = SCHEMES[self.scheme]['classes']
        if SCHEMES[self.scheme]['task'] != self.training_task:
            raise ValueError('模型任務與標籤方案不一致')
        self.size, self.pooling = 224, 'cls'
        if self.kind in BASELINES:
            from src.workbench.baselines import Baseline

            self.baseline = Baseline(self.kind, self.path, len(self.classes), self.device)
        elif self.kind == 'efficientnet_b0':
            self.model = load_efficient(classes=len(self.classes))
            self.model.load_state_dict(torch.load(self.path / 'model.pt', map_location='cpu', weights_only=True))
            self.model.to(self.device).eval()
        else:
            from transformers import Dinov2Model

            self.model = (
                Dinov2Model.from_pretrained(dino_weights(self.path), local_files_only=True, use_safetensors=True)
                .to(self.device)
                .eval()
            )
            pipeline = read_json(self.path / 'pipeline.json') if (self.path / 'pipeline.json').exists() else {}
            self.size = pipeline.get('resolution', 224)
            self.pooling = 'cls_mean' if pipeline.get('pooling') == 'CLS+mean' else 'cls'
            self.classifier = np.load(self.path / 'classifier.npz', allow_pickle=False)
            if self.classifier['classes'].tolist() != list(range(len(self.classes))):
                raise ValueError('Classifier label mapping mismatch')
            rows = self.classifier['coef'].shape[0]
            expected = 1 if len(self.classes) == 2 or 'coef2' in self.classifier.files else len(self.classes)
            if rows != expected:
                raise ValueError('Classifier output dimension does not match its label scheme')

    def class_scores(self, x):
        """Uncalibrated per-class model scores (softmax or sigmoid); never a disease probability."""
        import torch

        with torch.inference_mode():
            if self.kind == 'efficientnet_b0':
                return self.model(x).softmax(1)[0].cpu().numpy()
            features = dino_pool(self.model(pixel_values=x).last_hidden_state, self.pooling).cpu().numpy()
        c = self.classifier
        if 'coef2' in c.files:
            positive = logit_scores(c, features)[1]
            scaled = (features - c['mean']) / c['scale']
            stage2 = 1 / (1 + np.exp(-np.clip((scaled @ c['coef2'].T + c['intercept2'])[0, 0], -700, 700)))
            return np.array([1 - positive, positive * (1 - stage2), positive * stage2])
        return logit_scores(c, features)

    def predict(self, content):
        import torch
        import cv2

        start = time.perf_counter()
        im = decode_image(content, self.config)
        cfg = self.policy
        gray = np.asarray(ImageOps.grayscale(ImageOps.contain(im, (512, 512))))
        quality = {
            'blur_variance': float(cv2.Laplacian(gray, cv2.CV_64F).var()),
            'dark_fraction': float((gray < 15).mean()),
            'bright_fraction': float((gray > 240).mean()),
            'mode': cfg.quality_mode,
            'content_recognition': 'unsupported',
        }
        reasons = []
        if quality['blur_variance'] < cfg.blur_threshold:
            reasons.append('可能失焦，請確認拍攝清晰度')
        if quality['dark_fraction'] > cfg.dark_fraction:
            reasons.append('大部分畫面過暗')
        if quality['bright_fraction'] > cfg.bright_fraction:
            reasons.append('大部分畫面過亮')
        quality['reasons'] = reasons
        predicted_class = None
        scores = None
        decision = 'threshold'
        if self.kind in BASELINES:
            values = self.baseline.scores(im)
        else:
            values = self.class_scores(tensor_image(im, size=self.size).unsqueeze(0).to(self.device))
        scores = {name: round(float(v), 6) for name, v in zip(self.classes, values)}
        annotated = im
        if self.scheme == 'binary_v1':
            score = float(values[1])
            prediction = int(score >= cfg.threshold)
            predicted_class = 'positive' if prediction else 'negative'
            semantics = 'uncalibrated positive-class model score; not disease probability'
        else:
            # Stage models decide by argmax; the binary view is derived from the predicted class.
            index = int(np.argmax(values))
            predicted_class = self.classes[index]
            decision = 'argmax'
            prediction = int(predicted_class != 'normal')
            score = float(1 - values[self.classes.index('normal')])
            semantics = 'uncalibrated: 1 - normal-class softmax score; class decided by argmax; not disease probability or stage certainty'
        status = 'suspected' if prediction else 'not_detected'
        if reasons and cfg.quality_mode == 'reject':
            status = 'quality_rejected'
        jpeg, size = encode_result(annotated)
        record = {
            'schema_version': 2,
            'status': status,
            'task_type': self.task,
            'task': self.training_task,
            'label_scheme': self.scheme,
            'model_id': self.kind,
            'model_version': self.metadata['id'],
            'preprocess_version': cfg.preprocess,
            'prediction_score': score,
            'score_semantics': semantics,
            'decision_rule': {**cfg.model_dump(), 'decision': decision},
            'binary_prediction': prediction,
            'predicted_class': predicted_class,
            'class_scores': scores,
            'quality': quality,
            'demo_only': self.metadata['demo_only'],
            'elapsed_ms': round((time.perf_counter() - start) * 1000, 2),
            'source_size': list(im.size),
            'annotated_size': list(size),
            'severity': None,
        }
        return record, jpeg


def evaluate(ident, dataset, device, folder):
    from src.workbench.registry import get
    from src.workbench.metrics import binary_metrics, multiclass_metrics

    split = validate_split(inside(dataset))
    metadata = get(ident)
    predictor = ModelPredictor(ident, device)
    task = predictor.training_task
    if split.get('purpose') != 'independent_test':
        check_split_task(split, task)
    if split_scheme(split) != predictor.scheme:
        raise ValueError('評估快照的標籤方案與模型不同，不能比較（例如二分類模型不能以分期快照評估）')
    training_dataset = metadata.get('extra', {}).get('dataset')
    actual_training = validate_split(inside(training_dataset)) if training_dataset else split
    if split.get('purpose') != 'independent_test' and training_dataset and inside(training_dataset) != inside(dataset):
        raise ValueError(
            'Validation must match the trained fold; choose an explicitly reserved independent test snapshot for external evaluation'
        )
    if {m['group'] for m in actual_training['members']['train']} & {m['group'] for m in split['members']['val']}:
        raise ValueError('Evaluation contains a training subject')
    multiclass = predictor.scheme != 'binary_v1'

    def predicted(result):
        return predictor.classes.index(result['predicted_class']) if multiclass else result['binary_prediction']

    records = []
    for n, row in enumerate(split['members']['val']):
        check_cancel(folder)
        sample = {'image_id': row['image_id'], 'group': row['group'], 'truth': truth_of(row, split, task)}
        try:
            result, _ = predictor.predict(inside(row['image_path']).read_bytes())
            sample.update(
                prediction=predicted(result),
                status=result['status'],
                score=result['prediction_score'],
                class_scores=result.get('class_scores'),
                elapsed_ms=result['elapsed_ms'],
                quality=result['quality'],
                source_size=result.get('source_size'),
                annotated_size=result.get('annotated_size'),
            )
        except Exception as exc:
            sample.update(error=type(exc).__name__ + ': ' + str(exc), prediction=None)
        records.append(sample)
        progress(folder, 'evaluating', completed=n + 1, total=len(split['members']['val']))
    score = (
        (lambda samples, expected=None: multiclass_metrics(samples, predictor.classes, expected))
        if multiclass
        else binary_metrics
    )
    metrics = score(records, [r['image_id'] for r in split['members']['val']])
    # Evaluate training fit without augmentation; never label this as validation accuracy.
    train_samples = []
    for row in actual_training['members']['train']:
        check_cancel(folder)
        r, _ = predictor.predict(inside(row['image_path']).read_bytes())
        train_samples.append(
            {
                'image_id': row['image_id'],
                'truth': truth_of(row, actual_training, task),
                'prediction': predicted(r),
                'status': r['status'],
            }
        )
    report = {
        'schema_version': 2,
        'task': task,
        'label_scheme': predictor.scheme,
        'classes': predictor.classes if multiclass else ['negative', 'positive'],
        'artifact': ident,
        'artifact_hash': metadata['artifact_hash'],
        'model': metadata['model'],
        'config': metadata['config'],
        'dataset': dataset,
        'snapshot': inside(dataset).parent.parent.name,
        'split_hash': sha256(inside(dataset).parent / 'split.json'),
        'fold': split['fold'],
        'repeat': split.get('repeat', 0),
        'evaluated_at': stamp(),
        'purpose': 'validation',
        'demo_only': split['demo_only'],
        'selection_bias': 'fixed epochs and a training-fold threshold; validation picks nothing inside a run',
        'metrics': metrics,
        'samples': records,
        'train_groups': sorted({r['group'] for r in split['members']['train']}),
        'training_fit': score(train_samples),
        'code_version': code_version(),
    }
    report.update(
        report_id=folder.name,
        purpose=split.get('purpose', 'validation'),
        train_groups=sorted({r['group'] for r in actual_training['members']['train']}),
        training_members_hash=digest(sorted(r['image_id'] for r in actual_training['members']['train'])),
        expected_folds=len(read_json(inside(dataset).parent.parent / 'dataset_version.json')['folds']),
    )
    experiment = ROOT / 'runs/workbench/jobs' / metadata['experiment'] / 'request.json'
    if experiment.exists():
        protocol = read_json(experiment)['config'].copy()
        for key in ('dataset', 'resume_job'):
            protocol.pop(key, None)
        report['training_protocol'] = protocol
    write_json(folder / 'report.json', report)
    return report


def code_version():
    return digest({str(p.relative_to(CODE_ROOT)): sha256(p) for p in (CODE_ROOT / 'src').rglob('*.py')})


def prepare_verified(model, folder):
    """Explicit prepare uses a fresh official download to establish provenance.

    This runs only in a dedicated worker process while holding the compute lock.
    Existing official files are never overwritten on a different hash.
    """
    global PRETRAINED
    original = PRETRAINED
    verification = folder / 'official_verification'
    try:
        PRETRAINED = verification
        downloaded = prepare(model, folder)
    finally:
        PRETRAINED = original
    destination = original / downloaded.name
    if not destination.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        if downloaded.is_dir():
            shutil.copytree(downloaded, destination)
        else:
            shutil.copy2(downloaded, destination)
    elif downloaded.is_file() and sha256(downloaded) != sha256(destination):
        raise ValueError('既有基礎權重與本次官方下載不同；已保留既有檔案，請核對來源')
    elif downloaded.is_dir():
        expected = {p.relative_to(downloaded).as_posix(): sha256(p) for p in downloaded.rglob('*') if p.is_file()}
        actual = {p.relative_to(destination).as_posix(): sha256(p) for p in destination.rglob('*') if p.is_file()}
        if expected != actual:
            raise ValueError('既有基礎權重目錄與官方下載不同；已保留既有檔案')
    return destination


def imported_base(cfg):
    from src.imports.service import resolve_package

    path, package = resolve_package(ROOT, cfg.base_import, 'base', cfg.model)
    return path if cfg.model == 'dinov2_small' else path / next(iter(package['files']))


def resume_folder(cfg):
    if not cfg.checkpoint_import:
        return ROOT / 'runs/workbench/jobs' / cfg.resume_job
    from src.imports.service import resolve_package

    path, package = resolve_package(ROOT, cfg.checkpoint_import, 'checkpoint', cfg.model)
    if package['source']['id'] != cfg.resume_job:
        raise ValueError('Checkpoint 原工作不相符')
    return path
