"""
Alert Şemaları — İhlal/Alarm bildirimleri için Pydantic modelleri.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class AlertType(str, Enum):
    """Alarm türleri."""

    PPE_VIOLATION = "ppe_violation"
    ENVIRONMENTAL = "environmental"
    SYSTEM = "system"


class AlertPriority(str, Enum):
    """Alarm öncelik seviyesi."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Alarm durumu."""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class Alert(BaseModel):
    """Tek bir alarm/ihlal kaydı."""

    alert_id: str = Field(..., description="Benzersiz alarm kimliği")
    alert_type: AlertType
    priority: AlertPriority = Field(default=AlertPriority.MEDIUM)
    status: AlertStatus = Field(default=AlertStatus.ACTIVE)
    title: str = Field(..., description="Alarm başlığı")
    description: str = Field(default="", description="Detaylı açıklama")
    camera_id: Optional[str] = Field(
        default=None, description="İlgili kamera (PPE ihlali için)"
    )
    sensor_id: Optional[str] = Field(
        default=None, description="İlgili sensör (çevresel alarm için)"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    violations: List[str] = Field(
        default_factory=list,
        description="İlgili sınıf ihlalleri (ör: ['NO-Hardhat', 'NO-Mask'])",
    )


class AlertAcknowledge(BaseModel):
    """Alarm onaylama isteği."""

    acknowledged_by: str = Field(..., description="Onaylayan kullanıcı adı")
    note: Optional[str] = Field(
        default=None, description="Onay notu"
    )
