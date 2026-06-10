## ADDED Requirements

### Requirement: Helper audit() como único punto de escritura al log
El sistema SHALL implementar en `app/core/audit.py` la función async `audit(db: AsyncSession, actor_id: UUID, tenant_id: UUID, accion: str, *, impersonado_id: UUID | None = None, materia_id: UUID | None = None, detalle: dict | None = None, filas_afectadas: int | None = None, ip: str | None = None, user_agent: str | None = None) -> None`. La función crea un `AuditLog` y lo agrega a la sesión sin hacer commit (el commit es responsabilidad del caller o de la transacción de negocio que lo engloba).

#### Scenario: Llamada con parámetros mínimos crea registro en sesión
- **WHEN** se llama `await audit(db, actor_id=user_id, tenant_id=tid, accion="PADRON_CARGAR")`
- **THEN** la sesión contiene un `AuditLog` con los campos correctos y `impersonado_id=None`

#### Scenario: Llamada con todos los parámetros crea registro completo
- **WHEN** se llama `await audit(db, actor_id=uid, tenant_id=tid, accion="CALIFICACIONES_IMPORTAR", impersonado_id=iid, materia_id=mid, detalle={"archivo": "notas.csv"}, filas_afectadas=45, ip="10.0.0.1", user_agent="Mozilla/5.0")`
- **THEN** el `AuditLog` generado contiene todos los campos con los valores indicados

---

### Requirement: Códigos de acción estandarizados mínimos
El sistema SHALL definir como constantes de string en `app/core/audit.py` los códigos de acción mínimos: `CALIFICACIONES_IMPORTAR`, `PADRON_CARGAR`, `COMUNICACION_ENVIAR`, `ASIGNACION_MODIFICAR`, `LIQUIDACION_CERRAR`, `IMPERSONACION_INICIAR`, `IMPERSONACION_FINALIZAR`. Otros módulos pueden usar cualquier string, pero SHOULD usar estas constantes para los casos documentados.

#### Scenario: Constante de acción de impersonación disponible en el módulo
- **WHEN** se importa `from app.core.audit import IMPERSONACION_INICIAR`
- **THEN** el valor es el string `"IMPERSONACION_INICIAR"`

---

### Requirement: AuditLogRepository solo expone insert
El sistema SHALL implementar `app/repositories/audit_log_repository.py` con una clase `AuditLogRepository` que expone únicamente el método `async insert(audit_log: AuditLog) -> None`. No debe tener métodos `get`, `list`, `update` ni `delete`.

#### Scenario: El repositorio no expone métodos de lectura ni borrado
- **WHEN** se inspecciona `AuditLogRepository` en el código
- **THEN** los métodos públicos son solo `insert` (verificable via `dir()` o inspección estática)

#### Scenario: insert persiste el registro en DB
- **WHEN** se llama `await repo.insert(audit_entry)` y se hace commit de la sesión
- **THEN** el registro aparece en `audit_log` al ejecutar un SELECT directo via SQL crudo
