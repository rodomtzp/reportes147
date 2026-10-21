from flask import Flask, jsonify
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException

from app.domain.exceptions import (
    CambioDePasswordRequerido,
    Conflicto,
    CuentaBloqueada,
    NoAutenticado,
    NoEncontrado,
    PermisoDenegado,
    ReglaDeNegocioViolada,
)


def registrar_manejadores_de_error(app: Flask) -> None:
    def _resp(status: int, mensaje: str, **extra):
        return jsonify(error=mensaje, **extra), status

    @app.errorhandler(CuentaBloqueada)
    def _bloqueada(e):
        return _resp(429, str(e), codigo="CUENTA_BLOQUEADA")

    @app.errorhandler(NoAutenticado)  # incluye CredencialesInvalidas
    def _no_autenticado(e):
        return _resp(401, str(e))

    @app.errorhandler(CambioDePasswordRequerido)
    def _password_pendiente(e):
        return _resp(403, str(e), codigo="CAMBIO_PASSWORD_REQUERIDO")

    @app.errorhandler(PermisoDenegado)
    def _denegado(e):
        return _resp(403, str(e))

    @app.errorhandler(NoEncontrado)
    def _no_encontrado_dominio(e):
        return _resp(404, str(e))

    @app.errorhandler(Conflicto)
    def _conflicto(e):
        return _resp(409, str(e))

    @app.errorhandler(ReglaDeNegocioViolada)
    def _regla(e):
        return _resp(422, str(e))

    @app.errorhandler(ValidationError)
    def _validacion(e: ValidationError):
        detalle = [
            {"campo": ".".join(str(x) for x in err["loc"]), "mensaje": err["msg"]}
            for err in e.errors()
        ]
        primero = detalle[0] if detalle else {"campo": "", "mensaje": "Datos inválidos."}
        mensaje = f"{primero['campo']}: {primero['mensaje']}" if primero["campo"] else primero["mensaje"]
        return _resp(422, mensaje, detalle=detalle)

    @app.errorhandler(404)
    def _no_encontrado(e):
        return _resp(404, "Recurso no encontrado.")

    @app.errorhandler(Exception)
    def _inesperado(e):
        if isinstance(e, HTTPException):
            return _resp(e.code or 500, e.description)
        app.logger.exception("Error no controlado")
        return _resp(500, "Error interno del servidor.")
