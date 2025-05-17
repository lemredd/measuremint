from decimal import Decimal, ROUND_UP
from typing import Annotated

from fastapi import FastAPI, Request, Response, Form
from fastapi.templating import Jinja2Templates

from pint import UnitRegistry

app = FastAPI()

templates = Jinja2Templates(directory="html")


@app.get("/")
async def index(request: Request) -> Response:
    return templates.TemplateResponse(request=request, name="index.html")


hx = FastAPI()
units = sorted([str(unit).replace("_", " ") for unit in UnitRegistry()])


@hx.middleware("http")
async def check_hx_request(request: Request, call_next):
    if request.headers.get("HX-Request"):
        return await call_next(request)
    return Response("Cannot process this request", status_code=403)


@hx.get("/suggestions")
async def suggest_units(request: Request) -> Response:
    value = request.query_params.get("from_unit") or request.query_params.get("to_unit")

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


@hx.post("/convert")
async def convert(
    request: Request,
    quantity: Annotated[float, Form()],
    from_unit: Annotated[str, Form()],
    to_unit: Annotated[str, Form()],
) -> Response:
    from_unit = from_unit.replace(" ", "_")
    to_unit = to_unit.replace(" ", "_")

    try:
        result = UnitRegistry().Quantity(quantity, from_unit).to(to_unit)
        result = Decimal(str(result.magnitude))
        result = result.quantize(Decimal("0.0001"), rounding=ROUND_UP)
    except Exception as e:
        # TODO: return 400 bad request template
        result = f"Error: {e}"

    context = {"result": result}
    return templates.TemplateResponse(
        request=request, name="convert.html", context=context
    )


app.mount("/hx", hx)
