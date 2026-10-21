from app.application.ports.repositorios import UsuarioRepositorio
from app.application.ports.seguridad import HasherPuerto
from app.domain.entities.usuario import Usuario
from app.domain.exceptions import ReglaDeNegocioViolada
from app.domain.value_objects.rol import Rol

LONGITUD_MINIMA_PASSWORD = 10


class CrearUsuario:
    def __init__(self, usuarios: UsuarioRepositorio, hasher: HasherPuerto):
        self._usuarios = usuarios
        self._hasher = hasher

    def ejecutar(self, nombre: str, correo: str, password: str, roles: list) -> Usuario:
        if len(password) < LONGITUD_MINIMA_PASSWORD:
            raise ReglaDeNegocioViolada(
                f"La contraseña debe tener al menos {LONGITUD_MINIMA_PASSWORD} caracteres."
            )
        if self._usuarios.obtener_por_correo(correo.strip().lower()):
            raise ReglaDeNegocioViolada("Ya existe un usuario con ese correo.")
        usuario = Usuario(
            nombre=nombre.strip(),
            correo=correo,
            password_hash=self._hasher.hashear(password),
            roles=frozenset(Rol(r) for r in roles),
        )
        return self._usuarios.guardar(usuario)
