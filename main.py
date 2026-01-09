from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from core.config import settings
from db.session import init_db
from routes.home import router as home_router
from routes.estimates import router as estimates_router
from routes.payments import router as payments_router
from routes.blog import router as blog_router
from routes.seo_routes import router as seo_router
from routes.static_pages import router as pages_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    # DB init (MVP)
    init_db()

    # Static
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Routes
    app.include_router(home_router)
    app.include_router(estimates_router)
    app.include_router(payments_router)
    app.include_router(blog_router)
    app.include_router(seo_router)
    app.include_router(pages_router)

    return app


app = create_app()
