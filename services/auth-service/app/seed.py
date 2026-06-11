import asyncio
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import engine, async_session
from app.models.enums import UserRole
from app.models.user import User

ADMIN_USER = {
    "email": "admin@sicure.com",
    "password": "admin1234",
    "full_name": "Procurement Admin",
    "role": UserRole.ADMIN,
}

REQUESTER_USERS = [
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
    {
        "email": "requester3@sicure.com",
        "password": "requester1234",
        "full_name": "Rizky Pratama",
        "role": UserRole.REQUESTER,
    },
]


async def seed_users(db: AsyncSession):
    # Ensure tables are created first
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Admin
    result = await db.execute(select(User).where(User.email == ADMIN_USER["email"]))
    if result.scalar_one_or_none() is None:
        print(f"🌱 Seeding admin user: {ADMIN_USER['email']}")
        admin = User(
            email=ADMIN_USER["email"],
            hashed_password=hash_password(ADMIN_USER["password"]),
            full_name=ADMIN_USER["full_name"],
            role=ADMIN_USER["role"],
        )
        db.add(admin)

    # Requesters
    for user_data in REQUESTER_USERS:
        result = await db.execute(select(User).where(User.email == user_data["email"]))
        if result.scalar_one_or_none() is None:
            print(f"🌱 Seeding requester user: {user_data['email']}")
            req = User(
                email=user_data["email"],
                hashed_password=hash_password(user_data["password"]),
                full_name=user_data["full_name"],
                role=user_data["role"],
            )
            db.add(req)

    await db.commit()


async def main():
    print("🔄 Starting Auth Service database seeding...")
    async with async_session() as session:
        await seed_users(session)
    print("✅ Auth Service database seeding completed.")


if __name__ == "__main__":
    asyncio.run(main())
