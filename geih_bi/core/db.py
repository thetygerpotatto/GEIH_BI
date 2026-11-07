"""Acceso a MongoDB mediante el patrón Singleton.

Toda la aplicación (ETL, repositorios y dashboard) comparte una única instancia
de ``MongoClient``, que internamente mantiene el pool de conexiones.
"""
from __future__ import annotations

import threading
from typing import Optional

from pymongo import MongoClient
from pymongo.database import Database

from geih_bi.core.config import get_settings


class MongoConnection:
    """Singleton thread-safe que expone la base de datos del proyecto."""

    _instance: Optional["MongoConnection"] = None
    _lock = threading.Lock()

    def __init__(self, client: MongoClient, db_name: str) -> None:
        self._client = client
        self._db = client[db_name]

    @classmethod
    def get_instance(cls, client: Optional[MongoClient] = None) -> "MongoConnection":
        """Devuelve la instancia única; ``client`` permite inyectar un mock en pruebas."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    settings = get_settings()
                    client = client or MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=5000)
                    cls._instance = cls(client, settings.mongo_db)
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Cierra y descarta la instancia (usado en pruebas)."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance._client.close()
            cls._instance = None

    @property
    def db(self) -> Database:
        return self._db

    def ping(self) -> bool:
        self._client.admin.command("ping")
        return True
