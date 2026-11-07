"""Orquestación del ETL.

Etapa 1 (``process``): zips del DANE -> Parquet en ``data/processed`` + informe JSON.
Etapa 2 (``load``):    Parquet -> MongoDB.
Separarlas permite repetir la carga sin reprocesar y probar la transformación sin MongoDB.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

import pandas as pd
from pymongo.database import Database

from geih_bi.analytics.indicators import compute_indicators
from geih_bi.etl.aggregate import build_monthly_cube
from geih_bi.etl.extract import MonthArchive, read_module_csv
from geih_bi.etl.load import MongoLoader
from geih_bi.etl.transform import transform_month
from geih_bi.etl.validate import validate_month

logger = logging.getLogger(__name__)

REPORT_FILE = "etl_report.json"


@dataclass
class MonthResult:
    archivo: str
    periodo: int
    separador: str
    columnas_faltantes: dict[str, list[str]]
    filas_entrada: dict[str, int]
    duplicados_eliminados: dict[str, int]
    huerfanos: dict[str, int]
    sin_factor_expansion: int
    valores_anulados: dict[str, int]
    filas_salida: int
    td: float | None
    to: float | None
    tgp: float | None
    problemas: list[str] = field(default_factory=list)
    segundos: float = 0.0


class ETLPipeline:
    def __init__(self, processed_dir: Path) -> None:
        self.processed_dir = processed_dir

    def fact_path(self, periodo: int) -> Path:
        return self.processed_dir / f"personas_{periodo}.parquet"

    def cube_path(self, periodo: int) -> Path:
        return self.processed_dir / f"cubo_{periodo}.parquet"

    # ---------------------------------------------------------------- etapa 1
    def process_archive(self, archive: MonthArchive) -> MonthResult:
        start = time.perf_counter()
        raw = archive.read_raw_modules()
        extracted = {module: read_module_csv(data, module) for module, data in raw.items()}
        fact, report = transform_month({m: e.frame for m, e in extracted.items()})

        periodos = fact["periodo"].dropna().unique()
        periodo = int(periodos[0]) if len(periodos) else 0
        indicators = compute_indicators(fact)
        issues = validate_month(fact, indicators.td)
        if periodo // 100 != archive.year:
            issues.append(f"el periodo {periodo} no corresponde a la carpeta {archive.year}")

        self.processed_dir.mkdir(parents=True, exist_ok=True)
        fact.to_parquet(self.fact_path(periodo), index=False)
        build_monthly_cube(fact).to_parquet(self.cube_path(periodo), index=False)

        seps = {e.separator for e in extracted.values()}
        return MonthResult(
            archivo=archive.label,
            periodo=periodo,
            separador="".join(sorted(seps)),
            columnas_faltantes={m.value: e.missing_columns for m, e in extracted.items() if e.missing_columns},
            filas_entrada=report.rows_in,
            duplicados_eliminados=report.duplicates_removed,
            huerfanos=report.orphans,
            sin_factor_expansion=report.invalid_weight_removed,
            valores_anulados=report.values_nullified,
            filas_salida=report.rows_out,
            td=indicators.td,
            to=indicators.to,
            tgp=indicators.tgp,
            problemas=issues,
            segundos=round(time.perf_counter() - start, 2),
        )

    def process(self, archives: list[MonthArchive]) -> list[MonthResult]:
        results: list[MonthResult] = []
        for archive in archives:
            result = self.process_archive(archive)
            logger.info(
                "%s -> %s: %s filas, TD=%.1f%% %s",
                archive.label, result.periodo, result.filas_salida, result.td or float("nan"),
                "OK" if not result.problemas else result.problemas,
            )
            results.append(result)

        periods = [r.periodo for r in results]
        duplicated = sorted({p for p in periods if periods.count(p) > 1})
        if duplicated:
            raise ValueError(f"Periodos repetidos entre archivos: {duplicated}")

        self.write_report(results)
        return results

    def write_report(self, results: list[MonthResult]) -> Path:
        path = self.processed_dir / REPORT_FILE
        summary = {
            "meses": len(results),
            "filas_totales": sum(r.filas_salida for r in results),
            "meses_con_problemas": [r.periodo for r in results if r.problemas],
            "detalle": [asdict(r) for r in sorted(results, key=lambda r: r.periodo)],
        }
        path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    # ---------------------------------------------------------------- etapa 2
    def processed_periods(self) -> list[int]:
        return sorted(int(p.stem.split("_")[1]) for p in self.processed_dir.glob("personas_*.parquet"))

    def load(self, db: Database) -> int:
        periods = self.processed_periods()
        if not periods:
            raise FileNotFoundError(f"No hay archivos procesados en {self.processed_dir}")
        loader = MongoLoader(db)
        loader.ensure_indexes()
        loader.load_dimensions()
        loader.load_time_dimension(periods)
        total = 0
        for periodo in periods:
            fact = pd.read_parquet(self.fact_path(periodo))
            cube = pd.read_parquet(self.cube_path(periodo))
            total += loader.load_month(fact, cube, periodo)
        loader.log_run({"periodos": periods, "documentos": total})
        return total
