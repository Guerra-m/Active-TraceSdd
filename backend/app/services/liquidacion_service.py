"""Servicio de liquidaciones y honorarios (C-18).

Contiene toda la lógica de negocio para:
  - Calcular honorarios por docente (Base + N×Plus) — RN-34
  - Cerrar liquidaciones (Abierta → Cerrada, inmutable) — RN-22
  - Calcular KPIs financieros del período — RN-38

Fórmula (RN-34):
  Total = Base(rol, período) + Σ(Plus(grupo_plus, rol) × N_comisiones_del_grupo)
  N_comisiones = cantidad de comisiones vigentes cuyas materias tienen ese grupo_plus

Reglas:
  - RN-22: Cerrada = inmutable. Intentar cerrar una cerrada → LiquidacionCerradaError
  - RN-35: facturador=True → excluido_por_factura=True, montos=0
  - RN-36: NEXO presentado separado en KPIs (es_nexo=True)
  - RN-37: unidad de liquidación = (cohorte, mes)
  - RN-38: KPIs separan total_general / total_nexo / total_facturantes

Flujo: Routers → LiquidacionService → Repositories → Models (regla #11)
Sin acceso directo a DB: todo via repositories.
"""

from collections import defaultdict
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import LIQUIDACION_CERRAR, audit
from app.core.exceptions import LiquidacionCerradaError, SalarioNoEncontradoError
from app.models.liquidacion import EstadoLiquidacion, Liquidacion
from app.models.user import User
from app.repositories.liquidacion_repository import LiquidacionRepository
from app.repositories.salario_repository import SalarioRepository


def _primer_dia(periodo: str) -> date:
    """Parsea 'AAAA-MM' y retorna el primer día del mes."""
    year, month = int(periodo[:4]), int(periodo[5:7])
    return date(year, month, 1)


class LiquidacionService:
    """Lógica de negocio para liquidaciones y honorarios."""

    def __init__(self, session: AsyncSession, *, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._liq_repo = LiquidacionRepository(session, tenant_id=tenant_id)
        self._sal_repo = SalarioRepository(session, tenant_id=tenant_id)

    async def calcular_monto(
        self,
        *,
        usuario: User,
        rol: str,
        cohorte_id: UUID,
        periodo: str,
    ) -> dict:
        """Calcula el monto de honorarios para un docente en un período.

        Aplica RN-34: Total = Base(rol, período) + Σ(Plus(grupo, rol) × N_comisiones_grupo)
        Aplica RN-35: docentes facturantes → excluido_por_factura=True, montos=0

        Args:
            usuario: Instancia User del docente.
            rol: Rol del docente para la liquidación.
            cohorte_id: UUID de la cohorte del período.
            periodo: String 'AAAA-MM' del período.

        Returns:
            dict con:
              - monto_base (Decimal)
              - monto_plus (Decimal)
              - total (Decimal)
              - excluido_por_factura (bool)
              - comisiones (list[str])
              - es_nexo (bool)

        Raises:
            SalarioNoEncontradoError: Si no existe salario vigente para el rol/período.
        """
        # RN-35: docentes facturantes se excluyen del cálculo estándar
        if usuario.facturador:
            return {
                "monto_base": Decimal("0.00"),
                "monto_plus": Decimal("0.00"),
                "total": Decimal("0.00"),
                "excluido_por_factura": True,
                "comisiones": [],
                "es_nexo": rol == "NEXO",
            }

        # 1. Obtener salario base vigente al período
        salario_base = await self._sal_repo.get_vigente_base(rol=rol, periodo=periodo)
        if salario_base is None:
            raise SalarioNoEncontradoError(rol=rol, periodo=periodo)

        monto_base = Decimal(str(salario_base.monto))

        # 2. Obtener asignaciones vigentes en el período para este usuario/cohorte
        n_comisiones_por_grupo = await self._contar_comisiones_por_grupo(
            usuario_id=usuario.id,
            cohorte_id=cohorte_id,
            periodo=periodo,
        )

        # 3. Calcular plus acumulado para cada grupo (PA-23: acumulación ilimitada)
        monto_plus = Decimal("0.00")
        grupos_en_comisiones = list(n_comisiones_por_grupo.keys())

        for grupo, n_comisiones in n_comisiones_por_grupo.items():
            plus = await self._sal_repo.get_vigente_plus(
                grupo=grupo, rol=rol, periodo=periodo
            )
            if plus is not None:
                monto_plus += Decimal(str(plus.monto)) * n_comisiones

        return {
            "monto_base": monto_base,
            "monto_plus": monto_plus,
            "total": monto_base + monto_plus,
            "excluido_por_factura": False,
            "comisiones": grupos_en_comisiones,
            "es_nexo": rol == "NEXO",
        }

    async def _contar_comisiones_por_grupo(
        self,
        usuario_id: UUID,
        cohorte_id: UUID,
        periodo: str,
    ) -> dict[str, int]:
        """Cuenta comisiones vigentes agrupadas por grupo_plus de la materia.

        Para cada asignación vigente del docente en la cohorte:
          - Si la materia tiene grupo_plus: suma el len(comisiones) de la asignación al grupo
          - Si la materia no tiene grupo_plus: se ignora (no genera plus)

        Returns:
            dict[grupo_plus -> cantidad_de_comisiones]
        """
        from sqlalchemy import select
        from app.models.asignacion import Asignacion
        from app.models.materia import Materia

        primer_dia = _primer_dia(periodo)

        # Buscar asignaciones vigentes al período con su materia
        stmt = (
            select(Asignacion, Materia)
            .join(Materia, Asignacion.materia_id == Materia.id)
            .where(Asignacion.tenant_id == self._tenant_id)
            .where(Asignacion.deleted_at.is_(None))
            .where(Asignacion.usuario_id == usuario_id)
            .where(Asignacion.cohorte_id == cohorte_id)
            .where(Asignacion.desde <= primer_dia)
            .where(
                (Asignacion.hasta.is_(None)) | (Asignacion.hasta >= primer_dia)
            )
            .where(Materia.deleted_at.is_(None))
            .where(Materia.grupo_plus.isnot(None))
        )

        result = await self._session.execute(stmt)
        rows = result.all()

        conteo: dict[str, int] = defaultdict(int)
        for asig, materia in rows:
            # Contar comisiones: len de la lista JSONB
            n = len(asig.comisiones) if asig.comisiones else 1
            conteo[materia.grupo_plus] += n

        return dict(conteo)

    async def cerrar_liquidacion(
        self,
        liquidacion_id: UUID,
        actor_id: UUID,
    ) -> Liquidacion:
        """Cierra una liquidación Abierta, haciéndola inmutable.

        Aplica RN-22: una vez cerrada no puede modificarse.
        Genera entrada de auditoría LIQUIDACION_CERRAR.

        Args:
            liquidacion_id: UUID de la liquidación a cerrar.
            actor_id: UUID del actor que realiza el cierre (del JWT).

        Returns:
            La liquidación cerrada.

        Raises:
            LiquidacionCerradaError: Si la liquidación ya está cerrada.
            ValueError: Si la liquidación no existe en el tenant.
        """
        liq = await self._liq_repo.get_by_id(liquidacion_id)
        if liq is None:
            raise ValueError(f"Liquidación {liquidacion_id} no encontrada")

        if liq.estado == EstadoLiquidacion.CERRADA.value:
            raise LiquidacionCerradaError(liquidacion_id)

        liq.estado = EstadoLiquidacion.CERRADA.value
        liq = await self._liq_repo.update(liq)

        # Audit log — LIQUIDACION_CERRAR (regla #13 + CLAUDE.md)
        await audit(
            self._session,
            actor_id=actor_id,
            tenant_id=self._tenant_id,
            accion=LIQUIDACION_CERRAR,
            detalle={
                "liquidacion_id": str(liquidacion_id),
                "periodo": liq.periodo,
                "usuario_id": str(liq.usuario_id),
            },
        )

        return liq

    async def get_kpis(
        self,
        periodo: str,
        cohorte_id: UUID,
    ) -> dict:
        """Calcula KPIs financieros del período para la cohorte dada.

        Aplica RN-38: segrega total_general / total_nexo / total_facturantes.

        Args:
            periodo: String 'AAAA-MM'.
            cohorte_id: UUID de la cohorte.

        Returns:
            dict con total_general, total_nexo, total_facturantes, cantidad_liquidaciones.
        """
        return await self._liq_repo.sum_kpis(periodo=periodo, cohorte_id=cohorte_id)
