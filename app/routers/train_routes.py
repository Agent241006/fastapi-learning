from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.train import Train, Seat
from app.schemas.train_schema import TrainCreate, TrainResponse
from typing import List

router = APIRouter(prefix="/trains", tags=["Trains"])

@router.post("/", response_model=TrainResponse, status_code=status.HTTP_201_CREATED)
async def create_train(train_data: TrainCreate, db: AsyncSession = Depends(get_db)):
    # Create train
    new_train = Train(
        train_number=train_data.train_number,
        train_name=train_data.train_name,
        source=train_data.source,
        destination=train_data.destination,
        total_seats=train_data.total_seats
    )
    db.add(new_train)
    await db.flush()
    
    # Automatically generate seats for the train
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

@router.get("/", response_model=List[TrainResponse])
async def get_all_trains(db: AsyncSession = Depends(get_db)):
    query = select(Train)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/search", response_model=List[TrainResponse])
async def search_trains(source: str, destination: str, db: AsyncSession = Depends(get_db)):
    query = select(Train).where(
        Train.source.ilike(f"%{source}%"),
        Train.destination.ilike(f"%{destination}%")
    )
    result = await db.execute(query)
    trains = result.scalars().all()
    
    if not trains:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No trains found for this route.")
    return trains