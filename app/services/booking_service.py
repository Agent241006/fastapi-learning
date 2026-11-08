from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.models.booking import Booking
from app.models.train import Seat
import random
import string

async def book_ticket_safely(db: AsyncSession, user_id: int, train_id: int, seat_id: int) -> Booking:
    # 1. Pessimistic Locking: Lock the specific seat row to prevent race conditions
    seat_query = select(Seat).where(Seat.id == seat_id, Seat.train_id == train_id).with_for_update()
    seat_result = await db.execute(seat_query)
    seat = seat_result.scalar_one_or_none()

    if not seat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seat not found for this train.")

    if seat.is_booked == 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seat is already booked. Try another seat.")

    # 2. Mark seat as booked
    seat.is_booked = 1

    # 3. Generate unique PNR
    pnr_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    pnr_number = f"PNR-{pnr_chars}"

    # 4. Create booking record
    new_booking = Booking(
        pnr_number=pnr_number,
        user_id=user_id,
        train_id=train_id,
        seat_id=seat_id,
        booking_status="CONFIRMED"
    )

    db.add(new_booking)
    await db.flush()
    await db.refresh(new_booking)
    return new_booking

async def cancel_ticket_safely(db: AsyncSession, booking_id: int, user_id: int) -> Booking:
    # 1. Fetch booking
    query = select(Booking).where(Booking.id == booking_id)
    result = await db.execute(query)
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found.")
    
    if booking.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to cancel this ticket.")

    if booking.booking_status == "CANCELLED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticket is already cancelled.")

    # 2. Free up the seat with row lock
    seat_query = select(Seat).where(Seat.id == booking.seat_id).with_for_update()
    seat_result = await db.execute(seat_query)
    seat = seat_result.scalar_one_or_none()

    if seat:
        seat.is_booked = 0  # Seat wapas available ho gayi

    # 3. Update booking status
    booking.booking_status = "CANCELLED"
    await db.flush()
    await db.refresh(booking)
    return booking