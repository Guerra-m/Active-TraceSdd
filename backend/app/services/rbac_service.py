"""Servicio de resolución de permisos RBAC.

RbacService resuelve los permisos efectivos de un usuario dado su tenant,
consultando DB en cada llamada (siempre server-side, sin cache cross-request).

Algoritmo (Decisión D4 + D5 del design):
  1. Obtener las asignaciones UsuarioRol vigentes del usuario (por fecha).
  2. Para cada rol vigente, obtener sus permisos (código + is_own_resource).
  3. Unir todos los permisos de todos los roles.
  4. Regla de prevalencia: si el mismo permiso_code aparece con
     is_own_resource=True en un rol y False en otro → resultado es False
     (acceso global prevalece sobre restricto).

Retorna: set[tuple[str, bool]] donde cada tupla es (permiso_code, is_own_resource).

El resultado del primer call se cachea en request.state para evitar queries
redundantes dentro del mismo request (ver core/permissions.py).

Flujo unidireccional (regla #11):
  require_permission (core/permissions.py)
    → RbacService.get_effective_permissions
      → UsuarioRolRepository.get_vigentes
      → RolPermisoRepository.get_permisos_for_rol
"""

from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.rol_permiso_repository import RolPermisoRepository
from app.repositories.usuario_rol_repository import UsuarioRolRepository


class RbacService:
    """Resolución de permisos efectivos para un usuario autenticado."""

    @staticmethod
    async def get_effective_permissions(
        user_id: UUID,
        tenant_id: UUID,
        db: AsyncSession,
        reference_date: date | None = None,
    ) -> set[tuple[str, bool]]:
        """Calcula el conjunto de permisos efectivos del usuario en el tenant.

        Args:
            user_id:        UUID del usuario autenticado.
            tenant_id:      UUID del tenant del usuario (del JWT).
            db:             AsyncSession de la request actual.
            reference_date: Fecha de referencia para vigencia (default: today).

        Returns:
            set de tuplas (permiso_code: str, is_own_resource: bool).
            Set vacío si el usuario no tiene roles vigentes.

        REGLA: identidad SIEMPRE del JWT (user_id, tenant_id del caller).
        NUNCA se deriva identidad de parámetros del request.
        """
        if reference_date is None:
            reference_date = date.today()

        # 1. Obtener asignaciones vigentes del usuario en el tenant
        ur_repo = UsuarioRolRepository(db, tenant_id=tenant_id)
        asignaciones = await ur_repo.get_vigentes(user_id, reference_date)

        if not asignaciones:
            return set()

        # 2. Para cada rol vigente, obtener sus permisos
        rp_repo = RolPermisoRepository(db, tenant_id=tenant_id)

        # Mapa: permiso_code → is_own_resource acumulado
        # Regla D4.3: si el mismo code aparece con True y False → False prevalece
        perms_map: dict[str, bool] = {}

        for asignacion in asignaciones:
            rol_perms = await rp_repo.get_permisos_for_rol(asignacion.rol_id)
            for code, is_own in rol_perms:
                if code not in perms_map:
                    perms_map[code] = is_own
                else:
                    # Global (False) prevalece sobre propio (True)
                    perms_map[code] = perms_map[code] and is_own

        # 3. Convertir a set de tuplas
        return {(code, is_own) for code, is_own in perms_map.items()}
