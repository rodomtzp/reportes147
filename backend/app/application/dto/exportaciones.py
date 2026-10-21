from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple

ALCANCES = ("estudiante", "grupo", "carrera")
MAX_FILAS_EXPORTACION = 5000
TIPO_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@dataclass(frozen=True)
class FilaReporte:
    folio: str
    fecha_incidente: datetime
    numero_control: str
    estudiante: str
    grupo: Optional[str]
    carrera: Optional[str]
    tipo_incidencia: str
    descripcion: str
    gravedad: str
    estado: str
    cancelado: bool
    motivo_cancelacion: Optional[str]
    cuenta_acumulacion: bool
    creado_por: str
    llamada: str
    sancion: Optional[str]
    # Solo si se pidió contacto y el usuario puede verlo para ese estudiante:
    tutor_legal: Optional[str] = None
    telefono_tutor: Optional[str] = None
    correo_tutor: Optional[str] = None
    domicilio: Optional[str] = None


@dataclass(frozen=True)
class LibroReportes:
    titulo: str
    subtitulo: str  # alcance y filtros, en texto
    plantel: str
    generado_por: str
    generado_en: datetime
    incluye_contacto: bool
    filas: List[FilaReporte]
    por_gravedad: List[Tuple[str, int]] = field(default_factory=list)
    por_estado: List[Tuple[str, int]] = field(default_factory=list)
    por_sancion: List[Tuple[str, int]] = field(default_factory=list)
    sin_llamada_efectiva: int = 0


@dataclass(frozen=True)
class ArchivoExportado:
    nombre: str
    contenido: bytes
    filas: int
