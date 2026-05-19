"""
Konfigurasi test untuk SiCure — setup async database test.
Menggunakan PostgreSQL test database terpisah atau SQLite untuk testing cepat.
"""
import asyncio
import pytest
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db, engine as original_engine
from app.main import app


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