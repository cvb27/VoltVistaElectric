"""
Modelos SQLite con SQLModel (simple y rápido).

- EstimateRequest: solicitudes de estimado
- EstimatePhoto: fotos asociadas
- PaymentRecord: pagos confirmados (Stripe webhook + PayPal capture)
"""

from datetime import datetime, date as date_type
from typing import Optional
from sqlmodel import SQLModel, Field


class EstimateRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    name: str
    phone: str
    email: Optional[str] = None

    address: Optional[str] = None
    zip_code: Optional[str] = None

    job_type: str
    description: str

    urgency: str  # low|normal|high|emergency
    contact_preference: str  # call|text|whatsapp

    # Para seguimiento básico
    status: str = "new"  # new|reviewed|quoted|closed


class EstimatePhoto(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    estimate_id: int = Field(index=True)
    file_path: str  # ruta relativa dentro de /static (ej: /static/uploads/...)
    original_name: str


class PaymentRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    provider: str  # stripe|paypal
    purpose: str   # deposit|invoice

    amount: float
    currency: str

    # IDs del proveedor para auditoría
    provider_payment_id: str = Field(index=True)
    email: Optional[str] = None
    notes: Optional[str] = None

class Booking(SQLModel, table=True):
    """Reserva de instalacion de surge protector con deposito pagado."""

    id: Optional[int] = Field(default=None, primary_key=True)

    # Id publico corto y aleatorio. Va en la URL de confirmacion.
    # No se usa el id numerico ahi porque seria enumerable: cualquiera
    # podria pasear por /booking/1, /booking/2 y ver reservas ajenas.
    # Tambien es el transaction_id que se manda a GA4 para que no cuente
    # dos veces si el cliente recarga la pagina de confirmacion.
    public_id: str = Field(index=True, unique=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Plan elegido. El precio se congela aqui a proposito: si manana
    # cambian los precios en surge_offers.json, esta reserva conserva
    # lo que se le prometio al cliente.
    plan_key: str                      # basic|recommended|premium
    plan_name: str                     # Essential|Complete|Total Home
    plan_price: int                    # 299|399|599 — es el value del evento GA4
    deposit_amount: int                # lo que se cobra ahora (50)
    balance_due: int                   # plan_price - deposit_amount

    # La cita
    service_date: date_type = Field(index=True)
    slot: int                          # 1..5, ver SLOTS en core/booking.py

    # Cliente. Sin email a proposito: Stripe lo pide el mismo para el
    # recibo y llega en el objeto de la sesion si hace falta.
    customer_name: str
    customer_phone: str
    address: str
    notes: Optional[str] = None

    # Estado
    status: str = "pending"            # pending|paid|cancelled
    stripe_session_id: Optional[str] = Field(default=None, index=True)
    paid_at: Optional[datetime] = None