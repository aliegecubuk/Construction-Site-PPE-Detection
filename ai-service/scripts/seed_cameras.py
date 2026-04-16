"""
Seed Cameras — Varsayılan kamera konfigürasyonlarını JSON'dan yükler.

Kullanım:
    python scripts/seed_cameras.py
"""

import asyncio
import json
from pathlib import Path

from app.api.dependencies import get_camera_service
from app.models.schemas.camera import CameraConfig


async def seed_cameras():
    """camera_class_map.json'dan kamera konfigürasyonlarını yükler."""
    config_path = Path("ai/config/camera_class_map.json")

    if not config_path.exists():
        print(f"❌ Konfigürasyon dosyası bulunamadı: {config_path}")
        return

    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    service = get_camera_service()

    for cam_data in data.get("cameras", []):
        config = CameraConfig(**cam_data)
        await service.add_camera(config)
        print(f"✅ Kamera eklendi: {config.camera_id} — {config.name}")

    cameras = await service.get_all_cameras()
    print(f"\n📷 Toplam {len(cameras)} kamera yüklendi.")


if __name__ == "__main__":
    asyncio.run(seed_cameras())
