"""Schemas Pydantic para la entidad Usuario (C-07 usuarios-y-asignaciones).

Dos niveles de respuesta:
  - UsuarioResponse    : sin PII (dni, cuil, cbu, alias_cbu) — respuesta estándar
  - UsuarioPIIResponse : con PII desencriptada — solo endpoint /usuarios/{id}/pii

Regla dura #5: extra='forbid' en todos.
Regla dura #12: PII (dni, cuil, cbu) nunca en respuestas estándar.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

EstadoUsuario = Literal["Activo", "Inactivo"]


class UsuarioCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str
    nombre: str | None = None
    apellidos: str | None = None
    # PII — recibidos en texto plano, cifrados antes de persistir
    dni: str | None = None
    cuil: str | None = None
    cbu: str | None = None
    alias_cbu: str | None = None
    banco: str | None = None
    regional: str | None = None
    legajo: str | None = None
    legajo_profesional: str | None = None
    facturador: bool = False
    estado: EstadoUsuario = "Activo"


class UsuarioUpdate(BaseModel):
    """Actualización parcial de perfil — todos los campos son opcionales."""

    model_config = ConfigDict(extra="forbid")

    nombre: str | None = None
    apellidos: str | None = None
    dni: str | None = None
    cuil: str | None = None
    cbu: str | None = None
    alias_cbu: str | None = None
    banco: str | None = None
    regional: str | None = None
    legajo: str | None = None
    legajo_profesional: str | None = None
    facturador: bool | None = None
    estado: EstadoUsuario | None = None


class UsuarioResponse(BaseModel):
    """Respuesta estándar — sin PII sensible (dni/cuil/cbu/alias_cbu omitidos)."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    tenant_id: UUID
    nombre: str | None
    apellidos: str | None
    banco: str | None
    regional: str | None
    legajo: str | None
    legajo_profesional: str | None
    facturador: bool
    estado: str
    is_active: bool
    totp_enabled: bool
    created_at: datetime
    updated_at: datetime


class UsuarioPIIResponse(BaseModel):
    """Respuesta extendida con PII desencriptada — solo para endpoint /pii."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    nombre: str | None
    apellidos: str | None
    # PII desencriptada — solo en este schema
    dni: str | None
    cuil: str | None
    cbu: str | None
    alias_cbu: str | None
    banco: str | None
    regional: str | None
    legajo: str | None
    legajo_profesional: str | None
    facturador: bool
    estado: str
