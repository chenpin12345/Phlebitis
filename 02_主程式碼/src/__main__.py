from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from src.common import ROOT, read_json, stamp, write_json
from src.paths import EVIDENCE_DIR


def main():
    parser = argparse.ArgumentParser(description="靜脈炎研究工作台：照片分類與 LINE")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="檢查 GPU、套件版本與工作區（資料夾、備份、外部來源）")
    p = sub.add_parser("workbench", help="啟動本地研究網頁工作台")
    p.add_argument("--port", type=int, default=8765)
    sub.add_parser("migrate-tasks", help="把舊資料列改為單一工作區（可重複執行），並套用已授權的檔名規則")
    sub.add_parser("audit", help="檢查資料清單與標註")
    p = sub.add_parser("build", help="建立三折個案分組資料集")
    p.add_argument("--demo", action="store_true", help="流程展示用快照，不能當正式成績")
    p.add_argument("--folds", type=int, default=3, help="每次切成幾折")
    p.add_argument("--repeats", type=int, default=5, help="重複切分幾次")
    p.add_argument(
        "--task",
        default="binary_classification",
        choices=["binary_classification", "stage_classification"],
        help="快照服務的訓練任務",
    )
    p = sub.add_parser("review", help="人工確認資料狀態並同步搬移檔案")
    p.add_argument("image_id")
    p.add_argument("--status", required=True, choices=["approved", "pending_review", "excluded"])
    p.add_argument("--label", required=True, choices=["positive", "negative", "unknown"])
    p.add_argument("--reviewer", required=True)
    p.add_argument("--reason", required=True)
    p.add_argument("--subject-id", default="")
    p.add_argument(
        "--category",
        default="",
        help="隔離原因子目錄：blurry、unclear、unreadable、other；待確認可用 annotation、unknown_source、duplicate_variant",
    )
    p = sub.add_parser("predict", help="分析一張圖片或一個資料夾")
    p.add_argument("source")
    p.add_argument("--device", default="0")
    p.add_argument("--allow-demo", action="store_true")
    p = sub.add_parser("serve", help="啟動本地 LINE webhook")
    p.add_argument("--port", type=int, default=8000)
    p = sub.add_parser("menu", help="產生 LINE 圖文選單素材；只有 --publish 才寫入帳號")
    p.add_argument("--publish", action="store_true")
    p = sub.add_parser('imports', help='研究照片與模型匯入（不使用 legacy migrate）')
    p.add_argument(
        'action', choices=['scan', 'commit', 'status', 'retry', 'external-scan', 'external-commit', 'apply-rules']
    )
    p.add_argument('--kind', choices=['photos', 'models'])
    p.add_argument('--batch')
    p.add_argument('--id')
    p.add_argument('--key')
    p.add_argument('--source', help='configs/import_sources.json 中的外部來源代號，例如 gangshan')
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--size', type=int, default=30)
    args = parser.parse_args()
    os.chdir(ROOT)
    if args.command == 'imports':
        from src.imports import service

        if args.action == 'apply-rules':
            from src.data.source_rules import apply_authorized_rules

            report = apply_authorized_rules(ROOT)
            print(json.dumps({'summary': report['summary'], 'items': report['items']}, ensure_ascii=False, indent=2))
            return 0
        if args.action.startswith('external'):
            from src.imports import external

            if args.action == 'external-scan':
                if not args.source:
                    parser.error('imports external-scan 需要 --source')
                result = external.scan(ROOT, args.source)
            else:
                if not args.id:
                    parser.error('imports external-commit 需要 --id')
                state = service.load(ROOT, args.id)['state']
                result = external.commit(
                    ROOT, args.id, args.key or ('external:' + args.id), retry=state in ('failed', 'needs_check')
                )
            print(json.dumps(service.public(result, args.page, args.size), ensure_ascii=False, indent=2))
            return 1 if result['state'] == 'failed' else 0
        if args.action == 'scan' and (not args.kind or not args.batch):
            parser.error('imports scan 需要 --kind 與 --batch')
        if args.action != 'scan' and not args.id:
            parser.error('此匯入操作需要 --id')
        if args.action == 'scan':
            result = service.preview(ROOT, args.kind, args.batch)
        elif args.action == 'status':
            result = service.load(ROOT, args.id)
        else:
            result = service.commit(ROOT, args.id, args.key or ('import:' + args.id), retry=args.action == 'retry')
        print(json.dumps(service.public(result, args.page, args.size), ensure_ascii=False, indent=2))
        return 1 if result['state'] == 'failed' else 0
    if args.command == "workbench":
        import uvicorn
        from src.workbench.api import create_app

        uvicorn.run(create_app(), host="127.0.0.1", port=args.port, access_log=False)
        return 0
    elif args.command == "doctor":
        from src.environment import environment

        result = environment()
        from src.workspace_check import check, summary_lines

        result["workspace"] = check()
        print("工作區檢查：", *summary_lines(result["workspace"]), "", sep="\n", file=sys.stderr)
        write_json(EVIDENCE_DIR / "environment.json", result)
    elif args.command == "migrate-tasks":
        from src.data.area_migration import migrate_single_area
        from src.data.source_rules import apply_authorized_rules, prefill_named_files

        result = {
            'areas': migrate_single_area(),
            'rules': apply_authorized_rules()['summary'],
            'prefilled_other_named_files': prefill_named_files(),
        }
    elif args.command == "audit":
        from src.data.dataset import audit

        result = audit()
        write_json(ROOT / "data/audit_report.json", result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return int(bool(result["errors"]))
    elif args.command == "build":
        from src.data.dataset import build

        info = build(demo=args.demo, task=args.task, folds=args.folds, repeats=args.repeats)
        result = {
            "version": info["version"],
            "task": info["task"],
            "demo_only": info["demo_only"],
            "folds": [
                {"dataset": f["dataset"], "train": len(f["members"]["train"]), "val": len(f["members"]["val"])}
                for f in info["folds"]
            ],
        }
    elif args.command == "review":
        from src.data.dataset import review

        result = review(
            args.image_id,
            status=args.status,
            label=args.label,
            reviewer=args.reviewer,
            reason=args.reason,
            subject_id=args.subject_id,
            category=args.category,
        )
    elif args.command == "predict":
        from src.inference.engine import InvalidImage
        from src.lock import OperationLock
        from src.workbench.adapters import ModelPredictor

        source = Path(args.source).resolve()
        inputs = (
            [source]
            if source.is_file()
            else sorted(p for p in source.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"})
        )
        if not inputs:
            raise ValueError("No supported images found")
        reference = ROOT / "models/references/local.json"
        if not reference.exists():
            raise ValueError("尚未指定本地模擬模型；請先在工作台「模型版本」啟用。")
        out = ROOT / "runs" / ("prediction_" + stamp())
        out.mkdir(parents=True)
        records = []
        with OperationLock():
            predictor = ModelPredictor(read_json(reference)["artifact"], args.device)
            if predictor.metadata.get("demo_only") and not args.allow_demo:
                raise ValueError("這是研究展示模型，需要加上 --allow-demo。")
            for path in inputs:
                try:
                    record, _ = predictor.predict(path.read_bytes())
                except InvalidImage as exc:
                    record = {"status": "invalid_image", "message": str(exc)}
                record["source"] = path.name
                records.append(record)
        write_json(out / "results.json", records)
        lines = [
            "# 本地影像分析結果",
            "",
            "整張照片分類的研究展示。分數未校準，不是疾病機率，也不能用作嚴重度分級；未達門檻不代表排除。",
            "",
            "此批包含手動輸入的照片，並非獨立效能評估。",
            "",
            "| 編號 | 結果 | 模型分數 |",
            "|---|---|---|",
        ]
        labels = {
            "suspected": "達到陽性門檻",
            "not_detected": "未達陽性門檻",
            "quality_rejected": "照片品質不足",
            "invalid_image": "無法讀取",
        }
        for n, record in enumerate(records):
            score = record.get("prediction_score")
            shown = "" if score is None else f"{score:.3f}"
            lines.append(f"| {n+1} | {labels.get(record['status'], record['status'])} | {shown} |")
        (out / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        result = {"output": str(out.relative_to(ROOT)), "images": len(records)}
    elif args.command == "serve":
        import uvicorn
        from src.line_bot.service import create_app

        uvicorn.run(create_app(), host="127.0.0.1", port=args.port, log_level="warning", access_log=False)
        return 0
    elif args.command == "menu":
        from src.line_bot.menu import prepare, publish

        result = publish() if args.publish else prepare()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError, FileNotFoundError) as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        raise SystemExit(1)
