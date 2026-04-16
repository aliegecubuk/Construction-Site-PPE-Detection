"""
Alert Router — Alarm/ihlal endpoint'leri.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_alert_service
from app.models.schemas.alert import Alert, AlertAcknowledge
from app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/", response_model=List[Alert])
async def list_alerts(
    service: AlertService = Depends(get_alert_service),
):
    """Tüm alarmları listeler."""
    return await service.get_all_alerts()


@router.get("/active", response_model=List[Alert])
async def list_active_alerts(
    service: AlertService = Depends(get_alert_service),
):
    """Sadece aktif (onaylanmamış) alarmları listeler."""
    return await service.get_active_alerts()


@router.post(
    "/acknowledge/{alert_id}",
    response_model=Alert,
)
async def acknowledge_alert(
    alert_id: str,
    ack: AlertAcknowledge,
    service: AlertService = Depends(get_alert_service),
):
    """Alarmı onaylar (kabul eder)."""
    try:
        return await service.acknowledge_alert(alert_id, ack)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{alert_id}/frame")
async def get_alert_frame(alert_id: str):
    """Alarm/ihlal anına ait PNG/JPG frame'i döndürür."""
    import os
    from fastapi.responses import FileResponse
    frame_path = f"data/frames/{alert_id}.jpg"
    if os.path.exists(frame_path):
        return FileResponse(frame_path)
    raise HTTPException(status_code=404, detail="Görsel bulunamadı")
