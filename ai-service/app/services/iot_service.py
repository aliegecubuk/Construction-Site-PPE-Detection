"""
IoT Service — IoT sensör verilerini işleme ve eşik kontrolü.
"""

from typing import List

from loguru import logger

from app.core.constants import IOT_THRESHOLDS
from app.models.schemas.iot import (
    EnvironmentData,
    SensorReading,
    SensorType,
    SeverityLevel,
)
from app.repositories.iot_repository import IoTRepository


class IoTService:
    """IoT sensör verilerini işleyen iş mantığı katmanı."""

    def __init__(self, repository: IoTRepository) -> None:
        self._repo = repository

    def evaluate_severity(
        self, sensor_type: str, value: float
    ) -> SeverityLevel:
        """
        Sensör değerini eşik değerlerine göre değerlendirir.

        Returns:
            SeverityLevel.NORMAL / WARNING / CRITICAL
        """
        thresholds = IOT_THRESHOLDS.get(sensor_type)
        if not thresholds:
            return SeverityLevel.NORMAL

        if value >= thresholds["critical"]:
            return SeverityLevel.CRITICAL
        elif value >= thresholds["warning"]:
            return SeverityLevel.WARNING
        return SeverityLevel.NORMAL

    async def process_reading(self, reading: SensorReading) -> SensorReading:
        """
        Sensör okumasını değerlendirir ve kaydeder.
        Şiddet seviyesini otomatik hesaplar.
        """
        reading.severity = self.evaluate_severity(
            reading.sensor_type.value, reading.value
        )

        await self._repo.create(reading)

        if reading.severity in (SeverityLevel.WARNING, SeverityLevel.CRITICAL):
            logger.warning(
                f"[IoT] {reading.sensor_type.value} = {reading.value} "
                f"{reading.unit} → {reading.severity.value.upper()}"
            )

        return reading

    def evaluate_environment(self, data: EnvironmentData) -> EnvironmentData:
        """Toplu çevresel veriyi değerlendirir, her değer için şiddet atar."""
        data.gas_severity = self.evaluate_severity("gas_level", data.gas_level)
        data.temperature_severity = self.evaluate_severity(
            "temperature", data.temperature
        )
        data.humidity_severity = self.evaluate_severity(
            "humidity", data.humidity
        )
        data.noise_severity = self.evaluate_severity(
            "noise_level", data.noise_level
        )
        data.vibration_severity = self.evaluate_severity(
            "vibration", data.vibration
        )
        return data

    async def get_latest_readings(
        self, limit: int = 20
    ) -> List[SensorReading]:
        """Son sensör okumalarını getirir."""
        return await self._repo.get_latest_readings(limit=limit)
