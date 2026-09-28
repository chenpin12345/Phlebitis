"""Local phlebitis research demonstration. No clinical severity inference."""
import os
from pathlib import Path
_config = Path(__file__).resolve().parents[1] / "runtime" / "ultralytics"
(_config / "Ultralytics").mkdir(parents=True, exist_ok=True)
os.environ.setdefault("YOLO_CONFIG_DIR", str(_config))
os.environ.setdefault("YOLO_AUTOINSTALL", "false")
