from datetime import date
from typing import List, Optional

from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.domain.entities.periodo_escolar import PeriodoEscolar
from app.domain.exceptions import Conflicto, NoEncontrado


class CrearPeriodo:
    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(self, nombre: str, fecha_inicio: date, fecha_fin: date) -> PeriodoEscolar:
        periodo = PeriodoEscolar(nombre=nombre, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)
        with self._uow as uow:
            if uow.periodos.obtener_por_nombre(periodo.nombre):
                raise Conflicto("Ya existe un periodo con ese nombre.")
            uow.periodos.guardar(periodo)
            uow.commit()
            return periodo


class ActualizarPeriodo:
    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(
        self,
        periodo_id: int,
        nombre: Optional[str] = None,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
    ) -> PeriodoEscolar:
        with self._uow as uow:
            periodo = uow.periodos.obtener_por_id(periodo_id)
            if periodo is None:
                raise NoEncontrado("Periodo no encontrado.")
            if nombre is not None:
                periodo.nombre = nombre
            if fecha_inicio is not None:
                periodo.fecha_inicio = fecha_inicio
            if fecha_fin is not None:
                periodo.fecha_fin = fecha_fin
            periodo.validar()
            otro = uow.periodos.obtener_por_nombre(periodo.nombre)
            if otro and otro.id != periodo.id:
                raise Conflicto("Ya existe un periodo con ese nombre.")
            uow.periodos.guardar(periodo)
            uow.commit()
            return periodo


class EstablecerPeriodoVigente:
    """Solo un periodo puede estar vigente a la vez."""

    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(self, periodo_id: int) -> PeriodoEscolar:
        with self._uow as uow:
            periodo = uow.periodos.obtener_por_id(periodo_id)
            if periodo is None:
                raise NoEncontrado("Periodo no encontrado.")
            uow.periodos.desactivar_vigentes()
            periodo.vigente = True
            uow.periodos.guardar(periodo)
            uow.commit()
            return periodo


class ListarPeriodos:
    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(self) -> List[PeriodoEscolar]:
        with self._uow as uow:
            return uow.periodos.listar()
