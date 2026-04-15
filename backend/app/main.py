from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
    version="0.1.0",
)

# ── CORS middleware (reads ALLOWED_ORIGINS from .env) ─────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return {"status": "ok"}
