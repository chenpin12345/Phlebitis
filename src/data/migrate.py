from __future__ import annotations

import json
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image

from src.common import ROOT, inside, read_json, sha256, stamp, write_json, write_manifest
from src.data.labels import from_labelme, text

LEGACY = ["不清楚的", "圖片", "熱像儀", "雜燴", "train-label", "val-label", "YOLODataset", "3.0.py", "AI.py", "AI2.0.py", "test.py", "import json.py", "my_data.yaml", "train.cache", "val.cache"]


def copy_verified(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        shutil.copy2(src, dst)
    if sha256(src) != sha256(dst):
        raise ValueError(f"Copy verification failed: {dst}")


def migrate(root: Path = ROOT) -> dict:
    root = root.resolve()
    marker = root / "archive/migration_complete.json"
    if marker.exists():
        return read_json(marker)
    archive = inside("archive/legacy", root)
    sources = {name: inside(name, root) if inside(name, root).exists() else archive / name for name in LEGACY}
    all_files = []
    for name, p in sources.items():
        if p.exists():
            all_files.extend([(name + "/" + str(f.relative_to(p)).replace("\\", "/"), f) for f in p.rglob("*") if f.is_file()] if p.is_dir() else [(name, p)])
    if not all_files:
        raise ValueError("Original project data was not found")
    inventory = [{"original_path": n, "sha256": sha256(p), "bytes": p.stat().st_size} for n, p in all_files]
    write_json(root / "archive/migration_inventory.json", inventory)
    annotations = defaultdict(list)
    for n, p in all_files:
        if p.suffix.lower() == ".json" and n.split("/")[0] in {"train-label", "val-label"}:
            annotations[p.stem].append((n, p))
    excluded_stems = {p.stem for n, p in all_files if n.startswith("不清楚的/")}
    groups = defaultdict(list)
    for n, p in all_files:
        if p.suffix.lower() in {".jpg", ".jpeg", ".png"}:
            groups[sha256(p)].append((n, p))
    rows = []
    when = stamp()
    approved_stems = set()
    ordered = sorted(groups.items(), key=lambda item: (not any(n.startswith("YOLODataset/") for n, _ in item[1]), item[0]))
    for digest, copies in ordered:
        n, image = sorted(copies, key=lambda a: (not a[0].startswith("YOLODataset/"), a[0]))[0]
        names = [name for name, _ in copies]
        stems = {p.stem for _, p in copies}
        candidates = [v for stem in stems for v in annotations.get(stem, [])]
        normal = any(name.startswith("圖片/一般/") for name in names)
        status, label, reason = "pending_review", "unknown", "來源或正負樣本狀態待確認"
        subfolder, boxes, annotation = "pending_review/unknown_source", [], ""
        image_size = None
        try:
            with Image.open(image) as im:
                im.verify()
            with Image.open(image) as im:
                image_size = im.size
        except Exception:
            status, subfolder, reason = "excluded", "excluded/unreadable", "圖片無法完整讀取"
        if image_size:
            if excluded_stems & stems:
                status, subfolder, reason = "excluded", "excluded/unclear", "原資料列於不清楚的；保留既有排除狀態"
            elif normal and candidates:
                subfolder, reason = "pending_review/annotation", "正常來源與病灶標註衝突"
            elif candidates:
                try:
                    versions = [from_labelme(read_json(p), image_size) for _, p in candidates]
                    if not versions[0] or any(v != versions[0] for v in versions):
                        raise ValueError("Empty or conflicting source annotations")
                    boxes = versions[0]
                    status, label, subfolder, reason = "approved", "positive", "approved", "既有人工矩形標註；格式已核對，未重新臨床覆核"
                except (KeyError, ValueError, TypeError) as exc:
                    subfolder, reason = "pending_review/annotation", f"標註需核對：{exc}"
            elif normal:
                status, label, subfolder, reason = "approved", "negative", "approved", "原始圖片/一般分類；來源分類沿用，未重新臨床覆核"
            elif any(name.startswith("圖片/靜脈炎/") for name in names):
                subfolder, reason = "pending_review/annotation", "病灶來源缺少可配對矩形標註"
        if status == "approved":
            if stems & approved_stems:
                status, subfolder, reason = "pending_review", "pending_review/duplicate_variant", "同名拍攝的不同檔案版本；優先保留原 YOLODataset 版本"
            else:
                approved_stems.update(stems)
        ident = digest[:16]
        destination = inside(f"data/{subfolder}/images/{image.stem}_{ident}{image.suffix.lower()}", root)
        copy_verified(image, destination)
        if candidates:
            for i, (_, ann) in enumerate(candidates):
                ann_dst = inside(f"data/{subfolder}/annotations/{ident}_{i}.json", root)
                copy_verified(ann, ann_dst)
                if not annotation:
                    annotation = ann_dst.relative_to(root).as_posix()
        yolo_path = ""
        if status == "approved":
            yolo = root / f"data/approved/annotations/{ident}.txt"
            yolo.parent.mkdir(parents=True, exist_ok=True)
            yolo.write_text(text(boxes), encoding="utf-8")
            yolo_path = yolo.relative_to(root).as_posix()
        match = re.match(r"\d{8}_([^_]+)_", image.stem)
        rows.append({"image_id": ident, "sha256": digest, "image_path": destination.relative_to(root).as_posix(), "annotation_path": annotation, "yolo_path": yolo_path, "status": status, "label_state": label, "candidate_group": match.group(1) if match else "", "subject_id": "", "group_verified": "false", "reviewer": "", "reason": reason, "updated_at": when, "original_paths": json.dumps(names, ensure_ascii=False)})
    write_manifest(rows, root)
    # Thermal files are independent of RGB training. All source paths remain traceable.
    for n, p in all_files:
        if p.suffix.lower() == ".csv":
            copy_verified(p, inside("data/thermal/" + n, root))
    for source, dest in [("yolo11n.pt", "models/pretrained/yolo11n.pt"), ("成果報告NEW.docx", "docs/成果報告NEW.docx")]:
        old, new = inside(source, root), inside(dest, root)
        if old.exists():
            copy_verified(old, new)
            saved = inside("archive/legacy/" + source, root)
            saved.parent.mkdir(parents=True, exist_ok=True)
            if saved.exists():
                raise ValueError(f"Refusing overwrite: {saved}")
            shutil.move(str(old), str(saved))
    # Validate resolved absolute paths before every directory move; never overwrite archives.
    archive.mkdir(parents=True, exist_ok=True)
    for name in LEGACY:
        old, new = inside(name, root), inside("archive/legacy/" + name, root)
        if old.exists():
            if new.exists():
                raise ValueError(f"Refusing overwrite: {new}")
            shutil.move(str(old), str(new))
    for entry in inventory:
        archived = inside("archive/legacy/" + entry["original_path"], root)
        if not archived.is_file() or sha256(archived) != entry["sha256"]:
            raise ValueError(f"Archive integrity failed: {entry['original_path']}")
    result = {"completed_at": when, "original_files_verified": len(inventory), "canonical_images": len(rows), "status_counts": dict(Counter(r["status"] for r in rows)), "label_counts": dict(Counter(r["label_state"] for r in rows)), "model": "YOLO11n", "note": "candidate_group is a filename hint, NOT a verified patient identifier"}
    write_json(marker, result)
    return result
