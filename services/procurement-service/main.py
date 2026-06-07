"""
Procurement Service — Microservice untuk Procurement Management.

Tanggung jawab:
- Purchase Requisitions (CRUD + approval)
- Purchase Orders (issue + list)
- GRN Documents (upload + verification)

TIDAK menangani auth — verifikasi token dilakukan via HTTP call ke Auth Service.
"""

import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import httpx
from sqlalchemy import text

from logging_config import setup_logging
from logging_middleware import RequestLoggingMiddleware
from metrics import metrics

setup_logging()
logger = logging.getLogger(__name__)

from database import engine, Base
from auth_client import auth_circuit, AUTH_SERVICE_URL, TIMEOUT_SECONDS
from routers import requisitions, requisitions_admin, purchase_orders, grn, grn_admin

app = FastAPI(
    title="SiCure Procurement Service",
    description="Procurement microservice — PR, PO, GRN management",
    version="2.0.0",
)


@app.on_event("startup")
async def startup():
    """Buat tabel jika belum ada."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ── CORS ──────────────────────────────────────────────────────────
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

app.add_middleware(RequestLoggingMiddleware)

# ── Routers ───────────────────────────────────────────────────────
app.include_router(requisitions.router)
app.include_router(requisitions_admin.router)
app.include_router(purchase_orders.router)
app.include_router(grn.router)
app.include_router(grn_admin.router)

# ── Static files (uploads) ────────────────────────────────────────
upload_path = Path(os.getenv("UPLOAD_DIR", "./uploads"))
upload_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")


# ── Health Check (Aggregated) ─────────────────────────────────────
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
                f"{AUTH_SERVICE_URL}/health", timeout=2.0
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
        "version": "2.0.0",
        "checks": checks,
    }


# ── GET /metrics ──────────────────────────────────────────────────
@app.get("/metrics")
def get_metrics():
    """Return application metrics termasuk recent error rate untuk alerting."""
    return {
        "service": "procurement-service",
        **metrics.get_metrics(),
        "recent_error_rate": metrics.get_recent_error_rate(window_seconds=60),
    }
