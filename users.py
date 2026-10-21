from fastapi import APIRouter, HTTPException, status

from app.schemas import UserCreate, UserResponse

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

users = {
    1: {"name": "Hardik", "age": 21},
    2: {"name": "Aman", "age": 22}
}

next_id = 3


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse
)
def create_user(user: UserCreate):
    global next_id

    user_id = next_id

    users[user_id] = user.model_dump()
    next_id += 1

    return {"id": user_id, **users[user_id]}


@router.get("/", response_model=list[UserResponse])
def get_users():
    return [
        {"id": user_id, **user_data}
        for user_id, user_data in users.items()
    ]


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    if user_id not in users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {"id": user_id, **users[user_id]}


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserCreate):
    if user_id not in users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    users[user_id] = user.model_dump()

    return {"id": user_id, **users[user_id]}


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_user(user_id: int):
    if user_id not in users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    del users[user_id]
    return None