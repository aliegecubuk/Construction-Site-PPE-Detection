"""
Detection Şemaları — Tespit sonuçları için Pydantic modelleri.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Tek bir tespit kutusunun koordinatları."""

    x1: float = Field(..., description="Sol üst köşe X")
    y1: float = Field(..., description="Sol üst köşe Y")
    x2: float = Field(..., description="Sağ alt köşe X")
    y2: float = Field(..., description="Sağ alt köşe Y")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Güven skoru")
    class_name: str = Field(..., description="Sınıf adı (ör: Hardhat, NO-Mask)")
    class_id: int = Field(..., description="Sınıf index numarası")


class DetectionResult(BaseModel):
    """Tek bir frame'in tespit sonuçları."""

    camera_id: str = Field(..., description="Kamera kimliği")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    frame_number: int = Field(default=0, description="Frame numarası")
    detections: List[BoundingBox] = Field(default_factory=list)
    violation_count: int = Field(default=0, description="Toplam ihlal sayısı")
    person_count: int = Field(default=0, description="Tespit edilen kişi sayısı")
    violations: List[str] = Field(
        default_factory=list,
        description="Frame üzerinde tespit edilen tekil ihlal etiketleri",
    )


class DetectionSummary(BaseModel):
    """Belirli bir zaman dilimindeki tespit özeti."""

    camera_id: str
    start_time: datetime
    end_time: datetime
    total_frames: int = 0
    total_violations: int = 0
    violation_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Sınıf başına ihlal sayısı (ör: {'NO-Hardhat': 5})",
    )
