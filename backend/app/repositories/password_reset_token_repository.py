"""Repository para la entidad PasswordResetToken.

Gestiona la persistencia de tokens de recuperación de contraseña.

Operaciones clave:
  - create_token: persiste un nuevo token de reset (solo el hash)
  - find_valid_by_hash: busca un token válido (no usado, no expirado)
  - mark_used: marca el token como usado (un solo uso)

Regla: un token de reset solo puede usarse una vez. Una vez marcado como
usado, find_valid_by_hash retorna None aunque el token exista en DB.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.password_reset_token import PasswordResetToken


class PasswordResetTokenRepository:
    """Repository para PasswordResetToken con filtro de tenant explícito."""

    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def create_token(
        self,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> PasswordResetToken:
        """Persiste un nuevo token de recuperación.

        Args:
            user_id: UUID del usuario propietario.
            token_hash: SHA-256 del token crudo.
            expires_at: Timestamp UTC de expiración (máx 1h).

        Returns:
            PasswordResetToken persistido.
        """
        prt = PasswordResetToken(
            user_id=user_id,
            tenant_id=self._tenant_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self._session.add(prt)
        await self._session.flush()
        await self._session.refresh(prt)
        return prt

    async def find_valid_by_hash(self, token_hash: str) -> PasswordResetToken | None:
        """Busca un token válido (no usado, no expirado) por su hash.

        Args:
            token_hash: SHA-256 del token a buscar.

        Returns:
            PasswordResetToken si existe, es válido y pertenece al tenant.
            None si no existe, ya fue usado, o expiró.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            select(PasswordResetToken)
            .where(PasswordResetToken.token_hash == token_hash)
            .where(PasswordResetToken.tenant_id == self._tenant_id)
            .where(PasswordResetToken.used_at.is_(None))
            .where(PasswordResetToken.expires_at > now)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_used(self, token_hash: str) -> bool:
        """Marca un token como usado (un solo uso).

        Args:
            token_hash: SHA-256 del token a marcar.

        Returns:
            True si el token existía y fue marcado.
            False si no existía o no pertenece al tenant.
        """
        prt = await self.find_valid_by_hash(token_hash)
        if prt is None:
            return False

        prt.used_at = datetime.now(timezone.utc)
        self._session.add(prt)
        await self._session.flush()
        return True
