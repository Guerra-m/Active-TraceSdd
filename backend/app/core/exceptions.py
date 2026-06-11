"""Excepciones y handlers estandarizados de la aplicacion.

Excepciones de dominio usadas por los servicios para señalizar
condiciones de error específicas del negocio.
"""


class DomainError(Exception):
    """Excepción base para errores de dominio."""
    pass


class LiquidacionCerradaError(DomainError):
    """Se intenta modificar o cerrar una liquidación ya cerrada (RN-22)."""

    def __init__(self, liquidacion_id=None):
        msg = "La liquidación ya está cerrada y es inmutable."
        if liquidacion_id:
            msg = f"La liquidación {liquidacion_id} ya está cerrada y es inmutable."
        super().__init__(msg)


class SalarioNoEncontradoError(DomainError):
    """No existe salario vigente para el rol y período solicitado."""

    def __init__(self, rol: str = "", periodo: str = ""):
        msg = f"No existe salario vigente para rol='{rol}' en período '{periodo}'."
        super().__init__(msg)
