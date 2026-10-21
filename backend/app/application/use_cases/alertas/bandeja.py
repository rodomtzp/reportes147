from app.application.dto.sanciones import AlertasPagina
from app.application.ports.reloj import RelojPuerto
from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.domain.exceptions import NoEncontrado

ROL_BANDEJA = "SUBDIRECCION"


class ListarAlertas:
    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(self, solo_pendientes: bool = True, limite: int = 100, offset: int = 0) -> AlertasPagina:
        with self._uow as uow:
            return AlertasPagina(
                notificaciones=uow.notificaciones.listar(ROL_BANDEJA, solo_pendientes, max(1, min(limite, 200)), max(0, offset)),
                pendientes=uow.notificaciones.contar_pendientes(ROL_BANDEJA),
            )


class ContarAlertasPendientes:
    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(self) -> int:
        with self._uow as uow:
            return uow.notificaciones.contar_pendientes(ROL_BANDEJA)


class MarcarAlertaAtendida:
    def __init__(self, uow: UnidadDeTrabajo, reloj: RelojPuerto):
        self._uow, self._reloj = uow, reloj

    def ejecutar(self, actor_id: int, notificacion_id: int):
        with self._uow as uow:
            n = uow.notificaciones.obtener_por_id(notificacion_id)
            if n is None:
                raise NoEncontrado("Alerta no encontrada.")
            if n.atendida_en is None:
                n.atendida_por, n.atendida_en = actor_id, self._reloj.ahora()
                uow.notificaciones.guardar(n)
                uow.commit()
            return n
