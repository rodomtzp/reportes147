from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.domain.entities.registro_bitacora import RegistroBitacora
from app.domain.value_objects.accion_bitacora import AccionBitacora

LIMITE_MAXIMO = 200


@dataclass(frozen=True)
class RegistroBitacoraDetalle:
    registro: RegistroBitacora
    usuario_nombre: str
    estudiante: Optional[str]


class ConsultarBitacora:
    """Solo el Administrador (el permiso se exige en la API)."""

    def __init__(self, uow: UnidadDeTrabajo):
        self._uow = uow

    def ejecutar(
        self,
        accion: Optional[AccionBitacora] = None,
        usuario_id: Optional[int] = None,
        estudiante_id: Optional[int] = None,
        desde: Optional[datetime] = None,
        hasta: Optional[datetime] = None,
        limite: int = 100,
        offset: int = 0,
    ) -> List[RegistroBitacoraDetalle]:
        with self._uow as uow:
            registros = uow.bitacora.listar(
                accion=accion, usuario_id=usuario_id, estudiante_id=estudiante_id, desde=desde, hasta=hasta,
                limite=max(1, min(limite, LIMITE_MAXIMO)), offset=max(0, offset))
            usuarios = uow.usuarios.obtener_por_ids({r.usuario_id for r in registros})
            estudiantes = uow.estudiantes.obtener_por_ids({r.estudiante_id for r in registros if r.estudiante_id})
            return [
                RegistroBitacoraDetalle(
                    r, usuarios[r.usuario_id].nombre if r.usuario_id in usuarios else "?",
                    estudiantes[r.estudiante_id].nombre_completo if r.estudiante_id in estudiantes else None)
                for r in registros
            ]
