"""
seed_completo.py — Seed único para desarrollo/demo.

Crea TODO lo necesario desde cero:
  - Tenant de prueba
  - RBAC (roles, permisos, matriz)
  - Usuarios de todos los roles (staff + docentes + alumnos demo)
  - Estructura académica (carrera, cohorte, 2 materias)
  - Asignaciones docentes
  - Padrones con alumnos y calificaciones (3 comisiones × 8 alumnos × 2 materias)
  - Linkeo de cuentas de alumnos demo a sus entradas de padrón

Seguro de re-ejecutar: todo usa upsert/ON CONFLICT DO NOTHING.

Uso (dentro del contenedor Docker):
    docker cp seed_completo.py active-trace-api-1:/tmp/seed_completo.py
    docker exec active-trace-api-1 python /tmp/seed_completo.py

Requisito previo: alembic upgrade head ya aplicado.

Credenciales resultantes:
    admin@trace.dev                          / admin123     → ADMIN
    coord@trace.dev                          / coord123     → COORDINADOR
    finanzas@trace.dev                       / fin123       → FINANZAS
    rgarcia@trace.dev                        / garcia123    → PROFESOR  (ALGO1 Com A,B)
    asilva@trace.dev                         / silva123     → PROFESOR  (BD1   Com A,C)
    cmartinez@trace.dev                      / cmartinez123 → TUTOR     (ALGO1)
    blopez@trace.dev                         / blopez123    → TUTOR     (BD1)
    facundo.benitez@alumno.utn.edu.ar        / alumno123    → ALUMNO    (al día)
    valentina.morales@alumno.utn.edu.ar      / alumno123    → ALUMNO    (atrasada)
    florencia.vargas@alumno.utn.edu.ar       / alumno123    → ALUMNO    (muy atrasada)
"""

import asyncio
import uuid
from datetime import date, datetime, timezone

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, text

from app.core.config import get_settings
from app.core.encryption import encrypt, decrypt
from app.core.security import hash_email, hash_password
from app.core.rbac_seed import get_roles_seed, get_permisos_seed, get_matriz_seed
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

# ── Constantes globales ───────────────────────────────────────────────────────

TENANT_ID  = uuid.UUID('f180086f-c1a6-4df2-b57a-3acc2fb29998')
TENANT_NAME = 'UTN Trace Demo'
TENANT_SLUG = 'utn-trace-demo'

ADMIN_ID = uuid.UUID('e5c06e3f-5f25-4862-a9f9-af277b5f0499')

NS_SEED = uuid.UUID('cccccccc-0000-0000-0000-000000000000')

def sid(label: str) -> uuid.UUID:
    return uuid.uuid5(NS_SEED, label)

ROLE_IDS = {
    'ALUMNO':      uuid.uuid5(uuid.NAMESPACE_OID, 'role:ALUMNO'),
    'TUTOR':       uuid.uuid5(uuid.NAMESPACE_OID, 'role:TUTOR'),
    'PROFESOR':    uuid.uuid5(uuid.NAMESPACE_OID, 'role:PROFESOR'),
    'COORDINADOR': uuid.uuid5(uuid.NAMESPACE_OID, 'role:COORDINADOR'),
    'NEXO':        uuid.uuid5(uuid.NAMESPACE_OID, 'role:NEXO'),
    'ADMIN':       uuid.uuid5(uuid.NAMESPACE_OID, 'role:ADMIN'),
    'FINANZAS':    uuid.uuid5(uuid.NAMESPACE_OID, 'role:FINANZAS'),
}

# ── Definición de usuarios ────────────────────────────────────────────────────

STAFF_USERS = [
    {
        'id': ADMIN_ID,
        'nombre': 'Admin', 'apellidos': 'Sistema',
        'email': 'admin@trace.dev', 'password': 'admin123',
        'rol': 'ADMIN',
    },
    {
        'id': sid('user:coord'),
        'nombre': 'Carla', 'apellidos': 'Coordinadora',
        'email': 'coord@trace.dev', 'password': 'coord123',
        'rol': 'COORDINADOR',
    },
    {
        'id': sid('user:finanzas'),
        'nombre': 'Silvia', 'apellidos': 'Finanzas',
        'email': 'finanzas@trace.dev', 'password': 'fin123',
        'rol': 'FINANZAS',
    },
]

DOCENTES = [
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

ALUMNOS_DEMO = [
    {
        'id': sid('alumno:facundo.benitez'),
        'nombre': 'Facundo', 'apellidos': 'Benitez',
        'email': 'facundo.benitez@alumno.utn.edu.ar', 'password': 'alumno123',
        'rol': 'ALUMNO', 'tag': 'al día (notas altas)',
    },
    {
        'id': sid('alumno:valentina.morales'),
        'nombre': 'Valentina', 'apellidos': 'Morales',
        'email': 'valentina.morales@alumno.utn.edu.ar', 'password': 'alumno123',
        'rol': 'ALUMNO', 'tag': 'atrasada (notas medias-bajas)',
    },
    {
        'id': sid('alumno:florencia.vargas'),
        'nombre': 'Florencia', 'apellidos': 'Vargas',
        'email': 'florencia.vargas@alumno.utn.edu.ar', 'password': 'alumno123',
        'rol': 'ALUMNO', 'tag': 'muy atrasada (notas bajas)',
    },
]

# ── Alumnos por comisión (entradas de padrón) ─────────────────────────────────

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
    ('Bruno',        'Juárez',   'bruno.juarez@alumno.utn.edu.ar'),
    ('Sofía',        'Keller',   'sofia.keller@alumno.utn.edu.ar'),
    ('Ignacio',      'Luna',     'ignacio.luna@alumno.utn.edu.ar'),
    ('Rocío',        'Medina',   'rocio.medina@alumno.utn.edu.ar'),
    ('Maximiliano',  'Navarro',  'maxi.navarro@alumno.utn.edu.ar'),
    ('Antonela',     'Ortiz',    'antonela.ortiz@alumno.utn.edu.ar'),
    ('Franco',       'Páez',     'franco.paez@alumno.utn.edu.ar'),
    ('Julieta',      'Quiroga',  'julieta.quiroga@alumno.utn.edu.ar'),
]

# Notas: None = sin corregir aún
NOTAS_COM_A = [
    ( 8.5,  9.0,  7.5,  8.0,  9.0),   # Benitez    — al día
    ( 5.0,  4.0,  6.0,  3.0,  5.0),   # Castillo   — riesgo
    ( 9.0,  8.5,  9.5,  9.0, None),   # Herrera    — excelente
    (None,  3.0,  2.0,  4.0,  3.0),   # Morales    — atrasada
    ( 7.0,  7.5,  8.0,  7.0,  7.5),   # Pereyra    — bien
    ( 6.0,  5.5,  6.5,  6.0, None),   # Ríos       — aprobado justo
    ( 8.0,  8.0,  7.0,  9.0,  8.5),   # Suárez     — bien
    ( 2.0,  3.0,  4.0,  2.0,  3.0),   # Vargas     — muy atrasada
]

NOTAS_COM_B = [
    ( 7.0,  6.5,  7.0,  6.0,  7.0),
    ( 4.0,  4.5,  3.5,  5.0,  4.0),
    ( 9.5, 10.0,  9.0, 10.0,  9.5),
    ( 6.5,  7.0,  6.0,  5.0,  6.0),
    ( 3.0,  2.5,  4.0,  3.0, None),
    ( 8.0,  8.5,  9.0,  8.0,  8.5),
    ( 5.5,  6.0,  5.0,  6.5,  5.5),
    ( 7.5,  7.0,  8.0,  7.5,  8.0),
]

NOTAS_COM_C = [
    ( 6.0,  5.5,  7.0,  6.5,  6.0),
    ( 9.0,  8.0,  8.5,  9.0,  9.5),
    ( 4.5,  4.0,  5.0,  3.5,  4.0),
    ( 7.0,  7.5,  7.0,  8.0,  7.0),
    ( 2.0, None,  3.0,  2.5,  3.0),
    ( 8.5,  9.0,  8.0,  9.5,  8.5),
    ( 5.0,  5.5,  6.0,  4.5,  5.0),
    (None,  6.0,  5.5,  6.0, None),
]

COMISIONES_DATA = [
    ('A', ALUMNOS_COM_A, NOTAS_COM_A),
    ('B', ALUMNOS_COM_B, NOTAS_COM_B),
    ('C', ALUMNOS_COM_C, NOTAS_COM_C),
]

ACTIVIDADES = ['TP1', 'TP2', 'TP3', 'Parcial 1', 'Parcial 2']
UMBRAL_PCT  = 60
UMBRAL_NOTA = 6.0

# ── Helpers ───────────────────────────────────────────────────────────────────

async def upsert_user(db, u_data: dict, now: datetime) -> User:
    r = await db.execute(select(User).where(User.email_hash == hash_email(u_data['email'])))
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
        tag = u_data.get('tag', u_data.get('rol', ''))
        print(f'  ✓ creado:   {u_data["email"]}  ({tag})')
    else:
        tag = u_data.get('tag', u_data.get('rol', ''))
        print(f'  · existente: {u_data["email"]}  ({tag})')
    return user


async def upsert_rol(db, user_id: uuid.UUID, rol: str, now: datetime) -> None:
    r = await db.execute(select(UsuarioRol).where(
        UsuarioRol.user_id == user_id,
        UsuarioRol.rol_id == ROLE_IDS[rol],
        UsuarioRol.tenant_id == TENANT_ID,
        UsuarioRol.deleted_at.is_(None),
    ))
    if not r.scalar_one_or_none():
        ur = UsuarioRol(
            user_id=user_id,
            rol_id=ROLE_IDS[rol],
            valid_from=date.today(),
            valid_until=None,
            created_at=now,
            updated_at=now,
        )
        ur.tenant_id = TENANT_ID
        db.add(ur)
        await db.flush()


# ── Seed principal ────────────────────────────────────────────────────────────

async def seed() -> None:
    settings = get_settings()
    engine   = create_async_engine(settings.database_url, echo=False)
    Session  = async_sessionmaker(engine, expire_on_commit=False)
    now      = datetime.now(timezone.utc)

    async with Session() as db:

        # ── 1. Tenant ─────────────────────────────────────────────────────────
        print('\n=== 1. Tenant ===')
        await db.execute(text("""
            INSERT INTO tenants (id, name, slug, is_active, created_at, updated_at)
            VALUES (:id, :name, :slug, true, :now, :now)
            ON CONFLICT DO NOTHING
        """), {'id': str(TENANT_ID), 'name': TENANT_NAME, 'slug': TENANT_SLUG, 'now': now})
        print(f'  tenant: {TENANT_SLUG}  ({TENANT_ID})')

        # ── 2. RBAC ───────────────────────────────────────────────────────────
        print('\n=== 2. RBAC ===')
        for r in get_roles_seed():
            await db.execute(text("""
                INSERT INTO roles (id, code, name, is_system, tenant_id, is_active, created_at, updated_at)
                VALUES (:id, :code, :name, true, NULL, true, :now, :now)
                ON CONFLICT DO NOTHING
            """), {**r, 'now': now})

        for p in get_permisos_seed():
            await db.execute(text("""
                INSERT INTO permisos (id, code, description, is_active, created_at)
                VALUES (:id, :code, :description, true, :now)
                ON CONFLICT DO NOTHING
            """), {**p, 'now': now})

        for rol_code, perm_code, is_own in get_matriz_seed():
            rp_id = str(uuid.uuid5(uuid.NAMESPACE_OID, f'rp:{rol_code}:{perm_code}'))
            await db.execute(text("""
                INSERT INTO rol_permiso (id, tenant_id, rol_id, permiso_id, is_own_resource, created_at, updated_at)
                VALUES (
                    :id, NULL,
                    (SELECT id FROM roles WHERE code = :rol_code AND tenant_id IS NULL),
                    (SELECT id FROM permisos WHERE code = :perm_code),
                    :is_own, :now, :now
                )
                ON CONFLICT DO NOTHING
            """), {'id': rp_id, 'rol_code': rol_code, 'perm_code': perm_code, 'is_own': is_own, 'now': now})
        print('  roles, permisos y matriz listos')

        # ── 3. Usuarios staff ─────────────────────────────────────────────────
        print('\n=== 3. Staff ===')
        for u_data in STAFF_USERS:
            user = await upsert_user(db, u_data, now)
            await upsert_rol(db, user.id, u_data['rol'], now)

        # ── 4. Docentes ───────────────────────────────────────────────────────
        print('\n=== 4. Docentes ===')
        docente_users: dict[str, User] = {}
        for u_data in DOCENTES:
            user = await upsert_user(db, u_data, now)
            await upsert_rol(db, user.id, u_data['rol'], now)
            docente_users[u_data['email']] = user

        prof1  = docente_users['rgarcia@trace.dev']
        prof2  = docente_users['asilva@trace.dev']
        tutor1 = docente_users['cmartinez@trace.dev']
        tutor2 = docente_users['blopez@trace.dev']

        # ── 5. Alumnos demo (con cuenta de usuario) ───────────────────────────
        print('\n=== 5. Alumnos demo ===')
        alumno_users: dict[str, User] = {}
        for u_data in ALUMNOS_DEMO:
            user = await upsert_user(db, u_data, now)
            await upsert_rol(db, user.id, u_data['rol'], now)
            alumno_users[u_data['email']] = user

        # ── 6. Estructura académica ───────────────────────────────────────────
        print('\n=== 6. Estructura académica ===')

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
            print(f'  ✓ Carrera TPI creada: {carrera.id}')
        else:
            print(f'  · Carrera TPI existente: {carrera.id}')

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
            print(f'  ✓ Cohorte 2024-A creada: {cohorte.id}')
        else:
            print(f'  · Cohorte 2024-A existente: {cohorte.id}')

        materias_def = [
            ('ALGO1', 'Algoritmos y Estructuras de Datos'),
            ('BD1',   'Bases de Datos I'),
        ]
        materias: dict[str, Materia] = {}
        for codigo, nombre in materias_def:
            r = await db.execute(select(Materia).where(
                Materia.tenant_id == TENANT_ID, Materia.codigo == codigo,
                Materia.deleted_at.is_(None)
            ))
            m = r.scalar_one_or_none()
            if not m:
                m = Materia(codigo=codigo, nombre=nombre, estado='Activa',
                            created_at=now, updated_at=now)
                m.tenant_id = TENANT_ID
                db.add(m)
                await db.flush()
                print(f'  ✓ Materia {codigo} creada')
            else:
                print(f'  · Materia {codigo} existente')
            materias[codigo] = m

        # ── 7. Asignaciones ───────────────────────────────────────────────────
        print('\n=== 7. Asignaciones ===')

        asig_def = [
            (prof1,  'ALGO1', ['A', 'B'], tutor1),
            (prof2,  'BD1',   ['A', 'C'], tutor2),
        ]
        asignaciones: dict[tuple, Asignacion] = {}
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
                print(f'  ✓ {prof.apellidos} → {mat_code} {comisiones}  (tutor: {tutor.apellidos})')
            else:
                print(f'  · {prof.apellidos} → {mat_code} existente')
            asignaciones[(prof.id, mat_code)] = asig

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
                print(f'  ✓ {tutor.apellidos} → {mat_code} (TUTOR)')
            else:
                print(f'  · {tutor.apellidos} → {mat_code} (TUTOR) existente')

        # ── 8. Padrones y calificaciones ─────────────────────────────────────
        print('\n=== 8. Padrones y calificaciones ===')

        for mat_code, prof in [('ALGO1', prof1), ('BD1', prof2)]:
            mat  = materias[mat_code]
            asig = asignaciones[(prof.id, mat_code)]

            # Umbral
            await db.execute(text(
                f"DELETE FROM umbral_materia "
                f"WHERE asignacion_id = '{asig.id}' AND materia_id = '{mat.id}'"
            ))
            umbral = UmbralMateria(
                asignacion_id=asig.id, materia_id=mat.id,
                umbral_pct=UMBRAL_PCT,
                valores_aprobatorios=['Satisfactorio', 'Supera lo esperado'],
                created_at=now, updated_at=now,
            )
            umbral.tenant_id = TENANT_ID
            db.add(umbral)
            await db.flush()

            # VersionPadron (una por materia/cohorte)
            r = await db.execute(select(VersionPadron).where(
                VersionPadron.tenant_id == TENANT_ID,
                VersionPadron.materia_id == mat.id,
                VersionPadron.cohorte_id == cohorte.id,
                VersionPadron.activa.is_(True),
                VersionPadron.deleted_at.is_(None),
            ))
            vp = r.scalar_one_or_none()
            if not vp:
                vp = VersionPadron(
                    materia_id=mat.id, cohorte_id=cohorte.id,
                    cargado_por=ADMIN_ID, cargado_at=now, activa=True,
                    created_at=now, updated_at=now,
                )
                vp.tenant_id = TENANT_ID
                db.add(vp)
                await db.flush()

            # Limpiar calificaciones anteriores UNA sola vez (antes del loop)
            await db.execute(text(
                f"DELETE FROM calificaciones "
                f"WHERE asignacion_id = '{asig.id}' AND materia_id = '{mat.id}'"
            ))
            await db.flush()

            total_alumnos = 0
            total_cal     = 0

            for com_letra, alumnos_list, notas_list in COMISIONES_DATA:
                for (nombre, apellidos, email), notas in zip(alumnos_list, notas_list):
                    ep = EntradaPadron(
                        version_id=vp.id, nombre=nombre, apellidos=apellidos,
                        email_encrypted=encrypt(email), comision=com_letra,
                        regional='Buenos Aires', created_at=now, updated_at=now,
                    )
                    ep.tenant_id = TENANT_ID

                    # Linkear directamente si es alumno demo
                    if email in alumno_users:
                        ep.usuario_id = alumno_users[email].id

                    db.add(ep)
                    await db.flush()
                    total_alumnos += 1

                    for act, nota in zip(ACTIVIDADES, notas):
                        cal = Calificacion(
                            asignacion_id=asig.id, materia_id=mat.id,
                            entrada_padron_id=ep.id, actividad=act,
                            nota_numerica=nota if nota is not None else None,
                            nota_textual=None,
                            aprobado=(nota >= UMBRAL_NOTA) if nota is not None else False,
                            origen='Importado', importado_at=now,
                            created_at=now, updated_at=now,
                        )
                        cal.tenant_id = TENANT_ID
                        db.add(cal)
                        total_cal += 1

                await db.flush()

            print(f'  {mat_code}: {total_alumnos} alumnos, {total_cal} calificaciones')

        await db.commit()

    print()
    print('=' * 60)
    print('SEED COMPLETADO')
    print('=' * 60)
    print()
    print('Credenciales:')
    print()
    print('  STAFF')
    print('  ─────')
    for u in STAFF_USERS:
        print(f'  {u["email"]:<45} / {u["password"]:<14} → {u["rol"]}')
    print()
    print('  DOCENTES')
    print('  ────────')
    for u in DOCENTES:
        print(f'  {u["email"]:<45} / {u["password"]:<14} → {u["rol"]}')
    print()
    print('  ALUMNOS DEMO (pueden iniciar sesión)')
    print('  ─────────────────────────────────────')
    for u in ALUMNOS_DEMO:
        print(f'  {u["email"]:<45} / {u["password"]:<14} → {u["tag"]}')
    print()

    await engine.dispose()


asyncio.run(seed())
