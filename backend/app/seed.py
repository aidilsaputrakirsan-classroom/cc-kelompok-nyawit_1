"""
Database seeder — creates demo users for development/testing.

Creates:
  1. Procurement Admin  : admin@sicure.com     (role=admin)
  2. Demo Requester #1  : requester1@sicure.com (role=requester)
  3. Demo Requester #2  : requester2@sicure.com (role=requester)

Usage:
    python -m app.seed
"""

import asyncio

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import async_session
from app.models.enums import UserRole
from app.models.user import User

# ── Demo users ────────────────────────────────────────────────────
DEMO_USERS = [
    {
        "email": "admin@sicure.com",
        "password": "admin1234",
        "full_name": "Procurement Admin",
        "role": UserRole.ADMIN,
    },
    {
        "email": "requester1@sicure.com",
        "password": "requester1234",
        "full_name": "Budi Santoso",
        "role": UserRole.REQUESTER,
    },
    {
        "email": "requester2@sicure.com",
        "password": "requester1234",
        "full_name": "Siti Rahayu",
        "role": UserRole.REQUESTER,
    },
]


async def seed_users() -> None:
    """Insert demo users if they don't already exist."""
    async with async_session() as session:
        for user_data in DEMO_USERS:
            result = await session.execute(
                select(User).where(User.email == user_data["email"])
            )
            existing = result.scalar_one_or_none()

            if existing is not None:
                role_display = (
                    existing.role.value
                    if hasattr(existing.role, "value")
                    else str(existing.role)
                )
                print(
                    f"[seed] Sudah ada : {existing.email} "
                    f"(id={existing.id}, role={role_display})"
                )
                continue

            user = User(
                email=user_data["email"],
                hashed_password=hash_password(user_data["password"]),
                full_name=user_data["full_name"],
                role=user_data["role"],
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

            role_display = (
                user.role.value if hasattr(user.role, "value") else str(user.role)
            )
            print(f"[seed] Dibuat    : {user.email}")
            print(f"       Password  : {user_data['password']}")
            print(f"       Nama      : {user.full_name}")
            print(f"       Role      : {role_display}")
            print(f"       ID        : {user.id}")
            print()

    print("[seed] Seeding selesai.")
    print()
    print("=== Demo Credentials ===")
    print(f"{'Email':<30} {'Password':<20} {'Role'}")
    print("-" * 70)
    for u in DEMO_USERS:
        role_val = u["role"].value if hasattr(u["role"], "value") else str(u["role"])
        print(f"{u['email']:<30} {u['password']:<20} {role_val}")


if __name__ == "__main__":
    asyncio.run(seed_users())
