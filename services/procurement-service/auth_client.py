"""
HTTP Client untuk berkomunikasi dengan Auth Service.

Procurement Service memanggil GET /verify di Auth Service via HTTP.
Dilengkapi retry (exponential backoff) dan circuit breaker.
"""

import asyncio
import logging
import os

import httpx
from fastapi import HTTPException, Header, Request

from circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")

# Retry config
MAX_RETRIES = 3
BASE_DELAY = 0.5
TIMEOUT_SECONDS = 5.0
RETRYABLE_STATUS_CODES = {500, 502, 503, 504}

# Circuit breaker: 5 failure berturut-turut → OPEN, cooldown 30 detik
auth_circuit = CircuitBreaker(
    name="auth-service",
    failure_threshold=5,
    cooldown_seconds=30,
)


async def _call_auth_service(authorization: str, correlation_id: str | None = None) -> dict:
    """Panggil Auth Service dengan circuit breaker + retry + exponential backoff + correlation ID."""
    if not auth_circuit.can_execute():
        raise HTTPException(
            status_code=503,
            detail="Auth Service circuit breaker OPEN. Try again later.",
        )

    headers = {"Authorization": authorization}
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id

    last_exception = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{AUTH_SERVICE_URL}/verify",
                    headers=headers,
                    timeout=TIMEOUT_SECONDS,
                )

            if response.status_code == 200:
                auth_circuit.record_success()
                logger.info(
                    f"Auth verified (attempt {attempt})",
                    extra={"correlation_id": correlation_id},
                )
                return response.json()

            # Non-retryable
            if response.status_code == 401:
                auth_circuit.record_success()
                detail = response.json().get("detail", "Token tidak valid")
                raise HTTPException(status_code=401, detail=detail)
            if response.status_code == 400:
                auth_circuit.record_success()
                raise HTTPException(status_code=400, detail="Bad auth request")

            # Retryable server errors (5xx)
            if response.status_code in RETRYABLE_STATUS_CODES:
                logger.warning(
                    f"Auth service returned {response.status_code} "
                    f"(attempt {attempt}/{MAX_RETRIES})",
                    extra={"correlation_id": correlation_id},
                )
                last_exception = HTTPException(
                    status_code=response.status_code,
                    detail=f"Auth service error: {response.status_code}",
                )
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Unexpected auth response: {response.status_code}",
                )

        except httpx.ConnectError as e:
            logger.warning(
                f"Cannot connect to Auth Service (attempt {attempt}/{MAX_RETRIES}): {e}",
                extra={"correlation_id": correlation_id},
            )
            last_exception = e

        except httpx.TimeoutException as e:
            logger.warning(
                f"Auth Service timeout (attempt {attempt}/{MAX_RETRIES}): {e}",
                extra={"correlation_id": correlation_id},
            )
            last_exception = e

        # Exponential backoff: 0.5s, 1s, 2s
        if attempt < MAX_RETRIES:
            delay = BASE_DELAY * (2 ** (attempt - 1))
            logger.info(f"Retrying in {delay}s...")
            await asyncio.sleep(delay)

    # Semua retry gagal
    auth_circuit.record_failure()
    logger.error(
        f"Auth Service unreachable after {MAX_RETRIES} attempts",
        extra={"correlation_id": correlation_id},
    )
    raise HTTPException(
        status_code=503,
        detail="Auth Service unavailable. Please try again later.",
    )


async def verify_token_with_auth_service(
    request: Request,
    authorization: str = Header(...),
) -> dict:
    """FastAPI Dependency: verifikasi token via Auth Service dengan correlation ID."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    correlation_id = getattr(request.state, "correlation_id", None)
    return await _call_auth_service(authorization, correlation_id)


async def optional_verify_token(
    request: Request,
    authorization: str = Header(None),
) -> dict | None:
    """
    FastAPI Dependency (degraded mode): verifikasi token jika Auth Service tersedia.
    Return None jika circuit breaker OPEN atau token tidak ada — endpoint tetap jalan.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None

    if not auth_circuit.can_execute():
        logger.warning("Circuit breaker OPEN — degraded mode, skip auth")
        return None

    correlation_id = getattr(request.state, "correlation_id", None)
    try:
        return await _call_auth_service(authorization, correlation_id)
    except HTTPException:
        return None


async def require_role_via_auth(
    request: Request,
    roles: list[str],
    authorization: str = Header(...),
) -> dict:
    """
    Verifikasi token DAN cek role user dengan correlation ID.
    Digunakan untuk endpoint admin-only.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    correlation_id = getattr(request.state, "correlation_id", None)
    user = await _call_auth_service(authorization, correlation_id)

    if user["role"] not in roles:
        raise HTTPException(
            status_code=403,
            detail=f"Akses ditolak. Role yang diizinkan: {', '.join(roles)}",
        )

    return user
