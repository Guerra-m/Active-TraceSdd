"""Schemas Pydantic v2 para el módulo de tareas internas (C-16)."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TareaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asignado_a: UUID
    descripcion: str = Field(..., min_length=1)
    materia_id: UUID | None = None
    contexto_id: UUID | None = None


class TareaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estado: Literal["Pendiente", "En progreso", "Resuelta", "Cancelada"] | None = None
    descripcion: str | None = Field(default=None, min_length=1)


class TareaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    materia_id: UUID | None
    asignado_a: UUID
    asignado_por: UUID
    estado: str
    descripcion: str
    contexto_id: UUID | None
    created_at: datetime | None


class ComentarioCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    texto: str = Field(..., min_length=1)


class ComentarioResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tarea_id: UUID
    autor_id: UUID
    texto: str
    created_at: datetime | None
