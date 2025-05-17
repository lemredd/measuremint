from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

app.mount("/", StaticFiles(directory="static", html=True), name="static")

templates = Jinja2Templates(directory="html")


@app.get("/suggestions")
async def index(request):
    return templates.TemplateResponse(request=request, name="suggestions.html")
