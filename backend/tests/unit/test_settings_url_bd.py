from app.config.settings import _normalizar_url_bd


def test_normaliza_urls_de_proveedores_en_la_nube():
    assert _normalizar_url_bd("postgres://u:p@h:5432/d") == "postgresql+psycopg://u:p@h:5432/d"
    assert _normalizar_url_bd("postgresql://u:p@h/d") == "postgresql+psycopg://u:p@h/d"


def test_respeta_url_con_driver():
    assert _normalizar_url_bd("postgresql+psycopg://u:p@h/d") == "postgresql+psycopg://u:p@h/d"
