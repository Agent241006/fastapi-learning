import asyncio
from app.database import AsyncSessionLocal
from app.models.train import Train, Seat

async def seed_database():
    async with AsyncSessionLocal() as session:
        # Check if trains already exist to avoid duplication
        from sqlalchemy.future import select
        existing = await session.execute(select(Train))
        if existing.scalars().first():
            print("Database already has data!")
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
        print("Sample Train & Seats Added Successfully! Train ID is 1, Seat IDs are 1 to 10.")

if __name__ == "__main__":
    asyncio.run(seed_database())