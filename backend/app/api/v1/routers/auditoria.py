"""Router del panel de auditoría y métricas (C-19).

Endpoints (todos requieren auditoria:ver):
  GET /api/v1/auditoria          → log filtrado (últimas N acciones del tenant)
  GET /api/v1/auditoria/metricas → métricas agregadas (acciones/día, por actor×materia)

Scoping:
  - ADMIN/FINANZAS (is_own=False) → todos los registros del tenant
  - COORDINADOR (is_own=True)     → solo acciones propias (actor_id=current_user.id)

Regla #8: identidad SIEMPRE del JWT.
Regla #11: no lógica de negocio en el router — queries vía repository.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.repositories.audit_query_repository import AuditLogQueryRepository
from app.schemas.auditoria import (
    AccionPorDia,
    AuditLogEntry,
    InteraccionPorActor,
    MetricasAuditoria,
)

router = APIRouter(prefix="/api/v1/auditoria", tags=["auditoria"])

_PERM = Depends(require_permission("auditoria:ver"))


def _entry(a) -> AuditLogEntry:
    return AuditLogEntry(
        id=a.id,
        tenant_id=a.tenant_id,
        fecha_hora=a.fecha_hora,
        actor_id=a.actor_id,
        impersonado_id=a.impersonado_id,
        materia_id=a.materia_id,
        accion=a.accion,
        detalle=a.detalle,
        filas_afectadas=a.filas_afectadas,
        ip=a.ip,
        user_agent=a.user_agent,
    )


# Nota: /metricas DEBE ir antes del potencial /{id} para evitar conflicto de rutas.

@router.get("/metricas", response_model=MetricasAuditoria)
async def get_metricas(
    request: Request,
    fecha_desde: datetime | None = Query(default=None),
    fecha_hasta: datetime | None = Query(default=None),
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MetricasAuditoria:
    is_own = getattr(request.state, "permission_is_own_resource", False)
    actor_id = current_user.id if is_own else None

    repo = AuditLogQueryRepository(db, tenant_id=current_user.tenant_id)
    por_dia = await repo.acciones_por_dia(
        actor_id=actor_id, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta
    )
    por_actor = await repo.por_actor_materia(
        actor_id=actor_id, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta
    )
    return MetricasAuditoria(
        acciones_por_dia=[AccionPorDia(fecha=r["fecha"], total=r["total"]) for r in por_dia],
        por_actor=[
            InteraccionPorActor(actor_id=r["actor_id"], materia_id=r["materia_id"], total=r["total"])
            for r in por_actor
        ],
    )


@router.get("", response_model=list[AuditLogEntry])
async def get_log(
    request: Request,
    actor_id: UUID | None = Query(default=None),
    materia_id: UUID | None = Query(default=None),
    accion: str | None = Query(default=None),
    fecha_desde: datetime | None = Query(default=None),
    fecha_hasta: datetime | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AuditLogEntry]:
    is_own = getattr(request.state, "permission_is_own_resource", False)
    # COORDINADOR (propio): ignora el actor_id del query param, fuerza el suyo
    if is_own:
        actor_id = current_user.id

    repo = AuditLogQueryRepository(db, tenant_id=current_user.tenant_id)
    entries = await repo.list_filtrado(
        actor_id=actor_id,
        materia_id=materia_id,
        accion=accion,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        limit=limit,
    )
    return [_entry(e) for e in entries]
