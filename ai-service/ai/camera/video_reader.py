"""
Video Reader — Yerel video dosyası (MP4) okuyucu.
"""

from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from loguru import logger


class VideoReader:
    """
    Yerel MP4/AVI dosyalarından frame okuyan sınıf.

    Kullanım:
        reader = VideoReader("workspace/legacy-ml/source_files/hardhat.mp4")
        reader.open()
        frame = reader.read_frame()
        reader.close()
    """

    def __init__(self, file_path: str, loop: bool = True) -> None:
        self._file_path = Path(file_path)
        self._loop = loop
        self._cap: Optional[cv2.VideoCapture] = None

    @property
    def is_opened(self) -> bool:
        return self._cap is not None and self._cap.isOpened()

    def open(self) -> bool:
        """Video dosyasını açar."""
        if not self._file_path.exists():
            logger.error(f"Dosya bulunamadı: {self._file_path}")
            return False

        self._cap = cv2.VideoCapture(str(self._file_path))
        if self.is_opened:
            logger.info(f"Video açıldı: {self._file_path}")
            return True

        logger.error(f"Video açılamadı: {self._file_path}")
        return False

    def read_frame(self) -> Optional[np.ndarray]:
        """
        Bir frame okur. Video sonuna gelindiyse ve loop=True ise
        başa sarar.
        """
        if not self.is_opened:
            return None

        ret, frame = self._cap.read()
        if ret:
            return frame

        if self._loop:
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self._cap.read()
            if ret:
                return frame

        return None

    def close(self) -> None:
        """Dosyayı kapatır."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
            logger.info(f"Video kapatıldı: {self._file_path}")

    def get_properties(self) -> dict:
        """Video dosyası özelliklerini döner."""
        if not self.is_opened:
            return {}
        return {
            "width": int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": self._cap.get(cv2.CAP_PROP_FPS),
            "total_frames": int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        }
