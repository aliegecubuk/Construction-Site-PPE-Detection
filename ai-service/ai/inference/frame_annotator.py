"""
Frame Annotator — Tespit kutularını frame üzerine çizer.
OpenCV kullanarak görselleştirme yapar.
"""

from typing import Dict, List, Tuple

import cv2
import numpy as np

from app.core.constants import VIOLATION_CLASSES
from app.models.schemas.detection import BoundingBox

# Sınıf renklerini tanımla (BGR)
CLASS_COLORS: Dict[str, Tuple[int, int, int]] = {
    "Hardhat": (0, 255, 0),        # Yeşil
    "Mask": (0, 255, 0),            # Yeşil
    "Safety Vest": (0, 255, 0),     # Yeşil
    "NO-Hardhat": (0, 0, 255),      # Kırmızı
    "NO-Mask": (0, 0, 255),         # Kırmızı
    "NO-Safety Vest": (0, 0, 255),  # Kırmızı
    "Person": (255, 255, 0),        # Cyan
    "Safety Cone": (0, 165, 255),   # Turuncu
    "machinery": (255, 0, 255),     # Magenta
    "vehicle": (128, 128, 0),       # Teal
}

DEFAULT_COLOR: Tuple[int, int, int] = (200, 200, 200)  # Gri


class FrameAnnotator:
    """
    Tespit sonuçlarını frame üzerine çizen sınıf.

    Kullanım:
        annotator = FrameAnnotator()
        annotated_frame = annotator.annotate(frame, detections)
    """

    def __init__(
        self,
        line_thickness: int = 2,
        font_scale: float = 0.6,
        show_confidence: bool = True,
    ) -> None:
        self._thickness = line_thickness
        self._font_scale = font_scale
        self._show_conf = show_confidence
        self._font = cv2.FONT_HERSHEY_SIMPLEX

    def annotate(
        self,
        frame: np.ndarray,
        detections: List[BoundingBox],
    ) -> np.ndarray:
        """
        Frame üzerine tespit kutularını ve etiketleri çizer.
        İhlal sınıfları kırmızı, uyumlu sınıflar yeşil olarak işaretlenir.

        Args:
            frame: BGR formatında OpenCV frame.
            detections: BoundingBox listesi.

        Returns:
            Annotated frame (kopyası).
        """
        annotated = frame.copy()

        for det in detections:
            color = CLASS_COLORS.get(det.class_name, DEFAULT_COLOR)
            pt1 = (int(det.x1), int(det.y1))
            pt2 = (int(det.x2), int(det.y2))

            # Bounding box çiz
            cv2.rectangle(annotated, pt1, pt2, color, self._thickness)

            # Etiket oluştur
            label = det.class_name
            if self._show_conf:
                label += f" {det.confidence:.0%}"

            # Etiket arka planı
            (label_w, label_h), baseline = cv2.getTextSize(
                label, self._font, self._font_scale, 1
            )
            cv2.rectangle(
                annotated,
                (pt1[0], pt1[1] - label_h - baseline - 4),
                (pt1[0] + label_w, pt1[1]),
                color,
                -1,
            )

            # Etiket metni
            cv2.putText(
                annotated,
                label,
                (pt1[0], pt1[1] - baseline - 2),
                self._font,
                self._font_scale,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

        return annotated

    def add_info_overlay(
        self,
        frame: np.ndarray,
        camera_name: str,
        person_count: int,
        violation_count: int,
    ) -> np.ndarray:
        """Frame'in üst köşesine bilgi paneli ekler."""
        overlay = frame.copy()
        h, w = frame.shape[:2]

        # Yarı saydam arka plan
        cv2.rectangle(overlay, (0, 0), (320, 80), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)

        cv2.putText(
            frame,
            f"Kamera: {camera_name}",
            (10, 22),
            self._font,
            0.5,
            (255, 255, 255),
            1,
        )
        cv2.putText(
            frame,
            f"Kisi: {person_count}",
            (10, 45),
            self._font,
            0.5,
            (255, 255, 0),
            1,
        )

        violation_color = (0, 0, 255) if violation_count > 0 else (0, 255, 0)
        cv2.putText(
            frame,
            f"Ihlal: {violation_count}",
            (10, 68),
            self._font,
            0.5,
            violation_color,
            1,
        )

        return frame
