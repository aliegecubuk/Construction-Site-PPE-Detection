"""
REPORT-AI — Loglama Konfigürasyonu
====================================
Loguru tabanlı merkezi loglama ayarları.
"""

import sys
from pathlib import Path

from loguru import logger

from app.core.config import settings


def setup_logging() -> None:
    """Uygulama genelinde loglama sistemini yapılandırır."""
    log_dir = Path("..") / "logs" / "ai"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Varsayılan Loguru handler'ını kaldır
    logger.remove()

    # Konsol çıktısı
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # Dosya çıktısı (rotasyonlu)
    logger.add(
        log_dir / "report_ai_{time:YYYY-MM-DD}.log",
        level="DEBUG",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        encoding="utf-8",
    )

    logger.info(f"Loglama sistemi başlatıldı — seviye: {settings.LOG_LEVEL}")
