from sqlalchemy.ext.asyncio import AsyncSession
from app.models.train import Train, Seat

async def create_train_with_seats(db: AsyncSession, train_data):
    new_train = Train(
        train_number=train_data.train_number,
        train_name=train_data.train_name,
        source=train_data.source,
        destination=train_data.destination,
        total_seats=train_data.total_seats
    )
    db.add(new_train)
    await db.flush() # Train ID generate karne ke liye
    
    # Auto-generate seats for this train
    for i in range(1, train_data.total_seats + 1):
        seat = Seat(
            train_id=new_train.id,
            seat_number=f"S-{i}",
            class_type="SLEEPER",
            is_booked=0
        )
        db.add(seat)
        
    await db.refresh(new_train)
    return new_train