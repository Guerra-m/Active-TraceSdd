"""Modelo ORM para InstanciaEncuentro (C-13).

Encuentro concreto derivado de un slot (recurrente) o independiente (único).
Cada instancia tiene estado propio — modificarla no afecta al slot ni a otras
instancias del mismo slot (RN-14).
"""

from sqlalchemy import CheckConstraint, Column, Date, ForeignKey, Index, String, Text, Time
from sqlalchemy import UUID as SAUUID

from app.core.database import Base
from app.models.base import TenantScopedBase

_ESTADOS = ("Programado", "Realizado", "Cancelado")
_ESTADO_CHECK = f"estado IN ({', '.join(repr(e) for e in _ESTADOS)})"


class InstanciaEncuentro(TenantScopedBase, Base):
    __tablename__ = "instancias_encuentro"

    slot_id = Column(SAUUID(as_uuid=True), ForeignKey("slot_encuentros.id", ondelete="SET NULL"), nullable=True)
    materia_id = Column(SAUUID(as_uuid=True), ForeignKey("materias.id", ondelete="RESTRICT"), nullable=False)
    fecha = Column(Date, nullable=False)
    hora = Column(Time, nullable=False)
    titulo = Column(String(200), nullable=False)
    estado = Column(String(20), nullable=False, default="Programado", server_default="Programado")
    meet_url = Column(String(500), nullable=True)
    video_url = Column(String(500), nullable=True)
    comentario = Column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(_ESTADO_CHECK, name="ck_instancias_encuentro_estado"),
        Index("ix_instancias_encuentro_tenant", "tenant_id"),
        Index("ix_instancias_encuentro_tenant_materia", "tenant_id", "materia_id"),
        Index("ix_instancias_encuentro_tenant_fecha", "tenant_id", "fecha"),
    )
