"""
YOLODetector — Production-grade YOLO model yükleme ve çıkarım sınıfı.

Bu sınıf:
    • Thread-safe singleton pattern ile tek model instance'ı yönetir.
    • Model yükleme sırasında warm-up (ısınma) çalıştırarak ilk predict'i hızlandırır.
    • asyncio event loop'a bridge sağlayan predict_async() metodu sunar.
    • Detaylı hata yakalama, retry ve graceful degradation uygular.

Katmanlı mimari kuralı:
    Bu sınıf ai/ katmanındadır; app/ katmanından bağımsız çalışabilir.
    Sadece app.core.constants ve app.models.schemas'a bağımlıdır.
"""

from __future__ import annotations

import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Optional

import numpy as np
from loguru import logger

from app.core.constants import CLASS_INDEX_MAP, DEFAULT_CONFIDENCE_THRESHOLD
from app.core.exceptions import InferenceError, ModelLoadError
from app.models.schemas.detection import BoundingBox


class YOLODetector:
    """
    Thread-safe YOLOv8 nesne tespit motoru.

    Singleton olarak kullanılır — birden fazla kamera thread'i aynı
    model instance'ını paylaşır. predict() metodu thread-safe'dir
    çünkü her çağrı kendi YOLO result nesnesini üretir.

    Kullanım:
        detector = YOLODetector(weights_path="ai/weights/best.pt")
        detector.load_model()
        detections = detector.predict(frame)
        # veya async context'te:
        detections = await detector.predict_async(frame)
    """

    _instance: Optional[YOLODetector] = None
    _init_lock = threading.Lock()

    def __new__(cls, *args, **kwargs) -> YOLODetector:
        """Thread-safe singleton: Aynı anda tek bir instance oluşturulur."""
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        weights_path: str = "ai/weights/best.pt",
        confidence: float = DEFAULT_CONFIDENCE_THRESHOLD,
        iou_threshold: float = 0.45,
        device: str = "cpu",
    ) -> None:
        # __init__ singleton'da birden fazla kez çağrılabilir; guard koy
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._weights_path = Path(weights_path)
        self._confidence = confidence
        self._iou_threshold = iou_threshold
        self._device = device
        self._model = None
        self._model_lock = threading.Lock()

        # Performans metrikleri
        self._total_predictions: int = 0
        self._total_inference_ms: float = 0.0

        # Async bridge için thread pool
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="yolo")

        self._initialized = True

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Properties
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @property
    def is_loaded(self) -> bool:
        """Model yüklenmiş mi kontrolü."""
        return self._model is not None

    @property
    def avg_inference_ms(self) -> float:
        """Ortalama çıkarım süresi (ms)."""
        if self._total_predictions == 0:
            return 0.0
        return self._total_inference_ms / self._total_predictions

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Model Yaşam Döngüsü
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def load_model(self) -> None:
        """
        YOLO model ağırlıklarını yükler ve warm-up çalıştırır.

        Warm-up: Boş bir frame ile ilk predict çağrılır. Bu sayede
        CUDA/CPU kernel'ları önceden derlenir ve ilk gerçek predict
        gecikme yaşamaz.

        Raises:
            ModelLoadError: Model dosyası bulunamazsa veya ultralytics yoksa.
        """
        with self._model_lock:
            if self._model is not None:
                logger.warning("Model zaten yüklü — load_model() atlanıyor.")
                return

            try:
                from ultralytics import YOLO
            except ImportError:
                raise ModelLoadError(
                    str(self._weights_path),
                    "ultralytics paketi kurulu değil. Çalıştırın: pip install ultralytics",
                )

            if not self._weights_path.exists():
                raise ModelLoadError(
                    str(self._weights_path),
                    f"Model dosyası bulunamadı: {self._weights_path.resolve()}",
                )

            try:
                logger.info(f"Model yükleniyor: {self._weights_path} (device: {self._device})")
                self._model = YOLO(str(self._weights_path))

                # ── Warm-up: boş frame ile ilk çıkarım ──
                dummy_frame = np.zeros((640, 640, 3), dtype=np.uint8)
                self._model.predict(
                    source=dummy_frame,
                    conf=self._confidence,
                    device=self._device,
                    verbose=False,
                )
                logger.info(
                    f"Model yüklendi ve warm-up tamamlandı: "
                    f"{self._weights_path.name} ({self._device})"
                )

            except Exception as exc:
                self._model = None
                raise ModelLoadError(str(self._weights_path), str(exc))

    def unload_model(self) -> None:
        """Model belleğini serbest bırakır."""
        with self._model_lock:
            self._model = None
            self._total_predictions = 0
            self._total_inference_ms = 0.0
            logger.info("Model bellekten kaldırıldı.")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Çıkarım (Predict)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def predict(
        self,
        frame: np.ndarray,
        confidence: Optional[float] = None,
        iou_threshold: Optional[float] = None,
    ) -> List[BoundingBox]:
        """
        Tek bir frame üzerinde senkron nesne tespiti yapar.

        Thread-safe: Birden fazla kamera thread'i bu metodu eşzamanlı
        çağırabilir. YOLO predict() zaten thread-safe olduğundan
        ek kilitleme gerekmez.

        Args:
            frame: BGR formatında OpenCV frame (numpy array).
            confidence: Opsiyonel güven eşiği (override).
            iou_threshold: Opsiyonel IoU eşiği (override).

        Returns:
            BoundingBox listesi.

        Raises:
            InferenceError: Model yüklenmemişse veya predict sırasında hata oluşursa.
        """
        if not self.is_loaded:
            raise InferenceError(
                "Model henüz yüklenmedi. Önce load_model() çağrılmalı."
            )

        if frame is None or frame.size == 0:
            logger.warning("Boş frame alındı — predict atlanıyor.")
            return []

        conf = confidence or self._confidence
        iou = iou_threshold or self._iou_threshold

        start_time = time.perf_counter()

        try:
            results = self._model.predict(
                source=frame,
                conf=conf,
                iou=iou,
                device=self._device,
                verbose=False,
            )

            detections = self._parse_results(results)

            # ── Performans metriği güncelle ──
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            self._total_predictions += 1
            self._total_inference_ms += elapsed_ms

            return detections

        except InferenceError:
            raise  # Zaten domain hatası — tekrar fırlatma
        except Exception as exc:
            logger.error(f"YOLO predict hatası: {exc}")
            raise InferenceError(f"Tahmin sırasında beklenmeyen hata: {exc}")

    async def predict_async(
        self,
        frame: np.ndarray,
        confidence: Optional[float] = None,
    ) -> List[BoundingBox]:
        """
        Asenkron çıkarım — CPU-bound predict() işlemini asyncio event loop'u
        bloklamadan ThreadPoolExecutor üzerinde çalıştırır.

        FastAPI endpoint'lerinden veya async pipeline'lardan çağrılmalıdır.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._executor,
            self.predict,
            frame,
            confidence,
        )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #  Yardımcı (Private)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @staticmethod
    def _parse_results(results) -> List[BoundingBox]:
        """
        Ultralytics Results nesnesini BoundingBox listesine dönüştürür.

        Her kutu için: koordinatlar, sınıf ID, sınıf adı ve güven skoru çıkarılır.
        Bilinmeyen sınıf ID'leri 'unknown' olarak etiketlenir.
        """
        detections: List[BoundingBox] = []

        for result in results:
            boxes = result.boxes
            if boxes is None or len(boxes) == 0:
                continue

            # Tensör → numpy dönüşümünü toplu yap (daha performanslı)
            xyxy_all = boxes.xyxy.cpu().numpy()
            cls_all = boxes.cls.cpu().numpy().astype(int)
            conf_all = boxes.conf.cpu().numpy()

            for i in range(len(boxes)):
                detections.append(
                    BoundingBox(
                        x1=float(xyxy_all[i][0]),
                        y1=float(xyxy_all[i][1]),
                        x2=float(xyxy_all[i][2]),
                        y2=float(xyxy_all[i][3]),
                        confidence=float(conf_all[i]),
                        class_name=CLASS_INDEX_MAP.get(int(cls_all[i]), "unknown"),
                        class_id=int(cls_all[i]),
                    )
                )

        return detections
