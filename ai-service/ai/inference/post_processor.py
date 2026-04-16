"""
Post Processor — Tespit sonrası filtreleme ve iyileştirme.
Kamera bazlı sınıf filtreleme, güven eşiği ve NMS uygular.
"""

from typing import Dict, List, Optional

from app.core.constants import DEFAULT_CONFIDENCE_THRESHOLD
from app.models.schemas.detection import BoundingBox


class PostProcessor:
    """
    Tespit sonuçlarına post-processing uygular.

    İşlem sırası:
        1. Güven eşiği filtresi
        2. Kamera bazlı sınıf filtresi
        3. Küçük kutu filtresi (opsiyonel)
    """

    def __init__(
        self,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
        min_box_area: float = 100.0,
    ) -> None:
        self._confidence_threshold = confidence_threshold
        self._min_box_area = min_box_area

    def filter_by_confidence(
        self,
        detections: List[BoundingBox],
        threshold: Optional[float] = None,
    ) -> List[BoundingBox]:
        """Güven eşiğinin altındaki tespitleri filtreler."""
        t = threshold or self._confidence_threshold
        return [d for d in detections if d.confidence >= t]

    def filter_by_classes(
        self,
        detections: List[BoundingBox],
        active_classes: Dict[str, bool],
    ) -> List[BoundingBox]:
        """Kamera konfigürasyonuna göre sınıf filtresi uygular."""
        if not active_classes:
            return detections
        return [
            d for d in detections if active_classes.get(d.class_name, False)
        ]

    def filter_small_boxes(
        self, detections: List[BoundingBox]
    ) -> List[BoundingBox]:
        """Çok küçük bounding box'ları filtreler (gürültü azaltma)."""
        return [
            d
            for d in detections
            if (d.x2 - d.x1) * (d.y2 - d.y1) >= self._min_box_area
        ]

    def process(
        self,
        detections: List[BoundingBox],
        active_classes: Optional[Dict[str, bool]] = None,
        confidence_threshold: Optional[float] = None,
    ) -> List[BoundingBox]:
        """
        Tüm post-processing adımlarını sırayla uygular.
        """
        result = self.filter_by_confidence(detections, confidence_threshold)
        result = self.filter_small_boxes(result)
        if active_classes:
            result = self.filter_by_classes(result, active_classes)
        return result
