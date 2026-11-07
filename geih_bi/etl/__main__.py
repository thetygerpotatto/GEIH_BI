"""CLI del ETL.

    python -m geih_bi.etl process [--years 2022 2023]   # zips -> parquet + informe
    python -m geih_bi.etl load                           # parquet -> MongoDB
    python -m geih_bi.etl run                            # ambas etapas
"""
from __future__ import annotations

import argparse
import logging
import sys

from geih_bi.core.config import get_settings
from geih_bi.core.db import MongoConnection
from geih_bi.etl.extract import discover_archives
from geih_bi.etl.pipeline import ETLPipeline


def main(argv: list[str] | None = None) -> int:
    settings = get_settings()
    parser = argparse.ArgumentParser(prog="python -m geih_bi.etl", description="ETL GEIH -> MongoDB")
    parser.add_argument("stage", choices=["process", "load", "run"])
    parser.add_argument("--years", type=int, nargs="+", default=list(settings.years))
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    pipeline = ETLPipeline(settings.processed_dir)

    if args.stage in ("process", "run"):
        results = pipeline.process(discover_archives(settings.data_dir, tuple(args.years)))
        total = sum(r.filas_salida for r in results)
        logging.info("Procesados %s meses, %s filas. Informe en %s", len(results), f"{total:,}", settings.processed_dir)
    if args.stage in ("load", "run"):
        connection = MongoConnection.get_instance()
        connection.ping()
        total = pipeline.load(connection.db)
        logging.info("Cargados %s documentos en MongoDB (%s)", f"{total:,}", settings.mongo_db)
    return 0


if __name__ == "__main__":
    sys.exit(main())
