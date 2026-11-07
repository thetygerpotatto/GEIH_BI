"""Formato numérico en español (coma decimal, punto de miles)."""
from __future__ import annotations


def _es(number: str) -> str:
    return number.replace(",", "_").replace(".", ",").replace("_", ".")


def fmt_pct(value: float | None, decimals: int = 1) -> str:
    return "—" if value is None else f"{_es(f'{value:,.{decimals}f}')} %"


def fmt_pp(value: float | None) -> str | None:
    """Variación en puntos porcentuales con signo, o None si no aplica."""
    return None if value is None else f"{'+' if value >= 0 else '−'}{_es(f'{abs(value):,.1f}')} p.p."


def fmt_thousands(people: float | None) -> str:
    """Personas expresadas en miles: 23456789 -> '23.456,8 mil'."""
    return "—" if people is None else f"{_es(f'{people / 1000:,.1f}')} mil"


def fmt_int(value: int) -> str:
    return _es(f"{value:,}")
