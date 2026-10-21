from typing import List, Optional

from app.application.dto.academico import AsignacionDetalle
from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.domain.entities.asignacion_tutor import AsignacionTutor
from app.domain.exceptions import Conflicto, NoEncontrado, ReglaDeNegocioViolada
from app.domain.value_objects.rol import Rol


def _detalle(uow, a: AsignacionTutor) -> AsignacionDetalle:
    usuario = uow.usuarios.obtener_por_id(a.usuario_id)
    grupo = uow.grupos.obtener_por_id(a.grupo_id)
    carrera = uow.carreras.obtener_por_id(grupo.carrera_id) if grupo else None
    periodo = uow.periodos.obtener_por_id(a.periodo_id)
    return AsignacionDetalle(
        asignacion=a,
        usuario_nombre=usuario.nombre if usuario else "?",
        grupo_clave=grupo.clave if grupo else "?",
        carrera_nombre=carrera.nombre if carrera else "?",
        periodo_nombre=periodo.nombre if periodo else "?",
    )


class AsignarTutor:
    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(self, usuario_id: int, grupo_id: int, periodo_id: int) -> AsignacionDetalle:
        with self._uow as uow:
            usuario = uow.usuarios.obtener_por_id(usuario_id)
            if usuario is None:
                raise NoEncontrado("Usuario no encontrado.")
            if not usuario.activo or not usuario.tiene_rol(Rol.DOCENTE):
                raise ReglaDeNegocioViolada("Solo un docente activo puede ser tutor.")
            grupo = uow.grupos.obtener_por_id(grupo_id)
            if grupo is None:
                raise NoEncontrado("Grupo no encontrado.")
            if not grupo.activo:
                raise ReglaDeNegocioViolada("El grupo está desactivado.")
            if uow.periodos.obtener_por_id(periodo_id) is None:
                raise NoEncontrado("Periodo no encontrado.")
            if uow.asignaciones_tutor.obtener_por_grupo_y_periodo(grupo_id, periodo_id):
                raise Conflicto("Ese grupo ya tiene tutor en el periodo indicado.")
            asignacion = uow.asignaciones_tutor.guardar(
                AsignacionTutor(usuario_id=usuario_id, grupo_id=grupo_id, periodo_id=periodo_id)
            )
            uow.commit()
            return _detalle(uow, asignacion)


class RetirarAsignacionTutor:
    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(self, asignacion_id: int) -> None:
        with self._uow as uow:
            if uow.asignaciones_tutor.obtener_por_id(asignacion_id) is None:
                raise NoEncontrado("Asignación no encontrada.")
            uow.asignaciones_tutor.eliminar(asignacion_id)
            uow.commit()


class ListarAsignacionesTutor:
    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(
        self,
        periodo_id: Optional[int] = None,
        grupo_id: Optional[int] = None,
        usuario_id: Optional[int] = None,
    ) -> List[AsignacionDetalle]:
        with self._uow as uow:
            asignaciones = uow.asignaciones_tutor.listar(
                periodo_id=periodo_id, grupo_id=grupo_id, usuario_id=usuario_id
            )
            return [_detalle(uow, a) for a in asignaciones]
