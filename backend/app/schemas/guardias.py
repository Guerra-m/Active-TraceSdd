"""Schemas Pydantic para guardias de atención (C-13)."""

import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


_DIAS_VALIDOS = {"Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"}
_ESTADOS_VALIDOS = {"Pendiente", "Realizada", "Cancelada"}


class GuardiaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    carrera_id: UUID
    cohorte_id: UUID
    dia: str = Field(..., max_length=15)
    horario: str = Field(..., max_length=50)
    estado: str = "Pendiente"
    comentarios: str | None = None

    @model_validator(mode="after")
    def validar_campos(self) -> "GuardiaCreate":
        if self.dia not in _DIAS_VALIDOS:
            raise ValueError(f"dia debe ser uno de {_DIAS_VALIDOS}")
        if self.estado not in _ESTADOS_VALIDOS:
            raise ValueError(f"estado debe ser uno de {_ESTADOS_VALIDOS}")
        return self


class GuardiaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    asignacion_id: UUID
    materia_id: UUID
    carrera_id: UUID
    cohorte_id: UUID
    dia: str
    horario: str
    estado: str
    comentarios: str | None
    created_at: datetime.datetime | None
