"""
Detection Service — Tespit sonuçları iş mantığı.
Kamera bazlı sınıf filtrelemeyi burada uygular.
"""

from typing import Dict, List, Optional

from loguru import logger

from app.core.constants import VIOLATION_CLASSES
from app.models.schemas.detection import BoundingBox, DetectionResult
from app.repositories.detection_repository import DetectionRepository


class DetectionService:
    """Tespit sonuçlarını işleyen iş mantığı katmanı."""

    def __init__(self, repository: DetectionRepository) -> None:
        self._repo = repository

    def filter_by_active_classes(
        self,
        detections: List[BoundingBox],
        active_classes: Dict[str, bool],
    ) -> List[BoundingBox]:
        """
        Kamera konfigürasyonuna göre tespitleri filtreler.

        Sadece aktif (True) olan sınıfların tespitlerini döndürür.
        Bu mekanizma, her kameranın farklı ekipman denetimi yapmasını sağlar.

        Örnek:
            active_classes = {"Hardhat": True, "Mask": False, ...}
            → Sadece Hardhat tespitleri döner, Mask tespitleri filtrelenir.
        """
        if not active_classes:
            return detections

        return [
            det
            for det in detections
            if active_classes.get(det.class_name, False)
        ]

    def count_violations(self, detections: List[BoundingBox]) -> int:
        """İhlal sınıflarına (NO-Hardhat, NO-Mask, vb.) ait tespit sayısı."""
        return sum(
            1 for det in detections if det.class_name in VIOLATION_CLASSES
        )

    def count_persons(self, detections: List[BoundingBox]) -> int:
        """Tespit edilen kişi sayısı."""
        return sum(
            1 for det in detections if det.class_name == "Person"
        )

    async def process_and_store(
        self,
        camera_id: str,
        detections: List[BoundingBox],
        active_classes: Dict[str, bool],
        frame_number: int = 0,
        violations: Optional[List[str]] = None,
    ) -> DetectionResult:
        """
        Ham tespitleri filtreler, ihlal sayar ve kaydeder.

        1. Kamera bazlı sınıf filtreleme uygular
        2. İhlal ve kişi sayısını hesaplar
        3. Sonucu repository'ye kaydeder
        """
        filtered = self.filter_by_active_classes(detections, active_classes)
        violation_labels = sorted(set(violations or []))
        violation_count = len(violation_labels) or self.count_violations(filtered)
        persons = self.count_persons(filtered)

        result = DetectionResult(
            camera_id=camera_id,
            frame_number=frame_number,
            detections=filtered,
            violation_count=violation_count,
            person_count=persons,
            violations=violation_labels,
        )

        await self._repo.create(result)
        logger.debug(
            f"[{camera_id}] Frame #{frame_number}: "
            f"{len(filtered)} tespit, {violation_count} ihlal, {persons} kişi"
        )
        return result

    async def get_latest(
        self, camera_id: Optional[str] = None, limit: int = 10
    ) -> List[DetectionResult]:
        """Son tespitleri getirir."""
        return await self._repo.get_latest(camera_id=camera_id, limit=limit)
