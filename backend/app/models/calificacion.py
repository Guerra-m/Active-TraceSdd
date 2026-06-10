"""Modelo ORM para Calificacion (E7 — C-10 calificaciones-y-umbral).

Registra la nota de un alumno en una actividad evaluable de una materia.
El campo `aprobado` se calcula al importar usando el UmbralMateria vigente.
`entrada_padron_id` es nullable: permite importar sin padrón activo (D2).
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy import UUID as SAUUID
from sqlalchemy.sql import text

from app.core.database import Base
from app.models.base import TenantScopedBase


class Calificacion(TenantScopedBase, Base):
    """Nota de un alumno en una actividad evaluable, con scope de asignación docente."""

    __tablename__ = "calificaciones"

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
    # nullable: alumno puede no estar en el padrón activo (D2)
    entrada_padron_id = Column(
        SAUUID(as_uuid=True),
        ForeignKey("entrada_padron.id", ondelete="SET NULL"),
        nullable=True,
    )
    actividad = Column(String(500), nullable=False)
    nota_numerica = Column(Numeric(6, 2), nullable=True)
    nota_textual = Column(String(200), nullable=True)
    aprobado = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    origen = Column(String(20), nullable=False, default="Importado", server_default="Importado")
    importado_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_calificaciones_tenant_asignacion_materia", "tenant_id", "asignacion_id", "materia_id"),
        Index("ix_calificaciones_tenant_materia", "tenant_id", "materia_id"),
        Index("ix_calificaciones_tenant_entrada_padron", "tenant_id", "entrada_padron_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<Calificacion actividad={self.actividad!r} "
            f"aprobado={self.aprobado} asignacion={self.asignacion_id}>"
        )
