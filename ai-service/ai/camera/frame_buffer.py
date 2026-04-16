"""
Frame Buffer — Thread-safe ring buffer ile frame yönetimi.
"""

import threading
from collections import deque
from typing import Optional

import numpy as np


class FrameBuffer:
    """
    Thread-safe ring (circular) buffer.

    Birden fazla tüketici (consumer) için son N frame'i tutar.
    Kamera okuyucusu frame üretir, inference motoru ve stream
    servisi frame tüketir.

    Kullanım:
        buffer = FrameBuffer(max_size=30)
        buffer.put(frame)         # Üretici
        latest = buffer.get()     # Tüketici
    """

    def __init__(self, max_size: int = 30) -> None:
        self._buffer: deque = deque(maxlen=max_size)
        self._lock = threading.Lock()

    def put(self, frame: np.ndarray) -> None:
        """Buffer'a yeni frame ekler. Buffer doluysa en eski frame silinir."""
        with self._lock:
            self._buffer.append(frame)

    def get(self) -> Optional[np.ndarray]:
        """En son frame'i döner. Buffer boşsa None döner."""
        with self._lock:
            if len(self._buffer) == 0:
                return None
            return self._buffer[-1]

    def get_all(self):
        """Buffer'daki tüm frame'lerin bir kopyasını döner."""
        with self._lock:
            return list(self._buffer)

    def clear(self) -> None:
        """Buffer'ı temizler."""
        with self._lock:
            self._buffer.clear()

    @property
    def size(self) -> int:
        """Buffer'daki frame sayısı."""
        with self._lock:
            return len(self._buffer)

    @property
    def is_empty(self) -> bool:
        """Buffer boş mu?"""
        return self.size == 0
