from pydantic import BaseModel
from datetime import datetime

class TrainCreate(BaseModel):
    train_number: str
    train_name: str
    source: str
    destination: str
    total_seats: int

class TrainResponse(BaseModel):
    id: int
    train_number: str
    train_name: str
    source: str
    destination: str
    total_seats: int

    class Config:
        from_attributes = True