import json
from pathlib import Path
import pytest
from PIL import Image
from src.common import sha256,write_manifest,read_manifest
from src.data.labels import from_labelme,validate
from src.data.dataset import audit,build,validate_split,review
from src.data.migrate import migrate


@pytest.fixture
def dataset(tmp_path):
    rows=[]
    for g in range(3):
        for label in ["positive","negative"]:
            ident=f"g{g}_{label}"
            im=tmp_path/f"data/approved/images/{ident}.jpg"
            im.parent.mkdir(parents=True,exist_ok=True)
            Image.new("RGB",(100,100),(20+g*40,80 if label=="positive" else 160,50)).save(im)
            lab=tmp_path/f"data/approved/annotations/{ident}.txt"
            lab.parent.mkdir(parents=True,exist_ok=True)
            lab.write_text("0 0.5 0.5 0.2 0.2" if label=="positive" else "")
            rows.append(dict(image_id=ident,sha256=sha256(im),image_path=im.relative_to(tmp_path).as_posix(),annotation_path="",yolo_path=lab.relative_to(tmp_path).as_posix(),status="approved",label_state=label,candidate_group=f"g{g}",subject_id=f"patient{g}",group_verified="true",reviewer="tester",reason="fixture",updated_at="test",original_paths="[]"))
    write_manifest(rows,tmp_path)
    return tmp_path


def test_annotations_reject_unknown_and_bounds():
    base={"imageWidth":100,"imageHeight":100,"shapes":[{"label":"Phlebits","shape_type":"rectangle","points":[[20,20],[80,80]]}]}
    assert from_labelme(base)==[[0,0.5,0.5,0.6,0.6]]
    base["shapes"][0]["label"]="another_class"
    with pytest.raises(ValueError,match="Unknown"):from_labelme(base)
    with pytest.raises(ValueError):validate([[0,0.1,0.1,0.8,0.8]])


def test_grouped_split_and_extra_image_blocked(dataset):
    info=build(root=dataset)
    assert len(info["folds"])==3
    for fold in info["folds"]:
        f=validate_split(dataset/fold["dataset"],dataset)
        assert not ({x["group"] for x in f["members"]["train"]}&{x["group"] for x in f["members"]["val"]})
    path=dataset/info["folds"][0]["dataset"]
    Image.new("RGB",(100,100)).save(path.parent/"images/train/unapproved.jpg")
    with pytest.raises(ValueError,match="Unlisted image"):validate_split(path,dataset)


def test_formal_build_requires_verified_subject(dataset):
    rows=read_manifest(dataset);rows[0]["group_verified"]="false";rows[0]["subject_id"]="";write_manifest(rows,dataset)
    with pytest.raises(ValueError,match="identifiers"):build(root=dataset)


def test_changed_manifest_preserves_old_split(dataset):
    info=build(root=dataset)
    rows=read_manifest(dataset);rows[0]["reason"]="reviewed again";write_manifest(rows,dataset)
    assert validate_split(dataset/info["folds"][0]["dataset"],dataset)["members"]


def test_review_moves_image_and_labels_and_blocks_training(dataset):
    ident="g0_positive"
    r=review(ident,status="excluded",label="positive",reviewer="human",reason="blurred",root=dataset)
    assert r["status"]=="excluded"
    assert (dataset/r["image_path"]).is_file()
    assert not (dataset/f"data/approved/images/{ident}.jpg").exists()
    assert not (dataset/f"data/approved/annotations/{ident}.txt").exists()
    assert not audit(dataset)["errors"]


def test_positive_detection_requires_annotation(dataset):
    # Confirming lesion boxes still requires a real annotation...
    with pytest.raises(ValueError,match="require"):
        review("g0_positive",task="detection",detection="boxes",status="approved",label="positive",reviewer="human",reason="check",root=dataset)
    # ...but a positive image-level label no longer needs boxes (classification task).
    r=review("g0_positive",task="classification",stage="stage2",status="approved",label="positive",reviewer="human",reason="check",root=dataset)
    assert r["stage_label"]=="stage2" and r["status"]=="approved"
    assert not audit(dataset)["errors"]


def test_migration_is_lossless_and_exclusion_wins(tmp_path):
    source=tmp_path/"YOLODataset/images/train/a.jpg";source.parent.mkdir(parents=True);Image.new("RGB",(100,100),"red").save(source)
    excluded=tmp_path/"不清楚的/a.jpg";excluded.parent.mkdir();excluded.write_bytes(source.read_bytes())
    original=sha256(source)
    result=migrate(tmp_path)
    assert result["canonical_images"]==1
    assert result["status_counts"]=={"excluded":1}
    assert sha256(tmp_path/"archive/legacy/YOLODataset/images/train/a.jpg")==original
    assert read_manifest(tmp_path)[0]["status"]=="excluded"
    assert migrate(tmp_path)==result


def test_exif_rotation_transforms_box_coordinates():
    from src.data.labels import orient_boxes
    result=orient_boxes([[0,0.25,0.3,0.2,0.1]],6)[0]
    assert result==pytest.approx([0,0.7,0.25,0.1,0.2])

@pytest.mark.parametrize('orientation',range(1,9))
def test_exif_roundtrip_all_orientations(orientation):
    from src.data.labels import orient_boxes
    boxes=[[0,.35,.45,.2,.3]]
    assert orient_boxes(orient_boxes(boxes,orientation),{6:8,8:6}.get(orientation,orientation))[0]==pytest.approx(boxes[0])

def test_snapshot_split_metadata_tamper_rejected(dataset):
    info=build(root=dataset);path=dataset/info['folds'][0]['dataset']
    split=json.loads((path.parent/'split.json').read_text())
    split['members']['val'][0]['group']='tampered'
    (path.parent/'split.json').write_text(json.dumps(split))
    with pytest.raises(ValueError,match='Snapshot'):validate_split(path,dataset)

def test_review_revision_conflict(dataset):
    with pytest.raises(ValueError,match='revision conflict'):
        review('g0_positive',status='excluded',label='positive',reviewer='human',reason='blur',revision='stale',root=dataset)
    assert read_manifest(dataset)[0]['status']=='approved'

def test_review_failure_restores_files_and_manifest(dataset,monkeypatch):
    from src.data import dataset as module
    before=read_manifest(dataset);image=dataset/before[0]['image_path'];original=image.read_bytes()
    def fail(*args):raise OSError('injected manifest write failure')
    monkeypatch.setattr(module,'write_manifest',fail)
    with pytest.raises(OSError):review('g0_positive',status='excluded',label='positive',reviewer='human',reason='blur',root=dataset)
    assert read_manifest(dataset)==before and image.read_bytes()==original
    assert not (dataset/'data/excluded/other/images/g0_positive.jpg').exists()

def test_substantive_review_marks_old_snapshot_unusable(dataset):
    info=build(root=dataset)
    review('g0_positive',status='excluded',label='positive',reviewer='human',reason='blur',root=dataset)
    with pytest.raises(ValueError,match='withdrawn or superseded'):validate_split(dataset/info['folds'][0]['dataset'],dataset)
