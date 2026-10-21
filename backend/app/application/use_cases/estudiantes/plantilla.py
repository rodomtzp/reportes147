import csv
import io

from app.application.dto.estudiantes import COLUMNAS_IMPORTACION

_EJEMPLO = [
    "24301080150001", "Pérez", "Gómez", "Ana María", "4491234567", "ana@correo.com",
    "Av. Principal", "123", "Centro", "Ameca", "2024-2027", "1G",
    "Laura Gómez", "Madre", "4497654321", "laura@correo.com",
]


def plantilla_importacion_csv() -> str:
    """CSV de ejemplo con los encabezados correctos."""
    buf = io.StringIO()
    escritor = csv.writer(buf)
    escritor.writerow(COLUMNAS_IMPORTACION)
    escritor.writerow(_EJEMPLO)
    return buf.getvalue()
