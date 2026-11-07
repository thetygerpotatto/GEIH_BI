import pytest

from geih_bi.controllers.dashboard import DashboardController
from geih_bi.models.filters import DashboardFilters
from geih_bi.models.repositories import CubeRepository


@pytest.fixture
def controller(seeded_db):
    return DashboardController(CubeRepository(seeded_db))


def test_kpis_weighted_rates(controller):
    s = controller.kpis(DashboardFilters(anios=(2025,), dptos=("76",)))
    assert s.actual.td == pytest.approx(120 / 1200 * 100)
    assert s.meses == 1
    assert s.muestra == 250


def test_kpis_year_over_year_variation(controller):
    s = controller.kpis(DashboardFilters(anios=(2025,), dptos=("76",)))
    assert s.variacion("td") == pytest.approx(10.0 - 12.5)


def test_no_variation_without_previous_data_or_with_many_years(controller):
    assert controller.kpis(DashboardFilters(anios=(2024,))).variacion("td") is None
    assert controller.kpis(DashboardFilters(anios=(2024, 2025))).variacion("td") is None


def test_kpis_average_populations_over_months(controller):
    s = controller.kpis(DashboardFilters(anios=(2024, 2025), dptos=("76",), sexos=(1,), rangos_edad=("29-44",)))
    assert s.meses == 2
    assert s.actual.ocupados == pytest.approx((540 + 552) / 2)


def test_small_sample_is_flagged(controller):
    assert controller.kpis(DashboardFilters(dptos=("11",))).muestra_insuficiente


def test_no_data_returns_none(controller):
    assert controller.kpis(DashboardFilters(anios=(2019,))) is None


def test_monthly_series_ignores_time_filters(controller):
    series = controller.monthly_series(DashboardFilters(anios=(2025,), meses=(1,), dptos=("76",)))
    assert series["periodo"].tolist() == [202401, 202501]
    assert series.loc[0, "td"] == pytest.approx(12.5)


def test_by_department_sorted_and_small_samples_removed(controller):
    df = controller.by_department(DashboardFilters(anios=(2025,)))
    assert df["departamento"].tolist() == ["Valle del Cauca"]


def test_by_sex_and_age_excludes_children(controller):
    df = controller.by_sex_and_age(DashboardFilters(anios=(2025,), dptos=("76",)))
    assert set(df["rango_edad"]) == {"29-44"}
    assert df.set_index("sexo_nombre")["td"].to_dict() == pytest.approx({"Hombre": 8.0, "Mujer": 12.0})


def test_available_years(controller):
    assert controller.available_years() == [2024, 2025]
