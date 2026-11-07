import pandas as pd
import pytest

from geih_bi.analytics.indicators import compute_indicators, indicators_from_sums


def test_indicators_from_sums():
    ind = indicators_from_sums({"w_pet": 1000, "w_ft": 600, "w_oci": 540, "w_dsi": 60, "w_fft": 400})
    assert ind.td == pytest.approx(10.0)
    assert ind.to == pytest.approx(54.0)
    assert ind.tgp == pytest.approx(60.0)


def test_multiple_months_average_populations_but_not_rates():
    sums = {"w_pet": 2000, "w_ft": 1200, "w_oci": 1080, "w_dsi": 120, "w_fft": 800}
    ind = indicators_from_sums(sums, n_months=2)
    assert ind.ocupados == pytest.approx(540)
    assert ind.td == pytest.approx(10.0)


def test_zero_denominator_returns_none():
    ind = indicators_from_sums({})
    assert ind.td is None and ind.to is None and ind.tgp is None


def test_invalid_months():
    with pytest.raises(ValueError):
        indicators_from_sums({}, n_months=0)


def test_compute_indicators_uses_expansion_factor():
    df = pd.DataFrame({
        "anio": [2025] * 3, "mes": [1] * 3,
        "fex": [300.0, 100.0, 600.0],
        "pet": [1, 1, 1], "ft": [1, 1, 0], "oci": [1, 0, 0], "dsi": [0, 1, 0], "fft": [0, 0, 1],
    })
    ind = compute_indicators(df)
    assert ind.td == pytest.approx(25.0)  # 100 / 400
    assert ind.tgp == pytest.approx(40.0)  # 400 / 1000


def test_synthetic_month_indicators(month_zip):
    from geih_bi.etl.extract import MonthArchive, read_module_csv
    from geih_bi.etl.transform import transform_month

    raw = MonthArchive(month_zip, 2025).read_raw_modules()
    df, _ = transform_month({m: read_module_csv(d, m).frame for m, d in raw.items()})
    ind = compute_indicators(df)
    assert ind.td == pytest.approx(100 / 3)  # 1 desocupado de 3 en la FT
    assert ind.tgp == pytest.approx(75.0)  # 3 de 4 en la PET
