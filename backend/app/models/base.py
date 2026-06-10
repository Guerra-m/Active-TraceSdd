"""Mixin base para todos los modelos de dominio.

TenantScopedBase es un mixin Python puro (sin __tablename__ ni mapper propio)
que aporta las columnas fundacionales a cada modelo de dominio:

  - id         : UUID v4, PK, generado en Python al instanciar
  - tenant_id  : UUID, FK → tenants.id, NOT NULL, indexado
  - created_at : timestamp UTC, auto-seteado en insert
  - updated_at : timestamp UTC, auto-actualizado en cada modificacion
  - deleted_at : timestamp UTC nullable — marca de soft delete (NULL = activo)

Decision D1 del design: mixin puro para evitar conflictos con herencia ORM
y Alembic autogenerate. Los modelos concretos combinan:
    class MiModelo(TenantScopedBase, Base):
        __tablename__ = "mi_tabla"
        ...

No existe metodo hard_delete: el sistema es append-only por diseno (regla dura #13).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import UUID, Column, DateTime, ForeignKey, Index
from sqlalchemy.orm import declared_attr


def _utcnow() -> datetime:
    """Devuelve el momento actual en UTC (aware)."""
    return datetime.now(timezone.utc)


class TenantScopedBase:
    """Mixin que agrega id UUID, tenant_id, timestamps y soft-delete a modelos ORM.

    Combinar con Base declarativa de SQLAlchemy:
        class MiModelo(TenantScopedBase, Base):
            __tablename__ = "mi_tabla"
    """

    # PK: UUID v4 generado en Python al instanciar (Decision D2)
    @declared_attr
    def id(cls):  # noqa: N805
        return Column(
            UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
            nullable=False,
        )

    # FK obligatoria al tenant propietario del registro
    @declared_attr
    def tenant_id(cls):  # noqa: N805
        return Column(
            UUID(as_uuid=True),
            ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        )

    # Timestamp de creacion — seteado una sola vez en el insert
    @declared_attr
    def created_at(cls):  # noqa: N805
        return Column(
            DateTime(timezone=True),
            nullable=False,
            default=_utcnow,
        )

    # Timestamp de ultima modificacion — actualizado en cada flush/commit
    @declared_attr
    def updated_at(cls):  # noqa: N805
        return Column(
            DateTime(timezone=True),
            nullable=False,
            default=_utcnow,
            onupdate=_utcnow,
        )

    # Marca de soft delete — NULL significa registro activo
    @declared_attr
    def deleted_at(cls):  # noqa: N805
        return Column(
            DateTime(timezone=True),
            nullable=True,
            default=None,
        )
