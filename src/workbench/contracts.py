from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

MODELS = {
    'yolo11n': {'name':'YOLO11n', 'task':'detection', 'source':'https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo11n.pt'},
    'yolo11s': {'name':'YOLO11s', 'task':'detection', 'source':'https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo11s.pt'},
    'yolo26s': {'name':'YOLO26s', 'task':'detection', 'source':'https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26s.pt'},
    'efficientnet_b0': {'name':'EfficientNet-B0', 'task':'classification', 'source':'https://download.pytorch.org/models/efficientnet_b0_rwightman-7f5810bc.pth'},
    'dinov2_small': {'name':'DINOv2 ViT-S/14 + Logistic Regression', 'task':'classification', 'source':'facebook/dinov2-small'},
}

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)

class InferenceConfig(Strict):
    version: int = 1
    imgsz: int = Field(640, ge=64, le=1536)
    threshold: float = Field(.5, gt=0, lt=1)
    candidate_threshold: float = Field(.1, gt=0, lt=1)
    iou: float = Field(.7, gt=0, lt=1)
    preprocess: str = 'ultralytics-letterbox-v1'
    postprocess: Literal['nms','end2end'] = 'nms'
    label_mapping: dict[str, int] = {'negative':0, 'positive':1}
    review_low_confidence: bool = False
    quality_mode: Literal['advisory','reject'] = 'advisory'
    blur_threshold: float = Field(30, ge=0)
    dark_fraction: float = Field(.85, ge=0, le=1)
    bright_fraction: float = Field(.85, ge=0, le=1)

    @model_validator(mode='after')
    def check(self):
        if self.label_mapping!={'negative':0,'positive':1}:raise ValueError('This binary task requires negative=0, positive=1')
        return self

class Experiment(Strict):
    model: Literal['yolo11n','yolo11s','yolo26s','efficientnet_b0','dinov2_small']
    dataset: str
    device: Literal['0','cpu'] = '0'
    demo: bool = False
    epochs: int = Field(120, ge=1, le=500)
    batch: int = Field(4, ge=1, le=64)
    seed: int = Field(42, ge=0, le=2147483647)
    patience: int = Field(25, ge=0, le=100)
    imgsz: int = Field(640, ge=64, le=1536)
    parameters: dict = {}
    inference: InferenceConfig = InferenceConfig()
    resume_job: str | None = None
    initial_artifact: str | None = None
    allow_amp_check_download: bool = False

    @model_validator(mode='after')
    def capabilities(self):
        yolo = {'optimizer','lr0','lrf','momentum','weight_decay','warmup_epochs','warmup_momentum','warmup_bias_lr','cos_lr','freeze','amp','workers','cache','deterministic','degrees','translate','scale','shear','perspective','hsv_h','hsv_s','hsv_v','mosaic','mixup','fliplr','flipud','box','cls','nbs'}
        if self.model != 'yolo26s': yolo.add('dfl')
        efficient = {'learning_rate','optimizer','weight_decay','scheduler','freeze','class_weight','flip','rotation'}
        dino = {'C','solver','max_iter','class_weight','standardize'}
        allowed = yolo if self.model.startswith('yolo') else efficient if self.model == 'efficientnet_b0' else dino
        bad = set(self.parameters) - allowed
        if bad: raise ValueError(f'Unsupported parameters: {sorted(bad)}')
        p = self.parameters
        import math
        if any(isinstance(v,float) and not math.isfinite(v) for v in p.values()):raise ValueError('Parameters must be finite')
        if self.model.startswith('yolo'):
            if self.inference.candidate_threshold>self.inference.threshold:raise ValueError('Candidate threshold cannot exceed acceptance threshold')
            if self.model!='yolo26s' and self.inference.postprocess!='nms':raise ValueError('NMS-free inference is only supported by YOLO26s')
            if self.imgsz%32 or self.inference.imgsz%32:raise ValueError('YOLO input size must be a multiple of 32')
            if self.inference.preprocess!='ultralytics-letterbox-v1':raise ValueError('Unsupported YOLO preprocessing')
            for key,value in p.items():
                if key in {'optimizer','cache'}:continue
                if key in {'amp','cos_lr','deterministic'}:
                    if not isinstance(value,bool):raise ValueError(f'{key} must be boolean')
                elif key in {'freeze','workers','nbs'}:
                    if not isinstance(value,int) or value<0:raise ValueError(f'{key} must be a nonnegative integer')
                elif not isinstance(value,(int,float)) or value<0 or value>1e5:raise ValueError(f'Invalid numeric {key}')
            if p.get('optimizer','auto') not in {'auto','SGD','Adam','AdamW','NAdam','RAdam','RMSProp'}:raise ValueError('Unsupported YOLO optimizer')
            if p.get('cache',False) not in (False,True,'ram','disk'):raise ValueError('Unsupported cache mode')
            for key in ('fliplr','flipud','mosaic','mixup','hsv_h','hsv_s','hsv_v','translate','perspective'):
                if key in p and not 0<=p[key]<=1:raise ValueError(f'{key} must be 0..1')
            if p.get('optimizer','auto') == 'auto' and {'lr0','momentum'} & set(p):
                raise ValueError('optimizer=auto ignores lr0/momentum; select a manual optimizer')
            if p.get('amp',False) and not self.allow_amp_check_download:raise ValueError('AMP requires explicit acknowledgement: framework may download YOLO26n for its check only, not as the training model')
            if not 0<=p.get('workers',0)<=4:raise ValueError('workers must be 0..4 on this local workbench')
            if p.get('nbs',64)<1:raise ValueError('nbs must be positive')
        elif self.model == 'efficientnet_b0':
            if p.get('optimizer','AdamW') not in {'AdamW','SGD'}: raise ValueError('Unsupported optimizer')
            if p.get('freeze','backbone') not in {'backbone','last_stage'}: raise ValueError('Unsupported freeze strategy')
            if p.get('scheduler','none') not in {'none','cosine'}: raise ValueError('Unsupported scheduler')
            for key in ('learning_rate','weight_decay','rotation'):
                if key in p and (not isinstance(p[key], (int,float)) or p[key] < 0): raise ValueError(f'Invalid {key}')
            if p.get('learning_rate',.001)<=0 or p.get('rotation',0)>45:raise ValueError('learning_rate must be positive; rotation must be <=45 degrees')
            if 'flip' in p and not isinstance(p['flip'],bool):raise ValueError('flip must be boolean')
        else:
            if self.initial_artifact:raise ValueError('DINOv2 keeps its official frozen backbone; start a fresh classifier fit')
            if self.resume_job: raise ValueError('Logistic regression has no checkpoint resume; create a new fit')
            if p.get('solver','lbfgs') not in {'lbfgs','liblinear'}: raise ValueError('Supported solvers: lbfgs, liblinear')
            if not 0 < float(p.get('C',1)) <= 10000: raise ValueError('C must be in (0,10000]')
            if not 1 <= int(p.get('max_iter',200)) <= 2000: raise ValueError('max_iter must be 1..2000')
            if not isinstance(p.get('max_iter',200),int):raise ValueError('max_iter must be an integer')
            if not isinstance(p.get('C',1),(int,float)):raise ValueError('C must be numeric')
            if 'standardize' in p and not isinstance(p['standardize'],bool):raise ValueError('standardize must be boolean')
        if not self.model.startswith('yolo'):
            if 'epochs' not in self.model_fields_set:self.epochs=20
            if 'patience' not in self.model_fields_set:self.patience=5
            if p.get('class_weight') not in (None,'balanced'): raise ValueError('class_weight must be null or balanced')
            self.imgsz = 224
            self.inference.imgsz = 224
            self.inference.preprocess = 'rgb-letterbox224-imagenet-v1'
        if self.resume_job and self.initial_artifact: raise ValueError('Resume and new fine-tuning are different operations')
        return self

class Review(Strict):
    revision: str
    status: Literal['approved','pending_review','excluded']
    label: Literal['positive','negative','unknown']
    reviewer: str = Field(min_length=1, max_length=100)
    reason: str = Field(min_length=1, max_length=1000)
    subject_id: str = Field('', max_length=100)
    clear_subject: bool = False
    category: str = ''
    boxes: list[list[float]] = []

class SnapshotRequest(Strict):
    demo: bool = False
    folds: int = Field(3, ge=2, le=10)
    seed: int = Field(42, ge=0)

class SwitchRequest(Strict):
    artifact: str
    target: Literal['local','line'] = 'local'
    allow_unevaluated: bool = False
