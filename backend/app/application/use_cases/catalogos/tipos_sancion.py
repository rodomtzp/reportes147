from typing import List, Optional

from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.domain.entities.tipo_sancion import TipoSancion
from app.domain.exceptions import Conflicto, NoEncontrado


class CrearTipoSancion:
    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(self, nombre: str, requiere_dias: bool = False) -> TipoSancion:
        tipo = TipoSancion(nombre=nombre, requiere_dias=requiere_dias)
        with self._uow as uow:
            if uow.tipos_sancion.obtener_por_nombre(tipo.nombre):
                raise Conflicto("Ya existe una sanción con ese nombre.")
            uow.tipos_sancion.guardar(tipo)
            uow.commit()
            return tipo


class ActualizarTipoSancion:
    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(
        self,
        tipo_id: int,
        nombre: Optional[str] = None,
        requiere_dias: Optional[bool] = None,
        activo: Optional[bool] = None,
    ) -> TipoSancion:
        with self._uow as uow:
            tipo = uow.tipos_sancion.obtener_por_id(tipo_id)
            if tipo is None:
                raise NoEncontrado("Tipo de sanción no encontrado.")
            if nombre is not None:
                tipo.nombre = nombre
            tipo.validar()
            otro = uow.tipos_sancion.obtener_por_nombre(tipo.nombre)
            if otro and otro.id != tipo.id:
                raise Conflicto("Ya existe una sanción con ese nombre.")
            if requiere_dias is not None:
                tipo.requiere_dias = requiere_dias
            if activo is not None:
                tipo.activo = activo
            uow.tipos_sancion.guardar(tipo)
            uow.commit()
            return tipo


class ListarTiposSancion:
    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(self, solo_activos: bool = False) -> List[TipoSancion]:
        with self._uow as uow:
            return uow.tipos_sancion.listar(solo_activos=solo_activos)
