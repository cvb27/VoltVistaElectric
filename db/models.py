"""
Modelos SQLite con SQLModel (simple y rápido).

- EstimateRequest: solicitudes de estimado
- EstimatePhoto: fotos asociadas
- PaymentRecord: pagos confirmados (Stripe webhook + PayPal capture)
"""

from datetime import datetime
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
