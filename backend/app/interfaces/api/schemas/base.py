from pydantic import BaseModel, ConfigDict


class EsquemaBase(BaseModel):
    """Entrada estricta: rechaza campos desconocidos y recorta espacios."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
