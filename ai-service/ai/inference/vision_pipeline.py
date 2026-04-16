"""
VisionPipeline — Ana görüntü analiz pipeline'ı.

Bu modül, tüm sistemin kalbidir. Her kamera için:
    1) CameraManager'dan frame okur.
    2) YOLODetector ile nesne tespiti yapar.
    3) PostProcessor ile kamera bazlı sınıf filtreleme uygular.
    4) Filtrelenmiş sonuçları DetectionService'e iletir.
    5) İhlal varsa AlertService'i tetikler.

Asenkron çalışır: Her kamera için ayrı bir asyncio Task oluşturulur.
CPU-bound YOLO predict(), ThreadPoolExecutor üzerinden çağrılır.

Katmanlı mimari kuralı:
    VisionPipeline (ai/) → DetectionService (app/services/) → DetectionRepository (app/repositories/)
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime
from time import monotonic
from typing import Dict, List, Optional

import cv2
from loguru import logger

from ai.camera.camera_manager import CameraManager
from ai.inference.detector import YOLODetector
from ai.inference.frame_annotator import FrameAnnotator
from ai.inference.post_processor import PostProcessor
from app.core.constants import PPE_REQUIREMENT_TO_DETECTION
from app.core.config import settings
from app.models.schemas.camera import CameraConfig
from app.models.schemas.detection import BoundingBox, DetectionResult
from app.models.schemas.iot import EnvironmentData
from app.services.alert_service import AlertService
from app.services.camera_service import CameraService
from app.services.camera_telemetry_service import CameraTelemetryService
from app.services.detection_service import DetectionService
from app.services.stream_service import StreamService


class VisionPipeline:
    """
    Asenkron çoklu kamera görüntü analiz pipeline'ı.

    Kullanım (main.py startup'ta):
        pipeline = VisionPipeline(
            camera_service=camera_service,
            detection_service=detection_service,
            detector=YOLODetector(...),
        )
        await pipeline.start()
        # ...
        await pipeline.stop()
    """

    def __init__(
        self,
        camera_service: CameraService,
        detection_service: DetectionService,
        detector: YOLODetector,
        alert_service: AlertService,
        stream_service: StreamService,
        telemetry_service: CameraTelemetryService,
        camera_manager: Optional[CameraManager] = None,
    ) -> None:
        self._camera_service = camera_service
        self._detection_service = detection_service
        self._detector = detector
        self._alert_service = alert_service
        self._stream_service = stream_service
        self._telemetry_service = telemetry_service
        self._camera_manager = camera_manager or CameraManager()
        self._post_processor = PostProcessor(
            confidence_threshold=settings.MODEL_CONFIDENCE_THRESHOLD,
        )
        self._annotator = FrameAnnotator()

        # Frame kaydetmek icin klasor altyapisi
        os.makedirs("data/frames", exist_ok=True)

        # Aktif analiz task'ları
        self._analysis_tasks: Dict[str, asyncio.Task] = {}
        self._running = False

        # Son sonuçları sakla (her kamera için en son DetectionResult)
        self._latest_results: Dict[str, DetectionResult] = {}
        self._latest_telemetry = {}

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Yaşam Döngüsü
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def start(self) -> None:
        """
        Pipeline'ı başlatır:
            1) YOLO modelini yükler.
            2) JSON'dan kamera konfigürasyonlarını yükler.
            3) Her aktif kamera için CameraManager + analiz task'ı başlatır.
        """
        if self._running:
            logger.warning("VisionPipeline zaten çalışıyor.")
            return

        self._running = True
        logger.info("=" * 60)
        logger.info("VisionPipeline başlatılıyor...")
        enabled_cameras = await self._camera_service.get_enabled_cameras()
        started = 0

        for cam_config in enabled_cameras:
            try:
                self._telemetry_service.register_camera(cam_config)
                self._camera_manager.add_camera(cam_config)
                if self._camera_manager.start(cam_config.camera_id):
                    self._start_analysis_task(cam_config)
                    started += 1
                else:
                    logger.warning(
                        f"Kamera başlatılamadı (atlanıyor): {cam_config.camera_id}"
                    )
            except Exception as exc:
                logger.error(
                    f"Kamera başlatma hatası ({cam_config.camera_id}): {exc}"
                )

        logger.info(
            f"VisionPipeline hazır: {started}/{len(enabled_cameras)} kamera aktif"
        )
        logger.info("=" * 60)

    async def stop(self) -> None:
        """
        Pipeline'ı graceful durdurur:
            1) Tüm analiz task'larını iptal eder.
            2) CameraManager'ı durdurur.
            3) YOLO modelini bellekten kaldırır.
        """
        self._running = False
        logger.info("VisionPipeline durduruluyor...")

        # Analiz task'larını iptal et
        for camera_id, task in self._analysis_tasks.items():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            logger.debug(f"[{camera_id}] Analiz task'ı iptal edildi.")

        self._analysis_tasks.clear()

        # Kameraları durdur
        self._camera_manager.stop_all()

        # Modeli kaldır (opsiyonel)
        if self._detector.is_loaded:
            self._detector.unload_model()

        logger.info("VisionPipeline durduruldu.")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Analiz Döngüsü
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _start_analysis_task(self, config: CameraConfig) -> None:
        """Kamera için async analiz task'ı oluşturur."""
        task = asyncio.create_task(
            self._analysis_loop(config.camera_id),
            name=f"analysis-{config.camera_id}",
        )
        self._analysis_tasks[config.camera_id] = task
        logger.info(f"[{config.camera_id}] Analiz task'ı başlatıldı.")

    async def _analysis_loop(self, camera_id: str) -> None:
        """
        Tek bir kamera için sürekli çalışan asenkron analiz döngüsü.

        Her iterasyonda:
            1) CameraManager'dan son frame'i al
            2) YOLO ile tespit yap (async — ThreadPool)
            3) Kamera konfigürasyonuna göre sınıf filtrele
            4) Sonucu DetectionService'e kaydet
        """
        interval_s = settings.INFERENCE_INTERVAL_MS / 1000.0
        frame_counter = 0
        next_iot_due_at = 0.0

        logger.debug(
            f"[{camera_id}] Analiz döngüsü başladı "
            f"(interval: {settings.INFERENCE_INTERVAL_MS}ms)"
        )

        while self._running:
            try:
                # ── 1) Kamera konfigürasyonunu ve aktiflik durumunu kontrol et ──
                try:
                    cam_config = await self._camera_service.get_camera(camera_id)
                except Exception as exc:
                    logger.warning(
                        f"[{camera_id}] Kamera konfigürasyonu okunamadı: {exc}"
                    )
                    await asyncio.sleep(interval_s)
                    continue

                if not cam_config.enabled:
                    # Eger kamera pasif ise CPU harcamamak adina bekle ve atla
                    # Daha kisa bir bekleme (2 sn) ile durum degisikligine daha hızlı tepki ver
                    await asyncio.sleep(2.0)
                    continue

                active_classes = cam_config.detection_classes

                # ── 2) Frame oku ──
                frame = self._camera_manager.get_frame(camera_id)
                if frame is None:
                    await asyncio.sleep(interval_s)
                    continue

                frame_counter += 1

                # ── 3) YOLO predict (async bridge) ──
                raw_detections: List[BoundingBox] = await self._detector.predict_async(
                    frame
                )

                filtered = self._post_processor.process(
                    detections=raw_detections,
                    active_classes=active_classes,
                )

                # ── 4) Sonucu işle ve kaydet ──
                result = await self._detection_service.process_and_store(
                    camera_id=camera_id,
                    detections=filtered,
                    active_classes=active_classes,
                    frame_number=frame_counter,
                    violations=self._resolve_required_ppe_violations(
                        filtered,
                        cam_config,
                    ),
                )

                self._latest_results[camera_id] = result
                alerts = await self._alert_service.emit_ppe_alerts(
                    camera=cam_config,
                    violations=result.violations,
                    occurred_at=result.timestamp,
                    frame_number=frame_counter,
                )

                if alerts:
                    annotated_for_disk = self._build_annotated_frame(
                        frame=frame,
                        camera=cam_config,
                        detections=filtered,
                        result=result,
                        telemetry=self._latest_telemetry.get(camera_id),
                    )
                    for alert in alerts:
                        try:
                            cv2.imwrite(f"data/frames/{alert.alert_id}.jpg", annotated_for_disk)
                        except Exception as e:
                            logger.error(f"Gorsel kaydedilemedi: {e}")

                now = monotonic()
                if now >= next_iot_due_at:
                    telemetry = self._telemetry_service.generate_for_camera(cam_config)
                    self._latest_telemetry[camera_id] = telemetry
                    environment = EnvironmentData(
                        gas_level=telemetry.gas_level,
                        gas_severity=telemetry.gas_severity,
                        temperature=telemetry.temperature,
                        temperature_severity=telemetry.temperature_severity,
                        humidity=telemetry.humidity,
                        humidity_severity=telemetry.humidity_severity,
                        noise_level=telemetry.noise_level,
                        noise_severity=telemetry.noise_severity,
                        vibration=telemetry.vibration,
                        vibration_severity=telemetry.vibration_severity,
                        timestamp=telemetry.occurred_at,
                        location=telemetry.camera_name,
                    )
                    await self._alert_service.emit_environment_alerts(
                        camera=cam_config,
                        data=environment,
                        occurred_at=telemetry.occurred_at,
                        frame_number=frame_counter,
                    )
                    next_iot_due_at = now + settings.IOT_POLL_INTERVAL_S

                annotated = self._build_annotated_frame(
                    frame=frame,
                    camera=cam_config,
                    detections=filtered,
                    result=result,
                    telemetry=self._latest_telemetry.get(camera_id),
                )
                success, encoded = cv2.imencode(
                    ".jpg",
                    annotated,
                    [
                        int(cv2.IMWRITE_JPEG_QUALITY),
                        settings.MJPEG_JPEG_QUALITY,
                    ],
                )
                if success:
                    self._stream_service.publish_frame(camera_id, encoded.tobytes())

                # Her 50 frame'de bir özet logla
                if frame_counter % 50 == 0:
                    logger.info(
                        f"[{camera_id}] Frame #{frame_counter}: "
                        f"{len(raw_detections)} ham → {len(filtered)} filtreli, "
                        f"{result.violation_count} ihlal"
                    )

                await asyncio.sleep(interval_s)

            except asyncio.CancelledError:
                logger.debug(f"[{camera_id}] Analiz görevi iptal edildi.")
                break
            except Exception as exc:
                logger.error(
                    f"[{camera_id}] Analiz döngüsü hatası: {exc}"
                )
                await asyncio.sleep(interval_s * 2)  # Hata sonrası ekstra bekleme

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Erişim Metotları
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def get_latest_result(self, camera_id: str) -> Optional[DetectionResult]:
        """Belirli bir kameranın en son tespit sonucunu döner."""
        return self._latest_results.get(camera_id)

    def get_all_latest_results(self) -> Dict[str, DetectionResult]:
        """Tüm kameraların en son sonuçlarını döner."""
        return dict(self._latest_results)

    def _resolve_required_ppe_violations(
        self,
        detections: List[BoundingBox],
        camera: CameraConfig,
    ) -> List[str]:
        """Kamera gereksinimine göre frame üzerindeki eksik KKD ihlallerini çıkarır."""
        detected_classes = {d.class_name for d in detections}
        violations: List[str] = []
        requirements = camera.required_ppe.model_dump(by_alias=False)

        for requirement_key, mapping in PPE_REQUIREMENT_TO_DETECTION.items():
            if not requirements.get(requirement_key, False):
                continue
            if mapping["missing"] in detected_classes:
                violations.append(mapping["label"])

        return violations

    def _build_annotated_frame(
        self,
        frame,
        camera: CameraConfig,
        detections: List[BoundingBox],
        result: DetectionResult,
        telemetry=None,
    ):
        """Bounding box ve durum overlay'leri ile Angular'a gidecek frame'i üretir."""
        annotated = self._annotator.annotate(frame, detections)
        annotated = self._annotator.add_info_overlay(
            annotated,
            camera_name=camera.name,
            person_count=result.person_count,
            violation_count=result.violation_count,
        )

        required = []
        if camera.required_ppe.hardhat:
            required.append("Baret")
        if camera.required_ppe.safety_vest:
            required.append("Yelek")
        if camera.required_ppe.mask:
            required.append("Maske")

        requirements_text = "Gerekli PPE: " + (", ".join(required) if required else "-")
        violations_text = "Aktif Ihlal: " + (", ".join(result.violations) if result.violations else "Yok")

        cv2.putText(
            annotated,
            requirements_text,
            (10, max(annotated.shape[0] - 34, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            annotated,
            violations_text,
            (10, max(annotated.shape[0] - 12, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 0, 255) if result.violations else (0, 255, 0),
            2,
            cv2.LINE_AA,
        )
        if telemetry is not None:
            telemetry_text = (
                f"IoT  S:{telemetry.temperature:.1f}C "
                f"G:{telemetry.gas_level:.0f}ppm "
                f"N:{telemetry.noise_level:.0f}dB "
                f"Nem:{telemetry.humidity:.0f}% "
                f"Tit:{telemetry.vibration:.1f}"
            )
            cv2.putText(
                annotated,
                telemetry_text,
                (10, 54),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (102, 255, 178),
                2,
                cv2.LINE_AA,
            )
        return annotated

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def active_cameras(self) -> int:
        """Aktif analiz task sayısı."""
        return sum(
            1 for t in self._analysis_tasks.values() if not t.done()
        )
