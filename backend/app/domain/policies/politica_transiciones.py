from app.domain.exceptions import ReglaDeNegocioViolada
from app.domain.value_objects.estado_reporte import EstadoReporte as E

TRANSICIONES = {
    E.CREADO: {E.EN_REVISION_ORIENTACION},
    E.EN_REVISION_ORIENTACION: {E.ATENDIDO_SUBDIRECCION},
    E.ATENDIDO_SUBDIRECCION: {E.SANCIONADO_CONCLUIDO},
    E.SANCIONADO_CONCLUIDO: set(),
}


def validar_transicion(origen: E, destino: E) -> None:
    if destino not in TRANSICIONES[origen]:
        raise ReglaDeNegocioViolada(
            f"No se puede pasar un reporte de '{origen.value}' a '{destino.value}'."
        )
