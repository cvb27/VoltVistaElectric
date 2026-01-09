"""
Envía correo al dueño (opcional).
Si no hay SMTP configurado, NO falla: solo devuelve False.

Esto es ideal para MVP: primero guardamos en DB, luego activas email.
"""

import smtplib
from email.message import EmailMessage
from core.config import settings


def can_send_email() -> bool:
    return all([settings.smtp_host, settings.smtp_user, settings.smtp_pass, settings.email_to_owner])


def send_owner_email(subject: str, body: str) -> bool:
    if not can_send_email():
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_user
    msg["To"] = settings.email_to_owner
    msg.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_pass)
            server.send_message(msg)
        return True
    except Exception:
        # Para producción: loggear excepción. Para MVP: no explotar la app.
        return False
