"""
API Dependencies — FastAPI Dependency Injection tanımları.

Service, Repository ve AI nesnelerini oluşturup router'lara enjekte eder.
Tüm singleton nesneler burada yönetilir.

Kullanım:
    @router.get("/")
    async def endpoint(service=Depends(get_camera_service)):
        ...
"""

from ai.inference.detector import YOLODetector
from ai.inference.vision_pipeline import VisionPipeline
from app.core.config import settings
from app.repositories.alert_repository import AlertRepository
from app.repositories.camera_repository import CameraRepository
from app.repositories.detection_repository import DetectionRepository
from app.repositories.iot_repository import IoTRepository
from app.services.alert_service import AlertService
from app.services.alert_delivery_service import AlertDeliveryService
from app.services.camera_service import CameraService
from app.services.camera_telemetry_service import CameraTelemetryService
from app.services.detection_service import DetectionService
from app.services.iot_service import IoTService
from app.services.risk_engine import RiskEngine
from app.services.stream_service import StreamService

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Singleton Repository Nesneleri (in-memory, uygulama ömrü boyunca yaşar)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_camera_repo = CameraRepository()
_detection_repo = DetectionRepository()
_iot_repo = IoTRepository()
_alert_repo = AlertRepository()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Service Nesneleri
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_camera_service = CameraService(repository=_camera_repo)
_detection_service = DetectionService(repository=_detection_repo)
_iot_service = IoTService(repository=_iot_repo)
_camera_telemetry_service = CameraTelemetryService(iot_service=_iot_service)
_stream_service = StreamService()
_alert_delivery_service = AlertDeliveryService(
    webhook_url=settings.DOTNET_ALERT_WEBHOOK_URL,
    timeout_seconds=settings.DOTNET_ALERT_WEBHOOK_TIMEOUT_S,
)
_alert_service = AlertService(
    repository=_alert_repo,
    delivery_service=_alert_delivery_service,
    cooldown_seconds=settings.ALERT_COOLDOWN_SECONDS,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Risk Engine
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_risk_engine = RiskEngine(
    vision_weight=settings.RISK_VISION_WEIGHT,
    iot_weight=settings.RISK_IOT_WEIGHT,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  AI Nesneleri (Lazy — model startup'ta yüklenir)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_detector = YOLODetector(
    weights_path=settings.MODEL_WEIGHTS_PATH,
    confidence=settings.MODEL_CONFIDENCE_THRESHOLD,
    iou_threshold=settings.MODEL_IOU_THRESHOLD,
    device=settings.MODEL_DEVICE,
)
_vision_pipeline = VisionPipeline(
    camera_service=_camera_service,
    detection_service=_detection_service,
    detector=_detector,
    alert_service=_alert_service,
    stream_service=_stream_service,
    telemetry_service=_camera_telemetry_service,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  FastAPI Depends() fonksiyonları
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def get_camera_service() -> CameraService:
    return _camera_service


def get_detection_service() -> DetectionService:
    return _detection_service


def get_iot_service() -> IoTService:
    return _iot_service


def get_camera_telemetry_service() -> CameraTelemetryService:
    return _camera_telemetry_service


def get_alert_service() -> AlertService:
    return _alert_service


def get_alert_delivery_service() -> AlertDeliveryService:
    return _alert_delivery_service


def get_stream_service() -> StreamService:
    return _stream_service


def get_risk_engine() -> RiskEngine:
    return _risk_engine


def get_detector() -> YOLODetector:
    return _detector


def get_vision_pipeline() -> VisionPipeline:
    return _vision_pipeline
