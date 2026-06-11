"""Modelo ORM para SlotEncuentro (C-13).

Un slot es la plantilla de recurrencia de un encuentro sincrónico.
Modo recurrente: genera N instancias (cant_semanas > 0).
Modo único: fecha_unica no nula, cant_semanas = 0.
"""

from sqlalchemy import CheckConstraint, Column, Date, ForeignKey, Index, Integer, String, Time
from sqlalchemy import UUID as SAUUID

from app.core.database import Base
from app.models.base import TenantScopedBase

_DIAS_VALIDOS = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")
_DIA_CHECK = f"dia_semana IN ({', '.join(repr(d) for d in _DIAS_VALIDOS)})"


class SlotEncuentro(TenantScopedBase, Base):
    __tablename__ = "slot_encuentros"

    asignacion_id = Column(SAUUID(as_uuid=True), ForeignKey("asignaciones.id", ondelete="RESTRICT"), nullable=False)
    materia_id = Column(SAUUID(as_uuid=True), ForeignKey("materias.id", ondelete="RESTRICT"), nullable=False)
    titulo = Column(String(200), nullable=False)
    hora = Column(Time, nullable=False)
    dia_semana = Column(String(15), nullable=True)
    fecha_inicio = Column(Date, nullable=True)
    cant_semanas = Column(Integer, nullable=False, default=0)
    fecha_unica = Column(Date, nullable=True)
    meet_url = Column(String(500), nullable=True)
    vig_desde = Column(Date, nullable=True)
    vig_hasta = Column(Date, nullable=True)

    __table_args__ = (
        CheckConstraint(_DIA_CHECK, name="ck_slot_encuentros_dia_semana"),
        Index("ix_slot_encuentros_tenant", "tenant_id"),
        Index("ix_slot_encuentros_tenant_materia", "tenant_id", "materia_id"),
    )
