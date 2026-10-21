from typing import Optional

from app.application.dto.reportes import ACCESO_TOTAL, FiltroReportes
from app.application.dto.sanciones import SancionDetalle
from app.application.ports.reloj import RelojPuerto
from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.application.use_cases.reportes._comun import cargar_reporte, registrar
from app.application.use_cases.sanciones._comun import concluir, exigir_llamada_efectiva
from app.application.use_cases.sanciones.vistas import detalle_sancion
from app.domain.entities.sancion import Sancion
from app.domain.exceptions import NoEncontrado, ReglaDeNegocioViolada
from app.domain.policies.politica_acumulacion import UMBRAL_ACUMULACION, alcanza_umbral
from app.domain.policies.politica_sanciones import validar_tipo_y_dias
from app.domain.value_objects.estado_reporte import TipoEventoReporte
from app.domain.value_objects.origen_sancion import OrigenSancion


def _texto_sancion(tipo, dias) -> str:
    return f"{tipo.nombre} ({dias} días)" if dias else tipo.nombre


class AplicarSancionDirecta:
    """Subdirección o Dirección sancionan por la magnitud de un reporte Grave o Muy grave.

    El reporte pasa a 'Sancionado / Concluido' y deja de contar para las 3 faltas del ciclo;
    el ciclo NO se cierra ni se reinicia."""

    def __init__(self, uow: UnidadDeTrabajo, reloj: RelojPuerto):
        self._uow, self._reloj = uow, reloj

    def ejecutar(self, actor_id: int, reporte_id: int, tipo_sancion_id: int,
                 dias: Optional[int] = None, observaciones: Optional[str] = None) -> SancionDetalle:
        ahora = self._reloj.ahora()
        with self._uow as uow:
            reporte = cargar_reporte(uow, reporte_id)
            reporte.asegurar_sancion_directa()
            tipo = uow.tipos_sancion.obtener_por_id(tipo_sancion_id)
            if tipo is None:
                raise NoEncontrado("Tipo de sanción no encontrado.")
            dias = validar_tipo_y_dias(tipo, dias)
            exigir_llamada_efectiva(uow, [reporte])

            sancion = uow.sanciones.guardar(Sancion(
                tipo_sancion_id=tipo.id, origen=OrigenSancion.DIRECTA, estudiante_id=reporte.estudiante_id,
                aplicada_por=actor_id, aplicada_en=ahora, reporte_id=reporte.id, dias=dias, observaciones=observaciones))
            reporte.cuenta_acumulacion = False
            registrar(uow, reporte.id, TipoEventoReporte.SANCION, actor_id, ahora, campo="sanción directa",
                      valor_nuevo=_texto_sancion(tipo, dias), comentario=sancion.observaciones)
            concluir(uow, reporte, actor_id, ahora, "Sanción directa por la magnitud del reporte.")
            uow.reportes.guardar(reporte)
            uow.commit()
            return detalle_sancion(uow, sancion)


class AplicarSancionPorAcumulacion:
    """Con 3 o más reportes contables en el ciclo, Subdirección o Dirección aplican una sola sanción
    que cubre todos los reportes del ciclo, los concluye y reinicia el contador del estudiante."""

    def __init__(self, uow: UnidadDeTrabajo, reloj: RelojPuerto):
        self._uow, self._reloj = uow, reloj

    def ejecutar(self, actor_id: int, estudiante_id: int, tipo_sancion_id: int,
                 dias: Optional[int] = None, observaciones: Optional[str] = None) -> SancionDetalle:
        ahora = self._reloj.ahora()
        with self._uow as uow:
            if uow.estudiantes.obtener_por_id(estudiante_id) is None:
                raise NoEncontrado("Estudiante no encontrado.")
            ciclo = uow.ciclos.obtener_abierto(estudiante_id)
            cubiertos = (
                uow.reportes.listar(FiltroReportes(acceso=ACCESO_TOTAL, ciclo_id=ciclo.id, solo_contables=True, limite=1000))
                if ciclo else []
            )
            if not alcanza_umbral(len(cubiertos)):
                raise ReglaDeNegocioViolada(
                    f"El estudiante lleva {len(cubiertos)} de {UMBRAL_ACUMULACION} reportes: "
                    "aún no procede una sanción por acumulación."
                )
            tipo = uow.tipos_sancion.obtener_por_id(tipo_sancion_id)
            if tipo is None:
                raise NoEncontrado("Tipo de sanción no encontrado.")
            dias = validar_tipo_y_dias(tipo, dias)
            exigir_llamada_efectiva(uow, cubiertos)

            sancion = uow.sanciones.guardar(Sancion(
                tipo_sancion_id=tipo.id, origen=OrigenSancion.ACUMULACION, estudiante_id=estudiante_id,
                aplicada_por=actor_id, aplicada_en=ahora, ciclo_id=ciclo.id, dias=dias, observaciones=observaciones))
            for reporte in cubiertos:
                registrar(uow, reporte.id, TipoEventoReporte.SANCION, actor_id, ahora, campo="sanción por acumulación",
                          valor_nuevo=_texto_sancion(tipo, dias),
                          comentario=f"Cubre {len(cubiertos)} reportes del ciclo {ciclo.numero}.")
                concluir(uow, reporte, actor_id, ahora, "Sanción por acumulación de reportes.")
                uow.reportes.guardar(reporte)
            ciclo.cerrar(ahora)
            uow.ciclos.guardar(ciclo)  # el siguiente reporte abrirá un ciclo nuevo
            uow.commit()
            return detalle_sancion(uow, sancion)
