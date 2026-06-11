"""Modelos ORM para ProgramaMateria y FechaAcademica (C-17).

E15 — FechaAcademica: calendarización de instancias evaluativas.
E16 — ProgramaMateria: documento del programa oficial por materia×carrera×cohorte.
"""

from datetime import datetime
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy import UUID as SAUUID

from app.core.database import Base
from app.models.base import TenantScopedBase

_TIPOS = ("Parcial", "TP", "Coloquio", "Recuperatorio")
_TIPO_CHECK = f"tipo IN ({', '.join(repr(t) for t in _TIPOS)})"


class FechaAcademica(TenantScopedBase, Base):
    __tablename__ = "fechas_academicas"

    materia_id = Column(SAUUID(as_uuid=True), ForeignKey("materias.id", ondelete="RESTRICT"), nullable=False)
    cohorte_id = Column(SAUUID(as_uuid=True), ForeignKey("cohortes.id", ondelete="RESTRICT"), nullable=False)
    tipo = Column(String(20), nullable=False)
    numero = Column(Integer, nullable=False, default=1, server_default="1")
    periodo = Column(String(20), nullable=False)
    fecha = Column(String(20), nullable=False)
    titulo = Column(String(300), nullable=False)

    __table_args__ = (
        CheckConstraint(_TIPO_CHECK, name="ck_fechas_academicas_tipo"),
        Index("ix_fechas_academicas_tenant", "tenant_id"),
        Index("ix_fechas_academicas_tenant_materia", "tenant_id", "materia_id"),
        Index("ix_fechas_academicas_tenant_periodo", "tenant_id", "periodo"),
    )


class ProgramaMateria(TenantScopedBase, Base):
    __tablename__ = "programas_materia"

    materia_id = Column(SAUUID(as_uuid=True), ForeignKey("materias.id", ondelete="RESTRICT"), nullable=False)
    carrera_id = Column(SAUUID(as_uuid=True), ForeignKey("carreras.id", ondelete="RESTRICT"), nullable=False)
    cohorte_id = Column(SAUUID(as_uuid=True), ForeignKey("cohortes.id", ondelete="RESTRICT"), nullable=False)
    titulo = Column(String(300), nullable=False)
    referencia_archivo = Column(Text, nullable=False)
    cargado_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_programas_materia_tenant", "tenant_id"),
        Index("ix_programas_materia_tenant_materia", "tenant_id", "materia_id"),
    )
