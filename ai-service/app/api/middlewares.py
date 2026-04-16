"""
API Middlewares — CORS, hata yakalama ve rate-limiting.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import ReportAIBaseError


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Merkezi hata yakalama middleware'i.
    Proje exception'larını uygun HTTP yanıtına dönüştürür.
    """

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except ReportAIBaseError as exc:
            logger.error(f"İş hatası: {exc.message}")
            return JSONResponse(
                status_code=400,
                content={
                    "error": type(exc).__name__,
                    "message": exc.message,
                },
            )
        except Exception as exc:
            logger.exception(f"Beklenmeyen hata: {exc}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "InternalServerError",
                    "message": "Beklenmeyen bir sunucu hatası oluştu.",
                },
            )
