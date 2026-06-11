"""Schemas Pydantic v2 para el módulo de programas y fechas académicas (C-17)."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FechaAcademicaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    cohorte_id: UUID
    tipo: Literal["Parcial", "TP", "Coloquio", "Recuperatorio"]
    numero: int = Field(default=1, ge=1)
    periodo: str = Field(..., min_length=1, max_length=20)
    fecha: str = Field(..., min_length=1, max_length=20)
    titulo: str = Field(..., min_length=1, max_length=300)


class FechaAcademicaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fecha: str | None = Field(default=None, max_length=20)
    titulo: str | None = Field(default=None, max_length=300)


class FechaAcademicaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    materia_id: UUID
    cohorte_id: UUID
    tipo: str
    numero: int
    periodo: str
    fecha: str
    titulo: str


class ProgramaMateriaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    carrera_id: UUID
    cohorte_id: UUID
    titulo: str = Field(..., min_length=1, max_length=300)
    referencia_archivo: str = Field(..., min_length=1)


class ProgramaMateriaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    materia_id: UUID
    carrera_id: UUID
    cohorte_id: UUID
    titulo: str
    referencia_archivo: str
    cargado_at: datetime | None
