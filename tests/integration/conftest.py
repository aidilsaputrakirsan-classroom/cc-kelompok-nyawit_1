"""
Fixtures untuk integration tests.
Syarat: semua service running via docker compose.
"""

import os
import time

import httpx
import pytest

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost")


@pytest.fixture(scope="session")
def gateway_url():
    """Base URL gateway."""
    return GATEWAY_URL


@pytest.fixture(scope="session")
def test_user():
    """Register requester via /auth/register-requester, login, return token + headers."""
    email = f"integration-test-{int(time.time())}@example.com"
    password = "IntegrationTestPass123"
    full_name = "Integration Test User"

    # Register requester (public endpoint)
    response = httpx.post(
        f"{GATEWAY_URL}/api/v1/auth/register-requester",
        json={"email": email, "password": password, "full_name": full_name},
        timeout=10,
    )
    assert response.status_code == 201, f"Register failed: {response.text}"

    # Login
    response = httpx.post(
        f"{GATEWAY_URL}/api/v1/auth/login",
        json={"email": email, "password": password},
        timeout=10,
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["data"]["access_token"]

    return {
        "email": email,
        "password": password,
        "full_name": full_name,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }
