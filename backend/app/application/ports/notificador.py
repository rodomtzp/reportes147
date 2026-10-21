from abc import ABC, abstractmethod
from typing import List

from app.application.dto.reportes import AlertaAcumulacion, AlertaReporte


class NotificadorPuerto(ABC):
    @abstractmethod
    def alertar_gravedad_a_subdireccion(self, alertas: List[AlertaReporte]) -> None:
        """Avisa a Subdirección de reportes Grave o Muy grave (bandeja y correo en la Fase 5)."""

    @abstractmethod
    def alertar_acumulacion_a_subdireccion(self, alertas: List[AlertaAcumulacion]) -> None:
        """Avisa que un estudiante llegó a 3 o más reportes en su ciclo y requiere sanción."""
