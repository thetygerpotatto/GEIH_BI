"""Carga a MongoDB (modelo estrella: hecho ``personas_mes`` + dimensiones + cubo)."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Iterable, Iterator

import pandas as pd
import pyarrow as pa
from pymongo import ASCENDING, IndexModel
from pymongo.database import Database

from geih_bi.etl import catalogs

logger = logging.getLogger(__name__)

FACT = "personas_mes"
CUBE = "cubo_mensual"
ETL_RUNS = "etl_ejecuciones"
BATCH_SIZE = 20_000

FACT_INDEXES = [
    IndexModel([("anio", ASCENDING), ("mes", ASCENDING)]),
    IndexModel([("periodo", ASCENDING), ("dpto", ASCENDING)]),
    IndexModel([("condicion", ASCENDING), ("anio", ASCENDING)]),
    IndexModel([("sexo", ASCENDING), ("rango_edad", ASCENDING)]),
    IndexModel([("rama_seccion", ASCENDING)], sparse=True),
    IndexModel(
        [("periodo", ASCENDING), ("directorio", ASCENDING), ("secuencia_p", ASCENDING), ("orden", ASCENDING)],
        unique=True,
        name="llave_persona",
    ),
]
CUBE_INDEXES = [IndexModel([("periodo", ASCENDING), ("dpto", ASCENDING)])]


def dataframe_to_documents(df: pd.DataFrame) -> Iterator[dict]:
    """Convierte a documentos con tipos nativos de Python, omitiendo campos nulos."""
    table = pa.Table.from_pandas(df, preserve_index=False)
    for batch in table.to_batches(max_chunksize=BATCH_SIZE):
        for row in batch.to_pylist():
            yield {k: v for k, v in row.items() if v is not None}


def _chunks(docs: Iterable[dict], size: int) -> Iterator[list[dict]]:
    chunk: list[dict] = []
    for doc in docs:
        chunk.append(doc)
        if len(chunk) == size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def dimension_documents() -> dict[str, list[dict]]:
    """Documentos de las dimensiones a partir de los catálogos."""
    return {
        "dim_departamento": [{"_id": c, "nombre": n} for c, n in catalogs.DEPARTAMENTOS.items()],
        "dim_sexo": [{"_id": c, "nombre": n} for c, n in catalogs.SEXO.items()],
        "dim_clase": [{"_id": c, "nombre": n} for c, n in catalogs.CLASE.items()],
        "dim_condicion": [{"_id": c, "nombre": n} for c, n in catalogs.CONDICION.items()],
        "dim_nivel_educativo": [
            {"_id": c, "nombre": n, "grupo": g} for c, (n, g) in catalogs.NIVEL_EDUCATIVO.items()
        ],
        "dim_grupo_educativo": [{"_id": c, "nombre": n} for c, n in catalogs.GRUPO_EDUCATIVO.items()],
        "dim_posicion_ocupacional": [
            {"_id": c, "nombre": n} for c, n in catalogs.POSICION_OCUPACIONAL.items()
        ],
        "dim_rama": [{"_id": c, "nombre": n} for c, n in catalogs.RAMA_SECCION.items()],
        "dim_rango_edad": [{"_id": lbl, "desde": a, "hasta": b} for a, b, lbl in catalogs.RANGOS_EDAD],
    }


class MongoLoader:
    """Carga idempotente: recargar un mes reemplaza sus documentos, no los duplica."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def ensure_indexes(self) -> None:
        self._db[FACT].create_indexes(FACT_INDEXES)
        self._db[CUBE].create_indexes(CUBE_INDEXES)

    def load_dimensions(self) -> None:
        for name, docs in dimension_documents().items():
            self._db[name].delete_many({})
            self._db[name].insert_many(docs)

    def load_time_dimension(self, periods: Iterable[int]) -> None:
        docs = []
        for periodo in sorted(set(periods)):
            anio, mes = divmod(int(periodo), 100)
            docs.append(
                {
                    "_id": int(periodo),
                    "anio": anio,
                    "mes": mes,
                    "nombre_mes": catalogs.MESES[mes],
                    "trimestre": (mes - 1) // 3 + 1,
                    "semestre": 1 if mes <= 6 else 2,
                }
            )
        self._db["dim_tiempo"].delete_many({})
        if docs:
            self._db["dim_tiempo"].insert_many(docs)

    def load_month(self, fact: pd.DataFrame, cube: pd.DataFrame, periodo: int) -> int:
        """Reemplaza los documentos del ``periodo`` en el hecho y en el cubo."""
        self._db[FACT].delete_many({"periodo": periodo})
        inserted = 0
        for chunk in _chunks(dataframe_to_documents(fact), BATCH_SIZE):
            self._db[FACT].insert_many(chunk, ordered=False)
            inserted += len(chunk)
        self._db[CUBE].delete_many({"periodo": periodo})
        self._db[CUBE].insert_many(list(dataframe_to_documents(cube)))
        logger.info("Periodo %s: %s documentos cargados", periodo, inserted)
        return inserted

    def log_run(self, summary: dict) -> None:
        self._db[ETL_RUNS].insert_one({"fecha": datetime.now(timezone.utc), **summary})
