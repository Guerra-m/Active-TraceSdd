"""Helper de auditoría — punto único de escritura al log (E-AUD).

Uso:
    from app.core.audit import audit, IMPERSONACION_INICIAR

    await audit(
        db,
        actor_id=request.state.actor_id,
        tenant_id=current_user.tenant_id,
        accion=IMPERSONACION_INICIAR,
        impersonado_id=target_user.id,
        ip=request.client.host,
        user_agent=request.headers.get("user-agent"),
    )

El helper NO hace commit — la transacción de negocio que engloba la llamada
es responsable del commit. Esto garantiza atomicidad: si la operación falla,
el registro de auditoría también se revierte.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.repositories.audit_log_repository import AuditLogRepository

# ---------------------------------------------------------------------------
# Códigos de acción estandarizados del catálogo (knowledge-base/04 §Códigos)
# ---------------------------------------------------------------------------

CALIFICACIONES_IMPORTAR = "CALIFICACIONES_IMPORTAR"
PADRON_CARGAR = "PADRON_CARGAR"
COMUNICACION_ENVIAR = "COMUNICACION_ENVIAR"
ASIGNACION_MODIFICAR = "ASIGNACION_MODIFICAR"
LIQUIDACION_CERRAR = "LIQUIDACION_CERRAR"
IMPERSONACION_INICIAR = "IMPERSONACION_INICIAR"
IMPERSONACION_FINALIZAR = "IMPERSONACION_FINALIZAR"


# ---------------------------------------------------------------------------
# Función helper
# ---------------------------------------------------------------------------


async def audit(
    db: AsyncSession,
    actor_id: UUID,
    tenant_id: UUID,
    accion: str,
    *,
    impersonado_id: UUID | None = None,
    materia_id: UUID | None = None,
    detalle: dict | None = None,
    filas_afectadas: int | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
) -> None:
    """Registra una acción significativa en el log de auditoría.

    Args:
        db: Sesión async activa. El registro se agrega a la sesión sin commit.
        actor_id: UUID del actor real (quien ejecuta la acción).
        tenant_id: UUID del tenant donde ocurre la acción.
        accion: Código de acción estandarizado (usar las constantes de este módulo).
        impersonado_id: UUID del usuario impersonado, si aplica.
        materia_id: UUID de la materia relacionada, si aplica.
        detalle: Contexto adicional en forma de dict (se almacena como JSONB).
        filas_afectadas: Cantidad de registros afectados por la acción.
        ip: Dirección IP del cliente.
        user_agent: User-Agent del cliente.
    """
    entry = AuditLog(
        actor_id=actor_id,
        tenant_id=tenant_id,
        accion=accion,
        impersonado_id=impersonado_id,
        materia_id=materia_id,
        detalle=detalle,
        filas_afectadas=filas_afectadas,
        ip=ip,
        user_agent=user_agent,
    )
    repo = AuditLogRepository(db)
    await repo.insert(entry)
