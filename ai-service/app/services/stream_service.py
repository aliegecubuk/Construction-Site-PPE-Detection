"""
Stream Service — Annotated frame'leri MJPEG olarak Angular'a sunar.
"""

from __future__ import annotations

import asyncio
import threading
from datetime import datetime
from typing import AsyncGenerator, Dict, Optional, Tuple

from loguru import logger

from app.core.config import settings


class StreamService:
    """Kamera başına son annotate edilmiş JPEG frame'i saklar ve MJPEG üretir."""

    def __init__(self) -> None:
        self._frames: Dict[str, bytes] = {}
        self._versions: Dict[str, int] = {}
        self._subscribers: Dict[str, int] = {}
        self._last_frame_at: Dict[str, datetime] = {}
        self._lock = threading.Lock()

    def publish_frame(self, camera_id: str, jpeg_bytes: bytes) -> None:
        """Analiz pipeline'ından gelen annotate edilmiş JPEG frame'i kaydeder."""
        with self._lock:
            self._frames[camera_id] = jpeg_bytes
            self._versions[camera_id] = self._versions.get(camera_id, 0) + 1
            self._last_frame_at[camera_id] = datetime.utcnow()

    def get_latest_frame(self, camera_id: str) -> Tuple[Optional[bytes], int]:
        """Kameranın son JPEG frame'ini ve sürüm numarasını döner."""
        with self._lock:
            return self._frames.get(camera_id), self._versions.get(camera_id, 0)

    async def generate_mjpeg_stream(
        self,
        camera_id: str,
    ) -> AsyncGenerator[bytes, None]:
        """
        Angular <img> etiketi için MJPEG stream üretir.

        Python servis varsayılanı:
            GET http://localhost:8000/api/v1/stream/mjpeg/{camera_id}
        """
        frame_interval = settings.MJPEG_FRAME_INTERVAL_MS / 1000.0
        last_version = -1

        with self._lock:
            self._subscribers[camera_id] = self._subscribers.get(camera_id, 0) + 1

        logger.info(f"[Stream] MJPEG istemcisi bağlandı: {camera_id}")

        try:
            while True:
                frame, version = self.get_latest_frame(camera_id)
                if frame is None or version == last_version:
                    await asyncio.sleep(frame_interval)
                    continue

                last_version = version
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
                )
        finally:
            with self._lock:
                current = self._subscribers.get(camera_id, 0)
                if current <= 1:
                    self._subscribers.pop(camera_id, None)
                else:
                    self._subscribers[camera_id] = current - 1
            logger.info(f"[Stream] MJPEG istemcisi ayrıldı: {camera_id}")

    def get_active_streams(self) -> Dict[str, Dict[str, Optional[str]]]:
        """Aktif stream'lerin subscriber sayısını ve son frame zamanını döner."""
        with self._lock:
            return {
                camera_id: {
                    "subscribers": self._subscribers.get(camera_id, 0),
                    "last_frame_at": (
                        self._last_frame_at.get(camera_id).isoformat()
                        if self._last_frame_at.get(camera_id)
                        else None
                    ),
                }
                for camera_id in set(self._frames) | set(self._subscribers)
            }
