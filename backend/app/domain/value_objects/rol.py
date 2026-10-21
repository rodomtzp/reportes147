from enum import Enum


class Rol(str, Enum):
    """Roles del sistema.

    El rol *Tutor* no vive aquí: se deriva de la AsignacionTutor
    (docente + grupo + periodo), que se implementa en la Fase 1.
    """

    DOCENTE = "DOCENTE"
    PREFECTO = "PREFECTO"
    ORIENTACION = "ORIENTACION"
    SUBDIRECCION = "SUBDIRECCION"
    DIRECCION = "DIRECCION"
    ADMINISTRADOR = "ADMINISTRADOR"
