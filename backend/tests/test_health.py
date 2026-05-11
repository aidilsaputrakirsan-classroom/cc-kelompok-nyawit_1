"""Test health check endpoints."""
import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    """Test health endpoint → 200 dan status healthy."""
    response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data


@pytest.mark.asyncio
async def test_api_health_check(client):
    """Test API health endpoint → 200 dan status healthy."""
    response = await client.get("/api/v1/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "healthy"
    assert data["data"]["environment"] in ["development", "production"]