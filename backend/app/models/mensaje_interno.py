"""Modelos ORM para mensajería interna entre usuarios (C-20).

HiloMensaje: hilo de conversación entre dos usuarios del mismo tenant.
MensajeInterno: cada mensaje dentro del hilo.

Regla dura #9: tenant_id en cada tabla; repositories filtran por tenant por defecto.
Regla dura #13: soft delete siempre (deleted_at en TenantScopedBase).
"""

from sqlalchemy import Column, Index, String, Text
from sqlalchemy import UUID as SAUUID

from app.core.database import Base
from app.models.base import TenantScopedBase


class HiloMensaje(TenantScopedBase, Base):
    __tablename__ = "hilos_mensaje"

    asunto = Column(String(200), nullable=False)
    remitente_id = Column(SAUUID(as_uuid=True), nullable=False)
    destinatario_id = Column(SAUUID(as_uuid=True), nullable=False)

    __table_args__ = (
        Index("ix_hilos_tenant_dest", "tenant_id", "destinatario_id"),
        Index("ix_hilos_tenant_rem", "tenant_id", "remitente_id"),
    )


class MensajeInterno(TenantScopedBase, Base):
    __tablename__ = "mensajes_internos"

    hilo_id = Column(SAUUID(as_uuid=True), nullable=False)
    autor_id = Column(SAUUID(as_uuid=True), nullable=False)
    cuerpo = Column(Text, nullable=False)

    __table_args__ = (
        Index("ix_mensajes_hilo", "tenant_id", "hilo_id"),
    )
