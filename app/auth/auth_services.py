import os
from datetime import datetime, timedelta, timezone

from passlib.context import CryptContext
from jose import jwt
from sqlalchemy.future import select

from app.models.user import User, UserCreate
from app.database import async_session

# === Константы конфигурации ===
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# === Контекст для хэширования паролей ===
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка соответствия пароля и хэша."""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Хэширует пароль с использованием bcrypt."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)) -> str:
    """Создаёт JWT access token с заданным временем жизни."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Декодирует JWT токен."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


async def register_user(user_data: UserCreate) -> User:
    """Создаёт нового пользователя."""
    async with async_session() as session:
        user = User(
            username=user_data.username,
            hashed_password=hash_password(user_data.password)
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def authenticate_user(username: str, password: str) -> User | None:
    """Проверяет логин и пароль пользователя."""
    async with async_session() as session:
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.hashed_password):
            return None
        return user
