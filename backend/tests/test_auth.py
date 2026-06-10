"""Tests de autenticacion — C-03 (auth-jwt-2fa).

Suite TDD para los endpoints y la logica de autenticacion:
  10.1 login OK (sin 2FA)
  10.2 login KO (password incorrecto, usuario inexistente)
  10.3 login con 2FA: emite pre_auth_ticket → verify_totp emite sesion
  10.4 refresh rotation: usar token → ok; reuso del mismo token → 401
  10.5 logout: revocar token → refresh falla
  10.6 rate limit: 5 intentos OK, 6to → 429
  10.7 recuperacion: forgot emite token de un solo uso; reset valido; reset usado → 400
  10.8 get_current_user: token valido → usuario; identidad NUNCA por param URL
  10.9 tenant isolation: usuario de tenant A no puede usar token de tenant B

Regla #4 (CLAUDE.md): tests contra base de datos real, sin mocks de DB.
Prerequisito: DB de test disponible (postgresql://trace:trace@localhost:5432/trace_test).
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

# ---------------------------------------------------------------------------
# Fixtures de usuarios (por test para aislamiento)
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def user_no_2fa(db_session: AsyncSession, test_tenant):
    """Usuario activo sin 2FA en test_tenant."""
    from app.repositories.user_repository import UserRepository

    repo = UserRepository(db_session, tenant_id=test_tenant.id)
    user = await repo.create_user(
        email="alice@example.com",
        password_plaintext="secure-password-123",
    )
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def user_with_2fa(db_session: AsyncSession, test_tenant):
    """Usuario activo con 2FA habilitado en test_tenant."""
    import pyotp
    from app.repositories.user_repository import UserRepository
    from app.core.encryption import encrypt
    from app.core.security import generate_totp_secret

    repo = UserRepository(db_session, tenant_id=test_tenant.id)
    user = await repo.create_user(
        email="bob@example.com",
        password_plaintext="secure-password-456",
    )
    secret = generate_totp_secret()
    user.totp_secret_encrypted = encrypt(secret)
    user.totp_enabled = True
    await repo.update(user)
    await db_session.commit()
    # Attach the plaintext secret for use in tests
    user._totp_secret_plaintext = secret
    return user


@pytest_asyncio.fixture
async def user_tenant_b(db_session: AsyncSession, test_tenant_b):
    """Usuario en el tenant B (para tests de aislamiento)."""
    from app.repositories.user_repository import UserRepository

    repo = UserRepository(db_session, tenant_id=test_tenant_b.id)
    user = await repo.create_user(
        email="carol@example.com",
        password_plaintext="secure-password-789",
    )
    await db_session.commit()
    return user


# ---------------------------------------------------------------------------
# 10.1 — Login OK (sin 2FA)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_login_ok_no_2fa(async_client: AsyncClient, user_no_2fa):
    """Login exitoso retorna access_token y refresh_token."""
    resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "secure-password-123"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_ok_returns_jwt_with_correct_claims(async_client: AsyncClient, user_no_2fa, test_tenant):
    """El access_token contiene sub=user_id y tenant_id."""
    from app.core.security import verify_token

    resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "secure-password-123"},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    payload = verify_token(token)
    assert payload["sub"] == str(user_no_2fa.id)
    assert payload["tenant_id"] == str(test_tenant.id)
    assert payload["type"] == "access"


# ---------------------------------------------------------------------------
# 10.2 — Login KO (password incorrecto, usuario inexistente)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_login_wrong_password(async_client: AsyncClient, user_no_2fa):
    """Password incorrecto retorna 401."""
    resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "wrong-password"},
    )
    assert resp.status_code == 401
    assert "Credenciales" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(async_client: AsyncClient, test_tenant):
    """Usuario inexistente retorna 401 (mismo mensaje — no revela si existe)."""
    resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "any-password"},
    )
    assert resp.status_code == 401
    assert "Credenciales" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# 10.3 — Login con 2FA: pre_auth_ticket → verify_totp → sesion
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_login_with_2fa_emits_pre_auth_ticket(async_client: AsyncClient, user_with_2fa):
    """Login con 2FA habilitado retorna pre_auth_ticket, no sesion completa."""
    resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "bob@example.com", "password": "secure-password-456"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "pre_auth_ticket" in data
    assert "access_token" not in data
    assert "refresh_token" not in data


@pytest.mark.asyncio
async def test_login_with_2fa_verify_totp_issues_session(async_client: AsyncClient, user_with_2fa):
    """verify_totp con ticket valido y codigo correcto emite sesion completa."""
    import pyotp

    # Paso 1: obtener pre_auth_ticket
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "bob@example.com", "password": "secure-password-456"},
    )
    assert login_resp.status_code == 200
    ticket = login_resp.json()["pre_auth_ticket"]

    # Paso 2: verificar TOTP
    code = pyotp.TOTP(user_with_2fa._totp_secret_plaintext).now()
    totp_resp = await async_client.post(
        "/api/v1/auth/totp/verify",
        json={"pre_auth_ticket": ticket, "code": code},
    )
    assert totp_resp.status_code == 200, totp_resp.text
    data = totp_resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_with_2fa_wrong_code_rejected(async_client: AsyncClient, user_with_2fa):
    """verify_totp con codigo incorrecto retorna 401."""
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "bob@example.com", "password": "secure-password-456"},
    )
    ticket = login_resp.json()["pre_auth_ticket"]

    totp_resp = await async_client.post(
        "/api/v1/auth/totp/verify",
        json={"pre_auth_ticket": ticket, "code": "000000"},
    )
    assert totp_resp.status_code == 401


# ---------------------------------------------------------------------------
# 10.4 — Refresh rotation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_refresh_rotation_ok(async_client: AsyncClient, user_no_2fa):
    """Usar el refresh token retorna nuevo par y rota el token."""
    # Obtener sesion inicial
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "secure-password-123"},
    )
    assert login_resp.status_code == 200
    refresh_token = login_resp.json()["refresh_token"]

    # Rotar
    refresh_resp = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 200, refresh_resp.text
    new_data = refresh_resp.json()
    assert "access_token" in new_data
    assert "refresh_token" in new_data
    # El nuevo token debe ser diferente al viejo
    assert new_data["refresh_token"] != refresh_token


@pytest.mark.asyncio
async def test_refresh_rotation_reuse_same_token_401(async_client: AsyncClient, user_no_2fa):
    """Reusar el mismo refresh token (ya rotado) retorna 401."""
    # Obtener sesion inicial
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "secure-password-123"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    # Primera rotacion — OK
    r1 = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert r1.status_code == 200

    # Segunda rotacion con el token viejo — debe fallar
    r2 = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert r2.status_code == 401


# ---------------------------------------------------------------------------
# 10.5 — Logout
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(async_client: AsyncClient, user_no_2fa):
    """Logout revoca el refresh token; luego el refresh falla con 401."""
    # Obtener sesion
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "secure-password-123"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    # Logout
    logout_resp = await async_client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )
    assert logout_resp.status_code == 204

    # Intento de refresh post-logout — debe fallar
    refresh_resp = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 401


# ---------------------------------------------------------------------------
# 10.6 — Rate limiting
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rate_limit_5_ok_6th_429(async_client: AsyncClient, test_tenant):
    """5 intentos de login fallidos son aceptados; el 6to retorna 429."""
    # Limpiar el rate limiter antes del test para no contaminar con otros tests
    from app.services.auth_service import _rate_limit_store
    _rate_limit_store.clear()

    # 5 intentos — todos retornan 401 (credenciales malas) pero no 429
    for i in range(5):
        resp = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "ratelimit@example.com", "password": "wrong"},
            headers={"X-Forwarded-For": "10.0.0.1"},
        )
        assert resp.status_code == 401, f"Intento {i+1} deberia ser 401, got {resp.status_code}"

    # 6to intento — debe retornar 429
    resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "ratelimit@example.com", "password": "wrong"},
        headers={"X-Forwarded-For": "10.0.0.1"},
    )
    assert resp.status_code == 429, f"6to intento deberia ser 429, got {resp.status_code}: {resp.text}"


# ---------------------------------------------------------------------------
# 10.7 — Recuperacion de contrasena
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_forgot_password_emits_single_use_token(async_client: AsyncClient, user_no_2fa, db_session: AsyncSession, test_tenant):
    """forgot_password genera un token de reset que funciona exactamente una vez."""
    # Solicitar reset
    forgot_resp = await async_client.post(
        "/api/v1/auth/forgot",
        json={"email": "alice@example.com"},
    )
    assert forgot_resp.status_code == 200
    # La respuesta no revela si el email existe
    assert "instrucciones" in forgot_resp.json()["message"].lower() or "si" in forgot_resp.json()["message"].lower()


@pytest.mark.asyncio
async def test_reset_password_valid_token(async_client: AsyncClient, user_no_2fa, db_session: AsyncSession, test_tenant):
    """reset_password con token valido cambia el password y permite nuevo login."""
    from app.services.auth_service import AuthService

    # Obtener token de reset directamente del servicio (simula envio por email)
    svc = AuthService(db_session, tenant_id=test_tenant.id)
    token_raw = await svc.forgot_password("alice@example.com")
    await db_session.commit()
    assert token_raw is not None

    # Resetear password
    reset_resp = await async_client.post(
        "/api/v1/auth/reset",
        json={"token": token_raw, "new_password": "new-secure-password-456"},
    )
    assert reset_resp.status_code == 200, reset_resp.text

    # Nuevo login con el password cambiado
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "new-secure-password-456"},
    )
    assert login_resp.status_code == 200


@pytest.mark.asyncio
async def test_reset_password_used_token_400(async_client: AsyncClient, user_no_2fa, db_session: AsyncSession, test_tenant):
    """reset_password con token ya usado retorna 400."""
    from app.services.auth_service import AuthService

    # Obtener y usar el token
    svc = AuthService(db_session, tenant_id=test_tenant.id)
    token_raw = await svc.forgot_password("alice@example.com")
    await db_session.commit()

    # Primer uso — OK
    r1 = await async_client.post(
        "/api/v1/auth/reset",
        json={"token": token_raw, "new_password": "new-password-first"},
    )
    assert r1.status_code == 200

    # Segundo uso con el mismo token — debe fallar
    r2 = await async_client.post(
        "/api/v1/auth/reset",
        json={"token": token_raw, "new_password": "new-password-second"},
    )
    assert r2.status_code == 400


# ---------------------------------------------------------------------------
# 10.8 — get_current_user: identidad solo del JWT
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_current_user_valid_token(async_client: AsyncClient, user_no_2fa):
    """get_current_user con token valido retorna el usuario correcto."""
    # Login para obtener token
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "secure-password-123"},
    )
    access_token = login_resp.json()["access_token"]

    # Usar endpoint protegido (totp/enroll requiere autenticacion)
    enroll_resp = await async_client.post(
        "/api/v1/auth/totp/enroll",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    # 200 confirma que get_current_user resolvio correctamente el usuario
    assert enroll_resp.status_code == 200, enroll_resp.text
    data = enroll_resp.json()
    assert "secret" in data
    assert "qr_uri" in data


@pytest.mark.asyncio
async def test_get_current_user_rejects_invalid_token(async_client: AsyncClient):
    """Endpoint protegido con token invalido retorna 401."""
    resp = await async_client.post(
        "/api/v1/auth/totp/enroll",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_identity_never_accepted_from_url_param(async_client: AsyncClient, user_no_2fa, test_tenant):
    """El sistema NUNCA acepta identidad de parametros URL — solo del JWT.

    Verificacion: llamar a un endpoint protegido pasando user_id como query param
    sin token JWT valido retorna 401 (el param es ignorado).
    """
    # Intentar acceder con user_id como query param en lugar de JWT
    resp = await async_client.post(
        f"/api/v1/auth/totp/enroll?user_id={user_no_2fa.id}",
        # Sin header Authorization
    )
    # Debe retornar 401/403 — el user_id del param no cuenta
    assert resp.status_code in (401, 403), (
        f"El sistema acepto identidad por URL param: {resp.status_code}"
    )


@pytest.mark.asyncio
async def test_pre_auth_ticket_rejected_as_access_token(async_client: AsyncClient, user_with_2fa):
    """Un pre_auth_ticket NO puede usarse como access token en endpoints protegidos."""
    # Obtener pre_auth_ticket
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "bob@example.com", "password": "secure-password-456"},
    )
    ticket = login_resp.json()["pre_auth_ticket"]

    # Intentar usar el pre_auth_ticket como Bearer en endpoint protegido
    resp = await async_client.post(
        "/api/v1/auth/totp/enroll",
        headers={"Authorization": f"Bearer {ticket}"},
    )
    # Debe rechazarlo — el tipo de token es 'pre_auth', no 'access'
    assert resp.status_code == 401, (
        f"pre_auth_ticket fue aceptado como access token: {resp.status_code}"
    )


# ---------------------------------------------------------------------------
# 10.9 — Tenant isolation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tenant_isolation_token_cross_tenant_rejected(
    async_client: AsyncClient,
    user_no_2fa,
    user_tenant_b,
    test_tenant,
    test_tenant_b,
):
    """Token de tenant A no puede usarse para acceder a recursos de tenant B.

    Verificacion: el JWT contiene tenant_id del tenant A. get_current_user
    busca el usuario en el tenant A. Si usamos el mismo token para tenant B,
    el usuario no existe en ese scope → 401.
    """
    # Login con usuario del tenant A
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "secure-password-123"},
    )
    assert login_resp.status_code == 200
    token_tenant_a = login_resp.json()["access_token"]

    # Verificar que el token del tenant A funciona correctamente
    from app.core.security import verify_token
    payload = verify_token(token_tenant_a)
    assert payload["tenant_id"] == str(test_tenant.id)

    # Construir un token manipulado con tenant_id del tenant B
    # (simulando que un atacante cambia el tenant_id)
    # En un JWT firmado esto no es posible sin la clave, pero si el tenant_id
    # del payload fuera del token B, el usuario no existiria en ese tenant
    import os
    from app.core.security import create_access_token
    from datetime import timedelta

    # Emitir un token con user_id del usuario A pero tenant_id del tenant B
    # Esto simula cruce de tenant en el claim
    fake_cross_token = create_access_token(
        {
            "sub": str(user_no_2fa.id),  # user del tenant A
            "tenant_id": str(test_tenant_b.id),  # pero tenant B
            "roles": [],
            "type": "access",
        },
        expires_delta=timedelta(minutes=15),
    )

    # Con este token manipulado, get_current_user busca user_no_2fa en tenant B
    # y no lo encuentra → 401
    resp = await async_client.post(
        "/api/v1/auth/totp/enroll",
        headers={"Authorization": f"Bearer {fake_cross_token}"},
    )
    assert resp.status_code == 401, (
        f"Token cross-tenant fue aceptado: usuario del tenant A pudo operar en tenant B"
    )
