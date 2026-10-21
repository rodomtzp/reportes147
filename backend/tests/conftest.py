import pytest

from app.config.settings import Settings
from app.main import create_app


@pytest.fixture
def app(tmp_path):
    app = create_app(Settings(database_url="sqlite://", secret_key="s" * 40, uploads_dir=str(tmp_path / "uploads")))
    from app.infrastructure.persistence.models import Base

    Base.metadata.create_all(app.extensions["container"].engine)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def crear_usuario(app):
    def _crear(correo, roles, password="una-clave-larga-123", nombre="Usuario Prueba", debe_cambiar=False):
        app.extensions["container"].crear_usuario().ejecutar(
            nombre, correo, password, roles, debe_cambiar_password=debe_cambiar
        )
        return correo, password

    return _crear


@pytest.fixture
def login(client):
    def _login(correo, password):
        return client.post("/api/v1/auth/login", json={"correo": correo, "password": password})

    return _login


@pytest.fixture
def headers_de(crear_usuario, login):
    """headers_de('ADMINISTRADOR') → encabezado Authorization de un usuario con ese rol."""
    contador = {"n": 0}

    def _headers(*roles):
        contador["n"] += 1
        correo, pwd = crear_usuario(f"u{contador['n']}@cbtis.mx", list(roles))
        token = login(correo, pwd).get_json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _headers
