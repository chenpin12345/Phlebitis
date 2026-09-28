import io
import pytest
from PIL import Image
from src.inference.engine import decode_image,InvalidImage,validate_model
from src.lock import OperationLock

CFG={"max_image_bytes":100000,"max_image_pixels":1000000,"allowed_formats":["JPEG","PNG","WEBP"]}

def test_corrupt_oversize_and_unsupported_rejected():
    for raw in [b"not an image",b"x"*100001]:
        with pytest.raises(InvalidImage):decode_image(raw,CFG)
    buf=io.BytesIO();Image.new("RGB",(100,100)).save(buf,format="GIF")
    with pytest.raises(InvalidImage):decode_image(buf.getvalue(),CFG)

def test_valid_image_decodes_without_source_metadata():
    buf=io.BytesIO();Image.new("RGB",(100,100),"blue").save(buf,format="PNG")
    result=decode_image(buf.getvalue(),CFG)
    assert result.mode=="RGB"

def test_generic_weights_rejected():
    class Model:names={0:"person",1:"car"}
    with pytest.raises(ValueError,match="single-class"):validate_model(Model())

def test_gpu_operation_lock_excludes_second_operation(tmp_path,monkeypatch):
    monkeypatch.setattr('src.lock.ROOT',tmp_path)
    with OperationLock(tmp_path/'compute.lock'):
        with pytest.raises(RuntimeError):
            with OperationLock(tmp_path/'compute.lock'):pass
    with OperationLock(tmp_path/'compute.lock'):pass
