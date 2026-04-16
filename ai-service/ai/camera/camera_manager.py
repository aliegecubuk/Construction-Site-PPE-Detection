"""
Camera Manager — Production-grade çoklu kamera orkestrasyonu.

Bu sınıf:
    • Birden fazla kamerayı (RTSP/MP4/USB) yönetir.
    • Her kamera için ayrı daemon thread'de frame okur.
    • RTSP kesintilerinde otomatik reconnect uygular.
    • FPS ölçümü ve sağlık kontrolü metrikleri sağlar.
    • Thread-safe FrameBuffer aracılığıyla consumer'lara frame dağıtır.

Üretim kuralı:
    frame okuma (I/O-bound) → thread
    frame analizi (CPU-bound) → VisionPipeline tarafından yönetilir
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
from loguru import logger

from ai.camera.frame_buffer import FrameBuffer
from ai.camera.rtsp_reader import RTSPReader
from ai.camera.video_reader import VideoReader
from app.core.config import settings
from app.models.schemas.camera import CameraConfig, CameraSourceType


@dataclass
class CameraMetrics:
    """Kamera performans metrikleri."""

    frames_read: int = 0
    frames_dropped: int = 0
    reconnect_count: int = 0
    last_frame_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    fps: float = 0.0

    # FPS hesaplama için iç state
    _fps_frame_count: int = field(default=0, repr=False)
    _fps_last_time: float = field(default_factory=time.perf_counter, repr=False)


class CameraManager:
    """
    Çoklu kamera orkestratör — her kamera için:
        1) Uygun okuyucu (RTSP veya Video) oluşturur
        2) Daemon thread'de sürekli frame okur
        3) Frame'leri FrameBuffer'a yazar
        4) RTSP kesintisinde otomatik reconnect dener
        5) FPS ve frame sayacı metrikleri tutar
    """

    def __init__(self) -> None:
        self._cameras: Dict[str, Dict] = {}
        self._stop_events: Dict[str, threading.Event] = {}
        self._threads: Dict[str, threading.Thread] = {}
        self._metrics: Dict[str, CameraMetrics] = {}
        self._lock = threading.Lock()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Kamera Ekleme / Kaldırma
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def add_camera(self, config: CameraConfig) -> None:
        """Kamera konfigürasyonunu ekler ve okuyucu oluşturur."""
        with self._lock:
            if config.camera_id in self._cameras:
                logger.warning(
                    f"Kamera zaten kayıtlı, güncelleniyor: {config.camera_id}"
                )
                self.stop(config.camera_id)

            reader = self._create_reader(config)

            self._cameras[config.camera_id] = {
                "config": config,
                "reader": reader,
                "buffer": FrameBuffer(max_size=settings.FRAME_BUFFER_SIZE),
            }
            self._metrics[config.camera_id] = CameraMetrics()

            logger.info(
                f"Kamera kayıt edildi: {config.camera_id} ({config.name}) "
                f"[{config.source_type.value}]"
            )

    def remove_camera(self, camera_id: str) -> None:
        """Kamerayı durdurur ve kayıttan siler."""
        self.stop(camera_id)
        with self._lock:
            self._cameras.pop(camera_id, None)
            self._metrics.pop(camera_id, None)
            logger.info(f"Kamera kayıttan silindi: {camera_id}")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Başlat / Durdur
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def start(self, camera_id: str) -> bool:
        """
        Kameranın frame okuma thread'ini başlatır.

        Returns:
            True başarılıysa, False kamera bulunamazsa veya bağlanamazsa.
        """
        cam = self._cameras.get(camera_id)
        if cam is None:
            logger.error(f"Kamera bulunamadı: {camera_id}")
            return False

        # Zaten çalışıyorsa atla
        if camera_id in self._threads and self._threads[camera_id].is_alive():
            logger.warning(f"Kamera zaten çalışıyor: {camera_id}")
            return True

        reader = cam["reader"]
        if not reader.open():
            logger.error(f"Kamera bağlantısı açılamadı: {camera_id}")
            return False

        stop_event = threading.Event()
        self._stop_events[camera_id] = stop_event

        metrics = self._metrics[camera_id]
        metrics.started_at = datetime.utcnow()

        thread = threading.Thread(
            target=self._read_loop,
            args=(camera_id, reader, cam["buffer"], stop_event, metrics),
            daemon=True,
            name=f"cam-{camera_id}",
        )
        self._threads[camera_id] = thread
        thread.start()

        logger.info(f"Kamera başlatıldı: {camera_id}")
        return True

    def start_all(self) -> Dict[str, bool]:
        """
        Kayıtlı tüm kameraları başlatır.

        Returns:
            {camera_id: başarı_durumu} dict'i.
        """
        results = {}
        for camera_id in list(self._cameras.keys()):
            results[camera_id] = self.start(camera_id)
        return results

    def stop(self, camera_id: str) -> None:
        """Belirli bir kamerayı graceful durdurur."""
        if camera_id in self._stop_events:
            self._stop_events[camera_id].set()

        if camera_id in self._threads:
            thread = self._threads[camera_id]
            if thread.is_alive():
                thread.join(timeout=5)
                if thread.is_alive():
                    logger.warning(f"Kamera thread'i düzgün kapanmadı: {camera_id}")

            del self._threads[camera_id]

        self._stop_events.pop(camera_id, None)
        logger.info(f"Kamera durduruldu: {camera_id}")

    def stop_all(self) -> None:
        """Tüm kameraları graceful durdurur."""
        for camera_id in list(self._stop_events.keys()):
            self.stop(camera_id)
        logger.info("Tüm kameralar durduruldu.")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Frame Erişimi
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def get_frame(self, camera_id: str) -> Optional[np.ndarray]:
        """Belirli bir kameradan en son frame'i döner."""
        cam = self._cameras.get(camera_id)
        if cam is None:
            return None
        return cam["buffer"].get()

    def get_camera_ids(self) -> List[str]:
        """Kayıtlı kamera ID'lerini döner."""
        return list(self._cameras.keys())

    def is_running(self, camera_id: str) -> bool:
        """Kameranın thread'inin aktif olup olmadığını kontrol eder."""
        return (
            camera_id in self._threads
            and self._threads[camera_id].is_alive()
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Metrikler
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def get_metrics(self, camera_id: str) -> Optional[CameraMetrics]:
        """Kameranın performans metriklerini döner."""
        return self._metrics.get(camera_id)

    def get_all_metrics(self) -> Dict[str, CameraMetrics]:
        """Tüm kamera metriklerini döner."""
        return dict(self._metrics)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Arka Plan Thread Döngüsü (Private)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _read_loop(
        self,
        camera_id: str,
        reader,
        buffer: FrameBuffer,
        stop_event: threading.Event,
        metrics: CameraMetrics,
    ) -> None:
        """
        Arka plan daemon thread'inde çalışan frame okuma döngüsü.

        RTSP kesintisinde:
            • settings.RTSP_RECONNECT_ATTEMPTS kadar tekrar bağlanmayı dener.
            • Her denemede settings.RTSP_RECONNECT_DELAY_S kadar bekler.
            • Tüm denemeler başarısız olursa thread sonlanır.
        """
        consecutive_failures = 0
        max_failures = 30  # Arka arkaya bu kadar boş frame sonrası reconnect dene

        logger.debug(f"[{camera_id}] Frame okuma döngüsü başladı.")

        while not stop_event.is_set():
            try:
                frame = reader.read_frame()

                if frame is not None:
                    buffer.put(frame)
                    metrics.frames_read += 1
                    metrics.last_frame_at = datetime.utcnow()
                    consecutive_failures = 0

                    # ── FPS hesapla (her 30 frame'de bir) ──
                    metrics._fps_frame_count += 1
                    if metrics._fps_frame_count >= 30:
                        now = time.perf_counter()
                        elapsed = now - metrics._fps_last_time
                        if elapsed > 0:
                            metrics.fps = round(
                                metrics._fps_frame_count / elapsed, 1
                            )
                        metrics._fps_frame_count = 0
                        metrics._fps_last_time = now

                else:
                    consecutive_failures += 1
                    metrics.frames_dropped += 1

                    if consecutive_failures >= max_failures:
                        logger.warning(
                            f"[{camera_id}] {max_failures} ardışık boş frame — "
                            "reconnect deneniyor."
                        )
                        if self._try_reconnect(camera_id, reader):
                            consecutive_failures = 0
                        else:
                            logger.error(
                                f"[{camera_id}] Reconnect başarısız — thread sonlanıyor."
                            )
                            break

                    stop_event.wait(0.01)  # CPU'yu yormamak için kısa bekleme

            except Exception as exc:
                logger.error(f"[{camera_id}] Frame okuma hatası: {exc}")
                consecutive_failures += 1
                stop_event.wait(0.1)

        # Cleanup
        try:
            reader.close()
        except Exception as exc:
            logger.warning(f"[{camera_id}] Reader kapatma hatası: {exc}")

        logger.debug(f"[{camera_id}] Frame okuma döngüsü sonlandı.")

    def _try_reconnect(self, camera_id: str, reader) -> bool:
        """
        RTSP/video bağlantısını yeniden kurmayı dener.

        Returns:
            True başarılı ise.
        """
        max_attempts = settings.RTSP_RECONNECT_ATTEMPTS
        delay = settings.RTSP_RECONNECT_DELAY_S

        for attempt in range(1, max_attempts + 1):
            logger.info(
                f"[{camera_id}] Reconnect denemesi {attempt}/{max_attempts}..."
            )

            try:
                reader.close()
            except Exception:
                pass

            time.sleep(delay)

            try:
                if reader.open():
                    metrics = self._metrics.get(camera_id)
                    if metrics:
                        metrics.reconnect_count += 1
                    logger.info(
                        f"[{camera_id}] Reconnect başarılı (deneme {attempt})."
                    )
                    return True
            except Exception as exc:
                logger.warning(
                    f"[{camera_id}] Reconnect denemesi {attempt} başarısız: {exc}"
                )

        return False

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Fabrika (Private)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @staticmethod
    def _create_reader(config: CameraConfig):
        """Kamera türüne göre uygun reader instance'ı oluşturur."""
        if config.source_type == CameraSourceType.LOCAL_FILE:
            return VideoReader(config.source, loop=True)
        else:
            return RTSPReader(
                config.source,
                reconnect_attempts=settings.RTSP_RECONNECT_ATTEMPTS,
            )
