"""
Pytest fikstürleri — Test konfigürasyonu.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Test HTTP istemcisi — FastAPI uygulamasına istek gönderir."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
