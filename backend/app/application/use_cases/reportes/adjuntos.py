import os
from typing import List, Optional, Tuple

from app.application.dto.reportes import AccesoReportes, FiltroReportes, MAX_ADJUNTOS_POR_REPORTE, MAX_BYTES_ADJUNTO
from app.application.ports.almacen_archivos import AlmacenArchivosPuerto
from app.application.ports.reloj import RelojPuerto
from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.application.use_cases.reportes._comun import cargar_reporte, cargar_visible, registrar
from app.domain.entities.adjunto import Adjunto
from app.domain.entities.reporte import Reporte
from app.domain.entities.usuario import Usuario
from app.domain.exceptions import NoEncontrado, PermisoDenegado, ReglaDeNegocioViolada
from app.domain.policies.politica_permisos import Permiso, tiene_permiso
from app.domain.value_objects.estado_reporte import EstadoReporte, TipoEventoReporte


def detectar_tipo(contenido: bytes) -> Optional[Tuple[str, str]]:
    """Identifica el tipo real por su firma (no se confía en la extensión ni en el MIME enviado)."""
    if contenido.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", ".jpg"
    if contenido.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", ".png"
    if contenido.startswith(b"%PDF-"):
        return "application/pdf", ".pdf"
    if contenido[:4] == b"RIFF" and contenido[8:12] == b"WEBP":
        return "image/webp", ".webp"
    return None


def _puede_adjuntar(actor: Usuario, r: Reporte) -> bool:
    """Orientación, Subdirección y Dirección, o el autor mientras el reporte está en revisión."""
    return tiene_permiso(actor.roles, Permiso.CORREGIR_REPORTE) or (
        r.creado_por == actor.id and r.estado == EstadoReporte.EN_REVISION_ORIENTACION
    )


class AgregarAdjunto:
    def __init__(self, uow: UnidadDeTrabajo, almacen: AlmacenArchivosPuerto, reloj: RelojPuerto):
        self._uow, self._almacen, self._reloj = uow, almacen, reloj

    def ejecutar(self, actor: Usuario, reporte_id: int, nombre_original: str, contenido: bytes,
                 aplicar_a_incidente: bool = False) -> List[Adjunto]:
        if not contenido:
            raise ReglaDeNegocioViolada("El archivo está vacío.")
        if len(contenido) > MAX_BYTES_ADJUNTO:
            raise ReglaDeNegocioViolada(f"El archivo excede {MAX_BYTES_ADJUNTO // (1024 * 1024)} MB.")
        tipo = detectar_tipo(contenido)
        if tipo is None:
            raise ReglaDeNegocioViolada("Solo se permiten imágenes (JPG, PNG, WEBP) o PDF.")
        mime, extension = tipo
        nombre = os.path.basename((nombre_original or "").replace("\\", "/")).strip()[:120] or f"evidencia{extension}"
        ahora = self._reloj.ahora()

        with self._uow as uow:
            r = cargar_reporte(uow, reporte_id)
            r.asegurar_modificable()
            if not _puede_adjuntar(actor, r):
                raise PermisoDenegado("No puedes agregar evidencias a este reporte.")
            destinos = [r]
            if aplicar_a_incidente:
                hermanos = uow.reportes.listar(FiltroReportes(
                    acceso=AccesoReportes(total=True), incidente_id=r.incidente_id, limite=100))
                for h in hermanos:
                    if h.id != r.id and h.estado != EstadoReporte.SANCIONADO_CONCLUIDO and _puede_adjuntar(actor, h):
                        destinos.append(h)
            for d in destinos:
                if len(uow.adjuntos.listar_por_reporte(d.id)) >= MAX_ADJUNTOS_POR_REPORTE:
                    raise ReglaDeNegocioViolada(f"El reporte {d.folio} ya tiene {MAX_ADJUNTOS_POR_REPORTE} evidencias.")

            clave = self._almacen.guardar(contenido, extension)  # una sola copia física
            guardados = []
            for d in destinos:
                guardados.append(uow.adjuntos.guardar(Adjunto(
                    reporte_id=d.id, nombre_original=nombre, tipo_mime=mime, clave_almacen=clave,
                    tamano=len(contenido), subido_por=actor.id, subido_en=ahora)))
                registrar(uow, d.id, TipoEventoReporte.ADJUNTO, actor.id, ahora, valor_nuevo=nombre)
            uow.commit()
            return guardados


class ObtenerAdjunto:
    def __init__(self, uow: UnidadDeTrabajo, almacen: AlmacenArchivosPuerto):
        self._uow, self._almacen = uow, almacen

    def ejecutar(self, actor: Usuario, reporte_id: int, adjunto_id: int) -> Tuple[Adjunto, bytes]:
        with self._uow as uow:
            cargar_visible(uow, actor, reporte_id)
            adjunto = uow.adjuntos.obtener_por_id(adjunto_id)
            if adjunto is None or adjunto.reporte_id != reporte_id:
                raise NoEncontrado("Evidencia no encontrada.")
        return adjunto, self._almacen.leer(adjunto.clave_almacen)
