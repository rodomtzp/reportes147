from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.ports.repositorios import BitacoraRepositorio
from app.domain.entities.registro_bitacora import RegistroBitacora
from app.domain.value_objects.accion_bitacora import AccionBitacora
from app.infrastructure.persistence.models import BitacoraModel
from app.infrastructure.persistence.utils import flush_o_conflicto

_CAMPOS = ("usuario_id", "fecha", "descripcion", "estudiante_id", "grupo_id", "carrera_id", "filas", "con_contacto")


def _registro(m: BitacoraModel) -> RegistroBitacora:
    return RegistroBitacora(id=m.id, accion=AccionBitacora(m.accion), **{c: getattr(m, c) for c in _CAMPOS})


class BitacoraRepositorioSQLAlchemy(BitacoraRepositorio):
    def __init__(self, session: Session):
        self._s = session

    def agregar(self, registro: RegistroBitacora) -> RegistroBitacora:
        m = BitacoraModel(accion=registro.accion.value, **{c: getattr(registro, c) for c in _CAMPOS})
        self._s.add(m)
        flush_o_conflicto(self._s)
        registro.id = m.id
        return registro

    def listar(self, accion: Optional[AccionBitacora] = None, usuario_id: Optional[int] = None,
               estudiante_id: Optional[int] = None, desde: Optional[datetime] = None,
               hasta: Optional[datetime] = None, limite: int = 100, offset: int = 0) -> List[RegistroBitacora]:
        q = select(BitacoraModel)
        if accion is not None:
            q = q.where(BitacoraModel.accion == accion.value)
        if usuario_id is not None:
            q = q.where(BitacoraModel.usuario_id == usuario_id)
        if estudiante_id is not None:
            q = q.where(BitacoraModel.estudiante_id == estudiante_id)
        if desde is not None:
            q = q.where(BitacoraModel.fecha >= desde)
        if hasta is not None:
            q = q.where(BitacoraModel.fecha <= hasta)
        q = q.order_by(BitacoraModel.fecha.desc(), BitacoraModel.id.desc()).limit(limite).offset(offset)
        return [_registro(m) for m in self._s.scalars(q).all()]
