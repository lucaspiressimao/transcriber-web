from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.future import select
from .database import get_db
from .models import User
import os
import datetime

SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_default_user(db, username: str, password: str):
    result = await db.execute(select(User).where(User.username == username))
    existing_user = result.scalars().first()
    if not existing_user:
        await register_user(username, password, db)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def hash_password(password):
    return pwd_context.hash(password)

def create_access_token(username: str):
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": username, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(request: Request, db=Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None

    # Se quiser validar com o banco, pode descomentar abaixo:
    # result = await db.execute(select(User).where(User.username == username))
    # user = result.scalars().first()
    # return user

    class UserMock:
        def __init__(self, username):
            self.username = username

    return UserMock(username)

async def register_user(username: str, password: str, db):
    hashed = hash_password(password)
    user = User(username=username, hashed_password=hashed)
    db.add(user)
    await db.commit()

async def authenticate_user(username: str, password: str, db):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    if user and verify_password(password, user.hashed_password):
        return user
    return None