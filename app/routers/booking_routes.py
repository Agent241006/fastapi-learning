from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.booking import Booking
from app.models.train import Train, Seat
from pydantic import BaseModel
from datetime import datetime
import random
import string

router = APIRouter(prefix="/bookings", tags=["Bookings"])

class BookingCreate(BaseModel):
    user_id: int
    train_id: int
    seat_id: int

@router.post("/")
async def create_booking(payload: BookingCreate, db: AsyncSession = Depends(get_db)):
    # Check seat and book logic...
    seat_result = await db.execute(select(Seat).filter_by(id=payload.seat_id, train_id=payload.train_id))
    seat = seat_result.scalars().first()
    
    if not seat:
        raise HTTPException(status_code=404, detail="Seat not found for this train.")
    if seat.is_booked == 1:
        raise HTTPException(status_code=400, detail="Seat is already booked.")
    
    seat.is_booked = 1
    
    # Generate random PNR
    pnr = "PNR-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    booking = Booking(
        pnr_number=pnr,
        user_id=payload.user_id,
        train_id=payload.train_id,
        seat_id=payload.seat_id,
        booking_status="CONFIRMED",
        booked_at=datetime.utcnow()
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking

@router.get("/pnr/{pnr_number}")
async def get_pnr_status(pnr_number: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Booking).filter_by(pnr_number=pnr_number))
    booking = result.scalars().first()
    if not booking:
        raise HTTPException(status_code=404, detail="Invalid PNR number. Booking not found.")
    return booking

@router.put("/pnr/{pnr_number}/cancel")
async def cancel_booking_by_pnr(pnr_number: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Booking).filter_by(pnr_number=pnr_number))
    booking = result.scalars().first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found for this PNR.")
    
    if booking.booking_status == "CANCELLED":
        return {"message": "Booking is already cancelled.", "pnr_number": pnr_number}
    
    booking.booking_status = "CANCELLED"
    
    # Free up the seat
    seat_result = await db.execute(select(Seat).filter_by(id=booking.seat_id))
    seat = seat_result.scalars().first()
    if seat:
        seat.is_booked = 0
        
    await db.commit()
    return {"message": "Booking cancelled successfully!", "pnr_number": pnr_number, "status": "CANCELLED"}