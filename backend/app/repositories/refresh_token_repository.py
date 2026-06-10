"""Repository para la entidad RefreshToken.

Gestiona la persistencia y rotación de refresh tokens.

Operaciones clave:
  - create_token: persiste un nuevo refresh token (solo el hash)
  - find_by_hash: busca un token por su hash SHA-256
  - revoke: invalida un token (revoked_at = now)

Regla de rotación (design D2):
  Al usar un token → revocar el viejo antes de emitir el nuevo.
  Si el mismo token llega dos veces → ya está revocado → 401.

Nota: RefreshToken no hereda TenantScopedBase pero sí tiene tenant_id.
Los queries incluyen filtro de tenant manualmente.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    """Repository para RefreshToken con filtro de tenant explícito."""

    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def create_token(
        self,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshToken:
        """Persiste un nuevo refresh token.

        Args:
            user_id: UUID del usuario propietario.
            token_hash: SHA-256 del token crudo (nunca el valor original).
            expires_at: Timestamp UTC de expiración.

        Returns:
            RefreshToken persistido.
        """
        rt = RefreshToken(
            user_id=user_id,
            tenant_id=self._tenant_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self._session.add(rt)
        await self._session.flush()
        await self._session.refresh(rt)
        return rt

    async def find_by_hash(self, token_hash: str) -> RefreshToken | None:
        """Busca un refresh token por su hash SHA-256.

        Filtra por tenant_id para aislamiento multi-tenant.

        Args:
            token_hash: SHA-256 del token a buscar.

        Returns:
            RefreshToken si existe en el tenant, None en otro caso.
        """
        stmt = (
            select(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .where(RefreshToken.tenant_id == self._tenant_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke(self, token_hash: str) -> bool:
        """Revoca un refresh token (soft-revoke).

        Args:
            token_hash: SHA-256 del token a revocar.

        Returns:
            True si el token existía y fue revocado.
            False si no existía o no pertenece al tenant.
        """
        rt = await self.find_by_hash(token_hash)
        if rt is None:
            return False

        rt.revoked_at = datetime.now(timezone.utc)
        self._session.add(rt)
        await self._session.flush()
        return True
