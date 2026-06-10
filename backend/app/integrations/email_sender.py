"""Capa de envío de email — stub y SMTP real (C-12).

En dev/test: EMAIL_BACKEND=stub → escribe a log, sin SMTP real.
En prod: EMAIL_BACKEND=smtp → configura con SMTP_HOST, SMTP_PORT, etc.
"""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class AbstractEmailSender(ABC):

    @abstractmethod
    async def send(self, to: str, asunto: str, cuerpo: str) -> None:
        """Envía un email. Lanza excepción si falla."""


class StubSender(AbstractEmailSender):
    """Sender stub para desarrollo y tests — escribe a log, no envía SMTP."""

    async def send(self, to: str, asunto: str, cuerpo: str) -> None:
        logger.info(
            "STUB EMAIL enviado",
            extra={"to": to, "asunto": asunto, "cuerpo_len": len(cuerpo)},
        )


class SmtpSender(AbstractEmailSender):
    """Placeholder para sender SMTP real. Configurar via settings en prod."""

    def __init__(self, host: str, port: int, user: str, password: str, from_addr: str) -> None:
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._from_addr = from_addr

    async def send(self, to: str, asunto: str, cuerpo: str) -> None:
        # TODO(C-12-prod): implementar con aiosmtplib
        raise NotImplementedError("SmtpSender pendiente de configuración SMTP")


def get_sender() -> AbstractEmailSender:
    """Fábrica de sender según settings.email_backend."""
    from app.core.config import get_settings
    settings = get_settings()
    if getattr(settings, "email_backend", "stub") == "stub":
        return StubSender()
    raise ValueError(f"email_backend desconocido: {settings.email_backend}")
