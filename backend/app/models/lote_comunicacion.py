"""Modelo ORM para LoteComunicacion — C-12 comunicaciones-cola-worker.

Agrupa un envío masivo (N mensajes) bajo una única cabecera con estado de aprobación.
El estado del lote controla cuándo el worker puede despachar sus mensajes.
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy import UUID as SAUUID

from app.core.database import Base
from app.models.base import TenantScopedBase

# Estados posibles del lote
LOTE_PENDIENTE = "Pendiente"
LOTE_PENDIENTE_APROBACION = "PendienteAprobacion"
LOTE_APROBADO = "Aprobado"
LOTE_DESPACHANDO = "Despachando"
LOTE_COMPLETADO = "Completado"
LOTE_CANCELADO = "Cancelado"


class LoteComunicacion(TenantScopedBase, Base):
    """Cabecera de un lote de mensajes salientes (F3.2, RN-17)."""

    __tablename__ = "lotes_comunicacion"

    enviado_por = Column(
        SAUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    materia_id = Column(
        SAUUID(as_uuid=True),
        ForeignKey("materias.id", ondelete="RESTRICT"),
        nullable=True,
    )
    asunto_template = Column(Text, nullable=False)
    cuerpo_template = Column(Text, nullable=False)
    estado = Column(String(30), nullable=False, default=LOTE_PENDIENTE, server_default=LOTE_PENDIENTE)
    requiere_aprobacion = Column(Boolean, nullable=False, default=False, server_default="false")
    aprobado_por = Column(
        SAUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    aprobado_at = Column(DateTime(timezone=True), nullable=True)
    total_mensajes = Column(Integer, nullable=False, default=0, server_default="0")
    enviados = Column(Integer, nullable=False, default=0, server_default="0")
    errores = Column(Integer, nullable=False, default=0, server_default="0")

    __table_args__ = (
        Index("ix_lotes_comunicacion_tenant", "tenant_id"),
        Index("ix_lotes_comunicacion_tenant_estado", "tenant_id", "estado"),
    )

    def __repr__(self) -> str:
        return f"<LoteComunicacion id={self.id} estado={self.estado} total={self.total_mensajes}>"
