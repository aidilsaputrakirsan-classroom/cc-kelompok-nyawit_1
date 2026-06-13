import logging
import time
import uuid

from fastapi import FastAPI, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging_config import correlation_id_ctx, setup_logging
from app.db.session import get_db
from app.routers import auth
from app.routers import requisitions
from app.routers import requisitions_admin
from app.routers import purchase_orders
from app.routers import grn
from app.routers import grn_admin

# ── Structured logging (JSON) ─────────────────────────────────────
# Diaktifkan sedini mungkin agar log startup pun sudah berformat JSON.
setup_logging(level="INFO")
logger = logging.getLogger("sicure.request")

# Nama header yang dipakai untuk membawa correlation ID antar service/klien.
CORRELATION_ID_HEADER = "X-Correlation-ID"

app = FastAPI(
    title="SiCure API",
    description="Sistem Procurement API",
    version="1.0.0",
)


# ── Correlation ID + request logging middleware ──────────────────
@app.middleware("http")
async def correlation_and_logging(request: Request, call_next):
    """
    Untuk setiap request:
      1. Ambil correlation ID dari header (X-Correlation-ID / X-Request-ID)
         atau generate baru bila tidak ada.
      2. Simpan ke ContextVar agar muncul di semua log selama request ini.
      3. Catat structured log saat request masuk & selesai (method, path,
         status, durasi ms), lalu kembalikan correlation ID di response header.
    """
    correlation_id = (
        request.headers.get(CORRELATION_ID_HEADER)
        or request.headers.get("X-Request-ID")
        or str(uuid.uuid4())
    )
    token = correlation_id_ctx.set(correlation_id)
    start = time.perf_counter()

    logger.info(
        "request.start",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else None,
        },
    )

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.exception(
            "request.error",
            extra={
                "method": request.method,
                "path": request.url.path,
                "duration_ms": duration_ms,
            },
        )
        correlation_id_ctx.reset(token)
        raise

    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info(
        "request.end",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )

    response.headers[CORRELATION_ID_HEADER] = correlation_id
    correlation_id_ctx.reset(token)
    return response

# ── CORS middleware ───────────────────────────────────────────────
# In production, only explicitly listed origins are allowed.
# In development, localhost origins are accepted by default.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)


# ── Production: enforce max request body size ────────────────────
if settings.is_production:

    @app.middleware("http")
    async def limit_upload_size(request: Request, call_next):
        """
        Reject requests whose Content-Length exceeds the configured
        maximum upload size.  This is a defence-in-depth measure;
        individual endpoints also validate file sizes.
        """
        content_length = request.headers.get("content-length")
        # Allow 2x the per-file limit to account for multipart overhead
        # when uploading multiple files in a single request.
        max_body = settings.max_upload_bytes * 2 + 1024 * 100  # +100KB overhead
        if content_length and int(content_length) > max_body:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "success": False,
                    "data": None,
                    "message": (
                        f"Request body terlalu besar. "
                        f"Maksimum {settings.MAX_UPLOAD_SIZE_MB}MB per file."
                    ),
                },
            )
        return await call_next(request)


# ── Routers ───────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(requisitions.router)
app.include_router(requisitions_admin.router)
app.include_router(purchase_orders.router)
app.include_router(grn.router)
app.include_router(grn_admin.router)

# ── Static files — serve uploaded documents ───────────────────────
upload_path = Path(settings.UPLOAD_DIR)
upload_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint — cek status semua komponen."""
    health = {
        "status": "healthy",
        "service": "backend",
        "version": "1.0.0",
    }
    
    # Cek database connection
    try:
        await db.execute(text("SELECT 1"))
        health["database"] = "connected"
    except Exception as e:
        health["status"] = "unhealthy"
        health["database"] = f"error: {str(e)}"
    
    status_code = 200 if health["status"] == "healthy" else 503
    return JSONResponse(content=health, status_code=status_code)


@app.get("/api/v1/health")
async def api_health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint for API monitoring with detailed component status"""
    health = {
        "success": True,
        "data": {
            "status": "healthy",
            "environment": settings.APP_ENV,
            "version": "1.0.0",
            "components": {}
        },
        "message": "API is running normally"
    }
    
    # Cek database connection
    try:
        await db.execute(text("SELECT 1"))
        health["data"]["components"]["database"] = "connected"
    except Exception as e:
        health["data"]["status"] = "unhealthy"
        health["data"]["components"]["database"] = f"error: {str(e)}"
        health["success"] = False
        health["message"] = "API is experiencing issues"
    
    status_code = 200 if health["data"]["status"] == "healthy" else 503
    return JSONResponse(content=health, status_code=status_code)
