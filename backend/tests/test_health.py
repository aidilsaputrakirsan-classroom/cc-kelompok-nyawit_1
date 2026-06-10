"""
Basic smoke tests for the SiCure API.

Run with:
    python -m pytest tests/ -v
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.anyio
async def test_health_endpoint(client: AsyncClient):
    """GET /health should return 200 with service metadata."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "backend"
    assert data["version"] == "1.0.0"
    assert data["status"] in ("healthy", "degraded")
    assert data["database"] in ("connected", "disconnected")


@pytest.mark.anyio
async def test_login_missing_credentials(client: AsyncClient):
    """POST /api/v1/auth/login with empty body should return 422."""
    response = await client.post("/api/v1/auth/login", data={})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_protected_route_without_token(client: AsyncClient):
    """GET /api/v1/auth/me without token should be rejected."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code in (401, 403)


@pytest.mark.anyio
async def test_requisitions_without_auth(client: AsyncClient):
    """GET /api/v1/requisitions/ without auth should be rejected."""
    response = await client.get("/api/v1/requisitions/")
    assert response.status_code in (401, 403)
