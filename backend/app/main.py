from typing import Optional

from flask import Flask

from app.config.settings import Settings
from app.container import Container
from app.interfaces.api.blueprints import academico, auth, catalogos, dashboard, estudiantes, exportaciones, health, reportes, sanciones, usuarios
from app.interfaces.api.errors import registrar_manejadores_de_error

API_PREFIX = "/api/v1"


def create_app(settings: Optional[Settings] = None) -> Flask:
    settings = settings or Settings.desde_entorno()
    app = Flask(__name__)
    app.config["JSON_AS_ASCII"] = False
    app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # rechaza cargas desmedidas (los archivos permitidos son de hasta 5 MB)
    app.extensions["container"] = Container(settings)

    app.register_blueprint(health.bp, url_prefix=API_PREFIX)
    app.register_blueprint(auth.bp, url_prefix=f"{API_PREFIX}/auth")
    app.register_blueprint(usuarios.bp, url_prefix=API_PREFIX)
    app.register_blueprint(academico.bp, url_prefix=API_PREFIX)
    app.register_blueprint(catalogos.bp, url_prefix=API_PREFIX)
    app.register_blueprint(estudiantes.bp, url_prefix=API_PREFIX)
    app.register_blueprint(reportes.bp, url_prefix=API_PREFIX)
    app.register_blueprint(sanciones.bp, url_prefix=API_PREFIX)
    app.register_blueprint(exportaciones.bp, url_prefix=API_PREFIX)
    app.register_blueprint(dashboard.bp, url_prefix=API_PREFIX)
    registrar_manejadores_de_error(app)
    _cabeceras_de_seguridad(app, settings)
    return app


def _cabeceras_de_seguridad(app: Flask, settings: Settings) -> None:
    @app.after_request
    def _cabeceras(respuesta):
        h = respuesta.headers
        h.setdefault("X-Content-Type-Options", "nosniff")
        h.setdefault("X-Frame-Options", "DENY")
        h.setdefault("Referrer-Policy", "no-referrer")
        # La API solo sirve JSON y descargas: no debe incrustar ni cargar nada.
        h.setdefault("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
        h.setdefault("Cache-Control", "no-store")  # las descargas ya fijan su propio valor privado
        if settings.entorno == "production":
            h.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return respuesta
