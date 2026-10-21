from typing import List, Optional

from app.application.dto.llamadas import LlamadaDetalle, MensajeDetalle
from app.domain.entities.tutor_legal import TutorLegal


def tutor_principal(tutores: List[TutorLegal]) -> Optional[TutorLegal]:
    return next((t for t in tutores if t.es_principal), tutores[0] if tutores else None)


def llamadas_detalle(uow, reporte_id: int) -> List[LlamadaDetalle]:
    intentos = uow.llamadas.listar_por_reporte(reporte_id)
    if not intentos:
        return []
    estudiante_id = uow.reportes.obtener_por_id(reporte_id).estudiante_id
    tutores = {t.id: t for t in uow.tutores_legales.listar_por_estudiante(estudiante_id)}
    usuarios = uow.usuarios.obtener_por_ids({i.realizado_por for i in intentos if i.realizado_por})
    salida = []
    for i in intentos:
        t = tutores.get(i.tutor_legal_id) or uow.tutores_legales.obtener_por_id(i.tutor_legal_id)
        u = usuarios.get(i.realizado_por)
        salida.append(LlamadaDetalle(i, t.nombre if t else "?", t.parentesco if t else None, u.nombre if u else None))
    return salida


def mensajes_detalle(uow, reporte_id: int) -> List[MensajeDetalle]:
    mensajes = uow.mensajes_whatsapp.listar_por_reporte(reporte_id)
    if not mensajes:
        return []
    usuarios = uow.usuarios.obtener_por_ids({m.generado_por for m in mensajes})
    salida = []
    for m in mensajes:
        t = uow.tutores_legales.obtener_por_id(m.tutor_legal_id)
        u = usuarios.get(m.generado_por)
        salida.append(MensajeDetalle(m, t.nombre if t else "?", u.nombre if u else "?"))
    return salida
