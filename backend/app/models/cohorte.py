"""Modelo ORM para la entidad Cohorte (E2 — temporal, por carrera y tenant).

Cohorte representa una instancia temporal de una carrera (ej. "2024-A").
Su nombre es único por (tenant_id, carrera_id, nombre). Tiene vigencia
temporal: vig_desde/vig_hasta. No tiene campo estado — la carrera padre
es quien porta Activa/Inactiva.

Soft delete via TenantScopedBase — nunca hard delete.
"""

import uuid

from sqlalchemy import Column, Date, ForeignKey, SmallInteger, String, UniqueConstraint
from sqlalchemy import UUID as SAUUID

from app.core.database import Base
from app.models.base import TenantScopedBase


class Cohorte(TenantScopedBase, Base):
    """Cohorte temporal asociada a una carrera del tenant."""

    __tablename__ = "cohortes"

    carrera_id = Column(
        SAUUID(as_uuid=True),
        ForeignKey("carreras.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    nombre = Column(String(100), nullable=False)
    anio = Column(SmallInteger, nullable=False)
    vig_desde = Column(Date, nullable=False)
    vig_hasta = Column(Date, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "carrera_id", "nombre", name="uq_cohortes_tenant_carrera_nombre"
        ),
    )

    def __repr__(self) -> str:
        return f"<Cohorte nombre={self.nombre!r} anio={self.anio} carrera={self.carrera_id}>"
