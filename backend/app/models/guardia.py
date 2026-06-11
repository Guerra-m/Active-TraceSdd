"""Modelo ORM para Guardia (C-13).

Registro de guardia de atención cubierta por un tutor o docente.
"""

from sqlalchemy import CheckConstraint, Column, ForeignKey, Index, String, Text
from sqlalchemy import UUID as SAUUID

from app.core.database import Base
from app.models.base import TenantScopedBase

_DIAS_VALIDOS = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")
_DIA_CHECK = f"dia IN ({', '.join(repr(d) for d in _DIAS_VALIDOS)})"

_ESTADOS = ("Pendiente", "Realizada", "Cancelada")
_ESTADO_CHECK = f"estado IN ({', '.join(repr(e) for e in _ESTADOS)})"


class Guardia(TenantScopedBase, Base):
    __tablename__ = "guardias"

    asignacion_id = Column(SAUUID(as_uuid=True), ForeignKey("asignaciones.id", ondelete="RESTRICT"), nullable=False)
    materia_id = Column(SAUUID(as_uuid=True), ForeignKey("materias.id", ondelete="RESTRICT"), nullable=False)
    carrera_id = Column(SAUUID(as_uuid=True), ForeignKey("carreras.id", ondelete="RESTRICT"), nullable=False)
    cohorte_id = Column(SAUUID(as_uuid=True), ForeignKey("cohortes.id", ondelete="RESTRICT"), nullable=False)
    dia = Column(String(15), nullable=False)
    horario = Column(String(50), nullable=False)
    estado = Column(String(20), nullable=False, default="Pendiente", server_default="Pendiente")
    comentarios = Column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(_DIA_CHECK, name="ck_guardias_dia"),
        CheckConstraint(_ESTADO_CHECK, name="ck_guardias_estado"),
        Index("ix_guardias_tenant", "tenant_id"),
        Index("ix_guardias_tenant_asignacion", "tenant_id", "asignacion_id"),
    )
