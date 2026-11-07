"""Controlador de administración de usuarios (HU 4, 5) y calidad de datos (HU 8)."""
from __future__ import annotations

import re

import pandas as pd

from geih_bi.core.security import PasswordHasher
from geih_bi.models.repositories import QualityRepository, UserAlreadyExists, UserRepository
from geih_bi.models.user import Role, User

USERNAME_PATTERN = re.compile(r"^[a-z0-9_.]{3,30}$")
MIN_PASSWORD = 8


class ValidationError(Exception):
    """Error de validación con un mensaje apto para mostrar al usuario."""


class AdminController:
    def __init__(self, users: UserRepository, quality: QualityRepository, hasher: PasswordHasher) -> None:
        self._users = users
        self._quality = quality
        self._hasher = hasher

    # ------------------------------------------------------------- usuarios
    def create_user(self, username: str, nombre: str, password: str, rol: Role) -> User:
        username = (username or "").strip().lower()
        nombre = (nombre or "").strip()
        if not USERNAME_PATTERN.match(username):
            raise ValidationError("El usuario debe tener 3 a 30 caracteres: letras minúsculas, números, '.' o '_'.")
        if not nombre:
            raise ValidationError("El nombre es obligatorio.")
        if len(password or "") < MIN_PASSWORD:
            raise ValidationError(f"La contraseña debe tener al menos {MIN_PASSWORD} caracteres.")
        user = User(username=username, nombre=nombre, rol=Role(rol), password_hash=self._hasher.hash(password))
        try:
            self._users.create(user)
        except UserAlreadyExists:
            raise ValidationError(f"Ya existe un usuario '{username}'.") from None
        return user

    def list_users(self) -> list[User]:
        return self._users.list()

    def set_active(self, actor: User, username: str, activo: bool) -> None:
        if not activo and username == actor.username:
            raise ValidationError("No puede desactivar su propia cuenta.")
        target = self._users.find(username)
        if target is None:
            raise ValidationError(f"No existe el usuario '{username}'.")
        if not activo and target.rol is Role.ADMINISTRADOR and self._users.count_active_admins() <= 1:
            raise ValidationError("El sistema debe conservar al menos un administrador activo.")
        self._users.update(username, activo=activo)

    # ---------------------------------------------------- calidad de datos
    def quality_report(self) -> pd.DataFrame:
        rows = self._quality.list()
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(
            {
                "Periodo": [r["periodo"] for r in rows],
                "Archivo": [r["archivo"] for r in rows],
                "Filas entrada (características)": [r["filas_entrada"].get("caracteristicas", 0) for r in rows],
                "Duplicados": [sum(r["duplicados_eliminados"].values()) for r in rows],
                "Huérfanos": [sum(r["huerfanos"].values()) for r in rows],
                "Sin factor expansión": [r["sin_factor_expansion"] for r in rows],
                "Valores anulados": [sum(r["valores_anulados"].values()) for r in rows],
                "Filas salida": [r["filas_salida"] for r in rows],
                "TD (%)": [r["td"] for r in rows],
                "Problemas": ["; ".join(r["problemas"]) for r in rows],
            }
        )
        df["Estado"] = df["Problemas"].map(lambda p: "Con problemas" if p else "Válido")
        return df
