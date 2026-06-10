"""Seed data para el catálogo RBAC — roles, permisos y matriz base.

Este módulo contiene los datos del seed RBAC que se insertan en la migración 003.
También es usado por los tests de integración para poblar la DB de prueba.

Los UUIDs son determinísticos (uuid5) para que el seed sea reproducible
y los tests puedan referenciar IDs conocidos.

Fuente: knowledge-base/03_actores_y_roles.md §3.3
"""

import uuid
from datetime import datetime, timezone


def _uid(key: str) -> str:
    """UUID5 determinístico desde una clave de dominio."""
    return str(uuid.uuid5(uuid.NAMESPACE_OID, key))


def get_roles_seed() -> list[dict]:
    """Los 7 roles del dominio (is_system=True, tenant_id=NULL)."""
    return [
        {"id": _uid("role:ALUMNO"),      "code": "ALUMNO",      "name": "Alumno"},
        {"id": _uid("role:TUTOR"),       "code": "TUTOR",       "name": "Tutor"},
        {"id": _uid("role:PROFESOR"),    "code": "PROFESOR",    "name": "Profesor"},
        {"id": _uid("role:COORDINADOR"), "code": "COORDINADOR", "name": "Coordinador"},
        {"id": _uid("role:NEXO"),        "code": "NEXO",        "name": "Nexo"},
        {"id": _uid("role:ADMIN"),       "code": "ADMIN",       "name": "Admin"},
        {"id": _uid("role:FINANZAS"),    "code": "FINANZAS",    "name": "Finanzas"},
    ]


def get_permisos_seed() -> list[dict]:
    """Permisos del dominio (≥21) en formato modulo:accion."""
    permisos = [
        ("academico:ver_propio",        "Ver estado académico propio del alumno"),
        ("evaluacion:reservar",         "Reservar instancia de evaluación"),
        ("avisos:confirmar",            "Confirmar (acknowledge) avisos"),
        ("avisos:publicar",             "Publicar avisos para alumnos"),
        ("calificaciones:importar",     "Importar calificaciones desde Moodle"),
        ("atrasados:ver",               "Ver alumnos con atrasos en entregas"),
        ("entregas:ver",                "Ver entregas sin corregir"),
        ("comunicacion:enviar",         "Enviar comunicaciones a alumnos"),
        ("comunicacion:aprobar",        "Aprobar comunicaciones masivas"),
        ("encuentros:gestionar",        "Gestionar encuentros docentes"),
        ("guardias:registrar",          "Registrar guardias"),
        ("tareas:gestionar",            "Gestionar tareas internas"),
        ("equipos:asignar",             "Gestionar equipos docentes y asignaciones"),
        ("estructura:gestionar",        "Gestionar estructura académica (carreras, cohortes, materias)"),
        ("usuarios:gestionar",          "Gestionar usuarios del tenant"),
        ("auditoria:ver",               "Ver registros de auditoría"),
        ("liquidaciones:operar",        "Operar grilla salarial"),
        ("liquidaciones:cerrar",        "Calcular y cerrar liquidaciones"),
        ("facturas:gestionar",          "Gestionar facturas"),
        ("tenant:configurar",           "Configurar el tenant"),
        ("impersonacion:usar",          "Impersonar a otro usuario (soporte/ADMIN)"),
        ("roles:ver",                   "Ver catálogo de roles y permisos"),
    ]
    return [
        {"id": _uid(f"perm:{code}"), "code": code, "description": desc}
        for code, desc in permisos
    ]


def get_matriz_seed() -> list[tuple[str, str, bool]]:
    """Matriz rol_permiso base: (rol_code, permiso_code, is_own_resource).

    Basada en knowledge-base/03_actores_y_roles.md §3.3.
    (propio) → is_own_resource=True
    NEXO     → sin permisos predefinidos (configurable por tenant)
    """
    return [
        # ALUMNO
        ("ALUMNO", "academico:ver_propio",    False),
        ("ALUMNO", "evaluacion:reservar",     False),
        ("ALUMNO", "avisos:confirmar",        False),

        # TUTOR
        ("TUTOR", "avisos:confirmar",         False),
        ("TUTOR", "atrasados:ver",            False),
        ("TUTOR", "entregas:ver",             False),
        ("TUTOR", "encuentros:gestionar",     False),
        ("TUTOR", "guardias:registrar",       True),   # (propio)

        # PROFESOR
        ("PROFESOR", "avisos:confirmar",      False),
        ("PROFESOR", "calificaciones:importar", True), # (propio)
        ("PROFESOR", "atrasados:ver",         True),   # (propio)
        ("PROFESOR", "entregas:ver",          True),   # (propio)
        ("PROFESOR", "comunicacion:enviar",   True),   # (propio)
        ("PROFESOR", "encuentros:gestionar",  True),   # (propio)
        ("PROFESOR", "guardias:registrar",    True),   # (propio)
        ("PROFESOR", "tareas:gestionar",      True),   # (propio)

        # COORDINADOR
        ("COORDINADOR", "avisos:confirmar",       False),
        ("COORDINADOR", "calificaciones:importar", False),
        ("COORDINADOR", "atrasados:ver",           False),
        ("COORDINADOR", "entregas:ver",            False),
        ("COORDINADOR", "comunicacion:enviar",     False),
        ("COORDINADOR", "comunicacion:aprobar",    False),
        ("COORDINADOR", "encuentros:gestionar",    False),
        ("COORDINADOR", "guardias:registrar",      False),
        ("COORDINADOR", "tareas:gestionar",        False),
        ("COORDINADOR", "avisos:publicar",         False),
        ("COORDINADOR", "equipos:asignar",         False),
        ("COORDINADOR", "auditoria:ver",           True),  # (propio)

        # ADMIN
        ("ADMIN", "avisos:confirmar",          False),
        ("ADMIN", "calificaciones:importar",   False),
        ("ADMIN", "atrasados:ver",             False),
        ("ADMIN", "entregas:ver",              False),
        ("ADMIN", "comunicacion:enviar",       False),
        ("ADMIN", "comunicacion:aprobar",      False),
        ("ADMIN", "encuentros:gestionar",      False),
        ("ADMIN", "guardias:registrar",        False),
        ("ADMIN", "tareas:gestionar",          False),
        ("ADMIN", "avisos:publicar",           False),
        ("ADMIN", "equipos:asignar",           False),
        ("ADMIN", "estructura:gestionar",      False),
        ("ADMIN", "usuarios:gestionar",        False),
        ("ADMIN", "auditoria:ver",             False),
        ("ADMIN", "tenant:configurar",         False),
        ("ADMIN", "roles:ver",                 False),
        ("ADMIN", "impersonacion:usar",        False),

        # FINANZAS
        ("FINANZAS", "avisos:confirmar",       False),
        ("FINANZAS", "auditoria:ver",          False),
        ("FINANZAS", "liquidaciones:operar",   False),
        ("FINANZAS", "liquidaciones:cerrar",   False),
        ("FINANZAS", "facturas:gestionar",     False),

        # NEXO — sin permisos predefinidos (configurable por tenant)
    ]


async def insert_rbac_seed(session) -> None:
    """Inserta el seed RBAC completo en la sesión async dada.

    Usado en tests para poblar la DB de prueba con los datos del catálogo.
    Llama flush() pero no commit() — el test controla la transacción.
    """
    import uuid as uuid_mod
    from sqlalchemy import text

    from app.models.permiso import Permiso
    from app.models.rol import Rol
    from app.models.rol_permiso import RolPermiso

    now = datetime.now(timezone.utc)

    # --- Insertar roles ---
    roles_by_code = {}
    for r in get_roles_seed():
        rol = Rol(
            id=uuid_mod.UUID(r["id"]),
            code=r["code"],
            name=r["name"],
            is_system=True,
            tenant_id=None,
            is_active=True,
        )
        session.add(rol)
        roles_by_code[r["code"]] = rol

    await session.flush()

    # --- Insertar permisos ---
    perms_by_code = {}
    for p in get_permisos_seed():
        perm = Permiso(
            id=uuid_mod.UUID(p["id"]),
            code=p["code"],
            description=p["description"],
            is_active=True,
        )
        session.add(perm)
        perms_by_code[p["code"]] = perm

    await session.flush()

    # --- Insertar matriz rol_permiso (con tenant_id=None para el seed base) ---
    for rol_code, perm_code, is_own in get_matriz_seed():
        rol = roles_by_code[rol_code]
        perm = perms_by_code[perm_code]
        rp_id = uuid_mod.UUID(str(uuid_mod.uuid5(uuid_mod.NAMESPACE_OID, f"rp:{rol_code}:{perm_code}")))
        # RolPermiso.tenant_id es nullable=True para admitir el seed global
        rp = RolPermiso(
            id=rp_id,
            tenant_id=None,
            rol_id=rol.id,
            permiso_id=perm.id,
            is_own_resource=is_own,
        )
        session.add(rp)

    await session.flush()
