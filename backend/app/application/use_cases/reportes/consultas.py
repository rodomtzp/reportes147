from datetime import datetime
from typing import List, Optional

from app.application.dto.reportes import AccesoReportes, FiltroReportes, ReporteDetalle, ReporteListado
from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.application.use_cases.reportes._comun import acceso_de, cargar_visible, detalle_de, enriquecer
from app.domain.entities.usuario import Usuario
from app.domain.exceptions import PermisoDenegado
from app.domain.policies.politica_permisos import Permiso, tiene_permiso
from app.domain.value_objects.estado_reporte import EstadoReporte
from app.domain.value_objects.gravedad import Gravedad

LIMITE_MAXIMO = 200


class ListarReportes:
    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(
        self,
        actor: Usuario,
        estudiante_id: Optional[int] = None,
        grupo_id: Optional[int] = None,
        carrera_id: Optional[int] = None,
        estado: Optional[EstadoReporte] = None,
        gravedad: Optional[Gravedad] = None,
        tipo_incidencia_id: Optional[int] = None,
        desde: Optional[datetime] = None,
        hasta: Optional[datetime] = None,
        texto: Optional[str] = None,
        incluir_cancelados: bool = False,
        sin_llamada_efectiva: bool = False,
        limite: int = 100,
        offset: int = 0,
    ) -> List[ReporteListado]:
        with self._uow as uow:
            acceso: AccesoReportes = acceso_de(uow, actor)
            if acceso.sin_acceso:
                raise PermisoDenegado("No tienes permiso para consultar reportes.")
            reportes = uow.reportes.listar(FiltroReportes(
                acceso=acceso, estudiante_id=estudiante_id, grupo_id=grupo_id, carrera_id=carrera_id,
                estado=estado, gravedad=gravedad, tipo_incidencia_id=tipo_incidencia_id, desde=desde,
                hasta=hasta, texto=texto, incluir_cancelados=incluir_cancelados,
                sin_llamada_efectiva=sin_llamada_efectiva,
                limite=max(1, min(limite, LIMITE_MAXIMO)), offset=max(0, offset),
            ))
            return enriquecer(uow, reportes)


class ObtenerReporte:
    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(self, actor: Usuario, reporte_id: int) -> ReporteDetalle:
        with self._uow as uow:
            reporte, acceso = cargar_visible(uow, actor, reporte_id)
            # El seguimiento de llamadas incluye datos de contacto: solo para quienes pueden verlos.
            return detalle_de(
                uow, acceso, reporte,
                incluir_seguimiento=tiene_permiso(actor.roles, Permiso.VER_DATOS_CONTACTO),
                incluir_acumulacion=tiene_permiso(actor.roles, Permiso.VER_TODOS_LOS_REPORTES),
            )
