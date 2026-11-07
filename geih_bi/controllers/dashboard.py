"""Controlador del tablero descriptivo (HU 10, 11, 21, 22, 23)."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from geih_bi.analytics.indicators import LaborIndicators, add_rates, indicators_from_sums
from geih_bi.etl import catalogs
from geih_bi.models.filters import DashboardFilters, FilterQueryBuilder
from geih_bi.models.repositories import CUBE_MEASURES, CubeRepository

MIN_SAMPLE = 30


@dataclass(frozen=True)
class KpiSummary:
    actual: LaborIndicators
    anterior: LaborIndicators | None
    muestra: int
    meses: int

    @property
    def muestra_insuficiente(self) -> bool:
        return self.muestra < MIN_SAMPLE

    def variacion(self, campo: str) -> float | None:
        """Variación en puntos porcentuales frente al mismo periodo del año anterior."""
        if self.anterior is None:
            return None
        actual, anterior = getattr(self.actual, campo), getattr(self.anterior, campo)
        if actual is None or anterior is None:
            return None
        return actual - anterior


class DashboardController:
    def __init__(self, cube: CubeRepository) -> None:
        self._cube = cube

    def _by_period(self, filters: DashboardFilters) -> pd.DataFrame:
        return self._cube.aggregate(FilterQueryBuilder.from_filters(filters), ["periodo"])

    def _indicators(self, filters: DashboardFilters) -> tuple[LaborIndicators, int, int] | None:
        df = self._by_period(filters)
        if df.empty:
            return None
        sums = df[CUBE_MEASURES].sum().to_dict()
        return indicators_from_sums(sums, n_months=len(df)), int(sums["n"]), len(df)

    def kpis(self, filters: DashboardFilters) -> KpiSummary | None:
        current = self._indicators(filters)
        if current is None:
            return None
        previous_filters = filters.previous_year()
        previous = self._indicators(previous_filters) if previous_filters else None
        indicators, sample, months = current
        return KpiSummary(
            actual=indicators,
            anterior=previous[0] if previous else None,
            muestra=sample,
            meses=months,
        )

    def monthly_series(self, filters: DashboardFilters) -> pd.DataFrame:
        """TD/TO/TGP mes a mes para todo el histórico (respeta los filtros no temporales)."""
        df = self._by_period(filters.without_time())
        if df.empty:
            return df
        df = add_rates(df).sort_values("periodo")
        df["fecha"] = pd.to_datetime(df["periodo"].astype(str), format="%Y%m")
        return df[["periodo", "fecha", "td", "to", "tgp", "n"]].reset_index(drop=True)

    def by_department(self, filters: DashboardFilters) -> pd.DataFrame:
        df = self._cube.aggregate(FilterQueryBuilder.from_filters(filters), ["dpto"])
        if df.empty:
            return df
        df = add_rates(df)
        df["departamento"] = df["dpto"].map(catalogs.DEPARTAMENTOS).fillna(df["dpto"])
        df = df[df["n"] >= MIN_SAMPLE].sort_values("td", ascending=False)
        return df[["dpto", "departamento", "td", "to", "tgp", "n"]].reset_index(drop=True)

    def by_sex_and_age(self, filters: DashboardFilters) -> pd.DataFrame:
        df = self._cube.aggregate(FilterQueryBuilder.from_filters(filters), ["sexo", "rango_edad"])
        if df.empty:
            return df
        df = add_rates(df).dropna(subset=["td", "sexo", "rango_edad"])
        df = df[df["rango_edad"] != "0-14"]
        df["sexo_nombre"] = df["sexo"].map(catalogs.SEXO)
        order = [r[2] for r in catalogs.RANGOS_EDAD]
        df["orden"] = df["rango_edad"].map(order.index)
        return df.sort_values(["orden", "sexo"])[["sexo", "sexo_nombre", "rango_edad", "td", "n"]].reset_index(
            drop=True
        )

    def available_years(self) -> list[int]:
        return sorted({p // 100 for p in self._cube.available_periods()})
