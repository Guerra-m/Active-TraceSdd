## ADDED Requirements

### Requirement: Preview y envío de comunicación a atrasados
El sistema SHALL permitir al profesor enviar comunicaciones a alumnos atrasados con un paso de preview antes del envío, consumiendo `POST /api/comunicaciones/`.

#### Scenario: Flujo completo de envío
- **WHEN** el profesor configura el mensaje y confirma
- **THEN** el sistema muestra el preview, el profesor confirma y el sistema llama al endpoint de envío

#### Scenario: Cancelar antes de enviar
- **WHEN** el profesor ve el preview y cancela
- **THEN** el sistema vuelve al formulario sin enviar

#### Scenario: Error en envío
- **WHEN** el endpoint retorna error
- **THEN** el sistema muestra el mensaje de error y permite reintentar

### Requirement: Tracking de estado de comunicación
El sistema SHALL mostrar el estado actualizado de las comunicaciones enviadas consumiendo `GET /api/comunicaciones/{id}/estado` con polling cada 3 segundos mientras el estado sea PENDIENTE o ENVIANDO.

#### Scenario: Estado evoluciona a ENVIADO
- **WHEN** la comunicación pasa de ENVIANDO a ENVIADO
- **THEN** el sistema actualiza la UI automáticamente con badge verde

#### Scenario: Estado FALLIDO
- **WHEN** la comunicación queda en estado FALLIDO
- **THEN** el sistema muestra badge rojo con el motivo del fallo

#### Scenario: Polling se detiene en estado final
- **WHEN** el estado es ENVIADO o FALLIDO o CANCELADO
- **THEN** el polling se detiene automáticamente
