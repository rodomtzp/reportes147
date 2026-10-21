from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.application.ports.unidad_de_trabajo import UnidadDeTrabajo
from app.domain.exceptions import Conflicto
from app.infrastructure.persistence.repositories.academico_repositorios_sqlalchemy import (
    AsignacionTutorRepositorioSQLAlchemy,
    CarreraRepositorioSQLAlchemy,
    GrupoRepositorioSQLAlchemy,
    PeriodoRepositorioSQLAlchemy,
)
from app.infrastructure.persistence.repositories.bitacora_repositorio_sqlalchemy import BitacoraRepositorioSQLAlchemy
from app.infrastructure.persistence.repositories.catalogo_repositorios_sqlalchemy import (
    TipoIncidenciaRepositorioSQLAlchemy,
    TipoSancionRepositorioSQLAlchemy,
)
from app.infrastructure.persistence.repositories.estudiante_repositorios_sqlalchemy import (
    EstudianteRepositorioSQLAlchemy,
    InscripcionRepositorioSQLAlchemy,
    TutorLegalRepositorioSQLAlchemy,
)
from app.infrastructure.persistence.repositories.llamada_repositorios_sqlalchemy import (
    LlamadaRepositorioSQLAlchemy,
    MensajeWhatsAppRepositorioSQLAlchemy,
)
from app.infrastructure.persistence.repositories.reporte_repositorios_sqlalchemy import (
    AdjuntoRepositorioSQLAlchemy,
    HistorialReporteRepositorioSQLAlchemy,
    ReporteRepositorioSQLAlchemy,
)
from app.infrastructure.persistence.repositories.sancion_repositorios_sqlalchemy import (
    CicloRepositorioSQLAlchemy,
    NotificacionRepositorioSQLAlchemy,
    SancionRepositorioSQLAlchemy,
)
from app.infrastructure.persistence.repositories.usuario_repositorio_sqlalchemy import (
    UsuarioRepositorioSQLAlchemy,
)


class UnidadDeTrabajoSQLAlchemy(UnidadDeTrabajo):
    """Abre una sesión al entrar y la cierra al salir; lo no confirmado se descarta."""

    def __init__(self, session_factory: sessionmaker):
        self._factory = session_factory
        self._session = None

    def __enter__(self) -> "UnidadDeTrabajoSQLAlchemy":
        s = self._session = self._factory()
        self.usuarios = UsuarioRepositorioSQLAlchemy(s)
        self.carreras = CarreraRepositorioSQLAlchemy(s)
        self.grupos = GrupoRepositorioSQLAlchemy(s)
        self.periodos = PeriodoRepositorioSQLAlchemy(s)
        self.tipos_incidencia = TipoIncidenciaRepositorioSQLAlchemy(s)
        self.tipos_sancion = TipoSancionRepositorioSQLAlchemy(s)
        self.asignaciones_tutor = AsignacionTutorRepositorioSQLAlchemy(s)
        self.estudiantes = EstudianteRepositorioSQLAlchemy(s)
        self.tutores_legales = TutorLegalRepositorioSQLAlchemy(s)
        self.inscripciones = InscripcionRepositorioSQLAlchemy(s)
        self.reportes = ReporteRepositorioSQLAlchemy(s)
        self.historial_reportes = HistorialReporteRepositorioSQLAlchemy(s)
        self.adjuntos = AdjuntoRepositorioSQLAlchemy(s)
        self.llamadas = LlamadaRepositorioSQLAlchemy(s)
        self.mensajes_whatsapp = MensajeWhatsAppRepositorioSQLAlchemy(s)
        self.ciclos = CicloRepositorioSQLAlchemy(s)
        self.sanciones = SancionRepositorioSQLAlchemy(s)
        self.notificaciones = NotificacionRepositorioSQLAlchemy(s)
        self.bitacora = BitacoraRepositorioSQLAlchemy(s)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            self._session.rollback()  # no-op si ya se confirmó
        finally:
            self._session.close()
            self._session = None

    def commit(self) -> None:
        try:
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            raise Conflicto("El registro duplica o viola una restricción de datos.") from exc

    def rollback(self) -> None:
        self._session.rollback()
