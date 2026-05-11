"""Test authentication endpoints untuk SiCure."""
import pytest


@pytest.mark.asyncio
async def test_register_requester_success(client):
    """Test register requester mandiri berhasil."""
    response = await client.post("/api/v1/auth/register-requester", json={
        "email": "newrequester@example.com",
        "password": "SecurePass123",
        "full_name": "New Requester"
    })
    
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == "newrequester@example.com"
    assert data["data"]["full_name"] == "New Requester"
    assert data["data"]["role"] == "requester"
    assert "id" in data["data"]
    # Password TIDAK boleh ada di response
    assert "password" not in data["data"]
    assert "hashed_password" not in data["data"]


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    """Test register dengan email yang sudah ada → 409."""
    # Register pertama
    await client.post("/api/v1/auth/register-requester", json={
        "email": "duplicate@example.com",
        "password": "Pass1234",
        "full_name": "User 1"
    })
    
    # Register kedua dengan email sama
    response = await client.post("/api/v1/auth/register-requester", json={
        "email": "duplicate@example.com",
        "password": "Pass5678",
        "full_name": "User 2"
    })
    
    assert response.status_code == 409
    assert "Email sudah terdaftar" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client):
    """Test login dengan kredensial benar → return token."""
    # Register dulu
    await client.post("/api/v1/auth/register-requester", json={
        "email": "login@example.com",
        "password": "MyPassword123",
        "full_name": "Login User"
    })
    
    # Login
    response = await client.post("/api/v1/auth/login", json={
        "email": "login@example.com",
        "password": "MyPassword123"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]
    assert data["data"]["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    """Test login dengan password salah → 401."""
    # Register
    await client.post("/api/v1/auth/register-requester", json={
        "email": "wrongpass@example.com",
        "password": "CorrectPass123",
        "full_name": "User"
    })
    
    # Login dengan password salah
    response = await client.post("/api/v1/auth/login", json={
        "email": "wrongpass@example.com",
        "password": "WrongPassword"
    })
    
    assert response.status_code == 401
    assert "Email atau password salah" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_me_authenticated(client, auth_headers):
    """Test endpoint /auth/me dengan token valid."""
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == "test@example.com"
    assert data["data"]["full_name"] == "Test User"


@pytest.mark.asyncio
async def test_get_me_unauthorized(client):
    """Test endpoint /auth/me tanpa token → 401."""
    response = await client.get("/api/v1/auth/me")
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client):
    """Test refresh token flow."""
    # Register + login
    await client.post("/api/v1/auth/register-requester", json={
        "email": "refresh@example.com",
        "password": "RefreshPass123",
        "full_name": "Refresh User"
    })
    
    login_response = await client.post("/api/v1/auth/login", json={
        "email": "refresh@example.com",
        "password": "RefreshPass123"
    })
    
    refresh_token = login_response.json()["data"]["refresh_token"]
    
    # Refresh token
    response = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]


@pytest.mark.asyncio
async def test_logout(client, auth_headers):
    """Test logout dan token revocation."""
    response = await client.post("/api/v1/auth/logout", headers=auth_headers)
    
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Token seharusnya sudah di-revoke, coba akses /me lagi
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 401