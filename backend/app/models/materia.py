"""Modelo ORM para la entidad Materia (E3 — catálogo plano por tenant).

Materia es el catálogo único de materias de un tenant (ADR-006 cerrada).
No está anidada bajo ninguna carrera. El código es único por tenant.
Las instancias de cursado (Dictado = materia × carrera × cohorte) se
crean en changes posteriores cuando los módulos académicos los requieran.

Soft delete via TenantScopedBase — nunca hard delete.
"""

from sqlalchemy import CheckConstraint, Column, Index, String, UniqueConstraint

from app.core.database import Base
from app.models.base import TenantScopedBase


class Materia(TenantScopedBase, Base):
    """Catálogo de materias del tenant."""

    __tablename__ = "materias"

    codigo = Column(String(50), nullable=False)
    nombre = Column(String(200), nullable=False)
    estado = Column(String(20), nullable=False, default="Activa", server_default="Activa")

    # PA-22 resuelto: clave de Plus para esta materia; NULL = no genera Plus
    grupo_plus = Column(String(50), nullable=True, default=None)

    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo", name="uq_materias_tenant_codigo"),
        CheckConstraint("estado IN ('Activa', 'Inactiva')", name="ck_materias_estado"),
        Index("ix_materias_tenant", "tenant_id"),
    )

    def __repr__(self) -> str:
        return f"<Materia codigo={self.codigo!r} estado={self.estado!r} tenant={self.tenant_id}>"
