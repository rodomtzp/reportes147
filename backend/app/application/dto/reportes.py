from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from app.application.dto.llamadas import LlamadaDetalle, MensajeDetalle
from app.domain.entities.adjunto import Adjunto
from app.domain.entities.historial_reporte import HistorialReporte
from app.domain.entities.reporte import Reporte
from app.domain.value_objects.estado_reporte import EstadoReporte
from app.domain.value_objects.gravedad import Gravedad

MAX_ADJUNTOS_POR_REPORTE = 5
MAX_BYTES_ADJUNTO = 5 * 1024 * 1024
MAX_ESTUDIANTES_POR_INCIDENTE = 20


@dataclass(frozen=True)
class AccesoReportes:
    """Qué reportes puede ver quien consulta (se aplican como OR)."""

    total: bool = False  # Orientación, Subdirección y Dirección
    creador_id: Optional[int] = None  # Docente: los que él creó
    grupo_ids: List[int] = field(default_factory=list)  # Tutor: estudiantes de sus grupos hoy
    periodo_id: Optional[int] = None  # periodo con el que se resuelven grupo_ids

    @property
    def sin_acceso(self) -> bool:
        return not self.total and self.creador_id is None and not self.grupo_ids


ACCESO_TOTAL = AccesoReportes(total=True)


@dataclass(frozen=True)
class FiltroReportes:
    acceso: AccesoReportes = field(default_factory=AccesoReportes)
    reporte_id: Optional[int] = None
    incidente_id: Optional[str] = None
    estudiante_id: Optional[int] = None
    grupo_id: Optional[int] = None  # grupo del estudiante cuando ocurrió
    carrera_id: Optional[int] = None
    estado: Optional[EstadoReporte] = None
    gravedad: Optional[Gravedad] = None
    tipo_incidencia_id: Optional[int] = None
    desde: Optional[datetime] = None
    hasta: Optional[datetime] = None
    texto: Optional[str] = None  # folio o nombre/control del estudiante
    incluir_cancelados: bool = False
    sin_llamada_efectiva: bool = False  # sin ninguna llamada Realizada o Atendida
    ciclo_id: Optional[int] = None
    solo_contables: bool = False  # excluye cancelados y con sanción directa
    limite: int = 100
    offset: int = 0


@dataclass(frozen=True)
class AlertaReporte:
    reporte_id: int
    estudiante_id: int
    folio: str
    estudiante: str
    grupo: Optional[str]
    gravedad: Gravedad
    tipo_incidencia: str


@dataclass(frozen=True)
class AlertaAcumulacion:
    estudiante_id: int
    estudiante: str
    numero_control: str
    grupo: Optional[str]
    total: int
    umbral: int
    folios: List[str]


@dataclass(frozen=True)
class ReporteCreado:
    reporte_id: int
    folio: str
    estudiante_id: int
    numero_control: str
    estudiante: str


@dataclass(frozen=True)
class ReporteListado:
    reporte: Reporte
    estudiante: str
    numero_control: str
    grupo_clave: Optional[str]
    carrera_nombre: Optional[str]
    tipo_incidencia: str
    creado_por_nombre: str
    estado_llamada: str = "PENDIENTE"


@dataclass(frozen=True)
class EventoDetalle:
    evento: HistorialReporte
    usuario_nombre: str


@dataclass(frozen=True)
class ReporteDetalle:
    listado: ReporteListado
    adjuntos: List[Adjunto]
    historial: List[EventoDetalle]
    relacionados: List[ReporteListado]  # otros reportes del mismo incidente a los que el usuario tiene acceso
    cancelado_por_nombre: Optional[str] = None
    llamadas: Optional[List[LlamadaDetalle]] = None  # solo para roles con acceso a datos de contacto
    mensajes: Optional[List[MensajeDetalle]] = None
    sancion: Optional[object] = None  # SancionDetalle (si el reporte fue sancionado)
    acumulacion: Optional[object] = None  # ResumenAcumulacion (solo roles directivos)
