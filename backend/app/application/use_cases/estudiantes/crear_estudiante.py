from typing import List

from app.application.dto.estudiantes import EstudianteDetalle
from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.application.use_cases.estudiantes._comun import (
    armar_detalle, asegurar_un_principal, grupo_activo_o_error, periodo_vigente_o_error,
)
from app.domain.entities.estudiante import Estudiante
from app.domain.entities.inscripcion import Inscripcion
from app.domain.entities.tutor_legal import TutorLegal
from app.domain.exceptions import Conflicto, ReglaDeNegocioViolada


class CrearEstudiante:
    """Alta manual: el estudiante, al menos un padre o tutor con teléfono, y su grupo actual."""

    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(self, grupo_id: int, tutores: List[dict], **datos) -> EstudianteDetalle:
        estudiante = Estudiante(**datos)  # valida y normaliza
        if not tutores:
            raise ReglaDeNegocioViolada("Registra al menos un padre o tutor legal con teléfono.")
        tutores_legales = [TutorLegal(**t) for t in tutores]
        asegurar_un_principal(tutores_legales)

        with self._uow as uow:
            periodo = periodo_vigente_o_error(uow)
            grupo_activo_o_error(uow, grupo_id)
            if uow.estudiantes.obtener_por_numero_control(estudiante.numero_control):
                raise Conflicto("Ya existe un estudiante con ese número de control.")
            uow.estudiantes.guardar(estudiante)
            for t in tutores_legales:
                t.estudiante_id = estudiante.id
                uow.tutores_legales.guardar(t)
            uow.inscripciones.guardar(
                Inscripcion(estudiante_id=estudiante.id, grupo_id=grupo_id, periodo_id=periodo.id)
            )
            uow.commit()
            return armar_detalle(uow, estudiante)
