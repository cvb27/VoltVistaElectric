import os
import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from sqlmodel import Session

from core.utils import get_lang
from core.i18n import t
from core.config import settings
from core.emailer import send_owner_email
from core.templating import templates
from db.session import get_session
from db.models import EstimateRequest, EstimatePhoto

router = APIRouter(prefix="/estimate", tags=["estimate"])

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}
UPLOAD_ROOT = Path("static/uploads/estimates")


def _safe_filename(name: str) -> str:
    # Evita caracteres raros en nombres
    keep = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_ ."
    cleaned = "".join(c for c in name if c in keep).strip()
    return cleaned or "upload"


def _check_upload_rules(files: List[UploadFile]) -> str | None:
    if len(files) > 5:
        return "You can upload up to 5 photos."

    for f in files:
        ext = Path(f.filename or "").suffix.lower()
        if ext not in ALLOWED_EXT:
            return "Invalid format. Use JPG, PNG or WEBP."
    return None


def _render_form(request: Request, error: str = ""):
    """Pinta el formulario. Con `error`, lo muestra arriba y responde 400.

    Existe porque este mismo bloque estaba copiado cuatro veces; la proxima
    validacion que se anada solo tendra que llamar aqui.
    """
    lang = get_lang(request)
    return templates.TemplateResponse(
        "estimate_form.html",
        {
            "request": request,
            "lang": lang,
            "t": lambda k: t(lang, k),
            "app_name": settings.app_name,
            "error": error,
        },
        status_code=400 if error else 200,
    )


def _success(request: Request, estimate_id=None):
    """Pagina de gracias. Sin estimate_id no muestra numero de referencia."""
    lang = get_lang(request)
    return templates.TemplateResponse(
        "estimate_success.html",
        {
            "request": request,
            "lang": lang,
            "t": lambda k: t(lang, k),
            "app_name": settings.app_name,
            "estimate_id": estimate_id,
        },
    )


def _notify_owner(est: EstimateRequest, photo_count: int) -> None:
    """Avisa al dueno de un estimado nuevo.

    Mismo formato que el aviso de reservas (core/notify.py) para que los dos
    correos se lean igual. El asunto lleva el nombre porque en el movil es lo
    unico que se ve sin abrir el mensaje.
    """
    body = (
        f"NEW ESTIMATE  #{est.id}\n"
        f"{'=' * 44}\n\n"
        f"WHO       {est.name}  -  {est.phone}\n"
        f"EMAIL     {est.email or '-'}\n"
        f"WHERE     {est.address or '-'}  -  ZIP {est.zip_code or '-'}\n\n"
        f"JOB       {est.job_type}\n"
        f"URGENCY   {est.urgency}\n"
        f"PREFERS   {est.contact_preference}\n"
        f"PHOTOS    {photo_count}\n\n"
        f"DETAILS\n{est.description}\n"
    )
    send_owner_email(subject=f"NEW ESTIMATE #{est.id} - {est.name}", body=body)


@router.get("", response_class=HTMLResponse)
def estimate_form(request: Request):
    return _render_form(request)


@router.post("", response_class=HTMLResponse)
async def submit_estimate(
    request: Request,
    session: Session = Depends(get_session),

    name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(""),

    address: str = Form(""),
    zip_code: str = Form(""),

    job_type: str = Form(...),
    description: str = Form(...),

    urgency: str = Form("normal"),
    contact_preference: str = Form("text"),

    # Honeypot: campo oculto por CSS que un humano nunca ve ni rellena. Los
    # bots rellenan todo lo que encuentran en el HTML, asi que si llega con
    # algo dentro, es spam.
    website: str = Form(""),

    photos: List[UploadFile] = File(default=[]),
):
    # Spam: se descarta en silencio y se le muestra la pagina de gracias.
    # Devolver un error le diria al bot que fue detectado y volveria a
    # intentarlo cambiando cosas; asi cree que funciono y no insiste.
    if website.strip():
        return _success(request)

    # Validación mínima
    name = name.strip()
    phone = phone.strip()
    job_type = job_type.strip()
    description = description.strip()

    if not name or not phone or not job_type or not description:
        return _render_form(request, "Please fill in the required fields.")

    err = _check_upload_rules(photos)
    if err:
        return _render_form(request, err)

    # Guardar solicitud
    est = EstimateRequest(
        name=name,
        phone=phone,
        email=email.strip() or None,
        address=address.strip() or None,
        zip_code=zip_code.strip() or None,
        job_type=job_type,
        description=description,
        urgency=urgency,
        contact_preference=contact_preference,
    )
    session.add(est)
    session.commit()
    session.refresh(est)

    # Guardar fotos
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    saved_paths = []

    for f in photos:
        if not f.filename:
            continue
        ext = Path(f.filename).suffix.lower()
        unique = f"{est.id}_{uuid.uuid4().hex}{ext}"
        disk_path = UPLOAD_ROOT / unique

        # Guardado streaming (no cargar todo en memoria)
        with open(disk_path, "wb") as out:
            while True:
                chunk = await f.read(1024 * 1024)
                if not chunk:
                    break
                # Límite simple por tamaño total (aprox): MAX_UPLOAD_MB
                if out.tell() > settings.max_upload_mb * 1024 * 1024:
                    # Si excede, borramos y no guardamos
                    out.close()
                    try:
                        os.remove(disk_path)
                    except Exception:
                        pass
                    return _render_form(
                        request,
                        f"One of the photos is larger than {settings.max_upload_mb}MB.",
                    )
                out.write(chunk)

        rel_path = f"/static/uploads/estimates/{unique}"
        session.add(EstimatePhoto(estimate_id=est.id, file_path=rel_path, original_name=_safe_filename(f.filename)))
        saved_paths.append(rel_path)

    session.commit()

    # Aviso al dueño (no rompe si no hay SMTP configurado)
    _notify_owner(est, len(saved_paths))

    return _success(request, est.id)
