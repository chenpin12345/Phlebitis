"""Fixed independent test set chosen inside a snapshot (B5, 2026-10-17).

When "執行獨立測試集" is ticked in 建立實驗, about RATIO of the snapshot's photos are kept out
of training and cross-validation and evaluated once after training.  The chosen photos are whole
case groups (never split across train/test), stratified by class and picked in a fixed hash
order, so the same groups stay in the test set for every experiment and every later snapshot.

Two new snapshots are written next to the source; the source snapshot is never modified:
  <kind>_<task>holdout_<stamp>  training folds without the test groups (purpose holdout_training)
  <kind>_<task>testset_<stamp>  one split whose 'val' members are the test photos (purpose independent_test)
The pair is reused for the same source snapshot (data/snapshots/holdout_index.json).
"""

from __future__ import annotations

import hashlib
import shutil
from collections import Counter, defaultdict
from pathlib import Path

from src.common import ROOT, SNAPSHOT_DIR, inside, read_json, sha256, snapshot_folder, stamp, write_json

RATIO = 0.2
SALT = 'phlebitis-independent-test-v1'
INDEX = SNAPSHOT_DIR + '/holdout_index.json'
PREFIX = {'binary_classification': 'binary_', 'stage_classification': 'stage_'}
CLASS_NAMES = {
    'positive': '陽性',
    'negative': '正常',
    'normal': '正常',
    'stage1': '第一期',
    'stage2': '第二期',
}


def _rank(group: str) -> str:
    return hashlib.sha256((SALT + group).encode('utf-8')).hexdigest()


def choose(members: list[dict], ratio: float = RATIO) -> set[str]:
    """Whole groups per class, in fixed hash order, until about `ratio` of that class's photos."""
    by_group: dict[str, list[dict]] = defaultdict(list)
    for m in members:
        by_group[m['group']].append(m)
    per_class = Counter(m['target'] for m in members)
    chosen: set[str] = set()
    # Rarest class first, so its few groups are not used up by the larger classes.
    for cls in sorted(per_class, key=lambda c: (per_class[c], c)):
        need = max(1, round(per_class[cls] * ratio))
        taken = sum(1 for m in members if m['group'] in chosen and m['target'] == cls)
        for g in sorted((g for g in by_group if any(x['target'] == cls for x in by_group[g])), key=_rank):
            if taken >= need:
                break
            if g not in chosen:
                chosen.add(g)
                taken += sum(1 for x in by_group[g] if x['target'] == cls)
    return chosen


def _counts(members: list[dict]) -> str:
    c = Counter(m['target'] for m in members)
    return '、'.join(f'{CLASS_NAMES.get(k, k)} {v}' for k, v in sorted(c.items()))


def _usable(pair: dict, root: Path) -> bool:
    from src.data.dataset import validate_split

    try:
        for dataset in [*pair['folds'], pair['test_dataset']]:
            validate_split(inside(dataset, root), root)
        return True
    except Exception:
        return False


def source_of(dataset: str, root: Path = ROOT) -> dict:
    """Snapshot info of a fold dataset path."""
    return read_json(inside(dataset, root).parent.parent / 'dataset_version.json')


def derive(dataset: str, root: Path = ROOT) -> dict:
    """Training folds without the fixed test set, plus the test set, for the snapshot of `dataset`."""
    from src.data.dataset import validate_split
    from src.workbench.storage import dataset_lock

    validate_split(inside(dataset, root), root)  # active, not superseded or withdrawn, intact
    info = source_of(dataset, root)
    if info.get('purpose'):
        raise ValueError('這個快照已是獨立測試集的衍生快照；請選原本的資料快照。')
    if info.get('schema_version', 2) < 3 or not info.get('task'):
        raise ValueError('舊版快照不支援獨立測試集；請先到「新增快照」重新建立。')
    with dataset_lock(root):
        index_path = root / INDEX
        index = read_json(index_path) if index_path.exists() else {}
        known = index.get(info['version'])
        if known and _usable(known, root):
            return known
        pair = _build(info, root)
        index[info['version']] = pair
        write_json(index_path, index)
    return pair


def _build(info: dict, root: Path) -> dict:
    import numpy as np
    from sklearn.model_selection import StratifiedGroupKFold
    from src.data import revocations
    from src.data.dataset import validate_split

    task = info['task']
    folds = info.get('folds_per_repeat') or len(info['folds'])
    first = info['folds'][0]['members']
    members = first['train'] + first['val']
    if len({m['image_id'] for m in members}) != len(members):
        raise ValueError('快照成員重複，無法保留獨立測試集')
    table = revocations.revoked(root)
    if any(revocations.is_revoked(m, table) for m in members):
        raise ValueError('快照含已停止使用的資料；請重新建立快照。')
    classes = sorted({m['target'] for m in members})
    chosen = choose(members)
    test = [m for m in members if m['group'] in chosen]
    rest = [m for m in members if m['group'] not in chosen]
    counts = Counter(m['target'] for m in rest)
    if (
        {m['target'] for m in test} != set(classes)
        or len({m['group'] for m in rest}) < folds
        or any(counts[c] < folds for c in classes)
    ):
        raise ValueError(
            f'資料不足以保留獨立測試集：保留約 {RATIO:.0%} 照片（{_counts(test)}）後，剩下 {_counts(rest)}；'
            f'{folds} 折訓練每一類至少需要 {folds} 張。請增加照片或取消勾選「執行獨立測試集」。'
        )
    labels = [classes.index(m['target']) for m in rest]
    groups = [m['group'] for m in rest]
    splits = list(
        StratifiedGroupKFold(n_splits=folds, shuffle=True, random_state=info.get('seed', 42)).split(
            np.zeros(len(rest)), labels, groups
        )
    )
    for train, val in splits:
        if {labels[i] for i in train} != set(range(len(classes))) or {labels[i] for i in val} != set(
            range(len(classes))
        ):
            raise ValueError(
                f'保留獨立測試集後，無法讓每一折的訓練與驗證都包含全部 {len(classes)} 類；請增加照片或取消勾選「執行獨立測試集」。'
            )
    kind = 'demo' if info.get('demo_only') else 'verified'
    when = stamp()
    training_version = f"{kind}_{PREFIX[task]}holdout_{when}"
    test_version = f"{kind}_{PREFIX[task]}testset_{when}"
    label = info.get('name') or info['version']
    note = {
        'source': info['version'],
        'ratio': RATIO,
        'test_images': len(test),
        'test_groups': len(chosen),
        'test_classes': dict(Counter(m['target'] for m in test)),
        'rule': 'whole groups per class in fixed hash order (' + SALT + ')',
    }
    common = {
        k: info[k]
        for k in (
            'task',
            'label_scheme',
            'class_mapping',
            'demo_only',
            'patient_identity_verified',
            'seed',
            'manifest_digest',
        )
        if k in info
    }
    written = []
    try:
        _write(
            root,
            training_version,
            [{'train': [rest[int(i)] for i in t], 'val': [rest[int(i)] for i in v]} for t, v in splits],
            {
                **common,
                'name': (label + '・保留獨立測試集')[:60],
                'purpose': 'holdout_training',
                'derived_from': info['version'],
                'holdout': {**note, 'test_snapshot': test_version},
                'note': 'Cross-validation folds without the fixed independent test set.',
            },
            None,
        )
        written.append(training_version)
        _write(
            root,
            test_version,
            [{'train': [], 'val': test}],
            {
                **common,
                'name': (label + '・獨立測試集')[:60],
                'purpose': 'independent_test',
                'derived_from': info['version'],
                'holdout': {**note, 'training_snapshot': training_version},
                'note': 'Fixed independent test set; never used for training or model selection.',
            },
            'independent_test',
        )
        written.append(test_version)
        pair = {
            'source': info['version'],
            'training': training_version,
            'test': test_version,
            'created_at': when,
            'folds': [f'{SNAPSHOT_DIR}/{training_version}/fold{k}/dataset.yaml' for k in range(folds)],
            'test_dataset': f'{SNAPSHOT_DIR}/{test_version}/fold0/dataset.yaml',
            'test_images': len(test),
            'ratio': RATIO,
        }
        for dataset in [*pair['folds'], pair['test_dataset']]:
            validate_split(inside(dataset, root), root)
        return pair
    except BaseException:
        for version in written:
            shutil.rmtree(snapshot_folder(version, root), ignore_errors=True)
        raise


def _write(root: Path, version: str, folds: list[dict], info: dict, purpose: str | None) -> None:
    import yaml

    task = info['task']
    final = inside(f'{SNAPSHOT_DIR}/{version}', root)
    building = inside(f'{SNAPSHOT_DIR}/.building-{version}', root)
    building.parent.mkdir(parents=True, exist_ok=True)
    out = {**info, 'version': version, 'schema_version': 3, 'created_at': stamp(), 'folds': [], 'repeats': 1}
    try:
        (building / 'images').mkdir(parents=True, exist_ok=True)
        for m in {m['image_id']: m for f in folds for ms in f.values() for m in ms}.values():
            shutil.copy2(inside(m['image_path'], root), building / 'images' / f"{m['image_id']}.jpg")
        for k, split in enumerate(folds):
            target = building / f'fold{k}'
            members = {}
            for name in ('train', 'val'):
                members[name] = []
                for m in split[name]:
                    m = dict(m)
                    m['image_path'] = f"{SNAPSHOT_DIR}/{version}/images/{m['image_id']}.jpg"
                    members[name].append(m)
            target.mkdir(parents=True, exist_ok=True)
            spec = {
                'path': str(final / f'fold{k}'),
                'task': task,
                'label_scheme': info['label_scheme'],
                'names': {i: n for n, i in info['class_mapping'].items()},
            }
            (target / 'dataset.yaml').write_text(yaml.safe_dump(spec, allow_unicode=True), encoding='utf-8')
            fold = {
                'schema_version': 3,
                'fold': k,
                'task': task,
                'label_scheme': info['label_scheme'],
                'class_mapping': info['class_mapping'],
                'dataset': f'{SNAPSHOT_DIR}/{version}/fold{k}/dataset.yaml',
                'members': members,
                'demo_only': info.get('demo_only', False),
                'manifest_digest': info.get('manifest_digest'),
            }
            if purpose:
                fold['purpose'] = purpose
            write_json(target / 'split.json', fold)
            fold['split_sha256'] = sha256(target / 'split.json')
            out['folds'].append(fold)
        write_json(building / 'dataset_version.json', out)
        building.rename(final)
    except BaseException:
        if building.exists():
            shutil.rmtree(building)
        raise
