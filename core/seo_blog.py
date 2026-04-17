"""Schema JSON-LD para blog posts — separado de core/seo.py por cap de 120 líneas."""


def build_article_schema(cfg, post: dict) -> dict:
    """Construye JSON-LD BlogPosting para un post del blog.
    Recibe cfg (business_name/business_url/logo_url) y post (title, excerpt, published_at, slug).
    Devuelve dict listo para json.dumps en blog_post.html."""
    org = {"@type": "Organization", "name": cfg.business_name}
    return {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": post.get("title", ""),
        "description": post.get("excerpt", ""),
        "datePublished": post.get("published_at", ""),
        "url": f"{cfg.business_url}/blog/{post.get('slug', '')}",
        "author": org,
        "publisher": {**org, "logo": cfg.logo_url},
    }
