"""Modelo ORM para Factura (C-18 liquidaciones-y-honorarios).

Factura: documento de cobro para docentes facturantes.
Relaciona un docente con un período de facturación.

Estados: Pendiente → Abonada.
Soft delete via TenantScopedBase — append-only.
"""

import enum

from sqlalchemy import CheckConstraint, Column, Date, DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy import UUID as SAUUID

from app.core.database import Base
from app.models.base import TenantScopedBase


class EstadoFactura(str, enum.Enum):
    """Estados posibles de una factura."""

    PENDIENTE = "Pendiente"
    ABONADA = "Abonada"


class Factura(TenantScopedBase, Base):
    """Documento de cobro para docentes facturantes por período."""

    __tablename__ = "facturas"

    usuario_id = Column(
        SAUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    periodo = Column(String(7), nullable=False)  # AAAA-MM
    monto = Column(Numeric(12, 2), nullable=False)
    detalle = Column(String(500), nullable=False, default="")

    # Referencia opcional al archivo adjunto (URL o path)
    archivo_ref = Column(String(500), nullable=True, default=None)

    estado = Column(
        String(20),
        nullable=False,
        default=EstadoFactura.PENDIENTE.value,
        server_default="Pendiente",
    )

    # Fecha de carga (datetime) y fecha de pago (date nullable)
    fecha_carga = Column(DateTime(timezone=True), nullable=False)
    fecha_pago = Column(Date, nullable=True, default=None)

    __table_args__ = (
        CheckConstraint(
            "estado IN ('Pendiente', 'Abonada')",
            name="ck_facturas_estado",
        ),
        CheckConstraint(
            "periodo ~ '^[0-9]{4}-[0-9]{2}$'",
            name="ck_facturas_periodo_formato",
        ),
        Index("ix_facturas_tenant_periodo", "tenant_id", "periodo"),
        Index("ix_facturas_tenant_usuario", "tenant_id", "usuario_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<Factura usuario={self.usuario_id} periodo={self.periodo!r} "
            f"monto={self.monto} estado={self.estado!r}>"
        )
