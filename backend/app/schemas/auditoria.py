"""Schemas Pydantic v2 para el panel de auditoría y métricas (C-19)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditLogEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_id: UUID
    fecha_hora: datetime
    actor_id: UUID
    impersonado_id: UUID | None
    materia_id: UUID | None
    accion: str
    detalle: dict[str, Any] | None
    filas_afectadas: int | None
    ip: str | None
    user_agent: str | None


class AccionPorDia(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fecha: datetime  # date_trunc retorna datetime en PostgreSQL
    total: int


class InteraccionPorActor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actor_id: UUID
    materia_id: UUID | None
    total: int


class MetricasAuditoria(BaseModel):
    model_config = ConfigDict(extra="forbid")

    acciones_por_dia: list[AccionPorDia]
    por_actor: list[InteraccionPorActor]
