from http import HTTPStatus
from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from services import (get_text, inverse_document_frequency, term_frequency)
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
db = []
@app.get('/', response_class=HTMLResponse)
async def get_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.post('/uploadfile', response_class=RedirectResponse)
async def handle_upload(file: UploadFile = File()):
    text = await get_text(file)
    tf = await term_frequency(text)
    idf = await inverse_document_frequency(tf)
    db.append(tf)
    db.append(idf)
    return RedirectResponse(url="/output", status_code=HTTPStatus.SEE_OTHER)


@app.get('/output', response_class=HTMLResponse)
async def get_output(request: Request):
    context = {
        "words": db[1],
        "tf": db[0]
    }
    return templates.TemplateResponse(
        request=request, name="output.html", context=context
    )