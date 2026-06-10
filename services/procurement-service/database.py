"""
Database connection untuk Procurement Service.

Procurement Service punya database SENDIRI (procurement_db).
Tabel: purchase_requisitions, pr_line_items, purchase_orders, grn_documents.

TIDAK ADA tabel users di sini — user info didapat dari Auth Service via HTTP.
"""

import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5434/procurement_db",
)

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class untuk semua model di Procurement Service."""
    pass


async def get_db() -> AsyncSession:
    """Dependency: beri database session ke setiap request."""
    async with async_session() as session:
        yield session
