from typing import Optional

from fastapi import Request
from app.auth.auth_services import decode_token
from app.database import async_session
from sqlalchemy import select
from app.auth.auth_models import User

async def get_current_user_optional(request: Request) -> Optional[User]:
    token = request.cookies.get("access_token")
    if not token:
        return None

    try:
        payload = decode_token(token)
        user_id: int = int(payload.get("sub"))  # 👈 исправлено
        if user_id is None:
            return None
    except Exception:
        return None

    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()