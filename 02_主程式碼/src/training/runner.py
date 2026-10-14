from __future__ import annotations

import importlib.metadata
import json
import subprocess
import sys
from pathlib import Path

from src.common import ROOT, inside, read_json, sha256, stamp, write_json
from src.data.dataset import validate_split


def environment() -> dict:
    import torch
    info = {"python": sys.version, "torch": torch.__version__, "cuda_runtime": torch.version.cuda, "cuda_available": torch.cuda.is_available()}
    if info["cuda_available"]:
        info.update(gpu=torch.cuda.get_device_name(0), vram_bytes=torch.cuda.get_device_properties(0).total_memory)
        x = torch.ones((128, 128), device="cuda")
        info["gpu_compute_ok"] = bool((x @ x).mean().item() == 128)
        del x
    for name in ["ultralytics","torchvision","fastapi","httpx","Pillow","numpy"]:
        try: info[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: info[name] = None
    return info


def train(dataset: Path, *, config: Path, epochs: int | None = None, batch: int | None = None, device: str = "0", demo: bool = False, no_color: bool = False, resume: Path | None = None) -> Path:
    from src.model_api import yolo_api
    YOLO = yolo_api()
    import torch
    from src.lock import OperationLock
    split = validate_split(dataset)
    if split["demo_only"] and not demo:
        raise ValueError("Unverified patient identities: pass --demo explicitly; this is not formal validation.")
    if device != "cpu" and not torch.cuda.is_available():
        raise ValueError("CUDA unavailable. Install the GPU environment or explicitly choose --device cpu.")
    cfg = read_json(config)
    cfg.update(data=str(dataset.resolve()), device=device)
    if epochs is not None: cfg["epochs"] = epochs
    if batch is not None: cfg["batch"] = batch
    if no_color: cfg.update(hsv_h=0.0, hsv_s=0.0, hsv_v=0.0)
    if device == "cpu": cfg["amp"] = False
    base = inside(cfg.pop("model"))
    if base.name != "yolo11n.pt":
        raise ValueError("This project is fixed to YOLO11n.")
    with OperationLock():
        from src.workbench.resources import check_managed_path
        check_managed_path(base)
        if resume:
            resume = inside(resume)
            check_managed_path(resume)
            out = resume.parent.parent
            record = read_json(out / "experiment.json")
            if record["split"]["manifest_digest"] != split["manifest_digest"]:
                raise ValueError("Resume requires the original dataset manifest")
            if inside(record["dataset"]).resolve() != dataset.resolve():
                raise ValueError("Resume requires the exact original fold")
            if not resume.is_file():
                raise ValueError("Checkpoint does not exist")
            model = YOLO(str(resume))
            record.update(status="running")
            write_json(out / "experiment.json", record)
            try:
                model.train(resume=True, device=device, workers=0)
            except BaseException as exc:
                record.update(status="interrupted_or_failed", error_type=type(exc).__name__)
                write_json(out / "experiment.json", record)
                raise
        else:
            name = ("demo_" if demo else "train_") + ("no_color_" if no_color else "baseline_") + stamp()
            out = ROOT / "runs" / name
            out.mkdir(parents=True)
            record = {"model_family":"YOLO11n", "created_at":stamp(), "demo_only":bool(split["demo_only"]), "dataset":dataset.relative_to(ROOT).as_posix(), "split":split, "parameters":cfg, "base_weight_sha256":sha256(base), "environment":environment(), "status":"running"}
            write_json(out / "experiment.json", record)
            freeze = subprocess.check_output([sys.executable,"-m","pip","freeze"],text=True)
            (out / "requirements.freeze.txt").write_text(freeze,encoding="utf-8")
            model = YOLO(str(base))
            try:
                model.train(**cfg, project=str(ROOT/"runs"), name=name, exist_ok=True)
            except BaseException as exc:
                record.update(status="interrupted_or_failed", error_type=type(exc).__name__)
                write_json(out / "experiment.json",record)
                raise
        record.update(status="completed")
        write_json(out / "experiment.json",record)
        return out


def evaluate(weights: Path, dataset: Path, *, device: str = "0", confidence: float = 0.5, imgsz: int = 640, iou: float = .7) -> Path:
    import math
    import torch
    from src.model_api import yolo_api
    YOLO = yolo_api()
    from src.inference.engine import validate_model
    from src.lock import OperationLock
    split=validate_split(dataset)
    from src.workbench.contracts import InferenceConfig
    inference=InferenceConfig(threshold=confidence,imgsz=imgsz,iou=iou)
    weights=inside(weights)
    out=ROOT/"runs"/("evaluation_"+stamp())
    out.mkdir(parents=True)
    if device != "cpu" and not torch.cuda.is_available():
        raise ValueError("CUDA unavailable; CPU must be requested explicitly")
    with OperationLock():
        from src.workbench.resources import check_managed_path
        check_managed_path(weights)
        model=YOLO(str(weights))
        validate_model(model)
        metrics=model.val(data=str(dataset),device=device,imgsz=inference.imgsz,batch=4,workers=0,conf=0.001,iou=inference.iou,plots=True,project=str(out),name="validation")
        samples=[]
        errors=out/"error_examples"
        errors.mkdir()
        for item in split["members"]["val"]:
            image=inside(item["image_path"])
            result=model.predict(str(image),device=device,imgsz=inference.imgsz,conf=inference.threshold,iou=inference.iou,verbose=False)[0]
            detected=len(result.boxes)>0
            truth=item["label_state"]=="positive"
            record={"image_id":item["image_id"],"group":item["group"],"true_positive_image":truth,"detected":detected,"boxes":len(result.boxes),"inference_ms":float(result.speed.get("inference",0))}
            samples.append(record)
            if truth!=detected:
                result.save(filename=str(errors/(item["image_id"]+".jpg")))
        tp=sum(x["true_positive_image"] and x["detected"] for x in samples)
        fn=sum(x["true_positive_image"] and not x["detected"] for x in samples)
        fp=sum(not x["true_positive_image"] and x["detected"] for x in samples)
        tn=sum(not x["true_positive_image"] and not x["detected"] for x in samples)
        values={k:float(v) for k,v in metrics.results_dict.items() if isinstance(v,(int,float)) and math.isfinite(float(v))}
        report={"demo_only":split["demo_only"],"note":"Validation fold only; image-level presence metrics do not measure box localization.", "weights_sha256":sha256(weights),"dataset":str(dataset),"confidence":confidence,"detection_metrics":values,"image_level":{"tp":tp,"fn":fn,"fp":fp,"tn":tn,"sensitivity":tp/(tp+fn) if tp+fn else None,"normal_image_false_positive_rate":fp/(fp+tn) if fp+tn else None},"images":samples}
        report['inference_config']=inference.model_dump()
        write_json(out/"evaluation.json",report)
        (out/"README.md").write_text("# 評估紀錄\n\n"+("此資料使用未確認的個案代碼，只能供流程展示，不能視為正式臨床評估。\n\n" if split["demo_only"] else "此為分組驗證結果，並非獨立臨床測試。\n\n")+"詳細結果見 evaluation.json；漏報及正常影像誤報見 error_examples；定位、PR 與混淆矩陣见 validation。\n",encoding="utf-8")
        return out


def select(weights: Path, evaluation: Path, confidence: float = 0.5) -> dict:
    import shutil
    from src.lock import OperationLock
    weights,evaluation=inside(weights),inside(evaluation)
    if (ROOT/'models/references/line.json').exists():
        raise ValueError('LINE reference is managed by the workbench. Use its explicit model activation action; CLI selection will not overwrite it.')
    experiment=read_json(weights.parent.parent/"experiment.json")
    report=read_json(evaluation/"evaluation.json")
    if report["weights_sha256"]!=sha256(weights):
        raise ValueError("Evaluation belongs to a different checkpoint")
    if experiment.get("model_family")!="YOLO11n" or not 0<confidence<1:
        raise ValueError("Invalid model or confidence")
    if experiment.get("status") != "completed":
        raise ValueError("Select only a completed training run")
    if report.get("confidence") != confidence:
        raise ValueError("Selection confidence must match the evaluation threshold")
    if inside(report["dataset"]) != inside(experiment["dataset"]):
        raise ValueError("Evaluation must use the training run validation fold")
    validate_split(inside(experiment["dataset"]))
    with OperationLock():
        from src.workbench.resources import check_managed_path
        check_managed_path(weights)
        selected=ROOT/"models/selected"
        selected.mkdir(parents=True,exist_ok=True)
        metadata={"model_family":"YOLO11n","model_version":weights.parent.parent.name,"weights_sha256":sha256(weights),"confidence":confidence,"demo_only":experiment["demo_only"],"evaluation":str(evaluation.relative_to(ROOT)),"selected_at":stamp(),"severity_supported":False}
        version=ROOT/'models/legacy_versions'/stamp()
        version.mkdir(parents=True)
        shutil.copy2(weights,version/'best.pt')
        metadata['inference_config']=report.get('inference_config',{'imgsz':640,'iou':.7,'threshold':confidence})
        write_json(version/'metadata.json',metadata)
        shutil.copy2(evaluation/'evaluation.json',version/'evaluation.json')
        write_json(selected/'reference.json',{'weights':(version/'best.pt').relative_to(ROOT).as_posix()})
        return metadata
