import logging
from typing import List

from app.application.dto.reportes import AlertaReporte
from app.application.ports.notificador import NotificadorPuerto

log = logging.getLogger("alertas")


class NotificadorLog(NotificadorPuerto):
    """Provisional (Fase 3): deja la alerta en el log. En la Fase 5 se reemplaza por la
    bandeja interna de Subdirección y el envío de correo, sin tocar los casos de uso."""

    def alertar_gravedad_a_subdireccion(self, alertas: List[AlertaReporte]) -> None:
        for a in alertas:
            log.warning("ALERTA %s: %s (%s) – %s – %s", a.gravedad.value, a.folio, a.grupo or "sin grupo",
                        a.estudiante, a.tipo_incidencia)
