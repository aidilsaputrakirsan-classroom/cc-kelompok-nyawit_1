"""
Database connection untuk Auth Service.

Auth Service punya database SENDIRI (auth_db), terpisah dari
database procurement. Ini prinsip "database per service".
"""

import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# URL database — di Docker Compose, hostname "auth-db" merujuk ke container PostgreSQL auth
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5433/auth_db",
)

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class untuk semua model di Auth Service."""
    pass


async def get_db() -> AsyncSession:
    """Dependency: beri database session ke setiap request."""
    async with async_session() as session:
        yield session
