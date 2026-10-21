"""Comandos de administración. Uso:

    python -m app.cli crear-usuario --nombre "Ana" --correo ana@cbtis147.edu.mx --roles ADMINISTRADOR
"""
import argparse
import getpass
import sys

from app.config.settings import Settings
from app.container import Container
from app.domain.exceptions import ErrorDominio
from app.domain.value_objects.rol import Rol


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="comando", required=True)
    cu = sub.add_parser("crear-usuario", help="Crea un usuario (útil para el primer administrador)")
    cu.add_argument("--nombre", required=True)
    cu.add_argument("--correo", required=True)
    cu.add_argument("--roles", required=True, nargs="+", choices=[r.value for r in Rol])
    cu.add_argument("--password", help="Si se omite, se pide de forma interactiva")
    args = parser.parse_args(argv)

    password = args.password or getpass.getpass("Contraseña: ")
    container = Container(Settings.desde_entorno())
    try:
        usuario = container.crear_usuario().ejecutar(args.nombre, args.correo, password, args.roles)
        print(f"Usuario creado: {usuario.correo} ({', '.join(sorted(r.value for r in usuario.roles))})")
        return 0
    except ErrorDominio as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
