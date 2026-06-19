"""Router de calificaciones — importación desde LMS y configuración de umbral (C-10).

Endpoints:
  POST   /calificaciones/importar              → importar archivo LMS → 201
  DELETE /calificaciones/{asignacion_id}/{materia_id} → vaciar datos propios → 204
  GET    /calificaciones/umbral/{asignacion_id}/{materia_id} → obtener umbral
  PUT    /calificaciones/umbral/{asignacion_id}/{materia_id} → configurar umbral

PROFESOR con is_own_resource: solo puede operar sobre sus propias asignaciones.
COORDINADOR/ADMIN: acceso global dentro del tenant.

Flujo (regla #11): Router → Service → Repository → Models.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import CALIFICACIONES_IMPORTAR, audit
from app.core.dependencies import get_current_user, get_db, require_permission
from app.models.umbral_materia import UMBRAL_DEFAULT_PCT
from app.repositories.asignacion_repository import AsignacionRepository
from app.repositories.calificacion_repository import CalificacionRepository
from app.repositories.umbral_materia_repository import UmbralMateriaRepository
from app.schemas.calificaciones import (
    ImportarCalificacionesResponse,
    MiCalificacionResponse,
    UmbralMateriaRequest,
    UmbralMateriaResponse,
)
from app.services.calificacion_parser import CalificacionParseError, parse_calificaciones_file
from app.services.calificacion_service import importar_calificaciones

_VALORES_APROBATORIOS_DEFAULT = ["Satisfactorio", "Supera lo esperado"]

router = APIRouter(prefix="/api/v1", tags=["calificaciones"])

_PERM = Depends(require_permission("calificaciones:importar"))


@router.get(
    "/calificaciones/mis-calificaciones",
    response_model=list[MiCalificacionResponse],
)
async def mis_calificaciones(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MiCalificacionResponse]:
    """Calificaciones del alumno autenticado, con nombre de materia incluido.

    Resuelve el alumno por email (auto-link a entrada_padron si no está linkeado).
    No requiere permiso especial — solo autenticación.
    """
    from sqlalchemy import select
    from app.models.entrada_padron import EntradaPadron
    from app.models.calificacion import Calificacion
    from app.models.materia import Materia
    from app.core.encryption import decrypt

    # Fast path: entradas ya linkeadas
    fast_stmt = (
        select(EntradaPadron)
        .where(EntradaPadron.tenant_id == current_user.tenant_id)
        .where(EntradaPadron.usuario_id == current_user.id)
        .where(EntradaPadron.deleted_at.is_(None))
    )
    fast_result = await db.execute(fast_stmt)
    eps = list(fast_result.scalars().all())

    # Slow path: siempre buscamos EPs sin linkear que coincidan por email
    # (garantiza que encontramos EPs con cals aunque los linkeados estén vacíos)
    try:
        user_email = decrypt(current_user.email_encrypted).lower().strip()
        scan_stmt = (
            select(EntradaPadron)
            .where(EntradaPadron.tenant_id == current_user.tenant_id)
            .where(EntradaPadron.deleted_at.is_(None))
            .where(EntradaPadron.usuario_id.is_(None))
        )
        scan_result = await db.execute(scan_stmt)
        unlinked_eps = scan_result.scalars().all()

        newly_linked = False
        for ep in unlinked_eps:
            try:
                if decrypt(ep.email_encrypted).lower().strip() == user_email:
                    ep.usuario_id = current_user.id
                    eps.append(ep)
                    newly_linked = True
            except Exception:
                continue

        if newly_linked:
            await db.commit()
    except Exception:
        pass

    if not eps:
        return []

    ep_ids = [ep.id for ep in eps]

    cal_stmt = (
        select(Calificacion, Materia.nombre.label("materia_nombre"))
        .outerjoin(Materia, Calificacion.materia_id == Materia.id)
        .where(Calificacion.tenant_id == current_user.tenant_id)
        .where(Calificacion.deleted_at.is_(None))
        .where(Calificacion.entrada_padron_id.in_(ep_ids))
        .order_by(Materia.nombre, Calificacion.actividad)
    )
    cal_result = await db.execute(cal_stmt)
    rows = cal_result.all()

    return [
        MiCalificacionResponse(
            actividad=row.Calificacion.actividad,
            nota_numerica=row.Calificacion.nota_numerica,
            nota_textual=row.Calificacion.nota_textual,
            aprobado=row.Calificacion.aprobado,
            materia_nombre=row.materia_nombre,
        )
        for row in rows
    ]


async def _check_asignacion_scope(
    asignacion_id: UUID,
    current_user,
    request: Request,
    db: AsyncSession,
) -> None:
    """Verifica que el actor sea el titular de la asignación (si is_own_resource)."""
    is_own = getattr(request.state, "permission_is_own_resource", False)
    if not is_own:
        return
    repo = AsignacionRepository(db, tenant_id=current_user.tenant_id)
    asignacion = await repo.get_by_id(asignacion_id)
    if asignacion is None or asignacion.usuario_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sin acceso a esta asignación",
        )


@router.post(
    "/calificaciones/importar",
    response_model=ImportarCalificacionesResponse,
    status_code=status.HTTP_201_CREATED,
)
async def importar_calificaciones_endpoint(
    request: Request,
    archivo: UploadFile,
    asignacion_id: UUID = Form(...),
    materia_id: UUID = Form(...),
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ImportarCalificacionesResponse:
    """Importa calificaciones desde un archivo xlsx/csv exportado del LMS.

    Detecta columnas numéricas (header termina en ' (Real)', RN-01) y textuales.
    Vincula alumnos al padrón activo por email. Calcula `aprobado` según umbral.

    Requiere permiso: `calificaciones:importar`
    """
    await _check_asignacion_scope(asignacion_id, current_user, request, db)

    # Verificar que la asignación existe y pertenece al tenant
    asig_repo = AsignacionRepository(db, tenant_id=current_user.tenant_id)
    if await asig_repo.get_by_id(asignacion_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asignación no encontrada")

    contents = await archivo.read()
    try:
        filas = parse_calificaciones_file(contents, archivo.filename or "upload.csv")
    except CalificacionParseError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    if not filas:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El archivo no contiene datos de calificaciones",
        )

    # Buscar cualquier versión activa del padrón para esta materia (cualquier cohorte)
    from sqlalchemy import select
    from app.models.version_padron import VersionPadron
    stmt = (
        select(VersionPadron)
        .where(VersionPadron.tenant_id == current_user.tenant_id)
        .where(VersionPadron.materia_id == materia_id)
        .where(VersionPadron.activa.is_(True))
        .where(VersionPadron.deleted_at.is_(None))
        .limit(1)
    )
    result = await db.execute(stmt)
    vp = result.scalar_one_or_none()
    version_padron_id = vp.id if vp else None

    total, actividades = await importar_calificaciones(
        filas=filas,
        asignacion_id=asignacion_id,
        materia_id=materia_id,
        tenant_id=current_user.tenant_id,
        version_padron_id=version_padron_id,
        db=db,
    )

    await audit(
        db,
        actor_id=request.state.actor_id,
        tenant_id=current_user.tenant_id,
        accion=CALIFICACIONES_IMPORTAR,
        materia_id=materia_id,
        filas_afectadas=total,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        detalle={"asignacion_id": str(asignacion_id), "actividades": list(actividades)},
    )

    await db.commit()

    return ImportarCalificacionesResponse(
        asignacion_id=asignacion_id,
        materia_id=materia_id,
        filas_importadas=total,
        actividades_detectadas=sorted(actividades),
    )


@router.delete(
    "/calificaciones/{asignacion_id}/{materia_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def vaciar_calificaciones(
    asignacion_id: UUID,
    materia_id: UUID,
    request: Request,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Vacía las calificaciones propias del docente para la asignación × materia (RN-04).

    Solo elimina los datos de la asignación del actor, sin afectar a otros docentes.
    """
    await _check_asignacion_scope(asignacion_id, current_user, request, db)

    cal_repo = CalificacionRepository(db, tenant_id=current_user.tenant_id)
    deleted = await cal_repo.delete_by_asignacion_materia(asignacion_id, materia_id)
    if deleted == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay calificaciones para esta asignación y materia",
        )

    await db.commit()


@router.get(
    "/calificaciones/umbral/{asignacion_id}/{materia_id}",
    response_model=UmbralMateriaResponse,
)
async def get_umbral(
    asignacion_id: UUID,
    materia_id: UUID,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UmbralMateriaResponse:
    """Obtiene el umbral de aprobación configurado. Si no existe → retorna default (60%)."""
    repo = UmbralMateriaRepository(db, tenant_id=current_user.tenant_id)
    umbral = await repo.get_by_asignacion_materia(asignacion_id, materia_id)

    if umbral is None:
        return UmbralMateriaResponse(
            umbral_pct=UMBRAL_DEFAULT_PCT,
            valores_aprobatorios=_VALORES_APROBATORIOS_DEFAULT,
            es_default=True,
        )
    return UmbralMateriaResponse(
        umbral_pct=umbral.umbral_pct,
        valores_aprobatorios=list(umbral.valores_aprobatorios),
        es_default=False,
    )


@router.put(
    "/calificaciones/umbral/{asignacion_id}/{materia_id}",
    response_model=UmbralMateriaResponse,
)
async def put_umbral(
    asignacion_id: UUID,
    materia_id: UUID,
    payload: UmbralMateriaRequest,
    request: Request,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UmbralMateriaResponse:
    """Configura el umbral de aprobación para una asignación × materia (upsert)."""
    await _check_asignacion_scope(asignacion_id, current_user, request, db)

    repo = UmbralMateriaRepository(db, tenant_id=current_user.tenant_id)
    umbral = await repo.upsert(
        asignacion_id=asignacion_id,
        materia_id=materia_id,
        umbral_pct=payload.umbral_pct,
        valores_aprobatorios=payload.valores_aprobatorios,
    )
    await db.commit()
    await db.refresh(umbral)

    return UmbralMateriaResponse(
        umbral_pct=umbral.umbral_pct,
        valores_aprobatorios=list(umbral.valores_aprobatorios),
        es_default=False,
    )
