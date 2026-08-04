"""Safe image-upload validation and server-side naming helpers."""

from __future__ import annotations

import hashlib
import io
import warnings
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageOps, UnidentifiedImageError
from werkzeug.utils import secure_filename


ALLOWED_FORMATS = {"JPEG": (".jpg", "image/jpeg"), "PNG": (".png", "image/png")}
DEFAULT_MAX_IMAGE_BYTES = 12 * 1024 * 1024
DEFAULT_MAX_IMAGE_PIXELS = 36_000_000


class InvalidImageUpload(ValueError):
    """Raised when uploaded bytes are not an allowed, safely decodable image."""


@dataclass(frozen=True)
class ValidatedImage:
    original_name: str
    stored_name: str
    mime_type: str
    image_format: str
    byte_size: int
    width: int
    height: int
    sha256: str


def _safe_original_name(filename: str | None) -> str:
    clean = secure_filename(Path(filename or "uploaded-maize-image").name)
    return clean or "uploaded-maize-image"


def read_limited(stream, max_bytes: int = DEFAULT_MAX_IMAGE_BYTES) -> bytes:
    """Read at most one byte beyond the limit so oversized bodies fail early."""
    data = stream.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise InvalidImageUpload(f"Image exceeds the {max_bytes // (1024 * 1024)} MB limit")
    if not data:
        raise InvalidImageUpload("Image file is empty")
    return data


def validate_image_bytes(
    data: bytes,
    filename: str | None,
    declared_content_type: str | None = None,
    *,
    max_bytes: int = DEFAULT_MAX_IMAGE_BYTES,
    max_pixels: int = DEFAULT_MAX_IMAGE_PIXELS,
) -> ValidatedImage:
    if not data:
        raise InvalidImageUpload("Image file is empty")
    if len(data) > max_bytes:
        raise InvalidImageUpload(f"Image exceeds the {max_bytes // (1024 * 1024)} MB limit")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as opened:
                opened.verify()
            with Image.open(io.BytesIO(data)) as opened:
                image_format = (opened.format or "").upper()
                if image_format not in ALLOWED_FORMATS:
                    raise InvalidImageUpload("Only valid JPG and PNG images are allowed")
                width, height = opened.size
                if width <= 0 or height <= 0 or width * height > max_pixels:
                    raise InvalidImageUpload("Image dimensions are not allowed")
                ImageOps.exif_transpose(opened).convert("RGB").load()
    except InvalidImageUpload:
        raise
    except (Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise InvalidImageUpload("Image dimensions are not allowed") from None
    except (UnidentifiedImageError, OSError, ValueError):
        raise InvalidImageUpload("The uploaded file is not a valid JPG or PNG image") from None

    suffix, detected_mime = ALLOWED_FORMATS[image_format]
    declared_mime = (declared_content_type or "").split(";", 1)[0].strip().lower()
    if declared_mime and declared_mime not in {"application/octet-stream", detected_mime}:
        raise InvalidImageUpload("The declared content type does not match the image")

    return ValidatedImage(
        original_name=_safe_original_name(filename),
        stored_name=f"{uuid4().hex}{suffix}",
        mime_type=detected_mime,
        image_format=image_format,
        byte_size=len(data),
        width=int(width),
        height=int(height),
        sha256=hashlib.sha256(data).hexdigest(),
    )
