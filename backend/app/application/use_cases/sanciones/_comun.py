from typing import List

from app.application.use_cases.reportes._comun import registrar
from app.domain.entities.reporte import Reporte
from app.domain.exceptions import ReglaDeNegocioViolada
from app.domain.policies.politica_llamadas import tiene_llamada_efectiva
from app.domain.value_objects.estado_reporte import EstadoReporte, TipoEventoReporte


def exigir_llamada_efectiva(uow, reportes: List[Reporte]) -> None:
    """Un reporte no puede concluir sin al menos una llamada Realizada o Atendida."""
    intentos = uow.llamadas.listar_por_reportes([r.id for r in reportes])
    sin_llamada = [r.folio for r in reportes if not tiene_llamada_efectiva(i.estado for i in intentos.get(r.id, []))]
    if sin_llamada:
        raise ReglaDeNegocioViolada(
            "Antes de sancionar, Orientación debe registrar al menos una llamada Realizada o Atendida en: "
            + ", ".join(sin_llamada) + "."
        )


def concluir(uow, reporte: Reporte, usuario_id: int, ahora, motivo: str) -> None:
    """Lleva el reporte a 'Sancionado / Concluido'; si aún estaba en Orientación, pasa antes por
    'Atendido por Subdirección' (queda registrado en el historial)."""
    if reporte.estado == EstadoReporte.EN_REVISION_ORIENTACION:
        reporte.transicionar(EstadoReporte.ATENDIDO_SUBDIRECCION)
        registrar(uow, reporte.id, TipoEventoReporte.ESTADO, usuario_id, ahora, campo="estado",
                  valor_anterior=EstadoReporte.EN_REVISION_ORIENTACION.value,
                  valor_nuevo=EstadoReporte.ATENDIDO_SUBDIRECCION.value, comentario=motivo)
    anterior = reporte.estado
    reporte.transicionar(EstadoReporte.SANCIONADO_CONCLUIDO)
    registrar(uow, reporte.id, TipoEventoReporte.ESTADO, usuario_id, ahora, campo="estado",
              valor_anterior=anterior.value, valor_nuevo=reporte.estado.value, comentario=motivo)
