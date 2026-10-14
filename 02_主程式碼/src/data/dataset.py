from __future__ import annotations

import json
import shutil
from collections import Counter
from pathlib import Path

from PIL import Image, ImageOps
from src.common import ROOT, inside, read_json, read_manifest, rows_digest, sha256, stamp, write_json, write_manifest
from src.data.labels import from_labelme, text, validate, orient_boxes
from src.data import tasks
from src.data.tasks import STAGES, STAGE_TO_BINARY, DETECTION_STATES, QUALITY, TASKS, TASK_SCHEME, SCHEMES


def _yolo_boxes(path: Path) -> list[list[float]]:
    return [list(map(float, line.split())) for line in path.read_text().splitlines() if line.strip()]


def audit(root: Path = ROOT, on_progress=None) -> dict:
    rows = read_manifest(root)
    errors, warnings = [], []
    seen, ids = {}, set()
    for index,r in enumerate(rows):
        if on_progress and index%25==0:on_progress(index,len(rows))
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
            if tasks.storage_status(effective['cls_state'], effective['det_state']) != r["status"]:
                raise ValueError("storage status does not match the two area review states")
            if r["status"] == "approved":
                # Each area is checked only for what it confirmed; the areas are independent.
                if effective['cls_state'] == 'confirmed' and r["label_state"] not in {"positive", "negative"}:
                    raise ValueError("approved image has unknown ground truth")
                with Image.open(image) as im:
                    im.verify()
                if effective['det_state'] == 'confirmed' and effective['detection'] in ('boxes', 'no_target'):
                    if not r.get("yolo_path"):
                        raise ValueError("detection labels missing")
                    boxes = _yolo_boxes(inside(r["yolo_path"], root))
                    validate(boxes)
                    if bool(boxes) != (effective['detection'] == 'boxes'):
                        raise ValueError("labels do not match positive/negative status")
                    if r["annotation_path"]:
                        with Image.open(image) as im:
                            size = im.size
                        converted = from_labelme(read_json(inside(r["annotation_path"], root)), size)
                        if len(converted) != len(boxes) or any(any(abs(a-b)>2e-7 for a,b in zip(x,y)) for x,y in zip(converted, boxes)):
                            raise ValueError("JSON and YOLO annotation differ")
                if r["group_verified"] != "true" or not r["subject_id"]:
                    warnings.append(f"{ident}: subject identity unverified; formal evaluation blocked")
        except (ValueError, OSError, KeyError, TypeError) as exc:
            errors.append(f"{ident}: {exc}")
    if on_progress:on_progress(len(rows),len(rows))
    return {"images": len(rows), "statuses": dict(Counter(r["status"] for r in rows)), "approved_labels": dict(Counter(r["label_state"] for r in rows if r["status"]=="approved")), "errors": errors, "warnings": warnings}


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


def plan_status(row: dict, *, task: str, decision: str | None, status: str | None, category: str = '') -> dict:
    """Area states, derived storage status and destination folder for one review.

    Area reviews (classification / detection) change only their own area; the other
    area's current state is written explicitly so it never shifts because status moved.
    The legacy single form sets both areas from one status, as before.
    """
    from src.workbench.views import DECISIONS
    if task == 'legacy':
        decision = decision or {'approved': 'approve', 'excluded': 'exclude', 'pending_review': 'needs_changes'}.get(status)
        if DECISIONS.get(decision) != status:
            raise ValueError('審查決定與資料狀態不一致')
        state = tasks.DECISION_STATE[decision]
        cls = det = state
    elif task in ('classification', 'detection'):
        decision = decision or {'approved': 'approve', 'excluded': 'exclude', 'pending_review': 'needs_changes'}.get(status)
        if decision not in tasks.DECISION_STATE:
            raise ValueError('Invalid review decision')
        state = tasks.DECISION_STATE[decision]
        cls = state if task == 'classification' else tasks.area_state(row, 'cls')
        det = state if task == 'detection' else tasks.area_state(row, 'det')
    else:
        raise ValueError('Invalid review task')
    new_status = tasks.storage_status(cls, det)
    categories = {"excluded": {"unclear", "blurry", "unreadable", "other"},
                  "pending_review": {"annotation", "unknown_source", "duplicate_variant"}}
    if category and (new_status == "approved" or category not in categories[new_status]):
        raise ValueError("Category does not match the review status")
    if new_status == 'approved':
        base = 'approved'
    elif task != 'legacy' and new_status == row.get('status') and not category:
        # Same storage status: keep the current sub-folder instead of reshuffling files.
        base = Path(row['image_path']).parent.parent.relative_to(Path('data')).as_posix()
    else:
        base = f"{new_status}/" + (category or ("other" if new_status == "excluded" else "annotation"))
    return {'decision': decision, 'cls': cls, 'det': det, 'status': new_status, 'base': base}


def _review(image_id: str, *, label: str | None = None, reviewer: str, reason: str, status: str | None = None, subject_id: str = "", annotation: str = "", category: str = "", clear_subject: bool = False, decision=None, coordinate_resolution=None, task: str = 'legacy', stage=None, detection=None, quality=None, source: str = 'self_declared_operator', root: Path = ROOT) -> dict:
    """Apply one review to one work area.

    task='classification' (other-model area) changes binary/stage/quality and cls_review only.
    task='detection' (YOLO area) changes boxes / no_target / not_annotated and det_review only.
    Neither area reads or constrains the other.  task='legacy' keeps the previous single
    form for the CLI and old clients (both areas follow one status).
    """
    rows = read_manifest(root)
    r = next((r for r in rows if r["image_id"] == image_id), None)
    if r is None or not reviewer.strip() or not reason.strip():
        raise ValueError("Existing image_id, reviewer and reason are required")
    if task == 'detection':
        label = r['label_state'] or 'unknown'   # untouched by the YOLO area
    if label is None:
        raise ValueError('Binary label is required')
    if status is not None and status not in {"approved", "pending_review", "excluded"}:
        raise ValueError("Invalid status")
    _check_review_labels(label, stage, quality)
    plan = plan_status(r, task=task, decision=decision, status=status, category=category)
    decision, status = plan['decision'], plan['status']
    if task in ('legacy', 'classification') and plan['cls'] == 'confirmed' and label not in ('positive', 'negative'):
        raise ValueError("Confirm positive or negative before approval")
    old = dict(r)
    old_annotation = {k:v for k,v in read_json(inside(r['annotation_path'],root)).items() if k!='imageData'} if r.get('annotation_path') and inside(r['annotation_path'],root).is_file() else None
    src = inside(r["image_path"], root)
    current = tasks.effective(r)
    new_detection = r.get('detection_state', '') or (current['detection'] if current['detection'] != 'not_annotated' else '')
    write_boxes = None  # None: keep existing YOLO labels
    ann = None
    if task == 'detection':
        if detection not in DETECTION_STATES:
            raise ValueError('請選擇病灶偵測狀態')
        if plan['det'] == 'confirmed' and detection == 'not_annotated':
            raise ValueError('「尚未處理」不能標為完成；請框選病灶或確認無病灶')
        ann = inside(annotation, root) if annotation else None
        with Image.open(src) as im:
            im.verify()
        with Image.open(src) as im:
            size = im.size
        if detection == 'boxes':
            if not ann:
                raise ValueError("Lesion boxes require a LabelMe annotation")
            write_boxes = from_labelme(read_json(ann), size)
            if not write_boxes:
                raise ValueError("Lesion annotation cannot be empty")
        elif detection == 'no_target':
            if ann and read_json(ann).get("shapes"):
                raise ValueError("「確認無病灶」不可包含病灶框")
            write_boxes = []
        new_detection = detection
    elif task == 'classification':
        if detection is not None:
            raise ValueError('分類區不處理病灶框')
        if plan['cls'] == 'confirmed':
            with Image.open(src) as im:
                im.verify()
    else:  # legacy single form
        ann = inside(annotation, root) if annotation else (inside(r["annotation_path"], root) if r["annotation_path"] else None)
        if status == "approved":
            with Image.open(src) as im:
                im.verify()
            if label == "positive":
                if ann:
                    with Image.open(src) as im:
                        boxes = from_labelme(read_json(ann), im.size)
                    if boxes:
                        write_boxes, new_detection = boxes, 'boxes'
                    elif current['detection'] == 'boxes':
                        raise ValueError("Positive annotation cannot be empty")
            elif label != "negative":
                raise ValueError("Confirm positive or negative before approval")
            else:
                if ann and read_json(ann).get("shapes"):
                    raise ValueError("Negative image still has positive annotations")
                write_boxes, new_detection = [], 'no_target'
    base = plan['base']
    dst = inside(f"data/{base}/images/{src.name}", root)
    moves = []
    if dst != src:
        moves.append((src, dst))
        old_ann_dir = src.parent.parent / "annotations"
        new_ann_dir = dst.parent.parent / "annotations"
        if old_ann_dir.exists():
            moves.extend((p, inside(new_ann_dir / p.name, root))
                         for p in old_ann_dir.glob(image_id + "*") if p.is_file())
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
    ann_path = relocated(r.get('annotation_path'))
    yolo = relocated(r.get('yolo_path'))
    for s, t in completed:
        if ann and ann.resolve() == s.resolve():
            ann = t
    if ann and task in ('legacy', 'detection'):
        ann_dst = inside(f"data/{base}/annotations/{image_id}_review.json", root)
        ann_dst.parent.mkdir(parents=True, exist_ok=True)
        if ann.resolve() != ann_dst.resolve():
            shutil.copy2(ann, ann_dst)
        ann_path = ann_dst.relative_to(root).as_posix()
    if write_boxes is not None:
        lab = inside(f"data/{base}/annotations/{image_id}.txt", root)
        lab.parent.mkdir(parents=True, exist_ok=True)
        lab.write_text(text(write_boxes), encoding="utf-8")
        yolo = lab.relative_to(root).as_posix()
    elif task == 'detection' and new_detection == 'not_annotated':
        yolo = ''
    elif task == 'legacy' and status != 'approved' and not r.get('detection_state'):
        # Legacy behaviour: an unapproved legacy row has no active detection label.
        yolo = ''
        new_detection = ''
    updates = dict(status=status, cls_review=plan['cls'], det_review=plan['det'], reason=reason, reviewer=reviewer, updated_at=stamp(),
                   image_path=dst.relative_to(root).as_posix(), annotation_path=ann_path, yolo_path=yolo)
    if task in ('legacy', 'classification'):
        updates['label_state'] = label
    if new_detection != r.get('detection_state', ''):
        updates['detection_state'] = new_detection
    if stage is not None and task == 'classification':
        updates['stage_label'] = '' if stage == 'unknown' else stage
        updates['label_scheme'] = 'stage_v1' if stage != 'unknown' else ''
    elif task == 'classification' and r.get('stage_label') and STAGE_TO_BINARY.get(r['stage_label']) != label:
        updates['stage_label'] = ''
        updates['label_scheme'] = ''
    if quality is not None and task in ('legacy', 'classification'):
        updates['quality_state'] = quality
    r.update(updates)
    if subject_id:
        r.update(subject_id=subject_id, group_verified="true")
    elif clear_subject:r.update(subject_id='',group_verified='false')
    for problem in tasks.consistency_errors(r):
        raise ValueError(problem)
    from src.data import evidence
    rule = source == 'authorized_filename_rule'
    evidence.append(image_id, {'task': {'classification': 'classification', 'detection': 'detection'}.get(task, 'legacy'), 'source': source if rule else 'human_review',
                               'method': 'rule_applied' if rule else 'review', 'actor': reviewer, 'decision': decision,
                               **({'binary': label, 'stage': r.get('stage_label') or None} if task != 'detection' else {}),
                               **({'detection': r.get('detection_state') or None} if task != 'classification' else {}), 'reason': reason}, root)
    write_manifest(rows, root)
    write_json(root / f"data/reviews/{stamp()}_{image_id}.json", {"schema_version":4,"task":task,"area":{'classification':'cls','detection':'det'}.get(task,'both'),"before": old, "after": r,"decision":decision,"source":source,"coordinate_resolution":coordinate_resolution,"annotation_before":old_annotation,"annotation_after":read_json(inside(ann_path,root)) if ann_path and task!='classification' else None})
    return r


def _eligible_rows(root: Path, task: str) -> list[dict]:
    from src.workbench.views import data_rows
    return [r for r in data_rows(root) if r['tasks'][task]['eligible']]


def _build(*, demo: bool = False, root: Path = ROOT, folds: int = 3, seed: int = 42, task: str = 'detection', name: str | None = None) -> dict:
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
    if unverified and not demo:
        raise ValueError("Patient identifiers are not verified. Review manifest first, or explicitly use --demo for workflow validation only.")
    review_revisions = {r['image_id']:r['review']['revision'] if r['review'] else None for r in eligible}
    ids = {r['image_id'] for r in eligible}
    rows = [r for r in read_manifest(root) if r['image_id'] in ids]
    groups = [r["subject_id"] if r["group_verified"]=="true" else "candidate:"+(r["candidate_group"] or r["image_id"]) for r in rows]
    targets = [tasks.target(r, task) for r in rows]
    class_names = SCHEMES[scheme]['classes'] if task != 'detection' else ['background', 'phlebitis']
    labels = [class_names.index(t) for t in targets]
    counts = Counter(labels)
    missing = [class_names[i] for i in range(len(class_names)) if counts.get(i, 0) < folds]
    if len(set(groups)) < folds or missing:
        detail = '、'.join(f"{name}={counts.get(i,0)}" for i, name in enumerate(class_names))
        raise ValueError(f"資料不足以建立 {folds} 折：每一類至少需要 {folds} 張且至少 {folds} 個分組。目前可用：{detail}；分組 {len(set(groups))} 個。不會複製樣本或偽造分組。")
    splitter = StratifiedGroupKFold(n_splits=folds, shuffle=True, random_state=seed)
    splits = list(splitter.split(np.zeros(len(rows)), labels, groups))
    for train, val in splits:
        if set(groups[i] for i in train) & set(groups[i] for i in val):
            raise ValueError("Group leakage")
        if len({labels[i] for i in train}) != len(class_names) or len({labels[i] for i in val}) != len(class_names):
            raise ValueError(f"無法讓每一折的訓練與驗證都包含全部 {len(class_names)} 類；需要更多已審查的分組。")
    prefix = {'detection': '', 'binary_classification': 'binary_', 'stage_classification': 'stage_'}[task]
    version = ("demo_" if demo else "verified_") + prefix + stamp()
    final = inside("data/yolo/" + version, root)
    building = inside("data/yolo/.building-" + version, root)
    manifest_digest = rows_digest(read_manifest(root))
    mapping = {name: i for i, name in enumerate(SCHEMES[scheme]['classes'])}
    info = {"version": version, "task": task, "label_scheme": scheme, "class_mapping": mapping, "demo_only": demo,
            "patient_identity_verified": not unverified, "seed": seed, "schema_version": 3, "manifest_digest": manifest_digest,
            "folds": [], "created_at": stamp(), "note": "Cross-validation folds, not an independent clinical test set."}
    if name:
        info["name"] = name  # display label only; the version stays the immutable ID
    from src.data import evidence
    def normalized(image, target):
        with Image.open(image) as im:
            orientation = im.getexif().get(274, 1)
            ImageOps.exif_transpose(im).convert("RGB").save(target, format="JPEG", quality=95)
        return orientation
    try:
        shared = {}
        if task != 'detection':
            # One normalized copy per snapshot; folds only list members.
            (building / 'images').mkdir(parents=True, exist_ok=True)
            for r in rows:
                target = building / 'images' / f"{r['image_id']}.jpg"
                normalized(inside(r['image_path'], root), target)
                shared[r['image_id']] = {'image_path': f"data/yolo/{version}/images/{r['image_id']}.jpg", 'dataset_sha256': sha256(target)}
        for fold, (train, val) in enumerate(splits):
            target_dir = building / f"fold{fold}"
            members = {}
            for split, indices in [("train", train), ("val", val)]:
                members[split] = []
                for i in indices:
                    r = rows[int(i)]
                    ev = evidence.path(r['image_id'], root)
                    member = {"review_revision": review_revisions[r["image_id"]], "image_id": r["image_id"], "sha256": r["sha256"],
                              "normalization": "exif_transpose_rgb_jpeg95", "group": groups[int(i)], "label_state": r["label_state"],
                              "stage_label": tasks.effective(r)['stage'], "target": targets[int(i)],
                              "label_evidence_sha256": sha256(ev) if ev.exists() else None}
                    if task == 'detection':
                        ip = target_dir / f"images/{split}/{r['image_id']}.jpg"
                        lp = target_dir / f"labels/{split}/{r['image_id']}.txt"
                        ip.parent.mkdir(parents=True, exist_ok=True)
                        lp.parent.mkdir(parents=True, exist_ok=True)
                        source_label = inside(r["yolo_path"], root)
                        orientation = normalized(inside(r["image_path"], root), ip)
                        lp.write_text(text(orient_boxes(_yolo_boxes(source_label), orientation)), encoding="utf-8")
                        member.update({"dataset_sha256": sha256(ip), "source_label_sha256": sha256(source_label), "label_sha256": sha256(lp),
                                       "image_path": f"data/yolo/{version}/fold{fold}/images/{split}/{r['image_id']}.jpg",
                                       "label_path": f"data/yolo/{version}/fold{fold}/labels/{split}/{r['image_id']}.txt"})
                    else:
                        member.update(shared[r['image_id']])
                    members[split].append(member)
            target_dir.mkdir(parents=True, exist_ok=True)
            if task == 'detection':
                dataset = {"path": str(final / f"fold{fold}"), "train": "images/train", "val": "images/val", "names": {0: "phlebitis"}}
            else:
                dataset = {"path": str(final / f"fold{fold}"), "task": task, "label_scheme": scheme, "names": {i: n for n, i in mapping.items()}}
            (target_dir / "dataset.yaml").write_text(yaml.safe_dump(dataset, allow_unicode=True), encoding="utf-8")
            fold_info = {"schema_version": 3, "fold": fold, "task": task, "label_scheme": scheme, "class_mapping": mapping,
                         "dataset": f"data/yolo/{version}/fold{fold}/dataset.yaml", "members": members, "demo_only": demo, "manifest_digest": manifest_digest}
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
    latest = "latest.json" if task == 'detection' else f"latest_{task}.json"
    write_json(root / "data/yolo" / latest, {"version": version})
    return info


def snapshot_task(split: dict) -> str | None:
    """Task of a fold; None for schema-2 snapshots (legacy binary + detection layout)."""
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
    state_path=root/'data/snapshot_states.json'
    states=read_json(state_path) if state_path.exists() else {}
    if dataset.parent.parent.name in states:
        raise ValueError('Snapshot withdrawn or superseded: '+states[dataset.parent.parent.name]['reason'])
    _require_active_snapshot(dataset.parent.parent.name, root)
    sealed = next((f for f in version["folds"] if f["fold"] == split["fold"]), None)
    if sealed is None:
        raise ValueError("Unlisted fold")
    if {k:v for k,v in sealed.items() if k!='split_sha256'}!=split:
        raise ValueError('Snapshot member metadata does not match the version manifest')
    if sealed.get("split_sha256") and sealed["split_sha256"] != sha256(dataset.parent / "split.json"):
        raise ValueError("Snapshot split integrity failure")
    if version.get("withdrawn"):
        raise ValueError("Snapshot has been withdrawn")
    task = snapshot_task(split)
    cfg = yaml.safe_load(dataset.read_text(encoding="utf-8"))
    if task in (None, 'detection'):
        expected = {"path": str(dataset.parent.resolve()), "train": "images/train", "val": "images/val", "names": {0:"phlebitis"}}
    else:
        scheme = split['label_scheme']
        if task != SCHEMES[scheme]['task'] or split.get('class_mapping') != tasks.mapping(scheme):
            raise ValueError('Snapshot label scheme does not match its task')
        expected = {"path": str(dataset.parent.resolve()), "task": task, "label_scheme": scheme, "names": {i: n for n, i in tasks.mapping(scheme).items()}}
    if cfg != expected:
        raise ValueError("Dataset YAML changed or points outside its version")
    table = revocations.revoked(root)
    seen, split_groups = set(), {}
    for name in ["train", "val"]:
        members = split["members"][name]
        expected_images, expected_labels = set(), set()
        split_groups[name] = set()
        for m in members:
            ident = m["image_id"]
            if ident in seen:
                raise ValueError("Duplicate or unapproved image in split")
            if task is None and m["label_state"] not in {"positive", "negative"}:
                raise ValueError("Duplicate or unapproved image in split")
            if task == 'detection' and m.get('target') not in ('phlebitis', 'background'):
                raise ValueError("Duplicate or unapproved image in split")
            if task not in (None, 'detection'):
                tasks.member_class(m, split['label_scheme'])
            if revocations.is_revoked(m, table):
                raise ValueError('Snapshot contains data whose use was withdrawn')
            seen.add(ident)
            p = inside(m["image_path"], root)
            expected_images.add(p.resolve())
            if task in (None, 'detection'):
                lab = inside(m["label_path"], root)
                expected_labels.add(lab.resolve())
                if not p.is_relative_to(dataset.parent / f"images/{name}") or not lab.is_relative_to(dataset.parent / f"labels/{name}") or sha256(p) != m["dataset_sha256"] or sha256(lab) != m["label_sha256"]:
                    raise ValueError("Dataset image or label has changed")
            elif not p.is_relative_to(dataset.parent.parent / "images") or sha256(p) != m["dataset_sha256"]:
                raise ValueError("Dataset image or label has changed")
            split_groups[name].add(m["group"])
        if task in (None, 'detection'):
            if {p.resolve() for p in (dataset.parent / f"images/{name}").iterdir() if p.is_file()} != expected_images:
                raise ValueError("Unlisted image detected in generated dataset")
            if {p.resolve() for p in (dataset.parent / f"labels/{name}").glob("*.txt")} != expected_labels:
                raise ValueError("Unlisted annotation detected in generated dataset")
    if task not in (None, 'detection'):
        listed = {inside(m['image_path'], root).resolve() for f in version['folds'] for ms in f['members'].values() for m in ms}
        if {p.resolve() for p in (dataset.parent.parent / 'images').iterdir() if p.is_file()} != listed:
            raise ValueError("Unlisted image detected in generated dataset")
    if split_groups["train"] & split_groups["val"]:
        raise ValueError("Cross-split group leakage")
    return split


def latest_dataset(fold: int = 0, root: Path = ROOT) -> Path:
    version = read_json(root / "data/yolo/latest.json")["version"]
    return inside(f"data/yolo/{version}/fold{fold}/dataset.yaml", root)


def build(*, demo=False, root=ROOT, folds=3, seed=42, task='detection', name=None):
    from src.workbench.storage import dataset_lock
    if not 2 <= folds <= 10:
        raise ValueError("Fold count must be 2..10")
    with dataset_lock(root):
        recover_reviews(root)
        return _build(demo=demo, root=root, folds=folds, seed=seed, task=task, name=name)


def recover_reviews(root=ROOT):
    """Restore a transaction's before-images after a crash, before accepting writes."""
    for journal in (root / "runtime/review_transactions").glob("*/journal.json"):
        tx = read_json(journal)
        if tx["state"] != "pending": continue
        for item in tx["files"]:
            path = inside(item["path"], root)
            if item["backup"]:
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(journal.parent / item["backup"], path)
            else: path.unlink(missing_ok=True)
        for log in (root / "data/reviews").glob("*.json"):
            if log.name not in tx["logs_before"]: log.unlink()
        tx["state"] = "rolled_back"
        write_json(journal, tx)
        for backup in journal.parent.glob('*.bak'):backup.unlink()


SUBSTANTIVE = ('status', 'label_state', 'subject_id', 'group_verified', 'stage_label', 'detection_state', 'usage_state', 'quality_state', 'cls_review', 'det_review')


def review(image_id, *, revision=None, root=ROOT, **kwargs):
    from src.workbench.storage import dataset_lock
    with dataset_lock(root):
        recover_reviews(root)
        rows = read_manifest(root)
        row = next((r for r in rows if r["image_id"] == image_id), None)
        if row is None: raise ValueError("Unknown image")
        if revision is not None and tasks.row_revision(row) != revision:
            raise ValueError("revision conflict: reload before saving")
        src = inside(row["image_path"], root)
        base = plan_status(row, task=kwargs.get('task', 'legacy'), decision=kwargs.get('decision'), status=kwargs.get('status'), category=kwargs.get('category', ''))['base']
        dst = inside(f"data/{base}/images/{src.name}", root)
        from src.data import evidence
        paths = {root / "data/manifest.csv", src, dst,
                 root / 'data/snapshot_states.json',
                 evidence.path(image_id, root),
                 root / f"data/{base}/annotations/{image_id}_review.json",
                 root / f"data/{base}/annotations/{image_id}.txt",
                 root / f"data/approved/annotations/{image_id}.txt"}
        for p in (src.parent.parent / "annotations").glob(image_id + "*"):
            paths.add(p); paths.add(dst.parent.parent / "annotations" / p.name)
        import uuid
        folder = root / "runtime/review_transactions" / (stamp() + "-" + uuid.uuid4().hex[:8])
        folder.mkdir(parents=True)
        old_label_hash=sha256(inside(row['yolo_path'],root)) if row.get('yolo_path') and inside(row['yolo_path'],root).exists() else None
        tx = {"state":"pending", "image_id":image_id, "logs_before":[p.name for p in (root / "data/reviews").glob("*.json")], "files":[]}
        for i, path in enumerate(sorted(paths)):
            backup = f"{i}.bak" if path.exists() else None
            if backup: shutil.copy2(path, folder / backup)
            tx["files"].append({"path":path.relative_to(root).as_posix(), "backup":backup})
        write_json(folder / "journal.json", tx)
        try:
            result = _review(image_id, root=root, **kwargs)
            new_label_hash=sha256(inside(result['yolo_path'],root)) if result.get('yolo_path') else None
            substantive=any((row.get(k) or '')!=(result.get(k) or '') for k in SUBSTANTIVE) or old_label_hash!=new_label_hash
            if substantive:
                state_path=root/'data/snapshot_states.json'
                states=read_json(state_path) if state_path.exists() else {}
                for version in (root/'data/yolo').glob('*/dataset_version.json'):
                    info=read_json(version)
                    if any(m['image_id']==image_id for f in info['folds'] for members in f['members'].values() for m in members):
                        states[version.parent.name]={'reason':'Human review changed labels, eligibility or grouping','image_id':image_id,'at':stamp(),'status':'superseded'}
                write_json(state_path,states)
            tx["state"] = "committed"; write_json(folder / "journal.json", tx)
            # Backups are transient recovery data, not a second research archive.
            for p in folder.glob("*.bak"): p.unlink()
            return result
        except BaseException:
            recover_reviews(root)
            raise
