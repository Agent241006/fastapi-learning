from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.train import Train, Seat
from app.models.user import User, UserRole
from app.services.auth_service import get_current_admin, create_access_token
from app.core.security import verify_password

router = APIRouter(prefix="/admin", tags=["Admin Train Management"])

@router.post("/trains", status_code=status.HTTP_201_CREATED)
async def create_train(train_data: dict, current_user: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    train_number = train_data.get("train_number")
    
    # Check if train already exists
    existing_train = await db.execute(select(Train).filter_by(train_number=train_number))
    if existing_train.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Train with this number already exists.")

    new_train = Train(
        train_number=train_number,
        train_name=train_data.get("train_name"),
        source=train_data.get("source"),
        destination=train_data.get("destination"),
        total_seats=train_data.get("total_seats", 50)
    )
    db.add(new_train)
    await db.commit()
    await db.refresh(new_train)

    # Automatically generate seats for the train
    for i in range(1, new_train.total_seats + 1):
        seat = Seat(
            train_id=new_train.id,
            seat_number=f"S-{i}",
            class_type="CHAIR_CAR",
            is_booked=0
        )
        db.add(seat)
    
    await db.commit()

    return {
        "message": "Train created successfully with seats generated!",
        "train_id": new_train.id,
        "train_number": new_train.train_number,
        "total_seats": new_train.total_seats
    }

@router.delete("/trains/{train_id}")
async def delete_train(train_id: int, current_user: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Train).filter_by(id=train_id))
    train = result.scalar_one_or_none()

    if not train:
        raise HTTPException(status_code=404, detail="Train not found.")

    await db.delete(train)
    await db.commit()

    return {"message": f"Train ID {train_id} and its seats deleted successfully."}

@router.post("/login")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter_by(email=form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    role_value = user.role.value if hasattr(user.role, "value") else user.role
    access_token = create_access_token(data={"sub": user.email, "role": role_value})
    return {"access_token": access_token, "token_type": "bearer"}