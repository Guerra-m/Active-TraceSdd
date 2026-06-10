## MODIFIED Requirements

### Requirement: SQLAlchemy Base registers TenantScopedBase metadata
The SQLAlchemy `Base` declarative instance (defined in `core/database.py`) SHALL have its `metadata` reflect all columns declared by `TenantScopedBase` in every model that inherits the mixin. Alembic autogenerate SHALL detect `tenant_id`, `created_at`, `updated_at`, and `deleted_at` columns on any model that inherits `TenantScopedBase`, without additional configuration.

#### Scenario: Base metadata includes mixin columns after model import
- **WHEN** a domain model that inherits `TenantScopedBase` is imported
- **THEN** `Base.metadata.tables` SHALL include that model's table with all mixin columns present

#### Scenario: Alembic autogenerate detects mixin columns
- **WHEN** `alembic revision --autogenerate` is run after adding a new model that inherits `TenantScopedBase`
- **THEN** the generated migration SHALL include `tenant_id`, `created_at`, `updated_at`, and `deleted_at` columns for that model
