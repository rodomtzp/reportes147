from abc import ABC, abstractmethod

from app.application.dto.exportaciones import LibroReportes


class ExportadorExcelPuerto(ABC):
    @abstractmethod
    def generar(self, libro: LibroReportes) -> bytes:
        """Devuelve el contenido de un .xlsx con la hoja Resumen y la hoja Reportes."""
