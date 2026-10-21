import logging
from datetime import timedelta
from typing import Optional

from app.application.ports.notificador import NotificadorPuerto
from app.application.ports.reloj import RelojPuerto
from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.application.use_cases.reportes._comun import alertas_de, cargar_reporte, registrar
from app.domain.exceptions import NoEncontrado, ReglaDeNegocioViolada
from app.domain.policies.politica_escalamiento import debe_alertar_subdireccion
from app.domain.value_objects.estado_reporte import EstadoReporte, TipoEventoReporte
from app.domain.value_objects.gravedad import Gravedad

log = logging.getLogger(__name__)
CAMPOS_CORREGIBLES = {"tipo_incidencia_id", "descripcion_otro", "descripcion", "fecha_hora_incidente"}
MOTIVO_GRAVEDAD_MIN = 5


class CorregirReporte:
    """Orientación, Subdirección y Dirección corrigen datos del reporte; cada campo queda en el historial."""

    def __init__(self, uow: UnidadDeTrabajo, reloj: RelojPuerto):
        self._uow = uow
        self._reloj = reloj

    def ejecutar(self, actor_id: int, reporte_id: int, comentario: Optional[str] = None, **cambios):
        desconocidos = set(cambios) - CAMPOS_CORREGIBLES
        if desconocidos or not cambios:
            raise ReglaDeNegocioViolada("Indica al menos un campo corregible: " + ", ".join(sorted(CAMPOS_CORREGIBLES)) + ".")
        ahora = self._reloj.ahora()
        with self._uow as uow:
            r = cargar_reporte(uow, reporte_id)
            r.asegurar_modificable()
            antes = {c: getattr(r, c) for c in CAMPOS_CORREGIBLES}

            tipo = uow.tipos_incidencia.obtener_por_id(cambios.get("tipo_incidencia_id", r.tipo_incidencia_id))
            if tipo is None:
                raise NoEncontrado("Tipo de incidencia no encontrado.")
            if tipo.id != r.tipo_incidencia_id and not tipo.activo:
                raise ReglaDeNegocioViolada("Ese tipo de incidencia está desactivado.")
            if "fecha_hora_incidente" in cambios:
                fecha = self._reloj.localizar(cambios["fecha_hora_incidente"])
                if fecha > ahora + timedelta(minutes=5):
                    raise ReglaDeNegocioViolada("La fecha del incidente no puede ser futura.")
                cambios["fecha_hora_incidente"] = fecha
            for campo, valor in cambios.items():
                setattr(r, campo, valor)
            if tipo.es_otro and not (r.descripcion_otro or "").strip():
                raise ReglaDeNegocioViolada("Describe el tipo de incidencia (opción 'Otro').")
            if not tipo.es_otro:
                r.descripcion_otro = None
            r.validar()

            def legible(campo, valor):
                if valor is None:
                    return None
                if campo == "tipo_incidencia_id":
                    t = uow.tipos_incidencia.obtener_por_id(valor)
                    return t.nombre if t else str(valor)
                return valor.isoformat(timespec="minutes") if campo == "fecha_hora_incidente" else str(valor)

            diferencias = [c for c in sorted(CAMPOS_CORREGIBLES) if getattr(r, c) != antes[c]]
            if not diferencias:
                raise ReglaDeNegocioViolada("No hay cambios que guardar.")
            uow.reportes.guardar(r)
            for c in diferencias:
                registrar(uow, r.id, TipoEventoReporte.CORRECCION, actor_id, ahora, campo=c,
                          valor_anterior=legible(c, antes[c]), valor_nuevo=legible(c, getattr(r, c)),
                          comentario=comentario)
            uow.commit()
            return r


class CambiarGravedad:
    def __init__(self, uow: UnidadDeTrabajo, reloj: RelojPuerto, notificador: NotificadorPuerto):
        self._uow, self._reloj, self._notificador = uow, reloj, notificador

    def ejecutar(self, actor_id: int, reporte_id: int, nueva: Gravedad, motivo: str):
        motivo = (motivo or "").strip()
        if len(motivo) < MOTIVO_GRAVEDAD_MIN:
            raise ReglaDeNegocioViolada("Indica el motivo del cambio de gravedad.")
        ahora = self._reloj.ahora()
        with self._uow as uow:
            r = cargar_reporte(uow, reporte_id)
            anterior = r.gravedad
            r.cambiar_gravedad(Gravedad(nueva))
            uow.reportes.guardar(r)
            registrar(uow, r.id, TipoEventoReporte.GRAVEDAD, actor_id, ahora, campo="gravedad",
                      valor_anterior=anterior.value, valor_nuevo=r.gravedad.value, comentario=motivo)
            alertas = alertas_de(uow, [r]) if debe_alertar_subdireccion(anterior, r.gravedad) else []
            uow.commit()
        if alertas:
            try:
                self._notificador.alertar_gravedad_a_subdireccion(alertas)
            except Exception:  # noqa: BLE001
                log.exception("No se pudo enviar la alerta a Subdirección")
        return r


class TurnarASubdireccion:
    def __init__(self, uow: UnidadDeTrabajo, reloj: RelojPuerto):
        self._uow, self._reloj = uow, reloj

    def ejecutar(self, actor_id: int, reporte_id: int, comentario: Optional[str] = None):
        with self._uow as uow:
            r = cargar_reporte(uow, reporte_id)
            anterior = r.estado
            r.transicionar(EstadoReporte.ATENDIDO_SUBDIRECCION)
            uow.reportes.guardar(r)
            registrar(uow, r.id, TipoEventoReporte.ESTADO, actor_id, self._reloj.ahora(), campo="estado",
                      valor_anterior=anterior.value, valor_nuevo=r.estado.value, comentario=(comentario or "").strip() or None)
            uow.commit()
            return r


class CancelarReporte:
    """Los reportes no se borran (afectaría el historial): se cancelan con motivo y dejan de contar."""

    def __init__(self, uow: UnidadDeTrabajo, reloj: RelojPuerto):
        self._uow, self._reloj = uow, reloj

    def ejecutar(self, actor_id: int, reporte_id: int, motivo: str):
        ahora = self._reloj.ahora()
        with self._uow as uow:
            r = cargar_reporte(uow, reporte_id)
            r.cancelar(motivo, actor_id, ahora)
            uow.reportes.guardar(r)
            registrar(uow, r.id, TipoEventoReporte.CANCELACION, actor_id, ahora, comentario=r.motivo_cancelacion)
            uow.commit()
            return r
