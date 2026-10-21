from typing import List, Optional

from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.domain.entities.carrera import Carrera
from app.domain.exceptions import Conflicto, NoEncontrado, ReglaDeNegocioViolada


class CrearCarrera:
    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(self, nombre: str, clave: str) -> Carrera:
        carrera = Carrera(nombre=nombre, clave=clave)
        with self._uow as uow:
            if uow.carreras.obtener_por_clave(carrera.clave):
                raise Conflicto("Ya existe una carrera con esa clave.")
            uow.carreras.guardar(carrera)
            uow.commit()
            return carrera


class ActualizarCarrera:
    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(
        self,
        carrera_id: int,
        nombre: Optional[str] = None,
        clave: Optional[str] = None,
        activa: Optional[bool] = None,
    ) -> Carrera:
        with self._uow as uow:
            carrera = uow.carreras.obtener_por_id(carrera_id)
            if carrera is None:
                raise NoEncontrado("Carrera no encontrada.")
            if nombre is not None:
                carrera.nombre = nombre
            if clave is not None:
                carrera.clave = clave
            carrera.validar()
            otra = uow.carreras.obtener_por_clave(carrera.clave)
            if otra and otra.id != carrera.id:
                raise Conflicto("Ya existe una carrera con esa clave.")
            if activa is False and carrera.activa:
                if uow.grupos.listar(carrera_id=carrera.id, solo_activos=True):
                    raise ReglaDeNegocioViolada(
                        "La carrera tiene grupos activos. Desactívalos antes de desactivar la carrera."
                    )
            if activa is not None:
                carrera.activa = activa
            uow.carreras.guardar(carrera)
            uow.commit()
            return carrera


class ListarCarreras:
    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(self, solo_activas: bool = False) -> List[Carrera]:
        with self._uow as uow:
            return uow.carreras.listar(solo_activas=solo_activas)
