# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select
# from fastapi import HTTPException, status
# from app.models.user import User, UserRole
# from app.core.security import get_password_hash, verify_password, create_access_token

# async def register_user(db: AsyncSession, user_data):
#     # Check if email exists
#     query = select(User).where(User.email == user_data.email)
#     result = await db.execute(query)
#     if result.scalar_one_or_none():
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Email is already registered."
#         )
    
#     hashed_pwd = get_password_hash(user_data.password)
#     new_user = User(
#         email=user_data.email,
#         hashed_password=hashed_pwd,
#         full_name=user_data.full_name,
#         role=UserRole.PASSENGER
#     )
    
#     db.add(new_user)
#     await db.flush()
#     await db.refresh(new_user)
#     return new_user

# async def authenticate_user(db: AsyncSession, credentials):
#     query = select(User).where(User.email == credentials.email)
#     result = await db.execute(query)
#     user = result.scalar_one_or_none()
    
#     if not user or not verify_password(credentials.password, user.hashed_password):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect email or password.",
#             headers={"WWW-Authenticate": "Bearer"}
#         )
    
#     access_token = create_access_token(data={"sub": user.email, "role": user.role})
#     return {"access_token": access_token, "token_type": "bearer"}

import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.future import select
from app.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash, verify_password

SECRET_KEY = "super_secret_train_booking_jwt_key_2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def register_user(db: AsyncSessionLocal, user_data):
    query = select(User).where(User.email == user_data.email)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered."
        )
    
    hashed_pwd = get_password_hash(user_data.password)
    
    # Determine role (default to PASSENGER if not provided, or handle admin check)
    user_role = getattr(user_data, "role", UserRole.PASSENGER)

    new_user = User(
        email=user_data.email,
        hashed_password=hashed_pwd,
        full_name=user_data.full_name,
        role=user_role
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def authenticate_user(db: AsyncSessionLocal, credentials):
    query = select(User).where(User.email == credentials.username) # OAuth2PasswordRequestForm uses 'username' field for email/username
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Handle role representation cleanly as string or Enum
    role_value = user.role.value if hasattr(user.role, "value") else user.role

    access_token = create_access_token(data={"sub": user.email, "role": role_value})
    return {"access_token": access_token, "token_type": "bearer"}

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email: str = payload.get("sub")
        if user_email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).filter_by(email=user_email))
        user = result.scalar_one_or_none()
        if user is None:
            raise credentials_exception
        return user

def get_current_admin(current_user: User = Depends(get_current_user)):
    role_value = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    if role_value != "ADMIN" and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required to perform this action."
        )
    return current_user