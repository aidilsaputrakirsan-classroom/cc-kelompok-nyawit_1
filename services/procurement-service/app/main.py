from pathlib import Path
import httpx
from sqlalchemy import text

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.core.deps import auth_circuit
from app.routers import requisitions, requisitions_admin, purchase_orders, grn, grn_admin
from app.models.purchase_requisition import PurchaseRequisition
from app.models.pr_line_item import PRLineItem
from app.models.purchase_order import PurchaseOrder
from app.models.grn_document import GRNDocument

app = FastAPI(
    title="SiCure Procurement Service",
    description="Procurement core microservice (PR, PO, GRN)",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Enforce max request body size in production
if settings.is_production:
    @app.middleware("http")
    async def limit_upload_size(request: Request, call_next):
        content_length = request.headers.get("content-length")
        max_body = settings.max_upload_bytes * 2 + 1024 * 100
        if content_length and int(content_length) > max_body:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "success": False,
                    "data": None,
                    "message": f"Request body terlalu besar. Maksimum {settings.MAX_UPLOAD_SIZE_MB}MB per file.",
                },
            )
        return await call_next(request)

# Include Routers
app.include_router(requisitions.router)
app.include_router(requisitions_admin.router)
app.include_router(purchase_orders.router)
app.include_router(grn.router)
app.include_router(grn_admin.router)

# Mount static files for uploads
upload_path = Path(settings.UPLOAD_DIR)
upload_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")


@app.on_event("startup")
async def startup_event():
    # Automatically create tables in procurement-db on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health")
async def health_check():
    """
    Aggregated health check: cek DB + Auth Service + circuit breaker.
    Status overall = healthy hanya jika semua dependency healthy.
    """
    checks = {}

    # 1. Database connectivity
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = {"status": "healthy"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "detail": str(e)}

    # 2. Circuit breaker status
    cb_status = auth_circuit.get_status()
    checks["circuit_breaker"] = {
        "status": "healthy" if cb_status["state"] != "OPEN" else "degraded",
        **cb_status,
    }

    # 3. Auth Service reachability (non-blocking, short timeout)
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.AUTH_SERVICE_URL}/api/v1/auth/health", timeout=2.0
            )
        if resp.status_code == 200:
            checks["auth_service"] = {"status": "healthy"}
        else:
            checks["auth_service"] = {
                "status": "degraded",
                "status_code": resp.status_code,
            }
    except Exception as e:
        checks["auth_service"] = {"status": "unhealthy", "detail": str(e)}

    # Overall status
    statuses = [c["status"] for c in checks.values()]
    if all(s == "healthy" for s in statuses):
        overall = "healthy"
    elif any(s == "unhealthy" for s in statuses):
        overall = "unhealthy"
    else:
        overall = "degraded"

    return {
        "status": overall,
        "service": "procurement-service",
        "version": "1.0.0",
        "checks": checks,
    }


@app.get("/api/v1/health")
async def api_health_check():
    return {
        "success": True,
        "data": {
            "status": "healthy",
            "service": "procurement-service",
            "environment": settings.APP_ENV,
            "version": "1.0.0"
        },
        "message": "Procurement Service is running normally"
    }
