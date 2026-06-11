"""Router de encuentros sincrónicos (C-13).

Endpoints:
  POST   /encuentros/slots          → crear slot recurrente o único (RN-13)
  GET    /encuentros/slots          → listar slots del tenant con filtros
  GET    /encuentros                → listar instancias con filtros
  GET    /encuentros/{id}           → obtener instancia por id
  PATCH  /encuentros/{id}           → editar instancia individual (RN-14)
  GET    /encuentros/aula-virtual   → bloque HTML para LMS (F6.4)
  GET    /encuentros/admin          → vista transversal COORD/ADMIN (F6.5)

Regla #8: identidad SIEMPRE del JWT.
Regla #11: Router → Service → Repository → Models.
"""

import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_permission
from app.models.instancia_encuentro import InstanciaEncuentro
from app.repositories.instancia_encuentro_repository import InstanciaEncuentroRepository
from app.repositories.slot_encuentro_repository import SlotEncuentroRepository
from app.schemas.encuentros import (
    InstanciaEncuentroResponse,
    InstanciaEncuentroUpdate,
    SlotEncuentroCreate,
    SlotEncuentroResponse,
)
from app.services.encuentro_service import EncuentroService

router = APIRouter(prefix="/api/v1/encuentros", tags=["encuentros"])

_PERM = Depends(require_permission("encuentros:gestionar"))


def _slot_to_dict(s) -> dict:
    return {
        "id": str(s.id),
        "tenant_id": str(s.tenant_id),
        "asignacion_id": str(s.asignacion_id),
        "materia_id": str(s.materia_id),
        "titulo": s.titulo,
        "hora": s.hora.isoformat() if s.hora else None,
        "dia_semana": s.dia_semana,
        "fecha_inicio": s.fecha_inicio.isoformat() if s.fecha_inicio else None,
        "cant_semanas": s.cant_semanas,
        "fecha_unica": s.fecha_unica.isoformat() if s.fecha_unica else None,
        "meet_url": s.meet_url,
        "vig_desde": s.vig_desde.isoformat() if s.vig_desde else None,
        "vig_hasta": s.vig_hasta.isoformat() if s.vig_hasta else None,
    }


def _inst_to_dict(i) -> dict:
    return {
        "id": str(i.id),
        "tenant_id": str(i.tenant_id),
        "slot_id": str(i.slot_id) if i.slot_id else None,
        "materia_id": str(i.materia_id),
        "fecha": i.fecha.isoformat() if i.fecha else None,
        "hora": i.hora.isoformat() if i.hora else None,
        "titulo": i.titulo,
        "estado": i.estado,
        "meet_url": i.meet_url,
        "video_url": i.video_url,
        "comentario": i.comentario,
    }


# ---------------------------------------------------------------------------
# POST /encuentros/slots — RN-13 crear slot + instancias
# ---------------------------------------------------------------------------


@router.post("/slots", status_code=status.HTTP_201_CREATED)
async def crear_slot(
    payload: SlotEncuentroCreate,
    request: Request,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Crea slot recurrente o único y genera instancias automáticamente."""
    from app.repositories.asignacion_repository import AsignacionRepository

    asig_repo = AsignacionRepository(db, tenant_id=current_user.tenant_id)
    asignaciones = await asig_repo.list_filtrado(
        usuario_id=current_user.id,
        materia_id=payload.materia_id,
    )
    asignacion_id = asignaciones[0].id if asignaciones else current_user.id

    slot, instancias = await EncuentroService.crear_slot(
        payload,
        db,
        tenant_id=current_user.tenant_id,
        asignacion_id=asignacion_id,
    )
    await db.commit()
    for inst in instancias:
        await db.refresh(inst)
    if slot:
        await db.refresh(slot)

    return {
        "slot": _slot_to_dict(slot) if slot else None,
        "instancias": [_inst_to_dict(i) for i in instancias],
    }


# ---------------------------------------------------------------------------
# GET /encuentros/slots — listar slots con filtros
# ---------------------------------------------------------------------------


@router.get("/slots", response_model=list[SlotEncuentroResponse])
async def listar_slots(
    materia_id: UUID | None = Query(default=None),
    asignacion_id: UUID | None = Query(default=None),
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SlotEncuentroResponse]:
    repo = SlotEncuentroRepository(db, tenant_id=current_user.tenant_id)
    items = await repo.list_filtrado(
        materia_id=materia_id,
        asignacion_id=asignacion_id,
    )
    return [SlotEncuentroResponse(**_slot_to_dict(s)) for s in items]


# ---------------------------------------------------------------------------
# GET /encuentros/aula-virtual — F6.4 bloque HTML (orden antes de /{id})
# ---------------------------------------------------------------------------


@router.get("/aula-virtual")
async def aula_virtual(
    materia_id: UUID | None = Query(default=None),
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Genera bloque HTML con encuentros no cancelados, ordenados por fecha ASC."""
    repo = InstanciaEncuentroRepository(db, tenant_id=current_user.tenant_id)
    items = await repo.list_para_html(materia_id=materia_id)

    items_html = []
    for inst in items:
        meet_link = f' <a href="{inst.meet_url}">Unirse</a>' if inst.meet_url else ""
        video_link = f' <a href="{inst.video_url}">Ver grabación</a>' if inst.video_url else ""
        items_html.append(
            f"<li>{inst.fecha} {inst.hora.strftime('%H:%M')} — {inst.titulo}{meet_link}{video_link}</li>"
        )

    html = f"<ul>{''.join(items_html)}</ul>"
    return Response(content=html, media_type="text/html")


# ---------------------------------------------------------------------------
# GET /encuentros/admin — F6.5 vista transversal COORD/ADMIN
# ---------------------------------------------------------------------------


@router.get("/admin")
async def admin_view(
    materia_id: UUID | None = Query(default=None),
    estado: str | None = Query(default=None),
    fecha_desde: datetime.date | None = Query(default=None),
    fecha_hasta: datetime.date | None = Query(default=None),
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Vista transversal de todas las instancias del tenant (COORD/ADMIN)."""
    repo = InstanciaEncuentroRepository(db, tenant_id=current_user.tenant_id)
    items = await repo.list_filtrado(
        materia_id=materia_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    return [_inst_to_dict(i) for i in items]


# ---------------------------------------------------------------------------
# GET /encuentros — listar instancias con filtros
# ---------------------------------------------------------------------------


@router.get("", response_model=list[InstanciaEncuentroResponse])
async def listar_instancias(
    materia_id: UUID | None = Query(default=None),
    estado: str | None = Query(default=None),
    fecha_desde: datetime.date | None = Query(default=None),
    fecha_hasta: datetime.date | None = Query(default=None),
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[InstanciaEncuentroResponse]:
    repo = InstanciaEncuentroRepository(db, tenant_id=current_user.tenant_id)
    items = await repo.list_filtrado(
        materia_id=materia_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    return [InstanciaEncuentroResponse(**_inst_to_dict(i)) for i in items]


# ---------------------------------------------------------------------------
# GET /encuentros/{id} — obtener instancia por id
# ---------------------------------------------------------------------------


@router.get("/{id}", response_model=InstanciaEncuentroResponse)
async def get_instancia(
    id: UUID,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InstanciaEncuentroResponse:
    repo = InstanciaEncuentroRepository(db, tenant_id=current_user.tenant_id)
    inst = await repo.get_by_id(id)
    if inst is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instancia no encontrada")
    return InstanciaEncuentroResponse(**_inst_to_dict(inst))


# ---------------------------------------------------------------------------
# PATCH /encuentros/{id} — RN-14 editar instancia individual
# ---------------------------------------------------------------------------


@router.patch("/{id}", response_model=InstanciaEncuentroResponse)
async def editar_instancia(
    id: UUID,
    payload: InstanciaEncuentroUpdate,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InstanciaEncuentroResponse:
    """Edita instancia individual; no afecta slot ni otras instancias (RN-14)."""
    repo = InstanciaEncuentroRepository(db, tenant_id=current_user.tenant_id)
    inst = await repo.get_by_id(id)
    if inst is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instancia no encontrada")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(inst, field, value)

    inst = await repo.update(inst)
    await db.commit()
    await db.refresh(inst)
    return InstanciaEncuentroResponse(**_inst_to_dict(inst))
