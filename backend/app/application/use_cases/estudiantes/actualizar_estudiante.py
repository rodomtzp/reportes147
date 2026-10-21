from app.application.dto.estudiantes import EstudianteDetalle
from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.application.use_cases.estudiantes._comun import (
    armar_detalle, grupo_activo_o_error, periodo_vigente_o_error,
)
from app.domain.entities.inscripcion import Inscripcion
from app.domain.exceptions import NoEncontrado, ReglaDeNegocioViolada
from app.domain.value_objects.estatus_estudiante import EstatusEstudiante

CAMPOS_EDITABLES = {
    "primer_apellido", "segundo_apellido", "nombres", "telefono", "correo",
    "calle", "numero", "colonia", "ciudad", "generacion", "estatus",
}


class ActualizarEstudiante:
    """El número de control no se modifica: es la identidad del estudiante."""

    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(self, estudiante_id: int, **cambios) -> EstudianteDetalle:
        with self._uow as uow:
            estudiante = uow.estudiantes.obtener_por_id(estudiante_id)
            if estudiante is None:
                raise NoEncontrado("Estudiante no encontrado.")
            for campo, valor in cambios.items():
                if campo not in CAMPOS_EDITABLES:
                    raise ReglaDeNegocioViolada(f"El campo '{campo}' no se puede modificar.")
                setattr(estudiante, campo, valor)
            estudiante.validar()
            uow.estudiantes.guardar(estudiante)
            uow.commit()
            return armar_detalle(uow, estudiante)


class CambiarGrupoEstudiante:
    """Corrige el grupo del periodo vigente (p. ej. un estudiante capturado en el grupo equivocado)."""

    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(self, estudiante_id: int, grupo_id: int) -> EstudianteDetalle:
        with self._uow as uow:
            estudiante = uow.estudiantes.obtener_por_id(estudiante_id)
            if estudiante is None:
                raise NoEncontrado("Estudiante no encontrado.")
            if estudiante.estatus != EstatusEstudiante.ACTIVO:
                raise ReglaDeNegocioViolada("Solo se puede asignar grupo a estudiantes activos.")
            periodo = periodo_vigente_o_error(uow)
            grupo_activo_o_error(uow, grupo_id)
            insc = uow.inscripciones.obtener(estudiante_id, periodo.id)
            if insc is None:
                insc = Inscripcion(estudiante_id=estudiante_id, grupo_id=grupo_id, periodo_id=periodo.id)
            insc.grupo_id = grupo_id
            uow.inscripciones.guardar(insc)
            uow.commit()
            return armar_detalle(uow, estudiante)
