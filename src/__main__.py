from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from src.common import ROOT, inside, read_json, stamp, write_json


def main():
    parser=argparse.ArgumentParser(description="靜脈炎研究展示：YOLO11n 本地訓練與 LINE")
    sub=parser.add_subparsers(dest="command",required=True)
    sub.add_parser("doctor",help="檢查 GPU 與套件版本")
    p=sub.add_parser("workbench",help="啟動本地研究網頁工作台");p.add_argument("--port",type=int,default=8765)
    sub.add_parser("migrate",help="整理原始專案並保存封存副本")
    sub.add_parser("audit",help="檢查資料清單與標註")
    p=sub.add_parser("build",help="建立三折個案分組資料集");p.add_argument("--demo",action="store_true",help="允許未確認個案代碼，只供流程展示")
    p=sub.add_parser("review",help="人工確認資料狀態並同步搬移檔案")
    p.add_argument("image_id");p.add_argument("--status",required=True,choices=["approved","pending_review","excluded"]);p.add_argument("--label",required=True,choices=["positive","negative","unknown"])
    p.add_argument("--reviewer",required=True);p.add_argument("--reason",required=True);p.add_argument("--subject-id",default="");p.add_argument("--annotation",default="");p.add_argument("--category",default="",help="隔離原因子目錄：blurry、unclear、unreadable、other；待確認可用 annotation、unknown_source、duplicate_variant")
    p=sub.add_parser("train",help="本地訓練或續訓")
    p.add_argument("--dataset");p.add_argument("--fold",type=int,choices=[0,1,2],default=0);p.add_argument("--config",default="configs/train.json")
    p.add_argument("--epochs",type=int);p.add_argument("--batch",type=int);p.add_argument("--device",default="0");p.add_argument("--demo",action="store_true");p.add_argument("--no-color",action="store_true");p.add_argument("--resume")
    p=sub.add_parser("evaluate",help="輸出驗證指標與誤判案例")
    p.add_argument("--weights",required=True);p.add_argument("--dataset");p.add_argument("--fold",type=int,choices=[0,1,2],default=0);p.add_argument("--device",default="0");p.add_argument("--confidence",type=float,default=0.5)
    p.add_argument('--imgsz',type=int,default=640);p.add_argument('--iou',type=float,default=.7)
    p=sub.add_parser("select",help="指定 LINE 展示模型")
    p.add_argument("--weights",required=True);p.add_argument("--evaluation",required=True);p.add_argument("--confidence",type=float,default=0.5)
    p=sub.add_parser("predict",help="分析一張圖片或一個資料夾")
    p.add_argument("source");p.add_argument("--device",default="0");p.add_argument("--allow-demo",action="store_true")
    p=sub.add_parser("serve",help="啟動本地 LINE webhook");p.add_argument("--port",type=int,default=8000)
    p=sub.add_parser("menu",help="產生 LINE 圖文選單素材；只有 --publish 才寫入帳號");p.add_argument("--publish",action="store_true")
    args=parser.parse_args()
    os.chdir(ROOT)
    if args.command=="workbench":
        import uvicorn
        from src.workbench.api import create_app
        uvicorn.run(create_app(),host="127.0.0.1",port=args.port,access_log=False)
        return 0
    elif args.command=="doctor":
        from src.training.runner import environment
        result=environment()
        write_json(ROOT/"docs/environment.json",result)
    elif args.command=="migrate":
        from src.data.migrate import migrate
        result=migrate()
    elif args.command=="audit":
        from src.data.dataset import audit
        result=audit();write_json(ROOT/"data/audit_report.json",result)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return int(bool(result["errors"]))
    elif args.command=="build":
        from src.data.dataset import build
        info=build(demo=args.demo)
        result={"version":info["version"],"demo_only":info["demo_only"],"folds":[{"dataset":f["dataset"],"train":len(f["members"]["train"]),"val":len(f["members"]["val"])} for f in info["folds"]]}
    elif args.command=="review":
        from src.data.dataset import review
        result=review(args.image_id,status=args.status,label=args.label,reviewer=args.reviewer,reason=args.reason,subject_id=args.subject_id,annotation=args.annotation,category=args.category)
    elif args.command in {"train","evaluate"}:
        from src.data.dataset import latest_dataset
        from src.training.runner import train,evaluate
        if args.dataset: dataset=inside(args.dataset)
        elif args.command=="train" and args.resume:
            checkpoint=inside(args.resume)
            dataset=inside(read_json(checkpoint.parent.parent/"experiment.json")["dataset"])
        else: dataset=latest_dataset(args.fold)
        if args.command=="train":
            out=train(dataset,config=inside(args.config),epochs=args.epochs,batch=args.batch,device=args.device,demo=args.demo,no_color=args.no_color,resume=inside(args.resume) if args.resume else None)
        else:
            if not 0<args.confidence<1:raise ValueError("Confidence must be between 0 and 1")
            out=evaluate(inside(args.weights),dataset,device=args.device,confidence=args.confidence,imgsz=args.imgsz,iou=args.iou)
        result={"output":out.relative_to(ROOT).as_posix()}
    elif args.command=="select":
        from src.training.runner import select
        result=select(inside(args.weights),inside(args.evaluation),args.confidence)
    elif args.command=="predict":
        from src.inference.engine import Predictor,InvalidImage
        from src.lock import OperationLock
        source=Path(args.source).resolve()
        inputs=[source] if source.is_file() else sorted(p for p in source.iterdir() if p.suffix.lower() in {".jpg",".jpeg",".png",".webp"})
        if not inputs:raise ValueError("No supported images found")
        out=ROOT/"runs"/("prediction_"+stamp());out.mkdir(parents=True)
        records=[]
        with OperationLock():
            predictor=Predictor(ROOT/"models/selected/best.pt",device=args.device,allow_demo=args.allow_demo)
            for n,path in enumerate(inputs):
                try:
                    record,jpeg=predictor.predict(path.read_bytes())
                    (out/f"{n:04d}.jpg").write_bytes(jpeg)
                    record["annotated_image"]=f"{n:04d}.jpg"
                except InvalidImage as exc:record={"status":"invalid_image","message":str(exc)}
                record["source"]=path.name;records.append(record)
        write_json(out/"results.json",records)
        lines=["# 本地影像分析結果", "", "YOLO11n 研究展示。疑似區域與信心分數不能用作嚴重度分級；未偵測到不代表排除疾病。", "",
               "此批包含手動輸入的照片，並非獨立效能評估。框座標在 JSON 中對應原圖尺寸。", "",
               "| 編號 | 結果 | 疑似區域數 | 框選圖片 |", "|---|---|---|---|"]
        labels={"suspected":"偵測到疑似區域","not_detected":"未偵測到疑似區域","invalid_image":"圖片無法讀取"}
        for n,record in enumerate(records):
            picture=f"[開啟圖片]({record['annotated_image']})" if "annotated_image" in record else "無"
            lines.append(f"| {n+1} | {labels[record['status']]} | {len(record.get('boxes',[]))} | {picture} |")
        (out/"README.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
        result={"output":str(out.relative_to(ROOT)),"images":len(records)}
    elif args.command=="serve":
        import uvicorn
        from src.line_bot.service import create_app
        uvicorn.run(create_app(),host="127.0.0.1",port=args.port,log_level="warning",access_log=False)
        return 0
    elif args.command=="menu":
        from src.line_bot.menu import prepare,publish
        result=publish() if args.publish else prepare()
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0


if __name__=="__main__":
    if hasattr(sys.stdout,"reconfigure"):sys.stdout.reconfigure(encoding="utf-8")
    try:
        raise SystemExit(main())
    except (ValueError,RuntimeError,FileNotFoundError) as exc:
        print(f"錯誤：{exc}",file=sys.stderr)
        raise SystemExit(1)
