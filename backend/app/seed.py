"""
Database seeder — creates the initial admin user if it doesn't exist.

Usage:
    python -m app.seed
"""

import asyncio

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import async_session
from app.models.enums import UserRole
from app.models.user import User

# ── Default admin credentials ─────────────────────────────────────
ADMIN_EMAIL = "admin@sicure.com"
ADMIN_PASSWORD = "admin1234"
ADMIN_FULL_NAME = "System Administrator"


async def seed_admin() -> None:
    """Insert the default admin user if not already present."""
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.email == ADMIN_EMAIL)
        )
        existing = result.scalar_one_or_none()

        if existing is not None:
            print(f"[seed] Admin user sudah ada: {existing.email} (id={existing.id})")
            return

        admin = User(
            email=ADMIN_EMAIL,
            hashed_password=hash_password(ADMIN_PASSWORD),
            full_name=ADMIN_FULL_NAME,
            role=UserRole.ADMIN,
        )
        session.add(admin)
        await session.commit()
        await session.refresh(admin)

        # Extract role value safely for display (handles both Enum and string)
        role_display = admin.role.value if hasattr(admin.role, 'value') else str(admin.role)

        print(f"[seed] Admin user berhasil dibuat:")
        print(f"       Email    : {admin.email}")
        print(f"       Password : {ADMIN_PASSWORD}")
        print(f"       Role     : {role_display}")
        print(f"       ID       : {admin.id}")


if __name__ == "__main__":
    asyncio.run(seed_admin())
