"""
Ana Router — Tüm v1 router'ları birleştiren merkezi router.
main.py bu tek router'ı include eder.
"""

from fastapi import APIRouter

from app.api.v1.camera_router import router as camera_router
from app.api.v1.detection_router import router as detection_router
from app.api.v1.iot_router import router as iot_router
from app.api.v1.alert_router import router as alert_router
from app.api.v1.stream_router import router as stream_router
from app.api.v1.risk_router import router as risk_router

api_router = APIRouter()

api_router.include_router(camera_router)
api_router.include_router(detection_router)
api_router.include_router(iot_router)
api_router.include_router(alert_router)
api_router.include_router(stream_router)
api_router.include_router(risk_router)
