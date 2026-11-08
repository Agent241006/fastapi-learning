from pydantic import BaseModel
from datetime import datetime

class BookingCreate(BaseModel):
    train_id: int
    seat_id: int

class BookingResponse(BaseModel):
    id: int
    pnr_number: str
    user_id: int
    train_id: int
    seat_id: int
    booking_status: str
    booked_at: datetime

    class Config:
        from_attributes = True