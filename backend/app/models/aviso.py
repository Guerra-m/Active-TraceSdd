"""Modelos ORM para Aviso y AcknowledgmentAviso (C-15).

E13 — Aviso: notificación institucional segmentada por rol/cohorte/materia.
"""

from datetime import datetime
from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy import UUID as SAUUID

from app.core.database import Base
from app.models.base import TenantScopedBase

_ALCANCES = ("Global", "PorMateria", "PorCohorte", "PorRol")
_ALCANCE_CHECK = f"alcance IN ({', '.join(repr(a) for a in _ALCANCES)})"

_SEVERIDADES = ("Info", "Advertencia", "Crítico")
_SEVERIDAD_CHECK = f"severidad IN ({', '.join(repr(s) for s in _SEVERIDADES)})"


class Aviso(TenantScopedBase, Base):
    __tablename__ = "avisos"

    alcance = Column(String(20), nullable=False, default="Global", server_default="Global")
    materia_id = Column(SAUUID(as_uuid=True), ForeignKey("materias.id", ondelete="SET NULL"), nullable=True)
    cohorte_id = Column(SAUUID(as_uuid=True), ForeignKey("cohortes.id", ondelete="SET NULL"), nullable=True)
    rol_destino = Column(String(30), nullable=True)
    severidad = Column(String(15), nullable=False, default="Info", server_default="Info")
    titulo = Column(String(300), nullable=False)
    cuerpo = Column(Text, nullable=False)
    inicio_en = Column(DateTime(timezone=True), nullable=False)
    fin_en = Column(DateTime(timezone=True), nullable=True)
    orden = Column(Integer, nullable=False, default=0, server_default="0")
    activo = Column(Boolean, nullable=False, default=True, server_default="true")
    requiere_ack = Column(Boolean, nullable=False, default=False, server_default="false")

    __table_args__ = (
        CheckConstraint(_ALCANCE_CHECK, name="ck_avisos_alcance"),
        CheckConstraint(_SEVERIDAD_CHECK, name="ck_avisos_severidad"),
        Index("ix_avisos_tenant", "tenant_id"),
        Index("ix_avisos_tenant_activo", "tenant_id", "activo"),
    )


class AcknowledgmentAviso(TenantScopedBase, Base):
    __tablename__ = "acknowledgments_aviso"

    aviso_id = Column(SAUUID(as_uuid=True), ForeignKey("avisos.id", ondelete="CASCADE"), nullable=False)
    usuario_id = Column(SAUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    confirmado_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_acks_aviso_tenant", "tenant_id"),
        Index("ix_acks_aviso_tenant_aviso", "tenant_id", "aviso_id"),
        Index("ix_acks_aviso_tenant_usuario", "tenant_id", "usuario_id"),
    )
