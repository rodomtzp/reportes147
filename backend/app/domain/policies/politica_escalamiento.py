from typing import Optional

from app.domain.value_objects.gravedad import Gravedad


def debe_alertar_subdireccion(anterior: Optional[Gravedad], nueva: Gravedad) -> bool:
    """Alerta cuando un reporte llega a Grave o Muy grave (al crearse o al ser escalado),
    no cada vez que se vuelve a modificar dentro de esas gravedades."""
    return nueva.escala_a_subdireccion and not (anterior is not None and anterior.escala_a_subdireccion)
