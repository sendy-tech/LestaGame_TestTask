import logging
import os
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from http import HTTPStatus
from urllib.parse import unquote

from fastapi import FastAPI, Request, UploadFile, File, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session, engine, Base, get_db
from app.auth.dependencies import get_current_user, get_current_user_optional
from app.models.user import User
from app.models.document import FileUpload, WordStat
from app.routes.html_routes import router as html_router
from app.routes.api_routes import router as api_router
from app.services import get_text, term_frequency, inverse_document_frequency
from app.crud.document_crud import get_user_files
from app.crud.collection_crud import add_file_to_default_collection

VERSION = "0.0.2"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ База данных инициализирована.")
    except Exception as e:
        logger.exception(f"❌ Ошибка инициализации БД: {e}")
    yield


app = FastAPI(
    lifespan=lifespan,
    max_multipart_memory_size=1024 * 1024 * 100,
    title="Document Processing API",
    description="API для загрузки документов, управления коллекциями и анализа текста.",
    version=VERSION,
    docs_url="/docs",
    openapi_url="/openapi.json"
)

app.include_router(html_router, prefix="/auth")
app.include_router(api_router, prefix="/api")

BASE_DIR = os.path.dirname(__file__)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


def localtime(value):
    if isinstance(value, datetime):
        return (value + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')
    return value


templates.env.filters["localtime"] = localtime

@app.get(
    "/",
    response_class=HTMLResponse,
    summary="Главная страница",
    description="Главная страница с возможностью загрузки файла, доступна только авторизованным пользователям",
    tags=["Сервис"]
)
async def get_root(request: Request, current_user: User | None = Depends(get_current_user_optional)):
    if current_user is None:
        return RedirectResponse("/auth/login", status_code=HTTPStatus.SEE_OTHER)

    msg = unquote(request.cookies.get("msg")) if request.cookies.get("msg") else None
    response = templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request, "current_user": current_user, "msg": msg}
    )
    response.delete_cookie("msg")
    return response


@app.post("/uploadfile", response_class=RedirectResponse, summary="Добавление данных в базу", tags=["Статистика"])
async def handle_upload(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user:
        return RedirectResponse("/auth/login", status_code=HTTPStatus.SEE_OTHER)

    try:
        text = await get_text(file)
        tf = term_frequency(text)  # TF для всех слов

        # Сохраняем файл
        file_upload = FileUpload(
            user_id=current_user.id,
            filename=file.filename,
            content=text,
            unique_words=len(tf)
        )
        db.add(file_upload)
        await db.flush()  # Получим file_upload.id

        # Считаем IDF для всех слов, которые есть в этом файле
        words_all = list(tf.keys())
        idf_map = await inverse_document_frequency(db, current_user, words_all)

        # Выбираем 50 самых "редких" слов (по IDF — убывание редкости)
        sorted_words = sorted(words_all, key=lambda word: (idf_map.get(word, 0.0), tf[word]))
        selected_words = sorted_words[:50]

        # Создаём объекты WordStat
        word_stat = [
            WordStat(
                file_id=file_upload.id,
                user_id=current_user.id,
                word=word,
                tf=tf[word],
                idf=idf_map.get(word, 0.0)
            )
            for word in selected_words
        ]
        db.add_all(word_stat)

        # Добавляем файл в дефолтную коллекцию
        await add_file_to_default_collection(db, file_upload, current_user)

        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка при загрузке файла: {e}")
        return RedirectResponse("/?msg=Upload+failed", status_code=HTTPStatus.SEE_OTHER)

    return RedirectResponse(url="/output", status_code=HTTPStatus.SEE_OTHER)

@app.get(
    "/output",
    response_class=HTMLResponse,
    summary="Таблица с результатами",
    description="Вывод набора из 50 наиболее редко встречающихся в документе слов их частота (TF) и обратная частота документа (IDF)",
    tags=["Статистика"]
)
async def get_output(request: Request, current_user: User = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/auth/login", status_code=HTTPStatus.SEE_OTHER)

    async with async_session() as session:
        result = await session.execute(
            WordStat.__table__.select()
            .join(FileUpload, WordStat.file_id == FileUpload.id)
            .where(FileUpload.user_id == current_user.id)
            .order_by(WordStat.id.desc())
            .limit(50)
        )
        word_stat = result.fetchall()

    tf = {row.word: row.tf for row in word_stat}

    words = [(row.word, row.idf) for row in word_stat]


    return templates.TemplateResponse(
        request=request,
        name="output.html",
        context={"words": words, "tf": tf, "current_user": current_user}
    )

@app.get(
    "/myfiles",
    summary="Файлы пользователя",
    description="Отображение всех файлов, загруженных пользователем (id, filename, дата и время загрузки)",
    tags=["Сервис"]
)
async def list_user_files(request: Request, current_user: User = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse("/auth/login", status_code=HTTPStatus.SEE_OTHER)

    async with async_session() as session:
        files = await get_user_files(session, current_user.id)

    return templates.TemplateResponse(
        request=request,
        name="myfiles.html",
        context={"request": request, "files": files, "current_user": current_user}
    )


@app.get(
    "/version",
    summary="Версия приложения",
    description="Отображение версии приложения в JSON формате",
    tags=["Сервис"]
)
async def version():
    return JSONResponse(content={"version": VERSION})


@app.get(
    "/status",
    summary="Статус приложения",
    description="Отображение работоспособности приложения в JSON формате",
    tags=["Сервис"]
)
async def status():
    return JSONResponse(content={"status": "OK"})


@app.exception_handler(404)
async def not_found_404(request: Request, exc):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
