---
name: trace-pii-encryption
description: >
  Patrones de cifrado y comparación de PII (email, DNI, CUIL, CBU) con AES-256-GCM
  en active-trace. Cubre cuándo cifrar, cómo comparar sin exponer valores,
  el patrón email_hash para búsquedas, y los bugs frecuentes con datos cifrados.
  Trigger: al tocar campos PII (email, dni, cuil, cbu, alias_cbu) en modelos,
  repositories o endpoints de active-trace.
license: MIT
metadata:
  author: active-trace-team
  version: "1.0"
---

## Cuándo usar esta skill

- Leer, escribir o comparar los campos `email_encrypted`, `dni_encrypted`, `cuil_encrypted`, `cbu_encrypted`, `alias_cbu_encrypted` en cualquier modelo.
- Implementar búsqueda por email u otro campo PII.
- Debuggear por qué un alumno no encuentra sus calificaciones o mensajes (causa más frecuente: comparación de cifrados).
- Crear seeds o fixtures que usen emails reales.

---

## Campos PII en active-trace

| Modelo | Campos cifrados | Campo hash (para búsqueda) |
|--------|----------------|---------------------------|
| `Usuario` | `email_encrypted`, `dni_encrypted`, `cuil_encrypted`, `cbu_encrypted`, `alias_cbu_encrypted` | `email_hash` |
| `EntradaPadron` | `email_encrypted` | — |
| `Comunicacion` | `destinatario_encrypted` | — |

> **Regla**: los campos terminados en `_encrypted` nunca se comparan directamente entre sí — dos cifrados del mismo valor producen bytes distintos (IV aleatorio por cifrado).

---

## Patrones críticos

### 1. Cifrar al escribir, descifrar al leer

```python
from app.core.encryption import encrypt, decrypt

# Al crear o actualizar
usuario.email_encrypted = encrypt(email_plano)
usuario.email_hash = hash_email(email_plano)   # para búsqueda rápida

# Al leer para mostrar
email_visible = decrypt(usuario.email_encrypted)
```

### 2. Buscar por email — usar el hash, no el cifrado

```python
from app.core.security import hash_email

# ✅ CORRECTO — búsqueda O(1) por hash
email_hash = hash_email(email_buscado)
stmt = select(Usuario).where(
    Usuario.tenant_id == tenant_id,
    Usuario.email_hash == email_hash,
)

# ❌ INCORRECTO — nunca funciona, AES-GCM usa IV aleatorio
stmt = select(Usuario).where(
    Usuario.email_encrypted == encrypt(email_buscado)  # distinto cada vez
)
```

### 3. Comparar emails entre tablas distintas (auto-link alumno)

Cuando `EntradaPadron` no tiene `email_hash`, la comparación debe hacerse en Python
descifrado, no en SQL:

```python
user_email = decrypt(current_user.email_encrypted).lower().strip()

# Traer todos los EPs no vinculados y comparar en memoria
unlinked = (await db.execute(
    select(EntradaPadron).where(
        EntradaPadron.tenant_id == tenant_id,
        EntradaPadron.usuario_id.is_(None),
        EntradaPadron.deleted_at.is_(None),
    )
)).scalars().all()

for ep in unlinked:
    try:
        if decrypt(ep.email_encrypted).lower().strip() == user_email:
            ep.usuario_id = current_user.id
    except Exception:
        continue   # EP con cifrado corrupto — ignorar, no romper el flujo
```

### 4. Nunca loguear PII

```python
# ✅ CORRECTO
logger.info("usuario autenticado", extra={"user_id": str(user.id)})

# ❌ INCORRECTO — el email descifrado no debe aparecer en logs
logger.info(f"autenticado: {decrypt(user.email_encrypted)}")
```

### 5. Seeds y fixtures — cifrar siempre

```python
# ✅ En seeds
ep = EntradaPadron(
    email_encrypted=encrypt("valentina.morales@alumno.utn.edu.ar"),
    tenant_id=TENANT_ID,
    ...
)

# ❌ Nunca guardar en texto plano
ep = EntradaPadron(email="valentina.morales@alumno.utn.edu.ar")  # columna no existe
```

---

## Bug frecuente: alumno no ve sus calificaciones

**Causa más común**: `EntradaPadron.usuario_id` es `None` — el EP existe pero no está vinculado al usuario.

**Diagnóstico**:
```sql
-- Ver EPs del tenant sin usuario vinculado
SELECT id, usuario_id FROM entrada_padron
WHERE tenant_id = '<tenant_id>' AND deleted_at IS NULL AND usuario_id IS NULL;
```

**Solución**: el endpoint `mis-calificaciones` tiene un slow-path que descifra todos los EPs sin `usuario_id` y los compara con el email del usuario autenticado. Si el slow-path no corre, verificar que el endpoint llame a `decrypt()` y no compare cifrados directamente.

---

## Antipatrones que fallan en code review

| Antipatrón | Por qué falla |
|------------|---------------|
| `WHERE email_encrypted = encrypt(x)` en SQL | AES-GCM produce ciphertext distinto cada vez (IV aleatorio) — nunca matchea |
| Loguear `decrypt(campo)` | Expone PII en logs — violación de seguridad |
| Guardar campo PII sin `encrypt()` | Dato en texto plano en la DB |
| Comparar `ep1.email_encrypted == ep2.email_encrypted` | Mismo email cifrado dos veces → bytes distintos |
| No manejar `Exception` en `decrypt()` | Un registro corrupto rompe todo el endpoint |

---

## Archivos de referencia en active-trace

- Utilidad de cifrado: `backend/app/core/encryption.py`
- Hash de email: `backend/app/core/security.py` (`hash_email`)
- Patrón auto-link completo: `backend/app/api/v1/routers/calificaciones.py` (`mis-calificaciones`)
- Modelo con PII: `backend/app/models/usuario.py`
