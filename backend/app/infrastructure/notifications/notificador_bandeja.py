import logging
from typing import Callable, List, Optional

from app.application.dto.reportes import AlertaAcumulacion, AlertaReporte
from app.application.ports.correo import CorreoPuerto
from app.application.ports.notificador import NotificadorPuerto
from app.application.ports.reloj import RelojPuerto
from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.application.use_cases.alertas.bandeja import ROL_BANDEJA
from app.domain.entities.notificacion import Notificacion
from app.domain.value_objects.rol import Rol

log = logging.getLogger(__name__)
_ETIQUETA = {"GRAVE": "Grave", "MUY_GRAVE": "Muy grave"}


class NotificadorBandejaCorreo(NotificadorPuerto):
    """Guarda cada alerta en la bandeja de Subdirección y además la envía por correo a sus usuarios activos.

    Si el correo falla, la alerta sigue en la bandeja y se registra el motivo del fallo."""

    def __init__(self, uow_factory: Callable[[], UnidadDeTrabajo], correo: CorreoPuerto, reloj: RelojPuerto,
                 app_url: str, plantel: str):
        self._uow_factory, self._correo, self._reloj = uow_factory, correo, reloj
        self._app_url, self._plantel = app_url.rstrip("/"), plantel

    def alertar_gravedad_a_subdireccion(self, alertas: List[AlertaReporte]) -> None:
        for a in alertas:
            gravedad = _ETIQUETA.get(a.gravedad.value, a.gravedad.value)
            self._publicar(
                tipo="REPORTE_GRAVE", titulo=f"Reporte {gravedad}: {a.folio}",
                mensaje=f"{a.estudiante} ({a.grupo or 'sin grupo'}) · {a.tipo_incidencia} · Gravedad: {gravedad}.",
                enlace=f"{self._app_url}/reportes/{a.reporte_id}", reporte_id=a.reporte_id, estudiante_id=a.estudiante_id)

    def alertar_acumulacion_a_subdireccion(self, alertas: List[AlertaAcumulacion]) -> None:
        for a in alertas:
            self._publicar(
                tipo="ACUMULACION", titulo=f"{a.estudiante} acumula {a.total} reportes",
                mensaje=(f"{a.estudiante} ({a.numero_control}, {a.grupo or 'sin grupo'}) lleva {a.total} reportes en su ciclo "
                         f"actual (umbral: {a.umbral}): {', '.join(a.folios)}. Procede una sanción por acumulación."),
                enlace=f"{self._app_url}/estudiantes/{a.estudiante_id}/expediente", estudiante_id=a.estudiante_id)

    def _publicar(self, tipo: str, titulo: str, mensaje: str, enlace: str,
                  reporte_id: Optional[int] = None, estudiante_id: Optional[int] = None) -> None:
        with self._uow_factory() as uow:
            n = uow.notificaciones.guardar(Notificacion(
                tipo=tipo, titulo=titulo, mensaje=mensaje, rol_destino=ROL_BANDEJA, creada_en=self._reloj.ahora(),
                reporte_id=reporte_id, estudiante_id=estudiante_id))
            destinatarios = [u.correo for u in uow.usuarios.listar(rol=Rol.SUBDIRECCION, activo=True)]
            uow.commit()

        enviado, error = False, None
        if not destinatarios:
            error = "No hay usuarios activos con rol Subdirección."
        else:
            cuerpo = f"{mensaje}\n\nRevisar en el sistema: {enlace}\n\n— Sistema de Control de Reportes · {self._plantel}"
            try:
                self._correo.enviar(destinatarios, f"[{self._plantel}] {titulo}", cuerpo)
                enviado = True
            except Exception as exc:  # noqa: BLE001
                error = str(exc)[:300] or exc.__class__.__name__
                log.warning("No se pudo enviar el correo de la alerta %s: %s", n.id, error)
        with self._uow_factory() as uow:
            n.correo_enviado, n.correo_error = enviado, error
            uow.notificaciones.guardar(n)
            uow.commit()
