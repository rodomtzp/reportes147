from typing import Dict, Iterable, List, Optional

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.application.ports.repositorios import LlamadaRepositorio, MensajeWhatsAppRepositorio
from app.domain.entities.intento_llamada import IntentoLlamada
from app.domain.entities.mensaje_whatsapp import MensajeWhatsApp
from app.domain.value_objects.estado_llamada import EstadoLlamada
from app.infrastructure.persistence.models import IntentoLlamadaModel, MensajeWhatsAppModel
from app.infrastructure.persistence.utils import flush_o_conflicto

_CAMPOS = ("reporte_id", "tutor_legal_id", "realizado_por", "fecha_hora", "atendio_nombre", "observaciones", "creado_en")


def _intento(m: IntentoLlamadaModel) -> IntentoLlamada:
    return IntentoLlamada(id=m.id, estado=EstadoLlamada(m.estado), **{c: getattr(m, c) for c in _CAMPOS})


class LlamadaRepositorioSQLAlchemy(LlamadaRepositorio):
    def __init__(self, session: Session):
        self._s = session

    def guardar(self, intento: IntentoLlamada) -> IntentoLlamada:
        m = self._s.get(IntentoLlamadaModel, intento.id) if intento.id else IntentoLlamadaModel()
        for c in _CAMPOS:
            setattr(m, c, getattr(intento, c))
        m.estado = EstadoLlamada(intento.estado).value
        self._s.add(m)
        flush_o_conflicto(self._s)
        intento.id = m.id
        return intento

    def obtener_pendiente(self, reporte_id: int) -> Optional[IntentoLlamada]:
        q = select(IntentoLlamadaModel).where(
            IntentoLlamadaModel.reporte_id == reporte_id, IntentoLlamadaModel.estado == EstadoLlamada.PENDIENTE.value
        ).order_by(IntentoLlamadaModel.id).limit(1)
        m = self._s.scalar(q)
        return _intento(m) if m else None

    def listar_por_reporte(self, reporte_id: int) -> List[IntentoLlamada]:
        q = select(IntentoLlamadaModel).where(IntentoLlamadaModel.reporte_id == reporte_id).order_by(IntentoLlamadaModel.id)
        return [_intento(m) for m in self._s.scalars(q).all()]

    def listar_por_reportes(self, reporte_ids: Iterable[int]) -> Dict[int, List[IntentoLlamada]]:
        ids = list(reporte_ids)
        if not ids:
            return {}
        q = select(IntentoLlamadaModel).where(IntentoLlamadaModel.reporte_id.in_(ids)).order_by(IntentoLlamadaModel.id)
        salida: Dict[int, List[IntentoLlamada]] = {}
        for m in self._s.scalars(q).all():
            salida.setdefault(m.reporte_id, []).append(_intento(m))
        return salida

    def tutor_tiene_resultados(self, tutor_id: int) -> bool:
        q = select(IntentoLlamadaModel.id).where(
            IntentoLlamadaModel.tutor_legal_id == tutor_id, IntentoLlamadaModel.estado != EstadoLlamada.PENDIENTE.value
        ).limit(1)
        return self._s.scalar(q) is not None

    def reasignar_pendientes(self, tutor_id: int, nuevo_tutor_id: int) -> None:
        self._s.execute(
            update(IntentoLlamadaModel)
            .where(IntentoLlamadaModel.tutor_legal_id == tutor_id, IntentoLlamadaModel.estado == EstadoLlamada.PENDIENTE.value)
            .values(tutor_legal_id=nuevo_tutor_id)
            .execution_options(synchronize_session="fetch")
        )


def _mensaje(m: MensajeWhatsAppModel) -> MensajeWhatsApp:
    return MensajeWhatsApp(id=m.id, reporte_id=m.reporte_id, tutor_legal_id=m.tutor_legal_id, texto=m.texto,
                           generado_por=m.generado_por, generado_en=m.generado_en, enviado_en=m.enviado_en)


class MensajeWhatsAppRepositorioSQLAlchemy(MensajeWhatsAppRepositorio):
    def __init__(self, session: Session):
        self._s = session

    def guardar(self, mensaje: MensajeWhatsApp) -> MensajeWhatsApp:
        m = self._s.get(MensajeWhatsAppModel, mensaje.id) if mensaje.id else MensajeWhatsAppModel()
        m.reporte_id, m.tutor_legal_id, m.texto = mensaje.reporte_id, mensaje.tutor_legal_id, mensaje.texto
        m.generado_por, m.generado_en, m.enviado_en = mensaje.generado_por, mensaje.generado_en, mensaje.enviado_en
        self._s.add(m)
        flush_o_conflicto(self._s)
        mensaje.id = m.id
        return mensaje

    def obtener_por_id(self, mensaje_id: int) -> Optional[MensajeWhatsApp]:
        m = self._s.get(MensajeWhatsAppModel, mensaje_id)
        return _mensaje(m) if m else None

    def listar_por_reporte(self, reporte_id: int) -> List[MensajeWhatsApp]:
        q = select(MensajeWhatsAppModel).where(MensajeWhatsAppModel.reporte_id == reporte_id).order_by(MensajeWhatsAppModel.id)
        return [_mensaje(m) for m in self._s.scalars(q).all()]

    def tutor_tiene_mensajes(self, tutor_id: int) -> bool:
        q = select(MensajeWhatsAppModel.id).where(MensajeWhatsAppModel.tutor_legal_id == tutor_id).limit(1)
        return self._s.scalar(q) is not None
