"""Repository para SalarioBase y SalarioPlus (C-18 liquidaciones).

Extiende BaseRepository con queries de vigencia temporal:
  - get_vigente_base: retorna el SalarioBase vigente al primer día del período
  - get_vigente_plus: retorna el SalarioPlus vigente al primer día del período
  - list_base: lista salarios base del tenant con filtros opcionales
  - list_plus: lista salarios plus del tenant con filtros opcionales

Regla dura #9: TODOS los queries filtran por tenant_id.
Vigencia: se toma el registro con mayor `desde` que sea <= primer_día_período
y cuyo `hasta` sea NULL o >= primer_día_período.
"""

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.salario import SalarioBase, SalarioPlus
from app.repositories.base import BaseRepository


def _primer_dia(periodo: str) -> date:
    """Parsea 'AAAA-MM' y retorna el primer día del mes."""
    year, month = int(periodo[:4]), int(periodo[5:7])
    return date(year, month, 1)


class SalarioRepository:
    """Repository para SalarioBase y SalarioPlus con scope de tenant."""

    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._base_repo = BaseRepository(session, tenant_id=tenant_id, model=SalarioBase)
        self._plus_repo = BaseRepository(session, tenant_id=tenant_id, model=SalarioPlus)

    # ------------------------------------------------------------------
    # SalarioBase
    # ------------------------------------------------------------------

    async def get_vigente_base(self, rol: str, periodo: str) -> SalarioBase | None:
        """Retorna el SalarioBase vigente al primer día del período para el rol dado.

        Vigencia: desde <= primer_día AND (hasta IS NULL OR hasta >= primer_día).
        Si hay varios, retorna el de mayor `desde` (el más reciente).
        """
        primer_dia = _primer_dia(periodo)
        stmt = (
            select(SalarioBase)
            .where(SalarioBase.tenant_id == self._tenant_id)
            .where(SalarioBase.deleted_at.is_(None))
            .where(SalarioBase.rol == rol)
            .where(SalarioBase.desde <= primer_dia)
            .where(
                (SalarioBase.hasta.is_(None)) | (SalarioBase.hasta >= primer_dia)
            )
            .order_by(SalarioBase.desde.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_base(
        self,
        *,
        rol: str | None = None,
        solo_vigentes: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> list[SalarioBase]:
        """Lista salarios base con filtros opcionales."""
        hoy = date.today()
        stmt = (
            select(SalarioBase)
            .where(SalarioBase.tenant_id == self._tenant_id)
            .where(SalarioBase.deleted_at.is_(None))
        )
        if rol:
            stmt = stmt.where(SalarioBase.rol == rol)
        if solo_vigentes:
            stmt = stmt.where(SalarioBase.desde <= hoy).where(
                (SalarioBase.hasta.is_(None)) | (SalarioBase.hasta >= hoy)
            )
        stmt = stmt.order_by(SalarioBase.desde.desc()).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create_base(self, obj: SalarioBase) -> SalarioBase:
        """Persiste un nuevo SalarioBase inyectando tenant_id."""
        obj.tenant_id = self._tenant_id
        self._session.add(obj)
        await self._session.flush()
        await self._session.refresh(obj)
        return obj

    async def get_base_by_id(self, id: UUID) -> SalarioBase | None:
        """Retorna SalarioBase por id dentro del tenant."""
        return await self._base_repo.get_by_id(id)

    async def update_base(self, obj: SalarioBase) -> SalarioBase:
        """Actualiza un SalarioBase existente."""
        return await self._base_repo.update(obj)

    # ------------------------------------------------------------------
    # SalarioPlus
    # ------------------------------------------------------------------

    async def get_vigente_plus(
        self, grupo: str, rol: str, periodo: str
    ) -> SalarioPlus | None:
        """Retorna el SalarioPlus vigente al primer día del período.

        Vigencia: desde <= primer_día AND (hasta IS NULL OR hasta >= primer_día).
        Más reciente primero.
        """
        primer_dia = _primer_dia(periodo)
        stmt = (
            select(SalarioPlus)
            .where(SalarioPlus.tenant_id == self._tenant_id)
            .where(SalarioPlus.deleted_at.is_(None))
            .where(SalarioPlus.grupo == grupo)
            .where(SalarioPlus.rol == rol)
            .where(SalarioPlus.desde <= primer_dia)
            .where(
                (SalarioPlus.hasta.is_(None)) | (SalarioPlus.hasta >= primer_dia)
            )
            .order_by(SalarioPlus.desde.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_plus(
        self,
        *,
        grupo: str | None = None,
        rol: str | None = None,
        solo_vigentes: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> list[SalarioPlus]:
        """Lista salarios plus con filtros opcionales."""
        hoy = date.today()
        stmt = (
            select(SalarioPlus)
            .where(SalarioPlus.tenant_id == self._tenant_id)
            .where(SalarioPlus.deleted_at.is_(None))
        )
        if grupo:
            stmt = stmt.where(SalarioPlus.grupo == grupo)
        if rol:
            stmt = stmt.where(SalarioPlus.rol == rol)
        if solo_vigentes:
            stmt = stmt.where(SalarioPlus.desde <= hoy).where(
                (SalarioPlus.hasta.is_(None)) | (SalarioPlus.hasta >= hoy)
            )
        stmt = stmt.order_by(SalarioPlus.desde.desc()).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create_plus(self, obj: SalarioPlus) -> SalarioPlus:
        """Persiste un nuevo SalarioPlus inyectando tenant_id."""
        obj.tenant_id = self._tenant_id
        self._session.add(obj)
        await self._session.flush()
        await self._session.refresh(obj)
        return obj

    async def get_plus_by_id(self, id: UUID) -> SalarioPlus | None:
        """Retorna SalarioPlus por id dentro del tenant."""
        return await self._plus_repo.get_by_id(id)

    async def update_plus(self, obj: SalarioPlus) -> SalarioPlus:
        """Actualiza un SalarioPlus existente."""
        return await self._plus_repo.update(obj)
