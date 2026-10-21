from datetime import datetime, timedelta, timezone

import jwt

from app.application.ports.seguridad import ClaimsToken, TokenPuerto
from app.domain.exceptions import NoAutenticado


class TokenJWT(TokenPuerto):
    ALGORITMO = "HS256"

    def __init__(self, secret_key: str, access_minutos: int, refresh_horas: int):
        self._secret = secret_key
        self._access = timedelta(minutes=access_minutos)
        self._refresh = timedelta(hours=refresh_horas)

    def _emitir(self, usuario_id: int, tipo: str, duracion: timedelta, version: int, extra: dict = None) -> str:
        ahora = datetime.now(timezone.utc)
        payload = {"sub": str(usuario_id), "tipo": tipo, "iat": ahora, "exp": ahora + duracion, "sv": version}
        payload.update(extra or {})
        return jwt.encode(payload, self._secret, algorithm=self.ALGORITMO)

    def emitir_access(self, usuario_id: int, roles: list, version: int = 0) -> str:
        return self._emitir(usuario_id, "access", self._access, version, {"roles": roles})

    def emitir_refresh(self, usuario_id: int, version: int = 0) -> str:
        return self._emitir(usuario_id, "refresh", self._refresh, version)

    def decodificar(self, token: str) -> ClaimsToken:
        try:
            datos = jwt.decode(
                token, self._secret, algorithms=[self.ALGORITMO],
                options={"require": ["exp", "sub", "tipo"]},
            )
            return ClaimsToken(usuario_id=int(datos["sub"]), tipo=datos["tipo"], version=int(datos.get("sv", 0)))
        except (jwt.PyJWTError, ValueError) as exc:
            raise NoAutenticado("Token inválido o expirado.") from exc
