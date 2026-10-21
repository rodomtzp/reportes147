from dataclasses import dataclass
from typing import Optional


@dataclass
class Inscripcion:
    """Grupo en el que cursó (o cursa) un estudiante durante un periodo escolar.

    Es la base del historial: 1G en el periodo A, 2G en el B, etc.
    """

    estudiante_id: int
    grupo_id: int
    periodo_id: int
    id: Optional[int] = None
