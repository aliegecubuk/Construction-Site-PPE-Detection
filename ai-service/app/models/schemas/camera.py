"""
Camera Şemaları — Kamera konfigürasyonu için Pydantic modelleri.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class CameraSourceType(str, Enum):
    """Kamera kaynak türü."""

    RTSP = "rtsp"
    LOCAL_FILE = "local_file"
    USB_DEVICE = "usb_device"


class CameraStatus(str, Enum):
    """Kamera durumu."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    CONNECTING = "connecting"


class PPERequirements(BaseModel):
    """Kamera bazında zorunlu KKD gereksinimleri."""

    model_config = ConfigDict(populate_by_name=True)

    hardhat: bool = Field(default=False, description="Baret zorunlu mu?")
    safety_vest: bool = Field(
        default=False,
        alias="safetyVest",
        description="Reflektif yelek zorunlu mu?",
    )
    mask: bool = Field(default=False, description="Maske zorunlu mu?")


class PPERequirementsUpdate(BaseModel):
    """Kamera KKD gereksinimlerini kısmi güncelleme isteği."""

    model_config = ConfigDict(populate_by_name=True)

    hardhat: Optional[bool] = None
    safety_vest: Optional[bool] = Field(default=None, alias="safetyVest")
    mask: Optional[bool] = None


class CameraConfig(BaseModel):
    """Tek bir kameranın konfigürasyon modeli."""

    model_config = ConfigDict(populate_by_name=True)

    camera_id: str = Field(..., description="Benzersiz kamera kimliği")
    name: str = Field(..., description="Kamera insan-okunur adı")
    source: str = Field(..., description="RTSP URL veya dosya yolu")
    source_type: CameraSourceType = Field(default=CameraSourceType.RTSP)
    enabled: bool = Field(default=True, description="Kamera aktif mi?")
    detection_classes: Dict[str, bool] = Field(
        default_factory=dict,
        description="Sınıf adı → aktif/pasif eşlemesi",
    )
    required_ppe: PPERequirements = Field(
        default_factory=PPERequirements,
        description="Kamera için zorunlu KKD gereksinimleri",
    )


class CameraStatusResponse(BaseModel):
    """Kamera durum bilgisi (API yanıtı)."""

    camera_id: str
    name: str
    status: CameraStatus = CameraStatus.INACTIVE
    source_type: CameraSourceType = CameraSourceType.RTSP
    enabled: bool = True
    fps: float = 0.0
    last_frame_at: Optional[datetime] = None
    active_classes: int = Field(
        default=0, description="Aktif tespit sınıfı sayısı"
    )
    required_ppe: PPERequirements = Field(default_factory=PPERequirements)


class CameraConfigUpdate(BaseModel):
    """Kamera konfigürasyonu güncelleme isteği."""

    name: Optional[str] = None
    source: Optional[str] = None
    source_type: Optional[CameraSourceType] = None
    enabled: Optional[bool] = None
    detection_classes: Optional[Dict[str, bool]] = None
    required_ppe: Optional[PPERequirements] = None
