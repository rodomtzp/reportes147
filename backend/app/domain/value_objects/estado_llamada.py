from enum import Enum


class EstadoLlamada(str, Enum):
    PENDIENTE = "PENDIENTE"  # aún sin intentar
    REALIZADA = "REALIZADA"  # se realizó la llamada y se comunicó el asunto
    NO_CONTESTO = "NO_CONTESTO"
    ATENDIDA = "ATENDIDA"  # contestó; se registra quién atendió
