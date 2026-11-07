"""Entidades de usuario y roles."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class Role(str, Enum):
    ADMINISTRADOR = "administrador"
    ANALISTA = "analista"
    GERENTE = "gerente"

    @property
    def label(self) -> str:
        return self.value.capitalize()


@dataclass
class User:
    username: str
    nombre: str
    rol: Role
    password_hash: str
    activo: bool = True
    creado: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_document(self) -> dict:
        return {
            "_id": self.username,
            "nombre": self.nombre,
            "rol": self.rol.value,
            "password_hash": self.password_hash,
            "activo": self.activo,
            "creado": self.creado,
        }

    @classmethod
    def from_document(cls, doc: dict) -> "User":
        return cls(
            username=doc["_id"],
            nombre=doc["nombre"],
            rol=Role(doc["rol"]),
            password_hash=doc["password_hash"],
            activo=doc.get("activo", True),
            creado=doc.get("creado", datetime.now(timezone.utc)),
        )
