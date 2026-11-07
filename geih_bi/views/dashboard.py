"""Vista del tablero descriptivo: filtros (HU 16–18, 20), métricas (HU 10–11) y gráficas (HU 21–23)."""
from __future__ import annotations

import streamlit as st

from geih_bi.controllers.dashboard import MIN_SAMPLE, DashboardController
from geih_bi.core.permissions import Feature, has_feature
from geih_bi.etl import catalogs
from geih_bi.models.filters import DashboardFilters
from geih_bi.models.user import User
from geih_bi.views import charts
from geih_bi.views.formatting import fmt_int, fmt_pct, fmt_pp, fmt_thousands

FILTER_KEYS = ["f_anios", "f_meses", "f_dptos", "f_clases", "f_sexos", "f_edades", "f_educacion"]
_PENDING_DPTO = "dpto_desde_grafica"
EDADES = [r[2] for r in catalogs.RANGOS_EDAD if r[2] != "0-14"]
GRUPOS_EDUCATIVOS = [g for g in catalogs.GRUPO_EDUCATIVO if g != "sin_informacion"]


def _reset_filters(default_year: int) -> None:
    for key in FILTER_KEYS:
        st.session_state.pop(key, None)
    st.session_state["f_anios"] = [default_year]


def _filters(years: list[int]) -> DashboardFilters:
    default_year = years[-1]
    st.session_state.setdefault("f_anios", [default_year])
    pending = st.session_state.pop(_PENDING_DPTO, None)
    if pending:
        st.session_state["f_dptos"] = [pending]

    row1 = st.columns([1, 1.4, 1.6, 1.2])
    anios = row1[0].multiselect("Año", years, key="f_anios", placeholder="Todos")
    meses = row1[1].multiselect("Mes", list(catalogs.MESES), key="f_meses",
                                format_func=catalogs.MESES.get, placeholder="Todos")
    dptos = row1[2].multiselect("Departamento", list(catalogs.DEPARTAMENTOS), key="f_dptos",
                                format_func=catalogs.DEPARTAMENTOS.get, placeholder="Todos")
    clases = row1[3].multiselect("Zona", list(catalogs.CLASE), key="f_clases",
                                 format_func=catalogs.CLASE.get, placeholder="Todas")
    row2 = st.columns([1, 1.4, 1.6, 1.2])
    sexos = row2[0].multiselect("Sexo", list(catalogs.SEXO), key="f_sexos",
                                format_func=catalogs.SEXO.get, placeholder="Todos")
    edades = row2[1].multiselect("Rango de edad", EDADES, key="f_edades", placeholder="Todos")
    educacion = row2[2].multiselect("Nivel educativo", GRUPOS_EDUCATIVOS, key="f_educacion",
                                    format_func=catalogs.GRUPO_EDUCATIVO.get, placeholder="Todos")
    row2[3].button("Limpiar filtros", on_click=_reset_filters, args=(default_year,), width="stretch")

    return DashboardFilters(
        anios=tuple(anios), meses=tuple(meses), dptos=tuple(dptos), clases=tuple(clases),
        sexos=tuple(sexos), rangos_edad=tuple(edades), grupos_educativos=tuple(educacion),
    )


def _kpis(controller: DashboardController, filters: DashboardFilters):
    summary = controller.kpis(filters)
    if summary is None:
        st.warning("No hay datos para la combinación de filtros seleccionada.")
        return None
    if summary.muestra_insuficiente:
        st.warning(f"Muestra insuficiente ({summary.muestra} encuestados, mínimo {MIN_SAMPLE}): "
                   "las cifras no son representativas.")
    ind = summary.actual
    comparison = "frente al mismo periodo del año anterior" if summary.anterior else ""
    cols = st.columns(3)
    cols[0].metric("Tasa de desempleo (TD)", fmt_pct(ind.td), fmt_pp(summary.variacion("td")),
                   delta_color="inverse", help=f"Desocupados / fuerza de trabajo. Variación {comparison}.")
    cols[1].metric("Tasa de ocupación (TO)", fmt_pct(ind.to), fmt_pp(summary.variacion("to")),
                   help=f"Ocupados / población en edad de trabajar. Variación {comparison}.")
    cols[2].metric("Tasa global de participación (TGP)", fmt_pct(ind.tgp), fmt_pp(summary.variacion("tgp")),
                   help=f"Fuerza de trabajo / población en edad de trabajar. Variación {comparison}.")
    cols = st.columns(3)
    note = " (promedio mensual)" if summary.meses > 1 else ""
    cols[0].metric(f"Ocupados{note}", fmt_thousands(ind.ocupados))
    cols[1].metric(f"Desocupados{note}", fmt_thousands(ind.desocupados))
    cols[2].metric(f"Fuera de la fuerza de trabajo{note}", fmt_thousands(ind.inactivos))
    st.caption(f"{summary.meses} mes(es) · {fmt_int(summary.muestra)} encuestados · "
               "cifras expandidas con el factor FEX_C18 · Fuente: DANE, GEIH.")
    return summary


def _monthly_chart(controller: DashboardController, filters: DashboardFilters) -> None:
    series = controller.monthly_series(filters)
    if series.empty:
        return
    st.plotly_chart(charts.monthly_rates(series), width="stretch", key="g_mensual")
    with st.expander("Ver datos de la serie mensual"):
        st.dataframe(series[["periodo", "td", "to", "tgp"]].rename(
            columns={"periodo": "Periodo", "td": "TD (%)", "to": "TO (%)", "tgp": "TGP (%)"}),
            hide_index=True, width="stretch")


def _department_chart(controller: DashboardController, filters: DashboardFilters, national_td) -> None:
    df = controller.by_department(filters)
    if df.empty:
        return
    event = st.plotly_chart(charts.department_unemployment(df, national_td), width="stretch",
                            key="g_dptos", on_select="rerun", selection_mode="points")
    points = (event or {}).get("selection", {}).get("points", []) if event else []
    if points:
        dpto = points[0].get("customdata")
        dpto = dpto[0] if isinstance(dpto, list) else dpto
        if dpto and st.session_state.get("f_dptos") != [dpto]:
            st.session_state[_PENDING_DPTO] = dpto
            st.rerun()
    st.caption("Haga clic en una barra para filtrar por ese departamento. "
               f"Se omiten departamentos con menos de {MIN_SAMPLE} encuestados.")
    with st.expander("Ver datos por departamento"):
        st.dataframe(df[["departamento", "td", "to", "tgp", "n"]].rename(columns={
            "departamento": "Departamento", "td": "TD (%)", "to": "TO (%)", "tgp": "TGP (%)", "n": "Encuestados"}),
            hide_index=True, width="stretch")


def _sex_age_chart(controller: DashboardController, filters: DashboardFilters) -> None:
    df = controller.by_sex_and_age(filters)
    if df.empty:
        return
    st.plotly_chart(charts.unemployment_by_sex_age(df), width="stretch", key="g_sexo_edad")
    with st.expander("Ver datos por sexo y edad"):
        st.dataframe(df[["sexo_nombre", "rango_edad", "td", "n"]].rename(columns={
            "sexo_nombre": "Sexo", "rango_edad": "Rango de edad", "td": "TD (%)", "n": "Encuestados"}),
            hide_index=True, width="stretch")


def render(controller: DashboardController, user: User) -> None:
    st.title("Tablero del mercado laboral")
    years = controller.available_years()
    if not years:
        st.error("No hay datos cargados. Un administrador debe ejecutar el proceso ETL.")
        return
    filters = _filters(years)
    st.divider()
    summary = _kpis(controller, filters)
    if summary is None:
        return
    st.subheader("Evolución mensual 2022–2025")
    _monthly_chart(controller, filters)
    if has_feature(user.rol, Feature.GRAFICA_SEXO_EDAD):
        left, right = st.columns([1.1, 1])
        with left:
            _department_chart(controller, filters, summary.actual.td)
        with right:
            _sex_age_chart(controller, filters)
    else:
        _department_chart(controller, filters, summary.actual.td)
