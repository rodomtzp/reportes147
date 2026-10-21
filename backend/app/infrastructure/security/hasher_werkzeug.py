from werkzeug.security import check_password_hash, generate_password_hash

from app.application.ports.seguridad import HasherPuerto


class HasherWerkzeug(HasherPuerto):
    def hashear(self, password: str) -> str:
        return generate_password_hash(password, method="scrypt")

    def verificar(self, password: str, password_hash: str) -> bool:
        return check_password_hash(password_hash, password)
