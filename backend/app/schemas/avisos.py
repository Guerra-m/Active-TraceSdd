"""Schemas Pydantic v2 para el módulo de avisos y acknowledgments (C-15)."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AvisoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alcance: Literal["Global", "PorMateria", "PorCohorte", "PorRol"] = "Global"
    materia_id: UUID | None = None
    cohorte_id: UUID | None = None
    rol_destino: str | None = None
    severidad: Literal["Info", "Advertencia", "Crítico"] = "Info"
    titulo: str = Field(..., min_length=1, max_length=300)
    cuerpo: str = Field(..., min_length=1)
    inicio_en: datetime
    fin_en: datetime | None = None
    orden: int = Field(default=0, ge=0)
    activo: bool = True
    requiere_ack: bool = False


class AvisoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titulo: str | None = Field(default=None, max_length=300)
    cuerpo: str | None = None
    severidad: Literal["Info", "Advertencia", "Crítico"] | None = None
    inicio_en: datetime | None = None
    fin_en: datetime | None = None
    orden: int | None = Field(default=None, ge=0)
    activo: bool | None = None


class AvisoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    alcance: str
    materia_id: UUID | None
    cohorte_id: UUID | None
    rol_destino: str | None
    severidad: str
    titulo: str
    cuerpo: str
    inicio_en: datetime
    fin_en: datetime | None
    orden: int
    activo: bool
    requiere_ack: bool


class AckResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    aviso_id: UUID
    usuario_id: UUID
    confirmado_at: datetime


class AvisoStatsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    aviso_id: UUID
    total_acks: int
