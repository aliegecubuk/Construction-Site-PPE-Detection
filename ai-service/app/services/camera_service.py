"""
Camera Service — Kamera yaşam döngüsü, konfigürasyon yönetimi ve JSON persistence.

Bu servis:
    • Kamera CRUD operasyonlarını yönetir.
    • Her değişiklikte konfigürasyonu disk üzerindeki JSON'a persist eder.
    • Kamera bazlı tespit sınıflarını dinamik olarak günceller (aç/kapa toggle).
    • Başlangıçta JSON dosyasından seed verisi yükler.

Katmanlı mimari kuralı:
    Router → CameraService (burada iş mantığı) → CameraRepository (veri erişimi)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from app.core.config import settings
from app.core.constants import DETECTION_CLASSES
from app.core.exceptions import CameraNotFoundError, ReportAIBaseError
from app.models.schemas.camera import (
    CameraConfig,
    CameraConfigUpdate,
    PPERequirements,
    PPERequirementsUpdate,
    CameraSourceType,
    CameraStatus,
    CameraStatusResponse,
)
from app.repositories.camera_repository import CameraRepository


class DuplicateCameraError(ReportAIBaseError):
    """Aynı ID'ye sahip kamera zaten mevcutken fırlatılır."""

    def __init__(self, camera_id: str):
        super().__init__(f"Bu ID'ye sahip kamera zaten mevcut: {camera_id}")


class CameraService:
    """
    Kamera CRUD, konfigürasyon yönetimi ve JSON persistence servisi.

    Tüm yazma operasyonları (_persist_to_json aracılığıyla) disk'e de yansıtılır;
    böylece uygulama yeniden başlatıldığında son durum korunur.
    """

    def __init__(self, repository: CameraRepository) -> None:
        self._repo = repository
        report_ai_root = Path(__file__).resolve().parents[2]
        config_path = settings.camera_config_path
        self._config_path: Path = (
            config_path
            if config_path.is_absolute()
            else (report_ai_root / config_path).resolve()
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  JSON Persistence
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def load_from_json(self) -> int:
        """
        Disk üzerindeki JSON dosyasından kameraları in-memory repository'ye yükler.
        Uygulama başlangıcında (startup) bir kez çağrılır.

        Returns:
            Yüklenen kamera sayısı.

        Raises:
            FileNotFoundError: JSON dosyası bulunamazsa.
            json.JSONDecodeError: JSON parse hatası.
        """
        if not self._config_path.exists():
            logger.warning(
                f"Kamera konfigürasyon dosyası bulunamadı: {self._config_path}. "
                "Boş konfigürasyon ile devam ediliyor."
            )
            return 0

        try:
            raw = self._config_path.read_text(encoding="utf-8")
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.error(f"JSON parse hatası ({self._config_path}): {exc}")
            raise

        cameras_data: List[Dict[str, Any]] = data.get("cameras", [])
        loaded = 0

        for cam_dict in cameras_data:
            try:
                config = CameraConfig(**cam_dict)
                config.source = self._normalize_source_path(
                    config.source,
                    config.source_type,
                )
                # Eksik sınıfları varsayılan False ile doldur
                config.detection_classes = self._ensure_all_classes(
                    config.detection_classes
                )
                if config.required_ppe is None:
                    config.required_ppe = PPERequirements()
                await self._repo.create(config)
                loaded += 1
                logger.debug(f"Kamera yüklendi: {config.camera_id} — {config.name}")
            except Exception as exc:
                logger.warning(
                    f"Kamera yüklenemedi (atlanıyor): {cam_dict.get('camera_id', '?')} — {exc}"
                )

        logger.info(
            f"{loaded}/{len(cameras_data)} kamera JSON'dan yüklendi "
            f"({self._config_path})"
        )
        return loaded

    async def _persist_to_json(self) -> None:
        """
        In-memory repository'deki tüm kameraları disk üzerindeki JSON'a yazar.
        Her yazma operasyonundan sonra çağrılır — atomic write pattern.
        """
        try:
            all_cameras = await self._repo.get_all()
            payload = {
                "cameras": [cam.model_dump(mode="json") for cam in all_cameras]
            }

            # Atomic write: önce geçici dosyaya yaz, sonra rename et
            tmp_path = self._config_path.with_suffix(".tmp")
            tmp_path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            tmp_path.replace(self._config_path)

            logger.debug(
                f"Kamera konfigürasyonu persist edildi: {len(all_cameras)} kamera"
            )
        except Exception as exc:
            logger.error(f"JSON persist hatası: {exc}")
            # Persist hatası kritik değil — in-memory verisi hâlâ güncel.
            # Bir sonraki yazma denemesinde tekrar denenecek.

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  CRUD Operasyonları
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def add_camera(self, config: CameraConfig) -> CameraConfig:
        """
        Yeni kamera ekler.

        • Var olan ID kontrolü yapar.
        • Eksik detection_classes alanlarını varsayılan True ile doldurur.
        • Sonucu JSON'a persist eder.
        """
        # Duplicate kontrolü
        existing = await self._repo.get_by_id(config.camera_id)
        if existing is not None:
            raise DuplicateCameraError(config.camera_id)

        # Varsayılan sınıfları ata (tümü True)
        if not config.detection_classes:
            config.detection_classes = {cls: True for cls in DETECTION_CLASSES}
        else:
            config.detection_classes = self._ensure_all_classes(
                config.detection_classes
            )

        created = await self._repo.create(config)
        await self._persist_to_json()

        logger.info(f"Kamera eklendi: {created.camera_id} — {created.name}")
        return created

    async def get_camera(self, camera_id: str) -> CameraConfig:
        """
        Kamera konfigürasyonunu getirir.

        Raises:
            CameraNotFoundError: Kamera bulunamazsa.
        """
        camera = await self._repo.get_by_id(camera_id)
        if camera is None:
            raise CameraNotFoundError(camera_id)
        return camera

    async def get_all_cameras(self) -> List[CameraConfig]:
        """Tüm kameraları listeler."""
        return await self._repo.get_all()

    async def get_enabled_cameras(self) -> List[CameraConfig]:
        """Sadece aktif (enabled=True) kameraları listeler."""
        return await self._repo.get_enabled()

    async def update_camera(
        self, camera_id: str, update: CameraConfigUpdate
    ) -> CameraConfig:
        """
        Kamera konfigürasyonunu kısmi güncelleme (partial update) ile günceller.
        Sadece gönderilen alanlar değişir; diğerleri korunur.
        """
        existing = await self.get_camera(camera_id)

        update_data = update.model_dump(exclude_unset=True)
        updated_config = existing.model_copy(update=update_data)

        await self._repo.update(camera_id, updated_config)
        await self._persist_to_json()

        logger.info(
            f"Kamera güncellendi: {camera_id} "
            f"(değişen alanlar: {list(update_data.keys())})"
        )
        return updated_config

    async def delete_camera(self, camera_id: str) -> bool:
        """
        Kamerayı siler ve JSON'dan kaldırır.

        Raises:
            CameraNotFoundError: Kamera bulunamazsa.
        """
        success = await self._repo.delete(camera_id)
        if not success:
            raise CameraNotFoundError(camera_id)

        await self._persist_to_json()
        logger.info(f"Kamera silindi: {camera_id}")
        return True

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Dinamik Sınıf Filtreleme (Toggle API)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def update_detection_classes(
        self, camera_id: str, class_updates: Dict[str, bool]
    ) -> CameraConfig:
        """
        Kameranın tespit sınıflarını toplu günceller (aç/kapa butonları).

        Bilinmeyen sınıf adları sessizce yoksayılır (log'a yazılır).

        Args:
            camera_id: Hedef kamera ID'si.
            class_updates: {"Hardhat": True, "Mask": False, ...}

        Returns:
            Güncellenmiş CameraConfig.
        """
        existing = await self.get_camera(camera_id)

        applied: Dict[str, bool] = {}
        ignored: List[str] = []

        for cls_name, is_active in class_updates.items():
            if cls_name in DETECTION_CLASSES:
                existing.detection_classes[cls_name] = is_active
                applied[cls_name] = is_active
            else:
                ignored.append(cls_name)

        if ignored:
            logger.warning(
                f"[{camera_id}] Bilinmeyen sınıflar yoksayıldı: {ignored}"
            )

        await self._repo.update(camera_id, existing)
        await self._persist_to_json()

        logger.info(
            f"[{camera_id}] Sınıf güncellendi: {applied} "
            f"(aktif: {sum(1 for v in existing.detection_classes.values() if v)}/"
            f"{len(existing.detection_classes)})"
        )
        return existing

    async def toggle_single_class(
        self, camera_id: str, class_name: str, is_active: bool
    ) -> CameraConfig:
        """Tekil sınıf aç/kapa toggle'ı."""
        return await self.update_detection_classes(
            camera_id, {class_name: is_active}
        )

    async def update_required_ppe(
        self,
        camera_id: str,
        update: PPERequirementsUpdate,
    ) -> CameraConfig:
        """
        Kameranın zorunlu KKD gereksinimlerini günceller.

        .NET orkestratör veya Angular doğrudan bu endpoint'i çağırabilir.
        """
        existing = await self.get_camera(camera_id)
        update_data = update.model_dump(exclude_unset=True, by_alias=False)
        existing.required_ppe = existing.required_ppe.model_copy(update=update_data)

        await self._repo.update(camera_id, existing)
        await self._persist_to_json()

        logger.info(
            f"[{camera_id}] KKD gereksinimleri güncellendi: "
            f"{existing.required_ppe.model_dump(by_alias=True)}"
        )
        return existing

    async def get_required_ppe(self, camera_id: str) -> PPERequirements:
        """Kameranın aktif KKD gereksinimlerini döner."""
        camera = await self.get_camera(camera_id)
        return camera.required_ppe

    def get_active_classes(self, config: CameraConfig) -> List[str]:
        """Kameranın aktif (True) tespit sınıflarının listesini döner."""
        return [
            cls_name
            for cls_name, is_active in config.detection_classes.items()
            if is_active
        ]

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Durum Raporu
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def get_camera_status(self, camera_id: str) -> CameraStatusResponse:
        """Kamera durum bilgisini döner."""
        camera = await self.get_camera(camera_id)
        active_count = sum(1 for v in camera.detection_classes.values() if v)

        return CameraStatusResponse(
            camera_id=camera.camera_id,
            name=camera.name,
            source_type=camera.source_type,
            enabled=camera.enabled,
            active_classes=active_count,
            required_ppe=camera.required_ppe,
            status=(
                CameraStatus.ACTIVE if camera.enabled else CameraStatus.INACTIVE
            ),
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Yardımcı (Private)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @staticmethod
    def _ensure_all_classes(
        classes: Dict[str, bool],
    ) -> Dict[str, bool]:
        """
        Verilen sınıf haritasını, desteklenen tüm sınıfları içerecek şekilde
        doldurur. Eksik sınıflar varsayılan olarak False atanır.
        """
        complete = {cls: False for cls in DETECTION_CLASSES}
        complete.update(classes)
        return complete

    def _normalize_source_path(
        self,
        source: str,
        source_type: CameraSourceType,
    ) -> str:
        """
        Yerel video yollarını farklı çalışma dizinlerinden bağımsız normalize eder.

        Arama sırası:
        1. Verilen path zaten mevcutsa onu kullan
        2. JSON config dizinine göre çöz
        3. `ai-service/` köküne göre çöz
        4. Repo köküne göre çöz
        """
        if source_type != CameraSourceType.LOCAL_FILE:
            return source

        raw_path = Path(source)
        if raw_path.is_absolute() and raw_path.exists():
            return str(raw_path)

        ai_service_root = Path(__file__).resolve().parents[2]
        repo_root = ai_service_root.parent
        candidates = [
            Path.cwd() / raw_path,
            self._config_path.resolve().parent / raw_path,
            ai_service_root / raw_path,
            repo_root / raw_path,
        ]

        for candidate in candidates:
            if candidate.exists():
                return str(candidate.resolve())

        logger.warning(f"Yerel video kaynağı çözümlenemedi, ham değer korunuyor: {source}")
        return source
