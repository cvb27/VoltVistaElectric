# CLAUDE.md — VoltVista

Archivo de memoria del agente. Léelo completo antes de escribir cualquier código.

---

## 1. Proyecto

**Nombre:** VoltVista  
**Tipo:** Sitio web de empresa de servicios eléctricos  
**Mercado:** Orlando, Florida (servicio local)  
**Stack:** Python · FastAPI · Jinja2 · Bootstrap 5 · JSON para datos  
**Idioma del sitio:** English (all user-facing content must be in English — templates, CTAs, buttons, headings, meta tags, JSON-LD text, error messages)  
**Deploy:** Servidor Linux (producción)

---

## 2. Datos del negocio (NAP)

Estos valores se usan en JSON-LD, footer, meta tags y Google Ads.  
Están centralizados en `core/config.py` — nunca hardcodearlos en templates.

```python
BUSINESS_NAME = "VoltVista"
BUSINESS_PHONE = ""          # Completar antes de deploy
BUSINESS_ADDRESS = ""        # Calle, ciudad, estado, ZIP
BUSINESS_CITY = "Orlando"
BUSINESS_STATE = "FL"
BUSINESS_ZIP = ""
BUSINESS_LAT = 0.0
BUSINESS_LNG = 0.0
BUSINESS_HOURS = "Mo-Fr 08:00-18:00"
BUSINESS_EMAIL = ""
GA4_ID = ""                  # G-XXXXXXXXXX
GADS_ID = ""                 # AW-XXXXXXXXX
```

---

## 3. Estructura de carpetas

```
voltvista/
├── main.py                  # App FastAPI, middlewares, montaje de rutas
├── core/
│   ├── config.py            # Variables globales del negocio (NAP, IDs)
│   ├── seo_blog.py
│   └── seo.py               # Generadores de JSON-LD (funciones puras)
├── routes/
│   ├── home.py
│   ├── services.py          # Landings por servicio
│   ├── seo_routes.py        # sitemap.xml, robots.txt
│   └── payments.py
├── templates/
│   ├── _footer.html 
│   ├── base.html            # Shell HTML, bloques SEO, GA4, JSON-LD
│   ├── home.html
│   ├── estimate_form.html
│   ├── blog_list.html
│   ├── blog_post.html
│   ├── payments.html
│   ├── payment_success.html
│   ├── payment.result.html
│   ├── estimate_success.html
│   └── services/
│       ├── panel_upgrade.html
│       ├── electrical_installations.html
│       └── ev_charger_installation.html
├── static/
│   ├── css/
│   ├── js/
│   │   └── site.js          # Event tracking GA4 (tel, wa, form submit)
│   └── img/
│       └── gallery/
├── data/
│   └── blog_posts.json      # Incluir "description" y "published_at"
└── posts/                   # Archivos .md del blog
```

---

## 4. Reglas de código

### 4.1 Tamaño de archivos

- **Límite:** 120 líneas por archivo (sin contar comentarios en blanco).
- Si un archivo supera ese límite, **dividirlo antes de continuar**.
- Ejemplo: si `seo.py` crece, separar en `seo_jsonld.py`, `seo_meta.py`, etc.
- Nunca acumular lógica en `main.py` — ese archivo solo monta la app.

### 4.2 Funciones

- Una función = una responsabilidad. Si hace dos cosas, dividirla.
- Máximo **20 líneas por función**. Si crece, extraer sub-funciones.
- Nombres en inglés, descriptivos y en snake_case.

```python
# BIEN
def build_local_business_schema(config: dict) -> dict:
    ...

# MAL
def seo():  # ambiguo, hace demasiado
    ...
```

### 4.3 Comentarios

- Cada archivo comienza con un docstring de 2-3 líneas que explica **qué hace y por qué existe**.
- Cada función tiene docstring con: qué recibe, qué devuelve, para qué sirve.
- Comentarios en español (el equipo es hispanohablante).
- Comentar el **por qué**, no el **qué** (el código ya dice el qué).

```python
# MAL
x = x + 1  # suma 1 a x

# BIEN
# El contador empieza en 0 pero Google requiere índice desde 1
x = x + 1
```

### 4.4 Imports

- Solo importar lo que se usa.
- Orden: stdlib → third-party → módulos locales, separados por línea en blanco.
- Sin imports con `*`.

```python
# BIEN
import json
from pathlib import Path

from fastapi import APIRouter

from core.config import BUSINESS_NAME
```

### 4.5 Configuración

- **Nunca** hardcodear strings de negocio (teléfono, dirección, ciudad) en templates o rutas.
- Todo viene de `core/config.py`.
- Los templates reciben variables via contexto Jinja, no directamente del config.

### 4.6 Templates Jinja2

- `base.html` define los bloques. Las páginas los sobreescriben. Nunca al revés.
- Bloques obligatorios en cada página:

```html
{% block title %}Título único con keyword | VoltVista{% endblock %}
{% block description %}Meta description 150-160 chars con keyword local{% endblock %}
{% block canonical %}<link rel="canonical" href="https://voltvista.com/url-de-pagina">{% endblock %}
{% block jsonld %}<!-- Schema JSON-LD específico de la página si aplica -->{% endblock %}
```

- Nada de lógica de negocio dentro de templates. Solo presentación.
- Variables de negocio globales (NAP, teléfono) se pasan desde `main.py` via `app.state` o context processor.

### 4.7 JSON-LD

- Toda la lógica de schemas vive en `core/seo.py`.
- Cada tipo de schema es una función pura que recibe datos y devuelve un dict.
- El template solo llama `{{ jsonld | tojson }}` — nunca construye el schema en HTML.

```python
# core/seo.py

def build_local_business_schema(config) -> dict:
    """
    Genera el schema JSON-LD de tipo LocalBusiness + ElectricalContractor.
    Recibe: objeto config con datos del negocio (NAP, horario, coordenadas).
    Devuelve: dict listo para serializar con json.dumps en el template.
    """
    return {
        "@context": "https://schema.org",
        "@type": ["LocalBusiness", "ElectricalContractor"],
        ...
    }
```

### 4.8 Rutas FastAPI

- Un archivo de rutas por dominio funcional (`home.py`, `services.py`, `payments.py`).
- El router no contiene lógica — delega a funciones en `core/` o `data/`.
- Cada ruta tiene un comentario de una línea explicando qué página sirve.

```python
@router.get("/servicios/panel-electrico")
# Landing SEO para el servicio de actualización de panel eléctrico
async def panel_electrico(request: Request):
    ...
```

### 4.9 JavaScript

- `site.js` es el único archivo JS custom. Solo para tracking de eventos.
- Sin jQuery. Vanilla JS únicamente.
- Cada event listener tiene un comentario indicando qué conversión trackea.

---

## 5. Prioridades SEO (en orden)

1. JSON-LD `LocalBusiness` + `ElectricalContractor` en todas las páginas
2. `<title>` y `<meta description>` únicos por página
3. `<link rel="canonical">` en cada página
4. NAP idéntico en footer, JSON-LD y Google Business Profile
5. Una landing dedicada por servicio principal
6. Schema `AggregateRating` en página de reseñas
7. Sitemap dinámico con todas las URLs y `lastmod`
8. Core Web Vitals: imágenes WebP, lazy load, Gzip, Cache-Control

---

## 6. Prioridades Google Ads

- Cada grupo de anuncios apunta a una landing dedicada (nunca al home).
- El `<title>` H1 de cada landing debe coincidir con el texto del anuncio.
- Las páginas de conversión (`estimate_success.html`, `payment_success.html`) tienen el pixel de Google Ads.
- Tracking de llamadas habilitado via `tel:` con evento GA4.

---

## 7. Bugs conocidos

_Sin bugs conocidos actualmente._

---

## 8. Lo que NO hacer

- No crear archivos de más de 120 líneas sin dividirlos.
- No hardcodear datos del negocio fuera de `core/config.py`.
- No poner lógica en templates Jinja.
- No usar jQuery ni librerías JS innecesarias.
- No tocar `main.py` para agregar rutas — usar los archivos de `routes/`.
- No aplicar cambios sin confirmar primero con el usuario si el impacto es alto.
- No generar código sin leer este archivo primero.