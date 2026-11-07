from geih_bi.models.filters import DashboardFilters, FilterQueryBuilder


def test_empty_filters_only_restrict_default_year():
    assert FilterQueryBuilder.from_filters(DashboardFilters()) == {"anio": 2025}


def test_single_value_is_equality_and_many_use_in():
    match = FilterQueryBuilder().years([2024, 2025]).departments(["76"]).build()
    assert match == {"anio": {"$in": [2024, 2025]}, "dpto": "76"}


def test_all_filters_are_combined():
    filters = DashboardFilters(anios=(2025,), meses=(1, 2), dptos=("76",), clases=(1,), sexos=(2,),
                               rangos_edad=("15-28",), grupos_educativos=("universitaria",))
    assert FilterQueryBuilder.from_filters(filters) == {
        "anio": 2025, "mes": {"$in": [1, 2]}, "dpto": "76", "clase": 1, "sexo": 2,
        "rango_edad": "15-28", "grupo_educativo": "universitaria",
    }


def test_builder_returns_a_copy():
    builder = FilterQueryBuilder().years([2025])
    builder.build()["anio"] = 1999
    assert builder.build() == {"anio": 2025}


def test_previous_year_only_with_one_year():
    assert DashboardFilters(anios=(2025,), sexos=(1,)).previous_year() == DashboardFilters(anios=(2024,), sexos=(1,))
    assert DashboardFilters(anios=(2024, 2025)).previous_year() is None
    assert DashboardFilters(anios=()).previous_year() is None


def test_without_time_keeps_other_filters():
    f = DashboardFilters(anios=(2025,), meses=(3,), dptos=("11",)).without_time()
    assert (f.anios, f.meses, f.dptos) == ((), (), ("11",))
