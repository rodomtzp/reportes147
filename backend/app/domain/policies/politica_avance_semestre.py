"""Qué pasa con un estudiante al cerrar el periodo: avanza conservando la letra del grupo,
repite, egresa (sexto semestre) o causa baja."""
from dataclasses import dataclass
from typing import Optional

from app.domain.entities.grupo import SEMESTRE_MAX, Grupo
from app.domain.value_objects.estatus_estudiante import AccionAvance, EstatusEstudiante


@dataclass(frozen=True)
class DestinoAvance:
    accion: str  # AVANZA | REPITE | EGRESA | BAJA
    semestre: Optional[int] = None
    letra: Optional[str] = None
    nuevo_estatus: Optional[EstatusEstudiante] = None

    @property
    def clave_grupo(self) -> Optional[str]:
        return f"{self.semestre}{self.letra}" if self.semestre else None


def decidir_destino(grupo: Grupo, excepcion: Optional[AccionAvance] = None) -> DestinoAvance:
    if excepcion == AccionAvance.BAJA:
        return DestinoAvance("BAJA", nuevo_estatus=EstatusEstudiante.BAJA)
    if excepcion == AccionAvance.REPETIR:
        return DestinoAvance("REPITE", grupo.semestre, grupo.letra)
    if grupo.semestre >= SEMESTRE_MAX:
        return DestinoAvance("EGRESA", nuevo_estatus=EstatusEstudiante.EGRESADO)
    return DestinoAvance("AVANZA", grupo.semestre + 1, grupo.letra)
