from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    age: int = Field(ge=18, le=100)


class UserResponse(BaseModel):
    id: int
    name: str
    age: int