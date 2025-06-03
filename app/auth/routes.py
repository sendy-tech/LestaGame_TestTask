from http import HTTPStatus
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from starlette.responses import HTMLResponse
from starlette.status import HTTP_303_SEE_OTHER

from app.database import async_session
from app.auth.auth_models import User
from app.auth.auth_services import verify_password, hash_password, create_access_token

templates = Jinja2Templates(directory="app/templates")
router = APIRouter()

# Форма регистрации
@router.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

# Обработка регистрации
@router.post("/register")
async def register_user(request: Request, username: str = Form(...), password: str = Form(...)):
    response_class = HTMLResponse
    async with async_session() as session:
        result = await session.execute(select(User).where(User.username == username))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            return templates.TemplateResponse("register.html", {
                "request": request,
                "error": "Пользователь уже существует"
            })

        new_user = User(username=username, hashed_password=hash_password(password))
        session.add(new_user)
        await session.commit()

    return RedirectResponse(url="/auth/login", status_code=HTTP_303_SEE_OTHER)

# Форма входа
@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    response_class = HTMLResponse
    return templates.TemplateResponse("login.html", {"request": request})

# Обработка входа
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

# Выход из системы
@router.get("/logout", response_class=HTMLResponse)
def logout():
    response = RedirectResponse(url="/", status_code=HTTPStatus.SEE_OTHER)
    response.delete_cookie("access_token")
    response.set_cookie("msg", "Upload available to authorized users only", max_age=5)
    return response


