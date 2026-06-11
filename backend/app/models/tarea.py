"""Modelos ORM para Tarea y ComentarioTarea (C-16).

E12 — Tarea interna de coordinación/docente.
"""

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy import UUID as SAUUID

from app.core.database import Base
from app.models.base import TenantScopedBase

_ESTADOS = ("Pendiente", "En progreso", "Resuelta", "Cancelada")
_ESTADO_CHECK = f"estado IN ({', '.join(repr(e) for e in _ESTADOS)})"


class Tarea(TenantScopedBase, Base):
    __tablename__ = "tareas"

    materia_id = Column(SAUUID(as_uuid=True), ForeignKey("materias.id", ondelete="SET NULL"), nullable=True)
    asignado_a = Column(SAUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    asignado_por = Column(SAUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    estado = Column(String(20), nullable=False, default="Pendiente", server_default="Pendiente")
    descripcion = Column(Text, nullable=False)
    contexto_id = Column(SAUUID(as_uuid=True), nullable=True)

    __table_args__ = (
        CheckConstraint(_ESTADO_CHECK, name="ck_tareas_estado"),
        Index("ix_tareas_tenant", "tenant_id"),
        Index("ix_tareas_tenant_asignado_a", "tenant_id", "asignado_a"),
        Index("ix_tareas_tenant_estado", "tenant_id", "estado"),
    )


class ComentarioTarea(TenantScopedBase, Base):
    __tablename__ = "comentarios_tarea"

    tarea_id = Column(SAUUID(as_uuid=True), ForeignKey("tareas.id", ondelete="CASCADE"), nullable=False)
    autor_id = Column(SAUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    texto = Column(Text, nullable=False)

    __table_args__ = (
        Index("ix_comentarios_tarea_tenant", "tenant_id"),
        Index("ix_comentarios_tarea_tenant_tarea", "tenant_id", "tarea_id"),
    )
