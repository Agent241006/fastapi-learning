from fastapi import FastAPI

from app.routers import users

app = FastAPI(
    title="User Management API",
    version="1.0.0"
)

app.include_router(users.router)


@app.get("/")
def home():
    return {"message": "User Management API is running"}