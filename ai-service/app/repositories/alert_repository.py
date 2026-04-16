"""
Alert Repository — Alarm kayıtları veri erişim katmanı.
"""

from typing import List, Optional

from app.models.schemas.alert import Alert, AlertStatus
from app.repositories.base_repository import InMemoryRepository


class AlertRepository(InMemoryRepository[Alert]):
    """Alarm/ihlal kayıtları için in-memory repository."""

    async def create(self, entity: Alert) -> Alert:
        self._store[entity.alert_id] = entity
        return entity

    async def get_active(self) -> List[Alert]:
        """Sadece aktif (henüz onaylanmamış) alarmları döner."""
        return [
            alert
            for alert in self._store.values()
            if alert.status == AlertStatus.ACTIVE
        ]

    async def get_by_camera(self, camera_id: str) -> List[Alert]:
        """Belirli bir kameraya ait alarmları döner."""
        return [
            alert
            for alert in self._store.values()
            if alert.camera_id == camera_id
        ]
