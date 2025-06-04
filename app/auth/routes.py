import re
from http import HTTPStatus
from urllib.parse import quote, unquote

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select,update
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import HTMLResponse
from starlette.status import HTTP_303_SEE_OTHER

from app.database import async_session, get_db
from app.auth.auth_models import User
from app.auth.auth_services import (
    verify_password, hash_password,
    create_access_token
)
from app.auth.dependencies import get_current_user_optional

templates = Jinja2Templates(directory="app/templates")
router = APIRouter()

PASSWORD_HINT = "Пароль должен быть не менее 8 символов и содержать буквы и цифры."

def is_valid_password(password: str) -> bool:
    return (
        len(password) >= 8 and
        bool(re.search(r"[A-Za-z]", password)) and
        bool(re.search(r"\d", password))
    )

@router.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "password_hint": PASSWORD_HINT})

@router.post("/register")
async def register_user(request: Request, username: str = Form(...), password: str = Form(...)):
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

    return RedirectResponse(url="/auth/login", status_code=HTTP_303_SEE_OTHER)

@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login_user(request: Request, username: str = Form(...), password: str = Form(...)):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.hashed_password):
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": "Неверный логин или пароль"
            })

    response = RedirectResponse(url="/", status_code=HTTP_303_SEE_OTHER)
    token = create_access_token({"sub": str(user.id)})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax"
    )
    return response

@router.get("/logout", response_class=HTMLResponse)
def logout():
    response = RedirectResponse(url="/", status_code=HTTPStatus.SEE_OTHER)
    response.delete_cookie("access_token")
    response.set_cookie("msg", "Upload available to authorized users only", max_age=5)
    return response

# Страница управления аккаунтом
@router.get("/account", response_class=HTMLResponse)
async def account_page(
    request: Request,
    current_user: User = Depends(get_current_user_optional)
):
    msg = request.cookies.get("msg")
    msg_class = request.cookies.get("msg_class", "flash-success")

    context = {
        "request": request,
        "username": current_user.username,
        "password_hint": PASSWORD_HINT,
        "msg": unquote(msg) if msg else None,
        "msg_class": msg_class
    }

    response = templates.TemplateResponse("account.html", context)
    response.delete_cookie("msg")
    response.delete_cookie("msg_class")
    return response

# Смена пароля
@router.post("/change-password")
async def change_password(
    request: Request,
    old_password: str = Form(...),
    new_password: str = Form(...),
    current_user: User = Depends(get_current_user_optional)
):
    if not verify_password(old_password, current_user.hashed_password):
        msg = quote("Старый пароль неверен")
        response = RedirectResponse("/auth/account", status_code=303)
        response.set_cookie("msg", msg, max_age=5)
        response.set_cookie("msg_class", "flash-error", max_age=5)
        return response

    if not is_valid_password(new_password):
        msg = quote("Новый пароль не соответствует требованиям.")
        response = RedirectResponse("/auth/account", status_code=303)
        response.set_cookie("msg", msg, max_age=5)
        response.set_cookie("msg_class", "flash-error", max_age=5)
        return response

    async with async_session() as session:
        await session.execute(
            update(User)
            .where(User.id == current_user.id)
            .values(hashed_password=hash_password(new_password))
        )
        await session.commit()

    msg = quote("Пароль успешно изменён")
    response = RedirectResponse("/auth/account", status_code=303)
    response.set_cookie("msg", msg, max_age=5)
    response.set_cookie("msg_class", "flash-success", max_age=5)
    return response

# Удаление аккаунта
@router.post("/delete-account")
async def delete_account(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user_optional)
):
    await db.delete(user)
    await db.commit()

    msg = quote("Аккаунт удалён. Вы можете войти под другим пользователем.")
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    response.set_cookie("msg", msg, max_age=5)
    response.set_cookie("msg_class", "flash-success", max_age=5)
    return response