"""Repository para la entidad Asignacion (C-07 + C-08).

C-07: list_filtrado — listado con filtros individuales.
C-08: list_equipo, bulk_create, clone_equipo, bulk_update_vigencia — operaciones de equipo.
"""

import datetime
from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asignacion import Asignacion
from app.repositories.base import BaseRepository


class AsignacionRepository(BaseRepository[Asignacion]):
    """Repository de Asignacion con scope de tenant obligatorio."""

    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        super().__init__(session, tenant_id=tenant_id, model=Asignacion)

    async def list_filtrado(
        self,
        *,
        usuario_id: UUID | None = None,
        rol: str | None = None,
        materia_id: UUID | None = None,
        carrera_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Asignacion]:
        """Lista asignaciones del tenant con filtros opcionales acumulables."""
        stmt = self._base_query()

        if usuario_id is not None:
            stmt = stmt.where(Asignacion.usuario_id == usuario_id)
        if rol is not None:
            stmt = stmt.where(Asignacion.rol == rol)
        if materia_id is not None:
            stmt = stmt.where(Asignacion.materia_id == materia_id)
        if carrera_id is not None:
            stmt = stmt.where(Asignacion.carrera_id == carrera_id)
        if cohorte_id is not None:
            stmt = stmt.where(Asignacion.cohorte_id == cohorte_id)

        stmt = stmt.offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # C-08 — Operaciones de equipo
    # ------------------------------------------------------------------

    async def list_equipo(
        self,
        *,
        materia_id: UUID | None = None,
        carrera_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        rol: str | None = None,
        estado_vigencia: str | None = None,
    ) -> list[Asignacion]:
        """Lista asignaciones con filtros de equipo; filtra estado_vigencia en Python."""
        stmt = self._base_query()

        if materia_id is not None:
            stmt = stmt.where(Asignacion.materia_id == materia_id)
        if carrera_id is not None:
            stmt = stmt.where(Asignacion.carrera_id == carrera_id)
        if cohorte_id is not None:
            stmt = stmt.where(Asignacion.cohorte_id == cohorte_id)
        if rol is not None:
            stmt = stmt.where(Asignacion.rol == rol)

        result = await self._session.execute(stmt)
        items = list(result.scalars().all())

        if estado_vigencia is not None:
            items = [a for a in items if a.estado_vigencia == estado_vigencia]

        return items

    async def bulk_create(self, items: list[Asignacion]) -> list[Asignacion]:
        """Inserta una lista de asignaciones en una sola transacción."""
        created = []
        for item in items:
            item.tenant_id = self._tenant_id
            self._session.add(item)
            created.append(item)
        await self._session.flush()
        for item in created:
            await self._session.refresh(item)
        return created

    async def clone_equipo(
        self,
        *,
        materia_id: UUID,
        carrera_id: UUID,
        cohorte_origen_id: UUID,
        cohorte_destino_id: UUID,
        desde: datetime.date,
        hasta: datetime.date | None,
    ) -> tuple[list[Asignacion], list[dict]]:
        """Clona asignaciones vigentes de origen a destino.

        Retorna (creadas, conflictos) donde conflictos es lista de dicts con
        los registros omitidos por ya existir en destino.
        """
        stmt_origen = (
            select(Asignacion)
            .where(Asignacion.tenant_id == self._tenant_id)
            .where(Asignacion.deleted_at.is_(None))
            .where(Asignacion.materia_id == materia_id)
            .where(Asignacion.carrera_id == carrera_id)
            .where(Asignacion.cohorte_id == cohorte_origen_id)
        )
        result = await self._session.execute(stmt_origen)
        candidatos = [a for a in result.scalars().all() if a.estado_vigencia == "Vigente"]

        stmt_destino = (
            select(Asignacion)
            .where(Asignacion.tenant_id == self._tenant_id)
            .where(Asignacion.deleted_at.is_(None))
            .where(Asignacion.materia_id == materia_id)
            .where(Asignacion.carrera_id == carrera_id)
            .where(Asignacion.cohorte_id == cohorte_destino_id)
        )
        result_dest = await self._session.execute(stmt_destino)
        existentes = {
            (a.usuario_id, a.rol)
            for a in result_dest.scalars().all()
        }

        creadas: list[Asignacion] = []
        conflictos: list[dict] = []

        for origen in candidatos:
            clave = (origen.usuario_id, origen.rol)
            if clave in existentes:
                conflictos.append({
                    "usuario_id": str(origen.usuario_id),
                    "rol": origen.rol,
                    "razon": "ya existe en destino",
                })
                continue

            nueva = Asignacion(
                tenant_id=self._tenant_id,
                usuario_id=origen.usuario_id,
                rol=origen.rol,
                materia_id=materia_id,
                carrera_id=carrera_id,
                cohorte_id=cohorte_destino_id,
                comisiones=origen.comisiones,
                responsable_id=origen.responsable_id,
                desde=desde,
                hasta=hasta,
            )
            self._session.add(nueva)
            creadas.append(nueva)

        await self._session.flush()
        for a in creadas:
            await self._session.refresh(a)

        return creadas, conflictos

    async def bulk_update_vigencia(
        self,
        *,
        materia_id: UUID,
        carrera_id: UUID,
        cohorte_id: UUID,
        desde: datetime.date | None,
        hasta: datetime.date | None,
    ) -> int:
        """Actualiza desde/hasta de todas las asignaciones activas del equipo.

        Retorna el número de filas actualizadas.
        """
        valores: dict = {}
        if desde is not None:
            valores["desde"] = desde
        if hasta is not None:
            valores["hasta"] = hasta

        if not valores:
            return 0

        stmt = (
            update(Asignacion)
            .where(
                and_(
                    Asignacion.tenant_id == self._tenant_id,
                    Asignacion.deleted_at.is_(None),
                    Asignacion.materia_id == materia_id,
                    Asignacion.carrera_id == carrera_id,
                    Asignacion.cohorte_id == cohorte_id,
                )
            )
            .values(**valores)
            .execution_options(synchronize_session="fetch")
        )
        result = await self._session.execute(stmt)
        return result.rowcount
