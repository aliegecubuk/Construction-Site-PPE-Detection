"""
RTSP Reader — RTSP protokolü üzerinden video akışı okuyucu.
"""

import cv2
import numpy as np
from loguru import logger
from typing import Optional


class RTSPReader:
    """
    RTSP stream'den frame okuyan sınıf.

    Kullanım:
        reader = RTSPReader("rtsp://192.168.1.101:554/stream")
        reader.open()
        frame = reader.read_frame()
        reader.close()
    """

    def __init__(self, source: str, reconnect_attempts: int = 3) -> None:
        self._source = source
        self._reconnect_attempts = reconnect_attempts
        self._cap: Optional[cv2.VideoCapture] = None

    @property
    def is_opened(self) -> bool:
        return self._cap is not None and self._cap.isOpened()

    def open(self) -> bool:
        """RTSP bağlantısını açar."""
        try:
            self._cap = cv2.VideoCapture(self._source)
            if self.is_opened:
                logger.info(f"RTSP bağlantısı açıldı: {self._source}")
                return True
            else:
                logger.error(f"RTSP bağlantısı açılamadı: {self._source}")
                return False
        except Exception as e:
            logger.error(f"RTSP bağlantı hatası: {e}")
            return False

    def read_frame(self) -> Optional[np.ndarray]:
        """Bir frame okur. Başarısızsa None döner."""
        if not self.is_opened:
            return None

        ret, frame = self._cap.read()
        if ret:
            return frame

        logger.warning(f"Frame okunamadı: {self._source}")
        return None

    def close(self) -> None:
        """Bağlantıyı kapatır ve kaynakları serbest bırakır."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
            logger.info(f"RTSP bağlantısı kapatıldı: {self._source}")

    def get_properties(self) -> dict:
        """Stream özelliklerini döner."""
        if not self.is_opened:
            return {}
        return {
            "width": int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": self._cap.get(cv2.CAP_PROP_FPS),
        }
