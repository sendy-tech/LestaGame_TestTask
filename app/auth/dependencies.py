from fastapi import Request, HTTPException, Depends
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth_services import SECRET_KEY, ALGORITHM
from app.database import get_db
from app.models.user import User


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Получить текущего авторизованного пользователя.
    Выбрасывает исключение 401, если токен отсутствует или некорректен.
    """
    token = extract_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Недопустимый токен")
        user = await db.get(User, int(user_id))
        if not user:
            raise HTTPException(status_code=401, detail="Пользователь не найден")
        return user
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Неверный токен")


async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User | None:
    """
    Получает пользователя, если токен передан и валиден.
    Возвращает None, если токена нет или он некорректен.
    """
    token = extract_token_from_request(request)
    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return None
        return await db.get(User, int(user_id))
    except Exception:
        return None


def extract_token_from_request(request: Request) -> str | None:
    """
    Извлекает токен из заголовка Authorization или из cookie.
    """
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]

    return request.cookies.get("access_token")
