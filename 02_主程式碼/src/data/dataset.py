from __future__ import annotations

import json
import shutil
from collections import Counter
from pathlib import Path

from PIL import Image, ImageOps
from src.common import (
    ROOT,
    SNAPSHOT_DIR,
    inside,
    read_json,
    read_manifest,
    rows_digest,
    sha256,
    snapshot_versions,
    stamp,
    write_json,
    write_manifest,
)
from src.data import tasks
from src.data.tasks import STAGES, STAGE_TO_BINARY, QUALITY, TASKS, TASK_SCHEME, SCHEMES


def audit(root: Path = ROOT, on_progress=None) -> dict:
    rows = read_manifest(root)
    errors, warnings = [], []
    seen, ids = {}, set()
    for index, r in enumerate(rows):
        if on_progress and index % 25 == 0:
            on_progress(index, len(rows))
        ident = r["image_id"]
        try:
            image = inside(r["image_path"], root)
            if ident in ids:
                raise ValueError("duplicate image_id")
            ids.add(ident)
            if sha256(image) != r["sha256"]:
                raise ValueError("image hash changed")
            if r["sha256"] in seen:
                raise ValueError("duplicate canonical image")
            seen[r["sha256"]] = r["status"]
            if not image.is_relative_to(inside("data/" + r["status"], root)):
                raise ValueError("folder does not match status")
            for problem in tasks.consistency_errors(r):
                raise ValueError(problem)
            effective = tasks.effective(r)
            if tasks.storage_status(effective['cls_state']) != r["status"]:
                raise ValueError("storage status does not match the review state")
            if r["status"] == "approved":
                if r["label_state"] not in {"positive", "negative"}:
                    raise ValueError("approved image has unknown ground truth")
                with Image.open(image) as im:
                    im.verify()
                if r["group_verified"] != "true" or not r["subject_id"]:
                    warnings.append(f"{ident}: subject identity unverified; formal evaluation blocked")
        except (ValueError, OSError, KeyError, TypeError) as exc:
            errors.append(f"{ident}: {exc}")
    if on_progress:
        on_progress(len(rows), len(rows))
    return {
        "images": len(rows),
        "statuses": dict(Counter(r["status"] for r in rows)),
        "approved_labels": dict(Counter(r["label_state"] for r in rows if r["status"] == "approved")),
        "errors": errors,
        "warnings": warnings,
    }


def _check_review_labels(label, stage, quality):
    if label not in ('positive', 'negative', 'unknown'):
        raise ValueError('Invalid binary label')
    if stage is not None:
        if stage not in STAGES:
            raise ValueError('Invalid stage label')
        if stage in STAGE_TO_BINARY and STAGE_TO_BINARY[stage] != label:
            raise ValueError('分期與二分類標籤不一致：第一期、第二期與陽性未分期必須為陽性，正常必須為陰性')
    if quality is not None and quality not in QUALITY:
        raise ValueError('Invalid quality state')


def plan_status(row: dict, *, decision: str | None, status: str | None, category: str = '') -> dict:
    """Review state, derived storage status and destination folder for one review."""
    decision = decision or {'approved': 'approve', 'excluded': 'exclude', 'pending_review': 'needs_changes'}.get(status)
    if decision not in tasks.DECISION_STATE:
        raise ValueError('Invalid review decision')
    cls = tasks.DECISION_STATE[decision]
    new_status = tasks.storage_status(cls)
    categories = {
        "excluded": {"unclear", "blurry", "unreadable", "other"},
        "pending_review": {"annotation", "unknown_source", "duplicate_variant"},
    }
    if category and (new_status == "approved" or category not in categories[new_status]):
        raise ValueError("Category does not match the review status")
    if new_status == 'approved':
        base = 'approved'
    elif new_status == row.get('status') and not category:
        # Same storage status: keep the current sub-folder instead of reshuffling files.
        base = Path(row['image_path']).parent.parent.relative_to(Path('data')).as_posix()
    else:
        base = f"{new_status}/" + (category or ("other" if new_status == "excluded" else "annotation"))
    return {'decision': decision, 'cls': cls, 'status': new_status, 'base': base}


def move_with_annotations(row: dict, base: str, root: Path) -> dict:
    """Move a photo and its kept annotation files to another storage folder, all or nothing."""
    src = inside(row["image_path"], root)
    dst = inside(f"data/{base}/images/{src.name}", root)
    moves = []
    if dst != src:
        moves.append((src, dst))
        old_ann_dir = src.parent.parent / "annotations"
        new_ann_dir = dst.parent.parent / "annotations"
        if old_ann_dir.exists():
            moves.extend(
                (p, inside(new_ann_dir / p.name, root)) for p in old_ann_dir.glob(row['image_id'] + "*") if p.is_file()
            )
    # Preflight every destination before changing the dataset.
    if any(target.exists() for _, target in moves):
        raise ValueError("Destination already exists; no files moved")
    completed = []
    try:
        for source_path, target in moves:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source_path), str(target))
            completed.append((source_path, target))
    except OSError:
        for source_path, target in reversed(completed):
            shutil.move(str(target), str(source_path))
        raise
    moved = {s.resolve(): t for s, t in completed}

    def relocated(value):
        if not value:
            return ''
        p = inside(value, root)
        return moved.get(p.resolve(), p).relative_to(root.resolve()).as_posix()

    return {'image_path': dst.relative_to(root).as_posix(), 'annotation_path': relocated(row.get('annotation_path'))}


def _review(
    image_id: str,
    *,
    label: str | None = None,
    reviewer: str,
    reason: str,
    status: str | None = None,
    subject_id: str = "",
    category: str = "",
    clear_subject: bool = False,
    decision=None,
    stage=None,
    quality=None,
    source: str = 'self_declared_operator',
    root: Path = ROOT,
) -> dict:
    """Apply one classification review: binary, stage, quality and cls_review."""
    rows = read_manifest(root)
    r = next((r for r in rows if r["image_id"] == image_id), None)
    if r is None or not reviewer.strip() or not reason.strip():
        raise ValueError("Existing image_id, reviewer and reason are required")
    if label is None:
        raise ValueError('Binary label is required')
    if status is not None and status not in {"approved", "pending_review", "excluded"}:
        raise ValueError("Invalid status")
    _check_review_labels(label, stage, quality)
    plan = plan_status(r, decision=decision, status=status, category=category)
    decision, status = plan['decision'], plan['status']
    if plan['cls'] == 'confirmed' and label not in ('positive', 'negative'):
        raise ValueError("Confirm positive or negative before approval")
    old = dict(r)
    if plan['cls'] == 'confirmed':
        with Image.open(inside(r["image_path"], root)) as im:
            im.verify()
    paths = move_with_annotations(r, plan['base'], root)
    updates = dict(
        status=status,
        cls_review=plan['cls'],
        reason=reason,
        reviewer=reviewer,
        updated_at=stamp(),
        label_state=label,
        **paths,
    )
    if stage is not None:
        updates['stage_label'] = '' if stage == 'unknown' else stage
        updates['label_scheme'] = 'stage_v1' if stage != 'unknown' else ''
    elif r.get('stage_label') and STAGE_TO_BINARY.get(r['stage_label']) != label:
        updates['stage_label'] = ''
        updates['label_scheme'] = ''
    if quality is not None:
        updates['quality_state'] = quality
    r.update(updates)
    if subject_id:
        r.update(subject_id=subject_id, group_verified="true")
    elif clear_subject:
        r.update(subject_id='', group_verified='false')
    for problem in tasks.consistency_errors(r):
        raise ValueError(problem)
    from src.data import evidence

    rule = source == 'authorized_filename_rule'
    evidence.append(
        image_id,
        {
            'task': 'classification',
            'source': source if rule else 'human_review',
            'method': 'rule_applied' if rule else 'review',
            'actor': reviewer,
            'decision': decision,
            'binary': label,
            'stage': r.get('stage_label') or None,
            'reason': reason,
        },
        root,
    )
    write_manifest(rows, root)
    write_json(
        root / f"data/reviews/{stamp()}_{image_id}.json",
        {
            "schema_version": 5,
            "task": 'classification',
            "area": 'cls',
            "before": old,
            "after": r,
            "decision": decision,
            "source": source,
        },
    )
    return r


def _eligible_rows(root: Path, task: str) -> list[dict]:
    from src.workbench.views import data_rows

    return [r for r in data_rows(root) if r['tasks'][task]['eligible']]


def leakage(rows: list[dict], groups: list[str], splits: list, root: Path) -> list[str]:
    """Reasons a train/validation split would leak: the same patient on both sides, or the same
    or nearly the same picture of two different patients on both sides."""
    from src.imports.external import NEAR_DISTANCE, _distance, project_fingerprints

    prints = project_fingerprints(root, rows)
    problems: list[str] = []
    for fold, (train, val) in enumerate(splits):
        train, val = [int(i) for i in train], [int(i) for i in val]
        if {groups[i] for i in train} & {groups[i] for i in val}:
            problems.append(f'第 {fold} 折：同一位病人同時在訓練與驗證')
        pairs = 0
        for i in train:
            a = prints.get(rows[i]['sha256']) or {}
            for j in val:
                b = prints.get(rows[j]['sha256']) or {}
                if rows[i]['sha256'] == rows[j]['sha256'] or (
                    a.get('pixel_sha256') and a.get('pixel_sha256') == b.get('pixel_sha256')
                ):
                    pairs += 1
                elif a.get('dhash') and b.get('dhash') and _distance(a['dhash'], b['dhash']) <= NEAR_DISTANCE:
                    pairs += 1
        if pairs:
            problems.append(f'第 {fold} 折：{pairs} 組相同或近似照片同時在訓練與驗證，請先到資料審查處理重複')
    return problems


def _partitions(labels, groups, folds, repeats, seed, classes) -> tuple[list, list[int]]:
    """Up to `repeats` different whole-patient partitions.  One that leaves a class (normal
    patients included) out of any fold is thrown away and the next seed is tried."""
    import numpy as np
    from sklearn.model_selection import StratifiedGroupKFold

    found, seeds, seen = [], [], set()
    for attempt in range(50 * repeats):
        if len(found) == repeats:
            break
        splitter = StratifiedGroupKFold(n_splits=folds, shuffle=True, random_state=seed + attempt)
        parts = list(splitter.split(np.zeros(len(labels)), labels, groups))
        if any(len({labels[i] for i in side}) != classes for part in parts for side in part):
            continue
        key = frozenset(frozenset(groups[i] for i in val) for _, val in parts)
        if key not in seen:
            seen.add(key)
            found.append(parts)
            seeds.append(seed + attempt)
    return found, seeds


def _build(
    *,
    demo: bool = False,
    root: Path = ROOT,
    folds: int = 3,
    seed: int = 42,
    task: str = 'binary_classification',
    name: str | None = None,
    repeats: int = 1,
) -> dict:
    import numpy as np
    import yaml
    from sklearn.model_selection import StratifiedGroupKFold
    from src.data import revocations

    if task not in TASKS:
        raise ValueError('Unknown training task')
    scheme = TASK_SCHEME[task]
    report = audit(root)
    if report["errors"]:
        raise ValueError("Dataset audit failed: " + "; ".join(report["errors"]))
    eligible = _eligible_rows(root, task)
    unverified = [r for r in eligible if r['group_verified'] != 'true' or not r['subject_id']]
    if unverified:
        raise ValueError(f'{len(unverified)} 張照片還沒有病人分組，不能建立快照。同一位病人一定要在同一折。')
    from src.data import prospective

    held_back = prospective.reserved(root)
    eligible = [r for r in eligible if tasks.group_key(r) not in held_back]
    review_revisions = {r['image_id']: r['review']['revision'] if r['review'] else None for r in eligible}
    ids = {r['image_id'] for r in eligible}
    rows = [r for r in read_manifest(root) if r['image_id'] in ids]
    groups = [tasks.group_key(r) for r in rows]
    targets = [tasks.target(r, task) for r in rows]
    class_names = SCHEMES[scheme]['classes']
    labels = [class_names.index(t) for t in targets]
    counts = Counter(labels)
    missing = [class_names[i] for i in range(len(class_names)) if counts.get(i, 0) < folds]
    if len(set(groups)) < folds or missing:
        detail = '、'.join(f"{name}={counts.get(i,0)}" for i, name in enumerate(class_names))
        raise ValueError(
            f"資料不足以建立 {folds} 折：每一類至少需要 {folds} 張且至少 {folds} 個分組。目前可用：{detail}；分組 {len(set(groups))} 個。不會複製樣本或偽造分組。"
        )
    normal_patients = len({g for g, label in zip(groups, labels) if label == 0})
    if normal_patients < folds:
        raise ValueError(f'正常照片只來自 {normal_patients} 位病人，不足以讓 {folds} 折都有正常病人。')
    partitions, split_seeds = _partitions(labels, groups, folds, repeats, seed, len(class_names))
    if not partitions:
        raise ValueError(f"無法讓每一折的訓練與驗證都包含全部 {len(class_names)} 類；需要更多已審查的分組。")
    splits = [fold for partition in partitions for fold in partition]
    problems = leakage(rows, groups, splits, root)
    if problems:
        raise ValueError('快照未建立，訓練與驗證之間有資料洩漏：' + '；'.join(problems))
    prefix = {'binary_classification': 'binary_', 'stage_classification': 'stage_'}[task]
    version = ("demo_" if demo else "verified_") + prefix + stamp()
    final = inside(f"{SNAPSHOT_DIR}/{version}", root)
    building = inside(f"{SNAPSHOT_DIR}/.building-{version}", root)
    building.parent.mkdir(parents=True, exist_ok=True)
    manifest_digest = rows_digest(read_manifest(root))
    mapping = {name: i for i, name in enumerate(SCHEMES[scheme]['classes'])}
    info = {
        "version": version,
        "task": task,
        "label_scheme": scheme,
        "class_mapping": mapping,
        "demo_only": demo,
        "patient_identity_verified": True,
        "seed": seed,
        "repeats": len(partitions),
        "repeats_requested": repeats,
        "folds_per_repeat": folds,
        "split_seeds": split_seeds,
        "schema_version": 3,
        "manifest_digest": manifest_digest,
        "folds": [],
        "created_at": stamp(),
        "note": "Cross-validation folds, not an independent clinical test set.",
    }
    if name:
        info["name"] = name  # display label only; the version stays the immutable ID
    from src.data import evidence

    def normalized(image, target):
        with Image.open(image) as im:
            orientation = im.getexif().get(274, 1)
            ImageOps.exif_transpose(im).convert("RGB").save(target, format="JPEG", quality=95)
        return orientation

    try:
        # One normalized copy per snapshot; folds only list members.
        shared = {}
        (building / 'images').mkdir(parents=True, exist_ok=True)
        for r in rows:
            target = building / 'images' / f"{r['image_id']}.jpg"
            normalized(inside(r['image_path'], root), target)
            shared[r['image_id']] = {
                'image_path': f"{SNAPSHOT_DIR}/{version}/images/{r['image_id']}.jpg",
                'dataset_sha256': sha256(target),
            }
        for fold, (train, val) in enumerate(splits):
            target_dir = building / f"fold{fold}"
            members = {}
            for split, indices in [("train", train), ("val", val)]:
                members[split] = []
                for i in indices:
                    r = rows[int(i)]
                    ev = evidence.path(r['image_id'], root)
                    member = {
                        "review_revision": review_revisions[r["image_id"]],
                        "image_id": r["image_id"],
                        "sha256": r["sha256"],
                        "normalization": "exif_transpose_rgb_jpeg95",
                        "group": groups[int(i)],
                        "label_state": r["label_state"],
                        "stage_label": tasks.effective(r)['stage'],
                        "target": targets[int(i)],
                        "label_evidence_sha256": sha256(ev) if ev.exists() else None,
                    }
                    member.update(shared[r['image_id']])
                    members[split].append(member)
            target_dir.mkdir(parents=True, exist_ok=True)
            dataset = {
                "path": str(final / f"fold{fold}"),
                "task": task,
                "label_scheme": scheme,
                "names": {i: n for n, i in mapping.items()},
            }
            (target_dir / "dataset.yaml").write_text(yaml.safe_dump(dataset, allow_unicode=True), encoding="utf-8")
            fold_info = {
                "schema_version": 3,
                "fold": fold,
                "repeat": fold // folds,
                "fold_in_repeat": fold % folds,
                "task": task,
                "label_scheme": scheme,
                "class_mapping": mapping,
                "dataset": f"{SNAPSHOT_DIR}/{version}/fold{fold}/dataset.yaml",
                "members": members,
                "demo_only": demo,
                "manifest_digest": manifest_digest,
            }
            write_json(target_dir / "split.json", fold_info)
            fold_info["split_sha256"] = sha256(target_dir / "split.json")
            info["folds"].append(fold_info)
        write_json(building / "dataset_version.json", info)
        # A withdrawal that landed while copying wins: nothing is published.
        table = revocations.revoked(root)
        if any(revocations.is_revoked(r, table) for r in rows):
            raise ValueError('建立期間有資料被停止使用，快照未發布；請重新建立。')
        building.rename(final)
    except BaseException:
        if building.exists():
            shutil.rmtree(building)
        raise
    write_json(root / SNAPSHOT_DIR / f"latest_{task}.json", {"version": version})
    return info


def snapshot_task(split: dict) -> str | None:
    """Task of a fold; None for schema-2 snapshots, which no current model can use."""
    return split.get('task') if split.get('schema_version', 2) >= 3 else None


def _require_active_snapshot(version: str, root: Path) -> None:
    """A snapshot moved to the workbench trash (or purged) is never used again.
    Only checked for the workbench's own project root (isolated data tests use other roots)."""
    try:
        from src.workbench import registry, resources
    except ImportError:
        return
    if Path(root).resolve() != Path(registry.ROOT).resolve():
        return
    state = resources.record('snapshot', version)['state']
    if state != 'active':
        raise ValueError('此資料快照位於垃圾桶或已永久刪除，不能再使用')


def validate_split(dataset: Path, root: Path = ROOT) -> dict:
    import yaml
    from src.data import revocations

    dataset = inside(dataset, root)
    split = read_json(dataset.parent / "split.json")
    version = read_json(dataset.parent.parent / "dataset_version.json")
    state_path = root / 'data/snapshot_states.json'
    states = read_json(state_path) if state_path.exists() else {}
    if dataset.parent.parent.name in states:
        raise ValueError('Snapshot withdrawn or superseded: ' + states[dataset.parent.parent.name]['reason'])
    _require_active_snapshot(dataset.parent.parent.name, root)
    sealed = next((f for f in version["folds"] if f["fold"] == split["fold"]), None)
    if sealed is None:
        raise ValueError("Unlisted fold")
    if {k: v for k, v in sealed.items() if k != 'split_sha256'} != split:
        raise ValueError('Snapshot member metadata does not match the version manifest')
    if sealed.get("split_sha256") and sealed["split_sha256"] != sha256(dataset.parent / "split.json"):
        raise ValueError("Snapshot split integrity failure")
    if version.get("withdrawn"):
        raise ValueError("Snapshot has been withdrawn")
    task = snapshot_task(split)
    if task not in TASKS:
        raise ValueError('這是已移除模型使用的舊快照，不能再使用')
    cfg = yaml.safe_load(dataset.read_text(encoding="utf-8"))
    scheme = split['label_scheme']
    if task != SCHEMES[scheme]['task'] or split.get('class_mapping') != tasks.mapping(scheme):
        raise ValueError('Snapshot label scheme does not match its task')
    expected = {
        "path": str(dataset.parent.resolve()),
        "task": task,
        "label_scheme": scheme,
        "names": {i: n for n, i in tasks.mapping(scheme).items()},
    }
    if cfg != expected:
        raise ValueError("Dataset YAML changed or points outside its version")
    table = revocations.revoked(root)
    seen, split_groups = set(), {}
    for name in ["train", "val"]:
        split_groups[name] = set()
        for m in split["members"][name]:
            ident = m["image_id"]
            if ident in seen:
                raise ValueError("Duplicate or unapproved image in split")
            tasks.member_class(m, split['label_scheme'])
            if revocations.is_revoked(m, table):
                raise ValueError('Snapshot contains data whose use was withdrawn')
            seen.add(ident)
            p = inside(m["image_path"], root)
            if not p.is_relative_to(dataset.parent.parent / "images") or sha256(p) != m["dataset_sha256"]:
                raise ValueError("Dataset image or label has changed")
            split_groups[name].add(m["group"])
    listed = {
        inside(m['image_path'], root).resolve() for f in version['folds'] for ms in f['members'].values() for m in ms
    }
    if {p.resolve() for p in (dataset.parent.parent / 'images').iterdir() if p.is_file()} != listed:
        raise ValueError("Unlisted image detected in generated dataset")
    if split_groups["train"] & split_groups["val"]:
        raise ValueError("Cross-split group leakage")
    return split


def build(*, demo=False, root=ROOT, folds=3, seed=42, task='binary_classification', name=None, repeats=1):
    from src.workbench.storage import dataset_lock

    if not 2 <= folds <= 10:
        raise ValueError("Fold count must be 2..10")
    if not 1 <= repeats <= 10:
        raise ValueError("Repeat count must be 1..10")
    with dataset_lock(root):
        recover_reviews(root)
        return _build(demo=demo, root=root, folds=folds, seed=seed, task=task, name=name, repeats=repeats)


def recover_reviews(root=ROOT):
    """Restore a transaction's before-images after a crash, before accepting writes."""
    for journal in (root / "runtime/review_transactions").glob("*/journal.json"):
        tx = read_json(journal)
        if tx["state"] != "pending":
            continue
        for item in tx["files"]:
            path = inside(item["path"], root)
            if item["backup"]:
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(journal.parent / item["backup"], path)
            else:
                path.unlink(missing_ok=True)
        for log in (root / "data/reviews").glob("*.json"):
            if log.name not in tx["logs_before"]:
                log.unlink()
        tx["state"] = "rolled_back"
        write_json(journal, tx)
        for backup in journal.parent.glob('*.bak'):
            backup.unlink()


SUBSTANTIVE = (
    'status',
    'label_state',
    'subject_id',
    'group_verified',
    'stage_label',
    'usage_state',
    'quality_state',
    'cls_review',
)


def review(image_id, *, revision=None, root=ROOT, **kwargs):
    from src.workbench.storage import dataset_lock

    with dataset_lock(root):
        recover_reviews(root)
        rows = read_manifest(root)
        row = next((r for r in rows if r["image_id"] == image_id), None)
        if row is None:
            raise ValueError("Unknown image")
        if revision is not None and tasks.row_revision(row) != revision:
            raise ValueError("revision conflict: reload before saving")
        src = inside(row["image_path"], root)
        base = plan_status(
            row,
            decision=kwargs.get('decision'),
            status=kwargs.get('status'),
            category=kwargs.get('category', ''),
        )['base']
        dst = inside(f"data/{base}/images/{src.name}", root)
        from src.data import evidence

        paths = {
            root / "data/manifest.csv",
            src,
            dst,
            root / 'data/snapshot_states.json',
            evidence.path(image_id, root),
        }
        for p in (src.parent.parent / "annotations").glob(image_id + "*"):
            paths.add(p)
            paths.add(dst.parent.parent / "annotations" / p.name)
        import uuid

        folder = root / "runtime/review_transactions" / (stamp() + "-" + uuid.uuid4().hex[:8])
        folder.mkdir(parents=True)
        tx = {
            "state": "pending",
            "image_id": image_id,
            "logs_before": [p.name for p in (root / "data/reviews").glob("*.json")],
            "files": [],
        }
        for i, path in enumerate(sorted(paths)):
            backup = f"{i}.bak" if path.exists() else None
            if backup:
                shutil.copy2(path, folder / backup)
            tx["files"].append({"path": path.relative_to(root).as_posix(), "backup": backup})
        write_json(folder / "journal.json", tx)
        try:
            result = _review(image_id, root=root, **kwargs)
            if any((row.get(k) or '') != (result.get(k) or '') for k in SUBSTANTIVE):
                state_path = root / 'data/snapshot_states.json'
                states = read_json(state_path) if state_path.exists() else {}
                for version in snapshot_versions(root):
                    info = read_json(version)
                    if any(
                        m['image_id'] == image_id
                        for f in info['folds']
                        for members in f['members'].values()
                        for m in members
                    ):
                        states[version.parent.name] = {
                            'reason': 'Human review changed labels, eligibility or grouping',
                            'image_id': image_id,
                            'at': stamp(),
                            'status': 'superseded',
                        }
                write_json(state_path, states)
            tx["state"] = "committed"
            write_json(folder / "journal.json", tx)
            # Backups are transient recovery data, not a second research archive.
            for p in folder.glob("*.bak"):
                p.unlink()
            return result
        except BaseException:
            recover_reviews(root)
            raise
