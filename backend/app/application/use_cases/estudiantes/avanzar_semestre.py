from typing import Dict, List

from app.application.dto.estudiantes import MovimientoAvance, ResumenAvance
from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.domain.entities.inscripcion import Inscripcion
from app.domain.exceptions import NoEncontrado, ReglaDeNegocioViolada
from app.domain.policies.politica_avance_semestre import decidir_destino
from app.domain.value_objects.estatus_estudiante import AccionAvance, EstatusEstudiante


class AvanzarSemestre:
    """Proceso masivo de cierre de periodo.

    Cada estudiante activo inscrito en el periodo de origen pasa, en el de destino, al grupo del
    siguiente semestre conservando la letra (1G → 2G). Excepciones: REPETIR (mismo grupo) y BAJA.
    Los de sexto semestre egresan. Es idempotente (quien ya tiene inscripción en el destino se
    omite) y `simular=True` solo calcula el resumen sin guardar nada.
    """

    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(
        self,
        periodo_origen_id: int,
        periodo_destino_id: int,
        excepciones: Dict[int, AccionAvance],
        simular: bool = True,
    ) -> ResumenAvance:
        with self._uow as uow:
            origen = uow.periodos.obtener_por_id(periodo_origen_id)
            destino = uow.periodos.obtener_por_id(periodo_destino_id)
            if origen is None or destino is None:
                raise NoEncontrado("Periodo no encontrado.")
            if destino.id == origen.id or destino.fecha_inicio <= origen.fecha_inicio:
                raise ReglaDeNegocioViolada("El periodo de destino debe ser posterior al de origen.")

            inscripciones = uow.inscripciones.listar_por_periodo(origen.id)
            en_origen = {i.estudiante_id for i in inscripciones}
            ajenos = [eid for eid in excepciones if eid not in en_origen]
            if ajenos:
                raise ReglaDeNegocioViolada(
                    "Hay excepciones de estudiantes que no están inscritos en el periodo de origen."
                )
            ya_en_destino = {i.estudiante_id for i in uow.inscripciones.listar_por_periodo(destino.id)}
            estudiantes = uow.estudiantes.obtener_por_ids(en_origen)
            grupos_por_id = {g.id: g for g in uow.grupos.listar()}
            grupos_por_clave = {g.clave: g for g in grupos_por_id.values()}

            movimientos: List[MovimientoAvance] = []
            faltantes, ya_inscritos = set(), 0
            for insc in inscripciones:
                est = estudiantes.get(insc.estudiante_id)
                if est is None or est.estatus != EstatusEstudiante.ACTIVO:
                    continue
                if est.id in ya_en_destino:
                    ya_inscritos += 1
                    continue
                grupo = grupos_por_id[insc.grupo_id]
                d = decidir_destino(grupo, excepciones.get(est.id))
                grupo_destino_id = None
                if d.clave_grupo:
                    gd = grupos_por_clave.get(d.clave_grupo)
                    if gd is None or not gd.activo:
                        faltantes.add(d.clave_grupo)
                    else:
                        grupo_destino_id = gd.id
                movimientos.append(MovimientoAvance(
                    estudiante_id=est.id, numero_control=est.numero_control, nombre=est.nombre_completo,
                    grupo_origen=grupo.clave, grupo_destino=d.clave_grupo, accion=d.accion,
                    grupo_destino_id=grupo_destino_id,
                    nuevo_estatus=d.nuevo_estatus.value if d.nuevo_estatus else None,
                ))

            resumen = ResumenAvance(movimientos, sorted(faltantes), ya_inscritos, ejecutado=not simular)
            if simular:
                return resumen
            if faltantes:
                raise ReglaDeNegocioViolada(
                    "Faltan grupos activos para el siguiente semestre: " + ", ".join(sorted(faltantes)) + "."
                )
            for m in movimientos:
                if m.grupo_destino_id:
                    uow.inscripciones.guardar(
                        Inscripcion(estudiante_id=m.estudiante_id, grupo_id=m.grupo_destino_id, periodo_id=destino.id)
                    )
                if m.nuevo_estatus:
                    est = estudiantes[m.estudiante_id]
                    est.estatus = EstatusEstudiante(m.nuevo_estatus)
                    uow.estudiantes.guardar(est)
            uow.commit()
            return resumen
