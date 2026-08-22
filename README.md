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
| `/services/surge-protector-installation` | Landing de la campaña de Google Ads |
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
| Depósito de reserva | `BOOKING_DEPOSIT` en `.env` |
| Horario, cupos por franja, anticipación mínima | constantes al inicio de `core/booking.py` |

## Despliegue

Railway detrás de Cloudflare. El arranque debe llevar `--proxy-headers`, y el
servicio corre con **una sola réplica**: el apartado de cupos de las reservas
asume escrituras serializadas.

Variables obligatorias en producción: `BASE_URL`, `DATABASE_URL`,
`STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET_BOOKING`, `ADMIN_PASSWORD`.
La lista completa está en `.env.example`.

> Añadir un campo a un modelo **no** basta: `init_db()` sólo crea tablas que
> faltan, no columnas. Sobre una tabla que ya existe hace falta un `ALTER TABLE`.
