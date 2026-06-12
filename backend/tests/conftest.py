"""
Konfigurasi test untuk SiCure — setup async database test.
Menggunakan PostgreSQL test database terpisah atau SQLite untuk testing cepat.
"""
import asyncio
import json
import pytest
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db, engine as original_engine
from app.main import app


# ── Ambang nilai PR yang menentukan jumlah minimal vendor (lihat config) ──
QUOTE_THRESHOLD = 5_000_000.0


def pr_multipart(title, justification, items, vendors=None):
    """Bangun payload multipart untuk POST /api/v1/requisitions/ (kontrak baru).

    Mengembalikan tuple ``(data, files)`` yang siap dipakai:
        data, files = pr_multipart(...)
        await client.post(url, data=data, files=files, headers=headers)

    Argumen:
        title (str), justification (str | None)
        items (list[dict]): tiap item {item_name, quantity, unit_of_measure,
            estimated_unit_price}
        vendors (list[dict] | None): tiap vendor {vendor_name, vendor_contact,
            quoted_price, survey_date, is_recommended}. Jika None, helper membuat
            jumlah vendor minimal sesuai total PR (3 bila total > 5.000.000,
            selain itu 1), vendor pertama is_recommended=true, quoted_price tiap
            vendor = total PR (atau nilai positif bila total 0), survey_date
            "2026-01-01".
    """
    total = sum(
        round(i["quantity"] * i["estimated_unit_price"], 2) for i in items
    )

    if vendors is None:
        count = 3 if total > QUOTE_THRESHOLD else 1
        price = total if total > 0 else 1000
        vendors = []
        for idx in range(count):
            vendors.append(
                {
                    "vendor_name": f"Vendor {idx + 1}",
                    "vendor_contact": f"0812000000{idx:02d}",
                    "quoted_price": price,
                    "survey_date": "2026-01-01",
                    "is_recommended": idx == 0,
                }
            )

    data = {
        "title": title,
        "justification": justification if justification is not None else "",
        "items_json": json.dumps(items),
        "vendor_quotes_json": json.dumps(vendors),
    }

    files = [
        (
            f"vendor_quotes[{idx}].survey_evidence",
            ("bukti.jpg", b"\xff\xd8\xff", "image/jpeg"),
        )
        for idx in range(len(vendors))
    ]

    return data, files


# Opsi 1: Gunakan SQLite untuk testing cepat (recommended untuk CI)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_sicure.db"

# Opsi 2: Jika ingin tetap pakai PostgreSQL (lebih realistis tapi lebih lambat)
# SQLALCHEMY_TEST_DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/sicure_test_db"


@pytest.fixture(scope="session")
def event_loop():
    """Buat event loop untuk async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_engine():
    """Buat engine test terpisah."""
    engine = create_async_engine(
        SQLALCHEMY_TEST_DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_TEST_DATABASE_URL else {},
        poolclass=StaticPool,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup: drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Buat session test baru untuk setiap test function."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    async with async_session_maker() as session:
        yield session


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Test client async dengan database override.
    Menggunakan AsyncClient karena FastAPI app Anda async.
    """
    async def override_get_db():
        """Override dependency get_db dengan test session."""
        yield db_session
    
    # Override the dependency
    app.dependency_overrides[get_db] = override_get_db
    
    # Create async test client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    # Clear overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
async def auth_headers(client: AsyncClient):
    """
    Helper: Register + login user test, return auth headers.
    """
    # Register requester
    register_data = {
        "email": "test@example.com",
        "password": "TestPassword123",
        "full_name": "Test User"
    }
    
    await client.post("/api/v1/auth/register-requester", json=register_data)
    
    # Login
    login_data = {
        "email": "test@example.com",
        "password": "TestPassword123"
    }
    
    response = await client.post("/api/v1/auth/login", json=login_data)
    data = response.json()
    
    # Extract access token from APIResponse structure
    access_token = data["data"]["access_token"]
    
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
async def admin_auth_headers(client: AsyncClient, db_session: AsyncSession):
    """
    Helper: Create admin user and login, return auth headers.
    """
    from app.core.security import hash_password
    from app.models.user import User
    from app.models.enums import UserRole
    
    # Create admin user directly in database
    admin_user = User(
        email="admin@test.com",
        hashed_password=hash_password("AdminPass123"),
        full_name="Admin User",
        role=UserRole.ADMIN
    )
    db_session.add(admin_user)
    await db_session.commit()
    
    # Login as admin
    login_data = {
        "email": "admin@test.com",
        "password": "AdminPass123"
    }
    
    response = await client.post("/api/v1/auth/login", json=login_data)
    data = response.json()
    
    # Extract access token from APIResponse structure
    access_token = data["data"]["access_token"]
    
    return {"Authorization": f"Bearer {access_token}"}