"""
IoT Repository — Sensör verileri veri erişim katmanı.
"""

from typing import List
from uuid import uuid4

from app.models.schemas.iot import SensorReading
from app.repositories.base_repository import InMemoryRepository


class IoTRepository(InMemoryRepository[SensorReading]):
    """IoT sensör okumaları için in-memory repository."""

    async def create(self, entity: SensorReading) -> SensorReading:
        record_id = str(uuid4())
        self._store[record_id] = entity
        return entity

    async def get_by_sensor_type(self, sensor_type: str) -> List[SensorReading]:
        """Belirli bir sensör türüne ait okumaları döner."""
        return [
            reading
            for reading in self._store.values()
            if reading.sensor_type.value == sensor_type
        ]

    async def get_latest_readings(self, limit: int = 20) -> List[SensorReading]:
        """Son N sensör okumasını döner."""
        results = list(self._store.values())
        results.sort(key=lambda x: x.timestamp, reverse=True)
        return results[:limit]
