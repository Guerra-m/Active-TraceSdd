---
name: trace-multitenant-repository
description: >
  Patrones de repository con scope de tenant obligatorio para active-trace.
  Cubre cómo extender el base repository, filtrar siempre por tenant_id,
  y los antipatrones que fallan en code review.
  Trigger: al implementar cualquier repository, endpoint o query que acceda
  a tablas del dominio en active-trace.
license: MIT
metadata:
  author: active-trace-team
  version: "1.0"
---

## Cuándo usar esta skill

- Crear o modificar un repository en `backend/app/repositories/`.
- Escribir queries SQLAlchemy que toquen tablas del dominio (usuarios, calificaciones, comunicaciones, etc.).
- Revisar código que accede a la DB para detectar escapes de tenant scope.

**No usar cuando:** solo se trabaja con tablas globales del sistema (`roles`, `permisos`, `tenants`) que no tienen `tenant_id`.

---

## Regla fundamental

> **Todo query sobre una tabla de dominio DEBE filtrar por `tenant_id`.**  
> Un query sin scope de tenant es un bug de seguridad que falla en code review sin excepción.

---

## Patrones críticos

### 1. Extender el base repository

Todos los repositories heredan de `BaseRepository` que inyecta `tenant_id` automáticamente
en cada query. Nunca instanciar `select()` directo sin pasar por el método del base.

```python
# ✅ CORRECTO — hereda scope automático
class CalificacionRepository(BaseRepository[Calificacion]):
    async def list_by_asignacion(self, asignacion_id: str) -> list[Calificacion]:
        stmt = (
            select(Calificacion)
            .where(
                Calificacion.tenant_id == self.tenant_id,   # siempre explícito también
                Calificacion.asignacion_id == asignacion_id,
                Calificacion.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

# ❌ INCORRECTO — query sin tenant scope
stmt = select(Calificacion).where(Calificacion.asignacion_id == asignacion_id)
```

### 2. Soft delete obligatorio — nunca hard delete

```python
# ✅ CORRECTO
entity.deleted_at = datetime.now(timezone.utc)
await db.commit()

# ❌ INCORRECTO — viola auditoría append-only
await db.delete(entity)
```

### 3. Inyectar tenant_id desde el JWT, nunca del request body

```python
# ✅ CORRECTO — tenant viene del usuario autenticado
async def create_aviso(
    data: AvisoCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    aviso = Aviso(tenant_id=current_user.tenant_id, **data.model_dump())

# ❌ INCORRECTO — nunca confiar en tenant_id del cliente
async def create_aviso(data: AvisoCreate):  # data incluye tenant_id → exploit
```

### 4. Aislamiento en joins

Al hacer join entre tablas, filtrar `tenant_id` en AMBAS:

```python
stmt = (
    select(Calificacion, EntradaPadron)
    .join(EntradaPadron, Calificacion.entrada_padron_id == EntradaPadron.id)
    .where(
        Calificacion.tenant_id == tenant_id,      # tabla principal
        EntradaPadron.tenant_id == tenant_id,     # tabla joined también
        Calificacion.deleted_at.is_(None),
        EntradaPadron.deleted_at.is_(None),
    )
)
```

---

## Antipatrones que fallan en code review

| Antipatrón | Por qué falla |
|------------|---------------|
| `select(Model)` sin `.where(Model.tenant_id == ...)` | Un tenant puede leer datos de otro |
| `db.delete(entity)` | Viola auditoría — todo es soft delete |
| `tenant_id` en el body del request | El cliente puede impersonar otro tenant |
| Join sin filtro de tenant en la tabla secundaria | Fuga de datos cross-tenant en el join |
| `query.first()` sin scope | Puede retornar el registro del tenant equivocado |

---

## Checklist antes de hacer PR

- [ ] Cada `select()` tiene `.where(Model.tenant_id == current_user.tenant_id)`
- [ ] Cada `select()` tiene `.where(Model.deleted_at.is_(None))`  
- [ ] No hay ningún `db.delete()` — solo soft delete via `deleted_at`
- [ ] El `tenant_id` se inyecta desde `current_user`, no del request
- [ ] Los joins filtran `tenant_id` en todas las tablas involucradas

---

## Archivos de referencia en active-trace

- Base repository: `backend/app/repositories/base.py`
- Ejemplo correcto: `backend/app/repositories/comunicacion_repository.py`
- Guard de identidad: `backend/app/core/deps.py` (`get_current_user`)
- Modelo con mixin: `backend/app/models/base.py`
