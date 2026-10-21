from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.periodo_escolar import PeriodoEscolar


class PeriodoRepositorio(ABC):
    @abstractmethod
    def obtener_por_id(self, periodo_id: int) -> Optional[PeriodoEscolar]: ...

    @abstractmethod
    def obtener_por_nombre(self, nombre: str) -> Optional[PeriodoEscolar]: ...

    @abstractmethod
    def obtener_vigente(self) -> Optional[PeriodoEscolar]: ...

    @abstractmethod
    def listar(self) -> List[PeriodoEscolar]: ...

    @abstractmethod
    def desactivar_vigentes(self) -> None: ...

    @abstractmethod
    def guardar(self, periodo: PeriodoEscolar) -> PeriodoEscolar: ...
