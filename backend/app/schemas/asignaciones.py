"""Schemas Pydantic para la entidad Asignacion (C-07 usuarios-y-asignaciones).

AsignacionResponse incluye estado_vigencia como campo calculado (no persiste en DB).
El campo se obtiene del @property del modelo ORM y se inyecta manualmente en el router.

Regla dura #5: extra='forbid' en todos.
"""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

RolAsignacion = Literal[
    "ALUMNO", "TUTOR", "PROFESOR", "COORDINADOR", "NEXO", "ADMIN", "FINANZAS"
]


class AsignacionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    usuario_id: UUID
    rol: RolAsignacion
    materia_id: UUID | None = None
    carrera_id: UUID | None = None
    cohorte_id: UUID | None = None
    comisiones: list[str] = []
    responsable_id: UUID | None = None
    desde: date
    hasta: date | None = None


class AsignacionUpdate(BaseModel):
    """Actualización parcial — todos los campos son opcionales."""

    model_config = ConfigDict(extra="forbid")

    rol: RolAsignacion | None = None
    materia_id: UUID | None = None
    carrera_id: UUID | None = None
    cohorte_id: UUID | None = None
    comisiones: list[str] | None = None
    responsable_id: UUID | None = None
    desde: date | None = None
    hasta: date | None = None


class AsignacionResponse(BaseModel):
    """Respuesta con estado_vigencia derivado en runtime."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    usuario_id: UUID
    rol: str
    materia_id: UUID | None
    carrera_id: UUID | None
    cohorte_id: UUID | None
    comisiones: list[str]
    responsable_id: UUID | None
    desde: date
    hasta: date | None
    estado_vigencia: str
    created_at: datetime
    updated_at: datetime
