from abc import ABC, abstractmethod
from typing import Dict, List


class LectorEstudiantesPuerto(ABC):
    @abstractmethod
    def leer(self, contenido: bytes, nombre_archivo: str) -> List[Dict[str, str]]:
        """Devuelve una fila por estudiante con las columnas canónicas (ver COLUMNAS_IMPORTACION).

        Lanza ReglaDeNegocioViolada si el formato es inválido o faltan columnas obligatorias.
        """
