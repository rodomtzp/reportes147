from enum import Enum


class EstatusEstudiante(str, Enum):
    ACTIVO = "ACTIVO"
    BAJA = "BAJA"
    EGRESADO = "EGRESADO"


class AccionAvance(str, Enum):
    """Excepciones al avance de semestre."""

    REPETIR = "REPETIR"  # se queda en el mismo grupo/semestre el siguiente periodo
    BAJA = "BAJA"  # causa baja: no se inscribe en el siguiente periodo
