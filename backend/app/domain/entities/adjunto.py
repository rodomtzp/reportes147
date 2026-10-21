from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Adjunto:
    reporte_id: int
    nombre_original: str
    tipo_mime: str
    clave_almacen: str  # referencia en el almacén de archivos (no es una ruta pública)
    tamano: int
    subido_por: int
    subido_en: datetime
    id: Optional[int] = None
