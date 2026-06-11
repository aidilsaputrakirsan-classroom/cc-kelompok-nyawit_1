from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.routers import auth
from app.models.user import User
from app.models.token_blacklist import TokenBlacklist

app = FastAPI(
    title="SiCure Auth Service",
    description="Authentication and Authorization microservice",
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

# Include Auth router
app.include_router(auth.router)


@app.on_event("startup")
async def startup_event():
    # Automatically create tables in auth-db on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "auth-service", "env": settings.APP_ENV}


@app.get("/api/v1/health")
async def api_health_check():
    return {
        "success": True,
        "data": {
            "status": "healthy",
            "service": "auth-service",
            "environment": settings.APP_ENV,
            "version": "1.0.0"
        },
        "message": "Auth Service is running normally"
    }


@app.get("/api/v1/auth/health")
async def api_auth_health_check():
    return {
        "status": "healthy",
        "service": "auth-service",
        "env": settings.APP_ENV
    }

