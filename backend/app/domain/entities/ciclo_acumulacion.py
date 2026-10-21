from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class CicloAcumulacion:
    """Periodo durante el cual se cuentan los reportes de un estudiante. Se cierra solo con una
    sanción por acumulación; entonces el contador vuelve a cero (se abre el ciclo siguiente)."""

    estudiante_id: int
    numero: int
    fecha_inicio: datetime
    abierto: bool = True
    fecha_cierre: Optional[datetime] = None
    id: Optional[int] = None

    def cerrar(self, cuando: datetime) -> None:
        self.abierto, self.fecha_cierre = False, cuando
