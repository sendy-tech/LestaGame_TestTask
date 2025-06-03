import logging, os
from http import HTTPStatus
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Request, UploadFile, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

from sqlalchemy import insert, select, func

from app.services import get_text, term_frequency, inverse_document_frequency
from app.database import async_session, engine, Base
from app.models import FileUpload, WordStat
from app.auth.routes import router as auth_router
from app.auth.dependencies import get_current_user_optional
from app.auth.auth_models import User

VERSION = "0.0.1"

# Настройка логгера
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Инициализация FastAPI
app = FastAPI(
    lifespan=lambda app: lifespan(app),
    max_multipart_memory_size=1024 * 1024 * 100  # Лимит загрузки: 100 MB
)

# Подключение роутов авторизации
app.include_router(auth_router, prefix="/auth", tags=["auth"])

# Настройка Jinja2-шаблонов и статики
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")),
    name="static"
)

# Жизненный цикл приложения: инициализация базы
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ База данных инициализирована.")
    except Exception as e:
        logger.exception(f"❌ Ошибка инициализации БД: {e}")
    yield

# Главная страница: отображает форму и приветствие
@app.get("/", response_class=HTMLResponse)
async def get_root(request: Request, current_user: User = Depends(get_current_user_optional)):
    # Проверка авторизации
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=HTTPStatus.SEE_OTHER)
    msg = request.cookies.get("msg")
    response = templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"current_user": current_user, "msg": msg}
    )
    response.delete_cookie("msg")
    return response

# Обработка загрузки файла: TF/IDF + сохранение
@app.post("/uploadfile", response_class=RedirectResponse)
async def handle_upload(
    file: UploadFile = File(),
    current_user: User = Depends(get_current_user_optional)
):
    # Проверка авторизации
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=HTTPStatus.SEE_OTHER)

    text = await get_text(file)
    tf = await term_frequency(text)
    idf = await inverse_document_frequency(tf)

    # Сохраняем файл и метрики
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                insert(FileUpload).values(user_id=current_user.id, unique_words=len(tf))
            )
            file_id = result.inserted_primary_key[0]

            session.add_all([
                WordStat(file_id=file_id, word=word, tf=tf[word], idf=idf_val)
                for word, idf_val in idf
            ])

    return RedirectResponse(url="/output", status_code=HTTPStatus.SEE_OTHER)

# Страница вывода TF/IDF по последней загрузке пользователя
@app.get("/output", response_class=HTMLResponse)
async def get_output(
    request: Request,
    current_user: User = Depends(get_current_user_optional)
):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=HTTPStatus.SEE_OTHER)

    async with async_session() as session:
        result = await session.execute(
            select(WordStat)
            .join(FileUpload, WordStat.file_id == FileUpload.id)
            .where(FileUpload.user_id == current_user.id)
            .order_by(WordStat.id.desc())
            .limit(50)
        )
        word_stats = result.scalars().all()

    tf = {ws.word: ws.tf for ws in word_stats}
    words = [(ws.word, ws.idf) for ws in word_stats]

    return templates.TemplateResponse(
        request=request,
        name="output.html",
        context={"words": words, "tf": tf}
    )

# Проверка доступности приложения
@app.get("/status")
async def status():
    return JSONResponse(content={"status": "OK"})

# Метрики для пользователя: количество загрузок и уникальные слова
@app.get("/metrics")
async def metrics(current_user: User = Depends(get_current_user_optional)):
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=HTTPStatus.SEE_OTHER)

    async with async_session() as session:
        total_uploads = await session.scalar(
            select(func.count()).select_from(FileUpload).where(FileUpload.user_id == current_user.id)
        )
        last_upload = await session.scalar(
            select(FileUpload)
            .where(FileUpload.user_id == current_user.id)
            .order_by(FileUpload.id.desc())
            .limit(1)
        )
        unique_words = last_upload.unique_words if last_upload else 0

    return JSONResponse(content={
        "total_uploads": total_uploads,
        "unique_words": unique_words
    })

# Версия приложения
@app.get("/version")
async def version():
    return JSONResponse(content={"version": VERSION})

@app.exception_handler(404)
async def not_found_404(request: Request, exc):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)