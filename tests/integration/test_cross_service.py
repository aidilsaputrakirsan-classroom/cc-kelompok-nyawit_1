"""
Integration Tests — verifikasi komunikasi antar services via gateway.
Jalankan dengan: pytest tests/integration/ -v
Syarat: docker compose -f docker-compose.microservices.yml up -d
"""

import subprocess
import time

import httpx


# ── PR payload helper ────────────────────────────────────────────
def _pr_payload(title="Integration Test PR"):
    return {
        "title": title,
        "justification": "Integration test justification",
        "items": [
            {
                "item_name": "Test Item",
                "quantity": 2,
                "unit_of_measure": "pcs",
                "estimated_unit_price": 50000,
            }
        ],
    }


# ── Test 1: Gateway health ───────────────────────────────────────
def test_gateway_health(gateway_url):
    """Gateway bisa diakses."""
    response = httpx.get(f"{gateway_url}/health", timeout=10)
    assert response.status_code == 200


# ── Test 2: Auth Service health via gateway ──────────────────────
def test_auth_service_health(gateway_url):
    """Auth Service health check via gateway /api/v1/auth/health."""
    response = httpx.get(f"{gateway_url}/api/v1/auth/health", timeout=10)
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "auth-service"
    assert data["status"] == "healthy"


# ── Test 3: Procurement Service aggregated health ────────────────
def test_procurement_service_health(gateway_url):
    """Procurement Service aggregated health check (DB + circuit breaker + auth)."""
    result = subprocess.run(
        ["docker", "exec", "sicure-procurement-service",
         "python", "-c",
         "import urllib.request; print(urllib.request.urlopen('http://localhost:8002/health').read().decode())"],
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, f"Health check failed: {result.stderr}"
    import json
    data = json.loads(result.stdout)
    assert data["service"] == "procurement-service"
    assert data["status"] == "healthy"
    assert data["checks"]["database"]["status"] == "healthy"
    assert data["checks"]["circuit_breaker"]["state"] == "CLOSED"
    assert data["checks"]["auth_service"]["status"] == "healthy"


# ── Test 4: Register + Login flow ────────────────────────────────
def test_register_login_flow(gateway_url):
    """Full flow: register-requester → login → dapat token."""
    email = f"flow-test-{int(time.time())}@example.com"

    # Register requester
    resp = httpx.post(
        f"{gateway_url}/api/v1/auth/register-requester",
        json={"email": email, "password": "FlowTest123", "full_name": "Flow User"},
        timeout=10,
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["email"] == email

    # Login
    resp = httpx.post(
        f"{gateway_url}/api/v1/auth/login",
        json={"email": email, "password": "FlowTest123"},
        timeout=10,
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()["data"]



# ── Test 5: Cross-service auth verification ──────────────────────
def test_cross_service_auth_verification(gateway_url, test_user):
    """Procurement Service verifikasi token via Auth Service (cross-service call)."""
    resp = httpx.post(
        f"{gateway_url}/api/v1/requisitions/",
        json=_pr_payload("Cross-Service Test PR"),
        headers=test_user["headers"],
        timeout=10,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["title"] == "Cross-Service Test PR"


# ── Test 6: CRUD via gateway ─────────────────────────────────────
def test_crud_via_gateway(gateway_url, test_user):
    """Full CRUD melalui gateway (melibatkan semua services)."""
    headers = test_user["headers"]

    # Create
    resp = httpx.post(
        f"{gateway_url}/api/v1/requisitions/",
        json=_pr_payload("CRUD Test PR"),
        headers=headers,
        timeout=10,
    )
    assert resp.status_code == 201
    pr_id = resp.json()["data"]["id"]

    # Read
    resp = httpx.get(
        f"{gateway_url}/api/v1/requisitions/{pr_id}",
        headers=headers,
        timeout=10,
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["title"] == "CRUD Test PR"

    # Update
    resp = httpx.put(
        f"{gateway_url}/api/v1/requisitions/{pr_id}",
        json={
            "title": "CRUD Test PR Updated",
            "justification": "Updated justification",
            "items": [
                {
                    "item_name": "Updated Item",
                    "quantity": 5,
                    "unit_of_measure": "box",
                    "estimated_unit_price": 25000,
                }
            ],
        },
        headers=headers,
        timeout=10,
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["title"] == "CRUD Test PR Updated"

    # Delete
    resp = httpx.delete(
        f"{gateway_url}/api/v1/requisitions/{pr_id}",
        headers=headers,
        timeout=10,
    )
    assert resp.status_code == 200

    # Verify deleted (404)
    resp = httpx.get(
        f"{gateway_url}/api/v1/requisitions/{pr_id}",
        headers=headers,
        timeout=10,
    )
    assert resp.status_code == 404


# ── Test 7: Unauthorized without token ───────────────────────────
def test_unauthorized_without_token(gateway_url):
    """Request tanpa token harus ditolak oleh Procurement Service."""
    resp = httpx.post(
        f"{gateway_url}/api/v1/requisitions/",
        json=_pr_payload("Should Fail"),
        timeout=10,
    )
    assert resp.status_code in [401, 422]


# ── Test 8: Invalid token rejected ──────────────────────────────
def test_invalid_token_rejected(gateway_url):
    """Token invalid harus ditolak."""
    resp = httpx.get(
        f"{gateway_url}/api/v1/requisitions/",
        headers={"Authorization": "Bearer invalid-fake-token"},
        timeout=10,
    )
    assert resp.status_code == 401


# ── Test 9: Public endpoint (no auth) ────────────────────────────
def test_public_endpoint_no_auth(gateway_url):
    """Endpoint /public dapat diakses tanpa token."""
    resp = httpx.get(f"{gateway_url}/api/v1/requisitions/public", timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert "pagination" in data


# ── Test 10: Stats endpoint degraded mode (no auth) ─────────────
def test_stats_degraded_mode(gateway_url):
    """Endpoint /stats berjalan dalam degraded mode saat tanpa token."""
    resp = httpx.get(f"{gateway_url}/api/v1/requisitions/stats", timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["degraded"] is True
    assert isinstance(data["data"]["by_status"], dict)
