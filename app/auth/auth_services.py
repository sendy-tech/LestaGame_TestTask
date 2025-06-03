from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.auth.auth_models import User, UserCreate
from app.database import async_session
import os

# Константы и секреты
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Контекст для хэширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=30)) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

# Регистрация пользователя
async def register_user(user_data: UserCreate) -> User:
    async with async_session() as session:
        user = User(
            username=user_data.username,
            hashed_password=hash_password(user_data.password)
        )
        session.add(user)
        await session.commit()
        return user

# Аутентификация пользователя
async def authenticate_user(username: str, password: str) -> User | None:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.hashed_password):
            return None
        return user
