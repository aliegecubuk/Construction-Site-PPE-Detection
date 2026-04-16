"""
Alert Service Unit Test
"""

import pytest

from app.core.constants import VIOLATION_CLASSES
from app.models.schemas.detection import BoundingBox, DetectionResult
from app.models.schemas.iot import EnvironmentData, SeverityLevel
from app.repositories.alert_repository import AlertRepository
from app.services.alert_service import AlertService


class TestAlertService:
    """AlertService birim testleri."""

    def setup_method(self):
        self.repo = AlertRepository()
        self.service = AlertService(repository=self.repo)

    @pytest.mark.asyncio
    async def test_no_alert_when_no_violations(self):
        result = DetectionResult(
            camera_id="cam_01",
            detections=[],
            violation_count=0,
            person_count=0,
        )
        alert = await self.service.check_detection_violations(result)
        assert alert is None

    @pytest.mark.asyncio
    async def test_alert_created_on_violation(self):
        result = DetectionResult(
            camera_id="cam_01",
            detections=[
                BoundingBox(
                    x1=10, y1=10, x2=100, y2=100,
                    confidence=0.85,
                    class_name="NO-Hardhat",
                    class_id=2,
                ),
            ],
            violation_count=1,
            person_count=1,
        )
        alert = await self.service.check_detection_violations(result)
        assert alert is not None
        assert alert.camera_id == "cam_01"
        assert "NO-Hardhat" in alert.violations

    @pytest.mark.asyncio
    async def test_no_environment_alert_for_normal_data(self):
        data = EnvironmentData(
            gas_level=20, temperature=25, humidity=50,
            noise_level=60, vibration=2.0,
        )
        alert = await self.service.check_environment_alert(data)
        assert alert is None

    @pytest.mark.asyncio
    async def test_environment_alert_for_critical_data(self):
        data = EnvironmentData(
            gas_level=90,
            gas_severity=SeverityLevel.CRITICAL,
            temperature=45,
            temperature_severity=SeverityLevel.CRITICAL,
            humidity=50,
            noise_level=60,
            vibration=2.0,
        )
        alert = await self.service.check_environment_alert(data)
        assert alert is not None
        assert alert.priority.value == "critical"

    @pytest.mark.asyncio
    async def test_emit_environment_alerts_for_warning_and_critical(self):
        from app.models.schemas.camera import CameraConfig, CameraSourceType

        camera = CameraConfig(
            camera_id="cam_iot",
            name="Kamera IoT",
            source="video/sample.mp4",
            source_type=CameraSourceType.LOCAL_FILE,
            enabled=True,
        )
        data = EnvironmentData(
            gas_level=55,
            gas_severity=SeverityLevel.WARNING,
            temperature=44,
            temperature_severity=SeverityLevel.CRITICAL,
            humidity=50,
            noise_level=60,
            vibration=2.0,
            location="Kamera IoT",
        )

        alerts = await self.service.emit_environment_alerts(
            camera=camera,
            data=data,
            occurred_at=data.timestamp,
            frame_number=12,
        )

        assert len(alerts) == 2
        assert any(alert.priority.value == "critical" for alert in alerts)
        assert any("IoT Gaz Uyarı" in alert.violations for alert in alerts)
