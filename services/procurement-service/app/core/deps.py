import asyncio
import logging
from typing import List

import httpx
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)

_bearer = HTTPBearer()

# Shared circuit breaker instance
auth_circuit = CircuitBreaker(
    name="auth-service",
    failure_threshold=5,
    cooldown_seconds=30,
)

# Retry config
MAX_RETRIES = 3
BASE_DELAY = 0.5
TIMEOUT_SECONDS = 5.0
RETRYABLE_STATUS_CODES = {500, 502, 503, 504}


class CurrentUser:
    def __init__(self, id: int, email: str, full_name: str, role: str):
        self.id = id
        self.email = email
        self.full_name = full_name
        self.role = role

    def __repr__(self) -> str:
        return f"<CurrentUser id={self.id} email={self.email!r} role={self.role}>"


async def _call_verify_api(token: str) -> dict:
    """Helper to call verify endpoint with retry logic and circuit breaker."""
    if not auth_circuit.can_execute():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth Service circuit breaker OPEN. Try again later.",
        )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.AUTH_SERVICE_URL}/api/v1/auth/verify",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=TIMEOUT_SECONDS,
                )

            # Success responses (including deterministic auth errors)
            if response.status_code == 200:
                auth_circuit.record_success()
                res_data = response.json()
                if res_data.get("success"):
                    return res_data.get("data")
                else:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=res_data.get("message", "Token tidak valid"),
                    )

            if response.status_code == 401:
                auth_circuit.record_success()
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token tidak valid atau sudah kedaluwarsa",
                )

            if response.status_code == 400:
                auth_circuit.record_success()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Bad request to auth service",
                )

            # Retryable server errors (5xx)
            if response.status_code in RETRYABLE_STATUS_CODES:
                logger.warning(
                    f"Auth service returned {response.status_code} "
                    f"(attempt {attempt}/{MAX_RETRIES})"
                )
            else:
                auth_circuit.record_success()
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Unexpected auth response: {response.status_code}",
                )

        except (httpx.ConnectError, httpx.TimeoutException) as e:
            logger.warning(
                f"Connection/Timeout error with Auth Service (attempt {attempt}/{MAX_RETRIES}): {e}"
            )

        # Exponential backoff
        if attempt < MAX_RETRIES:
            delay = BASE_DELAY * (2 ** (attempt - 1))
            await asyncio.sleep(delay)

    # All retries failed
    auth_circuit.record_failure()
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Auth Service tidak tersedia saat ini.",
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> CurrentUser:
    """
    Validate the JWT access token by calling the Auth Service's verify API.
    Raises 401 if the token is invalid, expired, or revoked.
    """
    token = credentials.credentials
    user_data = await _call_verify_api(token)
    return CurrentUser(
        id=user_data["id"],
        email=user_data["email"],
        full_name=user_data["full_name"],
        role=user_data["role"]
    )


async def optional_verify_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
) -> CurrentUser | None:
    """
    Dependency for degraded mode.
    Returns None if circuit breaker is OPEN, token is missing/invalid, or Auth Service is down.
    Otherwise returns CurrentUser.
    """
    if not credentials:
        return None

    token = credentials.credentials
    if not auth_circuit.can_execute():
        logger.warning("Circuit breaker OPEN — degraded mode, skip auth")
        return None

    try:
        user_data = await _call_verify_api(token)
        return CurrentUser(
            id=user_data["id"],
            email=user_data["email"],
            full_name=user_data["full_name"],
            role=user_data["role"]
        )
    except Exception as e:
        logger.warning(f"Verify failed in optional_verify_token: {e}")
        return None


def require_role(roles: List[str]):
    """
    Factory that returns a dependency which checks whether the
    authenticated user has one of the allowed roles.
    """

    async def _role_checker(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Akses ditolak. Role yang diizinkan: {', '.join(roles)}",
            )
        return current_user

    return _role_checker

