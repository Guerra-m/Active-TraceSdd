"""Router de padrón — importación y sincronización con Moodle (C-09).

Endpoints:
  POST   /padron/importar          → importar padrón (xlsx/csv) — 201
  DELETE /padron/{materia_id}/{cohorte_id} → desactivar versión activa — 204
  POST   /padron/sync-moodle       → importar desde Moodle WS — 201

PROFESOR con is_own_resource solo puede importar/desactivar para materias
donde tiene una asignación vigente.

Flujo (regla #11): Router → Service/Repository → Models.
Identidad desde JWT (regla #8). PII email cifrada con AES-256 (regla #12).
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import PADRON_CARGAR, audit
from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.encryption import encrypt
from app.integrations.moodle_ws import MoodleNotConfiguredError, MoodleWSClient, MoodleWSError
from app.models.entrada_padron import EntradaPadron
from app.models.version_padron import VersionPadron
from app.repositories.asignacion_repository import AsignacionRepository
from app.repositories.cohorte_repository import CohorteRepository
from app.repositories.entrada_padron_repository import EntradaPadronRepository
from app.repositories.materia_repository import MateriaRepository
from app.repositories.version_padron_repository import VersionPadronRepository
from app.schemas.padron import EntradaPadronResponse, ImportarPadronResponse, SyncMoodleRequest
from app.services.padron_parser import PadronParseError, parse_padron_file

router = APIRouter(prefix="/api/v1", tags=["padron"])

_PERM = Depends(require_permission("padron:importar"))


def _to_entrada_response(e: EntradaPadron) -> EntradaPadronResponse:
    return EntradaPadronResponse(
        id=e.id,
        version_id=e.version_id,
        usuario_id=e.usuario_id,
        nombre=e.nombre,
        apellidos=e.apellidos,
        comision=e.comision,
        regional=e.regional,
    )


async def _check_profesor_scope(
    materia_id: UUID,
    current_user,
    request: Request,
    db: AsyncSession,
) -> None:
    """Si is_own_resource, verifica que el PROFESOR tenga asignación vigente en la materia."""
    if not getattr(request.state, "permission_is_own_resource", False):
        return
    repo = AsignacionRepository(db, tenant_id=current_user.tenant_id)
    items = await repo.list_filtrado(
        usuario_id=current_user.id,
        rol="PROFESOR",
        materia_id=materia_id,
    )
    vigentes = [a for a in items if a.estado_vigencia == "Vigente"]
    if not vigentes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sin asignación vigente como PROFESOR para esta materia",
        )


async def _validate_materia_cohorte(
    materia_id: UUID,
    cohorte_id: UUID,
    tenant_id: UUID,
    db: AsyncSession,
) -> None:
    mat_repo = MateriaRepository(db, tenant_id=tenant_id)
    if await mat_repo.get_by_id(materia_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Materia no encontrada")
    coh_repo = CohorteRepository(db, tenant_id=tenant_id)
    if await coh_repo.get_by_id(cohorte_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cohorte no encontrada")


async def _importar_filas(
    filas: list[dict],
    materia_id: UUID,
    cohorte_id: UUID,
    current_user,
    request: Request,
    db: AsyncSession,
) -> ImportarPadronResponse:
    """Crea nueva VersionPadron, desactiva la anterior, inserta entradas. Retorna respuesta."""
    vp_repo = VersionPadronRepository(db, tenant_id=current_user.tenant_id)
    ep_repo = EntradaPadronRepository(db, tenant_id=current_user.tenant_id)

    # Desactivar versión anterior si existe
    version_anterior = await vp_repo.get_activa(materia_id, cohorte_id)
    if version_anterior is not None:
        await vp_repo.desactivar(version_anterior)

    # Crear nueva versión
    nueva_version = VersionPadron(
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        cargado_por=current_user.id,
        cargado_at=datetime.now(timezone.utc),
        activa=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    nueva_version.tenant_id = current_user.tenant_id
    db.add(nueva_version)
    await db.flush()

    # Construir entradas con email cifrado
    entradas = []
    for fila in filas:
        entrada = EntradaPadron(
            version_id=nueva_version.id,
            nombre=fila["nombre"],
            apellidos=fila["apellidos"],
            email_encrypted=encrypt(fila["email"]),
            comision=fila.get("comision"),
            regional=fila.get("regional"),
            usuario_id=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        entradas.append(entrada)

    total = await ep_repo.create_batch(entradas)

    await audit(
        db,
        actor_id=request.state.actor_id,
        tenant_id=current_user.tenant_id,
        accion=PADRON_CARGAR,
        materia_id=materia_id,
        filas_afectadas=total,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        detalle={"materia_id": str(materia_id), "cohorte_id": str(cohorte_id)},
    )

    await db.commit()
    await db.refresh(nueva_version)

    return ImportarPadronResponse(
        version_id=nueva_version.id,
        filas_importadas=total,
        materia_id=materia_id,
        cohorte_id=cohorte_id,
    )


@router.post(
    "/padron/importar",
    response_model=ImportarPadronResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Importar padrón desde archivo xlsx o csv",
)
async def importar_padron(
    request: Request,
    archivo: UploadFile,
    materia_id: UUID = Form(...),
    cohorte_id: UUID = Form(...),
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ImportarPadronResponse:
    """Importa un padrón de alumnos desde un archivo xlsx o csv.

    Crea una nueva versión del padrón para la combinación materia×cohorte.
    Si existe una versión activa previa, se desactiva automáticamente.
    El email de cada entrada queda cifrado en reposo (AES-256-GCM).

    Requiere permiso: `padron:importar`
    PROFESOR con is_own_resource solo puede importar su propia materia.
    """
    await _check_profesor_scope(materia_id, current_user, request, db)
    await _validate_materia_cohorte(materia_id, cohorte_id, current_user.tenant_id, db)

    contents = await archivo.read()
    try:
        filas = parse_padron_file(contents, archivo.filename or "upload.csv")
    except PadronParseError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    if not filas:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El archivo no contiene filas de datos",
        )

    return await _importar_filas(filas, materia_id, cohorte_id, current_user, request, db)


@router.delete(
    "/padron/{materia_id}/{cohorte_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar versión activa del padrón",
)
async def desactivar_padron(
    materia_id: UUID,
    cohorte_id: UUID,
    request: Request,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Desactiva la versión activa del padrón para una materia×cohorte.

    No elimina datos — soft-deactivate (activa=False + deleted_at en VersionPadron).
    Si no hay versión activa, retorna 404.

    Requiere permiso: `padron:importar`
    """
    await _check_profesor_scope(materia_id, current_user, request, db)

    vp_repo = VersionPadronRepository(db, tenant_id=current_user.tenant_id)
    version = await vp_repo.get_activa(materia_id, cohorte_id)
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe versión activa del padrón para esta materia y cohorte",
        )

    await vp_repo.desactivar(version)
    await vp_repo.soft_delete(version.id)
    await db.commit()


@router.post(
    "/padron/sync-moodle",
    response_model=ImportarPadronResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Sincronizar padrón desde Moodle WS",
)
async def sync_moodle(
    payload: SyncMoodleRequest,
    request: Request,
    _: None = _PERM,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ImportarPadronResponse:
    """Importa el padrón de alumnos directamente desde Moodle Web Services.

    Obtiene la lista de participantes del curso indicado en Moodle y genera
    una nueva versión del padrón, desactivando la anterior si existiera.

    Requiere permiso: `padron:importar`
    Requiere MOODLE_URL y MOODLE_TOKEN configurados.
    """
    await _check_profesor_scope(payload.materia_id, current_user, request, db)
    await _validate_materia_cohorte(
        payload.materia_id, payload.cohorte_id, current_user.tenant_id, db
    )

    try:
        client = MoodleWSClient()
        participantes = await client.get_course_participants(payload.moodle_course_id)
    except MoodleNotConfiguredError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except MoodleWSError as e:
        headers = {}
        if e.retry_after is not None:
            headers["Retry-After"] = str(e.retry_after)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
            headers=headers or None,
        )

    # Mapear participantes de Moodle al formato interno
    filas = []
    for p in participantes:
        nombre = str(p.get("firstname", "")).strip()
        apellidos = str(p.get("lastname", "")).strip()
        email = str(p.get("email", "")).strip()
        if not nombre or not apellidos or not email:
            continue
        filas.append({
            "nombre": nombre,
            "apellidos": apellidos,
            "email": email,
            "comision": None,
            "regional": None,
        })

    if not filas:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Moodle no retornó participantes válidos para el curso",
        )

    return await _importar_filas(
        filas, payload.materia_id, payload.cohorte_id, current_user, request, db
    )
