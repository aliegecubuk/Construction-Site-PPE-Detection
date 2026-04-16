"""
REPORT-AI — İSG Karar Destek Sistemi
=====================================
FastAPI tabanlı backend uygulamasının giriş noktası.

Startup sırası:
    1. Loglama sistemi başlatılır.
    2. FastAPI uygulaması oluşturulur.
    3. CORS middleware eklenir.
    4. Router'lar bağlanır.
    5. Startup event'inde:
       a) Kamera konfigürasyonları JSON'dan yüklenir.
       b) (Opsiyonel) YOLO modeli yüklenir.
       c) (Opsiyonel) VisionPipeline başlatılır.
    6. Shutdown event'inde tüm kaynaklar graceful temizlenir.

Kullanım:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.api.router import api_router
from app.api.dependencies import (
    get_alert_delivery_service,
    get_camera_service,
    get_detection_service,
    get_detector,
    get_vision_pipeline,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Loglama Başlatma
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
setup_logging()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Yaşam Döngüsü (Lifespan)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Uygulama yaşam döngüsü yönetimi.
    Startup: Kameraları yükle ve (opsiyonel) VisionPipeline başlat.
    Shutdown: Tüm kaynakları temizle.
    """
    # ── STARTUP ──
    logger.info("=" * 60)
    logger.info(f"{settings.PROJECT_NAME} v{settings.VERSION} başlatılıyor...")
    logger.info("=" * 60)

    # 1) Kamera konfigürasyonlarını JSON'dan yükle
    camera_service = get_camera_service()
    try:
        loaded = await camera_service.load_from_json()
        logger.info(f"Kamera konfigürasyonu: {loaded} kamera yüklendi.")
    except Exception as exc:
        logger.warning(f"Kamera konfigürasyon yükleme hatası: {exc}")

    # 2) YOLO modelini yükle (opsiyonel — kaPatılabilir)
    detector = get_detector()
    try:
        if not detector.is_loaded:
            detector.load_model()
            logger.info("YOLO modeli başarıyla yüklendi.")
    except Exception as exc:
        logger.warning(
            f"YOLO model yükleme hatası (pipeline'sız devam ediliyor): {exc}"
        )

    # 3) Vision pipeline'ı başlat
    pipeline = get_vision_pipeline()
    try:
        await pipeline.start()
        logger.info(
            "VisionPipeline başlatıldı. "
            "Angular MJPEG akışı: http://localhost:8000/api/v1/stream/mjpeg/{camera_id}"
        )
    except Exception as exc:
        logger.warning(f"VisionPipeline başlatılamadı: {exc}")

    logger.info(f"{settings.PROJECT_NAME} hazır — http://localhost:8000/docs")
    logger.info("=" * 60)

    yield  # ← Uygulama çalışma süresince burada bekler

    # ── SHUTDOWN ──
    logger.info("Uygulama kapatılıyor...")

    # Önce pipeline'ı durdur; model ve kamera thread cleanup burada yapılır.
    try:
        await get_vision_pipeline().stop()
    except Exception as exc:
        logger.warning(f"VisionPipeline kapatma hatası: {exc}")

    try:
        await get_alert_delivery_service().aclose()
    except Exception as exc:
        logger.warning(f"Alert delivery kapanış hatası: {exc}")

    logger.info(f"{settings.PROJECT_NAME} kapatıldı.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  FastAPI Uygulama Nesnesi
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "İş Sağlığı ve Güvenliği Karar Destek Sistemi — "
        "Kamera Görüntü Analizi, IoT Sensör Verisi & Risk Skorlama"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CORS Middleware
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Router'lar
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
from app.api.v1.dashboard_router import router as dashboard_router

app.include_router(dashboard_router)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Health Check
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@app.get("/health", tags=["System"])
async def health_check():
    """
    Sistem sağlık durumu kontrolü.
    Model yükleme durumu ve kamera sayısını raporlar.
    """
    detector = get_detector()
    camera_service = get_camera_service()
    cameras = await camera_service.get_all_cameras()

    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "model_loaded": detector.is_loaded,
        "model_device": settings.MODEL_DEVICE,
        "cameras_loaded": len(cameras),
        "avg_inference_ms": round(detector.avg_inference_ms, 1),
    }
