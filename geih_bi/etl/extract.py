"""Extracción: localiza los archivos mensuales de la GEIH y lee sus módulos CSV.

Heterogeneidades que se resuelven aquí:
* Cada mes viene en un .zip con nombre distinto ("Ene_2024.zip", "GEIH_Octubre_Marco_2018.zip", ...).
* En 2023 los CSV vienen dentro de un segundo .zip ("Abril/CSV.zip").
* Los nombres internos tienen tildes mal codificadas ("Caracterбsticas") y espacios no separables.
* Enero 2022 usa ',' como separador; el resto usa ';'.
* El orden y la cantidad de columnas cambian entre versiones; las columnas se seleccionan por nombre.
"""
from __future__ import annotations

import io
import logging
import re
import unicodedata
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import pandas as pd

from geih_bi.etl.schema import KEYS, MODULE_COLUMNS, Module

logger = logging.getLogger(__name__)

ENCODING = "latin-1"


def normalize_name(name: str) -> str:
    """Nombre base en minúsculas, sin tildes ni caracteres no ASCII y con espacios simples."""
    base = re.split(r"[\\/]", name)[-1]
    base = unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", base).strip().lower()


def classify_member(name: str) -> Module | None:
    """Identifica a qué módulo de la GEIH corresponde un archivo del zip (None si no interesa)."""
    base = normalize_name(name)
    if not base.endswith(".csv"):
        return None
    if base.startswith("caracter"):
        return Module.CARACTERISTICAS
    if base.startswith("fuerza"):
        return Module.FUERZA_TRABAJO
    if base.startswith("no ocupad"):
        return Module.NO_OCUPADOS
    if base.startswith("ocupados"):
        return Module.OCUPADOS
    return None


def _is_nested_csv_zip(name: str) -> bool:
    base = normalize_name(name)
    return base.endswith(".zip") and base.startswith("csv")


def detect_separator(header: str) -> str:
    return ";" if header.count(";") >= header.count(",") else ","


def _clean_column(name: str) -> str:
    return name.replace("﻿", "").replace("ï»¿", "").strip().strip('"').upper()


@dataclass(frozen=True)
class MonthArchive:
    """Un archivo .zip mensual publicado por el DANE."""

    path: Path
    year: int

    @property
    def label(self) -> str:
        return f"{self.year}/{self.path.name}"

    def _iter_csv_members(self, zf: zipfile.ZipFile) -> Iterator[tuple[Module, bytes]]:
        for info in zf.infolist():
            if _is_nested_csv_zip(info.filename):
                with zipfile.ZipFile(io.BytesIO(zf.read(info))) as inner:
                    yield from self._iter_csv_members(inner)
                continue
            module = classify_member(info.filename)
            if module is not None:
                yield module, zf.read(info)

    def read_raw_modules(self) -> dict[Module, bytes]:
        """Devuelve el contenido crudo de los 4 módulos que usa el proyecto."""
        found: dict[Module, bytes] = {}
        with zipfile.ZipFile(self.path) as zf:
            for module, raw in self._iter_csv_members(zf):
                if module in found:
                    logger.warning("%s: módulo %s duplicado, se conserva el primero", self.label, module.value)
                    continue
                found[module] = raw
        missing = set(Module) - set(found)
        if missing:
            raise FileNotFoundError(f"{self.label}: faltan módulos {sorted(m.value for m in missing)}")
        return found


def discover_archives(data_dir: Path, years: tuple[int, ...]) -> list[MonthArchive]:
    """Busca los zips originales en ``<data_dir>/<año>/zipfiles/*.zip``."""
    archives = [
        MonthArchive(path=p, year=year)
        for year in years
        for p in sorted((data_dir / str(year) / "zipfiles").glob("*.zip"))
    ]
    if not archives:
        raise FileNotFoundError(f"No se encontraron archivos .zip en {data_dir} para {years}")
    return archives


@dataclass
class ExtractedModule:
    frame: pd.DataFrame
    separator: str
    missing_columns: list[str]


def read_module_csv(raw: bytes, module: Module) -> ExtractedModule:
    """Lee solo las columnas de interés de un módulo, como texto, y completa las faltantes."""
    header = raw[: raw.find(b"\n")].decode(ENCODING)
    sep = detect_separator(header)
    wanted = KEYS + list(MODULE_COLUMNS[module])
    wanted_set = set(wanted)

    frame = pd.read_csv(
        io.BytesIO(raw),
        sep=sep,
        encoding=ENCODING,
        dtype=str,
        usecols=lambda c: _clean_column(c) in wanted_set,
        keep_default_na=True,
        na_values=["", " ", "."],
    )
    frame.columns = [_clean_column(c) for c in frame.columns]
    frame = frame.loc[:, ~frame.columns.duplicated()]

    missing = [c for c in wanted if c not in frame.columns]
    missing_keys = [k for k in KEYS if k in missing]
    if missing_keys:
        raise ValueError(f"Módulo {module.value} sin columnas llave {missing_keys}")
    for col in missing:
        frame[col] = pd.NA
    return ExtractedModule(frame=frame[wanted], separator=sep, missing_columns=missing)
