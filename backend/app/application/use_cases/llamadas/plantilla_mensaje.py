from datetime import datetime
from typing import Optional

_MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
          "octubre", "noviembre", "diciembre"]


def fecha_larga(fecha: datetime) -> str:
    return f"{fecha.day} de {_MESES[fecha.month - 1]} de {fecha.year}"


def construir_mensaje_whatsapp(
    tutor: str, estudiante: str, grupo: Optional[str], folio: str, incidencia: str,
    fecha: datetime, plantel: str, contacto: Optional[str] = None,
) -> str:
    """Mensaje formal. Por privacidad no incluye la descripción de los hechos ni la gravedad:
    esos detalles se tratan en la llamada o en persona con Orientación Educativa."""
    estudiante_grupo = f"{estudiante} ({grupo})" if grupo else estudiante
    invitacion = "Le invitamos a comunicarse con Orientación Educativa a la brevedad para atender este asunto."
    if contacto:
        invitacion += f" {contacto.strip()}"
    return (
        f"Estimado(a) {tutor}:\n\n"
        f"Le saluda Orientación Educativa del {plantel}. Le informamos que el/la estudiante "
        f"{estudiante_grupo} cuenta con un reporte (folio {folio}) por «{incidencia}», ocurrido el "
        f"{fecha_larga(fecha)}.\n\n"
        f"{invitacion}\n\n"
        f"Agradecemos su atención.\nOrientación Educativa – {plantel}"
    )
