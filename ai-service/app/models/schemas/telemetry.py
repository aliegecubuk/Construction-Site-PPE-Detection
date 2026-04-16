"""
Kamera Telemetry Şemaları — Kamera bazlı IoT snapshot sözleşmeleri.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.schemas.iot import SeverityLevel


class CameraTelemetrySnapshot(BaseModel):
    """Bir kameraya atanmış anlık IoT telemetri verisi."""

    model_config = ConfigDict(populate_by_name=True)

    camera_id: str = Field(..., alias="cameraId")
    camera_name: str = Field(..., alias="cameraName")
    occurred_at: datetime = Field(default_factory=datetime.utcnow, alias="occurredAt")
    gas_level: float = Field(default=0.0, alias="gasLevel")
    gas_severity: SeverityLevel = Field(default=SeverityLevel.NORMAL, alias="gasSeverity")
    temperature: float = 0.0
    temperature_severity: SeverityLevel = Field(
        default=SeverityLevel.NORMAL,
        alias="temperatureSeverity",
    )
    humidity: float = 0.0
    humidity_severity: SeverityLevel = Field(
        default=SeverityLevel.NORMAL,
        alias="humiditySeverity",
    )
    noise_level: float = Field(default=0.0, alias="noiseLevel")
    noise_severity: SeverityLevel = Field(default=SeverityLevel.NORMAL, alias="noiseSeverity")
    vibration: float = 0.0
    vibration_severity: SeverityLevel = Field(
        default=SeverityLevel.NORMAL,
        alias="vibrationSeverity",
    )
