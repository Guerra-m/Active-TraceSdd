"""Schemas Pydantic v2 para perfil de usuario y mensajería interna (C-20)."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PerfilResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    nombre: str | None
    apellidos: str | None
    banco: str | None
    regional: str | None
    legajo: str | None
    legajo_profesional: str | None
    facturador: bool
    cuil: str | None  # solo lectura — descifrado para mostrar
    cbu: str | None   # descifrado para mostrar
    alias_cbu: str | None
    is_active: bool


class PerfilUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str | None = Field(default=None, max_length=200)
    apellidos: str | None = Field(default=None, max_length=200)
    banco: str | None = Field(default=None, max_length=100)
    regional: str | None = Field(default=None, max_length=100)
    legajo: str | None = Field(default=None, max_length=50)
    legajo_profesional: str | None = Field(default=None, max_length=50)
    facturador: bool | None = None
    cbu: str | None = Field(default=None, max_length=30)
    alias_cbu: str | None = Field(default=None, max_length=60)


class HiloMensajeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    destinatario_id: UUID
    asunto: str = Field(..., min_length=1, max_length=200)
    primer_mensaje: str = Field(..., min_length=1)


class HiloMensajeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    asunto: str
    remitente_id: UUID
    destinatario_id: UUID


class MensajeInternoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cuerpo: str = Field(..., min_length=1)


class MensajeInternoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    hilo_id: UUID
    autor_id: UUID
    cuerpo: str
