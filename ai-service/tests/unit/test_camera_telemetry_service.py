from app.models.schemas.camera import CameraConfig, CameraSourceType
from app.repositories.iot_repository import IoTRepository
from app.services.camera_telemetry_service import CameraTelemetryService
from app.services.iot_service import IoTService


def test_generate_camera_telemetry_snapshot():
    service = CameraTelemetryService(iot_service=IoTService(repository=IoTRepository()))
    camera = CameraConfig(
        camera_id="camera_1",
        name="Kamera 1",
        source="video/sample.mp4",
        source_type=CameraSourceType.LOCAL_FILE,
        enabled=True,
    )

    snapshot = service.generate_for_camera(camera)

    assert snapshot.camera_id == "camera_1"
    assert snapshot.camera_name == "Kamera 1"
    assert 0 <= snapshot.gas_level <= 100
    assert 10 <= snapshot.temperature <= 55
    assert service.get_latest("camera_1") is not None
