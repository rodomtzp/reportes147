from dataclasses import dataclass
from typing import Optional


@dataclass
class AsignacionTutor:
    """Un docente es tutor de un grupo durante un periodo escolar (uno por grupo y periodo)."""

    usuario_id: int
    grupo_id: int
    periodo_id: int
    id: Optional[int] = None
