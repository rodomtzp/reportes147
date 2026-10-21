from abc import ABC, abstractmethod
from typing import Dict, Iterable, List, Optional

from app.domain.entities.intento_llamada import IntentoLlamada


class LlamadaRepositorio(ABC):
    @abstractmethod
    def guardar(self, intento: IntentoLlamada) -> IntentoLlamada: ...

    @abstractmethod
    def obtener_pendiente(self, reporte_id: int) -> Optional[IntentoLlamada]: ...

    @abstractmethod
    def listar_por_reporte(self, reporte_id: int) -> List[IntentoLlamada]: ...

    @abstractmethod
    def listar_por_reportes(self, reporte_ids: Iterable[int]) -> Dict[int, List[IntentoLlamada]]: ...

    @abstractmethod
    def tutor_tiene_resultados(self, tutor_id: int) -> bool:
        """True si hay llamadas ya registradas (no pendientes) con ese padre o tutor."""

    @abstractmethod
    def reasignar_pendientes(self, tutor_id: int, nuevo_tutor_id: int) -> None: ...
