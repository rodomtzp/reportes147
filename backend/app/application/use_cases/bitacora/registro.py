"""Alta de registros de bitácora. Se llama dentro de la transacción del caso de uso que accede al dato."""
from typing import Optional

from app.domain.entities.registro_bitacora import RegistroBitacora
from app.domain.value_objects.accion_bitacora import AccionBitacora


def registrar_consulta_contacto(uow, reloj, usuario_id: int, estudiante_id: int, descripcion: str) -> None:
    uow.bitacora.agregar(RegistroBitacora(
        accion=AccionBitacora.CONSULTA_CONTACTO, usuario_id=usuario_id, fecha=reloj.ahora(),
        descripcion=descripcion, estudiante_id=estudiante_id, con_contacto=True,
    ))


def registrar_exportacion(uow, reloj, usuario_id: int, descripcion: str, filas: int, con_contacto: bool,
                          estudiante_id: Optional[int] = None, grupo_id: Optional[int] = None,
                          carrera_id: Optional[int] = None) -> None:
    uow.bitacora.agregar(RegistroBitacora(
        accion=AccionBitacora.EXPORTACION, usuario_id=usuario_id, fecha=reloj.ahora(), descripcion=descripcion,
        estudiante_id=estudiante_id, grupo_id=grupo_id, carrera_id=carrera_id, filas=filas, con_contacto=con_contacto,
    ))
