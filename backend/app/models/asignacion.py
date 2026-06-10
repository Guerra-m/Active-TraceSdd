"""Modelo ORM para la entidad Asignacion (C-07 usuarios-y-asignaciones).

Asignacion vincula un usuario con un rol en un contexto académico (materia, carrera,
cohorte) y una vigencia temporal (desde/hasta). El campo estado_vigencia es derivado
en runtime via @property — no se persiste en DB.

Regla de diseño (ADR en design.md):
  - comisiones: JSONB array (evita tabla pivot, suficiente para el MVP)
  - estado_vigencia: derivado en Python, no en DB (evita triggers/vistas)
  - responsable_id: FK nullable → users (jerarquía docente)
"""

import datetime

from sqlalchemy import CheckConstraint, Column, Date, ForeignKey, Index, String, text
from sqlalchemy import UUID as SAUUID
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base
from app.models.base import TenantScopedBase

_ROLES_VALIDOS = (
    "ALUMNO", "TUTOR", "PROFESOR", "COORDINADOR", "NEXO", "ADMIN", "FINANZAS"
)
_ROL_CHECK = f"rol IN ({', '.join(repr(r) for r in _ROLES_VALIDOS)})"


class Asignacion(TenantScopedBase, Base):
    """Asignación de usuario a rol en contexto académico con vigencia."""

    __tablename__ = "asignaciones"

    usuario_id = Column(
        SAUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    rol = Column(String(20), nullable=False)

    # Contexto académico — todos opcionales (una asignación puede ser solo de rol)
    materia_id = Column(
        SAUUID(as_uuid=True),
        ForeignKey("materias.id", ondelete="RESTRICT"),
        nullable=True,
    )
    carrera_id = Column(
        SAUUID(as_uuid=True),
        ForeignKey("carreras.id", ondelete="RESTRICT"),
        nullable=True,
    )
    cohorte_id = Column(
        SAUUID(as_uuid=True),
        ForeignKey("cohortes.id", ondelete="RESTRICT"),
        nullable=True,
    )

    # Lista de comisiones como strings (ej. ["A", "B"])
    comisiones = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))

    # FK nullable — a quién rinde cuentas el docente en este contexto
    responsable_id = Column(
        SAUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )

    desde = Column(Date, nullable=False)
    hasta = Column(Date, nullable=True)

    __table_args__ = (
        CheckConstraint(_ROL_CHECK, name="ck_asignaciones_rol"),
        Index("ix_asignaciones_tenant", "tenant_id"),
        Index("ix_asignaciones_tenant_usuario", "tenant_id", "usuario_id"),
        Index("ix_asignaciones_tenant_materia", "tenant_id", "materia_id"),
        Index("ix_asignaciones_tenant_rol", "tenant_id", "rol"),
    )

    @property
    def estado_vigencia(self) -> str:
        """'Vigente' si hoy >= desde AND (hasta IS NULL OR hoy <= hasta)."""
        hoy = datetime.date.today()
        if self.desde is None:
            return "Vencida"
        if hoy < self.desde:
            return "Vencida"
        if self.hasta is not None and hoy > self.hasta:
            return "Vencida"
        return "Vigente"

    def __repr__(self) -> str:
        return (
            f"<Asignacion id={self.id} usuario={self.usuario_id} "
            f"rol={self.rol!r} vigencia={self.estado_vigencia}>"
        )
