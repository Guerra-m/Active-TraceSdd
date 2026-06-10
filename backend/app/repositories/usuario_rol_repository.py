"""Repository para la entidad UsuarioRol.

Consulta las asignaciones de roles de un usuario, filtrando por vigencia.
La vigencia activa se define como:
  valid_from <= date <= valid_until  (o valid_until IS NULL = abierta)

Regla dura #9: todos los queries filtran por tenant_id.
"""

from datetime import date
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usuario_rol import UsuarioRol


class UsuarioRolRepository:
    """Repository de asignaciones usuario↔rol, con scope de tenant y vigencia."""

    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def get_vigentes(
        self,
        user_id: UUID,
        reference_date: date | None = None,
    ) -> list[UsuarioRol]:
        """Retorna las asignaciones vigentes del usuario en la fecha dada.

        Una asignación es vigente si:
          valid_from <= reference_date
          AND (valid_until IS NULL OR valid_until >= reference_date)

        Args:
            user_id:        UUID del usuario.
            reference_date: Fecha de referencia (default: today).

        Returns:
            Lista de UsuarioRol vigentes del usuario en el tenant.
        """
        if reference_date is None:
            reference_date = date.today()

        stmt = (
            select(UsuarioRol)
            .where(UsuarioRol.user_id == user_id)
            .where(UsuarioRol.tenant_id == self._tenant_id)
            .where(UsuarioRol.valid_from <= reference_date)
            .where(
                or_(
                    UsuarioRol.valid_until.is_(None),
                    UsuarioRol.valid_until >= reference_date,
                )
            )
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
