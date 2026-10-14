from src.common import ROOT


def yolo_api():
    from ultralytics import YOLO, settings
    settings.update({
        "sync": False, "clearml": False, "comet": False, "dvc": False,
        "mlflow": False, "raytune": False, "wandb": False, "tensorboard": False,
        "datasets_dir": str(ROOT / "data/yolo"),
        "weights_dir": str(ROOT / "models/pretrained"),
        "runs_dir": str(ROOT / "runs")
    })
    return YOLO
