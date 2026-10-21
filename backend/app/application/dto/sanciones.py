from dataclasses import dataclass, field
from typing import List, Optional

from app.application.dto.reportes import ReporteListado
from app.domain.entities.ciclo_acumulacion import CicloAcumulacion
from app.domain.entities.notificacion import Notificacion
from app.domain.entities.sancion import Sancion


@dataclass(frozen=True)
class SancionDetalle:
    sancion: Sancion
    tipo_nombre: str
    aplicada_por_nombre: str
    folios: List[str] = field(default_factory=list)  # reportes que cubre (directa: uno; acumulación: los del ciclo)


@dataclass(frozen=True)
class ResumenAcumulacion:
    ciclo_numero: int
    total: int
    umbral: int

    @property
    def listo_para_sancion(self) -> bool:
        return self.total >= self.umbral


@dataclass(frozen=True)
class CicloDetalle:
    ciclo: CicloAcumulacion
    reportes: List[ReporteListado]
    contables: int
    sancion: Optional[SancionDetalle] = None


@dataclass(frozen=True)
class ExpedienteDisciplinario:
    estudiante_id: int
    estudiante: str
    numero_control: str
    grupo_actual: Optional[str]
    total_reportes: int  # no cancelados, en toda la carrera
    umbral: int
    ciclo_actual: Optional[CicloDetalle]
    ciclos_anteriores: List[CicloDetalle]
    sanciones_directas: List[SancionDetalle]


@dataclass(frozen=True)
class AlertasPagina:
    notificaciones: List[Notificacion]
    pendientes: int
