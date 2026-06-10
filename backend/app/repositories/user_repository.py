"""Repository para la entidad User.

Extiende BaseRepository[User] con operaciones específicas de auth y perfil:
  - find_by_email_hash: lookup por hash SHA-256 del email (O(1) por índice único)
  - create_user: crea usuario de auth (solo credenciales)
  - create_usuario: crea usuario con perfil docente completo (cifra PII)
  - update_perfil: actualiza campos de perfil (cifra PII donde corresponde)

El email se cifra con AES-256-GCM antes de persistir.
Las búsquedas usan el hash determinístico (no el email en texto plano).
Los campos PII (dni, cuil, cbu, alias_cbu) se cifran con AES-256-GCM — nunca texto plano en DB.

Regla dura #9: todos los queries filtran por tenant_id (heredado de BaseRepository).
Regla dura #12: email/PII cifrado — nunca texto plano en DB.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import encrypt
from app.core.security import hash_email, hash_password
from app.models.user import User
from app.repositories.base import BaseRepository

_UNSET = object()


class UserRepository(BaseRepository[User]):
    """Repository de User con scope de tenant obligatorio."""

    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        super().__init__(session, tenant_id=tenant_id, model=User)

    async def find_by_email_hash(self, email: str) -> User | None:
        """Busca un usuario activo por su email (usando el hash)."""
        email_hash = hash_email(email)
        stmt = self._base_query().where(User.email_hash == email_hash)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_email_hash_raw(self, email_hash: str) -> User | None:
        """Busca por hash precomputado (para reutilizar el hash ya calculado)."""
        stmt = self._base_query().where(User.email_hash == email_hash)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(
        self,
        email: str,
        password_plaintext: str,
        is_active: bool = True,
    ) -> User:
        """Crea usuario de autenticación (solo credenciales, sin perfil docente)."""
        user = User(
            email_encrypted=encrypt(email),
            email_hash=hash_email(email),
            password_hash=hash_password(password_plaintext),
            is_active=is_active,
        )
        return await self.create(user)

    async def create_usuario(
        self,
        email: str,
        password_plaintext: str,
        *,
        nombre: str | None = None,
        apellidos: str | None = None,
        dni: str | None = None,
        cuil: str | None = None,
        cbu: str | None = None,
        alias_cbu: str | None = None,
        banco: str | None = None,
        regional: str | None = None,
        legajo: str | None = None,
        legajo_profesional: str | None = None,
        facturador: bool = False,
        estado: str = "Activo",
    ) -> User:
        """Crea usuario con perfil docente completo. Cifra PII antes de persistir."""
        user = User(
            email_encrypted=encrypt(email),
            email_hash=hash_email(email),
            password_hash=hash_password(password_plaintext),
            nombre=nombre,
            apellidos=apellidos,
            dni_encrypted=encrypt(dni) if dni else None,
            cuil_encrypted=encrypt(cuil) if cuil else None,
            cbu_encrypted=encrypt(cbu) if cbu else None,
            alias_cbu_encrypted=encrypt(alias_cbu) if alias_cbu else None,
            banco=banco,
            regional=regional,
            legajo=legajo,
            legajo_profesional=legajo_profesional,
            facturador=facturador,
            estado=estado,
        )
        return await self.create(user)

    async def update_perfil(
        self,
        user_id: UUID,
        campos: dict,
    ) -> User | None:
        """Actualiza campos de perfil docente. Cifra PII donde corresponde.

        Args:
            user_id: UUID del usuario a actualizar.
            campos: Dict con los campos a actualizar (solo los provistos).
                    Los campos PII (dni, cuil, cbu, alias_cbu) se cifran automáticamente.

        Returns:
            User actualizado, o None si no existe en el tenant.
        """
        user = await self.get_by_id(user_id)
        if user is None:
            return None

        pii_fields = {"dni": "dni_encrypted", "cuil": "cuil_encrypted",
                      "cbu": "cbu_encrypted", "alias_cbu": "alias_cbu_encrypted"}

        for campo, valor in campos.items():
            if campo in pii_fields:
                encrypted_field = pii_fields[campo]
                setattr(user, encrypted_field, encrypt(valor) if valor else None)
            else:
                setattr(user, campo, valor)

        return await self.update(user)
