"""
Detection Repository — Tespit kayıtlarının veri erişim katmanı.
"""

from typing import List, Optional
from uuid import uuid4

from app.models.schemas.detection import DetectionResult
from app.repositories.base_repository import InMemoryRepository


class DetectionRepository(InMemoryRepository[DetectionResult]):
    """Tespit sonuçları için in-memory repository."""

    async def create(self, entity: DetectionResult) -> DetectionResult:
        record_id = str(uuid4())
        self._store[record_id] = entity
        return entity

    async def get_by_camera(self, camera_id: str) -> List[DetectionResult]:
        """Belirli bir kameraya ait tespit sonuçlarını döner."""
        return [
            det
            for det in self._store.values()
            if det.camera_id == camera_id
        ]

    async def get_latest(
        self, camera_id: Optional[str] = None, limit: int = 10
    ) -> List[DetectionResult]:
        """Son N tespit sonucunu döner (opsiyonel kamera filtresi)."""
        results = list(self._store.values())
        if camera_id:
            results = [r for r in results if r.camera_id == camera_id]
        results.sort(key=lambda x: x.timestamp, reverse=True)
        return results[:limit]
