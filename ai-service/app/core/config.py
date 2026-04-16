"""
REPORT-AI — Uygulama Konfigürasyonu
====================================
Pydantic Settings ile tip-güvenli ortam değişkeni yönetimi.
Tüm konfigürasyon değerleri buradan okunur; farklı katmanlar
doğrudan .env veya OS ortam değişkenlerinden okuma YAPMAZ.

Kullanım:
    from app.core.config import settings
    print(settings.MODEL_WEIGHTS_PATH)
"""

from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Uygulama genelinde kullanılan konfigürasyon değerleri."""

    # ── Genel ─────────────────────────────────────────────────────────
    PROJECT_NAME: str = "REPORT-AI"
    VERSION: str = "0.2.0"
    DEBUG: bool = False

    # ── API ───────────────────────────────────────────────────────────
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:4200"]

    # ── Veritabanı (İleride aktif edilecek) ────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./report_ai_dev.db"

    # ── AI / Model ────────────────────────────────────────────────────
    MODEL_WEIGHTS_PATH: str = "ai/weights/best.pt"
    MODEL_CONFIDENCE_THRESHOLD: float = 0.5
    MODEL_IOU_THRESHOLD: float = 0.45
    MODEL_DEVICE: str = "cpu"  # "cpu" | "cuda:0"

    # ── Kamera ────────────────────────────────────────────────────────
    CAMERA_CONFIG_PATH: str = "ai/config/camera_class_map.json"
    INFERENCE_INTERVAL_MS: int = 15000  # Her kamera için ms cinsinden çıkarım aralığı
    FRAME_BUFFER_SIZE: int = 30
    RTSP_RECONNECT_ATTEMPTS: int = 5
    RTSP_RECONNECT_DELAY_S: float = 3.0
    MJPEG_FRAME_INTERVAL_MS: int = 120
    MJPEG_JPEG_QUALITY: int = 85
    ALERT_COOLDOWN_SECONDS: int = 8
    DOTNET_ALERT_WEBHOOK_URL: str = "http://localhost:8080/api/python/violations"
    DOTNET_ALERT_WEBHOOK_TIMEOUT_S: float = 5.0

    # ── IoT ───────────────────────────────────────────────────────────
    IOT_POLL_INTERVAL_S: float = 5.0
    IOT_SPIKE_PROBABILITY: float = 0.06

    # ── Risk Engine ───────────────────────────────────────────────────
    RISK_VISION_WEIGHT: float = 0.6
    RISK_IOT_WEIGHT: float = 0.4

    # ── Loglama ───────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"

    # ── Pydantic Settings Konfig ──────────────────────────────────────
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # ── Yardımcı Propertyler ──────────────────────────────────────────
    @property
    def weights_path(self) -> Path:
        """Model ağırlık dosyasının Path nesnesi."""
        return Path(self.MODEL_WEIGHTS_PATH)

    @property
    def camera_config_path(self) -> Path:
        """Kamera konfigürasyon JSON dosyasının Path nesnesi."""
        return Path(self.CAMERA_CONFIG_PATH)


# Tekil (singleton) settings nesnesi — her yerden import edilir.
settings = Settings()
