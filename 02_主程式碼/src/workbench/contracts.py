from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MODELS = {
    'efficientnet_b0': {
        'name': 'EfficientNet-B0',
        'task': 'classification',
        'source': 'https://download.pytorch.org/models/efficientnet_b0_rwightman-7f5810bc.pth',
    },
    'dinov2_small': {
        'name': 'DINOv2 ViT-S/14 + Logistic Regression',
        'task': 'classification',
        'source': 'facebook/dinov2-small',
    },
    'dinov2_base': {
        'name': 'DINOv2 ViT-B/14 + Logistic Regression',
        'task': 'classification',
        'source': 'facebook/dinov2-base',
    },
    'baseline_majority': {'name': '基線：多數類', 'task': 'classification', 'source': '', 'baseline': True},
    'baseline_colour': {'name': '基線：色彩直方圖', 'task': 'classification', 'source': '', 'baseline': True},
    'baseline_dino_knn': {'name': '基線：DINOv2 最近鄰', 'task': 'classification', 'source': '', 'baseline': True},
}
BASELINES = {key for key, value in MODELS.items() if value.get('baseline')}


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


class InferenceConfig(Strict):
    version: int = 1
    imgsz: int = Field(224, ge=64, le=1536)
    threshold: float = Field(0.5, gt=0, lt=1)
    # candidate_threshold, iou and postprocess no longer do anything; saved model configs still
    # carry them, and this model rejects unknown fields.
    candidate_threshold: float = Field(0.1, gt=0, lt=1)
    iou: float = Field(0.7, gt=0, lt=1)
    preprocess: str = 'rgb-letterbox224-imagenet-v1'
    postprocess: Literal['nms', 'end2end'] = 'nms'
    label_mapping: dict[str, int] = {'negative': 0, 'positive': 1}
    review_low_confidence: bool = False
    quality_mode: Literal['advisory', 'reject'] = 'advisory'
    blur_threshold: float = Field(30, ge=0)
    dark_fraction: float = Field(0.85, ge=0, le=1)
    bright_fraction: float = Field(0.85, ge=0, le=1)
    # None = legacy binary_v1. Stored only when set, so old configs dump unchanged.
    label_scheme: Literal['binary_v1', 'stage_v1'] | None = None

    def model_dump(self, *args, **kwargs):
        value = super().model_dump(*args, **kwargs)
        if value.get('label_scheme') is None:
            value.pop('label_scheme', None)
        return value

    @property
    def scheme(self):
        return self.label_scheme or 'binary_v1'

    @model_validator(mode='after')
    def check(self):
        from src.data.tasks import mapping

        expected = mapping(self.scheme)
        if self.label_scheme == 'stage_v1' and 'label_mapping' not in self.model_fields_set:
            self.label_mapping = expected
        if self.label_mapping != expected:
            raise ValueError(
                'This binary task requires negative=0, positive=1'
                if self.scheme == 'binary_v1'
                else '分期方案必須為 normal=0、stage1=1、stage2=2'
            )
        return self


def experiment_task(model, task=None):
    """Task of an experiment or artifact; absent means the legacy binary default.
    Records of removed models keep working for display and report as 'removed'."""
    return task or ('binary_classification' if model in MODELS else 'removed')


class Experiment(Strict):
    model: Literal[
        'efficientnet_b0', 'dinov2_small', 'dinov2_base', 'baseline_majority', 'baseline_colour', 'baseline_dino_knn'
    ]
    dataset: str
    device: Literal['0', 'cpu'] = '0'
    demo: bool = False
    epochs: int = Field(20, ge=1, le=500)
    batch: int = Field(4, ge=1, le=64)
    seed: int = Field(42, ge=0, le=2147483647)
    patience: int = Field(5, ge=0, le=100)  # unused since training runs a fixed number of epochs (#7)
    imgsz: int = Field(224, ge=64, le=1536)
    parameters: dict = {}
    inference: InferenceConfig = InferenceConfig()
    resume_job: str | None = None
    initial_artifact: str | None = None
    base_import: str | None = None
    checkpoint_import: str | None = None
    allow_amp_check_download: bool = False  # unused; kept so saved job configs still load
    control: Literal['', 'shuffled_labels'] = ''
    # sensitivity_090: the decision threshold comes from the training fold (src/data/threshold.py).
    threshold_policy: Literal['fixed', 'sensitivity_090'] = 'fixed'
    task: Literal['binary_classification', 'stage_classification'] | None = None
    name: str | None = Field(None, max_length=60)
    # Jobs of one cross-validation run (one per fold) share this id (B1); absent for single runs.
    cv_group: str | None = Field(None, pattern='^[0-9a-f]{16}$')
    # B5: train without a fixed independent test set of the snapshot and evaluate that set once.
    # The client only ticks `holdout`; the server swaps `dataset` and sets `independent_test`.
    holdout: bool = False
    independent_test: str | None = None

    @field_validator('name')
    @classmethod
    def clean_name(cls, v):
        from src.workbench.contracts import display_name

        return display_name(v)

    def model_dump(self, *args, **kwargs):
        value = super().model_dump(*args, **kwargs)
        # Keep old idempotency fingerprints stable when optional import features are unused.
        for key in ('base_import', 'checkpoint_import', 'task', 'name', 'cv_group', 'independent_test'):
            if value.get(key) is None:
                value.pop(key, None)
        if not value.get('holdout'):
            value.pop('holdout', None)
        return value

    @model_validator(mode='after')
    def capabilities(self):
        task = experiment_task(self.model, self.task)
        if task == 'stage_classification':
            if self.inference.label_scheme != 'stage_v1':
                if self.inference.label_scheme is not None:
                    raise ValueError('分期任務必須使用 stage_v1 標籤方案')
                self.inference = InferenceConfig(
                    **{
                        **self.inference.model_dump(),
                        'label_scheme': 'stage_v1',
                        'label_mapping': {'normal': 0, 'stage1': 1, 'stage2': 2},
                    }
                )
            if self.model.startswith('dinov2') and self.parameters.get('solver', 'lbfgs') != 'lbfgs':
                raise ValueError('三類分期只支援 lbfgs（多項式 logistic regression）；liblinear 為一對多，分數意義不同')
        elif self.inference.label_scheme not in (None, 'binary_v1'):
            raise ValueError('二分類與偵測任務不可使用分期標籤方案')
        if self.checkpoint_import and not self.resume_job:
            raise ValueError('匯入 checkpoint 必須指定原工作')
        if self.base_import and (self.initial_artifact or self.resume_job):
            raise ValueError('基礎權重、微調與續訓來源不可混用')
        efficient = {
            'learning_rate',
            'optimizer',
            'weight_decay',
            'scheduler',
            'freeze',
            'class_weight',
            'flip',
            'rotation',
        }
        dino = {'C', 'solver', 'max_iter', 'class_weight', 'standardize', 'pooling', 'resolution', 'strategy'}
        linear = {'C', 'solver', 'max_iter', 'class_weight', 'standardize'}
        allowed = (
            efficient
            if self.model == 'efficientnet_b0'
            else (
                dino
                if self.model.startswith('dinov2')
                else linear if self.model == 'baseline_colour' else {'class_weight'}
            )
        )
        bad = set(self.parameters) - allowed
        if bad:
            raise ValueError(f'Unsupported parameters: {sorted(bad)}')
        p = self.parameters
        import math

        if any(isinstance(v, float) and not math.isfinite(v) for v in p.values()):
            raise ValueError('Parameters must be finite')
        if p.get('pooling', 'cls') not in {'cls', 'cls_mean'} or p.get('resolution', 224) not in {224, 518}:
            raise ValueError('Unsupported DINOv2 setting')
        if p.get('strategy', 'flat') not in {'flat', 'hierarchical'}:
            raise ValueError('Unsupported stage strategy')
        if p.get('strategy') == 'hierarchical' and self.task != 'stage_classification':
            raise ValueError('階層式分期只用於分期任務')
        if self.model == 'efficientnet_b0':
            if p.get('optimizer', 'AdamW') not in {'AdamW', 'SGD'}:
                raise ValueError('Unsupported optimizer')
            if p.get('freeze', 'backbone') not in {'backbone', 'last_stage'}:
                raise ValueError('Unsupported freeze strategy')
            if p.get('scheduler', 'none') not in {'none', 'cosine'}:
                raise ValueError('Unsupported scheduler')
            for key in ('learning_rate', 'weight_decay', 'rotation'):
                if key in p and (not isinstance(p[key], (int, float)) or p[key] < 0):
                    raise ValueError(f'Invalid {key}')
            if p.get('learning_rate', 0.001) <= 0 or p.get('rotation', 0) > 45:
                raise ValueError('learning_rate must be positive; rotation must be <=45 degrees')
            if 'flip' in p and not isinstance(p['flip'], bool):
                raise ValueError('flip must be boolean')
        else:
            if self.initial_artifact:
                raise ValueError('DINOv2 keeps its official frozen backbone; start a fresh classifier fit')
            if self.resume_job:
                raise ValueError('Logistic regression has no checkpoint resume; create a new fit')
            if p.get('solver', 'lbfgs') not in {'lbfgs', 'liblinear'}:
                raise ValueError('Supported solvers: lbfgs, liblinear')
            if not 0 < float(p.get('C', 1)) <= 10000:
                raise ValueError('C must be in (0,10000]')
            if not 1 <= int(p.get('max_iter', 200)) <= 2000:
                raise ValueError('max_iter must be 1..2000')
            if not isinstance(p.get('max_iter', 200), int):
                raise ValueError('max_iter must be an integer')
            if not isinstance(p.get('C', 1), (int, float)):
                raise ValueError('C must be numeric')
            if 'standardize' in p and not isinstance(p['standardize'], bool):
                raise ValueError('standardize must be boolean')
        if p.get('class_weight') not in (None, 'balanced'):
            raise ValueError('class_weight must be null or balanced')
        self.imgsz = 224
        self.inference.imgsz = 224
        self.inference.preprocess = 'rgb-letterbox224-imagenet-v1'
        if self.resume_job and self.initial_artifact:
            raise ValueError('Resume and new fine-tuning are different operations')
        return self


class ClassificationReview(Strict):
    """Image-level labels only; never carries boxes."""

    decision: Literal['approve', 'exclude', 'needs_changes', 'reopen']
    revision: str
    label: Literal['positive', 'negative', 'unknown']
    stage: Literal['normal', 'stage1', 'stage2', 'positive_unstaged', 'unknown'] = 'unknown'
    quality: Literal['', 'acceptable', 'limited', 'unusable'] = ''
    reviewer: str = Field(min_length=1, max_length=100)
    reason: str = Field(min_length=1, max_length=1000)
    subject_id: str = Field('', max_length=100)
    clear_subject: bool = False
    category: str = ''


class BatchStageConfirm(Strict):
    """Confirm rule-prefilled stages for several images at once; each gets its own review record."""

    items: list[dict] = Field(min_length=1, max_length=100)
    reviewer: str = Field(min_length=1, max_length=100)
    reason: str = Field(min_length=1, max_length=1000)


def display_name(value):
    """Optional human label (snapshot / experiment); never used as a path or identifier."""
    if value is None:
        return None
    value = ' '.join(str(value).split())
    if any(ord(c) < 32 for c in value):
        raise ValueError('名稱不可包含控制字元')
    return value or None


class SnapshotRequest(Strict):
    demo: bool = False
    folds: int = Field(3, ge=2, le=10)
    repeats: int = Field(1, ge=1, le=10)
    seed: int = Field(42, ge=0)
    task: Literal['binary_classification', 'stage_classification'] = 'binary_classification'
    name: str | None = Field(None, max_length=60)

    @field_validator('name')
    @classmethod
    def clean_name(cls, v):
        return display_name(v)


class SwitchRequest(Strict):
    artifact: str
    target: Literal['local', 'line'] = 'local'
    allow_unevaluated: bool = False
