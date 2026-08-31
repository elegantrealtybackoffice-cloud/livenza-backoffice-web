"""Image preparation for public Livenza property photography.

The consumer site only receives browser-safe JPEGs. Processing here also strips
EXIF metadata and bounds image dimensions before the public object is stored.
"""
from __future__ import annotations

import io
from typing import NamedTuple

from PIL import Image, ImageOps, UnidentifiedImageError


class PropertyMediaError(ValueError):
    """Raised when an uploaded property image cannot be safely published."""


class PreparedPropertyMedia(NamedTuple):
    data: bytes
    content_type: str
    extension: str
    width: int
    height: int


def prepare_property_media_image(
    raw: bytes,
    *,
    max_bytes: int = 15 * 1024 * 1024,
    max_side: int = 2400,
    quality: int = 88,
) -> PreparedPropertyMedia:
    """Validate and convert an upload to a bounded progressive JPEG."""
    if not raw:
        raise PropertyMediaError('Choose a property image to upload.')
    if len(raw) > max_bytes:
        raise PropertyMediaError('Property images must be 15 MB or smaller.')
    if max_side < 640:
        raise ValueError('max_side must be at least 640 pixels.')

    try:
        probe = Image.open(io.BytesIO(raw))
        probe.verify()
        image = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert('RGB')
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise PropertyMediaError('Use a valid JPG, PNG, WebP, HEIC/HEIF, TIFF or BMP image.') from exc

    image.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    output = io.BytesIO()
    image.save(output, format='JPEG', quality=max(72, min(int(quality), 94)), optimize=True, progressive=True)
    data = output.getvalue()
    if not data:
        raise PropertyMediaError('The property image could not be prepared for publishing.')
    return PreparedPropertyMedia(data, 'image/jpeg', '.jpg', image.width, image.height)
