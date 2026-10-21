from typing import List, Optional

from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.domain.entities.grupo import Grupo
from app.domain.exceptions import Conflicto, NoEncontrado, ReglaDeNegocioViolada


def _validar_carrera_activa(uow, carrera_id: int) -> None:
    carrera = uow.carreras.obtener_por_id(carrera_id)
    if carrera is None:
        raise NoEncontrado("Carrera no encontrada.")
    if not carrera.activa:
        raise ReglaDeNegocioViolada("La carrera está desactivada.")


class CrearGrupo:
    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(self, carrera_id: int, semestre: int, letra: str) -> Grupo:
        grupo = Grupo(carrera_id=carrera_id, semestre=semestre, letra=letra)
        with self._uow as uow:
            _validar_carrera_activa(uow, carrera_id)
            if uow.grupos.obtener_por_semestre_y_letra(grupo.semestre, grupo.letra):
                raise Conflicto(f"Ya existe el grupo {grupo.clave}.")
            uow.grupos.guardar(grupo)
            uow.commit()
            return grupo


class ActualizarGrupo:
    """Nota: en la Fase 2, cuando el grupo tenga inscripciones, cambiar semestre,
    letra o carrera deberá restringirse para no alterar el historial."""

    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(
        self,
        grupo_id: int,
        carrera_id: Optional[int] = None,
        semestre: Optional[int] = None,
        letra: Optional[str] = None,
        activo: Optional[bool] = None,
    ) -> Grupo:
        with self._uow as uow:
            grupo = uow.grupos.obtener_por_id(grupo_id)
            if grupo is None:
                raise NoEncontrado("Grupo no encontrado.")
            if carrera_id is not None and carrera_id != grupo.carrera_id:
                _validar_carrera_activa(uow, carrera_id)
                grupo.carrera_id = carrera_id
            if semestre is not None:
                grupo.semestre = semestre
            if letra is not None:
                grupo.letra = letra
            grupo.validar()
            otro = uow.grupos.obtener_por_semestre_y_letra(grupo.semestre, grupo.letra)
            if otro and otro.id != grupo.id:
                raise Conflicto(f"Ya existe el grupo {grupo.clave}.")
            if activo is not None:
                grupo.activo = activo
            uow.grupos.guardar(grupo)
            uow.commit()
            return grupo


class ListarGrupos:
    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(
        self,
        carrera_id: Optional[int] = None,
        semestre: Optional[int] = None,
        solo_activos: bool = False,
    ) -> List[Grupo]:
        with self._uow as uow:
            return uow.grupos.listar(carrera_id=carrera_id, semestre=semestre, solo_activos=solo_activos)
