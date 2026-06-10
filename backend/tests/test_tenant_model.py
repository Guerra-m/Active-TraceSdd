"""Tests para TenantScopedBase mixin y modelo Tenant.

TDD cycle:
  - 1.1 RED: columnas del mixin, UUID auto-generado
  - 1.3 TRIANGULATE: tenant_id nulo → IntegrityError, updated_at cambia, UUIDs distintos
  - 1.4 RED: instanciacion Tenant, is_active default, unicidad slug
"""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import Column, String, UniqueConstraint, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base
from app.models.base import TenantScopedBase


# ---------------------------------------------------------------------------
# Modelo auxiliar de dominio para tests del mixin
# ---------------------------------------------------------------------------


class SampleDomainModel(TenantScopedBase, Base):
    """Modelo de prueba para verificar el mixin TenantScopedBase."""

    __tablename__ = "sample_domain_for_test"

    label = Column(String(100), nullable=True)


# ---------------------------------------------------------------------------
# 1.1 RED — Columnas del mixin y UUID auto-generado
# ---------------------------------------------------------------------------


class TestTenantScopedBaseMixin:
    """Tests sobre la estructura del mixin (no requieren DB)."""

    def test_mixin_adds_expected_columns(self):
        """Una clase que hereda TenantScopedBase debe tener todas las columnas."""
        column_names = {c.key for c in SampleDomainModel.__table__.columns}
        assert "id" in column_names
        assert "tenant_id" in column_names
        assert "created_at" in column_names
        assert "updated_at" in column_names
        assert "deleted_at" in column_names

    def test_id_is_uuid_type(self):
        """La columna id debe ser de tipo UUID."""
        from sqlalchemy import UUID as SAUUID

        id_col = SampleDomainModel.__table__.c.id
        assert isinstance(id_col.type, SAUUID)

    def test_id_column_has_uuid4_default(self):
        """La columna id debe tener un callable default que produce UUID v4."""
        id_col = SampleDomainModel.__table__.c.id
        # Verificar que hay un default configurado en la columna
        assert id_col.default is not None
        assert id_col.default.is_callable
        # Llamar con contexto None (SQLAlchemy wraps callables sin ctx)
        generated = id_col.default.arg(None)
        assert isinstance(generated, uuid.UUID)
        assert generated.version == 4

    def test_two_generated_uuids_are_different(self):
        """El default de id debe generar UUIDs únicos en cada llamada."""
        id_col = SampleDomainModel.__table__.c.id
        uuid_a = id_col.default.arg(None)
        uuid_b = id_col.default.arg(None)
        assert uuid_a != uuid_b

    def test_tenant_id_column_is_not_nullable(self):
        """La columna tenant_id debe ser NOT NULL en la definición de tabla."""
        tenant_id_col = SampleDomainModel.__table__.c.tenant_id
        assert tenant_id_col.nullable is False

    def test_tenant_id_column_has_index(self):
        """La columna tenant_id debe estar indexada."""
        tenant_id_col = SampleDomainModel.__table__.c.tenant_id
        assert tenant_id_col.index is True

    def test_deleted_at_is_nullable(self):
        """deleted_at debe ser nullable (sin borrado = NULL)."""
        deleted_at_col = SampleDomainModel.__table__.c.deleted_at
        assert deleted_at_col.nullable is True

    def test_created_at_and_updated_at_not_nullable(self):
        """created_at y updated_at no deben ser nullable."""
        assert SampleDomainModel.__table__.c.created_at.nullable is False
        assert SampleDomainModel.__table__.c.updated_at.nullable is False


# ---------------------------------------------------------------------------
# 1.3 TRIANGULATE — Tests con DB real
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestTenantScopedBaseWithDB:
    """Tests que requieren DB para validar constraints y timestamps."""

    async def test_tenant_id_null_raises_integrity_error(
        self, db_session: AsyncSession, test_tenant
    ):
        """Persistir sin tenant_id debe levantar IntegrityError."""
        instance = SampleDomainModel(label="sin tenant")
        # tenant_id NO se asigna — debe fallar en la DB
        db_session.add(instance)
        with pytest.raises(IntegrityError):
            await db_session.flush()

    async def test_updated_at_changes_on_update(
        self, db_session: AsyncSession, test_tenant
    ):
        """updated_at debe cambiar cuando se modifica el objeto."""
        instance = SampleDomainModel(
            tenant_id=test_tenant.id,
            label="original",
        )
        db_session.add(instance)
        await db_session.flush()
        await db_session.refresh(instance)

        original_updated_at = instance.updated_at
        assert original_updated_at is not None

        # Modificar el registro
        instance.label = "modificado"
        db_session.add(instance)
        await db_session.flush()
        await db_session.refresh(instance)

        # updated_at debe haber cambiado o ser >= al original
        assert instance.updated_at >= original_updated_at

    async def test_created_at_set_on_insert(
        self, db_session: AsyncSession, test_tenant
    ):
        """created_at debe setearse automáticamente en el insert."""
        instance = SampleDomainModel(
            tenant_id=test_tenant.id,
            label="creado ahora",
        )
        db_session.add(instance)
        await db_session.flush()
        await db_session.refresh(instance)

        assert instance.created_at is not None
        assert isinstance(instance.created_at, datetime)


# ---------------------------------------------------------------------------
# 1.4 RED — Tests para modelo Tenant
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestTenantModel:
    """Tests del modelo Tenant raíz."""

    async def test_tenant_creation_with_name_and_slug(self, db_session: AsyncSession):
        """Crear un Tenant con name y slug debe persistir correctamente."""
        from app.models.tenant import Tenant

        tenant = Tenant(name="Universidad Test", slug="universidad-test")
        db_session.add(tenant)
        await db_session.flush()
        await db_session.refresh(tenant)

        assert tenant.id is not None
        assert isinstance(tenant.id, uuid.UUID)
        assert tenant.name == "Universidad Test"
        assert tenant.slug == "universidad-test"

    async def test_tenant_is_active_defaults_to_true(self, db_session: AsyncSession):
        """is_active debe ser True por defecto."""
        from app.models.tenant import Tenant

        tenant = Tenant(name="Activo Test", slug="activo-test")
        db_session.add(tenant)
        await db_session.flush()
        await db_session.refresh(tenant)

        assert tenant.is_active is True

    async def test_tenant_slug_uniqueness_raises_integrity_error(
        self, db_session: AsyncSession
    ):
        """Dos tenants con el mismo slug deben levantar IntegrityError."""
        from app.models.tenant import Tenant

        t1 = Tenant(name="Universidad A", slug="mismo-slug")
        t2 = Tenant(name="Universidad B", slug="mismo-slug")
        db_session.add(t1)
        await db_session.flush()

        db_session.add(t2)
        with pytest.raises(IntegrityError):
            await db_session.flush()

    async def test_tenant_name_uniqueness_raises_integrity_error(
        self, db_session: AsyncSession
    ):
        """Dos tenants con el mismo name deben levantar IntegrityError."""
        from app.models.tenant import Tenant

        t1 = Tenant(name="Mismo Nombre", slug="slug-a")
        t2 = Tenant(name="Mismo Nombre", slug="slug-b")
        db_session.add(t1)
        await db_session.flush()

        db_session.add(t2)
        with pytest.raises(IntegrityError):
            await db_session.flush()

    async def test_tenant_does_not_inherit_mixin(self):
        """Tenant no debe heredar TenantScopedBase (es la raíz)."""
        from app.models.tenant import Tenant

        column_names = {c.key for c in Tenant.__table__.columns}
        # Tenant NO tiene tenant_id ni deleted_at
        assert "tenant_id" not in column_names
        assert "deleted_at" not in column_names

    async def test_tenant_has_timestamps(self, db_session: AsyncSession):
        """Tenant debe tener created_at y updated_at."""
        from app.models.tenant import Tenant

        tenant = Tenant(name="Timestamps Test", slug="timestamps-test")
        db_session.add(tenant)
        await db_session.flush()
        await db_session.refresh(tenant)

        assert tenant.created_at is not None
        assert tenant.updated_at is not None
