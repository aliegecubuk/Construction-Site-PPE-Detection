"""
IoT Şemaları — Sensör verileri için Pydantic modelleri.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SensorType(str, Enum):
    """Desteklenen sensör türleri."""

    GAS = "gas"
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    NOISE = "noise"
    VIBRATION = "vibration"


class SeverityLevel(str, Enum):
    """Sensör okuması şiddet seviyesi."""

    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"


class SensorReading(BaseModel):
    """Tek bir sensör okuması."""

    sensor_id: str = Field(..., description="Sensör benzersiz kimliği")
    sensor_type: SensorType
    value: float = Field(..., description="Ölçüm değeri")
    unit: str = Field(..., description="Ölçüm birimi (ppm, °C, %, dB, mm/s)")
    severity: SeverityLevel = Field(default=SeverityLevel.NORMAL)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    location: Optional[str] = Field(
        default=None, description="Sensörün bulunduğu bölge"
    )


class EnvironmentData(BaseModel):
    """Tüm çevresel sensörlerin anlık toplu okuması."""

    gas_level: float = Field(default=0.0, description="Gaz seviyesi (ppm)")
    temperature: float = Field(default=0.0, description="Sıcaklık (°C)")
    humidity: float = Field(default=0.0, description="Nem (%)")
    noise_level: float = Field(default=0.0, description="Gürültü (dB)")
    vibration: float = Field(default=0.0, description="Titreşim (mm/s)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    location: str = Field(default="Genel Alan")

    # Her değer için şiddet seviyesi
    gas_severity: SeverityLevel = Field(default=SeverityLevel.NORMAL)
    temperature_severity: SeverityLevel = Field(default=SeverityLevel.NORMAL)
    humidity_severity: SeverityLevel = Field(default=SeverityLevel.NORMAL)
    noise_severity: SeverityLevel = Field(default=SeverityLevel.NORMAL)
    vibration_severity: SeverityLevel = Field(default=SeverityLevel.NORMAL)
