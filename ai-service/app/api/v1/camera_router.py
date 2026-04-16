"""
Camera Router — Kamera CRUD, sınıf toggle ve yaşam döngüsü endpoint'leri.

Bu router hiçbir iş mantığı içermez; tüm işlemleri CameraService'e delege eder.
Hata yakalama blokları ile domain exception'lar HTTP yanıtlarına dönüştürülür.

Endpoints:
    GET    /cameras                       → Tüm kameraları listele
    GET    /cameras/{id}                  → Tek kamera detayı
    POST   /cameras                       → Yeni kamera ekle
    PUT    /cameras/{id}                  → Kamera güncelle (partial)
    DELETE /cameras/{id}                  → Kamera sil
    PUT    /cameras/{id}/classes          → Toplu sınıf güncelle
    PATCH  /cameras/{id}/classes/{class}  → Tekil sınıf toggle
    GET    /cameras/{id}/status           → Kamera durumu
"""

from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from loguru import logger

from app.api.dependencies import get_camera_service, get_camera_telemetry_service
from app.core.exceptions import CameraNotFoundError, ReportAIBaseError
from app.models.schemas.camera import (
    CameraConfig,
    CameraConfigUpdate,
    CameraStatusResponse,
    PPERequirements,
    PPERequirementsUpdate,
)
from app.models.schemas.telemetry import CameraTelemetrySnapshot
from app.services.camera_service import CameraService, DuplicateCameraError
from app.services.camera_telemetry_service import CameraTelemetryService

router = APIRouter(prefix="/cameras", tags=["Cameras"])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Ortak hata yakalama wrapper
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _handle_not_found(exc: CameraNotFoundError) -> None:
    raise HTTPException(status_code=404, detail=exc.message)


def _handle_duplicate(exc: DuplicateCameraError) -> None:
    raise HTTPException(status_code=409, detail=exc.message)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CRUD Endpoint'leri
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get("/", response_model=List[CameraConfig], summary="Tüm kameraları listele")
async def list_cameras(
    enabled_only: bool = Query(False, description="Sadece aktif kameraları getir"),
    service: CameraService = Depends(get_camera_service),
):
    """Tüm kameraları veya sadece aktif olanları listeler."""
    try:
        if enabled_only:
            return await service.get_enabled_cameras()
        return await service.get_all_cameras()
    except Exception as exc:
        logger.error(f"Kamera listeleme hatası: {exc}")
        raise HTTPException(status_code=500, detail="Kameralar listelenirken hata oluştu.")


@router.get(
    "/{camera_id}",
    response_model=CameraConfig,
    summary="Kamera detayı",
)
async def get_camera(
    camera_id: str = Path(..., description="Kamera benzersiz kimliği"),
    service: CameraService = Depends(get_camera_service),
):
    """Belirli bir kameranın konfigürasyonunu getirir."""
    try:
        return await service.get_camera(camera_id)
    except CameraNotFoundError as exc:
        _handle_not_found(exc)


@router.post(
    "/",
    response_model=CameraConfig,
    status_code=201,
    summary="Yeni kamera ekle",
)
async def add_camera(
    config: CameraConfig,
    service: CameraService = Depends(get_camera_service),
):
    """
    Yeni kamera ekler.

    • detection_classes boş bırakılırsa tüm sınıflar aktif olarak atanır.
    • Aynı camera_id mevcutsa 409 Conflict döner.
    """
    try:
        return await service.add_camera(config)
    except DuplicateCameraError as exc:
        _handle_duplicate(exc)
    except Exception as exc:
        logger.error(f"Kamera ekleme hatası: {exc}")
        raise HTTPException(status_code=500, detail="Kamera eklenirken hata oluştu.")


@router.put(
    "/{camera_id}",
    response_model=CameraConfig,
    summary="Kamera güncelle (partial)",
)
async def update_camera(
    camera_id: str,
    update: CameraConfigUpdate,
    service: CameraService = Depends(get_camera_service),
):
    """Kamera konfigürasyonunu kısmi güncelleme ile günceller."""
    try:
        return await service.update_camera(camera_id, update)
    except CameraNotFoundError as exc:
        _handle_not_found(exc)


@router.delete("/{camera_id}", status_code=204, summary="Kamera sil")
async def delete_camera(
    camera_id: str,
    service: CameraService = Depends(get_camera_service),
):
    """Kamerayı siler. Konfigürasyon JSON'dan da kaldırılır."""
    try:
        await service.delete_camera(camera_id)
    except CameraNotFoundError as exc:
        _handle_not_found(exc)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Sınıf Toggle Endpoint'leri
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.put(
    "/{camera_id}/classes",
    response_model=CameraConfig,
    summary="Toplu sınıf güncelle",
)
async def update_detection_classes(
    camera_id: str,
    class_updates: Dict[str, bool],
    service: CameraService = Depends(get_camera_service),
):
    """
    Kameranın tespit sınıflarını toplu günceller (aç/kapa butonları).

    Body örneği:
    ```json
    {"Hardhat": true, "Mask": false, "Safety Vest": true}
    ```
    """
    try:
        return await service.update_detection_classes(camera_id, class_updates)
    except CameraNotFoundError as exc:
        _handle_not_found(exc)


@router.patch(
    "/{camera_id}/classes/{class_name}",
    response_model=CameraConfig,
    summary="Tekil sınıf toggle",
)
async def toggle_single_class(
    camera_id: str,
    class_name: str = Path(..., description="Sınıf adı (ör: Hardhat)"),
    active: bool = Query(..., description="True=Aktif, False=Pasif"),
    service: CameraService = Depends(get_camera_service),
):
    """
    Tek bir tespit sınıfını aç veya kapat.

    Örnek: `PATCH /cameras/cam_01/classes/Hardhat?active=true`
    """
    try:
        return await service.toggle_single_class(camera_id, class_name, active)
    except CameraNotFoundError as exc:
        _handle_not_found(exc)


@router.get(
    "/{camera_id}/requirements",
    response_model=PPERequirements,
    summary="KKD gereksinimlerini getir",
)
async def get_required_ppe(
    camera_id: str,
    service: CameraService = Depends(get_camera_service),
):
    """
    Kamera için zorunlu KKD ayarlarını döner.

    Python API varsayılanı:
        GET http://localhost:8000/api/v1/cameras/{camera_id}/requirements
    """
    try:
        return await service.get_required_ppe(camera_id)
    except CameraNotFoundError as exc:
        _handle_not_found(exc)


@router.get(
    "/{camera_id}/telemetry",
    response_model=CameraTelemetrySnapshot,
    summary="Kamera için son IoT telemetrisi",
)
async def get_camera_telemetry(
    camera_id: str,
    camera_service: CameraService = Depends(get_camera_service),
    telemetry_service: CameraTelemetryService = Depends(get_camera_telemetry_service),
):
    """
    Kamera için en son üretilen dummy IoT telemetrisini döner.

    Python API varsayılanı:
        GET http://localhost:8000/api/v1/cameras/{camera_id}/telemetry
    """
    try:
        await camera_service.get_camera(camera_id)
    except CameraNotFoundError as exc:
        _handle_not_found(exc)

    snapshot = telemetry_service.get_latest(camera_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Telemetri henüz üretilmedi.")
    return snapshot


@router.put(
    "/{camera_id}/requirements",
    response_model=CameraConfig,
    summary="KKD gereksinimlerini güncelle",
)
async def update_required_ppe(
    camera_id: str,
    update: PPERequirementsUpdate,
    service: CameraService = Depends(get_camera_service),
):
    """
    Kamera için zorunlu KKD toggle'larını günceller.

    Python API varsayılanı:
        PUT http://localhost:8000/api/v1/cameras/{camera_id}/requirements

    Body örneği:
    ```json
    {"hardhat": true, "safetyVest": false, "mask": true}
    ```
    """
    try:
        return await service.update_required_ppe(camera_id, update)
    except CameraNotFoundError as exc:
        _handle_not_found(exc)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Durum Endpoint'i
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get(
    "/{camera_id}/status",
    response_model=CameraStatusResponse,
    summary="Kamera durumu",
)
async def get_camera_status(
    camera_id: str,
    service: CameraService = Depends(get_camera_service),
):
    """Kameranın anlık durum bilgisini döner."""
    try:
        return await service.get_camera_status(camera_id)
    except CameraNotFoundError as exc:
        _handle_not_found(exc)
