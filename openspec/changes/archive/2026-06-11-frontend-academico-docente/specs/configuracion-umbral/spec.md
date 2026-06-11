## ADDED Requirements

### Requirement: Configurar umbral de aprobación
El sistema SHALL permitir al profesor configurar el porcentaje de umbral de aprobación para su materia/comisión mediante `PUT /api/umbrales/{id}`.

#### Scenario: Guardar umbral exitoso
- **WHEN** el profesor ingresa un valor válido (0-100) y guarda
- **THEN** el sistema actualiza el umbral y muestra feedback de éxito

#### Scenario: Valor de umbral inválido
- **WHEN** el profesor ingresa un valor fuera del rango 0-100
- **THEN** el sistema muestra el error de validación y bloquea el submit

#### Scenario: Carga inicial del umbral actual
- **WHEN** el profesor accede a la página de configuración
- **THEN** el sistema muestra el valor de umbral actualmente configurado
