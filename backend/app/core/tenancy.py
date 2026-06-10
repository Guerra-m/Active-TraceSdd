"""Modulo de multi-tenancy — resolucion y aislamiento de tenant.

Implementa C-03 (auth-jwt-2fa):
  - get_tenant_id_from_token: extrae y valida tenant_id del payload JWT
  - get_current_tenant: dependency FastAPI que resuelve el tenant del request

Reglas duras:
  - tenant_id SIEMPRE del JWT verificado, nunca de parametros del request (#8, #9)
  - Un query sin scope de tenant es un bug que falla en code review (#9)
"""

from uuid import UUID


def get_tenant_id_from_token(token_payload: dict) -> UUID:
    """Extrae el tenant_id del payload JWT verificado.

    Args:
        token_payload: Payload del JWT ya verificado (sin la firma).
                       Debe contener el claim 'tenant_id' como string UUID.

    Returns:
        UUID del tenant extraido del token.

    Raises:
        ValueError: Si el claim 'tenant_id' no existe o no es un UUID válido.
    """
    tenant_id_raw = token_payload.get("tenant_id")
    if not tenant_id_raw:
        raise ValueError("Claim 'tenant_id' ausente en el token JWT")

    try:
        return UUID(str(tenant_id_raw))
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"Claim 'tenant_id' no es un UUID válido: {tenant_id_raw!r}") from exc


async def get_current_tenant() -> UUID:
    """Placeholder — usar get_current_user de app.core.dependencies para obtener usuario+tenant.

    El tenant_id real se extrae en get_current_user desde el JWT verificado.
    """
    raise NotImplementedError(
        "Usar get_current_user de app.core.dependencies para obtener usuario+tenant."
    )
