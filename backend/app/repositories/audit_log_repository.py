"""Repository de solo-escritura para el log de auditoría.

AuditLogRepository expone únicamente insert() — ningún método de lectura,
actualización ni borrado. Esto hace imposible errar accidentalmente en la
dirección de append-only a nivel de código de aplicación.

La inmutabilidad a nivel DB está garantizada por el trigger de migración 004.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditLogRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def insert(self, audit_log: AuditLog) -> None:
        """Agrega el registro al log. No hace commit — responsabilidad del caller."""
        self._db.add(audit_log)
        await self._db.flush()
