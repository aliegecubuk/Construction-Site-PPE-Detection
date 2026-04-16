"""
Camera Repository — Kamera konfigürasyonlarının veri erişim katmanı.
"""

from typing import List, Optional

from app.models.schemas.camera import CameraConfig
from app.repositories.base_repository import InMemoryRepository


class CameraRepository(InMemoryRepository[CameraConfig]):
    """Kamera konfigürasyonları için in-memory repository."""

    async def create(self, entity: CameraConfig) -> CameraConfig:
        self._store[entity.camera_id] = entity
        return entity

    async def get_by_id(self, entity_id: str) -> Optional[CameraConfig]:
        return self._store.get(entity_id)

    async def get_enabled(self) -> List[CameraConfig]:
        """Sadece aktif kameraları döner."""
        return [cam for cam in self._store.values() if cam.enabled]
