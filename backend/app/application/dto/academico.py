from dataclasses import dataclass

from app.domain.entities.asignacion_tutor import AsignacionTutor


@dataclass(frozen=True)
class AsignacionDetalle:
    asignacion: AsignacionTutor
    usuario_nombre: str
    grupo_clave: str
    carrera_nombre: str
    periodo_nombre: str
