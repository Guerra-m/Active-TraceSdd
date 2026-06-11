"""Servicio de avisos: resolución de contexto del usuario para filtrado (C-15)."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.aviso_repository import AvisoRepository
from app.models.aviso import Aviso


async def get_user_context(session: AsyncSession, *, user_id: UUID, tenant_id: UUID) -> dict:
    """Resuelve roles, materia_ids y cohorte_ids del usuario para el filtrado de avisos."""
    from sqlalchemy import select
    from app.models.usuario_rol import UsuarioRol
    from app.models.rol import Rol
    from app.models.asignacion import Asignacion

    # Roles del usuario en este tenant
    stmt_roles = (
        select(Rol.code)
        .join(UsuarioRol, UsuarioRol.rol_id == Rol.id)
        .where(UsuarioRol.tenant_id == tenant_id)
        .where(UsuarioRol.user_id == user_id)
        .where(UsuarioRol.deleted_at.is_(None))
    )
    result = await session.execute(stmt_roles)
    roles = [row[0] for row in result.fetchall()]

    # Asignaciones activas: materia_ids y cohorte_ids
    stmt_asig = (
        select(Asignacion.materia_id, Asignacion.cohorte_id)
        .where(Asignacion.tenant_id == tenant_id)
        .where(Asignacion.usuario_id == user_id)
        .where(Asignacion.deleted_at.is_(None))
    )
    result_asig = await session.execute(stmt_asig)
    rows = result_asig.fetchall()
    materia_ids = list({r[0] for r in rows if r[0] is not None})
    cohorte_ids = list({r[1] for r in rows if r[1] is not None})

    return {"roles": roles, "materia_ids": materia_ids, "cohorte_ids": cohorte_ids}


async def get_avisos_para_usuario(
    session: AsyncSession,
    *,
    user_id: UUID,
    tenant_id: UUID,
    now: datetime | None = None,
) -> list[Aviso]:
    """Retorna los avisos visibles para el usuario, aplicando scope y vigencia."""
    ctx = await get_user_context(session, user_id=user_id, tenant_id=tenant_id)
    repo = AvisoRepository(session, tenant_id=tenant_id)
    return await repo.list_visibles_para_usuario(
        user_id=user_id,
        roles=ctx["roles"],
        materia_ids=ctx["materia_ids"],
        cohorte_ids=ctx["cohorte_ids"],
        now=now,
    )
