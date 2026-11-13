from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.future import select
from app.database import engine, Base, AsyncSessionLocal
from app.routers import auth_routes, train_routes, booking_routes, admin_routes
from app.models.user import User, UserRole
from app.core.security import get_password_hash

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
app.include_router(admin_routes.router)

@app.on_event("startup")
async def startup():
    # 1. Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 2. Auto-seed Admin and Passenger safely without hardcoding ID
    async with AsyncSessionLocal() as session:
        # Check and seed Admin
        admin_res = await session.execute(select(User).filter_by(email="admin@example.com"))
        if not admin_res.scalar_one_or_none():
            admin_user = User(
                email="admin@example.com",
                full_name="System Admin",
                hashed_password=get_password_hash("admin_password"),
                role=UserRole.ADMIN
            )
            session.add(admin_user)
            print(">>> DEFAULT ADMIN USER CREATED SUCCESSFULLY! <<<")

        # Check and seed Passenger
        passenger_res = await session.execute(select(User).filter_by(email="test@example.com"))
        if not passenger_res.scalar_one_or_none():
            passenger_user = User(
                email="test@example.com",
                full_name="Test Passenger",
                hashed_password=get_password_hash("dummy_password"),
                role=UserRole.PASSENGER
            )
            session.add(passenger_user)
            print(">>> DEFAULT PASSENGER USER CREATED SUCCESSFULLY! <<<")

        await session.commit()
@app.get("/")
def read_root():
    return {"message": "Welcome to the Train Ticket Booking API. Server is running smoothly!"}