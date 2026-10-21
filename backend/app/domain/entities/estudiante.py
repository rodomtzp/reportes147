import re
from dataclasses import dataclass
from typing import Optional

from app.domain.exceptions import ReglaDeNegocioViolada
from app.domain.policies.politica_contacto import limpiar, normalizar_correo, normalizar_telefono
from app.domain.value_objects.estatus_estudiante import EstatusEstudiante

_NUMERO_CONTROL = re.compile(r"^[A-Z0-9]{5,20}$")


@dataclass
class Estudiante:
    numero_control: str
    primer_apellido: str
    nombres: str
    generacion: str
    segundo_apellido: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[str] = None
    calle: Optional[str] = None
    numero: Optional[str] = None
    colonia: Optional[str] = None
    ciudad: Optional[str] = None
    estatus: EstatusEstudiante = EstatusEstudiante.ACTIVO
    id: Optional[int] = None

    def __post_init__(self) -> None:
        self.validar()

    def validar(self) -> None:
        self.numero_control = (self.numero_control or "").strip().upper()
        if not _NUMERO_CONTROL.match(self.numero_control):
            raise ReglaDeNegocioViolada("El número de control debe tener de 5 a 20 letras o dígitos.")
        self.primer_apellido = limpiar(self.primer_apellido) or ""
        self.nombres = limpiar(self.nombres) or ""
        self.generacion = limpiar(self.generacion) or ""
        if not (self.primer_apellido and self.nombres and self.generacion):
            raise ReglaDeNegocioViolada("Primer apellido, nombre(s) y generación son obligatorios.")
        if len(self.generacion) > 20:
            raise ReglaDeNegocioViolada("La generación no debe exceder 20 caracteres.")
        self.segundo_apellido = limpiar(self.segundo_apellido)
        self.calle, self.numero = limpiar(self.calle), limpiar(self.numero)
        self.colonia, self.ciudad = limpiar(self.colonia), limpiar(self.ciudad)
        self.telefono = normalizar_telefono(self.telefono) if limpiar(self.telefono) else None
        self.correo = normalizar_correo(self.correo)
        self.estatus = EstatusEstudiante(self.estatus)

    @property
    def nombre_completo(self) -> str:
        return " ".join(p for p in (self.primer_apellido, self.segundo_apellido, self.nombres) if p)
