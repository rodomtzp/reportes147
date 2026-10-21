from app.infrastructure.persistence.models.base import Base  # noqa: F401
from app.infrastructure.persistence.models.usuario_model import (  # noqa: F401
    UsuarioModel,
    UsuarioRolModel,
)
from app.infrastructure.persistence.models.academico_models import (  # noqa: F401
    AsignacionTutorModel,
    CarreraModel,
    GrupoModel,
    PeriodoEscolarModel,
)
from app.infrastructure.persistence.models.catalogo_models import (  # noqa: F401
    TipoIncidenciaModel,
    TipoSancionModel,
)
from app.infrastructure.persistence.models.estudiante_models import (  # noqa: F401
    EstudianteModel,
    InscripcionModel,
    TutorLegalModel,
)
from app.infrastructure.persistence.models.reporte_models import (  # noqa: F401
    AdjuntoModel,
    FolioContadorModel,
    HistorialReporteModel,
    ReporteModel,
)
from app.infrastructure.persistence.models.llamada_models import (  # noqa: F401
    IntentoLlamadaModel,
    MensajeWhatsAppModel,
)
from app.infrastructure.persistence.models.sancion_models import (  # noqa: F401
    CicloAcumulacionModel,
    NotificacionModel,
    SancionModel,
)
from app.infrastructure.persistence.models.bitacora_models import BitacoraModel  # noqa: F401
