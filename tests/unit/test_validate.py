import pandas as pd

from geih_bi.etl.validate import validate_month


def _frame(**overrides):
    data = {"periodo": [202501, 202501], "dpto": ["76", "11"],
            "pet": [1, 1], "ft": [1, 1], "oci": [1, 0], "dsi": [0, 1]}
    data.update(overrides)
    return pd.DataFrame(data)


def test_valid_month_has_no_issues():
    assert validate_month(_frame(), td=10.0) == []


def test_detects_mixed_periods():
    assert any("periodo" in i for i in validate_month(_frame(periodo=[202501, 202502]), 10.0))


def test_detects_inconsistent_labor_force():
    assert any("FT != OCI + DSI" in i for i in validate_month(_frame(ft=[1, 0]), 10.0))


def test_detects_employed_outside_pet():
    assert any("fuera de la PET" in i for i in validate_month(_frame(pet=[0, 1]), 10.0))


def test_detects_missing_department():
    assert any("departamento" in i for i in validate_month(_frame(dpto=["76", None]), 10.0))


def test_detects_implausible_td():
    assert any("TD" in i for i in validate_month(_frame(), td=55.0))
    assert any("TD" in i for i in validate_month(_frame(), td=None))
