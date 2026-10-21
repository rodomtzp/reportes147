from app.application.ports.repositorios.adjunto_repositorio import AdjuntoRepositorio
from app.application.ports.repositorios.asignacion_tutor_repositorio import AsignacionTutorRepositorio
from app.application.ports.repositorios.bitacora_repositorio import BitacoraRepositorio
from app.application.ports.repositorios.carrera_repositorio import CarreraRepositorio
from app.application.ports.repositorios.ciclo_repositorio import CicloRepositorio
from app.application.ports.repositorios.estudiante_repositorio import EstudianteRepositorio
from app.application.ports.repositorios.grupo_repositorio import GrupoRepositorio
from app.application.ports.repositorios.historial_reporte_repositorio import HistorialReporteRepositorio
from app.application.ports.repositorios.inscripcion_repositorio import InscripcionRepositorio
from app.application.ports.repositorios.notificacion_repositorio import NotificacionRepositorio
from app.application.ports.repositorios.periodo_repositorio import PeriodoRepositorio
from app.application.ports.repositorios.sancion_repositorio import SancionRepositorio
from app.application.ports.repositorios.llamada_repositorio import LlamadaRepositorio
from app.application.ports.repositorios.mensaje_whatsapp_repositorio import MensajeWhatsAppRepositorio
from app.application.ports.repositorios.reporte_repositorio import ReporteRepositorio
from app.application.ports.repositorios.tipo_incidencia_repositorio import TipoIncidenciaRepositorio
from app.application.ports.repositorios.tipo_sancion_repositorio import TipoSancionRepositorio
from app.application.ports.repositorios.tutor_legal_repositorio import TutorLegalRepositorio
from app.application.ports.repositorios.usuario_repositorio import UsuarioRepositorio

__all__ = [
    "AsignacionTutorRepositorio", "CarreraRepositorio", "GrupoRepositorio", "PeriodoRepositorio",
    "TipoIncidenciaRepositorio", "TipoSancionRepositorio", "UsuarioRepositorio",
    "EstudianteRepositorio", "InscripcionRepositorio", "TutorLegalRepositorio",
    "AdjuntoRepositorio", "HistorialReporteRepositorio", "ReporteRepositorio",
    "LlamadaRepositorio", "MensajeWhatsAppRepositorio", "CicloRepositorio", "SancionRepositorio",
    "NotificacionRepositorio", "BitacoraRepositorio",
]
