from pathlib import Path

import pytest

from geih_bi.etl.extract import (
    MonthArchive,
    classify_member,
    detect_separator,
    discover_archives,
    normalize_name,
    read_module_csv,
)
from geih_bi.etl.schema import Module
from tests.conftest import FT_HEADER, FT_ROWS, build_month_zip, csv_bytes


@pytest.mark.parametrize(
    "name, expected",
    [
        ("GEIH_Enero_2022_Marco_2018/CSV/Caracterбsticas generales, seguridad social en salud y educaciвn.csv",
         Module.CARACTERISTICAS),
        ("CSV/Características generales, seguridad social en salud y educación.CSV", Module.CARACTERISTICAS),
        ("CSV/Fuerza de trabajo.CSV", Module.FUERZA_TRABAJO),
        ("Ocupados.CSV", Module.OCUPADOS),
        ("CVS/No ocupados.CSV", Module.NO_OCUPADOS),
        ("No ocupado.CSV", Module.NO_OCUPADOS),
        ("DTA/Ocupados.DTA", None),
        ("CSV/Migración.CSV", None),
        ("CSV/Datos del hogar y la vivienda.CSV", None),
    ],
)
def test_classify_member(name, expected):
    assert classify_member(name) == expected


def test_normalize_name_removes_accents_and_nbsp():
    assert normalize_name("a/b/Fuerza de  trabajo.CSV") == "fuerza de trabajo.csv"


@pytest.mark.parametrize("header, sep", [("A;B;C", ";"), ("A,B,C", ","), ("A", ";")])
def test_detect_separator(header, sep):
    assert detect_separator(header) == sep


@pytest.mark.parametrize("sep", [";", ","])
def test_read_module_csv_handles_both_separators(sep):
    result = read_module_csv(csv_bytes(FT_HEADER, FT_ROWS, sep), Module.FUERZA_TRABAJO)
    assert result.separator == sep
    assert len(result.frame) == len(FT_ROWS)
    assert result.missing_columns == []


def test_read_module_csv_fills_missing_columns_and_strips_bom():
    data = "﻿DIRECTORIO;SECUENCIA_P;ORDEN;PET\n1;1;1;1\n".encode("utf-8")
    result = read_module_csv(data, Module.FUERZA_TRABAJO)
    assert "DIRECTORIO" in result.frame.columns
    assert set(result.missing_columns) == {"FT", "FFT", "P6240"}
    assert result.frame["FT"].isna().all()


def test_read_module_csv_without_keys_fails():
    with pytest.raises(ValueError, match="llave"):
        read_module_csv(b"PET;FT\n1;1\n", Module.FUERZA_TRABAJO)


@pytest.mark.parametrize("nested", [False, True])
def test_archive_reads_four_modules(tmp_path, nested):
    archive = MonthArchive(build_month_zip(tmp_path / "m.zip", nested=nested), 2025)
    assert set(archive.read_raw_modules()) == set(Module)


def test_archive_missing_module_raises(tmp_path):
    import zipfile

    path = tmp_path / "incompleto.zip"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("CSV/Ocupados.CSV", b"DIRECTORIO;SECUENCIA_P;ORDEN\n")
    with pytest.raises(FileNotFoundError, match="faltan"):
        MonthArchive(path, 2025).read_raw_modules()


def test_discover_archives(tmp_path: Path):
    (tmp_path / "2025" / "zipfiles").mkdir(parents=True)
    build_month_zip(tmp_path / "2025" / "zipfiles" / "Enero 2025.zip")
    archives = discover_archives(tmp_path, (2025,))
    assert [a.year for a in archives] == [2025]
    with pytest.raises(FileNotFoundError):
        discover_archives(tmp_path, (2019,))
