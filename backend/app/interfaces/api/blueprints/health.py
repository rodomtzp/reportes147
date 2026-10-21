from flask import Blueprint, jsonify
from sqlalchemy import text

from app.interfaces.api.helpers import contenedor

bp = Blueprint("health", __name__)


@bp.get("/health")
def health():
    with contenedor().engine.connect() as conexion:
        conexion.execute(text("SELECT 1"))
    return jsonify(estado="ok")
