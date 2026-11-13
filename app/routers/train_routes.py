# from fastapi import APIRouter, Depends, status, HTTPException
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select
# from app.database import get_db
# from app.models.train import Train, Seat
# from app.schemas.train_schema import TrainCreate, TrainResponse
# from typing import List

# router = APIRouter(prefix="/trains", tags=["Trains"])

# @router.post("/", response_model=TrainResponse, status_code=status.HTTP_201_CREATED)
# async def create_train(train_data: TrainCreate, db: AsyncSession = Depends(get_db)):
#     # Create train
#     new_train = Train(
#         train_number=train_data.train_number,
#         train_name=train_data.train_name,
#         source=train_data.source,
#         destination=train_data.destination,
#         total_seats=train_data.total_seats
#     )
#     db.add(new_train)
#     await db.flush()
    
#     # Automatically generate seats for the train
#     for i in range(1, train_data.total_seats + 1):
#         seat = Seat(
#             train_id=new_train.id,
#             seat_number=f"S-{i}",
#             class_type="SLEEPER",
#             is_booked=0
#         )
#         db.add(seat)
        
#     await db.refresh(new_train)
#     return new_train

# @router.get("/", response_model=List[TrainResponse])
# async def get_all_trains(db: AsyncSession = Depends(get_db)):
#     query = select(Train)
#     result = await db.execute(query)
#     return result.scalars().all()

# @router.get("/search", response_model=List[TrainResponse])
# async def search_trains(source: str, destination: str, db: AsyncSession = Depends(get_db)):
#     query = select(Train).where(
#         Train.source.ilike(f"%{source}%"),
#         Train.destination.ilike(f"%{destination}%")
#     )
#     result = await db.execute(query)
#     trains = result.scalars().all()
    
#     if not trains:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No trains found for this route.")
#     return trains
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_, and_
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
    await db.flush() # Generate train.id
    
    # Automatically generate seats for the train
    for i in range(1, train_data.total_seats + 1):
        seat = Seat(
            train_id=new_train.id,
            seat_number=f"S-{i}",
            class_type="CHAIR_CAR",
            is_booked=0
        )
        db.add(seat)
        
    await db.commit()
    await db.refresh(new_train)
    return new_train

@router.get("/", response_model=List[TrainResponse])
async def get_all_trains(db: AsyncSession = Depends(get_db)):
    query = select(Train)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/search")
async def search_trains(source: str, destination: str, db: AsyncSession = Depends(get_db)):
    # Strict directional case-insensitive match (Source -> Destination only)
    query = select(Train).filter(
        Train.source.ilike(f"%{source}%"),
        Train.destination.ilike(f"%{destination}%")
    )
    result = await db.execute(query)
    trains = result.scalars().all()

    if not trains:
        return []

    train_results = []
    for train in trains:
        seat_count_query = select(func.count(Seat.id)).filter_by(train_id=train.id, is_booked=0)
        seat_res = await db.execute(seat_count_query)
        available_seats = seat_res.scalar() or 0

        train_results.append({
            "id": train.id,
            "train_number": train.train_number,
            "train_name": train.train_name,
            "source": train.source,
            "destination": train.destination,
            "total_seats": train.total_seats,
            "available_seats": available_seats
        })

    return train_results

@router.get("/{train_id}/seats")
async def get_train_seats(train_id: int, db: AsyncSession = Depends(get_db)):
    # Fetch only unbooked seats for interactive dropdown selection
    result = await db.execute(select(Seat).filter_by(train_id=train_id, is_booked=0))
    seats = result.scalars().all()
    return seats