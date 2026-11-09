"""Evaluation reading aids (batch 4): confidence intervals and a plain-language summary
(B2), the error gallery (B3), three-fold aggregation (B1), Grad-CAM heat maps (B4),
snapshot differences (B7) and model cards (B8).

Everything here is read-only and derived from the saved reports; old reports keep their
meaning.  Intervals: a percentile bootstrap (2000 resamples, fixed seed) that draws whole
patients, because photos of one patient are not independent.  Reports without patient groups
fall back to Wilson intervals and a bootstrap over images.
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

Z = 1.959964
BOOT = 2000


# ---------------------------------------------------------------- statistics
def wilson(k: int, n: int) -> list[float] | None:
    if not n:
        return None
    p = k / n
    centre = (p + Z * Z / (2 * n)) / (1 + Z * Z / n)
    half = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / (1 + Z * Z / n)
    return [max(0.0, centre - half), min(1.0, centre + half)]


def _binary_ba(samples):
    tp = sum(s['truth'] == 1 and s['prediction'] == 1 for s in samples)
    fn = sum(s['truth'] == 1 and s['prediction'] == 0 for s in samples)
    tn = sum(s['truth'] == 0 and s['prediction'] == 0 for s in samples)
    fp = sum(s['truth'] == 0 and s['prediction'] == 1 for s in samples)
    if not (tp + fn) or not (tn + fp):
        return None
    return (tp / (tp + fn) + tn / (tn + fp)) / 2


def _macro_f1(samples, k):
    f1s = []
    for c in range(k):
        tp = sum(s['truth'] == c and s['prediction'] == c for s in samples)
        fp = sum(s['truth'] != c and s['prediction'] == c for s in samples)
        fn = sum(s['truth'] == c and s['prediction'] != c for s in samples)
        if tp + fn == 0:
            return None
        p = tp / (tp + fp) if tp + fp else None
        r = tp / (tp + fn)
        if p is None:
            f1s.append(0.0)
        else:
            f1s.append(2 * p * r / (p + r) if p + r else 0.0)
    return sum(f1s) / k


def _macro_mae(samples, k):
    """Mean stage distance, averaged over the classes that occur (normal < stage1 < stage2)."""
    errors = []
    for c in range(k):
        rows = [abs(s['prediction'] - c) for s in samples if s['truth'] == c]
        if rows:
            errors.append(sum(rows) / len(rows))
    return sum(errors) / len(errors) if errors else None


def bootstrap(samples, fn, seed=0) -> list[float] | None:
    """Resamples whole patients when every sample names one, otherwise single samples."""
    if len(samples) < 5:
        return None
    rng = random.Random(seed)
    clusters: dict = {}
    if all(s.get('group') for s in samples):
        for s in samples:
            clusters.setdefault(s['group'], []).append(s)
        if len(clusters) < 3:
            return None
    units = list(clusters.values()) or [[s] for s in samples]
    values = []
    n = len(units)
    for _ in range(BOOT):
        value = fn([s for _ in range(n) for s in units[rng.randrange(n)]])
        if value is not None:
            values.append(value)
    if len(values) < BOOT * 0.8:
        return None
    values.sort()
    return [values[int(0.025 * (len(values) - 1))], values[int(0.975 * (len(values) - 1))]]


def _rate(valid, hit, among, k, n):
    """Interval of a proportion and how it was made."""
    if valid and all(s.get('group') for s in valid):

        def value(rows):
            base = [s for s in rows if among(s)]
            return sum(hit(s) for s in base) / len(base) if base else None

        return bootstrap(valid, value), 'patient_bootstrap'
    return wilson(k, n), 'wilson'


def calibration(samples, bins=5) -> dict | None:
    """Brier score and a reliability table of the positive score.  Shown only: nothing recalibrates."""
    rows = [(float(s['score']), s['truth']) for s in samples if isinstance(s.get('score'), (int, float))]
    if not rows:
        return None
    table = []
    for i in range(bins):
        low, high = i / bins, (i + 1) / bins
        part = [(p, y) for p, y in rows if low <= p < high or (i == bins - 1 and p == 1)]
        if part:
            table.append(
                {
                    'low': low,
                    'high': high,
                    'n': len(part),
                    'score': sum(p for p, _ in part) / len(part),
                    'observed': sum(y for _, y in part) / len(part),
                }
            )
    return {'brier': sum((p - y) ** 2 for p, y in rows) / len(rows), 'bins': table, 'n': len(rows)}


def _pct(v):
    return '—' if v is None else f'{v * 100:.0f}%'


def _ci_text(ci):
    return '' if not ci else f'（95% 信賴區間 {_pct(ci[0])}–{_pct(ci[1])}）'


def _valid(samples, multiclass, k=2):
    out = []
    for s in samples:
        t, p = s.get('truth'), s.get('prediction')
        if s.get('error') or not isinstance(t, int) or not isinstance(p, int) or not (0 <= t < k and 0 <= p < k):
            continue
        if multiclass and s.get('status') in ('quality_rejected', 'needs_review'):
            continue
        out.append(
            {'truth': t, 'prediction': p, **{k: s[k] for k in ('group', 'score', 'image_id') if s.get(k) is not None}}
        )
    return out


def summarize(
    samples: list[dict],
    *,
    classes: list[str] | None,
    multiclass: bool,
    demo_only: bool,
    subjects: int | None = None,
    task: str | None = None,
) -> dict:
    """Metrics with intervals and plain sentences, from per-image results."""
    from src.workbench.metrics import multiclass_metrics

    names = {'negative': '正常', 'positive': '陽性', 'normal': '正常', 'stage1': '第一期', 'stage2': '第二期'}
    k = len(classes) if multiclass and classes else 2
    valid = _valid(samples, multiclass, k)
    n = len(valid)
    lines, rows = [], []
    if not multiclass:
        tp = sum(s['truth'] == 1 and s['prediction'] == 1 for s in valid)
        fn = sum(s['truth'] == 1 and s['prediction'] == 0 for s in valid)
        tn = sum(s['truth'] == 0 and s['prediction'] == 0 for s in valid)
        fp = sum(s['truth'] == 0 and s['prediction'] == 1 for s in valid)
        pos, neg = tp + fn, tn + fp
        sens = tp / pos if pos else None
        spec = tn / neg if neg else None
        fpr = fp / neg if neg else None
        prec = tp / (tp + fp) if tp + fp else None
        ba = (sens + spec) / 2 if sens is not None and spec is not None else None
        acc = (tp + tn) / n if n else None
        truth_pos, truth_neg = (lambda s: s['truth'] == 1), (lambda s: s['truth'] == 0)
        said_pos = lambda s: s['prediction'] == 1  # noqa: E731
        right = lambda s: s['prediction'] == s['truth']  # noqa: E731

        def row(key, name, value, hit, among, k_, n_):
            ci, method = _rate(valid, hit, among, k_, n_)
            return {'key': key, 'name': name, 'value': value, 'ci': ci, 'method': method, 'count': f'{k_}/{n_}'}

        rows = [
            {
                'key': 'balanced_accuracy',
                'name': '平衡準確率',
                'value': ba,
                'ci': bootstrap(valid, _binary_ba),
                'method': 'bootstrap',
            },
            row('sensitivity', '敏感度（陽性找出比例）', sens, said_pos, truth_pos, tp, pos),
            row('specificity', '特異度（正常判為正常）', spec, right, truth_neg, tn, neg),
            row('false_positive_rate', '正常照片誤報率', fpr, said_pos, truth_neg, fp, neg),
            row('precision', '判為陽性中確實為陽性', prec, truth_pos, said_pos, tp, tp + fp),
            row('accuracy', '準確率', acc, right, lambda s: True, tp + tn, n),
        ]
        if pos:
            lines.append(
                f'在 {pos} 張陽性照片中找出 {tp} 張，漏掉 {fn} 張（敏感度 {_pct(sens)}{_ci_text(rows[1]["ci"])}）。'
            )
        if neg:
            lines.append(f'在 {neg} 張正常照片中，{fp} 張被誤判為陽性（誤報率 {_pct(fpr)}{_ci_text(rows[3]["ci"])}）。')
        if ba is not None:
            lines.append(f'兩類各占一半時的平均正確率（平衡準確率）為 {_pct(ba)}{_ci_text(rows[0]["ci"])}。')
        matrix = {'kind': 'binary', 'tp': tp, 'fn': fn, 'fp': fp, 'tn': tn}
    else:
        m = multiclass_metrics(
            [{**s, 'image_id': str(i), 'status': 'ok'} for i, s in enumerate(valid)],
            classes,
            [str(i) for i in range(len(valid))],
        )
        correct = sum(m['confusion_matrix'][i][i] for i in range(k))
        accuracy_ci = _rate(valid, lambda s: s['prediction'] == s['truth'], lambda s: True, correct, n)
        rows = [
            {
                'key': 'macro_f1',
                'name': 'Macro F1（各期平均）',
                'value': m['macro_f1'],
                'ci': bootstrap(valid, lambda xs: _macro_f1(xs, k)),
                'method': 'bootstrap',
            },
            {
                'key': 'macro_mae',
                'name': 'Macro-MAE（平均差幾期，越小越好）',
                'value': _macro_mae(valid, k),
                'ci': bootstrap(valid, lambda xs: _macro_mae(xs, k)),
                'method': 'bootstrap',
            },
            {
                'key': 'accuracy',
                'name': '準確率',
                'value': m['accuracy'],
                'ci': accuracy_ci[0],
                'method': accuracy_ci[1],
                'count': f'{correct}/{n}',
            },
        ]
        for i, c in enumerate(classes):
            support = sum(m['confusion_matrix'][i])
            hit = m['confusion_matrix'][i][i]
            ci, method = _rate(valid, lambda s, i=i: s['prediction'] == i, lambda s, i=i: s['truth'] == i, hit, support)
            rows.append(
                {
                    'key': 'recall_' + c,
                    'name': f'{names.get(c, c)}的找出比例',
                    'value': hit / support if support else None,
                    'ci': ci,
                    'method': method,
                    'count': f'{hit}/{support}',
                }
            )
            if support:
                wrong = [
                    f'{names.get(classes[j], classes[j])} {m["confusion_matrix"][i][j]} 張'
                    for j in range(k)
                    if j != i and m['confusion_matrix'][i][j]
                ]
                lines.append(
                    f'{names.get(c, c)} {support} 張中判對 {hit} 張（{_pct(hit / support)}）'
                    + (f'，誤判為 ' + '、'.join(wrong) if wrong else '')
                    + '。'
                )
        if m['macro_f1'] is not None:
            lines.append(f'各期平均的 F1 為 {_pct(m["macro_f1"])}{_ci_text(rows[0]["ci"])}。')
        matrix = {'kind': 'multiclass', 'classes': classes, 'confusion_matrix': m['confusion_matrix']}
    cautions = []
    if n < 30:
        cautions.append(f'只有 {n} 張驗證照片，信賴區間很寬，數字可能大幅變動。')
    if subjects is not None and subjects < n:
        cautions.append(f'這些照片來自 {subjects} 位病人；同一人的照片並不獨立，實際不確定性比區間更大。')
    if demo_only:
        cautions.append('這是流程展示，結果不能當正式成績。')
    cautions.append('模型分數未校準，不是疾病機率；此結果只供研究參考，不能作為診斷。')
    patients = {s['group'] for s in valid if s.get('group')}
    return {
        'n': n,
        'photos': len({s['image_id'] for s in valid if s.get('image_id')}) or n,
        'patients': len(patients) or subjects,
        'calibration': None if multiclass else calibration(valid),
        'metrics': rows,
        'lines': lines,
        'cautions': cautions,
        'matrix': matrix,
        'method': '95% 區間：2000 次 bootstrap 百分位區間（固定種子），以病人為單位重抽；沒有病人分組的舊報告才用 Wilson。',
    }


def _report_kind(report):
    multiclass = (report.get('metrics') or {}).get('kind') == 'multiclass'
    classes = report.get('classes') if multiclass else ['negative', 'positive']
    return multiclass, classes


def removed_photos(samples: list[dict], root: Path) -> int:
    """Photos of a report that left the project; such a result no longer describes the data."""
    from src.common import read_manifest

    if not (root / 'data/manifest.csv').exists():
        return 0
    current = {r['image_id'] for r in read_manifest(root)}
    return len({s['image_id'] for s in samples if s.get('image_id')} - current)


def _unverified(n: int) -> str:
    return f'待驗證：含 {n} 張已移出專案的照片，這個成績不能代表目前的資料。'


def report_summary(report: dict, root: Path | None = None) -> dict:
    multiclass, classes = _report_kind(report)
    groups = {s.get('group') for s in report.get('samples', []) if s.get('group')}
    summary = summarize(
        report.get('samples', []),
        classes=classes,
        multiclass=multiclass,
        demo_only=bool(report.get('demo_only')),
        subjects=len(groups) or None,
        task=report.get('task'),
    )
    if ((report.get('training_protocol') or {}).get('parameters') or {}).get('strategy') == 'hierarchical':
        summary['cautions'].insert(0, '階層式分期是描述性分析，不當正式分期結果。')
    removed = removed_photos(report.get('samples', []), root) if root else 0
    if removed:
        summary['cautions'].insert(0, _unverified(removed))
    return summary


# ---------------------------------------------------------------- error gallery
def errors(report: dict, root: Path) -> dict:
    from src.common import read_manifest

    multiclass, classes = _report_kind(report)
    names = {'negative': '正常', 'positive': '陽性', 'normal': '正常', 'stage1': '第一期', 'stage2': '第二期'}
    known = {r['image_id'] for r in read_manifest(root)}
    area = 'cls'
    groups: dict[str, dict] = {}
    for s in report.get('samples', []):
        t, p = s.get('truth'), s.get('prediction')
        if s.get('error'):
            key, title = 'failed', '分析失敗'
        elif t is None or p is None or t == p:
            continue
        elif not multiclass:
            key, title = (
                ('missed', '漏掉的陽性（實際陽性、判為正常）')
                if t == 1
                else ('false_alarm', '誤報（實際正常、判為陽性）')
            )
        else:
            key = f'{classes[t]}->{classes[p]}'
            title = f'實際{names.get(classes[t], classes[t])}、判為{names.get(classes[p], classes[p])}'
        g = groups.setdefault(key, {'key': key, 'title': title, 'items': []})
        g['items'].append(
            {
                'image_id': s['image_id'],
                'score': s.get('score'),
                'status': s.get('status'),
                'error': s.get('error'),
                'report': report.get('report_id'),
                'fold': report.get('fold'),
                'review_href': f"#data?area={area}&view=all&image={s['image_id']}" if s['image_id'] in known else None,
            }
        )
    order = ['missed', 'false_alarm']
    return {
        'groups': sorted(
            groups.values(),
            key=lambda g: (g['key'] not in order, order.index(g['key']) if g['key'] in order else 0, g['key']),
        ),
        'total': sum(len(g['items']) for g in groups.values()),
    }


# ---------------------------------------------------------------- three-fold groups
def groups(root: Path, model: str = '') -> list[dict]:
    from src.workbench import ledger, report_views
    from src.workbench.contracts import BASELINES

    out: dict[str, dict] = {}
    for r in report_views.listing():
        group = (r.get('training_protocol') or {}).get('cv_group')
        if (
            not group
            or r.get('purpose') == 'independent_test'
            or r.get('source_model_state') == 'purged'
            or (model and r.get('model') != model)
        ):
            continue
        g = out.setdefault(
            group,
            {
                'cv_group': group,
                'model': r.get('model'),
                'task': r.get('task'),
                'label_scheme': r.get('label_scheme'),
                'snapshot': r.get('snapshot'),
                'expected_folds': r.get('expected_folds'),
                'name': (r.get('training_protocol') or {}).get('name'),
                'folds': {},
            },
        )
        current = g['folds'].get(r['fold'])
        if not current or (r.get('evaluated_at') or '') > (current.get('evaluated_at') or ''):
            g['folds'][r['fold']] = r
    result = []
    for g in out.values():
        folds = [g['folds'][k] for k in sorted(g['folds'])]
        multiclass, classes = _report_kind(folds[0])
        samples = [s for r in folds for s in r.get('samples', [])]
        subjects = {s.get('group') for s in samples if s.get('group')}
        summary = summarize(
            samples,
            classes=classes,
            multiclass=multiclass,
            demo_only=any(r.get('demo_only') for r in folds),
            subjects=len(subjects) or None,
            task=g['task'],
        )
        removed = removed_photos(samples, root)
        if removed:
            summary['cautions'].insert(0, _unverified(removed))
        key = 'macro_f1' if multiclass else 'balanced_accuracy'
        repeats = sorted({r.get('repeat', 0) for r in folds})
        if len(repeats) > 1:
            # One value per repeat, from all of that repeat's folds together: a fold alone has
            # too few patients to mean anything.
            score = (lambda xs: _macro_f1(xs, len(classes))) if multiclass else _binary_ba
            values = [
                score(
                    _valid(
                        [s for r in folds if r.get('repeat', 0) == n for s in r.get('samples', [])],
                        multiclass,
                        len(classes or [0, 1]),
                    )
                )
                for n in repeats
            ]
        else:
            values = [(r.get('metrics') or {}).get(key) for r in folds]
        present = [v for v in values if v is not None]
        mean = sum(present) / len(present) if present else None
        sd = math.sqrt(sum((v - mean) ** 2 for v in present) / (len(present) - 1)) if len(present) > 1 else None
        name = g['name'] or ''
        if ' · fold' in name:
            name = name.split(' · fold')[0]
        result.append(
            {
                **{k: v for k, v in g.items() if k != 'folds'},
                'name': name or None,
                'complete': g['expected_folds'] is not None
                and len(folds) >= g['expected_folds']
                and all((r.get('metrics') or {}).get('complete') for r in folds),
                'fold_count': len(folds),
                'repeats': len(repeats),
                'removed_photos': removed,
                'baseline': g['model'] in BASELINES,
                'ledger': ledger.summary(root, g['snapshot']),
                'key_metric': key,
                'mean': mean,
                'sd': sd,
                'pooled': summary,
                'folds': [
                    {
                        'fold': r['fold'],
                        'repeat': r.get('repeat', 0),
                        'report_id': r['report_id'],
                        'artifact': r.get('artifact'),
                        'evaluated_at': r.get('evaluated_at'),
                        'value': (r.get('metrics') or {}).get(key),
                        'accuracy_display': (r.get('metrics') or {}).get('accuracy_display'),
                        'complete': (r.get('metrics') or {}).get('complete'),
                    }
                    for r in folds
                ],
                'evaluated_at': max((r.get('evaluated_at') or '') for r in folds),
            }
        )
    result.sort(key=lambda g: g['evaluated_at'], reverse=True)
    return result


def group_errors(root: Path, cv_group: str) -> dict:
    match = next((g for g in groups(root) if g['cv_group'] == cv_group), None)
    if not match:
        raise FileNotFoundError(cv_group)
    from src.workbench import report_views

    merged: dict[str, dict] = {}
    for fold in match['folds']:
        report = {**report_views.get(fold['report_id']), 'report_id': fold['report_id']}
        for g in errors(report, root)['groups']:
            target = merged.setdefault(g['key'], {'key': g['key'], 'title': g['title'], 'items': []})
            target['items'] += g['items']
    return {'groups': list(merged.values()), 'total': sum(len(g['items']) for g in merged.values())}


# ---------------------------------------------------------------- snapshot differences
def _members(root: Path, version: str) -> tuple[dict, dict]:
    from src.workbench.trash import snapshot_root

    info = json.loads((snapshot_root(version) / 'dataset_version.json').read_text(encoding='utf-8-sig'))
    members = {}
    for fold in info.get('folds', []):
        for subset in fold.get('members', {}).values():
            for m in subset:
                if isinstance(m, dict):
                    members[m['image_id']] = m.get('target') or m.get('label_state')
    return info, members


def snapshot_diff(root: Path, a: str, b: str) -> dict:
    if a == b:
        raise ValueError('請選擇兩個不同的快照')
    info_a, ma = _members(root, a)
    info_b, mb = _members(root, b)
    names = {}
    try:
        from src.data import sources

        for ident, entry in sources.load(root)['images'].items():
            alias = next(iter(entry.get('aliases', [])), None)
            if alias:
                names[ident] = alias['filename']
    except Exception:
        pass
    added = sorted(set(mb) - set(ma))
    removed = sorted(set(ma) - set(mb))
    changed = sorted(i for i in set(ma) & set(mb) if ma[i] != mb[i])
    item = lambda i, before=None, after=None: {
        'image_id': i,
        'display_name': names.get(i),
        'before': before,
        'after': after,
    }
    return {
        'a': {
            'version': a,
            'name': info_a.get('name'),
            'task': info_a.get('task'),
            'count': len(ma),
            'created_at': info_a.get('created_at'),
        },
        'b': {
            'version': b,
            'name': info_b.get('name'),
            'task': info_b.get('task'),
            'count': len(mb),
            'created_at': info_b.get('created_at'),
        },
        'same_task': info_a.get('task') == info_b.get('task'),
        'added': [item(i, after=mb[i]) for i in added],
        'removed': [item(i, before=ma[i]) for i in removed],
        'changed': [item(i, ma[i], mb[i]) for i in changed],
        'unchanged': len(set(ma) & set(mb)) - len(changed),
    }


# ---------------------------------------------------------------- heat maps (EfficientNet Grad-CAM)
import threading

_heat_lock = threading.Lock()
HEATMAP_NOTE = '熱區圖顯示模型做出這次判斷時較依賴的區域（Grad-CAM），不是病灶位置，也不代表模型理解醫學意義。'


def heatmap(root: Path, report_id: str, image: str) -> Path:
    from src.workbench import report_views

    report = report_views.get(report_id)
    model = report.get('model') or ''
    if model != 'efficientnet_b0' and not model.startswith('dinov2'):
        raise ValueError('基線沒有熱區圖')
    source = report_views.image_path(report_id, image)  # refuses withdrawn data (410) and foreign images
    folder = root / 'runs/workbench/evaluations' / report_id / 'heatmaps'
    target = folder / (image + '.png')
    if target.is_file():
        return target
    from src.lock import OperationLock

    with _heat_lock:  # gallery images arrive together; compute them one at a time
        if target.is_file():
            return target
        try:
            lock = OperationLock()
            lock.__enter__()
        except RuntimeError as exc:
            raise RuntimeError('運算資源正在使用（訓練、評估或 LINE 服務），請稍後再產生熱區圖。') from exc
        try:
            overlay = (_gradcam if model == 'efficientnet_b0' else _attention)(report['artifact'], source)
        finally:
            lock.__exit__(None, None, None)
        folder.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix('.tmp.png')
        overlay.save(tmp, 'PNG')
        tmp.replace(target)
    return target


def _gradcam(artifact: str, source: Path):
    import numpy as np
    import torch
    from PIL import Image, ImageOps
    from src.workbench.adapters import ModelPredictor, tensor_image

    predictor = ModelPredictor(artifact, 'cpu')
    model = predictor.model.cpu().eval()
    with Image.open(source) as im:
        image = ImageOps.exif_transpose(im).convert('RGB')
    x = tensor_image(image).unsqueeze(0)
    store = {}
    layer = model.features[-1]
    forward = layer.register_forward_hook(lambda m, i, o: store.__setitem__('a', o))
    backward = layer.register_full_backward_hook(lambda m, gi, go: store.__setitem__('g', go[0]))
    try:
        for p in model.parameters():
            p.requires_grad_(True)
        with torch.enable_grad():
            logits = model(x)
            target = int(logits.argmax(1))
            model.zero_grad()
            logits[0, target].backward()
    finally:
        forward.remove()
        backward.remove()
    a, g = store['a'][0].detach(), store['g'][0].detach()
    cam = torch.relu((g.mean((1, 2))[:, None, None] * a).sum(0))
    del predictor, model
    return _overlay(image, cam, 224)


def _attention(artifact: str, source: Path):
    """DINOv2: how much the CLS token looks at each patch in the last layer, heads averaged."""
    import torch
    from PIL import Image, ImageOps
    from transformers import Dinov2Model
    from src.common import read_json
    from src.workbench import registry
    from src.workbench.adapters import dino_weights, tensor_image

    path = registry.artifact_path(artifact)
    pipeline = read_json(path / 'pipeline.json') if (path / 'pipeline.json').exists() else {}
    size = pipeline.get('resolution', 224)
    model = Dinov2Model.from_pretrained(
        dino_weights(path), local_files_only=True, use_safetensors=True, attn_implementation='eager'
    ).eval()
    with Image.open(source) as im:
        image = ImageOps.exif_transpose(im).convert('RGB')
    with torch.inference_mode():
        out = model(pixel_values=tensor_image(image, size=size).unsqueeze(0), output_attentions=True)
    side = size // model.config.patch_size
    cam = out.attentions[-1][0].mean(0)[0, 1:].reshape(side, side)
    del model
    return _overlay(image, cam, size)


def _overlay(image, cam, size):
    """Blend a coarse map onto the photo, undoing the square letterbox."""
    import numpy as np
    import torch
    from PIL import Image

    cam = torch.nn.functional.interpolate(
        cam[None, None].float(), size=(size, size), mode='bilinear', align_corners=False
    )[0, 0].numpy()
    cam = cam - cam.min()
    if cam.max() > 0:
        cam = cam / cam.max()
    w, h = image.size
    scale = min(size / w, size / h)
    nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
    left, top = (size - nw) // 2, (size - nh) // 2
    region = Image.fromarray((cam[top : top + nh, left : left + nw] * 255).astype('uint8')).resize(
        (w, h), Image.Resampling.BILINEAR
    )
    weight = np.asarray(region, dtype=np.float32) / 255
    import matplotlib

    colour = matplotlib.colormaps['inferno'](weight)[..., :3]
    base = np.asarray(image, dtype=np.float32) / 255
    alpha = (0.15 + 0.5 * weight)[..., None]
    blended = base * (1 - alpha) + colour * alpha
    return Image.fromarray((blended * 255).clip(0, 255).astype('uint8'))


def model_card(root: Path, ident: str) -> dict:
    from src.common import read_json
    from src.workbench import registry, jobs
    from src.common import snapshot_folder
    from src.workbench.contracts import MODELS

    meta = next((m for m in registry.listing() if m['id'] == ident), None)
    if meta is None:
        raise FileNotFoundError(ident)
    extra = meta.get('extra', {})
    request = {}
    try:
        path = jobs.folder(meta['experiment']) / 'request.json'
        request = read_json(path)['config'] if path.exists() else {}
    except (ValueError, OSError):
        pass
    dataset = extra.get('dataset') or request.get('dataset')
    data = None
    if dataset and str(dataset).startswith('data/') and str(dataset).count('/') >= 3:
        version = str(dataset).split('/')[2]
        try:
            info = json.loads((snapshot_folder(version, root) / 'dataset_version.json').read_text(encoding='utf-8-sig'))
            fold = next((f for f in info.get('folds', []) if f.get('dataset') == dataset), None)
            counts = {k: len(v) for k, v in (fold or {}).get('members', {}).items()}
            from collections import Counter

            classes = {
                k: dict(Counter((m.get('target') or m.get('label_state')) for m in v if isinstance(m, dict)))
                for k, v in (fold or {}).get('members', {}).items()
            }
            data = {
                'snapshot': version,
                'name': info.get('name'),
                'fold': (fold or {}).get('fold'),
                'folds': len(info.get('folds', [])),
                'counts': counts,
                'classes': classes,
                'demo_only': info.get('demo_only'),
                'created_at': info.get('created_at'),
            }
        except (OSError, ValueError):
            data = {'snapshot': version}
    applicable = [r for r in meta.get('reports', []) if r.get('applicable') is not False]
    reports = [r for r in applicable if r.get('purpose') != 'independent_test']
    tests = [r for r in applicable if r.get('purpose') == 'independent_test']
    latest = reports[-1] if reports else None
    independent = None
    if tests:
        from src.workbench import report_views

        try:
            t = tests[-1]
            independent = {
                'report_id': t['report_id'],
                'snapshot': t.get('snapshot'),
                'accuracy_display': (t.get('metrics') or {}).get('accuracy_display'),
                'summary': report_summary(report_views.get(t['report_id'])),
            }
        except Exception:
            independent = None
    summary = None
    if latest:
        from src.workbench import report_views

        try:
            summary = report_summary(report_views.get(latest['report_id']))
        except Exception:
            summary = None
    refs = {}
    for target in ('local', 'line', 'shadow'):
        path = registry.REFS / (target + '.json')
        value = read_json(path) if path.exists() else None
        refs[target] = bool(value and value.get('artifact') == ident)
    effective = (extra.get('effective') or {}).get('parameters') or {}
    training = {
        k: request.get(k)
        for k in ('epochs', 'batch', 'imgsz', 'seed', 'patience', 'device')
        if request.get(k) is not None
    }
    for key in ('learning_rate', 'lr0', 'optimizer', 'freeze', 'class_weight', 'C', 'solver'):
        if key in effective:
            training[key] = effective[key]
    limitations = [
        '研究原型，不可作為臨床診斷。',
        '模型分數未校準，不是疾病機率。',
        '只在本專案的照片上訓練與驗證，換拍攝條件或醫院時表現可能不同。',
    ]
    if meta.get('demo_only'):
        limitations.append('這是流程展示模型，不能當正式成績。')
    if meta.get('attention'):
        limitations.append('需要重新評估：' + str(meta['attention'].get('reason', '')))
    if extra.get('source') == 'external':
        from src.workbench.external_models import NOTE

        # Replaces 「只在本專案的照片上訓練與驗證」, which is not true for this model.
        limitations[2] = (
            '在本專案以外訓練（' + str(extra.get('training_data', '未說明')) + '），只在本專案的照片上驗證。'
        )
        limitations.append(NOTE)
    task = meta.get('task')
    use = {
        'binary_classification': '判斷整張照片為正常或陽性（疑似靜脈炎），不提供位置。',
        'stage_classification': '把整張照片分為正常、第一期或第二期，不提供位置。',
    }.get(task, '')
    return {
        'id': ident,
        'model': meta['model'],
        'model_name': MODELS.get(meta['model'], {}).get('name', meta['model']),
        'task': task,
        'label_scheme': meta.get('label_scheme'),
        'created': meta['created'],
        'experiment': meta['experiment'],
        'experiment_name': request.get('name'),
        'cv_group': request.get('cv_group'),
        'intended_use': use,
        'data': data,
        'training': training,
        'evaluation': (
            {
                'report_id': latest['report_id'],
                'fold': latest.get('fold'),
                'accuracy_display': (latest.get('metrics') or {}).get('accuracy_display'),
                'summary': summary,
            }
            if latest
            else None
        ),
        'evaluation_status': meta.get('evaluation_status'),
        'in_use': refs,
        'limitations': limitations,
        'demo_only': meta.get('demo_only'),
        'independent_test': independent,
        'holdout': bool(request.get('independent_test')),
    }
