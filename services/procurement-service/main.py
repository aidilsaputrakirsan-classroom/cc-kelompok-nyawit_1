"""
Procurement Service — Microservice untuk Procurement Management.

Tanggung jawab:
- Purchase Requisitions (CRUD + approval)
- Purchase Orders (issue + list)
- GRN Documents (upload + verification)

TIDAK menangani auth — verifikasi token dilakukan via HTTP call ke Auth Service.
"""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import engine, Base
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


# ── Health Check ──────────────────────────────────────────────────
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "procurement-service",
        "version": "2.0.0",
    }
