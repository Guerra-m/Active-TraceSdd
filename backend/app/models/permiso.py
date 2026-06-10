"""Modelo ORM para la entidad Permiso.

Un Permiso es una capacidad atómica expresada como 'modulo:accion'.
Ejemplos: 'calificaciones:importar', 'comunicacion:enviar'.

Los permisos son globales (sin tenant_id) — no pertenecen a un tenant.
Cada tenant tiene su propio catálogo de asignaciones (rol_permiso),
pero los permisos en sí son compartidos.

Hereda Base directamente (Decisión D6 del design).
"""

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy import UUID as SAUUID, Boolean, Column, DateTime, Index, String

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Permiso(Base):
    """Permiso atómico del dominio en formato 'modulo:accion'."""

    __tablename__ = "permisos"

    id = Column(
        SAUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # Código único del permiso — formato obligatorio: 'modulo:accion'
    code = Column(
        String(200),
        nullable=False,
        unique=True,
    )

    # Descripción legible del permiso
    description = Column(
        String(500),
        nullable=False,
        default="",
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default=sa.text("true"),
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )

    __table_args__ = (
        Index("ix_permisos_code", "code", unique=True),
    )

    def __repr__(self) -> str:
        return f"<Permiso code={self.code!r} active={self.is_active}>"
