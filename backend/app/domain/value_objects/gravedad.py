from enum import Enum


class Gravedad(str, Enum):
    LEVE = "LEVE"
    MEDIA = "MEDIA"
    GRAVE = "GRAVE"
    MUY_GRAVE = "MUY_GRAVE"

    @property
    def escala_a_subdireccion(self) -> bool:
        """Grave y Muy grave alertan a Subdirección sin esperar la acumulación."""
        return self in (Gravedad.GRAVE, Gravedad.MUY_GRAVE)
