from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.core.config import settings
from app.routers import auth
from app.routers import requisitions
from app.routers import requisitions_admin
from app.routers import purchase_orders
from app.routers import grn
from app.routers import grn_admin

app = FastAPI(
    title="SiCure API",
    description="Sistem Procurement API",
    version="1.0.0",
)

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
async def health_check():
    return {"status": "ok", "env": settings.APP_ENV}


@app.get("/api/v1/health")
async def api_health_check():
    """Health check endpoint for API monitoring"""
    return {
        "success": True,
        "data": {
            "status": "healthy",
            "environment": settings.APP_ENV,
            "version": "1.0.0"
        },
        "message": "API is running normally"
    }
