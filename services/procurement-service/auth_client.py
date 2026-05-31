"""
HTTP Client untuk berkomunikasi dengan Auth Service.

╔══════════════════════════════════════════════════════════════════╗
║  INI ADALAH INTI DARI MICROSERVICES!                            ║
║                                                                  ║
║  Di monolith: token di-decode langsung, query ke tabel users     ║
║  Di microservices: Procurement Service TIDAK punya akses ke      ║
║  auth_db. Ia harus BERTANYA ke Auth Service via HTTP.            ║
╚══════════════════════════════════════════════════════════════════╝

Alur:
1. User kirim request ke Procurement Service dengan header "Authorization: Bearer xxx"
2. Procurement Service ambil header tersebut
3. Procurement Service panggil GET http://auth-service:8001/verify dengan header yang sama
4. Auth Service cek token → return {user_id, email, full_name, role}
5. Procurement Service lanjutkan proses dengan data user tersebut

Di Docker Compose, "auth-service" adalah hostname yang resolve ke container Auth Service.
"""

import os

import httpx
from fastapi import HTTPException, Header

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")


async def verify_token_with_auth_service(authorization: str = Header(...)) -> dict:
    """
    FastAPI Dependency: Verifikasi token dengan memanggil Auth Service.

    Digunakan sebagai Depends() di setiap endpoint yang butuh autentikasi.
    Menggantikan fungsi get_current_user() di monolith.

    Returns:
        dict: {"user_id": int, "email": str, "full_name": str, "role": str}

    Raises:
        HTTPException 401: Token tidak valid
        HTTPException 503: Auth Service tidak bisa dihubungi
        HTTPException 504: Auth Service timeout
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{AUTH_SERVICE_URL}/verify",
                headers={"Authorization": authorization},
                timeout=5.0,  # timeout 5 detik
            )

        if response.status_code == 200:
            return response.json()  # {user_id, email, full_name, role}

        elif response.status_code == 401:
            # Auth Service bilang token tidak valid
            detail = response.json().get("detail", "Token tidak valid")
            raise HTTPException(status_code=401, detail=detail)

        else:
            raise HTTPException(
                status_code=503,
                detail="Auth Service mengembalikan error yang tidak diharapkan",
            )

    except httpx.ConnectError:
        # Auth Service tidak bisa dihubungi (container mati?)
        raise HTTPException(
            status_code=503,
            detail="Tidak bisa terhubung ke Auth Service. Apakah service sedang berjalan?",
        )
    except httpx.TimeoutException:
        # Auth Service terlalu lama merespons
        raise HTTPException(
            status_code=504,
            detail="Auth Service timeout — coba lagi nanti",
        )


async def require_role_via_auth(roles: list[str], authorization: str = Header(...)) -> dict:
    """
    Verifikasi token DAN cek role user.
    Digunakan untuk endpoint admin-only.
    """
    user = await verify_token_with_auth_service(authorization)

    if user["role"] not in roles:
        raise HTTPException(
            status_code=403,
            detail=f"Akses ditolak. Role yang diizinkan: {', '.join(roles)}",
        )

    return user
