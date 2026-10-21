from typing import Iterable

from app.domain.value_objects.estado_llamada import EstadoLlamada


def tiene_llamada_efectiva(estados: Iterable[EstadoLlamada]) -> bool:
    """Requisito para concluir un reporte: al menos una llamada Realizada o Atendida."""
    return any(EstadoLlamada(e) in (EstadoLlamada.REALIZADA, EstadoLlamada.ATENDIDA) for e in estados)


def resumen_estado_llamada(estados: Iterable[EstadoLlamada]) -> EstadoLlamada:
    """Estado que se muestra de un reporte: el mejor logrado, o NO_CONTESTO si ya se intentó y nadie
    contestó, o PENDIENTE si falta intentar."""
    estados = [EstadoLlamada(e) for e in estados]
    if EstadoLlamada.ATENDIDA in estados:
        return EstadoLlamada.ATENDIDA
    if EstadoLlamada.REALIZADA in estados:
        return EstadoLlamada.REALIZADA
    if EstadoLlamada.PENDIENTE not in estados and EstadoLlamada.NO_CONTESTO in estados:
        return EstadoLlamada.NO_CONTESTO
    return EstadoLlamada.PENDIENTE
