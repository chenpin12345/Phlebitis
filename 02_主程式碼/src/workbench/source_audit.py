"""Data trust page (#1, #2): could the labels be explained by where a photo came from?

Three checks on approved photos, none of which looks at the lesion on purpose:
  * source x class table;
  * a model that sees only file metadata (size, format, camera, EXIF);
  * a colour-histogram model.
Every score is compared with the same model trained on shuffled labels, so 0.5 is not assumed.
A photo's filename is never a feature.  Results hold counts only, never codes or filenames.
"""

from __future__ import annotations

import io
import math
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from src.common import ROOT, inside, read_json, read_manifest, rows_digest, stamp, write_json
from src.data import sources, tasks

PATH = 'runtime/source_audit.json'
SOURCE_NAMES = {'gangshan': '岡山高醫', 'line': 'LINE', 'other': '其他'}
MIN_PER_CLASS = 3
MIN_PATIENTS_PER_CLASS = 5  # below this a class is one or two people, not a population
REPEATS = 5
SHUFFLES = 20
METADATA_ALERT = 0.75  # metadata alone should not separate the classes
GAP_ALERT = 0.5  # share of a class differing this much between sources
MIN_SIZE_GROUP = 5  # photos of one pixel size before its class mix means anything


def metadata_features(data: bytes) -> dict:
    with Image.open(io.BytesIO(data)) as im:
        exif = im.getexif()
        width, height = im.size
        fmt = im.format or ''
    camera = ' '.join(str(exif.get(tag, '')).strip() for tag in (271, 272)).strip()
    return {
        'width': width,
        'height': height,
        'aspect': width / max(height, 1),
        'megapixels': width * height / 1e6,
        'log_bytes': math.log(max(len(data), 1)),
        'bytes_per_pixel': len(data) / max(width * height, 1),
        'jpeg': int(fmt == 'JPEG'),
        'png': int(fmt == 'PNG'),
        'exif_tags': len(exif),
        'orientation': exif.get(274, 1) if isinstance(exif.get(274, 1), int) else 1,
        'has_datetime': int(306 in exif),
        'camera': camera,
    }


def colour_features(image) -> list[float]:
    import numpy as np

    pixels = np.asarray(image.convert('RGB').resize((64, 64)), dtype=float)
    parts = [np.histogram(pixels[..., c], bins=8, range=(0, 255))[0] / (64 * 64) for c in range(3)]
    return [*np.concatenate(parts), *pixels.mean(axis=(0, 1)) / 255, *pixels.std(axis=(0, 1)) / 255]


def _metadata_matrix(items: list[dict]):
    import numpy as np

    cameras = sorted({m['camera'] for m in items})
    numeric = [k for k in items[0] if k != 'camera']
    return np.array([[float(m[k]) for k in numeric] + [float(m['camera'] == c) for c in cameras] for m in items])


def _balanced_accuracy(x, y, groups, seed: int) -> float | None:
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import balanced_accuracy_score
    from sklearn.model_selection import StratifiedGroupKFold
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    y = np.asarray(y)
    per_class = [len({g for g, v in zip(groups, y) if v == c}) for c in sorted(set(y))]
    folds = min(5, *per_class) if len(per_class) > 1 else 0
    if folds < 2:
        return None
    predicted = np.empty(len(y), dtype=y.dtype)
    splitter = StratifiedGroupKFold(n_splits=folds, shuffle=True, random_state=seed)
    for train, test in splitter.split(x, y, groups):
        if len(set(y[train])) < 2:
            return None
        model = make_pipeline(StandardScaler(), LogisticRegression(class_weight='balanced', max_iter=2000))
        predicted[test] = model.fit(x[train], y[train]).predict(x[test])
    return float(balanced_accuracy_score(y, predicted))


def separability(x, y, groups) -> dict | None:
    """Out-of-fold balanced accuracy, whole groups held out, against shuffled labels."""
    import numpy as np

    real = [_balanced_accuracy(x, y, groups, seed) for seed in range(REPEATS)]
    if any(v is None for v in real):
        return None
    rng = np.random.default_rng(0)
    chance = []
    for n in range(SHUFFLES):
        score = _balanced_accuracy(x, rng.permutation(np.asarray(y)), groups, n)
        if score is not None:
            chance.append(score)
    return {
        'balanced_accuracy': round(float(np.mean(real)), 3),
        'shuffled_labels': round(float(np.mean(chance)), 3) if chance else None,
        'photos': len(y),
        'groups': len(set(groups)),
    }


def _group(row: dict) -> str:
    """A photo without a known patient counts alone, exactly as the old snapshots did."""
    return row.get('subject_id') or row.get('candidate_group') or row['image_id']


def check(root: Path = ROOT, rows: list[dict] | None = None) -> dict:
    """Run all three checks on `rows` (default: every photo in the manifest)."""
    import numpy as np

    rows = read_manifest(root) if rows is None else rows
    names = sources.load(root)['images']
    origin = {r['image_id']: sources.origin(r, names.get(r['image_id'])) for r in rows}
    table = defaultdict(Counter)
    for r in rows:
        table[origin[r['image_id']]][r['label_state'] if r['status'] == 'approved' else r['status']] += 1
    crosstab = [
        {
            'source': key,
            'name': SOURCE_NAMES.get(key, key),
            'normal': table[key]['negative'],
            'positive': table[key]['positive'],
            'pending': table[key]['pending_review'] + table[key]['unknown'],
            'excluded': table[key]['excluded'],
        }
        for key in sorted(table)
    ]
    labelled = [r for r in rows if r['status'] == 'approved' and r['label_state'] in ('negative', 'positive')]
    meta, colour, kept, unreadable = [], [], [], 0
    for r in labelled:
        try:
            data = inside(r['image_path'], root).read_bytes()
            meta.append(metadata_features(data))
            with Image.open(io.BytesIO(data)) as im:
                colour.append(colour_features(im))
            kept.append(r)
        except (OSError, ValueError, UnidentifiedImageError):
            unreadable += 1
    result = {
        'checked_at': stamp(),
        'photos': len(rows),
        'labelled': len(kept),
        'unreadable': unreadable,
        'crosstab': crosstab,
        'label_from_metadata': None,
        'label_from_colour': None,
        'source_from_metadata': None,
        'source_from_colour': None,
        'sizes': _sizes(kept, meta),
    }
    counts = Counter(r['label_state'] for r in kept)
    if len(counts) == 2 and min(counts.values()) >= MIN_PER_CLASS:
        groups = [_group(r) for r in kept]
        y = [r['label_state'] for r in kept]
        x_meta, x_colour = _metadata_matrix(meta), np.array(colour)
        result['label_from_metadata'] = separability(x_meta, y, groups)
        result['label_from_colour'] = separability(x_colour, y, groups)
        where = [origin[r['image_id']] for r in kept]
        spread = Counter(where)
        if len(spread) > 1 and min(spread.values()) >= MIN_PER_CLASS:
            result['source_from_metadata'] = separability(x_meta, where, groups)
            result['source_from_colour'] = separability(x_colour, where, groups)
    result.update(_verdict(result))
    return result


def _sizes(rows: list[dict], meta: list[dict]) -> list[dict]:
    """Pixel sizes against classes, turned photos counted together: a size only one class has
    means that class was prepared differently (cropped, resized), which a model can pick up."""
    table = defaultdict(Counter)
    for r, m in zip(rows, meta):
        long, short = sorted((m['width'], m['height']), reverse=True)
        table[f'{long}×{short}'][r['label_state']] += 1
    ordered = sorted(table.items(), key=lambda item: -sum(item[1].values()))
    return [{'size': k, 'normal': c['negative'], 'positive': c['positive']} for k, c in ordered]


def _verdict(result: dict) -> dict:
    findings = []
    shares = {}
    for row in result['crosstab']:
        total = row['normal'] + row['positive']
        if total >= MIN_PER_CLASS:
            shares[row['name']] = row['normal'] / total
    if len(shares) < 2:
        findings.append('目前已核准照片只有一個來源，無法比較來源差異。')
    elif max(shares.values()) - min(shares.values()) >= GAP_ALERT:
        detail = '、'.join(f'{k} {v:.0%}' for k, v in shares.items())
        findings.append(f'各來源的正常照片比例差很多（{detail}），模型可能學到來源而不是病灶。')
    metadata = result['label_from_metadata']
    high_metadata = bool(metadata and metadata['balanced_accuracy'] >= METADATA_ALERT)
    if high_metadata:
        findings.append(f'只看檔案資訊就能分開正常與陽性（平衡準確率 {metadata["balanced_accuracy"]:.2f}）。')
    for key, name in (('source_from_metadata', '檔案資訊'), ('source_from_colour', '色彩')):
        value = result[key]
        if value and value['balanced_accuracy'] >= METADATA_ALERT:
            findings.append(f'只看{name}就能認出來源（平衡準確率 {value["balanced_accuracy"]:.2f}）。')
    has_both = sum(s['normal'] for s in result['sizes']) and sum(s['positive'] for s in result['sizes'])
    one_sided = [
        s
        for s in result['sizes']
        if has_both and s['normal'] + s['positive'] >= MIN_SIZE_GROUP and not (s['normal'] and s['positive'])
    ]
    for s in one_sided:
        name, count = ('正常', s['normal']) if s['normal'] else ('陽性', s['positive'])
        findings.append(f'{s["size"]} 的 {count} 張全是{name}，這一類照片的處理方式可能不同（例如裁切）。')
    gap = len(shares) >= 2 and max(shares.values()) - min(shares.values()) >= GAP_ALERT
    if gap or high_metadata:
        level = 'high'
    elif one_sided:
        level = 'watch'
    else:
        level = 'none' if len(shares) >= 2 else 'single_source'
    return {'level': level, 'findings': findings}


def inventory(root: Path = ROOT) -> dict:
    """Patients behind the approved photos.  Patients are numbered, never named."""
    rows = [r for r in read_manifest(root) if r['status'] == 'approved']
    known = [r for r in rows if r['group_verified'] == 'true' and r['subject_id']]
    by = defaultdict(Counter)
    for r in known:
        by[r['subject_id']][tasks.effective(r)['stage'] or 'unknown'] += 1
    ordered = sorted(by.values(), key=lambda c: -sum(c.values()))
    patients = [
        {
            'label': f'病人 {i:02d}',
            'photos': sum(c.values()),
            'normal': c['normal'],
            'stage1': c['stage1'],
            'stage2': c['stage2'],
        }
        for i, c in enumerate(ordered, 1)
    ]
    normal = [p for p in patients if p['normal']]
    warnings = []
    if len(rows) != len(known):
        warnings.append(f'{len(rows) - len(known)} 張已核准照片還沒有病人分組，不能建立快照。')
    if patients and len(normal) < MIN_PATIENTS_PER_CLASS:
        warnings.append(f'正常照片只來自 {len(normal)} 位病人，二分類的正常誤報率信賴區間會很寬，成績只能當流程驗證。')
    return {
        'approved': len(rows),
        'patients': len(patients),
        'unassigned': len(rows) - len(known),
        'normal_photos': sum(p['normal'] for p in patients),
        'normal_patients': len(normal),
        'mixed_patients': sum(1 for p in normal if p['normal'] != p['photos']),
        'rows': patients,
        'warnings': warnings,
    }


def run(root: Path = ROOT) -> dict:
    result = {**check(root), 'digest': rows_digest(read_manifest(root))}
    write_json(root / PATH, result)
    return view(root)


def view(root: Path = ROOT) -> dict:
    path = root / PATH
    saved = read_json(path) if path.exists() else None
    fresh = bool(saved) and saved.get('digest') == rows_digest(read_manifest(root))
    return {'audit': saved, 'fresh': fresh, 'inventory': inventory(root)}
