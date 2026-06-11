"""Schemas Pydantic para la gestión de equipos docentes (C-08).

Cubre: mis-equipos, asignación masiva, clonado entre cohortes,
vigencia masiva, búsqueda de docentes y exportación CSV.
"""

import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class MisEquiposFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID | None = None
    carrera_id: UUID | None = None
    cohorte_id: UUID | None = None
    estado_vigencia: str | None = None


class AsignacionMasivaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    usuario_ids: list[UUID]
    rol: str
    materia_id: UUID | None = None
    carrera_id: UUID | None = None
    cohorte_id: UUID | None = None
    comisiones: list[str] = []
    responsable_id: UUID | None = None
    desde: datetime.date
    hasta: datetime.date | None = None

    @field_validator("usuario_ids")
    @classmethod
    def validate_usuario_ids(cls, v: list[UUID]) -> list[UUID]:
        if len(v) == 0:
            raise ValueError("Debe especificar al menos un usuario")
        if len(v) > 200:
            raise ValueError("Máximo 200 docentes por operación masiva")
        return v


class ClonarEquipoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    carrera_id: UUID
    cohorte_origen_id: UUID
    cohorte_destino_id: UUID
    desde: datetime.date
    hasta: datetime.date | None = None

    @model_validator(mode="after")
    def origen_distinto_destino(self) -> "ClonarEquipoRequest":
        if self.cohorte_origen_id == self.cohorte_destino_id:
            raise ValueError("La cohorte destino debe ser distinta a la origen")
        return self


class VigenciaMasivaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    carrera_id: UUID
    cohorte_id: UUID
    desde: datetime.date | None = None
    hasta: datetime.date | None = None

    @model_validator(mode="after")
    def al_menos_un_campo(self) -> "VigenciaMasivaRequest":
        if self.desde is None and self.hasta is None:
            raise ValueError("Debe especificar al menos desde o hasta")
        return self


class BuscarDocenteItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    nombre: str | None
    apellidos: str | None


class AsignacionMasivaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    creadas: int
    asignaciones: list[dict]


class ClonarEquipoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    creadas: int
    conflictos: int
    asignaciones: list[dict]
    omitidos: list[dict]


class VigenciaMasivaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filas_actualizadas: int
