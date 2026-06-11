## ADDED Requirements

### Requirement: Editar instancia de encuentro individualmente (RN-14)
El sistema SHALL permitir `PATCH /api/v1/encuentros/{id}` para editar `estado`, `meet_url`, `video_url` y `comentario` de una instancia. Cada instancia es independiente: modificarla no afecta al slot ni a otras instancias del mismo slot.

#### Scenario: Marcar instancia como Realizado con video_url
- **WHEN** se envía `PATCH /encuentros/<id>` con `{"estado": "Realizado", "video_url": "https://..."}`
- **THEN** el sistema actualiza solo esa instancia, retorna 200 con la instancia actualizada; el slot y las demás instancias del mismo slot no cambian

#### Scenario: Edición parcial — solo comentario
- **WHEN** se envía `PATCH /encuentros/<id>` con `{"comentario": "Reunión reprogramada"}`
- **THEN** solo el comentario se actualiza; estado, meet_url y video_url permanecen igual

#### Scenario: Instancia de otro tenant
- **WHEN** se intenta editar una instancia que pertenece a un tenant distinto al del JWT
- **THEN** el sistema retorna 404

### Requirement: Listar instancias con filtros
El sistema SHALL retornar `GET /api/v1/encuentros` con filtros opcionales por `materia_id`, `estado`, `fecha_desde`, `fecha_hasta`. Solo instancias no eliminadas del tenant del actor.

#### Scenario: Filtrar por estado Programado
- **WHEN** se llama `GET /encuentros?estado=Programado`
- **THEN** el sistema retorna solo las instancias con `estado="Programado"` del tenant

#### Scenario: Filtrar por rango de fechas
- **WHEN** se llama con `fecha_desde=2024-03-01&fecha_hasta=2024-03-31`
- **THEN** el sistema retorna solo instancias cuya `fecha` cae dentro del rango inclusivo
