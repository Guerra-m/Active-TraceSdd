"""Schemas Pydantic para encuentros sincrónicos (C-13)."""

import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


_DIAS_VALIDOS = {"Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"}
_ESTADOS_VALIDOS = {"Programado", "Realizado", "Cancelado"}


class SlotEncuentroCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    titulo: str = Field(..., max_length=200)
    hora: datetime.time

    # Modo recurrente
    dia_semana: str | None = None
    fecha_inicio: datetime.date | None = None
    cant_semanas: int | None = Field(default=None, ge=1, le=52)

    # Modo único
    fecha_unica: datetime.date | None = None

    meet_url: str | None = Field(default=None, max_length=500)
    vig_desde: datetime.date | None = None
    vig_hasta: datetime.date | None = None

    @model_validator(mode="after")
    def validar_modo_excluyente(self) -> "SlotEncuentroCreate":
        tiene_recurrente = self.cant_semanas is not None
        tiene_unico = self.fecha_unica is not None
        if tiene_recurrente and tiene_unico:
            raise ValueError("Los modos recurrente y único son excluyentes")
        if not tiene_recurrente and not tiene_unico:
            raise ValueError("Debe especificar cant_semanas (recurrente) o fecha_unica (único)")
        if tiene_recurrente:
            if not self.fecha_inicio:
                raise ValueError("fecha_inicio es requerida en modo recurrente")
        return self


class InstanciaEncuentroUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estado: str | None = None
    meet_url: str | None = Field(default=None, max_length=500)
    video_url: str | None = Field(default=None, max_length=500)
    comentario: str | None = None

    @model_validator(mode="after")
    def validar_estado(self) -> "InstanciaEncuentroUpdate":
        if self.estado is not None and self.estado not in _ESTADOS_VALIDOS:
            raise ValueError(f"estado debe ser uno de {_ESTADOS_VALIDOS}")
        return self


class SlotEncuentroResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    asignacion_id: UUID
    materia_id: UUID
    titulo: str
    hora: datetime.time
    dia_semana: str | None
    fecha_inicio: datetime.date | None
    cant_semanas: int
    fecha_unica: datetime.date | None
    meet_url: str | None
    vig_desde: datetime.date | None
    vig_hasta: datetime.date | None


class InstanciaEncuentroResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    slot_id: UUID | None
    materia_id: UUID
    fecha: datetime.date
    hora: datetime.time
    titulo: str
    estado: str
    meet_url: str | None
    video_url: str | None
    comentario: str | None
