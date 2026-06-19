"""Schemas Pydantic para el módulo de calificaciones (C-10)."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ImportarCalificacionesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asignacion_id: UUID
    materia_id: UUID
    filas_importadas: int
    actividades_detectadas: list[str]


class UmbralMateriaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    umbral_pct: int = Field(..., ge=1, le=100)
    valores_aprobatorios: list[str] = Field(
        default_factory=lambda: ["Satisfactorio", "Supera lo esperado"]
    )


class UmbralMateriaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    umbral_pct: int
    valores_aprobatorios: list[str]
    es_default: bool


class CalificacionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    actividad: str
    nota_numerica: Decimal | None
    nota_textual: str | None
    aprobado: bool
    nombre_alumno: str | None
    apellidos_alumno: str | None


class MiCalificacionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actividad: str
    nota_numerica: Decimal | None
    nota_textual: str | None
    aprobado: bool
    materia_nombre: str | None
