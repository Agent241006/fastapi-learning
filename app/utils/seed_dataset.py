import csv
import asyncio
from sqlalchemy import text
from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.train import Train, Seat
from app.models.booking import Booking

async def import_trains_from_csv(file_path: str):
    async with AsyncSessionLocal() as session:
        try:
            # 1. Clear existing records safely with CASCADE to avoid FK conflicts
            print(">>> Cleaning old database records...")
            await session.execute(text("TRUNCATE TABLE bookings, seats, trains CASCADE;"))
            await session.commit()

            print(f">>> Reading dataset from {file_path}...")
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                count = 0
                for row in reader:
                    # Add Train
                    train = Train(
                        train_number=row['train_number'].strip(),
                        train_name=row['train_name'].strip(),
                        source=row['source'].strip(),
                        destination=row['destination'].strip(),
                        total_seats=int(row['total_seats'])
                    )
                    session.add(train)
                    await session.flush() # Flush to generate train.id

                    # Auto-generate seats for this train
                    for i in range(1, int(row['total_seats']) + 1):
                        seat = Seat(
                            train_id=train.id,
                            seat_number=f"S-{i}",
                            class_type="CHAIR_CAR",
                            is_booked=0
                        )
                        session.add(seat)
                    count += 1
                
                await session.commit()
                print(f">>> SUCCESS: {count} trains along with their seats successfully seeded!")
        except Exception as e:
            await session.rollback()
            print(f">>> ERROR DURING SEEDING: {e}")

if __name__ == "__main__":
    asyncio.run(import_trains_from_csv("data/trains_dataset.csv"))