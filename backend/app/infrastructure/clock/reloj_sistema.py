from datetime import datetime
from zoneinfo import ZoneInfo

from app.application.ports.reloj import RelojPuerto


class RelojSistema(RelojPuerto):
    def __init__(self, zona_horaria: str):
        self._tz = ZoneInfo(zona_horaria)

    def ahora(self) -> datetime:
        return datetime.now(self._tz)

    def localizar(self, valor: datetime) -> datetime:
        return valor.replace(tzinfo=self._tz) if valor.tzinfo is None else valor.astimezone(self._tz)
