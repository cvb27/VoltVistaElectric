import os
import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from core.utils import get_lang
from core.i18n import t
from core.config import settings
from core.emailer import send_owner_email
from db.session import get_session
from db.models import EstimateRequest, EstimatePhoto

router = APIRouter(prefix="/estimate", tags=["estimate"])
templates = Jinja2Templates(directory="templates")

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}
UPLOAD_ROOT = Path("static/uploads/estimates")


def _safe_filename(name: str) -> str:
    # Evita caracteres raros en nombres
    keep = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_ ."
    cleaned = "".join(c for c in name if c in keep).strip()
    return cleaned or "upload"


def _check_upload_rules(files: List[UploadFile]) -> str | None:
    if len(files) > 5:
        return "Puedes subir hasta 5 fotos."

    for f in files:
        ext = Path(f.filename or "").suffix.lower()
        if ext not in ALLOWED_EXT:
            return "Formato inválido. Usa JPG, PNG o WEBP."
    return None


@router.get("", response_class=HTMLResponse)
def estimate_form(request: Request):
    lang = get_lang(request)
    return templates.TemplateResponse(
        "estimate_form.html",
        {
            "request": request,
            "lang": lang,
            "t": lambda k: t(lang, k),
            "app_name": settings.app_name,
        },
    )


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

    photos: List[UploadFile] = File(default=[]),
):
    lang = get_lang(request)

    # Validación mínima
    name = name.strip()
    phone = phone.strip()
    job_type = job_type.strip()
    description = description.strip()

    if not name or not phone or not job_type or not description:
        return templates.TemplateResponse(
            "estimate_form.html",
            {
                "request": request,
                "lang": lang,
                "t": lambda k: t(lang, k),
                "app_name": settings.app_name,
                "error": "Por favor completa los campos requeridos.",
            },
            status_code=400,
        )

    # Regla uploads
    err = _check_upload_rules(photos)
    if err:
        return templates.TemplateResponse(
            "estimate_form.html",
            {
                "request": request,
                "lang": lang,
                "t": lambda k: t(lang, k),
                "app_name": settings.app_name,
                "error": err,
            },
            status_code=400,
        )

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
                    return templates.TemplateResponse(
                        "estimate_form.html",
                        {
                            "request": request,
                            "lang": lang,
                            "t": lambda k: t(lang, k),
                            "app_name": settings.app_name,
                            "error": f"Una imagen excede el límite de {settings.max_upload_mb}MB.",
                        },
                        status_code=400,
                    )
                out.write(chunk)

        rel_path = f"/static/uploads/estimates/{unique}"
        session.add(EstimatePhoto(estimate_id=est.id, file_path=rel_path, original_name=_safe_filename(f.filename)))
        saved_paths.append(rel_path)

    session.commit()

    # Email opcional al dueño (no rompe si no está configurado)
    body = (
        f"NUEVO ESTIMADO - {settings.app_name}\n\n"
        f"Nombre: {name}\nTeléfono: {phone}\nEmail: {email or '-'}\n"
        f"Tipo: {job_type}\nUrgencia: {urgency}\nPreferencia: {contact_preference}\n\n"
        f"Descripción:\n{description}\n\n"
        f"Fotos: {len(saved_paths)}\n"
    )
    send_owner_email(subject=f"Nuevo estimado #{est.id}", body=body)

    return templates.TemplateResponse(
        "estimate_success.html",
        {
            "request": request,
            "lang": lang,
            "t": lambda k: t(lang, k),
            "app_name": settings.app_name,
            "estimate_id": est.id,
        },
    )
