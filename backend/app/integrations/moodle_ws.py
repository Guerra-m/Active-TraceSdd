"""Cliente HTTP para Moodle Web Services (C-09 padron-ingesta-moodle).

Provee MoodleWSClient para consultar participantes de un curso.

Errores:
  MoodleNotConfiguredError — MOODLE_URL o MOODLE_TOKEN vacíos → 422
  MoodleWSError            — error HTTP o respuesta de error de Moodle → 502
"""

import httpx

from app.core.config import get_settings


class MoodleNotConfiguredError(Exception):
    """Moodle WS no está configurado (MOODLE_URL o MOODLE_TOKEN vacíos)."""


class MoodleWSError(Exception):
    """Error al comunicarse con Moodle WS."""

    def __init__(self, message: str, *, retry_after: int | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class MoodleWSClient:
    """Cliente para Moodle Web Services REST API.

    Raises MoodleNotConfiguredError al construirse si MOODLE_URL o MOODLE_TOKEN
    están vacíos — el router debe capturarlo y devolver 422.
    """

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.moodle_url or not settings.moodle_token:
            raise MoodleNotConfiguredError(
                "Moodle WS no configurado. Configure MOODLE_URL y MOODLE_TOKEN."
            )
        self._base_url = settings.moodle_url.rstrip("/")
        self._token = settings.moodle_token
        self._timeout = settings.moodle_timeout

    async def get_course_participants(self, course_id: int) -> list[dict]:
        """Obtiene la lista de participantes inscriptos en un curso de Moodle.

        Args:
            course_id: ID numérico del curso en Moodle.

        Returns:
            Lista de dicts con keys: id, firstname, lastname, email, username, roles.

        Raises:
            MoodleWSError: si la respuesta HTTP falla o Moodle devuelve error.
        """
        url = f"{self._base_url}/webservice/rest/server.php"
        params = {
            "wstoken": self._token,
            "wsfunction": "core_enrol_get_enrolled_users",
            "moodlewsrestformat": "json",
            "courseid": course_id,
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url, params=params)
        except httpx.TimeoutException as e:
            raise MoodleWSError(
                f"Timeout al conectar con Moodle (courseid={course_id})",
                retry_after=60,
            ) from e
        except httpx.RequestError as e:
            raise MoodleWSError(
                f"Error de red al conectar con Moodle: {e}",
            ) from e

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise MoodleWSError("Moodle rate-limited (429)", retry_after=retry_after)

        if response.status_code >= 500:
            raise MoodleWSError(
                f"Moodle devolvió error del servidor: HTTP {response.status_code}",
                retry_after=120,
            )

        if not response.is_success:
            raise MoodleWSError(
                f"Moodle devolvió HTTP {response.status_code}"
            )

        data = response.json()

        # Moodle devuelve {"exception": ..., "message": ...} ante errores de WS
        if isinstance(data, dict) and "exception" in data:
            raise MoodleWSError(
                f"Error de Moodle WS: {data.get('message', data['exception'])}"
            )

        if not isinstance(data, list):
            raise MoodleWSError(
                f"Respuesta inesperada de Moodle (esperaba lista): {type(data).__name__}"
            )

        return data
