from datetime import datetime, timedelta
from typing import Optional

from app.application.ports.reloj import RelojPuerto
from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.application.use_cases.llamadas._comun import tutor_principal
from app.application.use_cases.reportes._comun import cargar_reporte, registrar
from app.domain.entities.intento_llamada import IntentoLlamada
from app.domain.exceptions import ReglaDeNegocioViolada
from app.domain.value_objects.estado_llamada import EstadoLlamada
from app.domain.value_objects.estado_reporte import TipoEventoReporte

ETIQUETA = {"REALIZADA": "Realizada", "NO_CONTESTO": "No contestó", "ATENDIDA": "Atendida"}


class RegistrarLlamada:
    """Orientación registra el resultado de una llamada.

    Si el reporte tiene un intento PENDIENTE (el que se crea con el reporte) se completa; si no, se
    agrega un nuevo intento (p. ej. tras un 'No contestó'). Se puede elegir otro padre o tutor."""

    def __init__(self, uow: UnidadDeTrabajo, reloj: RelojPuerto):
        self._uow, self._reloj = uow, reloj

    def ejecutar(
        self,
        actor_id: int,
        reporte_id: int,
        estado: EstadoLlamada,
        tutor_legal_id: Optional[int] = None,
        atendio_nombre: Optional[str] = None,
        observaciones: Optional[str] = None,
        fecha_hora: Optional[datetime] = None,
    ) -> IntentoLlamada:
        estado = EstadoLlamada(estado)
        if estado == EstadoLlamada.PENDIENTE:
            raise ReglaDeNegocioViolada("Registra el resultado: Realizada, No contestó o Atendida.")
        ahora = self._reloj.ahora()
        fecha = self._reloj.localizar(fecha_hora) if fecha_hora else ahora
        if fecha > ahora + timedelta(minutes=5):
            raise ReglaDeNegocioViolada("La fecha de la llamada no puede ser futura.")

        with self._uow as uow:
            reporte = cargar_reporte(uow, reporte_id)
            reporte.asegurar_modificable()
            tutores = {t.id: t for t in uow.tutores_legales.listar_por_estudiante(reporte.estudiante_id)}
            pendiente = uow.llamadas.obtener_pendiente(reporte_id)
            destino = tutor_legal_id or (pendiente.tutor_legal_id if pendiente else None)
            if destino is None:
                principal = tutor_principal(list(tutores.values()))
                destino = principal.id if principal else None
            if destino not in tutores:
                raise ReglaDeNegocioViolada("El padre o tutor indicado no corresponde a este estudiante.")

            intento = pendiente or IntentoLlamada(reporte_id=reporte_id, tutor_legal_id=destino, creado_en=ahora)
            intento.tutor_legal_id = destino
            intento.estado, intento.realizado_por, intento.fecha_hora = estado, actor_id, fecha
            intento.atendio_nombre, intento.observaciones = atendio_nombre, observaciones
            intento.validar()
            uow.llamadas.guardar(intento)

            detalle = [f"Atendió: {intento.atendio_nombre}" if intento.atendio_nombre else None, intento.observaciones]
            registrar(uow, reporte_id, TipoEventoReporte.LLAMADA, actor_id, ahora,
                      campo=tutores[destino].nombre, valor_nuevo=ETIQUETA[estado.value],
                      comentario=". ".join(x for x in detalle if x) or None)
            uow.commit()
            return intento
