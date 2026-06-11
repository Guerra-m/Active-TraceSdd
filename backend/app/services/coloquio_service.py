"""Lógica de negocio para el módulo de coloquios (C-14).

Reglas de cupo: reservas_activas < dias_disponibles * cupos_por_dia.
"""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluacion import Evaluacion, ReservaEvaluacion, ResultadoEvaluacion
from app.repositories.evaluacion_repository import (
    EvaluacionRepository,
    ReservaEvaluacionRepository,
    ResultadoEvaluacionRepository,
)
from app.schemas.coloquios import MetricasColoquioResponse


class ColoquioService:
    @staticmethod
    async def reservar_turno(
        *,
        evaluacion_id: UUID,
        alumno_id: UUID,
        fecha_hora: str,
        session: AsyncSession,
        tenant_id: UUID,
    ) -> ReservaEvaluacion:
        eval_repo = EvaluacionRepository(session, tenant_id=tenant_id)
        reserva_repo = ReservaEvaluacionRepository(session, tenant_id=tenant_id)

        ev = await eval_repo.get_by_id(evaluacion_id)
        if ev is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluacion no encontrada")

        # Verificar que el alumno no tenga ya una reserva activa
        existente = await reserva_repo.get_by_alumno_evaluacion(
            alumno_id=alumno_id, evaluacion_id=evaluacion_id
        )
        if existente is not None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El alumno ya tiene una reserva activa en esta evaluacion",
            )

        # Verificar cupo disponible
        activas = await reserva_repo.count_activas(evaluacion_id)
        cupo_total = ev.dias_disponibles * ev.cupos_por_dia
        if activas >= cupo_total:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Sin cupo disponible ({activas}/{cupo_total} ocupados)",
            )

        reserva = ReservaEvaluacion(
            evaluacion_id=evaluacion_id,
            alumno_id=alumno_id,
            fecha_hora=fecha_hora,
            estado="Activa",
        )
        return await reserva_repo.create(reserva)

    @staticmethod
    async def get_metricas(session: AsyncSession, *, tenant_id: UUID) -> MetricasColoquioResponse:
        from sqlalchemy import func, select
        from app.models.evaluacion import Evaluacion, ReservaEvaluacion, ResultadoEvaluacion

        eval_repo = EvaluacionRepository(session, tenant_id=tenant_id)
        reserva_repo = ReservaEvaluacionRepository(session, tenant_id=tenant_id)
        resultado_repo = ResultadoEvaluacionRepository(session, tenant_id=tenant_id)

        evaluaciones = await eval_repo.list(limit=10000)
        instancias_activas = len(evaluaciones)

        total_convocados = 0
        reservas_activas = 0
        notas_registradas = 0

        for ev in evaluaciones:
            resultados = await resultado_repo.list_by_evaluacion(ev.id)
            total_convocados += len(resultados)
            notas_registradas += sum(1 for r in resultados if r.nota_final is not None)
            reservas_activas += await reserva_repo.count_activas(ev.id)

        return MetricasColoquioResponse(
            total_convocados=total_convocados,
            instancias_activas=instancias_activas,
            reservas_activas=reservas_activas,
            notas_registradas=notas_registradas,
        )
