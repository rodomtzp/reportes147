from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Tuple

RANGOS = ("periodo", "mes", "30dias")


@dataclass(frozen=True)
class EstudianteEnRiesgo:
    estudiante_id: int
    estudiante: str
    grupo: Optional[str]
    total: int  # reportes que cuentan en su ciclo abierto


@dataclass(frozen=True)
class Dashboard:
    rango: str
    desde: date
    hasta: date
    granularidad: str  # "dia" | "semana"
    periodo_nombre: Optional[str]
    alcance: str  # "total" (todo el plantel) | "propio" (sus grupos y/o los que creó) | "ninguno"
    total_rango: int = 0
    mes_actual: int = 0
    mes_anterior: int = 0
    por_gravedad: List[Tuple[str, int]] = field(default_factory=list)
    pendientes_llamada: Optional[int] = None   # solo Orientación, Subdirección y Dirección
    alertas_pendientes: Optional[int] = None   # solo quien ve la bandeja de alertas
    en_riesgo: List[EstudianteEnRiesgo] = field(default_factory=list)   # 2 o más reportes en el ciclo abierto
    listos_para_sancion: int = 0               # 3 o más
    total_en_riesgo: int = 0
    serie: List[Tuple[str, int]] = field(default_factory=list)
    por_grupo: List[Tuple[str, int]] = field(default_factory=list)
    por_carrera: List[Tuple[str, int]] = field(default_factory=list)
    por_tipo: List[Tuple[str, int]] = field(default_factory=list)
    por_estado: List[Tuple[str, int]] = field(default_factory=list)
