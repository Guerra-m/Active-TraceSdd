"""Service para gestión de encuentros sincrónicos (C-13).

Lógica de negocio para creación de slots y generación de instancias.
"""

import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.instancia_encuentro import InstanciaEncuentro
from app.models.slot_encuentro import SlotEncuentro
from app.repositories.instancia_encuentro_repository import InstanciaEncuentroRepository
from app.repositories.slot_encuentro_repository import SlotEncuentroRepository
from app.schemas.encuentros import SlotEncuentroCreate


class EncuentroService:

    @staticmethod
    async def crear_slot(
        payload: SlotEncuentroCreate,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        asignacion_id: UUID,
    ) -> tuple[SlotEncuentro | None, list[InstanciaEncuentro]]:
        """Crea un slot y sus instancias.

        Modo recurrente: crea 1 SlotEncuentro + N InstanciaEncuentro.
        Modo único: crea solo 1 InstanciaEncuentro con slot_id=NULL.

        Retorna (slot_o_none, instancias).
        """
        slot_repo = SlotEncuentroRepository(session, tenant_id=tenant_id)
        inst_repo = InstanciaEncuentroRepository(session, tenant_id=tenant_id)

        if payload.cant_semanas is not None:
            # Modo recurrente
            slot = SlotEncuentro(
                asignacion_id=asignacion_id,
                materia_id=payload.materia_id,
                titulo=payload.titulo,
                hora=payload.hora,
                dia_semana=payload.dia_semana,
                fecha_inicio=payload.fecha_inicio,
                cant_semanas=payload.cant_semanas,
                fecha_unica=None,
                meet_url=payload.meet_url,
                vig_desde=payload.vig_desde,
                vig_hasta=payload.vig_hasta,
            )
            slot = await slot_repo.create(slot)

            instancias: list[InstanciaEncuentro] = []
            for i in range(payload.cant_semanas):
                fecha = payload.fecha_inicio + datetime.timedelta(weeks=i)
                inst = InstanciaEncuentro(
                    slot_id=slot.id,
                    materia_id=payload.materia_id,
                    fecha=fecha,
                    hora=payload.hora,
                    titulo=payload.titulo,
                    estado="Programado",
                    meet_url=payload.meet_url,
                )
                inst = await inst_repo.create(inst)
                instancias.append(inst)

            return slot, instancias

        else:
            # Modo único — sin slot
            inst = InstanciaEncuentro(
                slot_id=None,
                materia_id=payload.materia_id,
                fecha=payload.fecha_unica,
                hora=payload.hora,
                titulo=payload.titulo,
                estado="Programado",
                meet_url=payload.meet_url,
            )
            inst = await inst_repo.create(inst)
            return None, [inst]
