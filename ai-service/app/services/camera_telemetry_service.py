"""
Camera Telemetry Service — Kamera bazlı dummy IoT telemetri üretimi ve saklama.
"""

from __future__ import annotations

from typing import Dict, Optional

from app.core.config import settings
from app.models.schemas.camera import CameraConfig
from app.models.schemas.telemetry import CameraTelemetrySnapshot
from app.services.iot_service import IoTService
from iot.dummy_generator import DummySensorGenerator


class CameraTelemetryService:
    """Her kamera için deterministik dummy IoT akışı üretir."""

    def __init__(self, iot_service: IoTService) -> None:
        self._iot_service = iot_service
        self._generators: Dict[str, DummySensorGenerator] = {}
        self._latest: Dict[str, CameraTelemetrySnapshot] = {}

    def register_camera(self, camera: CameraConfig) -> None:
        """Kamera için generator yoksa oluşturur."""
        if camera.camera_id in self._generators:
            return

        seed = sum(ord(char) for char in camera.camera_id)
        self._generators[camera.camera_id] = DummySensorGenerator(
            location=camera.name,
            spike_probability=settings.IOT_SPIKE_PROBABILITY,
            seed=seed,
        )

    def generate_for_camera(self, camera: CameraConfig) -> CameraTelemetrySnapshot:
        """Kamera için tek bir telemetri snapshot üretir ve cache'ler."""
        self.register_camera(camera)
        generator = self._generators[camera.camera_id]
        environment = self._iot_service.evaluate_environment(
            generator.generate_environment(),
        )
        snapshot = CameraTelemetrySnapshot(
            cameraId=camera.camera_id,
            cameraName=camera.name,
            occurredAt=environment.timestamp,
            gasLevel=environment.gas_level,
            gasSeverity=environment.gas_severity,
            temperature=environment.temperature,
            temperatureSeverity=environment.temperature_severity,
            humidity=environment.humidity,
            humiditySeverity=environment.humidity_severity,
            noiseLevel=environment.noise_level,
            noiseSeverity=environment.noise_severity,
            vibration=environment.vibration,
            vibrationSeverity=environment.vibration_severity,
        )
        self._latest[camera.camera_id] = snapshot
        return snapshot

    def get_latest(self, camera_id: str) -> Optional[CameraTelemetrySnapshot]:
        """Kamera için en son üretilen telemetriyi döner."""
        return self._latest.get(camera_id)
