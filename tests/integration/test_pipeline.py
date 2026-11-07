"""Integración ETL completo: zip -> parquet -> MongoDB (mongomock)."""
import json

import pytest

from geih_bi.core.db import MongoConnection
from geih_bi.etl.extract import discover_archives
from geih_bi.etl.load import CUBE, FACT, MongoLoader
from geih_bi.etl.pipeline import REPORT_FILE, ETLPipeline
from tests.conftest import build_month_zip


@pytest.fixture
def data_dir(tmp_path):
    (tmp_path / "2025" / "zipfiles").mkdir(parents=True)
    build_month_zip(tmp_path / "2025" / "zipfiles" / "Enero 2025.zip")
    return tmp_path


@pytest.fixture
def pipeline(tmp_path):
    return ETLPipeline(tmp_path / "processed")


def test_process_writes_parquet_and_report(data_dir, pipeline):
    results = pipeline.process(discover_archives(data_dir, (2025,)))
    assert [r.periodo for r in results] == [202501]
    # el hogar sintético tiene TD = 33 %, la regla de plausibilidad debe advertirlo
    assert results[0].problemas == ["TD fuera de rango plausible: 33.33%"]
    assert pipeline.fact_path(202501).exists()
    report = json.loads((pipeline.processed_dir / REPORT_FILE).read_text(encoding="utf-8"))
    assert report["filas_totales"] == 5


def test_duplicated_period_is_rejected(data_dir, pipeline):
    build_month_zip(data_dir / "2025" / "zipfiles" / "Enero 2025 (copia).zip", nested=True)
    with pytest.raises(ValueError, match="repetidos"):
        pipeline.process(discover_archives(data_dir, (2025,)))


def test_load_is_idempotent(data_dir, pipeline, mongo_db):
    pipeline.process(discover_archives(data_dir, (2025,)))
    assert pipeline.load(mongo_db) == 5
    assert pipeline.load(mongo_db) == 5
    assert mongo_db[FACT].count_documents({}) == 5
    assert mongo_db[FACT].count_documents({"condicion": "ocupado"}) == 2
    assert mongo_db["dim_tiempo"].find_one({"_id": 202501})["nombre_mes"] == "Enero"
    assert mongo_db["dim_departamento"].find_one({"_id": "76"})["nombre"] == "Valle del Cauca"
    assert mongo_db["etl_ejecuciones"].count_documents({}) == 2


def test_documents_omit_nulls(data_dir, pipeline, mongo_db):
    pipeline.process(discover_archives(data_dir, (2025,)))
    pipeline.load(mongo_db)
    nino = mongo_db[FACT].find_one({"orden": 5})
    assert "ingreso_laboral" not in nino
    assert nino["condicion"] == "fuera_pet"


def test_cube_sums_match_fact(data_dir, pipeline, mongo_db):
    pipeline.process(discover_archives(data_dir, (2025,)))
    pipeline.load(mongo_db)
    cube_ft = sum(d["w_ft"] for d in mongo_db[CUBE].find())
    assert cube_ft == pytest.approx(3 * 1000.5)


def test_load_without_processed_files_fails(pipeline, mongo_db):
    with pytest.raises(FileNotFoundError):
        pipeline.load(mongo_db)


def test_mongo_connection_is_singleton(mongo_db):
    import mongomock

    MongoConnection.reset()
    try:
        first = MongoConnection.get_instance(client=mongomock.MongoClient())
        second = MongoConnection.get_instance()
        assert first is second
    finally:
        MongoConnection.reset()


def test_loader_creates_unique_person_index(mongo_db):
    MongoLoader(mongo_db).ensure_indexes()
    assert "llave_persona" in mongo_db[FACT].index_information()
