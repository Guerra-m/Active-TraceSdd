"""Repository de solo-lectura para el panel de auditoría (C-19).

Separado de AuditLogRepository (solo-escritura) para mantener la invariante
append-only del log: el repositorio de escritura no expone reads, y viceversa.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditLogQueryRepository:
    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    def _base_stmt(self):
        return select(AuditLog).where(AuditLog.tenant_id == self._tenant_id)

    async def list_filtrado(
        self,
        *,
        actor_id: UUID | None = None,
        materia_id: UUID | None = None,
        accion: str | None = None,
        fecha_desde: datetime | None = None,
        fecha_hasta: datetime | None = None,
        limit: int = 200,
    ) -> list[AuditLog]:
        stmt = self._base_stmt()
        if actor_id is not None:
            stmt = stmt.where(AuditLog.actor_id == actor_id)
        if materia_id is not None:
            stmt = stmt.where(AuditLog.materia_id == materia_id)
        if accion is not None:
            stmt = stmt.where(AuditLog.accion == accion)
        if fecha_desde is not None:
            stmt = stmt.where(AuditLog.fecha_hora >= fecha_desde)
        if fecha_hasta is not None:
            stmt = stmt.where(AuditLog.fecha_hora <= fecha_hasta)
        stmt = stmt.order_by(AuditLog.fecha_hora.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def acciones_por_dia(
        self,
        *,
        actor_id: UUID | None = None,
        fecha_desde: datetime | None = None,
        fecha_hasta: datetime | None = None,
    ) -> list[dict]:
        """Conteo de acciones agrupado por día (fecha_hora truncada a día)."""
        dia = func.date_trunc("day", AuditLog.fecha_hora).label("dia")
        stmt = (
            select(dia, func.count().label("total"))
            .where(AuditLog.tenant_id == self._tenant_id)
        )
        if actor_id is not None:
            stmt = stmt.where(AuditLog.actor_id == actor_id)
        if fecha_desde is not None:
            stmt = stmt.where(AuditLog.fecha_hora >= fecha_desde)
        if fecha_hasta is not None:
            stmt = stmt.where(AuditLog.fecha_hora <= fecha_hasta)
        stmt = stmt.group_by(dia).order_by(dia.asc())
        result = await self._session.execute(stmt)
        return [{"fecha": row.dia, "total": row.total} for row in result.all()]

    async def por_actor_materia(
        self,
        *,
        actor_id: UUID | None = None,
        fecha_desde: datetime | None = None,
        fecha_hasta: datetime | None = None,
    ) -> list[dict]:
        """Conteo de acciones agrupado por actor_id × materia_id."""
        stmt = (
            select(
                AuditLog.actor_id,
                AuditLog.materia_id,
                func.count().label("total"),
            )
            .where(AuditLog.tenant_id == self._tenant_id)
        )
        if actor_id is not None:
            stmt = stmt.where(AuditLog.actor_id == actor_id)
        if fecha_desde is not None:
            stmt = stmt.where(AuditLog.fecha_hora >= fecha_desde)
        if fecha_hasta is not None:
            stmt = stmt.where(AuditLog.fecha_hora <= fecha_hasta)
        stmt = stmt.group_by(AuditLog.actor_id, AuditLog.materia_id)
        result = await self._session.execute(stmt)
        return [
            {"actor_id": row.actor_id, "materia_id": row.materia_id, "total": row.total}
            for row in result.all()
        ]
