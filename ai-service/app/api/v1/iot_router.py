"""
IoT Router — Sensör verileri endpoint'leri.
"""

from typing import List

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_iot_service
from app.models.schemas.iot import EnvironmentData, SensorReading
from app.services.iot_service import IoTService

router = APIRouter(prefix="/iot", tags=["IoT Sensors"])


@router.get("/readings", response_model=List[SensorReading])
async def get_readings(
    limit: int = Query(20, ge=1, le=200),
    service: IoTService = Depends(get_iot_service),
):
    """Son sensör okumalarını getirir."""
    return await service.get_latest_readings(limit=limit)


@router.post("/readings", response_model=SensorReading, status_code=201)
async def post_reading(
    reading: SensorReading,
    service: IoTService = Depends(get_iot_service),
):
    """Yeni sensör okuması gönderir (dummy generator veya gerçek sensör)."""
    return await service.process_reading(reading)


@router.post("/environment", response_model=EnvironmentData)
async def evaluate_environment(
    data: EnvironmentData,
    service: IoTService = Depends(get_iot_service),
):
    """Toplu çevresel veriyi değerlendirir ve şiddet seviyelerini atar."""
    return service.evaluate_environment(data)
