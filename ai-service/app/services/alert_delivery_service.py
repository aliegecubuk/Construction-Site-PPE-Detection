"""
Alert Delivery Service — Python servisinden .NET orkestratörüne ihlal event'i gönderir.
"""

from __future__ import annotations

from typing import Optional

import httpx
from loguru import logger

from app.models.schemas.violation import ViolationEvent


class AlertDeliveryService:
    """İhlal event'lerini dış sistemlere ileten HTTP webhook istemcisi."""

    def __init__(
        self,
        webhook_url: str,
        timeout_seconds: float = 5.0,
    ) -> None:
        self._webhook_url = webhook_url
        self._timeout_seconds = timeout_seconds
        self._client: Optional[httpx.AsyncClient] = None

    async def publish_violation(self, event: ViolationEvent) -> bool:
        """
        Tekil ihlal olayını .NET orkestratörüne gönderir.

        .NET API varsayılanı:
            POST http://localhost:8080/api/python/violations
        """
        if not self._webhook_url:
            logger.debug("Alert webhook URL boş; ihlal event'i yalnızca local store'a yazıldı.")
            return False

        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self._timeout_seconds)

        try:
            response = await self._client.post(
                self._webhook_url,
                json=event.model_dump(mode="json", by_alias=True),
            )
            response.raise_for_status()
            return True
        except httpx.HTTPError as exc:
            logger.warning(f".NET alert webhook gönderimi başarısız: {exc}")
            return False

    async def aclose(self) -> None:
        """Açık HTTP client varsa kapatır."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
