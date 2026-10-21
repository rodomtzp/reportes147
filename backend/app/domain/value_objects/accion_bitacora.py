from enum import Enum


class AccionBitacora(str, Enum):
    EXPORTACION = "EXPORTACION"            # descarga de un Excel
    CONSULTA_CONTACTO = "CONSULTA_CONTACTO"  # vio teléfonos o direcciones en pantalla
