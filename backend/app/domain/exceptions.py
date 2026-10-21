class ErrorDominio(Exception):
    """Base de los errores de negocio."""


class NoAutenticado(ErrorDominio):
    """Falta o es inválida la identidad del usuario."""


class CredencialesInvalidas(NoAutenticado):
    """Correo o contraseña incorrectos (mensaje deliberadamente genérico)."""


class CuentaBloqueada(NoAutenticado):
    """Demasiados intentos fallidos de inicio de sesión: la cuenta espera unos minutos."""


class PermisoDenegado(ErrorDominio):
    """El usuario está autenticado pero no tiene permiso."""


class ReglaDeNegocioViolada(ErrorDominio):
    """Una regla del dominio impide la operación."""


class NoEncontrado(ErrorDominio):
    """El recurso solicitado no existe."""


class Conflicto(ErrorDominio):
    """La operación choca con datos existentes (duplicados, restricciones)."""


class CambioDePasswordRequerido(PermisoDenegado):
    """El usuario debe cambiar su contraseña temporal antes de continuar."""
