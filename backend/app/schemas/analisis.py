"""Schemas Pydantic para el módulo de análisis académico (C-11)."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AlumnoAtrasadoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entrada_padron_id: UUID
    nombre: str
    apellidos: str
    faltantes: list[str]
    reprobadas: list[str]


class AtrasadosResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_atrasados: int
    alumnos: list[AlumnoAtrasadoResponse]


class AlumnoRankingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    posicion: int
    entrada_padron_id: UUID
    nombre: str
    apellidos: str
    aprobadas: int
    total: int


class RankingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_alumnos: int
    ranking: list[AlumnoRankingResponse]


class AlumnoNotaFinalResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entrada_padron_id: UUID
    nombre: str
    apellidos: str
    promedio_numerico: Decimal | None
    aprobadas: int
    total: int


class NotasFinalesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_alumnos: int
    alumnos: list[AlumnoNotaFinalResponse]
