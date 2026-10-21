from dataclasses import dataclass, field
from typing import List, Optional

from app.domain.entities.estudiante import Estudiante
from app.domain.entities.inscripcion import Inscripcion
from app.domain.entities.tutor_legal import TutorLegal

COLUMNAS_IMPORTACION = [
    "numero_control", "primer_apellido", "segundo_apellido", "nombres", "telefono", "correo",
    "calle", "numero", "colonia", "ciudad", "generacion", "grupo",
    "tutor_nombre", "tutor_parentesco", "tutor_telefono", "tutor_correo",
]
MAX_FILAS_IMPORTACION = 2000
MAX_BYTES_IMPORTACION = 2 * 1024 * 1024
COLUMNAS_OBLIGATORIAS = [
    "numero_control", "primer_apellido", "nombres", "generacion", "grupo", "tutor_nombre", "tutor_telefono",
]


@dataclass(frozen=True)
class EstudianteListado:
    estudiante: Estudiante
    grupo_clave: Optional[str]
    carrera_nombre: Optional[str]


@dataclass(frozen=True)
class EstudianteResumen:
    """Datos mínimos (sin teléfonos ni dirección) para quien crea reportes."""

    id: int
    numero_control: str
    nombre_completo: str
    grupo_clave: Optional[str]
    carrera_nombre: Optional[str]


@dataclass(frozen=True)
class InscripcionDetalle:
    inscripcion: Inscripcion
    periodo_nombre: str
    grupo_clave: str
    semestre: int
    carrera_nombre: str


@dataclass(frozen=True)
class EstudianteDetalle:
    estudiante: Estudiante
    tutores_legales: List[TutorLegal]
    inscripciones: List[InscripcionDetalle]
    grupo_actual: Optional[str]
    carrera_actual: Optional[str]


@dataclass(frozen=True)
class FilaConProblema:
    fila: int
    numero_control: str
    motivo: str


@dataclass(frozen=True)
class ResultadoImportacion:
    creados: int
    omitidos: List[FilaConProblema] = field(default_factory=list)  # ya existían o repetidos
    errores: List[FilaConProblema] = field(default_factory=list)  # datos inválidos


@dataclass(frozen=True)
class MovimientoAvance:
    estudiante_id: int
    numero_control: str
    nombre: str
    grupo_origen: str
    grupo_destino: Optional[str]
    accion: str  # AVANZA | REPITE | EGRESA | BAJA
    grupo_destino_id: Optional[int] = None
    nuevo_estatus: Optional[str] = None


@dataclass(frozen=True)
class ResumenAvance:
    movimientos: List[MovimientoAvance]
    grupos_faltantes: List[str]
    omitidos_ya_inscritos: int
    ejecutado: bool
