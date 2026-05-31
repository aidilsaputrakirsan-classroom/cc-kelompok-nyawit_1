"""
Seeder untuk Auth Service — membuat user demo.

Jalankan:
    python seed.py

Atau via Docker:
    docker compose -f docker-compose.microservices.yml exec auth-service python seed.py

User yang dibuat:
    - admin@sicure.com (admin) — bisa approve PR, issue PO, verify GRN
    - requester1@sicure.com (requester) — bisa buat PR, upload GRN
    - requester2@sicure.com (requester) — user kedua untuk testing
"""

import asyncio

from sqlalchemy import select

from database import async_session, engine, Base
from models import User, UserRole
from security import hash_password

# Data user demo
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


async def seed():
    """Buat tabel dan insert user demo."""
    # Buat tabel jika belum ada
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        for user_data in DEMO_USERS:
            # Cek apakah user sudah ada
            result = await db.execute(
                select(User).where(User.email == user_data["email"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"  ⏭️  {user_data['email']} sudah ada, skip.")
                continue

            user = User(
                email=user_data["email"],
                hashed_password=hash_password(user_data["password"]),
                full_name=user_data["full_name"],
                role=user_data["role"],
            )
            db.add(user)
            print(f"  ✅ {user_data['email']} ({user_data['role'].value}) dibuat.")

        await db.commit()

    print("\n🎉 Seeding selesai!")
    print("\nCredential login:")
    print("  admin@sicure.com / admin1234 (Admin)")
    print("  requester1@sicure.com / requester1234 (Requester)")
    print("  requester2@sicure.com / requester1234 (Requester)")


if __name__ == "__main__":
    print("🌱 Seeding Auth Service database...\n")
    asyncio.run(seed())
