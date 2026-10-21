from app.application.dto.estudiantes import FilaConProblema, ResultadoImportacion
from app.application.ports.lector_estudiantes import LectorEstudiantesPuerto
from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.application.use_cases.estudiantes._comun import periodo_vigente_o_error
from app.domain.entities.estudiante import Estudiante
from app.domain.entities.inscripcion import Inscripcion
from app.domain.entities.tutor_legal import TutorLegal
from app.domain.exceptions import ReglaDeNegocioViolada


class ImportarEstudiantes:
    """Crea los estudiantes nuevos; los que ya existen (o se repiten en el archivo) se omiten y
    se reportan. Las filas con datos inválidos se reportan como errores y no frenan al resto.
    Los estudiantes se inscriben en su grupo (columna `grupo`, ej. 1G) del periodo vigente."""

    def __init__(self, uow: UnidadDeTrabajo, lector: LectorEstudiantesPuerto):
        self._uow = uow
        self._lector = lector

    def ejecutar(self, contenido: bytes, nombre_archivo: str) -> ResultadoImportacion:
        filas = self._lector.leer(contenido, nombre_archivo)
        creados, omitidos, errores, vistos = 0, [], [], set()

        with self._uow as uow:
            periodo = periodo_vigente_o_error(uow)
            grupos = {g.clave: g for g in uow.grupos.listar()}

            for numero_fila, fila in enumerate(filas, start=2):  # la fila 1 es el encabezado
                control = (fila.get("numero_control") or "").strip().upper()
                try:
                    if control and control in vistos:
                        omitidos.append(FilaConProblema(numero_fila, control, "Repetido en el archivo."))
                        continue
                    grupo = grupos.get((fila.get("grupo") or "").strip().upper())
                    if grupo is None or not grupo.activo:
                        raise ReglaDeNegocioViolada(f"El grupo '{fila.get('grupo', '')}' no existe o está desactivado.")
                    estudiante = Estudiante(**{
                        k: fila.get(k) for k in (
                            "numero_control", "primer_apellido", "segundo_apellido", "nombres", "telefono",
                            "correo", "calle", "numero", "colonia", "ciudad", "generacion",
                        )
                    })
                    tutor = TutorLegal(
                        nombre=fila.get("tutor_nombre"), telefono=fila.get("tutor_telefono"),
                        parentesco=fila.get("tutor_parentesco"), correo=fila.get("tutor_correo"),
                        es_principal=True,
                    )
                    if uow.estudiantes.obtener_por_numero_control(estudiante.numero_control):
                        omitidos.append(FilaConProblema(numero_fila, control, "Ya existe en el sistema."))
                        vistos.add(estudiante.numero_control)
                        continue
                except ReglaDeNegocioViolada as e:
                    errores.append(FilaConProblema(numero_fila, control, str(e)))
                    continue

                uow.estudiantes.guardar(estudiante)
                tutor.estudiante_id = estudiante.id
                uow.tutores_legales.guardar(tutor)
                uow.inscripciones.guardar(
                    Inscripcion(estudiante_id=estudiante.id, grupo_id=grupo.id, periodo_id=periodo.id)
                )
                vistos.add(estudiante.numero_control)
                creados += 1

            uow.commit()
        return ResultadoImportacion(creados=creados, omitidos=omitidos, errores=errores)
