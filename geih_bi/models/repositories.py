"""Repositorios: único punto de acceso a las colecciones de MongoDB."""
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from geih_bi.models.user import Role, User

USERS = "usuarios"
ACCESS_LOG = "bitacora_accesos"
CUBE = "cubo_mensual"
QUALITY = "etl_calidad"

CUBE_MEASURES = [
    "n", "w_pob", "w_pet", "w_ft", "w_oci", "w_dsi", "w_fft",
    "w_ingreso", "w_ingreso_n", "w_horas", "w_horas_n",
    "w_informal", "w_informal_n", "w_semanas", "w_semanas_n",
]


class UserAlreadyExists(Exception):
    pass


class UserRepository:
    def __init__(self, db: Database) -> None:
        self._col = db[USERS]

    def find(self, username: str) -> User | None:
        doc = self._col.find_one({"_id": username})
        return User.from_document(doc) if doc else None

    def list(self) -> list[User]:
        return [User.from_document(d) for d in self._col.find().sort("_id", 1)]

    def create(self, user: User) -> None:
        try:
            self._col.insert_one(user.to_document())
        except DuplicateKeyError as exc:
            raise UserAlreadyExists(user.username) from exc

    def update(self, username: str, *, rol: Role | None = None, activo: bool | None = None) -> None:
        changes: dict = {}
        if rol is not None:
            changes["rol"] = rol.value
        if activo is not None:
            changes["activo"] = activo
        if changes:
            self._col.update_one({"_id": username}, {"$set": changes})

    def count_active_admins(self) -> int:
        return self._col.count_documents({"rol": Role.ADMINISTRADOR.value, "activo": True})


class AccessLogRepository:
    def __init__(self, db: Database) -> None:
        self._col = db[ACCESS_LOG]

    def record(self, username: str, success: bool) -> None:
        self._col.insert_one({"usuario": username, "exitoso": success, "fecha": datetime.now(timezone.utc)})

    def recent(self, limit: int = 100) -> list[dict]:
        return list(self._col.find({}, {"_id": 0}).sort("fecha", -1).limit(limit))


class CubeRepository:
    """Consultas agregadas sobre ``cubo_mensual``."""

    def __init__(self, db: Database) -> None:
        self._col = db[CUBE]

    def aggregate(self, match: dict, group_by: list[str]) -> pd.DataFrame:
        group_id = {field: f"${field}" for field in group_by} if group_by else None
        pipeline = [
            {"$match": match},
            {"$group": {"_id": group_id, **{m: {"$sum": f"${m}"} for m in CUBE_MEASURES}}},
        ]
        rows = list(self._col.aggregate(pipeline))
        if not rows:
            return pd.DataFrame(columns=group_by + CUBE_MEASURES)
        records = [{**(row["_id"] or {}), **{m: row[m] for m in CUBE_MEASURES}} for row in rows]
        return pd.DataFrame.from_records(records, columns=group_by + CUBE_MEASURES)

    def available_periods(self) -> list[int]:
        return sorted(self._col.distinct("periodo"))


class QualityRepository:
    def __init__(self, db: Database) -> None:
        self._col = db[QUALITY]

    def replace_all(self, rows: list[dict]) -> None:
        self._col.delete_many({})
        if rows:
            self._col.insert_many([{"_id": r["periodo"], **r} for r in rows])

    def list(self) -> list[dict]:
        return list(self._col.find({}, {"_id": 0}).sort("periodo", 1))
