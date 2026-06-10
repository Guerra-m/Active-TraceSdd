"""Schemas Pydantic para la estructura académica: Carrera, Cohorte, Materia.

Todos los schemas siguen la regla dura #5: extra='forbid'.
Los schemas de respuesta usan from_attributes=True para construirse desde ORM.
"""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

# ---------------------------------------------------------------------------
# Carrera
# ---------------------------------------------------------------------------

EstadoCarrera = Literal["Activa", "Inactiva"]


class CarreraCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    codigo: str
    nombre: str


class CarreraUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    codigo: str
    nombre: str


class CarreraEstadoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estado: EstadoCarrera


class CarreraResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    tenant_id: UUID
    codigo: str
    nombre: str
    estado: str
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Cohorte
# ---------------------------------------------------------------------------


class CohorteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    carrera_id: UUID
    nombre: str
    anio: int
    vig_desde: date
    vig_hasta: date | None = None


class CohorteResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    tenant_id: UUID
    carrera_id: UUID
    nombre: str
    anio: int
    vig_desde: date
    vig_hasta: date | None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Materia
# ---------------------------------------------------------------------------

EstadoMateria = Literal["Activa", "Inactiva"]


class MateriaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    codigo: str
    nombre: str


class MateriaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    codigo: str
    nombre: str


class MateriaEstadoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estado: EstadoMateria


class MateriaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    tenant_id: UUID
    codigo: str
    nombre: str
    estado: str
    created_at: datetime
    updated_at: datetime
