"""
IoT Collector — Sensör verilerini toplayan servis.
Gerçek donanım geldiğinde bu modül fiziksel sensörlere bağlanacak.
Şu an DummySensorGenerator ile çalışır.
"""

import asyncio
from typing import Callable, Optional

from loguru import logger

from iot.dummy_generator import DummySensorGenerator
from app.models.schemas.iot import EnvironmentData


class IoTCollector:
    """
    Periyodik olarak sensör verisi toplayan servis.

    Kullanım:
        collector = IoTCollector(interval=5.0)
        collector.start(callback=on_new_data)
        ...
        collector.stop()
    """

    def __init__(
        self,
        interval: float = 5.0,
        location: str = "Genel Alan",
    ) -> None:
        self._interval = interval
        self._generator = DummySensorGenerator(location=location)
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(
        self,
        callback: Optional[Callable[[EnvironmentData], None]] = None,
    ) -> None:
        """Periyodik veri toplama döngüsünü başlatır."""
        self._running = True
        logger.info(
            f"IoT Collector başlatıldı (aralık: {self._interval}s)"
        )

        while self._running:
            data = self._generator.generate_environment()

            if callback:
                callback(data)

            logger.debug(
                f"[IoT] Sıcaklık={data.temperature}°C, "
                f"Gaz={data.gas_level}ppm, "
                f"Nem={data.humidity}%"
            )

            await asyncio.sleep(self._interval)

    def stop(self) -> None:
        """Veri toplama döngüsünü durdurur."""
        self._running = False
        logger.info("IoT Collector durduruldu.")
