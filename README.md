# VoltVista Electric

Sitio web de VoltVista Electric — servicios eléctricos residenciales en Orlando, FL.
FastAPI + Jinja2 + Bootstrap 5, con reservas de instalación y pagos por Stripe.

Las reglas de código y la estructura del proyecto están en **[CLAUDE.md](CLAUDE.md)**.
Léelo antes de tocar nada.

## Arrancar en local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edita .env con tus datos y llaves

uvicorn main:app --reload
```

Sin `DATABASE_URL` en el `.env`, la app usa un SQLite local (`voltvista.db`) y
crea las tablas sola al arrancar. No hace falta instalar Postgres para desarrollar.

## Rutas principales

| Ruta | Qué es |
|---|---|
| `/` | Home |
| `/services/lighting-installation` | Hub de iluminación: una tarjeta por servicio |
| `/services/{slug}` | Página de cada servicio (roofline, landscape, relamping…) |
| `/booking?plan=recommended` | Elegir fecha y pagar el depósito |
| `/estimate` | Formulario de estimado gratuito |
| `/payments` | Cobros manuales por Stripe |
| `/blog` | Blog (índice en `data/blog_posts.json`, cuerpos en `posts/*.md`) |
| `/admin/bookings` | Agenda del negocio — HTTP Basic con `ADMIN_PASSWORD` |

## Cambios sin tocar código

| Qué | Dónde |
|---|---|
| Precios y textos de los 3 planes | `data/surge_offers.json` |
| Feriados y días sin servicio | `data/blocked_dates.json` |
| Publicar un post | `data/blog_posts.json` + un `.md` en `posts/` |
| Servicios de iluminación (nav, hub, páginas, sitemap, schema) | `data/lighting_services.json` — ver abajo |
| Depósito de reserva | `BOOKING_DEPOSIT` en `.env` |
| Horario, cupos por franja, anticipación mínima | constantes al inicio de `core/booking.py` |

### Agregar un servicio de iluminación

1. Sube la foto principal (y las de galería, si hay) a `static/img/lighting/`,
   en WebP de ~1200 px de ancho. Una foto de 2 MB hunde el LCP de la página.
2. Añade una entrada a `services` en `data/lighting_services.json` copiando una
   existente. Campos obligatorios: `slug`, `nav_label`, `h1`, `subtitle`,
   `card_blurb`, `meta_title`, `meta_description` (150-160 caracteres),
   `hero_image`, `hero_alt`, `cta_text`, `cta_href`, `order`, `published`.
   Opcionales: `sections`, `bullets`, `gallery`, `faq` (vacías no se pintan) y
   `price_note`.
3. Mientras falte contenido, deja `"published": false` y marca lo pendiente con
   `[PLACEHOLDER]`. Un borrador no sale en ningún sitio y su URL da 404.
4. Para publicarlo, pon `"published": true`. Si queda algún `[PLACEHOLDER]` o
   falta una foto, **la app no arranca** y el error dice qué entrada y qué campo.
5. Despliega. La página `/services/{slug}`, el menú, la tarjeta del hub, el
   sitemap y el schema salen solos.

## Despliegue

Railway detrás de Cloudflare. El arranque debe llevar `--proxy-headers`, y el
servicio corre con **una sola réplica**: el apartado de cupos de las reservas
asume escrituras serializadas.

Variables obligatorias en producción: `BASE_URL`, `DATABASE_URL`,
`STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET_BOOKING`, `ADMIN_PASSWORD`.
La lista completa está en `.env.example`.

> Añadir un campo a un modelo **no** basta: `init_db()` sólo crea tablas que
> faltan, no columnas. Sobre una tabla que ya existe hace falta un `ALTER TABLE`.
