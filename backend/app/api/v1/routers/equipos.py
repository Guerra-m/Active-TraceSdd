"""Router de equipos docentes (C-08).

Endpoints:
  GET    /equipos/mis-equipos          → asignaciones del usuario autenticado (JWT)
  GET    /equipos                      → listado global con filtros (COORD/ADMIN)
  GET    /equipos/buscar-docentes      → autocompletado de usuarios por nombre
  POST   /equipos/masiva               → asignación masiva (N docentes × contexto)
  POST   /equipos/clonar               → clonar equipo entre cohortes (RN-12)
  PATCH  /equipos/vigencia             → modificar vigencia en bloque (F4.6)
  GET    /equipos/exportar             → export CSV descargable (F4.7)

Regla #8: identidad SIEMPRE del JWT — nunca de parámetros.
Regla #11: Router → Repository → Models (sin lógica en el router más allá de
           validación de entradas y despacho al repository).
"""

import csv
import io
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import ASIGNACION_MODIFICAR, audit
from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.encryption import decrypt
from app.models.asignacion import Asignacion
from app.repositories.asignacion_repository import AsignacionRepository
from app.repositories.carrera_repository import CarreraRepository
from app.repositories.cohorte_repository import CohorteRepository
from app.repositories.materia_repository import MateriaRepository
from app.repositories.user_repository import UserRepository
from app.schemas.asignaciones import AsignacionResponse
from app.schemas.equipos import (
    AsignacionMasivaRequest,
    AsignacionMasivaResponse,
    BuscarDocenteItem,
    ClonarEquipoRequest,
    ClonarEquipoResponse,
    VigenciaMasivaRequest,
    VigenciaMasivaResponse,
)

router = APIRouter(prefix="/api/v1/equipos", tags=["equipos"])

_PERM = Depends(require_permission("equipos:asignar"))


def _asignacion_to_dict(a: Asignacion) -> dict:
    return {
        "id": str(a.id),
        "tenant_id": str(a.tenant_id),
        "usuario_id": str(a.usuario_id),
        "rol": a.rol,
        "materia_id": str(a.materia_id) if a.materia_id else None,
        "carrera_id": str(a.carrera_id) if a.carrera_id else None,
        "cohorte_id": str(a.cohorte_id) if a.cohorte_id else None,
        "comisiones": a.comisiones or [],
        "responsable_id": str(a.responsable_id) if a.responsable_id else None,
        "desde": str(a.desde) if a.desde else None,
        "hasta": str(a.hasta) if a.hasta else None,
        "estado_vigencia": a.estado_vigencia,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
    }


# ---------------------------------------------------------------------------
# GET /equipos/mis-equipos — F4.2
# ---------------------------------------------------------------------------


@router.get("/mis-equipos", response_model=list[AsignacionResponse])
async def mis_equipos(
    materia_id: UUID | None = Query(default=None),
    carrera_id: UUID | None = Query(default=None),
    cohorte_id: UUID | None = Query(default=None),
    estado_vigencia: str | None = Query(default=None),
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AsignacionResponse]:
    """Devuelve las asignaciones del usuario autenticado. Identidad del JWT."""
    repo = AsignacionRepository(db, tenant_id=current_user.tenant_id)
    items = await repo.list_filtrado(
        usuario_id=current_user.id,
        materia_id=materia_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
    )
    if estado_vigencia is not None:
        items = [a for a in items if a.estado_vigencia == estado_vigencia]
    return [AsignacionResponse(**_asignacion_to_dict(a)) for a in items]


# ---------------------------------------------------------------------------
# GET /equipos — F4.3 listado global
# ---------------------------------------------------------------------------


@router.get("", response_model=list[AsignacionResponse])
async def list_equipos(
    materia_id: UUID | None = Query(default=None),
    carrera_id: UUID | None = Query(default=None),
    cohorte_id: UUID | None = Query(default=None),
    rol: str | None = Query(default=None),
    estado_vigencia: str | None = Query(default=None),
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AsignacionResponse]:
    """Listado global de asignaciones del tenant con filtros."""
    repo = AsignacionRepository(db, tenant_id=current_user.tenant_id)
    items = await repo.list_equipo(
        materia_id=materia_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
        rol=rol,
        estado_vigencia=estado_vigencia,
    )
    return [AsignacionResponse(**_asignacion_to_dict(a)) for a in items]


# ---------------------------------------------------------------------------
# GET /equipos/buscar-docentes — RN-30 autocompletado
# ---------------------------------------------------------------------------


@router.get("/buscar-docentes", response_model=list[BuscarDocenteItem])
async def buscar_docentes(
    q: str = Query(..., min_length=2, description="Término de búsqueda (mín. 2 caracteres)"),
    limit: int = Query(default=10, le=50),
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[BuscarDocenteItem]:
    """Autocompletado de usuarios por nombre/apellidos."""
    repo = UserRepository(db, tenant_id=current_user.tenant_id)
    users = await repo.search_by_name(q, limit=limit)
    return [BuscarDocenteItem(id=u.id, nombre=u.nombre, apellidos=u.apellidos) for u in users]


# ---------------------------------------------------------------------------
# POST /equipos/masiva — F4.4 asignación masiva
# ---------------------------------------------------------------------------


@router.post("/masiva", response_model=AsignacionMasivaResponse, status_code=status.HTTP_201_CREATED)
async def asignacion_masiva(
    payload: AsignacionMasivaRequest,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AsignacionMasivaResponse:
    """Asigna N docentes en bloque a un contexto académico."""
    user_repo = UserRepository(db, tenant_id=current_user.tenant_id)
    for uid in payload.usuario_ids:
        if await user_repo.get_by_id(uid) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Usuario {uid} no encontrado en el tenant")

    now = datetime.now(timezone.utc)
    nuevas = [
        Asignacion(
            usuario_id=uid,
            rol=payload.rol,
            materia_id=payload.materia_id,
            carrera_id=payload.carrera_id,
            cohorte_id=payload.cohorte_id,
            comisiones=payload.comisiones,
            responsable_id=payload.responsable_id,
            desde=payload.desde,
            hasta=payload.hasta,
            created_at=now,
            updated_at=now,
        )
        for uid in payload.usuario_ids
    ]

    repo = AsignacionRepository(db, tenant_id=current_user.tenant_id)
    creadas = await repo.bulk_create(nuevas)
    await db.commit()

    await audit(db, current_user.id, current_user.tenant_id, ASIGNACION_MODIFICAR,
                filas_afectadas=len(creadas))
    await db.commit()

    return AsignacionMasivaResponse(
        creadas=len(creadas),
        asignaciones=[_asignacion_to_dict(a) for a in creadas],
    )


# ---------------------------------------------------------------------------
# POST /equipos/clonar — F4.5 / RN-12
# ---------------------------------------------------------------------------


@router.post("/clonar", response_model=ClonarEquipoResponse, status_code=status.HTTP_201_CREATED)
async def clonar_equipo(
    payload: ClonarEquipoRequest,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ClonarEquipoResponse:
    """Clona asignaciones vigentes de una cohorte origen a una destino (RN-12)."""
    coh_repo = CohorteRepository(db, tenant_id=current_user.tenant_id)
    if await coh_repo.get_by_id(payload.cohorte_destino_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cohorte destino no encontrada")

    repo = AsignacionRepository(db, tenant_id=current_user.tenant_id)
    creadas, conflictos = await repo.clone_equipo(
        materia_id=payload.materia_id,
        carrera_id=payload.carrera_id,
        cohorte_origen_id=payload.cohorte_origen_id,
        cohorte_destino_id=payload.cohorte_destino_id,
        desde=payload.desde,
        hasta=payload.hasta,
    )
    await db.commit()

    if creadas:
        await audit(db, current_user.id, current_user.tenant_id, ASIGNACION_MODIFICAR,
                    filas_afectadas=len(creadas))
        await db.commit()

    return ClonarEquipoResponse(
        creadas=len(creadas),
        conflictos=len(conflictos),
        asignaciones=[_asignacion_to_dict(a) for a in creadas],
        omitidos=conflictos,
    )


# ---------------------------------------------------------------------------
# PATCH /equipos/vigencia — F4.6
# ---------------------------------------------------------------------------


@router.patch("/vigencia", response_model=VigenciaMasivaResponse)
async def actualizar_vigencia_masiva(
    payload: VigenciaMasivaRequest,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VigenciaMasivaResponse:
    """Actualiza desde/hasta de todas las asignaciones activas del equipo."""
    repo = AsignacionRepository(db, tenant_id=current_user.tenant_id)
    count = await repo.bulk_update_vigencia(
        materia_id=payload.materia_id,
        carrera_id=payload.carrera_id,
        cohorte_id=payload.cohorte_id,
        desde=payload.desde,
        hasta=payload.hasta,
    )
    await db.commit()

    if count > 0:
        await audit(db, current_user.id, current_user.tenant_id, ASIGNACION_MODIFICAR,
                    filas_afectadas=count)
        await db.commit()

    return VigenciaMasivaResponse(filas_actualizadas=count)


# ---------------------------------------------------------------------------
# GET /equipos/exportar — F4.7 export CSV
# ---------------------------------------------------------------------------


def _csv_row(a: Asignacion, email_plain: str, materia_cod: str, carrera_cod: str, cohorte_nom: str, resp_email: str) -> list:
    return [
        str(a.id),
        email_plain,
        a.rol,
        materia_cod,
        carrera_cod,
        cohorte_nom,
        ",".join(a.comisiones or []),
        resp_email,
        str(a.desde) if a.desde else "",
        str(a.hasta) if a.hasta else "",
        a.estado_vigencia,
    ]


@router.get("/exportar")
async def exportar_equipo(
    materia_id: UUID | None = Query(default=None),
    carrera_id: UUID | None = Query(default=None),
    cohorte_id: UUID | None = Query(default=None),
    rol: str | None = Query(default=None),
    estado_vigencia: str | None = Query(default=None),
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Exporta el equipo a CSV con detalle de asignaciones."""
    repo = AsignacionRepository(db, tenant_id=current_user.tenant_id)
    items = await repo.list_equipo(
        materia_id=materia_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
        rol=rol,
        estado_vigencia=estado_vigencia,
    )

    user_repo = UserRepository(db, tenant_id=current_user.tenant_id)
    mat_repo = MateriaRepository(db, tenant_id=current_user.tenant_id)
    car_repo = CarreraRepository(db, tenant_id=current_user.tenant_id)
    coh_repo = CohorteRepository(db, tenant_id=current_user.tenant_id)

    output = io.StringIO()
    writer = csv.writer(output)
    _HEADERS = ["id", "usuario_email", "rol", "materia_codigo", "carrera_codigo",
                "cohorte_nombre", "comisiones", "responsable_email", "desde", "hasta", "estado_vigencia"]
    writer.writerow(_HEADERS)

    for a in items:
        u = await user_repo.get_by_id(a.usuario_id)
        email = decrypt(u.email_encrypted) if u and u.email_encrypted else ""

        mat = await mat_repo.get_by_id(a.materia_id) if a.materia_id else None
        car = await car_repo.get_by_id(a.carrera_id) if a.carrera_id else None
        coh = await coh_repo.get_by_id(a.cohorte_id) if a.cohorte_id else None
        resp_u = await user_repo.get_by_id(a.responsable_id) if a.responsable_id else None
        resp_email = decrypt(resp_u.email_encrypted) if resp_u and resp_u.email_encrypted else ""

        writer.writerow(_csv_row(
            a, email,
            mat.codigo if mat else "",
            car.codigo if car else "",
            coh.nombre if coh else "",
            resp_email,
        ))

    output.seek(0)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=equipo_{ts}.csv"},
    )
