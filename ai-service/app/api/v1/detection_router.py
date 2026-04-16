"""
Detection Router — Tespit sonuçları endpoint'leri.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_detection_service
from app.models.schemas.detection import DetectionResult
from app.services.detection_service import DetectionService

router = APIRouter(prefix="/detections", tags=["Detections"])


@router.get("/latest", response_model=List[DetectionResult])
async def get_latest_detections(
    camera_id: Optional[str] = Query(None, description="Kamera filtresi"),
    limit: int = Query(10, ge=1, le=100, description="Sonuç limiti"),
    service: DetectionService = Depends(get_detection_service),
):
    """Son tespit sonuçlarını getirir (opsiyonel kamera filtresi)."""
    return await service.get_latest(camera_id=camera_id, limit=limit)


@router.get("/camera/{camera_id}", response_model=List[DetectionResult])
async def get_detections_by_camera(
    camera_id: str,
    limit: int = Query(10, ge=1, le=100),
    service: DetectionService = Depends(get_detection_service),
):
    """Belirli bir kameranın tespit sonuçlarını getirir."""
    return await service.get_latest(camera_id=camera_id, limit=limit)
