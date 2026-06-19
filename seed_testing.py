"""
seed_testing.py — Datos de prueba completos para testing del frontend.

Crea:
  - 2 materias extra (Algoritmos, Bases de Datos)
  - 2 profesores con asignaciones vigentes, cada uno con tutor responsable
  - 3 comisiones (A, B, C) con 8 alumnos cada una
  - Calificaciones variadas (aprobados, desaprobados, sin nota)
  - Umbral por materia

Uso (dentro del contenedor):
    python /tmp/seed_testing.py

IDs determinísticos generados con uuid5 para que sean reproducibles.
"""

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

# ── Constantes ────────────────────────────────────────────────────────────────
TENANT_ID = uuid.UUID('f180086f-c1a6-4df2-b57a-3acc2fb29998')
ADMIN_ID  = uuid.UUID('e5c06e3f-5f25-4862-a9f9-af277b5f0499')

NS = uuid.UUID('aaaaaaaa-0000-0000-0000-000000000000')  # namespace seed testing

def sid(label: str) -> uuid.UUID:
    return uuid.uuid5(NS, label)

ROLE_IDS = {
    'ALUMNO':      uuid.uuid5(uuid.NAMESPACE_OID, 'role:ALUMNO'),
    'TUTOR':       uuid.uuid5(uuid.NAMESPACE_OID, 'role:TUTOR'),
    'PROFESOR':    uuid.uuid5(uuid.NAMESPACE_OID, 'role:PROFESOR'),
    'COORDINADOR': uuid.uuid5(uuid.NAMESPACE_OID, 'role:COORDINADOR'),
    'NEXO':        uuid.uuid5(uuid.NAMESPACE_OID, 'role:NEXO'),
    'ADMIN':       uuid.uuid5(uuid.NAMESPACE_OID, 'role:ADMIN'),
    'FINANZAS':    uuid.uuid5(uuid.NAMESPACE_OID, 'role:FINANZAS'),
}

# ── Usuarios de prueba ────────────────────────────────────────────────────────
PROFESORES = [
    {
        'id': sid('user:prof_garcia'),
        'nombre': 'Roberto', 'apellidos': 'García',
        'email': 'rgarcia@trace.dev', 'password': 'garcia123',
        'rol': 'PROFESOR',
    },
    {
        'id': sid('user:prof_silva'),
        'nombre': 'Ana', 'apellidos': 'Silva',
        'email': 'asilva@trace.dev', 'password': 'silva123',
        'rol': 'PROFESOR',
    },
]

TUTORES = [
    {
        'id': sid('user:tutor_martinez'),
        'nombre': 'Carlos', 'apellidos': 'Martínez',
        'email': 'cmartinez@trace.dev', 'password': 'cmartinez123',
        'rol': 'TUTOR',
    },
    {
        'id': sid('user:tutor_lopez'),
        'nombre': 'Beatriz', 'apellidos': 'López',
        'email': 'blopez@trace.dev', 'password': 'blopez123',
        'rol': 'TUTOR',
    },
]

# ── Alumnos por comisión ──────────────────────────────────────────────────────
ALUMNOS_COM_A = [
    ('Facundo',   'Benitez',   'facundo.benitez@alumno.utn.edu.ar'),
    ('Luciana',   'Castillo',  'luciana.castillo@alumno.utn.edu.ar'),
    ('Tomás',     'Herrera',   'tomas.herrera@alumno.utn.edu.ar'),
    ('Valentina', 'Morales',   'valentina.morales@alumno.utn.edu.ar'),
    ('Agustín',   'Pereyra',   'agustin.pereyra@alumno.utn.edu.ar'),
    ('Camila',    'Ríos',      'camila.rios@alumno.utn.edu.ar'),
    ('Nicolás',   'Suárez',    'nicolas.suarez@alumno.utn.edu.ar'),
    ('Florencia', 'Vargas',    'florencia.vargas@alumno.utn.edu.ar'),
]

ALUMNOS_COM_B = [
    ('Sebastián', 'Acosta',    'sebastian.acosta@alumno.utn.edu.ar'),
    ('Natalia',   'Blanco',    'natalia.blanco@alumno.utn.edu.ar'),
    ('Ezequiel',  'Cabrera',   'ezequiel.cabrera@alumno.utn.edu.ar'),
    ('Marina',    'Delgado',   'marina.delgado@alumno.utn.edu.ar'),
    ('Leandro',   'Esquivel',  'leandro.esquivel@alumno.utn.edu.ar'),
    ('Yamila',    'Figueroa',  'yamila.figueroa@alumno.utn.edu.ar'),
    ('Rodrigo',   'Giménez',   'rodrigo.gimenez@alumno.utn.edu.ar'),
    ('Micaela',   'Ibarra',    'micaela.ibarra@alumno.utn.edu.ar'),
]

ALUMNOS_COM_C = [
    ('Bruno',     'Juárez',    'bruno.juarez@alumno.utn.edu.ar'),
    ('Sofía',     'Keller',    'sofia.keller@alumno.utn.edu.ar'),
    ('Ignacio',   'Luna',      'ignacio.luna@alumno.utn.edu.ar'),
    ('Rocío',     'Medina',    'rocio.medina@alumno.utn.edu.ar'),
    ('Maximiliano','Navarro',  'maxi.navarro@alumno.utn.edu.ar'),
    ('Antonela',  'Ortiz',     'antonela.ortiz@alumno.utn.edu.ar'),
    ('Franco',    'Páez',      'franco.paez@alumno.utn.edu.ar'),
    ('Julieta',   'Quiroga',   'julieta.quiroga@alumno.utn.edu.ar'),
]

# Notas: None = sin corregir, 0-10
NOTAS_COM_A = [
    #  TP1   TP2   TP3   P1    P2
    ( 8.5,   9.0,  7.5,  8.0,  9.0),
    ( 5.0,   4.0,  6.0,  3.0,  5.0),
    ( 9.0,   8.5,  9.5,  9.0, None),
    (None,   3.0,  2.0,  4.0,  3.0),
    ( 7.0,   7.5,  8.0,  7.0,  7.5),
    ( 6.0,   5.5,  6.5,  6.0, None),
    ( 8.0,   8.0,  7.0,  9.0,  8.5),
    ( 2.0,   3.0,  4.0,  2.0,  3.0),
]

NOTAS_COM_B = [
    ( 7.0,   6.5,  7.0,  6.0,  7.0),
    ( 4.0,   4.5,  3.5,  5.0,  4.0),
    ( 9.5,  10.0,  9.0, 10.0,  9.5),
    ( 6.5,   7.0,  6.0,  5.0,  6.0),
    ( 3.0,   2.5,  4.0,  3.0, None),
    ( 8.0,   8.5,  9.0,  8.0,  8.5),
    ( 5.5,   6.0,  5.0,  6.5,  5.5),
    ( 7.5,   7.0,  8.0,  7.5,  8.0),
]

NOTAS_COM_C = [
    ( 6.0,   5.5,  7.0,  6.5,  6.0),
    ( 9.0,   8.0,  8.5,  9.0,  9.5),
    ( 4.5,   4.0,  5.0,  3.5,  4.0),
    ( 7.0,   7.5,  7.0,  8.0,  7.0),
    ( 2.0,  None,  3.0,  2.5,  3.0),
    ( 8.5,   9.0,  8.0,  9.5,  8.5),
    ( 5.0,   5.5,  6.0,  4.5,  5.0),
    (None,   6.0,  5.5,  6.0, None),
]


async def upsert_user(db, u_data: dict, now: datetime) -> User:
    r = await db.execute(select(User).where(User.email_hash == __import__('app.core.security', fromlist=['hash_email']).hash_email(u_data['email'])))
    user = r.scalar_one_or_none()
    if not user:
        from app.core.security import hash_email, hash_password
        from app.core.encryption import encrypt
        user = User(
            id=u_data['id'],
            nombre=u_data['nombre'],
            apellidos=u_data['apellidos'],
            email_encrypted=encrypt(u_data['email']),
            email_hash=hash_email(u_data['email']),
            password_hash=hash_password(u_data['password']),
            is_active=True, estado='Activo',
            created_at=now, updated_at=now,
        )
        user.tenant_id = TENANT_ID
        db.add(user)
        await db.flush()
        print(f'  Usuario creado: {u_data["email"]}')
    else:
        print(f'  Usuario existente: {u_data["email"]}')
    return user


async def upsert_rol(db, user_id: uuid.UUID, rol: str, now: datetime):
    r = await db.execute(select(UsuarioRol).where(
        UsuarioRol.user_id == user_id,
        UsuarioRol.rol_id == ROLE_IDS[rol],
        UsuarioRol.tenant_id == TENANT_ID,
        UsuarioRol.deleted_at.is_(None),
    ))
    if not r.scalar_one_or_none():
        ur = UsuarioRol(
            user_id=user_id, rol_id=ROLE_IDS[rol],
            valid_from=date.today(), valid_until=None,
            created_at=now, updated_at=now,
        )
        ur.tenant_id = TENANT_ID
        db.add(ur)
        await db.flush()


async def seed():
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.now(timezone.utc)

    async with Session() as db:

        # ── Carrera (reusar la del seed académico) ────────────────────────────
        r = await db.execute(select(Carrera).where(
            Carrera.tenant_id == TENANT_ID, Carrera.codigo == 'TPI',
            Carrera.deleted_at.is_(None)
        ))
        carrera = r.scalar_one_or_none()
        if not carrera:
            carrera = Carrera(
                codigo='TPI', nombre='Tecnicatura en Programacion Informatica',
                estado='Activa', created_at=now, updated_at=now,
            )
            carrera.tenant_id = TENANT_ID
            db.add(carrera)
            await db.flush()
        print(f'Carrera: {carrera.id}')

        # ── Cohorte ───────────────────────────────────────────────────────────
        r = await db.execute(select(Cohorte).where(
            Cohorte.tenant_id == TENANT_ID, Cohorte.carrera_id == carrera.id,
            Cohorte.nombre == '2024-A', Cohorte.deleted_at.is_(None)
        ))
        cohorte = r.scalar_one_or_none()
        if not cohorte:
            cohorte = Cohorte(
                carrera_id=carrera.id, nombre='2024-A', anio=2024,
                vig_desde=date(2024, 3, 1), vig_hasta=date(2025, 3, 1),
                created_at=now, updated_at=now,
            )
            cohorte.tenant_id = TENANT_ID
            db.add(cohorte)
            await db.flush()
        print(f'Cohorte: {cohorte.id}')

        # ── Materias ──────────────────────────────────────────────────────────
        materias_def = [
            ('ALGO1', 'Algoritmos y Estructuras de Datos'),
            ('BD1',   'Bases de Datos I'),
        ]
        materias = {}
        for codigo, nombre in materias_def:
            r = await db.execute(select(Materia).where(
                Materia.tenant_id == TENANT_ID, Materia.codigo == codigo,
                Materia.deleted_at.is_(None)
            ))
            m = r.scalar_one_or_none()
            if not m:
                m = Materia(codigo=codigo, nombre=nombre, estado='Activa', created_at=now, updated_at=now)
                m.tenant_id = TENANT_ID
                db.add(m)
                await db.flush()
                print(f'Materia creada: {nombre}')
            else:
                print(f'Materia existente: {nombre}')
            materias[codigo] = m

        # ── Profesores ────────────────────────────────────────────────────────
        print('\n=== Profesores ===')
        prof_users = {}
        for p in PROFESORES:
            u = await upsert_user(db, p, now)
            await upsert_rol(db, u.id, 'PROFESOR', now)
            prof_users[p['email']] = u

        # ── Tutores ───────────────────────────────────────────────────────────
        print('\n=== Tutores ===')
        tutor_users = {}
        for t in TUTORES:
            u = await upsert_user(db, t, now)
            await upsert_rol(db, u.id, 'TUTOR', now)
            tutor_users[t['email']] = u

        tutor1 = tutor_users['cmartinez@trace.dev']
        tutor2 = tutor_users['blopez@trace.dev']
        prof1  = prof_users['rgarcia@trace.dev']
        prof2  = prof_users['asilva@trace.dev']

        # ── Asignaciones: profe + tutor responsable ───────────────────────────
        # García → ALGO1 comisiones A y B, tutor responsable = Martínez
        # Silva  → BD1   comisiones A y C, tutor responsable = López
        print('\n=== Asignaciones ===')
        asig_def = [
            # (prof, materia_codigo, comisiones, tutor_responsable)
            (prof1, 'ALGO1', ['A', 'B'], tutor1),
            (prof2, 'BD1',   ['A', 'C'], tutor2),
        ]
        asignaciones = {}
        for prof, mat_code, comisiones, tutor in asig_def:
            mat = materias[mat_code]
            r = await db.execute(select(Asignacion).where(
                Asignacion.tenant_id == TENANT_ID,
                Asignacion.usuario_id == prof.id,
                Asignacion.materia_id == mat.id,
                Asignacion.deleted_at.is_(None),
            ))
            asig = r.scalar_one_or_none()
            if not asig:
                asig = Asignacion(
                    usuario_id=prof.id, rol='PROFESOR', materia_id=mat.id,
                    carrera_id=carrera.id, cohorte_id=cohorte.id,
                    comisiones=comisiones, responsable_id=tutor.id,
                    desde=date(2024, 3, 1), hasta=date(2025, 3, 1),
                    created_at=now, updated_at=now,
                )
                asig.tenant_id = TENANT_ID
                db.add(asig)
                await db.flush()
                print(f'  Asignacion creada: {prof.apellidos} → {mat_code} {comisiones} (tutor: {tutor.apellidos})')
            else:
                print(f'  Asignacion existente: {prof.apellidos} → {mat_code}')
            asignaciones[(prof.id, mat_code)] = asig

        # Asignacion TUTOR en la misma materia (para que el tutor vea los datos)
        for tutor, mat_code in [(tutor1, 'ALGO1'), (tutor2, 'BD1')]:
            mat = materias[mat_code]
            r = await db.execute(select(Asignacion).where(
                Asignacion.tenant_id == TENANT_ID,
                Asignacion.usuario_id == tutor.id,
                Asignacion.materia_id == mat.id,
                Asignacion.deleted_at.is_(None),
            ))
            if not r.scalar_one_or_none():
                ta = Asignacion(
                    usuario_id=tutor.id, rol='TUTOR', materia_id=mat.id,
                    carrera_id=carrera.id, cohorte_id=cohorte.id,
                    comisiones=['A', 'B', 'C'],
                    desde=date(2024, 3, 1), hasta=date(2025, 3, 1),
                    created_at=now, updated_at=now,
                )
                ta.tenant_id = TENANT_ID
                db.add(ta)
                await db.flush()
                print(f'  Asignacion TUTOR creada: {tutor.apellidos} → {mat_code}')

        # ── Padrones y alumnos ────────────────────────────────────────────────
        print('\n=== Padrones y alumnos ===')

        comisiones_data = [
            ('A', ALUMNOS_COM_A, NOTAS_COM_A),
            ('B', ALUMNOS_COM_B, NOTAS_COM_B),
            ('C', ALUMNOS_COM_C, NOTAS_COM_C),
        ]

        actividades = ['TP1', 'TP2', 'TP3', 'Parcial 1', 'Parcial 2']
        UMBRAL = 6.0

        for mat_code, prof in [('ALGO1', prof1), ('BD1', prof2)]:
            mat = materias[mat_code]
            asig = asignaciones[(prof.id, mat_code)]

            # Limpiar umbral anterior
            await db.execute(text(
                f"DELETE FROM umbral_materia "
                f"WHERE asignacion_id = '{asig.id}' AND materia_id = '{mat.id}'"
            ))

            # Umbral
            umbral = UmbralMateria(
                asignacion_id=asig.id, materia_id=mat.id,
                umbral_pct=60, valores_aprobatorios=['Satisfactorio', 'Supera lo esperado'],
                created_at=now, updated_at=now,
            )
            umbral.tenant_id = TENANT_ID
            db.add(umbral)
            await db.flush()

            total_alumnos = 0
            total_cal = 0

            # Limpiar calificaciones previas de esta asignacion (UNA sola vez antes del loop)
            await db.execute(text(
                f"DELETE FROM calificaciones "
                f"WHERE asignacion_id = '{asig.id}' AND materia_id = '{mat.id}'"
            ))
            await db.flush()

            # VersionPadron compartida por materia/cohorte
            vp_r = await db.execute(select(VersionPadron).where(
                VersionPadron.tenant_id == TENANT_ID,
                VersionPadron.materia_id == mat.id,
                VersionPadron.cohorte_id == cohorte.id,
                VersionPadron.activa.is_(True),
                VersionPadron.deleted_at.is_(None),
            ))
            vp = vp_r.scalar_one_or_none()
            if not vp:
                vp = VersionPadron(
                    materia_id=mat.id, cohorte_id=cohorte.id,
                    cargado_por=ADMIN_ID, cargado_at=now, activa=True,
                    created_at=now, updated_at=now,
                )
                vp.tenant_id = TENANT_ID
                db.add(vp)
                await db.flush()

            for com_letra, alumnos_list, notas_list in comisiones_data:
                # Alumnos y calificaciones
                for (nombre, apellidos, email), notas in zip(alumnos_list, notas_list):
                    ep = EntradaPadron(
                        version_id=vp.id, nombre=nombre, apellidos=apellidos,
                        email_encrypted=encrypt(email), comision=com_letra,
                        regional='Buenos Aires', created_at=now, updated_at=now,
                    )
                    ep.tenant_id = TENANT_ID
                    db.add(ep)
                    await db.flush()
                    total_alumnos += 1

                    for act, nota in zip(actividades, notas):
                        cal = Calificacion(
                            asignacion_id=asig.id, materia_id=mat.id,
                            entrada_padron_id=ep.id, actividad=act,
                            nota_numerica=nota if nota is not None else None,
                            nota_textual=None,
                            aprobado=(nota >= UMBRAL) if nota is not None else False,
                            origen='Importado', importado_at=now,
                            created_at=now, updated_at=now,
                        )
                        cal.tenant_id = TENANT_ID
                        db.add(cal)
                        total_cal += 1

                await db.flush()

            print(f'  {mat_code}: {total_alumnos} alumnos, {total_cal} calificaciones, umbral 60%')

        await db.commit()

    print()
    print('=== Credenciales testing ===')
    print('admin@trace.dev       / admin123     -> ADMIN')
    print('rgarcia@trace.dev     / garcia123    -> PROFESOR (ALGO1 - Com A,B - Tutor: Martínez)')
    print('asilva@trace.dev      / silva123     -> PROFESOR (BD1   - Com A,C - Tutor: López)')
    print('cmartinez@trace.dev   / cmartinez123 -> TUTOR (ALGO1)')
    print('blopez@trace.dev      / blopez123    -> TUTOR (BD1)')
    print()
    print('=== IDs para router.tsx ===')
    print('# García / ALGO1:')

    await engine.dispose()


asyncio.run(seed())
