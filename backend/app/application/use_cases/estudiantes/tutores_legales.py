from typing import List

from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.application.use_cases.estudiantes._comun import asegurar_un_principal
from app.domain.entities.tutor_legal import TutorLegal
from app.domain.exceptions import NoEncontrado, ReglaDeNegocioViolada


def _guardar_todos(uow, tutores: List[TutorLegal]) -> None:
    for t in tutores:
        uow.tutores_legales.guardar(t)


class AgregarTutorLegal:
    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(self, estudiante_id: int, **datos) -> List[TutorLegal]:
        nuevo = TutorLegal(estudiante_id=estudiante_id, **datos)
        with self._uow as uow:
            if uow.estudiantes.obtener_por_id(estudiante_id) is None:
                raise NoEncontrado("Estudiante no encontrado.")
            tutores = uow.tutores_legales.listar_por_estudiante(estudiante_id)
            tutores.append(nuevo)
            asegurar_un_principal(tutores, preferido=nuevo)
            uow.tutores_legales.guardar(nuevo)
            _guardar_todos(uow, [t for t in tutores if t is not nuevo])
            uow.commit()
            return uow.tutores_legales.listar_por_estudiante(estudiante_id)


class ActualizarTutorLegal:
    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(self, tutor_id: int, **cambios) -> List[TutorLegal]:
        with self._uow as uow:
            tutor = uow.tutores_legales.obtener_por_id(tutor_id)
            if tutor is None:
                raise NoEncontrado("Padre o tutor no encontrado.")
            for campo, valor in cambios.items():
                setattr(tutor, campo, valor)
            tutor.validar()
            tutores = [t for t in uow.tutores_legales.listar_por_estudiante(tutor.estudiante_id) if t.id != tutor.id]
            tutores.append(tutor)
            if cambios.get("es_principal") is False and not any(t.es_principal for t in tutores):
                tutor.es_principal = True  # siempre debe haber un principal
            asegurar_un_principal(tutores, preferido=tutor)
            _guardar_todos(uow, tutores)
            uow.commit()
            return uow.tutores_legales.listar_por_estudiante(tutor.estudiante_id)


class EliminarTutorLegal:
    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(self, tutor_id: int) -> List[TutorLegal]:
        with self._uow as uow:
            tutor = uow.tutores_legales.obtener_por_id(tutor_id)
            if tutor is None:
                raise NoEncontrado("Padre o tutor no encontrado.")
            restantes = [t for t in uow.tutores_legales.listar_por_estudiante(tutor.estudiante_id) if t.id != tutor.id]
            if not restantes:
                raise ReglaDeNegocioViolada("El estudiante debe conservar al menos un padre o tutor.")
            if uow.llamadas.tutor_tiene_resultados(tutor_id) or uow.mensajes_whatsapp.tutor_tiene_mensajes(tutor_id):
                raise ReglaDeNegocioViolada(
                    "Este padre o tutor tiene llamadas o mensajes registrados en reportes y no puede eliminarse."
                )
            asegurar_un_principal(restantes)
            _guardar_todos(uow, restantes)
            principal = next(t for t in restantes if t.es_principal)
            uow.llamadas.reasignar_pendientes(tutor_id, principal.id)  # las llamadas pendientes pasan al principal
            uow.tutores_legales.eliminar(tutor_id)
            uow.commit()
            return uow.tutores_legales.listar_por_estudiante(tutor.estudiante_id)
