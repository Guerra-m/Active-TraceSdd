"""Schemas Pydantic para el módulo de padrón (C-09 padron-ingesta-moodle).

ImportarPadronResponse — respuesta tras POST /padron/importar.
EntradaPadronResponse  — entrada individual (sin email — PII).
SyncMoodleRequest      — body para POST /padron/sync-moodle.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ImportarPadronResponse(BaseModel):
    """Respuesta de la importación de padrón (versionada)."""

    model_config = ConfigDict(extra="forbid")

    version_id: UUID
    filas_importadas: int
    materia_id: UUID
    cohorte_id: UUID


class EntradaPadronResponse(BaseModel):
    """Entrada de padrón (sin email — campo PII no expuesto en listados)."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    version_id: UUID
    usuario_id: UUID | None
    nombre: str
    apellidos: str
    comision: str | None
    regional: str | None


class SyncMoodleRequest(BaseModel):
    """Request para sincronizar padrón desde Moodle WS."""

    model_config = ConfigDict(extra="forbid")

    materia_id: UUID
    cohorte_id: UUID
    moodle_course_id: int
