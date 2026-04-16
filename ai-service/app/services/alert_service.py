"""
Alert Service — PPE ihlallerini kaydeder ve .NET SignalR katmanına iletir.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from loguru import logger

from app.models.schemas.alert import (
    Alert,
    AlertAcknowledge,
    AlertPriority,
    AlertStatus,
    AlertType,
)
from app.models.schemas.camera import CameraConfig
from app.models.schemas.detection import DetectionResult
from app.models.schemas.iot import EnvironmentData, SeverityLevel
from app.models.schemas.violation import ViolationEvent
from app.repositories.alert_repository import AlertRepository
from app.services.alert_delivery_service import AlertDeliveryService


class AlertService:
    """İhlal ve alarm yönetimi iş mantığı."""

    def __init__(
        self,
        repository: AlertRepository,
        delivery_service: Optional[AlertDeliveryService] = None,
        cooldown_seconds: int = 8,
    ) -> None:
        self._repo = repository
        self._delivery_service = delivery_service or AlertDeliveryService(webhook_url="")
        self._cooldown = timedelta(seconds=cooldown_seconds)
        self._last_emitted: Dict[Tuple[str, str], datetime] = {}

    async def emit_ppe_alerts(
        self,
        camera: CameraConfig,
        violations: List[str],
        occurred_at: datetime,
        frame_number: int = 0,
    ) -> List[Alert]:
        """
        Kamera için tekil PPE ihlallerini kaydeder ve .NET webhook'una yollar.

        Aynı kamera + ihlal tipi için cooldown süresi içinde tekrar event üretmez.
        """
        if not camera.enabled:
            return []

        created: List[Alert] = []
        for violation in sorted(set(violations)):
            key = (camera.camera_id, violation)
            previous_at = self._last_emitted.get(key)
            if previous_at and (occurred_at - previous_at) < self._cooldown:
                continue

            self._last_emitted[key] = occurred_at

            alert = Alert(
                alert_id=str(uuid4()),
                alert_type=AlertType.PPE_VIOLATION,
                priority=AlertPriority.HIGH,
                title=f"{camera.name} - {violation}",
                description=f"{camera.name} kamerasinda {violation} tespit edildi.",
                camera_id=camera.camera_id,
                created_at=occurred_at,
                violations=[violation],
            )
            await self._repo.create(alert)
            created.append(alert)

            event = ViolationEvent(
                eventId=alert.alert_id,
                cameraId=camera.camera_id,
                cameraName=camera.name,
                violationType=violation,
                message=alert.description,
                occurredAt=occurred_at,
                frameNumber=frame_number,
            )
            await self._delivery_service.publish_violation(event)
            logger.warning(f"[ALERT] {camera.camera_id} -> {violation}")

        return created

    async def emit_environment_alerts(
        self,
        camera: CameraConfig,
        data: EnvironmentData,
        occurred_at: datetime,
        frame_number: int = 0,
    ) -> List[Alert]:
        """
        Kamera bazlı IoT telemetrisini değerlendirir ve warning/critical alarm üretir.
        """
        if not camera.enabled:
            return []

        factors = self._extract_environment_factors(data)
        created: List[Alert] = []

        for violation_type, description, priority in factors:
            key = (camera.camera_id, violation_type)
            previous_at = self._last_emitted.get(key)
            if previous_at and (occurred_at - previous_at) < self._cooldown:
                continue

            self._last_emitted[key] = occurred_at

            alert = Alert(
                alert_id=str(uuid4()),
                alert_type=AlertType.ENVIRONMENTAL,
                priority=priority,
                title=f"{camera.name} - {violation_type}",
                description=description,
                camera_id=camera.camera_id,
                created_at=occurred_at,
                violations=[violation_type],
            )
            await self._repo.create(alert)
            created.append(alert)

            event = ViolationEvent(
                eventId=alert.alert_id,
                cameraId=camera.camera_id,
                cameraName=camera.name,
                violationType=violation_type,
                message=description,
                occurredAt=occurred_at,
                frameNumber=frame_number,
            )
            await self._delivery_service.publish_violation(event)
            logger.warning(f"[IOT ALERT] {camera.camera_id} -> {violation_type}")

        return created

    async def check_detection_violations(
        self,
        result: DetectionResult,
    ) -> Optional[Alert]:
        """
        Geriye dönük uyumluluk için tekil DetectionResult'tan toplu alert üretir.
        """
        violation_names = result.violations or [
            det.class_name
            for det in result.detections
            if det.class_name.startswith("NO-")
        ]

        if not violation_names and result.violation_count == 0:
            return None

        alert = Alert(
            alert_id=str(uuid4()),
            alert_type=AlertType.PPE_VIOLATION,
            priority=AlertPriority.HIGH if len(violation_names) >= 2 else AlertPriority.MEDIUM,
            title=f"KKD İhlali — {result.camera_id}",
            description=", ".join(violation_names) if violation_names else "KKD ihlali tespit edildi.",
            camera_id=result.camera_id,
            created_at=result.timestamp,
            violations=violation_names,
        )
        await self._repo.create(alert)
        return alert

    async def check_environment_alert(
        self, data: EnvironmentData
    ) -> Optional[Alert]:
        """
        Çevresel verileri kontrol edip, kritik değer varsa alarm oluşturur.
        """
        critical_factors = []
        if data.gas_severity == SeverityLevel.CRITICAL:
            critical_factors.append(f"Gaz: {data.gas_level} ppm")
        if data.temperature_severity == SeverityLevel.CRITICAL:
            critical_factors.append(f"Sıcaklık: {data.temperature} °C")
        if data.noise_severity == SeverityLevel.CRITICAL:
            critical_factors.append(f"Gürültü: {data.noise_level} dB")
        if data.vibration_severity == SeverityLevel.CRITICAL:
            critical_factors.append(f"Titreşim: {data.vibration} mm/s")

        if not critical_factors:
            return None

        alert = Alert(
            alert_id=str(uuid4()),
            alert_type=AlertType.ENVIRONMENTAL,
            priority=AlertPriority.CRITICAL,
            title=f"Çevresel Tehlike — {data.location}",
            description=(
                f"Kritik seviyede değer(ler): {', '.join(critical_factors)}"
            ),
            violations=critical_factors,
        )

        await self._repo.create(alert)
        logger.critical(f"[ALERT] Çevresel alarm: {alert.description}")
        return alert

    async def acknowledge_alert(
        self, alert_id: str, ack: AlertAcknowledge
    ) -> Alert:
        """Alarmı onaylar (kabul eder)."""
        alert = await self._repo.get_by_id(alert_id)
        if not alert:
            raise ValueError(f"Alarm bulunamadı: {alert_id}")

        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.utcnow()
        await self._repo.update(alert_id, alert)

        logger.info(
            f"[ALERT] Alarm onaylandı: {alert_id} — {ack.acknowledged_by}"
        )
        return alert

    async def get_active_alerts(self) -> List[Alert]:
        """Aktif alarmları getirir."""
        return await self._repo.get_active()

    async def get_all_alerts(self) -> List[Alert]:
        """Tüm alarmları getirir."""
        return await self._repo.get_all()

    def _extract_environment_factors(
        self,
        data: EnvironmentData,
    ) -> List[Tuple[str, str, AlertPriority]]:
        """Warning ve critical sensörleri bağımsız alert faktörlerine çevirir."""
        metrics = [
            ("Gaz", data.gas_level, "ppm", data.gas_severity),
            ("Sıcaklık", data.temperature, "°C", data.temperature_severity),
            ("Nem", data.humidity, "%", data.humidity_severity),
            ("Gürültü", data.noise_level, "dB", data.noise_severity),
            ("Titreşim", data.vibration, "mm/s", data.vibration_severity),
        ]
        factors: List[Tuple[str, str, AlertPriority]] = []

        for label, value, unit, severity in metrics:
            if severity == SeverityLevel.NORMAL:
                continue

            severity_label = "Kritik" if severity == SeverityLevel.CRITICAL else "Uyarı"
            priority = (
                AlertPriority.CRITICAL
                if severity == SeverityLevel.CRITICAL
                else AlertPriority.MEDIUM
            )
            violation_type = f"IoT {label} {severity_label}"
            description = (
                f"{data.location} için {label.lower()} değeri {value} {unit} ölçüldü "
                f"ve {severity_label.lower()} eşik seviyesine ulaştı."
            )
            factors.append((violation_type, description, priority))

        return factors
