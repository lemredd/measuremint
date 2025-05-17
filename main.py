from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

from pint import UnitRegistry

app = FastAPI()

templates = Jinja2Templates(directory="html")


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


units = sorted([str(unit).replace("_", " ") for unit in UnitRegistry()])


@app.get("/suggestions")
async def suggest_units(request: Request):
    value = request.query_params.get("from") or request.query_params.get("to")

    if value:
        filtered = [*filter(lambda u: value in u, units)][:10]
    else:
        filtered = units[:10]

    if not len(filtered):
        filtered = ["No units found"]

    context = {"units": filtered}
    return templates.TemplateResponse(
        request=request, name="suggestions.html", context=context
    )
