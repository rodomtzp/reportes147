from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.exceptions import Conflicto


def flush_o_conflicto(session: Session) -> None:
    """Convierte una violación de restricción de la BD en un error de negocio (409)."""
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise Conflicto("El registro duplica o viola una restricción de datos.") from exc
