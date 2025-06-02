import logging
from http import HTTPStatus
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

from sqlalchemy import insert, select, func

from services import get_text, term_frequency, inverse_document_frequency
from database import async_session, engine, Base
from models import FileUpload, WordStat

VERSION = "0.0.1"
logger = logging.getLogger(__name__)

app = FastAPI(
    lifespan=lambda app: lifespan(app),
    max_multipart_memory_size=1024 * 1024 * 100  # 100 MB лимит на загрузку файлов
)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


# Инициализация базы данных
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ База данных инициализирована.")
    except Exception as e:
        logger.exception(f"❌ Ошибка инициализации БД: {e}")
    yield

# Главная страница с формой загрузки.
@app.get("/", response_class=HTMLResponse)
async def get_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

# Обработка загруженного файла: вычисление TF/IDF, сохранение в БД.
@app.post("/uploadfile", response_class=RedirectResponse)
async def handle_upload(file: UploadFile = File()):
    # Получаем текст из файла
    text = await get_text(file)

    # Вычисляем TF и IDF
    tf = await term_frequency(text)
    idf = await inverse_document_frequency(tf)

    # Сохраняем метрики в базу
    async with async_session() as session:
        async with session.begin():
            # Сохраняем информацию о файле
            result = await session.execute(
                insert(FileUpload).values(unique_words=len(tf))
            )
            file_id = result.inserted_primary_key[0]

            # Сохраняем статистику слов
            session.add_all([
                WordStat(file_id=file_id, word=word, tf=tf[word], idf=idf_val)
                for word, idf_val in idf
            ])

    return RedirectResponse(url="/output", status_code=HTTPStatus.SEE_OTHER)

# Страница с отображением TF/IDF-метрик для последнего загруженного файла.
@app.get("/output", response_class=HTMLResponse)
async def get_output(request: Request):
    async with async_session() as session:
        result = await session.execute(
            select(WordStat).order_by(WordStat.id.desc()).limit(50)
        )
        word_stats = result.scalars().all()

    # Формируем данные для шаблона
    tf = {ws.word: ws.tf for ws in word_stats}
    words = [(ws.word, ws.idf) for ws in word_stats]

    context = {"words": words, "tf": tf}
    return templates.TemplateResponse(request=request, name="output.html", context=context)

# Проверка состояния приложения.
@app.get("/status")
async def status():
    return JSONResponse(content={"status": "OK"})

# Метрики: количество загрузок и уникальных слов в последнем файле.
@app.get("/metrics")
async def metrics():
    async with async_session() as session:
        total_uploads = await session.scalar(select(func.count()).select_from(FileUpload))
        last_upload = await session.scalar(
            select(FileUpload).order_by(FileUpload.id.desc()).limit(1)
        )
        unique_words = last_upload.unique_words if last_upload else 0

    return JSONResponse(content={
        "total_uploads": total_uploads,
        "unique_words": unique_words
    })

# Версия приложения.
@app.get("/version")
async def version():
    return JSONResponse(content={"version": VERSION})
