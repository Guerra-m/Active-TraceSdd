"""Schemas Pydantic para el módulo de liquidaciones y honorarios (C-18).

Todos los schemas siguen la regla dura #5: extra='forbid'.
Los schemas de respuesta usan from_attributes=True para ORM.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

# ---------------------------------------------------------------------------
# Tipos reutilizables
# ---------------------------------------------------------------------------

EstadoLiquidacionEnum = Literal["Abierta", "Cerrada"]
EstadoFacturaEnum = Literal["Pendiente", "Abonada"]

_ROLES_VALIDOS = frozenset(
    {"ALUMNO", "TUTOR", "PROFESOR", "COORDINADOR", "NEXO", "ADMIN", "FINANZAS"}
)


def _validar_periodo(v: str) -> str:
    import re
    if not re.match(r"^\d{4}-\d{2}$", v):
        raise ValueError("El período debe tener formato AAAA-MM")
    return v


# ---------------------------------------------------------------------------
# SalarioBase
# ---------------------------------------------------------------------------


class SalarioBaseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rol: str
    monto: Decimal
    desde: date
    hasta: date | None = None

    @field_validator("rol")
    @classmethod
    def rol_valido(cls, v: str) -> str:
        if v not in _ROLES_VALIDOS:
            raise ValueError(f"Rol inválido: {v!r}")
        return v


class SalarioBaseUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rol: str
    monto: Decimal
    desde: date
    hasta: date | None = None

    @field_validator("rol")
    @classmethod
    def rol_valido(cls, v: str) -> str:
        if v not in _ROLES_VALIDOS:
            raise ValueError(f"Rol inválido: {v!r}")
        return v


class SalarioBaseResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    tenant_id: UUID
    rol: str
    monto: Decimal
    desde: date
    hasta: date | None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# SalarioPlus
# ---------------------------------------------------------------------------


class SalarioPlusCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    grupo: str
    rol: str
    descripcion: str = ""
    monto: Decimal
    desde: date
    hasta: date | None = None

    @field_validator("rol")
    @classmethod
    def rol_valido(cls, v: str) -> str:
        if v not in _ROLES_VALIDOS:
            raise ValueError(f"Rol inválido: {v!r}")
        return v


class SalarioPlusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    grupo: str
    rol: str
    descripcion: str = ""
    monto: Decimal
    desde: date
    hasta: date | None = None

    @field_validator("rol")
    @classmethod
    def rol_valido(cls, v: str) -> str:
        if v not in _ROLES_VALIDOS:
            raise ValueError(f"Rol inválido: {v!r}")
        return v


class SalarioPlusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    tenant_id: UUID
    grupo: str
    rol: str
    descripcion: str
    monto: Decimal
    desde: date
    hasta: date | None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Liquidacion
# ---------------------------------------------------------------------------


class LiquidacionCalcularRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cohorte_id: UUID
    periodo: str  # AAAA-MM

    @field_validator("periodo")
    @classmethod
    def periodo_valido(cls, v: str) -> str:
        return _validar_periodo(v)


class LiquidacionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    tenant_id: UUID
    cohorte_id: UUID
    periodo: str
    usuario_id: UUID
    rol: str
    comisiones: list
    monto_base: Decimal
    monto_plus: Decimal
    total: Decimal
    es_nexo: bool
    excluido_por_factura: bool
    estado: str
    created_at: datetime
    updated_at: datetime


class LiquidacionKPIResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    periodo: str
    cohorte_id: UUID
    total_general: Decimal
    total_nexo: Decimal
    total_facturantes: Decimal
    cantidad_liquidaciones: int


# ---------------------------------------------------------------------------
# Factura
# ---------------------------------------------------------------------------


class FacturaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    usuario_id: UUID
    periodo: str
    monto: Decimal
    detalle: str = ""
    archivo_ref: str | None = None

    @field_validator("periodo")
    @classmethod
    def periodo_valido(cls, v: str) -> str:
        return _validar_periodo(v)


class FacturaAbonarRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fecha_pago: date


class FacturaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    tenant_id: UUID
    usuario_id: UUID
    periodo: str
    monto: Decimal
    detalle: str
    archivo_ref: str | None
    estado: str
    fecha_carga: datetime
    fecha_pago: date | None
    created_at: datetime
    updated_at: datetime
