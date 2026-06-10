"""Servicio de comunicaciones — C-12 comunicaciones-cola-worker.

Encapsula la lógica de negocio para preview, creación de lotes y aprobación.
Flujo: Router → Service → Repository → Models.
"""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import decrypt, encrypt
from app.models.comunicacion import MSG_PENDIENTE, Comunicacion
from app.models.lote_comunicacion import (
    LOTE_CANCELADO,
    LOTE_PENDIENTE,
    LOTE_PENDIENTE_APROBACION,
    LoteComunicacion,
)
from app.repositories.comunicacion_repository import ComunicacionRepository

_VARS = ("{{nombre}}", "{{apellidos}}")


def render_preview(asunto_tpl: str, cuerpo_tpl: str, variables: dict) -> tuple[str, str]:
    """Interpola variables en las plantillas y retorna (asunto, cuerpo) renderizados.

    Variables soportadas: {{nombre}}, {{apellidos}}.
    """
    nombre = variables.get("nombre", "")
    apellidos = variables.get("apellidos", "")
    asunto = asunto_tpl.replace("{{nombre}}", nombre).replace("{{apellidos}}", apellidos)
    cuerpo = cuerpo_tpl.replace("{{nombre}}", nombre).replace("{{apellidos}}", apellidos)
    return asunto, cuerpo


async def crear_lote(
    *,
    asunto_tpl: str,
    cuerpo_tpl: str,
    destinatarios: list[dict],
    materia_id: UUID | None,
    enviado_por: UUID,
    tenant_id: UUID,
    umbral_aprobacion: int,
    db: AsyncSession,
) -> LoteComunicacion:
    """Crea un LoteComunicacion con sus Comunicaciones en estado Pendiente.

    Cada destinatario requiere: {entrada_padron_id, nombre, apellidos, email_encrypted}.
    El email se descifra para verificar integridad y se re-cifra en Comunicacion.destinatario.
    """
    requiere = len(destinatarios) > umbral_aprobacion
    estado_inicial = LOTE_PENDIENTE_APROBACION if requiere else LOTE_PENDIENTE

    repo = ComunicacionRepository(db, tenant_id=tenant_id)

    lote = LoteComunicacion(
        enviado_por=enviado_por,
        materia_id=materia_id,
        asunto_template=asunto_tpl,
        cuerpo_template=cuerpo_tpl,
        estado=estado_inicial,
        requiere_aprobacion=requiere,
        total_mensajes=len(destinatarios),
    )
    lote = await repo.create_lote(lote)

    mensajes = []
    for d in destinatarios:
        nombre = d.get("nombre", "")
        apellidos = d.get("apellidos", "")
        # email_encrypted viene del padrón — descifrar para re-cifrar en Comunicacion
        email_enc = d.get("email_encrypted", "")
        try:
            email_plain = decrypt(email_enc) if email_enc else ""
        except Exception:
            email_plain = ""
        # Re-cifrar para almacenar en comunicaciones.destinatario
        destinatario_cifrado = encrypt(email_plain) if email_plain else encrypt("")

        asunto_render, cuerpo_render = render_preview(
            asunto_tpl, cuerpo_tpl, {"nombre": nombre, "apellidos": apellidos}
        )

        c = Comunicacion(
            lote_id=lote.id,
            enviado_por=enviado_por,
            materia_id=materia_id,
            entrada_padron_id=d.get("entrada_padron_id"),
            destinatario=destinatario_cifrado,
            asunto=asunto_render,
            cuerpo=cuerpo_render,
            estado=MSG_PENDIENTE,
        )
        mensajes.append(c)

    await repo.create_batch(mensajes)
    return lote


async def aprobar_lote(
    lote_id: UUID,
    aprobado_por: UUID,
    tenant_id: UUID,
    db: AsyncSession,
) -> LoteComunicacion:
    """Aprueba el lote. Solo aplicable a lotes en PendienteAprobacion."""
    repo = ComunicacionRepository(db, tenant_id=tenant_id)
    lote = await repo.get_lote(lote_id)

    if lote is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote no encontrado")

    if lote.estado != LOTE_PENDIENTE_APROBACION:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El lote no está en estado PendienteAprobacion (estado actual: {lote.estado})",
        )

    lote = await repo.marcar_lote_aprobado(lote_id, aprobado_por)
    return lote


async def cancelar_lote(
    lote_id: UUID,
    tenant_id: UUID,
    db: AsyncSession,
) -> int:
    """Cancela los mensajes Pendiente del lote. Retorna cantidad cancelada."""
    repo = ComunicacionRepository(db, tenant_id=tenant_id)
    lote = await repo.get_lote(lote_id)

    if lote is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote no encontrado")

    if lote.estado in ("Despachando", "Completado"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No se puede cancelar un lote en estado {lote.estado}",
        )

    cancelados = await repo.cancelar_por_lote(lote_id)
    lote = await repo.update_lote_estado(lote_id, LOTE_CANCELADO)
    return cancelados
