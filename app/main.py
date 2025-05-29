from http import HTTPStatus
from fastapi import FastAPI, File, Request, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from services import get_text, inverse_document_frequency, term_frequency
from database import async_session
from models import FileUpload, WordStat
from sqlalchemy import insert,select, func

VERSION = "0.0.1"  # Версия

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get('/', response_class=HTMLResponse)
async def get_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.post('/uploadfile', response_class=RedirectResponse)
async def handle_upload(file: UploadFile = File()):
    text = await get_text(file)
    tf = await term_frequency(text)
    idf = await inverse_document_frequency(tf)

    # Сохраняем в базу
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(insert(FileUpload).values(unique_words=len(tf)))
            file_id = result.inserted_primary_key[0]
            session.add_all([
                WordStat(file_id=file_id, word=word, tf=tf[word], idf=idf_val)
                for word, idf_val in idf
            ])
    return RedirectResponse(url="/output", status_code=HTTPStatus.SEE_OTHER)

@app.get('/output', response_class=HTMLResponse)
async def get_output(request: Request):
    async with async_session() as session:
        result = await session.execute(select(WordStat).order_by(WordStat.id.desc()).limit(50))
        words = result.all()
        tf = {w.word: w.tf for w in words}

    context = {"words": words, "tf": tf}
    return templates.TemplateResponse(request=request, name="output.html", context=context)

#/status
@app.get('/status')
async def status():
    return JSONResponse(content={"status": "OK"})

#/metrics
@app.get('/metrics')
async def metrics():
    # total_uploads — сколько было успешных загрузок файлов, можно мониторить нагрузку
    # last_upload — сколько уникальных слов в последней обработанной загрузке, чтобы оценить объем текста
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

#/version
@app.get('/version')
async def version():
    return JSONResponse(content={"version": VERSION})