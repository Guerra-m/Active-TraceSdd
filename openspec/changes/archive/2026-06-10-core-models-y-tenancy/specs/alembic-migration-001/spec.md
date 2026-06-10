## ADDED Requirements

### Requirement: Alembic migration 001 creates tenants table
The system SHALL have an Alembic migration file at `alembic/versions/` that creates the `tenants` table with columns: `id` (UUID, PK), `name` (VARCHAR NOT NULL UNIQUE), `slug` (VARCHAR NOT NULL UNIQUE), `is_active` (BOOLEAN NOT NULL DEFAULT TRUE), `created_at` (TIMESTAMP WITH TIME ZONE NOT NULL), `updated_at` (TIMESTAMP WITH TIME ZONE NOT NULL). The migration SHALL be reversible (downgrade drops the table).

#### Scenario: Upgrade creates tenants table
- **WHEN** `alembic upgrade head` is executed against an empty database
- **THEN** the `tenants` table SHALL exist with all specified columns and constraints

#### Scenario: Downgrade removes tenants table
- **WHEN** `alembic downgrade base` is executed
- **THEN** the `tenants` table SHALL be dropped and `alembic_version` SHALL be empty

#### Scenario: Migration is idempotent via Alembic version tracking
- **WHEN** `alembic upgrade head` is executed a second time
- **THEN** Alembic SHALL skip the migration (already applied) without error

### Requirement: Alembic migration naming convention
All migration files SHALL follow the naming convention `YYYYMMDD_NNN_short_description.py` (e.g., `20260610_001_create_tenants.py`). The revision ID in `.openspec.yaml` of each change SHALL match the migration file's `revision` variable.

#### Scenario: Migration filename matches convention
- **WHEN** a new migration file is created
- **THEN** its filename SHALL match the pattern `^\d{8}_\d{3}_[a-z_]+\.py$`

### Requirement: Alembic env.py uses async engine
The `alembic/env.py` SHALL use `run_async_migrations()` with `AsyncEngine` from `core/database.py`. It SHALL import the `Base` metadata so that autogenerate detects model changes correctly.

#### Scenario: alembic check passes with no pending changes after migration
- **WHEN** `alembic check` is run after applying migration 001 with the `Tenant` model registered
- **THEN** it SHALL report no pending autogenerate changes
