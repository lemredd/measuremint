from decimal import Decimal, ROUND_UP
from typing import Annotated

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi import FastAPI, Request, Form, Query, APIRouter, Body, HTTPException

from pint import UnitRegistry
from pint.errors import DimensionalityError, UndefinedUnitError

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="html")

units = sorted([str(unit).replace("_", " ") for unit in UnitRegistry()])


@app.get("/")
async def index(request: Request) -> Response:
    return templates.TemplateResponse(request=request, name="index.html")


hx_description = """You would not usually access this API directly.
All of the documentation below are read-only.
The use of `HX-Request` header is also **required** for requests to work.
\nTo see the web app in action, visit the [homepage](/)."""
hx = FastAPI(
    title="MeasureMint HTMX API",
    summary="MeasureMint's HTMX API Documentation. For developer use only.",
    description=hx_description,
    # TODO: get latest git tag
    version="0.1.0",
    swagger_ui_parameters={
        "supportedSubmitMethods": [],
        "defaultModelsExpandDepth": -1,
    },
    docs_url=None,
    redoc_url=None,
)


@hx.get("/docs", include_in_schema=False)
async def hx_docs(request: Request) -> HTMLResponse:
    root_path = request.scope.get("root_path").rstrip("/")
    return get_swagger_ui_html(
        openapi_url=f"{root_path}{hx.openapi_url}",
        title=f"{hx.title} | Swagger UI",
        swagger_favicon_url="/static/favicon/favicon.ico",
        swagger_ui_parameters=hx.swagger_ui_parameters,
    )


@hx.middleware("http")
async def check_hx_request(request: Request, call_next):
    if request.headers.get("HX-Request"):
        return await call_next(request)

    stripped = request.url.path.strip("/hx/")
    if stripped in ["docs", "openapi.json"]:
        return await call_next(request)
    return Response("Cannot process this request", status_code=403)


@hx.get("/suggestions", response_class=HTMLResponse)
async def suggest_units(
    request: Request,
    from_unit: Annotated[str | None, Query()] = None,
    to_unit: Annotated[str | None, Query()] = None,
) -> HTMLResponse:
    """
    Returns a list of units that match the query.
    List of units come from [pint](https://pint.readthedocs.io/en/stable/).
    \nThese are used by the unit inputs in the main form.
    """
    value = from_unit or to_unit

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


@hx.post("/convert", response_class=HTMLResponse)
async def convert(
    request: Request,
    quantity: Annotated[float, Form()],
    from_unit: Annotated[str, Form()],
    to_unit: Annotated[str, Form()],
) -> HTMLResponse:
    """
    Converts `quantity` from `from_unit` to `to_unit`.
    validation of units is handled by
    [pint](https://pint.readthedocs.io/en/stable/).
    \nThis takes action when the form is submitted.
    """
    from_unit = from_unit.replace(" ", "_")
    to_unit = to_unit.replace(" ", "_")

    try:
        result = UnitRegistry().Quantity(quantity, from_unit).to(to_unit)
        result = Decimal(str(result.magnitude))
        result = result.quantize(Decimal("0.0001"), rounding=ROUND_UP)
    except UndefinedUnitError as e:
        unit = e.args[0]
        message = f"'{unit}' is not a valid unit!"
        context = {"message": message}
        if from_unit == unit:
            context["from_unit"] = unit
        if to_unit == unit:
            context["to_unit"] = unit
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context=context,
            status_code=422,
        )
    except DimensionalityError:
        message = f"Converting {from_unit} to {to_unit} is not possible!"
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"message": message},
            status_code=422,
        )
    except Exception as e:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"message": str(e)},
            status_code=500,
        )

    context = {"result": result}
    return templates.TemplateResponse(
        request=request, name="convert.html", context=context
    )


json = APIRouter(prefix="/json")


@json.post("/convert")
async def convert_json(
    request: Request,
    quantity: Annotated[float, Body()],
    from_unit: Annotated[str, Body()],
    to_unit: Annotated[str, Body()],
) -> JSONResponse:
    try:
        result = UnitRegistry().Quantity(quantity, from_unit).to(to_unit)
        result = Decimal(str(result.magnitude))
        result = result.quantize(Decimal("0.0001"), rounding=ROUND_UP)
    except Exception as e:
        raise HTTPException(
            status_code=422, detail=f"Error while converting: {str(e)}"
        ) from e
    return {"result": result}


app.mount("/hx", hx)
app.include_router(json)
