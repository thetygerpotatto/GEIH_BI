"""Controlador de autenticación (HU 1)."""
from __future__ import annotations

from geih_bi.core.security import PasswordHasher
from geih_bi.models.repositories import AccessLogRepository, UserRepository
from geih_bi.models.user import User

LOGIN_ERROR = "Usuario o contraseña incorrectos"


class AuthController:
    def __init__(self, users: UserRepository, access_log: AccessLogRepository, hasher: PasswordHasher) -> None:
        self._users = users
        self._log = access_log
        self._hasher = hasher

    def login(self, username: str, password: str) -> User | None:
        """Devuelve el usuario si las credenciales son válidas y está activo; si no, None."""
        username = (username or "").strip().lower()
        user = self._users.find(username) if username else None
        valid = self._hasher.verify(password or "", user.password_hash if user else None)
        success = bool(user and user.activo and valid)
        self._log.record(username, success)
        return user if success else None
