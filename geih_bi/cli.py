"""Utilidades de línea de comandos.

    python -m geih_bi.cli create-user admin "Nombre Apellido" administrador
"""
from __future__ import annotations

import argparse
import getpass
import sys

from geih_bi.context import build_context
from geih_bi.controllers.admin import ValidationError
from geih_bi.models.user import Role


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m geih_bi.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create-user", help="crea un usuario (pide la contraseña)")
    create.add_argument("username")
    create.add_argument("nombre")
    create.add_argument("rol", choices=[r.value for r in Role])
    args = parser.parse_args(argv)

    password = getpass.getpass("Contraseña: ")
    if password != getpass.getpass("Repita la contraseña: "):
        print("Las contraseñas no coinciden.", file=sys.stderr)
        return 1
    try:
        user = build_context().admin.create_user(args.username, args.nombre, password, Role(args.rol))
    except ValidationError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"Usuario '{user.username}' creado con rol {user.rol.value}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
