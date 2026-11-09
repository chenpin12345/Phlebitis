from __future__ import annotations

import io
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError


class InvalidImage(ValueError):
    pass


def decode_image(content: bytes, config: dict):
    if not content or len(content) > config["max_image_bytes"]:
        raise InvalidImage("圖片為空或超過 10 MB，請重新傳送較小的照片。")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content)) as im:
                if im.format not in config["allowed_formats"]:
                    raise InvalidImage("請使用 JPEG、PNG 或 WEBP 圖片。")
                if im.width * im.height > config["max_image_pixels"] or min(im.size) < 64:
                    raise InvalidImage("圖片尺寸不合適，請重新拍攝或縮小圖片。")
                im.load()
                return ImageOps.exif_transpose(im).convert("RGB")
    except InvalidImage:
        raise
    except (
        OSError,
        UnidentifiedImageError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        ValueError,
    ) as exc:
        raise InvalidImage("無法讀取圖片，請重新傳送照片。") from exc


def encode_result(image):
    """Bound the JPEG below LINE's 1 MB preview limit."""
    image = image.copy()
    image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
    while True:
        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=85, optimize=True)
        content = buf.getvalue()
        if len(content) <= 900000:
            return content, image.size
        image.thumbnail((max(1, image.width * 3 // 4), max(1, image.height * 3 // 4)), Image.Resampling.LANCZOS)
