from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class Train(Base):
    __tablename__ = "trains"

    id = Column(Integer, primary_key=True, index=True)
    train_number = Column(String, unique=True, index=True, nullable=False)
    train_name = Column(String, nullable=False)
    source = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    total_seats = Column(Integer, nullable=False)

    seats = relationship("Seat", back_populates="train", cascade="all, delete-orphan")
    schedules = relationship("TrainSchedule", back_populates="train", cascade="all, delete-orphan")

class TrainSchedule(Base):
    __tablename__ = "train_schedules"

    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(Integer, ForeignKey("trains.id"), nullable=False)
    departure_time = Column(DateTime, nullable=False)
    arrival_time = Column(DateTime, nullable=False)

    train = relationship("Train", back_populates="schedules")

class Seat(Base):
    __tablename__ = "seats"

    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(Integer, ForeignKey("trains.id"), nullable=False)
    seat_number = Column(String, nullable=False) # e.g., "A1-24", "S2-12"
    class_type = Column(String, nullable=False) # AC_1, AC_2, SLEEPER
    is_booked = Column(Integer, default=0) # 0 = Available, 1 = Booked

    train = relationship("Train", back_populates="seats")
    bookings = relationship("Booking", back_populates="seat")