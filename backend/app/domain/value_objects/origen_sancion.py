from enum import Enum


class OrigenSancion(str, Enum):
    DIRECTA = "DIRECTA"  # por la magnitud de un reporte Grave o Muy grave
    ACUMULACION = "ACUMULACION"  # por 3 o más reportes en el ciclo
