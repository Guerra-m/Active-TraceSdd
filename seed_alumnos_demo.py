"""
seed_alumnos_demo.py — Crea cuentas de usuario para 3 alumnos demo y linkea sus padrones.

Alumnos (todos de ALGO1 ComA, en seed_testing.py):
  - Facundo Benitez    → al día (notas altas)
  - Valentina Morales  → atrasada (notas bajas, sin algunas entregas)
  - Florencia Vargas   → atrasada (notas muy bajas)

Password para todos: alumno123
"""

import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select

from app.core.config import get_settings
from app.core.encryption import encrypt, decrypt
from app.core.security import hash_email, hash_password
from app.models.user import User
from app.models.usuario_rol import UsuarioRol
from app.models.entrada_padron import EntradaPadron

TENANT_ID = uuid.UUID('f180086f-c1a6-4df2-b57a-3acc2fb29998')

NS = uuid.UUID('bbbbbbbb-0000-0000-0000-000000000000')

ROLE_ID_ALUMNO = uuid.uuid5(uuid.NAMESPACE_OID, 'role:ALUMNO')

DEMO_ALUMNOS = [
    {
        'id': uuid.uuid5(NS, 'alumno:facundo.benitez'),
        'nombre': 'Facundo',
        'apellidos': 'Benitez',
        'email': 'facundo.benitez@alumno.utn.edu.ar',
        'password': 'alumno123',
        'tag': 'al día (notas altas)',
    },
    {
        'id': uuid.uuid5(NS, 'alumno:valentina.morales'),
        'nombre': 'Valentina',
        'apellidos': 'Morales',
        'email': 'valentina.morales@alumno.utn.edu.ar',
        'password': 'alumno123',
        'tag': 'atrasada (notas bajas)',
    },
    {
        'id': uuid.uuid5(NS, 'alumno:florencia.vargas'),
        'nombre': 'Florencia',
        'apellidos': 'Vargas',
        'email': 'florencia.vargas@alumno.utn.edu.ar',
        'password': 'alumno123',
        'tag': 'atrasada (notas muy bajas)',
    },
]


async def seed():
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.now(timezone.utc)

    async with Session() as db:
        for alumno in DEMO_ALUMNOS:
            email_hash = hash_email(alumno['email'])

            # Crear o recuperar usuario
            r = await db.execute(select(User).where(User.email_hash == email_hash))
            user = r.scalar_one_or_none()
            if not user:
                user = User(
                    id=alumno['id'],
                    nombre=alumno['nombre'],
                    apellidos=alumno['apellidos'],
                    email_encrypted=encrypt(alumno['email']),
                    email_hash=email_hash,
                    password_hash=hash_password(alumno['password']),
                    is_active=True,
                    estado='Activo',
                    created_at=now,
                    updated_at=now,
                )
                user.tenant_id = TENANT_ID
                db.add(user)
                await db.flush()
                print(f'  ✓ Usuario creado: {alumno["email"]} ({alumno["tag"]})')
            else:
                print(f'  · Usuario existente: {alumno["email"]}')

            # Asignar rol ALUMNO
            r2 = await db.execute(select(UsuarioRol).where(
                UsuarioRol.user_id == user.id,
                UsuarioRol.rol_id == ROLE_ID_ALUMNO,
                UsuarioRol.tenant_id == TENANT_ID,
                UsuarioRol.deleted_at.is_(None),
            ))
            if not r2.scalar_one_or_none():
                from datetime import date
                ur = UsuarioRol(
                    user_id=user.id,
                    rol_id=ROLE_ID_ALUMNO,
                    valid_from=date.today(),
                    valid_until=None,
                    created_at=now,
                    updated_at=now,
                )
                ur.tenant_id = TENANT_ID
                db.add(ur)
                await db.flush()

            # Linkear entradas de padrón por email
            r3 = await db.execute(
                select(EntradaPadron).where(
                    EntradaPadron.tenant_id == TENANT_ID,
                    EntradaPadron.deleted_at.is_(None),
                )
            )
            all_eps = r3.scalars().all()
            linked = 0
            for ep in all_eps:
                try:
                    ep_email = decrypt(ep.email_encrypted).lower().strip()
                except Exception:
                    continue
                if ep_email == alumno['email'].lower():
                    if ep.usuario_id != user.id:
                        ep.usuario_id = user.id
                        linked += 1
            if linked:
                print(f'    → Linkeadas {linked} entrada(s) de padrón')
            else:
                print(f'    → Sin entradas de padrón (ya linkeadas o no existen)')

        await db.commit()

    print()
    print('=== Credenciales alumnos demo ===')
    for a in DEMO_ALUMNOS:
        print(f'{a["email"]:50s} / alumno123  ({a["tag"]})')

    await engine.dispose()


asyncio.run(seed())
