"""Fixtures compartidas: un zip GEIH sintético que reproduce las heterogeneidades reales."""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import mongomock
import pytest

CARAC_HEADER = ["PERIODO", "MES", "PER", "DIRECTORIO", "SECUENCIA_P", "ORDEN", "HOGAR", "FEX_C18",
                "DPTO", "AREA", "CLASE", "P3271", "P6040", "P3042", "P6090", "P6100"]
FT_HEADER = ["DIRECTORIO", "SECUENCIA_P", "ORDEN", "PET", "FT", "FFT", "P6240"]
OCU_HEADER = ["DIRECTORIO", "SECUENCIA_P", "ORDEN", "OCI", "INGLABO", "P6800", "P6430", "RAMA2D_R4",
              "P6920", "P3069", "P6440"]
NOC_HEADER = ["DIRECTORIO", "SECUENCIA_P", "ORDEN", "DSI", "FFT", "P7250"]

# 5 personas del mismo hogar: ocupado, ocupada informal, desocupado, inactiva, niño
CARAC_ROWS = [
    ["20250105", "01", "2025", "1", "1", "1", "1", "1000.5", "76", "76", "1", "1", "35", "10", "1", "1"],
    ["20250105", "01", "2025", "1", "1", "2", "1", "1000.5", "76", "76", "1", "2", "30", "5", "1", "3"],
    ["20250105", "01", "2025", "1", "1", "3", "1", "1000.5", "76", "76", "1", "1", "20", "5", "1", "3"],
    ["20250105", "01", "2025", "1", "1", "4", "1", "1000.5", "76", "76", "1", "2", "65", "3", "1", "2"],
    ["20250105", "01", "2025", "1", "1", "5", "1", "1000.5", "76", "76", "1", "1", "8", "", "1", "3"],
]
FT_ROWS = [
    ["1", "1", "1", "1", "1", "", "1"],
    ["1", "1", "2", "1", "1", "", "1"],
    ["1", "1", "3", "1", "1", "", "2"],
    ["1", "1", "4", "1", "", "1", "4"],
]
OCU_ROWS = [
    ["1", "1", "1", "1", "3000000", "48", "1", "62", "1", "5", "1"],
    ["1", "1", "2", "1", "900000", "30", "4", "47", "2", "1", ""],
]
NOC_ROWS = [
    ["1", "1", "3", "1", "", "12"],
    ["1", "1", "4", "", "1", ""],
]


def csv_bytes(header: list[str], rows: list[list[str]], sep: str = ";") -> bytes:
    lines = [sep.join(header)] + [sep.join(r) for r in rows]
    return ("\r\n".join(lines) + "\r\n").encode("latin-1")


def build_month_zip(path: Path, sep: str = ";", nested: bool = False) -> Path:
    """Crea un zip mensual; ``nested`` imita 2023 (CSV dentro de otro zip)."""
    members = {
        "Caracterбsticas generales, seguridad social en salud y educaciвn.CSV":
            csv_bytes(CARAC_HEADER, CARAC_ROWS, sep),
        "Fuerza de trabajo.CSV": csv_bytes(FT_HEADER, FT_ROWS, sep),
        "Ocupados.CSV": csv_bytes(OCU_HEADER, OCU_ROWS, sep),
        "No ocupados.CSV": csv_bytes(NOC_HEADER, NOC_ROWS, sep),
    }
    with zipfile.ZipFile(path, "w") as outer:
        if nested:
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w") as inner:
                for name, data in members.items():
                    inner.writestr(f"CVS/{name}", data)
            outer.writestr("Enero/CSV.zip", buffer.getvalue())
            outer.writestr("Enero/DTA 9.zip", b"ignored")
        else:
            for name, data in members.items():
                outer.writestr(f"CSV/{name}", data)
            outer.writestr("DTA/Ocupados.DTA", b"ignored")
    return path


@pytest.fixture
def month_zip(tmp_path: Path) -> Path:
    return build_month_zip(tmp_path / "Enero 2025.zip")


@pytest.fixture
def mongo_db():
    return mongomock.MongoClient()["geih_test"]


# ---------------------------------------------------------------- capa de aplicación
from geih_bi.core.security import PasswordHasher  # noqa: E402
from geih_bi.models.repositories import CUBE_MEASURES  # noqa: E402


def cube_doc(periodo, dpto="76", sexo=1, rango_edad="29-44", clase=1, grupo="media",
             n=100, pet=1000.0, ft=600.0, oci=540.0, dsi=60.0, fft=400.0):
    doc = {m: 0.0 for m in CUBE_MEASURES}
    doc.update({
        "anio": periodo // 100, "mes": periodo % 100, "periodo": periodo, "dpto": dpto, "clase": clase,
        "sexo": sexo, "rango_edad": rango_edad, "grupo_educativo": grupo,
        "n": n, "w_pob": pet, "w_pet": pet, "w_ft": ft, "w_oci": oci, "w_dsi": dsi, "w_fft": fft,
    })
    return doc


@pytest.fixture(scope="session")
def fast_hasher():
    return PasswordHasher(rounds=4)


@pytest.fixture
def seeded_db(mongo_db):
    """Cubo sintético: 2024-01 y 2025-01 en Valle y Bogotá, hombres y mujeres."""
    docs = [
        cube_doc(202401, "76", 1, dsi=60.0),               # TD 10 %
        cube_doc(202401, "76", 2, dsi=90.0, oci=510.0),     # TD 15 %
        cube_doc(202501, "76", 1, dsi=48.0, oci=552.0),     # TD 8 %
        cube_doc(202501, "76", 2, dsi=72.0, oci=528.0),     # TD 12 %
        cube_doc(202501, "11", 1, n=20, dsi=30.0, oci=570.0),  # muestra pequeña
        cube_doc(202501, "76", 1, rango_edad="0-14", n=50, pet=0.0, ft=0.0, oci=0.0, dsi=0.0, fft=0.0),
    ]
    mongo_db["cubo_mensual"].insert_many(docs)
    return mongo_db
