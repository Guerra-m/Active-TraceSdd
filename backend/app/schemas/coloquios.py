"""Schemas Pydantic v2 para el módulo de coloquios y evaluaciones (C-14)."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EvaluacionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    cohorte_id: UUID
    tipo: Literal["Parcial", "TP", "Coloquio", "Recuperatorio"] = "Coloquio"
    instancia: str = Field(..., min_length=1, max_length=200)
    dias_disponibles: int = Field(default=1, ge=1)
    cupos_por_dia: int = Field(default=10, ge=1)


class EvaluacionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    materia_id: UUID
    cohorte_id: UUID
    tipo: str
    instancia: str
    dias_disponibles: int
    cupos_por_dia: int


class ReservaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fecha_hora: str = Field(..., min_length=1, max_length=50)


class ReservaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    evaluacion_id: UUID
    alumno_id: UUID
    fecha_hora: str
    estado: str


class AlumnosImportPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alumno_ids: list[UUID] = Field(..., min_length=1)


class ResultadoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alumno_id: UUID
    nota_final: str | None = Field(default=None, max_length=50)


class ResultadoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    evaluacion_id: UUID
    alumno_id: UUID
    nota_final: str | None


class MetricasColoquioResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_convocados: int
    instancias_activas: int
    reservas_activas: int
    notas_registradas: int
