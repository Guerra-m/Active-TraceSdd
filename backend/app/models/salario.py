"""Modelos ORM para SalarioBase y SalarioPlus (C-18 liquidaciones).

SalarioBase: base por rol con vigencia temporal (desde/hasta nullable).
SalarioPlus: plus por (grupo_plus × rol) con vigencia temporal.

La vigencia se aplica como:
  - salario activo si desde <= primer_día_período AND (hasta IS NULL OR hasta >= último_día_período)
  - Se selecciona el registro con mayor `desde` que cumpla la condición.

Soft delete via TenantScopedBase — append-only por auditoría.
"""

from sqlalchemy import CheckConstraint, Column, Date, Index, Numeric, String

from app.core.database import Base
from app.models.base import TenantScopedBase

_ROLES_VALIDOS = (
    "ALUMNO", "TUTOR", "PROFESOR", "COORDINADOR", "NEXO", "ADMIN", "FINANZAS"
)
_ROL_CHECK = f"rol IN ({', '.join(repr(r) for r in _ROLES_VALIDOS)})"


class SalarioBase(TenantScopedBase, Base):
    """Tabla de salarios base por rol y vigencia temporal.

    El monto es la retribución fija mensual del rol, independiente
    de las materias o comisiones asignadas.
    """

    __tablename__ = "salarios_base"

    rol = Column(String(20), nullable=False)
    monto = Column(Numeric(12, 2), nullable=False)
    desde = Column(Date, nullable=False)
    hasta = Column(Date, nullable=True)

    __table_args__ = (
        CheckConstraint(_ROL_CHECK, name="ck_salarios_base_rol"),
        Index("ix_salarios_base_tenant_rol", "tenant_id", "rol"),
        Index("ix_salarios_base_tenant_desde", "tenant_id", "desde"),
    )

    def __repr__(self) -> str:
        return (
            f"<SalarioBase rol={self.rol!r} monto={self.monto} "
            f"desde={self.desde} hasta={self.hasta}>"
        )


class SalarioPlus(TenantScopedBase, Base):
    """Tabla de plus salariales por grupo de materia y rol.

    El monto se multiplica por la cantidad de comisiones vigentes
    cuyas materias pertenecen al grupo_plus correspondiente.
    """

    __tablename__ = "salarios_plus"

    grupo = Column(String(50), nullable=False)
    rol = Column(String(20), nullable=False)
    descripcion = Column(String(200), nullable=False, default="")
    monto = Column(Numeric(12, 2), nullable=False)
    desde = Column(Date, nullable=False)
    hasta = Column(Date, nullable=True)

    __table_args__ = (
        CheckConstraint(_ROL_CHECK, name="ck_salarios_plus_rol"),
        Index("ix_salarios_plus_tenant_grupo_rol", "tenant_id", "grupo", "rol"),
        Index("ix_salarios_plus_tenant_desde", "tenant_id", "desde"),
    )

    def __repr__(self) -> str:
        return (
            f"<SalarioPlus grupo={self.grupo!r} rol={self.rol!r} "
            f"monto={self.monto} desde={self.desde}>"
        )
