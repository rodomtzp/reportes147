from typing import Dict, Iterable, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.ports.repositorios import UsuarioRepositorio
from app.domain.entities.usuario import Usuario
from app.domain.value_objects.rol import Rol
from app.infrastructure.persistence.models import UsuarioModel, UsuarioRolModel
from app.infrastructure.persistence.utils import flush_o_conflicto


def _a_entidad(m: UsuarioModel) -> Usuario:
    return Usuario(
        id=m.id,
        nombre=m.nombre,
        correo=m.correo,
        password_hash=m.password_hash,
        activo=m.activo,
        debe_cambiar_password=m.debe_cambiar_password,
        roles=frozenset(r.rol for r in m.roles),
        intentos_fallidos=m.intentos_fallidos,
        bloqueado_hasta=m.bloqueado_hasta,
        sesion_version=m.sesion_version,
    )


class UsuarioRepositorioSQLAlchemy(UsuarioRepositorio):
    def __init__(self, session: Session):
        self._s = session

    def obtener_por_id(self, usuario_id: int) -> Optional[Usuario]:
        m = self._s.get(UsuarioModel, usuario_id)
        return _a_entidad(m) if m else None

    def obtener_por_ids(self, ids: Iterable[int]) -> Dict[int, Usuario]:
        ids = list(ids)
        if not ids:
            return {}
        filas = self._s.scalars(select(UsuarioModel).where(UsuarioModel.id.in_(ids))).all()
        return {m.id: _a_entidad(m) for m in filas}

    def obtener_por_correo(self, correo: str) -> Optional[Usuario]:
        m = self._s.scalar(select(UsuarioModel).where(UsuarioModel.correo == correo.strip().lower()))
        return _a_entidad(m) if m else None

    def listar(self, rol: Optional[Rol] = None, activo: Optional[bool] = None) -> List[Usuario]:
        q = select(UsuarioModel).order_by(UsuarioModel.nombre)
        if rol is not None:
            q = q.where(UsuarioModel.roles.any(UsuarioRolModel.rol == rol.value))
        if activo is not None:
            q = q.where(UsuarioModel.activo.is_(activo))
        return [_a_entidad(m) for m in self._s.scalars(q).all()]

    def guardar(self, usuario: Usuario) -> Usuario:
        m = self._s.get(UsuarioModel, usuario.id) if usuario.id else UsuarioModel()
        m.nombre = usuario.nombre
        m.correo = usuario.correo
        m.password_hash = usuario.password_hash
        m.activo = usuario.activo
        m.debe_cambiar_password = usuario.debe_cambiar_password
        m.intentos_fallidos = usuario.intentos_fallidos
        m.bloqueado_hasta = usuario.bloqueado_hasta
        m.sesion_version = usuario.sesion_version
        # Sincroniza roles sin borrar y recrear filas con la misma clave primaria.
        actuales = {r.rol: r for r in m.roles}
        deseados = {r.value for r in usuario.roles}
        for rol, fila in actuales.items():
            if rol not in deseados:
                m.roles.remove(fila)
        for rol in deseados - set(actuales):
            m.roles.append(UsuarioRolModel(rol=rol))
        self._s.add(m)
        flush_o_conflicto(self._s)
        usuario.id = m.id
        return usuario
