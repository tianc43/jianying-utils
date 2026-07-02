"""Compatibility helpers for pyJianYingDraft video/photo materials."""

from __future__ import annotations

import os
import uuid
from typing import Optional

from pyJianYingDraft import CropSettings, VideoMaterial


def create_video_material(
    path: str,
    material_name: Optional[str] = None,
    crop_settings: CropSettings = CropSettings(),
) -> VideoMaterial:
    """Create a VideoMaterial, with native WebP photo support.

    pyJianYingDraft 0.2.7 relies on MediaInfo for photo dimensions. MediaInfo
    may detect WebP as an image while omitting width/height, causing
    VideoMaterial construction to fail. For WebP, read dimensions with Pillow
    and build the same VideoMaterial shape while keeping the original .webp
    path in the exported draft.
    """
    if _is_webp(path):
        return _create_webp_photo_material(path, material_name, crop_settings)

    material = VideoMaterial(path, material_name=material_name, crop_settings=crop_settings)
    if _has_dimensions(material):
        return material
    return material


def _has_dimensions(material: VideoMaterial) -> bool:
    return bool(material.width) and bool(material.height)


def _is_webp(path: str) -> bool:
    return os.path.splitext(path)[1].lower() == ".webp"


def _create_webp_photo_material(
    path: str,
    material_name: Optional[str],
    crop_settings: CropSettings,
) -> VideoMaterial:
    path = os.path.abspath(path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"找不到 {path}")
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("WebP 图片需要 Pillow 才能读取宽高: pip install Pillow") from exc

    with Image.open(path) as image:
        width, height = image.size

    material = VideoMaterial.__new__(VideoMaterial)
    material.material_name = material_name if material_name else os.path.basename(path)
    material.material_id = uuid.uuid4().hex
    material.path = path
    material.crop_settings = crop_settings
    material.local_material_id = ""
    material.material_type = "photo"
    material.duration = 10800000000
    material.width = int(width)
    material.height = int(height)
    return material
