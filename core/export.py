"""
Exportacion de reservas a CSV para facturacion.

Se separa de routes/admin.py para que el formato del archivo se pueda probar
sin levantar el servidor: es una funcion pura que recibe filas y devuelve
texto. Usa el modulo csv de la libreria estandar, sin dependencias nuevas.
"""

import csv
import io

from core.booking import slot_label
from db.models import Booking

# Columnas del CSV, en el orden en que se veran al abrirlo en Excel o Sheets.
_HEADER = ["ref", "date", "time", "customer", "phone", "email", "address",
           "package", "total", "deposit_paid", "balance_due", "paid_at"]


def bookings_csv(rows: list[Booking]) -> str:
    """Convierte reservas en el texto de un CSV listo para descargar.

    Se usa csv.writer y no un join de comas a mano porque una direccion con
    una coma, o unas comillas en el nombre, romperian el archivo. El modulo
    estandar escapa todo eso por su cuenta.
    """
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(_HEADER)

    for b in rows:
        writer.writerow([
            b.public_id,
            b.service_date.isoformat(),      # ISO: ordenable en la hoja de calculo
            slot_label(b.slot),
            b.customer_name,
            b.customer_phone,
            b.customer_email,
            b.address,
            b.plan_name,
            b.plan_price,
            b.deposit_amount,
            b.balance_due,
            b.paid_at.isoformat() if b.paid_at else "",
        ])

    return buf.getvalue()
