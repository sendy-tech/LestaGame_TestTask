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
    token = None

    # 1. Попытка из заголовка Authorization
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

    # 2. Попытка из cookie
    if not token:
        token = request.cookies.get("access_token")
    print(f"[DEBUG] Access token received: {token}")

    if not token:
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Недопустимый токен")
    except JWTError:
        raise HTTPException(status_code=401, detail="Неверный токен")

    try:
        user = await db.get(User, int(user_id))
    except ValueError:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    return user


async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User | None:
    token = None

    # 1. Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

    # 2. Cookie fallback
    if not token:
        token = request.cookies.get("access_token")
    print(f"[DEBUG] (Optional) Access token received: {token}")

    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return None
    except JWTError:
        return None

    try:
        user = await db.get(User, int(user_id))
        return user
    except Exception:
        return None
