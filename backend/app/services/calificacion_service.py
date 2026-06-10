"""Servicio de importación de calificaciones (C-10 calificaciones-y-umbral).

Orquesta: parseo → mapeo a padrón → cálculo de aprobado → batch insert.
No hace commit — el router es responsable de la transacción.
"""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calificacion import Calificacion
from app.models.umbral_materia import UMBRAL_DEFAULT_PCT, UmbralMateria
from app.repositories.calificacion_repository import CalificacionRepository
from app.repositories.entrada_padron_repository import EntradaPadronRepository
from app.repositories.umbral_materia_repository import UmbralMateriaRepository

_DEFAULT_VALORES_APROBATORIOS = ["Satisfactorio", "Supera lo esperado"]


def _calcular_aprobado(
    nota_numerica: Decimal | None,
    nota_textual: str | None,
    umbral_pct: int,
    valores_aprobatorios: list[str],
    nota_max: Decimal = Decimal("100"),
) -> bool:
    if nota_numerica is not None:
        umbral_abs = nota_max * Decimal(umbral_pct) / Decimal(100)
        return nota_numerica >= umbral_abs
    if nota_textual is not None:
        return nota_textual.strip() in valores_aprobatorios
    return False


async def importar_calificaciones(
    filas: list[dict],
    asignacion_id: UUID,
    materia_id: UUID,
    tenant_id: UUID,
    version_padron_id: UUID | None,
    db: AsyncSession,
) -> tuple[int, set[str]]:
    """Importa calificaciones para una asignación × materia.

    Args:
        filas: Output de parse_calificaciones_file.
        asignacion_id: UUID de la asignación del docente importador.
        materia_id: UUID de la materia.
        tenant_id: UUID del tenant.
        version_padron_id: UUID de la versión activa del padrón (o None).
        db: AsyncSession activa.

    Returns:
        Tuple (total_insertado, actividades_detectadas).
    """
    umbral_repo = UmbralMateriaRepository(db, tenant_id=tenant_id)
    umbral = await umbral_repo.get_by_asignacion_materia(asignacion_id, materia_id)

    umbral_pct = umbral.umbral_pct if umbral else UMBRAL_DEFAULT_PCT
    valores_aprobatorios = (
        list(umbral.valores_aprobatorios) if umbral else _DEFAULT_VALORES_APROBATORIOS
    )

    # Índice email → entrada_padron_id (solo si hay versión activa)
    email_a_entrada: dict[str, UUID] = {}
    if version_padron_id is not None:
        ep_repo = EntradaPadronRepository(db, tenant_id=tenant_id)
        entradas = await ep_repo.list_by_version(version_padron_id)
        from app.core.encryption import decrypt
        for entrada in entradas:
            try:
                email = decrypt(entrada.email_encrypted).strip().lower()
                email_a_entrada[email] = entrada.id
            except Exception:
                pass

    actividades_detectadas: set[str] = set()
    calificaciones: list[Calificacion] = []
    now = datetime.now(timezone.utc)

    for fila in filas:
        email_lower = fila.get("email", "").strip().lower()
        entrada_padron_id = email_a_entrada.get(email_lower)
        actividad = fila["actividad"]
        actividades_detectadas.add(actividad)

        aprobado = _calcular_aprobado(
            fila.get("nota_numerica"),
            fila.get("nota_textual"),
            umbral_pct,
            valores_aprobatorios,
        )

        cal = Calificacion(
            asignacion_id=asignacion_id,
            materia_id=materia_id,
            entrada_padron_id=entrada_padron_id,
            actividad=actividad,
            nota_numerica=fila.get("nota_numerica"),
            nota_textual=fila.get("nota_textual"),
            aprobado=aprobado,
            importado_at=now,
        )
        calificaciones.append(cal)

    cal_repo = CalificacionRepository(db, tenant_id=tenant_id)
    total = await cal_repo.create_batch(calificaciones)
    return total, actividades_detectadas
