"""Modelo ORM para Liquidacion (C-18 liquidaciones-y-honorarios).

Liquidacion: resumen de honorarios de un docente en un período (cohorte × AAAA-MM).

Estados:
  - Abierta: editable, se puede recalcular
  - Cerrada: inmutable, genera audit LIQUIDACION_CERRAR (RN-22)

RN-35: docentes facturantes → excluido_por_factura=True, montos en 0.
RN-36: NEXO presentado separado en reportes → es_nexo=True.
RN-37: unidad de liquidación = (cohorte, mes).

Soft delete via TenantScopedBase — append-only.
"""

import enum

from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Index, Numeric, String, text
from sqlalchemy import UUID as SAUUID
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base
from app.models.base import TenantScopedBase


class EstadoLiquidacion(str, enum.Enum):
    """Estados posibles de una liquidación."""

    ABIERTA = "Abierta"
    CERRADA = "Cerrada"


class Liquidacion(TenantScopedBase, Base):
    """Resumen de honorarios docente por período/cohorte (RN-37)."""

    __tablename__ = "liquidaciones"

    cohorte_id = Column(
        SAUUID(as_uuid=True),
        ForeignKey("cohortes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    periodo = Column(String(7), nullable=False)  # AAAA-MM
    usuario_id = Column(
        SAUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    rol = Column(String(20), nullable=False)

    # Lista de claves de grupo_plus de las comisiones consideradas
    comisiones = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))

    monto_base = Column(Numeric(12, 2), nullable=False, default=0)
    monto_plus = Column(Numeric(12, 2), nullable=False, default=0)
    total = Column(Numeric(12, 2), nullable=False, default=0)

    es_nexo = Column(Boolean, nullable=False, default=False, server_default="false")
    excluido_por_factura = Column(Boolean, nullable=False, default=False, server_default="false")

    estado = Column(
        String(20),
        nullable=False,
        default=EstadoLiquidacion.ABIERTA.value,
        server_default="Abierta",
    )

    __table_args__ = (
        CheckConstraint(
            "estado IN ('Abierta', 'Cerrada')",
            name="ck_liquidaciones_estado",
        ),
        CheckConstraint(
            "periodo ~ '^[0-9]{4}-[0-9]{2}$'",
            name="ck_liquidaciones_periodo_formato",
        ),
        Index("ix_liquidaciones_tenant_periodo", "tenant_id", "periodo"),
        Index("ix_liquidaciones_tenant_usuario", "tenant_id", "usuario_id"),
        Index("ix_liquidaciones_tenant_cohorte", "tenant_id", "cohorte_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<Liquidacion usuario={self.usuario_id} rol={self.rol!r} "
            f"periodo={self.periodo!r} estado={self.estado!r} total={self.total}>"
        )
