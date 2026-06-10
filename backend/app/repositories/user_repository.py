"""Repository para la entidad User.

Extiende BaseRepository[User] con operaciones específicas de auth:
  - find_by_email_hash: lookup por hash SHA-256 del email (O(1) por índice único)
  - create_user: crea usuario con email_encrypted + email_hash en una operación

El email se cifra con AES-256-GCM antes de persistir.
Las búsquedas usan el hash determinístico (no el email en texto plano).

Regla dura #9: todos los queries filtran por tenant_id (heredado de BaseRepository).
Regla dura #12: email cifrado — nunca texto plano en DB.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import encrypt
from app.core.security import hash_email, hash_password
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository de User con scope de tenant obligatorio."""

    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        super().__init__(session, tenant_id=tenant_id, model=User)

    async def find_by_email_hash(self, email: str) -> User | None:
        """Busca un usuario activo por su email (usando el hash).

        El email se normaliza y hashea antes de la consulta.
        Retorna None si no existe o no pertenece al tenant.

        Args:
            email: Email en texto plano (se hashea internamente).

        Returns:
            User si existe y está activo en el tenant, None en otro caso.
        """
        email_hash = hash_email(email)
        stmt = (
            self._base_query()
            .where(User.email_hash == email_hash)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_email_hash_raw(self, email_hash: str) -> User | None:
        """Busca por hash precomputado (para reutilizar el hash ya calculado).

        Args:
            email_hash: SHA-256 hex del email normalizado.

        Returns:
            User si existe y está activo en el tenant, None en otro caso.
        """
        stmt = (
            self._base_query()
            .where(User.email_hash == email_hash)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(
        self,
        email: str,
        password_plaintext: str,
        is_active: bool = True,
    ) -> User:
        """Crea un nuevo usuario cifrado y hasheado.

        Centraliza el cifrado del email y el hash del password para
        garantizar que ningún código los maneje en texto plano.

        Args:
            email: Email en texto plano (se cifra y hashea internamente).
            password_plaintext: Password en texto plano (se hashea con Argon2id).
            is_active: Estado del usuario.

        Returns:
            User persistido con id y timestamps populados.
        """
        user = User(
            email_encrypted=encrypt(email),
            email_hash=hash_email(email),
            password_hash=hash_password(password_plaintext),
            is_active=is_active,
        )
        return await self.create(user)
