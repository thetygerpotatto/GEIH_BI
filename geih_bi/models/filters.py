"""Filtros del dashboard y su traducción a consultas MongoDB (patrón Builder)."""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Iterable

DEFAULT_YEAR = 2025


@dataclass(frozen=True)
class DashboardFilters:
    """Selección del usuario. Una tupla vacía significa "todos los valores"."""

    anios: tuple[int, ...] = (DEFAULT_YEAR,)
    meses: tuple[int, ...] = ()
    dptos: tuple[str, ...] = ()
    clases: tuple[int, ...] = ()
    sexos: tuple[int, ...] = ()
    rangos_edad: tuple[str, ...] = ()
    grupos_educativos: tuple[str, ...] = ()

    def previous_year(self) -> "DashboardFilters | None":
        """Mismos filtros un año antes; solo aplica si hay exactamente un año seleccionado."""
        if len(self.anios) != 1:
            return None
        return replace(self, anios=(self.anios[0] - 1,))

    def without_time(self) -> "DashboardFilters":
        """Mismos filtros sin restricción de año ni mes (para series históricas)."""
        return replace(self, anios=(), meses=())


class FilterQueryBuilder:
    """Construye el documento ``$match`` paso a paso."""

    def __init__(self) -> None:
        self._match: dict[str, Any] = {}

    def _in(self, field: str, values: Iterable) -> "FilterQueryBuilder":
        values = list(values)
        if values:
            self._match[field] = values[0] if len(values) == 1 else {"$in": values}
        return self

    def years(self, values: Iterable[int]) -> "FilterQueryBuilder":
        return self._in("anio", values)

    def months(self, values: Iterable[int]) -> "FilterQueryBuilder":
        return self._in("mes", values)

    def departments(self, values: Iterable[str]) -> "FilterQueryBuilder":
        return self._in("dpto", values)

    def zones(self, values: Iterable[int]) -> "FilterQueryBuilder":
        return self._in("clase", values)

    def sexes(self, values: Iterable[int]) -> "FilterQueryBuilder":
        return self._in("sexo", values)

    def age_ranges(self, values: Iterable[str]) -> "FilterQueryBuilder":
        return self._in("rango_edad", values)

    def education_groups(self, values: Iterable[str]) -> "FilterQueryBuilder":
        return self._in("grupo_educativo", values)

    def build(self) -> dict[str, Any]:
        return dict(self._match)

    @classmethod
    def from_filters(cls, filters: DashboardFilters) -> dict[str, Any]:
        return (
            cls()
            .years(filters.anios)
            .months(filters.meses)
            .departments(filters.dptos)
            .zones(filters.clases)
            .sexes(filters.sexos)
            .age_ranges(filters.rangos_edad)
            .education_groups(filters.grupos_educativos)
            .build()
        )
