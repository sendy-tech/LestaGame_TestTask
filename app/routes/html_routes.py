import re
from http import HTTPStatus
from urllib.parse import quote, unquote

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session, get_db
from app.models.user import User
from app.auth.auth_services import verify_password, hash_password, create_access_token
from app.auth.dependencies import get_current_user

templates = Jinja2Templates(directory="app/templates")
router = APIRouter()

PASSWORD_HINT = "Пароль должен быть не менее 8 символов и содержать буквы и цифры."

def is_valid_password(password: str) -> bool:
    """Простая валидация пароля по длине и наличию букв/цифр."""
    return (
        len(password) >= 8 and
        bool(re.search(r"[A-Za-z]", password)) and
        bool(re.search(r"\d", password))
    )


@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_form(request: Request):
    """Форма входа."""
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", include_in_schema=False)
async def login_user(request: Request, username: str = Form(...), password: str = Form(...)):
    """Обработка логина пользователя."""
    async with async_session() as session:
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.hashed_password):
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": "Неверный логин или пароль"
            })

    # Устанавливаем токен в cookie
    response = RedirectResponse(url="/", status_code=HTTPStatus.SEE_OTHER)
    token = create_access_token({"sub": str(user.id)})
    response.set_cookie("access_token", token, httponly=True, samesite="lax")
    return response


@router.get("/register", response_class=HTMLResponse, include_in_schema=False)
async def register_form(request: Request):
    """Форма регистрации."""
    return templates.TemplateResponse("register.html", {"request": request, "password_hint": PASSWORD_HINT})


@router.post("/register", include_in_schema=False)
async def register_user(request: Request, username: str = Form(...), password: str = Form(...)):
    """Обработка регистрации."""
    async with async_session() as session:
        result = await session.execute(select(User).where(User.username == username))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            return templates.TemplateResponse("register.html", {
                "request": request,
                "error": "Пользователь уже существует",
                "password_hint": PASSWORD_HINT
            })

        if not is_valid_password(password):
            return templates.TemplateResponse("register.html", {
                "request": request,
                "error": "Пароль не соответствует требованиям.",
                "password_hint": PASSWORD_HINT
            })

        new_user = User(username=username, hashed_password=hash_password(password))
        session.add(new_user)
        await session.commit()

    return RedirectResponse(url="/auth/login", status_code=HTTPStatus.SEE_OTHER)


@router.get("/logout", response_class=HTMLResponse, include_in_schema=False)
def logout():
    """Выход пользователя — удаление токена."""
    response = RedirectResponse(url="/", status_code=HTTPStatus.SEE_OTHER)
    response.delete_cookie("access_token")
    response.set_cookie("msg", "Upload available to authorized users only", max_age=5)
    return response


@router.get("/account", response_class=HTMLResponse, include_in_schema=False)
async def account_page(request: Request, current_user: User = Depends(get_current_user)):
    """Страница управления аккаунтом."""
    msg = request.cookies.get("msg")
    msg_class = request.cookies.get("msg_class", "flash-success")

    context = {
        "request": request,
        "current_user": current_user,
        "password_hint": PASSWORD_HINT,
        "msg": unquote(msg) if msg else None,
        "msg_class": msg_class
    }

    response = templates.TemplateResponse("account.html", context)
    response.delete_cookie("msg")
    response.delete_cookie("msg_class")
    return response


@router.post("/change-password", include_in_schema=False)
async def change_password(
    old_password: str = Form(...),
    new_password: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """Изменение пароля."""
    if not verify_password(old_password, current_user.hashed_password):
        response = RedirectResponse("/auth/account", status_code=HTTPStatus.SEE_OTHER)
        response.set_cookie("msg", quote("Старый пароль неверен"), max_age=5)
        response.set_cookie("msg_class", "flash-error", max_age=5)
        return response

    if not is_valid_password(new_password):
        response = RedirectResponse("/auth/account", status_code=HTTPStatus.SEE_OTHER)
        response.set_cookie("msg", quote("Новый пароль не соответствует требованиям."), max_age=5)
        response.set_cookie("msg_class", "flash-error", max_age=5)
        return response

    async with async_session() as session:
        await session.execute(
            update(User)
            .where(User.id == current_user.id)
            .values(hashed_password=hash_password(new_password))
        )
        await session.commit()

    response = RedirectResponse("/auth/account", status_code=HTTPStatus.SEE_OTHER)
    response.set_cookie("msg", quote("Пароль успешно изменён"), max_age=5)
    response.set_cookie("msg_class", "flash-success", max_age=5)
    return response


@router.post("/delete-account", include_in_schema=False)
async def delete_account(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Удаление аккаунта."""
    await db.delete(current_user)
    await db.commit()

    response = RedirectResponse(url="/", status_code=HTTPStatus.SEE_OTHER)
    response.delete_cookie("access_token")
    response.set_cookie("msg", quote("Аккаунт удалён. Вы можете войти под другим пользователем."), max_age=5)
    response.set_cookie("msg_class", "flash-success", max_age=5)
    return response
