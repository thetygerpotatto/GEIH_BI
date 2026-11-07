"""Hash de contraseñas con bcrypt."""
from __future__ import annotations

import bcrypt


class PasswordHasher:
    def __init__(self, rounds: int = 12) -> None:
        self._rounds = rounds
        # hash ficticio para que verificar un usuario inexistente tarde lo mismo que uno real
        self._dummy = self.hash("contraseña-inexistente")

    def hash(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt(self._rounds)).decode()

    def verify(self, password: str, hashed: str | None) -> bool:
        target = (hashed or self._dummy).encode()
        return bcrypt.checkpw(password.encode(), target) and hashed is not None
