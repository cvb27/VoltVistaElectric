# CLAUDE.md — VoltVista

Archivo de memoria del agente. Léelo completo antes de escribir cualquier código.

---

## 1. Proyecto

**Nombre:** VoltVista  
**Tipo:** Sitio web de empresa de servicios eléctricos  
**Mercado:** Orlando, Florida (servicio local)  
**Stack:** Python 3.13 · FastAPI · Jinja2 · Bootstrap 5 (CDN) · SQLModel  
**Datos:** Postgres en producción vía `DATABASE_URL`; SQLite en local si no está definida.
Los contenidos editables (planes, precios, feriados, índice del blog) van en JSON bajo `data/`.  
**Pagos:** Stripe Checkout — depósito de reserva y cobros manuales.  
**Idioma del sitio:** English (all user-facing content must be in English — templates, CTAs, buttons, headings, meta tags, JSON-LD text, error messages).
Los comentarios y docstrings del código van en español (§4.3).  
**Deploy:** Railway detrás de Cloudflare. Una sola réplica: SQLite/Postgres y el
apartado de cupos asumen escrituras serializadas.

---

## 2. Datos del negocio (NAP)

Estos valores se usan en JSON-LD, footer, meta tags y Google Ads.

**No están escritos en el código.** Viven en `.env` y los lee `core/config.py`,
que expone un único objeto `settings`. Nunca hardcodearlos en templates ni rutas.

```bash
# .env — la lista completa está en .env.example
BUSINESS_NAME=VoltVista
BUSINESS_PHONE=+1XXXXXXXXXX
BUSINESS_ADDRESS=
BUSINESS_CITY=Orlando
BUSINESS_STATE=FL
BUSINESS_ZIP=
BUSINESS_LAT=
BUSINESS_LNG=
BUSINESS_HOURS=Mo-Fr 08:00-18:00
BUSINESS_EMAIL=

GA4_ID=                   # G-XXXXXXXXXX — el Measurement ID, NO el Stream ID
GADS_ID=                  # AW-XXXXXXXXX — el conversion ID, NO el customer ID
GADS_CONVERSION_LABEL=    # la parte tras la barra en AW-XXXXXXXXX/LABEL

BOOKING_DEPOSIT=50        # depósito de la reserva, en dólares enteros
ADMIN_PASSWORD=           # vacío = /admin cerrado
DATABASE_URL=             # en Railway lo inyecta Postgres; vacío = SQLite local
```

Los tres IDs de tracking son fáciles de confundir con otros números de los
mismos paneles. Si el valor no tiene el formato del comentario, está mal.

**Cómo se usa:**

```python
from core.config import settings
settings.phone, settings.ga4_id, settings.booking_deposit
```

En plantillas `settings` es un global de Jinja (ver `core/templating.py`), así
que se usa directamente: `{{ settings.phone }}`.

---

## 3. Estructura de carpetas

```
voltvista/
├── main.py                  # Monta la app: middlewares, static y routers. Nada más.
├── core/                    # Lógica y piezas compartidas. No conoce HTTP.
│   ├── config.py            # settings: TODAS las variables de .env
│   ├── templating.py        # instancia única de Jinja2 (inyecta `settings`)
│   ├── booking.py           # disponibilidad: franjas, cupos, validación de fecha
│   ├── offers.py            # planes y precios (lee data/surge_offers.json)
│   ├── posts.py             # índice del blog (lee data/blog_posts.json)
│   ├── checkout.py          # sesiones de Stripe + configura stripe.api_key
│   ├── emailer.py           # envío SMTP en crudo
│   ├── notify.py            # aviso al dueño de una reserva pagada
│   ├── export.py            # CSV de reservas para facturación
│   ├── admin_auth.py        # HTTP Basic de /admin
│   ├── seo.py               # JSON-LD: LocalBusiness, Service, Breadcrumb
│   ├── seo_blog.py          # JSON-LD de posts (separado por el cap de 120)
│   ├── i18n.py, utils.py    # idioma y helpers varios
├── db/
│   ├── models.py            # SQLModel: EstimateRequest, EstimatePhoto,
│   │                        #           PaymentRecord, Booking
│   ├── session.py           # engine (Postgres o SQLite) + init_db + get_session
│   └── booking.py           # consultas de reservas: taken_map, mark_paid…
├── routes/                  # Un router por dominio. Capa fina: delega en core/
│   ├── home.py  services.py  blog.py  estimates.py
│   ├── booking.py           # /booking: fecha, checkout, confirmación, webhook
│   ├── payments.py          # /payments: cobros manuales
│   ├── admin.py             # /admin/bookings: agenda, cancelar, CSV
│   └── seo_routes.py        # sitemap.xml y robots.txt
├── templates/
│   ├── base.html            # shell + bloques SEO + gtag
│   ├── booking/             # select_date.html, confirmed.html
│   ├── services/            # una landing por servicio
│   └── admin/               # bookings.html (NO extiende base.html, ver abajo)
├── static/                  # css/, js/site.js, img/, video/
├── data/                    # JSON editables sin tocar código
│   ├── surge_offers.json    # los 3 planes y sus precios
│   ├── blocked_dates.json   # feriados y días sin servicio
│   └── blog_posts.json      # índice del blog
└── posts/                   # cuerpo de los posts en .md
```

### Dónde va cada cosa

- **`routes/`** contiene routers que se montan en `main.py`, y nada más. Es una
  capa fina: recibe la petición, llama a `core/` o a `db/`, devuelve la respuesta.
- **`core/`** es todo lo demás: reglas de negocio, formatos, integraciones. No
  importa nada de `routes/`.
- Cuando un archivo de `routes/` pasa de 120 líneas, lo que sobra casi siempre
  es lógica que pertenecía a `core/`. Así salió `core/admin_auth.py` de
  `routes/admin.py`.
- Si dos módulos leen el mismo archivo de `data/`, ese lector va en `core/`
  (ejemplo: `core/posts.py`, que usan `/blog` y `/sitemap.xml`).
- **`templates/admin/` no extiende `base.html`** a propósito: esa plantilla carga
  gtag, y cada visita del equipo contaría como tráfico en GA4.

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

- **Nunca** hardcodear strings de negocio (teléfono, dirección, ciudad, precios)
  en templates o rutas. Todo viene de `.env` a través de `core/config.py`.
- Un valor que cambie sin desplegar código va a `.env`, no a una constante. El
  depósito de reserva estuvo en `$2` publicado porque un valor de prueba entró
  en un commit; ahora es `BOOKING_DEPOSIT`.
- `settings` está registrado como **global de Jinja** en `core/templating.py`, así
  que las plantillas lo usan directo (`{{ settings.phone }}`) sin pasarlo en cada
  `TemplateResponse`. Los datos propios de cada página sí van por contexto.

### 4.6 Templates Jinja2

- `base.html` define los bloques. Las páginas los sobreescriben. Nunca al revés.
- Bloques obligatorios en cada página:

```html
{% block title %}Título único con keyword | VoltVista{% endblock %}
{% block description %}Meta description 150-160 chars con keyword local{% endblock %}
{% block canonical %}<link rel="canonical" href="https://voltvistaelectric.com/url-de-pagina">{% endblock %}
{% block jsonld %}<!-- Schema JSON-LD específico de la página si aplica -->{% endblock %}
```

- Una página que **no debe salir en Google** (checkout, confirmaciones)
  sobreescribe dos bloques: `robots` con el meta `noindex, nofollow`, y
  `canonical` **vacío**. El canonical por defecto apunta a la home, y decirle a
  Google que una página de checkout "es" la home es peor que no decirle nada.
  Ejemplo en `templates/booking/confirmed.html`.

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

## 7. Deuda técnica conocida

Actualizado 2026-08-22. Nada de esto rompe el sitio hoy, pero está pendiente.

**Archivos que superan el límite de 120 líneas (§4.1)**
- `routes/booking.py` (195) — se partiría sacando `/confirmed` y el webhook.
- `routes/estimates.py` (204) y `routes/services.py` (135).

**Fragilidad**
- `datetime.utcnow()` está deprecado en Python 3.12+ y se usa en 4 archivos.
- No hay tests automatizados: cada cambio se verifica a mano.

**Pendiente de decidir**
- `core/i18n.py` lo importan 5 rutas para pasar `t` al contexto, pero ninguna
  plantilla llama a `t()`. El sitio es monolingüe: sobra, pero quitarlo toca
  6 archivos.
- `/estimate` no tiene el campo `urgency` en el formulario, aunque la ruta lo
  acepta con default `"normal"` y el correo al dueño lo imprime siempre así.

---

## 8. Lo que NO hacer

- No crear archivos de más de 120 líneas sin dividirlos.
- No hardcodear datos del negocio, precios ni credenciales fuera de `.env`.
- No poner lógica de negocio en templates Jinja.
- No usar jQuery ni librerías JS innecesarias. El sitio funciona sin JS propio
  salvo el tracking y el calendario de reservas.
- No tocar `main.py` para agregar rutas — usar los archivos de `routes/`.
- No aceptar del cliente ningún dato que decida cuánto se cobra. El formulario
  manda la *key* del plan; el precio lo resuelve el servidor con `get_plan()`.
- No borrar filas de `booking`: una reserva cancelada se marca `cancelled`,
  porque el depósito ya se cobró y tiene que quedar constancia.
- No añadir columnas a un modelo dando por hecho que `create_all()` las creará:
  sólo crea **tablas** que faltan. Sobre una tabla existente hace falta un
  `ALTER TABLE` a mano, tenga filas o no.
- No aplicar cambios sin confirmar primero con el usuario si el impacto es alto.
- No generar código sin leer este archivo primero.