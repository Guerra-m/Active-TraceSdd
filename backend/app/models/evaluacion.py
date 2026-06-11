"""Modelos ORM para Evaluacion, ReservaEvaluacion y ResultadoEvaluacion (C-14).

E14 — Evaluación (instancia de examen / coloquio).
"""

from sqlalchemy import CheckConstraint, Column, ForeignKey, Index, Integer, String, Text
from sqlalchemy import UUID as SAUUID

from app.core.database import Base
from app.models.base import TenantScopedBase

_TIPOS = ("Parcial", "TP", "Coloquio", "Recuperatorio")
_TIPO_CHECK = f"tipo IN ({', '.join(repr(t) for t in _TIPOS)})"

_ESTADOS_RESERVA = ("Activa", "Cancelada")
_ESTADO_RESERVA_CHECK = f"estado IN ({', '.join(repr(e) for e in _ESTADOS_RESERVA)})"


class Evaluacion(TenantScopedBase, Base):
    __tablename__ = "evaluaciones"

    materia_id = Column(SAUUID(as_uuid=True), ForeignKey("materias.id", ondelete="RESTRICT"), nullable=False)
    cohorte_id = Column(SAUUID(as_uuid=True), ForeignKey("cohortes.id", ondelete="RESTRICT"), nullable=False)
    tipo = Column(String(20), nullable=False, default="Coloquio", server_default="Coloquio")
    instancia = Column(String(200), nullable=False)
    dias_disponibles = Column(Integer, nullable=False, default=1, server_default="1")
    cupos_por_dia = Column(Integer, nullable=False, default=10, server_default="10")

    __table_args__ = (
        CheckConstraint(_TIPO_CHECK, name="ck_evaluaciones_tipo"),
        Index("ix_evaluaciones_tenant", "tenant_id"),
        Index("ix_evaluaciones_tenant_materia", "tenant_id", "materia_id"),
    )


class ReservaEvaluacion(TenantScopedBase, Base):
    __tablename__ = "reservas_evaluacion"

    evaluacion_id = Column(SAUUID(as_uuid=True), ForeignKey("evaluaciones.id", ondelete="RESTRICT"), nullable=False)
    alumno_id = Column(SAUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    fecha_hora = Column(String(50), nullable=False)
    estado = Column(String(20), nullable=False, default="Activa", server_default="Activa")

    __table_args__ = (
        CheckConstraint(_ESTADO_RESERVA_CHECK, name="ck_reservas_evaluacion_estado"),
        Index("ix_reservas_evaluacion_tenant", "tenant_id"),
        Index("ix_reservas_evaluacion_tenant_evaluacion", "tenant_id", "evaluacion_id"),
        Index("ix_reservas_evaluacion_tenant_alumno", "tenant_id", "alumno_id"),
    )


class ResultadoEvaluacion(TenantScopedBase, Base):
    __tablename__ = "resultados_evaluacion"

    evaluacion_id = Column(SAUUID(as_uuid=True), ForeignKey("evaluaciones.id", ondelete="RESTRICT"), nullable=False)
    alumno_id = Column(SAUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    nota_final = Column(String(50), nullable=True)

    __table_args__ = (
        Index("ix_resultados_evaluacion_tenant", "tenant_id"),
        Index("ix_resultados_evaluacion_tenant_evaluacion", "tenant_id", "evaluacion_id"),
    )
