"""Instrumentacion OpenTelemetry para active-trace.

Inicializa la instrumentacion de FastAPI con OpenTelemetry de forma
que cada request HTTP genere un span de traza. La configuracion es
opcional: si no hay endpoint OTLP definido, la app arranca normalmente
sin exportar trazas (no hay acoplamiento a un backend de telemetria).

Uso:
    from app.core.observability import setup_telemetry
    setup_telemetry(app)  # llamar en el lifespan con la instancia FastAPI

Configuracion:
    OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
    Si la variable esta ausente o vacia, solo se configura un TracerProvider
    en memoria (NoopSpanExporter / SimpleSpanProcessor) sin exportar nada.
"""

import logging

logger = logging.getLogger(__name__)


def setup_telemetry(app=None, service_name: str = "active-trace") -> None:
    """Inicializa la instrumentacion OpenTelemetry para la app FastAPI.

    - Si OTEL_EXPORTER_OTLP_ENDPOINT esta configurado, exporta trazas via OTLP gRPC.
    - Si no esta configurado, instrumenta con un provider en memoria (sin exportar).
    - En ambos casos la app arranca sin fallar por ausencia del backend de telemetria.

    Args:
        app: Instancia de FastAPI. Si es None, solo configura el TracerProvider global.
        service_name: Nombre del servicio en las trazas (default: "active-trace").
    """
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

        from app.core.config import get_settings

        settings = get_settings()
        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)

        otlp_endpoint = settings.otel_exporter_otlp_endpoint
        if otlp_endpoint:
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                    OTLPSpanExporter,
                )

                otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
                provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
                logger.info(
                    "OpenTelemetry: exportando trazas via OTLP",
                    extra={"endpoint": otlp_endpoint},
                )
            except Exception as exc:
                # Si el exporter falla (backend no disponible), continuar sin exportar
                logger.warning(
                    "OpenTelemetry: no se pudo configurar el exporter OTLP; "
                    "la app continua sin exportar trazas.",
                    extra={"error": str(exc)},
                )
        else:
            logger.info(
                "OpenTelemetry: OTEL_EXPORTER_OTLP_ENDPOINT no configurado; "
                "instrumentacion activa sin exportacion."
            )

        trace.set_tracer_provider(provider)

        # Instrumentar FastAPI si se provee la instancia
        if app is not None:
            try:
                from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

                FastAPIInstrumentor.instrument_app(app)
                logger.info("OpenTelemetry: FastAPI instrumentado correctamente.")
            except Exception as exc:
                logger.warning(
                    "OpenTelemetry: no se pudo instrumentar FastAPI.",
                    extra={"error": str(exc)},
                )

    except ImportError as exc:
        # Si opentelemetry no esta instalado, no fallar el arranque
        logger.warning(
            "OpenTelemetry no disponible; la app arranca sin instrumentacion.",
            extra={"error": str(exc)},
        )
    except Exception as exc:
        # Cualquier otro error en la configuracion de OTel no debe bloquear el arranque
        logger.warning(
            "Error al inicializar OpenTelemetry; la app continua sin trazas.",
            extra={"error": str(exc)},
        )
