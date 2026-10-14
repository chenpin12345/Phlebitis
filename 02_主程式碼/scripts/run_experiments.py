"""Run the planned YOLO11n comparison on all three folds, locally."""
from pathlib import Path
import argparse
import csv
import statistics
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.common import ROOT, read_json, write_json, stamp, config_path
from src.data.dataset import latest_dataset
from src.training.runner import train, evaluate, select

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--epochs", type=int, default=120)
    args=parser.parse_args()
    datasets=[latest_dataset(i) for i in range(3)]
    summary={"created_at":stamp(), "demo_only":args.demo, "model_family":"YOLO11n",
             "selection_rule":"Predeclared fold 0 only: highest validation mAP50-95; ties use lower normal-image false-positive rate. Other folds describe variability. No independent test set.",
             "experiments":[]}
    output=ROOT/"runs"/("comparison_"+stamp())
    output.mkdir(parents=True)
    write_json(ROOT/"runs/latest_comparison.json", {"directory":output.relative_to(ROOT).as_posix()})
    for fold,dataset in enumerate(datasets):
        for no_color in (False,True):
            run=train(dataset, config=config_path("train.json"), epochs=args.epochs,
                      demo=args.demo, no_color=no_color)
            ev=evaluate(run/"weights/best.pt",dataset)
            report=read_json(ev/"evaluation.json")
            with (run/"results.csv").open() as f:
                epochs=list(csv.DictReader(f))
            entry={"fold":fold,"variant":"no_color" if no_color else "baseline",
                   "run":run.relative_to(ROOT).as_posix(),
                   "evaluation":ev.relative_to(ROOT).as_posix(),
                   "completed_epochs":len(epochs), "metrics":report["detection_metrics"],
                   "image_level":report["image_level"]}
            summary["experiments"].append(entry)
            write_json(output/"comparison.json",summary)
            print("COMPLETED",fold,entry["variant"],entry["metrics"],flush=True)
    summary["aggregate"]={}
    for variant in ("baseline","no_color"):
        entries=[e for e in summary["experiments"] if e["variant"]==variant]
        keys=entries[0]["metrics"]
        summary["aggregate"][variant]={k:{"mean":statistics.mean(e["metrics"][k] for e in entries),
              "std_across_folds":statistics.pstdev(e["metrics"][k] for e in entries)} for k in keys}
    candidates=[e for e in summary["experiments"] if e["fold"]==0]
    chosen=max(candidates,key=lambda e:(e["metrics"].get("metrics/mAP50-95(B)",0),
              -(e["image_level"]["normal_image_false_positive_rate"] or 0)))
    summary["recommended"]=chosen
    summary["activation_required"]=True
    write_json(output/"comparison.json",summary)
    print("SUMMARY",output.relative_to(ROOT),flush=True)

if __name__=="__main__":
    main()
