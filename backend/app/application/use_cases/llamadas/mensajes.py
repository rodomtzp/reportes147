from typing import Optional

from app.application.dto.llamadas import MensajeGenerado
from app.application.ports.mensajeria import MensajeriaPuerto
from app.application.ports.reloj import RelojPuerto
from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.application.use_cases.estudiantes._comun import mapas_academicos
from app.application.use_cases.llamadas._comun import tutor_principal
from app.application.use_cases.llamadas.plantilla_mensaje import construir_mensaje_whatsapp
from app.application.use_cases.reportes._comun import cargar_reporte, registrar
from app.domain.entities.mensaje_whatsapp import MensajeWhatsApp
from app.domain.exceptions import NoEncontrado, ReglaDeNegocioViolada
from app.domain.value_objects.estado_reporte import TipoEventoReporte


class GenerarMensajeWhatsApp:
    """Genera el texto formal y el enlace para enviarlo desde WhatsApp, y deja registro del mensaje."""

    def __init__(self, uow: UnidadDeTrabajo, reloj: RelojPuerto, mensajeria: MensajeriaPuerto,
                 plantel: str, contacto_orientacion: Optional[str] = None):
        self._uow, self._reloj, self._mensajeria = uow, reloj, mensajeria
        self._plantel, self._contacto = plantel, contacto_orientacion

    def ejecutar(self, actor_id: int, reporte_id: int, tutor_legal_id: Optional[int] = None) -> MensajeGenerado:
        ahora = self._reloj.ahora()
        with self._uow as uow:
            reporte = cargar_reporte(uow, reporte_id)
            reporte.asegurar_modificable()
            tutores = {t.id: t for t in uow.tutores_legales.listar_por_estudiante(reporte.estudiante_id)}
            tutor = tutores.get(tutor_legal_id) if tutor_legal_id else tutor_principal(list(tutores.values()))
            if tutor is None:
                raise ReglaDeNegocioViolada("El padre o tutor indicado no corresponde a este estudiante.")

            estudiante = uow.estudiantes.obtener_por_id(reporte.estudiante_id)
            insc = uow.inscripciones.obtener_por_ids([reporte.inscripcion_id]).get(reporte.inscripcion_id)
            grupos, _ = mapas_academicos(uow)
            tipo = uow.tipos_incidencia.obtener_por_id(reporte.tipo_incidencia_id)
            incidencia = tipo.nombre + (f": {reporte.descripcion_otro}" if reporte.descripcion_otro else "")
            texto = construir_mensaje_whatsapp(
                tutor=tutor.nombre, estudiante=estudiante.nombre_completo,
                grupo=grupos[insc.grupo_id].clave if insc else None, folio=reporte.folio,
                incidencia=incidencia, fecha=self._reloj.localizar(reporte.fecha_hora_incidente),
                plantel=self._plantel, contacto=self._contacto,
            )
            mensaje = uow.mensajes_whatsapp.guardar(MensajeWhatsApp(
                reporte_id=reporte_id, tutor_legal_id=tutor.id, texto=texto, generado_por=actor_id, generado_en=ahora))
            registrar(uow, reporte_id, TipoEventoReporte.MENSAJE, actor_id, ahora, campo=tutor.nombre,
                      valor_nuevo="Mensaje de WhatsApp generado")
            uow.commit()
            return MensajeGenerado(mensaje, tutor, self._mensajeria.preparar(tutor.telefono, texto).enlace)


class MarcarMensajeEnviado:
    def __init__(self, uow: UnidadDeTrabajo, reloj: RelojPuerto):
        self._uow, self._reloj = uow, reloj

    def ejecutar(self, actor_id: int, mensaje_id: int) -> MensajeWhatsApp:
        ahora = self._reloj.ahora()
        with self._uow as uow:
            mensaje = uow.mensajes_whatsapp.obtener_por_id(mensaje_id)
            if mensaje is None:
                raise NoEncontrado("Mensaje no encontrado.")
            if mensaje.enviado_en is None:
                mensaje.enviado_en = ahora
                uow.mensajes_whatsapp.guardar(mensaje)
                tutor = uow.tutores_legales.obtener_por_id(mensaje.tutor_legal_id)
                registrar(uow, mensaje.reporte_id, TipoEventoReporte.MENSAJE, actor_id, ahora,
                          campo=tutor.nombre if tutor else None, valor_nuevo="Mensaje de WhatsApp enviado")
                uow.commit()
            return mensaje
