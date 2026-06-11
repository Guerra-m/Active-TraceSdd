"""Repository para Aviso y AcknowledgmentAviso (C-15)."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.aviso import AcknowledgmentAviso, Aviso
from app.repositories.base import BaseRepository


class AvisoRepository(BaseRepository[Aviso]):
    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        super().__init__(session, tenant_id=tenant_id, model=Aviso)

    async def list_visibles_para_usuario(
        self,
        *,
        user_id: UUID,
        roles: list[str],
        materia_ids: list[UUID],
        cohorte_ids: list[UUID],
        now: datetime | None = None,
    ) -> list[Aviso]:
        """Retorna avisos visibles para el usuario aplicando RN-18/19/20.

        Excluye avisos ya ack-eados cuando requiere_ack=True.
        """
        if now is None:
            now = datetime.now(timezone.utc)

        # Subquery: aviso_ids ya ack-eados por el usuario
        acked_sq = (
            select(AcknowledgmentAviso.aviso_id)
            .where(AcknowledgmentAviso.tenant_id == self._tenant_id)
            .where(AcknowledgmentAviso.deleted_at.is_(None))
            .where(AcknowledgmentAviso.usuario_id == user_id)
            .scalar_subquery()
        )

        # Filtros de scope (RN-20)
        scope_conditions = [Aviso.alcance == "Global"]
        if roles:
            scope_conditions.append(
                and_(Aviso.alcance == "PorRol", Aviso.rol_destino.in_(roles))
            )
        if materia_ids:
            scope_conditions.append(
                and_(Aviso.alcance == "PorMateria", Aviso.materia_id.in_(materia_ids))
            )
        if cohorte_ids:
            scope_conditions.append(
                and_(Aviso.alcance == "PorCohorte", Aviso.cohorte_id.in_(cohorte_ids))
            )

        stmt = (
            select(Aviso)
            .where(Aviso.tenant_id == self._tenant_id)
            .where(Aviso.deleted_at.is_(None))
            .where(Aviso.activo.is_(True))
            # RN-18: ventana de vigencia
            .where(Aviso.inicio_en <= now)
            .where(or_(Aviso.fin_en.is_(None), Aviso.fin_en >= now))
            # RN-20: scope
            .where(or_(*scope_conditions))
            # RN-19: excluir ack-eados (si requiere_ack)
            .where(
                or_(
                    Aviso.requiere_ack.is_(False),
                    Aviso.id.not_in(acked_sq),
                )
            )
            .order_by(Aviso.orden.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class AcknowledgmentRepository(BaseRepository[AcknowledgmentAviso]):
    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        super().__init__(session, tenant_id=tenant_id, model=AcknowledgmentAviso)

    async def get_by_aviso_usuario(self, *, aviso_id: UUID, usuario_id: UUID) -> AcknowledgmentAviso | None:
        stmt = (
            self._base_query()
            .where(AcknowledgmentAviso.aviso_id == aviso_id)
            .where(AcknowledgmentAviso.usuario_id == usuario_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_by_aviso(self, aviso_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(AcknowledgmentAviso)
            .where(AcknowledgmentAviso.tenant_id == self._tenant_id)
            .where(AcknowledgmentAviso.deleted_at.is_(None))
            .where(AcknowledgmentAviso.aviso_id == aviso_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()
