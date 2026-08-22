"""
Puerta de entrada de /admin: HTTP Basic contra una sola contrasena en .env.

Vive aparte del router porque autenticar y mostrar la agenda son dos cosas
distintas — y porque cualquier pagina interna futura reutilizara esto sin
arrastrar el resto de routes/admin.py.
"""

import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from core.config import settings

_basic = HTTPBasic()


def require_admin(creds: HTTPBasicCredentials = Depends(_basic)) -> str:
    """Deja pasar solo con la contrasena correcta. El navegador la pide solo.

    El usuario da igual, solo se comprueba la contrasena. Se usa
    compare_digest en vez de "==" porque "==" tarda un poco mas cuando los
    primeros caracteres aciertan, y ese tiempo basta para ir adivinando la
    clave letra a letra. compare_digest siempre tarda lo mismo.

    Si ADMIN_PASSWORD esta vacia, no entra nadie: un despliegue al que se le
    olvide la variable no deja la agenda abierta.
    """
    ok = settings.admin_password and secrets.compare_digest(
        creds.password, settings.admin_password
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Basic"},
        )
    return creds.username
