"""Modelo ORM para Comunicacion — C-12 comunicaciones-cola-worker.

Mensaje individual dentro de un lote. El destinatario está cifrado (PII AES-256-GCM).
El asunto y cuerpo se almacenan ya renderizados (variables interpoladas al crear el lote).
"""

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy import UUID as SAUUID

from app.core.database import Base
from app.models.base import TenantScopedBase

# Estados del mensaje (RN-15)
MSG_PENDIENTE = "Pendiente"
MSG_ENVIANDO = "Enviando"
MSG_ENVIADO = "Enviado"
MSG_ERROR = "Error"
MSG_CANCELADO = "Cancelado"


class Comunicacion(TenantScopedBase, Base):
    """Mensaje saliente con máquina de estados (RN-15)."""

    __tablename__ = "comunicaciones"

    lote_id = Column(
        SAUUID(as_uuid=True),
        ForeignKey("lotes_comunicacion.id", ondelete="CASCADE"),
        nullable=False,
    )
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
    entrada_padron_id = Column(
        SAUUID(as_uuid=True),
        ForeignKey("entrada_padron.id", ondelete="SET NULL"),
        nullable=True,
    )
    # PII cifrada AES-256-GCM — nunca texto plano en DB
    destinatario = Column(Text, nullable=False)
    asunto = Column(String(500), nullable=False)
    cuerpo = Column(Text, nullable=False)
    estado = Column(String(20), nullable=False, default=MSG_PENDIENTE, server_default=MSG_PENDIENTE)
    enviado_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_comunicaciones_tenant_lote", "tenant_id", "lote_id"),
        Index("ix_comunicaciones_tenant_estado", "tenant_id", "estado"),
        Index("ix_comunicaciones_tenant_entrada_padron", "tenant_id", "entrada_padron_id"),
    )

    def __repr__(self) -> str:
        return f"<Comunicacion id={self.id} estado={self.estado} lote={self.lote_id}>"
