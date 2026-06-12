"""Schemas Pydantic para el módulo de comunicaciones (C-12)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asunto_template: str = Field(..., min_length=1, max_length=500)
    cuerpo_template: str = Field(..., min_length=1)
    variables_ejemplo: dict[str, str] = Field(
        default_factory=lambda: {"nombre": "Juan", "apellidos": "Pérez"}
    )


class PreviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asunto_renderizado: str
    cuerpo_renderizado: str


class DestinatarioInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entrada_padron_id: UUID | None = None
    nombre: str
    apellidos: str
    email_encrypted: str


class CrearLoteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID | None = None
    asunto_template: str = Field(..., min_length=1, max_length=500)
    cuerpo_template: str = Field(..., min_length=1)
    destinatarios: list[DestinatarioInput] = Field(..., min_length=1)


class CrearLotePorCriterioRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asignacion_id: UUID
    materia_id: UUID
    criterio: str = Field(..., pattern="^(atrasados|todos)$")
    asunto_template: str = Field(..., min_length=1, max_length=500)
    cuerpo_template: str = Field(..., min_length=1)


class LoteComunicacionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    estado: str
    requiere_aprobacion: bool
    total_mensajes: int
    enviados: int
    errores: int
    materia_id: UUID | None
    aprobado_at: datetime | None
    created_at: datetime
