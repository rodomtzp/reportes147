from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from app.domain.entities.registro_bitacora import RegistroBitacora
from app.domain.value_objects.accion_bitacora import AccionBitacora


class BitacoraRepositorio(ABC):
    @abstractmethod
    def agregar(self, registro: RegistroBitacora) -> RegistroBitacora: ...

    @abstractmethod
    def listar(
        self,
        accion: Optional[AccionBitacora] = None,
        usuario_id: Optional[int] = None,
        estudiante_id: Optional[int] = None,
        desde: Optional[datetime] = None,
        hasta: Optional[datetime] = None,
        limite: int = 100,
        offset: int = 0,
    ) -> List[RegistroBitacora]:
        """Más recientes primero."""
