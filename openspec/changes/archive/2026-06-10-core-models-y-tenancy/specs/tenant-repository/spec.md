## ADDED Requirements

### Requirement: BaseRepository generic with mandatory tenant scope
The system SHALL provide a generic `BaseRepository[T]` class that wraps SQLAlchemy async session operations. It SHALL be initialized with `(session: AsyncSession, tenant_id: UUID)`. Every SELECT query issued by the repository SHALL automatically include `WHERE tenant_id = :tenant_id AND deleted_at IS NULL`.

#### Scenario: get_by_id returns only records from the requesting tenant
- **WHEN** `repo.get_by_id(some_id)` is called with a `tenant_id` of Tenant A
- **THEN** it SHALL return the record only if `record.tenant_id == tenant_a_id`

#### Scenario: cross-tenant isolation — record from another tenant is invisible
- **WHEN** Tenant B's repository attempts to fetch a record owned by Tenant A using its `id`
- **THEN** the result SHALL be `None` (not a 403, just not found — tenant scope is transparent)

#### Scenario: list returns only active, non-deleted records of the tenant
- **WHEN** `repo.list()` is called
- **THEN** it SHALL return only records where `tenant_id` matches and `deleted_at IS NULL`

### Requirement: BaseRepository CRUD operations
The repository SHALL provide async methods: `get_by_id(id: UUID) -> T | None`, `list(offset: int, limit: int) -> list[T]`, `create(obj: T) -> T`, `update(obj: T) -> T`, `soft_delete(id: UUID) -> bool`.

#### Scenario: create sets tenant_id automatically
- **WHEN** `repo.create(obj)` is called with a model instance that has no `tenant_id`
- **THEN** `obj.tenant_id` SHALL be set to the repository's `tenant_id` before persisting

#### Scenario: soft_delete marks deleted_at and returns True
- **WHEN** `repo.soft_delete(existing_id)` is called
- **THEN** the record's `deleted_at` SHALL be set to now and the method SHALL return `True`

#### Scenario: soft_delete on non-existent id returns False
- **WHEN** `repo.soft_delete(unknown_id)` is called
- **THEN** the method SHALL return `False` without raising an exception

#### Scenario: update persists changes and refreshes updated_at
- **WHEN** `repo.update(modified_obj)` is called
- **THEN** the changes SHALL be persisted and `updated_at` SHALL be greater than its previous value

### Requirement: Tenant scope enforced — no escape hatch
The system SHALL NOT provide any method on `BaseRepository` that executes a query without the `tenant_id` filter. Code review MUST reject any such method. There SHALL be no `get_all_tenants()` or equivalent cross-tenant bulk query in the base class.

#### Scenario: Repository initialization requires tenant_id
- **WHEN** `BaseRepository` is instantiated without `tenant_id`
- **THEN** a `TypeError` SHALL be raised (required parameter)
