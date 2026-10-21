from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.exceptions import ReglaDeNegocioViolada
from app.domain.value_objects.estado_llamada import EstadoLlamada


@dataclass
class IntentoLlamada:
    """Un intento de llamada a un padre o tutor por un reporte.

    Al crearse el reporte nace uno PENDIENTE (al tutor principal). Orientación registra el resultado
    y, si no contestaron, puede registrar más intentos (a ese u otro tutor)."""

    reporte_id: int
    tutor_legal_id: int
    creado_en: datetime
    estado: EstadoLlamada = EstadoLlamada.PENDIENTE
    realizado_por: Optional[int] = None
    fecha_hora: Optional[datetime] = None
    atendio_nombre: Optional[str] = None
    observaciones: Optional[str] = None
    id: Optional[int] = None

    def __post_init__(self) -> None:
        self.validar()

    def validar(self) -> None:
        self.estado = EstadoLlamada(self.estado)
        self.observaciones = (self.observaciones or "").strip() or None
        if self.observaciones and len(self.observaciones) > 500:
            raise ReglaDeNegocioViolada("Las observaciones no deben exceder 500 caracteres.")
        nombre = " ".join((self.atendio_nombre or "").split())
        if self.estado == EstadoLlamada.ATENDIDA:
            if not nombre:
                raise ReglaDeNegocioViolada("Indica quién atendió la llamada.")
            if len(nombre) > 120:
                raise ReglaDeNegocioViolada("El nombre de quien atendió es demasiado largo.")
            self.atendio_nombre = nombre
        else:
            self.atendio_nombre = None

    @property
    def es_efectiva(self) -> bool:
        return self.estado in (EstadoLlamada.REALIZADA, EstadoLlamada.ATENDIDA)
