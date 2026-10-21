from functools import wraps

from flask import current_app, g, request

from app.domain.exceptions import CambioDePasswordRequerido, NoAutenticado, PermisoDenegado
from app.domain.policies.politica_permisos import Permiso, tiene_permiso


def _extraer_bearer() -> str:
    partes = request.headers.get("Authorization", "").split()
    if len(partes) != 2 or partes[0].lower() != "bearer":
        raise NoAutenticado("Falta el token de autenticación.")
    return partes[1]


def requiere_autenticacion(f=None, *, permitir_password_pendiente: bool = False):
    """Exige un access token válido.

    Si el usuario tiene una contraseña temporal pendiente de cambio, solo puede
    usar los endpoints marcados con permitir_password_pendiente=True.
    Se puede usar como @requiere_autenticacion o @requiere_autenticacion(permitir_password_pendiente=True).
    """

    def decorador(func):
        @wraps(func)
        def envoltura(*args, **kwargs):
            container = current_app.extensions["container"]
            usuario = container.usuario_autenticado().ejecutar(_extraer_bearer())
            if usuario.debe_cambiar_password and not permitir_password_pendiente:
                raise CambioDePasswordRequerido("Debes cambiar tu contraseña temporal para continuar.")
            g.usuario = usuario
            return func(*args, **kwargs)

        return envoltura

    return decorador(f) if f is not None else decorador


def requiere_permiso(permiso: Permiso):
    def decorador(f):
        @wraps(f)
        @requiere_autenticacion
        def envoltura(*args, **kwargs):
            if not tiene_permiso(g.usuario.roles, permiso):
                raise PermisoDenegado("No tienes permiso para realizar esta acción.")
            return f(*args, **kwargs)

        return envoltura

    return decorador
