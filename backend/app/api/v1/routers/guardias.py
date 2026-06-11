"""Router de guardias de atención (C-13).

Endpoints:
  POST   /guardias           → registrar guardia (TUTOR — asignacion_id del JWT)
  GET    /guardias           → listar (TUTOR: propias; COORD/ADMIN: todas del tenant)
  GET    /guardias/exportar  → export CSV (F6.6)

Regla #8: identidad SIEMPRE del JWT.
Regla #11: Router → Repository → Models.
D-04: scope resuelto por is_own_resource del permiso efectivo.
"""

import csv
import io
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.models.guardia import Guardia
from app.repositories.guardia_repository import GuardiaRepository
from app.schemas.guardias import GuardiaCreate, GuardiaResponse

router = APIRouter(prefix="/api/v1/guardias", tags=["guardias"])

_PERM_GESTIONAR = Depends(require_permission("encuentros:gestionar"))
# guardias:registrar discrimina TUTOR (is_own=True) vs COORD/ADMIN (is_own=False)
_PERM_REGISTRAR = Depends(require_permission("guardias:registrar"))


def _guardia_to_dict(g: Guardia) -> dict:
    return {
        "id": str(g.id),
        "tenant_id": str(g.tenant_id),
        "asignacion_id": str(g.asignacion_id),
        "materia_id": str(g.materia_id),
        "carrera_id": str(g.carrera_id),
        "cohorte_id": str(g.cohorte_id),
        "dia": g.dia,
        "horario": g.horario,
        "estado": g.estado,
        "comentarios": g.comentarios,
        "created_at": g.created_at,
    }


# ---------------------------------------------------------------------------
# POST /guardias — F6.6 registrar guardia
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED, response_model=GuardiaResponse)
async def crear_guardia(
    payload: GuardiaCreate,
    request: Request,
    _: None = _PERM_GESTIONAR,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GuardiaResponse:
    """Registra una guardia. El asignacion_id se resuelve del JWT."""
    from app.repositories.asignacion_repository import AsignacionRepository

    asig_repo = AsignacionRepository(db, tenant_id=current_user.tenant_id)
    asignaciones = await asig_repo.list_filtrado(
        usuario_id=current_user.id,
        materia_id=payload.materia_id,
    )
    if not asignaciones:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró asignación vigente para el usuario en la materia indicada",
        )
    asignacion_id = asignaciones[0].id

    guardia = Guardia(
        asignacion_id=asignacion_id,
        materia_id=payload.materia_id,
        carrera_id=payload.carrera_id,
        cohorte_id=payload.cohorte_id,
        dia=payload.dia,
        horario=payload.horario,
        estado=payload.estado,
        comentarios=payload.comentarios,
    )
    repo = GuardiaRepository(db, tenant_id=current_user.tenant_id)
    guardia = await repo.create(guardia)
    await db.commit()
    await db.refresh(guardia)
    return GuardiaResponse(**_guardia_to_dict(guardia))


# ---------------------------------------------------------------------------
# GET /guardias/exportar — F6.6 export CSV
# ---------------------------------------------------------------------------


@router.get("/exportar")
async def exportar_guardias(
    request: Request,
    _: None = _PERM_REGISTRAR,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Exporta guardias del tenant a CSV. Solo COORD/ADMIN."""
    is_own = getattr(request.state, "permission_is_own_resource", True)
    repo = GuardiaRepository(db, tenant_id=current_user.tenant_id)

    if is_own:
        from app.repositories.asignacion_repository import AsignacionRepository
        asig_repo = AsignacionRepository(db, tenant_id=current_user.tenant_id)
        asignaciones = await asig_repo.list_filtrado(usuario_id=current_user.id)
        asig_id = asignaciones[0].id if asignaciones else None
        items = await repo.list_filtrado(solo_tenant=False, asignacion_id=asig_id)
    else:
        items = await repo.list_filtrado(solo_tenant=True)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "asignacion_id", "materia_id", "carrera_id", "cohorte_id",
                     "dia", "horario", "estado", "comentarios"])
    for g in items:
        writer.writerow([
            str(g.id), str(g.asignacion_id), str(g.materia_id),
            str(g.carrera_id), str(g.cohorte_id),
            g.dia, g.horario, g.estado, g.comentarios or "",
        ])

    output.seek(0)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=guardias_{ts}.csv"},
    )


# ---------------------------------------------------------------------------
# GET /guardias — listar (scope por rol via is_own_resource)
# ---------------------------------------------------------------------------


@router.get("", response_model=list[GuardiaResponse])
async def listar_guardias(
    request: Request,
    materia_id: UUID | None = Query(default=None),
    estado: str | None = Query(default=None),
    _: None = _PERM_REGISTRAR,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[GuardiaResponse]:
    """Lista guardias. TUTOR: solo las suyas. COORD/ADMIN: todas del tenant."""
    is_own = getattr(request.state, "permission_is_own_resource", True)
    repo = GuardiaRepository(db, tenant_id=current_user.tenant_id)

    if is_own:
        # TUTOR: filtrar por su asignacion_id
        from app.repositories.asignacion_repository import AsignacionRepository
        asig_repo = AsignacionRepository(db, tenant_id=current_user.tenant_id)
        asignaciones = await asig_repo.list_filtrado(usuario_id=current_user.id, materia_id=materia_id)
        if not asignaciones:
            return []
        asig_id = asignaciones[0].id
        items = await repo.list_filtrado(
            materia_id=materia_id,
            estado=estado,
            asignacion_id=asig_id,
            solo_tenant=False,
        )
    else:
        # COORD/ADMIN: todas del tenant
        items = await repo.list_filtrado(
            materia_id=materia_id,
            estado=estado,
            solo_tenant=True,
        )

    return [GuardiaResponse(**_guardia_to_dict(g)) for g in items]
