# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select
# from app.database import get_db
# from app.models.booking import Booking
# from app.models.train import Train, Seat
# from pydantic import BaseModel
# from datetime import datetime
# import random
# import string

# router = APIRouter(prefix="/bookings", tags=["Bookings"])

# class BookingCreate(BaseModel):
#     user_id: int
#     train_id: int
#     seat_id: int

# @router.post("/")
# async def create_booking(payload: BookingCreate, db: AsyncSession = Depends(get_db)):
#     # Check seat and book logic...
#     seat_result = await db.execute(select(Seat).filter_by(id=payload.seat_id, train_id=payload.train_id))
#     seat = seat_result.scalars().first()
    
#     if not seat:
#         raise HTTPException(status_code=404, detail="Seat not found for this train.")
#     if seat.is_booked == 1:
#         raise HTTPException(status_code=400, detail="Seat is already booked.")
    
#     seat.is_booked = 1
    
#     # Generate random PNR
#     pnr = "PNR-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
#     booking = Booking(
#         pnr_number=pnr,
#         user_id=payload.user_id,
#         train_id=payload.train_id,
#         seat_id=payload.seat_id,
#         booking_status="CONFIRMED",
#         booked_at=datetime.utcnow()
#     )
#     db.add(booking)
#     await db.commit()
#     await db.refresh(booking)
#     return booking

# @router.get("/pnr/{pnr_number}")
# async def get_pnr_status(pnr_number: str, db: AsyncSession = Depends(get_db)):
#     result = await db.execute(select(Booking).filter_by(pnr_number=pnr_number))
#     booking = result.scalars().first()
#     if not booking:
#         raise HTTPException(status_code=404, detail="Invalid PNR number. Booking not found.")
#     return booking

# @router.put("/pnr/{pnr_number}/cancel")
# async def cancel_booking_by_pnr(pnr_number: str, db: AsyncSession = Depends(get_db)):
#     result = await db.execute(select(Booking).filter_by(pnr_number=pnr_number))
#     booking = result.scalars().first()
    
#     if not booking:
#         raise HTTPException(status_code=404, detail="Booking not found for this PNR.")
    
#     if booking.booking_status == "CANCELLED":
#         return {"message": "Booking is already cancelled.", "pnr_number": pnr_number}
    
#     booking.booking_status = "CANCELLED"
    
#     # Free up the seat
#     seat_result = await db.execute(select(Seat).filter_by(id=booking.seat_id))
#     seat = seat_result.scalars().first()
#     if seat:
#         seat.is_booked = 0
        
#     await db.commit()
#     return {"message": "Booking cancelled successfully!", "pnr_number": pnr_number, "status": "CANCELLED"}



from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.booking import Booking
from app.models.train import Seat, Train
from app.services.auth_service import get_current_user
from app.models.user import User
import uuid

router = APIRouter(prefix="/bookings", tags=["Bookings"])

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_booking(booking_data: dict, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    train_id = booking_data.get("train_id")
    seat_id = booking_data.get("seat_id")

    seat_res = await db.execute(select(Seat).filter_by(id=seat_id, train_id=train_id, is_booked=0))
    seat = seat_res.scalar_one_or_none()

    if not seat:
        raise HTTPException(status_code=400, detail="Seat is already booked or invalid.")

    seat.is_booked = 1
    pnr = f"PNR-{uuid.uuid4().hex[:8].upper()}"

    new_booking = Booking(
        pnr_number=pnr,
        user_id=current_user.id,
        train_id=train_id,
        seat_id=seat_id,
        booking_status="CONFIRMED"
    )

    db.add(new_booking)
    await db.commit()
    await db.refresh(new_booking)

    return {
        "id": new_booking.id,
        "pnr_number": new_booking.pnr_number,
        "booking_status": new_booking.booking_status,
        "train_id": new_booking.train_id,
        "seat_number": seat.seat_number
    }

@router.get("/pnr/{pnr_number}")
async def check_pnr_status(pnr_number: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Booking).filter_by(pnr_number=pnr_number))
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found for this PNR.")

    # Safely handle role whether it's an Enum or string
    user_role = current_user.role.value if hasattr(current_user.role, "value") else current_user.role

    if user_role != "ADMIN" and booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access to this booking details.")

    train_res = await db.execute(select(Train).filter_by(id=booking.train_id))
    train = train_res.scalar_one_or_none()

    seat_res = await db.execute(select(Seat).filter_by(id=booking.seat_id))
    seat = seat_res.scalar_one_or_none()

    return {
        "pnr_number": booking.pnr_number,
        "booking_status": booking.booking_status,
        "booked_at": booking.booked_at,
        "train_name": train.train_name if train else "N/A",
        "train_number": train.train_number if train else "N/A",
        "source": train.source if train else "N/A",
        "destination": train.destination if train else "N/A",
        "seat_number": seat.seat_number if seat else "N/A"
    }

@router.delete("/cancel/{pnr_number}")
async def cancel_booking(pnr_number: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Booking).filter_by(pnr_number=pnr_number))
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")

    # Safely handle role whether it's an Enum or string
    user_role = current_user.role.value if hasattr(current_user.role, "value") else current_user.role

    if user_role != "ADMIN" and booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized to cancel this booking.")

    seat_res = await db.execute(select(Seat).filter_by(id=booking.seat_id))
    seat = seat_res.scalar_one_or_none()
    if seat:
        seat.is_booked = 0

    booking.booking_status = "CANCELLED"
    await db.commit()

    return {"message": f"Booking with PNR {pnr_number} has been cancelled successfully."}