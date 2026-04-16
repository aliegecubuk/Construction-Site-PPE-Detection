"""
Risk Router — Risk skorlama endpoint'leri.

Endpoints:
    GET  /risk/current   → Anlık risk raporu (tüm kameralar + IoT)
    POST /risk/calculate → Manuel risk hesaplama
"""

from fastapi import APIRouter, Depends
from loguru import logger

from app.api.dependencies import (
    get_detection_service,
    get_iot_service,
    get_risk_engine,
)
from app.models.schemas.risk import RiskCalculateRequest, RiskReport
from app.services.detection_service import DetectionService
from app.services.iot_service import IoTService
from app.services.risk_engine import RiskEngine
from iot.dummy_generator import DummySensorGenerator

router = APIRouter(prefix="/risk", tags=["Risk Engine"])

# Dummy generator instance (IoT verisi olmadığında simülasyon için)
_dummy_generator = DummySensorGenerator(location="Şantiye Genel")


@router.get(
    "/current",
    response_model=RiskReport,
    summary="Anlık risk raporu",
)
async def get_current_risk(
    engine: RiskEngine = Depends(get_risk_engine),
    detection_service: DetectionService = Depends(get_detection_service),
    iot_service: IoTService = Depends(get_iot_service),
):
    """
    Anlık risk raporu üretir.

    1. Son tespit sonuçlarını getirir (tüm kameralardan).
    2. IoT verisi üretir (dummy generator).
    3. İkisini birleştirerek risk skoru hesaplar.
    """
    try:
        # Son tespitleri al
        latest_detections = await detection_service.get_latest(limit=20)

        # IoT verisi üret (dummy)
        env_data = _dummy_generator.generate_environment()

        # IoT severity değerlendirmesi
        env_data = iot_service.evaluate_environment(env_data)

        # Risk hesapla
        report = engine.calculate(
            detection_results=latest_detections,
            environment=env_data,
        )

        return report

    except Exception as exc:
        logger.error(f"Risk hesaplama hatası: {exc}")
        # Hata durumunda güvenli varsayılan döner
        return RiskReport(
            total_score=0.0,
            risk_level="low",
            recommendation="Risk hesaplanamadı — sistem verisi yetersiz.",
        )


@router.post(
    "/calculate",
    response_model=RiskReport,
    summary="Manuel risk hesaplama",
)
async def calculate_risk(
    request: RiskCalculateRequest,
    engine: RiskEngine = Depends(get_risk_engine),
):
    """
    Manuel risk hesaplama.

    İhlal sayıları ve sensör değerlerini doğrudan göndererek
    risk skoru hesaplatabilirsiniz.

    Örnek body:
    ```json
    {
        "violation_counts": {"NO-Hardhat": 3, "NO-Mask": 1},
        "gas_level": 85.0,
        "temperature": 38.0,
        "noise_level": 95.0,
        "location": "B Blok"
    }
    ```
    """
    try:
        return engine.calculate_from_request(request)
    except Exception as exc:
        logger.error(f"Manuel risk hesaplama hatası: {exc}")
        return RiskReport(
            total_score=0.0,
            risk_level="low",
            recommendation="Hesaplama sırasında hata oluştu.",
        )
