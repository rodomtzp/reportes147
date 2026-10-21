from pydantic import Field

from app.interfaces.api.schemas.base import EsquemaBase


class LoginIn(EsquemaBase):
    correo: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=200)


class RefreshIn(EsquemaBase):
    refresh_token: str = Field(min_length=1)


class CambiarPasswordIn(EsquemaBase):
    password_actual: str = Field(min_length=1, max_length=200)
    password_nueva: str = Field(min_length=1, max_length=200)
