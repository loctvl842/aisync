import re
from contextlib import asynccontextmanager
from pathlib import Path

import toml
import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from aisync_api.env import env
from aisync_api.exceptions import APIException
from aisync_api.routes import router
from aisync_api.routes.types import Error


def make_middleware() -> list[Middleware]:
    return [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        ),
    ]


_cached_project_name = None
_cached_authors = None


def init_docs(app: FastAPI):
    @app.get("/docs", include_in_schema=False)
    async def swagger_ui_html(req: Request) -> HTMLResponse:
        root_path = req.scope.get("root_path", "").rstrip("/")
        openapi_url = root_path + app.openapi_url
        oauth2_redirect_url = app.swagger_ui_oauth2_redirect_url
        if oauth2_redirect_url:
            oauth2_redirect_url = root_path + oauth2_redirect_url
        return get_swagger_ui_html(
            openapi_url=openapi_url,
            title=app.title + " - Swagger UI",
            oauth2_redirect_url=oauth2_redirect_url,
            init_oauth=app.swagger_ui_init_oauth,
            swagger_favicon_url=f"{app.root_path}/static/favicon.svg",
            swagger_ui_parameters=app.swagger_ui_parameters,
        )

    @app.get("/redoc", include_in_schema=False)
    async def redoc_html(req: Request) -> HTMLResponse:
        root_path = req.scope.get("root_path", "").rstrip("/")
        openapi_url = root_path + app.openapi_url
        return get_redoc_html(
            openapi_url=openapi_url,
            title=app.title + " - ReDoc",
            redoc_favicon_url=f"{app.root_path}/static/favicon.svg",
        )

    TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
    templates = Jinja2Templates(directory=TEMPLATES_DIR)

    @app.get("/")
    def root(request: Request):
        global _cached_project_name, _cached_authors

        if _cached_project_name is None or _cached_authors is None:
            pyproject_path = Path("pyproject.toml")
            if pyproject_path.is_file():
                with open(pyproject_path, "r") as f:
                    toml_content = f.read()
                toml_data = toml.loads(toml_content)

                _cached_project_name = re.sub(
                    r"[-_]",
                    " ",
                    toml_data.get("tool", {})
                    .get("poetry", {})
                    .get("name", "FastAPI Project"),
                ).title()
                _cached_authors = (
                    toml_data.get("tool", {}).get("poetry", {}).get("authors", [])
                )
            else:
                _cached_project_name = "FastAPI Project"
                _cached_authors = []
        context = {
            "project_name": _cached_project_name,
            "authors": _cached_authors,
            "root_path": app.root_path,
        }
        response = templates.TemplateResponse(
            "index.html", {"request": request, **context}
        )
        response.headers["Cache-Control"] = "public, max-age=3600"
        return response


def init_listeners(app_: FastAPI) -> None:
    @app_.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        return JSONResponse(
            status_code=422,
            content=Error(
                error_code=422, message="Request validation failed", detail=exc.errors()
            ).model_dump(exclude_none=True),
        )

    @app_.exception_handler(ResponseValidationError)
    async def response_validation_exception_handler(
        request: Request, exc: ResponseValidationError
    ):
        return JSONResponse(
            status_code=422,
            content=Error(
                error_code=422,
                message="Response validation failed",
                detail=exc.errors(),
            ).model_dump(exclude_none=True),
        )

    @app_.exception_handler(APIException)
    async def custom_exception_handler(request: Request, exc: APIException):
        return JSONResponse(
            status_code=exc.code,
            content=Error(
                error_code=exc.error_code, message=exc.message, detail=exc.detail
            ).model_dump(exclude_none=True),
            headers=exc.headers,
        )

    @app_.exception_handler(Exception)
    async def exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=Error(error_code=500, message="Internal Server Error").model_dump(
                exclude_none=True
            ),
        )


def init_routers(app: FastAPI) -> None:
    app.include_router(router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


server = FastAPI(
    title="AISync API",
    description="AISync API",
    version="0.0.1",
    root_path="/api",
    docs_url=None,
    redoc_url=None,
    middleware=make_middleware(),
    lifespan=lifespan,
)
STATIC_DIR = Path(__file__).resolve().parents[1] / "static"
server.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
init_docs(server)
init_listeners(server)
init_routers(server)


if __name__ == "__main__":
    uvicorn.run(
        "aisync_api.main:server",
        host=env.API_HOST,
        port=env.API_PORT,
        reload=env.API_DEBUG,
    )
