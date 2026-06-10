"""Modelo ORM para EntradaPadron (C-09 padron-ingesta-moodle).

Cada fila representa un alumno en una versión de padrón.
email_encrypted almacena el email cifrado con AES-256-GCM (PII — nunca texto plano).
usuario_id es nullable: el alumno puede no tener cuenta en el sistema aún.
"""

from sqlalchemy import Column, ForeignKey, Index, String, Text
from sqlalchemy import UUID as SAUUID

from app.core.database import Base
from app.models.base import TenantScopedBase


class EntradaPadron(TenantScopedBase, Base):
    """Alumno registrado en una versión de padrón."""

    __tablename__ = "entrada_padron"

    version_id = Column(
        SAUUID(as_uuid=True),
        ForeignKey("version_padron.id", ondelete="RESTRICT"),
        nullable=False,
    )
    # nullable: alumno puede no tener cuenta en el sistema
    usuario_id = Column(
        SAUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    nombre = Column(String(200), nullable=False)
    apellidos = Column(String(200), nullable=False)
    # PII cifrada AES-256-GCM — nunca texto plano en DB
    email_encrypted = Column(Text, nullable=False)
    comision = Column(String(100), nullable=True)
    regional = Column(String(100), nullable=True)

    __table_args__ = (
        Index("ix_entrada_padron_tenant_version", "tenant_id", "version_id"),
        Index("ix_entrada_padron_tenant_usuario", "tenant_id", "usuario_id"),
    )

    def __repr__(self) -> str:
        return f"<EntradaPadron id={self.id} version={self.version_id} usuario={self.usuario_id}>"
