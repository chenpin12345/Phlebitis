from __future__ import annotations

import json
import shutil
from collections import Counter
from pathlib import Path

from PIL import Image, ImageOps
from src.common import ROOT, inside, read_json, read_manifest, rows_digest, sha256, stamp, write_json, write_manifest
from src.data.labels import from_labelme, text, validate, orient_boxes


def audit(root: Path = ROOT) -> dict:
    rows = read_manifest(root)
    errors, warnings = [], []
    seen, ids = {}, set()
    for r in rows:
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
            if r["status"] == "approved":
                if r["label_state"] not in {"positive", "negative"}:
                    raise ValueError("approved image has unknown ground truth")
                with Image.open(image) as im:
                    im.verify()
                boxes = [list(map(float, line.split())) for line in inside(r["yolo_path"], root).read_text().splitlines() if line.strip()]
                validate(boxes)
                if bool(boxes) != (r["label_state"] == "positive"):
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
    return {"images": len(rows), "statuses": dict(Counter(r["status"] for r in rows)), "approved_labels": dict(Counter(r["label_state"] for r in rows if r["status"]=="approved")), "errors": errors, "warnings": warnings}


def _review(image_id: str, *, status: str, label: str, reviewer: str, reason: str, subject_id: str = "", annotation: str = "", category: str = "", clear_subject: bool = False, root: Path = ROOT) -> dict:
    rows = read_manifest(root)
    r = next((r for r in rows if r["image_id"] == image_id), None)
    if r is None or not reviewer.strip() or not reason.strip():
        raise ValueError("Existing image_id, reviewer and reason are required")
    if status not in {"approved", "pending_review", "excluded"}:
        raise ValueError("Invalid status")
    old = dict(r)
    src = inside(r["image_path"], root)
    ann = inside(annotation, root) if annotation else (inside(r["annotation_path"], root) if r["annotation_path"] else None)
    boxes = []
    if status == "approved":
        with Image.open(src) as im:
            im.verify()
        if label == "positive":
            if not ann:
                raise ValueError("Positive images require a LabelMe annotation")
            with Image.open(src) as im:
                boxes = from_labelme(read_json(ann), im.size)
            if not boxes:
                raise ValueError("Positive annotation cannot be empty")
        elif label != "negative":
            raise ValueError("Confirm positive or negative before approval")
        elif ann:
            if read_json(ann).get("shapes"):
                raise ValueError("Negative image still has positive annotations")
    categories = {"excluded":{"unclear","blurry","unreadable","other"},
                  "pending_review":{"annotation","unknown_source","duplicate_variant"}}
    if category and (status == "approved" or category not in categories[status]):
        raise ValueError("Category does not match the review status")
    base = "approved" if status == "approved" else f"{status}/" + (category or ("other" if status == "excluded" else "annotation"))
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
        for source, target in moves:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(target))
            completed.append((source, target))
    except OSError:
        for source, target in reversed(completed):
            shutil.move(str(target), str(source))
        raise
    for source, target in completed:
        if ann and ann.resolve() == source.resolve():
            ann = target
    ann_path = ""
    if ann:
        ann_dst = inside(f"data/{base}/annotations/{image_id}_review.json", root)
        ann_dst.parent.mkdir(parents=True, exist_ok=True)
        if ann.resolve() != ann_dst.resolve():
            shutil.copy2(ann, ann_dst)
        ann_path = ann_dst.relative_to(root).as_posix()
    yolo = ""
    if status == "approved":
        lab = inside(f"data/approved/annotations/{image_id}.txt", root)
        lab.parent.mkdir(parents=True, exist_ok=True)
        lab.write_text(text(boxes), encoding="utf-8")
        yolo = lab.relative_to(root).as_posix()
    r.update(status=status, label_state=label, reason=reason, reviewer=reviewer, updated_at=stamp(), image_path=dst.relative_to(root).as_posix(), annotation_path=ann_path, yolo_path=yolo)
    if subject_id:
        r.update(subject_id=subject_id, group_verified="true")
    elif clear_subject:r.update(subject_id='',group_verified='false')
    write_manifest(rows, root)
    write_json(root / f"data/reviews/{stamp()}_{image_id}.json", {"before": old, "after": r})
    return r


def _build(*, demo: bool = False, root: Path = ROOT, folds: int = 3, seed: int = 42) -> dict:
    import numpy as np
    import yaml
    from sklearn.model_selection import StratifiedGroupKFold
    report = audit(root)
    if report["errors"]:
        raise ValueError("Dataset audit failed: " + "; ".join(report["errors"]))
    if report["warnings"] and not demo:
        raise ValueError("Patient identifiers are not verified. Review manifest first, or explicitly use --demo for workflow validation only.")
    rows = [r for r in read_manifest(root) if r["status"] == "approved"]
    groups = [r["subject_id"] if r["group_verified"]=="true" else "candidate:"+(r["candidate_group"] or r["image_id"]) for r in rows]
    labels = [int(r["label_state"] == "positive") for r in rows]
    if len(set(groups)) < folds or min(Counter(labels).values(), default=0) < folds or len(set(labels)) < 2:
        raise ValueError("At least three groups and both positive/negative samples are required")
    splitter = StratifiedGroupKFold(n_splits=folds, shuffle=True, random_state=seed)
    splits = list(splitter.split(np.zeros(len(rows)), labels, groups))
    for train, val in splits:
        if set(groups[i] for i in train) & set(groups[i] for i in val):
            raise ValueError("Group leakage")
        if len({labels[i] for i in train}) != 2 or len({labels[i] for i in val}) != 2:
            raise ValueError("Cannot form three folds with both classes; more reviewed groups are needed")
    version = ("demo_" if demo else "verified_") + stamp()
    base = inside("data/yolo/" + version, root)
    manifest_digest = rows_digest(read_manifest(root))
    info = {"version": version, "demo_only": demo, "patient_identity_verified": not bool(report["warnings"]), "seed": seed, "schema_version": 2, "manifest_digest": manifest_digest, "folds": [], "note": "Cross-validation folds, not an independent clinical test set."}
    for fold, (train, val) in enumerate(splits):
        target = base / f"fold{fold}"
        members = {}
        for split, indices in [("train", train), ("val", val)]:
            members[split] = []
            for i in indices:
                r = rows[int(i)]
                image = inside(r["image_path"], root)
                ip = target / f"images/{split}/{r['image_id']}.jpg"
                lp = target / f"labels/{split}/{r['image_id']}.txt"
                ip.parent.mkdir(parents=True, exist_ok=True)
                lp.parent.mkdir(parents=True, exist_ok=True)
                source_label = inside(r["yolo_path"], root)
                boxes = [list(map(float,line.split())) for line in source_label.read_text().splitlines() if line.strip()]
                with Image.open(image) as im:
                    orientation = im.getexif().get(274, 1)
                    normalized = ImageOps.exif_transpose(im).convert("RGB")
                    normalized.save(ip, format="JPEG", quality=95)
                lp.write_text(text(orient_boxes(boxes, orientation)), encoding="utf-8")
                members[split].append({"image_id": r["image_id"], "sha256": r["sha256"], "dataset_sha256": sha256(ip), "source_label_sha256": sha256(source_label), "normalization": "exif_transpose_rgb_jpeg95", "label_sha256": sha256(lp), "image_path": ip.relative_to(root).as_posix(), "label_path": lp.relative_to(root).as_posix(), "group": groups[int(i)], "label_state": r["label_state"]})
        dataset = {"path": str(target.resolve()), "train": "images/train", "val": "images/val", "names": {0: "phlebitis"}}
        (target / "dataset.yaml").write_text(yaml.safe_dump(dataset, allow_unicode=True), encoding="utf-8")
        fold_info = {"schema_version": 2, "fold": fold, "dataset": (target / "dataset.yaml").relative_to(root).as_posix(), "members": members, "demo_only": demo, "manifest_digest": manifest_digest}
        write_json(target / "split.json", fold_info)
        fold_info["split_sha256"] = sha256(target / "split.json")
        info["folds"].append(fold_info)
    write_json(base / "dataset_version.json", info)
    write_json(root / "data/yolo/latest.json", {"version": version})
    return info


def validate_split(dataset: Path, root: Path = ROOT) -> dict:
    import yaml
    dataset = inside(dataset, root)
    split = read_json(dataset.parent / "split.json")
    version = read_json(dataset.parent.parent / "dataset_version.json")
    state_path=root/'data/snapshot_states.json'
    states=read_json(state_path) if state_path.exists() else {}
    if dataset.parent.parent.name in states:
        raise ValueError('Snapshot withdrawn or superseded: '+states[dataset.parent.parent.name]['reason'])
    sealed = next((f for f in version["folds"] if f["fold"] == split["fold"]), None)
    if sealed is None:
        raise ValueError("Unlisted fold")
    if {k:v for k,v in sealed.items() if k!='split_sha256'}!=split:
        raise ValueError('Snapshot member metadata does not match the version manifest')
    if sealed.get("split_sha256") and sealed["split_sha256"] != sha256(dataset.parent / "split.json"):
        raise ValueError("Snapshot split integrity failure")
    if version.get("withdrawn"):
        raise ValueError("Snapshot has been withdrawn")
    cfg = yaml.safe_load(dataset.read_text(encoding="utf-8"))
    expected = {"path": str(dataset.parent.resolve()), "train": "images/train", "val": "images/val", "names": {0:"phlebitis"}}
    if cfg != expected:
        raise ValueError("Dataset YAML changed or points outside its version")
    seen, split_groups = set(), {}
    for name in ["train", "val"]:
        members = split["members"][name]
        expected_images, expected_labels = set(), set()
        split_groups[name] = set()
        for m in members:
            ident = m["image_id"]
            if ident in seen or m["label_state"] not in {"positive", "negative"}:
                raise ValueError("Duplicate or unapproved image in split")
            seen.add(ident)
            p, lab = inside(m["image_path"], root), inside(m["label_path"], root)
            expected_images.add(p.resolve())
            expected_labels.add(lab.resolve())
            if not p.is_relative_to(dataset.parent / f"images/{name}") or not lab.is_relative_to(dataset.parent / f"labels/{name}") or sha256(p) != m["dataset_sha256"] or sha256(lab) != m["label_sha256"]:
                raise ValueError("Dataset image or label has changed")
            split_groups[name].add(m["group"])
        if {p.resolve() for p in (dataset.parent / f"images/{name}").iterdir() if p.is_file()} != expected_images:
            raise ValueError("Unlisted image detected in generated dataset")
        if {p.resolve() for p in (dataset.parent / f"labels/{name}").glob("*.txt")} != expected_labels:
            raise ValueError("Unlisted annotation detected in generated dataset")
    if split_groups["train"] & split_groups["val"]:
        raise ValueError("Cross-split group leakage")
    return split


def latest_dataset(fold: int = 0, root: Path = ROOT) -> Path:
    version = read_json(root / "data/yolo/latest.json")["version"]
    return inside(f"data/yolo/{version}/fold{fold}/dataset.yaml", root)


def build(*, demo=False, root=ROOT, folds=3, seed=42):
    from src.workbench.storage import file_lock
    if not 2 <= folds <= 10:
        raise ValueError("Fold count must be 2..10")
    with file_lock(root / "runtime/data.lock"):
        recover_reviews(root)
        return _build(demo=demo, root=root, folds=folds, seed=seed)


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


def review(image_id, *, revision=None, root=ROOT, **kwargs):
    from src.workbench.storage import file_lock, digest
    with file_lock(root / "runtime/data.lock"):
        recover_reviews(root)
        rows = read_manifest(root)
        row = next((r for r in rows if r["image_id"] == image_id), None)
        if row is None: raise ValueError("Unknown image")
        if revision is not None and digest(row) != revision:
            raise ValueError("revision conflict: reload before saving")
        src = inside(row["image_path"], root)
        status = kwargs["status"]
        category = kwargs.get("category", "")
        base = "approved" if status == "approved" else status + "/" + (category or ("other" if status == "excluded" else "annotation"))
        dst = inside(f"data/{base}/images/{src.name}", root)
        paths = {root / "data/manifest.csv", src, dst,
                 root / 'data/snapshot_states.json',
                 root / f"data/{base}/annotations/{image_id}_review.json",
                 root / f"data/approved/annotations/{image_id}.txt"}
        for p in (src.parent.parent / "annotations").glob(image_id + "*"):
            paths.add(p); paths.add(dst.parent.parent / "annotations" / p.name)
        folder = root / "runtime/review_transactions" / stamp()
        folder.mkdir(parents=True)
        old_label_hash=sha256(inside(row['yolo_path'],root)) if row.get('yolo_path') and inside(row['yolo_path'],root).exists() else None
        tx = {"state":"pending", "image_id":image_id, "logs_before":[p.name for p in (root / "data/reviews").glob("*.json")], "files":[]}
        for i, path in enumerate(paths):
            backup = f"{i}.bak" if path.exists() else None
            if backup: shutil.copy2(path, folder / backup)
            tx["files"].append({"path":path.relative_to(root).as_posix(), "backup":backup})
        write_json(folder / "journal.json", tx)
        try:
            result = _review(image_id, root=root, **kwargs)
            new_label_hash=sha256(inside(result['yolo_path'],root)) if result.get('yolo_path') else None
            substantive=any(row.get(k)!=result.get(k) for k in ('status','label_state','subject_id','group_verified')) or old_label_hash!=new_label_hash
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
