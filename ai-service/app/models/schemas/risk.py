"""
Risk Şemaları — Risk skorlama için Pydantic modelleri.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Risk seviyesi."""

    LOW = "low"           # 0–25
    MEDIUM = "medium"     # 26–50
    HIGH = "high"         # 51–75
    CRITICAL = "critical"  # 76–100


class RiskFactor(BaseModel):
    """Tek bir risk faktörü (vision veya IoT kaynağından)."""

    source: str = Field(..., description="Faktör kaynağı (ör: 'vision', 'iot')")
    name: str = Field(..., description="Faktör adı (ör: 'NO-Hardhat', 'gas_level')")
    raw_value: float = Field(..., description="Ham değer (count veya ölçüm)")
    score: float = Field(
        ..., ge=0.0, le=100.0, description="Normalize skor (0–100)"
    )
    description: str = Field(default="", description="İnsan-okunur açıklama")


class RiskReport(BaseModel):
    """
    Birleşik risk raporu.

    Vision (görüntü ihlalleri) ve IoT (çevresel tehlikeler) verilerini
    ağırlıklı olarak birleştirerek tek bir risk skoru üretir.
    """

    # Genel skor
    total_score: float = Field(
        ..., ge=0.0, le=100.0, description="Toplam risk skoru (0–100)"
    )
    risk_level: RiskLevel = Field(..., description="Risk seviyesi")

    # Alt skorlar
    vision_score: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Görüntü risk skoru"
    )
    iot_score: float = Field(
        default=0.0, ge=0.0, le=100.0, description="IoT risk skoru"
    )

    # Ağırlıklar
    vision_weight: float = Field(default=0.6, description="Vision ağırlığı")
    iot_weight: float = Field(default=0.4, description="IoT ağırlığı")

    # Detay faktörler
    factors: List[RiskFactor] = Field(
        default_factory=list, description="Risk faktörleri listesi"
    )

    # Meta
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    location: str = Field(default="Genel Alan")
    camera_count: int = Field(
        default=0, description="Analiz edilen kamera sayısı"
    )
    active_violations: int = Field(
        default=0, description="Toplam aktif ihlal sayısı"
    )
    recommendation: str = Field(
        default="", description="Sistem önerisi"
    )


class RiskCalculateRequest(BaseModel):
    """Manuel risk hesaplama isteği."""

    violation_counts: Dict[str, int] = Field(
        default_factory=dict,
        description="İhlal sayıları: {'NO-Hardhat': 3, 'NO-Mask': 1}",
    )
    gas_level: Optional[float] = Field(default=None, description="Gaz (ppm)")
    temperature: Optional[float] = Field(default=None, description="Sıcaklık (°C)")
    humidity: Optional[float] = Field(default=None, description="Nem (%)")
    noise_level: Optional[float] = Field(default=None, description="Gürültü (dB)")
    vibration: Optional[float] = Field(default=None, description="Titreşim (mm/s)")
    location: str = Field(default="Genel Alan")
