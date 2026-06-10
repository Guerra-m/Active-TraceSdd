## MODIFIED Requirements

### Requirement: audit_log registra referencia opcional a materia
El sistema SHALL almacenar en `audit_log` una referencia opcional al `id` de la materia afectada por una acción auditada. El campo `materia_id` SHALL ser `UUID`, nullable, con FK a `materias.id` con `ON DELETE SET NULL`. La FK es deferida respecto a la creación del modelo AuditLog (se añade en la migración de C-06 para evitar dependencia circular). Las filas existentes sin `materia_id` son válidas (NULL). El trigger de inmutabilidad protege todas las filas incluyendo aquellas con `materia_id` nulo.

#### Scenario: Insertar registro de audit con materia_id válida
- **WHEN** una acción auditada referencia una materia que existe en el tenant
- **THEN** el sistema inserta el registro en `audit_log` con `materia_id` igual al UUID de esa materia y la FK no viola integridad referencial

#### Scenario: Insertar registro de audit sin materia_id
- **WHEN** una acción auditada no está relacionada con ninguna materia específica
- **THEN** el sistema inserta el registro con `materia_id = NULL` sin error

#### Scenario: FK audit_log.materia_id con ON DELETE SET NULL
- **WHEN** una materia es soft-deleted (su fila en `materias` permanece con `deleted_at` poblado)
- **THEN** los registros de audit_log que la referencian mantienen el `materia_id` intacto (la fila de materias no desaparece, el soft delete no viola la FK)
