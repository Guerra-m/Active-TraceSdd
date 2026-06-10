"""Modelo ORM para la entidad Carrera (E1 — catálogo por tenant).

Carrera es el catálogo de carreras de una institución. Cada carrera tiene
un código único por tenant. El estado (Activa/Inactiva) controla si pueden
crearse nuevas cohortes: una carrera Inactiva no admite cohortes nuevas.

Las cohortes existentes no se ven afectadas al inactivar la carrera.
Soft delete via TenantScopedBase — nunca hard delete.
"""

from sqlalchemy import CheckConstraint, Column, Index, String, UniqueConstraint

from app.core.database import Base
from app.models.base import TenantScopedBase


class Carrera(TenantScopedBase, Base):
    """Catálogo de carreras de un tenant."""

    __tablename__ = "carreras"

    codigo = Column(String(50), nullable=False)
    nombre = Column(String(200), nullable=False)
    estado = Column(String(20), nullable=False, default="Activa", server_default="Activa")

    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo", name="uq_carreras_tenant_codigo"),
        CheckConstraint("estado IN ('Activa', 'Inactiva')", name="ck_carreras_estado"),
        Index("ix_carreras_tenant", "tenant_id"),
    )

    def __repr__(self) -> str:
        return f"<Carrera codigo={self.codigo!r} estado={self.estado!r} tenant={self.tenant_id}>"
