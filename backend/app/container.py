"""Composición de dependencias: único lugar que conoce las implementaciones concretas.

Cada método devuelve un caso de uso con su propia unidad de trabajo, de modo que
cada ejecución abre y cierra su propia transacción.
"""
from app.application.use_cases.academico.asignaciones_tutor import (
    AsignarTutor, ListarAsignacionesTutor, RetirarAsignacionTutor,
)
from app.application.use_cases.academico.carreras import ActualizarCarrera, CrearCarrera, ListarCarreras
from app.application.use_cases.academico.grupos import ActualizarGrupo, CrearGrupo, ListarGrupos
from app.application.use_cases.academico.periodos import (
    ActualizarPeriodo, CrearPeriodo, EstablecerPeriodoVigente, ListarPeriodos,
)
from app.application.use_cases.auth.cambiar_password import CambiarPassword
from app.application.use_cases.auth.iniciar_sesion import IniciarSesion
from app.application.use_cases.auth.obtener_usuario_autenticado import ObtenerUsuarioAutenticado
from app.application.use_cases.auth.renovar_token import RenovarToken
from app.application.use_cases.catalogos.tipos_incidencia import (
    ActualizarTipoIncidencia, CrearTipoIncidencia, ListarTiposIncidencia,
)
from app.application.use_cases.catalogos.tipos_sancion import (
    ActualizarTipoSancion, CrearTipoSancion, ListarTiposSancion,
)
from app.application.use_cases.estudiantes.actualizar_estudiante import (
    ActualizarEstudiante, CambiarGrupoEstudiante,
)
from app.application.use_cases.estudiantes.avanzar_semestre import AvanzarSemestre
from app.application.use_cases.estudiantes.consultas import (
    BuscarEstudiantes, GruposTutelados, ListarEstudiantes, ObtenerEstudiante,
)
from app.application.use_cases.estudiantes.crear_estudiante import CrearEstudiante
from app.application.use_cases.estudiantes.importar_estudiantes import ImportarEstudiantes
from app.application.use_cases.estudiantes.tutores_legales import (
    ActualizarTutorLegal, AgregarTutorLegal, EliminarTutorLegal,
)
from app.application.use_cases.alertas.bandeja import ContarAlertasPendientes, ListarAlertas, MarcarAlertaAtendida
from app.application.use_cases.llamadas.mensajes import GenerarMensajeWhatsApp, MarcarMensajeEnviado
from app.application.use_cases.llamadas.registrar_llamada import RegistrarLlamada
from app.application.use_cases.llamadas.seguimiento import ObtenerSeguimientoLlamadas
from app.application.use_cases.reportes.adjuntos import AgregarAdjunto, ObtenerAdjunto
from app.application.use_cases.reportes.consultas import ListarReportes, ObtenerReporte
from app.application.use_cases.reportes.crear_reportes import CrearReportes
from app.application.use_cases.reportes.gestion import (
    CambiarGravedad, CancelarReporte, CorregirReporte, TurnarASubdireccion,
)
from app.application.use_cases.bitacora.consultar import ConsultarBitacora
from app.application.use_cases.dashboard.obtener_dashboard import ObtenerDashboard
from app.application.use_cases.exportaciones.exportar_reportes import ExportarReportes
from app.application.use_cases.sanciones.aplicar_sanciones import AplicarSancionDirecta, AplicarSancionPorAcumulacion
from app.application.use_cases.sanciones.expediente import ObtenerExpediente
from app.application.use_cases.usuarios.actualizar_usuario import ActualizarUsuario
from app.application.use_cases.usuarios.crear_usuario import CrearUsuario
from app.application.use_cases.usuarios.listar_usuarios import ListarUsuarios
from app.application.use_cases.usuarios.registrar_usuario import RegistrarUsuario
from app.application.use_cases.usuarios.restablecer_password import RestablecerPassword
from app.config.settings import Settings
from app.infrastructure.clock.reloj_sistema import RelojSistema
from app.infrastructure.exportacion.excel_openpyxl import ExportadorExcelOpenpyxl
from app.infrastructure.importacion.lector_estudiantes import LectorEstudiantes
from app.infrastructure.messaging.whatsapp_enlace import MensajeriaEnlaceManual
from app.infrastructure.notifications.correo import CorreoNulo, CorreoSMTP
from app.infrastructure.notifications.notificador_bandeja import NotificadorBandejaCorreo
from app.infrastructure.storage.almacen_local import AlmacenArchivosLocal
from app.infrastructure.persistence.database import crear_engine, crear_session_factory
from app.infrastructure.persistence.unit_of_work import UnidadDeTrabajoSQLAlchemy
from app.infrastructure.security.hasher_werkzeug import HasherWerkzeug
from app.infrastructure.security.token_jwt import TokenJWT


class Container:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.engine = crear_engine(settings.database_url)
        self.session_factory = crear_session_factory(self.engine)
        self.hasher = HasherWerkzeug()
        self.lector_estudiantes = LectorEstudiantes()
        self.reloj = RelojSistema(settings.zona_horaria)
        self.exportador_excel = ExportadorExcelOpenpyxl()
        self.almacen = AlmacenArchivosLocal(settings.uploads_dir)
        self.mensajeria = MensajeriaEnlaceManual(settings.whatsapp_codigo_pais)  # luego: API de WhatsApp Business
        self.correo = (
            CorreoSMTP(settings.smtp_host, settings.smtp_puerto, settings.smtp_usuario, settings.smtp_password,
                       settings.smtp_remitente, settings.smtp_starttls)
            if settings.smtp_host else CorreoNulo()
        )
        self.notificador = NotificadorBandejaCorreo(
            self.uow, self.correo, self.reloj, settings.app_url, settings.plantel_nombre)
        self.tokens = TokenJWT(settings.secret_key, settings.access_minutos, settings.refresh_horas)

    def uow(self) -> UnidadDeTrabajoSQLAlchemy:
        return UnidadDeTrabajoSQLAlchemy(self.session_factory)

    # --- auth ---
    def iniciar_sesion(self): return IniciarSesion(self.uow(), self.hasher, self.tokens, self.reloj)
    def renovar_token(self): return RenovarToken(self.uow(), self.tokens)
    def usuario_autenticado(self): return ObtenerUsuarioAutenticado(self.uow(), self.tokens)
    def cambiar_password(self): return CambiarPassword(self.uow(), self.hasher, self.tokens)

    # --- usuarios ---
    def crear_usuario(self): return CrearUsuario(self.uow(), self.hasher)
    def registrar_usuario(self): return RegistrarUsuario(self.uow(), self.hasher)
    def listar_usuarios(self): return ListarUsuarios(self.uow())
    def actualizar_usuario(self): return ActualizarUsuario(self.uow())
    def restablecer_password(self): return RestablecerPassword(self.uow(), self.hasher)

    # --- académico ---
    def crear_carrera(self): return CrearCarrera(self.uow())
    def actualizar_carrera(self): return ActualizarCarrera(self.uow())
    def listar_carreras(self): return ListarCarreras(self.uow())
    def crear_grupo(self): return CrearGrupo(self.uow())
    def actualizar_grupo(self): return ActualizarGrupo(self.uow())
    def listar_grupos(self): return ListarGrupos(self.uow())
    def crear_periodo(self): return CrearPeriodo(self.uow())
    def actualizar_periodo(self): return ActualizarPeriodo(self.uow())
    def establecer_periodo_vigente(self): return EstablecerPeriodoVigente(self.uow())
    def listar_periodos(self): return ListarPeriodos(self.uow())
    def asignar_tutor(self): return AsignarTutor(self.uow())
    def retirar_asignacion_tutor(self): return RetirarAsignacionTutor(self.uow())
    def listar_asignaciones_tutor(self): return ListarAsignacionesTutor(self.uow())

    # --- catálogos ---
    def crear_tipo_incidencia(self): return CrearTipoIncidencia(self.uow())
    def actualizar_tipo_incidencia(self): return ActualizarTipoIncidencia(self.uow())
    def listar_tipos_incidencia(self): return ListarTiposIncidencia(self.uow())
    def crear_tipo_sancion(self): return CrearTipoSancion(self.uow())
    def actualizar_tipo_sancion(self): return ActualizarTipoSancion(self.uow())
    def listar_tipos_sancion(self): return ListarTiposSancion(self.uow())

    # --- estudiantes ---
    def crear_estudiante(self): return CrearEstudiante(self.uow())
    def actualizar_estudiante(self): return ActualizarEstudiante(self.uow())
    def cambiar_grupo_estudiante(self): return CambiarGrupoEstudiante(self.uow())
    def listar_estudiantes(self): return ListarEstudiantes(self.uow())
    def obtener_estudiante(self): return ObtenerEstudiante(self.uow(), self.reloj)
    def buscar_estudiantes(self): return BuscarEstudiantes(self.uow())
    def agregar_tutor_legal(self): return AgregarTutorLegal(self.uow())
    def actualizar_tutor_legal(self): return ActualizarTutorLegal(self.uow())
    def eliminar_tutor_legal(self): return EliminarTutorLegal(self.uow())
    def importar_estudiantes(self): return ImportarEstudiantes(self.uow(), self.lector_estudiantes)
    def avanzar_semestre(self): return AvanzarSemestre(self.uow())
    def grupos_tutelados(self): return GruposTutelados(self.uow())

    # --- reportes ---
    def crear_reportes(self): return CrearReportes(self.uow(), self.reloj, self.notificador)
    def listar_reportes(self): return ListarReportes(self.uow())
    def obtener_reporte(self): return ObtenerReporte(self.uow())
    def corregir_reporte(self): return CorregirReporte(self.uow(), self.reloj)
    def cambiar_gravedad(self): return CambiarGravedad(self.uow(), self.reloj, self.notificador)
    def turnar_a_subdireccion(self): return TurnarASubdireccion(self.uow(), self.reloj)
    def cancelar_reporte(self): return CancelarReporte(self.uow(), self.reloj)
    def agregar_adjunto(self): return AgregarAdjunto(self.uow(), self.almacen, self.reloj)
    def obtener_adjunto(self): return ObtenerAdjunto(self.uow(), self.almacen)

    # --- llamadas y WhatsApp ---
    def registrar_llamada(self): return RegistrarLlamada(self.uow(), self.reloj)
    def obtener_seguimiento_llamadas(self): return ObtenerSeguimientoLlamadas(self.uow(), self.reloj)
    def generar_mensaje_whatsapp(self):
        return GenerarMensajeWhatsApp(self.uow(), self.reloj, self.mensajeria, self.settings.plantel_nombre,
                                      self.settings.orientacion_contacto or None)
    def marcar_mensaje_enviado(self): return MarcarMensajeEnviado(self.uow(), self.reloj)

    # --- sanciones y alertas ---
    def aplicar_sancion_directa(self): return AplicarSancionDirecta(self.uow(), self.reloj)
    def aplicar_sancion_por_acumulacion(self): return AplicarSancionPorAcumulacion(self.uow(), self.reloj)
    def obtener_expediente(self): return ObtenerExpediente(self.uow())
    def listar_alertas(self): return ListarAlertas(self.uow())
    def contar_alertas_pendientes(self): return ContarAlertasPendientes(self.uow())
    def marcar_alerta_atendida(self): return MarcarAlertaAtendida(self.uow(), self.reloj)

    # --- exportaciones y bitácora ---
    def exportar_reportes(self):
        return ExportarReportes(self.uow(), self.reloj, self.exportador_excel, self.settings.plantel_nombre)
    def consultar_bitacora(self): return ConsultarBitacora(self.uow())

    # --- dashboard ---
    def obtener_dashboard(self): return ObtenerDashboard(self.uow(), self.reloj)
