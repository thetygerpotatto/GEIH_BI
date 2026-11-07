"""Configuración centralizada de la aplicación (leída de variables de entorno)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    """Parámetros de ejecución. Se pueden sobreescribir con variables de entorno."""

    data_dir: Path
    processed_dir: Path
    mongo_uri: str
    mongo_db: str
    years: tuple[int, ...]


def _parse_years(raw: str) -> tuple[int, ...]:
    return tuple(int(y) for y in raw.replace(",", " ").split())


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        data_dir=Path(os.getenv("GEIH_DATA_DIR", PROJECT_ROOT.parent / "GEIH_DATA")),
        processed_dir=Path(os.getenv("GEIH_PROCESSED_DIR", PROJECT_ROOT / "data" / "processed")),
        mongo_uri=os.getenv("MONGO_URI", "mongodb://localhost:27017"),
        mongo_db=os.getenv("MONGO_DB", "geih_bi"),
        years=_parse_years(os.getenv("GEIH_YEARS", "2022 2023 2024 2025")),
    )
