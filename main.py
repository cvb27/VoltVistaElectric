from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.gzip import GZipMiddleware

from core.config import settings
from db.session import init_db
from routes.home import router as home_router
from routes.estimates import router as estimates_router
from routes.payments import router as payments_router
from routes.blog import router as blog_router
from routes.seo_routes import router as seo_router
from routes.services import router as services_router


def _register_middlewares(app: FastAPI) -> None:
    """Configura middlewares de la app (Gzip + Cache-Control en /static)."""
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    @app.middleware("http")
    async def add_cache_headers(request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/static"):
            response.headers["Cache-Control"] = "public, max-age=31536000"
        return response


def _register_routers(app: FastAPI) -> None:
    """Registra todos los routers del proyecto."""
    app.include_router(home_router)
    app.include_router(estimates_router)
    app.include_router(payments_router)
    app.include_router(blog_router)
    app.include_router(seo_router)
    app.include_router(services_router)


def create_app() -> FastAPI:
    """Construye la app FastAPI con DB init, middlewares, static y routers."""
    app = FastAPI(title=settings.app_name)
    init_db()
    _register_middlewares(app)
    app.mount("/static", StaticFiles(directory="static"), name="static")
    _register_routers(app)
    return app


app = create_app()
