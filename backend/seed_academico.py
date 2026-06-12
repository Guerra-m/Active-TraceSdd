import asyncio
import uuid
from datetime import date, datetime, timezone

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, text

from app.core.config import get_settings
from app.core.encryption import encrypt
from app.core.security import hash_email, hash_password
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.asignacion import Asignacion
from app.models.version_padron import VersionPadron
from app.models.entrada_padron import EntradaPadron
from app.models.calificacion import Calificacion
from app.models.umbral_materia import UmbralMateria
from app.models.user import User
from app.models.usuario_rol import UsuarioRol

TENANT_ID = uuid.UUID('f180086f-c1a6-4df2-b57a-3acc2fb29998')
USER_ID   = uuid.UUID('e5c06e3f-5f25-4862-a9f9-af277b5f0499')

# IDs de roles (determinísticos — generados en la migración 003)
ROLE_IDS = {
    'ALUMNO':      uuid.uuid5(uuid.NAMESPACE_OID, 'role:ALUMNO'),
    'TUTOR':       uuid.uuid5(uuid.NAMESPACE_OID, 'role:TUTOR'),
    'PROFESOR':    uuid.uuid5(uuid.NAMESPACE_OID, 'role:PROFESOR'),
    'COORDINADOR': uuid.uuid5(uuid.NAMESPACE_OID, 'role:COORDINADOR'),
    'NEXO':        uuid.uuid5(uuid.NAMESPACE_OID, 'role:NEXO'),
    'ADMIN':       uuid.uuid5(uuid.NAMESPACE_OID, 'role:ADMIN'),
    'FINANZAS':    uuid.uuid5(uuid.NAMESPACE_OID, 'role:FINANZAS'),
}

# Usuarios de prueba por rol (además del admin existente)
TEST_USERS = [
    {
        'id': uuid.UUID('11111111-0000-0000-0000-000000000001'),
        'nombre': 'Juan',
        'apellidos': 'Docente',
        'email': 'profesor@trace.dev',
        'password': 'profesor123',
        'rol': 'PROFESOR',
    },
    {
        'id': uuid.UUID('11111111-0000-0000-0000-000000000002'),
        'nombre': 'Laura',
        'apellidos': 'Tutora',
        'email': 'tutor@trace.dev',
        'password': 'tutor123',
        'rol': 'TUTOR',
    },
    {
        'id': uuid.UUID('11111111-0000-0000-0000-000000000003'),
        'nombre': 'Carla',
        'apellidos': 'Coordinadora',
        'email': 'coord@trace.dev',
        'password': 'coord123',
        'rol': 'COORDINADOR',
    },
    {
        'id': uuid.UUID('11111111-0000-0000-0000-000000000004'),
        'nombre': 'Pedro',
        'apellidos': 'Nexo',
        'email': 'nexo@trace.dev',
        'password': 'nexo123',
        'rol': 'NEXO',
    },
    {
        'id': uuid.UUID('11111111-0000-0000-0000-000000000005'),
        'nombre': 'Silvia',
        'apellidos': 'Finanzas',
        'email': 'finanzas@trace.dev',
        'password': 'fin123',
        'rol': 'FINANZAS',
    },
]


async def seed():
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.now(timezone.utc)

    async with Session() as db:

        # ── Patch admin existente: completar nombre si está vacío ────────────
        r = await db.execute(select(User).where(User.id == USER_ID))
        admin = r.scalar_one_or_none()
        if admin and not admin.nombre:
            admin.nombre = 'Admin'
            admin.apellidos = 'Sistema'
            print('Admin: nombre completado')

        # ── Usuarios de prueba por rol ────────────────────────────────────────
        print('\n=== Usuarios de prueba ===')
        for u_data in TEST_USERS:
            r = await db.execute(
                select(User).where(User.email_hash == hash_email(u_data['email']))
            )
            user = r.scalar_one_or_none()

            if not user:
                user = User(
                    id=u_data['id'],
                    nombre=u_data['nombre'],
                    apellidos=u_data['apellidos'],
                    email_encrypted=encrypt(u_data['email']),
                    email_hash=hash_email(u_data['email']),
                    password_hash=hash_password(u_data['password']),
                    is_active=True,
                    estado='Activo',
                    created_at=now,
                    updated_at=now,
                )
                user.tenant_id = TENANT_ID
                db.add(user)
                await db.flush()
                print(f'  Creado: {u_data["email"]} ({u_data["rol"]})')
            else:
                print(f'  Existente: {u_data["email"]} ({u_data["rol"]})')

            # UsuarioRol — asignar si no existe
            r2 = await db.execute(
                select(UsuarioRol).where(
                    UsuarioRol.user_id == user.id,
                    UsuarioRol.rol_id == ROLE_IDS[u_data['rol']],
                    UsuarioRol.tenant_id == TENANT_ID,
                    UsuarioRol.deleted_at.is_(None),
                )
            )
            ur = r2.scalar_one_or_none()
            if not ur:
                ur = UsuarioRol(
                    user_id=user.id,
                    rol_id=ROLE_IDS[u_data['rol']],
                    valid_from=date.today(),
                    valid_until=None,
                    created_at=now,
                    updated_at=now,
                )
                ur.tenant_id = TENANT_ID
                db.add(ur)
                await db.flush()
                print(f'    UsuarioRol asignado: {u_data["rol"]}')

        # ── Asignacion académica para el usuario PROFESOR ────────────────────
        # (necesita asignacion para ver datos en las páginas académicas)
        # Obtenemos la materia del seed académico existente para reutilizarla.

        # ── Carrera ──────────────────────────────────────────────────────────
        r = await db.execute(select(Carrera).where(
            Carrera.tenant_id == TENANT_ID, Carrera.codigo == 'TPI',
            Carrera.deleted_at.is_(None)
        ))
        carrera = r.scalar_one_or_none()
        if not carrera:
            carrera = Carrera(
                codigo='TPI', nombre='Tecnicatura en Programacion Informatica',
                estado='Activa', created_at=now, updated_at=now
            )
            carrera.tenant_id = TENANT_ID
            db.add(carrera)
            await db.flush()
            print(f'\nCarrera creada: {carrera.id}')
        else:
            print(f'\nCarrera existente: {carrera.id}')

        # ── Cohorte ──────────────────────────────────────────────────────────
        r = await db.execute(select(Cohorte).where(
            Cohorte.tenant_id == TENANT_ID, Cohorte.carrera_id == carrera.id,
            Cohorte.nombre == '2024-A', Cohorte.deleted_at.is_(None)
        ))
        cohorte = r.scalar_one_or_none()
        if not cohorte:
            cohorte = Cohorte(
                carrera_id=carrera.id, nombre='2024-A', anio=2024,
                vig_desde=date(2024, 3, 1), vig_hasta=date(2025, 3, 1),
                created_at=now, updated_at=now
            )
            cohorte.tenant_id = TENANT_ID
            db.add(cohorte)
            await db.flush()
            print(f'Cohorte creada: {cohorte.id}')
        else:
            print(f'Cohorte existente: {cohorte.id}')

        # ── Materia ──────────────────────────────────────────────────────────
        r = await db.execute(select(Materia).where(
            Materia.tenant_id == TENANT_ID, Materia.codigo == 'PROG1',
            Materia.deleted_at.is_(None)
        ))
        materia = r.scalar_one_or_none()
        if not materia:
            materia = Materia(
                codigo='PROG1', nombre='Programacion I', estado='Activa',
                created_at=now, updated_at=now
            )
            materia.tenant_id = TENANT_ID
            db.add(materia)
            await db.flush()
            print(f'Materia creada: {materia.id}')
        else:
            print(f'Materia existente: {materia.id}')

        # ── Asignacion (admin existente) ──────────────────────────────────────
        r = await db.execute(select(Asignacion).where(
            Asignacion.tenant_id == TENANT_ID,
            Asignacion.usuario_id == USER_ID,
            Asignacion.materia_id == materia.id,
            Asignacion.deleted_at.is_(None)
        ))
        asignacion = r.scalar_one_or_none()
        if not asignacion:
            asignacion = Asignacion(
                usuario_id=USER_ID, rol='PROFESOR', materia_id=materia.id,
                carrera_id=carrera.id, cohorte_id=cohorte.id, comisiones=['A'],
                desde=date(2024, 3, 1), hasta=date(2025, 3, 1),
                created_at=now, updated_at=now
            )
            asignacion.tenant_id = TENANT_ID
            db.add(asignacion)
            await db.flush()
            print(f'Asignacion creada: {asignacion.id}')
        else:
            print(f'Asignacion existente: {asignacion.id}')

        # ── Asignacion para usuario PROFESOR de prueba ────────────────────────
        profesor_id = uuid.UUID('11111111-0000-0000-0000-000000000001')
        r = await db.execute(select(Asignacion).where(
            Asignacion.tenant_id == TENANT_ID,
            Asignacion.usuario_id == profesor_id,
            Asignacion.materia_id == materia.id,
            Asignacion.deleted_at.is_(None)
        ))
        asig_prof = r.scalar_one_or_none()
        if not asig_prof:
            asig_prof = Asignacion(
                usuario_id=profesor_id, rol='PROFESOR', materia_id=materia.id,
                carrera_id=carrera.id, cohorte_id=cohorte.id, comisiones=['A'],
                desde=date(2024, 3, 1), hasta=date(2025, 3, 1),
                created_at=now, updated_at=now
            )
            asig_prof.tenant_id = TENANT_ID
            db.add(asig_prof)
            await db.flush()
            print(f'Asignacion PROFESOR prueba creada')
        else:
            print(f'Asignacion PROFESOR prueba existente')

        # ── VersionPadron ────────────────────────────────────────────────────
        r = await db.execute(select(VersionPadron).where(
            VersionPadron.tenant_id == TENANT_ID,
            VersionPadron.materia_id == materia.id,
            VersionPadron.cohorte_id == cohorte.id,
            VersionPadron.activa.is_(True),
            VersionPadron.deleted_at.is_(None)
        ))
        vp = r.scalar_one_or_none()
        if not vp:
            vp = VersionPadron(
                materia_id=materia.id, cohorte_id=cohorte.id,
                cargado_por=USER_ID, cargado_at=now, activa=True,
                created_at=now, updated_at=now
            )
            vp.tenant_id = TENANT_ID
            db.add(vp)
            await db.flush()
            print(f'VersionPadron creada: {vp.id}')
        else:
            # Limpiar entradas para regenerar
            await db.execute(text(f"DELETE FROM entrada_padron WHERE version_id = '{vp.id}'"))
            await db.flush()
            print(f'VersionPadron existente: {vp.id} (entradas limpias)')

        # ── Alumnos ──────────────────────────────────────────────────────────
        alumnos_data = [
            ('Maria',   'Gonzalez',  'maria.gonzalez@alumno.utn.edu.ar'),
            ('Carlos',  'Ramirez',   'carlos.ramirez@alumno.utn.edu.ar'),
            ('Ana',     'Lopez',     'ana.lopez@alumno.utn.edu.ar'),
            ('Luis',    'Martinez',  'luis.martinez@alumno.utn.edu.ar'),
            ('Sofia',   'Torres',    'sofia.torres@alumno.utn.edu.ar'),
            ('Diego',   'Fernandez', 'diego.fernandez@alumno.utn.edu.ar'),
            ('Paula',   'Sanchez',   'paula.sanchez@alumno.utn.edu.ar'),
            ('Matias',  'Romero',    'matias.romero@alumno.utn.edu.ar'),
            ('Valeria', 'Diaz',      'valeria.diaz@alumno.utn.edu.ar'),
            ('Marcos',  'Perez',     'marcos.perez@alumno.utn.edu.ar'),
        ]
        ep_map = {}
        for nombre, apellidos, email in alumnos_data:
            ep = EntradaPadron(
                version_id=vp.id, nombre=nombre, apellidos=apellidos,
                email_encrypted=encrypt(email), comision='A',
                regional='Buenos Aires', created_at=now, updated_at=now
            )
            ep.tenant_id = TENANT_ID
            db.add(ep)
            ep_map[nombre] = ep
        await db.flush()
        print(f'Alumnos creados: {len(ep_map)}')

        # ── Calificaciones ───────────────────────────────────────────────────
        # Limpiar calificaciones anteriores
        await db.execute(text(
            f"DELETE FROM calificaciones "
            f"WHERE asignacion_id = '{asignacion.id}' AND materia_id = '{materia.id}'"
        ))
        await db.flush()

        actividades = ['TP1', 'TP2', 'TP3', 'Parcial 1', 'Parcial 2']
        # None = entrega sin corregir (sin nota)
        tabla = [
            ('Maria',   8.5,  9.0,  7.5,  8.0,   9.0),
            ('Carlos',  5.0,  4.0,  6.0,  3.0,   5.0),
            ('Ana',     9.0,  8.5,  9.5,  9.0,  None),
            ('Luis',   None,  3.0,  2.0,  4.0,   3.0),
            ('Sofia',   7.0,  7.5,  8.0,  7.0,   7.5),
            ('Diego',   6.0,  5.5,  6.5,  6.0,  None),
            ('Paula',   8.0,  8.0,  7.0,  9.0,   8.5),
            ('Matias',  2.0,  3.0,  4.0,  2.0,   3.0),
            ('Valeria', 9.5, 10.0,  9.0, 10.0,   9.5),
            ('Marcos',  6.5,  7.0,  6.0,  5.0,   6.0),
        ]
        UMBRAL = 5.0
        total_cal = 0
        for nombre, *notas in tabla:
            ep = ep_map[nombre]
            for act, nota in zip(actividades, notas):
                cal = Calificacion(
                    asignacion_id=asignacion.id, materia_id=materia.id,
                    entrada_padron_id=ep.id, actividad=act,
                    nota_numerica=nota if nota is not None else None,
                    nota_textual=None,
                    aprobado=(nota >= UMBRAL) if nota is not None else False,
                    origen='Importado', importado_at=now,
                    created_at=now, updated_at=now
                )
                cal.tenant_id = TENANT_ID
                db.add(cal)
                total_cal += 1
        await db.flush()
        print(f'Calificaciones creadas: {total_cal}')

        # ── Umbral ───────────────────────────────────────────────────────────
        r = await db.execute(select(UmbralMateria).where(
            UmbralMateria.tenant_id == TENANT_ID,
            UmbralMateria.asignacion_id == asignacion.id,
            UmbralMateria.materia_id == materia.id,
            UmbralMateria.deleted_at.is_(None)
        ))
        umbral = r.scalar_one_or_none()
        if not umbral:
            umbral = UmbralMateria(
                asignacion_id=asignacion.id, materia_id=materia.id,
                umbral_pct=50, valores_aprobatorios=['Satisfactorio', 'Supera lo esperado'],
                created_at=now, updated_at=now
            )
            umbral.tenant_id = TENANT_ID
            db.add(umbral)
            await db.flush()
            print(f'Umbral creado: {umbral.umbral_pct}%')
        else:
            print(f'Umbral existente: {umbral.umbral_pct}%')

        await db.commit()

    print()
    print('=== IDs para router.tsx ===')
    print(f'ASIGNACION_ID = "{asignacion.id}"')
    print(f'MATERIA_ID    = "{materia.id}"')
    print('===========================')
    print()
    print('=== Credenciales de prueba ===')
    print('admin@trace.dev    / admin123    -> ADMIN')
    for u in TEST_USERS:
        print(f'{u["email"]:<26} / {u["password"]:<12} -> {u["rol"]}')
    print('==============================')
    await engine.dispose()


asyncio.run(seed())
