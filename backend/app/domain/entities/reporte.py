from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.exceptions import ReglaDeNegocioViolada
from app.domain.policies.politica_transiciones import validar_transicion
from app.domain.value_objects.estado_reporte import EstadoReporte
from app.domain.value_objects.gravedad import Gravedad

DESCRIPCION_MIN, DESCRIPCION_MAX = 10, 2000
MOTIVO_CANCELACION_MIN = 10


def _texto(valor: Optional[str]) -> str:
    return (valor or "").strip()


@dataclass
class Reporte:
    """Un reporte disciplinario sobre un estudiante (uno por estudiante; los de un mismo
    suceso comparten `incidente_id`). Nunca se borra: solo se cancela con motivo."""

    estudiante_id: int
    inscripcion_id: int  # grupo y periodo del estudiante cuando ocurrió
    creado_por: int
    tipo_incidencia_id: int
    descripcion: str
    fecha_hora_incidente: datetime
    gravedad: Gravedad
    incidente_id: str
    descripcion_otro: Optional[str] = None
    folio: Optional[str] = None
    estado: EstadoReporte = EstadoReporte.CREADO
    cancelado: bool = False
    motivo_cancelacion: Optional[str] = None
    cancelado_por: Optional[int] = None
    cancelado_en: Optional[datetime] = None
    creado_en: Optional[datetime] = None
    ciclo_id: Optional[int] = None  # ciclo de acumulación del estudiante al que pertenece
    cuenta_acumulacion: bool = True  # False cuando recibe una sanción directa
    id: Optional[int] = None

    def __post_init__(self) -> None:
        self.validar()

    def validar(self) -> None:
        self.descripcion = _texto(self.descripcion)
        if not DESCRIPCION_MIN <= len(self.descripcion) <= DESCRIPCION_MAX:
            raise ReglaDeNegocioViolada(
                f"La descripción debe tener entre {DESCRIPCION_MIN} y {DESCRIPCION_MAX} caracteres."
            )
        self.descripcion_otro = _texto(self.descripcion_otro) or None
        if self.descripcion_otro and len(self.descripcion_otro) > 200:
            raise ReglaDeNegocioViolada("La descripción del tipo 'Otro' no debe exceder 200 caracteres.")
        self.gravedad = Gravedad(self.gravedad)
        self.estado = EstadoReporte(self.estado)

    @property
    def es_contable(self) -> bool:
        """Cuenta para las 3 faltas del ciclo: no cancelado y sin sanción directa."""
        return not self.cancelado and self.cuenta_acumulacion

    def asegurar_sancion_directa(self) -> None:
        self.asegurar_modificable()
        if not self.gravedad.escala_a_subdireccion:
            raise ReglaDeNegocioViolada(
                "La sanción directa solo aplica a reportes Grave o Muy grave. "
                "Los demás se sancionan por acumulación (3 o más reportes)."
            )

    def asegurar_modificable(self) -> None:
        if self.cancelado:
            raise ReglaDeNegocioViolada("El reporte está cancelado y ya no se puede modificar.")
        if self.estado == EstadoReporte.SANCIONADO_CONCLUIDO:
            raise ReglaDeNegocioViolada("El reporte está concluido y ya no se puede modificar.")

    def transicionar(self, destino: EstadoReporte) -> None:
        self.asegurar_modificable()
        validar_transicion(self.estado, destino)
        self.estado = destino

    def cambiar_gravedad(self, nueva: Gravedad) -> None:
        self.asegurar_modificable()
        if Gravedad(nueva) == self.gravedad:
            raise ReglaDeNegocioViolada("El reporte ya tiene esa gravedad.")
        self.gravedad = Gravedad(nueva)

    def cancelar(self, motivo: str, usuario_id: int, cuando: datetime) -> None:
        self.asegurar_modificable()
        motivo = _texto(motivo)
        if len(motivo) < MOTIVO_CANCELACION_MIN:
            raise ReglaDeNegocioViolada(
                f"Indica el motivo de la cancelación (mínimo {MOTIVO_CANCELACION_MIN} caracteres)."
            )
        self.cancelado, self.motivo_cancelacion = True, motivo
        self.cancelado_por, self.cancelado_en = usuario_id, cuando
