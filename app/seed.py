import asyncio
from app.database import AsyncSessionLocal
from app.models.train import Train, Seat
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from sqlalchemy.future import select

async def seed_database():
    async with AsyncSessionLocal() as session:
        # 1. Seed Users (Admin & Passenger) with Proper Hashed Passwords
        admin_res = await session.execute(select(User).filter_by(email="admin@example.com"))
        if not admin_res.scalar_one_or_none():
            admin_user = User(
                email="admin@example.com",
                full_name="System Admin",
                hashed_password=get_password_hash("admin_password"),
                role=UserRole.ADMIN
            )
            session.add(admin_user)
            print(">>> Admin user added: admin@example.com / admin_password")

        passenger_res = await session.execute(select(User).filter_by(email="test@example.com"))
        if not passenger_res.scalar_one_or_none():
            passenger_user = User(
                email="test@example.com",
                full_name="Test Passenger",
                hashed_password=get_password_hash("dummy_password"),
                role=UserRole.PASSENGER
            )
            session.add(passenger_user)
            print(">>> Passenger user added: test@example.com / dummy_password")

        await session.commit()

        # 2. Check if trains already exist to avoid duplication
        existing_trains = await session.execute(select(Train))
        if existing_trains.scalars().first():
            print("Database users updated/checked, and trains already exist!")
            return

        # Add a sample train
        train = Train(
            train_number="12004",
            train_name="Kanpur Shatabdi",
            source="Kanpur",
            destination="Delhi",
            total_seats=10
        )
        session.add(train)
        await session.flush()

        # Add seats for this train
        for i in range(1, 11):
            seat = Seat(
                train_id=train.id,
                seat_number=f"S-{i}",
                class_type="CHAIR_CAR",
                is_booked=0
            )
            session.add(seat)

        await session.commit()
        print(">>> Sample Train, Seats, and Users Added Successfully!")

if __name__ == "__main__":
    asyncio.run(seed_database())