"""Servicio de análisis académico — C-11 analisis-atrasados-reportes.

Funciones de análisis sobre datos ya persistidos (C-09/C-10):
  get_atrasados             — alumnos con actividades faltantes o reprobadas (RN-06)
  get_ranking               — ranking por actividades aprobadas ≥1 (RN-09)
  get_notas_finales         — promedio numérico y resumen por alumno (F2.5)
  get_entregas_sin_corregir — calificaciones importadas sin nota
  get_monitor               — métricas agregadas de seguimiento

Todas las funciones retornan dicts planos listos para serializar a schema.
Identidad del alumno: solo alumnos con entrada_padron_id IS NOT NULL (D1).
"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_atrasados(
    asignacion_id: UUID,
    materia_id: UUID,
    tenant_id: UUID,
    db: AsyncSession,
) -> list[dict]:
    """Retorna alumnos atrasados (D3: faltante OR reprobado) para el scope dado.

    Un alumno es atrasado si:
    - Tiene al menos una actividad faltante (no registrada en calificaciones), o
    - Tiene al menos una calificación con aprobado=False.
    """
    stmt = text(
        """
        SELECT c.entrada_padron_id,
               ep.nombre,
               ep.apellidos,
               c.actividad,
               c.aprobado
        FROM calificaciones c
        JOIN entrada_padron ep ON ep.id = c.entrada_padron_id
        WHERE c.tenant_id   = :tid
          AND c.asignacion_id = :asig_id
          AND c.materia_id    = :mat_id
          AND c.deleted_at IS NULL
          AND c.entrada_padron_id IS NOT NULL
        ORDER BY ep.apellidos ASC, ep.nombre ASC, c.actividad ASC
        """
    )
    result = await db.execute(
        stmt,
        {"tid": tenant_id, "asig_id": asignacion_id, "mat_id": materia_id},
    )
    rows = result.fetchall()

    if not rows:
        return []

    # Conjunto de referencia de actividades para este scope
    reference_actividades: set[str] = {row.actividad for row in rows}

    # Agrupar por alumno
    alumnos: dict[UUID, dict] = {}
    for row in rows:
        ep_id = row.entrada_padron_id
        if ep_id not in alumnos:
            alumnos[ep_id] = {
                "entrada_padron_id": ep_id,
                "nombre": row.nombre,
                "apellidos": row.apellidos,
                "actividades_alumno": set(),
                "reprobadas": [],
            }
        alumnos[ep_id]["actividades_alumno"].add(row.actividad)
        if not row.aprobado:
            alumnos[ep_id]["reprobadas"].append(row.actividad)

    atrasados = []
    for ep_id, data in alumnos.items():
        faltantes = sorted(reference_actividades - data["actividades_alumno"])
        reprobadas = sorted(set(data["reprobadas"]))
        if faltantes or reprobadas:
            atrasados.append(
                {
                    "entrada_padron_id": ep_id,
                    "nombre": data["nombre"],
                    "apellidos": data["apellidos"],
                    "faltantes": faltantes,
                    "reprobadas": reprobadas,
                }
            )

    atrasados.sort(key=lambda a: (a["apellidos"], a["nombre"]))
    return atrasados


async def get_ranking(
    asignacion_id: UUID,
    materia_id: UUID,
    tenant_id: UUID,
    db: AsyncSession,
) -> list[dict]:
    """Ranking de alumnos por cantidad de actividades aprobadas (RN-09).

    Excluye alumnos sin ninguna actividad aprobada.
    Orden: aprobadas DESC, apellidos ASC (determinístico).
    """
    stmt = text(
        """
        SELECT ep.id AS entrada_padron_id,
               ep.nombre,
               ep.apellidos,
               COUNT(*) FILTER (WHERE c.aprobado = true)  AS aprobadas,
               COUNT(*)                                    AS total
        FROM calificaciones c
        JOIN entrada_padron ep ON ep.id = c.entrada_padron_id
        WHERE c.tenant_id     = :tid
          AND c.asignacion_id = :asig_id
          AND c.materia_id    = :mat_id
          AND c.deleted_at IS NULL
          AND c.entrada_padron_id IS NOT NULL
        GROUP BY ep.id, ep.nombre, ep.apellidos
        HAVING COUNT(*) FILTER (WHERE c.aprobado = true) > 0
        ORDER BY aprobadas DESC, ep.apellidos ASC
        """
    )
    result = await db.execute(
        stmt,
        {"tid": tenant_id, "asig_id": asignacion_id, "mat_id": materia_id},
    )
    rows = result.fetchall()

    ranking = []
    for pos, row in enumerate(rows, start=1):
        ranking.append(
            {
                "posicion": pos,
                "entrada_padron_id": row.entrada_padron_id,
                "nombre": row.nombre,
                "apellidos": row.apellidos,
                "aprobadas": int(row.aprobadas),
                "total": int(row.total),
            }
        )
    return ranking


async def get_notas_finales(
    asignacion_id: UUID,
    materia_id: UUID,
    tenant_id: UUID,
    db: AsyncSession,
) -> list[dict]:
    """Nota final promedio por alumno (F2.5).

    Promedia solo nota_numerica (actividades textuales quedan fuera del promedio).
    Retorna null en promedio_numerico si el alumno no tiene notas numéricas.
    """
    stmt = text(
        """
        SELECT ep.id AS entrada_padron_id,
               ep.nombre,
               ep.apellidos,
               AVG(c.nota_numerica)                         AS promedio,
               COUNT(*) FILTER (WHERE c.aprobado = true)   AS aprobadas,
               COUNT(*)                                     AS total
        FROM calificaciones c
        JOIN entrada_padron ep ON ep.id = c.entrada_padron_id
        WHERE c.tenant_id     = :tid
          AND c.asignacion_id = :asig_id
          AND c.materia_id    = :mat_id
          AND c.deleted_at IS NULL
          AND c.entrada_padron_id IS NOT NULL
        GROUP BY ep.id, ep.nombre, ep.apellidos
        ORDER BY ep.apellidos ASC
        """
    )
    result = await db.execute(
        stmt,
        {"tid": tenant_id, "asig_id": asignacion_id, "mat_id": materia_id},
    )
    rows = result.fetchall()

    return [
        {
            "entrada_padron_id": row.entrada_padron_id,
            "nombre": row.nombre,
            "apellidos": row.apellidos,
            "promedio_numerico": Decimal(str(row.promedio)).quantize(Decimal("0.01"))
            if row.promedio is not None
            else None,
            "aprobadas": int(row.aprobadas),
            "total": int(row.total),
        }
        for row in rows
    ]


async def get_entregas_sin_corregir(
    asignacion_id: UUID,
    materia_id: UUID,
    tenant_id: UUID,
    db: AsyncSession,
) -> list[dict]:
    """Calificaciones importadas sin nota (nota_numerica IS NULL AND nota_textual IS NULL)."""
    stmt = text(
        """
        SELECT c.entrada_padron_id,
               ep.nombre,
               ep.apellidos,
               c.actividad,
               c.importado_at
        FROM calificaciones c
        JOIN entrada_padron ep ON ep.id = c.entrada_padron_id
        WHERE c.tenant_id     = :tid
          AND c.asignacion_id = :asig_id
          AND c.materia_id    = :mat_id
          AND c.deleted_at IS NULL
          AND c.entrada_padron_id IS NOT NULL
          AND c.nota_numerica IS NULL
          AND c.nota_textual IS NULL
        ORDER BY ep.apellidos ASC, ep.nombre ASC, c.actividad ASC
        """
    )
    result = await db.execute(
        stmt,
        {"tid": tenant_id, "asig_id": asignacion_id, "mat_id": materia_id},
    )
    rows = result.fetchall()
    return [
        {
            "entrada_padron_id": row.entrada_padron_id,
            "nombre": row.nombre,
            "apellidos": row.apellidos,
            "actividad": row.actividad,
            "importado_at": row.importado_at,
        }
        for row in rows
    ]


async def get_monitor(
    asignacion_id: UUID,
    materia_id: UUID,
    tenant_id: UUID,
    db: AsyncSession,
) -> dict:
    """Métricas de seguimiento: totales, atrasados, promedio, comunicaciones."""
    from app.models.lote_comunicacion import LoteComunicacion, LOTE_COMPLETADO, LOTE_CANCELADO

    notas = await get_notas_finales(asignacion_id, materia_id, tenant_id, db)
    total_alumnos = len(notas)

    promedios = [float(n["promedio_numerico"]) for n in notas if n["promedio_numerico"] is not None]
    promedio_general = round(sum(promedios) / len(promedios), 2) if promedios else None

    atrasados_list = await get_atrasados(asignacion_id, materia_id, tenant_id, db)
    atrasados = len(atrasados_list)

    stmt_enviados = select(func.count()).where(
        LoteComunicacion.tenant_id == tenant_id,
        LoteComunicacion.materia_id == materia_id,
        LoteComunicacion.deleted_at.is_(None),
        LoteComunicacion.estado == LOTE_COMPLETADO,
    )
    stmt_pendientes = select(func.count()).where(
        LoteComunicacion.tenant_id == tenant_id,
        LoteComunicacion.materia_id == materia_id,
        LoteComunicacion.deleted_at.is_(None),
        LoteComunicacion.estado.not_in([LOTE_COMPLETADO, LOTE_CANCELADO]),
    )

    enviados_r = await db.execute(stmt_enviados)
    pendientes_r = await db.execute(stmt_pendientes)

    return {
        "total_alumnos": total_alumnos,
        "atrasados": atrasados,
        "al_dia": total_alumnos - atrasados,
        "promedio_general": promedio_general,
        "comunicaciones_enviadas": enviados_r.scalar_one() or 0,
        "comunicaciones_pendientes": pendientes_r.scalar_one() or 0,
    }
