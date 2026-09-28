from __future__ import annotations

import math

LABELS = {"Phlebits": 0, "phlebitis": 0, "靜脈炎": 0}


def from_labelme(data: dict, image_size: tuple[int, int] | None = None) -> list[list[float]]:
    w, h = int(data["imageWidth"]), int(data["imageHeight"])
    if w <= 0 or h <= 0 or (image_size and (w, h) != image_size):
        raise ValueError("Annotation/image dimensions do not agree")
    boxes = []
    for shape in data.get("shapes", []):
        if shape.get("label") not in LABELS:
            raise ValueError(f"Unknown label: {shape.get('label')}")
        if shape.get("shape_type") != "rectangle" or len(shape.get("points", [])) != 2:
            raise ValueError("Only two-corner rectangles are supported")
        (x1, y1), (x2, y2) = shape["points"]
        boxes.append([0, (x1 + x2) / (2 * w), (y1 + y2) / (2 * h), abs(x2-x1) / w, abs(y2-y1) / h])
    validate(boxes)
    return boxes


def validate(boxes: list[list[float]]) -> None:
    for row in boxes:
        if len(row) != 5 or not all(math.isfinite(x) for x in row):
            raise ValueError("Each label needs five finite values")
        c, x, y, w, h = row
        if c != 0 or w <= 0 or h <= 0 or min(x-w/2, y-h/2) < -1e-6 or max(x+w/2, y+h/2) > 1+1e-6:
            raise ValueError("Invalid class or box outside image")


def text(boxes: list[list[float]]) -> str:
    validate(boxes)
    return "\n".join(f"0 {x:.8f} {y:.8f} {w:.8f} {h:.8f}" for _, x, y, w, h in boxes)


def orient_boxes(boxes: list[list[float]], orientation: int) -> list[list[float]]:
    """Apply the same normalized-coordinate EXIF transformation as ImageOps.exif_transpose."""
    transforms = {
        1: lambda x,y: (x,y), 2: lambda x,y: (1-x,y),
        3: lambda x,y: (1-x,1-y), 4: lambda x,y: (x,1-y),
        5: lambda x,y: (y,x), 6: lambda x,y: (1-y,x),
        7: lambda x,y: (1-y,1-x), 8: lambda x,y: (y,1-x)
    }
    transform=transforms.get(orientation,transforms[1])
    result=[]
    for c,x,y,w,h in boxes:
        points=[transform(a,b) for a in (x-w/2,x+w/2) for b in (y-h/2,y+h/2)]
        xs,ys=zip(*points)
        result.append([c,(min(xs)+max(xs))/2,(min(ys)+max(ys))/2,max(xs)-min(xs),max(ys)-min(ys)])
    validate(result)
    return result
