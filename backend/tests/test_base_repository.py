"""Tests para BaseRepository[T] con scope de tenant obligatorio.

TDD cycle:
  - 3.1 RED         : aislamiento multi-tenant (tenant A no ve datos de B)
  - 3.3 TRIANGULATE : soft_delete inexistente → False, list excluye deleted,
                      create inyecta tenant_id, sin tenant_id → TypeError
"""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import Column, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base
from app.models.base import TenantScopedBase


# ---------------------------------------------------------------------------
# Modelo auxiliar para tests del repository (no va a produccion)
# ---------------------------------------------------------------------------


class DomainItem(TenantScopedBase, Base):
    """Modelo auxiliar para tests de BaseRepository."""

    __tablename__ = "test_domain_items"

    title = Column(String(200), nullable=True)


# ---------------------------------------------------------------------------
# 3.1 RED — Aislamiento multi-tenant
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestBaseRepositoryTenantIsolation:
    """El repository del tenant A no puede ver datos del tenant B."""

    async def test_tenant_a_cannot_see_tenant_b_record(
        self,
        db_session: AsyncSession,
        test_tenant,
        test_tenant_b,
    ):
        """get_by_id de repo del tenant A no debe retornar registro del tenant B."""
        from app.repositories.base import BaseRepository

        # Crear registro del tenant B directamente en DB
        item_b = DomainItem(tenant_id=test_tenant_b.id, title="item de B")
        db_session.add(item_b)
        await db_session.flush()
        await db_session.refresh(item_b)

        # Repository del tenant A intenta acceder al item de B
        repo_a = BaseRepository(db_session, tenant_id=test_tenant.id, model=DomainItem)
        result = await repo_a.get_by_id(item_b.id)

        assert result is None, (
            f"Tenant A no debe ver el item {item_b.id} que pertenece a Tenant B"
        )

    async def test_list_returns_only_own_tenant_records(
        self,
        db_session: AsyncSession,
        test_tenant,
        test_tenant_b,
    ):
        """list() solo debe retornar registros del propio tenant."""
        from app.repositories.base import BaseRepository

        # Crear items para ambos tenants
        item_a = DomainItem(tenant_id=test_tenant.id, title="item de A")
        item_b = DomainItem(tenant_id=test_tenant_b.id, title="item de B")
        db_session.add(item_a)
        db_session.add(item_b)
        await db_session.flush()

        repo_a = BaseRepository(db_session, tenant_id=test_tenant.id, model=DomainItem)
        items = await repo_a.list()

        ids = {i.id for i in items}
        assert item_a.id in ids
        assert item_b.id not in ids, "Tenant A no debe ver items de Tenant B"

    async def test_get_by_id_returns_own_tenant_record(
        self,
        db_session: AsyncSession,
        test_tenant,
    ):
        """get_by_id debe retornar el registro correcto del propio tenant."""
        from app.repositories.base import BaseRepository

        item = DomainItem(tenant_id=test_tenant.id, title="mi item")
        db_session.add(item)
        await db_session.flush()
        await db_session.refresh(item)

        repo = BaseRepository(db_session, tenant_id=test_tenant.id, model=DomainItem)
        result = await repo.get_by_id(item.id)

        assert result is not None
        assert result.id == item.id
        assert result.title == "mi item"


# ---------------------------------------------------------------------------
# 3.2 GREEN — CRUD operations
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestBaseRepositoryCRUD:
    """Tests de las operaciones CRUD del BaseRepository."""

    async def test_create_sets_tenant_id_automatically(
        self,
        db_session: AsyncSession,
        test_tenant,
    ):
        """create() debe inyectar tenant_id del repo en el objeto."""
        from app.repositories.base import BaseRepository

        repo = BaseRepository(db_session, tenant_id=test_tenant.id, model=DomainItem)
        item = DomainItem(title="auto tenant")
        # SIN asignar tenant_id — el repo debe inyectarlo

        created = await repo.create(item)

        assert created.tenant_id == test_tenant.id
        assert created.id is not None

    async def test_create_persists_and_returns_object(
        self,
        db_session: AsyncSession,
        test_tenant,
    ):
        """create() debe persistir el objeto y devolverlo con id."""
        from app.repositories.base import BaseRepository

        repo = BaseRepository(db_session, tenant_id=test_tenant.id, model=DomainItem)
        item = DomainItem(title="persistir")
        created = await repo.create(item)

        assert created.id is not None
        assert created.title == "persistir"

    async def test_soft_delete_marks_deleted_at(
        self,
        db_session: AsyncSession,
        test_tenant,
    ):
        """soft_delete() debe setear deleted_at y retornar True."""
        from app.repositories.base import BaseRepository

        repo = BaseRepository(db_session, tenant_id=test_tenant.id, model=DomainItem)
        item = DomainItem(tenant_id=test_tenant.id, title="a borrar")
        db_session.add(item)
        await db_session.flush()
        await db_session.refresh(item)

        result = await repo.soft_delete(item.id)

        assert result is True
        await db_session.refresh(item)
        assert item.deleted_at is not None

    async def test_soft_delete_record_not_in_list(
        self,
        db_session: AsyncSession,
        test_tenant,
    ):
        """list() no debe incluir registros con deleted_at IS NOT NULL."""
        from app.repositories.base import BaseRepository

        repo = BaseRepository(db_session, tenant_id=test_tenant.id, model=DomainItem)

        # Crear y soft-deletear
        item = DomainItem(tenant_id=test_tenant.id, title="borrado")
        db_session.add(item)
        await db_session.flush()
        await db_session.refresh(item)

        await repo.soft_delete(item.id)
        await db_session.flush()

        items = await repo.list()
        ids = {i.id for i in items}
        assert item.id not in ids, "Registros soft-deleted no deben aparecer en list()"

    async def test_soft_delete_record_not_found_by_get_by_id(
        self,
        db_session: AsyncSession,
        test_tenant,
    ):
        """get_by_id no debe retornar registros soft-deleted."""
        from app.repositories.base import BaseRepository

        repo = BaseRepository(db_session, tenant_id=test_tenant.id, model=DomainItem)
        item = DomainItem(tenant_id=test_tenant.id, title="invisible")
        db_session.add(item)
        await db_session.flush()
        await db_session.refresh(item)

        await repo.soft_delete(item.id)
        await db_session.flush()

        result = await repo.get_by_id(item.id)
        assert result is None


# ---------------------------------------------------------------------------
# 3.3 TRIANGULATE — Casos edge del repository
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestBaseRepositoryEdgeCases:
    """Casos edge y restricciones del BaseRepository."""

    async def test_soft_delete_nonexistent_id_returns_false(
        self,
        db_session: AsyncSession,
        test_tenant,
    ):
        """soft_delete() de ID inexistente debe retornar False sin levantar."""
        from app.repositories.base import BaseRepository

        repo = BaseRepository(db_session, tenant_id=test_tenant.id, model=DomainItem)
        nonexistent = uuid.uuid4()

        result = await repo.soft_delete(nonexistent)

        assert result is False

    async def test_create_without_explicit_tenant_id_uses_repo_tenant(
        self,
        db_session: AsyncSession,
        test_tenant,
    ):
        """Si el objeto no tiene tenant_id, create() debe asignar el del repo."""
        from app.repositories.base import BaseRepository

        repo = BaseRepository(db_session, tenant_id=test_tenant.id, model=DomainItem)
        item = DomainItem(title="sin tenant explicito")
        # tenant_id NO seteado en el objeto

        created = await repo.create(item)
        assert created.tenant_id == test_tenant.id

    async def test_list_with_offset_and_limit(
        self,
        db_session: AsyncSession,
        test_tenant,
    ):
        """list(offset, limit) debe paginar correctamente."""
        from app.repositories.base import BaseRepository

        repo = BaseRepository(db_session, tenant_id=test_tenant.id, model=DomainItem)

        # Crear 5 items
        for i in range(5):
            db_session.add(DomainItem(tenant_id=test_tenant.id, title=f"item {i}"))
        await db_session.flush()

        page1 = await repo.list(offset=0, limit=2)
        page2 = await repo.list(offset=2, limit=2)

        assert len(page1) == 2
        assert len(page2) == 2
        # No deben solaparse
        ids1 = {i.id for i in page1}
        ids2 = {i.id for i in page2}
        assert ids1.isdisjoint(ids2)

    def test_repository_requires_tenant_id(self, db_session: AsyncSession):
        """Instanciar BaseRepository sin tenant_id debe levantar TypeError."""
        from app.repositories.base import BaseRepository

        with pytest.raises(TypeError):
            BaseRepository(db_session, model=DomainItem)  # type: ignore[call-arg]

    async def test_update_persists_changes(
        self,
        db_session: AsyncSession,
        test_tenant,
    ):
        """update() debe persistir los cambios."""
        from app.repositories.base import BaseRepository

        repo = BaseRepository(db_session, tenant_id=test_tenant.id, model=DomainItem)
        item = DomainItem(tenant_id=test_tenant.id, title="original")
        db_session.add(item)
        await db_session.flush()
        await db_session.refresh(item)

        item.title = "modificado"
        updated = await repo.update(item)

        assert updated.title == "modificado"
