import uuid
from datetime import datetime
from pathlib import Path

from app.application.ports.almacen_archivos import AlmacenArchivosPuerto
from app.domain.exceptions import NoEncontrado, ReglaDeNegocioViolada

EXTENSIONES = {".jpg", ".png", ".webp", ".pdf"}


class AlmacenArchivosLocal(AlmacenArchivosPuerto):
    """Guarda en disco bajo un nombre aleatorio (nunca el que envía el usuario) y fuera de rutas públicas."""

    def __init__(self, directorio: str):
        self._base = Path(directorio).resolve()

    def guardar(self, contenido: bytes, extension: str) -> str:
        if extension not in EXTENSIONES:
            raise ReglaDeNegocioViolada("Tipo de archivo no permitido.")
        clave = f"{datetime.now().year}/{uuid.uuid4().hex}{extension}"
        ruta = self._base / clave
        ruta.parent.mkdir(parents=True, exist_ok=True)
        with open(ruta, "xb") as f:
            f.write(contenido)
        return clave

    def leer(self, clave: str) -> bytes:
        ruta = (self._base / clave).resolve()
        if self._base not in ruta.parents:  # evita salir del directorio con '..'
            raise NoEncontrado("Archivo no encontrado.")
        try:
            return ruta.read_bytes()
        except FileNotFoundError as exc:
            raise NoEncontrado("Archivo no encontrado.") from exc
