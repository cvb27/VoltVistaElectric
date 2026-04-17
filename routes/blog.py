import json
from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
import markdown as md

from core.utils import get_lang
from core.i18n import t
from core.config import settings
from core.templating import templates
from core.seo_blog import build_article_schema

router = APIRouter(prefix="/blog", tags=["blog"])

POSTS_INDEX = Path("data/blog_posts.json")
POSTS_DIR = Path("posts")


def _load_posts():
    if not POSTS_INDEX.exists():
        return []
    return json.loads(POSTS_INDEX.read_text(encoding="utf-8"))


@router.get("", response_class=HTMLResponse)
def blog_list(request: Request):
    lang = get_lang(request)
    posts = _load_posts()
    return templates.TemplateResponse(
        "blog_list.html",
        {"request": request, "lang": lang, "t": lambda k: t(lang, k), "app_name": settings.app_name, "posts": posts},
    )


@router.get("/{slug}", response_class=HTMLResponse)
def blog_post(request: Request, slug: str):
    lang = get_lang(request)
    posts = _load_posts()
    post = next((p for p in posts if p.get("slug") == slug), None)
    if not post:
        not_found = {"title": "Post Not Found", "excerpt": "The post you are looking for does not exist.", "slug": slug}
        return templates.TemplateResponse(
            "blog_post.html",
            {"request": request, "lang": lang, "t": lambda k: t(lang, k), "app_name": settings.app_name,
             "post": not_found, "html": "<p>Post not found.</p>"},
            status_code=404,
        )

    md_file = POSTS_DIR / post["file"]
    html = md.markdown(md_file.read_text(encoding="utf-8")) if md_file.exists() else "<p>Contenido no disponible.</p>"

    return templates.TemplateResponse(
        "blog_post.html",
        {"request": request, "lang": lang, "t": lambda k: t(lang, k), "app_name": settings.app_name,
         "post": post, "html": html, "article_jsonld": build_article_schema(settings, post)},
    )
