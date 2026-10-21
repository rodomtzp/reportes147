from typing import List, Optional

from app.application.dto.estudiantes import EstudianteDetalle, EstudianteListado, EstudianteResumen
from app.application.ports.reloj import RelojPuerto
from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.application.use_cases.bitacora.registro import registrar_consulta_contacto
from app.application.use_cases.estudiantes._comun import armar_detalle, grupo_y_carrera, mapas_academicos
from app.application.use_cases.estudiantes.acceso import grupos_tutelados, tiene_acceso_total
from app.domain.entities.usuario import Usuario
from app.domain.exceptions import NoEncontrado, PermisoDenegado, ReglaDeNegocioViolada
from app.domain.value_objects.estatus_estudiante import EstatusEstudiante

LIMITE_MAXIMO = 500


def _con_grupo_actual(uow, estudiantes, periodo):
    grupos, carreras = mapas_academicos(uow)
    insc = uow.inscripciones.obtener_de_estudiantes([e.id for e in estudiantes], periodo.id) if periodo else {}
    salida = []
    for e in estudiantes:
        clave, carrera = grupo_y_carrera(grupos, carreras, insc[e.id].grupo_id if e.id in insc else None)
        salida.append((e, clave, carrera))
    return salida


class ListarEstudiantes:
    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(
        self,
        actor: Usuario,
        texto: Optional[str] = None,
        estatus: Optional[EstatusEstudiante] = None,
        grupo_id: Optional[int] = None,
        carrera_id: Optional[int] = None,
        limite: int = 200,
        offset: int = 0,
    ) -> List[EstudianteListado]:
        limite = max(1, min(limite, LIMITE_MAXIMO))
        with self._uow as uow:
            periodo = uow.periodos.obtener_vigente()
            grupo_ids = [grupo_id] if grupo_id else None
            if not tiene_acceso_total(actor):
                tutelados = grupos_tutelados(uow, actor)
                if not tutelados:
                    raise PermisoDenegado("No tienes acceso a la lista de estudiantes.")
                if grupo_id and grupo_id not in tutelados:
                    raise PermisoDenegado("No eres tutor de ese grupo.")
                grupo_ids = [grupo_id] if grupo_id else sorted(tutelados)
            if (grupo_ids is not None or carrera_id is not None) and periodo is None:
                return []
            estudiantes = uow.estudiantes.listar(
                texto=texto, estatus=estatus, grupo_ids=grupo_ids, carrera_id=carrera_id,
                periodo_id=periodo.id if periodo else None, limite=limite, offset=offset,
            )
            return [EstudianteListado(e, c, car) for e, c, car in _con_grupo_actual(uow, estudiantes, periodo)]


class ObtenerEstudiante:
    """Ficha completa (con teléfonos y domicilio): cada consulta queda en la bitácora."""

    def __init__(self, uow: UnidadDeTrabajo, reloj: RelojPuerto):
        self._uow, self._reloj = uow, reloj

    def ejecutar(self, actor: Usuario, estudiante_id: int) -> EstudianteDetalle:
        with self._uow as uow:
            estudiante = uow.estudiantes.obtener_por_id(estudiante_id)
            if estudiante is None:
                raise NoEncontrado("Estudiante no encontrado.")
            if not tiene_acceso_total(actor):
                periodo = uow.periodos.obtener_vigente()
                insc = uow.inscripciones.obtener(estudiante_id, periodo.id) if periodo else None
                if insc is None or insc.grupo_id not in grupos_tutelados(uow, actor):
                    raise PermisoDenegado("No tienes acceso a este estudiante.")
            detalle = armar_detalle(uow, estudiante)
            registrar_consulta_contacto(uow, self._reloj, actor.id, estudiante.id, f"Ficha de {estudiante.nombre_completo}")
            uow.commit()
            return detalle


class BuscarEstudiantes:
    """Buscador para crear reportes: devuelve solo datos mínimos de estudiantes activos."""

    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(self, texto: str, limite: int = 15) -> List[EstudianteResumen]:
        texto = (texto or "").strip()
        if len(texto) < 2:
            raise ReglaDeNegocioViolada("Escribe al menos 2 caracteres para buscar.")
        with self._uow as uow:
            periodo = uow.periodos.obtener_vigente()
            encontrados = uow.estudiantes.buscar_activos(texto, limite=max(1, min(limite, 50)))
            return [
                EstudianteResumen(e.id, e.numero_control, e.nombre_completo, c, car)
                for e, c, car in _con_grupo_actual(uow, encontrados, periodo)
            ]


class GruposTutelados:
    """Grupos de los que el usuario es tutor en el periodo vigente (para el menú y los permisos)."""

    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(self, actor: Usuario) -> List[str]:
        with self._uow as uow:
            ids = grupos_tutelados(uow, actor)
            return sorted(g.clave for g in uow.grupos.listar() if g.id in ids)
