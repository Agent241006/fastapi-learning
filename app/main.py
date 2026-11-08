from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base, AsyncSessionLocal
from app.routers import auth_routes, train_routes, booking_routes
from app.models.train import Train, Seat
from app.models.user import User, UserRole

app = FastAPI(title="Train Booking System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(train_routes.router)
app.include_router(booking_routes.router)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as session:
        default_user = User(
            id=1,
            email="test@example.com",
            hashed_password="dummy_password",
            full_name="Test User",  # Added full_name to satisfy not-null constraint
            role=UserRole.PASSENGER
        )
        session.add(default_user)
        await session.flush()

        train = Train(
            id=1,
            train_number="12004",
            train_name="Kanpur Shatabdi",
            source="Kanpur",
            destination="Delhi",
            total_seats=10
        )
        session.add(train)
        await session.flush()

        for i in range(1, 11):
            seat = Seat(
                train_id=train.id,
                seat_number=f"S-{i}",
                class_type="CHAIR_CAR",
                is_booked=0
            )
            session.add(seat)
        
        await session.commit()
        print(">>> FRESH DATABASE MIGRATED & AUTO-SEEDED SUCCESSFULLY! <<<")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Train Ticket Booking API. Server is running smoothly!"}