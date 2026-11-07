import pandas as pd
import pytest

from geih_bi.etl.extract import MonthArchive, read_module_csv
from geih_bi.etl.schema import FACT_FIELDS
from geih_bi.etl.transform import (
    TransformReport,
    clean,
    informalidad,
    rango_edad,
    transform_month,
)


@pytest.fixture
def fact(month_zip):
    raw = MonthArchive(month_zip, 2025).read_raw_modules()
    frames = {m: read_module_csv(data, m).frame for m, data in raw.items()}
    df, report = transform_month(frames)
    return df.set_index("orden"), report


def test_output_has_fact_schema(fact):
    df, report = fact
    assert set(df.reset_index().columns) == set(FACT_FIELDS)
    assert report.rows_out == 5


def test_persons_without_labor_module_are_kept(fact):
    df, report = fact
    assert report.orphans == {"fuerza_trabajo": 0, "ocupados": 0, "no_ocupados": 0}
    assert df.loc[5, "condicion"] == "fuera_pet"


def test_condicion_laboral(fact):
    df, _ = fact
    assert df["condicion"].to_dict() == {
        1: "ocupado", 2: "ocupado", 3: "desocupado", 4: "inactivo", 5: "fuera_pet",
    }


def test_types_and_keys(fact):
    df, _ = fact
    assert df.loc[1, "periodo"] == 202501
    assert df.loc[1, "mes"] == 1  # "01" -> 1
    assert df.loc[1, "dpto"] == "76"
    assert df.loc[1, "fex"] == pytest.approx(1000.5)


def test_derived_fields(fact):
    df, _ = fact
    assert df.loc[1, "grupo_educativo"] == "universitaria"
    assert df.loc[1, "rama_seccion"] == "J"  # división 62
    assert df.loc[2, "rama_seccion"] == "G"  # división 47
    assert df.loc[3, "rango_edad"] == "15-28"
    assert df.loc[4, "rango_edad"] == "60+"
    assert df.loc[5, "rango_edad"] == "0-14"


def test_informalidad_proxy(fact):
    df, _ = fact
    assert df.loc[1, "informal"] == 0
    assert df.loc[2, "informal"] == 1
    assert pd.isna(df.loc[3, "informal"])  # desocupado: no aplica


@pytest.mark.parametrize("edad, esperado", [(0, "0-14"), (14, "0-14"), (15, "15-28"), (28, "15-28"),
                                            (29, "29-44"), (59, "45-59"), (60, "60+"), (110, "60+")])
def test_rango_edad_limites(edad, esperado):
    assert rango_edad(pd.Series([edad], dtype="Int64")).iloc[0] == esperado


def test_rango_edad_nulo():
    assert pd.isna(rango_edad(pd.Series([pd.NA], dtype="Int64")).iloc[0])


def test_informalidad_pensionado_es_formal():
    df = pd.DataFrame({"oci": [1, 1, 0], "cotiza_pension": [3, pd.NA, 2]}, dtype="Int64")
    assert informalidad(df).tolist() == [0, pd.NA, pd.NA]


def _base_frame(**overrides):
    data = {
        "fex": [100.0], "edad": [30], "sexo": [1], "ingreso_laboral": [1000.0],
        "horas_semanales": [40], "semanas_buscando": [pd.NA], "nivel_educativo": [10],
    }
    data.update(overrides)
    return pd.DataFrame(data).convert_dtypes()


@pytest.mark.parametrize("fex", [0.0, -5.0, None])
def test_clean_drops_rows_without_valid_weight(fex):
    report = TransformReport()
    out = clean(_base_frame(fex=[fex]), report)
    assert out.empty
    assert report.invalid_weight_removed == 1


@pytest.mark.parametrize(
    "field, value",
    [("edad", 150), ("edad", -1), ("sexo", 3), ("ingreso_laboral", -1.0),
     ("horas_semanales", 200), ("nivel_educativo", 50)],
)
def test_clean_nullifies_out_of_range_values(field, value):
    report = TransformReport()
    out = clean(_base_frame(**{field: [value]}), report)
    assert pd.isna(out[field].iloc[0])
    assert report.values_nullified == {field: 1}


def test_clean_does_not_count_already_missing_values():
    report = TransformReport()
    clean(_base_frame(nivel_educativo=[pd.NA]), report)
    assert report.values_nullified == {}
