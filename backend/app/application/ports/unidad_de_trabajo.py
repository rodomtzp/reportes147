from abc import ABC, abstractmethod

from app.application.ports.repositorios import (
    AdjuntoRepositorio,
    BitacoraRepositorio,
    HistorialReporteRepositorio,
    LlamadaRepositorio,
    MensajeWhatsAppRepositorio,
    NotificacionRepositorio,
    ReporteRepositorio,
    SancionRepositorio,
    AsignacionTutorRepositorio,
    CarreraRepositorio,
    CicloRepositorio,
    EstudianteRepositorio,
    GrupoRepositorio,
    InscripcionRepositorio,
    PeriodoRepositorio,
    TipoIncidenciaRepositorio,
    TipoSancionRepositorio,
    TutorLegalRepositorio,
    UsuarioRepositorio,
)


class UnidadDeTrabajo(ABC):
    """Transacción que agrupa los repositorios de un caso de uso.

    Uso:
        with uow:
            ...usar uow.usuarios, uow.carreras...
            uow.commit()      # si no se llama, todo se descarta al salir
    """

    usuarios: UsuarioRepositorio
    carreras: CarreraRepositorio
    grupos: GrupoRepositorio
    periodos: PeriodoRepositorio
    tipos_incidencia: TipoIncidenciaRepositorio
    tipos_sancion: TipoSancionRepositorio
    asignaciones_tutor: AsignacionTutorRepositorio
    estudiantes: EstudianteRepositorio
    tutores_legales: TutorLegalRepositorio
    inscripciones: InscripcionRepositorio
    reportes: ReporteRepositorio
    historial_reportes: HistorialReporteRepositorio
    adjuntos: AdjuntoRepositorio
    llamadas: LlamadaRepositorio
    mensajes_whatsapp: MensajeWhatsAppRepositorio
    ciclos: CicloRepositorio
    sanciones: SancionRepositorio
    notificaciones: NotificacionRepositorio
    bitacora: BitacoraRepositorio

    @abstractmethod
    def __enter__(self) -> "UnidadDeTrabajo": ...

    @abstractmethod
    def __exit__(self, exc_type, exc, tb) -> None: ...

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...
