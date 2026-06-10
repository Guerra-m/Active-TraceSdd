"""Modelo ORM para el log de auditoría (E-AUD).

AuditLog es append-only: ningún registro puede modificarse ni eliminarse.
La inmutabilidad se garantiza a dos niveles:
  - Aplicación: AuditLogRepository no expone update() ni delete().
  - Base de datos: trigger BEFORE UPDATE OR DELETE que rechaza toda modificación.

No hereda TenantScopedBase porque ese mixin añade soft-delete (deleted_at),
que no tiene sentido en un log inmutable. Lleva tenant_id como FK explícita.

materia_id es nullable y referencia a la tabla 'materias' que se crea en C-06.
La FK a materias se añade en esa migración para evitar dependencia circular.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import UUID as SAUUID, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AuditLog(Base):
    """Registro de auditoría inmutable de toda acción significativa del sistema."""

    __tablename__ = "audit_log"

    id = Column(
        SAUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    tenant_id = Column(
        SAUUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
    )

    fecha_hora = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )

    # Quién realizó la acción (actor real, incluso bajo impersonación)
    actor_id = Column(
        SAUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Usuario que estaba siendo impersonado (NULL si no hay impersonación activa)
    impersonado_id = Column(
        SAUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )

    # Materia relacionada con la acción (nullable; FK añadida en C-06)
    materia_id = Column(
        SAUUID(as_uuid=True),
        nullable=True,
    )

    # Código de acción estandarizado (e.g. "CALIFICACIONES_IMPORTAR")
    accion = Column(
        String(200),
        nullable=False,
    )

    # Contexto adicional de la acción (JSONB para queries flexibles)
    detalle = Column(
        JSONB,
        nullable=True,
    )

    filas_afectadas = Column(
        Integer,
        nullable=True,
    )

    ip = Column(
        String(45),  # IPv6 max = 39 chars; 45 para CIDR notation
        nullable=True,
    )

    user_agent = Column(
        Text,
        nullable=True,
    )

    __table_args__ = (
        Index("ix_audit_log_tenant_fecha", "tenant_id", "fecha_hora"),
        Index("ix_audit_log_tenant_actor", "tenant_id", "actor_id"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog accion={self.accion!r} actor={self.actor_id} tenant={self.tenant_id}>"
