"""Raíz de composición: construye repositorios y controladores a partir de la conexión."""
from __future__ import annotations

from dataclasses import dataclass

from pymongo.database import Database

from geih_bi.controllers.admin import AdminController
from geih_bi.controllers.auth import AuthController
from geih_bi.controllers.dashboard import DashboardController
from geih_bi.core.db import MongoConnection
from geih_bi.core.security import PasswordHasher
from geih_bi.models.repositories import (
    AccessLogRepository,
    CubeRepository,
    QualityRepository,
    UserRepository,
)


@dataclass(frozen=True)
class AppContext:
    auth: AuthController
    admin: AdminController
    dashboard: DashboardController


def build_context(db: Database | None = None, hasher: PasswordHasher | None = None) -> AppContext:
    db = db if db is not None else MongoConnection.get_instance().db
    hasher = hasher or PasswordHasher()
    users = UserRepository(db)
    return AppContext(
        auth=AuthController(users, AccessLogRepository(db), hasher),
        admin=AdminController(users, QualityRepository(db), hasher),
        dashboard=DashboardController(CubeRepository(db)),
    )
