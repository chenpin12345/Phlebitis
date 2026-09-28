from __future__ import annotations

import io
import time
import warnings
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError
from src.common import ROOT, read_json, sha256


class InvalidImage(ValueError):
    pass


def decode_image(content: bytes, config: dict):
    if not content or len(content)>config["max_image_bytes"]:
        raise InvalidImage("圖片為空或超過 10 MB，請重新傳送較小的照片。")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error",Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content)) as im:
                if im.format not in config["allowed_formats"]:
                    raise InvalidImage("請使用 JPEG、PNG 或 WEBP 圖片。")
                if im.width*im.height>config["max_image_pixels"] or min(im.size)<64:
                    raise InvalidImage("圖片尺寸不合適，請重新拍攝或縮小圖片。")
                im.load()
                return ImageOps.exif_transpose(im).convert("RGB")
    except InvalidImage:
        raise
    except (OSError,UnidentifiedImageError,Image.DecompressionBombError,Image.DecompressionBombWarning,ValueError) as exc:
        raise InvalidImage("無法讀取圖片，請重新傳送照片。") from exc


def encode_result(image):
    """Bound the annotated JPEG below LINE's 1 MB preview limit."""
    image = image.copy()
    image.thumbnail((1600,1600), Image.Resampling.LANCZOS)
    while True:
        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=85, optimize=True)
        content = buf.getvalue()
        if len(content) <= 900000:
            return content, image.size
        image.thumbnail((max(1,image.width*3//4),max(1,image.height*3//4)), Image.Resampling.LANCZOS)


def validate_model(model):
    names=model.names
    ordered=list(names.values()) if isinstance(names,dict) else list(names)
    if ordered!=["phlebitis"]:
        raise ValueError("A trained single-class phlebitis model is required; generic YOLO weights cannot be used.")


class Predictor:
    def __new__(cls,weights:Path,*,device:str="cpu",allow_demo:bool=False):
        reference=ROOT/'models/references/line.json'
        if reference.exists() and weights.resolve()==(ROOT/'models/selected/best.pt').resolve():
            from src.workbench.registry import get
            from src.workbench.adapters import ModelPredictor
            ident=read_json(reference)['artifact']
            metadata=get(ident)
            if metadata.get('demo_only') and not allow_demo:
                raise ValueError('Demonstration model requires explicit allow_demo')
            return ModelPredictor(ident,device)
        return super().__new__(cls)

    def __init__(self,weights:Path,*,device:str="cpu",allow_demo:bool=False):
        from src.model_api import yolo_api
        YOLO = yolo_api()
        import torch
        self.config=read_json(ROOT/"configs/service.json")
        reference=weights.parent/'reference.json'
        if reference.exists():
            from src.common import inside
            weights=inside(read_json(reference)['weights'])
        if not weights.is_file():
            raise ValueError("Selected weights are missing. Train, evaluate and select a model first.")
        self.metadata=read_json(weights.parent/"metadata.json")
        if self.metadata.get('inference_config'):
            config=self.metadata['inference_config']
            self.config.update(imgsz=config['imgsz'],iou=config['iou'],confidence=config['threshold'])
        if self.metadata.get("model_family")!="YOLO11n" or sha256(weights)!=self.metadata["weights_sha256"]:
            raise ValueError("Model identity/hash mismatch")
        if self.metadata.get("demo_only") and not allow_demo:
            raise ValueError("This is a demonstration-only model. Explicitly enable DEMO_MODEL_ALLOWED for a research demo.")
        if device!="cpu" and not torch.cuda.is_available():
            raise ValueError("CUDA unavailable")
        self.device=device
        self.model=YOLO(str(weights))
        validate_model(self.model)

    def predict(self,content:bytes):
        start=time.perf_counter()
        image=decode_image(content,self.config)
        confidence=float(self.metadata.get("confidence",self.config["confidence"]))
        result=self.model.predict(image,device=self.device,imgsz=self.config["imgsz"],conf=confidence,iou=self.config["iou"],verbose=False)[0]
        boxes=[{"xyxy":[round(float(v),2) for v in b.xyxy[0].tolist()],"confidence":round(float(b.conf.item()),4),"class":"phlebitis"} for b in result.boxes]
        # plot() returns BGR; re-encoding strips original EXIF and never persists the raw image.
        annotated=Image.fromarray(result.plot()[:,:,::-1])
        jpeg,output_size=encode_result(annotated)
        record={"status":"suspected" if boxes else "not_detected","boxes":boxes,"model_version":self.metadata["model_version"],"demo_only":bool(self.metadata.get("demo_only")),"severity":None,"elapsed_ms":round((time.perf_counter()-start)*1000,1),"source_size":list(image.size),"annotated_size":list(output_size),"box_coordinates":"source_size pixels"}
        return record,jpeg
