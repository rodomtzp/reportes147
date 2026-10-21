from typing import List, Optional

from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.domain.entities.usuario import Usuario
from app.domain.value_objects.rol import Rol


class ListarUsuarios:
    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(self, rol: Optional[Rol] = None, activo: Optional[bool] = None) -> List[Usuario]:
        with self._uow as uow:
            return uow.usuarios.listar(rol=rol, activo=activo)
