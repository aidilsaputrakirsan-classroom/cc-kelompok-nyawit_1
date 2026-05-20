"""Test auth endpoints tambahan untuk meningkatkan coverage."""
import pytest


@pytest.mark.asyncio
async def test_register_requester_missing_fields(client):
    """Test register dengan field yang hilang → 422."""
    response = await client.post("/api/v1/auth/register-requester", json={
        "email": "test@example.com"
        # missing password dan full_name
    })
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_requester_invalid_email(client):
    """Test register dengan email invalid → 422."""
    response = await client.post("/api/v1/auth/register-requester", json={
        "email": "invalid-email",
        "password": "Password123",
        "full_name": "Test User"
    })
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_missing_fields(client):
    """Test login tanpa field yang diperlukan → 422."""
    response = await client.post("/api/v1/auth/login", json={
        "email": "test@example.com"
        # missing password
    })
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    """Test login dengan user yang tidak ada → 401."""
    response = await client.post("/api/v1/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "Password123"
    })
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_invalid(client):
    """Test refresh token dengan token invalid → 401."""
    response = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": "invalid.token.here"
    })
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_missing(client):
    """Test refresh token tanpa token → 422."""
    response = await client.post("/api/v1/auth/refresh", json={})
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_logout_without_auth(client):
    """Test logout tanpa token → 401."""
    response = await client.post("/api/v1/auth/logout")
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_with_invalid_token(client):
    """Test /me dengan token invalid → 401."""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token"}
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_register_and_login_flow(client):
    """Test full flow: register → login → get me."""
    # Register
    reg_resp = await client.post("/api/v1/auth/register-requester", json={
        "email": "flow@example.com",
        "password": "FlowPass123",
        "full_name": "Flow User"
    })
    
    assert reg_resp.status_code == 201
    
    # Login
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "flow@example.com",
        "password": "FlowPass123"
    })
    
    assert login_resp.status_code == 200
    token = login_resp.json()["data"]["access_token"]
    
    # Get me
    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert me_resp.status_code == 200
    assert me_resp.json()["data"]["email"] == "flow@example.com"


@pytest.mark.asyncio
async def test_multiple_logins_same_user(client):
    """Test multiple login untuk user yang sama (should work)."""
    # Register
    await client.post("/api/v1/auth/register-requester", json={
        "email": "multi@example.com",
        "password": "MultiPass123",
        "full_name": "Multi User"
    })
    
    # Login pertama
    login1 = await client.post("/api/v1/auth/login", json={
        "email": "multi@example.com",
        "password": "MultiPass123"
    })
    
    assert login1.status_code == 200
    
    # Login kedua
    login2 = await client.post("/api/v1/auth/login", json={
        "email": "multi@example.com",
        "password": "MultiPass123"
    })
    
    assert login2.status_code == 200
    
    # Kedua token harus valid
    token1 = login1.json()["data"]["access_token"]
    token2 = login2.json()["data"]["access_token"]
    
    me1 = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token1}"})
    me2 = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token2}"})
    
    assert me1.status_code == 200
    assert me2.status_code == 200
