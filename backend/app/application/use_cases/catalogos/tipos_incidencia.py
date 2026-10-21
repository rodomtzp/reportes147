from typing import List, Optional

from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.domain.entities.tipo_incidencia import TipoIncidencia
from app.domain.exceptions import Conflicto, NoEncontrado, ReglaDeNegocioViolada


class CrearTipoIncidencia:
    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(self, nombre: str) -> TipoIncidencia:
        tipo = TipoIncidencia(nombre=nombre)
        with self._uow as uow:
            if uow.tipos_incidencia.obtener_por_nombre(tipo.nombre):
                raise Conflicto("Ya existe una incidencia con ese nombre.")
            uow.tipos_incidencia.guardar(tipo)
            uow.commit()
            return tipo


class ActualizarTipoIncidencia:
    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(
        self, tipo_id: int, nombre: Optional[str] = None, activo: Optional[bool] = None
    ) -> TipoIncidencia:
        with self._uow as uow:
            tipo = uow.tipos_incidencia.obtener_por_id(tipo_id)
            if tipo is None:
                raise NoEncontrado("Tipo de incidencia no encontrado.")
            if tipo.es_otro and (activo is False or (nombre is not None and nombre.strip() != tipo.nombre)):
                raise ReglaDeNegocioViolada("La opción 'Otro' no se puede renombrar ni desactivar.")
            if nombre is not None:
                tipo.nombre = nombre
            tipo.validar()
            otro = uow.tipos_incidencia.obtener_por_nombre(tipo.nombre)
            if otro and otro.id != tipo.id:
                raise Conflicto("Ya existe una incidencia con ese nombre.")
            if activo is not None:
                tipo.activo = activo
            uow.tipos_incidencia.guardar(tipo)
            uow.commit()
            return tipo


class ListarTiposIncidencia:
    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(self, solo_activos: bool = False) -> List[TipoIncidencia]:
        with self._uow as uow:
            tipos = uow.tipos_incidencia.listar(solo_activos=solo_activos)
        return sorted(tipos, key=lambda t: (t.es_otro, t.id or 0))  # "Otro" siempre al final
