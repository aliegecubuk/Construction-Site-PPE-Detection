"""
Stream Router — Angular'ın <img> etiketi ile tükettiği MJPEG endpoint'leri.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_camera_service, get_stream_service
from app.core.exceptions import CameraNotFoundError
from app.services.camera_service import CameraService
from app.services.stream_service import StreamService

router = APIRouter(prefix="/stream", tags=["Stream"])


@router.get("/mjpeg/{camera_id}")
async def mjpeg_stream(
    camera_id: str,
    stream_service: StreamService = Depends(get_stream_service),
    camera_service: CameraService = Depends(get_camera_service),
):
    """
    Belirli kameranın annotate edilmiş MJPEG akışını sunar.

    Angular tarafı bu endpoint'i doğrudan kullanır:
        <img src="http://localhost:8000/api/v1/stream/mjpeg/camera_1" />
    """
    try:
        await camera_service.get_camera(camera_id)
    except CameraNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    return StreamingResponse(
        stream_service.generate_mjpeg_stream(camera_id),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.get("/active")
async def get_active_streams(
    stream_service: StreamService = Depends(get_stream_service),
):
    """Aktif stream'leri ve bağlı istemci sayılarını döner."""
    return stream_service.get_active_streams()
