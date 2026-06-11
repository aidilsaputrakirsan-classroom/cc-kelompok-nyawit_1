from typing import List

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

_bearer = HTTPBearer()


class CurrentUser:
    def __init__(self, id: int, email: str, full_name: str, role: str):
        self.id = id
        self.email = email
        self.full_name = full_name
        self.role = role

    def __repr__(self) -> str:
        return f"<CurrentUser id={self.id} email={self.email!r} role={self.role}>"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer)
) -> CurrentUser:
    """
    Validate the JWT access token by calling the Auth Service's verify API.
    Raises 401 if the token is invalid, expired, or revoked.
    """
    token = credentials.credentials
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.AUTH_SERVICE_URL}/api/v1/auth/verify",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0
            )

        if response.status_code == 200:
            res_data = response.json()
            if res_data.get("success"):
                user_data = res_data.get("data")
                return CurrentUser(
                    id=user_data["id"],
                    email=user_data["email"],
                    full_name=user_data["full_name"],
                    role=user_data["role"]
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=res_data.get("message", "Token tidak valid"),
                    headers={"WWW-Authenticate": "Bearer"},
                )
        elif response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token tidak valid atau sudah kedaluwarsa",
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Layanan Auth Service tidak tersedia",
            )
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gagal menghubungi Auth Service",
        )


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
