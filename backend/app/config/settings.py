import os
from dataclasses import dataclass


def _normalizar_url_bd(url: str) -> str:
    """Los proveedores en la nube entregan postgres:// o postgresql://; SQLAlchemy necesita el driver psycopg."""
    for prefijo in ("postgres://", "postgresql://"):
        if url.startswith(prefijo):
            return "postgresql+psycopg://" + url[len(prefijo):]
    return url


@dataclass(frozen=True)
class Settings:
    database_url: str
    secret_key: str
    access_minutos: int = 15
    refresh_horas: int = 8
    entorno: str = "development"
    uploads_dir: str = "uploads"
    zona_horaria: str = "America/Mexico_City"
    plantel_nombre: str = "CBTis 147"
    whatsapp_codigo_pais: str = "52"
    smtp_host: str = ""  # vacío = sin correo (las alertas quedan solo en la bandeja)
    smtp_puerto: int = 587
    smtp_usuario: str = ""
    smtp_password: str = ""
    smtp_remitente: str = ""
    smtp_starttls: bool = True
    app_url: str = "http://localhost:5173"  # para los enlaces de los correos
    orientacion_contacto: str = ""  # texto opcional al final del mensaje (teléfono, horario)

    @classmethod
    def desde_entorno(cls) -> "Settings":
        entorno = os.getenv("APP_ENV", "development")
        secret = os.getenv("SECRET_KEY", "")
        if entorno == "production" and len(secret) < 32:
            raise RuntimeError("SECRET_KEY debe tener al menos 32 caracteres en producción.")
        if entorno == "production" and ("cambia" in secret.lower() or "desarrollo" in secret.lower()):
            raise RuntimeError("SECRET_KEY parece la clave de ejemplo. Genera una aleatoria (ver .env.example).")
        if not secret:
            secret = "clave-solo-para-desarrollo-cambiala-0123456789"
        return cls(
            database_url=_normalizar_url_bd(
                os.getenv("DATABASE_URL", "postgresql+psycopg://reportes:reportes@localhost:5432/reportes")
            ),
            secret_key=secret,
            access_minutos=int(os.getenv("ACCESS_TOKEN_MINUTOS", "15")),
            refresh_horas=int(os.getenv("REFRESH_TOKEN_HORAS", "8")),
            entorno=entorno,
            uploads_dir=os.getenv("UPLOADS_DIR", "uploads"),
            zona_horaria=os.getenv("APP_TIMEZONE", "America/Mexico_City"),
            plantel_nombre=os.getenv("PLANTEL_NOMBRE", "CBTis 147"),
            whatsapp_codigo_pais=os.getenv("WHATSAPP_CODIGO_PAIS", "52"),
            orientacion_contacto=os.getenv("ORIENTACION_CONTACTO", ""),
            smtp_host=os.getenv("SMTP_HOST", ""),
            smtp_puerto=int(os.getenv("SMTP_PORT", "587")),
            smtp_usuario=os.getenv("SMTP_USER", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            smtp_remitente=os.getenv("SMTP_FROM", ""),
            smtp_starttls=os.getenv("SMTP_STARTTLS", "true").lower() != "false",
            app_url=os.getenv("APP_URL", "http://localhost:5173"),
        )
