"""Application composition. Explicit configurations never read .env."""

from contextlib import asynccontextmanager
from hashlib import sha256
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import scheduler
from .config import AppConfig
from .errors import DomainError
from .routes import router
from .runtime import Runtime
from .security import MAX_REQUEST_BODY_BYTES, RequestBodyLimitMiddleware, security

STATIC = Path(__file__).parent / "static"


def create_app(config: AppConfig | None = None):
    @asynccontextmanager
    async def lifespan(app):
        resolved = config if config is not None else AppConfig.from_environment()
        rt = Runtime(resolved)
        app.state.runtime = rt
        rt.database.init()
        tasks = scheduler.start(rt) if resolved.background_enabled else []
        try:
            yield
        finally:
            await scheduler.stop(tasks)

    app = FastAPI(title="Samen · gezinsdashboard", lifespan=lifespan, docs_url=None, redoc_url=None)
    app.add_middleware(RequestBodyLimitMiddleware, max_body_size=MAX_REQUEST_BODY_BYTES)
    app.middleware("http")(security)

    @app.exception_handler(DomainError)
    async def domain_error(request, error):
        from http import HTTPStatus

        detail = error.detail if error.detail is not None else HTTPStatus(error.status_code).phrase
        return JSONResponse(
            {"detail": detail}, status_code=error.status_code, headers=error.headers
        )

    app.include_router(router)
    # Relative imports keep the entire module graph under the same cache key.
    frontend = sha256()
    for asset in sorted(STATIC.rglob("*")):
        if asset.suffix in {".html", ".css", ".js"} and asset.is_file():
            frontend.update(asset.relative_to(STATIC).as_posix().encode())
            frontend.update(asset.read_bytes())
    frontend_path = f"/frontend/{frontend.hexdigest()[:16]}"
    app.mount(frontend_path, StaticFiles(directory=STATIC), name="frontend")
    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    index_html = (
        (STATIC / "index.html")
        .read_text(encoding="utf-8")
        .replace('"/static/app.js"', f'"{frontend_path}/app.js"')
        .replace('"/static/style.css"', f'"{frontend_path}/style.css"')
    )

    @app.get("/")
    def index():
        return HTMLResponse(index_html, headers={"Cache-Control": "no-cache"})

    return app
