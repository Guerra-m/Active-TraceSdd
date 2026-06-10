## ADDED Requirements

### Requirement: Tenant entity as system root
The system SHALL define a `Tenant` SQLAlchemy model representing an institution. It SHALL have: `id` (UUID v4, PK, server-generated), `name` (non-empty text, unique), `slug` (lowercase kebab-case, unique, used in URLs), `is_active` (boolean, default True), `created_at` (UTC datetime, auto-set on insert), `updated_at` (UTC datetime, auto-updated on change).

#### Scenario: Tenant model creation
- **WHEN** a `Tenant` instance is created with `name` and `slug`
- **THEN** it SHALL have a non-null UUID `id` generated automatically, `is_active=True`, and `created_at` set to the current UTC time

#### Scenario: Tenant slug uniqueness
- **WHEN** two tenants are created with the same `slug`
- **THEN** the database SHALL raise an IntegrityError (unique constraint violation)

### Requirement: TenantScopedBase mixin for all domain models
The system SHALL provide a `TenantScopedBase` Python mixin that any domain model can inherit alongside the SQLAlchemy `Base`. The mixin SHALL declare: `id` (UUID v4, PK), `tenant_id` (UUID, FK → `tenants.id`, NOT NULL, indexed), `created_at` (UTC datetime, auto-set), `updated_at` (UTC datetime, auto-updated), `deleted_at` (UTC datetime, nullable — soft delete marker).

#### Scenario: Domain model inherits mixin columns
- **WHEN** a domain model class inherits `TenantScopedBase`
- **THEN** it SHALL automatically have `id`, `tenant_id`, `created_at`, `updated_at`, and `deleted_at` columns without redeclaring them

#### Scenario: tenant_id is non-nullable
- **WHEN** an attempt is made to persist a domain model instance without a `tenant_id`
- **THEN** the database SHALL raise an IntegrityError (NOT NULL constraint)

#### Scenario: UUID auto-generation
- **WHEN** a domain model instance is created without explicitly setting `id`
- **THEN** `id` SHALL be a new UUID v4 value distinct from any previously generated UUID

#### Scenario: Timestamps auto-populated
- **WHEN** a domain model instance is first persisted
- **THEN** `created_at` and `updated_at` SHALL be set to the current UTC datetime

#### Scenario: updated_at reflects last modification
- **WHEN** a domain model instance is updated and re-persisted
- **THEN** `updated_at` SHALL be greater than its previous value

### Requirement: Soft delete via deleted_at timestamp
The system SHALL never physically delete domain model rows. Instead, deletion SHALL set `deleted_at` to the current UTC timestamp. Rows with `deleted_at IS NOT NULL` are considered deleted and SHALL NOT appear in standard queries.

#### Scenario: Soft delete sets timestamp
- **WHEN** `soft_delete()` is called on a domain model instance
- **THEN** `deleted_at` SHALL be set to the current UTC datetime and the row SHALL remain in the database

#### Scenario: Hard delete is not available
- **WHEN** code attempts to call a hard-delete method on a domain model
- **THEN** no such method SHALL exist on the base mixin or `BaseRepository`
