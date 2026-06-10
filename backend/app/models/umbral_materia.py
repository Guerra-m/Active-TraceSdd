"""Modelo ORM para UmbralMateria (E8 — C-10 calificaciones-y-umbral).

Configuración del criterio de aprobación por asignación docente × materia.
Si no existe registro, el servicio usa el default (60%, RN-03).
valores_aprobatorios en JSONB (RN-02): ["Satisfactorio", "Supera lo esperado"].
"""

from sqlalchemy import Column, ForeignKey, SmallInteger, UniqueConstraint
from sqlalchemy import UUID as SAUUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import text

from app.core.database import Base
from app.models.base import TenantScopedBase

_DEFAULT_VALORES_APROBATORIOS = ["Satisfactorio", "Supera lo esperado"]
UMBRAL_DEFAULT_PCT = 60


class UmbralMateria(TenantScopedBase, Base):
    """Umbral de aprobación configurable por asignación docente × materia."""

    __tablename__ = "umbral_materia"

    asignacion_id = Column(
        SAUUID(as_uuid=True),
        ForeignKey("asignaciones.id", ondelete="CASCADE"),
        nullable=False,
    )
    materia_id = Column(
        SAUUID(as_uuid=True),
        ForeignKey("materias.id", ondelete="RESTRICT"),
        nullable=False,
    )
    umbral_pct = Column(SmallInteger, nullable=False, default=UMBRAL_DEFAULT_PCT, server_default="60")
    valores_aprobatorios = Column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text('\'["Satisfactorio","Supera lo esperado"]\'::jsonb'),
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "asignacion_id", "materia_id",
            name="uq_umbral_materia_asignacion_materia",
        ),
    )

    def __repr__(self) -> str:
        return f"<UmbralMateria asignacion={self.asignacion_id} materia={self.materia_id} umbral={self.umbral_pct}%>"
